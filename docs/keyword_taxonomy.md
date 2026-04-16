# Keyword Taxonomy for Geopolitical/Macro Event-Driven Trading System

Version: 1.0
Date: 2026-04-15
Reference: Algory Algorithmic Trading Idea (Design Doc, Section 2.3 Theme Ontology)

This document defines the complete theme library used by the NLP classification pipeline
to tag incoming news headlines, GDELT records, RSS items, and central bank text into
localized themes. Each theme feeds a specific expert model within a specific sleeve/sub-sleeve.

---

## How to read each theme entry

| Field | Purpose |
|---|---|
| **Theme ID** | Stable identifier used in code and feature schemas (`EventFeatureRow.theme`) |
| **Sleeve / Sub-sleeve** | Maps to the hierarchical universe (Level 1 / Level 2) |
| **Primary keywords** | Single tokens; at least one must appear for a candidate match |
| **Anchor phrases** | Multi-word phrases that strongly confirm the theme when matched |
| **Disambiguation negatives** | Terms that, if co-present with a primary keyword, indicate the text is NOT about this theme and the match should be suppressed |
| **Theme description** | One-paragraph summary used for semantic (embedding) similarity scoring |
| **GDELT/CAMEO mapping** | Related GKG themes, CAMEO root/base codes, or GCAM dimensions where available |

Themes are organized by sleeve. IDs use the pattern `{SLEEVE}_{SUBSLEEVE}_{SEQ}`.

---

## Sleeve 1: Defense & Security

### DEF_MUN_001 -- Munitions & Ordnance Procurement

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Munitions |
| **Primary keywords** | munitions, ordnance, ammunition, artillery, shells, projectiles, warheads, explosives, propellant |
| **Anchor phrases** | "munitions contract", "artillery shells", "ammunition production", "ordnance procurement", "defense procurement award", "munitions stockpile", "ammo shortage", "155mm shells", "precision-guided munition", "cluster munitions", "depleted uranium rounds", "munitions industrial base" |
| **Disambiguation negatives** | "civil engineering blast", "mining explosives", "fireworks", "demolition contractor", "controlled demolition", "quarry blasting", "Olympic shooting" |
| **Theme description** | Government or military procurement of munitions, artillery shells, bombs, and ordnance. Covers contract awards, production ramp-ups, stockpile depletion warnings, and industrial base capacity for ammunition manufacturing. |
| **GDELT/CAMEO** | CAMEO 0831 (Provide military aid), GKG: `MILITARY`, `TAX_FNCACT_DEFENSE` |

---

### DEF_MIS_002 -- Missile Defense Systems

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Missile Defense |
| **Primary keywords** | missile, ICBM, ballistic, interceptor, THAAD, Patriot, Iron Dome, hypersonic, SAM, anti-missile |
| **Anchor phrases** | "missile defense system", "ballistic missile test", "missile intercept", "air defense battery", "integrated air and missile defense", "hypersonic glide vehicle", "cruise missile launch", "missile shield", "anti-ballistic missile", "theater missile defense", "missile proliferation", "medium-range ballistic" |
| **Disambiguation negatives** | "SpaceX launch", "satellite launch vehicle", "rocket launch NASA", "Artemis mission", "commercial launch provider", "bottle rocket", "model rocketry" |
| **Theme description** | Development, testing, deployment, procurement, or use of missile systems and missile defense platforms. Includes both offensive ballistic/cruise/hypersonic missiles and defensive interceptor systems like THAAD, Patriot, and Iron Dome. |
| **GDELT/CAMEO** | CAMEO 190 (Use conventional military force), GKG: `MILITARY`, `WMD` |

---

### DEF_SAT_003 -- ISR / Satellites / Space Defense

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / ISR-Space-Comms |
| **Primary keywords** | satellite, ISR, reconnaissance, surveillance, SIGINT, IMINT, GEOINT, orbit, space force, ASAT |
| **Anchor phrases** | "intelligence surveillance reconnaissance", "spy satellite", "reconnaissance satellite", "space-based sensor", "anti-satellite weapon", "ASAT test", "space domain awareness", "orbital debris from", "military satellite launch", "National Reconnaissance Office", "overhead persistent infrared", "space defense" |
| **Disambiguation negatives** | "Starlink consumer", "broadband satellite internet", "DirecTV", "weather satellite NOAA", "GPS civilian", "satellite radio Sirius", "television satellite", "Planet Labs agriculture" |
| **Theme description** | Military and intelligence space assets, ISR platforms, satellite launches for defense purposes, anti-satellite weapons, and space-domain military operations. Covers procurement and deployment of reconnaissance and signals intelligence satellites. |
| **GDELT/CAMEO** | GKG: `MILITARY`, `INTELLIGENCE` |

---

### DEF_COM_004 -- Secure Communications / EW

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / ISR-Space-Comms |
| **Primary keywords** | comms, communications, encryption, electronic warfare, EW, jamming, SIGINT, signals, SATCOM, JADC2 |
| **Anchor phrases** | "secure communications", "electronic warfare system", "GPS jamming", "signals intelligence", "communications jamming", "spectrum warfare", "tactical data link", "joint all-domain command", "battlefield communications", "encrypted military network", "electronic countermeasures", "radio frequency weapon" |
| **Disambiguation negatives** | "5G rollout", "consumer broadband", "smartphone encryption", "WhatsApp privacy", "FCC spectrum auction", "telecom earnings", "cell tower", "WiFi router" |
| **Theme description** | Military secure communications systems, electronic warfare capabilities, jamming, signals intelligence collection, and tactical data networks. Covers procurement of EW platforms and incidents of GPS/communications jamming. |
| **GDELT/CAMEO** | GKG: `MILITARY`, `CYBER` |

---

### DEF_CYB_005 -- Cyber Warfare & Cyber Defense

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Cyber-EW |
| **Primary keywords** | cyber, cyberattack, hack, ransomware, malware, APT, cyberwarfare, CISA, zero-day |
| **Anchor phrases** | "state-sponsored cyberattack", "critical infrastructure hack", "cyber espionage", "advanced persistent threat", "cyber command", "nation-state hacker", "cyber defense contract", "offensive cyber operation", "election interference cyber", "SCADA attack", "cyberweapon", "cyber warfare unit", "information warfare" |
| **Disambiguation negatives** | "cybersecurity stock price", "antivirus software review", "password manager", "phishing email tips", "cyber Monday sale", "online safety for kids", "data breach notification law", "identity theft consumer" |
| **Theme description** | State-sponsored or military cyber operations, critical infrastructure cyberattacks, cyber espionage campaigns, and government cyber defense procurement. Excludes routine consumer cybersecurity news and corporate data breaches unless attributed to a state actor. |
| **GDELT/CAMEO** | CAMEO 1731 (Impose administrative sanctions -- cyber), GKG: `CYBER_ATTACK`, `HACK` |

---

### DEF_NAV_006 -- Naval / Shipbuilding (Military)

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Naval-Shipbuilding |
| **Primary keywords** | shipbuilding, frigate, destroyer, carrier, submarine, corvette, naval, fleet, Navy, warship, cruiser |
| **Anchor phrases** | "naval shipbuilding contract", "aircraft carrier deployment", "submarine procurement", "destroyer commissioning", "fleet expansion", "naval base construction", "shipyard modernization", "keel laying ceremony", "sea trial", "naval exercise", "carrier strike group", "blue-water navy", "littoral combat ship" |
| **Disambiguation negatives** | "cruise ship", "cargo vessel", "container ship order", "tanker fleet commercial", "yacht", "fishing vessel", "ferry service", "commercial shipyard order" |
| **Theme description** | Military naval shipbuilding programs, warship procurement, fleet modernization, submarine contracts, and naval base construction. Covers defense-industrial naval capacity and military vessel deployment decisions. |
| **GDELT/CAMEO** | CAMEO 0831 (Provide military aid), GKG: `MILITARY` |

---

### DEF_NUC_007 -- Nuclear Modernization & Infrastructure

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Nuclear Enterprise |
| **Primary keywords** | nuclear, warhead, ICBM, triad, plutonium, enrichment, nonproliferation, NNSA, deterrent |
| **Anchor phrases** | "nuclear modernization program", "nuclear triad", "warhead refurbishment", "ICBM replacement", "nuclear deterrent", "strategic nuclear forces", "nuclear posture review", "plutonium pit production", "nuclear arms control", "New START treaty", "nuclear weapons complex", "nuclear enterprise modernization", "tactical nuclear weapon" |
| **Disambiguation negatives** | "nuclear power plant", "nuclear energy generation", "nuclear reactor civilian", "nuclear medicine", "nuclear fusion research", "SMR small modular reactor", "nuclear waste storage civilian", "Chernobyl tourism" |
| **Theme description** | Military nuclear weapons modernization programs, warhead production and refurbishment, strategic delivery system upgrades (ICBMs, SLBMs, bombers), arms control treaty developments, and nuclear posture decisions. Explicitly excludes civilian nuclear energy. |
| **GDELT/CAMEO** | GKG: `WMD`, `NUCLEAR`, CAMEO 190 |

---

### DEF_PRM_008 -- Defense Primes / Spending Policy

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Primes |
| **Primary keywords** | defense budget, Pentagon, NDAA, defense spending, military aid, arms sale, FMS |
| **Anchor phrases** | "defense budget increase", "NDAA authorization", "Pentagon budget request", "foreign military sales", "defense appropriations", "arms export", "military aid package", "defense industrial base", "defense contractor award", "weapons package approved", "security assistance", "supplemental defense spending", "military readiness funding" |
| **Disambiguation negatives** | "self-defense class", "home security system", "defensive driving", "defense attorney", "legal defense fund", "defense mechanism psychology" |
| **Theme description** | Government defense spending policy, budget authorizations, military aid packages, foreign military sales approvals, and broad defense industrial base policy decisions. This is the policy/spending overlay that affects defense primes collectively rather than a specific sub-domain. |
| **GDELT/CAMEO** | CAMEO 0831, 0832 (Military aid), GKG: `TAX_FNCACT_DEFENSE`, `MILITARY` |

---

