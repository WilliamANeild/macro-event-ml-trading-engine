from __future__ import annotations

from src.engine.meta.schemas import MetaSignal
from src.engine.portfolio.schemas import PortfolioTarget

from .schemas import DerivativesOverlay


class DerivativesOverlayManager:
    def build_overlay(
        self,
        signal: MetaSignal,
        portfolio: PortfolioTarget,
    ) -> DerivativesOverlay:
        if signal.confidence >= 0.8 and signal.score >= 0.7:
            return DerivativesOverlay(
                as_of_date=signal.as_of_date,
                overlay_type="call_overlay",
                target_symbols=list(portfolio.weights.keys()),
                notionals={symbol: 0.1 for symbol in portfolio.weights},
                premium_budget_used=0.02,
                metadata={"note": "mock convexity overlay added"},
            )

        return DerivativesOverlay(
            as_of_date=signal.as_of_date,
            overlay_type="none",
            target_symbols=[],
            notionals={},
            premium_budget_used=0.0,
            metadata={"note": "no overlay triggered"},
        )