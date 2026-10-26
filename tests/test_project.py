import json
import tomllib

import pandas as pd
import pytest

from supportflow.data import ROOT, download_data, fingerprint


def test_modified_dataset_cache_is_rejected(tmp_path):
    (tmp_path / "train.csv").write_text("modified data", encoding="utf-8")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        download_data(tmp_path)


def test_normalization_catches_case_punctuation_and_spacing():
    assert fingerprint("WHERE's my CARD?!") == fingerprint("where s   my card")


def test_fitting_validation_and_test_are_disjoint():
    splits = pd.read_csv(ROOT / "reports" / "split_audit.csv")
    groups = {name: set(frame.fingerprint) for name, frame in splits.groupby("split")}
    assert not groups["fit"] & groups["validation"]
    assert not groups["fit"] & groups["test"]
    assert not groups["validation"] & groups["test"]


def test_model_selection_uses_validation_only():
    report = json.loads((ROOT / "reports" / "metrics.json").read_text())
    best = max(report["models"][1:], key=lambda row: row["validation"]["macro_f1"])
    assert report["selected_model"] == best["name"]
    assert report["test_metrics"] == best["test"]


def test_theme_tokens_do_not_drift():
    tokens = json.loads((ROOT / "assets" / "tokens.json").read_text())["colors"]
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())["theme"]
    assert config["primaryColor"] == tokens["primary"]
    assert config["backgroundColor"] == tokens["background"]
    assert config["textColor"] == tokens["text"]
    assert config["secondaryBackgroundColor"] == tokens["rail"]
    design = (ROOT / "DESIGN.md").read_text()
    assert all(f'{key}: "{value}"' in design for key, value in tokens.items())
