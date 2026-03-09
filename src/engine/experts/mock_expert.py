from __future__ import annotations

from .base import BaseExpert
from .schemas import ExpertContext, ExpertPrediction


class MockExpert(BaseExpert):
    expert_name = "mock_expert"
    model_version = "v0.1"

    def predict(self, context: ExpertContext) -> ExpertPrediction:
        return ExpertPrediction(
            expert_name=self.expert_name,
            as_of_date=context.as_of_date,
            theme=context.theme,
            subtheme=context.subtheme,
            probability_active=0.50,
            severity_score=0.50,
            confidence_score=0.50,
            direction="neutral",
            tags=["mock", "test"],
            metadata={"note": "placeholder expert for pipeline testing"},
            model_version=self.model_version,
        )