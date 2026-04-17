from __future__ import annotations

import io
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from urllib.parse import urlparse
from urllib.request import urlopen, Request

import pandas as pd

logger = logging.getLogger(__name__)

# GDELT v2 master list endpoint
MASTERFILE_URL = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
LAST_UPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# GDELT Events CSV column names (v2, 61 columns)
# Reference: http://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf
EVENTS_COLUMNS = [
    "GlobalEventID", "Day", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode",
    "QuadClass", "GoldsteinScale", "NumMentions", "NumSources", "NumArticles",
    "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_ADM2Code",
    "Actor1Geo_Lat", "Actor1Geo_Long", "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_ADM2Code",
    "Actor2Geo_Lat", "Actor2Geo_Long", "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_ADM2Code",
    "ActionGeo_Lat", "ActionGeo_Long", "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]

# CAMEO root codes that are relevant to our system (HIGH or MEDIUM relevance)
# Focused on conflict, coercion, cooperation, and force — the codes that move markets
RELEVANT_ROOT_CODES = {
    "02",  # Appeal (military aid requests)
    "03",  # Express intent (military cooperation, ceasefire intent)
    "05",  # Diplomatic cooperation (agreements, military aid)
    "06",  # Material cooperation (military aid delivery, intelligence sharing)
    "07",  # Yield (sanctions easing, military withdrawal)
    "08",  # Investigate (included for sanctions enforcement)
    "09",  # Disapprove (protests, denouncements)
    "10",  # Demand (ceasefire demands, withdrawal demands)
    "11",  # Disapprove (formal objections)
    "12",  # Reduce relations (expulsions, sanctions threats)
    "13",  # Threaten (military threats, sanctions threats)
    "14",  # Protest (mass demonstrations)
    "15",  # Exhibit force posture (military exercises, deployments)
    "16",  # Reduce relations (embargoes, port closures)
    "17",  # Coerce (blockades, restrictions)
    "18",  # Assault (airstrikes, shelling)
    "19",  # Fight (armed clashes, combat)
    "20",  # Mass violence (mass killings, ethnic cleansing)
}


@dataclass
class GDELTEvent:
    """A normalized event record parsed from GDELT."""
    event_date: date
    cameo_code: str
    cameo_root: str
    actor1_country: str
    actor2_country: str
    lat: float | None
    lon: float | None
    goldstein_scale: float
    avg_tone: float
    num_mentions: int
    num_sources: int
    num_articles: int
    source_url: str
    source_domain: str
    action_geo_name: str


class GDELTLoader:
    """Downloads and parses GDELT v2 event update files.

    GDELT publishes new CSV files every 15 minutes. This loader can fetch
    the latest update or a specific file by URL.
    """

    def __init__(self, relevant_roots: set[str] | None = None) -> None:
        self._relevant_roots = relevant_roots or RELEVANT_ROOT_CODES

    def load_latest(self) -> list[GDELTEvent]:
        """Download and parse the most recent GDELT update file."""
        try:
            events_url = self._get_latest_events_url()
            if not events_url:
                logger.warning("Could not find latest GDELT events URL")
                return []
            return self._download_and_parse(events_url)
        except Exception:
            logger.warning("Failed to load latest GDELT update", exc_info=True)
            return []

    def load_from_url(self, url: str) -> list[GDELTEvent]:
        """Download and parse a specific GDELT events file by URL."""
        return self._download_and_parse(url)

    def load_from_dataframe(self, df: pd.DataFrame) -> list[GDELTEvent]:
        """Parse events from a pre-loaded DataFrame (useful for backtesting)."""
        return self._parse_events(df)

    def _get_latest_events_url(self) -> str | None:
        """Get the URL of the most recent GDELT events CSV from lastupdate.txt."""
        req = Request(LAST_UPDATE_URL, headers={"User-Agent": "MacroEventEngine/1.0"})
        with urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8")

        for line in text.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 3 and parts[2].endswith(".export.CSV.zip"):
                return parts[2]
        return None

    def _download_and_parse(self, url: str) -> list[GDELTEvent]:
        """Download a GDELT zip file and parse the events CSV inside."""
        logger.info("Downloading GDELT events from %s", url)
        req = Request(url, headers={"User-Agent": "MacroEventEngine/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()

        # GDELT files are zipped CSVs
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".CSV")]
            if not csv_names:
                logger.warning("No CSV found in GDELT zip: %s", url)
                return []

            with zf.open(csv_names[0]) as f:
                df = pd.read_csv(
                    f,
                    sep="\t",
                    header=None,
                    names=EVENTS_COLUMNS,
                    dtype=str,
                    on_bad_lines="skip",
                )

        events = self._parse_events(df)
        logger.info("Parsed %d relevant events from %s", len(events), url)
        return events

    def _parse_events(self, df: pd.DataFrame) -> list[GDELTEvent]:
        """Filter and convert a GDELT DataFrame into GDELTEvent records."""
        if df.empty:
            return []

        # Filter to relevant CAMEO root codes
        if "EventRootCode" in df.columns:
            df = df[df["EventRootCode"].isin(self._relevant_roots)]

        events: list[GDELTEvent] = []
        for row in df.itertuples(index=False):
            try:
                event = self._row_to_event(row)
                if event is not None:
                    events.append(event)
            except Exception:
                continue

        return events

    def _row_to_event(self, row) -> GDELTEvent | None:
        """Convert a single GDELT named-tuple row to a GDELTEvent."""
        cameo_code = str(getattr(row, "EventCode", ""))
        cameo_root = str(getattr(row, "EventRootCode", ""))

        # Parse date from DATEADDED (YYYYMMDDHHMMSS) or Day (YYYYMMDD)
        event_date = _parse_gdelt_date(row)
        if event_date is None:
            return None

        # Parse coordinates
        lat = _safe_float(getattr(row, "ActionGeo_Lat", None))
        lon = _safe_float(getattr(row, "ActionGeo_Long", None))

        # Parse numeric fields
        goldstein = _safe_float(getattr(row, "GoldsteinScale", None)) or 0.0
        tone = _safe_float(getattr(row, "AvgTone", None)) or 0.0
        mentions = int(_safe_float(getattr(row, "NumMentions", None)) or 0)
        sources = int(_safe_float(getattr(row, "NumSources", None)) or 0)
        articles = int(_safe_float(getattr(row, "NumArticles", None)) or 0)

        source_url = str(getattr(row, "SOURCEURL", "") or "")
        source_domain = ""
        if source_url:
            try:
                source_domain = urlparse(source_url).netloc
            except Exception:
                pass

        return GDELTEvent(
            event_date=event_date,
            cameo_code=cameo_code,
            cameo_root=cameo_root,
            actor1_country=str(getattr(row, "Actor1CountryCode", "") or ""),
            actor2_country=str(getattr(row, "Actor2CountryCode", "") or ""),
            lat=lat,
            lon=lon,
            goldstein_scale=goldstein,
            avg_tone=tone,
            num_mentions=mentions,
            num_sources=sources,
            num_articles=articles,
            source_url=source_url,
            source_domain=source_domain,
            action_geo_name=str(getattr(row, "ActionGeo_FullName", "") or ""),
        )


def _parse_gdelt_date(row) -> date | None:
    """Parse event date from a GDELT row (named tuple or Series)."""
    dateadded = str(getattr(row, "DATEADDED", "") or "")
    if dateadded and len(dateadded) >= 8:
        try:
            return datetime.strptime(dateadded[:8], "%Y%m%d").date()
        except ValueError:
            pass

    day_str = str(getattr(row, "Day", "") or "")
    if day_str and len(day_str) == 8:
        try:
            return datetime.strptime(day_str, "%Y%m%d").date()
        except ValueError:
            pass

    return None


def _safe_float(val) -> float | None:
    """Safely convert a value to float, returning None on failure."""
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
