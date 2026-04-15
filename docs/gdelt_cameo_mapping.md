# GDELT CAMEO Event Code Mapping to Trading System Sleeves

Reference document for the macro-event-driven trading engine. Maps CAMEO event
codes, GKG theme tags, Goldstein scale values, and tone fields to the system's
sleeve/sub-sleeve taxonomy.

Last updated: 2026-04-15

---

## Table of Contents

1. [CAMEO Root Code Mapping (01-20)](#1-cameo-root-code-mapping-01-20)
2. [Critical CAMEO Sub-Code Drill-Downs](#2-critical-cameo-sub-code-drill-downs)
3. [GKG Theme Tag Mapping](#3-gkg-theme-tag-mapping)
4. [Goldstein Scale Integration](#4-goldstein-scale-integration)
5. [Tone and Sentiment Field Usage](#5-tone-and-sentiment-field-usage)
6. [Disambiguation Rules](#6-disambiguation-rules)
7. [Composite Signal Construction Notes](#7-composite-signal-construction-notes)

---

## 1. CAMEO Root Code Mapping (01-20)

The CAMEO (Conflict and Mediation Event Observations) taxonomy defines 20 root
event categories. Each root code below is mapped to zero or more sleeves in our
trading system. Relevance weight indicates how important events with this root
code are to the overall system.

### Legend

| Weight | Meaning |
|--------|---------|
| **HIGH** | Direct, first-order relevance; events should trigger signal generation immediately |
| **MEDIUM** | Indirect or contextual relevance; events feed into composite features or background escalation state |
| **LOW** | Weak or conditional relevance; useful only when combined with other signals or in specific geographic contexts |

---

### 01 -- MAKE PUBLIC STATEMENT

| Field | Value |
|-------|-------|
| **CAMEO Root** | 01 |
| **Description** | Public statements, declarations, speeches by state or non-state actors |
| **Primary Sleeves** | Rates (US), Rates (ex-US), Defense & Security, Commodities |
| **Relevance** | MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 010 | Make statement, not specified | All (contextual) | LOW |
| 011 | Decline comment | Rates (signals evasion on policy) | LOW |
| 012 | Make pessimistic comment | Rates, Commodities (risk-off signal) | MEDIUM |
| 013 | Make optimistic comment | Rates, Commodities (risk-on signal) | MEDIUM |
| 014 | Consider policy option | Rates (US), Rates (ex-US) | MEDIUM |
| 015 | Acknowledge or claim responsibility | Defense & Security | MEDIUM |
| 016 | Deny responsibility | Defense & Security | LOW |
| 017 | Engage in symbolic act | All | LOW |
| 018 | Make empathetic comment | All | LOW |

**Disambiguation:** Statements by central bank officials map to Rates; statements
by defense ministers or military officials map to Defense & Security; statements
about oil/gas supply map to Commodities (energy complex). Actor codes
(CAMEO actor type) must be checked. Filter on `Actor1Type1Code` for GOV, MIL,
BUS, etc.

---

### 02 -- APPEAL

| Field | Value |
|-------|-------|
| **CAMEO Root** | 02 |
| **Description** | Appeals for cooperation, aid, diplomatic support, or policy change |
| **Primary Sleeves** | Defense & Security, Shipping & Supply Chain, Rates (ex-US) |
| **Relevance** | LOW-MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 020 | Make appeal, not specified | Contextual | LOW |
| 021 | Appeal for material cooperation | Defense & Security, Shipping | LOW |
| 0211 | Appeal for economic cooperation | Rates (ex-US), Commodities | MEDIUM |
| 0212 | Appeal for military cooperation | Defense & Security | MEDIUM |
| 0213 | Appeal for judicial cooperation | LOW relevance | LOW |
| 0214 | Appeal for intelligence cooperation | Defense (ISR/cyber) | MEDIUM |
| 022 | Appeal for diplomatic cooperation | Rates (ex-US) | LOW |
| 023 | Appeal for aid | Rates (ex-US), Commodities | LOW |
| 0231 | Appeal for economic aid | Rates (ex-US) | MEDIUM |
| 0232 | Appeal for military aid | Defense & Security | HIGH |
| 0233 | Appeal for humanitarian aid | Shipping & Supply Chain | LOW |
| 024 | Appeal for political reform | Rates (ex-US) | LOW |
| 025 | Appeal to yield | Defense & Security | MEDIUM |
| 0253 | Appeal for ceasefire | Defense (de-escalation signal) | MEDIUM |
| 0254 | Appeal to release persons/property | Shipping (sanctions context) | LOW |
| 026 | Appeal to others to meet/negotiate | Defense, Rates (ex-US) | LOW |
| 027 | Appeal to others to settle dispute | Defense (de-escalation) | LOW |
| 028 | Appeal to others to engage in material cooperation | Shipping, Commodities | LOW |
| 0281 | Appeal for economic cooperation (3rd party) | Commodities, Rates (ex-US) | LOW |
| 0282 | Appeal for military cooperation (3rd party) | Defense & Security | MEDIUM |

**Disambiguation:** Appeals for military aid (0232) are HIGH relevance for Defense
because they signal active or impending conflict. Geographic filtering is essential:
appeals involving NATO/EU actors map differently from appeals involving Middle
Eastern or Indo-Pacific actors.

---

### 03 -- EXPRESS INTENT TO COOPERATE

| Field | Value |
|-------|-------|
| **CAMEO Root** | 03 |
| **Description** | Stated intention to cooperate economically, militarily, or diplomatically |
| **Primary Sleeves** | Defense & Security, Rates (ex-US), Commodities, Shipping |
| **Relevance** | MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 030 | Express intent to cooperate, unspecified | Contextual | LOW |
| 031 | Express intent to engage in material cooperation | Shipping, Commodities | MEDIUM |
| 0311 | Express intent for economic cooperation | Rates (ex-US), Commodities | MEDIUM |
| 0312 | Express intent for military cooperation | Defense & Security | HIGH |
| 0314 | Express intent for intelligence sharing | Defense (ISR/cyber) | HIGH |
| 032 | Express intent for diplomatic cooperation | Rates (ex-US) | LOW |
| 033 | Express intent to provide aid | Rates (ex-US) | LOW |
| 0331 | Express intent for economic aid | Rates (ex-US) | MEDIUM |
| 0332 | Express intent for military aid | Defense & Security | HIGH |
| 034 | Express intent for political reform | Rates (ex-US) | LOW |
| 035 | Express intent to yield | Defense (de-escalation) | MEDIUM |
| 0353 | Express intent for ceasefire | Defense (de-escalation) | HIGH |
| 036 | Express intent to meet/negotiate | Defense, Rates (ex-US) | MEDIUM |
| 037 | Express intent to settle dispute | Defense (de-escalation) | MEDIUM |
| 038 | Express intent for material cooperation (3rd party) | Shipping, Commodities | LOW |
| 039 | Express intent for diplomatic cooperation (3rd party) | Rates (ex-US) | LOW |

**Disambiguation:** Military cooperation intent (0312, 0332) is defense-positive
(bullish for defense equities) but may also be conflict-negative (de-escalatory).
The Goldstein scale helps resolve this: positive Goldstein = cooperation frame,
but must cross-reference with conflict context in the trailing event window.

---

### 04 -- CONSULT

| Field | Value |
|-------|-------|
| **CAMEO Root** | 04 |
| **Description** | Consultations, discussions, meetings between parties |
| **Primary Sleeves** | Rates (US), Rates (ex-US), Defense & Security |
| **Relevance** | LOW-MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 040 | Consult, not specified | Contextual | LOW |
| 041 | Discuss by telephone | Rates, Defense | LOW |
| 042 | Make a visit | Rates (ex-US), Defense | LOW |
| 043 | Host a visit | Rates (ex-US), Defense | LOW |
| 044 | Meet at 3rd location | Rates, Defense | MEDIUM |
| 045 | Mediate | Defense (de-escalation) | MEDIUM |
| 046 | Engage in negotiation | Defense, Rates (ex-US), Commodities | MEDIUM |

**Disambiguation:** Consultations are primarily background signals. They become
MEDIUM relevance when they involve heads of state or defense ministers (check
`Actor1Type1Code` = GOV + name entity resolution). Negotiations on trade deals
map to Commodities and Rates (ex-US).

---

### 05 -- ENGAGE IN DIPLOMATIC COOPERATION

| Field | Value |
|-------|-------|
| **CAMEO Root** | 05 |
| **Description** | Formal diplomatic cooperation: treaties, pacts, agreements, recognition |
| **Primary Sleeves** | Rates (ex-US), Defense & Security, Shipping & Supply Chain |
| **Relevance** | MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 050 | Engage in diplomatic cooperation, unspecified | Rates (ex-US) | LOW |
| 051 | Praise or endorse | Contextual | LOW |
| 052 | Defend verbally | Defense & Security, Rates (ex-US) | LOW |
| 053 | Rally support on behalf of | Defense, Rates (ex-US) | MEDIUM |
| 054 | Grant diplomatic recognition | Rates (ex-US) | MEDIUM |
| 055 | Forgive | Defense (de-escalation) | LOW |
| 056 | Sign formal agreement | Rates (ex-US), Shipping, Commodities | HIGH |
| 057 | Extend economic aid | Rates (ex-US) | MEDIUM |
| 058 | Extend military aid | Defense & Security | HIGH |

**Disambiguation:** Formal agreements (056) can relate to trade (Commodities,
Shipping routes), security pacts (Defense), or financial arrangements (Rates).
Cross-reference GKG themes to disambiguate. Military aid extension (058) is a
strong defense-positive signal and may indicate regional escalation.

---

### 06 -- ENGAGE IN MATERIAL COOPERATION

| Field | Value |
|-------|-------|
| **CAMEO Root** | 06 |
| **Description** | Tangible cooperation: economic, military, or humanitarian assistance |
| **Primary Sleeves** | Defense & Security, Commodities, Shipping & Supply Chain, Rates (ex-US) |
| **Relevance** | MEDIUM-HIGH |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 060 | Engage in material cooperation, unspecified | Contextual | LOW |
| 061 | Cooperate economically | Commodities, Rates (ex-US), Shipping | MEDIUM |
| 0611 | Impose economic cooperation (trade agreement enactment) | Commodities, Shipping, Rates (ex-US) | HIGH |
| 0612 | Engage in military cooperation | Defense & Security | HIGH |
| 0613 | Engage in judicial cooperation | LOW relevance | LOW |
| 0614 | Share intelligence | Defense (ISR/cyber) | HIGH |
| 062 | Provide aid | Rates (ex-US) | MEDIUM |
| 0621 | Provide economic aid | Rates (ex-US), Commodities | MEDIUM |
| 0622 | Provide military aid | Defense & Security | HIGH |
| 0623 | Provide humanitarian aid | Shipping & Supply Chain | MEDIUM |
| 063 | Provide refuge/asylum | LOW relevance | LOW |
| 064 | Share/open peacekeeping forces | Defense & Security | MEDIUM |

**Disambiguation:** Military cooperation (0612) and military aid (0622) are
defense-positive (bullish primes, munitions). Intelligence sharing (0614) maps
to ISR/space/comms and cyber/EW sub-sleeves. Economic cooperation can be
sanctions-relief (bearish for defense, but bullish for Shipping routes and
Commodities flow).

---

### 07 -- YIELD

| Field | Value |
|-------|-------|
| **CAMEO Root** | 07 |
| **Description** | Concessions, surrenders, retreats, compliance with demands |
| **Primary Sleeves** | Defense & Security, Shipping & Supply Chain, Commodities |
| **Relevance** | MEDIUM-HIGH |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 070 | Yield, not specified | Contextual | LOW |
| 071 | Ease administrative sanctions | Shipping (sanctions enforcement), Commodities | HIGH |
| 0711 | Ease economic sanctions/penalties | Shipping, Commodities, Rates (ex-US) | HIGH |
| 0712 | Ease military blockade/restrictions | Shipping (chokepoints), Defense | HIGH |
| 072 | Ease political dissent | Rates (ex-US) | LOW |
| 073 | Release or return | Shipping (detained vessels), Defense | MEDIUM |
| 0731 | Release persons (hostages/prisoners) | Defense | MEDIUM |
| 0732 | Release/return property (incl. vessels) | Shipping | HIGH |
| 074 | Allow passage/access (territory or waterway) | Shipping (chokepoints) | HIGH |
| 075 | Retreat or withdraw militarily | Defense (de-escalation), Commodities (risk-off easing) | HIGH |
| 076 | De-escalate military engagement | Defense (de-escalation) | HIGH |

**Disambiguation:** Yield events are STRONG de-escalation signals. Easing sanctions
(0711) is bearish for defense equities but bullish for Shipping and Commodities
flow. Retreat (075) is defense-negative (conflict winding down). These events
need directional inversion relative to escalation events. Use the sign of the
Goldstein score to confirm: positive Goldstein with yield = genuine de-escalation.

---

### 08 -- INVESTIGATE

| Field | Value |
|-------|-------|
| **CAMEO Root** | 08 |
| **Description** | Investigations, inquiries, inspections by official bodies |
| **Primary Sleeves** | Shipping & Supply Chain (sanctions enforcement), Defense & Security |
| **Relevance** | LOW-MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 080 | Investigate, not specified | Contextual | LOW |
| 081 | Investigate crime/corruption | LOW relevance | LOW |
| 0811 | Investigate financial crimes | Crypto (regulatory), Rates | MEDIUM |
| 082 | Investigate human rights | LOW relevance | LOW |
| 083 | Investigate military action | Defense & Security | MEDIUM |
| 084 | Investigate war crimes | Defense (reputational risk for contractors) | LOW |
| 085 | Investigate espionage/sabotage | Defense (cyber/EW, ISR) | MEDIUM |
| 086 | Inspect | Shipping (sanctions enforcement, port inspections) | MEDIUM |

**Disambiguation:** Inspections (086) in the context of sanctions enforcement
(e.g., North Korea, Iran, Russia) map strongly to Shipping & Supply Chain
(sanctions enforcement sub-sleeve). Financial crime investigations (0811) may
signal crypto regulatory action.

---

### 09 -- DISAPPROVE

| Field | Value |
|-------|-------|
| **CAMEO Root** | 09 |
| **Description** | Verbal disapproval, criticism, condemnation |
| **Primary Sleeves** | Defense & Security, Rates (ex-US), Commodities |
| **Relevance** | LOW-MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 090 | Disapprove, not specified | Contextual | LOW |
| 091 | Criticize or denounce | Contextual | LOW |
| 092 | Accuse of aggression/wrongdoing | Defense, Commodities | MEDIUM |
| 093 | Rally opposition against | Defense, Rates (ex-US) | MEDIUM |
| 094 | Complain officially | Shipping (trade disputes), Commodities | LOW |
| 095 | Formally reject/turn down proposal | Rates (ex-US), Defense | MEDIUM |
| 096 | Defy norms/law | Shipping (sanctions enforcement) | MEDIUM |

**Disambiguation:** Disapproval events are precursors to escalation. Track the
ratio of 09x events to 04x-06x events (disapproval vs. cooperation) over a
rolling window to build an escalation momentum indicator. Accusations of
aggression (092) with military actors map to Defense; with trade actors map
to Commodities/Shipping.

---

### 10 -- DEMAND

| Field | Value |
|-------|-------|
| **CAMEO Root** | 10 |
| **Description** | Demands for action, compliance, withdrawal, reform |
| **Primary Sleeves** | Defense & Security, Shipping & Supply Chain, Commodities, Rates (ex-US) |
| **Relevance** | MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 100 | Demand, not specified | Contextual | LOW |
| 101 | Demand for material cooperation | Commodities, Shipping | MEDIUM |
| 1011 | Demand for economic cooperation | Commodities, Rates (ex-US) | MEDIUM |
| 1012 | Demand for military cooperation | Defense & Security | HIGH |
| 1013 | Demand for judicial cooperation | LOW relevance | LOW |
| 1014 | Demand for intelligence cooperation | Defense (ISR/cyber) | MEDIUM |
| 102 | Demand for diplomatic cooperation | Rates (ex-US) | LOW |
| 103 | Demand for aid | Rates (ex-US) | MEDIUM |
| 1031 | Demand for economic aid | Rates (ex-US) | MEDIUM |
| 1032 | Demand for military aid | Defense & Security | HIGH |
| 104 | Demand political reform/change | Rates (ex-US) | MEDIUM |
| 105 | Demand to yield | Defense, Shipping | HIGH |
| 1051 | Demand easing of sanctions | Shipping, Commodities | HIGH |
| 1052 | Demand release of persons/property | Shipping (detained vessels) | MEDIUM |
| 1053 | Demand ceasefire | Defense (de-escalation demand) | HIGH |
| 1054 | Demand withdrawal | Defense & Security | HIGH |
| 106 | Demand that others meet/negotiate | Defense, Rates | MEDIUM |

**Disambiguation:** Demands for ceasefire (1053) and withdrawal (1054) are
escalation signals despite their cooperative content -- the demand itself
implies the conflict is ongoing. Demands for sanctions easing (1051) signal
sanctions-stress (bullish for Shipping insurance/freight stress sub-sleeve).

---

### 11 -- DISAPPROVE (FORMAL)

| Field | Value |
|-------|-------|
| **CAMEO Root** | 11 |
| **Description** | Formal protests, diplomatic complaints, rejection of proposals |
| **Primary Sleeves** | Rates (ex-US), Shipping & Supply Chain, Commodities |
| **Relevance** | MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 110 | Disapprove formally, not specified | Contextual | LOW |
| 111 | Formally protest/demonstrate | Rates (ex-US) | MEDIUM |
| 112 | Reduce/break diplomatic relations | Rates (ex-US), Commodities | HIGH |
| 1121 | Reduce/cut economic relations | Commodities, Shipping, Rates (ex-US) | HIGH |
| 1122 | Reduce/stop military cooperation | Defense & Security | HIGH |
| 1123 | Reduce/halt intelligence cooperation | Defense (ISR/cyber) | HIGH |
| 113 | Expel/withdraw diplomatic representation | Rates (ex-US) | HIGH |
| 114 | Rally opposition formally | Rates (ex-US), Defense | MEDIUM |

**Disambiguation:** Breaking economic relations (1121) is a pre-sanctions signal
and maps to both Commodities (trade disruption) and Shipping (route disruption).
Stopping military cooperation (1122) is bearish for defense cooperation plays
but bullish for conflict escalation positioning.

---

### 12 -- REJECT

| Field | Value |
|-------|-------|
| **CAMEO Root** | 12 |
| **Description** | Rejection of proposals, demands, cooperation, mediation |
| **Primary Sleeves** | Defense & Security, Rates (ex-US), Commodities |
| **Relevance** | MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 120 | Reject, not specified | Contextual | LOW |
| 121 | Reject material cooperation | Commodities, Shipping | MEDIUM |
| 1211 | Reject economic cooperation | Commodities, Rates (ex-US) | MEDIUM |
| 1212 | Reject military cooperation | Defense & Security | HIGH |
| 1213 | Reject judicial cooperation | LOW relevance | LOW |
| 1214 | Reject intelligence cooperation | Defense (ISR/cyber) | MEDIUM |
| 122 | Reject request/demand for aid | Rates (ex-US) | MEDIUM |
| 123 | Reject mediation | Defense (escalation signal) | HIGH |
| 1231 | Reject de-escalation/ceasefire | Defense (strong escalation signal) | HIGH |
| 1232 | Reject peace plan | Defense (escalation) | HIGH |
| 124 | Refuse to yield | Defense (conflict persistence) | HIGH |
| 1241 | Refuse to ease sanctions | Shipping (sanctions enforcement), Commodities | HIGH |
| 1242 | Refuse to release persons/property | Shipping, Defense | MEDIUM |
| 1243 | Refuse ceasefire | Defense (strong escalation signal) | HIGH |
| 1244 | Refuse to withdraw | Defense (conflict persistence) | HIGH |
| 125 | Reject proposal to meet/negotiate | Defense (escalation) | HIGH |
| 126 | Defy international norms | Shipping (sanctions), Defense, Commodities | HIGH |
| 127 | Veto | Rates (ex-US), Defense | MEDIUM |

**Disambiguation:** Reject events in the 123x-125x range are STRONG escalation
signals. Refusal to ceasefire (1243) or withdraw (1244) should trigger elevated
severity scores in Defense & Security and Commodities (energy complex via
supply risk).

---

### 13 -- THREATEN

| Field | Value |
|-------|-------|
| **CAMEO Root** | 13 |
| **Description** | Threats of force, sanctions, retaliation, or other punitive action |
| **Primary Sleeves** | Defense & Security, Shipping & Supply Chain, Commodities, Crypto, Rates |
| **Relevance** | HIGH |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 130 | Threaten, not specified | All sleeves (risk-off) | MEDIUM |
| 131 | Threaten non-force | Shipping, Commodities, Rates (ex-US) | MEDIUM |
| 1311 | Threaten to halt negotiations | Defense, Rates (ex-US) | MEDIUM |
| 1312 | Threaten to reduce/break relations | Rates (ex-US), Commodities | HIGH |
| 1313 | Threaten with sanctions/boycott | Shipping (sanctions enforcement), Commodities, Rates (ex-US) | HIGH |
| 132 | Threaten with political actions | Rates (ex-US) | MEDIUM |
| 1321 | Threaten to ban political parties | Rates (ex-US) | LOW |
| 133 | Threaten with force, unspecified | Defense & Security, Commodities | HIGH |
| 134 | Threaten with military force | Defense & Security, Commodities, Shipping | HIGH |
| 1341 | Threaten blockade | Shipping (chokepoints), Commodities | HIGH |
| 1342 | Threaten to occupy territory | Defense, Commodities | HIGH |
| 1343 | Threaten unconventional violence | Defense (nuclear enterprise) | HIGH |
| 1344 | Threaten conventional attack | Defense (munitions, primes) | HIGH |
| 135 | Threaten with WMD | Defense (nuclear enterprise), all sleeves (systemic risk) | HIGH |
| 136 | Threaten to attack with CBRN | Defense (nuclear enterprise) | HIGH |
| 137 | Threaten covert attack | Defense (cyber/EW, ISR) | HIGH |
| 138 | Threaten with reprisals | All sleeves | MEDIUM |
| 139 | Threaten with military mobilization | Defense & Security, Commodities | HIGH |

**Disambiguation:** This is the most critical root code for the trading system.
Threat events are leading indicators of kinetic escalation. Sub-codes 134x-139
should feed directly into the conflict_escalation expert with maximum severity
weighting. Threats of blockade (1341) are critical for Shipping chokepoint
analysis. WMD threats (135, 136) should trigger nuclear enterprise sub-sleeve
and systemwide risk-off signals. Threats of sanctions (1313) map to Shipping
(sanctions enforcement) and Commodities (supply disruption).

Geographic context is essential: threats involving Iran/Hormuz, Yemen/Bab
el-Mandeb, Russia/Black Sea, or China/Taiwan Strait should be routed to specific
chokepoint sub-sleeves.

---

### 14 -- PROTEST

| Field | Value |
|-------|-------|
| **CAMEO Root** | 14 |
| **Description** | Physical protests, demonstrations, strikes, boycotts, obstruction |
| **Primary Sleeves** | Rates (ex-US), Shipping & Supply Chain, Commodities |
| **Relevance** | MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 140 | Protest, not specified | Rates (ex-US) | LOW |
| 141 | Demonstrate/rally | Rates (ex-US) | LOW |
| 1411 | Demonstrate for political change | Rates (ex-US) | MEDIUM |
| 1412 | Demonstrate for economic change | Rates (ex-US), Commodities | MEDIUM |
| 1413 | Demonstrate for military/security issues | Defense | MEDIUM |
| 1414 | Demonstrate for rights | LOW relevance | LOW |
| 142 | Hunger strike | LOW relevance | LOW |
| 143 | Strike/boycott | Shipping (port disruption), Commodities | HIGH |
| 1431 | Strike (labor) | Shipping (port clusters), Commodities | HIGH |
| 1432 | Boycott | Commodities, Shipping | MEDIUM |
| 1433 | Obstruct passage/block | Shipping (chokepoints, ports) | HIGH |
| 144 | Riot/engage in political turmoil | Rates (ex-US), Commodities | MEDIUM |
| 145 | Engage in political violence (non-lethal) | Rates (ex-US), Defense | MEDIUM |

**Disambiguation:** Labor strikes at ports (1431) are critical for Shipping
(port clusters sub-sleeve). Passage obstruction (1433) maps to Shipping
chokepoints. Riots (144) in oil-producing regions map to Commodities (energy).
Filter by `ActionGeo_CountryCode` to route to the correct regional sub-sleeve.

---

### 15 -- EXHIBIT FORCE POSTURE

| Field | Value |
|-------|-------|
| **CAMEO Root** | 15 |
| **Description** | Military posturing, buildups, shows of force, alert level changes |
| **Primary Sleeves** | Defense & Security, Shipping & Supply Chain, Commodities, Crypto |
| **Relevance** | HIGH |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 150 | Demonstrate military/police power, not specified | Defense, Commodities | MEDIUM |
| 151 | Increase police/security forces | Rates (ex-US) | LOW |
| 152 | Increase military posture | Defense & Security | HIGH |
| 1521 | Increase military alert level | Defense, Commodities | HIGH |
| 1522 | Mobilize armed forces | Defense & Security, Commodities | HIGH |
| 1523 | Increase military build-up | Defense (primes, munitions) | HIGH |
| 153 | Conduct military exercises/show of force | Defense, Shipping | HIGH |
| 154 | Fortify/strengthen position | Defense | MEDIUM |
| 155 | Patrol/provide security | Shipping (chokepoints), Defense | MEDIUM |

**Disambiguation:** Force posture events near chokepoints are HIGH relevance for
Shipping. Chinese military exercises near Taiwan Strait, Iranian naval exercises
near Hormuz, and Russian Black Sea fleet movements should route to both Defense
and Shipping (chokepoints). Military build-up (1523) is strongly bullish for
Defense equities (especially primes and munitions sub-sleeves). Force posture
events also serve as a risk-off signal for Crypto (flight from risk assets).

---

### 16 -- REDUCE RELATIONS

| Field | Value |
|-------|-------|
| **CAMEO Root** | 16 |
| **Description** | Reduction, cessation, or withdrawal of cooperation/relations |
| **Primary Sleeves** | Shipping & Supply Chain, Commodities, Rates (ex-US), Defense & Security |
| **Relevance** | HIGH |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 160 | Reduce relations, not specified | All | MEDIUM |
| 161 | Reduce/break diplomatic relations | Rates (ex-US) | HIGH |
| 162 | Reduce/stop material aid | Rates (ex-US), Defense | MEDIUM |
| 1621 | Reduce/stop economic aid | Rates (ex-US) | MEDIUM |
| 1622 | Reduce/stop military aid | Defense & Security | HIGH |
| 163 | Impose embargo/blockade/sanctions | Shipping, Commodities, Rates (ex-US) | HIGH |
| 1631 | Impose economic sanctions | Shipping (sanctions enforcement), Commodities, Rates (ex-US) | HIGH |
| 1632 | Impose military blockade | Shipping (chokepoints), Commodities, Defense | HIGH |
| 164 | Halt negotiations | Defense (escalation), Rates (ex-US) | MEDIUM |
| 165 | Halt mediation | Defense (escalation) | MEDIUM |
| 166 | Expel/withdraw peacekeepers | Defense | MEDIUM |

**Disambiguation:** Sanctions imposition (1631) is one of the highest-impact
event types for this system. It feeds into Shipping (sanctions enforcement and
insurance/freight stress sub-sleeves), Commodities (supply disruption, especially
energy complex and industrial metals), and Rates (ex-US, country-specific).
Military blockade (1632) directly maps to Shipping chokepoint sub-sleeves.

---

### 17 -- COERCE

| Field | Value |
|-------|-------|
| **CAMEO Root** | 17 |
| **Description** | Non-violent coercion: seizures, detentions, restrictions, bans |
| **Primary Sleeves** | Shipping & Supply Chain, Commodities, Defense & Security, Crypto, Rates |
| **Relevance** | HIGH |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 170 | Coerce, not specified | Contextual | MEDIUM |
| 171 | Seize/confiscate property | Shipping, Commodities | HIGH |
| 1711 | Confiscate property (vessels, cargo) | Shipping (sanctions enforcement) | HIGH |
| 1712 | Seize/hijack vessel | Shipping (chokepoints, insurance/freight stress) | HIGH |
| 172 | Impose administrative sanctions | Shipping, Commodities, Rates (ex-US) | HIGH |
| 1721 | Impose trade restrictions/tariffs | Commodities, Shipping, Rates (ex-US) | HIGH |
| 1722 | Ban political activities | Rates (ex-US) | LOW |
| 1723 | Impose curfew | Rates (ex-US) | LOW |
| 1724 | Impose state of emergency | Rates (ex-US), Defense, Commodities | HIGH |
| 173 | Arrest/detain | Shipping (crew detention), Rates (ex-US) | MEDIUM |
| 174 | Expel/deport | Rates (ex-US) | LOW |
| 175 | Use tactics of violent repression | Defense, Rates (ex-US) | MEDIUM |

**Disambiguation:** Vessel seizure/hijacking (1712) is a critical signal for
Shipping (especially chokepoints and insurance/freight stress). This is the
code that fires for Houthi attacks on shipping in the Red Sea, Iranian seizures
in the Strait of Hormuz, and piracy events. Trade restrictions (1721) including
tariffs map to Commodities and Shipping. State of emergency (1724) in
commodity-producing nations maps to Commodities (energy, metals).

---

### 18 -- ASSAULT

| Field | Value |
|-------|-------|
| **CAMEO Root** | 18 |
| **Description** | Physical assaults, beatings, abductions (non-military) |
| **Primary Sleeves** | Defense & Security, Rates (ex-US) |
| **Relevance** | LOW-MEDIUM |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 180 | Use unconventional violence, not specified | Defense | LOW |
| 181 | Abduct/hijack/take hostage | Shipping (piracy), Defense | HIGH |
| 1811 | Kidnap for ransom | Shipping (piracy/insurance stress) | HIGH |
| 1812 | Hijack vehicle/aircraft/vessel | Shipping (chokepoints) | HIGH |
| 182 | Physically assault | LOW relevance | LOW |
| 183 | Conduct suicide/car/roadside bombing | Defense (munitions context) | MEDIUM |
| 184 | Use CBRN weapons | Defense (nuclear enterprise), all sleeves | HIGH |
| 185 | Assassination attempt | Defense, Rates (ex-US) | MEDIUM |
| 186 | Assassinate | Defense, Rates (ex-US), Commodities | HIGH |

**Disambiguation:** Hijacking of vessels (1812) and kidnapping (1811) in maritime
contexts are critical for Shipping chokepoint and insurance/freight stress
analysis. CBRN weapon use (184) is a systemwide risk event affecting all
sleeves. Assassinations of political/military leaders (186) create large
geopolitical shocks routing to Defense, Rates, and Commodities.

---

### 19 -- FIGHT

| Field | Value |
|-------|-------|
| **CAMEO Root** | 19 |
| **Description** | Armed combat, military engagements, bombardment, occupation |
| **Primary Sleeves** | Defense & Security, Commodities, Shipping & Supply Chain, Crypto, Rates |
| **Relevance** | HIGH (highest root code for conflict signals) |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 190 | Use conventional military force, not specified | Defense, Commodities | HIGH |
| 191 | Impose military blockade | Shipping (chokepoints), Commodities, Defense | HIGH |
| 192 | Occupy territory | Defense & Security, Commodities | HIGH |
| 193 | Fight with small arms/light weapons | Defense (munitions) | MEDIUM |
| 194 | Fight with artillery/heavy weapons | Defense (munitions, primes) | HIGH |
| 195 | Employ aerial weapons | Defense (primes, ISR/space) | HIGH |
| 1951 | Employ precision-guided munitions | Defense (munitions/missile defense) | HIGH |
| 1952 | Employ drone/UAV strikes | Defense (ISR/space, munitions) | HIGH |
| 196 | Violate ceasefire | Defense (escalation), Commodities | HIGH |
| 197 | Declare war | Defense, all sleeves (systemic) | HIGH |
| 198 | Use WMD | Defense (nuclear enterprise), all sleeves (systemic risk) | HIGH |

**Disambiguation:** All 19x events are high-priority for the system. Sub-codes
provide valuable signal routing: aerial weapons (195) and precision munitions
(1951) map to specific defense sub-sleeves (primes like LMT, RTX; munitions
like AXON, LHX). Drone strikes (1952) map to ISR/space/comms. Military
blockade (191) near chokepoints triggers Shipping signals. War declaration
(197) and WMD use (198) are maximum-severity systemwide events.

Geographic filtering is critical: conflict in the Middle East maps to
Commodities (energy complex) and Shipping (Hormuz, Bab el-Mandeb, Suez);
conflict in Eastern Europe maps to Commodities (agriculture, energy) and
Shipping (Black Sea); conflict in East Asia maps to Shipping (Taiwan Strait,
South China Sea) and Commodities (industrial metals, semiconductors).

---

### 20 -- USE UNCONVENTIONAL MASS VIOLENCE

| Field | Value |
|-------|-------|
| **CAMEO Root** | 20 |
| **Description** | Mass killing, ethnic cleansing, genocide, deliberate targeting of civilians |
| **Primary Sleeves** | Defense & Security, Rates (ex-US), all sleeves (systemic) |
| **Relevance** | HIGH |

**Sub-code breakdown:**

| Sub-code | Meaning | Sleeve Mapping | Weight |
|----------|---------|----------------|--------|
| 200 | Use unconventional mass violence, not specified | Defense, all | HIGH |
| 201 | Engage in mass expulsion | Rates (ex-US) | MEDIUM |
| 202 | Engage in mass killing | Defense, all sleeves (systemic) | HIGH |
| 203 | Engage in ethnic cleansing | Defense, all sleeves (systemic) | HIGH |
| 204 | Use chemical/biological/radiological weapons on civilians | Defense (nuclear enterprise), all | HIGH |

**Disambiguation:** These are the highest-severity CAMEO codes. Any 20x event
should trigger maximum escalation signals across all sleeves. They typically
lead to international intervention, sanctions, and sustained market disruption.
These events carry strong Goldstein scores (most negative on the scale).

---

## 2. Critical CAMEO Sub-Code Drill-Downs

### Chokepoint-Specific Event Mapping

Events at these locations require special routing to Shipping sub-sleeves:

| Chokepoint | Key Country Codes | CAMEO Codes of Interest | Shipping Sub-Sleeve |
|------------|-------------------|-------------------------|---------------------|
| Strait of Hormuz | IRN, ARE, OMN | 1341, 1632, 191, 1712, 1812, 155, 190 | `chokepoints.hormuz` |
| Bab el-Mandeb | YEM, DJI, ERI | 1341, 1632, 191, 1712, 1812, 190, 195 | `chokepoints.bab_el_mandeb` |
| Suez Canal | EGY | 1433, 1431, 1632, 191 | `chokepoints.suez` |
| Black Sea | RUS, UKR, TUR, ROU, BGR, GEO | 1632, 191, 190, 194, 195 | `chokepoints.black_sea` |
| Taiwan Strait | CHN, TWN | 153, 1522, 1632, 191, 190, 195, 197 | `chokepoints.taiwan_strait` |
| South China Sea | CHN, PHL, VNM, MYS, BRN | 153, 155, 1522, 192, 190 | `regional_routes.south_china_sea` |
| Indian Ocean | IND, LKA, MDV, SOM, MOZ | 155, 1712, 1812, 190 | `regional_routes.indian_ocean` |

### Defense Sub-Sleeve Routing by CAMEO Code

| Defense Sub-Sleeve | Primary CAMEO Codes | Signal Type |
|--------------------|---------------------|-------------|
| Primes (LMT, RTX, NOC, GD, BA) | 0612, 0622, 058, 152x, 190, 194, 195, 197 | Escalation = bullish |
| Munitions / Missile Defense (AXON, LHX) | 1344, 1951, 193, 194, 195 | Conflict intensity = bullish |
| ISR / Space / Comms | 0614, 1952, 085, 137 | Intel/surveillance demand = bullish |
| Cyber / EW | 085, 137, 1343, 0614 | Cyber threat activity = bullish |
| Naval / Shipbuilding (HII) | 155, 153, 191, 1632, 1712, 1812 | Maritime threat = bullish |
| Nuclear Enterprise | 135, 136, 184, 198, 204, 1343 | Nuclear escalation = bullish |

### Sanctions Event Chain

The sanctions lifecycle maps to a sequence of CAMEO codes:

```
Threat Phase:     1313 (threaten sanctions/boycott)
                  1312 (threaten to break relations)
Demand Phase:     1051 (demand easing of sanctions)
                  105  (demand to yield)
Imposition Phase: 1631 (impose economic sanctions) -- MOST CRITICAL
                  163  (impose embargo/blockade)
                  1632 (military blockade)
                  1721 (impose trade restrictions/tariffs)
Enforcement:      086  (inspect)
                  1711 (confiscate property)
                  1712 (seize vessels)
Easing Phase:     0711 (ease economic sanctions) -- REVERSAL SIGNAL
                  0712 (ease military restrictions)
                  074  (allow passage/access)
Rejection:        1241 (refuse to ease sanctions) -- PERSISTENCE SIGNAL
```

### Nuclear Escalation Ladder

Ordered from lowest to highest severity:

```
Level 1 (posture):  153  Military exercises
                    1521 Increase alert level
                    1522 Mobilize forces
Level 2 (threat):   133  Threaten with force
                    1343 Threaten unconventional violence
                    135  Threaten with WMD
Level 3 (coerce):   1632 Military blockade
                    191  Impose blockade (kinetic)
Level 4 (kinetic):  190  Conventional force
                    194  Heavy weapons
                    195  Aerial weapons
Level 5 (extreme):  184  CBRN weapon use
                    198  WMD use
                    204  CBRN on civilians
```

---

## 3. GKG Theme Tag Mapping

GDELT's Global Knowledge Graph (GKG) annotates articles with theme tags that
provide additional context beyond CAMEO codes. The following GKG themes are
relevant to the trading system.

### 3.1 Sanctions and Trade Restriction Themes

| GKG Theme | Description | Sleeve Mapping | Weight |
|-----------|-------------|----------------|--------|
| `TAX_FNCACT_SANCTIONS` | Sanctions-related content | Shipping (sanctions enforcement), Commodities, Rates (ex-US) | HIGH |
| `TAX_FNCACT_EMBARGO` | Embargo-related content | Shipping, Commodities | HIGH |
| `SANCTIONS` | General sanctions theme | Shipping (sanctions enforcement) | HIGH |
| `TRADE_DISPUTE` | Trade disputes and friction | Commodities, Shipping, Rates (ex-US) | MEDIUM |
| `TARIFF` | Tariff-related content | Commodities, Shipping, Rates | MEDIUM |
| `TRADE_WAR` | Explicit trade war references | Commodities, Shipping, Rates (all) | HIGH |
| `EXPORT_CONTROL` | Export controls and restrictions | Commodities (industrial metals), Defense | MEDIUM |
| `TAX_FNCACT_BLACKLIST` | Blacklisting / entity designation | Shipping (sanctions enforcement) | HIGH |

### 3.2 Conflict and Military Themes

| GKG Theme | Description | Sleeve Mapping | Weight |
|-----------|-------------|----------------|--------|
| `CRISISLEX_T03_DEAD` | Reports of deaths | Defense, Commodities | HIGH |
| `CRISISLEX_T02_INJURED` | Reports of injuries | Defense | MEDIUM |
| `CRISISLEX_T01_DISPLACED` | Displacement/refugee flows | Rates (ex-US) | LOW |
| `CRISISLEX_C04_MILITARY` | Military crisis context | Defense & Security | HIGH |
| `CRISISLEX_C03_CONFLICT` | Conflict crisis context | Defense, Commodities | HIGH |
| `CRISISLEX_CRISISLEXREC` | General crisis recommendation | All sleeves (risk-off) | MEDIUM |
| `MILITARY` | Military-related content | Defense & Security | MEDIUM |
| `ARMED_CONFLICT` | Armed conflict | Defense, Commodities | HIGH |
| `TAX_FNCACT_MILITARY` | Military function/actor | Defense & Security | MEDIUM |
| `TERROR` | Terrorism-related content | Defense (cyber/ISR), Commodities | MEDIUM |
| `WMD` | Weapons of mass destruction | Defense (nuclear enterprise) | HIGH |
| `NUCLEAR` | Nuclear-related content | Defense (nuclear enterprise), Commodities (uranium) | HIGH |
| `INSURGENCY` | Insurgency activity | Defense, Commodities (regional) | MEDIUM |
| `CEASEFIRE` | Ceasefire references | Defense (de-escalation) | HIGH |
| `PEACE_PROCESS` | Peace negotiations | Defense (de-escalation) | MEDIUM |
| `ARMS_TRADE` | Arms trading and transfers | Defense & Security | MEDIUM |

### 3.3 Energy and Commodities Themes

| GKG Theme | Description | Sleeve Mapping | Weight |
|-----------|-------------|----------------|--------|
| `ENV_OIL` | Oil-related content | Commodities (energy complex) | HIGH |
| `ENV_NATURALGAS` | Natural gas content | Commodities (energy complex) | HIGH |
| `ENV_COAL` | Coal-related content | Commodities (energy complex) | MEDIUM |
| `ENV_NUCLEAR` | Nuclear energy | Commodities (energy), Defense (nuclear) | MEDIUM |
| `ENV_SOLAR` | Solar energy | Commodities (energy) | LOW |
| `ENV_WIND` | Wind energy | Commodities (energy) | LOW |
| `ENERGY_SECURITY` | Energy security concerns | Commodities (energy complex), Shipping | HIGH |
| `OPEC` | OPEC references | Commodities (energy complex) | HIGH |
| `FOOD_SECURITY` | Food security concerns | Commodities (agriculture) | MEDIUM |
| `FAMINE` | Famine references | Commodities (agriculture) | MEDIUM |
| `WATER_SECURITY` | Water security | Commodities (agriculture) | LOW |
| `MINING` | Mining activity | Commodities (industrial metals, precious metals) | MEDIUM |
| `RARE_EARTH` | Rare earth minerals | Commodities (industrial metals) | HIGH |

### 3.4 Financial and Economic Themes

| GKG Theme | Description | Sleeve Mapping | Weight |
|-----------|-------------|----------------|--------|
| `ECON_INFLATION` | Inflation-related content | Rates (US), Rates (ex-US), Commodities | HIGH |
| `ECON_INTEREST_RATE` | Interest rate discussion | Rates (US), Rates (ex-US) | HIGH |
| `ECON_DEBT` | Debt/fiscal concerns | Rates (US), Rates (ex-US) | MEDIUM |
| `ECON_CURRENCY` | Currency discussion | Rates (ex-US), Crypto | MEDIUM |
| `ECON_RECESSION` | Recession references | Rates (US), Rates (ex-US), all sleeves | HIGH |
| `ECON_STOCKMARKET` | Stock market references | Contextual | LOW |
| `ECON_BANKRUPTCY` | Bankruptcy | Rates, Commodities | MEDIUM |
| `CENTRAL_BANK` | Central bank references | Rates (US), Rates (ex-US) | HIGH |
| `IMF` | IMF references | Rates (ex-US) | MEDIUM |
| `WORLD_BANK` | World Bank references | Rates (ex-US) | LOW |
| `TAX_FNCACT_CENTRAL_BANK` | Central bank function | Rates (US), Rates (ex-US) | HIGH |
| `TAX_FNCACT_FINANCE_MINISTER` | Finance minister function | Rates (ex-US) | MEDIUM |
| `CRYPTOCURRENCY` | Cryptocurrency references | Crypto (BTC core, ETH) | HIGH |
| `BLOCKCHAIN` | Blockchain references | Crypto | MEDIUM |
| `FINTECH` | Financial technology | Crypto | LOW |

### 3.5 Maritime and Shipping Themes

| GKG Theme | Description | Sleeve Mapping | Weight |
|-----------|-------------|----------------|--------|
| `MARITIME_INCIDENT` | Maritime incidents | Shipping (all sub-sleeves) | HIGH |
| `PIRACY` | Piracy events | Shipping (chokepoints, insurance/freight stress) | HIGH |
| `SHIPPING` | General shipping | Shipping | MEDIUM |
| `PORT` | Port references | Shipping (port clusters) | MEDIUM |
| `NAVY` | Naval references | Shipping, Defense (naval/shipbuilding) | MEDIUM |
| `COAST_GUARD` | Coast guard activity | Shipping | LOW |
| `MARITIME_SECURITY` | Maritime security | Shipping, Defense (naval) | MEDIUM |
| `OIL_TANKER` | Oil tanker references | Shipping, Commodities (energy) | HIGH |
| `CANAL` | Canal references (Suez, Panama) | Shipping (chokepoints) | HIGH |
| `STRAIT` | Strait references (Hormuz, Malacca) | Shipping (chokepoints) | HIGH |

### 3.6 Cyber and Technology Themes

| GKG Theme | Description | Sleeve Mapping | Weight |
|-----------|-------------|----------------|--------|
| `CYBER_ATTACK` | Cyber attack references | Defense (cyber/EW) | HIGH |
| `HACKING` | Hacking references | Defense (cyber/EW) | MEDIUM |
| `RANSOMWARE` | Ransomware | Defense (cyber/EW) | MEDIUM |
| `ESPIONAGE` | Espionage | Defense (ISR, cyber) | MEDIUM |
| `CYBER_SECURITY` | Cybersecurity | Defense (cyber/EW) | MEDIUM |
| `SURVEILLANCE` | Surveillance references | Defense (ISR/space/comms) | MEDIUM |
| `SATELLITE` | Satellite references | Defense (ISR/space/comms) | MEDIUM |
| `SPACE` | Space-related | Defense (ISR/space/comms) | MEDIUM |
| `DRONE` | Drone/UAV references | Defense (ISR, munitions) | HIGH |
| `ARTIFICIAL_INTELLIGENCE` | AI references | Defense, Crypto | LOW |

### 3.7 Country/Region Group Tags

These GKG tags help route events to the correct geographic sub-sleeves:

| GKG Theme Pattern | Description | Primary Routing |
|-------------------|-------------|-----------------|
| `TAX_WORLDREGION_*` | World region taxonomy | Geographic filtering |
| `COUNTRY_*` | Country-specific tags | Rates (ex-US) country buckets |
| `NATO` | NATO references | Defense & Security |
| `EU` | European Union | Rates (ex-US), Shipping |
| `G7` / `G20` | G7/G20 references | Rates (all), Commodities |
| `BRICS` | BRICS references | Rates (ex-US), Commodities |
| `ASEAN` | ASEAN references | Shipping (South China Sea), Rates (ex-US) |

---

## 4. Goldstein Scale Integration

### 4.1 Overview

The Goldstein scale is a numeric score assigned to each CAMEO event code,
ranging from **-10.0** (maximum conflict) to **+10.0** (maximum cooperation).
It provides a continuous intensity measure that maps directly to the system's
severity scoring.

### 4.2 Goldstein Score Reference Table

| Goldstein Range | CAMEO Roots | Interpretation | System Mapping |
|-----------------|-------------|----------------|----------------|
| +8.0 to +10.0 | 06 (material coop), 07 (yield) | Strong cooperation/de-escalation | Defense: bearish; Shipping: bullish (route reopening); Commodities: bearish (supply fear easing) |
| +5.0 to +7.9 | 05 (diplo coop), 03 (intent to coop) | Moderate cooperation | Rates (ex-US): positive sentiment; Defense: mildly bearish |
| +1.0 to +4.9 | 04 (consult), 02 (appeal) | Mild positive/neutral | Background signal only |
| -0.9 to +0.9 | 01 (statement), 08 (investigate) | Neutral | Minimal signal value |
| -1.0 to -4.9 | 09 (disapprove), 10 (demand) | Mild escalation | Monitoring threshold |
| -5.0 to -6.9 | 11 (formal disapproval), 12 (reject), 14 (protest) | Moderate escalation | Defense: mildly bullish; Commodities: mildly bullish |
| -7.0 to -8.9 | 13 (threaten), 15 (force posture), 16 (reduce relations), 17 (coerce) | Serious escalation | Defense: bullish; Commodities: bullish; Shipping: bearish (disruption risk); Crypto: bearish (risk-off) |
| -9.0 to -10.0 | 18 (assault), 19 (fight), 20 (mass violence) | Extreme conflict/violence | All sleeves activated; maximum severity |

### 4.3 Key Goldstein Scores for Specific CAMEO Codes

| CAMEO Code | Event | Goldstein Score | Notes |
|------------|-------|-----------------|-------|
| 0256 | Appeal to others to engage in ceasefire | +3.4 | De-escalation signal |
| 036 | Express intent to meet/negotiate | +4.0 | Mild positive |
| 050 | Diplomatic cooperation | +3.5 | Positive background |
| 056 | Sign formal agreement | +6.0 | Strong positive |
| 057 | Extend economic aid | +7.4 | Strong cooperation |
| 0622 | Provide military aid | +7.5 | Cooperation but defense-positive |
| 071 | Ease administrative sanctions | +5.0 | De-escalation |
| 0712 | Ease military restrictions | +5.0 | Shipping positive |
| 074 | Allow passage/access | +4.0 | Shipping positive |
| 075 | Retreat or withdraw | +4.0 | De-escalation |
| 092 | Accuse | -2.0 | Mild escalation |
| 111 | Formally protest | -2.2 | Moderate escalation |
| 1121 | Reduce economic relations | -5.0 | Sanctions precursor |
| 1231 | Reject de-escalation | -5.0 | Escalation persistence |
| 1243 | Refuse ceasefire | -5.0 | Escalation persistence |
| 1313 | Threaten sanctions | -5.2 | Pre-sanctions stress |
| 134 | Threaten with military force | -7.0 | Serious threat |
| 1341 | Threaten blockade | -7.2 | Shipping critical |
| 135 | Threaten with WMD | -9.0 | Nuclear escalation |
| 1631 | Impose economic sanctions | -8.0 | Sanctions imposition |
| 1632 | Impose military blockade | -9.0 | Shipping/conflict critical |
| 1712 | Seize vessel | -7.0 | Shipping critical |
| 1812 | Hijack vessel | -8.0 | Shipping critical |
| 190 | Use conventional military force | -10.0 | Maximum conflict |
| 195 | Employ aerial weapons | -10.0 | Maximum conflict |
| 197 | Declare war | -10.0 | Maximum conflict |
| 198 | Use WMD | -10.0 | Maximum conflict |

### 4.4 Mapping Goldstein to System Severity Score

The system's `severity_score` field is a `[0.0, 1.0]` unit interval. Goldstein
should be transformed as follows:

```
For escalation signals (negative Goldstein):
    severity_score = min(1.0, abs(goldstein_score) / 10.0)

For de-escalation signals (positive Goldstein):
    severity_score = min(1.0, goldstein_score / 10.0)
    direction = invert (e.g., "short" defense instead of "long")

Threshold recommendation:
    |Goldstein| < 3.0  -->  filter out (noise)
    |Goldstein| >= 3.0  -->  include in signal generation
    |Goldstein| >= 7.0  -->  elevated priority
    |Goldstein| >= 9.0  -->  maximum priority, trigger immediate signal
```

### 4.5 Goldstein Momentum (Derivative Signal)

Beyond individual event scores, track the rolling mean and rate of change of
Goldstein scores for a given actor-pair or region:

- **Goldstein_mean_7d**: 7-day rolling mean of Goldstein scores for a dyad
- **Goldstein_delta_3d**: 3-day rate of change (current 3d mean minus prior 3d mean)
- **Goldstein_vol_14d**: 14-day standard deviation of Goldstein scores

A rapidly declining Goldstein_delta (cooperation collapsing) is a leading
indicator of escalation, even before kinetic events (19x, 20x) appear.

---

## 5. Tone and Sentiment Field Usage

### 5.1 GDELT Tone Fields

Each GDELT event record includes a `AvgTone` field, and GKG records include
a richer set of tone/sentiment dimensions. These map to the system's
`confidence_score` and novelty detection.

**Event Database (GDELT 2.0 Events):**

| Field | Range | Description |
|-------|-------|-------------|
| `AvgTone` | -100 to +100 (typically -15 to +15) | Average tone of all source articles covering this event. Negative = negative sentiment. |

**GKG (Global Knowledge Graph):**

| Field | Description | System Usage |
|-------|-------------|--------------|
| `V2Tone` | Semicolon-delimited: tone, positive score, negative score, polarity, activity reference density, self/group reference density, word count | Primary sentiment input |
| `V2Tone.tone` | Overall tone (first value) | Maps to signal confidence |
| `V2Tone.positive_score` | Positive word percentage | De-escalation confidence |
| `V2Tone.negative_score` | Negative word percentage | Escalation confidence |
| `V2Tone.polarity` | Degree of emotional language | Novelty proxy (high polarity = strong conviction in sources) |
| `V2Tone.activity_ref_density` | Density of action-oriented language | Event intensity proxy |
| `V2Tone.word_count` | Article word count | Coverage depth indicator |

### 5.2 GCAM (Global Content Analysis Measures)

The GKG's GCAM column contains 2,200+ pre-computed content analysis dimensions
derived from multiple dictionaries. Key dimensions for the trading system:

| GCAM Dimension | Dictionary | Description | System Usage |
|----------------|------------|-------------|--------------|
| `c1.1` - `c1.4` | General Inquirer | Positive/Negative affect | General sentiment baseline |
| `c2.1` - `c2.5` | WordNet Affect | Joy, Sadness, Fear, Anger, Surprise | Fear (c2.3) and Anger (c2.4) for escalation intensity |
| `c3.1` | LIWC | Anxiety words | Risk-off signal proxy |
| `c3.2` | LIWC | Anger words | Escalation intensity |
| `c3.3` | LIWC | Sadness words | Post-event / humanitarian phase |
| `c4.1` - `c4.5` | SentiWordNet | Positive, Negative, Objective scores | Sentiment confirmation |
| `c5.1` - `c5.3` | AFINN | Sentiment valence | Rapid sentiment proxy |
| `c9.1` | HedgeFinder | Uncertainty/hedging language | Confidence dampener -- high hedge = lower system confidence |
| `c12.1` - `c12.14` | Loughran-McDonald Financial | Positive, Negative, Uncertainty, Litigious, Constraining, Superfluous | Financial sentiment; Uncertainty (c12.3) maps to Rates volatility signal |
| `c14.1` - `c14.3` | SentiStrength | Positive, Negative, Trinary | Rapid polarity check |
| `c17.1` - `c17.10` | VADER | Compound, Positive, Negative, Neutral | Social media-tuned sentiment |

### 5.3 Mapping Tone to System Confidence Score

The `confidence_score` in `ExpertPrediction` should incorporate tone signals:

```
Base confidence from tone:
    tone_confidence = 1.0 - (hedge_score / max_hedge)
    -- Higher hedging language = lower confidence

Confirmation from polarity:
    if event is escalation (Goldstein < 0) and tone < -3.0:
        polarity_boost = 0.1  -- Tone confirms escalation narrative
    if event is escalation (Goldstein < 0) and tone > 0:
        polarity_penalty = -0.15  -- Tone contradicts; possible de-escalation framing

Novelty detection:
    article_count = number of distinct source URLs for this event
    if article_count < 3:
        novelty_flag = "emerging"  -- early/unconfirmed
        confidence_penalty = -0.2
    if article_count > 15:
        novelty_flag = "saturated"  -- well-known, possibly priced in
        confidence_penalty = -0.1
    if article_count in [3, 15]:
        novelty_flag = "developing"  -- optimal signal window
        confidence_boost = 0.0  -- baseline
```

### 5.4 Source Diversity and Confidence

GDELT records include `NumSources` (number of distinct news sources) and
`NumArticles` (total article count) for each event. Use these for confidence:

| Source Count | Interpretation | Confidence Adjustment |
|--------------|----------------|----------------------|
| 1 source | Unconfirmed / single-source | confidence *= 0.5 |
| 2-4 sources | Emerging, partially confirmed | confidence *= 0.8 |
| 5-10 sources | Well-confirmed, developing story | confidence *= 1.0 (baseline) |
| 11-25 sources | Major event, broad coverage | confidence *= 1.0 |
| 25+ sources | Viral/saturated; may be priced in | confidence *= 0.9 (staleness risk) |

---

## 6. Disambiguation Rules

### 6.1 Actor-Based Disambiguation

CAMEO actor codes determine which sleeve an event routes to. Key actor type
codes from GDELT's `Actor1Type1Code` and `Actor2Type1Code` fields:

| Actor Type Code | Actor Type | Primary Sleeve Routing |
|-----------------|------------|------------------------|
| GOV | Government | Rates (US or ex-US depending on country), Defense |
| MIL | Military | Defense & Security |
| REB | Rebel/insurgent | Defense & Security |
| OPP | Political opposition | Rates (ex-US) |
| BUS | Business | Commodities, Shipping |
| COP | Police/law enforcement | Rates (ex-US) |
| JUD | Judiciary | Rates (ex-US) |
| SPY | Intelligence | Defense (ISR/cyber) |
| IGO | Intergovernmental organization | Rates (ex-US), Shipping |
| NGO | Non-governmental organization | LOW relevance |
| MED | Media | Contextual only |
| REL | Religious | LOW relevance |
| EDU | Education | LOW relevance |
| CVL | Civilian | LOW relevance (unless target of 20x events) |

### 6.2 Geographic Disambiguation

The `ActionGeo_CountryCode` (FIPS country code) determines regional routing:

| Region | FIPS Codes | Sleeve Routing |
|--------|------------|----------------|
| US/Canada | US, CA | Rates (US), Defense |
| Europe (NATO) | UK, FR, GM, IT, SP, PL, NO, TU, etc. | Rates (ex-US: EU bucket), Defense |
| Russia/FSU | RS, UP (Ukraine), BO, GG, etc. | Rates (ex-US: Russia), Shipping (Black Sea), Commodities (energy, agriculture) |
| Middle East Oil | SA, IR, IZ, KU, QA, AE, BH | Commodities (energy), Shipping (Hormuz, Bab el-Mandeb) |
| Red Sea/Horn | YM, DJ, ER, SO, SU | Shipping (Bab el-Mandeb, Suez), Commodities (energy routing) |
| East Asia | CH, TW, JA, KN, KS | Shipping (Taiwan Strait, SCS), Commodities (industrial metals), Defense |
| South Asia | IN, PK | Shipping (Indian Ocean, port clusters), Rates (ex-US: India), Defense |
| Southeast Asia | VM, RP, MY, BM, ID, TH | Shipping (South China Sea, Malacca), Commodities |
| Sub-Saharan Africa | NI, SF, CG, etc. | Commodities (industrial metals, energy), Rates (ex-US) |
| Latin America | BR, MX, VE, CO, AR | Commodities (energy, agriculture, metals), Rates (ex-US) |

### 6.3 Event Directionality Disambiguation

Some events can be interpreted as either bullish or bearish for a sleeve
depending on context. Resolution rules:

| Ambiguous Event | Condition | Direction for Defense | Direction for Shipping |
|-----------------|-----------|----------------------|----------------------|
| Military cooperation (0612, 058) | Between allies (e.g., US-NATO) | Bullish (primes, ISR) | Neutral |
| Military cooperation (0612, 058) | Involving adversary (e.g., RUS-IRN) | Bullish (escalation fear) | Bearish (route risk) |
| Sanctions easing (0711) | Against adversary | Bearish (conflict winding down) | Bullish (routes reopening) |
| Sanctions easing (0711) | Trade normalization | Neutral | Bullish |
| Military exercises (153) | Routine/annual | LOW relevance | LOW relevance |
| Military exercises (153) | In disputed region | Bullish (escalation) | Bearish (disruption risk) |
| Ceasefire (0353, 1053) | Accepted | Bearish (conflict ending) | Bullish (normalization) |
| Ceasefire (0353, 1053) | Rejected (1243) | Bullish (conflict persisting) | Bearish (disruption persisting) |

### 6.4 Crypto-Specific Disambiguation

Crypto sleeve activation is driven by:

| Signal Source | CAMEO/GKG Trigger | Crypto Direction |
|---------------|-------------------|------------------|
| Systemic geopolitical risk | Goldstein <= -8.0 with 19x/20x codes | BTC: initially bearish (risk-off), then bullish (safe-haven narrative for sustained crises) |
| Sanctions on financial system | 1631 targeting financial sector | BTC: bullish (sanctions evasion narrative) |
| Currency crisis | GKG themes: ECON_CURRENCY + ECON_INFLATION in emerging markets | BTC: bullish (capital flight narrative) |
| Crypto regulation | GKG theme CRYPTOCURRENCY + CAMEO 172x (impose admin sanctions) | BTC: bearish (regulatory clampdown) |
| Dollar strength signals | ECON_INTEREST_RATE + US actor codes | BTC: bearish (strong dollar = weak BTC) |

---

## 7. Composite Signal Construction Notes

### 7.1 Event Aggregation Windows

GDELT produces events every 15 minutes. Raw events must be aggregated before
feeding into expert models. Recommended windows:

| Window | Use Case | Aggregation Method |
|--------|----------|--------------------|
| 1-hour | Real-time signal generation | Count of events by CAMEO root, mean Goldstein, min tone |
| 6-hour | Intraday regime detection | Weighted sum of severity scores, geographic concentration |
| 24-hour | Daily feature construction | Event counts by root code, Goldstein momentum, source diversity |
| 7-day rolling | Trend and escalation trajectory | Goldstein_mean, delta, volatility; event type distribution shift |
| 30-day rolling | Baseline / regime classification | Background conflict level, sanctions intensity |

### 7.2 Feature Engineering from GDELT Fields

Recommended features to extract from GDELT for the expert models:

| Feature Name | GDELT Source | Computation | Target Expert |
|--------------|-------------|-------------|---------------|
| `escalation_count_24h` | Event DB | Count of events with CAMEO root in {13,15,17,18,19,20} in trailing 24h for a region | conflict_escalation |
| `cooperation_count_24h` | Event DB | Count of events with CAMEO root in {03,05,06,07} in trailing 24h | conflict_escalation (inverse) |
| `escalation_ratio_7d` | Event DB | escalation_count / (escalation_count + cooperation_count) over 7d | conflict_escalation |
| `goldstein_momentum_3d` | Event DB | Delta of 3d Goldstein mean vs prior 3d mean | conflict_escalation |
| `sanctions_intensity_7d` | Event DB + GKG | Count of CAMEO {163x, 172x} + GKG TAX_FNCACT_SANCTIONS in 7d | shipping_chokepoint |
| `chokepoint_event_count_24h` | Event DB | Count of events geo-located to chokepoint regions in 24h | shipping_chokepoint |
| `vessel_seizure_count_7d` | Event DB | Count of CAMEO {1712, 1812} events in 7d | shipping_chokepoint |
| `energy_theme_intensity_24h` | GKG | Count of articles with ENV_OIL or ENV_NATURALGAS themes in 24h | market_pricing (energy) |
| `tone_negativity_24h` | GKG V2Tone | Mean negative_score across conflict-tagged articles in 24h | All experts (confidence) |
| `source_diversity_event` | Event DB | NumSources for each event | All experts (confidence) |
| `nuclear_signal_7d` | Event DB + GKG | Count of CAMEO {135, 136, 184, 198} + GKG WMD/NUCLEAR in 7d | conflict_escalation (nuclear sub-ladder) |
| `central_bank_tone_24h` | GKG | Mean tone of articles with CENTRAL_BANK theme in 24h | rates_policy |
| `crypto_regulatory_7d` | GKG | Count of CRYPTOCURRENCY + negative tone articles in 7d | crypto_regime |
| `protest_intensity_7d` | Event DB | Count of CAMEO 14x events weighted by Goldstein, by country | rates_policy (ex-US) |

### 7.3 Event-to-Sleeve Priority Matrix

Summary matrix showing which CAMEO root codes have the highest priority for
each sleeve. Use this for efficient event routing in the pipeline.

| CAMEO Root | Defense | Shipping | Commodities | Crypto | Rates (US) | Rates (ex-US) |
|------------|---------|----------|-------------|--------|------------|---------------|
| 01 Statement | LOW | LOW | LOW | LOW | MEDIUM | MEDIUM |
| 02 Appeal | MEDIUM | LOW | LOW | -- | -- | LOW |
| 03 Intent Coop | MEDIUM | LOW | MEDIUM | -- | -- | MEDIUM |
| 04 Consult | LOW | -- | -- | -- | MEDIUM | MEDIUM |
| 05 Diplo Coop | MEDIUM | MEDIUM | MEDIUM | -- | -- | MEDIUM |
| 06 Material Coop | HIGH | MEDIUM | MEDIUM | -- | -- | MEDIUM |
| 07 Yield | HIGH | HIGH | HIGH | -- | -- | MEDIUM |
| 08 Investigate | LOW | MEDIUM | -- | MEDIUM | -- | LOW |
| 09 Disapprove | MEDIUM | LOW | MEDIUM | -- | -- | LOW |
| 10 Demand | HIGH | MEDIUM | MEDIUM | -- | -- | MEDIUM |
| 11 Formal Disap | HIGH | HIGH | HIGH | -- | -- | HIGH |
| 12 Reject | HIGH | MEDIUM | MEDIUM | -- | -- | MEDIUM |
| 13 Threaten | **HIGH** | **HIGH** | **HIGH** | MEDIUM | LOW | MEDIUM |
| 14 Protest | LOW | HIGH | MEDIUM | -- | -- | MEDIUM |
| 15 Force Posture | **HIGH** | **HIGH** | HIGH | MEDIUM | -- | MEDIUM |
| 16 Reduce Rel | HIGH | **HIGH** | **HIGH** | -- | -- | HIGH |
| 17 Coerce | HIGH | **HIGH** | HIGH | MEDIUM | -- | HIGH |
| 18 Assault | HIGH | HIGH | MEDIUM | -- | -- | MEDIUM |
| 19 Fight | **HIGH** | **HIGH** | **HIGH** | MEDIUM | LOW | HIGH |
| 20 Mass Violence | **HIGH** | MEDIUM | HIGH | MEDIUM | LOW | HIGH |

Cells marked `--` indicate no meaningful mapping for that combination.
Bolded **HIGH** indicates the highest-priority routing for the sleeve.

### 7.4 GDELT Data Access Quick Reference

| Access Method | URL/Endpoint | Best For |
|---------------|-------------|----------|
| Raw CSV (Events) | `http://data.gdeltproject.org/gdeltv2/masterfilelist.txt` | Backtesting, bulk historical |
| Raw CSV (GKG) | Same master file list (GKG rows) | Theme extraction, GCAM features |
| Raw CSV (Mentions) | Same master file list (mentions rows) | Source diversity, confidence scoring |
| DOC 2.0 API | `https://api.gdeltproject.org/api/v2/doc/doc` | Real-time monitoring, keyword search |
| Context API | `https://api.gdeltproject.org/api/v2/context/context` | Contextual article retrieval |
| GEO API | `https://api.gdeltproject.org/api/v2/geo/geo` | Geographic event mapping |
| BigQuery | `gdelt-bq.gdeltv2.events`, `gdelt-bq.gdeltv2.gkg` | Complex historical queries |

### 7.5 Event Database Column Reference (Key Fields)

| Column | Description | System Usage |
|--------|-------------|--------------|
| `GLOBALEVENTID` | Unique event ID | Dedup key |
| `SQLDATE` | Event date (YYYYMMDD) | Temporal windowing |
| `Actor1Code` | Primary actor CAMEO code | Actor-based routing |
| `Actor1Name` | Actor name string | Entity resolution |
| `Actor1CountryCode` | Actor 1 country (FIPS) | Geographic routing |
| `Actor1Type1Code` | Actor 1 type (GOV, MIL, etc.) | Sleeve disambiguation |
| `Actor2Code` | Secondary actor CAMEO code | Dyad analysis |
| `Actor2CountryCode` | Actor 2 country (FIPS) | Geographic routing |
| `Actor2Type1Code` | Actor 2 type | Sleeve disambiguation |
| `IsRootEvent` | Whether this is the root event in the cluster | Prefer root events for dedup |
| `EventCode` | Full CAMEO event code | Primary signal classification |
| `EventRootCode` | CAMEO root code (01-20) | High-level routing |
| `EventBaseCode` | CAMEO base code (2-3 digits) | Mid-level routing |
| `QuadClass` | Quad classification (1=Verbal Coop, 2=Material Coop, 3=Verbal Conflict, 4=Material Conflict) | Fast escalation filter |
| `GoldsteinScale` | Goldstein score for this event code | Severity mapping |
| `NumMentions` | Number of source mentions | Confidence proxy |
| `NumSources` | Number of distinct sources | Confidence proxy |
| `NumArticles` | Number of distinct articles | Coverage depth |
| `AvgTone` | Average tone of source documents | Sentiment signal |
| `ActionGeo_CountryCode` | Country where action took place (FIPS) | Geographic routing |
| `ActionGeo_Lat` / `ActionGeo_Long` | Latitude/longitude of action | Chokepoint proximity calculation |
| `DATEADDED` | Timestamp event was added to GDELT | Latency tracking |
| `SOURCEURL` | URL of source article | Source quality assessment |

### 7.6 QuadClass Shortcut for Fast Routing

GDELT's `QuadClass` field provides a fast pre-filter before examining detailed
CAMEO codes:

| QuadClass | Category | CAMEO Roots | System Action |
|-----------|----------|-------------|---------------|
| 1 | Verbal Cooperation | 01-05 | Low priority; feed into background features |
| 2 | Material Cooperation | 06-07 | Medium priority; potential de-escalation signal |
| 3 | Verbal Conflict | 08-13 | Medium-High priority; escalation monitoring |
| 4 | Material Conflict | 14-20 | **Highest priority**; immediate signal generation |

For real-time monitoring, filter on `QuadClass IN (3, 4)` first, then examine
detailed CAMEO codes for sleeve routing.

---

## Appendix A: CAMEO Root Code Quick Reference

| Code | Name | Goldstein Range | QuadClass | System Priority |
|------|------|-----------------|-----------|-----------------|
| 01 | Make Public Statement | -1.0 to +3.4 | 1 | Low |
| 02 | Appeal | +1.0 to +3.4 | 1 | Low |
| 03 | Express Intent to Cooperate | +3.0 to +5.0 | 1 | Medium |
| 04 | Consult | +1.0 to +4.0 | 1 | Low |
| 05 | Engage in Diplomatic Cooperation | +3.5 to +7.4 | 1 | Medium |
| 06 | Engage in Material Cooperation | +6.0 to +8.0 | 2 | Medium |
| 07 | Yield | +4.0 to +7.4 | 2 | Medium-High |
| 08 | Investigate | -2.0 to +0.0 | 3 | Low |
| 09 | Disapprove | -3.5 to -2.0 | 3 | Low-Medium |
| 10 | Demand | -5.0 to -3.0 | 3 | Medium |
| 11 | Disapprove (Formal) | -5.0 to -2.2 | 3 | Medium |
| 12 | Reject | -7.0 to -4.0 | 3 | Medium-High |
| 13 | Threaten | -9.2 to -4.4 | 3 | High |
| 14 | Protest | -6.5 to -3.0 | 4 | Medium |
| 15 | Exhibit Force Posture | -7.2 to -3.0 | 4 | High |
| 16 | Reduce Relations | -8.0 to -4.0 | 4 | High |
| 17 | Coerce | -9.0 to -5.0 | 4 | High |
| 18 | Assault | -9.5 to -6.5 | 4 | High |
| 19 | Fight | -10.0 to -8.0 | 4 | Highest |
| 20 | Use Unconventional Mass Violence | -10.0 to -9.0 | 4 | Highest |

---

## Appendix B: GKG Theme Combination Patterns

Certain GKG theme combinations are more informative than individual themes.
Use these as composite features:

| Theme Combination | Interpretation | Sleeve | Weight |
|-------------------|---------------|--------|--------|
| `TAX_FNCACT_SANCTIONS` + `ENV_OIL` | Oil sanctions (Iran/Russia style) | Commodities (energy), Shipping | HIGH |
| `CRISISLEX_C04_MILITARY` + `WMD` | Military crisis with WMD dimension | Defense (nuclear enterprise) | HIGH |
| `PIRACY` + `STRAIT` | Maritime piracy at chokepoint | Shipping (chokepoints, insurance) | HIGH |
| `CYBER_ATTACK` + `TAX_FNCACT_MILITARY` | State-sponsored cyber operation | Defense (cyber/EW) | HIGH |
| `ECON_INFLATION` + `CENTRAL_BANK` | Inflation + central bank response | Rates (US or ex-US) | HIGH |
| `CRYPTOCURRENCY` + `TAX_FNCACT_SANCTIONS` | Crypto sanctions intersection | Crypto (regulatory) | HIGH |
| `ARMED_CONFLICT` + `ENV_OIL` | Conflict in oil-producing region | Commodities (energy) | HIGH |
| `FOOD_SECURITY` + `ARMED_CONFLICT` | Conflict-driven food crisis | Commodities (agriculture) | HIGH |
| `TRADE_DISPUTE` + `RARE_EARTH` | Rare earth trade restrictions | Commodities (industrial metals) | HIGH |
| `NAVY` + `STRAIT` or `CANAL` | Naval presence at chokepoint | Shipping (chokepoints), Defense (naval) | HIGH |
| `DRONE` + `CRISISLEX_C04_MILITARY` | Military drone operation | Defense (ISR, munitions) | HIGH |
| `ECON_CURRENCY` + `ECON_INFLATION` + emerging market country | EM currency crisis | Rates (ex-US), Crypto (BTC) | HIGH |
| `NUCLEAR` + `ARMS_TRADE` | Nuclear proliferation signal | Defense (nuclear enterprise) | HIGH |
| `SATELLITE` + `MILITARY` | Military space activity | Defense (ISR/space/comms) | MEDIUM |

---

## Appendix C: Port Cluster Geographic Matching

For routing events to Shipping port cluster sub-sleeves, use `ActionGeo_Lat`
and `ActionGeo_Long` with bounding boxes:

| Port Cluster | Lat Range | Lon Range | Key Ports |
|--------------|-----------|-----------|-----------|
| India West Coast | 8.0 - 23.5 N | 68.0 - 74.0 E | Mumbai (JNPT), Mundra, Kandla, Kochi, Mangalore |
| India East Coast | 8.0 - 22.0 N | 78.0 - 89.0 E | Chennai, Visakhapatnam, Paradip, Haldia |
| Persian Gulf | 23.0 - 30.5 N | 47.0 - 56.5 E | Jebel Ali, Ras Tanura, Kharg Island, Bandar Abbas |
| Red Sea/Aden | 11.5 - 15.5 N | 42.0 - 45.5 E | Aden, Djibouti, Jeddah |
| Suez Zone | 29.5 - 31.5 N | 32.0 - 33.0 E | Port Said, Suez |
| Black Sea | 41.0 - 47.0 N | 28.0 - 42.0 E | Odesa, Novorossiysk, Constanta, Istanbul |
| Taiwan Strait | 23.0 - 26.0 N | 117.0 - 121.0 E | Kaohsiung, Xiamen, Fuzhou |
| Malacca Strait | 1.0 - 4.0 N | 99.0 - 104.5 E | Singapore, Port Klang |
