import joblib
import numpy as np
import pytest

from supportflow.model import routing_decisions
from supportflow.train import choose_threshold, save_artifact


def test_unsupported_precision_target_falls_back_to_review_all():
    probabilities = np.tile([1.0, 0.0], (120, 1))
    threshold, _ = choose_threshold(probabilities, np.repeat("b", 120), np.array(["a", "b"]))
    assert threshold == 1.0
    assert not routing_decisions(probabilities, threshold).any()


def test_threshold_curve_uses_the_exact_reported_threshold():
    probabilities = np.tile([0.3, 0.15, 0.14, 0.14, 0.14, 0.13], (120, 1))
    classes = np.array(["a", "b", "c", "d", "e", "f"])
    threshold, curve = choose_threshold(probabilities, np.repeat("a", 120), classes)
    for point in curve:
        assert point["accepted"] == int(routing_decisions(probabilities, point["threshold"]).sum())
    assert threshold == 0.3


def test_failed_save_preserves_previous_model(monkeypatch, tmp_path):
    destination = tmp_path / "model.joblib"
    joblib.dump({"version": "working"}, destination)

    def fail_dump(artifact, file, **kwargs):
        file.write(b"partial broken model")
        raise OSError("simulated interrupted write")

    monkeypatch.setattr("supportflow.train.joblib.dump", fail_dump)
    with pytest.raises(OSError, match="interrupted"):
        save_artifact({"version": "new"}, destination)
    assert joblib.load(destination) == {"version": "working"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["model.joblib"]


def test_successful_save_replaces_previous_model(tmp_path):
    destination = tmp_path / "model.joblib"
    save_artifact({"version": "first"}, destination)
    save_artifact({"version": "second"}, destination)
    assert joblib.load(destination) == {"version": "second"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["model.joblib"]
