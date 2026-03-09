from __future__ import annotations

from abc import ABC, abstractmethod

from .schemas import ExpertContext, ExpertPrediction


class BaseExpert(ABC):
    expert_name: str = "base_expert"
    model_version: str = "v0.1"

    @abstractmethod
    def predict(self, context: ExpertContext) -> ExpertPrediction:
        raise NotImplementedError