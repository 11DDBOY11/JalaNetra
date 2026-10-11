# JalaNetra Pulse — Hackathon Submission Demo Script

**Project:** JalaNetra Pulse  
**Positioning:** “Real-time community water-outage detection and neighborhood response for Mangaluru.”  
**Video File:** `submission/video/jalanetra_demo.mp4`  
**Format:** 1080p Full HD (1920x1080), 30 fps, H.264 / AAC MP4  
**Narration Engine:** Microsoft Edge Neural Voice (`en-IN-NeerjaNeural`, Indian English)  
**Target Duration:** 2 minutes 36 seconds (156.0s) — comfortably within 2m 20s to 2m 40s (140s–160s)  
**Resolution:** 1920x1080  
**Subtitles:** Synchronized lower-third high-contrast captions with contextual badge tags (`neural_narration.srt`)  
**Design Theme:** Current clean light civic-tech UI (zero dark neon styling, zero hackathon clutter)

---

## The Four Visibly Evidenced Areas

1. **About the Project:**
   Community-driven water outage detection for Mangaluru. Empowers residents to distinguish home plumbing failures from street-level municipal water cuts in under 90 minutes.
2. **Tech Stack and Architecture:**
   FastAPI, SQLite local store, React + TypeScript + Vite frontend, Python edge normalizer, and AWS CDK serverless infrastructure definition.
3. **How AWS is Used:**
   Serverless architecture defined with AWS CDK in `infra/`: Amazon API Gateway routes reports, AWS Lambda processes deduplication & SHA-256 masking, Amazon DynamoDB stores reports/alerts, Amazon EventBridge orchestrates 90-min rolling evaluations, Amazon SNS handles transactional notification previews with strict sandbox isolation, Amazon S3 stores historical CGWB observations, and AWS Amplify hosts the public dashboard.
4. **Working Product Flow:**
   Household status reporting (`Water available`, `Low supply`, `No water`) -> 90-minute cluster detection (3 independent reports in Kodialbail) -> Active Community Water Alert -> Operational Response Board with actionable checklist & recovery updates -> Grounded historical CGWB groundwater context with 180-day freshness safeguard.

---

## Core Honesty & Safety Disclosures (Strict Compliance)

1. **Simulated Scenario Disclosure:**
   In Scene 3, a prominent on-screen badge states: *“Simulated reports used for this recorded scenario.”*
2. **CDK Deployment Disclosure:**
   In Scene 6, the footer clearly discloses: *“Local demo shown. AWS deployment architecture defined with CDK.”*
3. **Zero Fabricated SMS:**
   SMS operates in preview-only mode with verified sandbox test send capability; no live cellular broadcasts were claimed or triggered.
4. **Historical vs Live Separation:**
   Historical quarterly observations from the Central Ground Water Board (4,962 records, 115 stations) provide geological context only. They are strictly blocked from generating present-day household tanker predictions via the 180-Day Freshness Guardrail.
5. **Privacy Protection:**
   Household telephone numbers are salted and SHA-256 hashed. No unmasked personal telephone numbers appear on the citizen dashboard.

---

## Detailed Scene Breakdown & Narration Transcript

### Scene 1 — Problem and Project (0:00 – 0:18, 18.0s)
- **Visual (`01_scene1_pulse_home.png`):**
  Current clean light civic-tech Pulse page for Mangaluru (`http://localhost:5173/`) showing monitored neighbourhoods and normal baseline conditions.
- **Spoken Narration (1.0s – 16.8s):**
  > “JalaNetra Pulse helps Mangaluru communities respond faster when a neighbourhood experiences a water-supply interruption. A resident often cannot tell whether a dry tap is only a home-level issue or a wider local outage.”
- **On-Screen Badge / Text:**
  - Badge: `JALANETRA PULSE • COMMUNITY WATER OUTAGE DETECTION FOR MANGALURU`
  - On-screen text: `JalaNetra Pulse` | `Community water outage detection for Mangaluru`

---

### Scene 2 — Current Community Reporting (0:18 – 0:38, 20.0s)
- **Visual (`02_scene2_report_water.png`):**
  Clean Report water status interface. Shows 3 status cards: `Available` (Normal flow), `Low supply` (Weak pressure), and `No water` (Taps dry) with `No water` selected, locality selector set to Kodialbail, and Submit update action.
- **Spoken Narration (19.0s – 30.3s):**
  > “Residents can report water availability, low supply, or no water. Reports are grouped by ward and time, while personal details are protected.”
- **On-Screen Badge / Text:**
  - Badge: `CURRENT COMMUNITY REPORTS • WATER AVAILABLE • LOW SUPPLY • NO WATER`
  - On-screen text: `Current community reports` | `Water available • Low supply • No water`

---

### Scene 3 — Outage Detection (0:38 – 1:05, 27.0s)
- **Visual (`03_scene3_outage_detected.png`):**
  Pulse page showing active incident banner: *“Water supply issue reported in Kodialbail: 3 residents reported no water in the last 90 minutes. Reported by local residents. Verification in progress. Confidence: MODERATE.”*
  Prominent honesty label: *“Simulated reports used for this recorded scenario.”*
- **Spoken Narration (39.0s – 50.8s):**
  > “When three independent residents in the same ward report no water within ninety minutes, JalaNetra Pulse detects a local pattern and creates a community water-issue incident.”
