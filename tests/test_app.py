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
