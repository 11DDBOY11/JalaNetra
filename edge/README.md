# JalaNetra Edge Module (Simulated)

> **Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.**

## Edge Roadmap & Future Architecture
In a potential future municipal deployment:
- Envisioned hardware target: Low-power microcontroller or single-board computer (e.g., ESP32 / Raspberry Pi) equipped with ultrasonic water level transceivers.
- Architecture: **AWS IoT Greengrass v2** component publishing to AWS IoT Core topic: `jalanetra/edge/{ward_id}/telemetry`.
- Current Status: **SIMULATED ONLY**. This repository provides an autonomous Python telemetry simulator to demonstrate ingestion schemas without physical hardware dependencies.

## Running the Edge Simulator Locally
Run the simulator to generate sample telemetry cycles:

```powershell
python edge/simulator.py --count 5 --interval 1.0
```

Sample output:
```
[INFO] [EDGE-SIMULATED] Starting JalaNetra Edge Sensor Simulator (SIMULATED MODE)
[INFO] [EDGE-SIMULATED] Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.
[INFO] [EDGE-SIMULATED] MQTT Publish -> topic: 'jalanetra/edge/dk-kodialbail/telemetry' | depth: 13.82 m | sim: True
```
