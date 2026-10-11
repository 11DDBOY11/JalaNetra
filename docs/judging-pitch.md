# JalaNetra: Judging Pitch & Track Alignment
**Hackathon:** WeMakeDevs x AWS Environmental Hacks  
**Track:** Heat & Water

---

## 1. Executive Summary
JalaNetra addresses coastal urban groundwater vulnerability in Mangaluru (Dakshina Kannada, Karnataka). By combining 25 years of Central Ground Water Board (CGWB) quarterly observations, regional rainfall trends, and hyper-local citizen reports, JalaNetra gives households an advance action window: booking water tankers before local depletion causes price gouging and dry taps.

---

## 2. Track Relevance: Heat & Water
- **Problem:** Intense tropical heat combined with rapid rainwater runoff through laterite terrain depletes shallow coastal aquifers rapidly from November through May.
- **Intervention:** Actionable citizen-facing early warning, preventing domestic panic and smoothing municipal tanker demand.

---

## 3. Core Technical Pillars & AWS Architecture
1. **Serverless Application Stack (AWS CDK v2):**
   - Amazon API Gateway -> AWS Lambda (Python 3.11).
   - Amazon DynamoDB for rapid single-table ward state and citizen feedback.
2. **Citizen Communication Services:**
   - Amazon SNS for automated localized SMS dispatches.
   - Amazon Polly for synthesized regional voice-alert scripts (English & Hindi).
3. **Future Edge Telemetry Roadmap:**
   - AWS IoT Greengrass v2 containerized component for open-well ultrasonic transducers.

---

## 4. Key Differentiator: Rigorous Data Honesty & Transparency
Unlike prototypes that simulate fake "live IoT data" without disclosure, JalaNetra explicitly declares:
- **Real Historical Data:** 4,962 CGWB quarterly observations across 115 Dakshina Kannada wells from `gwl_manual_quarterly_cgwb_ka_1991_2020.csv`.
- **Honest Cadence Disclosure:** *“Historical quarterly government groundwater observations; not live groundwater sensor data.”*
- **Strict Stale-Data Guardrail (`MAX_CURRENT_FORECAST_AGE_DAYS = 180`):** Suppresses false present-day tanker booking dates when historical data exceeds 180 days, classifying records honestly as `historical_context`.
- **What-if Scenario Simulator:** Provides clear, labeled simulation of hypothetical current conditions without polluting verified government historical records.
- **Heuristic Parameter:** *“Configurable demonstration water-stress threshold (16 m depth-below-ground-level). It is a decision-support parameter, not a universal official dry-well standard.”*
- **Hardware-Free Evaluation:** *“Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.”*
