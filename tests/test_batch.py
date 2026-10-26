import pandas as pd
import pytest

from supportflow.batch import classify_batch, export_csv, read_tickets
from supportflow.model import TicketClassifier


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"message\nhello",
        b"text\n",
        b"text,text\none,two",
        b"text\none,two",
        b"text\n\xff",
        b"text\n" + b"x" * 1_000_001,
        b"text\n" + b"Where is my card\n" * 251,
    ],
    ids=[
        "empty",
        "missing-column",
        "header-only",
        "duplicate-header",
        "ragged-row",
        "bad-encoding",
        "oversize",
        "too-many-rows",
    ],
)
def test_bad_csv_is_rejected(content):
    with pytest.raises(ValueError):
        read_tickets(content)


def test_csv_bom_and_quoted_newline():
    frame = read_tickets('\ufefftext,id\n"Where is\nmy card",123\n'.encode())
    assert len(frame) == 1
    assert frame.text.iloc[0] == "Where is\nmy card"
    assert list(frame.columns) == ["text"]


def test_batch_preserves_invalid_rows_and_order():
    frame = pd.DataFrame({"text": ["Where is my card", "", "I was charged twice at the shop"]})
    result = classify_batch(frame, TicketClassifier.load(), threshold=1.0)
    assert result.row.tolist() == [1, 2, 3]
    assert result.status.tolist() == ["Needs review", "Invalid ticket", "Needs review"]
    assert result.iloc[1].reason
    assert result.iloc[2].intent == "transaction_charged_twice"


def test_export_neutralizes_spreadsheet_formulas():
    exported = export_csv(pd.DataFrame({"text": ["=SUM(1,2)", " +cmd", "@test", "normal"]})).decode(
        "utf-8-sig"
    )
    assert "'=SUM" in exported
    assert "' +cmd" in exported
    assert "'@test" in exported
    assert "normal" in exported
