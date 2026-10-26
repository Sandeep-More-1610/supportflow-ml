# SupportFlow model card

## Model and intended use

A CPU-based, supervised, single-label classifier for English banking-support intent
demonstrations. Predicts one of the 77 BANKING77 labels. The saved artifact contains
word unigram/bigram TF-IDF and character-boundary 3–5-gram TF-IDF features, followed
by multinomial logistic regression with `C=12`, L2 regularization and the LBFGS solver.
Word features have weight 1.0; character features have weight 0.6. Maximum feature
counts are 25,000 and 20,000 respectively. Full settings are in supportflow/train.py.

The intended audience is a student learning applied ML and reviewers evaluating a
portfolio. It does not make financial decisions, resolve tickets, or dispatch work.
Team labels are manually assigned demo destinations, not evaluated dataset labels.

## Data and methodology

BANKING77, PolyAI, CC BY 4.0. Revision and file hashes appear in reports/metrics.json.
The original 10,003 training rows are cleaned by removing 2 conflicting rows,
30 normalized duplicates and 25 training/test overlaps. The retained data is split
into 7,956 fitting and 1,990 validation examples, stratified with random seed 42.
The official 3,080-row test set is unchanged; it has 4 repeated normalized texts.

TF-IDF is fitted on fitting data only. Three model configurations are compared by
validation macro-F1. The C=12 hybrid wins at 90.25% validation macro-F1. The saved
pipeline remains fitted to the fitting subset; there is no post-selection refit.
Test labels are used only after freezing selection and the review threshold.
No semantic-deduplication or cross-validation confidence interval is claimed.

## Recorded test results

- Accuracy: 0.900000.
- Macro-F1: 0.900141.
- Top-3 accuracy: 0.971753.
- Word-only baseline macro-F1: 0.876571.
- Majority baseline macro-F1: 0.000333.
- Median warm per-ticket inference: 7.31 ms, 100 examples on the recorded machine.

Per-intent results and the complete confusion matrix are saved in reports/.
Macro-F1 weights every intent equally. It complements overall accuracy and helps
expose weak categories. A single overall score does not describe every intent.

## Review policy

A ticket is eligible for the routing suggestion if its top score is at least 0.20
and it leads the next score by at least 0.10. Unknown feature vectors are also
flagged in the app. The threshold was selected on validation data to maximize
coverage while retaining at least 90% empirical accuracy and 100 accepted examples.

On the official test set, 2,881 tickets meet the score/margin policy: coverage 93.54%
and accepted-ticket accuracy 93.41%. The remaining 199 tickets are marked for review.
These are frozen in-domain metrics, not guarantees about new customer messages.
The sidebar slider changes live predictions but does not change the recorded report.

Model probabilities are not calibrated. A score of 0.8 must not be described as an
80% chance of correctness. The margin and threshold are simple empirical review
heuristics, not a validated out-of-domain or adversarial detector.

## Limitations and failure modes

- English banking vocabulary only; unrelated topics can still receive high scores.
- Single-intent labels do not cover multi-issue messages.
- Fine distinctions such as card arrival vs delivery estimate may be confused.
- Duplicate detection covers normalized exact matches, not all near-duplicates.
- Aggregate results may hide differences across dialects, spelling patterns or
  demographic groups; those subgroup effects have not been evaluated.
- The model has no current customer/account information or ability to verify claims.
- Word contributions describe linear associations, not causal explanations.
- Dataset-cleaning differences limit direct comparison with published benchmarks.
- Review corrections are only session exports; no automatic online learning exists.
- No production load test, hosted deployment, transformer benchmark or external user
  study has been completed as part of the recorded ML evaluation.

## Reproduction and artifacts

Use Python 3.11 and requirements.txt. Run `python -m supportflow.train`.
The script produces the selected pipeline, aggregate metrics, per-intent report,
test predictions, error analysis CSV, split audit and PNG charts. Full environment
information is recorded in reports/metrics.json and requirements-lock.txt.
Only load model artifacts from trusted sources.
