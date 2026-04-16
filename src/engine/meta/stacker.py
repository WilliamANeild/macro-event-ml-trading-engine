from __future__ import annotations

import numpy as np
import pandas as pd

from .combiner import MetaCombiner
from .regime_detector import RegimeDetector
from .schemas import MetaSignal
from .walk_forward import WalkForwardSplitter
from src.engine.experts.schemas import ExpertPrediction


class MetaStacker:
    def __init__(
        self,
        combiner: MetaCombiner | None = None,
        regime_detector: RegimeDetector | None = None,
    ) -> None:
        self.combiner = combiner
        self.regime_detector = regime_detector
        self._recent_returns: pd.DataFrame | None = None
        self._validation_scores: list[float] = []

    def fit(
        self,
        historical_predictions: list[list[ExpertPrediction]],
        labels: np.ndarray,
        price_history: pd.DataFrame | None = None,
    ) -> None:
        if self.combiner is not None:
            splitter = WalkForwardSplitter()
            splits = splitter.split(len(labels))
            if splits:
                # Validate across all splits to check combiner stability
                self._validation_scores = []
                for train_idx, test_idx in splits:
                    train_preds = [historical_predictions[i] for i in train_idx]
                    train_labels = labels[train_idx]
                    self.combiner.fit(train_preds, train_labels)

                    # Score on test set
                    correct = 0
                    for i in test_idx:
                        _, score, _, direction = self.combiner.predict(historical_predictions[i])
                        actual = labels[i]
                        predicted = 1 if score > 0.5 else 0
                        if predicted == int(actual):
                            correct += 1
                    accuracy = correct / len(test_idx) if len(test_idx) > 0 else 0.0
                    self._validation_scores.append(accuracy)

                # Final fit on the last split's full training window
                train_idx, _ = splits[-1]
                train_preds = [historical_predictions[i] for i in train_idx]
                train_labels = labels[train_idx]
                self.combiner.fit(train_preds, train_labels)

        if self.regime_detector is not None and price_history is not None:
            self.regime_detector.fit(price_history)
            self._recent_returns = price_history

    def set_recent_returns(self, returns: pd.DataFrame) -> None:
        self._recent_returns = returns

    def combine(self, predictions: list[ExpertPrediction]) -> MetaSignal:
        first = predictions[0]

        if self.combiner is not None:
            theme_scores, score, confidence, direction = self.combiner.predict(predictions)
        else:
            score = sum(p.probability_active * p.severity_score for p in predictions) / len(
                predictions
            )
            confidence = sum(p.confidence_score for p in predictions) / len(predictions)
            direction = first.direction
            theme_scores = {}

        regime = "normal"
        if self.regime_detector is not None and self._recent_returns is not None:
            regime = self.regime_detector.detect(self._recent_returns)

        metadata: dict = {"note": "meta signal from stacker"}
        if self._validation_scores:
            metadata["wf_accuracy_mean"] = float(np.mean(self._validation_scores))
            metadata["wf_accuracy_std"] = float(np.std(self._validation_scores))
            metadata["wf_n_splits"] = len(self._validation_scores)

        return MetaSignal(
            as_of_date=first.as_of_date,
            theme=first.theme,
            subtheme=first.subtheme,
            score=score,
            confidence=confidence,
            direction=direction,
            source_experts=[p.expert_name for p in predictions],
            metadata=metadata,
            theme_scores=theme_scores,
            regime=regime,
        )
