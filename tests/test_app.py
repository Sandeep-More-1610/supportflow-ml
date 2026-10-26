from streamlit.testing.v1 import AppTest

from supportflow.data import ROOT


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_classify_invalid_input_and_stale_results():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    button(app, "Classify ticket").click().run()
    assert not app.exception
    assert app.session_state["prediction"]["intent"] == "card_arrival"
    app.text_area[0].set_value("help").run()
    assert any("changed" in item.value for item in app.info)
    button(app, "Classify ticket").click().run()
    assert app.error
    assert "three words" in app.error[0].value
    assert not app.exception


def test_review_workflow_and_duplicate_prevention():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    button(app, "Classify ticket").click().run()
    button(app, "Add to review queue").click().run()
    button(app, "Add to review queue").click().run()
    assert len(app.session_state["review_queue"]) == 1
    app.sidebar.radio[0].set_value("Review queue").run()
    assert not app.exception
    app.selectbox[1].set_value("card_delivery_estimate").run()
    button(app, "Save review").click().run()
    assert app.session_state["review_queue"][0]["status"] == "Reviewed"
    assert app.session_state["review_queue"][0]["corrected_intent"] == "card_delivery_estimate"
    assert not app.exception


def test_all_pages_load_and_empty_states():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    for page in ["Batch desk", "Review queue", "Model report", "Triage ticket"]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page


def test_ticket_draft_and_prediction_survive_navigation():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    message = "I was charged twice for the same purchase"
    app.text_area[0].set_value(message).run()
    button(app, "Classify ticket").click().run()
    for page in ["Review queue", "Batch desk", "Model report", "Triage ticket"]:
        app.sidebar.radio[0].set_value(page).run()
    assert app.text_area[0].value == message
    assert app.session_state["prediction"]["text"] == message
    assert any(item.label == "Add to review queue" for item in app.button)
    assert not app.exception


def test_model_revision_invalidates_old_results_but_preserves_review_records():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    button(app, "Classify ticket").click().run()
    button(app, "Add to review queue").click().run()
    app.session_state["active_model_stamp"] = "previous-model-version"
    app.session_state["batch_result"] = ("previous-model-version", "old-results")
    app.run()
    assert "prediction" not in app.session_state
    assert "batch_result" not in app.session_state
    assert len(app.session_state["review_queue"]) == 1
    assert not app.exception


def test_batch_results_survive_navigation_and_clear_removes_them():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    app.session_state["batch_source"] = {
        "name": "tickets.csv",
        "content": b"text\nWhere is my card\n\n",
    }
    app.sidebar.radio[0].set_value("Batch desk").run()
    button(app, "Classify batch").click().run()
    app.sidebar.radio[0].set_value("Review queue").run()
    app.sidebar.radio[0].set_value("Batch desk").run()
    assert app.session_state["batch_result"][1].status.tolist() == [
        "Ready to route",
        "Invalid ticket",
    ]
    assert any(item.label == "Invalid tickets" for item in app.metric)
    button(app, "Clear loaded batch").click().run()
    assert "batch_source" not in app.session_state
    assert "batch_result" not in app.session_state
    assert any("Choose a CSV" in item.value for item in app.info)
    assert not app.exception


def test_missing_model_shows_recovery_instructions(monkeypatch, tmp_path):
    import supportflow.model

    monkeypatch.setattr(supportflow.model, "MODEL_PATH", tmp_path / "absent.joblib")
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    assert "model is missing" in app.error[0].value


def test_model_load_failure_shows_recovery_instructions(monkeypatch, tmp_path):
    import supportflow.model

    artifact = tmp_path / "broken.joblib"
    artifact.write_bytes(b"broken")
    monkeypatch.setattr(supportflow.model, "MODEL_PATH", artifact)

    def fail_load(*args, **kwargs):
        raise OSError("broken artifact")

    monkeypatch.setattr(supportflow.model.TicketClassifier, "load", fail_load)
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    assert "could not be loaded" in app.error[0].value
