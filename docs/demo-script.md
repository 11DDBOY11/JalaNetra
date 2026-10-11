# JalaNetra Hackathon Demo Script (60–90 Seconds)

## Video Recording / Live Presentation Walkthrough

### Part 1: The Paradox & The Core Outcome [00:00 - 00:20]
- **Visual:** Open browser to `http://localhost:5173`.
- **Narration:**
  > “India’s rainiest coast is running out of water. In Mangaluru, despite receiving over 3,800 mm of annual rainfall, laterite aquifers empty within weeks after the monsoon ceases. Households wake up to dry taps and must pay surge pricing for emergency water tankers.
  > JalaNetra provides an early warning system that tells households exactly which week to act: *'Water stress is likely in Kodialbail in approximately 3 weeks. Book a tanker by [Date].'*”

### Part 2: Data Honesty, Stale Guardrail & What-if Simulator [00:20 - 00:45]
- **Visual:** Point to the top banner: **“Hybrid mode: groundwater depth is derived from historical CGWB observations; rainfall and ward-level stress estimates include clearly labeled model/demo assumptions.”** Show the neutral slate card displaying **“Historical groundwater context — current forecast unavailable”**. Then click **“⚠️ Low supply”** or **“🚨 No water (Dry)”** in the **What-if Scenario Simulator**.
- **Narration:**
  > “We prioritize absolute data integrity: JalaNetra ingests 4,962 verified historical government well observations across 115 stations in Dakshina Kannada from CGWB quarterly records. Because these government records are historical, our strict Stale-Data Guardrail automatically flags them as 'historical_context' and suppresses false present-day booking dates.
  > To test household preparedness without fabricating environmental numbers, evaluators can use our What-if Scenario Simulator to simulate current supply conditions and preview precautionary tanker advisories.”

### Part 3: Transparent Heuristic & Citizen Ground Truth [00:45 - 01:05]
- **Visual:** Switch to **Depletion Forecast** tab showing the Recharts curve with the **Configurable demonstration water-stress threshold (16 m depth-below-ground-level)**. Then click **Citizen Sahayak**, submit a *"Dry / No Water"* report, and show it appearing instantly in the ground feed.
- **Narration:**
  > “Our model is an auditable, transparent heuristic using a configurable demonstration water-stress threshold of 16m bgl. It combines government baselines with citizen crowdsourcing: when a resident reports dry taps, the ward's alert urgency elevates immediately.”

### Part 4: Multilingual Alert Preview & Edge Roadmap [01:05 - 01:25]
- **Visual:** Click **Alert Dispatcher**, toggle English and Hindi to show the **Amazon Polly-compatible multilingual voice-alert script preview** (clearly labeled: *“Illustrative scenario preview — not triggered by current measurements”*). Then click **Simulated Edge Feed**.
- **Narration:**
  > “We preview bilingual SMS and Amazon Polly-compatible voice-alert scripts without sending unsolicited cellular messages. Finally, we showcase simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap, requiring zero physical hardware to evaluate today.”
