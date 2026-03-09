from __future__ import annotations

from src.engine.derivatives.schemas import DerivativesOverlay
from src.engine.portfolio.schemas import PortfolioTarget

from .schemas import BacktestResult


class BacktestEngine:
    def run(
        self,
        portfolio: PortfolioTarget,
        overlay: DerivativesOverlay,
    ) -> BacktestResult:
        gross_exposure = portfolio.gross_exposure
        overlay_cost = overlay.premium_budget_used

        mock_return = 0.01 * gross_exposure - overlay_cost

        return BacktestResult(
            returns=[mock_return],
            trades=[
                {
                    "weights": portfolio.weights,
                    "overlay_type": overlay.overlay_type,
                }
            ],
            costs=[overlay_cost],
            metadata={"note": "mock one-step backtest result"},
        )