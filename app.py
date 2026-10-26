"""SupportFlow's interactive workspace. Run with streamlit run app.py."""

from __future__ import annotations

import hashlib
import json

import pandas as pd
import streamlit as st

from supportflow.batch import classify_batch, export_csv, read_tickets
from supportflow.data import ROOT
from supportflow.model import MODEL_PATH, TicketClassifier, display_intent, team_for
from supportflow.ui import apply_styles, page_heading, route_card

st.set_page_config(page_title="SupportFlow | Ticket triage", page_icon="↗", layout="wide")
apply_styles()

EXAMPLES = {
    "Delayed card": "My card has not arrived and I ordered it two weeks ago.",
    "Duplicate payment": "I was charged twice for the same purchase at a shop.",
    "Pending transfer": "The bank transfer I sent yesterday is still pending.",
    "Unclear request": "Something is wrong with my account. Can you help me please?",
}


@st.cache_resource(show_spinner="Loading the ticket classifier…")
def load_model(stamp):
    return TicketClassifier.load()


def set_example(label):
    st.session_state.ticket_text = EXAMPLES[label]
    st.session_state.pop("prediction", None)


def triage(model, threshold):
    page_heading(
        "BANKING SUPPORT / TRIAGE",
        "Every ticket, a clearer next step.",
        "Identify the request, inspect the evidence, and decide who should handle it.",
    )
    left, right = st.columns([1.12, 1], gap="large")
    with left:
        st.subheader("Read the ticket")
        st.caption("Try an example, or paste an English banking-support request.")
        example = st.selectbox("Example ticket", list(EXAMPLES), key="example_choice")
        st.button("Load example", on_click=set_example, args=(example,))
        st.text_area(
            "Customer message",
            key="ticket_text",
            height=200,
            max_chars=4000,
            placeholder="Describe the issue in at least three words…",
            help="Up to 4,000 characters. Use sample or anonymized text.",
        )
        if st.button("Classify ticket", type="primary", width="stretch"):
            try:
                with st.spinner("Reading the ticket…"):
                    st.session_state.prediction = model.predict(
                        st.session_state.ticket_text, threshold
                    )
            except ValueError as error:
                st.session_state.pop("prediction", None)
                st.error(str(error))
        st.caption("Local inference • No API key • Routing suggestions only")
    with right:
        st.subheader("Suggested next step")
        result = st.session_state.get("prediction")
        if result and (
            result["text"] != st.session_state.ticket_text.strip()
            or result["threshold"] != threshold
        ):
            result = None
            st.info("The ticket or threshold changed. Classify again to update the suggestion.")
        if not result:
            with st.container(border=True):
                st.markdown("**Your routing suggestion will appear here.**")
                st.write(
                    "Classify a ticket to see the likely intent, suggested team, and alternatives."
                )
                st.caption("Ambiguous requests are flagged for human review.")
            return
        route_card(result["team"], display_intent(result["intent"]), result["needs_review"])
        a, b = st.columns(2)
        a.metric("Top model score", f"{result['score']:.1%}")
        b.metric("Lead over runner-up", f"{result['margin']:.1%}")
        if result["needs_review"]:
            st.warning(" • ".join(result["review_reasons"]))
        st.caption("Scores are uncalibrated model estimates, not a guarantee of correctness.")
        with st.expander("Compare the top 3 intents", expanded=True):
            for alternative in result["alternatives"]:
                st.progress(
                    alternative["score"],
                    text=f"{display_intent(alternative['intent'])} · {alternative['score']:.1%}",
                )
        evidence = model.explain(result["text"], result["intent"])
        if evidence:
            st.markdown("**Words supporting this prediction**")
            st.write(" · ".join(item["feature"] for item in evidence))
            st.caption(
                "Positive word contributions to this intent's linear score; not a causal explanation."
            )
        if st.button("Add to review queue", width="stretch"):
            key = hashlib.sha256(result["text"].encode()).hexdigest()[:16]
            queue = st.session_state.review_queue
            if any(item["id"] == key for item in queue):
                st.info("This ticket is already in the review queue.")
            elif len(queue) >= 250:
                st.warning("The session queue is full (250 tickets). Export your review records.")
            else:
                queue.append(
                    {
                        "id": key,
                        "text": result["text"],
                        "predicted_intent": result["intent"],
                        "score": result["score"],
                        "corrected_intent": "",
                        "status": "Awaiting review",
                    }
                )
                st.success("Added to review queue. Open Review queue in the sidebar.")