### DEF_CON_009 -- Active Conflict Escalation

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Conflict |
| **Primary keywords** | war, invasion, airstrike, offensive, escalation, ceasefire, troops, combat, shelling, bombardment |
| **Anchor phrases** | "military escalation", "ground offensive launched", "airstrikes on", "troops deployed to", "ceasefire collapsed", "cross-border shelling", "full-scale invasion", "military incursion", "armed conflict", "theater of war", "combat operations", "frontline advance", "counter-offensive", "siege of" |
| **Disambiguation negatives** | "trade war", "price war", "streaming wars", "browser war", "console war", "custody battle", "legal battle", "war on drugs rhetoric", "Star Wars movie" |
| **Theme description** | Active military conflict events including invasions, offensives, airstrikes, artillery exchanges, troop deployments, and ceasefire developments. Distinguishes actual kinetic conflict from procurement/spending themes and from metaphorical uses of conflict language. |
| **GDELT/CAMEO** | CAMEO 18x (Assault), 19x (Fight), 20x (Engage in mass violence), GKG: `KILL`, `CRISISLEX_T03_DEAD` |

---

## Sleeve 2: Shipping & Supply Chain

### SHP_HRM_010 -- Strait of Hormuz

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Chokepoint -- Hormuz |
| **Primary keywords** | Hormuz, Persian Gulf, Gulf of Oman, IRGC Navy, Iranian navy |
| **Anchor phrases** | "Strait of Hormuz", "Hormuz chokepoint", "Persian Gulf shipping", "tanker seized Hormuz", "Iranian naval forces", "Hormuz transit", "Gulf oil route", "IRGC fast boats", "tanker harassment Hormuz", "mine threat Hormuz", "Hormuz blockade", "Persian Gulf escort" |
| **Disambiguation negatives** | "Oman tourism", "Dubai real estate", "Qatar World Cup", "Bahrain Grand Prix", "Gulf Cooperation Council summit" |
| **Theme description** | Shipping disruptions, military incidents, vessel seizures, mine threats, and traffic anomalies in the Strait of Hormuz and immediate approaches in the Persian Gulf and Gulf of Oman. The world's most critical oil transit chokepoint. |
| **GDELT/CAMEO** | GKG: `ENV_OIL`, geolocation filter: lat 26-27, lon 56-57 |

---

### SHP_BAB_011 -- Bab el-Mandeb / Southern Red Sea

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Chokepoint -- Bab el-Mandeb |
| **Primary keywords** | Bab el-Mandeb, Red Sea, Houthi, Yemen, Aden, Djibouti |
| **Anchor phrases** | "Bab el-Mandeb strait", "Red Sea shipping attack", "Houthi missile ship", "Houthi drone attack vessel", "Red Sea transit suspended", "Red Sea rerouting", "southern Red Sea threat", "Gulf of Aden attack", "Red Sea insurance premium", "Ansar Allah maritime", "anti-ship ballistic missile Red Sea", "Red Sea naval escort" |
| **Disambiguation negatives** | "Red Sea resort", "Red Sea coral reef", "Red Sea diving", "Aqaba beach", "Eilat tourism", "Yemen humanitarian aid distribution" |
| **Theme description** | Shipping attacks, disruptions, and rerouting decisions in the Bab el-Mandeb strait, southern Red Sea, and Gulf of Aden. Primarily driven by Houthi/Ansar Allah anti-shipping campaigns but also covers piracy and any military naval activity in this corridor. |
| **GDELT/CAMEO** | GKG: `CRISISLEX`, `MILITARY`, geolocation: lat 12-15, lon 42-45 |

---

### SHP_SUE_012 -- Suez Canal

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Chokepoint -- Suez |
| **Primary keywords** | Suez, canal, SCA, Ever Given, Sumed pipeline |
| **Anchor phrases** | "Suez Canal transit", "Suez Canal blockage", "Suez Canal Authority", "canal transit fees", "Suez traffic", "vessel grounding Suez", "Suez Canal revenue", "Suez transit decline", "canal closure", "northbound Suez convoy", "southbound Suez convoy", "Suez alternative route" |
| **Disambiguation negatives** | "Suez Crisis 1956 history", "Suez city real estate", "documentary about Suez" |
| **Theme description** | Operational status, traffic volumes, blockages, groundings, fee changes, and revenue reports for the Suez Canal. Includes upstream effects of Red Sea disruptions that cause Suez traffic decline and rerouting via Cape of Good Hope. |
| **GDELT/CAMEO** | Geolocation filter: lat 29.9-31.3, lon 32.3-32.6 |

---

### SHP_BLK_013 -- Black Sea

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Chokepoint -- Black Sea |
| **Primary keywords** | Black Sea, Bosphorus, Dardanelles, Turkish Straits, Odesa, Novorossiysk, Constanta |
| **Anchor phrases** | "Black Sea shipping corridor", "grain corridor Black Sea", "Black Sea mine threat", "Bosphorus transit", "Turkish Straits closure", "Black Sea fleet", "Ukrainian port blockade", "Odesa port attack", "Novorossiysk oil terminal", "Black Sea grain initiative", "Danube ports", "Montreux Convention" |
| **Disambiguation negatives** | "Black Sea resort vacation", "Bulgarian beach", "Crimea tourism", "Black Sea property" |
| **Theme description** | Shipping disruptions in the Black Sea, including grain corridor operations, mine threats, port attacks, Turkish Straits transit restrictions, and military naval activity affecting commercial shipping. Critical for grain and Russian oil export flows. |
| **GDELT/CAMEO** | GKG: `ENV_OIL`, `FOOD_SECURITY`, geolocation filter for Black Sea basin |

---

### SHP_TWN_014 -- Taiwan Strait

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Chokepoint -- Taiwan Strait |
| **Primary keywords** | Taiwan Strait, Taiwan, PLA Navy, PLAN, Formosa, Kaohsiung, Keelung |
| **Anchor phrases** | "Taiwan Strait transit", "PLA military exercises Taiwan", "Taiwan Strait closure", "Chinese naval blockade Taiwan", "Taiwan contingency", "median line Taiwan Strait", "ADIZ incursion Taiwan", "quarantine Taiwan", "semiconductor supply Taiwan conflict", "Taiwan shipping disruption", "cross-strait tensions" |
| **Disambiguation negatives** | "TSMC earnings report", "Taiwan election results", "Taiwan tourism", "Taiwan GDP growth", "Taipei 101" |
| **Theme description** | Military tensions, naval exercises, potential blockade or quarantine scenarios, and shipping disruptions in the Taiwan Strait. A conflict scenario here affects global semiconductor supply chains and Pacific shipping routes simultaneously. |
| **GDELT/CAMEO** | CAMEO 17x (Coerce), 19x (Fight), GKG: `MILITARY` |

---

### SHP_MAL_015 -- Malacca Strait

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Chokepoint -- Malacca |
| **Primary keywords** | Malacca, Singapore Strait, Lombok, Sunda Strait, Andaman |
| **Anchor phrases** | "Strait of Malacca", "Malacca piracy", "Malacca chokepoint", "Singapore Strait transit", "Malacca traffic", "piracy Malacca", "armed robbery Malacca", "Malacca rerouting", "Lombok Strait alternative", "Malacca Strait patrol", "ReCAAP alert" |
| **Disambiguation negatives** | "Malacca city heritage", "Melaka tourism", "Singapore F1 Grand Prix", "Singapore housing prices" |
| **Theme description** | Shipping security, piracy incidents, armed robbery, and traffic disruptions in the Malacca Strait, Singapore Strait, and alternative routes through Lombok and Sunda Straits. Critical chokepoint for Asia-bound oil and container trade. |
| **GDELT/CAMEO** | Geolocation filter: lat 1-4, lon 100-104 |

---

### SHP_PAN_016 -- Panama Canal

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Chokepoint -- Panama |
| **Primary keywords** | Panama Canal, Gatun, Neopanamax, ACP, Panama locks |
| **Anchor phrases** | "Panama Canal transit restrictions", "Panama Canal draft limits", "Panama Canal drought", "Gatun Lake water level", "Panama Canal daily transits", "canal booking slots", "Panama Canal auction premium", "Neopanamax locks", "canal transit delays", "Panama Canal Authority restrictions" |
| **Disambiguation negatives** | "Panama Papers scandal", "Panama City Beach Florida", "Panama hat", "Van Halen Panama" |
| **Theme description** | Operational disruptions at the Panama Canal including drought-related draft restrictions, transit slot reductions, booking auction premiums, and any infrastructure or policy changes affecting canal throughput. |
| **GDELT/CAMEO** | Geolocation filter: lat 8.9-9.4, lon -79.9--79.5 |

---

### SHP_INW_017 -- India West Coast Ports

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Port Cluster -- India West |
| **Primary keywords** | Mumbai port, JNPT, Mundra, Kandla, Nhava Sheva, Deendayal, Mangalore port, Cochin port, Mormugao |
| **Anchor phrases** | "JNPT congestion", "Mundra port disruption", "India west coast port closure", "Arabian Sea cyclone port", "Kandla port operations", "Nhava Sheva terminal", "Gujarat port strike", "India west coast freight", "Adani Ports Mundra", "Cochin port embargo" |
| **Disambiguation negatives** | "Bollywood Mumbai", "Mumbai real estate", "Gujarat elections", "Goa tourism", "Kerala backwaters" |
| **Theme description** | Operational status, congestion, weather closures, labor actions, and disruptions at major Indian west coast ports including JNPT/Nhava Sheva, Mundra, Kandla/Deendayal, Cochin, and Mormugao. These handle the majority of India's containerized and bulk trade with Europe, Middle East, and Africa. |
| **GDELT/CAMEO** | Geolocation filter: India western seaboard |

---

### SHP_INE_018 -- India East Coast Ports

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Port Cluster -- India East |
| **Primary keywords** | Chennai port, Visakhapatnam, Vizag, Kolkata port, Haldia, Paradip, Ennore, Krishnapatnam, Gangavaram |
| **Anchor phrases** | "Chennai port congestion", "Bay of Bengal cyclone port", "Vizag port closure", "Kolkata port operations", "Paradip port coal", "Ennore terminal", "Krishnapatnam disruption", "India east coast port closure", "Haldia dock strike" |
| **Disambiguation negatives** | "Chennai IT sector", "Kolkata cultural festival", "Vizag beach tourism", "Andhra Pradesh elections" |
| **Theme description** | Operational status, cyclone closures, congestion, and disruptions at major Indian east coast ports including Chennai, Visakhapatnam, Kolkata/Haldia, Paradip, Ennore, and Krishnapatnam. Key nodes for India's trade with East Asia, Southeast Asia, and Pacific. |
| **GDELT/CAMEO** | Geolocation filter: India eastern seaboard |

---

