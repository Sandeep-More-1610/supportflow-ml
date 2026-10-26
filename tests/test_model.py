import numpy as np
import pytest

from supportflow.model import TicketClassifier, routing_decisions, validate_text


@pytest.fixture(scope="module")
def model():
    return TicketClassifier.load()


@pytest.mark.parametrize("text", ["", "   ", "help", "two words", "x" * 4001, None])
def test_invalid_tickets_are_rejected(text):
    with pytest.raises(ValueError):
        validate_text(text)


def test_margin_gate_rejects_ambiguous_predictions():
    scores = np.array([[0.46, 0.45, 0.09], [0.8, 0.1, 0.1], [0.4, 0.3, 0.3]])
    assert routing_decisions(scores, 0.45).tolist() == [False, True, False]


def test_single_and_batch_predictions_match(model):
    text = "I was charged twice for the same purchase at a shop"
    single = model.predict(text)
    batch = model.predict_many([text])[0]
    assert single == batch
    assert single["intent"] == "transaction_charged_twice"
    assert len(single["alternatives"]) == 3
    assert 0 <= single["score"] <= 1


def test_strict_threshold_always_requires_review(model):
    result = model.predict("My card has not arrived after two weeks", threshold=1)
    assert result["needs_review"]
    assert result["review_reasons"]


@pytest.mark.parametrize("threshold", [-0.1, 1.1, float("nan")])
def test_invalid_threshold(model, threshold):
    with pytest.raises(ValueError):
        model.predict("Where is my card", threshold)


def test_unknown_vocabulary_abstains(model):
    result = model.predict("zzqqxxvv zzqqxxvv zzqqxxvv")
    assert result["needs_review"]


def test_explanations_have_positive_word_contributions(model):
    text = "I was charged twice for the same purchase"
    result = model.predict(text)
    evidence = model.explain(text, result["intent"])
    assert evidence
    assert all(item["contribution"] > 0 for item in evidence)
    assert not any(item["feature"].startswith("char__") for item in evidence)


def test_artifact_has_all_intents_and_reproducibility_metadata(model):
    assert len(model.classes) == 77
    assert model.metadata["data_audit"]["seed"] == 42
    assert len(model.metadata["dataset"]["revision"]) == 40
    assert model.metadata["test_metrics"]["macro_f1"] > 0.70
