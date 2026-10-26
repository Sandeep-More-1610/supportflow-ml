"""Bounded CSV ingestion, row errors and spreadsheet-safe export."""

from __future__ import annotations

import csv
import io

import pandas as pd

from supportflow.model import TicketClassifier, validate_text

MAX_BYTES = 1_000_000
MAX_ROWS = 250


def read_tickets(content: bytes) -> pd.DataFrame:
    if len(content) > MAX_BYTES:
        raise ValueError("Upload a CSV smaller than 1 MB.")
    try:
        decoded = content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(decoded), strict=True)
        header = next(reader, None)
        if not header or "text" not in header:
            raise ValueError(
                "The CSV needs a column named text. Download the sample to get started."
            )
        if len(set(header)) != len(header):
            raise ValueError("CSV column names must be unique.")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(
                    "Every CSV row must have the same number of columns as the header."
                )
            rows.append(row)
            if len(rows) > MAX_ROWS:
                raise ValueError(f"Upload at most {MAX_ROWS} tickets at a time.")
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(
            "Use a valid UTF-8 CSV file. Download the sample for the expected format."
        ) from error
    if not rows:
        raise ValueError("The CSV contains a header but no tickets.")
    return pd.DataFrame(rows, columns=header)[["text"]]


def classify_batch(frame: pd.DataFrame, model: TicketClassifier, threshold: float) -> pd.DataFrame:
    rows, valid_texts, valid_positions = [], [], []
    for i, text in enumerate(frame["text"]):
        row = {
            "row": i + 1,
            "text": text,
            "intent": "",
            "suggested_team": "",
            "score": None,
            "status": "Invalid ticket",
            "reason": "",
        }
        try:
            valid_texts.append(validate_text(text))
            valid_positions.append(i)
        except ValueError as error:
            row["reason"] = str(error)
        rows.append(row)
    for position, prediction in zip(
        valid_positions, model.predict_many(valid_texts, threshold), strict=True
    ):
        rows[position].update(
            {
                "intent": prediction["intent"],
                "suggested_team": prediction["team"],
                "score": prediction["score"],
                "status": "Needs review" if prediction["needs_review"] else "Ready to route",
                "reason": "; ".join(prediction["review_reasons"]),
            }
        )
    return pd.DataFrame(rows)


def export_csv(frame: pd.DataFrame) -> bytes:
    def protect(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    return frame.map(protect).to_csv(index=False).encode("utf-8-sig")