### SHP_INS_019 -- Maritime Insurance & Freight Stress

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Insurance-Freight |
| **Primary keywords** | war risk premium, freight rate, insurance surcharge, P&I, hull insurance, BDI, WCI, SCFI |
| **Anchor phrases** | "war risk insurance premium", "marine insurance surcharge", "freight rate spike", "Baltic Dry Index", "container freight index", "war risk area designation", "Joint War Committee listed area", "insurance premium increase shipping", "P&I club surcharge", "hull and machinery war risk", "Drewry World Container Index", "Shanghai Containerized Freight Index" |
| **Disambiguation negatives** | "car insurance rate", "health insurance premium", "home insurance", "life insurance policy", "insurance company earnings" |
| **Theme description** | Changes in maritime war risk insurance premiums, freight rate indices, and shipping cost stress indicators. War risk area designations by Lloyd's Joint War Committee are particularly significant as they directly affect shipping route economics and rerouting decisions. |
| **GDELT/CAMEO** | GKG: `ECON_COST`, `ECON_PRICE` |

---

### SHP_SAN_020 -- Sanctions Enforcement at Sea

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Sanctions Enforcement |
| **Primary keywords** | ship-to-ship transfer, dark fleet, shadow fleet, AIS transponder off, sanctions evasion, flag hopping, sanctions tanker |
| **Anchor phrases** | "ship-to-ship oil transfer", "dark fleet tanker", "shadow fleet vessel", "AIS signal dark", "transponder switched off", "sanctions evasion at sea", "illicit oil transfer", "flag state deregistration", "sanctions busting vessel", "price cap enforcement", "price cap violation tanker", "oil laundering at sea" |
| **Disambiguation negatives** | "AIS data science project", "fleet management software", "car rental fleet", "delivery fleet electric" |
| **Theme description** | Enforcement and evasion of maritime sanctions including dark/shadow fleet activity, ship-to-ship transfers, AIS manipulation, flag-hopping, and price cap compliance monitoring. Relevant to both the energy supply picture and sanctions effectiveness. |
| **GDELT/CAMEO** | GKG: `TAX_FNCACT_SANCTIONS`, `ENV_OIL` |

---

### SHP_ATK_021 -- Maritime Attack / Boarding / Piracy

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Incident Type |
| **Primary keywords** | piracy, boarding, hijack, vessel attack, maritime attack, armed robbery at sea, seized vessel |
| **Anchor phrases** | "vessel attacked", "ship boarded by", "pirates seized", "armed robbery against ship", "hijacked vessel", "maritime kidnapping", "vessel fired upon", "drone attack on ship", "limpet mine vessel", "RPG attack vessel", "anti-ship missile hit", "merchant vessel attacked" |
| **Disambiguation negatives** | "Pirates of the Caribbean", "pirate costume", "pirate radio", "Somali pirate movie", "software piracy", "music piracy" |
| **Theme description** | Specific incident reports of attacks on commercial vessels including piracy, armed robbery, hijacking, boarding, drone strikes, missile attacks, and mine damage. Covers all maritime theaters but tags should be combined with a chokepoint theme for localization. |
| **GDELT/CAMEO** | CAMEO 18x (Assault), GKG: `CRISISLEX_T03_DEAD`, `MARITIME` |

---

### SHP_CLS_022 -- Port Closure / Rerouting

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Incident Type |
| **Primary keywords** | port closure, rerouting, diversion, Cape of Good Hope, alternative route, port shutdown, congestion |
| **Anchor phrases** | "port closed due to", "vessels rerouting via", "Cape of Good Hope rerouting", "diverting around", "port operations suspended", "terminal shut down", "shipping lane closure", "transit suspended", "rerouting adds days", "longer transit time", "vessels avoiding", "no-go zone declared" |
| **Disambiguation negatives** | "airport closure", "road closure", "school closure", "store closure retail", "restaurant closed" |
| **Theme description** | Port closure events (weather, military, labor, infrastructure) and vessel rerouting decisions that add transit time and cost. Rerouting via Cape of Good Hope due to Red Sea threats is a key current example. |
| **GDELT/CAMEO** | GKG: `ECON_COST` |

---

## Sleeve 3: Commodities

### CMD_SPR_023 -- Supply Risk Premium (Oil)

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Energy Complex |
| **Primary keywords** | oil supply, crude disruption, OPEC, production cut, pipeline attack, refinery attack, embargo, supply outage |
| **Anchor phrases** | "oil supply disruption", "OPEC production cut", "crude oil supply risk", "pipeline sabotage", "refinery shutdown attack", "oil export embargo", "geopolitical risk premium crude", "supply outage barrels", "spare capacity OPEC", "oil field attack", "petroleum supply shock", "strategic petroleum reserve release", "force majeure crude" |
| **Disambiguation negatives** | "oil painting", "essential oils", "olive oil price", "cooking oil shortage", "motor oil change", "oil stock earnings beat" |
| **Theme description** | Geopolitical events that create supply disruption risk for crude oil, driving a risk premium into oil futures. Covers OPEC supply decisions, pipeline/refinery attacks, export embargoes, and conflict-driven production outages. |
| **GDELT/CAMEO** | GKG: `ENV_OIL`, `ECON_PRICE`, CAMEO 163 (Impose embargo) |

---

### CMD_GAS_024 -- Natural Gas / LNG Disruption

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Energy Complex |
| **Primary keywords** | natural gas, LNG, pipeline, Nord Stream, TTF, Henry Hub, gas supply, liquefaction |
| **Anchor phrases** | "natural gas supply cut", "LNG terminal disruption", "pipeline explosion", "gas pipeline sabotage", "TTF price spike", "European gas storage", "LNG cargo diversion", "gas rationing", "pipeline flow reduction", "gas transit dispute", "LNG export terminal", "regasification facility", "pipeline capacity constraint" |
| **Disambiguation negatives** | "gas station price", "gasoline pump price", "gas stove cooking", "natural gas vehicle NGV", "gas leak residential" |
| **Theme description** | Supply disruptions, pipeline incidents, LNG terminal issues, and transit disputes affecting natural gas and LNG markets. Includes both physical disruptions and contractual/political supply weaponization. |
| **GDELT/CAMEO** | GKG: `ENV_OIL` (GDELT groups energy broadly), `ECON_PRICE` |

---

### CMD_SPR_025 -- Energy Infrastructure Attack

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Energy Complex |
| **Primary keywords** | pipeline attack, refinery strike, oil terminal, energy infrastructure, power grid, substation |
| **Anchor phrases** | "attack on oil infrastructure", "refinery struck by", "pipeline bombed", "oil terminal fire", "power grid attack", "energy infrastructure sabotage", "drone strike refinery", "Abqaiq-style attack", "oil facility fire", "pumping station attack", "transformer substation hit", "energy infrastructure targeted" |
| **Disambiguation negatives** | "pipeline software CI/CD", "data pipeline", "infrastructure bill roads", "cloud infrastructure", "5G infrastructure" |
| **Theme description** | Physical attacks or sabotage targeting energy infrastructure including oil/gas pipelines, refineries, terminals, power grids, and substations. Distinct from supply policy decisions; focuses on kinetic/destructive events. |
| **GDELT/CAMEO** | CAMEO 18x (Assault), GKG: `ENV_OIL`, `INFRASTRUCTURE` |

---

### CMD_SAF_026 -- Safe-Haven Demand (Gold / Precious Metals)

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Precious Metals |
| **Primary keywords** | gold, safe haven, bullion, precious metals, platinum, palladium, silver, flight to safety |
| **Anchor phrases** | "flight to gold", "safe haven demand", "gold prices surge on", "bullion buying", "central bank gold purchases", "gold reserve accumulation", "precious metals rally geopolitical", "gold as hedge", "risk-off gold bid", "investor rush to gold", "gold ETF inflows", "physical gold demand", "de-dollarization gold" |
| **Disambiguation negatives** | "gold medal Olympics", "gold standard history essay", "golden age", "gold membership tier", "Gold Coast Australia", "gold jewelry fashion" |
| **Theme description** | Safe-haven demand flows into gold and precious metals driven by geopolitical risk, financial stress, or de-dollarization narratives. Covers both physical demand and ETF/futures positioning shifts. |
| **GDELT/CAMEO** | GKG: `ECON_PRICE`, `ECON_COST` |

---

### CMD_IND_027 -- Industrial Metals Disruption

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Industrial Metals |
| **Primary keywords** | copper, aluminum, nickel, zinc, tin, lithium, cobalt, rare earths, industrial metals |
| **Anchor phrases** | "copper supply disruption", "aluminum smelter closure", "nickel export ban", "rare earth export controls", "lithium supply chain", "cobalt supply Congo", "industrial metal shortage", "LME price spike", "mine closure strike", "smelter curtailment", "base metals supply shock", "critical minerals supply" |
| **Disambiguation negatives** | "copper wire theft", "aluminum can recycling", "penny copper content", "nickel and dime", "heavy metal music", "zinc vitamin supplement" |
| **Theme description** | Supply disruptions, export bans, mine closures, and demand shocks affecting industrial and critical metals. Covers copper, aluminum, nickel, zinc, tin, lithium, cobalt, and rare earth elements. |
| **GDELT/CAMEO** | GKG: `ECON_PRICE`, `MINING` |

---

### CMD_AGR_028 -- Agricultural Supply Disruption

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Agriculture |
| **Primary keywords** | wheat, grain, corn, soybean, rice, fertilizer, export ban, crop failure, drought, harvest |
| **Anchor phrases** | "grain export ban", "wheat supply disruption", "Black Sea grain deal", "fertilizer export restriction", "crop failure drought", "food price spike", "grain corridor", "agricultural export restriction", "harvest failure", "food security crisis", "grain stockpile drawdown", "rice export ban India", "corn crop damage", "soybean tariff" |
| **Disambiguation negatives** | "grain of sand", "wheat beer craft", "rice paper art", "corn maze attraction", "Whole Foods organic", "farm-to-table restaurant" |
| **Theme description** | Geopolitical or weather-driven disruptions to agricultural commodity supply including export bans, grain corridor interruptions, fertilizer restrictions, crop failures, and food security crises. |
| **GDELT/CAMEO** | GKG: `FOOD_SECURITY`, `FAMINE`, `ENV_DROUGHT`, CAMEO 163 (Embargo) |

---

### CMD_AGW_029 -- Agricultural Weather Events

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Agriculture |
| **Primary keywords** | drought, flood, frost, heatwave, El Nino, La Nina, monsoon, crop damage, growing season |
| **Anchor phrases** | "drought conditions corn belt", "flooding destroys crops", "frost damage wheat", "heatwave crop stress", "El Nino crop impact", "La Nina rainfall deficit", "monsoon failure India", "growing season shortened", "planting delayed rain", "yield estimate cut weather", "USDA crop condition downgrade" |
| **Disambiguation negatives** | "drought-resistant landscaping", "flood insurance homeowner", "frost advisory driving", "heat wave beach", "weather app review" |
| **Theme description** | Severe weather events impacting agricultural production, including droughts, floods, frost, heatwaves, and ENSO-cycle effects on crop yields. Distinguishes weather-driven supply disruptions from policy-driven disruptions. |
| **GDELT/CAMEO** | GKG: `ENV_DROUGHT`, `ENV_FLOOD`, `NATURAL_DISASTER`, `FOOD_SECURITY` |

