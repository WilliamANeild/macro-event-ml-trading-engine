from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from src.engine.events.schemas import EventFeatureRow
from .synthetic import EventShock


class SyntheticEventGenerator:
    def __init__(self, event_manifest: list[EventShock], seed: int = 42) -> None:
        self.event_manifest = event_manifest
        self.rng = np.random.default_rng(seed)

    def generate(
        self, start_date: date, n_days: int, decay_rate: float = 0.3
    ) -> list[EventFeatureRow]:
        rows: list[EventFeatureRow] = []
        for day_offset in range(n_days):
            current_date = start_date + timedelta(days=day_offset)
            # Compute event intensity as sum of decaying shocks
            intensity = 0.0
            novelty = 0.0
            active_theme = "none"
            for shock in self.event_manifest:
                days_since = (current_date - shock.date).days
                if 0 <= days_since <= 30:
                    contribution = abs(shock.mean_shift) * np.exp(-decay_rate * days_since)
                    intensity += contribution
                    if days_since <= 2:
                        novelty = max(novelty, 0.8 * np.exp(-0.5 * days_since))
                    active_theme = shock.theme

            intensity = min(intensity, 1.0)
            base_noise = self.rng.normal(0, 0.02)
            intensity = max(0.0, intensity + base_noise)

            rows.append(
                EventFeatureRow(
                    as_of_date=current_date,
                    theme=active_theme if intensity > 0.05 else "none",
                    subtheme="synthetic",
                    region="global",
                    values={
                        "event_intensity": round(intensity, 4),
                        "event_novelty": round(novelty, 4),
                        "event_decay": round(np.exp(-decay_rate), 4),
                    },
                    metadata={"source": "synthetic"},
                )
            )
        return rows
