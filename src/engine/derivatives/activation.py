from __future__ import annotations

from src.engine.meta.schemas import MetaSignal
from src.engine.portfolio.schemas import PortfolioTarget


class OverlayActivationRule:
    def __init__(
        self,
        min_confidence: float = 0.75,
        min_score: float = 0.65,
        max_net_exposure: float = 0.8,
        active_regimes: tuple[str, ...] = ("crisis", "transition"),
    ) -> None:
        self.min_confidence = min_confidence
        self.min_score = min_score
        self.max_net_exposure = max_net_exposure
        self.active_regimes = active_regimes

    def should_activate(
        self, signal: MetaSignal, portfolio: PortfolioTarget
    ) -> tuple[bool, str]:
        # Rule 1: high confidence + high score + active regime
        if (
            signal.confidence >= self.min_confidence
            and signal.score >= self.min_score
            and signal.regime in self.active_regimes
        ):
            return True, "high_conviction_regime"

        # Rule 2: excessive net exposure
        if abs(portfolio.net_exposure) > self.max_net_exposure:
            return True, "exposure_limit"

        return False, "none"
