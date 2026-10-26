# Dataset and attribution

SupportFlow uses **BANKING77** by PolyAI: 10,003 training queries and 3,080 test queries
across 77 fine-grained banking intents. It contains English support queries, not a
general-purpose helpdesk dataset. A query's `category` is the prediction target.

- Source: https://github.com/PolyAI-LDN/task-specific-datasets/tree/master/banking_data
- Frozen revision: `57ec275d8078af65b7731c2a98be812d844a6d6b`
- License: **Creative Commons Attribution 4.0 International (CC BY 4.0)**
- License text: https://creativecommons.org/licenses/by/4.0/
- Paper: https://arxiv.org/abs/2003.04807
- Dataset card: https://huggingface.co/datasets/PolyAI/banking77

The download script uses revision-pinned URLs, records SHA-256 file hashes, and
does not require Hugging Face, Kaggle, credentials, or a dataset execution script.
Raw downloads are excluded from Git. Aggregate results and the trained model are
included for a runnable demo. The dataset license is separate from the project's
MIT software license. Attribution applies to redistributed dataset-derived material.

## Changes to data for this experiment

Normalize Unicode, case, whitespace and punctuation **for duplicate detection only**.
Remove training texts assigned multiple labels. Deduplicate training texts. Remove
training examples whose normalized text occurs in the official test set. Split the
remaining training data 80/20 with stratification and seed 42. The official test set
is unchanged, including any duplicates within it. Features use the original text.

Using test text to remove exact overlap is explicitly a decontamination step; test
labels are not used for preprocessing, model selection or threshold selection.
This differs from a benchmark that trains on every official training example, so
do not present the result as directly comparable to every published BANKING77 score.
Semantic near-duplicates are not exhaustively removed.

The six destination teams are manually authored demo routing rules in
`supportflow/model.py`; BANKING77 does not supply these team labels.
`data/sample_tickets.csv` contains project-authored demonstration messages and is
not used as the held-out evaluation set.

## Citation

```bibtex
@inproceedings{Casanueva2020,
  author = {I\~nigo Casanueva and Tadas Temcinas and Daniela Gerz and Matthew Henderson and Ivan Vuli\'c},
  title = {Efficient Intent Detection with Dual Sentence Encoders},
  year = {2020},
  booktitle = {Proceedings of the 2nd Workshop on NLP for ConvAI},
  url = {https://arxiv.org/abs/2003.04807}
}
```
