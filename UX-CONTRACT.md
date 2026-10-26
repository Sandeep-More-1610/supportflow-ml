# SupportFlow interaction contract

## Product evidence and scope

Source: the user's request for a complete internship portfolio project in VS Code,
and the selected support-ticket classification brief in README.md. Dataset facts
come from DATASET.md; model limits come from MODEL_CARD.md and reports/metrics.json.
This is a local demonstration, with no operational banking authority.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | Streamlit st.selectbox | DESIGN.md | Authored library popup | Browser keyboard and popup check |
| Form | Streamlit widgets and supportflow validators | This contract | Single ticket, CSV upload | tests/test_app.py and tests/test_batch.py |
| Scrollbar | assets/app.css | assets/tokens.json | Global, forced colors | Browser computed styles |
| Toast | Streamlit inline status elements | This contract | Info, success, warning, error | tests/test_app.py |

- **Select/Listbox**: Streamlit `st.selectbox`, authored library control. Used for
  examples, batch status, review selection and corrected intent. Keyboard and popup
  behavior are owned by Streamlit; browser smoke checks cover representative use.
- **Form**: Streamlit `st.text_area`, `st.button`, `st.file_uploader`; server validation
  in `supportflow/model.py` and `supportflow/batch.py`. No native HTML form validation.
- **Scrollbar**: global `assets/app.css` with tokens from `assets/tokens.json`.
- **Toast**: persistent Streamlit `st.info`, `st.success`, `st.warning`, `st.error`.
  No transient toast is the only copy of an important message.
- **Data display**: `st.dataframe` with bounded rows and internal scrolling. No custom
  table-selection or destructive bulk operations.
- **Navigation**: sidebar `st.radio`; four views in one Streamlit session.

## State and flows

Triage: enter text → classify → inspect suggestion → optionally add to review queue.
Input is preserved after errors. A changed message or threshold hides stale results.
Adding the same trimmed ticket twice does not duplicate it. No classification sends
anything to a real support team. Error, empty and success states are inline.

Batch: pick CSV → validate structure/limits → classify → inspect status-filtered rows
→ export all rows. The UI rejects files over 1 MB or 250 rows. Invalid individual
tickets remain in the output with their reason. Changing upload or threshold hides
previous output. CSV export escapes spreadsheet formula prefixes.

Review: choose an awaiting ticket → confirm/correct intent → save → move to the next
pending ticket. Records stay in session memory; an export preserves them. Corrections
do not retrain the model. The queue is bounded at 250 tickets. No deletion workflow.

Report: read the frozen experiment results and download evidence. The sidebar's
threshold does not rewrite historical evaluation metrics. Missing detailed local
error records have regeneration instructions.

## Lifecycle and privacy

No authentication, payments, permissions, deletion, or legal-policy UI is in scope.
Inputs, batch results, and review corrections are transient and never saved to app
files or training data automatically. URL state deliberately omits customer text,
selection and filters. Page reload may reset session state; export guidance is visible.
Local network inference requires the Streamlit server to remain running. Streamlit
owns reconnect/session behavior. The application does not promise offline browser use.

## Verification ownership

`tests/test_model.py`: inference, invalid input, uncertainty and explanation contracts.
`tests/test_batch.py`: upload bounds, row recovery and safe CSV export.
`tests/test_app.py`: navigation, classification, stale results and review corrections.
`tests/test_project.py`: split integrity, model selection and theme token drift.
`scripts/browser_smoke.py`: actual browser workflow, uploads, download, keyboard,
viewport, screenshots and reduced motion; run against the local server.
