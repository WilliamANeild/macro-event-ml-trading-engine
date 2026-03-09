from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class ExpressionDecision:
    as_of_date: date
    theme: str
    subtheme: str
    expression_type: str
    target_symbols: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)