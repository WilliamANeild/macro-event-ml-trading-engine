# Logan's Part 3: Event and News Signal Pipeline — Build Guide

This document tells you what's done, what needs to be built, and how to build each piece. All the planning docs are already written in `docs/` — reference them as you go.

---

## What's Already Done

| Component | File | Status |
|-----------|------|--------|
| EventFeatureRow schema | `src/engine/events/schemas.py` | Done — defines theme, subtheme, region, values dict, metadata |
| EventFeatureBuilder | `src/engine/events/builder.py` | Mock — returns hardcoded intensity=0.5, novelty=0.3. Replace with real logic |
| SyntheticEventGenerator | `src/engine/data/synthetic_events.py` | Done — generates fake decaying shocks for backtest testing. Keep this, it's useful for testing |
| Keyword taxonomy | `docs/keyword_taxonomy.md` | Done — 70 themes with keywords, anchor phrases, disambiguation negatives |
| GDELT CAMEO mapping | `docs/gdelt_cameo_mapping.md` | Done — all 300 event codes mapped to our sleeves |
| Chokepoint coordinates | `docs/chokepoint_coordinates.md` | Done — GPS bounding boxes for all chokepoints and port clusters |
| Pipeline architecture | `docs/nlp_pipeline_architecture.md` | Done — full design for ingestion → classification → scoring → aggregation |
| Data architecture | `docs/data_architecture.md` | Done — storage layout, polling schedules, dedup strategy |

---

## What Needs to Be Built

### 1. GDELT Ingestion (`src/engine/events/gdelt_loader.py`)

**What it does:** Downloads GDELT 15-minute update files and parses them into structured event records.

**How to build it:**
- GDELT publishes a master file list at `http://data.gdeltproject.org/gdeltv2/masterfilelist.txt`
- Every 15 minutes a new CSV file appears (events table + GKG table)
- Download the latest CSV, parse it with pandas (tab-separated, no header — column names are in the GDELT codebook)
- Extract: CAMEO event code, actor countries, geo coordinates, Goldstein scale, tone, source URL, date
- Filter to only events relevant to our themes using the CAMEO mapping in `docs/gdelt_cameo_mapping.md`
- Return a list of normalized event records

**Key columns in GDELT events CSV:** EventCode (CAMEO), Actor1CountryCode, Actor2CountryCode, ActionGeo_Lat, ActionGeo_Long, GoldsteinScale, AvgTone, SOURCEURL, DATEADDED

**Reference:** `docs/gdelt_cameo_mapping.md` for which CAMEO codes map to which sleeves

---

### 2. RSS Feed Aggregator (`src/engine/events/rss_loader.py`)

**What it does:** Polls RSS feeds from news and maritime sources, extracts headlines.

**How to build it:**
- Use the `feedparser` library (`pip install feedparser`)
- Poll these feeds every 5-10 minutes:
  - AP News: `https://apnews.com/index.rss`
  - BBC World: `http://feeds.bbci.co.uk/news/world/rss.xml`
  - Al Jazeera: `https://www.aljazeera.com/xml/rss/all.xml`
  - Maritime Executive: `https://maritime-executive.com/feed`
  - gCaptain: `https://gcaptain.com/feed/`
  - Splash247: `https://splash247.com/feed/`
  - Defense News: `https://www.defensenews.com/arc/outboundfeeds/rss/`
  - Fed speeches: `https://www.federalreserve.gov/feeds/press_all.xml`
- For each entry: extract title, summary, publish date, source URL
- Deduplicate by URL (track seen URLs in a set or SQLite)
- Return normalized event records matching the same format as GDELT loader output

---

### 3. Keyword Matcher (`src/engine/events/keyword_matcher.py`)

**What it does:** Takes a headline/text and matches it against the 70-theme taxonomy to classify which themes it belongs to.

**How to build it:**
- Load the keyword taxonomy from `docs/keyword_taxonomy.md` or define it as a Python dict
- For each theme: check if any primary keywords appear in the text (case-insensitive)
- If keywords match, check disambiguation negatives — if a negative is present, skip this theme
- Check anchor phrases for stronger match confidence (multi-word phrases)
- A single headline can match multiple themes (cap at 4 max)
- Return a list of (theme, subtheme, confidence) tuples
- Confidence tiers: anchor phrase match = 0.9, multiple keyword match = 0.7, single keyword = 0.5

**Reference:** `docs/keyword_taxonomy.md` for the full taxonomy

---

### 4. Geographic Router (`src/engine/events/geo_router.py`)