---

### CMD_OPC_030 -- OPEC+ Policy Decisions

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Energy Complex |
| **Primary keywords** | OPEC, OPEC+, production quota, output target, Saudi Arabia oil policy, cartel |
| **Anchor phrases** | "OPEC production decision", "OPEC+ output cut", "OPEC+ meeting", "Saudi voluntary cut", "OPEC compliance", "production quota increase", "OPEC+ supply agreement", "oil production target", "OPEC spare capacity", "cartel supply decision", "OPEC ministerial meeting", "OPEC+ rollover" |
| **Disambiguation negatives** | "OPEC history documentary", "peak oil theory" |
| **Theme description** | OPEC and OPEC+ production policy decisions, quota changes, voluntary cuts, and compliance monitoring. These are deliberate supply management actions as distinct from involuntary disruptions. |
| **GDELT/CAMEO** | GKG: `ENV_OIL`, `ECON_PRICE` |

---

## Sleeve 4: Macro / Rates

### MAC_HWK_031 -- Hawkish Shock

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Hawkish Shock |
| **Primary keywords** | hawkish, rate hike, tightening, restrictive, inflation fight, higher for longer |
| **Anchor phrases** | "unexpected rate hike", "hawkish surprise", "more restrictive stance", "higher for longer", "inflation not yet conquered", "additional tightening needed", "rate path higher than expected", "dot plot shift upward", "hawkish hold", "removing accommodation faster", "insufficiently restrictive", "inflation persistence concern", "terminal rate revision higher" |
| **Disambiguation negatives** | "hawk bird watching", "hawk eye cricket", "Tony Hawk skateboard", "Hawkeye Marvel", "Black Hawk helicopter military" |
| **Theme description** | Unexpected hawkish shifts in central bank communication or policy action, including surprise rate hikes, upward dot plot revisions, hawkish hold language, and rhetoric signaling more restrictive policy than markets had priced. Primarily Fed-focused but applies to ECB/BOE/BOJ. |
| **GDELT/CAMEO** | GKG: `ECON_INTEREST_RATE`, `CENTRAL_BANK` |

---

### MAC_DOV_032 -- Easing Shock / Dovish Pivot

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Easing Shock |
| **Primary keywords** | dovish, rate cut, easing, accommodation, pivot, pause, lower rates |
| **Anchor phrases** | "unexpected rate cut", "dovish pivot", "easing cycle begins", "rate cut surprise", "removing restriction", "policy accommodation", "dovish surprise", "rate path lower", "dot plot shift downward", "dovish hold", "disinflation progress", "cutting rates sooner", "emergency rate cut", "inter-meeting cut", "balance sheet expansion" |
| **Disambiguation negatives** | "dove bird", "dove soap", "dove chocolate", "peace dove symbol", "mourning dove" |
| **Theme description** | Unexpected dovish shifts in central bank communication or policy action, including surprise rate cuts, downward dot plot revisions, early pivot language, and emergency easing measures. |
| **GDELT/CAMEO** | GKG: `ECON_INTEREST_RATE`, `CENTRAL_BANK` |

---

### MAC_CRV_033 -- Yield Curve Inversion Stress

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Curve Stress |
| **Primary keywords** | yield curve, inversion, 2s10s, term premium, steepening, flattening, bear steepener |
| **Anchor phrases** | "yield curve inversion", "2s10s spread", "curve inversion deepens", "term premium spike", "bear steepener", "bull flattener", "curve un-inversion", "recession signal yield curve", "long-end selloff", "term premium repricing", "duration risk", "curve steepening rapidly", "front-end rally" |
| **Disambiguation negatives** | "learning curve", "curve ball baseball", "bell curve statistics", "growth curve child development" |
| **Theme description** | Significant moves in the yield curve shape including inversions, steepening episodes, term premium repricing, and shifts in the 2s10s spread. These signals feed into recession probability and duration positioning. |
| **GDELT/CAMEO** | GKG: `ECON_INTEREST_RATE` |

---

### MAC_INF_034 -- Inflation Surprise

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Inflation |
| **Primary keywords** | CPI, PCE, inflation, deflation, disinflation, price index, core inflation |
| **Anchor phrases** | "CPI above expectations", "inflation surprise", "core PCE higher than forecast", "inflation reacceleration", "sticky inflation", "inflation expectations unanchored", "breakeven inflation spike", "services inflation persistent", "shelter inflation", "wage-price spiral", "deflation risk", "CPI miss", "PPI surprise" |
| **Disambiguation negatives** | "grade inflation school", "inflation adjusted historical", "tire inflation pressure", "balloon inflation party" |
| **Theme description** | Inflation data releases that deviate significantly from consensus expectations, whether hotter or cooler. Covers CPI, PCE, PPI, and inflation expectations measures. The direction of surprise determines whether this co-activates with hawkish or dovish themes. |
| **GDELT/CAMEO** | GKG: `ECON_PRICE`, `ECON_COST` |

---

### MAC_EMP_035 -- Employment Shock

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Employment |
| **Primary keywords** | jobs, NFP, unemployment, payrolls, jobless claims, labor market |
| **Anchor phrases** | "nonfarm payrolls surprise", "unemployment rate jump", "jobless claims spike", "labor market weakening", "hiring freeze", "mass layoffs", "job openings plunge", "JOLTS surprise", "wage growth accelerating", "labor market tight", "employment shock", "payrolls miss", "unemployment rate unexpected", "initial claims surge" |
| **Disambiguation negatives** | "job posting website", "career advice article", "resume tips", "job interview guide", "summer jobs students" |
| **Theme description** | Employment data releases that significantly surprise the market, including NFP misses, unemployment rate jumps, jobless claims spikes, and JOLTS data. Employment shocks feed directly into rate path expectations and recession probability. |
| **GDELT/CAMEO** | GKG: `ECON_UNEMPLOYMENT`, `LABOR` |

---

### MAC_FED_036 -- Fed Communication / FOMC

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Fed Communication |
| **Primary keywords** | FOMC, Fed, Federal Reserve, Powell, dot plot, minutes, Beige Book |
| **Anchor phrases** | "FOMC statement", "Fed meeting decision", "Powell press conference", "FOMC minutes released", "dot plot median", "summary of economic projections", "Beige Book", "Fed Chair testimony", "Fed Governor speech", "FOMC dissent", "balance sheet runoff", "quantitative tightening pace", "Fed communication" |
| **Disambiguation negatives** | "Fed Ex delivery", "federal holiday", "federal court ruling", "federal prison", "federal highway" |
| **Theme description** | Federal Reserve communications including FOMC statements, press conferences, meeting minutes, dot plot releases, Beige Book, and individual Fed official speeches. The raw material for hawkish/dovish classification. |
| **GDELT/CAMEO** | GKG: `CENTRAL_BANK`, `ECON_INTEREST_RATE` |

---

### MAC_ECB_037 -- ECB Communication

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (ex-US) / ECB |
| **Primary keywords** | ECB, Lagarde, Governing Council, eurozone rates, TPI, PEPP, APP |
| **Anchor phrases** | "ECB rate decision", "Lagarde press conference", "ECB Governing Council", "eurozone inflation", "transmission protection instrument", "ECB staff projections", "ECB hawkish", "ECB dovish", "fragmentation risk eurozone", "European rates path", "ECB quantitative tightening", "ECB meeting" |
| **Disambiguation negatives** | "European Championship football", "ECB cricket", "euro coin collecting" |
| **Theme description** | European Central Bank rate decisions, Governing Council communications, staff projections, and individual Executive Board member speeches. Feeds the ex-US rates sleeve. |
| **GDELT/CAMEO** | GKG: `CENTRAL_BANK`, `ECON_INTEREST_RATE` |

---

### MAC_BOE_038 -- Bank of England Communication

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (ex-US) / BOE |
| **Primary keywords** | BOE, Bank of England, MPC, Bailey, gilt, sterling rates |
| **Anchor phrases** | "Bank of England rate decision", "MPC vote split", "Bailey speech", "gilt market stress", "UK inflation surprise", "MPC hawkish majority", "BOE dovish pivot", "UK rates path", "gilt yield spike", "sterling rates market", "BOE financial stability" |
| **Disambiguation negatives** | "Bank of England museum", "Old Lady of Threadneedle Street history", "British pound coin design" |
| **Theme description** | Bank of England Monetary Policy Committee decisions, communications, and UK rates market reactions. Includes gilt market stress events that may require BOE intervention. |
| **GDELT/CAMEO** | GKG: `CENTRAL_BANK`, `ECON_INTEREST_RATE` |

---

### MAC_BOJ_039 -- Bank of Japan Communication

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (ex-US) / BOJ |
| **Primary keywords** | BOJ, Bank of Japan, Ueda, YCC, yield curve control, JGB, yen |
| **Anchor phrases** | "BOJ rate decision", "yield curve control adjustment", "BOJ policy normalization", "JGB yield cap", "BOJ rate hike", "negative interest rate exit", "BOJ surprise", "Ueda press conference", "yen intervention", "BOJ balance sheet", "JGB market function", "BOJ forward guidance" |
| **Disambiguation negatives** | "Japanese gardens", "Japan tourism visa", "anime Japan", "Toyota quarterly" |
| **Theme description** | Bank of Japan policy decisions, yield curve control adjustments, and yen intervention actions. BOJ is uniquely important because its policy shifts can trigger global carry trade unwinds and cross-asset volatility. |
| **GDELT/CAMEO** | GKG: `CENTRAL_BANK`, `ECON_INTEREST_RATE` |

---

### MAC_LIQ_040 -- Liquidity / Financial Plumbing Stress

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Financial Stress |
| **Primary keywords** | repo, reverse repo, TGA, bank reserves, liquidity, BTFP, discount window, funding stress |
| **Anchor phrases** | "repo rate spike", "reverse repo facility drain", "Treasury General Account drawdown", "bank reserves falling", "funding market stress", "discount window borrowing surge", "BTFP usage", "money market strain", "collateral shortage", "Treasury bill supply", "liquidity conditions tightening", "balance sheet capacity constraints" |
| **Disambiguation negatives** | "liquidity in stocks trading volume", "liquid assets personal finance", "liquid diet health", "repo man movie" |
| **Theme description** | Stress in funding markets and financial plumbing including repo rate spikes, reserve scarcity, TGA swings, and emergency facility usage. These often precede broader market stress and can force Fed policy responses. |
| **GDELT/CAMEO** | GKG: `ECON_INTEREST_RATE`, `ECON_BANKRUPTCY` |

