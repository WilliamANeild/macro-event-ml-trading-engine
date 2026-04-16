from __future__ import annotations

from src.engine.meta.schemas import MetaSignal
from src.engine.universe.registry import get_universe_by_sleeve
from src.engine.universe.schemas import Instrument

from .ml_selector import MLExpressionSelector  # noqa: F401
from .schemas import ExpressionDecision


class ExpressionSelector:
    """Simple rule-based expression selector.

    Uses the universe registry to find instruments matching the signal's theme.
    Falls back to theme-name-based ticker if no instruments match.
    """

    def select(self, signal: MetaSignal) -> ExpressionDecision:
        instruments = get_universe_by_sleeve(signal.theme)
        core = [i for i in instruments if i.role == "core"]
        satellite = [i for i in instruments if i.role == "satellite"]

        if signal.confidence >= 0.7 and signal.direction != "neutral" and satellite:
            # High confidence with clear direction -> single names
            targets = satellite[:3]
            n = len(targets)
            weights = {t.symbol: 1.0 / n for t in targets}
            if signal.direction == "short":
                weights = {k: -v for k, v in weights.items()}
            return ExpressionDecision(
                as_of_date=signal.as_of_date,
                theme=signal.theme,
                subtheme=signal.subtheme,
                expression_type="single_name",
                target_symbols=list(weights.keys()),
                weights=weights,
                confidence=signal.confidence,
                regime=signal.regime,
            )

        if core:
            # Default -> core ETF expression
            target = core[0]
            w = 1.0 if signal.direction != "short" else -1.0
            if signal.direction == "neutral":
                w = 0.25
            return ExpressionDecision(
                as_of_date=signal.as_of_date,
                theme=signal.theme,
                subtheme=signal.subtheme,
                expression_type="etf",
                target_symbols=[target.symbol],
                weights={target.symbol: w},
                confidence=signal.confidence,
                regime=signal.regime,
            )

        # Fallback if no instruments found for theme
        fallback = signal.theme.upper()[:3]
        return ExpressionDecision(
            as_of_date=signal.as_of_date,
            theme=signal.theme,
            subtheme=signal.subtheme,
            expression_type="etf",
            target_symbols=[fallback],
            weights={fallback: 1.0},
            confidence=signal.confidence,
            regime=signal.regime,
        )
