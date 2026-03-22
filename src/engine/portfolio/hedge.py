from __future__ import annotations

from src.engine.universe.schemas import Instrument


HEDGE_INSTRUMENTS = {
    "equity_beta": "SPY",
    "duration_proxy": "TLT",
    "usd_hedge": "UUP",
}


class HedgeSleeveManager:
    def compute_hedges(
        self,
        weights: dict[str, float],
        regime: str,
        confidence: float,
        universe: list[Instrument] | None = None,
    ) -> dict[str, float]:
        if not weights:
            return {}

        net_exposure = sum(weights.values())
        hedge_weights: dict[str, float] = {}

        # Equity beta hedge: offset net exposure
        if abs(net_exposure) > 0.1:
            beta_hedge = -net_exposure * 0.5
            if regime == "crisis":
                beta_hedge *= 1.5
            hedge_weights[HEDGE_INSTRUMENTS["equity_beta"]] = round(beta_hedge, 4)

        # Duration proxy hedge in crisis/transition
        if regime in ("crisis", "transition"):
            dur_weight = 0.1 if regime == "transition" else 0.2
            hedge_weights[HEDGE_INSTRUMENTS["duration_proxy"]] = round(dur_weight, 4)

        # USD hedge when confidence is low
        if confidence < 0.4:
            hedge_weights[HEDGE_INSTRUMENTS["usd_hedge"]] = 0.05

        return hedge_weights
