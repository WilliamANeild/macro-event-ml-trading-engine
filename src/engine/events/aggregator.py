from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from .schemas import EventFeatureRow
from .scorer import DailyScore


# Theme ID prefix -> sleeve name
_SLEEVE_MAP = {
    "DEF": "defense",
    "SHP": "shipping",
    "CMD": "commodities",
    "MAC": "rates_us",
    "RAT": "rates_exus",
    "CRY": "crypto",
    "SAN": "sanctions",
    "GEO": "geopolitical",
    "XSL": "cross_sleeve",
    "REG": "regional",
}

# Theme ID -> subtheme label (derived from prefix pattern)
_SUBTHEME_MAP = {
    "MUN": "Munitions", "MIS": "Missile Defense", "SAT": "ISR-Space",
    "COM": "Communications", "CYB": "Cyber", "NAV": "Naval",
    "NUC": "Nuclear", "PRM": "Primes", "CON": "Conflict",
    "HRM": "Hormuz", "BAB": "Bab el-Mandeb", "SUE": "Suez",
    "BLK": "Black Sea", "TWN": "Taiwan Strait", "MAL": "Malacca",
    "PAN": "Panama", "INW": "India West", "INE": "India East",
    "INS": "Insurance-Freight", "ATK": "Maritime Attack",
    "CLS": "Port Closure", "SAN": "Sanctions Enforcement",
    "SPR": "Supply Risk", "GAS": "Natural Gas", "SAF": "Safe Haven",
    "IND": "Industrial Metals", "AGR": "Agriculture", "AGW": "Ag Weather",
    "OPC": "OPEC+", "HWK": "Hawkish Shock", "DOV": "Dovish Pivot",
    "CRV": "Yield Curve", "INF": "Inflation", "EMP": "Employment",
    "FED": "Fed Communication", "ECB": "ECB", "BOE": "BOE", "BOJ": "BOJ",
    "FIN": "Financial Stress", "REC": "Recession",
    "RON": "Risk-On", "FLT": "Capital Flight", "REG": "Regulatory",
    "MKT": "Market Structure", "ESC": "Escalation", "DES": "De-escalation",
    "VOL": "Volatility", "FXD": "FX Disruption", "EMR": "EM Stress",
    "UKR": "Ukraine", "MDE": "Middle East", "SCS": "South China Sea",
    "KOR": "Korea", "SAS": "South Asia", "UAS": "Unmanned Systems",
    "ARM": "Arms Transfers", "LBR": "Port Labor",
}


def _get_subtheme(theme_id: str) -> str:
    """Extract subtheme label from theme ID like DEF_MUN_001."""
    parts = theme_id.split("_")
    if len(parts) >= 2:
        return _SUBTHEME_MAP.get(parts[1], parts[1])
    return ""


def _get_sleeve(theme_id: str) -> str:
    """Extract sleeve name from theme ID prefix."""
    prefix = theme_id.split("_")[0] if "_" in theme_id else theme_id
    return _SLEEVE_MAP.get(prefix, "unknown")


def _trimmed_mean(values: list[float]) -> float:
    """Trimmed mean: drop 1 highest and 1 lowest, mean of the rest.

    If fewer than 5 values, use median instead.
    """
    if not values:
        return 0.0
    if len(values) < 5:
        s = sorted(values)
        mid = len(s) // 2
        return s[mid] if len(s) % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0
    s = sorted(values)
    trimmed = s[1:-1]
    return sum(trimmed) / len(trimmed)


def _impulse_phase(intensity: float, novelty: float, acceleration: float) -> str:
    """Determine event impulse phase (Section 4.5 of pipeline architecture)."""
    if novelty >= 0.6 and intensity >= 0.3 and acceleration > 0.2:
        return "onset"
    if intensity >= 0.5 and acceleration > 0.2 and novelty < 0.6:
        return "escalation"
    if intensity >= 0.4 and abs(acceleration) <= 0.2:
        return "sustained"
    if intensity >= 0.1 and acceleration < -0.2:
        return "decay"
    return "baseline"


