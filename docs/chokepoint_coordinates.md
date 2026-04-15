# Maritime Chokepoint & Shipping Area GPS Bounding Boxes

Reference for aisstream.io AIS vessel tracking API. All coordinates in decimal degrees (WGS 84).

**Bounding box format:** `[[min_lat, min_lon], [max_lat, max_lon]]`

---

## 1. Chokepoints

### 1.1 Strait of Hormuz

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Tight (transit zone) | 26.20 | 55.80 | 26.80 | 56.60 |
| Wide (approach routes) | 25.00 | 54.00 | 27.50 | 58.00 |

- **Geopolitical significance:** The world's most critical oil chokepoint. Approximately 20-21 million barrels per day of crude oil and petroleum products transit here, representing roughly 20% of global oil supply. Connects the Persian Gulf oil-producing states (Saudi Arabia, Iraq, UAE, Kuwait, Qatar) to global markets.
- **Typical daily vessel transits:** ~80-100 vessels/day (tankers, LNG carriers, bulk, container)
- **Key risk factors:**
  - Iran-US/Western tensions; Iran has repeatedly threatened closure
  - Iranian Revolutionary Guard Corps (IRGC) naval provocations and seizures
  - Proximity to Iranian islands (Qeshm, Hormuz, Larak) that flank the shipping lanes
  - Mine warfare threat in shallow waters
  - Drone and missile attacks from Houthi-allied or Iranian proxy forces
  - Traffic separation scheme is only ~3 km wide per direction

---

### 1.2 Bab el-Mandeb

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Tight (transit zone) | 12.30 | 43.10 | 12.80 | 43.60 |
| Wide (approach routes) | 11.50 | 42.50 | 13.50 | 44.50 |

- **Geopolitical significance:** Southern gateway to the Red Sea and Suez Canal. All Europe-Asia traffic via Suez must pass here. Controls access for ~12% of global trade. Flanked by Yemen, Djibouti, and Eritrea.
- **Typical daily vessel transits:** ~60-80 vessels/day
- **Key risk factors:**
  - Houthi missile, drone, and naval mine attacks on commercial shipping (major escalation since late 2023)
  - Piracy from Somali coast (historically significant, re-emerging)
  - Yemen civil war spillover
  - Narrow passage (~29 km wide) between Perim Island and African coast
  - Multiple foreign military bases in Djibouti (US, China, France, Japan)
  - Rerouting around Cape of Good Hope adds 10-14 days and significant fuel costs

---

### 1.3 Suez Canal

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Tight (canal zone) | 29.85 | 32.30 | 31.30 | 32.60 |
| Wide (approaches, incl. Gulf of Suez + Port Said approaches) | 29.00 | 32.00 | 31.80 | 33.50 |

- **Geopolitical significance:** Connects the Mediterranean to the Red Sea, eliminating the need to circumnavigate Africa. Handles ~12-15% of global trade and ~7-8% of global seaborne oil. Operated by the Suez Canal Authority (Egypt); transit fees are a major Egyptian revenue source (~$9-10B/year).
- **Typical daily vessel transits:** ~50-70 vessels/day (northbound and southbound combined)
- **Key risk factors:**
  - Single point of failure: blockages (e.g., Ever Given 2021) halt global trade
  - Egyptian political instability
  - Revenue loss from Houthi-driven rerouting (traffic dropped significantly 2024-2025)
  - Terrorist threats in Sinai Peninsula
  - Canal width and depth limitations for ultra-large vessels
  - Congestion and scheduling delays

---

### 1.4 Panama Canal

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Tight (canal zone) | 8.85 | -79.95 | 9.40 | -79.50 |
| Wide (approaches, Pacific + Caribbean sides) | 8.00 | -80.50 | 9.80 | -79.00 |

