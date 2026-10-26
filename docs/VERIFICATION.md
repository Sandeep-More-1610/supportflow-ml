# Verification record

Recorded on 26 October 2026 with Python 3.11.7 on Windows.

## Executed successfully

- `python -m supportflow.train`: trained all three ML candidates, chose the model
  on validation macro-F1, selected the review threshold, and evaluated the official
  test set. No convergence warning was reported. Artifacts are in models/ and reports/.
- `python -m pytest -q --junitxml=reports/test-results.xml`: **34 passed**.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: 21 Python files already formatted.
- `python -m compileall -q supportflow app.py`: passed.
- `python -m pip check`: no broken requirements.
- `python -m supportflow.predict "I was charged twice for the same purchase"`:
  predicted `transaction_charged_twice`, with Payments & refunds as the demo team.
- The three pinned dataset file hashes were verified against their expected values.
- `python scripts/browser_smoke.py`: all seven grouped browser checks passed with
  no JavaScript page errors. Details: reports/browser_checks.json.
- The design skill's strict project audit: zero findings; reports/premium-audit.json.
- DESIGN.md structural lint: zero errors. Seven orphan-token warnings remain because
  colors are consumed by the Python/CSS adapter rather than component references in
  the document. Runtime theme mapping is checked by tests/test_project.py.
- Streamlit started on the local loopback interface and served the application.
- The project folder opened in Visual Studio Code; Python, Python Debugger, Pylance
  and Ruff extensions were already installed.

## Browser coverage

Microsoft Edge (Chromium), 1440×1200 desktop and 390×1000 mobile-sized viewport.
Reduced-motion mode was enabled. Checks exercised:

- A successful ticket prediction and visible model scores.
- The example selectbox opening by keyboard and closing with Escape.
- Review creation, confirmation and CSV export.
- Invalid short-text feedback.
- CSV empty/error/success states, row-level invalid input and result export.
- Report navigation and the global scrollbar theme.
- Narrow layout without page-width overflow; lower actions remain reachable.

Screenshots are in docs/. Framework-level app tests additionally check stale results,
review corrections and duplicate queue prevention. This is not a claim of complete
WCAG conformance or testing on every browser/device.

## Not executed in this environment

Docker build/run (Docker CLI was not available), hosted deployment, GitHub Actions on
a remote repository, production load testing, and external user testing. The Docker
and CI files are provided, but their remote execution is not claimed. GitHub publishing
and posting to LinkedIn are separate from this completed local build.
