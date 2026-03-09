from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


_ALLOWED_DIRECTIONS = {"long", "short", "neutral"}


def _validate_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")


@dataclass
class ExpertContext:
    as_of_date: date
    theme: str
    subtheme: str
    feature_row: dict[str, float] = field(default_factory=dict)
    event_features: dict[str, Any] = field(default_factory=dict)
    universe: list[str] = field(default_factory=list)


@dataclass
class ExpertPrediction:
    expert_name: str
    as_of_date: date
    theme: str
    subtheme: str
    probability_active: float
    severity_score: float
    confidence_score: float
    direction: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    model_version: str = "v0.1"

    def __post_init__(self) -> None:
        _validate_unit_interval(self.probability_active, "probability_active")
        _validate_unit_interval(self.severity_score, "severity_score")
        _validate_unit_interval(self.confidence_score, "confidence_score")

        if self.direction not in _ALLOWED_DIRECTIONS:
            raise ValueError(
                f"direction must be one of {_ALLOWED_DIRECTIONS}, got {self.direction}"
            )