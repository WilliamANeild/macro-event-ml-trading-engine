from __future__ import annotations

from src.engine.meta.schemas import MetaSignal
from src.engine.portfolio.schemas import PortfolioTarget

from .activation import OverlayActivationRule
from .budget import PremiumBudgetManager
from .schemas import DerivativesOverlay
from .structures import StructureSelector
from .unwind import UnwindManager


class DerivativesOverlayManager:
    def __init__(
        self, nav: float = 1.0, budget_reset_interval: int | None = None
    ) -> None:
        self.activation = OverlayActivationRule()
        self.structure_selector = StructureSelector()
        self.budget_manager = PremiumBudgetManager()
        self.unwind_manager = UnwindManager()
        self.nav = nav
        self.budget_reset_interval = budget_reset_interval
        self._prev_direction: str = ""
        self._days_held: int = 0
        self._active: bool = False
        self._period_count: int = 0

    def build_overlay(
        self,
        signal: MetaSignal,
        portfolio: PortfolioTarget,
    ) -> DerivativesOverlay:
        # Periodic budget reset
        self._period_count += 1
        if (
            self.budget_reset_interval is not None
            and self._period_count % self.budget_reset_interval == 0
        ):
            self.budget_manager.reset()

        # Check unwind conditions for active overlay
        if self._active:
            should_unwind, unwind_reason = self.unwind_manager.should_unwind(
                confidence=signal.confidence,
                direction=signal.direction,
                prev_direction=self._prev_direction,
                days_held=self._days_held,
                budget_remaining=self.budget_manager.remaining_budget(self.nav),
            )
            if should_unwind:
                fraction = self.unwind_manager.partial_unwind_fraction(
                    signal.confidence, self._days_held
                )
                held = self._days_held
                self._active = False
                self._days_held = 0
                return DerivativesOverlay(
                    as_of_date=signal.as_of_date,
                    overlay_type="unwind",
                    target_symbols=list(portfolio.weights.keys()),
                    notionals={},
                    premium_budget_used=0.0,
                    structure="unwind",
                    days_held=held,
                    unwind_fraction=fraction,
                    activation_reason=unwind_reason,
                )

        # Check activation
        should_activate, reason = self.activation.should_activate(signal, portfolio)
        if not should_activate:
            return DerivativesOverlay(
                as_of_date=signal.as_of_date,
                overlay_type="none",
                target_symbols=[],
                notionals={},
                premium_budget_used=0.0,
                metadata={"note": "no overlay triggered"},
            )

        # Select structure
        structure = self.structure_selector.select_structure(
            signal.direction, signal.confidence, signal.regime
        )

        # Budget allocation
        requested = 0.02 * self.nav  # 2% per overlay
        allocated = self.budget_manager.allocate(requested, self.nav)
        if allocated < 0.001:
            return DerivativesOverlay(
                as_of_date=signal.as_of_date,
                overlay_type="none",
                notionals={},
                premium_budget_used=0.0,
                activation_reason="budget_exhausted",
            )

        # Compute notionals
        notionals = self.structure_selector.compute_notionals(
            structure, portfolio.weights, allocated
        )

        self._active = True
        self._days_held += 1
        self._prev_direction = signal.direction

        return DerivativesOverlay(
            as_of_date=signal.as_of_date,
            overlay_type=structure,
            target_symbols=list(portfolio.weights.keys()),
            notionals=notionals,
            premium_budget_used=allocated,
            structure=structure,
            days_held=self._days_held,
            unwind_fraction=0.0,
            activation_reason=reason,
        )

    def tick_day(self) -> None:
        if self._active:
            self._days_held += 1

    def reset_budget(self) -> None:
        self.budget_manager.reset()
