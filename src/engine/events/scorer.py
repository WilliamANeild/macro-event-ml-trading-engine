from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class ScoredEvent:
    """A single event record with raw fields needed for scoring."""
    event_date: date
    theme: str
    region: str
    source_domain: str = ""
    goldstein_scale: float = 0.0
    avg_tone: float = 0.0
    fatalities: int = 0
    source_type: str = "gdelt"  # "gdelt", "rss", "acled"


@dataclass
class DailyScore:
    """Scored output for a single (theme, region, date)."""
    event_date: date
    theme: str
    region: str
    intensity: float = 0.0
    novelty: float = 0.0
    acceleration: float = 0.0
    source_count: int = 0
    article_count: int = 0


class EventScorer:
    """Converts classified events into intensity/novelty/acceleration scores.

    Follows the scoring spec from docs/nlp_pipeline_architecture.md Section 4.
    Maintains a rolling history buffer per (theme, region) for novelty and
    acceleration calculations.
    """

    # Intensity component weights (Section 4.1)
    W_ARTICLE_VOL = 0.30
    W_GOLDSTEIN = 0.25
    W_TONE = 0.20
    W_SOURCE_DIV = 0.15
    W_FATALITIES = 0.10

    # Novelty EWM parameters (Section 4.2)
    EWM_HALFLIFE = 3  # days
    NOVELTY_LOOKBACK = 60  # days for residual std

    # Acceleration parameters (Section 4.3)
    ACCEL_WEEK = 7  # days per week

    def __init__(self) -> None:
        # Rolling history: (theme, region) -> list of (date, intensity)
        self._history: dict[tuple[str, str], list[tuple[date, float]]] = defaultdict(list)

    def score_day(
        self,
        events: list[ScoredEvent],
        as_of_date: date,
    ) -> list[DailyScore]:
        """Score all events for a single day, grouped by (theme, region)."""
        # Group events by (theme, region)
        groups: dict[tuple[str, str], list[ScoredEvent]] = defaultdict(list)
        for e in events:
            groups[(e.theme, e.region)].append(e)

        results: list[DailyScore] = []
        for (theme, region), group in groups.items():
            intensity = self._compute_intensity(group)
            source_count = len({e.source_domain for e in group if e.source_domain})
            article_count = len(group)

            # Apply source diversity weight (Section 4.4)
            has_acled = any(e.source_type == "acled" for e in group)
            diversity_weight = _source_diversity_weight(source_count, has_acled)
            intensity *= diversity_weight

            # Store in history for novelty/acceleration
            key = (theme, region)
            self._history[key].append((as_of_date, intensity))
            # Keep 90 days max
            cutoff = as_of_date - timedelta(days=90)
            self._history[key] = [
                (d, v) for d, v in self._history[key] if d >= cutoff
            ]

            novelty = self._compute_novelty(key, as_of_date, intensity)
            acceleration = self._compute_acceleration(key, as_of_date)

            # Apply diversity weight to novelty and acceleration too
            novelty *= diversity_weight
            acceleration_weighted = acceleration  # acceleration is already relative

            results.append(DailyScore(
                event_date=as_of_date,
                theme=theme,
                region=region,
                intensity=round(intensity, 4),
                novelty=round(novelty, 4),
                acceleration=round(acceleration_weighted, 4),
                source_count=source_count,
                article_count=article_count,
            ))

        return results

    def _compute_intensity(self, events: list[ScoredEvent]) -> float:
        """Weighted intensity from article volume, Goldstein, tone, sources, fatalities."""
        n = len(events)
        if n == 0:
            return 0.0

        # Article volume: normalize by a reasonable daily cap
        article_vol = min(n / 20.0, 1.0)

        # Goldstein scale magnitude: average |Goldstein| normalized to [0, 1]
        # Goldstein ranges from -10 to +10
        goldstein_vals = [abs(e.goldstein_scale) for e in events if e.goldstein_scale != 0.0]
        goldstein_score = min(sum(goldstein_vals) / max(len(goldstein_vals), 1) / 10.0, 1.0) if goldstein_vals else 0.0

        # Tone: more negative = more severe. AvgTone typically ranges -15 to +15
        tone_vals = [e.avg_tone for e in events if e.avg_tone != 0.0]
        if tone_vals:
            avg_tone = sum(tone_vals) / len(tone_vals)
            tone_score = min(max(-avg_tone / 10.0, 0.0), 1.0)  # negative tone -> positive score
        else:
            tone_score = 0.0

        # Source diversity
        sources = {e.source_domain for e in events if e.source_domain}
        source_score = min(len(sources) / 5.0, 1.0)

        # Fatalities (log-transformed, ACLED only)
        total_fatalities = sum(e.fatalities for e in events)
        fatality_score = min(math.log2(1 + total_fatalities) / 10.0, 1.0) if total_fatalities > 0 else 0.0

        # Compute available weights (renormalize if some components are missing)
        components = []
        if n > 0:
            components.append((self.W_ARTICLE_VOL, article_vol))
        if goldstein_vals:
            components.append((self.W_GOLDSTEIN, goldstein_score))
        if tone_vals:
            components.append((self.W_TONE, tone_score))
        if sources:
            components.append((self.W_SOURCE_DIV, source_score))
        if total_fatalities > 0:
            components.append((self.W_FATALITIES, fatality_score))

        if not components:
            return 0.0

        total_weight = sum(w for w, _ in components)
        intensity = sum(w * v for w, v in components) / total_weight
        return max(0.0, min(intensity, 1.0))

    def _compute_novelty(
        self, key: tuple[str, str], as_of_date: date, intensity_today: float
    ) -> float:
        """Novelty via EWM residual z-score (Section 4.2)."""
        history = self._history[key]
        if len(history) < 3:
            # Not enough history — treat as novel if intensity is meaningful
            return 0.8 if intensity_today > 0.1 else 0.0

        # Build daily intensity series (last 60 days)
        cutoff = as_of_date - timedelta(days=self.NOVELTY_LOOKBACK)
        daily = {d: v for d, v in history if d >= cutoff and d < as_of_date}

        if not daily:
            return 0.8 if intensity_today > 0.1 else 0.0

        # Compute EWM of prior intensities (halflife=3 days)
        sorted_days = sorted(daily.keys())
        alpha = 1 - math.exp(-math.log(2) / self.EWM_HALFLIFE)
        ewm = daily[sorted_days[0]]
        residuals = []
        for d in sorted_days[1:]:
            ewm = alpha * daily[d] + (1 - alpha) * ewm
            residuals.append(daily[d] - ewm)

        intensity_ewm = ewm
        intensity_residual = intensity_today - intensity_ewm

        # Std of residuals
        if len(residuals) >= 2:
            mean_r = sum(residuals) / len(residuals)
            residual_std = math.sqrt(
                sum((r - mean_r) ** 2 for r in residuals) / len(residuals)
            )
        else:
            residual_std = 0.01

        novelty_z = intensity_residual / max(residual_std, 0.01)

        # Map z-score to novelty tier
        if novelty_z >= 3.0:
            return 1.0
        elif novelty_z >= 2.0:
            return 0.8
        elif novelty_z >= 1.0:
            return 0.5
        elif novelty_z >= 0.0:
            return 0.2
        else:
            return 0.0

    def _compute_acceleration(self, key: tuple[str, str], as_of_date: date) -> float:
        """Week-over-week intensity change (Section 4.3)."""
        history = self._history[key]
        if len(history) < 8:
            return 0.0

        # This week: last 7 days
        this_week_start = as_of_date - timedelta(days=self.ACCEL_WEEK - 1)
        last_week_start = this_week_start - timedelta(days=self.ACCEL_WEEK)

        this_week = [v for d, v in history if this_week_start <= d <= as_of_date]
        last_week = [v for d, v in history if last_week_start <= d < this_week_start]

        if not this_week or not last_week:
            return 0.0

        intensity_this = sum(this_week) / len(this_week)
        intensity_last = sum(last_week) / len(last_week)

        raw_accel = intensity_this - intensity_last
        acceleration = raw_accel / max(intensity_last, 0.05)

        return max(-1.0, min(acceleration, 1.0))


def _source_diversity_weight(source_count: int, has_acled: bool) -> float:
    """Source diversity multiplier (Section 4.4)."""
    if has_acled and source_count <= 1:
        return 0.85  # ACLED floor

    if source_count <= 1:
        return 0.50
    elif source_count == 2:
        return 0.70
    elif source_count <= 4:
        return 0.85
    else:
        return 1.00
