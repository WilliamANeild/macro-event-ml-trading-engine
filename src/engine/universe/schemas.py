from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Instrument:
    symbol: str
    name: str
    asset_class: str
    theme: str
    subtheme: str
    region: str = "global"
    tags: list[str] = field(default_factory=list)