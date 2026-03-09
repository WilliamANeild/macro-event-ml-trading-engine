from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class EventFeatureRow:
    as_of_date: date
    theme: str
    subtheme: str
    region: str
    values: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)