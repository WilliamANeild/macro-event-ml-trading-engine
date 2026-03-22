from datetime import date

from src.engine.expression.ml_selector import MLExpressionSelector
from src.engine.meta.schemas import MetaSignal
from src.engine.universe.registry import get_universe


def _make_signal(confidence=0.8, regime="normal", direction="long", score=0.7):
    return MetaSignal(
        as_of_date=date(2024, 1, 1),
        theme="energy",
        subtheme="oil",
        score=score,
        confidence=confidence,
        direction=direction,
        regime=regime,
        theme_scores={"energy": 0.7},
    )


def test_high_confidence_normal():
    selector = MLExpressionSelector(universe=get_universe())
    signal = _make_signal(confidence=0.8, regime="normal")
    decision = selector.select(signal)
    assert decision.expression_type == "single_name"
    assert len(decision.target_symbols) > 0


def test_medium_confidence():
    selector = MLExpressionSelector(universe=get_universe())
    signal = _make_signal(confidence=0.5, regime="normal")
    decision = selector.select(signal)
    assert decision.expression_type == "etf"


def test_low_confidence_crisis():
    selector = MLExpressionSelector(universe=get_universe())
    signal = _make_signal(confidence=0.3, regime="crisis")
    decision = selector.select(signal)
    assert decision.expression_type == "blend"
    assert decision.hedge_fraction > 0


def test_short_direction():
    selector = MLExpressionSelector(universe=get_universe())
    signal = _make_signal(direction="short")
    decision = selector.select(signal)
    assert all(w <= 0 for w in decision.weights.values())


def test_no_universe():
    selector = MLExpressionSelector()
    signal = _make_signal()
    decision = selector.select(signal)
    assert len(decision.target_symbols) > 0