- **Geopolitical significance:** Connects the Atlantic and Pacific oceans. Handles ~5-6% of global seaborne trade, especially critical for US East Coast-Asia routes, LNG exports, and grain shipments. Operated by Panama Canal Authority.
- **Typical daily vessel transits:** ~35-40 vessels/day (reduced during drought conditions; historically ~38)
- **Key risk factors:**
  - Freshwater dependency: Gatun Lake levels affected by drought/El Nino (severe restrictions in 2023-2024)
  - Lock-based system creates physical throughput limits
  - Draft restrictions during low water reduce vessel capacity
  - Neopanamax locks completed 2016 but still constrain ultra-large vessels
  - Booking slot auctions can cost $1-4M during restrictions
  - Climate change threatens long-term reliability

---

### 1.5 Strait of Malacca

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Tight (narrowest section, Phillips Channel to Singapore Strait) | 1.05 | 103.40 | 1.50 | 104.20 |
| Wide (full strait, Andaman Sea entrance to South China Sea exit) | 0.80 | 99.00 | 4.50 | 104.50 |

- **Geopolitical significance:** The shortest sea route between the Indian and Pacific Oceans. Carries ~25-30% of global seaborne trade, including ~16 million barrels/day of crude oil (mostly destined for China, Japan, South Korea). The economic lifeline of East Asian manufacturing economies.
- **Typical daily vessel transits:** ~200-250 vessels/day (one of the busiest waterways globally)
- **Key risk factors:**
  - Piracy and armed robbery (persistent, especially in the Singapore Strait section)
  - Extreme traffic density creates collision and grounding risk
  - Shallow waters in narrowest section (~25m depth) limit VLCC draft
  - Territorial waters of Malaysia, Indonesia, and Singapore overlap
  - Potential for state-level blockade during great power conflict
  - Environmental disaster risk from groundings in shallow, ecologically sensitive waters

---

### 1.6 Taiwan Strait

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Tight (main shipping channel) | 23.50 | 118.00 | 25.50 | 120.50 |
| Wide (full strait + approaches) | 22.00 | 116.50 | 26.50 | 121.50 |

- **Geopolitical significance:** Separates Taiwan from mainland China. Approximately 50% of global container shipping and 88% of the world's largest container ships transit through or near this strait. Taiwan itself produces ~90% of the world's advanced semiconductors (TSMC). Any disruption would devastate global supply chains.
- **Typical daily vessel transits:** ~150-200 vessels/day (container, bulk, tanker combined)
- **Key risk factors:**
  - China-Taiwan military tensions; PLA exercises and median line crossings
  - Risk of blockade, quarantine, or invasion scenario
  - US-China military confrontation risk
  - PLA live-fire exercises can close shipping lanes
  - Insurance premiums surge during military escalation
  - Undersea cable and infrastructure vulnerability

---

### 1.7 Turkish Straits (Bosphorus + Dardanelles)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Bosphorus tight | 40.98 | 28.95 | 41.25 | 29.15 |
| Dardanelles tight | 40.00 | 26.15 | 40.40 | 26.75 |
| Combined wide (full Sea of Marmara transit) | 39.80 | 25.80 | 41.40 | 29.40 |

