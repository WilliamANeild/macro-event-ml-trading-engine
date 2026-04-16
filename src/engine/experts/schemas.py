from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


_ALLOWED_DIRECTIONS = {"long", "short", "neutral"}


def _validate_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")


class ExpertFamily(str, Enum):
    """Expert family classifications for localized signal routing."""
    CONFLICT_ESCALATION = "conflict_escalation"
    SHIPPING_CHOKEPOINT = "shipping_chokepoint"
    RATES_POLICY = "rates_policy"
    MARKET_PRICING = "market_pricing"
    CRYPTO_REGIME = "crypto_regime"


class LocalizationType(str, Enum):
    """Localization scope for expert signals."""
    REGION = "region"
    CHOKEPOINT = "chokepoint"
    PORT_CLUSTER = "port_cluster"
    COMMODITY = "commodity"
    COUNTRY = "country"


@dataclass
class ExpertContext:
    as_of_date: date
    theme: str
    subtheme: str
    feature_row: dict[str, float] = field(default_factory=dict)
    event_features: dict[str, Any] = field(default_factory=dict)
    universe: list[str] = field(default_factory=list)


@dataclass
class LocalizationMetadata:
    """Metadata capturing localization of expert signals."""
    location_type: LocalizationType
    location_value: str
    region: str | None = None
    subregion: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocalizationMetadata:
        return cls(
            location_type=LocalizationType(data.get("location_type", "region")),
            location_value=data.get("location_value", "global"),
            region=data.get("region"),
            subregion=data.get("subregion"),
        )


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
    localization: LocalizationMetadata | None = None
    model_version: str = "v0.1"

    def __post_init__(self) -> None:
        _validate_unit_interval(self.probability_active, "probability_active")
        _validate_unit_interval(self.severity_score, "severity_score")
        _validate_unit_interval(self.confidence_score, "confidence_score")

        if self.direction not in _ALLOWED_DIRECTIONS:
            raise ValueError(
                f"direction must be one of {_ALLOWED_DIRECTIONS}, got {self.direction}"
            )