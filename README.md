# JalaNetra (जलनेत्र)
> **Mangaluru Water Security Early Warning System**  
> *Environmental Hacks (WeMakeDevs x AWS) — Heat & Water Track*

---

## 🎯 The Core Promise
> **“India’s rainiest coast is running out of water. JalaNetra tells Mangaluru households exactly which week to act.”**

Despite receiving over 3,800 mm of annual rainfall, the coastal city of Mangaluru (Dakshina Kannada, Karnataka) suffers acute groundwater depletion every dry season. Household borewells and open wells dry up with little notice, leaving residents scrambling for emergency water tankers at surge pricing.

**JalaNetra** fuses:
1. **Central Ground Water Board (CGWB)** historical monitoring well baselines in Dakshina Kannada
2. **IMD** precipitation trends and seasonal recharge models
3. **Crowdsourced Citizen Ground Truth** (“JalaNetra Sahayak” 1-click tap pressure reports)
4. **Simulated Edge Telemetry** (architectural roadmap for future AWS IoT Greengrass sensor nodes)

Into **one clear, actionable resident alert**:
> **“Water stress is likely in Kodialbail in approximately 3 weeks. Book a tanker by [Date].”**

---

## 🛡️ Hackathon Data Transparency & Honesty Policy
- **REAL CGWB GROUNDWATER DATA INGESTED**: JalaNetra ingests the real Central Ground Water Board (CGWB) quarterly dataset: `data/raw/groundwater/gwl_manual_quarterly_cgwb_ka_1991_2020.csv` (104,781 total records across Karnataka; filtered down to **4,962 verified historical records across 115 monitoring stations in Dakshina Kannada**, spanning 1996–2020).
- **Data Freshness Statement**:
  > **“Historical quarterly government groundwater observations; not live groundwater sensor data.”**
- **Hybrid Data Mode**: Ingested historical CGWB records are paired with clearly labeled municipal demo boundaries and seasonal precipitation baselines.
- **Configurable Demonstration Water-Stress Threshold (16 m depth-below-ground-level)**:
  > **Note:** This threshold is a configurable decision-support parameter for planning purposes, not a universal official dry-well standard.
- **Simulated Edge Telemetry**:
  > **“Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.”**
- **Amazon Polly Compatibility**:
  > **“Amazon Polly-compatible multilingual voice-alert script preview.”** Voice dispatches are script previews only; no real phone calls are placed.
- **No Real Phone Numbers / No Real SMS**: All phone numbers are masked in storage and responses (`+91 98*** **210`). No unsolicited real SMS or carrier fees are dispatched.

---

## 🏛️ System Architecture

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                      DATA SOURCES                            │
                    │  • CGWB Historical Monitoring Wells (Dakshina Kannada)      │
                    │  • Regional Precipitation Historical Baselines              │
                    │  • JalaNetra Sahayak (Citizen Tap Reports)                  │
                    │  • Simulated Edge Telemetry (Greengrass Roadmap)            │
                    └──────────────────────────────┬──────────────────────────────┘
                                                   │
                                                   ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                 INGESTION & DATA NORMALIZER                 │
                    │  • Canonical schema mapping (groundwater_depth_m, rain_mm) │
                    │  • Dakshina Kannada spatial filtering & quality audit       │
                    └──────────────────────────────┬──────────────────────────────┘
                                                   │
                                                   ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │             TRANSPARENT RISK FORECAST ENGINE                │
                    │  • Deterministic Coastal Aquifer Depletion Heuristic        │
                    │  • Configurable demonstration water-stress threshold (16m)  │
                    │  • Days-to-dry projection & recommended tanker booking date │
                    └──────────────────────────────┬──────────────────────────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         ▼                                                   ▼
         ┌───────────────────────────────┐                   ┌───────────────────────────────┐
         │     AWS CLOUD (CDK Stack)     │                   │       LOCAL DEMO STACK        │
         │ • API Gateway + Lambda        │                   │ • FastAPI Backend (Port 8000) │
         │ • Amazon DynamoDB Tables      │                   │ • SQLite / In-Memory Mock DB  │
         │ • Amazon SNS (SMS Dispatch)   │                   │ • React 19 + Vite (Port 5173) │
         │ • Amazon Polly Script Preview │                   │ • Edge Telemetry Simulator    │
         └───────────────────────────────┘                   └───────────────────────────────┘
