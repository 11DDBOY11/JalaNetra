# JalaNetra Pulse Demo Script & Walkthrough

## Primary Product Positioning
**“Real-time community water-outage detection and neighborhood response for Mangaluru.”**

### Mandatory Disclaimer
> **“Community-reported issue — not an official municipal confirmation.”**

### Primary Elevator Pitch
> “JalaNetra Pulse detects neighborhood water outages in real time from independent household reports. When multiple residents in the same ward report no water within 90 minutes, it raises a transparent community alert, notifies subscribed residents, and gives ward responders a structured incident timeline. Historical CGWB groundwater data provides vulnerability context, but current action is always driven by current community signals.”

---

## 2-Minute Judging Walkthrough Flow

### Step 1: Open JalaNetra Pulse & Select Ward [00:00 - 00:15]
- **Visual:** Open browser to `http://localhost:5173`. Default view is the **Community Pulse** tab.
- **Action:** Select **Kodialbail** in the ward selector dropdown.
- **Display:** Show that currently there is **No Active Alert** (monitoring mode, 0 reports in last 90 minutes).
- **Narration:**
  > “Welcome to JalaNetra Pulse — real-time community water-outage detection and neighborhood response for Mangaluru.
  > Instead of predicting present-day household shortages from stale historical spreadsheets, JalaNetra Pulse drives immediate action from current community signals. In Kodialbail right now, monitoring is calm with zero recent outage reports.”

---

### Step 2: Resident Reporting & 90-Minute Outage Clustering [00:15 - 00:45]
- **Visual:** Click **“What-if Scenarios”** or the Quick Demo seed button: **“Seed 3 independent No Water reports”**.
- **Action:** Click the button. Note badge: *“Demo scenario — creates simulated community reports only.”*
- **Display:** Instantly switch to the **Community Pulse** tab.
  - In-app notification bell counter jumps to **1 active alert**.
  - Top alert banner turns bold red:
    **“COMMUNITY WATER ALERT — Kodialbail: 3 independent households reported no water in the last 90 minutes.”**
  - Disclaimer prominently displayed:
    *“Community-reported issue — not an official municipal confirmation.”*
  - Ward Pulse card shows: 3 dry reports, 100% dry distribution, High Severity, and incident timeline showing the reports.
- **Narration:**
  > “When 3 or more independent households in the same ward report 'No water' within a 90-minute window, JalaNetra Pulse instantly activates a Community Water Alert.
  > Notice the mandatory safeguard: it is transparently labeled as a 'Community-reported issue — not an official municipal confirmation.' A single resident cannot spam the system thanks to a 30-minute deduplication hash.”

---

### Step 3: Ward Responder Dashboard & Actionable Next Steps [00:45 - 01:10]
- **Visual:** Switch to the **Ward Responder** tab.
- **Display:**
  - Active outage cluster for Kodialbail: Severity **Critical**, Confidence **High**, First/Latest report timestamps.
  - Actionable response checklist:
    - [ ] Verify supply interruption
    - [ ] Inspect borewell / pump
    - [ ] Coordinate tanker support
    - [ ] Escalate to ward office
- **Narration:**
  > “Ward representatives and neighborhood groups get an operational incident view. Instead of fielding scattered WhatsApp complaints, responders see the verified report cluster, confidence metrics, and a structured response checklist: verify the municipal pipeline, inspect community borewells, coordinate emergency tanker supplies, and escalate.”

---

### Step 4: Transactional SMS Notification Preview & Sandbox Safety [01:10 - 01:30]
- **Visual:** Switch to the **What-if Scenarios & SMS** tab.
- **Display:** The **SMS Alert Dispatcher (AWS SNS Integration)** panel.
  - Click **“Preview Alert SMS Payload”**.
  - Show formatted payload:
    `[JalaNetra Pulse ALERT] Kodialbail: 3 households reported dry taps in 90 min. Ref: #alert-... Community-reported, non-official.`
  - Mode indicates: `preview (Safe Default — SMS_LIVE_MODE=false)`.
  - Notice the locked live send button: *Requires `SMS_LIVE_MODE=true`, `confirm_test_send=true`, and verified personal sandbox phone.*
- **Narration:**
  > “For offline reach, JalaNetra integrates with Amazon SNS. By default, it operates safely in preview mode, outputting the exact transactional payload. Real cellular delivery is strictly restricted to verified sandbox numbers with explicit opt-in confirmation, preventing unsolicited broadcast in compliance with Indian telecom regulations.”

---

### Step 5: Historical CGWB Groundwater as Contextual Vulnerability [01:30 - 01:45]
- **Visual:** Switch to the **Historical Context** tab.
- **Display:**
  - Show the 4,962 CGWB well observation records across Dakshina Kannada.
  - Point out the **180-Day Stale-Data Guardrail**:
    *“Historical Context Only — Latest observation is 2020-11-30. Government records are not live monitoring; current forecast dates are suppressed.”*
- **Narration:**
  > “What happened to the historical groundwater data? It is preserved here as a background vulnerability layer. Our 180-day stale-data guardrail blocks stale 2020 CGWB records from fabricating current tanker dates, while highlighting which wards have vulnerable deep water tables when municipal supply trips.”

---

### Step 6: Community Recovery Flow [01:45 - 02:00]
- **Visual:** In **What-if Scenarios**, click **“Seed 2 recovery reports (Water Restored)”**.
- **Display:** Return to **Community Pulse** tab.
  - Alert banner turns green/amber:
    **“COMMUNITY WATER ALERT — Kodialbail (Community-reported recovery)”**
  - Note: Shows recovery reported by residents without claiming official municipal resolution.
- **Narration:**
  > “Finally, when two independent households confirm 'Water restored' or 'Water available', the incident transitions to 'Community-reported recovery' — keeping neighbors informed until full supply stabilizes.
  > Real-time signals, honest data boundaries, and actionable community resilience. That is JalaNetra Pulse.”
