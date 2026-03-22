from __future__ import annotations


class UnwindManager:
    def __init__(
        self,
        min_confidence: float = 0.4,
        max_holding_days: int = 30,
    ) -> None:
        self.min_confidence = min_confidence
        self.max_holding_days = max_holding_days

    def should_unwind(
        self,
        confidence: float,
        direction: str,
        prev_direction: str,
        days_held: int,
        budget_remaining: float,
    ) -> tuple[bool, str]:
        if confidence < self.min_confidence:
            return True, "low_confidence"
        if direction != prev_direction and prev_direction != "":
            return True, "direction_flip"
        if days_held >= self.max_holding_days:
            return True, "max_holding"
        if budget_remaining <= 0:
            return True, "budget_exhausted"
        return False, "hold"

    def partial_unwind_fraction(
        self, confidence: float, days_held: int
    ) -> float:
        # Gradual unwind based on confidence decay and time
        conf_factor = max(0.0, 1.0 - confidence) * 0.5
        time_factor = min(1.0, days_held / self.max_holding_days) * 0.5
        return min(1.0, conf_factor + time_factor)