- **Geopolitical significance:** Sole maritime connection between the Black Sea and the Mediterranean. Controls export routes for Russian/Ukrainian/Georgian/Romanian oil and grain. Governed by the 1936 Montreux Convention, giving Turkey significant control over naval vessel transits.
- **Typical daily vessel transits:** ~120-140 vessels/day through the Bosphorus (one of the world's busiest and most dangerous waterways)
- **Key risk factors:**
  - Extremely narrow: Bosphorus is ~700m wide at its narrowest, with sharp turns
  - Turkey's Montreux Convention enforcement restricts warship passage
  - Russia-Ukraine war impacts on Black Sea grain and oil exports
  - Heavy cross-traffic from Istanbul ferry system (1500+ crossings/day)
  - Collision risk in sharp turns and strong currents (up to 7 knots)
  - Turkey's new canal project (Canal Istanbul) could alter transit dynamics
  - Oil tanker queuing delays from new insurance verification requirements

---

### 1.8 Strait of Gibraltar

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Tight (transit zone) | 35.80 | -5.80 | 36.10 | -5.25 |
| Wide (approach routes) | 35.50 | -6.50 | 36.50 | -4.50 |

- **Geopolitical significance:** Gateway between the Atlantic Ocean and Mediterranean Sea. All maritime trade to/from Mediterranean ports, Suez Canal, and Black Sea passes here. Also a key route for North African energy exports (Algeria, Libya LNG and oil).
- **Typical daily vessel transits:** ~250-300 vessels/day (one of the busiest straits globally)
- **Key risk factors:**
  - High traffic density with crossing ferry traffic (Spain-Morocco)
  - Strong currents and tidal flows
  - Fog and weather conditions
  - Migrant vessel crossings create SAR obligations
  - Sovereignty disputes (Gibraltar, Ceuta, Melilla)
  - Relatively low geopolitical closure risk due to NATO presence on both flanks

---

### 1.9 Cape of Good Hope (Rerouting Waypoint)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Tight (cape rounding zone) | -35.00 | 17.50 | -33.50 | 19.00 |
| Wide (approach and rerouting corridor) | -36.00 | 15.00 | -32.00 | 21.00 |

- **Geopolitical significance:** Alternative route when Suez/Red Sea transits are disrupted. Became critically important again from late 2023 when Houthi attacks forced major rerouting. Adds 10-14 days to Europe-Asia voyages and significantly increases fuel costs and emissions.
- **Typical daily vessel transits:** Highly variable; ~50-80 vessels/day normally, surged to ~100-150 during peak Red Sea diversions (2024-2025)
- **Key risk factors:**
  - Severe weather: Southern Ocean storms, large swells, strong currents
  - Agulhas Current creates dangerous wave conditions
  - Limited port infrastructure for emergency stops between South Africa and next destination
  - Increased transit time impacts perishable cargo and just-in-time supply chains
  - Higher fuel costs and emissions per voyage
  - Insurance cost increases for longer voyages

---

### 1.10 Danish Straits (Baltic Sea Access)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Oresund tight | 55.40 | 12.50 | 55.95 | 12.85 |
| Great Belt tight | 55.10 | 10.80 | 55.60 | 11.20 |
| Combined wide (all three straits + approaches) | 54.50 | 9.50 | 57.80 | 13.50 |

- **Geopolitical significance:** The only maritime access to the Baltic Sea. Critical for Russian energy exports (oil, LNG, pipeline gas via Nord Stream), Baltic state trade, Finnish/Swedish imports, and Russian naval movements. The three straits are the Oresund (Denmark-Sweden), the Great Belt, and the Little Belt.
- **Typical daily vessel transits:** ~100-120 vessels/day across all straits combined
- **Key risk factors:**
  - Russia-NATO tensions in the Baltic
  - Subsea infrastructure sabotage (Nord Stream precedent)
  - Russian shadow fleet of aging tankers carrying sanctioned oil
  - Shallow draft restrictions (Great Belt ~17m, Oresund ~8m)
  - Denmark can restrict warship passage under the 1857 convention
  - Ice conditions in winter can restrict passage
  - Environmental sensitivity (Baltic is nearly enclosed)

---

## 2. Port Clusters

### 2.1 India West Coast (Mumbai/JNPT, Mundra, Kandla)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Mumbai/JNPT port area | 18.85 | 72.75 | 19.10 | 73.00 |
| Mundra port area | 22.65 | 69.60 | 22.85 | 69.80 |
| Kandla port area | 22.95 | 70.05 | 23.10 | 70.25 |
| Combined wide (full west coast cluster) | 18.50 | 68.50 | 23.50 | 73.50 |

- **Notes:** JNPT (Jawaharlal Nehru Port Trust) is India's largest container port. Mundra (Adani) is India's largest private port and fastest-growing. Kandla handles bulk and liquid cargo.

---

### 2.2 India East Coast (Chennai, Vizag, Paradip)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Chennai port area | 13.05 | 80.25 | 13.20 | 80.40 |
| Vizag (Visakhapatnam) port area | 17.65 | 83.25 | 17.75 | 83.35 |
| Paradip port area | 20.20 | 86.60 | 20.35 | 86.75 |
| Combined wide (full east coast cluster) | 12.80 | 79.50 | 20.80 | 87.50 |

- **Notes:** Chennai is a major container and auto-export port. Vizag handles steel, coal, and oil. Paradip is a major bulk port (coal, iron ore, POL).

---

### 2.3 Singapore (Transshipment Hub)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Port/anchorage area | 1.15 | 103.60 | 1.35 | 104.10 |
| Wide (including anchorages and approaches) | 0.90 | 103.30 | 1.55 | 104.30 |

- **Notes:** World's largest transshipment port. Handles ~37 million TEU/year. Key bunkering hub. Located at the crossroads of the Strait of Malacca and South China Sea.

---

### 2.4 Rotterdam / Antwerp (European Hub)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Rotterdam port complex | 51.85 | 3.85 | 52.00 | 4.50 |
| Antwerp port area | 51.20 | 4.25 | 51.40 | 4.45 |
| Combined wide (including North Sea approaches and Westerschelde) | 51.00 | 3.00 | 52.20 | 4.80 |

- **Notes:** Rotterdam is Europe's largest port (~14 million TEU + massive oil/LNG/chemicals). Antwerp (now Antwerp-Bruges) is Europe's second-largest. Together they form the gateway to the European industrial heartland via Rhine-Scheldt river systems.

---

### 2.5 Shanghai / Ningbo (China Hub)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Shanghai (Yangshan deep-water port) | 30.50 | 121.80 | 30.70 | 122.10 |
| Shanghai (Waigaoqiao) | 31.30 | 121.50 | 31.45 | 121.70 |
| Ningbo-Zhoushan port area | 29.70 | 121.60 | 30.10 | 122.40 |
| Combined wide (full Yangtze Delta cluster) | 29.50 | 121.00 | 31.60 | 122.80 |

- **Notes:** Shanghai is the world's busiest container port (~49 million TEU). Ningbo-Zhoushan is third globally (~35 million TEU) and the world's busiest by tonnage. Together they handle a massive share of China's manufactured exports and raw material imports.

---

## 3. Regional Route Monitoring Areas

### 3.1 Red Sea (Full)

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Full Red Sea | 12.30 | 32.00 | 30.00 | 44.00 |
| Northern Red Sea (Gulf of Suez approach) | 26.00 | 33.00 | 30.00 | 36.00 |
| Central Red Sea (main transit corridor) | 18.00 | 37.00 | 26.00 | 42.00 |
| Southern Red Sea (Bab el-Mandeb approach) | 12.30 | 42.00 | 18.00 | 44.00 |

- **Key context:** Since late 2023, Houthi attacks have made the southern Red Sea one of the most dangerous commercial shipping zones. Major carriers rerouted via Cape of Good Hope, collapsing Suez Canal revenues and adding billions in global shipping costs.

---

### 3.2 South China Sea

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Full South China Sea | 3.00 | 103.00 | 23.00 | 121.00 |
| Spratly Islands area (contested zone) | 7.00 | 111.00 | 12.00 | 117.00 |
| Main shipping lane (Singapore to Taiwan/China) | 1.00 | 103.00 | 22.00 | 118.00 |

- **Key context:** One of the most contested bodies of water globally. China claims sovereignty over most of the sea via the "nine-dash line." Carries an estimated $5.3 trillion in annual trade. Territorial disputes involve China, Vietnam, Philippines, Malaysia, Brunei, and Taiwan.

---

### 3.3 Persian Gulf

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Full Persian Gulf | 23.50 | 48.00 | 30.50 | 56.50 |
| Northern Gulf (Iraq/Kuwait/Iran terminals) | 28.50 | 48.00 | 30.50 | 50.50 |
| Central Gulf (Saudi/Bahrain/Qatar) | 25.00 | 50.00 | 28.50 | 52.50 |
| Southern Gulf (UAE/Oman approach) | 23.50 | 53.00 | 26.50 | 56.50 |

- **Key context:** Contains approximately 48% of the world's proven oil reserves and 38% of proven natural gas reserves. Key loading terminals include Ras Tanura (Saudi Arabia), Basra Oil Terminal (Iraq), Jebel Ali (UAE), and Ras Laffan (Qatar - world's largest LNG export facility).

