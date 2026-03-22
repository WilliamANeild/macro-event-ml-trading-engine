from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class PortfolioTarget:
    as_of_date: date
    weights: dict[str, float] = field(default_factory=dict)
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    turnover: float = 0.0
    risk_target: float = 0.10
    regime: str = "normal"
    hedge_weights: dict[str, float] = field(default_factory=dict)