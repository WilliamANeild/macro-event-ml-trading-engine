# Data Storage and Polling Architecture

This document defines the storage layout, ingestion schedule, pipeline stages,
and operational patterns for the macro-event-driven trading system's data layer.

---

## 1. Storage Architecture

### 1.1 Directory Structure

```
data/
  raw/                          # Immutable ingested files, partitioned by source and date
    gdelt/
      csv/YYYY/MM/DD/           # Raw GDELT export CSVs (15-min segments)
      doc_api/YYYY/MM/DD/       # GDELT DOC API JSON responses
    rss/
      YYYY/MM/DD/               # Deduplicated RSS items as NDJSON, one file per poll cycle
    ais/
      YYYY/MM/DD/               # AIS position reports, hourly Parquet rolls
    sanctions/
      YYYY/MM/DD/               # OFAC + OpenSanctions snapshots (JSON)
    acled/
      YYYY/                     # Weekly ACLED CSV drops
    fred/
      YYYY/MM/                  # FRED series JSON responses, monthly rollups
    yahoo/
      YYYY/MM/                  # Yahoo Finance OHLCV, monthly rollups
    calendars/
      central_bank_meetings.json  # Static JSON, updated annually

  normalized/                   # Source-aligned but schema-standardized tables
    events/                     # All event sources merged into common EventRecord Parquet
      YYYY/MM/                  # Monthly partitioned
    prices/                     # OHLCV Parquet, one file per symbol per month
      YYYY/MM/
    macro/                      # FRED series, wide-format Parquet
      YYYY/
    sanctions/                  # Flattened entity Parquet with effective dates
    ais/                        # Vessel tracks, Parquet partitioned by region+day
      YYYY/MM/DD/

  features/                     # Computed features, model-ready
    market/                     # Price-derived features (returns, vol, momentum)
      YYYY/MM/
    event/                      # Event-derived features (intensity, novelty, decay)
      YYYY/MM/
    combined/                   # Joined feature table aligned to daily index
      YYYY/MM/

  cache/                        # CacheManager working directory (existing)
    *.parquet                   # MD5-keyed Parquet files (current behavior)

  meta/                         # Bookkeeping
    ingestion_log.jsonl         # Append-only log of every poll: source, timestamp, status, rows
    dedup_index.db              # SQLite database for event deduplication (hash -> first_seen)
    source_health.jsonl         # Rolling health-check log
```

### 1.2 File Formats by Source

| Source | Raw Format | Normalized Format | Rationale |
|---|---|---|---|
| GDELT CSV | CSV (as-is from GDELT) | Parquet | Columnar compression; raw CSVs are large and repetitive |
| GDELT DOC API | JSON | Parquet | Structured article metadata normalizes well to columnar |
| RSS feeds | NDJSON (one JSON object per article) | Parquet (merged into events table) | NDJSON allows append-friendly raw storage |
| AIS WebSocket | Parquet (hourly roll from in-memory buffer) | Parquet (region-partitioned) | Binary vessel positions are already tabular |
| OFAC/OpenSanctions | JSON (API response snapshots) | Parquet (entity-level flat table) | Track entity additions/removals over time |
| ACLED | CSV | Parquet | Standard tabular conflict data |
| FRED | JSON (series observations) | Parquet (wide-format, one column per series) | Align with existing FREDDataSource patterns |
| Yahoo Finance | Parquet (via existing CacheManager) | Parquet (OHLCV per symbol) | Already Parquet; just reorganize into normalized layout |
| Central bank calendars | JSON | JSON (static, no normalization needed) | Low volume, rarely changes |

### 1.3 Retention Policies

| Tier | Contents | Retention | Notes |
|---|---|---|---|
| `raw/` | Original ingested files | **2 years** | Needed for pipeline replay and audit; compress after 90 days with gzip |
| `normalized/` | Schema-standardized tables | **5 years** | Primary analytical store; these power backtests |
| `features/` | Computed feature tables | **1 year rolling + rebuild on demand** | Recomputable from normalized; keep recent for fast iteration |
| `cache/` | CacheManager MD5-keyed files | **30 days TTL** | Ephemeral acceleration layer; stale data must expire |
| `meta/` | Ingestion logs, dedup index | **Indefinite** | Small footprint; critical for debugging |