class EventAggregator:
    """Rolls up daily DailyScore records into weekly EventFeatureRow objects.

    Follows the aggregation spec from docs/nlp_pipeline_architecture.md Section 5.
    - Intensity: trimmed mean of daily values
    - Novelty: max daily novelty in the week
    - Acceleration: computed at weekly level (already weekly in scorer)
    - Also produces sleeve-level rollup rows
    """

    def aggregate_week(
        self,
        daily_scores: list[DailyScore],
        week_end: date,
    ) -> list[EventFeatureRow]:
        """Aggregate daily scores into weekly EventFeatureRows.

        Args:
            daily_scores: All daily scores within the target week.
            week_end: The last day of the week (used as as_of_date).

        Returns:
            List of EventFeatureRow objects, one per (theme, region) plus
            sleeve-level rollup rows.
        """
        # Group by (theme, region)
        groups: dict[tuple[str, str], list[DailyScore]] = defaultdict(list)
        for s in daily_scores:
            groups[(s.theme, s.region)].append(s)

        rows: list[EventFeatureRow] = []

        # Per-theme rows
        for (theme, region), scores in groups.items():
            intensities = [s.intensity for s in scores]
            # Fill missing days with 0.0 (genuine absence)
            while len(intensities) < 7:
                intensities.append(0.0)

            intensity = _trimmed_mean(intensities)
            novelty = max(s.novelty for s in scores)
            acceleration = scores[-1].acceleration  # most recent day's value
            total_sources = len({s.source_count for s in scores})
            total_articles = sum(s.article_count for s in scores)

            # Recount unique sources across all days
            source_count = max(s.source_count for s in scores)

            phase = _impulse_phase(intensity, novelty, acceleration)

            rows.append(EventFeatureRow(
                as_of_date=week_end,
                theme=theme,
                subtheme=_get_subtheme(theme),
                region=region,
                values={
                    "event_intensity": round(intensity, 4),
                    "event_novelty": round(novelty, 4),
                    "event_acceleration": round(acceleration, 4),
                },
                metadata={
                    "source_count": source_count,
                    "article_count": total_articles,
                    "impulse_phase": phase,
                    "days_with_data": len([s for s in scores if s.intensity > 0]),
                },
            ))

        # Sleeve-level rollup rows
        sleeve_groups: dict[tuple[str, str], list[EventFeatureRow]] = defaultdict(list)
        for row in rows:
            sleeve = _get_sleeve(row.theme)
            sleeve_groups[(sleeve, row.region)].append(row)

        for (sleeve, region), theme_rows in sleeve_groups.items():
            sleeve_intensity = max(r.values["event_intensity"] for r in theme_rows)
            sleeve_novelty = max(r.values["event_novelty"] for r in theme_rows)

            # Intensity-weighted average of accelerations
            total_weight = sum(r.values["event_intensity"] for r in theme_rows)
            if total_weight > 0:
                sleeve_accel = sum(
                    r.values["event_acceleration"] * r.values["event_intensity"]
                    for r in theme_rows
                ) / total_weight
            else:
                sleeve_accel = 0.0

            rollup_theme = f"{sleeve.upper()}_ROLLUP"
            phase = _impulse_phase(sleeve_intensity, sleeve_novelty, sleeve_accel)

            rows.append(EventFeatureRow(
                as_of_date=week_end,
                theme=rollup_theme,
                subtheme="",
                region=region,
                values={
                    "event_intensity": round(sleeve_intensity, 4),
                    "event_novelty": round(sleeve_novelty, 4),
                    "event_acceleration": round(sleeve_accel, 4),
                },
                metadata={
                    "impulse_phase": phase,
                    "themes_active": len(theme_rows),
                    "rollup": True,
                },
            ))

        return rows
