# Free / Freemium News & Event Data Sources for Macro Event-Driven Trading

Research date: 2026-04-15

This document catalogs every free or freemium API and data source relevant to a
geopolitical/macro event-driven trading system that needs to detect conflicts,
shipping disruptions, sanctions, central bank language, chokepoint incidents,
and trade restrictions.

---

## Table of Contents

1. [Tier 1 -- Primary Recommendations](#tier-1----primary-recommendations)
2. [Tier 2 -- Strong Supplements](#tier-2----strong-supplements)
3. [Tier 3 -- Useful Niche Sources](#tier-3----useful-niche-sources)
4. [Tier 4 -- Worth Knowing About But Limited](#tier-4----worth-knowing-about-but-limited)
5. [Central Bank Speech & Statement Feeds](#central-bank-speech--statement-feeds)
6. [Sanctions Data](#sanctions-data)
7. [Maritime / Shipping Data](#maritime--shipping-data)
8. [Trade & Tariff Data](#trade--tariff-data)
9. [Social Media / Sentiment](#social-media--sentiment)
10. [Architecture Recommendation](#architecture-recommendation)

---

## Tier 1 -- Primary Recommendations

### 1. GDELT Project (Global Database of Events, Language, and Tone)

| Field | Detail |
|---|---|
| **URL** | https://www.gdeltproject.org/ |
| **Coverage** | Geopolitics, conflict, protests, diplomacy, military, sanctions, trade -- essentially everything. Global, 65+ languages. |
| **Free tier** | **Completely free.** No API key needed for raw file downloads. DOC API and Context API have soft rate limits (throttling, not hard caps). BigQuery: 1 TB/month free query processing. |
| **Data format** | CSV (raw files), JSON (DOC/Context APIs), BigQuery SQL |
| **Latency** | **15 minutes.** Both raw CSV files and the DOC API update every 15 min. |
| **Historical data** | **Back to 1979** for the Event Database. GKG back to 2015. DOC API only guarantees the most recent ~3 months. Raw CSV files cover the full history. |
| **Structured metadata** | **Extremely rich.** CAMEO event codes (300+ event types), actors, geolocations (city-level), Goldstein scale (conflict-cooperation), tone/sentiment, 2,200+ GCAM emotion dimensions, 150+ GKG themes (e.g., `CRISISLEX_T03_DEAD`, `TAX_FNCACT_SANCTIONS`, `ENV_OIL`). |
| **Gotchas** | (1) DOC API rate limits tighten during major world events. Build retry logic. (2) BigQuery 1 TB sounds generous but the GKG dataset alone is >2.5 TB so a single unfiltered query can blow through the free tier. Always filter by `_PARTITIONTIME`. (3) Raw CSV files are large; you need infrastructure to download/parse the 15-min update files. (4) Data is derived from news articles, not ground truth -- false positives happen. (5) No full article text, only metadata about articles. |

**Why Tier 1:** GDELT is the single most important free data source for this system. It provides pre-structured event data with CAMEO codes that map directly to your event taxonomy (conflicts, sanctions, military actions). The 15-minute update cadence is within your acceptable latency window. Historical depth back to 1979 is unmatched for backtesting.

**Access methods (ranked):**
- **Raw CSV downloads** (best for backtesting): Master file list at `http://data.gdeltproject.org/gdeltv2/masterfilelist.txt` updated every 15 min.
- **DOC 2.0 API** (best for real-time monitoring): REST API, returns JSON, search by keyword/theme/country/source domain. Max 250 results per query.
- **BigQuery** (best for complex historical analysis): Full SQL, but watch the free tier.
- **Python packages**: `gdelt` on PyPI, `gdelt-doc-api` on GitHub.

---

### 2. ACLED (Armed Conflict Location & Event Data Project)

| Field | Detail |
|---|---|
| **URL** | https://acleddata.com/ |
| **Coverage** | Armed conflict, protests, riots, violence against civilians, strategic developments. 250+ countries. |
| **Free tier** | **Free for non-commercial/academic use.** Requires free registration. Full API access and bulk CSV downloads. |
| **Data format** | JSON (API), CSV/Excel (bulk download) |
| **Latency** | Weekly updates (events coded with ~1-2 week lag). Not real-time. |
| **Historical data** | **Back to 1997** for Africa, 2016+ for global. Excellent for backtesting conflict events. |
| **Structured metadata** | **Very rich.** Event type taxonomy (battles, explosions/remote violence, violence against civilians, protests, riots, strategic developments), sub-event types, actors (named armed groups, state forces), precise geolocation, fatality estimates, source citations. |
| **Gotchas** | (1) Non-commercial use only on free tier -- commercial licensing is separate. If this is an academic project, you are fine. (2) Weekly update lag means it is **not suitable for real-time trading signals** but is **excellent for backtesting and training ML models** on conflict escalation patterns. (3) Data requires registration and agreement to terms of use. |

**Why Tier 1:** ACLED is the gold standard for structured conflict event data. Where GDELT gives you noisy, high-frequency news-derived signals, ACLED gives you carefully human-coded ground-truth events. Essential for training your conflict detection models and backtesting.

---

### 3. Event Registry / NewsAPI.ai

| Field | Detail |
|---|---|
| **URL** | https://newsapi.ai/ (also https://eventregistry.org/) |
| **Coverage** | Global news from 150,000+ sources in 30+ languages. General purpose but strong on geopolitics, economics, commodities. |
| **Free tier** | **2,000 tokens free** (not monthly -- appears to be a one-time or very limited replenishing allocation). 1 token = 1 search of recent articles (last 30 days). Each search returns up to 100 articles. |
| **Data format** | JSON (REST API), Python and Node.js SDKs |
| **Latency** | Near real-time for current articles. |
| **Historical data** | Free tier: last 30 days only. Paid plans: back to 2014. |
| **Structured metadata** | **Excellent.** Articles grouped into "events" (clustered articles about the same topic), categories, entities (people, orgs, locations), sentiment scores, concepts, and topics. |
| **Gotchas** | (1) 2,000 tokens is very limited -- roughly 2,000 search queries total. (2) Historical access requires paid plan. (3) Token cost increases for older date ranges (e.g., 5 tokens for 2017 data, 15 tokens for multi-year ranges). (4) The event clustering feature is genuinely useful -- it groups related articles, which helps de-duplicate signals. |

**Why Tier 1 (conditional):** The event clustering and entity extraction are superior to any other free source. However, the token budget is tight. Best used strategically for high-value queries rather than continuous polling.

---

## Tier 2 -- Strong Supplements

### 4. NewsAPI.org

| Field | Detail |
|---|---|
| **URL** | https://newsapi.org/ |
| **Coverage** | 150,000+ sources globally. Headlines and article metadata. |
| **Free tier** | **100 requests/day.** Development use only (cannot be used in production). |
| **Data format** | JSON (REST API) |
| **Latency** | **24-hour delay** on free tier. Real-time on paid. |
| **Historical data** | Free tier: articles from last 30 days (with 24h delay). |
| **Structured metadata** | Minimal: source, author, title, description, URL, image, publish date. No entity extraction, no sentiment, no categories. |
| **Gotchas** | (1) **24-hour delay is significant** -- outside your 15-30 min acceptable window. (2) Free tier is explicitly "development only" -- cannot be used in production. (3) No full article text -- only title + description snippet. (4) No structured metadata beyond basic fields. (5) CORS restrictions mean free tier only works server-side. |

**Verdict:** Useful for development/testing but the 24h delay and production restrictions limit real utility. Not suitable as a primary real-time source.

---

### 5. GNews API

| Field | Detail |
|---|---|
| **URL** | https://gnews.io/ |
| **Coverage** | Global news from Google News sources. |
| **Free tier** | **100 requests/day**, max 1 request/second. Development/testing only. |
| **Data format** | JSON (REST API) |
| **Latency** | Near real-time. |
| **Historical data** | Not specified in free tier. Limited. |
| **Structured metadata** | Title, description, content snippet (first ~260 chars), source, publish date. No entity extraction, no sentiment. |
| **Gotchas** | (1) Free tier is non-commercial, development only. (2) No full article content on free tier. (3) 100 requests/day is workable for periodic keyword polling (~4 requests/hour for 6 keyword categories). |

---

### 6. Newsdata.io

| Field | Detail |
|---|---|
| **URL** | https://newsdata.io/ |
| **Coverage** | 90,000+ sources, 150+ countries, news in 35+ languages. |
| **Free tier** | **200 credits/day** (each credit = 10 articles = 2,000 articles/day max). Rate limit: 30 credits per 15 minutes. |
| **Data format** | JSON (REST API) |
| **Latency** | **12-hour delay** on free tier. |
| **Historical data** | Free tier: last 48 hours only. Paid: up to 5 years. |
| **Structured metadata** | Categories, keywords, country, language, sentiment (paid tier). |
| **Gotchas** | (1) 12-hour delay on free tier is outside your acceptable window. (2) Sentiment analysis only on paid tier. (3) The 200 credits/day is more generous than NewsAPI.org in terms of article volume. |

---

### 7. Mediastack

| Field | Detail |
|---|---|
| **URL** | https://mediastack.com/ |
| **Coverage** | 7,500+ sources, 50+ countries. Live news and blog articles. |
| **Free tier** | **500 requests/month** (some sources say 100/month -- verify). |
| **Data format** | JSON (REST API) |
| **Latency** | **30-minute delay** on free tier. Right at the edge of your acceptable window. |
| **Historical data** | None on free tier. |
| **Structured metadata** | Source, author, title, description, URL, image, category, language, country, published date. Basic but includes category. |
| **Gotchas** | (1) No HTTPS on free tier -- data transmitted unencrypted. (2) 500/month is very limited. (3) Non-commercial only on free tier. (4) No full article content. |

---

## Tier 3 -- Useful Niche Sources

### 8. RSS Feeds from Key Sources

RSS feeds are free, have no rate limits, and provide near-real-time updates. They are an essential complement to APIs.

| Source | Feed URL | Coverage | Notes |
|---|---|---|---|
| **AP News - World** | `https://apnews.com/index.rss` | General world news | AP still maintains RSS feeds |
| **Reuters** | No official RSS since 2020 | Geopolitics, finance | Must use third-party feed generators (RSS.app, FiveFilters) or scrape |
| **Al Jazeera** | `https://www.aljazeera.com/xml/rss/all.xml` | Middle East, global geopolitics | Good for MENA region events |
| **BBC World** | `http://feeds.bbci.co.uk/news/world/rss.xml` | Global news | Reliable, headline + summary |
| **Defense News** | `https://www.defensenews.com/arc/outboundfeeds/rss/` | Military, defense industry | Key for military/defense events |
| **Maritime Executive** | `https://maritime-executive.com/feed` | Shipping, maritime | Critical for chokepoint/shipping events |
| **gCaptain** | `https://gcaptain.com/feed/` | Maritime shipping news | Shipping disruptions, port news |
| **Lloyd's List** | No free RSS | Maritime, insurance | Paywalled |
| **Splash247** | `https://splash247.com/feed/` | Maritime/shipping | Good for shipping market news |
| **Hellenic Shipping News** | `https://www.hellenicshippingnews.com/feed/` | Shipping, commodities | Commodities + shipping combined |

**Format:** XML/RSS (easily parsed with `feedparser` in Python)
**Latency:** Near real-time (minutes)
**Structured metadata:** Title, description/summary, publish date, link. No entity extraction or sentiment.
**Historical data:** None (current feed only). Can be archived by polling regularly.

**Gotchas:** (1) Reuters killed official RSS in 2020 -- third-party generators may break. (2) RSS only gives headlines + summaries, not full article text. (3) Feed URLs change without notice. (4) Need to build your own polling + dedup infrastructure.

---

## Central Bank Speech & Statement Feeds

Critical for detecting shifts in monetary policy language, hawkish/dovish signals, and rate decision context.

### 9. Federal Reserve

| Field | Detail |
|---|---|
| **URL** | https://www.federalreserve.gov/feeds/feeds.htm |
| **Coverage** | All Fed speeches, testimony, press releases, FOMC statements, minutes, Beige Book |
| **Format** | RSS (XML) |
| **Cost** | **Completely free.** No authentication. |
| **Latency** | Published at time of release. |
| **Historical** | FRED API (https://fred.stlouisfed.org/) has economic data back decades. Speech archives on website back to ~2006. |
| **Key feeds** | Speeches RSS, Press Releases RSS, FOMC Statements |

### 10. European Central Bank (ECB)

| Field | Detail |
|---|---|
| **URL** | https://www.ecb.europa.eu/home/html/rss.en.html |
| **Coverage** | ECB Executive Board speeches, press conferences, monetary policy decisions |
| **Format** | RSS (XML) for news. **CSV download** for full speeches dataset (pipe-delimited, UTF-8). SDMX API for statistical data. |
| **Cost** | **Completely free.** |
| **Historical** | Speeches dataset CSV covers full history of Executive Board speeches. |
| **Key asset** | The downloadable speeches CSV at https://www.ecb.europa.eu/press/key/html/downloads.en.html is a structured dataset ready for NLP analysis. |

### 11. Bank of England (BOE)

| Field | Detail |
|---|---|
| **URL** | https://www.bankofengland.co.uk/rss |
| **Coverage** | Speeches, publications, MPC decisions, financial stability reports |
| **Format** | RSS (XML) |
| **Cost** | **Completely free.** |
| **Key feeds** | Separate RSS feeds for Speeches, Publications, News, Statistics |

### 12. Bank of Japan (BOJ)

| Field | Detail |
|---|---|
| **URL** | https://www.boj.or.jp/en/about/press/index.htm |
| **Coverage** | Monetary policy statements, Governor/Deputy Governor speeches, meeting minutes |
| **Format** | RSS feed available, HTML pages for full text. English translations available with slight delay. |
| **Cost** | **Completely free.** |
| **Gotchas** | English versions of speeches are released with a delay (days to weeks after the Japanese original). |

**Architecture note for central banks:** All four central bank feeds should be polled via RSS and the full speech/statement text scraped from the linked HTML page. This text then feeds into an NLP pipeline for hawkish/dovish scoring. The ECB speeches CSV is a ready-made training dataset for such a model.

---

## Sanctions Data

### 13. OFAC Sanctions Lists (Official US Government)

| Field | Detail |
|---|---|
| **URL** | https://sanctionslist.ofac.treas.gov/ |
| **Coverage** | SDN List, Consolidated Non-SDN List (Foreign Sanctions Evaders, Sectoral Sanctions, etc.) |
| **Format** | XML, CSV (fixed-field and delimited) |
| **Cost** | **Completely free.** No API key. Direct download. |
| **Update frequency** | Updated as designations change (typically within hours of new sanctions) |
| **Historical** | Current list only; no official API for historical snapshots. You must archive snapshots yourself. |
| **Gotchas** | (1) No REST API -- you download the full list file. (2) Need to diff snapshots to detect new sanctions additions. (3) Only covers US sanctions. |

### 14. OpenSanctions

| Field | Detail |
|---|---|
| **URL** | https://www.opensanctions.org/ |
| **Coverage** | Aggregates sanctions lists from US (OFAC), EU, UK, UN, and 30+ other jurisdictions. Also includes PEPs (Politically Exposed Persons) and crime-related entities. |
| **Format** | JSON (structured entity data), CSV, API endpoints |
| **Cost** | **Free for non-commercial use.** Commercial use requires a data license. |
| **Update frequency** | Multiple times daily. |
| **Historical** | Dataset provides current state. Can be self-hosted for point-in-time snapshots. |
| **Structured metadata** | Entity names, aliases, nationalities, ID numbers, sanctions program, date listed, linked entities. |
| **Key advantage** | Consolidates multiple sanctions regimes into one normalized dataset. Much easier than parsing OFAC + EU + UK lists separately. |

### 15. EU Consolidated Sanctions List

| Field | Detail |
|---|---|
| **URL** | https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions |
| **Format** | XML, CSV |
| **Cost** | Free |

---

## Maritime / Shipping Data

### 16. aisstream.io

| Field | Detail |
|---|---|
| **URL** | https://aisstream.io/ |
| **Coverage** | Global real-time AIS vessel positions, vessel identity, port calls |
| **Format** | WebSocket (JSON messages) |
| **Cost** | **Free.** Requires GitHub sign-in for API key. |
| **Latency** | Real-time streaming |
| **Rate/volume** | ~300 messages/second if subscribed to entire world. Can filter by MMSI, message type, geographic bounding box. |
| **Historical** | No historical data. Real-time stream only. |
| **Gotchas** | (1) Must maintain persistent WebSocket connection. (2) Subscription message must be sent within 3 seconds of connection or it closes. (3) High bandwidth required for global feed. (4) No historical data -- must archive yourself. |

**Use case:** Monitor chokepoints (Suez, Hormuz, Malacca, Panama) by filtering to geographic bounding boxes around those locations. Detect anomalies in vessel traffic patterns.

### 17. AISHub

| Field | Detail |
|---|---|
| **URL** | https://www.aishub.net/ |
| **Coverage** | Community-sourced AIS data from volunteer receivers |
| **Format** | JSON, XML, CSV via API |
| **Cost** | **Free** but requires sharing AIS data from your own receiver (reciprocal model) OR a small fee for receive-only access. |
| **Gotchas** | Coverage depends on volunteer receivers -- gaps in remote areas. Not as reliable as commercial AIS providers. |

### 18. MarineTraffic / VesselFinder / Kpler

These are commercial services. Mentioned for completeness but free tiers are very limited (usually just a web interface, no API access on free tier).

---

## Trade & Tariff Data

### 19. UN Comtrade

| Field | Detail |
|---|---|
| **URL** | https://comtrade.un.org/ |
| **Coverage** | International trade flows (imports/exports) for all countries, all commodity codes |
| **Format** | JSON (API), CSV (bulk download) |
| **Cost** | **Free** with UN-prescribed limits. Premium subscription was cancelled Jan 2026. |
| **Limits** | API returns max 250K records per query. |
| **Historical** | Decades of trade data. |
| **Gotchas** | (1) Data has significant lag (months). (2) Useful for structural analysis and backtesting, not real-time signals. (3) Python library: `comtradeapicall`. |

### 20. WTO Tariff Data

| Field | Detail |
|---|---|
| **URL** | https://ttd.wto.org/ |
| **Coverage** | Applied and bound tariff rates by country and product |
| **Cost** | Free via WITS (World Bank) platform |
| **Use case** | Detecting tariff changes for trade restriction analysis |

---

## Social Media / Sentiment

### 21. Reddit API

| Field | Detail |
|---|---|
| **URL** | https://www.reddit.com/dev/api/ |
| **Coverage** | Subreddits like r/geopolitics, r/economics, r/shipping, r/commodities |
| **Free tier** | **100 requests/minute, 10,000 requests/month total.** Non-commercial only. OAuth required. |
| **Format** | JSON |
| **Gotchas** | (1) 10,000/month total cap is very restrictive. (2) Non-commercial only -- commercial is $12K+/year. (3) Requires pre-approval for apps since 2025. (4) Signal-to-noise ratio is low for geopolitical events. (5) Mostly useful for sentiment confirmation, not event detection. |

**Verdict:** Low priority. Reddit is not a reliable primary source for the event types this system targets. The effort-to-value ratio is poor compared to GDELT + RSS feeds.

---

## Architecture Recommendation

Based on this research, here is the recommended data architecture, ordered by priority:

### Real-Time Event Detection Pipeline (15-30 min cadence)

| Priority | Source | Role | Polling Interval |
|---|---|---|---|
| 1 | **GDELT DOC API** | Primary event detection -- keyword searches for each theme (conflict, sanctions, shipping, etc.) | Every 15 min |
| 2 | **GDELT Raw CSV Files** | Structured CAMEO event codes, GKG themes, tone scores | Every 15 min (download latest file) |
| 3 | **RSS Feeds** (AP, BBC, Al Jazeera, maritime sources) | Headline monitoring, early warning | Every 5-10 min |
| 4 | **Central Bank RSS** (Fed, ECB, BOE, BOJ) | Monetary policy language detection | Every 15 min |
| 5 | **OFAC/OpenSanctions** | Sanctions list change detection | Every 6 hours (diff snapshots) |
| 6 | **aisstream.io** | Chokepoint vessel traffic anomaly detection | Continuous WebSocket |

### Backtesting & Model Training Data

| Priority | Source | Role | Coverage |
|---|---|---|---|
| 1 | **GDELT Event Database** (raw CSV) | Historical event features, CAMEO codes, tone | 1979-present |
| 2 | **ACLED** | Ground-truth conflict events for training | 1997-present |
| 3 | **ECB Speeches CSV** | NLP training data for central bank language models | Full history |
| 4 | **Fed speeches** (scraped archive) | NLP training data | 2006-present |
| 5 | **Event Registry** (paid tier) | Rich historical articles with entity/event clustering | 2014-present (paid) |
| 6 | **UN Comtrade** | Trade flow structural analysis | Decades |

### Estimated Daily API Budget (Free Tier)

| Source | Daily Calls Available | Calls Needed | Status |
|---|---|---|---|
| GDELT DOC API | Soft limit (rate-throttled) | ~96 (every 15 min) | OK |
| GDELT Raw CSV | Unlimited downloads | ~96 files/day | OK |
| RSS Feeds | Unlimited | ~864 (6 feeds x 144/day) | OK |
| Central Bank RSS | Unlimited | ~576 (4 banks x 144/day) | OK |
| GNews API | 100/day | 24-48 (hourly topic polls) | Tight but workable |
| NewsAPI.org | 100/day | 24-48 | OK for dev/testing |
| OFAC download | Unlimited | 4 (every 6h) | OK |
| OpenSanctions | Soft limit | 4 | OK |
| aisstream.io | Unlimited (streaming) | Continuous | OK |
| ACLED API | Unlimited (registered) | Weekly batch | OK |

### Key Integration Points with Existing System

The system's `EventFeatureRow` schema (in `src/engine/events/schemas.py`) expects:
- `theme` -- maps directly to GDELT GKG themes and CAMEO event root codes
- `subtheme` -- maps to CAMEO sub-event codes or GKG sub-themes
- `region` -- maps to GDELT/ACLED geolocation fields
- `values` dict -- can hold `event_intensity` (GDELT tone/Goldstein scale), `event_novelty` (article volume spike detection), `event_decay`
- `metadata` dict -- can hold source attribution, CAMEO codes, entity lists

The `SyntheticEventGenerator` in `src/engine/data/synthetic_events.py` can be replaced or supplemented with a real data loader that produces the same `EventFeatureRow` format from GDELT/ACLED data.

### What You Cannot Get For Free

- **Full article text** at scale (all free news APIs give headlines + snippets only; full text requires scraping or paid plans)
- **Real-time** (<5 min) event data (free tiers have 15-30 min delays minimum)
- **Commercial-use licensed** news content
- **Historical AIS data** (only real-time streaming is free)
- **Point-in-time sanctions snapshots** (must build your own archive)
- **Commodity-specific shipping analytics** (chokepoint transit volumes, freight rates) -- requires commercial providers like Kpler or Vortexa

### Recommended First Implementation Steps

1. Build a GDELT raw CSV ingestion pipeline (15-min files into EventFeatureRow)
2. Build an RSS feed aggregator for the 6-8 key feeds listed above
3. Register for ACLED and download historical conflict data for backtesting
4. Download ECB speeches CSV and Fed speech archives for NLP model training
5. Set up OFAC list snapshot diffing
6. Prototype aisstream.io WebSocket consumer for chokepoint monitoring
7. Use GNews/NewsAPI.org for development and gap-filling