Disk budget estimate at full scale (164 instruments, all sources active):
- `raw/`: ~50 GB/year (GDELT dominates at ~30 GB/year; AIS ~15 GB/year)
- `normalized/`: ~20 GB/year (Parquet compression ~60-70% reduction from raw)
- `features/`: ~2 GB/year (daily granularity, 164 instruments, ~50 features each)

### 1.4 Extending the Existing CacheManager

The current `CacheManager` uses MD5-hashed keys and flat Parquet files in `data/cache/`.
It stays as-is for its current consumers (YahooDataSource, FREDDataSource) but gains
two capabilities:

**A. TTL-aware reads.** `CacheManager.has(name)` should check file modification time
against a configurable TTL (default 24h for prices, 7d for macro series). When the
file is older than the TTL, `has()` returns `False`, forcing a re-fetch.

**B. Namespace prefixes.** Add an optional `namespace` parameter to the constructor.
When set, the cache directory becomes `data/cache/{namespace}/` rather than flat.
This prevents collision when new sources (GDELT, AIS, etc.) adopt the same pattern.
The existing default (`namespace=None`) preserves backward compatibility.

The `CacheManager` remains the **read acceleration layer**. It is not the system of
record. The `raw/` and `normalized/` directories are the system of record. The cache
is populated either by direct API calls (existing pattern) or by a read-through from
the normalized store (new pattern for backtest replays).

---

## 2. Polling / Ingestion Schedule

### 2.1 Source Schedule

| Source | Interval | Method | Window |
|---|---|---|---|
| GDELT CSV export | Every 15 min | HTTP GET to `data.gdeltproject.org/gdeltv2/lastupdate.txt` then fetch listed CSV | 24/7 |
| GDELT DOC API | Every 15 min | HTTP GET with query parameters | 24/7 |
| RSS - AP, BBC, Al Jazeera | Every 5 min | HTTP GET, parse XML/Atom | 24/7 |
| RSS - maritime sources | Every 10 min | HTTP GET, parse XML | 24/7 |
| RSS - central banks | Every 10 min | HTTP GET, parse XML | Business hours + 2h buffer |
| AIS (aisstream.io) | Continuous | WebSocket persistent connection | 24/7 |
| OFAC/OpenSanctions | Every 6 hours | HTTP GET (bulk download) | 4 times daily: 00:00, 06:00, 12:00, 18:00 UTC |
| ACLED | Weekly (Monday 02:00 UTC) | HTTP GET (bulk CSV) | Once per week |
| FRED | Daily at 09:00 ET | HTTP GET per series via fredapi | Business days |
| Yahoo Finance | Daily at 17:30 ET (after market close) | yfinance API via existing YahooDataSource | Business days |
| Central bank calendars | Annually (Jan 1) + on-demand | Manual update or scrape | Static |

### 2.2 Error Handling and Retry Logic

All pollers follow a common retry envelope:

```
Attempt 1: immediate
Attempt 2: wait 30 seconds
Attempt 3: wait 2 minutes
Attempt 4: wait 10 minutes
Attempt 5 (final): wait 30 minutes
```

After 5 failures the poller enters **degraded mode**: it logs an alert to
`meta/source_health.jsonl`, continues operating with stale data, and retries at
the next scheduled interval. It does not crash the pipeline.

**Source-specific rules:**
- **AIS WebSocket**: on disconnect, reconnect immediately with exponential backoff
  (1s, 2s, 4s, 8s, cap at 60s). Buffer the last 5 minutes of messages in memory
  so a brief disconnect does not create gaps.
- **GDELT CSV**: if a 15-min file is missing (404), skip it. GDELT occasionally
  has gaps; the system logs the gap and moves on. Do not retry 404s.
- **FRED/Yahoo**: rate-limit-aware. See section 2.3.
- **RSS**: if a single feed fails, the others continue independently. Do not let
  one broken feed block the cycle.

### 2.3 Rate Limit Management

