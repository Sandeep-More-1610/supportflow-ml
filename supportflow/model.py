"""One inference contract shared by the app, CLI and tests."""

from __future__ import annotations

import re
from pathlib import Path

import joblib
import numpy as np

from supportflow.data import ROOT

MODEL_PATH = ROOT / "models" / "supportflow.joblib"
MAX_TEXT_LENGTH = 4000
MIN_MARGIN = 0.10

TEAM_INTENTS = {
    "Account & identity": {
        "age_limit",
        "country_support",
        "edit_personal_details",
        "terminate_account",
        "unable_to_verify_identity",
        "verify_my_identity",
        "verify_source_of_funds",
        "why_verify_identity",
        "passcode_forgotten",
        "lost_or_stolen_phone",
    },
    "Cash & ATMs": {
        "atm_support",
        "card_swallowed",
        "cash_withdrawal_charge",
        "cash_withdrawal_not_recognised",
        "declined_cash_withdrawal",
        "pending_cash_withdrawal",
        "wrong_amount_of_cash_received",
        "wrong_exchange_rate_for_cash_withdrawal",
    },
    "Transfers & exchange": {
        "balance_not_updated_after_bank_transfer",
        "beneficiary_not_allowed",
        "cancel_transfer",
        "declined_transfer",
        "exchange_charge",
        "exchange_rate",
        "exchange_via_app",
        "failed_transfer",
        "fiat_currency_support",
        "pending_transfer",
        "receiving_money",
        "transfer_fee_charged",
        "transfer_into_account",
        "transfer_not_received_by_recipient",
        "transfer_timing",
        "top_up_by_bank_transfer_charge",
    },
    "Top-ups": {
        "automatic_top_up",
        "balance_not_updated_after_cheque_or_cash_deposit",
        "pending_top_up",
        "supported_cards_and_currencies",
        "top_up_by_card_charge",
        "top_up_by_cash_or_cheque",
        "top_up_failed",
        "top_up_limits",
        "top_up_reverted",
        "topping_up_by_card",
        "verify_top_up",
    },
    "Payments & refunds": {
        "card_payment_fee_charged",
        "card_payment_not_recognised",
        "card_payment_wrong_exchange_rate",
        "declined_card_payment",
        "direct_debit_payment_not_recognised",
        "extra_charge_on_statement",
        "pending_card_payment",
        "Refund_not_showing_up",
        "request_refund",
        "reverted_card_payment?",
        "transaction_charged_twice",
    },
}


def team_for(intent: str) -> str:
    """Demo routing rules; team labels are not annotations from BANKING77."""
    for team, intents in TEAM_INTENTS.items():
        if intent in intents:
            return team
    return "Cards & access"


def display_intent(intent: str) -> str:
    return intent.replace("_", " ").replace("?", "").capitalize()


def validate_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter a ticket with at least three words.")
    text = text.strip()
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Keep each ticket under {MAX_TEXT_LENGTH:,} characters.")
    if len(re.findall(r"\b\w+\b", text)) < 3:
        raise ValueError("Enter at least three words so the model has enough context.")
    return text


def routing_decisions(probabilities: np.ndarray, threshold: float, margin: float = MIN_MARGIN):
    ranked = np.sort(probabilities, axis=1)
    return (ranked[:, -1] >= threshold) & (ranked[:, -1] - ranked[:, -2] >= margin)


class TicketClassifier:
    def __init__(self, artifact: dict):
        self.pipeline = artifact["pipeline"]
        self.threshold = float(artifact["threshold"])
        self.metadata = artifact["metadata"]
        self.classes = self.pipeline.classes_

    @classmethod
    def load(cls, path: Path = MODEL_PATH):
        # Only load the artifact produced by this project's training command.
        # joblib/pickle files are executable; never accept user-uploaded models.
        return cls(joblib.load(path))

    def predict(self, text: str, threshold: float | None = None) -> dict:
        return self.predict_many([text], threshold)[0]

    def predict_many(self, texts: list[str], threshold: float | None = None) -> list[dict]:
        if not texts:
            return []
        cleaned = [validate_text(text) for text in texts]
        threshold = self.threshold if threshold is None else float(threshold)
        if not np.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("The review threshold must be between 0 and 1.")
        features = self.pipeline.named_steps["features"].transform(cleaned)
        probabilities = self.pipeline.named_steps["classifier"].predict_proba(features)
        decisions = routing_decisions(probabilities, threshold)
        results = []
        for row, (text, scores) in enumerate(zip(cleaned, probabilities, strict=True)):
            indices = np.argsort(scores)[::-1][:3]
            best, runner_up = indices[:2]
            intent = str(self.classes[best])
            reasons = []
            if features[row].nnz == 0:
                reasons.append("No recognizable vocabulary")
            if scores[best] < threshold:
                reasons.append("Top score is below the review threshold")
            if scores[best] - scores[runner_up] < MIN_MARGIN:
                reasons.append("Two intents have similar scores")
            results.append(
                {
                    "text": text,
                    "intent": intent,
                    "team": team_for(intent),
                    "score": float(scores[best]),
                    "margin": float(scores[best] - scores[runner_up]),
                    "threshold": threshold,
                    "needs_review": bool(not decisions[row] or features[row].nnz == 0),
                    "review_reasons": reasons,
                    "alternatives": [
                        {"intent": str(self.classes[i]), "score": float(scores[i])} for i in indices
                    ],
                }
            )
        return results

    def explain(self, text: str, intent: str, limit: int = 6) -> list[dict]:
        """Positive feature contributions to the selected class's linear logit."""
        features = self.pipeline.named_steps["features"].transform([validate_text(text)])
        names = self.pipeline.named_steps["features"].get_feature_names_out()
        index = list(self.classes).index(intent)
        weights = self.pipeline.named_steps["classifier"].coef_[index]
        contributions = features.multiply(weights).tocsr()
        order = np.argsort(contributions.data)[::-1]
        evidence = []
        for position in order:
            value = float(contributions.data[position])
            if value <= 0:
                continue
            name = names[contributions.indices[position]]
            if name.startswith("char__"):
                continue
            evidence.append({"feature": name.removeprefix("word__"), "contribution": value})
            if len(evidence) >= limit:
                break
        return evidence
