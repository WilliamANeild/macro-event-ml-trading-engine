"""Tests for the events pipeline (GDELT loader, geo router, keyword matcher, scorer, aggregator)."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from src.engine.events.gdelt_loader import (
    EVENTS_COLUMNS,
    RELEVANT_ROOT_CODES,
    GDELTEvent,
    GDELTLoader,
    _parse_gdelt_date,
)
from src.engine.events.geo_router import GeoRouter
from src.engine.events.keyword_matcher import KeywordMatcher, ThemeEntry, ThemeMatch
from src.engine.events.scorer import DailyScore, EventScorer, ScoredEvent
from src.engine.events.aggregator import EventAggregator
from src.engine.events.schemas import EventFeatureRow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_gdelt_row(**overrides) -> dict:
    """Build a dict with all GDELT columns set to empty strings, then apply overrides."""
    row = {col: "" for col in EVENTS_COLUMNS}
    row.update(overrides)
    return row


def _make_gdelt_df(rows: list[dict]) -> pd.DataFrame:
    """Build a DataFrame matching GDELT column layout from a list of row dicts."""
    return pd.DataFrame(rows, columns=EVENTS_COLUMNS)


# ===========================================================================
# 1. GDELTLoader
# ===========================================================================


class TestParseGdeltDate:
    """Tests for _parse_gdelt_date()."""

    def test_valid_dateadded(self):
        row = pd.Series({"DATEADDED": "20240315120000", "Day": ""})
        assert _parse_gdelt_date(row) == date(2024, 3, 15)

    def test_valid_day_field(self):
        row = pd.Series({"DATEADDED": "", "Day": "20231201"})
        assert _parse_gdelt_date(row) == date(2023, 12, 1)

    def test_dateadded_takes_precedence_over_day(self):
        row = pd.Series({"DATEADDED": "20240101000000", "Day": "20231231"})
        assert _parse_gdelt_date(row) == date(2024, 1, 1)

    def test_invalid_dateadded_falls_back_to_day(self):
        row = pd.Series({"DATEADDED": "not_a_date", "Day": "20240501"})
        assert _parse_gdelt_date(row) == date(2024, 5, 1)

    def test_both_invalid_returns_none(self):
        row = pd.Series({"DATEADDED": "baddate", "Day": "bad"})
        assert _parse_gdelt_date(row) is None

    def test_empty_fields_returns_none(self):
        row = pd.Series({"DATEADDED": "", "Day": ""})
        assert _parse_gdelt_date(row) is None


class TestGDELTLoaderParseEvents:
    """Tests for GDELTLoader._parse_events() and _row_to_event()."""

    def test_parse_events_with_relevant_root_code(self):
        rows = [
            _make_gdelt_row(
                EventRootCode="18",
                EventCode="181",
                DATEADDED="20240315120000",
                ActionGeo_Lat="26.5",
                ActionGeo_Long="56.2",
                GoldsteinScale="-7.0",
                AvgTone="-5.5",
                NumMentions="10",
                NumSources="3",
                NumArticles="5",
                SOURCEURL="https://reuters.com/article/123",
                Actor1CountryCode="IRN",
                Actor2CountryCode="USA",
                ActionGeo_FullName="Strait of Hormuz",
            ),
        ]
        df = _make_gdelt_df(rows)
        loader = GDELTLoader()
        events = loader.load_from_dataframe(df)

        assert len(events) == 1
        e = events[0]
        assert isinstance(e, GDELTEvent)
        assert e.event_date == date(2024, 3, 15)
        assert e.cameo_root == "18"
        assert e.cameo_code == "181"
        assert e.actor1_country == "IRN"
        assert e.actor2_country == "USA"
        assert e.lat == pytest.approx(26.5)
        assert e.lon == pytest.approx(56.2)
        assert e.goldstein_scale == pytest.approx(-7.0)
        assert e.avg_tone == pytest.approx(-5.5)
        assert e.num_mentions == 10
        assert e.num_sources == 3
        assert e.num_articles == 5
        assert e.source_domain == "reuters.com"
        assert e.action_geo_name == "Strait of Hormuz"

    def test_filters_out_irrelevant_root_codes(self):
        rows = [
            _make_gdelt_row(EventRootCode="01", EventCode="011", DATEADDED="20240315120000"),
            _make_gdelt_row(EventRootCode="04", EventCode="041", DATEADDED="20240315120000"),
        ]
        df = _make_gdelt_df(rows)
        loader = GDELTLoader()
        events = loader.load_from_dataframe(df)
        assert len(events) == 0

    def test_keeps_only_relevant_root_codes(self):
        rows = [
            _make_gdelt_row(EventRootCode="18", EventCode="181", DATEADDED="20240315120000"),
            _make_gdelt_row(EventRootCode="01", EventCode="011", DATEADDED="20240315120000"),
            _make_gdelt_row(EventRootCode="19", EventCode="191", DATEADDED="20240315120000"),
        ]
        df = _make_gdelt_df(rows)
        loader = GDELTLoader()
        events = loader.load_from_dataframe(df)
        assert len(events) == 2
        root_codes = {e.cameo_root for e in events}
        assert root_codes == {"18", "19"}

    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame(columns=EVENTS_COLUMNS)
        loader = GDELTLoader()
        assert loader.load_from_dataframe(df) == []

    def test_custom_relevant_roots(self):
        rows = [
            _make_gdelt_row(EventRootCode="01", EventCode="011", DATEADDED="20240315120000"),
        ]
        df = _make_gdelt_df(rows)
        loader = GDELTLoader(relevant_roots={"01"})
        events = loader.load_from_dataframe(df)
        assert len(events) == 1

    def test_row_with_missing_date_is_skipped(self):
        rows = [
            _make_gdelt_row(EventRootCode="18", EventCode="181", DATEADDED="", Day=""),
        ]
        df = _make_gdelt_df(rows)
        loader = GDELTLoader()
        events = loader.load_from_dataframe(df)
        assert len(events) == 0

    def test_row_to_event_missing_coords(self):
        rows = [
            _make_gdelt_row(
                EventRootCode="18",
                EventCode="181",
                DATEADDED="20240315120000",
                ActionGeo_Lat="",
                ActionGeo_Long="",
                GoldsteinScale="-3.0",
            ),
        ]
        df = _make_gdelt_df(rows)
        loader = GDELTLoader()
        events = loader.load_from_dataframe(df)
        assert len(events) == 1
        assert events[0].lat is None
        assert events[0].lon is None


# ===========================================================================
# 2. GeoRouter
# ===========================================================================


class TestGeoRouter:
    """Tests for GeoRouter.route()."""

    @pytest.fixture
    def router(self):
        return GeoRouter()

    def test_hormuz_tight_box(self, router):
        # Center of Strait of Hormuz tight box
        assert router.route(26.5, 56.2) == "hormuz"

    def test_hormuz_wide_box(self, router):
        # Inside wide box but outside tight box
        assert router.route(25.5, 55.0) == "hormuz"

    def test_suez(self, router):
        assert router.route(30.5, 32.45) == "suez"

    def test_panama(self, router):
        assert router.route(9.0, -79.7) == "panama"

    def test_malacca(self, router):
        assert router.route(1.3, 103.8) == "malacca"

    def test_taiwan_strait(self, router):
        assert router.route(24.5, 119.0) == "taiwan_strait"

    def test_bab_el_mandeb(self, router):
        assert router.route(12.5, 43.3) == "bab_el_mandeb"

    def test_unlocalized_coordinates(self, router):
        # Middle of the Atlantic Ocean -- should not match any zone
        assert router.route(0.0, -30.0) == "unlocalized"

    def test_unlocalized_extreme_coordinates(self, router):
        # Antarctica
        assert router.route(-80.0, 0.0) == "unlocalized"

    def test_route_all_returns_list(self, router):
        result = router.route_all(26.5, 56.2)
        assert isinstance(result, list)
        assert "hormuz" in result

    def test_route_all_unlocalized(self, router):
        result = router.route_all(0.0, -30.0)
        assert result == ["unlocalized"]


# ===========================================================================
# 3. KeywordMatcher
# ===========================================================================


class TestKeywordMatcher:
    """Tests for KeywordMatcher.match()."""

    @pytest.fixture
    def matcher(self):
        themes = [
            ThemeEntry(
                theme_id="DEF_MUN_001",
                sleeve="Defense",
                subtheme="Munitions",
                primary_keywords=["artillery", "ammunition", "munitions"],
                anchor_phrases=["artillery shell shortage", "ammunition stockpile"],
                negatives=["video game"],
            ),
            ThemeEntry(
                theme_id="SHP_HRM_001",
                sleeve="Shipping",
                subtheme="Hormuz",
                primary_keywords=["hormuz", "tanker", "oil shipment"],
                anchor_phrases=["strait of hormuz blockade"],
                negatives=[],
            ),
            ThemeEntry(
                theme_id="CMD_OPC_001",
                sleeve="Commodities",
                subtheme="OPEC+",
                primary_keywords=["opec", "oil production", "output cut"],
                anchor_phrases=["opec+ production cut"],
                negatives=[],
            ),
        ]
        return KeywordMatcher(themes=themes)

    def test_anchor_phrase_gives_high_confidence(self, matcher):
        matches = matcher.match("Reports of an artillery shell shortage on the eastern front")
        assert len(matches) >= 1
        top = matches[0]
        assert top.theme_id == "DEF_MUN_001"
        assert top.confidence == 0.9

    def test_multiple_keywords_give_medium_confidence(self, matcher):
        matches = matcher.match("New artillery ammunition delivered to depot")
        assert len(matches) >= 1
        top = matches[0]
        assert top.theme_id == "DEF_MUN_001"
        assert top.confidence == 0.7

    def test_single_keyword_gives_low_confidence(self, matcher):
        matches = matcher.match("Tanker spotted near coast")
        shipping = [m for m in matches if m.theme_id == "SHP_HRM_001"]
        assert len(shipping) == 1
        assert shipping[0].confidence == 0.5

    def test_negative_keyword_excludes_match(self, matcher):
        matches = matcher.match("Video game features artillery and ammunition")
        defense = [m for m in matches if m.theme_id == "DEF_MUN_001"]
        assert len(defense) == 0

    def test_no_match_returns_empty(self, matcher):
        matches = matcher.match("The weather today is sunny and warm")
        assert matches == []

    def test_max_matches_limit(self):
        # Create more than MAX_MATCHES themes that all match
        themes = [
            ThemeEntry(
                theme_id=f"TEST_{i:03d}",
                sleeve="Test",
                subtheme=f"Sub{i}",
                primary_keywords=["conflict"],
                anchor_phrases=[],
                negatives=[],
            )
            for i in range(10)
        ]
        matcher = KeywordMatcher(themes=themes)
        matches = matcher.match("Major conflict reported")
        assert len(matches) == KeywordMatcher.MAX_MATCHES
        assert len(matches) == 4

    def test_case_insensitive_matching(self, matcher):
        matches = matcher.match("OPEC+ PRODUCTION CUT announced today")
        opec = [m for m in matches if m.theme_id == "CMD_OPC_001"]
        assert len(opec) == 1
        assert opec[0].confidence == 0.9

    def test_match_returns_theme_match_objects(self, matcher):
        matches = matcher.match("Strait of Hormuz blockade feared")
        assert all(isinstance(m, ThemeMatch) for m in matches)
        top = matches[0]
        assert top.sleeve == "Shipping"
        assert top.subtheme == "Hormuz"


# ===========================================================================
# 4. EventScorer
# ===========================================================================


class TestEventScorer:
    """Tests for EventScorer.score_day()."""

    def _make_event(self, theme="DEF_MUN_001", region="hormuz", **kwargs):
        defaults = dict(
            event_date=date(2024, 3, 15),
            theme=theme,
            region=region,
            source_domain="reuters.com",
            goldstein_scale=-5.0,
            avg_tone=-4.0,
            fatalities=0,
            source_type="gdelt",
        )
        defaults.update(kwargs)
        return ScoredEvent(**defaults)

    def test_score_day_produces_daily_scores(self):
        scorer = EventScorer()
        events = [self._make_event(source_domain=f"source{i}.com") for i in range(5)]
        results = scorer.score_day(events, date(2024, 3, 15))

        assert len(results) == 1
        score = results[0]
        assert isinstance(score, DailyScore)
        assert score.theme == "DEF_MUN_001"
        assert score.region == "hormuz"
        assert score.event_date == date(2024, 3, 15)

    def test_intensity_in_valid_range(self):
        scorer = EventScorer()
        events = [self._make_event(source_domain=f"source{i}.com") for i in range(5)]
        results = scorer.score_day(events, date(2024, 3, 15))
        assert 0.0 <= results[0].intensity <= 1.0

    def test_novelty_in_valid_range(self):
        scorer = EventScorer()
        events = [self._make_event()]
        results = scorer.score_day(events, date(2024, 3, 15))
        assert 0.0 <= results[0].novelty <= 1.0

    def test_multiple_theme_region_groups(self):
        scorer = EventScorer()
        events = [
            self._make_event(theme="DEF_MUN_001", region="hormuz"),
            self._make_event(theme="SHP_HRM_001", region="suez"),
        ]
        results = scorer.score_day(events, date(2024, 3, 15))
        assert len(results) == 2
        themes = {r.theme for r in results}
        assert themes == {"DEF_MUN_001", "SHP_HRM_001"}

    def test_empty_events_returns_empty(self):
        scorer = EventScorer()
        results = scorer.score_day([], date(2024, 3, 15))
        assert results == []

    def test_source_diversity_affects_intensity(self):
        scorer = EventScorer()

        # Single source -> diversity penalty
        single_source_events = [self._make_event(source_domain="same.com") for _ in range(5)]
        r1 = scorer.score_day(single_source_events, date(2024, 3, 15))

        # Reset scorer for fresh history
        scorer2 = EventScorer()
        # Multiple sources -> higher diversity weight
        multi_source_events = [
            self._make_event(source_domain=f"source{i}.com") for i in range(6)
        ]
        r2 = scorer2.score_day(multi_source_events, date(2024, 3, 16))

        # Multi-source should have higher intensity due to diversity weight
        assert r2[0].intensity >= r1[0].intensity

    def test_novelty_with_history(self):
        scorer = EventScorer()
        base_date = date(2024, 1, 1)

        # Build up history with low-intensity events
        for day_offset in range(10):
            low_events = [self._make_event(
                event_date=base_date + timedelta(days=day_offset),
                goldstein_scale=-1.0,
                avg_tone=-1.0,
                source_domain=f"src{day_offset}.com",
            )]
            scorer.score_day(low_events, base_date + timedelta(days=day_offset))

        # Now spike with high-intensity events
        spike_date = base_date + timedelta(days=10)
        spike_events = [
            self._make_event(
                event_date=spike_date,
                goldstein_scale=-9.0,
                avg_tone=-10.0,
                source_domain=f"spike{i}.com",
            )
            for i in range(15)
        ]
        results = scorer.score_day(spike_events, spike_date)
        # After sustained low activity, a spike should register meaningful novelty
        assert results[0].novelty > 0.0


# ===========================================================================
# 5. EventAggregator
# ===========================================================================


class TestEventAggregator:
    """Tests for EventAggregator.aggregate_week()."""

    def _make_daily_score(self, day_offset=0, theme="DEF_MUN_001", region="hormuz",
                          intensity=0.5, novelty=0.3, acceleration=0.1):
        return DailyScore(
            event_date=date(2024, 3, 11) + timedelta(days=day_offset),
            theme=theme,
            region=region,
            intensity=intensity,
            novelty=novelty,
            acceleration=acceleration,
            source_count=3,
            article_count=10,
        )

    def test_aggregate_week_produces_feature_rows(self):
        agg = EventAggregator()
        daily = [self._make_daily_score(day_offset=i) for i in range(7)]
        week_end = date(2024, 3, 17)
        rows = agg.aggregate_week(daily, week_end)

        # Should have at least 1 theme row + 1 sleeve rollup
        assert len(rows) >= 1
        theme_rows = [r for r in rows if "ROLLUP" not in r.theme]
        assert len(theme_rows) == 1

    def test_feature_row_structure(self):
        agg = EventAggregator()
        daily = [self._make_daily_score(day_offset=i) for i in range(7)]
        week_end = date(2024, 3, 17)
        rows = agg.aggregate_week(daily, week_end)

        theme_row = [r for r in rows if r.theme == "DEF_MUN_001"][0]
        assert isinstance(theme_row, EventFeatureRow)
        assert theme_row.as_of_date == week_end
        assert theme_row.theme == "DEF_MUN_001"
        assert theme_row.region == "hormuz"
        assert "event_intensity" in theme_row.values
        assert "event_novelty" in theme_row.values
        assert "event_acceleration" in theme_row.values
        assert "impulse_phase" in theme_row.metadata
        assert "source_count" in theme_row.metadata
        assert "article_count" in theme_row.metadata

    def test_sleeve_rollup_created(self):
        agg = EventAggregator()
        daily = [self._make_daily_score(day_offset=i) for i in range(7)]
        week_end = date(2024, 3, 17)
        rows = agg.aggregate_week(daily, week_end)

        rollup_rows = [r for r in rows if "ROLLUP" in r.theme]
        assert len(rollup_rows) >= 1
        rollup = rollup_rows[0]
        assert rollup.theme == "DEFENSE_ROLLUP"
        assert rollup.metadata.get("rollup") is True

    def test_multiple_themes_produce_separate_rows(self):
        agg = EventAggregator()
        daily = [
            self._make_daily_score(day_offset=0, theme="DEF_MUN_001", region="hormuz"),
            self._make_daily_score(day_offset=0, theme="SHP_HRM_001", region="suez"),
        ]
        week_end = date(2024, 3, 17)
        rows = agg.aggregate_week(daily, week_end)

        theme_rows = [r for r in rows if "ROLLUP" not in r.theme]
        assert len(theme_rows) == 2
        themes = {r.theme for r in theme_rows}
        assert themes == {"DEF_MUN_001", "SHP_HRM_001"}

    def test_intensity_values_are_reasonable(self):
        agg = EventAggregator()
        daily = [self._make_daily_score(day_offset=i, intensity=0.4 + i * 0.05) for i in range(7)]
        week_end = date(2024, 3, 17)
        rows = agg.aggregate_week(daily, week_end)

        theme_row = [r for r in rows if r.theme == "DEF_MUN_001"][0]
        intensity = theme_row.values["event_intensity"]
        # Trimmed mean of 0.4..0.7 should be somewhere in between
        assert 0.3 <= intensity <= 0.8

    def test_novelty_is_max_of_daily(self):
        agg = EventAggregator()
        daily = [
            self._make_daily_score(day_offset=0, novelty=0.2),
            self._make_daily_score(day_offset=1, novelty=0.8),
            self._make_daily_score(day_offset=2, novelty=0.5),
        ]
        week_end = date(2024, 3, 17)
        rows = agg.aggregate_week(daily, week_end)

        theme_row = [r for r in rows if r.theme == "DEF_MUN_001"][0]
        assert theme_row.values["event_novelty"] == pytest.approx(0.8)

    def test_empty_daily_scores(self):
        agg = EventAggregator()
        rows = agg.aggregate_week([], date(2024, 3, 17))
        assert rows == []

    def test_impulse_phase_present(self):
        agg = EventAggregator()
        daily = [self._make_daily_score(day_offset=i, intensity=0.6, novelty=0.7,
                                        acceleration=0.3) for i in range(7)]
        week_end = date(2024, 3, 17)
        rows = agg.aggregate_week(daily, week_end)

        theme_row = [r for r in rows if r.theme == "DEF_MUN_001"][0]
        phase = theme_row.metadata["impulse_phase"]
        assert phase in {"onset", "escalation", "sustained", "decay", "baseline"}
