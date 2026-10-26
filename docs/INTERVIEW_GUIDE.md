# Understand and explain SupportFlow

## Start here

Run the app, classify several messages, and deliberately try ambiguous and unrelated
requests. Read `supportflow/model.py`, then `data.py`, then `train.py`. The app is the
presentation layer; the model and experiment are the core of the project.

## What problem does this solve?

A support inbox contains free-text messages. This project turns each English banking
message into a likely intent and a suggested team. Human review handles uncertain
cases. Actual support dispatch, customer authentication and issue resolution are
outside the project.

## What is TF-IDF?

Each message becomes a sparse vector. A term gets more weight when it is useful in
the current message but less common across the training corpus. The implementation
uses sublinear term frequency and normalized vectors. It learns vocabulary and
document frequencies from fitting data only.

Word unigrams/bigrams capture phrases such as `charged twice`. Character n-grams
capture fragments within word boundaries and help represent related spellings.
They can also create misleading similarities; the effect must be measured, not
assumed. Here the hybrid configuration improved validation and final test macro-F1.

## Why logistic regression?

It is a strong, relatively inexpensive baseline for sparse text features. Despite
the name it is a classifier. It computes a linear score for each intent and converts
scores to a distribution across 77 labels. Regularization discourages excessive
weights. `C` is inverse regularization strength: a larger value regularizes less.

The experiment tested C=4 and C=12 for the hybrid. C=12 had the highest validation
macro-F1. It was selected before looking at final test labels. This small search
does not prove it is the globally best model.

## Why separate fitting, validation and test data?

- Fitting data learns vocabulary and model parameters.
- Validation data chooses the configuration and review threshold.
- Test data estimates final performance after those choices are fixed.

Repeatedly changing the model in response to test scores makes the test set part of
development and weakens its value. For future experiments, keep an untouched final
holdout or use a properly designed evaluation protocol.

SupportFlow also normalizes texts for duplicate checks. It removes conflicting
training labels, repeated training messages and training/test overlaps. This reduces
obvious leakage, but cannot prove the absence of semantic near-duplicates.

## What does 90.01% macro-F1 mean?

Precision measures how often predictions of an intent are correct. Recall measures
how many true examples of that intent are found. F1 is their harmonic mean.
Macro-F1 averages F1 equally across all 77 intents. Accuracy counts correct predictions
over all examples. The official test has 40 examples per intent, so accuracy and
macro-F1 happen to be similar here; they are different metrics.

The full model correctly classified 2,772 of 3,080 test tickets. There were 308
misclassifications. Open reports/errors.csv after training and look for recurring
confusions. A high-scoring error is especially important for review-policy design.

## How does the review policy work?

The top score must reach the chosen threshold and exceed the runner-up by at least
0.10. The threshold sweep uses validation predictions, choosing maximum coverage
subject to at least 90% accepted-ticket accuracy and 100 accepted examples. The
selected threshold was 0.20. If no threshold qualifies, the fallback sends all cases
for review.

On test data, 2,881 tickets passed the policy; accepted-ticket accuracy was 93.41%.
Coverage was 93.54%. The app can trade coverage for caution with the threshold slider.
This does not guarantee a target precision on live data. The scores are uncalibrated,
and unrelated messages can still receive high values.

## Are feature contributions explanations?

They are a limited, inspectable explanation of the linear model. For a selected
class, multiply each non-zero input feature by its learned coefficient. Positive
contributions raise that class's logit. The UI shows the strongest word features.
It omits character fragments for readability and does not claim a causal explanation
or a complete account of why one class outranked another.

## Is team routing also machine learning?

No. BANKING77 provides intent labels. The project groups those intents into six demo
teams with explicit rules. The 90% metric evaluates intent prediction, not operational
routing accuracy. A real helpdesk would need approved ownership rules or labelled
team-routing data and a separate evaluation.

## Why not use an LLM or a transformer immediately?

The chosen baseline trains and runs cheaply on a CPU, needs no external API, and is
easy to reproduce. A transformer may improve performance but needs a fair comparison
of quality, latency, compute and maintenance cost. This version has not run that
comparison, so do not claim that it beats a transformer or an LLM.

## What engineering did you add?

Shared inference code for the CLI and app, input bounds, bounded UTF-8 CSV parsing,
row-level error recovery, spreadsheet-safe exports, stale-result handling, session
review records, reproducible experiment artifacts, tests, a local browser smoke
script and a GitHub Actions configuration. The input data is not silently appended
to the training set. Only trusted local model artifacts are loaded.

## What would you improve next?

Pick one measurable extension and document the experiment:

1. Build an independently labelled set of out-of-domain messages and report false
   acceptance, not just in-domain accuracy.
2. Compare probability calibration using a separate calibration split. Plot
   reliability and evaluate the review policy on untouched examples.
3. Compare a sentence-embedding classifier using the same split and metrics.
4. Test typos, short inputs, mixed intents and dialect variation systematically.
5. Collect feedback with consent, remove duplicates, and evaluate a new model version
   before replacing the current one.

## Questions you should answer without reading code

- Why does fitting TF-IDF on all data cause leakage?
- Why can a high model score still be wrong?
- How does class imbalance affect accuracy and macro-F1?
- What is the trade-off between coverage and accepted-ticket accuracy?
- Why keep the selected model unchanged after choosing its threshold?
- What happens if an uploaded CSV contains one invalid ticket?
- What does the review queue change, and what does it leave for a future experiment?
- What evidence supports each number on your resume?

Before an interview, reproduce training once, inspect at least ten errors, explain
one test, and make one improvement that you can discuss in your own words.
