# JalaNetra Edge Sensor-Node Roadmap

> **DISCLAIMER:** Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.

## Overview
This document outlines the envisioned technical pathway for deploying physical well-depth telemetry nodes in Mangaluru as a future municipal scaling phase.

## Conceptual Deployment Architecture
1. **Physical Well Node:**
   - Low-power microcontroller (e.g. ESP32 / Nordic nRF9160 cellular IoT) or Linux SBC.
   - Non-contact ultrasonic transducer (e.g. MaxBotix / HC-SR04 waterproof) mounted above the open well water surface.
   - Solar panel (5W) with 18650 Li-ion battery buffer.
2. **Edge Processing & Greengrass Runtime:**
   - AWS IoT Greengrass v2 containerized component for edge filtering, local anomaly detection, and bandwidth throttling.
   - Telemetry batching and periodic MQTT publication over TLS.
3. **AWS Ingestion Pipeline:**
   - AWS IoT Core topic: `jalanetra/edge/{ward_id}/telemetry`
   - IoT Topic Rule routing payload to Amazon Kinesis Data Firehose -> Amazon S3 / DynamoDB `ward_state`.

## Hackathon Implementation Status
- **Current Demo Status:** Entirely simulated in software via `edge/simulator.py`.
- **Zero Physical Hardware Dependency:** Evaluators can inspect the pipeline end-to-end without needing IoT hardware, soldering, or specialized bench testing.
- **Audit Compliance:** Every telemetry frame carries `"simulated": true` and `"synthetic": true`.
