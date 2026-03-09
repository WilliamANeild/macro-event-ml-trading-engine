from __future__ import annotations

from datetime import date

from .schemas import EventFeatureRow


class EventFeatureBuilder:
    def build(
        self,
        as_of_date: date,
        theme: str,
        subtheme: str,
        region: str,
    ) -> EventFeatureRow:
        return EventFeatureRow(
            as_of_date=as_of_date,
            theme=theme,
            subtheme=subtheme,
            region=region,
            values={
                "event_intensity": 0.5,
                "event_novelty": 0.4,
            },
            metadata={"note": "mock event features for pipeline testing"},
        )