# NLP Processing Pipeline Architecture

Version: 1.0
Date: 2026-04-16

This document specifies the complete NLP pipeline that converts raw news, event,
and entity data from five heterogeneous sources into weekly `EventFeatureRow`
objects consumed by the expert models and the rebalance state machine.

---

## Table of Contents

1. [Ingestion Layer](#1-ingestion-layer)
2. [Normalization Layer](#2-normalization-layer)
3. [Classification Layer](#3-classification-layer)
4. [Scoring Layer](#4-scoring-layer)
5. [Aggregation Layer](#5-aggregation-layer)
6. [Output Layer](#6-output-layer)
7. [Data Flow Diagram](#7-data-flow-diagram)

---

## 1. Ingestion Layer

Each source has a dedicated ingestor that polls or streams raw data, handles
errors, and deduplicates records before passing them downstream.

### 1.1 GDELT (Event Database + GKG)

| Parameter | Value |
|-----------|-------|
| **Endpoint** | Raw CSV files from `data.gdeltproject.org/gdeltv2/` (15-min update files) |
| **Poll interval** | Every 15 minutes, aligned to GDELT's publication cadence (`:00`, `:15`, `:30`, `:45`) |
| **Format** | Tab-separated CSV. Two file types per update: Events (CAMEO-coded event records) and GKG (themes, tone, entity mentions, GCAM dimensions) |
| **Error handling** | Retry with exponential backoff (initial 30s, max 5 min, 5 retries). If a 15-min file is missing, skip and log; GDELT occasionally publishes late. Flag gaps in an ingestion-health table for downstream quality checks. |
| **Deduplication** | Primary key: `GLOBALEVENTID` for Events, `GKGRECORDID` for GKG. Maintain a rolling 48-hour Bloom filter of seen IDs. Duplicate records (same event re-published in a later file) are dropped. |
| **Backfill** | Master file list at `data.gdeltproject.org/gdeltv2/masterfilelist.txt` enables historical backfill. Backfill runs use the same parsing code but skip the Bloom filter and write directly to the historical store. |
| **Output** | One `RawGdeltEvent` record per row (Events file) and one `RawGdeltGkg` record per row (GKG file), written to an append-only staging table. |

### 1.2 RSS Feeds (AP, BBC, Al Jazeera, Maritime, Central Banks)

| Parameter | Value |
|-----------|-------|
| **Feeds** | AP World (`apnews.com/index.rss`), BBC World (`feeds.bbci.co.uk/news/world/rss.xml`), Al Jazeera (`aljazeera.com/xml/rss/all.xml`), Maritime Executive (`maritime-executive.com/feed`), gCaptain (`gcaptain.com/feed/`), Splash247 (`splash247.com/feed/`), Hellenic Shipping News (`hellenicshippingnews.com/feed/`), Defense News (`defensenews.com/arc/outboundfeeds/rss/`), Fed speeches RSS, ECB RSS, BOE RSS, BOJ press page |
| **Poll interval** | Every 10 minutes for news feeds; every 15 minutes for central bank feeds |
| **Format** | XML/RSS parsed via `feedparser` |
| **Error handling** | Per-feed circuit breaker: after 3 consecutive failures, back off to 30-min polling for that feed. Alert on feeds that have returned zero new items for >6 hours (likely a URL change or feed death). Timeout per request: 15 seconds. |
| **Deduplication** | Primary key: canonical URL (after stripping query parameters and UTM tags). Secondary: `(source_domain, title_hash)` for feeds that recycle URLs. Maintain a rolling 72-hour set of seen URLs per feed. |
| **Output** | One `RawRssItem` per article: `{source, url, title, summary, published_at, raw_xml}`. |

### 1.3 ACLED (Armed Conflict Location & Event Data)

| Parameter | Value |
|-----------|-------|
| **Endpoint** | ACLED API (`api.acleddata.com/acled/read`) with API key |
| **Poll interval** | Weekly batch pull, every Monday 06:00 UTC. ACLED updates weekly with a 1-2 week coding lag. |
| **Format** | JSON (API) or CSV (bulk download) |
| **Error handling** | Retry 3 times with 60-second intervals. If the weekly pull fails, retry every 6 hours until success or manual intervention. Log the data_date range returned to verify no gaps. |
| **Deduplication** | Primary key: `data_id` (ACLED's unique event identifier). Maintain a persistent set of all ingested `data_id` values. ACLED sometimes retroactively updates event records (changing fatality counts, event types); treat updated records as upserts keyed on `data_id`. |
| **Output** | One `RawAcledEvent` per event: `{data_id, event_date, event_type, sub_event_type, actor1, actor2, country, admin1, latitude, longitude, fatalities, source, notes}`. |

### 1.4 aisstream.io (Real-Time AIS Ship Tracking)

| Parameter | Value |
|-----------|-------|
| **Endpoint** | WebSocket at `wss://stream.aisstream.io/v0/stream` |
| **Connection model** | Persistent WebSocket. Subscription message must be sent within 3 seconds of connection. Subscribe to bounding boxes for the 10 monitored chokepoints and 6 port clusters defined in `docs/chokepoint_coordinates.md`. Use "wide" bounding boxes for detection, "tight" boxes for intensity scoring. |
| **Format** | JSON messages (AIS position reports, static data reports) |
| **Error handling** | Auto-reconnect on disconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s). Heartbeat monitoring: if no message received for 60 seconds, force reconnect. Log connection uptime and gap periods. |
| **Deduplication** | AIS messages are inherently duplicative (same vessel reports position every few seconds to minutes). Deduplicate by `(MMSI, message_type)` with a minimum inter-message interval of 5 minutes per vessel. For position reports, keep only the latest per MMSI within each 5-minute window. |
| **Volume management** | Filter subscription to ship types relevant to the system: tankers (type 80-89), cargo (70-79), and LNG carriers. Ignore fishing, pleasure craft, and SAR vessels. Expected volume: ~50-100 messages/second across all monitored boxes. |
| **Output** | Aggregated `AisSnapshot` records per chokepoint per 15-minute window: `{chokepoint_id, window_start, vessel_count, vessel_type_breakdown, avg_speed, anomaly_flags}`. Raw per-vessel records are discarded after aggregation. |

### 1.5 OFAC / OpenSanctions (Sanctions Lists)

| Parameter | Value |
|-----------|-------|
| **Endpoints** | OFAC SDN list XML from `sanctionslist.ofac.treas.gov/`; OpenSanctions bulk JSON from `data.opensanctions.org/` |
| **Poll interval** | Every 6 hours for both sources |
| **Format** | XML (OFAC), JSON (OpenSanctions) |
| **Error handling** | Standard retry (3 attempts, 30-second intervals). Sanctions data is critical for compliance; if both sources fail for >24 hours, raise a high-priority alert. |
| **Deduplication / change detection** | Full-list diff against the previously stored snapshot. Compute a set difference on entity identifiers (OFAC: `uid`; OpenSanctions: `id`). New additions, removals, and modifications are captured as `SanctionsDelta` records. |
| **Output** | `SanctionsDelta` records: `{delta_type: add|remove|modify, entity_id, entity_name, entity_type, programs, countries, detected_at}`. The full current list is also stored as a reference snapshot for entity matching in the Classification Layer. |

---

## 2. Normalization Layer

All raw records from the five ingestors are transformed into a common
**Unified Event Record (UER)** before classification. This decouples
source-specific parsing from theme logic.

### 2.1 Unified Event Record Schema

```
UnifiedEventRecord:
    record_id:        str        # Deterministic hash of (source, source_id)
    source:           str        # "gdelt_event" | "gdelt_gkg" | "rss" | "acled" | "ais" | "sanctions"
    source_id:        str        # Original ID from the source system
    timestamp:        datetime   # Event time (publication time for news, event time for ACLED/GDELT)
    ingested_at:      datetime   # When we ingested it
    text_primary:     str        # Main text for classification (headline, event description, etc.)
    text_secondary:   str | None # Supporting text (summary, article excerpt, GKG themes string)
    entities:         list[str]  # Named entities (actors, organizations, countries)
    geo_country:      str | None # ISO 3166-1 alpha-2 country code
    geo_fips:         str | None # FIPS 10-4 code (GDELT native geocoding)
    geo_lat:          float | None
    geo_lon:          float | None
    cameo_code:       str | None # CAMEO event code (GDELT only, null for other sources)
    goldstein_scale:  float | None # Goldstein conflict-cooperation score (GDELT only)
    tone:             float | None # Average tone (GDELT GKG tone field)
    gkg_themes:       list[str] # GKG theme tags (GDELT only, empty for others)
    source_url:       str | None # Link to original article or data record
    raw_metadata:     dict       # Source-specific fields not captured above
```

### 2.2 Source-Specific Normalization Rules

**GDELT Events -> UER:**
- `text_primary` = constructed from `Actor1Name + EventCode description + Actor2Name + ActionGeo_FullName`. GDELT Events do not contain article text; the "text" is a structured description derived from the coded fields.
- `cameo_code` = `EventCode` field (3-4 digit CAMEO code)
- `goldstein_scale` = `GoldsteinScale` field directly
- `geo_*` fields populated from `ActionGeo_Lat`, `ActionGeo_Long`, `ActionGeo_CountryCode`, `ActionGeo_ADM1Code`
- `entities` = `[Actor1Name, Actor2Name]` filtered to non-null

**GDELT GKG -> UER:**
- `text_primary` = `V2Themes` field (semicolon-delimited theme tags, treated as a keyword bag)
- `text_secondary` = `V2EnhancedLocations` + `V2EnhancedPersons` + `V2EnhancedOrganizations` (concatenated for entity context)
- `tone` = first element of `V2Tone` field (average tone on -100 to +100 scale)
- `gkg_themes` = parsed list from `V2Themes`
- `geo_*` = first location from `V2EnhancedLocations` (highest confidence)

**RSS Items -> UER:**
- `text_primary` = `title`
- `text_secondary` = `summary` (RSS description/summary field)
- `entities` = extracted via lightweight NER (spaCy `en_core_web_sm`) run on title + summary. Cache NER model in memory; run asynchronously if throughput is a concern.
- `geo_*` = inferred from NER location entities using a country/city gazetteer lookup. Null if no geographic entity found.
- `cameo_code`, `goldstein_scale`, `tone` = all null (not available from RSS)

**ACLED Events -> UER:**
- `text_primary` = `notes` field (free-text event description)
- `entities` = `[actor1, actor2]`
- `geo_country` = `country` mapped to ISO alpha-2
- `geo_lat`, `geo_lon` = `latitude`, `longitude` directly
- `cameo_code` = null (ACLED uses its own event taxonomy; mapped to themes in Classification Layer)
- `goldstein_scale` = estimated from ACLED event type: Battles = -8.0, Explosions/Remote violence = -9.0, Violence against civilians = -9.5, Protests = -4.0, Riots = -6.0, Strategic developments = 0.0

**AIS Snapshots -> UER:**
- `text_primary` = constructed descriptor: `"{vessel_count} vessels transiting {chokepoint_name}; {anomaly_description}"`
- `geo_*` = chokepoint centroid coordinates
- Only generates a UER when an anomaly is detected (vessel count deviation > 2 sigma from 30-day rolling mean, or average speed anomaly). Normal traffic snapshots are stored for baseline computation but do not generate UERs.

**Sanctions Deltas -> UER:**
- `text_primary` = `"{delta_type} sanction: {entity_name} ({entity_type}) under {programs}"`
- `entities` = `[entity_name]` + linked entities from OpenSanctions graph
- `geo_country` = `countries` field (may be multiple; primary country used)
- Generated only for additions and modifications, not removals (removals are logged but do not generate event signals).

### 2.3 Normalization Quality Checks

Before a UER is passed to the Classification Layer, it must pass:

1. **Timestamp validity**: `timestamp` must be within the last 30 days (for real-time pipeline) or within the backtest date range (for historical). Records with timestamps in the future or older than 30 days are dropped with a warning log.
2. **Text minimum length**: `text_primary` must contain at least 10 characters. Records below this threshold are likely parsing artifacts.
3. **Geographic plausibility**: If `geo_lat` and `geo_lon` are present, they must be within valid ranges (-90 to 90, -180 to 180). Out-of-range coordinates are nullified.
4. **Source clock skew**: RSS `published_at` timestamps occasionally drift. If the publication timestamp is more than 1 hour in the future relative to ingestion time, clamp it to ingestion time.

---

## 3. Classification Layer

The Classification Layer matches each Unified Event Record to one or more of the
70 themes defined in `docs/keyword_taxonomy.md`. Classification proceeds through
four parallel routing paths; results are merged via a co-activation resolver.

### 3.1 Keyword Matching

Keyword matching is the primary classification method for RSS, ACLED, and AIS
sources (which lack pre-structured theme codes).

**Three match levels, evaluated in order of decreasing confidence:**

1. **Anchor phrase match (confidence = 0.90)**
   - Exact substring match of any anchor phrase from the taxonomy against `text_primary + text_secondary`.
   - Case-insensitive. Whitespace-normalized (collapse multiple spaces, strip leading/trailing).
   - Example: "munitions contract" in headline -> `DEF_MUN_001` at confidence 0.90.

2. **Primary keyword match with context (confidence = 0.70)**
   - At least one primary keyword must appear in the text.
   - Then check disambiguation negatives: if any negative term co-occurs in the same text, suppress the match (confidence drops to 0.0).
   - Fuzzy matching for primary keywords: allow edit distance <= 1 for tokens >= 6 characters (catches typos like "sanctons" -> "sanctions"). Use a precomputed BK-tree over all primary keyword tokens for O(1) amortized lookup.
   - Example: "munitions" present and no negatives -> `DEF_MUN_001` at confidence 0.70.

3. **Fuzzy phrase match (confidence = 0.50)**
   - For anchor phrases only: if a phrase match fails exact substring, attempt token-level Jaccard similarity with a threshold of 0.75.
   - This catches reordered phrases like "contract for munitions" matching "munitions contract".
   - Higher computational cost; only run if levels 1 and 2 produce zero matches.

**Keyword index structure:**
- At startup, build an inverted index: `{keyword_token -> list[theme_id]}` from all primary keywords across all 70 themes.
- For each incoming UER, tokenize `text_primary`, look up each token in the inverted index, collect candidate theme IDs, then run the full match logic (anchor phrases, negatives) only for candidates. This avoids scanning all 70 themes for every record.

### 3.2 CAMEO Code Routing (GDELT Sources Only)

For UERs originating from GDELT Events (`source = "gdelt_event"`), the CAMEO
code provides a structured classification path that bypasses keyword matching.

**Routing logic (defined in `docs/gdelt_cameo_mapping.md`):**

1. **Root code routing**: Map the 2-digit CAMEO root code (01-20) to candidate sleeves using the mapping table. For example:
   - Root 14 (PROTEST) -> `GEO_PRO_031`, `GEO_PRO_032` (protest themes)
   - Root 19 (USE CONVENTIONAL MILITARY FORCE) -> `DEF_MUN_001`, `DEF_MIS_002`, `DEF_NAV_006`, etc.
   - Root 17 (COERCE) -> `GEO_SAN_020` and other sanctions/coercion themes

2. **Sub-code refinement**: Where the full 3-4 digit CAMEO code provides higher specificity, narrow the candidate set. For example:
   - 0831 (Provide military aid) -> `DEF_MUN_001` specifically
   - 1721 (Impose economic sanctions) -> `GEO_SAN_020` specifically

3. **GKG theme cross-reference**: If the same GDELT record also has a GKG entry (joined on `GLOBALEVENTID` or matching `SOURCEURL`), use the GKG theme tags to confirm or disambiguate the CAMEO routing. A CAMEO 19x code with a co-occurring GKG theme of `MILITARY` and `ENV_OIL` routes to both defense and energy-chokepoint themes.

4. **Relevance weight gating**: CAMEO root codes with LOW relevance weight (as defined in the mapping doc) only generate classifications when accompanied by geographic relevance (event occurs in a monitored region) or when the Goldstein scale magnitude exceeds 5.0.

**Confidence assignment for CAMEO routing:**
- HIGH relevance root code with matching sub-code: confidence = 0.95
- HIGH relevance root code without sub-code refinement: confidence = 0.85
- MEDIUM relevance root code: confidence = 0.70
- LOW relevance root code (with geographic or Goldstein gate): confidence = 0.55

### 3.3 Geographic Routing

Geographic routing assigns a `region` to each UER and can independently trigger
theme activation for spatially-defined themes (chokepoint disruptions, port
stress, regional conflict escalation).

**Three geographic resolution methods:**

1. **FIPS code mapping (GDELT native)**
   - GDELT provides FIPS 10-4 country and ADM1 codes.
   - Map FIPS codes to the system's region taxonomy:
     - Middle East: FIPS countries `IS`, `SY`, `IZ`, `IR`, `SA`, `YM`, `AE`, `KU`, `QA`, `BH`, `OM`, `JO`, `LE`
     - Eastern Europe: `UP` (Ukraine), `RS` (Russia), `BO` (Belarus), `PL`, `RO`, `BU`, `LH`, `LG`, `EN`
     - East Asia: `CH` (China), `TW`, `JA`, `KS`, `KN`
     - South Asia: `IN`, `PK`, `BG` (Bangladesh), `CE` (Sri Lanka)
     - Horn of Africa: `SO`, `ET`, `ER`, `DJ`
     - West Africa: `NI` (Nigeria), `ML`, `BF` (Burkina Faso), `NG` (Niger)
   - Unmapped FIPS codes default to `region = "other"`.

2. **Bounding box matching (AIS and coordinate-bearing records)**
   - For any UER with `geo_lat` and `geo_lon`, test membership in the bounding boxes from `docs/chokepoint_coordinates.md`.
   - Use the "wide" bounding boxes for initial region assignment.
   - Use the "tight" bounding boxes for chokepoint-specific theme activation:
     - Point inside Strait of Hormuz tight box -> activates `SHP_CHK_041` (Hormuz chokepoint theme)
     - Point inside Bab el-Mandeb tight box -> activates `SHP_CHK_042` (Red Sea chokepoint theme)
     - And so on for all 10 monitored chokepoints.
   - Bounding box test is O(1) per box (simple lat/lon range check); with 10 chokepoints + 6 port clusters + 5 regional boxes = 21 total boxes, this is negligible cost.

3. **NER-based geo inference (RSS sources)**
   - For RSS items where no coordinates exist, extract location entities from NER.
   - Resolve entity names to coordinates using a static gazetteer (GeoNames top-10000 cities + all country names/demonyms).
   - If multiple locations are mentioned, use the first location in the headline (`text_primary`) as the primary geo assignment. Locations mentioned only in the summary (`text_secondary`) are recorded in metadata but do not override the primary assignment.

**Region assignment hierarchy:**
1. If the UER falls inside a chokepoint tight bounding box, assign region = the chokepoint ID (e.g., `"hormuz"`, `"bab_el_mandeb"`).
2. Else if the UER falls inside a port cluster box, assign region = the port cluster ID (e.g., `"india_west"`, `"singapore"`).
3. Else if FIPS code maps to a defined region, assign region = the FIPS-derived region name.
4. Else if NER-based inference produced a country, assign region = the country ISO code.
5. Else assign region = `"global"`.

### 3.4 Multi-Theme Co-Activation Handling

A single UER can legitimately match multiple themes. For example, a headline
about "Houthi missile strike on oil tanker in Red Sea" should activate
`DEF_MIS_002` (Missile Defense), `SHP_CHK_042` (Red Sea chokepoint), and
`ENR_OIL_050` (Oil Supply Disruption).

**Co-activation rules:**

1. **Maximum co-activation limit**: A single UER may activate at most 4 themes. If more than 4 themes match, keep the 4 with highest classification confidence.

2. **Conflict suppression within sleeve**: If two themes within the same sleeve/sub-sleeve both match, keep only the one with higher confidence unless both have confidence >= 0.80, in which case both are retained. This prevents a single event from double-counting within a sleeve.

3. **Cross-sleeve co-activation is normal and expected**: A shipping event that also triggers a defense theme is legitimate multi-theme activation. No suppression across sleeves.

4. **Confidence aggregation**: When multiple routing paths (keyword + CAMEO + geographic) all point to the same theme, the final confidence for that theme is: `1 - product(1 - c_i for each path i)`. This gives diminishing returns but always increases confidence when multiple independent signals agree.

**Output of Classification Layer:**
For each incoming UER, emit one `ClassifiedEvent` per activated theme:

```
ClassifiedEvent:
    record_id:            str         # From UER
    theme:                str         # Theme ID, e.g., "DEF_MUN_001"
    subtheme:             str         # Sub-sleeve, e.g., "Munitions"
    region:               str         # From geographic routing
    classification_confidence: float  # 0.0-1.0
    classification_method: str        # "keyword_anchor" | "keyword_primary" | "keyword_fuzzy" | "cameo_route" | "geo_route" | "multi_path"
    source:               str         # Inherited from UER
    timestamp:            datetime    # Inherited from UER
    goldstein_scale:      float | None
    tone:                 float | None
    entities:             list[str]
    source_url:           str | None
    raw_metadata:         dict
```

---

## 4. Scoring Layer

The Scoring Layer converts each `ClassifiedEvent` into three quantitative scores:
**intensity**, **novelty**, and **acceleration**. These are the core numeric
fields that populate `EventFeatureRow.values`.

### 4.1 Intensity Computation

Intensity measures the current magnitude of coverage/activity for a
(theme, region) pair over a rolling window.

**Components (weighted sum):**

| Component | Weight | Source | Computation |
|-----------|--------|--------|-------------|
| Article volume | 0.30 | All sources | Count of `ClassifiedEvent` records for this (theme, region) in the scoring window (24 hours for daily, 7 days for weekly). Normalized by dividing by the 90-day rolling median count for the same (theme, region). A value of 1.0 = median activity; 2.0 = double the usual volume. |
| Goldstein magnitude | 0.25 | GDELT only | Absolute value of the average Goldstein scale across all GDELT-sourced events for this (theme, region) in the window. Normalized to [0, 1] by dividing by 10.0 (the max Goldstein magnitude). For non-GDELT events, use the ACLED-derived proxy Goldstein or null (excluded from average). |
| Tone severity | 0.20 | GDELT GKG | Average tone of GKG records. Tone is on a -100 to +100 scale; more negative = more severe. Transform: `tone_severity = clip(-tone / 20, 0, 1)`. A tone of -20 maps to 1.0 (maximum severity); a tone of 0 maps to 0.0. |
| Source diversity | 0.15 | All sources | Count of distinct source domains that contributed events for this (theme, region) in the window. Normalized: `min(distinct_sources / 5, 1.0)`. Rationale: a theme covered by 5+ independent sources is fully corroborated; fewer sources means lower confidence. |
| Fatality weight | 0.10 | ACLED only | Sum of reported fatalities for this (theme, region) in the window. Log-transformed: `min(log2(1 + fatalities) / 10, 1.0)`. Only non-zero for conflict/violence themes. |

**Final intensity** = weighted sum of components, clipped to [0, 1].

For themes where certain components are unavailable (e.g., fatalities for a monetary policy theme), the weights of available components are renormalized to sum to 1.0.

### 4.2 Novelty Computation

Novelty measures whether the current event is a fresh impulse or decaying
repetition of old news. This is critical for distinguishing actionable signals
from stale hype.

**Algorithm: Exponential Decay with Spike Detection**

1. **Maintain a (theme, region) history buffer**: a rolling 90-day list of daily intensity values.

2. **Compute the novelty spike indicator**:
   - `intensity_today` = today's intensity score (from 4.1)
   - `intensity_ewm` = exponentially weighted mean of intensity over the prior 14 days (halflife = 3 days)
   - `intensity_residual` = `intensity_today - intensity_ewm`
   - `residual_std` = standard deviation of the residual series over the prior 60 days
   - `novelty_z` = `intensity_residual / max(residual_std, 0.01)` (floored to avoid division by near-zero)

3. **Map z-score to novelty**:
   - `novelty_z >= 3.0` -> novelty = 1.0 (strong fresh impulse)
   - `novelty_z >= 2.0` -> novelty = 0.8
   - `novelty_z >= 1.0` -> novelty = 0.5
   - `novelty_z >= 0.0` -> novelty = 0.2 (above average but not novel)
   - `novelty_z < 0.0` -> novelty = 0.0 (decaying or below-average coverage)

4. **Headline deduplication boost**: If > 50% of today's articles for this (theme, region) have title similarity > 0.85 with articles from the previous 3 days (measured by trigram Jaccard on titles), apply a novelty penalty: `novelty *= 0.5`. This catches the common pattern where the same story is recirculated across outlets without new information.

**Intuition**: A sudden surge in coverage that departs from the recent trend is novel. Sustained high coverage that tracks the exponential mean is continuation (low novelty). Declining coverage is decay (zero novelty).

### 4.3 Acceleration Computation

Acceleration measures the rate of change in intensity, capturing whether an event
is escalating, stable, or de-escalating.

**Algorithm:**

1. **Compute daily intensity time series** for (theme, region) over a rolling 28-day window.

2. **Week-over-week change**:
   - `intensity_this_week` = mean of daily intensity for the most recent 7 days
   - `intensity_last_week` = mean of daily intensity for the 7 days prior to that
   - `raw_acceleration` = `intensity_this_week - intensity_last_week`

3. **Normalize to [-1, 1]**:
   - `acceleration = clip(raw_acceleration / max(intensity_last_week, 0.05), -1, 1)`
   - Division by last week's intensity makes acceleration relative (a jump from 0.1 to 0.3 is more significant than from 0.5 to 0.7).
   - Floor the denominator at 0.05 to prevent extreme values when last week's intensity was near zero.

4. **Interpretation**:
   - `acceleration > 0.5`: Rapid escalation. Signal to experts that this theme is gaining momentum.
   - `acceleration` in `[-0.2, 0.2]`: Stable. The event is neither growing nor fading.
   - `acceleration < -0.5`: Rapid de-escalation. The event impulse is decaying fast.

### 4.4 Source Diversity Weighting

Source diversity is already a component of intensity (section 4.1), but it also
serves as a standalone confidence multiplier applied to all three scores.

**Computation:**

- `n_sources` = count of distinct `(source, source_domain)` pairs contributing to this (theme, region) in the scoring window.
- `diversity_weight`:
  - 1 source: 0.50 (single-source; might be noise or a scoop)
  - 2 sources: 0.70
  - 3-4 sources: 0.85
  - 5+ sources: 1.00 (fully corroborated)

**Application**: After computing intensity, novelty, and acceleration, multiply each by `diversity_weight` to produce the final weighted scores. This means a single-source event will never score above 0.50 intensity, ensuring the system does not overreact to unconfirmed reports.

Exception: ACLED events are pre-corroborated (human-coded from multiple sources), so ACLED-only events receive a floor diversity weight of 0.85 regardless of the source count.

---

## 5. Aggregation Layer

The Scoring Layer produces daily, per-event scored records. The Aggregation Layer
rolls these up into weekly `EventFeatureRow` objects grouped by (theme, region).

### 5.1 Temporal Aggregation (Daily -> Weekly)

**Aggregation window**: Monday 00:00 UTC through Sunday 23:59 UTC, matching the
system's weekly rebalance cadence.

**Robust statistics (resistant to outlier days):**

| Field | Aggregation Method | Rationale |
|-------|-------------------|-----------|
| `event_intensity` | Trimmed mean of 7 daily intensities (trim 1 highest, 1 lowest from the 7 values; mean of remaining 5). If fewer than 5 days have data, use the median. | Trimmed mean resists a single outlier day (e.g., a one-day headline spike) from dominating the weekly score. |
| `event_novelty` | Maximum daily novelty in the week. | Novelty is an onset detector; we care about whether a fresh impulse occurred at any point during the week, not the average novelty. |
| `event_acceleration` | Computed directly at the weekly level (section 4.3 already uses weekly windows), not aggregated from daily. | Avoids double-smoothing. |

**Missing days**: If a (theme, region) pair has zero events on a given day, that
day's intensity = 0.0 and novelty = 0.0. These zeros participate in the weekly
aggregation (they represent genuine absence of coverage, not missing data).

### 5.2 Spatial Aggregation

Three levels of spatial rollup, computed in parallel:

1. **Per-chokepoint**: For the 10 monitored chokepoints, aggregate all events whose region matches the chokepoint ID. This feeds `ShippingChokePointExpert`.

2. **Per-region**: For the ~10 defined regions (Middle East, Eastern Europe, East Asia, etc.), aggregate all events whose region maps to the parent region. This feeds `ConflictEscalationExpert`.

3. **Per-port-cluster**: For the 6 port clusters, aggregate AIS-derived events and shipping news events localized to those ports. This feeds the port-stress sub-signal of `ShippingChokePointExpert`.

**Rollup method**: When aggregating from fine-grained (chokepoint) to coarse-grained (region), use the maximum intensity across constituent chokepoints/ports for that region. Rationale: a regional conflict score should reflect the hottest sub-region, not be diluted by averaging in quiet sub-regions.

### 5.3 Theme-Level Rollup

Each theme ID (e.g., `DEF_MUN_001`) produces one `EventFeatureRow` per region per
week. At the sleeve level, a rollup is also computed:

- `sleeve_intensity` = max of `event_intensity` across all themes in the sleeve for that region.
- `sleeve_novelty` = max of `event_novelty` across all themes in the sleeve.
- `sleeve_acceleration` = intensity-weighted average of theme-level accelerations within the sleeve.

Sleeve-level rollups are stored as `EventFeatureRow` records with `theme = "{SLEEVE}_ROLLUP"` (e.g., `"DEF_ROLLUP"`, `"SHP_ROLLUP"`).

### 5.4 Output Schema

The final aggregated record is written as an `EventFeatureRow`:

```python
EventFeatureRow(
    as_of_date=week_end_date,       # Sunday of the aggregation week
    theme="DEF_MUN_001",            # Theme ID from taxonomy
    subtheme="Munitions",           # Sub-sleeve label
    region="middle_east",           # Region from geographic routing
    values={
        "event_intensity": 0.72,    # Trimmed mean of daily intensities
        "event_novelty": 0.85,      # Max daily novelty in the week
        "event_acceleration": 0.34, # Week-over-week intensity change
    },
    metadata={
        "source_count": 8,                    # Distinct sources contributing
        "article_count": 47,                  # Total classified events in the week
        "top_cameo_codes": ["190", "1721"],   # Most frequent CAMEO codes
        "top_entities": ["Iran", "IRGC", "Strait of Hormuz"],
        "classification_methods": ["cameo_route", "keyword_anchor"],
        "diversity_weight": 1.0,
        "daily_intensities": [0.6, 0.7, 0.8, 0.75, 0.65, 0.7, 0.8],
    },
)
```

---

## 6. Output Layer

### 6.1 Impulse Detection (Onset, Continuation, Decay)

Each weekly `EventFeatureRow` is tagged with an impulse phase to guide expert
model behavior and the rebalance state machine.

**Phase classification rules (evaluated in order):**

| Phase | Condition | Meaning |
|-------|-----------|---------|
| `onset` | `event_novelty >= 0.6` AND `event_intensity >= 0.3` AND `event_acceleration > 0.2` | A new event impulse has begun. Experts should increase activation probability; the portfolio optimizer should prepare for a potential position change. |
| `escalation` | `event_intensity >= 0.5` AND `event_acceleration > 0.2` AND novelty < 0.6 | The event is growing in intensity but is no longer novel (continuation of an ongoing story with increasing coverage). |
| `sustained` | `event_intensity >= 0.4` AND `abs(event_acceleration) <= 0.2` | The event is at a stable elevated level. Coverage is persistent but neither growing nor shrinking. |
| `decay` | `event_intensity >= 0.1` AND `event_acceleration < -0.2` | The event is losing coverage. The signal is fading; experts should reduce activation probability. |
| `baseline` | `event_intensity < 0.1` | No meaningful event activity for this (theme, region). |

The impulse phase is stored in `metadata["impulse_phase"]` on the `EventFeatureRow`.

### 6.2 Mapping to ExpertContext.event_features

Each expert model receives an `ExpertContext` with an `event_features` dict
populated from the relevant `EventFeatureRow` objects. The routing is determined
by the expert's family and localization type.

**Routing rules:**

| Expert Family | Localization | EventFeatureRow Selection | Key Mappings |
|---------------|-------------|---------------------------|--------------|
| `ConflictEscalationExpert` | `REGION` | All rows where theme starts with `DEF_` or `GEO_` and region matches the expert's target region | `escalation_intensity` = `event_intensity`, `escalation_acceleration` = `event_acceleration`, `sanctions_mentions` = count of `GEO_SAN_*` rows, `spillover_flag` = 1.0 if both conflict AND energy themes are active in the same region |
| `ShippingChokePointExpert` | `CHOKEPOINT` / `PORT_CLUSTER` | All rows where theme starts with `SHP_` and region matches the expert's chokepoint or port cluster | `chokepoint_intensity` = `event_intensity`, `incident_novelty` = `event_novelty`, `port_stress` = intensity of port-cluster rollup row |
| `RatesPolicyExpert` | `COUNTRY` | All rows where theme starts with `MON_` (monetary policy themes) and region matches the expert's country | `cb_language_intensity` = `event_intensity`, `hawkish_shock_flag` = 1.0 if novelty > 0.6 and specific hawkish keywords in metadata |
| `MarketPricingExpert` | `COMMODITY` | Sleeve-level rollup rows (`*_ROLLUP`) | Uses sleeve rollup intensities as cross-theme context signals |
| `CryptoRegimeExpert` | Global | All rows with `region = "global"` or `theme` in crypto/DeFi themes | `risk_on_signal` / `risk_off_signal` derived from aggregate event intensity direction |

**Population procedure (runs weekly, before expert prediction):**

1. Query all `EventFeatureRow` records for the current week.
2. For each registered expert instance, filter rows by the routing rules above.
3. Flatten the matching rows into the `event_features` dict:
   - If multiple rows match (e.g., 3 conflict themes active in "middle_east"), aggregate: use max intensity, max novelty, sum article counts.
4. Inject the `event_features` dict into the `ExpertContext` alongside the market `feature_row`.
5. The expert's `predict()` method receives the fully populated `ExpertContext`.

### 6.3 Rebalance State Machine Integration

The impulse phase drives transitions in the rebalance state machine:

- **`onset` event detected**: The state machine transitions from `MONITORING` to `SIGNAL_ACTIVE`. This enables the portfolio optimizer to evaluate whether a position change is warranted.
- **`escalation` phase persists for 2+ weeks**: The state machine escalates to `CONVICTION_HIGH`, which unlocks the derivatives overlay (protective puts, event-driven option structures).
- **`decay` phase detected after `sustained` or `escalation`**: The state machine transitions to `UNWIND_CANDIDATE`. The portfolio optimizer begins reducing exposure to the affected theme over 1-2 weeks (not instantly, to avoid whipsawing on a brief coverage dip).
- **`baseline` for 3+ consecutive weeks**: The state machine returns to `MONITORING`. All event-driven positions for this (theme, region) are fully unwound.

---

## 7. Data Flow Diagram

```
                              INGESTION LAYER
    ┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐
    │   GDELT     │  │  RSS Feeds  │  │  ACLED   │  │ aisstream │  │   OFAC /  │
    │ Events+GKG  │  │ AP/BBC/AJ/  │  │ Conflict │  │   .io     │  │  Open-    │
    │  (15 min)   │  │ Maritime/CB │  │ (weekly) │  │  (stream) │  │ Sanctions │
    │             │  │  (10 min)   │  │          │  │           │  │  (6 hrs)  │
    └──────┬──────┘  └──────┬──────┘  └────┬─────┘  └─────┬─────┘  └─────┬─────┘
           │                │              │              │              │
           │  Dedup (Bloom) │  Dedup (URL) │ Dedup (ID)  │ Dedup (MMSI) │ Diff (snapshot)
           │                │              │              │              │
           ▼                ▼              ▼              ▼              ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                        NORMALIZATION LAYER                                   │
    │                                                                              │
    │  Source-specific parsers --> Unified Event Record (UER)                       │
    │  - Text extraction (headline, summary, event description)                    │
    │  - Entity extraction (actors, orgs, countries)                                │
    │  - Geo normalization (FIPS -> ISO, NER -> gazetteer, lat/lon)                │
    │  - Goldstein/tone passthrough (GDELT) or proxy estimation (ACLED)            │
    │  - Quality checks (timestamp, text length, geo validity)                     │
    │                                                                              │
    └───────────────────────────────────┬──────────────────────────────────────────┘
                                        │
                                        ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                        CLASSIFICATION LAYER                                  │
    │                                                                              │
    │  Four parallel routing paths:                                                │
    │                                                                              │
    │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
    │  │   Keyword    │ │    CAMEO     │ │  Geographic  │ │   ACLED      │        │
    │  │  Matching    │ │   Routing    │ │   Routing    │ │  Event Type  │        │
    │  │             │ │  (GDELT)     │ │ (FIPS/bbox/  │ │   Mapping    │        │
    │  │ Anchor phrase│ │ Root -> sub  │ │    NER)      │ │              │        │
    │  │ Primary kw   │ │ + relevance  │ │              │ │              │        │
    │  │ Fuzzy match  │ │   weight     │ │ Chokepoint   │ │              │        │
    │  └──────┬───────┘ └──────┬───────┘ │ Port cluster │ └──────┬───────┘        │
    │         │                │         │ Region       │        │                │
    │         │                │         └──────┬───────┘        │                │
    │         │                │                │                │                │
    │         └────────┬───────┴────────┬───────┴────────────────┘                │
    │                  │                │                                          │
    │                  ▼                ▼                                          │
    │         Co-activation resolver (max 4 themes, cross-sleeve OK)              │
    │         Confidence merge: 1 - prod(1 - c_i)                                │
    │                  │                                                           │
    │                  ▼                                                           │
    │         ClassifiedEvent (one per theme activation)                           │
    │                                                                              │
    └───────────────────────────────────┬──────────────────────────────────────────┘
                                        │
                                        ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                          SCORING LAYER                                       │
    │                                                                              │
    │  Per (theme, region, day):                                                   │
    │                                                                              │
    │  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐     │
    │  │     INTENSITY      │  │      NOVELTY       │  │   ACCELERATION     │     │
    │  │                    │  │                    │  │                    │     │
    │  │ 0.30 article vol   │  │ EWM residual       │  │ WoW intensity      │     │
    │  │ 0.25 |Goldstein|   │  │ z-score mapping    │  │ change, normalized │     │
    │  │ 0.20 tone severity │  │ Headline dedup     │  │ by prior week      │     │
    │  │ 0.15 source divers │  │ penalty            │  │                    │     │
    │  │ 0.10 fatalities    │  │                    │  │ Range: [-1, 1]     │     │
    │  │                    │  │ Range: [0, 1]      │  │                    │     │
    │  │ Range: [0, 1]      │  │                    │  │                    │     │
    │  └─────────┬──────────┘  └─────────┬──────────┘  └─────────┬──────────┘     │
    │            │                       │                       │                │
    │            └───────── * diversity_weight ──────────────────┘                │
    │                        (1 src=0.5 ... 5+=1.0)                               │
    │                                                                              │
    └───────────────────────────────────┬──────────────────────────────────────────┘
                                        │
                                        ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                        AGGREGATION LAYER                                     │
    │                                                                              │
    │  Daily scores --> Weekly EventFeatureRow                                     │
    │                                                                              │
    │  Temporal:   intensity = trimmed mean (drop 1 high, 1 low)                  │
    │              novelty   = max over the week                                   │
    │              acceleration = direct weekly computation                        │
    │                                                                              │
    │  Spatial:    Per-chokepoint  (10 chokepoints)                                │
    │              Per-region      (~10 regions)                                    │
    │              Per-port-cluster (6 port clusters)                               │
    │              Rollup: max intensity across sub-regions                        │
    │                                                                              │
    │  Theme:      Per-theme-ID rows + sleeve-level rollup rows                   │
    │                                                                              │
    └───────────────────────────────────┬──────────────────────────────────────────┘
                                        │
                                        ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                          OUTPUT LAYER                                        │
    │                                                                              │
    │  ┌──────────────────────┐     ┌──────────────────────────────────────┐       │
    │  │  Impulse Detection   │     │  Expert Context Population          │       │
    │  │                      │     │                                      │       │
    │  │  onset / escalation  │     │  ConflictExpert  <-- DEF_*, GEO_*   │       │
    │  │  sustained / decay   │     │  ShippingExpert  <-- SHP_*          │       │
    │  │  baseline            │     │  RatesExpert     <-- MON_*          │       │
    │  │                      │     │  MarketExpert    <-- *_ROLLUP       │       │
    │  └──────────┬───────────┘     │  CryptoExpert    <-- global         │       │
    │             │                 └───────────────┬──────────────────────┘       │
    │             │                                 │                              │
    │             ▼                                 ▼                              │
    │  ┌──────────────────────────────────────────────────────────────────┐        │
    │  │               Rebalance State Machine                           │        │
    │  │                                                                  │        │
    │  │  MONITORING --> SIGNAL_ACTIVE --> CONVICTION_HIGH                │        │
    │  │       ^              │                  │                        │        │
    │  │       │              ▼                  ▼                        │        │
    │  │       │         UNWIND_CANDIDATE    Derivatives                  │        │
    │  │       │              │              Overlay                      │        │
    │  │       └──────────────┘              Activation                   │        │
    │  └──────────────────────────────────────────────────────────────────┘        │
    │                                                                              │
    └──────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Latency Budget

| Stage | Target Latency | Notes |
|-------|---------------|-------|
| Ingestion (GDELT file download + parse) | < 60 seconds | Largest files are ~50 MB compressed |
| Ingestion (RSS poll cycle) | < 5 seconds per feed | 12 feeds * 5s = 60s total if sequential; parallelize to < 15s |
| Normalization (per record) | < 10 ms | Simple field mapping and NER (cached model) |
| Classification (per UER) | < 5 ms | Inverted index lookup + rule evaluation; no ML model in the hot path |
| Scoring (per theme-region-day) | < 50 ms | Requires history buffer lookup (in-memory or Redis) |
| Aggregation (full weekly rollup) | < 30 seconds | Batch computation over all (theme, region) pairs |
| **End-to-end (ingestion to EventFeatureRow)** | **< 5 minutes** | Well within the 15-min GDELT cadence |

## Appendix B: Storage Estimates

| Data | Retention | Estimated Size |
|------|-----------|----------------|
| Raw GDELT files | 5 years | ~500 GB (compressed) |
| Unified Event Records | 2 years | ~50 GB (structured, indexed) |
| ClassifiedEvents | 2 years | ~20 GB |
| Daily scored records | 5 years | ~5 GB |
| Weekly EventFeatureRows | Indefinite | ~500 MB (70 themes * 20 regions * 260 weeks * ~140 bytes) |
| AIS snapshots | 1 year | ~10 GB |
| Sanctions snapshots | Indefinite | ~2 GB |

## Appendix C: Failure Modes and Mitigations

| Failure | Impact | Mitigation |
|---------|--------|------------|
| GDELT delayed >1 hour | Missing 15-min updates; intensity scores may be stale for the period | RSS feeds provide partial coverage; the weekly aggregation smooths over short gaps. Log gap and flag affected EventFeatureRows in metadata. |
| RSS feed URL changes | Loss of one news source | Circuit breaker alerts ops. Source diversity weight naturally downgrades themes that lose a source. |
| aisstream.io disconnect | Loss of real-time vessel tracking | AIS anomalies only generate UERs for threshold breaches; a gap means no anomaly UERs, which is safe (fails to baseline, not to false positive). |
| ACLED data late >2 weeks | Stale conflict ground-truth | ACLED is a training/confirmation source, not a real-time signal. GDELT and RSS cover the real-time path. |
| Keyword taxonomy update | New themes not detected; old themes may false-positive | Taxonomy is versioned. On update: rebuild inverted index (< 1 second), re-score the last 7 days of UERs against the new taxonomy, and log theme-level classification-rate changes. |
| Goldstein/tone field missing | Intensity score degradation | Renormalize component weights to exclude missing components. This is already specified in section 4.1. |
