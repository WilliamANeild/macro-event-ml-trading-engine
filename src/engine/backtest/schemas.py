from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BacktestResult:
    returns: list[float] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    costs: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)