def batch_desk(model, threshold):
    page_heading(
        "BATCH DESK",
        "Triage a whole inbox.",
        "Upload a CSV, inspect the suggestions, and download a reviewable result.",
    )
    st.download_button(
        "Download sample CSV",
        (ROOT / "data" / "sample_tickets.csv").read_bytes(),
        "sample_tickets.csv",
        "text/csv",
    )
    uploaded = st.file_uploader(
        "Upload tickets",
        type=["csv"],
        help="UTF-8 CSV with a text column. Maximum 1 MB and 250 tickets.",
    )
    if uploaded is None:
        st.info("Choose a CSV to begin. Only the text column is used; other columns are ignored.")
        return
    content = uploaded.getvalue()
    batch_key = (hashlib.sha256(content).hexdigest(), threshold)
    try:
        frame = read_tickets(content)
    except ValueError as error:
        st.error(str(error))
        return
    st.caption(f"{len(frame):,} tickets loaded. Invalid rows will be marked individually.")
    with st.expander("Preview uploaded tickets"):
        st.dataframe(frame.head(10), hide_index=True, width="stretch")
    if st.button("Classify batch", type="primary"):
        with st.spinner("Classifying the batch…"):
            st.session_state.batch_result = (batch_key, classify_batch(frame, model, threshold))
    saved = st.session_state.get("batch_result")
    if not saved or saved[0] != batch_key:
        return
    result = saved[1]
    a, b, c = st.columns(3)
    a.metric("Ready to route", int(result.status.eq("Ready to route").sum()))
    b.metric("Needs review", int(result.status.eq("Needs review").sum()))
    c.metric("Invalid tickets", int(result.status.eq("Invalid ticket").sum()))
    selected = st.selectbox(
        "Show tickets", ["All", "Needs review", "Ready to route", "Invalid ticket"]
    )
    shown = result if selected == "All" else result[result.status.eq(selected)]
    if shown.empty:
        st.info("No tickets match this status. Choose All to see the full batch.")
    else:
        st.dataframe(
            shown,
            hide_index=True,
            width="stretch",
            height=380,
            column_config={"score": st.column_config.NumberColumn("Model score", format="%.3f")},
        )
    st.download_button(
        "Download all results", export_csv(result), "supportflow_predictions.csv", "text/csv"
    )
    st.caption("Downloads include every uploaded row. Spreadsheet formula prefixes are escaped.")