---

### MAC_REC_041 -- Recession Indicators

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Recession |
| **Primary keywords** | recession, GDP contraction, economic downturn, hard landing, Sahm rule, LEI |
| **Anchor phrases** | "recession probability rising", "GDP contraction unexpected", "economic recession signal", "hard landing risk", "Sahm rule triggered", "leading economic indicators decline", "PMI contraction territory", "ISM below 50", "consumer confidence plunge", "credit conditions tightening", "economic slowdown deepening" |
| **Disambiguation negatives** | "recession-proof business tips", "recession haircut style", "gum recession dental" |
| **Theme description** | Macroeconomic indicators and signals pointing to recession risk, including GDP misses, PMI/ISM contraction, Sahm rule triggers, and leading indicator deterioration. Informs rate path expectations and risk-off positioning. |
| **GDELT/CAMEO** | GKG: `ECON_UNEMPLOYMENT`, `ECON_BANKRUPTCY` |

---

## Sleeve 5: Crypto Behavioral

### CRY_RON_042 -- Crypto Risk-On Beta

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Crypto / Risk-On Beta |
| **Primary keywords** | bitcoin, crypto, BTC, ETH, altcoin, risk-on, correlation equities |
| **Anchor phrases** | "crypto rallying with equities", "bitcoin risk-on move", "crypto correlated with Nasdaq", "BTC following tech stocks", "risk appetite crypto", "crypto leverage long buildup", "bitcoin futures open interest surge", "altcoin rally broad", "crypto as risk asset", "meme coin frenzy", "crypto beta trade" |
| **Disambiguation negatives** | "cryptography course", "crypto wallet stolen scam", "cryptocurrency tax guide", "blockchain developer job" |
| **Theme description** | Regime where crypto assets behave as high-beta risk assets correlated with equities and broader risk sentiment. In this mode, crypto follows equity moves and benefits from risk-on flows. Key for determining whether crypto sleeve should be treated as risk amplifier or diversifier. |
| **GDELT/CAMEO** | GKG: limited crypto coverage; rely on specialized feeds |

---

### CRY_FLT_043 -- Crypto Capital Flight / Store of Value

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Crypto / Capital Flight |
| **Primary keywords** | bitcoin, capital flight, store of value, de-dollarization, capital controls, sanctions evasion crypto |
| **Anchor phrases** | "bitcoin as safe haven", "crypto capital flight", "bitcoin decoupling from equities", "digital gold narrative", "capital controls driving crypto adoption", "bitcoin premium emerging markets", "crypto as sanctions workaround", "stablecoin demand capital flight", "bitcoin store of value", "crypto haven from inflation", "Tether demand emerging market", "bitcoin premium Nigeria Turkey" |
| **Disambiguation negatives** | "flight delay airline", "capital gains tax", "Capital One bank", "flight simulator game" |
| **Theme description** | Regime where crypto, particularly bitcoin and stablecoins, acts as a capital flight vehicle or alternative store of value. Characterized by crypto decoupling from equities, emerging market premiums, and demand driven by capital controls, sanctions, or currency debasement. |
| **GDELT/CAMEO** | GKG: limited; combine with sanctions and capital control themes |

---

### CRY_REG_044 -- Crypto Regulatory Shock

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Crypto / Regulatory Shock |
| **Primary keywords** | SEC crypto, crypto regulation, crypto ban, CFTC, MiCA, stablecoin regulation, CBDC |
| **Anchor phrases** | "SEC enforcement crypto", "crypto exchange crackdown", "crypto trading ban", "stablecoin regulation bill", "CBDC launch", "digital asset regulation", "crypto securities classification", "exchange delisting", "crypto exchange license revoked", "mining ban crypto", "DeFi regulation", "crypto tax reporting rule", "Wells notice crypto" |
| **Disambiguation negatives** | "SEC football conference", "regular season sports", "regulation size football", "regulatory T margin stock" |
| **Theme description** | Government regulatory actions affecting crypto markets including SEC enforcement, exchange crackdowns, trading bans, stablecoin legislation, CBDC launches, and mining restrictions. Sudden regulatory actions can cause sharp crypto price moves and regime shifts. |
| **GDELT/CAMEO** | GKG: `LEGISLATION`, `REGULATION` |

---

### CRY_LIQ_045 -- Crypto Market Structure Stress

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Crypto / Market Structure |
| **Primary keywords** | exchange collapse, crypto contagion, stablecoin depeg, liquidation cascade, crypto insolvency |
| **Anchor phrases** | "crypto exchange insolvency", "stablecoin depeg event", "crypto liquidation cascade", "exchange withdrawal halt", "crypto contagion spreading", "proof of reserves concern", "crypto lender collapse", "DeFi protocol exploit", "bridge hack crypto", "stablecoin redemption run", "crypto market maker withdrawal", "exchange proof of reserves" |
| **Disambiguation negatives** | "stock exchange holiday", "foreign exchange rate", "exchange rate tourist", "student exchange program" |
| **Theme description** | Structural stress events in crypto markets including exchange collapses, stablecoin de-pegs, liquidation cascades, and contagion events. These can trigger regime shifts between risk-on beta and capital flight behavior. |
| **GDELT/CAMEO** | GKG: `ECON_BANKRUPTCY` |

---

## Sleeve 6: Sanctions & Trade Restrictions

### SNC_NEW_046 -- New Sanctions Designations

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Sanctions & Trade / New Designations |
| **Primary keywords** | sanctions, SDN, designated, blacklisted, OFAC, sanctioned entity, asset freeze |
| **Anchor phrases** | "new sanctions imposed on", "added to SDN list", "sanctions designation", "asset freeze order", "sanctions package announced", "entity sanctioned by", "secondary sanctions threat", "sanctions on Russian", "Iran sanctions new", "North Korea sanctions", "Venezuela sanctions", "designated under Executive Order", "Global Magnitsky designation" |
| **Disambiguation negatives** | "economic sanctions history essay", "sanction as approval", "sanctioned by the church", "officially sanctioned event meaning approved" |
| **Theme description** | New sanctions designations by US (OFAC), EU, UK, or UN against individuals, entities, or sectors. These are discrete events that create immediate compliance obligations and can disrupt trade flows, financial transactions, and commodity markets. |
| **GDELT/CAMEO** | CAMEO 163 (Impose embargo), 171-174 (Sanctions), GKG: `TAX_FNCACT_SANCTIONS` |

---

### SNC_TGT_047 -- Sanctions Tightening

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Sanctions & Trade / Tightening |
| **Primary keywords** | sanctions tightening, enforcement, compliance, loophole, circumvention, secondary sanctions |
| **Anchor phrases** | "sanctions enforcement intensified", "closing sanctions loopholes", "secondary sanctions imposed", "sanctions compliance crackdown", "sanctions evasion network dismantled", "tightening existing sanctions", "broadening sanctions scope", "sanctions package expanded", "compliance deadline", "sanctions penalty levied", "correspondent banking cut off", "de-risking sanctions" |
| **Disambiguation negatives** | "skin tightening cosmetic", "bolt tightening torque", "tightening labor market" |
| **Theme description** | Intensification of existing sanctions regimes through expanded scope, stricter enforcement, secondary sanctions threats, loophole closure, and compliance crackdowns. Distinct from new designations; this is about making existing sanctions bite harder. |
| **GDELT/CAMEO** | CAMEO 173 (Impose sanctions), GKG: `TAX_FNCACT_SANCTIONS` |

---

### SNC_LSN_048 -- Sanctions Loosening / Waivers

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Sanctions & Trade / Loosening |
| **Primary keywords** | sanctions relief, waiver, license, exemption, sanctions easing, delisting, unfreeze |
| **Anchor phrases** | "sanctions relief granted", "general license issued", "sanctions waiver", "sanctions exemption", "removed from SDN list", "sanctions lifted on", "asset unfreeze order", "sanctions easing", "nuclear deal sanctions relief", "humanitarian exemption sanctions", "wind-down period granted", "delisted from sanctions" |
| **Disambiguation negatives** | "driver's license renewal", "software license agreement", "creative commons license", "fishing license" |
| **Theme description** | Relaxation of sanctions through formal relief, waivers, general licenses, delistings, and exemptions. Can signal geopolitical de-escalation and potentially unlock commodity supply or trade flows previously restricted. |
| **GDELT/CAMEO** | CAMEO 164 (Reduce or stop sanctions), GKG: `TAX_FNCACT_SANCTIONS` |

---

### SNC_TRF_049 -- Tariff Escalation / Trade War

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Sanctions & Trade / Tariffs |
| **Primary keywords** | tariff, trade war, duties, import tax, retaliatory tariff, Section 301, Section 232 |
| **Anchor phrases** | "tariff increase announced", "retaliatory tariffs imposed", "trade war escalation", "Section 301 tariffs", "Section 232 investigation", "anti-dumping duties", "countervailing duties", "tariff threat", "import duties raised", "trade war retaliation", "tariff list expanded", "most-favored-nation tariff suspended", "reciprocal tariffs" |
| **Disambiguation negatives** | "tariff mobile phone plan", "electricity tariff household", "water tariff rate", "toll road tariff" |
| **Theme description** | Escalation in trade restrictions through new tariffs, tariff increases, retaliatory duties, and trade war rhetoric. Covers both US-China tariff dynamics and broader protectionist actions. Affects commodity flows, supply chains, and corporate margins. |
| **GDELT/CAMEO** | CAMEO 161 (Halt trade), 163 (Impose embargo), GKG: `ECON_TRADE`, `TAX_FNCACT_SANCTIONS` |

---

### SNC_TRD_050 -- Tariff De-escalation / Trade Agreement

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Sanctions & Trade / Trade Agreement |
| **Primary keywords** | trade deal, trade agreement, tariff reduction, tariff exemption, trade talks progress, tariff rollback |
| **Anchor phrases** | "trade deal announced", "tariff rollback agreed", "trade agreement signed", "tariff exemption granted", "trade talks progress", "tariff reduction phase", "trade war de-escalation", "trade normalization", "most-favored-nation restored", "trade barrier removal", "free trade agreement" |
| **Disambiguation negatives** | "deal of the day shopping", "trade school enrollment", "stock trade executed", "trade deadline NBA" |
| **Theme description** | De-escalation of trade conflicts through agreements, tariff reductions, exemptions, and constructive negotiations. The inverse of tariff escalation, signaling improved trade conditions and potentially lower input costs. |
| **GDELT/CAMEO** | CAMEO 0561 (Cooperate economically), GKG: `ECON_TRADE` |

