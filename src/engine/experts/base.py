from __future__ import annotations

from abc import ABC, abstractmethod

from .schemas import ExpertContext, ExpertPrediction


'''

expert base class and the standard expert output format

Build training and evaluation utilities shared across experts

Ship the localized expert models

Conflict by region experts

Shipping chokepoint experts

Shipping port cluster experts

Sanctions and trade restriction experts

Rates regime experts

Market pricing and complacency experts

Commodity shock experts

Crypto regime experts

 outputs core fields probability active, severity, confidence, and tags'''

class BaseExpert(ABC):
    expert_name: str = "base_expert"
    model_version: str = "v0.1"

    @abstractmethod
    def predict(self, context: ExpertContext) -> ExpertPrediction:
        raise NotImplementedError