def report_page(model):
    report = model.metadata
    page_heading(
        "MODEL REPORT",
        "Evidence behind the predictions.",
        "Measured on the official BANKING77 test set, after model selection on validation data.",
    )
    a, b, c = st.columns(3)
    a.metric("Test macro-F1", f"{report['test_metrics']['macro_f1']:.1%}")
    b.metric("Test accuracy", f"{report['test_metrics']['accuracy']:.1%}")
    c.metric("Test tickets", f"{report['data_audit']['test_rows']:,}")
    st.subheader("Model comparison")
    comparison = pd.DataFrame(
        [
            {
                "Model": row["name"],
                "Validation macro-F1": row["validation"]["macro_f1"],
                "Test macro-F1": row["test"]["macro_f1"],
                "Test accuracy": row["test"]["accuracy"],
            }
            for row in report["models"]
        ]
    )
    st.dataframe(comparison, hide_index=True, width="stretch")
    st.caption(
        f"Selected by validation macro-F1: {report['selected_model']}. The saved model is not refit on validation data."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("When to ask a human")
        routing = report["routing"]
        st.write(
            f"Default threshold: **{routing['threshold']:.1%}**, with a **{routing['minimum_margin']:.0%}** minimum lead over the runner-up."
        )
        st.metric("Test coverage at default threshold", f"{routing['test_coverage']:.1%}")
        precision = routing["test_accuracy_when_accepted"]
        st.metric(
            "Accuracy among accepted test tickets",
            f"{precision:.1%}" if precision else "No accepted tickets",
        )
        st.caption(
            "These figures use the frozen default threshold. The sidebar slider changes live suggestions only."
        )
        curve = pd.DataFrame(routing["validation_curve"]).set_index("threshold")
        st.line_chart(
            curve[["coverage", "accuracy_when_accepted"]],
            x_label="Review threshold (validation)",
            y_label="Fraction",
            height=240,
        )
    with right:
        st.subheader("How the experiment works")
        audit = report["data_audit"]
        st.write(
            f"**{audit['fit_rows']:,}** fitting examples → **{audit['validation_rows']:,}** validation examples → **{audit['test_rows']:,}** official test examples."
        )
        st.write(
            "The vocabulary is learned only from fitting data. Validation chooses the model and review threshold. Test labels are used only for final reporting."
        )
        st.write(
            f"Duplicate training rows removed: **{audit['duplicate_train_rows_removed']}**. Training rows overlapping the test set removed: **{audit['train_test_overlap_rows_removed_from_train']}**."
        )
        st.caption("Checks cover normalized exact text, not every possible paraphrase.")
        st.write(
            f"Median warm inference: **{report['latency_ms']['median']:.2f} ms** per ticket on the training machine (100 samples)."
        )
    with st.expander("Per-intent scores and confusion matrix"):
        path = ROOT / "reports" / "classification_report.json"
        if path.exists():
            scores = json.loads(path.read_text(encoding="utf-8"))
            rows = [
                {"Intent": name, **values}
                for name, values in scores.items()
                if isinstance(values, dict) and name in model.classes
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=350)
        matrix_path = ROOT / "reports" / "confusion_matrix.png"
        if matrix_path.exists():
            st.image(
                str(matrix_path),
                caption="Full 77-intent confusion matrix; download to inspect labels.",
            )
            st.download_button(
                "Download confusion matrix",
                matrix_path.read_bytes(),
                "confusion_matrix.png",
                "image/png",
            )
    with st.expander("Inspect misclassified test tickets"):
        errors_path = ROOT / "reports" / "errors.csv"
        if errors_path.exists():
            errors = pd.read_csv(errors_path)
            st.caption(f"{len(errors)} test errors. Highest-scoring mistakes appear first.")
            st.dataframe(errors, hide_index=True, width="stretch", height=350)
        else:
            st.info("Run python -m supportflow.train to regenerate detailed local error records.")
    with st.expander("Scope and limitations", expanded=True):
        for limitation in report["limitations"]:
            st.write(f"• {limitation}")
        st.markdown(
            "Dataset: [BANKING77 by PolyAI](https://github.com/PolyAI-LDN/task-specific-datasets), CC BY 4.0."
        )
    st.download_button(
        "Download evaluation JSON", json.dumps(report, indent=2), "metrics.json", "application/json"
    )


def review_page(model):
    page_heading(
        "HUMAN REVIEW",
        "Keep a person in the loop.",
        "Confirm or correct a prediction, then export the feedback for a future training cycle.",
    )
    queue = st.session_state.review_queue
    st.caption(
        "Review records live in this browser session. Export them before closing or refreshing it."
    )
    if not queue:
        st.info("No tickets to review yet. Classify a ticket and choose Add to review queue.")
        return
    st.dataframe(pd.DataFrame(queue), hide_index=True, width="stretch", height=250)
    pending = [item for item in queue if item["status"] == "Awaiting review"]
    if pending:
        choice = st.selectbox(
            "Ticket to review",
            [item["id"] for item in pending],
            format_func=lambda key: next(
                item["text"][:90] for item in pending if item["id"] == key
            ),
        )
        ticket = next(item for item in pending if item["id"] == choice)
        st.text(ticket["text"])
        corrected = st.selectbox(
            "Correct intent",
            list(model.classes),
            index=list(model.classes).index(ticket["predicted_intent"]),
            format_func=display_intent,
            key=f"correction_{choice}",
        )
        st.caption(f"Suggested team for this intent: {team_for(corrected)}")
        if st.button("Save review", type="primary"):
            ticket.update(corrected_intent=corrected, status="Reviewed")
            st.session_state.review_saved = True
            st.rerun()
    else:
        st.success("All queued tickets have been reviewed. Export the feedback below.")
    if st.session_state.pop("review_saved", False):
        st.success("Review saved in this session.")
    st.download_button(
        "Export review records",
        export_csv(pd.DataFrame(queue)),
        "supportflow_reviews.csv",
        "text/csv",
    )
    st.caption("Corrections do not automatically retrain or change the current model.")


def main():
    st.session_state.setdefault("ticket_text", EXAMPLES["Delayed card"])
    st.session_state.setdefault("review_queue", [])
    with st.sidebar:
        st.markdown("## ↗ SupportFlow")
        st.caption("A clearer route for every request.")
        st.divider()
        page = st.radio(
            "Workspace", ["Triage ticket", "Batch desk", "Review queue", "Model report"]
        )
    st.set_page_config(page_title=f"SupportFlow | {page}")
    if not MODEL_PATH.exists():
        st.error(
            "The trained model is missing. Run python -m supportflow.train, then refresh this page."
        )
        st.code("python -m supportflow.train", language="bash")
        return
    try:
        model = load_model(MODEL_PATH.stat().st_mtime_ns)
    except Exception:
        st.error(
            "The model could not be loaded. Install requirements.txt and rerun python -m supportflow.train."
        )
        return
    with st.sidebar:
        st.divider()
        st.markdown("**Review policy**")
        threshold = st.slider(
            "Minimum model score",
            0.0,
            1.0,
            model.threshold,
            0.025,
            help="Higher thresholds send more tickets for review. Scores are uncalibrated.",
        )
        st.caption(
            "A lead of at least 10 percentage points over the second intent is also required."
        )
        st.divider()
        st.caption(
            "77 banking intents · English\n\nPortfolio demo. No tickets are sent to a real support team."
        )
    if page == "Triage ticket":
        triage(model, threshold)
    elif page == "Batch desk":
        batch_desk(model, threshold)
    elif page == "Review queue":
        review_page(model)
    else:
        report_page(model)


main()
