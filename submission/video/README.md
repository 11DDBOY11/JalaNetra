# JalaNetra Pulse Hackathon Submission Video

This directory contains the final autonomous demo video package for **JalaNetra Pulse** (*Real-Time Community Water-Outage Detection and Neighborhood Response for Mangaluru*), prepared for the **WeMakeDevs x AWS Environmental Hacks** hackathon (Heat & Water Track).

---

## Deliverables Summary

| File / Folder | Description |
| :--- | :--- |
| **`jalanetra_demo.mp4`** | **Final Hackathon Submission Video** (1080p Full HD, H.264/AAC, 156.0s / 2m 36s) featuring Microsoft Edge Neural Voice narration (`en-IN-NeerjaNeural`), synchronized lower-third subtitles, and smooth crossfades. |
| **`jalanetra_demo_script.md`** | Scene-by-scene demo script with exact timings, narration transcripts, visual storyboard, on-screen badges, and truthfulness guardrails. |
| **`assets/`** | Visual scene assets (`01_scene1_pulse_home.png` through `07_scene7_impact_closing.png`) captured live from localhost (`http://localhost:5173/`) and generated diagrams. |
| **`narration/`** | Includes master audio tracks (`neural_narration.wav`, `neural_narration.mp3`), synchronized subtitles (`neural_narration.srt`), and individual scene voice clips. |
| **`video_generation/`** | Autonomous generation pipeline: `generate_demo_video.py`, `synthesize_pulse_narration.py`, `capture_and_build_assets.py`, and `generation_log.txt`. |

---

## Video Specifications

- **Title:** JalaNetra Pulse — Community Water Outage Detection for Mangaluru
- **Video Path:** `submission/video/jalanetra_demo.mp4`
- **Resolution:** 1920 × 1080 (1080p Full HD @ 30.0 fps)
- **Video Codec:** H.264 / AVC (libx264, High Profile, YUV420p, CRF 19)
- **Audio Codec:** AAC (192 kbps, 44.1 kHz, mono)
- **Voice Engine:** Microsoft Edge Neural Text-to-Speech (via `edge-tts`)
- **Selected Voice:** `en-IN-NeerjaNeural` (Calm, articulate, natural Indian English)
- **Voice Settings:** Rate `-2%`, Pitch `+0Hz`
- **Subtitles:** Embedded high-contrast lower-third banners + standalone synchronized SRT (`submission/video/narration/neural_narration.srt`)
- **Total Duration:** 156.0 seconds (2 minutes 36 seconds — strictly within the 2:20 to 2:40 target, < 3:00)
- **File Size:** 6.82 MB (7,151,809 bytes)

---

## Mandatory 4 Focus Areas Visibly Shown

1. **About the Project:**
   Community water outage detection for Mangaluru. Resolves the acute crisis gap where residents experience dry taps due to pump trips or pipe cuts without knowing if it is a localized home issue or ward outage.
2. **Tech Stack and Architecture:**
   FastAPI, SQLite, React, TypeScript, and serverless AWS infrastructure defined with AWS CDK in `infra/`.
3. **How AWS is Used:**
   Amazon API Gateway, AWS Lambda, Amazon DynamoDB, Amazon EventBridge, Amazon SNS (in sandbox safety mode), Amazon S3, and AWS Amplify.
4. **Working Product Flow:**
   Household reporting (`Water available`, `Low supply`, `No water`) -> 90-minute clustering (3 independent reports) -> Active community alert -> Response board with action checklist -> Real CGWB historical groundwater context with 180-day freshness safeguard.

---

## Scene Storyboard & Schedule

| Scene | Time Window | Visual Asset | Focus & On-Screen Elements |
| :--- | :--- | :--- | :--- |
| **Scene 1: Problem & Project** | 0:00 – 0:18 (18.0s) | `01_scene1_pulse_home.png` | Clean light Pulse page; monitored neighbourhoods in Mangaluru. |
| **Scene 2: Community Reporting** | 0:18 – 0:38 (20.0s) | `02_scene2_report_water.png` | Report water interface; `Available`, `Low supply`, and `No water` (selected). |
| **Scene 3: Outage Detection** | 0:38 – 1:05 (27.0s) | `03_scene3_outage_detected.png` | Active incident banner for Kodialbail; honesty label: *"Simulated reports used for this recorded scenario."* |
| **Scene 4: Response Board** | 1:05 – 1:27 (22.0s) | `04_scene4_response_board.png` | Active incident queue, report count, timeline, action checklist, and recovery update button. |
| **Scene 5: Historical Water Context** | 1:27 – 1:46 (19.0s) | `05_scene5_water_context.png` | 4,962 CGWB records, 115 stations, Padil chart, and 180-day freshness safeguard disclosure. |
| **Scene 6A: AWS Architecture** | 1:46 – 2:04 (18.0s) | `06_scene6_aws_architecture.png` | AWS serverless pipeline codified with CDK. Footer: *"Local demo shown. AWS deployment architecture defined with CDK."* |
| **Scene 6B: Notification Preview** | 2:04 – 2:19 (15.0s) | `06b_scene6_notification_test.png` | Transactional SNS notification preview tool with masked recipient and sandbox safety. |
| **Scene 7: Impact & Closing** | 2:19 – 2:36 (17.0s) | `07_scene7_impact_closing.png` | Clean closing slide with current UI in background; Report early • Respond together • Build water-resilient communities. |

---

## Strict Honesty & Environmental Disclosures

1. **Simulated Scenario:** The 3 dry reports in Kodialbail are prominently disclosed with on-screen badge: *“Simulated reports used for this recorded scenario.”*
2. **Architecture Codified with CDK:** Disclosed with footer: *“Local demo shown. AWS deployment architecture defined with CDK.”*
3. **No Fabricated SMS:** Delivery is restricted to sandbox test numbers; no unsolicited public broadcasts are triggered.
4. **Historical vs Live Separation:** 4,962 Central Ground Water Board records are quarterly historical data and never presented as live tap availability.