| Source | Known Limits | Strategy |
|---|---|---|
| GDELT CSV | None (public files) | No throttling needed |
| GDELT DOC API | ~60 requests/min | Token bucket: 1 request/second max |
| RSS feeds | Respect `Retry-After` / `429` headers | Adaptive backoff per feed |
| aisstream.io | Connection-based (1 concurrent connection per API key) | Single persistent connection; never open a second |
| OFAC | None (static file download) | No throttling needed |
| ACLED | API key rate limits (varies by tier) | Single weekly request; no concern |
| FRED | 120 requests/min per API key | Token bucket: 2 requests/second; batch series into single call when possible |
| Yahoo Finance | Unofficial; ~2000 requests/hour | Serialize symbol fetches with 200ms delay between; use bulk download endpoint for >20 symbols |

All HTTP clients set a `User-Agent` header identifying the system and include
contact information, per good-citizen crawling practices.

### 2.4 Deduplication Strategy

The same geopolitical event will appear in GDELT, multiple RSS feeds, and
potentially the GDELT DOC API simultaneously. Deduplication operates at two
levels:

**Level 1 -- Intra-source (raw ingestion).** Each raw record gets a content hash
computed from its core identity fields:
- GDELT: `GLOBALEVENTID`
- RSS: `SHA-256(feed_url + article_url + published_date)`
- GDELT DOC API: `SHA-256(url + title)`
- AIS: `MMSI + timestamp` (vessel ID + time, naturally unique)
- Sanctions: `entity_id + list_source + effective_date`

Hashes are checked against `meta/dedup_index.db` (SQLite, single writer). If
the hash exists, the record is dropped. The SQLite database stores hash, source,
and first-seen timestamp.

**Level 2 -- Cross-source (normalization).** During the raw-to-normalized
transformation, events from different sources that refer to the same real-world
occurrence are clustered. The clustering key is:
- Time window: events within +/- 6 hours
- Geographic overlap: same FIPS country code or within 200km
- Semantic similarity: TF-IDF cosine similarity > 0.6 on headline text

Clustered events are merged into a single `EventRecord` in the normalized store.
The record retains references to all contributing raw records (source + raw ID)
for provenance.

### 2.5 Health Monitoring

Each poller writes a heartbeat to `meta/source_health.jsonl` after every
successful cycle:

```json
{
  "source": "gdelt_csv",
  "timestamp": "2026-04-16T12:15:00Z",
  "status": "ok",
  "records_ingested": 4823,
  "latency_ms": 2340,
  "next_expected": "2026-04-16T12:30:00Z"
}
```

A lightweight monitor process reads this file and raises alerts when:
- A source misses 2 consecutive expected heartbeats.
- `records_ingested` drops below 10% of its 7-day rolling median (suggests
  upstream data drought, not a local failure).
- `latency_ms` exceeds 3x the 7-day p95 (suggests upstream degradation).

Alerts are written to a structured log. In production, these feed into whatever
alerting system is available (email, Slack webhook, etc.).

---

## 3. Data Pipeline Stages

### 3.1 Stage Overview

```
[External Sources]
       |
       v
  Stage 0: Raw Ingestion
       |  (pollers write to data/raw/, dedup at ingest)
       v
  Stage 1: Normalization
       |  (raw -> data/normalized/, cross-source dedup, schema alignment)
       v
  Stage 2: Feature Computation
       |  (normalized -> data/features/, per-source feature builders)
       v
  Stage 3: Feature Assembly
       |  (data/features/ -> data/features/combined/, temporal alignment)
       v
  [Model-Ready Feature Table]
       |
       v
  Stage 4: Expert Predictions -> MetaStacker -> Portfolio -> Backtest/Live
```

### 3.2 Stage 0: Raw Ingestion

Each source has a dedicated poller (or WebSocket listener) that:
1. Fetches data according to the schedule in section 2.1.
2. Writes the raw response verbatim to `data/raw/{source}/YYYY/MM/DD/`.
3. Computes per-record content hashes and checks the dedup index.
4. Logs the ingestion to `meta/ingestion_log.jsonl`.

No transformation happens here. The goal is an immutable, append-only archive
of exactly what the source returned.

### 3.3 Stage 1: Normalization

Normalization transforms raw source-specific formats into a common schema per
data category. There are three output categories:

