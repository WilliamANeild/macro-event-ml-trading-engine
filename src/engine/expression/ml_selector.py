from __future__ import annotations

import numpy as np
import pandas as pd

from src.engine.meta.schemas import MetaSignal
from src.engine.universe.schemas import Instrument

from .exposure_mapper import ExposureMapper
from .schemas import ExpressionDecision


REGIME_HEDGE_MULTIPLIER = {
    "normal": 0.0,
    "transition": 0.5,
    "crisis": 1.0,
    "euphoria": 0.2,
}

SLEEVE_THEMES = ["defense", "shipping", "commodities", "rates_us", "crypto"]
FALLBACK_ETFS = ["ITA", "XLE", "TLT", "GLD", "SPY"]


class MLExpressionSelector:
    def __init__(self, universe: list[Instrument] | None = None) -> None:
        self.universe = universe or []
        self.mapper = ExposureMapper()
        self._recent_returns: "pd.DataFrame | None" = None

    def set_recent_returns(self, returns: "pd.DataFrame") -> None:
        """Set recent returns for cross-asset momentum rotation."""
        self._recent_returns = returns

    def select(self, signal: MetaSignal) -> ExpressionDecision:
        themes = [signal.theme]
        if signal.theme_scores:
            themes = list(signal.theme_scores.keys()) or themes

        # Always include sleeve themes so fallback works
        all_themes = list(dict.fromkeys(themes + SLEEVE_THEMES))

        # Build exposure matrix
        if self.universe:
            exposure = self.mapper.build_exposure_matrix(self.universe, all_themes)
        else:
            exposure = {}

        regime = signal.regime
        confidence = signal.confidence

        # For catch-all "macro" theme, diversify across all sleeves
        # rather than trying to TF-IDF match the word "macro"
        is_macro_catchall = signal.theme in ("macro", "all", "")

        if is_macro_catchall:
            # Multi-sleeve diversified portfolio
            weights = self._multi_sleeve_weights(exposure, regime)
            expr_type = "blend"
        elif confidence >= 0.7 and regime == "normal":
            expr_type = "single_name"
            weights = self._top_exposed(exposure, signal.theme, top_n=2)
        elif confidence >= 0.4 and regime not in ("crisis",):
            expr_type = "etf"
            weights = self._theme_weights(exposure, signal.theme)
        else:
            expr_type = "blend"
            weights = self._blend_weights(exposure, signal.theme)

        # Fallback if primary theme produced no weights
        if not weights:
            for fallback_theme in SLEEVE_THEMES:
                weights = self._theme_weights(exposure, fallback_theme, top_n=5)
                if weights:
                    expr_type = "blend"
                    break

        # Last resort: equal-weight known ETFs
        if not weights:
            available = [s for s in FALLBACK_ETFS
                         if any(inst.symbol == s for inst in self.universe)]
            if available:
                eq = 1.0 / len(available)
                weights = {s: eq for s in available}
            else:
                weights = {"SPY": 1.0}

        # Apply direction scaling — reduce short conviction in euphoria
        # where shorting consistently loses money
        if signal.direction == "short":
            short_scale = 0.25 if regime == "euphoria" else 1.0
            weights = {k: -abs(v) * short_scale for k, v in weights.items()}
        elif signal.direction == "neutral":
            weights = {k: v * 0.25 for k, v in weights.items()}

        # Hedge fraction
        regime_mult = REGIME_HEDGE_MULTIPLIER.get(regime, 0.0)
        hedge_fraction = max(0.0, (1.0 - confidence)) * regime_mult

        symbols = list(weights.keys())

        return ExpressionDecision(
            as_of_date=signal.as_of_date,
            theme=signal.theme,
            subtheme=signal.subtheme,
            expression_type=expr_type,
            target_symbols=symbols,
            weights=weights,
            confidence=confidence,
            hedge_fraction=hedge_fraction,
            regime=regime,
        )

    def _top_exposed(
        self, exposure: dict[str, dict[str, float]], theme: str, top_n: int = 2
    ) -> dict[str, float]:
        if theme not in exposure:
            return {}
        theme_exp = exposure[theme]
        sorted_syms = sorted(theme_exp.items(), key=lambda x: x[1], reverse=True)[:top_n]
        total = sum(w for _, w in sorted_syms) or 1.0
        return {sym: w / total for sym, w in sorted_syms}

    def _theme_weights(
        self, exposure: dict[str, dict[str, float]], theme: str, top_n: int = 10
    ) -> dict[str, float]:
        if theme not in exposure:
            return {}
        theme_exp = exposure[theme]
        sorted_syms = sorted(theme_exp.items(), key=lambda x: x[1], reverse=True)
        if sorted_syms:
            max_score = sorted_syms[0][1]
            threshold = max_score * 0.01
            sorted_syms = [(s, w) for s, w in sorted_syms if w > threshold]
        sorted_syms = sorted_syms[:top_n]
        if not sorted_syms:
            return {}
        total = sum(w for _, w in sorted_syms) or 1.0
        return {sym: w / total for sym, w in sorted_syms}

    def _multi_sleeve_weights(
        self, exposure: dict[str, dict[str, float]], regime: str
    ) -> dict[str, float]:
        """Diversify across all sleeve themes — used when no specific theme."""
        # Regime-based sleeve allocation — shipping underweighted due to
        # poor historical signal-to-noise; commodities (gold) overweighted
        # as consistent risk-adjusted contributor
        if regime == "crisis":
            sleeve_alloc = {"commodities": 0.55, "defense": 0.25, "rates_us": 0.10, "shipping": 0.00, "crypto": 0.10}
        elif regime == "euphoria":
            sleeve_alloc = {"commodities": 0.30, "defense": 0.20, "crypto": 0.20, "shipping": 0.05, "rates_us": 0.25}
        elif regime == "transition":
            sleeve_alloc = {"commodities": 0.35, "defense": 0.25, "rates_us": 0.20, "shipping": 0.05, "crypto": 0.15}
        else:
            sleeve_alloc = {"commodities": 0.30, "defense": 0.20, "rates_us": 0.20, "shipping": 0.05, "crypto": 0.25}

        combined: dict[str, float] = {}
        for sleeve, alloc in sleeve_alloc.items():
            sleeve_wts = self._theme_weights(exposure, sleeve, top_n=3)
            for sym, w in sleeve_wts.items():
                combined[sym] = combined.get(sym, 0.0) + w * alloc

        # Normalize
        total = sum(combined.values()) or 1.0
        return {k: v / total for k, v in combined.items()}

    def _apply_momentum_tilt(
        self,
        base_alloc: dict[str, float],
        exposure: dict[str, dict[str, float]],
    ) -> dict[str, float]:
        """Tilt sleeve allocations toward sleeves with positive momentum."""
        if self._recent_returns is None or len(self._recent_returns) < 60:
            return base_alloc

        recent = self._recent_returns.iloc[-60:]

        # Compute average momentum per sleeve using top instruments
        sleeve_mom: dict[str, float] = {}
        for sleeve in base_alloc:
            if sleeve not in exposure:
                sleeve_mom[sleeve] = 0.0
                continue
            # Get top instruments for this sleeve
            top_syms = sorted(exposure[sleeve].items(), key=lambda x: x[1], reverse=True)[:3]
            moms = []
            for sym, _ in top_syms:
                if sym in recent.columns:
                    moms.append(float(recent[sym].sum()))
            sleeve_mom[sleeve] = np.mean(moms) if moms else 0.0

        # Tilt: boost sleeves with positive momentum, reduce negative ones
        # Max tilt: ±50% of base allocation
        tilted = {}
        for sleeve, base in base_alloc.items():
            mom = sleeve_mom.get(sleeve, 0.0)
            # Scale momentum to a multiplier: positive mom → up to 1.5x, negative → down to 0.5x
            tilt = 1.0 + np.clip(mom * 5.0, -0.5, 0.5)
            tilted[sleeve] = base * tilt

        # Re-normalize to sum to 1.0
        total = sum(tilted.values()) or 1.0
        return {k: v / total for k, v in tilted.items()}

    def _blend_weights(
        self, exposure: dict[str, dict[str, float]], theme: str, top_n: int = 15
    ) -> dict[str, float]:
        weights = self._theme_weights(exposure, theme, top_n=top_n)
        if weights:
            n = len(weights)
            eq = 1.0 / n
            blended = {k: 0.5 * v + 0.5 * eq for k, v in weights.items()}
            total = sum(blended.values()) or 1.0
            return {k: v / total for k, v in blended.items()}
        return {}