```

---

## 🚀 Quickstart: Running Locally on Windows

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 1. Install Backend Dependencies & Run Backend
In PowerShell terminal 1:
```powershell
pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Install Frontend Dependencies & Run Web App
In PowerShell terminal 2:
```powershell
cd web
npm install
npm run dev
```
Open your browser at: [http://localhost:5173](http://localhost:5173)

### 3. Run the Simulated Edge Telemetry Node (Optional)
In PowerShell terminal 3:
```powershell
python edge/simulator.py --count 5 --interval 1.0
```

---

## 🧪 Verification & Test Results

### Backend Automated Test Suite
Run all 52 unit and integration tests:
```powershell
python -m pytest tests
```
**Test Result: 52 passed (100% pass rate)**
- ✅ Ingestion & normalizer tests (CGWB aliases, missing values, Dakshina Kannada spatial filtering)
- ✅ Ward builder tests (Dakshina Kannada spatial mapping, hybrid data mode detection)
- ✅ Stale-data guardrail tests (`MAX_CURRENT_FORECAST_AGE_DAYS = 180`, `historical_context` risk classification)
- ✅ What-if scenario simulator tests (labeled scenario advisories, preserves verified historical source rows)
- ✅ Alert generator tests (SMS formatting, Polly voice synthesis script previews, illustrative labels)
- ✅ API endpoint tests (`/health`, `/api/wards`, `/api/forecast`, `/api/reports`, `/api/alerts/subscribe`, `/api/data-quality`)

### Frontend Build
```powershell
cd web
npm run build
```
**Build Result: Vite production bundle built successfully (`dist/index.html`, `dist/assets/`).**

### AWS CDK Synthesis Note
The infrastructure code in `infra/app.py` is written for AWS CDK v2. To synthesize CloudFormation templates, install the optional CDK dependencies:
```powershell
pip install -r infra/requirements.txt
cd infra
npx aws-cdk synth
```

---

## 📡 API Contract Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Healthcheck & data mode status (`"hybrid"` / `"real_historical"` / `"demo"`) |
| `GET` | `/api/wards` | List all 5 wards with groundwater depth, risk level, stale-data guardrail status & freshness disclosure |
| `GET` | `/api/wards/{ward_id}` | Detailed ward state with historical observations & forecast |
| `GET` | `/api/forecast?ward_id=...&scenario=...` | Rule-based forecast, stale guardrail (`historical_context`), or what-if scenario simulation |
| `GET` | `/api/reports?ward_id=...` | Community crowdsourced tap status feed |
| `POST` | `/api/reports` | Submit citizen report (`status: "came"\|"low"\|"dry"`, `tanker_booked: bool`) |
| `POST` | `/api/alerts/subscribe` | Register phone for alerts (masked, demo safe) |
| `POST` | `/api/alerts/preview` | Preview bilingual SMS and Amazon Polly voice scripts |
| `GET` | `/api/data-quality` | Audit report of dataset freshness, row counts, and synthetic flags |

---

## 🎬 60-Second Video Demo Walkthrough Checklist

1. **[00:00 - 00:10] The Problem**:
   - Open [http://localhost:5173](http://localhost:5173).
   - Point out headline: *"India’s rainiest coast is running out of water."* Show the top **Hybrid Data Mode banner** declaring that records are historical quarterly government observations, not live monitoring.
2. **[00:10 - 00:25] Data Honesty & Stale-Data Guardrail**:
   - Highlight the **Stale-Data Guardrail**: Since CGWB records are from 2020 (> 180 days old), JalaNetra honestly marks them as `historical_context` and displays *"Historical groundwater context — current forecast unavailable"* with CTA to report today's water status.
   - Use the **What-if Scenario Simulator** to select *"Low supply"* or *"No water"* to demonstrate how JalaNetra generates labeled precautionary tanker advisories during an active dry spell.
3. **[00:25 - 00:35] Transparent Depletion Forecast**:
   - Switch to the **Depletion Forecast** tab. Show the Interactive Recharts graph projecting the water table against the **Configurable demonstration water-stress threshold (16 m depth-below-ground-level)**.
4. **[00:35 - 00:45] Citizen Ground Truth (Sahayak)**:
   - Go to **Citizen Sahayak** tab. Click *"❌ Dry / No Water"*, check *"Private tanker booked"*, and submit. Show the new report immediately appearing in the live community feed.
5. **[00:45 - 00:55] Simulated Alerts (AWS SNS + Polly Preview)**:
   - Switch to **Alert Dispatcher**. Toggle between English and Hindi to display the bilingual SMS payload and **Amazon Polly-compatible multilingual voice-alert script preview**.
6. **[00:55 - 01:00] Edge Roadmap & Wrap-up**:
   - Click **Simulated Edge Feed**, hit *"Trigger Edge Reading"* to demonstrate simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.
