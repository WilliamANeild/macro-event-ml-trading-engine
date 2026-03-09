from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class FeatureRow:
    as_of_date: date
    theme: str
    subtheme: str
    values: dict[str, float] = field(default_factory=dict)