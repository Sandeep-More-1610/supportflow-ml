"""Download a pinned public dataset and prepare leakage-aware splits."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.request import urlopen

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"
REVISION = "57ec275d8078af65b7731c2a98be812d844a6d6b"
SOURCE = f"https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/{REVISION}"
SEED = 42
EXPECTED_HASHES = {
    "train.csv": "b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b",
    "test.csv": "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d",
    "categories.json": "53261da888122daf2d120d925458631d9619e15d82e56052e7a42e535ce32b63",
}


def fingerprint(text: str) -> str:
    """Normalize case, punctuation and whitespace for exact duplicate checks."""
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[\W_]+", " ", text).strip()


def download_data(directory: Path = DATA_DIR) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in ("train.csv", "test.csv", "categories.json"):
        path = directory / name
        url = f"{SOURCE}/banking_data/{name}"
        if not path.exists():
            with urlopen(url, timeout=60) as response:
                content = response.read()
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_bytes(content)
            temporary.replace(path)
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        if checksum != EXPECTED_HASHES[name]:
            raise ValueError(
                f"Checksum mismatch for {name}. Remove that cached file and download again."
            )
        files[name] = {
            "url": url,
            "sha256": checksum,
        }
    manifest = {"dataset": "BANKING77", "revision": REVISION, "files": files}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_splits(directory: Path = DATA_DIR):
    train = pd.read_csv(directory / "train.csv", keep_default_na=False)
    test = pd.read_csv(directory / "test.csv", keep_default_na=False)
    for frame in (train, test):
        if set(frame.columns) != {"text", "category"}:
            raise ValueError("Expected BANKING77 columns: text, category.")
        if frame["text"].str.strip().eq("").any():
            raise ValueError("Dataset contains empty text.")
        frame["fingerprint"] = frame["text"].map(fingerprint)
    original_count = len(train)
    conflicts = train.groupby("fingerprint")["category"].nunique()
    conflicting_keys = set(conflicts[conflicts > 1].index)
    train = train[~train.fingerprint.isin(conflicting_keys)].copy()
    conflicts_removed = original_count - len(train)
    before_dedup = len(train)
    train = train.drop_duplicates("fingerprint")
    duplicates_removed = before_dedup - len(train)
    overlap = train.fingerprint.isin(set(test.fingerprint))
    overlaps_removed = int(overlap.sum())
    train = train[~overlap].copy()
    fit, validation = train_test_split(
        train, test_size=0.2, random_state=SEED, stratify=train.category
    )
    audit = {
        "original_train_rows": original_count,
        "conflicting_train_rows_removed": conflicts_removed,
        "duplicate_train_rows_removed": duplicates_removed,
        "train_test_overlap_rows_removed_from_train": overlaps_removed,
        "fit_rows": len(fit),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "test_duplicate_fingerprints": int(test.fingerprint.duplicated().sum()),
        "intents": int(train.category.nunique()),
        "seed": SEED,
        "test_policy": "Official test unchanged; normalized exact overlap removed from training only.",
    }
    return fit.reset_index(drop=True), validation.reset_index(drop=True), test, audit


if __name__ == "__main__":
    print(json.dumps(download_data(), indent=2))
