from __future__ import annotations

from .schemas import MetaSignal
from src.engine.experts.schemas import ExpertPrediction


class MetaStacker:
    def combine(self, predictions: list[ExpertPrediction]) -> MetaSignal:
        first = predictions[0]

        avg_score = sum(p.probability_active * p.severity_score for p in predictions) / len(predictions)
        avg_confidence = sum(p.confidence_score for p in predictions) / len(predictions)

        return MetaSignal(
            as_of_date=first.as_of_date,
            theme=first.theme,
            subtheme=first.subtheme,
            score=avg_score,
            confidence=avg_confidence,
            direction=first.direction,
            source_experts=[p.expert_name for p in predictions],
            metadata={"note": "mock meta signal from average expert outputs"},
        )