---

### SNC_EXP_051 -- Export Controls (Technology / Chips)

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Sanctions & Trade / Export Controls |
| **Primary keywords** | export controls, chip ban, semiconductor restriction, entity list, BIS, technology transfer, dual-use |
| **Anchor phrases** | "chip export ban", "semiconductor export controls", "added to entity list", "BIS export restriction", "technology transfer ban", "dual-use technology restriction", "advanced chip restriction", "EUV lithography export ban", "AI chip export control", "computing power restriction", "Wassenaar Arrangement", "deemed export rule", "foreign direct product rule" |
| **Disambiguation negatives** | "chip and dip recipe", "poker chips", "wood chips mulch", "chip shot golf", "fish and chips" |
| **Theme description** | Government restrictions on technology exports, particularly semiconductors, AI chips, advanced computing, and dual-use technologies. Primarily covers US-China technology decoupling but also includes multilateral export control regime actions. |
| **GDELT/CAMEO** | CAMEO 163 (Impose embargo), GKG: `TAX_FNCACT_SANCTIONS`, `TECH` |

---

### SNC_FRZ_052 -- Financial Sanctions / Asset Freezes

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Sanctions & Trade / Financial Sanctions |
| **Primary keywords** | asset freeze, SWIFT, correspondent banking, central bank reserves frozen, financial sanctions |
| **Anchor phrases** | "SWIFT disconnection", "central bank reserves frozen", "correspondent banking severed", "financial sanctions imposed", "dollar access cut off", "sovereign asset freeze", "reserve confiscation", "blocked property", "prohibited transactions", "financial system exclusion", "payment channel blocked", "capital market restrictions" |
| **Disambiguation negatives** | "frozen food aisle", "bank account frozen overdraft", "credit card frozen lost", "frozen movie Disney", "Swift Taylor singer" |
| **Theme description** | Financial sanctions targeting banking access, SWIFT connectivity, central bank reserves, and capital market participation. The most economically severe form of sanctions, with direct implications for currency values, sovereign debt, and trade finance. |
| **GDELT/CAMEO** | CAMEO 173, GKG: `TAX_FNCACT_SANCTIONS`, `ECON_BANKRUPTCY` |

---

## Cross-Sleeve Themes

These themes span multiple sleeves and may co-activate with sleeve-specific themes.

### XSL_ESC_053 -- Geopolitical Escalation (General)

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Escalation |
| **Primary keywords** | escalation, tensions, brinkmanship, ultimatum, mobilization, provocation |
| **Anchor phrases** | "tensions escalating between", "military buildup near border", "diplomatic crisis", "embassy recalled", "ambassador expelled", "ultimatum issued", "military mobilization ordered", "national emergency declared", "threat level raised", "nuclear threat rhetoric", "provocative military action", "red line crossed" |
| **Disambiguation negatives** | "escalation clause contract", "escalator repair", "de-escalation training police", "escalation matrix customer service" |
| **Theme description** | General geopolitical escalation signals that may activate multiple sleeves simultaneously. A major escalation event (e.g., new conflict theater opening) triggers defense, shipping, commodity, and potentially rates themes concurrently. This theme acts as a cross-sleeve amplifier. |
| **GDELT/CAMEO** | CAMEO 13x-14x (Threaten), 17x (Coerce), Goldstein scale < -5.0 |

---

### XSL_DES_054 -- Geopolitical De-escalation

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / De-escalation |
| **Primary keywords** | de-escalation, ceasefire, peace talks, truce, diplomatic resolution, negotiations |
| **Anchor phrases** | "ceasefire agreement reached", "peace talks announced", "diplomatic breakthrough", "truce declared", "tensions easing", "de-escalation measures", "troops withdrawing", "prisoner exchange", "diplomatic channel reopened", "peace framework", "conflict resolution", "hostilities suspended" |
| **Disambiguation negatives** | "de-escalation customer service training", "conflict resolution workplace HR" |
| **Theme description** | Geopolitical de-escalation events including ceasefires, peace negotiations, troop withdrawals, and diplomatic breakthroughs. The inverse of escalation, potentially unwinding risk premia across defense, commodity, and shipping themes. |
| **GDELT/CAMEO** | CAMEO 03x-05x (Cooperate), Goldstein scale > 5.0 |

---

### XSL_VOL_055 -- Cross-Asset Volatility Spike

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Volatility |
| **Primary keywords** | VIX, volatility, MOVE index, risk-off, panic, selloff, contagion |
| **Anchor phrases** | "VIX spike above", "volatility surge", "risk-off selloff", "cross-asset contagion", "MOVE index surge", "panic selling", "flight to quality", "margin call cascade", "volatility regime shift", "correlation spike", "everything selloff", "liquidity evaporation" |
| **Disambiguation negatives** | "volatile personality", "volatile organic compound", "market volatility normal", "volatility trading strategy guide" |
| **Theme description** | Sharp cross-asset volatility spikes that indicate regime shifts in risk sentiment. These events affect portfolio construction across all sleeves through correlation changes, liquidity conditions, and risk budget recalculation. Used by the market pricing and complacency expert. |
| **GDELT/CAMEO** | GKG: `ECON_BANKRUPTCY`, `ECON_PRICE` |

---

### XSL_USD_056 -- USD Shock / Dollar Regime

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / FX |
| **Primary keywords** | dollar, DXY, USD, greenback, dollar index, dollar strength, dollar weakness |
| **Anchor phrases** | "dollar surge", "DXY breakout", "dollar weakness broad-based", "USD rally", "dollar funding stress", "eurodollar market", "dollar liquidity", "dollar smile", "safe haven dollar bid", "dollar wrecking ball", "emerging market FX pressure", "dollar milkshake theory" |
| **Disambiguation negatives** | "dollar store shopping", "dollar menu fast food", "silver dollar coin collecting", "million dollar listing TV" |
| **Theme description** | Significant USD moves and dollar regime shifts. Dollar strength/weakness affects commodity pricing, emerging market stress, crypto capital flight behavior, and cross-border trade economics. A cross-sleeve factor that modulates other themes. |
| **GDELT/CAMEO** | GKG: `ECON_CURRENCY` |

---

### XSL_EMR_057 -- Emerging Market Stress

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / EM Stress |
| **Primary keywords** | emerging market, EM, capital outflow, currency crisis, sovereign default, IMF bailout |
| **Anchor phrases** | "emerging market selloff", "EM currency crisis", "capital outflows emerging", "sovereign default risk", "IMF bailout requested", "EM bond spread widening", "foreign reserve depletion", "EM contagion", "frontier market stress", "hot money outflow", "current account crisis", "balance of payments crisis" |
| **Disambiguation negatives** | "emerging artist", "emerging technology trend", "emerging market ETF dividend" |
| **Theme description** | Stress events in emerging markets including currency crises, capital outflows, sovereign default risks, and IMF interventions. Relevant to rates (ex-US), commodities (demand shock), and crypto (capital flight) sleeves simultaneously. |
| **GDELT/CAMEO** | GKG: `ECON_BANKRUPTCY`, `ECON_CURRENCY` |

---

## Regional Conflict Themes

These provide geographic localization for conflict escalation signals.

### REG_UKR_058 -- Ukraine / Russia Theater

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Regional -- Ukraine |
| **Primary keywords** | Ukraine, Kyiv, Kharkiv, Donbas, Crimea, Zaporizhzhia, Russia-Ukraine |
| **Anchor phrases** | "Ukraine frontline", "Russian offensive Ukraine", "Ukrainian counter-offensive", "Crimea attack", "Donbas escalation", "Zaporizhzhia nuclear plant", "Ukraine aid package", "NATO Ukraine", "grain corridor Ukraine", "Black Sea mine Ukraine", "Ukraine mobilization", "Russia-Ukraine negotiations" |
| **Disambiguation negatives** | "Ukrainian restaurant", "Ukraine Eurovision", "Kyiv Dynamo football" |
| **Theme description** | Military developments, escalation/de-escalation, and geopolitical dynamics specific to the Russia-Ukraine conflict theater. Activates defense, Black Sea shipping, grain commodity, energy, and sanctions themes. The single most cross-connected regional theme. |
| **GDELT/CAMEO** | Actor filter: RUS, UKR; Geolocation: Ukraine bounding box |

---

### REG_MEA_059 -- Middle East Escalation

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Regional -- Middle East |
| **Primary keywords** | Iran, Israel, Hezbollah, Hamas, Syria, Iraq militia, IRGC, Gulf tensions |
| **Anchor phrases** | "Iran-Israel tensions", "Hezbollah rocket attack", "IRGC proxy strike", "Middle East escalation", "Gulf security alert", "Israel-Iran confrontation", "Syria airstrike Israel", "Iraq militia drone", "Iran nuclear", "regional conflagration Middle East", "Axis of Resistance", "Israeli defense operation" |
| **Disambiguation negatives** | "Middle Eastern cuisine", "Middle East airline review", "Dead Sea spa", "Israeli tech startup funding" |
| **Theme description** | Escalation dynamics in the broader Middle East including Iran-Israel tensions, proxy conflicts, Gulf security, and multi-front scenarios. Cross-activates Hormuz shipping, Bab el-Mandeb, oil supply risk, defense, and safe-haven themes. |
| **GDELT/CAMEO** | Actor filter: ISR, IRN, SYR, IRQ; Goldstein < -5 |

---

### REG_SCS_060 -- South China Sea

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Regional -- South China Sea |
| **Primary keywords** | South China Sea, Spratlys, Paracels, Scarborough Shoal, nine-dash line, Philippine coast guard, PLAN |
| **Anchor phrases** | "South China Sea confrontation", "China coast guard Philippines", "Scarborough Shoal incident", "Second Thomas Shoal", "water cannon Philippine vessel", "artificial island militarization", "freedom of navigation operation", "FONOP South China Sea", "maritime militia Chinese", "exclusive economic zone dispute SCS" |
| **Disambiguation negatives** | "Chinese New Year", "China GDP quarterly", "Chinese restaurant" |
| **Theme description** | Territorial disputes and military incidents in the South China Sea involving China, Philippines, Vietnam, and other claimants. Affects Malacca/regional shipping risk, Taiwan contingency probability, and defense spending themes. |
| **GDELT/CAMEO** | Actor filter: CHN, PHL; Geolocation: SCS bounding box |

---

