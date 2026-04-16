from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge

from src.engine.experts.schemas import ExpertPrediction


DIRECTION_MAP = {"long": 1.0, "short": -1.0, "neutral": 0.0}

# Neutral defaults when an expert is missing: prob=0.5, severity=0.0, confidence=0.5, direction=0.0
_NEUTRAL_SLOT = [0.5, 0.0, 0.5, 0.0]
_FEATURES_PER_EXPERT = 4


class MetaCombiner:
    def __init__(self, method: str = "logistic", expert_names: list[str] | None = None) -> None:
        self.method = method
        self.model: LogisticRegression | Ridge | None = None
        self._fitted = False
        self._expert_names: list[str] = expert_names or []

    def _register_experts(self, prediction_lists: list[list[ExpertPrediction]]) -> None:
        """Learn expert names from training data if not provided upfront."""
        if self._expert_names:
            return
        seen: dict[str, None] = {}
        for preds in prediction_lists:
            for p in preds:
                if p.expert_name not in seen:
                    seen[p.expert_name] = None
        self._expert_names = list(seen.keys())

    def _encode_predictions(self, predictions: list[ExpertPrediction]) -> np.ndarray:
        lookup: dict[str, ExpertPrediction] = {p.expert_name: p for p in predictions}
        features = []
        for name in self._expert_names:
            p = lookup.get(name)
            if p is not None:
                features.extend([
                    p.probability_active,
                    p.severity_score,
                    p.confidence_score,
                    DIRECTION_MAP.get(p.direction, 0.0),
                ])
            else:
                features.extend(_NEUTRAL_SLOT)
        return np.array(features)

    def _encode_batch(self, prediction_lists: list[list[ExpertPrediction]]) -> np.ndarray:
        return np.array([self._encode_predictions(preds) for preds in prediction_lists])

    def fit(self, prediction_lists: list[list[ExpertPrediction]], labels: np.ndarray) -> None:
        self._register_experts(prediction_lists)
        X = self._encode_batch(prediction_lists)
        if self.method == "logistic":
            self.model = LogisticRegression(solver="saga", C=1.0, l1_ratio=1.0, max_iter=1000)
            self.model.fit(X, labels.astype(int))
        else:
            self.model = Ridge(alpha=1.0)
            self.model.fit(X, labels)
        self._fitted = True

    def predict(
        self, predictions: list[ExpertPrediction]
    ) -> tuple[dict[str, float], float, float, str]:
        if not self._fitted or self.model is None:
            return self._fallback(predictions)

        X = self._encode_predictions(predictions).reshape(1, -1)
        if self.method == "logistic":
            proba = self.model.predict_proba(X)[0]
            score = float(proba[1]) if len(proba) > 1 else float(proba[0])
        else:
            score = float(np.clip(self.model.predict(X)[0], 0, 1))

        # Derive theme scores from expert predictions
        theme_scores: dict[str, float] = {}
        for p in predictions:
            key = p.theme
            expert_score = p.probability_active * p.severity_score
            theme_scores[key] = max(theme_scores.get(key, 0.0), expert_score)

        confidence = float(np.mean([p.confidence_score for p in predictions]))
        direction = "long" if score > 0.55 else ("short" if score < 0.45 else "neutral")
        return theme_scores, score, confidence, direction

    def _fallback(
        self, predictions: list[ExpertPrediction]
    ) -> tuple[dict[str, float], float, float, str]:
        score = float(np.mean([p.probability_active * p.severity_score for p in predictions]))
        confidence = float(np.mean([p.confidence_score for p in predictions]))
        theme_scores = {}
        for p in predictions:
            theme_scores[p.theme] = p.probability_active * p.severity_score
        direction = "long" if score > 0.55 else ("short" if score < 0.45 else "neutral")
        return theme_scores, score, confidence, direction
