# JalaNetra Pulse (जलनेत्र पल्स)
> **Real-time community water-outage detection and neighborhood response for Mangaluru.**  
> *Environmental Hacks (WeMakeDevs x AWS) — Heat & Water Track*

---

## 🎯 The Core Elevator Pitch
> **“JalaNetra Pulse detects neighborhood water outages in real time from independent household reports. When multiple residents in the same ward report no water within 90 minutes, it raises a transparent community alert, notifies subscribed residents, and gives ward responders a structured incident timeline. Historical CGWB groundwater data provides vulnerability context, but current action is always driven by current community signals.”**

### ⚠️ Mandatory Truthfulness Disclaimer
> **“Community-reported issue — not an official municipal confirmation.”**

---

## 🌊 Why JalaNetra Pulse?
Despite receiving ~3,500 mm of annual monsoon rainfall, Mangaluru (Dakshina Kannada, Karnataka) experiences severe post-monsoon water rationing and sudden localized dry-tap emergencies. 

Traditional municipal dashboards rely on historical government data that cannot detect whether taps in Kodialbail or Surathkal actually ran dry this morning. **JalaNetra Pulse pivots municipal resilience from stale forecasts to real-time community ground signals:**
1. **Current Action from Current Community Reports:** Households submit 1-click tap status (`available`, `low`, `dry`, `restored`).
2. **Deterministic 90-Minute Outage Clustering:** When 3 or more independent households in the same ward report `dry` within a 90-minute rolling window, an active **Community Water Alert** is created instantly.
3. **Structured Responder Guidance:** Provides ward engineers and private tanker coordinators with actionable next steps (*"Verify supply interruption"*, *"Coordinate tanker support"*, *"Escalate to ward office"*).
4. **Community-Reported Recovery:** 2 independent `restored` or `available` reports automatically transition the incident into recovery state without false claims of official municipal resolution.
5. **Historical CGWB Data as Contextual Vulnerability:** 4,962 Central Ground Water Board records (1996–2020) across 115 stations provide background aquifer depth trends, protected by a strict **180-day stale-data guardrail** that refuses to generate speculative future tanker bookings on old records.

---

## 🏛️ System Architecture

```
                               ┌─────────────────────────────────────────────────────────────┐
                               │                    LIVE RESIDENT SIGNALS                    │
                               │  • PWA 1-Click Tap Status (Available / Low / Dry / Restored)│
                               │  • Anonymous Client Hashing (Zero-Knowledge Device ID)      │
                               │  • 30-Minute Deduplication & Rate Limiting                  │
                               └──────────────────────────────┬──────────────────────────────┘
                                                              │
                                                              ▼
                               ┌─────────────────────────────────────────────────────────────┐
                               │               90-MINUTE CLUSTERING ENGINE                   │
                               │  • 3+ Independent Dry Reports -> ACTIVE COMMUNITY OUTAGE    │
                               │  • 2+ Restored Reports -> COMMUNITY RECOVERY                │
                               │  • Automated Incident Timeline & Confidence Scoring         │
                               └──────────────────────────────┬──────────────────────────────┘
                                                              │
                    ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
                    ▼                                                                                   ▼
    ┌───────────────────────────────┐                                                   ┌───────────────────────────────┐
    │     AWS CLOUD (CDK Stack)     │                                                   │       LOCAL DEMO STACK        │
    │ • API Gateway HTTP API        │                                                   │ • FastAPI Backend (Port 8000) │
    │ • DynamoDB (water_reports)    │                                                   │ • SQLite WAL Persistence      │
    │ • DynamoDB (community_alerts) │                                                   │ • React 19 + Vite (Port 5173) │
    │ • DynamoDB (subscriptions)    │                                                   │ • Live 8-Second Status Poll   │
    │ • EventBridge 6h Cron         │                                                   │ • Historical CGWB Guardrail   │
    │ • Amazon SNS Sandbox Dispatch │                                                   │ • What-If Scenario Simulator  │
    └───────────────────────────────┘                                                   └───────────────────────────────┘
```

> **Cloud Notice:** Local demonstration runs with SQLite. AWS architecture is codified with AWS CDK in `infra/` but **not deployed in this submission**. No live SMS messages or physical sensors are claimed.

---

## 🚀 Quickstart: Running Locally on Windows

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- FFmpeg (for video pipeline)

### 1. Start the FastAPI Backend
```powershell
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API docs available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Start the React Frontend
In a separate terminal:
```powershell
cd web
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
Open your browser at: [http://localhost:5173](http://localhost:5173)

---

## 📡 REST API Reference

### JalaNetra Pulse Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/pulse/summary` | Real-time community water-outage summary across all 5 Mangaluru wards. |
| `GET` | `/api/pulse/wards/{ward_id}` | Real-time pulse, 90-minute report breakdown, and incident timeline for a ward. |
| `POST` | `/api/pulse/reports` | Submit a current water status report. Enforces 30m deduplication & triggers clustering. |
| `GET` | `/api/pulse/alerts` | List all open community outage and recovery alerts. |
| `GET` | `/api/pulse/alerts/{alert_id}` | Detailed incident timeline and contributing report records. |
| `POST` | `/api/pulse/alerts/{id}/resolve-report` | Record a community restoration report for an active outage. |
| `POST` | `/api/pulse/scenario/seed-outage` | Demo scenario: Seeds 3 independent `dry` reports, triggering an instant active alert. |
| `POST` | `/api/pulse/scenario/seed-recovery` | Demo scenario: Seeds 2 independent `restored` reports, triggering recovery status. |
| `POST` | `/api/pulse/scenario/reset` | Clears all simulated demo reports. Real user reports remain unperturbed. |
| `POST` | `/api/pulse/sms/test` | Transactional SMS dispatch: Preview mode by default; verified personal test if enabled. |

### Historical CGWB & Guardrail Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/wards` | List wards with historical CGWB baseline context and stale-data guardrail flags. |
| `GET` | `/api/wards/{ward_id}` | Detailed historical depth time-series and IMD precipitation baselines. |
| `GET` | `/api/forecast` | Aquifer depletion forecast, explicitly constrained by `forecast_status: "historical_context_only"`. |

---

## 📲 Safe SMS Dispatch Behavior

`POST /api/pulse/sms/test` is **strictly safe by default**:
- **Environment Configuration:**
  - `SMS_LIVE_MODE=false` (Default)
  - `AWS_REGION=ap-south-1`
  - `SMS_TEST_PHONE=<optional verified personal phone>`
- **Preview Mode (Default):**
  - Returns `sent: false`, `mode: "preview"`, `reason: "SMS demo mode enabled. No message was sent."`, and `destination_masked: "+XX-XXXXX-XXXXX"`.
  - Zero AWS credentials called; zero network calls made.
- **Verified Sandbox Send (Explicit Opt-in):**
  - Only active when `SMS_LIVE_MODE=true`, `confirm_test_send=true`, and `SMS_TEST_PHONE` is configured.
  - Sends via AWS SNS `boto3.publish` **ONLY to the verified test phone number**.
  - **Never** sends SMS to crowdsourced or user-submitted numbers.
  - Transparently discloses that public mass delivery in India requires municipal DLT registration.

---

## 🧪 Testing

Run the full automated test suite (all 62 tests passing):
```powershell
python -m pytest tests
```

Build the production frontend bundle:
```powershell
cd web && npm run build
```

---

## ⚖️ License & Hackathon Attribution
Built for the **WeMakeDevs x AWS Environmental Hacks** (Heat & Water Track).  
Groundwater baselines derived from **Central Ground Water Board (CGWB)** open data.
