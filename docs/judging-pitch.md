# JalaNetra Pulse: Judging Pitch & Track Alignment
**Hackathon:** WeMakeDevs x AWS Environmental Hacks  
**Track:** Heat & Water  
**Product Name:** JalaNetra Pulse (जलनेत्र पल्स)  

---

## 1. Executive Summary & Primary Elevator Pitch
> **“JalaNetra Pulse detects neighborhood water outages in real time from independent household reports. When multiple residents in the same ward report no water within 90 minutes, it raises a transparent community alert, notifies subscribed residents, and gives ward responders a structured incident timeline. Historical CGWB groundwater data provides vulnerability context, but current action is always driven by current community signals.”**

### Mandatory Disclaimer
> **“Community-reported issue — not an official municipal confirmation.”**

---

## 2. Track Relevance: Heat & Water
- **The Problem:** Coastal Karnataka receives over 3,500 mm of rainfall during the monsoon, but steep terrain and porous lateritic soils accelerate runoff into the Arabian Sea. By March, municipal rationing and borewell drying hit Mangaluru wards hard.
- **The Gap in Existing Tools:** Dashboards relying on historical government data (quarterly CGWB wells from 1996–2020) cannot detect if taps ran dry this morning in Kodialbail or Surathkal.
- **The JalaNetra Pulse Solution:** Couples crowdsourced 1-click citizen reports with an automated 90-minute clustering engine that detects localized water outages, alerts subscribed neighbors, and coordinates tanker response before crisis escalates.

---

## 3. Core Technical Pillars & AWS Architecture
1. **Real-Time Clustering Engine (Local SQLite / AWS DynamoDB):**
   - 90-minute rolling window clusters independent reports.
   - Trigger threshold: 3 independent `dry` reports in the same ward creates an active Community Water Alert.
   - Deduplication: Single users are restricted to 1 report per ward/status per 30 minutes.
   - Recovery threshold: 2 independent `restored` or `available` reports transition the incident to Community Recovery.
2. **Production-Ready AWS CDK Architecture (`infra/`):**
   - Amazon API Gateway HTTP API -> AWS Lambda (Python 3.11).
   - DynamoDB tables: `water_reports`, `community_alerts`, `subscriptions`.
   - Amazon EventBridge 6-hour evaluation cron & daily data refresh.
   - Amazon SNS transactional SMS integration (safe test sandbox mode).
   - AWS Amplify hosting for high-contrast PWA.
   - *Cloud Status:* Codified via CDK; local demo runs with SQLite. No AWS cloud deployment or billing incurred.
3. **Emergency SMS Dispatch Sandbox:**
   - Safe by default: Returns payload preview when `SMS_LIVE_MODE=false`.
   - Verified send: Dispatches via boto3 SNS ONLY to configured `SMS_TEST_PHONE` when explicitly confirmed.
   - Never sends to crowdsourced user numbers.

---

## 4. Key Differentiators: Data Honesty & Responsible AI
- **Separation of Real-Time vs Contextual Layers:** Historical CGWB groundwater data (4,962 records, 115 stations) is clearly separated from live community reports.
- **Strict Stale-Data Guardrail:** Records older than 180 days are never extrapolated into false current alerts or speculative tanker bookings.
- **Zero-Knowledge Privacy:** Phone numbers are never stored in raw form; only salted SHA-256 hashes and masked strings (`+XX-XXXXX-XXXXX`) are persisted.
- **Simulation Transparency:** Demo scenario seeds are explicitly flagged with `simulation: true`.
