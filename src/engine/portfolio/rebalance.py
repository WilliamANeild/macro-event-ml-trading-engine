from __future__ import annotations

from dataclasses import dataclass, field


STATES = ["IDLE", "IMPULSE_ONSET", "ACTIVE", "DECAY", "UNWIND"]

STATE_MULTIPLIER = {
    "IDLE": 0.0,
    "IMPULSE_ONSET": 0.5,
    "ACTIVE": 1.0,
    "DECAY": 0.6,
    "UNWIND": 0.2,
}

# score thresholds for state transitions
ONSET_THRESHOLD = 0.4
ACTIVE_THRESHOLD = 0.6
DECAY_THRESHOLD = 0.3
UNWIND_THRESHOLD = 0.15


@dataclass
class RebalanceStateMachine:
    states: dict[str, str] = field(default_factory=dict)
    ticks_in_state: dict[str, int] = field(default_factory=dict)

    def update(self, theme: str, signal_score: float) -> str:
        current = self.states.get(theme, "IDLE")
        ticks = self.ticks_in_state.get(theme, 0) + 1

        if current == "IDLE":
            if signal_score >= ONSET_THRESHOLD:
                new_state = "IMPULSE_ONSET"
            else:
                new_state = "IDLE"
        elif current == "IMPULSE_ONSET":
            if signal_score >= ACTIVE_THRESHOLD:
                new_state = "ACTIVE"
            elif signal_score < UNWIND_THRESHOLD:
                new_state = "IDLE"
            else:
                new_state = "IMPULSE_ONSET"
        elif current == "ACTIVE":
            if signal_score < DECAY_THRESHOLD:
                new_state = "DECAY"
            else:
                new_state = "ACTIVE"
        elif current == "DECAY":
            if signal_score >= ACTIVE_THRESHOLD:
                new_state = "ACTIVE"
            elif signal_score < UNWIND_THRESHOLD or ticks > 10:
                new_state = "UNWIND"
            else:
                new_state = "DECAY"
        elif current == "UNWIND":
            if ticks > 5 or signal_score < UNWIND_THRESHOLD:
                new_state = "IDLE"
            elif signal_score >= ONSET_THRESHOLD:
                new_state = "IMPULSE_ONSET"
            else:
                new_state = "UNWIND"
        else:
            new_state = "IDLE"

        if new_state != current:
            ticks = 0
        self.states[theme] = new_state
        self.ticks_in_state[theme] = ticks
        return new_state

    def position_multiplier(self, theme: str) -> float:
        state = self.states.get(theme, "IDLE")
        return STATE_MULTIPLIER.get(state, 0.0)