**Events** (from GDELT, RSS, ACLED, sanctions changes):
```
EventRecord:
  event_id:        str         # System-generated UUID
  timestamp:       datetime    # When the event occurred (source time)
  ingested_at:     datetime    # When we first saw it
  source:          str         # "gdelt_csv", "rss_ap", "acled", etc.
  raw_ids:         list[str]   # References to raw records (for provenance)
  event_type:      str         # Normalized CAMEO code or taxonomy category
  headline:        str         # Article title or event description
  country_codes:   list[str]   # ISO-3166 alpha-2
  lat:             float|null
  lon:             float|null
  goldstein_scale: float|null  # GDELT-specific; null for non-GDELT sources
  tone:            float|null  # Average tone; null if unavailable
  entities:        list[str]   # Named entities extracted from text
  themes:          list[str]   # Maps to the system's theme taxonomy (energy, defense, shipping, etc.)
  severity:        float       # Normalized 0-1 severity score
```

**Prices** (from Yahoo Finance):
```
PriceRecord:
  symbol:    str
  date:      date
  open:      float
  high:      float
  low:       float
  close:     float
  adj_close: float
  volume:    int
```

**Macro** (from FRED):
```
MacroRecord:
  series_id:     str        # e.g., "VIXCLS"
  friendly_name: str        # e.g., "VIX" (from DEFAULT_SERIES mapping)
  date:          date
  value:         float
  frequency:     str        # "daily", "weekly", "monthly"
```

Normalization runs as a batch job triggered after each raw ingestion cycle
completes. For high-frequency sources (GDELT, RSS), normalization runs inline
within the same poller process to minimize latency.

### 3.4 Stage 2: Feature Computation

Feature builders consume normalized data and produce feature vectors. Each builder
is independent and writes to its own subdirectory under `data/features/`.

**Market features** (extends existing `FeatureBuilder`):
- 1d, 5d, 20d returns per symbol
- 20d rolling volatility per symbol
- 20d momentum per symbol
- Cross-asset correlation (rolling 60d pairwise)
- Relative value (z-score of return vs. sector average)

**Event features** (extends existing `EventFeatureBuilder`):
- `event_intensity`: exponentially decayed sum of recent event severities,
  per theme and region
- `event_novelty`: how unusual the current event flow is relative to the
  trailing 90-day baseline
- `event_breadth`: number of distinct sources reporting on the same cluster
- `event_sentiment`: average tone across sources in the cluster
- `sanctions_delta`: number of new entities added/removed since last snapshot
- `ais_anomaly_score`: deviation of vessel density in chokepoint regions from
  trailing 30-day average

**Macro features** (new):
- VIX level and 5d change
- Yield curve slope (10Y - 2Y) and change
- Oil price level and 5d change
- USD index level and change
- Breakeven inflation level and change
- Days until next central bank meeting (from calendar JSON)

### 3.5 Stage 3: Feature Assembly (Temporal Alignment)

The combined feature table has a **daily business-day index**. Alignment rules:

| Source Frequency | Alignment Rule |
|---|---|
| Intraday (GDELT, RSS, AIS) | Aggregate to end-of-day: last value for levels, sum for counts, max for severity |
| Daily (Yahoo, FRED daily series) | Direct join on date |
| Weekly (ACLED, FRED weekly) | Forward-fill: the value for Monday applies to Mon-Fri of that week |
| Monthly (FRED monthly) | Forward-fill: the value for the 1st applies to the entire month |
| Static (calendars, sanctions) | Computed as of each date (e.g., days-to-next-meeting is a daily countdown) |

The assembly step produces a single wide DataFrame (or Parquet file) per month
in `data/features/combined/YYYY/MM/`. Columns follow the naming convention:
`{category}_{source}_{metric}` (e.g., `event_gdelt_intensity`, `macro_fred_vix_5d_chg`,
`market_yahoo_XLE_return_1d`).

**Null handling:** after alignment and forward-fill, any remaining nulls are
filled with the column's trailing 20-day median. If fewer than 20 days of
history exist (early backtest periods), the column is dropped for that row.
Models must be tolerant of occasionally missing columns.

---

## 4. Backtest vs. Live Mode

### 4.1 Unified Pipeline, Two Clocks

The pipeline code is identical in both modes. The only difference is the **time
source**:

- **Live mode**: the system clock (`datetime.utcnow()`). Pollers run on their
  real schedules. Features are computed as new data arrives.
