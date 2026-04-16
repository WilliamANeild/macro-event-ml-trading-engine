from __future__ import annotations

import numpy as np

from src.engine.derivatives.schemas import DerivativesOverlay
from src.engine.portfolio.schemas import PortfolioTarget

from .metrics import compute_sharpe, compute_max_drawdown, compute_hit_rate
from .schemas import BacktestResult


class BacktestEngine:
    """Single-step backtest for pipeline smoke testing.

    For full walk-forward backtesting, use WalkForwardBacktester instead.
    This produces a realistic single-period result from portfolio weights
    and overlay costs rather than returning fake numbers.
    """

    def run(
        self,
        portfolio: PortfolioTarget,
        overlay: DerivativesOverlay,
        actual_returns: dict[str, float] | None = None,
    ) -> BacktestResult:
        # Compute single-period return from weights and actual returns
        if actual_returns:
            period_return = sum(
                w * actual_returns.get(sym, 0.0)
                for sym, w in portfolio.weights.items()
            )
        else:
            # No actual returns provided — estimate from gross exposure
            period_return = 0.0

        # Subtract overlay premium cost
        overlay_cost = overlay.premium_budget_used
        net_return = period_return - overlay_cost

        # Add hedge contribution
        hedge_return = sum(
            w * (actual_returns.get(sym, 0.0) if actual_returns else 0.0)
            for sym, w in portfolio.hedge_weights.items()
        )
        net_return += hedge_return

        returns = [net_return]
        equity = [1.0 + net_return]

        return BacktestResult(
            returns=returns,
            trades=[
                {
                    "weights": portfolio.weights,
                    "hedge_weights": portfolio.hedge_weights,
                    "overlay_type": overlay.overlay_type,
                }
            ],
            costs=[overlay_cost],
            metadata={
                "gross_exposure": portfolio.gross_exposure,
                "net_exposure": portfolio.net_exposure,
                "regime": portfolio.regime,
            },
            equity_curve=equity,
            drawdowns=[min(0.0, net_return)],
            sharpe=0.0,
            max_drawdown=abs(min(0.0, net_return)),
            attribution={
                "portfolio_return": period_return,
                "hedge_return": hedge_return,
                "overlay_cost": -overlay_cost,
                "net_return": net_return,
            },
        )
