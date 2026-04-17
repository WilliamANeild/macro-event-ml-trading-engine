from __future__ import annotations

import logging
from datetime import date, timedelta

from .aggregator import EventAggregator
from .gdelt_loader import GDELTLoader, GDELTEvent
from .geo_router import GeoRouter
from .keyword_matcher import KeywordMatcher
from .rss_loader import RSSLoader
from .schemas import EventFeatureRow
from .scorer import EventScorer, ScoredEvent

logger = logging.getLogger(__name__)


class EventFeatureBuilder:
    """Orchestrates the full event pipeline: load → classify → route → score → aggregate.

    Replaces the previous mock builder that returned hardcoded values.
    Set use_mock=True to get the old behavior for testing.
    """

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        if not use_mock:
            self._gdelt = GDELTLoader()
            self._rss = RSSLoader()
            self._matcher = KeywordMatcher()
            self._router = GeoRouter()
            self._scorer = EventScorer()
            self._aggregator = EventAggregator()
            self._cache: dict[date, list[EventFeatureRow]] = {}

    def build(
        self,
        as_of_date: date,
        theme: str,
        subtheme: str,
        region: str,
    ) -> EventFeatureRow:
        """Build an EventFeatureRow for a specific (theme, region) on a given date.

        If the full pipeline has data for this (theme, region), returns
        the aggregated row. Otherwise falls back to a baseline row.
        """
        if self.use_mock:
            return self._mock_build(as_of_date, theme, subtheme, region)

        # Build all rows for this week (cached per as_of_date)
        all_rows = self._build_all(as_of_date)

        # Find the matching row for the requested (theme, region)
        for row in all_rows:
            if row.theme == theme and row.region == region:
                return row

        # No data for this (theme, region) — return baseline
        return EventFeatureRow(
            as_of_date=as_of_date,
            theme=theme,
            subtheme=subtheme,
            region=region,
            values={
                "event_intensity": 0.0,
                "event_novelty": 0.0,
                "event_acceleration": 0.0,
            },
            metadata={"impulse_phase": "baseline", "note": "no event data found"},
        )

    def build_all(self, as_of_date: date) -> list[EventFeatureRow]:
        """Build EventFeatureRows for all themes and regions with activity.

        Returns all rows including sleeve-level rollups.
        """
        if self.use_mock:
            return [self._mock_build(as_of_date, "mock", "", "global")]
        return self._build_all(as_of_date)

    def _build_all(self, as_of_date: date) -> list[EventFeatureRow]:
        """Run the full pipeline and cache results per date."""
        if as_of_date in self._cache:
            return self._cache[as_of_date]

        # Step 1: Load events from GDELT and RSS
        gdelt_events = self._load_gdelt(as_of_date)
        rss_events = self._load_rss(as_of_date)

        # Step 2: Convert to ScoredEvents via classification and routing
        scored_inputs: list[ScoredEvent] = []
        scored_inputs.extend(self._process_gdelt(gdelt_events, as_of_date))
        scored_inputs.extend(self._process_rss(rss_events, as_of_date))

        if not scored_inputs:
            self._cache[as_of_date] = []
            return []

        # Step 3: Score daily
        daily_scores = self._scorer.score_day(scored_inputs, as_of_date)

        # Step 4: Aggregate into weekly rows
        rows = self._aggregator.aggregate_week(daily_scores, as_of_date)

        self._cache[as_of_date] = rows
        logger.info(
            "Built %d EventFeatureRows for %s (%d GDELT, %d RSS events)",
            len(rows), as_of_date, len(gdelt_events), len(rss_events),
        )
        return rows

    def _load_gdelt(self, as_of_date: date) -> list[GDELTEvent]:
        """Load GDELT events, catching errors gracefully."""
        try:
            return self._gdelt.load_latest()
        except Exception:
            logger.warning("GDELT load failed for %s", as_of_date, exc_info=True)
            return []

    def _load_rss(self, as_of_date: date) -> list:
        """Load RSS events, catching errors gracefully."""
        try:
            return self._rss.load(as_of_date)
        except Exception:
            logger.warning("RSS load failed for %s", as_of_date, exc_info=True)
            return []

    def _process_gdelt(
        self, gdelt_events: list[GDELTEvent], as_of_date: date
    ) -> list[ScoredEvent]:
        """Classify and route GDELT events into ScoredEvent records."""
        results: list[ScoredEvent] = []

        for ge in gdelt_events:
            # Geo-route using coordinates
            region = "global"
            if ge.lat is not None and ge.lon is not None:
                region = self._router.route(ge.lat, ge.lon)

            # Classify using action geo name + source URL as text
            text = f"{ge.action_geo_name} {ge.cameo_code}"
            matches = self._matcher.match(text)

            if matches:
                # Use the top match theme
                top = matches[0]
                results.append(ScoredEvent(
                    event_date=ge.event_date,
                    theme=top.theme_id,
                    region=region,
                    source_domain=ge.source_domain,
                    goldstein_scale=ge.goldstein_scale,
                    avg_tone=ge.avg_tone,
                    source_type="gdelt",
                ))
            else:
                # Use CAMEO root code as a fallback theme
                cameo_theme = f"CAMEO_{ge.cameo_root}"
                results.append(ScoredEvent(
                    event_date=ge.event_date,
                    theme=cameo_theme,
                    region=region,
                    source_domain=ge.source_domain,
                    goldstein_scale=ge.goldstein_scale,
                    avg_tone=ge.avg_tone,
                    source_type="gdelt",
                ))

        return results

    def _process_rss(self, rss_events: list, as_of_date: date) -> list[ScoredEvent]:
        """Classify RSS headlines into ScoredEvent records."""
        results: list[ScoredEvent] = []

        for re_event in rss_events:
            # Classify using title + summary
            text = f"{re_event.title} {re_event.summary}"
            matches = self._matcher.match(text)

            if not matches:
                continue

            # Create a ScoredEvent for each matched theme (up to 2)
            for match in matches[:2]:
                results.append(ScoredEvent(
                    event_date=re_event.publish_date,
                    theme=match.theme_id,
                    region="global",  # RSS events don't have coordinates
                    source_domain=re_event.source_domain,
                    goldstein_scale=0.0,  # RSS doesn't have Goldstein
                    avg_tone=0.0,  # RSS doesn't have tone
                    source_type="rss",
                ))

        return results

    @staticmethod
    def _mock_build(
        as_of_date: date, theme: str, subtheme: str, region: str
    ) -> EventFeatureRow:
        """Original mock behavior for pipeline testing."""
        return EventFeatureRow(
            as_of_date=as_of_date,
            theme=theme,
            subtheme=subtheme,
            region=region,
            values={
                "event_intensity": 0.5,
                "event_novelty": 0.4,
                "event_acceleration": 0.0,
            },
            metadata={"note": "mock event features for pipeline testing"},
        )