- **Backtest mode**: a simulated clock that advances day-by-day (or event-by-event).
  Data is read from the normalized store instead of fetched from external APIs.

A `TimeContext` object is threaded through the pipeline. Every data access call
receives `as_of: datetime` from this context. In live mode, `as_of` is always
"now." In backtest mode, it is the simulated date.

### 4.2 Point-in-Time Guarantees

Look-ahead bias is the most dangerous correctness bug in a backtest. The system
prevents it through three mechanisms:

**Mechanism 1 -- Ingestion timestamps on every record.** Every normalized record
has an `ingested_at` field recording when the system first observed it. In
backtest mode, all queries filter on `ingested_at <= as_of`. This means that if
ACLED data for week W is published on Wednesday of week W+1, the backtest does
not see it until that Wednesday.

**Mechanism 2 -- Feature builders receive explicit `as_of` dates.** The existing
`EventFeatureBuilder.build(as_of_date=...)` and `FeatureBuilder.build(as_of_date=...)`
patterns already enforce this. New builders must follow the same contract: they
receive an `as_of_date` and must not read any data with a timestamp after that date.

**Mechanism 3 -- No mutable global state in feature computation.** Feature
builders are stateless functions of (normalized data, as_of_date). They do not
cache intermediate results across dates. This means rerunning the backtest for
date D always produces the same features regardless of what dates were computed
before or after.

**Publication lag table** (used by the backtest to simulate realistic delays):

| Source | Typical Lag | Backtest Rule |
|---|---|---|
| GDELT CSV | ~15 minutes | Available same day |
| RSS | ~minutes | Available same day |
| AIS | Real-time | Available same day |
| Yahoo Finance | End of day + ~30 min | Available next business day open |
| FRED (daily series) | T+1 publication | Available T+1 |
| FRED (weekly series) | ~3 day lag | Available T+3 |
| FRED (monthly series) | ~2-4 week lag | Available on publication date (recorded in metadata) |
| ACLED | ~1 week lag | Available date = ingested_at, not event date |
| Sanctions lists | Same day | Available same day |

### 4.3 Historical Replay

To replay historical events through the pipeline (for backtest or strategy
research):

1. The `BacktestEngine` iterates over a date range.
2. For each date, it queries the normalized store with `as_of <= current_date`,
   applying the publication lag rules above.
3. It passes the filtered data through the same feature builders and expert
   models that live mode uses.
4. The `MetaStacker.combine()` produces signals. The `PortfolioOptimizer` and
   `DerivativesOverlay` produce trades. The `BacktestEngine` records results.

For the **existing synthetic data path** (`SyntheticDataGenerator` +
`SyntheticEventGenerator`), replay works identically: the synthetic data is
pre-generated and loaded into the normalized store format, then consumed
through the same pipeline.

---

## 5. Scalability Considerations

### 5.1 Scaling from 3 to 164 Instruments

The current system uses 3 symbols (`XLE`, `ITA`, `SEA`). At 164 instruments:

**Price data.** Yahoo Finance fetches become the bottleneck. Mitigation:
- Use `yfinance.download(tickers=list_of_164, group_by="ticker")` for bulk
  download instead of per-symbol serial fetches. This is a single HTTP request
  for all symbols.
- Partition the cache by symbol (`data/cache/yahoo/{symbol}.parquet`) so that
  updating one symbol does not invalidate others.
- At 164 symbols x ~252 trading days x 6 OHLCV columns, one year of price
  data is ~250K rows. This fits comfortably in memory as a single DataFrame.

**Feature computation.** The feature matrix grows from ~12 columns (3 symbols x
4 features) to ~650+ columns (164 x 4 + event + macro features). Mitigations:
- Compute features in chunks of 20 symbols, then concatenate. This bounds peak
  memory to ~20 symbols' worth of intermediate state.
- Store the combined feature table in Parquet with snappy compression. At 650
  columns x 252 rows/year, this is ~1 MB/year (trivial).
- Use `float32` instead of `float64` for feature values. Halves memory with
  negligible precision loss for ML models.

**Expert models.** Each expert scores each instrument. With 164 instruments and
(say) 5 experts, that is 820 predictions per date. The `MetaStacker` receives
predictions grouped by instrument, so the combination step scales linearly.

