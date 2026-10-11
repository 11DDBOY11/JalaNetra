"""
JalaNetra Edge Telemetry Simulator
Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap.
No physical edge device was used in this demo.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import time
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [EDGE-SIMULATED] %(message)s"
)
logger = logging.getLogger("jalanetra.edge")

WARDS = [
    {"ward_id": "dk-kodialbail", "name": "Kodialbail", "base_depth_m": 13.8},
    {"ward_id": "dk-kankanady", "name": "Kankanady", "base_depth_m": 12.1},
    {"ward_id": "dk-kadri", "name": "Kadri", "base_depth_m": 8.3},
    {"ward_id": "dk-surathkal", "name": "Surathkal", "base_depth_m": 14.2},
    {"ward_id": "dk-moodbidri", "name": "Moodbidri", "base_depth_m": 11.4},
]


def generate_reading(ward: dict) -> dict:
    """Generate a single simulated sensor reading for a ward."""
    noise = random.gauss(0, 0.04)
    depth = round(ward["base_depth_m"] + noise, 3)
    battery_v = round(3.7 + random.uniform(-0.1, 0.1), 2)
    signal_rssi = random.randint(-75, -55)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ward_id": ward["ward_id"],
        "ward_name": ward["name"],
        "sensor_type": "Ultrasonic_Well_Depth_HCSR04_Simulated",
        "groundwater_depth_m": depth,
        "battery_voltage_v": battery_v,
        "signal_rssi_dbm": signal_rssi,
        "device_id": f"greengrass-edge-{ward['ward_id']}",
        "simulated": True,
        "synthetic": True,
        "data_mode": "SIMULATED_EDGE_TELEMETRY",
        "notice": "Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo."
    }


def run_simulator(interval_sec: float = 2.0, count: int = 10, ward_id: str | None = None) -> list[dict]:
    """Run simulated telemetry loop and print/yield readings."""
    logger.info("Starting JalaNetra Edge Sensor Simulator (SIMULATED MODE)")
    logger.info("Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.")

    selected_wards = [w for w in WARDS if w["ward_id"] == ward_id] if ward_id else WARDS
    readings = []

    for i in range(count):
        ward = random.choice(selected_wards)
        reading = generate_reading(ward)
        readings.append(reading)
        logger.info(
            "MQTT Publish -> topic: 'jalanetra/edge/%s/telemetry' | depth: %.2f m | sim: %s",
            reading["ward_id"],
            reading["groundwater_depth_m"],
            reading["simulated"]
        )
        if i < count - 1:
            time.sleep(interval_sec)

    logger.info("Simulator completed %d cycles successfully.", count)
    return readings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JalaNetra Simulated Edge Telemetry")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between readings")
    parser.add_argument("--count", type=int, default=5, help="Number of telemetry cycles")
    parser.add_argument("--ward", type=str, default=None, help="Filter to specific ward_id")
    args = parser.parse_args()

    run_simulator(interval_sec=args.interval, count=args.count, ward_id=args.ward)