---

### 3.4 Black Sea

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Full Black Sea | 40.50 | 27.50 | 46.70 | 42.00 |
| Western Black Sea (Ukraine/Romania/Bulgaria grain ports) | 42.00 | 27.50 | 46.70 | 34.00 |
| Eastern Black Sea (Georgia/Russia) | 41.50 | 38.00 | 44.50 | 42.00 |
| Southern Black Sea (Turkey coast) | 40.50 | 29.00 | 42.50 | 41.50 |

- **Key context:** Critical for grain exports (Ukraine and Russia together account for ~25-30% of global wheat exports). Russia-Ukraine war has severely disrupted shipping since 2022. Maritime insurance premiums for Ukrainian ports remain elevated. Russia's shadow fleet transits sanctioned oil through here.

---

### 3.5 Eastern Mediterranean

| Box Type | min_lat | min_lon | max_lat | max_lon |
|----------|---------|---------|---------|---------|
| Full Eastern Mediterranean | 30.00 | 24.00 | 37.50 | 36.50 |
| Suez Canal exit / Port Said area | 30.50 | 31.50 | 31.80 | 33.00 |
| Levantine coast (Israel, Lebanon, Syria) | 32.00 | 33.50 | 36.00 | 36.50 |
| Crete-Cyprus corridor (main transit lane) | 33.50 | 24.00 | 36.00 | 34.00 |