### 5.2 Handling Large GDELT CSV Files

GDELT exports can exceed 100 MB per 15-minute segment during major global events.

**Ingestion strategy:**
- Stream-parse CSVs with `pandas.read_csv(chunksize=50_000)`. Never load a full
  CSV into memory.
- Filter rows during parsing: only retain rows where the CAMEO event code or
  geographic coordinates match the system's theme/region taxonomy. This typically
  discards 80-90% of rows.
- Write filtered rows immediately to Parquet in `data/raw/gdelt/csv/`. Parquet
  files for filtered data are typically 5-10 MB per segment.

**Normalization strategy:**
- Process raw Parquet files one at a time (they are already filtered and small).
- Maintain a GDELT-specific dedup index on `GLOBALEVENTID` to avoid reprocessing
  events that appear in multiple consecutive 15-minute files.

**Backtest strategy:**
- Never load all historical GDELT data at once. The backtest queries the
  normalized event store by date range, loading at most one month at a time.
- For long backtests (5+ years), pre-compute event features at daily granularity
  and store in `data/features/event/`. The backtest then reads features, not raw
  events.

### 5.3 Memory Management for Long Backtests

A 5-year backtest at daily granularity with 164 instruments and 700 features
produces ~1,260 rows x 700 columns = ~880K floats = ~7 MB. This is trivially
small for the feature table.

The risk is in **intermediate data**: loading 5 years of GDELT events, or
computing rolling features that require long lookback windows.

**Rules:**
- Feature builders operate on a **rolling window**, not the full history. The
  window size matches the longest lookback (e.g., 90 days for event novelty
  baseline). At any point, only ~90 days of normalized events are in memory.
- The backtest engine processes one date at a time. After computing features and
  recording the day's result, intermediate data for that day is released.
- Large DataFrames (price history, returns) are memory-mapped from Parquet using
  `pyarrow.memory_map` when they exceed 500 MB. Below that threshold, standard
  `pd.read_parquet` is fine.
- The `CacheManager` is not used during backtests (it would fill with stale
  date-specific entries). Backtests read directly from the normalized store.

---

## 6. Integration with Existing Code

### 6.1 New Data Sources and BaseDataSource

The existing `BaseDataSource` interface defines a single method:

```python
class BaseDataSource(ABC):
    @abstractmethod
    def load_prices(self, symbols: list[str]) -> dict[str, list[float]]:
        ...
```

This interface is too narrow for the new sources (events are not prices; AIS
data is not prices). Rather than forcing everything through `load_prices`, the
integration strategy is:

**A. Keep `BaseDataSource` for price-like data.** `YahooDataSource`,
`MockDataSource`, and `SyntheticDataGenerator` continue to implement it.

**B. Introduce a parallel `BaseEventSource` interface:**

```python
class BaseEventSource(ABC):
    @abstractmethod
    def load_events(self, as_of: date, lookback_days: int) -> list[EventRecord]:
        ...
```

Implementations: `GDELTEventSource`, `RSSEventSource`, `ACLEDEventSource`,
`SanctionsEventSource`, `SyntheticEventSource` (wrapping the existing
`SyntheticEventGenerator`).

**C. Introduce a `BaseMacroSource` interface:**

```python
class BaseMacroSource(ABC):
    @abstractmethod
    def load_macro(self, series_ids: list[str], as_of: date) -> pd.DataFrame:
        ...
```

The existing `FREDDataSource` already has a `load_macro` method with a
compatible signature. It becomes the first implementation.

**D. Introduce a `BaseStreamSource` interface for AIS:**

```python
class BaseStreamSource(ABC):
    @abstractmethod
    def subscribe(self, callback: Callable[[dict], None]) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...
```

Only `AISStreamSource` implements this initially. The callback receives
individual position reports as dicts.

### 6.2 Feeding EventFeatureBuilder from the New Pipeline

The existing `EventFeatureBuilder.build()` takes `(as_of_date, theme, subtheme,
region)` and returns hardcoded mock values. The integration path:

1. A new `EventFeatureBuilder.__init__` accepts an `event_store: BaseEventSource`
   (or a path to the normalized event Parquet store).
