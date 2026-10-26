# What the model gets wrong

The recorded test run contains **308 errors out of 3,080 tickets**. Inspect
`reports/errors.csv` after training for the actual messages, labels and scores.
The file is sorted by descending model score to make confident mistakes visible.

The most frequent directional confusions in this run include:

- `verify_my_identity` → `why_verify_identity`: 5 tickets.
- `card_acceptance` → `card_not_working`: 4 tickets.
- `fiat_currency_support` → `exchange_via_app`: 4 tickets.
- `top_up_failed` → `top_up_reverted`: 4 tickets.
- `why_verify_identity` → `unable_to_verify_identity`: 4 tickets.
- `top_up_reverted` → `top_up_failed`: 4 tickets.

These counts support a practical hypothesis: the model has difficulty with some
closely related intents. A failed top-up and a reversed top-up share vocabulary but
describe different states. Identity-verification questions can ask about the process,
its purpose, or a failure to complete it. The confusion counts alone do not prove
the reason for each individual error; read the examples before deciding what to fix.

## A useful follow-up experiment

Review these groups manually and categorize mistakes as missing context, ambiguous
label, unfamiliar wording, multiple intents, or a clear model error. Build a separate
development set of fresh examples for the hypothesized weakness. Compare an embedding
baseline or richer phrase representation on that development set, then reserve a
new untouched final test for a reliable claim about improvement.

Do not simply copy misclassified test messages into the training set and report
the original test score as a fair improvement.