- **Key context:** Major transit area for vessels entering/exiting the Suez Canal. Contains significant offshore gas fields (Leviathan, Zohr, Aphrodite). Subject to multiple overlapping territorial disputes (Turkey-Greece-Cyprus EEZ conflicts, Israel-Lebanon maritime boundary). East Mediterranean Gas Forum has created new geopolitical alignments.

---

## 4. API Integration Notes

### aisstream.io Bounding Box Format

The aisstream.io WebSocket API accepts bounding boxes in the following format within the subscription message:

```
BoundingBoxes: [[[min_lat, min_lon], [max_lat, max_lon]]]
```

Multiple bounding boxes can be specified in a single subscription to monitor several areas simultaneously:

```
BoundingBoxes: [
  [[min_lat_1, min_lon_1], [max_lat_1, max_lon_1]],
  [[min_lat_2, min_lon_2], [max_lat_2, max_lon_2]]
]
```

### Coordinate Precision

All coordinates in this document use 2 decimal places, providing precision to approximately 1.1 km. This is sufficient for regional monitoring boxes but may need refinement for tight canal/port monitoring where 3-4 decimal places would provide 100m-10m precision.

### Rate Limit Considerations

- Tight boxes produce fewer AIS messages and are suitable for detailed vessel-level tracking.
- Wide/regional boxes will generate high message volumes; apply MMSI filtering or message type filtering to manage throughput.
- The full South China Sea and full Persian Gulf boxes will generate very high volumes; consider subdividing or using ship type filters.

### Recommended Monitoring Priority (by geopolitical impact)

1. **Strait of Hormuz** - Oil price impact
2. **Bab el-Mandeb / Southern Red Sea** - Active threat zone
3. **Taiwan Strait** - Semiconductor supply chain risk
4. **Suez Canal** - Global trade flow indicator
5. **Strait of Malacca** - East Asian trade dependency
6. **Turkish Straits** - Grain/oil export bottleneck
7. **Panama Canal** - Americas trade + water level risk
8. **Danish Straits** - Russian energy/shadow fleet monitoring
9. **Cape of Good Hope** - Rerouting indicator
10. **Strait of Gibraltar** - Mediterranean access baseline