2. `build()` queries the event store for events matching the given theme/region
   within a lookback window (e.g., 30 days before `as_of_date`).
3. It computes real features (intensity, novelty, breadth, sentiment) from the
   queried events.
4. When no event store is provided (default), it falls back to the current mock
   behavior. This preserves backward compatibility for tests.

The same pattern applies to `FeatureBuilder`: it currently takes
`prices: dict[str, list[float]]` as an argument. The caller (the pipeline
orchestrator) is responsible for fetching prices from the appropriate
`BaseDataSource` and passing them in. This does not change. The pipeline
orchestrator simply switches from `MockDataSource` to `YahooDataSource` (or
reads from the normalized price store in backtest mode).

### 6.3 Extending CacheManager for New Data Types

The current `CacheManager` only handles Parquet DataFrames. New data types
(JSON event records, SQLite dedup index) require extensions:

**Option A (recommended): keep CacheManager focused on DataFrames.** It already
does one thing well. Non-DataFrame storage (JSON, SQLite, raw files) is handled
by the raw/normalized store directly, outside the `CacheManager`.

**Option B (if consolidation is desired): add format-aware save/load.**

```python
class CacheManager:
    def save(self, name: str, data: pd.DataFrame | dict | list, fmt: str = "parquet") -> None:
        ...
    def load(self, name: str, fmt: str = "parquet") -> pd.DataFrame | dict | list:
        ...
```

Option A is preferred because it keeps the `CacheManager` simple and testable.
The raw/normalized store is a separate concern with different retention rules,
partitioning logic, and access patterns.

**What changes in CacheManager regardless of option chosen:**
- Add TTL support (section 1.4A).
- Add namespace support (section 1.4B).
- Add a `save_if_missing(name, loader_fn)` convenience method that checks
  `has()`, calls `loader_fn()` on miss, saves the result, and returns it.
  This eliminates the repeated if/else pattern in `YahooDataSource._fetch`
  and `FREDDataSource.load_macro`.

---

## Appendix A: Ingestion Sequence Diagram (Live Mode)

```
 Scheduler (cron / APScheduler)
     |
     |--- every 5 min ----> RSSPoller -----> raw/rss/ -----> NormalizerWorker ---> normalized/events/
     |--- every 15 min ---> GDELTPoller ---> raw/gdelt/ --> NormalizerWorker ---> normalized/events/
     |--- every 6 hr -----> SanctionsPoller -> raw/sanctions/ -> NormalizerWorker -> normalized/sanctions/
     |--- daily 09:00 ET -> FREDPoller ----> raw/fred/ ----> NormalizerWorker ---> normalized/macro/
     |--- daily 17:30 ET -> YahooPoller ---> raw/yahoo/ ---> NormalizerWorker ---> normalized/prices/
     |--- weekly Mon 02:00 -> ACLEDPoller -> raw/acled/ --> NormalizerWorker ---> normalized/events/
     |
     |--- continuous ------> AISListener --> raw/ais/ (hourly roll) -> NormalizerWorker -> normalized/ais/
     |
     |--- after each normalization cycle:
     |        FeatureWorker reads normalized/ -> writes features/
     |        AssemblyWorker reads features/ -> writes features/combined/
```

## Appendix B: Backtest Data Flow

```
 BacktestEngine.run(date_range, universe)
     |
     for each date in date_range:
       |
       |-- NormalizedStore.query(source="prices", as_of=date) --> price data
       |-- NormalizedStore.query(source="events", as_of=date)  --> event data
       |-- NormalizedStore.query(source="macro", as_of=date)   --> macro data
       |
       |-- FeatureBuilder.build(as_of_date=date, prices=...) -------> FeatureRow
       |-- EventFeatureBuilder.build(as_of_date=date, events=...) --> EventFeatureRow
       |
       |-- ExpertModels.predict(features, event_features) --> ExpertPrediction[]
       |-- MetaStacker.combine(predictions) ----------------> MetaSignal
       |-- PortfolioOptimizer.optimize(signal) -------------> PortfolioTarget
       |-- DerivativesOverlay.apply(portfolio, signal) ------> DerivativesOverlay
       |
       |-- record(date, portfolio, overlay, pnl)
```