### REG_KOR_061 -- Korean Peninsula

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Regional -- Korea |
| **Primary keywords** | North Korea, DPRK, Kim Jong Un, Pyongyang, Korean peninsula, DMZ, ICBM test |
| **Anchor phrases** | "North Korea missile launch", "DPRK nuclear test", "Korean peninsula tensions", "DMZ provocation", "ICBM test North Korea", "Pyongyang threat", "UN Security Council North Korea", "THAAD deployment Korea", "inter-Korean", "denuclearization talks", "provocation cycle DPRK" |
| **Disambiguation negatives** | "Korean drama Netflix", "K-pop", "Korean BBQ restaurant", "Korean skincare routine", "Seoul fashion week" |
| **Theme description** | Security developments on the Korean Peninsula including DPRK missile and nuclear tests, provocations, and diplomatic cycles. Triggers defense (missile defense) and safe-haven themes. |
| **GDELT/CAMEO** | Actor filter: PRK, KOR |

---

### REG_IND_062 -- India-Pakistan / India-China Border

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Regional -- South Asia |
| **Primary keywords** | India-Pakistan, Kashmir, LAC, Ladakh, Galwan, Arunachal, India-China border |
| **Anchor phrases** | "India-Pakistan border clash", "Kashmir escalation", "Line of Actual Control incident", "Ladakh standoff", "India-China border tensions", "surgical strike India", "cross-border firing LoC", "Arunachal Pradesh incursion", "Galwan-type incident", "India military mobilization border" |
| **Disambiguation negatives** | "India cricket match", "Bollywood release", "Indian wedding season", "India monsoon forecast farmer" |
| **Theme description** | Border tensions and military incidents along India-Pakistan (Line of Control, Kashmir) and India-China (Line of Actual Control, Ladakh, Arunachal) borders. Affects India port clusters, defense spending, and regional shipping. |
| **GDELT/CAMEO** | Actor filter: IND, PAK, CHN; geolocation: border regions |

---

## Additional Defense Sub-themes

### DEF_UAS_063 -- Unmanned Systems / Drones

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Unmanned Systems |
| **Primary keywords** | drone, UAV, UAS, unmanned, loitering munition, autonomous, UCAV |
| **Anchor phrases** | "drone warfare", "unmanned aerial vehicle contract", "loitering munition deployment", "drone swarm", "counter-UAS system", "autonomous weapons", "drone strike military", "combat drone procurement", "unmanned combat aerial vehicle", "drone defense system", "FPV drone warfare", "naval drone USV" |
| **Disambiguation negatives** | "drone photography hobby", "drone delivery Amazon", "drone racing sport", "DJI consumer drone", "drone light show entertainment", "agricultural drone spraying" |
| **Theme description** | Military unmanned systems including combat drones, loitering munitions, counter-UAS systems, autonomous weapons, and unmanned surface/underwater vehicles. A rapidly growing defense sub-domain with high procurement activity. |
| **GDELT/CAMEO** | GKG: `MILITARY`, `DRONE` |

---

### DEF_AID_064 -- Military Aid & Arms Transfers

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Defense & Security / Arms Transfers |
| **Primary keywords** | military aid, arms transfer, weapons delivery, security assistance, arms package, FMS |
| **Anchor phrases** | "military aid package approved", "arms delivery to Ukraine", "weapons transfer", "security assistance package", "Presidential Drawdown Authority", "foreign military financing", "arms sale notification Congress", "DSCA notification", "defense articles transfer", "military equipment delivered" |
| **Disambiguation negatives** | "humanitarian aid delivery", "food aid shipment", "medical aid mission", "financial aid student" |
| **Theme description** | International military aid packages, arms transfers, and security assistance deliveries. These events signal escalation commitment and directly benefit defense contractors. Distinct from defense spending policy (which is domestic budget). |
| **GDELT/CAMEO** | CAMEO 0831 (Provide military aid), 0832 |

---

## Additional Shipping Themes

### SHP_LBR_065 -- Port Labor Disruption

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Port Labor |
| **Primary keywords** | dock strike, port strike, longshoremen, stevedore, ILWU, ILA, port workers |
| **Anchor phrases** | "dockworker strike", "port labor dispute", "longshoremen walkout", "ILWU contract negotiation", "ILA strike threat", "port automation dispute", "stevedore labor action", "port worker stoppage", "terminal operator labor", "port congestion labor" |
| **Disambiguation negatives** | "dock fishing", "loading dock warehouse", "dock connector Apple", "dry dock boat maintenance" |
| **Theme description** | Labor disputes and strikes at ports that disrupt cargo operations. These can cause sudden supply chain bottlenecks and freight rate spikes independent of geopolitical events. |
| **GDELT/CAMEO** | GKG: `LABOR`, `PROTEST` |

---

### SHP_SCN_066 -- South China Sea Shipping Route

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Regional Route -- SCS |
| **Primary keywords** | South China Sea shipping, SCS route, Luzon Strait, Karimata Strait, shipping lane SCS |
| **Anchor phrases** | "South China Sea shipping route", "shipping rerouted from SCS", "Luzon Strait transit", "SCS maritime exclusion zone", "container traffic South China Sea", "commercial shipping South China Sea diversion", "naval exercise disrupting SCS shipping" |
| **Disambiguation negatives** | (Same as REG_SCS_060 negatives) |
| **Theme description** | Commercial shipping route disruptions through the South China Sea, distinct from the territorial/military theme (REG_SCS_060). Focuses on actual traffic diversions, route changes, and commercial shipping impact. |
| **GDELT/CAMEO** | Geolocation: SCS shipping lanes |

---

### SHP_IOC_067 -- Indian Ocean Route

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Shipping & Supply Chain / Regional Route -- Indian Ocean |
| **Primary keywords** | Indian Ocean, Cape route, Cape of Good Hope, Mozambique Channel, Indian Ocean shipping |
| **Anchor phrases** | "Cape of Good Hope rerouting cost", "Indian Ocean shipping lane", "Mozambique Channel transit", "Indian Ocean piracy", "longer transit via Cape", "Cape route fuel cost", "Indian Ocean naval presence", "Cape of Good Hope transit time" |
| **Disambiguation negatives** | "Cape Town tourism", "Cape Cod vacation", "Good Hope hospital" |
| **Theme description** | Shipping activity and disruptions along Indian Ocean routes, particularly the Cape of Good Hope alternative when Red Sea/Suez routes are compromised. Extended transit times via this route have direct freight cost implications. |
| **GDELT/CAMEO** | Geolocation: Indian Ocean corridor |

---

## Additional Commodity Themes

### CMD_URN_068 -- Uranium / Nuclear Fuel

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Energy Complex |
| **Primary keywords** | uranium, yellowcake, enrichment, nuclear fuel, U3O8, conversion, SWU |
| **Anchor phrases** | "uranium spot price", "yellowcake supply", "uranium enrichment capacity", "nuclear fuel supply chain", "U3O8 price", "uranium mine production", "conversion capacity shortage", "enrichment services", "uranium stockpile", "Kazatomprom production", "Cameco output" |
| **Disambiguation negatives** | "uranium glass antique", "depleted uranium military" (-> DEF_MUN_001), "uranium element periodic table chemistry" |
| **Theme description** | Uranium and nuclear fuel supply chain dynamics including mining production, enrichment capacity, conversion services, and spot/term pricing. Relevant both as a commodity play and through nuclear energy policy shifts. |
| **GDELT/CAMEO** | GKG: `NUCLEAR`, `MINING` |

---

### CMD_FRT_069 -- Freight Rate Indices (Dry Bulk / Container)

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Freight |
| **Primary keywords** | BDI, freight rate, Capesize, Panamax, Supramax, container rate, charter rate |
| **Anchor phrases** | "Baltic Dry Index surge", "Capesize rate spike", "container freight rate increase", "charter rate market", "Panamax earnings", "Supramax daily rate", "freight market tightening", "tonnage shortage", "vessel supply tight", "time charter equivalent", "spot rate container" |
| **Disambiguation negatives** | "freight train derailment", "freight elevator building", "Amazon freight service" |
| **Theme description** | Freight rate indices and charter market dynamics for dry bulk and container shipping. BDI and container indices serve as real-time supply chain stress indicators and commodity demand proxies. Overlaps with but is distinct from insurance/war risk stress (SHP_INS_019). |
| **GDELT/CAMEO** | GKG: `ECON_PRICE` |

---

### CMD_MET_070 -- Critical Minerals & Supply Chain

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Commodities / Industrial Metals |
| **Primary keywords** | rare earths, gallium, germanium, graphite, manganese, critical minerals, supply chain reshoring |
| **Anchor phrases** | "rare earth export restriction China", "gallium export controls", "germanium supply disruption", "critical minerals partnership", "supply chain diversification", "friend-shoring minerals", "critical minerals processing", "battery materials supply", "mineral supply chain security", "EV battery supply chain" |
| **Disambiguation negatives** | "rare earth magnet hobby", "mineral water brand", "mineral makeup cosmetics" |
| **Theme description** | Critical minerals supply chain security and disruptions, particularly Chinese export restrictions on processing-dominant minerals like rare earths, gallium, and germanium. Intersects with export controls (SNC_EXP_051) and industrial metals (CMD_IND_027). |
| **GDELT/CAMEO** | GKG: `MINING`, `ECON_TRADE` |

---

## Additional Macro Themes

### MAC_FIS_071 -- Fiscal Policy Shock

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Fiscal |
| **Primary keywords** | fiscal, deficit, government shutdown, debt ceiling, spending bill, stimulus, austerity |
| **Anchor phrases** | "government shutdown threat", "debt ceiling deadline", "fiscal deficit widening", "spending bill passed", "fiscal stimulus package", "austerity measures", "bond vigilante", "Treasury issuance surge", "fiscal sustainability concern", "unfunded spending", "continuing resolution", "sequestration" |
| **Disambiguation negatives** | "fiscal year company earnings", "fiscal responsibility personal finance" |
| **Theme description** | Fiscal policy events including government shutdown risks, debt ceiling standoffs, major spending bills, and fiscal sustainability concerns. Affects Treasury supply, term premium, and deficit expectations. |
| **GDELT/CAMEO** | GKG: `LEGISLATION`, `ECON_DEBT` |

---

### MAC_CRD_072 -- Credit Stress / Spread Widening

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (US) / Credit |
| **Primary keywords** | credit spread, high yield, investment grade, default rate, corporate bond, CDS |
| **Anchor phrases** | "credit spreads widening", "high yield spread blow-out", "investment grade downgrade", "corporate default wave", "CDS spread surge", "credit conditions tightening", "leveraged loan stress", "CLO distress", "covenant-lite concern", "credit market freeze", "fallen angel bond" |
| **Disambiguation negatives** | "credit card rewards", "credit score personal", "credit union membership", "credit repair service" |
| **Theme description** | Corporate credit market stress including spread widening, rising default rates, rating downgrades, and credit market liquidity deterioration. A leading indicator of broader financial stress. |
| **GDELT/CAMEO** | GKG: `ECON_BANKRUPTCY`, `ECON_DEBT` |

