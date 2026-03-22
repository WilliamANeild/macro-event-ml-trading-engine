from __future__ import annotations


class PremiumBudgetManager:
    def __init__(self, nav_cap_pct: float = 0.03) -> None:
        self.nav_cap_pct = nav_cap_pct
        self._cumulative_spend: float = 0.0

    def remaining_budget(self, nav: float = 1.0) -> float:
        cap = nav * self.nav_cap_pct
        return max(0.0, cap - self._cumulative_spend)

    def allocate(self, amount: float, nav: float = 1.0) -> float:
        available = self.remaining_budget(nav)
        actual = min(amount, available)
        self._cumulative_spend += actual
        return actual

    def reset(self) -> None:
        self._cumulative_spend = 0.0

    @property
    def cumulative_spend(self) -> float:
        return self._cumulative_spend
