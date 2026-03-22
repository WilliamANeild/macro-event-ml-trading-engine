from datetime import date

from src.engine.derivatives.activation import OverlayActivationRule
from src.engine.derivatives.budget import PremiumBudgetManager
from src.engine.derivatives.overlay import DerivativesOverlayManager
from src.engine.derivatives.structures import StructureSelector
from src.engine.derivatives.unwind import UnwindManager
from src.engine.meta.schemas import MetaSignal
from src.engine.portfolio.schemas import PortfolioTarget


def _make_signal(conf=0.8, score=0.7, regime="crisis", direction="long"):
    return MetaSignal(
        as_of_date=date(2024, 1, 1),
        theme="energy",
        subtheme="oil",
        score=score,
        confidence=conf,
        direction=direction,
        regime=regime,
    )


def _make_portfolio(weights=None, net=0.5):
    weights = weights or {"XLE": 0.5}
    return PortfolioTarget(
        as_of_date=date(2024, 1, 1),
        weights=weights,
        gross_exposure=sum(abs(v) for v in weights.values()),
        net_exposure=net,
    )


def test_activation_high_conviction():
    rule = OverlayActivationRule()
    signal = _make_signal(conf=0.8, score=0.7, regime="crisis")
    should, reason = rule.should_activate(signal, _make_portfolio())
    assert should
    assert reason == "high_conviction_regime"


def test_activation_exposure_limit():
    rule = OverlayActivationRule()
    signal = _make_signal(conf=0.5, score=0.5, regime="normal")
    portfolio = _make_portfolio(net=0.9)
    should, reason = rule.should_activate(signal, portfolio)
    assert should
    assert reason == "exposure_limit"


def test_no_activation():
    rule = OverlayActivationRule()
    signal = _make_signal(conf=0.5, score=0.5, regime="normal")
    should, _ = rule.should_activate(signal, _make_portfolio(net=0.3))
    assert not should


def test_structure_selection():
    sel = StructureSelector()
    assert sel.select_structure("long", 0.8, "normal") == "call_spread"
    assert sel.select_structure("long", 0.5, "crisis") == "collar"
    assert sel.select_structure("short", 0.8, "normal") == "put_spread"
    assert sel.select_structure("neutral", 0.5, "normal") == "futures_scaling"


def test_budget_manager():
    mgr = PremiumBudgetManager(nav_cap_pct=0.03)
    assert mgr.remaining_budget(1.0) == 0.03
    allocated = mgr.allocate(0.02, 1.0)
    assert allocated == 0.02
    assert abs(mgr.remaining_budget(1.0) - 0.01) < 1e-10
    # Try to allocate more than remaining
    allocated = mgr.allocate(0.05, 1.0)
    assert abs(allocated - 0.01) < 1e-10
    assert mgr.remaining_budget(1.0) < 1e-10


def test_unwind_low_confidence():
    mgr = UnwindManager()
    should, reason = mgr.should_unwind(
        confidence=0.3, direction="long", prev_direction="long",
        days_held=5, budget_remaining=0.01,
    )
    assert should
    assert reason == "low_confidence"


def test_unwind_direction_flip():
    mgr = UnwindManager()
    should, reason = mgr.should_unwind(
        confidence=0.8, direction="short", prev_direction="long",
        days_held=5, budget_remaining=0.01,
    )
    assert should
    assert reason == "direction_flip"


def test_overlay_manager_integration():
    mgr = DerivativesOverlayManager()
    signal = _make_signal(conf=0.8, score=0.7, regime="crisis")
    portfolio = _make_portfolio()
    overlay = mgr.build_overlay(signal, portfolio)
    assert overlay.overlay_type != "none"
    assert overlay.premium_budget_used > 0
