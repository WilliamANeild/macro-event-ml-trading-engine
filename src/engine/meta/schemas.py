from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class MetaSignal:
    as_of_date: date
    theme: str
    subtheme: str
    score: float
    confidence: float
    direction: str
    source_experts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)