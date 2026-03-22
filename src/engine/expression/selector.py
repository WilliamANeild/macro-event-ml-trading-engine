from __future__ import annotations

from src.engine.meta.schemas import MetaSignal

from .ml_selector import MLExpressionSelector  # noqa: F401
from .schemas import ExpressionDecision


class ExpressionSelector:
    def select(self, signal: MetaSignal) -> ExpressionDecision:
        if signal.confidence >= 0.6:
            return ExpressionDecision(
                as_of_date=signal.as_of_date,
                theme=signal.theme,
                subtheme=signal.subtheme,
                expression_type="single_name",
                target_symbols=["SEA"],
                weights={"SEA": 1.0},
                confidence=signal.confidence,
                metadata={"note": "mock selector chose single name"},
            )

        return ExpressionDecision(
            as_of_date=signal.as_of_date,
            theme=signal.theme,
            subtheme=signal.subtheme,
            expression_type="etf",
            target_symbols=["SEA"],
            weights={"SEA": 1.0},
            confidence=signal.confidence,
            metadata={"note": "mock selector chose etf"},
        )