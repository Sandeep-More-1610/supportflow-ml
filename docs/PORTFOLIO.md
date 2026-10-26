# Presenting SupportFlow

Use these figures only for the recorded model. If you change the training setup,
rerun evaluation and update the claims. Read the walkthrough and reproduce the
experiment before presenting yourself as able to explain the implementation.

## Resume entry

**SupportFlow — ML Support Ticket Triage**

Python · scikit-learn · NLP · TF-IDF · Logistic Regression · Streamlit · pytest

- Built an English banking-support classifier for 77 intents, achieving **90.01%
  macro-F1 and 90.00% accuracy on 3,080 held-out BANKING77 tickets**.
- Compared word-only and word/character TF-IDF models; improved test macro-F1 by
  **2.36 percentage points** over the word-only baseline using validation-based selection.
- Added batch CSV inference, word-contribution explanations, and a human review
  workflow; the validation-selected policy achieved **93.41% accuracy at 93.54%
  coverage** on the test set.

Add your real GitHub and deployed-demo URLs after publishing. Avoid claiming
production impact, real support-team time savings, or a completed deep-learning
benchmark: this project has not measured those outcomes.

## LinkedIn post draft

I built SupportFlow, a machine-learning app that classifies banking-support messages
and suggests the team that should review them.

The app includes individual and batch predictions, top-three alternatives, word
contributions, and a queue for reviewing and correcting predictions.

For evaluation, I used BANKING77's 77 intents and separate official test set. The
selected word + character TF-IDF model with logistic regression achieved 90.01%
macro-F1 on 3,080 held-out tickets, compared with 87.66% for the word-only baseline.

An interesting part of the experiment was checking data leakage: the preprocessing
removed normalized training duplicates and 25 training examples that overlapped
the test set. The model and review threshold were selected using validation data.

The model runs locally without a paid API. Its scope is English banking queries;
scores are uncalibrated and it can still misclassify unfamiliar requests.

My next experiment is to evaluate probability calibration and out-of-domain detection.

GitHub: [add the actual repository link]
Demo: [add the actual demo link or attach a screen recording]

#MachineLearning #NLP #Python #StudentProjects

Personalize the draft to reflect what you learned, changed, and can demonstrate.
If asked about development tools, explain how you used AI assistance and what you
verified or improved yourself.

## 90-second demo script

1. **0–15 seconds:** explain the task: predicting one of 77 banking intents, with
   review when the model is uncertain.
2. **15–35 seconds:** classify the duplicate-payment example; show the top-three
   alternatives and supporting word features.
3. **35–50 seconds:** increase the threshold, reclassify, and add a ticket to review.
4. **50–65 seconds:** correct an intent in Review queue and export the record.
5. **65–80 seconds:** open Model report; explain test macro-F1 and the baseline.
6. **80–90 seconds:** state one limitation and the next experiment.

For a longer demo, upload data/sample_tickets.csv and show the batch export.

## GitHub presentation

- Repository name suggestion: `supportflow-ml`.
- Description: `Banking support intent classification with leakage-aware evaluation, batch inference and human review.`
- Topics: `machine-learning`, `nlp`, `scikit-learn`, `streamlit`, `text-classification`, `banking77`.
- Pin the repository after publishing.
- Keep the screenshot, measured results, reproduction command and limitations near
  the top of the README.
- Make future commits about real changes: new data validation, calibration results,
  comparison experiments or improvements found through error analysis.