- **On-Screen Badge / Text:**
  - Badge: `3 INDEPENDENT REPORTS • 90-MINUTE WINDOW • COMMUNITY WATER ISSUE REPORTED`
  - On-screen text: `3 independent reports` | `90-minute detection window` | `Community water issue reported`
  - Honesty badge: `Simulated reports used for this recorded scenario.`

---

### Scene 4 — Response Board (1:05 – 1:27, 22.0s)
- **Visual (`04_scene4_response_board.png`):**
  Operational response board showing active incident in Kodialbail:
  - Ward: Kodialbail
  - Independent report count: 3
  - Report timeline: Verified household updates with timestamp
  - Recommended next actions checklist: Verify pipeline pressure, Inspect borewell/booster pump, Coordinate emergency tanker support, Escalate to ward helpline
  - Record restoration update button.
- **Spoken Narration (66.0s – 82.3s):**
  > “The response board turns reports into a structured local workflow. Apartment associations, ward volunteers, and community responders can verify the interruption, coordinate water support, and record recovery updates.”
- **On-Screen Badge / Text:**
  - Badge: `RESPONSE BOARD • VERIFY INTERRUPTION • COORDINATE SUPPORT • RECORD RECOVERY`
  - On-screen text: `Verify supply interruption` | `Coordinate water support` | `Record recovery`

---

### Scene 5 — Historical Water Context (1:27 – 1:46, 19.0s)
- **Visual (`05_scene5_water_context.png`):**
  Water context page showing verified historical CGWB data:
  - 4,962 historical CGWB observations
  - 115 Dakshin Kannada monitoring stations
  - Historical quarterly trend chart for Padil station (2005–2020)
  - 180-Day Freshness Guardrail disclosure: historical records are never presented as live water availability.
- **Spoken Narration (87.8s – 105.2s):**
  > “Historical Central Ground Water Board observations provide long-term groundwater context for Dakshin Kannada. JalaNetra keeps this separate from current outage detection, so historical data is never presented as live water availability.”
- **On-Screen Badge / Text:**
  - Badge: `4,962 CGWB OBSERVATIONS • 115 STATIONS • HISTORICAL CONTEXT (NOT LIVE MONITORING)`
  - On-screen text: `4,962 historical CGWB observations` | `115 Dakshin Kannada monitoring stations` | `Historical context — not live monitoring`

---

### Scene 6 — AWS Use and Architecture (1:46 – 2:19, 33.0s)
- **Visual 6A (1:46 – 2:04, `06_scene6_aws_architecture.png`):**
  Clean light AWS serverless architecture diagram codified with AWS CDK:
  - API Gateway & Lambda (Ingestion) -> Amazon DynamoDB (Storage) -> Amazon EventBridge (Audit) -> Amazon SNS (Notifications) -> AWS Amplify & S3 (Dashboard & Data Store).
  - Callouts: 90-Min Cluster Rule, Zero Privacy Leakage, Strict Sandbox Safety, Cost Optimized.
  - Mandatory Footer: *“Local demo shown. AWS deployment architecture defined with CDK.”*
- **Visual 6B (2:04 – 2:19, `06b_scene6_notification_test.png`):**
  Notification preview & sandbox test interface showing exact transactional alert payload with masked recipient and sandbox safety disclosure.
- **Spoken Narration (106.7s – 138.3s):**
  > “JalaNetra Pulse is designed as an AWS serverless system. Amazon API Gateway routes water reports to AWS Lambda. Amazon DynamoDB stores reports, incidents, and subscriptions. Amazon EventBridge evaluates alert patterns, Amazon SNS supports controlled transactional notifications, Amazon S3 stores historical data, and AWS Amplify hosts the public dashboard.”
- **On-Screen Badge / Text:**
  - Part 6A: `AWS SERVERLESS ARCHITECTURE • API GATEWAY • LAMBDA • DYNAMODB • CDK DEFINED`
  - Part 6B: `EVENTBRIDGE • SNS NOTIFICATION PREVIEW (SANDBOX SAFETY) • S3 • AMPLIFY`
  - On-screen text: `API Gateway • Lambda • DynamoDB` | `EventBridge • SNS • S3 • Amplify` | `AWS infrastructure defined with CDK`
  - Mandatory Footer: `Local demo shown. AWS deployment architecture defined with CDK.`

---

### Scene 7 — Impact and Close (2:19 – 2:36, 17.0s)
- **Visual (`07_scene7_impact_closing.png`):**
  Clean closing slide with current civic UI softly visible in background:
  - 3 Takeaway Cards: `Report early`, `Respond together`, `Build water resilience`
  - Final Title: `JalaNetra Pulse — Community water response for Mangaluru`
  - Tech Stack: `FastAPI • React • TypeScript • AWS CDK`
- **Spoken Narration (139.5s – 155.5s):**
  > “JalaNetra Pulse turns scattered household complaints into a shared community signal. It helps neighbourhoods recognize a water issue earlier, coordinate a response, and build a more reliable picture of local water stress.”
- **On-Screen Badge / Text:**
  - Badge: `REPORT EARLY • RESPOND TOGETHER • BUILD WATER-RESILIENT COMMUNITIES`
  - On-screen text: `Report early` | `Respond together` | `Build water-resilient communities`
  - Final Title: `JalaNetra Pulse — Community water response for Mangaluru`
