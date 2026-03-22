from __future__ import annotations

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


class MLExpressionSelector:
    def __init__(self, universe: list[Instrument] | None = None) -> None:
        self.universe = universe or []
        self.mapper = ExposureMapper()

    def select(self, signal: MetaSignal) -> ExpressionDecision:
        themes = [signal.theme]
        if signal.theme_scores:
            themes = list(signal.theme_scores.keys()) or themes

        # Build exposure matrix
        if self.universe:
            exposure = self.mapper.build_exposure_matrix(self.universe, themes)
        else:
            exposure = {}

        regime = signal.regime
        confidence = signal.confidence

        # Decision logic
        if confidence >= 0.7 and regime == "normal":
            expr_type = "single_name"
            weights = self._top_exposed(exposure, signal.theme, top_n=2)
        elif confidence >= 0.4 and regime not in ("crisis",):
            expr_type = "etf"
            weights = self._theme_weights(exposure, signal.theme)
        else:
            expr_type = "blend"
            weights = self._blend_weights(exposure, signal.theme)

        # Direction
        if signal.direction == "short":
            weights = {k: -abs(v) for k, v in weights.items()}
        elif signal.direction == "neutral":
            weights = {k: v * 0.25 for k, v in weights.items()}

        # Hedge fraction
        regime_mult = REGIME_HEDGE_MULTIPLIER.get(regime, 0.0)
        hedge_fraction = max(0.0, (1.0 - confidence)) * regime_mult

        symbols = list(weights.keys())
        if not symbols:
            symbols = [signal.theme.upper()[:3]]
            weights = {symbols[0]: 1.0 if signal.direction == "long" else -1.0}

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
        self, exposure: dict[str, dict[str, float]], theme: str
    ) -> dict[str, float]:
        if theme not in exposure:
            return {}
        return dict(exposure[theme])

    def _blend_weights(
        self, exposure: dict[str, dict[str, float]], theme: str
    ) -> dict[str, float]:
        weights = self._theme_weights(exposure, theme)
        # Flatten towards equal weight in blend mode
        if weights:
            n = len(weights)
            eq = 1.0 / n
            return {k: 0.5 * v + 0.5 * eq for k, v in weights.items()}
        return {}
