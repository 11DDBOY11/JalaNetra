# JalaNetra Pulse — UI Redesign Notes for Video Assets

## Overview
The frontend of **JalaNetra Pulse** has been redesigned from a dark-neon dashboard into a clean, light-themed, modern civic-tech public service application.

Per the instruction rule, **the existing submission video (`submission/video/jalanetra_demo.mp4`) has NOT been overwritten**.

---

## What Changed in the UI
1. **Light Interface by Default**:
   - Replaced dark navy/black background and glowing borders with a clean, light civic palette (`#F8FAFC` page background, `#FFFFFF` crisp white cards, `#E4E7EC` subtle borders).
   - Accents: Deep Navy (`#16324F`), Water Blue (`#2F80ED`), Teal (`#159E9C`).
2. **Typography & Iconography**:
   - Switched to restrained `Inter` font hierarchy.
   - Removed all emojis from buttons, navigation, and badges. Replaced with clean SVG line icons (`DropletIcon`, `CheckCircleIcon`, `AlertTriangleIcon`, `AlertCircleIcon`, etc.).
3. **Elimination of Hackathon & Technical Labels**:
   - Completely removed hackathon branding, "Heat & Water Track", "WeMakeDevs", "AWS Environmental Hacks", "FastAPI Live", "SQLite", and "CDK" from end-user screens.
   - Humanized microcopy:
     - *"Reported by local residents. Verification in progress."*
     - *"Groundwater history is shown for context. Current alerts are based on community reports."*
     - *"Message preview. Delivery is available only for verified test numbers."*
4. **Clean Navigation & Pages**:
   - **Pulse** (`pulse`): Neighbourhood water status, 1-click status reporting (Available, Low supply, No water), recent updates timeline, monitored ward list, and "How response works" 3-step section.
   - **Report water** (`report`): Dedicated resident update form with private support option and salted SHA-256 privacy notice.
   - **Response board** (`admin`): Operational incident queue for ward volunteers with interactive response checklist.
   - **Water context** (`historical`): Clean Recharts depth chart with CGWB metadata and 180-day freshness safeguard notice.
   - **About** (`about`): How it works and data/privacy transparency.
   - **Notification test** (`tools`): Accessible under `/tools` or via About link for testing message previews and simulation controls.

---

## Screenshots to Capture If Video Is Regenerated
If the submission video is regenerated in the future, the following screen captures should be updated using `capture_and_build_assets.py`:

| Asset File | Target Route / View | Key Visual Highlights |
| :--- | :--- | :--- |
| **`03_community_pulse.png`** | `http://localhost:5173/` (Pulse tab) | Clean light card layout, Kodialbail selected, normal conditions badge, 1-click report buttons with SVG icons. |
| **`04_active_outage_alert.png`** | `http://localhost:5173/` (after seeding 3 reports) | High-contrast red alert banner: *"Water supply issue reported in Kodialbail"*, 3 independent reports, verified timeline. |
| **`05_ward_responder_dashboard.png`** | `http://localhost:5173/?tab=admin` (Response board) | Active incident queue, confidence metrics, responder action checklist with checkable items. |
| **`06_sms_dispatcher_preview.png`** | `http://localhost:5173/?tab=tools` (Notification test) | Clean message preview card, masked destination `+91-XXXXX-1234`, safe preview note. |

---

## Instructions to Regenerate Video (Optional)
To capture the new light-theme screens and re-encode the MP4:
```powershell
# 1. Ensure backend and frontend are running
# Backend: python -m uvicorn backend.main:app --port 8000
# Frontend: cd web && npm run dev -- --port 5173

# 2. Capture updated screens
python submission/video/video_generation/capture_and_build_assets.py

# 3. Assemble video
python submission/video/video_generation/generate_demo_video.py
```
