from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class DerivativesOverlay:
    as_of_date: date
    overlay_type: str
    target_symbols: list[str] = field(default_factory=list)
    notionals: dict[str, float] = field(default_factory=dict)
    premium_budget_used: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)