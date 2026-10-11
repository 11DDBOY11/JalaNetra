# JalaNetra Model Card: Transparent Coastal Aquifer Heuristic

## Model Overview
- **Model Name:** JalaNetra Deterministic Aquifer Depletion Engine v1
- **Model Type:** Transparent, rule-based hydrological decision-support heuristic (no opaque deep learning).
- **Core Purpose:** Estimates remaining headroom before municipal household borewells face severe water stress, recommending an advance tanker-booking timeline.

## Parameters & Thresholds
- **Configurable demonstration water-stress threshold (16 m depth-below-ground-level):**
  > **Note:** This is a decision-support parameter chosen for demonstration and planning purposes, not a universal official dry-well standard.
- **Decision Support Bands:**
  - `depth < 8.0 m`: Low Stress (adequate aquifer storage)
  - `8.0 <= depth < 11.0 m`: Moderate Stress
  - `11.0 <= depth < 14.0 m`: High Stress
  - `depth >= 14.0 m`: Critical Stress
- **Seasonal Recharge Modifiers:** Monsoonal recharge (June–September) models rising water tables (-0.5 m/month), whereas post-monsoon dry season models depletion rates (0.2 to 0.8 m/month) based on extraction trends.

## Inputs & Training Data
- **Primary Observations:** Historical quarterly CGWB groundwater observations from `gwl_manual_quarterly_cgwb_ka_1991_2020.csv` (115 wells in Dakshina Kannada, 1996–2020).
- **Precipitation:** Baseline precipitation curves calibrated to coastal Karnataka seasonal averages.
- **Citizen Ground Reports:** Crowdsourced tap flow statuses directly elevate risk urgency when a verified dry report is logged.

## Stale-Data Guardrail (`MAX_CURRENT_FORECAST_AGE_DAYS = 180`)
- **Stale Observation Policy:** Any groundwater observation older than 180 days triggers a strict guardrail:
  - `forecast_current`: `false`
  - `forecast_status`: `"historical_context_only"`
  - `risk_level`: `"historical_context"` (never falsely classified as current high/critical)
  - `days_to_dry_estimate`: `null`
  - `weeks_to_dry`: `null`
  - `book_tanker_by`: `null` (never outputs a future booking date for stale historical data)
  - `confidence`: `"low"`
  - `recommended_action`: *“This record is historical. Report today’s water availability or connect a recent ward measurement before making a tanker-booking decision.”*
  - `explanation`: *“The latest verified CGWB groundwater observation for this matched station is from <date>. It is useful for historical context but too old for a current household water forecast.”*

## What-if Scenario Simulator
- To preserve an interactive demonstration without fabricating environmental data, JalaNetra provides an isolated **Scenario Simulator**:
  - Allows selecting hypothetical current signals: *Normal supply*, *Low supply*, *No water (dry)*.
  - Generates labeled precautionary tanker advisories: *“Scenario simulation — based on your selected current water report, not a live groundwater reading.”*
  - Never mutates or confuses verified historical CGWB observation records.

## Confidence & Limitations
- **Data Freshness Disclosure:**
  > **“Historical quarterly government groundwater observations; not live groundwater sensor data.”**
- **Confidence Scoring:** Automatically degraded to `low` when observations are fewer than 2, older than 60 days, or when falling back to synthetic seasonal defaults.
- **No Certainty Claims:** The system explicitly avoids definitive claims ("will definitely dry up") and instead produces transparent decision-support indicators to assist household preparedness.

---

## JalaNetra Pulse Outage Clustering Engine
- **Model Type:** Spatial-Temporal Rolling Window Density Clusterer.
- **Temporal Window:** 90 minutes.
- **Deduplication:** Rate-limits single client identities to 1 report per 30 minutes per ward.
- **Trigger Rule:** 3 or more independent household `dry` reports in the same ward.
- **Alert Status:** Transitions to `active` with severity `high` (3–4 reports) or `critical` (5+ reports).
- **Recovery Rule:** 2 or more independent `restored` or `available` reports transition the incident to `recovery`.
- **Mandatory Output Label:** *“Community-reported issue — not an official municipal confirmation.”*
