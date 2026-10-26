"""Run: python -m supportflow.train. CPU-only, deterministic evaluation."""

from __future__ import annotations

import json
import platform
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import FeatureUnion, Pipeline
from threadpoolctl import threadpool_limits

from supportflow.data import ROOT, SEED, download_data, load_splits
from supportflow.model import MIN_MARGIN, MODEL_PATH, routing_decisions, team_for


def save_artifact(artifact: dict, destination: Path):
    """Keep the last working model intact if serialization is interrupted."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, suffix=".tmp", delete=False
        ) as file:
            temporary = Path(file.name)
            joblib.dump(artifact, file, compress=3)
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_pipeline(hybrid: bool = False, c: float = 4.0) -> Pipeline:
    transformers = [
        (
            "word",
            TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=2,
                max_features=25000,
                sublinear_tf=True,
                strip_accents="unicode",
                dtype=np.float64,
            ),
        )
    ]
    if hybrid:
        transformers.append(
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=3,
                    max_features=20000,
                    sublinear_tf=True,
                    dtype=np.float64,
                ),
            )
        )
    return Pipeline(
        [
            (
                "features",
                FeatureUnion(
                    transformers,
                    transformer_weights={"word": 1, "char": 0.6} if hybrid else {"word": 1},
                ),
            ),
            (
                "classifier",
                LogisticRegression(C=c, max_iter=600, random_state=SEED, solver="lbfgs"),
            ),
        ]
    )


def metrics(y, predicted) -> dict:
    return {
        "accuracy": float(accuracy_score(y, predicted)),
        "macro_f1": float(f1_score(y, predicted, average="macro", zero_division=0)),
    }


def choose_threshold(probabilities, y, classes, target=0.90) -> tuple[float, list[dict]]:
    """Maximize validation coverage subject to empirical precision and support."""
    correct = classes[probabilities.argmax(axis=1)] == np.asarray(y)
    curve = []
    for threshold in np.arange(0.20, 0.951, 0.025):
        threshold = round(float(threshold), 3)
        accepted = routing_decisions(probabilities, threshold)
        count = int(accepted.sum())
        curve.append(
            {
                "threshold": threshold,
                "accepted": count,
                "coverage": float(accepted.mean()),
                "accuracy_when_accepted": float(correct[accepted].mean()) if count else None,
            }
        )
    eligible = [
        row for row in curve if row["accepted"] >= 100 and row["accuracy_when_accepted"] >= target
    ]
    if not eligible:
        # All tickets go to review if the validation target cannot be supported.
        return 1.0, curve
    return max(eligible, key=lambda row: (row["coverage"], row["threshold"]))["threshold"], curve


def save_plots(report, class_report, matrix, classes):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = ROOT / "reports"
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "#f5f7fb",
        }
    )
    names = [row["name"] for row in report["models"]]
    values = [row["test"]["macro_f1"] for row in report["models"]]
    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
    bars = ax.barh(names[::-1], values[::-1], color="#3159c9")
    ax.bar_label(bars, labels=[f"{v:.1%}" for v in values[::-1]], padding=5)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Macro-F1 on the official test set")
    ax.set_title("SupportFlow / model comparison", loc="left", pad=18)
    fig.savefig(directory / "model_comparison.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(20, 19), layout="constrained")
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(classes)), classes, rotation=90, fontsize=6)
    ax.set_yticks(range(len(classes)), classes, fontsize=6)
    ax.set_xlabel("Predicted intent")
    ax.set_ylabel("True intent")
    ax.set_title("SupportFlow / full held-out confusion matrix (77 intents)")
    fig.colorbar(image, ax=ax, shrink=0.7, label="Tickets")
    fig.savefig(directory / "confusion_matrix.png", dpi=150)
    plt.close(fig)


def main():
    started = time.perf_counter()
    (ROOT / "reports").mkdir(exist_ok=True)
    MODEL_PATH.parent.mkdir(exist_ok=True)
    print("Downloading / checking pinned BANKING77 files...", flush=True)
    manifest = download_data()
    fit, validation, test, audit = load_splits()
    print(json.dumps(audit, indent=2), flush=True)
    experiments, pipelines = [], {}
    dummy = DummyClassifier(strategy="most_frequent").fit(fit.text, fit.category)
    experiments.append(
        {
            "name": "Majority baseline",
            "validation": metrics(validation.category, dummy.predict(validation.text)),
            "fit_seconds": 0.0,
        }
    )
    candidates = [
        ("Word TF-IDF + logistic regression", False, 4.0),
        ("Word + character TF-IDF (C=4)", True, 4.0),
        ("Word + character TF-IDF (C=12)", True, 12.0),
    ]
    with threadpool_limits(limits=2):
        for name, hybrid, c in candidates:
            print(f"Training {name}...", flush=True)
            tick = time.perf_counter()
            pipeline = build_pipeline(hybrid, c)
            pipeline.fit(fit.text, fit.category)
            scores = metrics(validation.category, pipeline.predict(validation.text))
            experiments.append(
                {"name": name, "validation": scores, "fit_seconds": time.perf_counter() - tick}
            )
            pipelines[name] = pipeline
            print(f"  Validation macro-F1: {scores['macro_f1']:.4f}", flush=True)
    selected = max(experiments[1:], key=lambda row: row["validation"]["macro_f1"])
    pipeline = pipelines[selected["name"]]
    threshold, curve = choose_threshold(
        pipeline.predict_proba(validation.text), validation.category.to_numpy(), pipeline.classes_
    )
    # Selection and threshold are now frozen. Only now evaluate the official test labels.
    for experiment in experiments:
        estimator = pipelines.get(experiment["name"], dummy)
        experiment["test"] = metrics(test.category, estimator.predict(test.text))
    probabilities = pipeline.predict_proba(test.text)
    predictions = pipeline.classes_[probabilities.argmax(axis=1)]
    accepted = routing_decisions(probabilities, threshold)
    correct = predictions == test.category.to_numpy()
    class_report = classification_report(
        test.category, predictions, output_dict=True, zero_division=0
    )
    matrix = confusion_matrix(test.category, predictions, labels=pipeline.classes_)
    top3 = np.argsort(probabilities, axis=1)[:, -3:]
    top3_accuracy = np.mean(
        [
            label in pipeline.classes_[indices]
            for label, indices in zip(test.category, top3, strict=True)
        ]
    )
    # Warm, single-ticket latency: 100 examples, not a production SLA.
    pipeline.predict_proba([test.text.iloc[0]])
    latencies = []
    for text in test.text.iloc[:100]:
        tick = time.perf_counter()
        pipeline.predict_proba([text])
        latencies.append((time.perf_counter() - tick) * 1000)
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": manifest,
        "data_audit": audit,
        "models": experiments,
        "selected_model": selected["name"],
        "selection_metric": "validation macro-F1",
        "test_metrics": metrics(test.category, predictions),
        "top3_accuracy": float(top3_accuracy),
        "routing": {
            "threshold": threshold,
            "minimum_margin": MIN_MARGIN,
            "validation_accuracy_target": 0.90,
            "validation_minimum_accepted": 100,
            "test_coverage": float(accepted.mean()),
            "test_accepted": int(accepted.sum()),
            "test_accuracy_when_accepted": float(correct[accepted].mean())
            if accepted.any()
            else None,
            "validation_curve": curve,
        },
        "latency_ms": {
            "median": float(np.median(latencies)),
            "p95": float(np.percentile(latencies, 95)),
            "samples": len(latencies),
            "scope": "Warm pipeline, single ticket, this machine",
        },
        "environment": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "training_seconds": time.perf_counter() - started,
        "limitations": [
            "English banking queries only; not a general support classifier.",
            "Scores are uncalibrated model probabilities, not correctness guarantees.",
            "Threshold uses in-domain validation only; no validated out-of-domain detector.",
            "Team routing is a hand-written demo mapping, not a learned or evaluated business policy.",
            "Exact normalized duplicates checked; semantic paraphrase overlap may remain.",
            "No transformer trained or benchmarked in this version.",
        ],
    }
    save_artifact({"pipeline": pipeline, "threshold": threshold, "metadata": report}, MODEL_PATH)
    directory = ROOT / "reports"
    (directory / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (directory / "classification_report.json").write_text(
        json.dumps(class_report, indent=2), encoding="utf-8"
    )
    pd.DataFrame(matrix, index=pipeline.classes_, columns=pipeline.classes_).to_csv(
        directory / "confusion_matrix.csv"
    )
    results = pd.DataFrame(
        {
            "text": test.text,
            "actual": test.category,
            "predicted": predictions,
            "score": probabilities.max(axis=1),
            "needs_review": ~accepted,
            "suggested_team": [team_for(label) for label in predictions],
        }
    )
    results.to_csv(directory / "test_predictions.csv", index=False)
    results[~correct].sort_values("score", ascending=False).to_csv(
        directory / "errors.csv", index=False
    )
    split_records = pd.concat(
        [
            frame.assign(split=name)[["fingerprint", "split"]]
            for name, frame in [("fit", fit), ("validation", validation), ("test", test)]
        ]
    )
    split_records.to_csv(directory / "split_audit.csv", index=False)
    save_plots(report, class_report, matrix, pipeline.classes_)
    print(
        json.dumps(
            {
                "selected_model": report["selected_model"],
                "test": report["test_metrics"],
                "threshold": threshold,
                "coverage": report["routing"]["test_coverage"],
                "accuracy_when_accepted": report["routing"]["test_accuracy_when_accepted"],
                "training_seconds": report["training_seconds"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