---

### MAC_CNY_073 -- China Macro Shock

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Rates (ex-US) / China |
| **Primary keywords** | PBOC, China GDP, yuan devaluation, Chinese economy, property crisis, stimulus China |
| **Anchor phrases** | "PBOC rate cut", "China GDP miss", "yuan weakening", "Chinese property developer default", "China stimulus package", "Chinese economic slowdown", "capital outflow China", "PBOC intervention", "China deflation", "Chinese manufacturing PMI contraction", "China credit impulse", "RRR cut China" |
| **Disambiguation negatives** | "Chinese restaurant review", "Chinese New Year celebration", "Chinese language course", "Chinatown San Francisco" |
| **Theme description** | Major Chinese macroeconomic developments including PBOC policy, GDP surprises, property sector stress, stimulus announcements, and yuan management. China's macro trajectory affects commodities demand, global trade flows, and risk sentiment broadly. |
| **GDELT/CAMEO** | Actor filter: CHN; GKG: `CENTRAL_BANK`, `ECON_PRICE` |

---

## Additional Cross-Sleeve Themes

### XSL_ELN_074 -- Election / Political Transition Risk

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Political Risk |
| **Primary keywords** | election, coup, regime change, political crisis, impeachment, constitutional crisis |
| **Anchor phrases** | "election uncertainty", "disputed election results", "military coup", "regime change", "political crisis deepening", "impeachment proceedings", "constitutional crisis", "snap election called", "election violence", "political instability", "government collapse coalition", "contested transition of power" |
| **Disambiguation negatives** | "election night party", "student council election", "beauty pageant election", "hall of fame election" |
| **Theme description** | Political transition events and election risks that can trigger policy uncertainty, geopolitical realignment, and market regime shifts. Particularly important when elections affect defense spending policy, trade relationships, or sanctions frameworks. |
| **GDELT/CAMEO** | CAMEO 020 (Appeal leadership), GKG: `ELECTION`, `POLITICAL_TURMOIL` |

---

### XSL_NUK_075 -- Nuclear Proliferation / WMD Threat

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / WMD |
| **Primary keywords** | nuclear proliferation, WMD, chemical weapons, biological weapons, IAEA, enrichment breakout |
| **Anchor phrases** | "nuclear breakout timeline", "IAEA inspection denied", "enrichment threshold exceeded", "weapons-grade uranium detected", "chemical weapons use confirmed", "WMD threat assessment", "nuclear weapons program", "biological weapons lab", "dirty bomb threat", "nuclear threshold state" |
| **Disambiguation negatives** | "nuclear family sociology", "nuclear option senate filibuster", "weapons-grade coffee joke" |
| **Theme description** | WMD proliferation developments including nuclear weapons program advancement, IAEA inspection issues, chemical/biological weapons incidents, and breakout timeline assessments. Extreme tail risk events that can trigger multi-sleeve activation. |
| **GDELT/CAMEO** | GKG: `WMD`, `NUCLEAR`; CAMEO 195 (Use WMD) |

---

### XSL_CLM_076 -- Climate / Natural Disaster Impact

| Field | Value |
|---|---|
| **Sleeve / Sub-sleeve** | Cross-Sleeve / Climate-Disaster |
| **Primary keywords** | hurricane, typhoon, cyclone, earthquake, tsunami, wildfire, extreme weather, climate disaster |
| **Anchor phrases** | "hurricane damage infrastructure", "typhoon port closure", "earthquake refinery damage", "tsunami warning coastal", "extreme weather supply chain", "wildfire threatening", "climate disaster economic impact", "storm surge port", "flood damage industrial", "natural disaster supply disruption" |
| **Disambiguation negatives** | "climate change debate policy", "carbon credit trading", "ESG fund performance", "climate activism protest" |
| **Theme description** | Natural disasters and extreme weather events with direct economic impact on ports, refineries, pipelines, agricultural production, and supply chains. Distinguished from policy climate discussions; focuses on acute physical events with market-moving potential. |
| **GDELT/CAMEO** | GKG: `NATURAL_DISASTER`, `ENV_FLOOD`, `ENV_DROUGHT` |

---

## Appendix A: CAMEO Code Quick Reference

The following CAMEO root codes are most relevant to this taxonomy:

| CAMEO Code | Description | Relevant Themes |
|---|---|---|
| 01x | Make public statement | MAC_FED, MAC_ECB, MAC_BOE, MAC_BOJ |
| 02x | Appeal | XSL_ELN |
| 03x-05x | Express intent to cooperate | XSL_DES, SNC_TRD |
| 06x | Material cooperation | SNC_LSN, DEF_AID |
| 07x | Provide aid | DEF_AID |
| 08x | Yield / Concede | SNC_LSN |
| 10x | Demand | SNC_TGT |
| 11x | Disapprove | SNC_TGT |
| 12x | Reject | SNC_TGT |
| 13x-14x | Threaten | XSL_ESC, DEF_CON |
| 15x | Protest | XSL_ELN |
| 16x | Reduce relations | SNC_NEW, SNC_FRZ |
| 17x | Coerce | SNC_TGT, SHP_TWN |
| 18x | Assault | DEF_CON, SHP_ATK |
| 19x | Fight | DEF_CON, REG_UKR, REG_MEA |
| 20x | Mass violence | DEF_CON |

---

## Appendix B: GKG Theme Quick Reference

| GKG Theme | Relevant Taxonomy Themes |
|---|---|
| `MILITARY` | DEF_MUN, DEF_MIS, DEF_SAT, DEF_COM, DEF_NAV, DEF_NUC, DEF_PRM, DEF_CON |
| `TAX_FNCACT_SANCTIONS` | SNC_NEW, SNC_TGT, SNC_LSN, SNC_FRZ, SHP_SAN |
| `ENV_OIL` | CMD_SPR, CMD_GAS, CMD_OPC, SHP_HRM |
| `FOOD_SECURITY` | CMD_AGR, SHP_BLK |
| `WMD` | DEF_NUC, DEF_MIS, XSL_NUK |
| `NUCLEAR` | DEF_NUC, CMD_URN, XSL_NUK |
| `ECON_INTEREST_RATE` | MAC_HWK, MAC_DOV, MAC_CRV, MAC_FED, MAC_ECB, MAC_BOE, MAC_BOJ |
| `ECON_PRICE` | CMD_SPR, CMD_SAF, CMD_IND, MAC_INF |
| `ECON_UNEMPLOYMENT` | MAC_EMP, MAC_REC |
| `ECON_BANKRUPTCY` | MAC_LIQ, MAC_CRD, CRY_LIQ |
| `ECON_TRADE` | SNC_TRF, SNC_TRD, CMD_MET |
| `CYBER_ATTACK` | DEF_CYB |
| `NATURAL_DISASTER` | CMD_AGW, XSL_CLM |
| `ELECTION` | XSL_ELN |
| `CRISISLEX_T03_DEAD` | DEF_CON, SHP_ATK |
| `PROTEST` | XSL_ELN, SHP_LBR |
| `CENTRAL_BANK` | MAC_FED, MAC_ECB, MAC_BOE, MAC_BOJ, MAC_CNY |

---

## Appendix C: Theme Count Summary

| Sleeve | Count | Theme ID Range |
|---|---|---|
| Defense & Security | 11 | DEF_MUN_001 -- DEF_UAS_063, DEF_AID_064 |
| Shipping & Supply Chain | 13 | SHP_HRM_010 -- SHP_IOC_067 |
| Commodities | 9 | CMD_SPR_023 -- CMD_MET_070 |
| Macro / Rates | 13 | MAC_HWK_031 -- MAC_CNY_073 |
| Crypto Behavioral | 4 | CRY_RON_042 -- CRY_LIQ_045 |
| Sanctions & Trade | 7 | SNC_NEW_046 -- SNC_FRZ_052 |
| Cross-Sleeve | 8 | XSL_ESC_053 -- XSL_CLM_076 |
| Regional Conflict | 5 | REG_UKR_058 -- REG_IND_062 |
| **Total** | **70** | |

---

## Appendix D: Usage Notes for Implementation

### Matching logic

1. **Primary keyword scan**: At least one primary keyword must appear in the text (case-insensitive).
2. **Anchor phrase boost**: Each matched anchor phrase adds significant confidence to the classification score.
3. **Negative suppression**: If any disambiguation negative appears in the same sentence or headline as the matched keyword, suppress the match or heavily penalize the confidence score.
4. **Multi-theme tagging**: A single headline can (and often should) activate multiple themes. For example, "Houthi missile strike on oil tanker in Red Sea" should activate SHP_BAB_011, SHP_ATK_021, CMD_SPR_023, and REG_MEA_059.
5. **Semantic fallback**: When lexical matching is ambiguous, use embedding similarity between the input text and the theme description paragraph for tie-breaking.

### Co-activation patterns

Certain theme combinations are expected and should be treated as signal amplifiers, not redundancy:

| Trigger Event | Expected Co-activations |
|---|---|
| Red Sea shipping attack | SHP_BAB_011 + SHP_ATK_021 + SHP_INS_019 + CMD_SPR_023 |
| Russia-Ukraine escalation | REG_UKR_058 + DEF_CON_009 + SHP_BLK_013 + CMD_AGR_028 + CMD_GAS_024 |
| China-Taiwan tension | SHP_TWN_014 + REG_SCS_060 + XSL_ESC_053 + CMD_IND_027 |
| Fed hawkish surprise | MAC_HWK_031 + MAC_FED_036 + XSL_USD_056 |
| New Iran sanctions | SNC_NEW_046 + SHP_HRM_010 + CMD_SPR_023 |
| OPEC surprise cut | CMD_OPC_030 + CMD_SPR_023 + MAC_INF_034 |
| Crypto exchange collapse | CRY_LIQ_045 + CRY_REG_044 |
| India-Pakistan border clash | REG_IND_062 + SHP_INW_017 + SHP_INE_018 + XSL_ESC_053 |

### Maintenance cadence

- Review theme definitions quarterly or after any major geopolitical regime change.
- When updating theme definitions, rerun the automated exposure estimation (Section 2.4 of design doc) rather than applying instrument-level overrides.
- New themes should be added when a novel, persistent geopolitical dynamic emerges that does not map cleanly to existing themes (e.g., a new sanctions regime, a new conflict theater, or a new commodity supply bottleneck).