**What it does:** Takes lat/lon coordinates (from GDELT) and determines which chokepoint, port cluster, or region the event belongs to.

**How to build it:**
- Load bounding boxes from `docs/chokepoint_coordinates.md` or define as a Python dict
- For each event with coordinates, check if it falls within any bounding box
- Check tight boxes first (chokepoint transit zones), then wide boxes (approach routes)
- Return the chokepoint/region name or "unlocalized" if no match
- This is simple rectangle containment: `min_lat <= lat <= max_lat and min_lon <= lon <= max_lon`

**Reference:** `docs/chokepoint_coordinates.md` for all bounding boxes

---

### 5. Event Scorer (`src/engine/events/scorer.py`)

**What it does:** Converts classified events into quantitative intensity/novelty/acceleration scores per theme per day.

**How to build it:**
- **Intensity** per (theme, region, day): weighted sum of:
  - Article count (volume) — more articles = higher intensity
  - Goldstein scale magnitude (from GDELT) — higher absolute value = bigger event
  - Tone negativity (from GDELT AvgTone) — more negative = more severe
  - Source diversity — events from 3+ different sources score higher than 1 source
- **Novelty**: compare today's intensity to a 7-day exponential moving average. Novelty = (today - EMA) / EMA_std. High novelty = fresh impulse. Low/negative novelty = decaying/repeated coverage
- **Acceleration**: week-over-week change in intensity. `acceleration = (this_week_intensity - last_week_intensity) / last_week_intensity`
- Normalize all scores to 0-1 range using min-max or sigmoid

**Reference:** `docs/nlp_pipeline_architecture.md` Section 4 (Scoring Layer) for exact formulas

---

### 6. Event Aggregator (`src/engine/events/aggregator.py`)

**What it does:** Rolls up daily per-event scores into weekly `EventFeatureRow` objects that the experts consume.

**How to build it:**
- Group scored events by (theme, subtheme, region, week)
- Aggregate using robust statistics:
  - Intensity: trimmed mean (drop top/bottom 10%)
  - Novelty: max (we care about the peak novelty in the week)
  - Acceleration: last day's value (most recent trend)
- Also compute source_count (number of unique sources that week)
- Output `EventFeatureRow` objects with values dict containing: `event_intensity`, `event_novelty`, `event_acceleration`, `source_diversity`, `article_count`
- These feed directly into `ExpertContext.event_features`

**Reference:** `docs/nlp_pipeline_architecture.md` Section 5 (Aggregation Layer)

---

### 7. Replace Mock EventFeatureBuilder (`src/engine/events/builder.py`)

**What it does:** Wire everything together. The builder should orchestrate: load events → classify → route → score → aggregate → return EventFeatureRow.

**How to build it:**
- Keep the existing `EventFeatureBuilder.build()` signature (as_of_date, theme, subtheme, region)
- Inside, call the GDELT loader and/or RSS loader for recent data
- Run keyword matching and geo routing
- Score and aggregate
- Return a real `EventFeatureRow` with computed values
- Add a `use_mock=True` parameter that preserves the current mock behavior for testing

---

## Build Order

Build in this order — each piece is testable independently:

1. **Keyword matcher** — pure Python, no external dependencies, easy to unit test
2. **Geographic router** — pure Python, just bounding box checks
3. **Event scorer** — pure math, test with fake event data
4. **RSS feed aggregator** — needs `feedparser`, test with live feeds
5. **GDELT ingestion** — needs network access, test with downloaded sample files
6. **Event aggregator** — combines scorer output into weekly rows
7. **Wire up EventFeatureBuilder** — integrate everything

## Testing

- Test keyword matcher against sample headlines (write 20-30 test cases)
- Test geo router with known coordinates (Suez Canal should route to "suez", etc.)
- Test scorer with synthetic event counts
- Test full pipeline end-to-end with a small GDELT sample file

## Dependencies to Install

```
pip install feedparser gdelt
```

## Key Files to Reference

- `docs/keyword_taxonomy.md` — all 70 themes
- `docs/gdelt_cameo_mapping.md` — CAMEO code → sleeve mapping
- `docs/chokepoint_coordinates.md` — GPS bounding boxes
- `docs/nlp_pipeline_architecture.md` — full pipeline design
- `docs/data_architecture.md` — storage and polling design
- `src/engine/events/schemas.py` — EventFeatureRow schema (your output format)
- `src/engine/experts/schemas.py` — ExpertContext (what experts expect in event_features)
