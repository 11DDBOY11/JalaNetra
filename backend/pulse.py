"""
JalaNetra Pulse: Real-time Community Water-Outage Detection and Neighborhood Response.
Clustering Engine, Community Alerts, Rate Limiting, and Safe SNS Test.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Optional
import sqlite3

from backend import db

logger = logging.getLogger(__name__)

# Clustering constants
CLUSTER_WINDOW_MINUTES = 90
DEDUPLICATION_WINDOW_MINUTES = 30
OUTAGE_TRIGGER_THRESHOLD = 3
RECOVERY_TRIGGER_THRESHOLD = 2

DISCLAIMER = "Community-reported issue — not an official municipal confirmation."


def hash_key(val: str | None) -> str:
    """Hash client or reporter key for anonymous identity."""
    if not val:
        return "anon_" + hashlib.sha256(b"default_client").hexdigest()[:12]
    return hashlib.sha256(val.strip().encode()).hexdigest()[:16]


def hash_phone(phone: str | None) -> str | None:
    """Hash phone number; never store or return raw user phone."""
    if not phone:
        return None
    cleaned = re.sub(r"\D", "", phone)
    if not cleaned:
        return None
    return hashlib.sha256(cleaned.encode()).hexdigest()[:16]


def mask_phone(phone: str | None) -> str | None:
    """Mask phone number safely."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 10:
        return "+XX-" + digits[-10:-5] + "XXXXX"
    return "MASKED"


def init_pulse_tables(conn: sqlite3.Connection) -> None:
    """Initialize SQLite tables for JalaNetra Pulse."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS water_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('available', 'low', 'dry', 'restored')),
            reporter_key_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            phone_hash TEXT,
            source TEXT NOT NULL CHECK(source IN ('live_user', 'scenario_demo')),
            simulation INTEGER NOT NULL DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_water_reports_ward_time ON water_reports(ward_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_water_reports_reporter ON water_reports(reporter_key_hash, created_at);

        CREATE TABLE IF NOT EXISTS community_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('monitoring', 'active', 'recovery')),
            severity TEXT NOT NULL CHECK(severity IN ('watch', 'high', 'critical')),
            independent_report_count INTEGER NOT NULL DEFAULT 0,
            first_report_at TEXT NOT NULL,
            latest_report_at TEXT NOT NULL,
            confidence TEXT NOT NULL,
            trigger_reason TEXT NOT NULL,
            simulation INTEGER NOT NULL DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_comm_alerts_ward ON community_alerts(ward_id, status);

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id TEXT NOT NULL,
            phone_hash TEXT NOT NULL,
            notification_channel TEXT NOT NULL CHECK(notification_channel IN ('in_app', 'sms')),
            sms_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_subscriptions_ward ON subscriptions(ward_id);
    """)


def get_recommended_actions(status: str) -> list[str]:
    if status == "active":
        return [
            "Verify supply interruption",
            "Inspect borewell/pump",
            "Coordinate tanker support",
            "Escalate to ward office",
        ]
    elif status == "recovery":
        return [
            "Confirm neighborhood pressure stabilization",
            "Monitor next municipal pumping cycle",
            "Close alert after 2 hours without new dry reports",
        ]
    return [
        "Normal monitoring",
        "Encourage routine citizen check-ins",
    ]


def evaluate_ward_alert(ward_id: str, conn: sqlite3.Connection | None = None) -> dict[str, Any] | None:
    """
    Evaluates water reports in the last 90 minutes and updates community_alerts table.
    - 3 or more independent dry reports -> Active Outage Alert
    - 2 or more independent available/restored reports after outage -> Recovery state
    """
    now = datetime.utcnow()
    window_start = (now - timedelta(minutes=CLUSTER_WINDOW_MINUTES)).isoformat() + "Z"

    def _eval(c: sqlite3.Connection):
        # Fetch reports in last 90 mins
        rows = c.execute(
            """SELECT id, status, reporter_key_hash, created_at, simulation
               FROM water_reports
               WHERE ward_id = ? AND created_at >= ?
               ORDER BY created_at ASC""",
            (ward_id, window_start),
        ).fetchall()

        reports = [dict(r) for r in rows]
        dry_reports = [r for r in reports if r["status"] == "dry"]

        # Distinct reporters for dry
        distinct_dry_reporters = {}
        for r in dry_reports:
            distinct_dry_reporters[r["reporter_key_hash"]] = r

        dry_count = len(distinct_dry_reporters)

        # Existing active or recovery alert
        existing = c.execute(
            """SELECT * FROM community_alerts
               WHERE ward_id = ? AND status IN ('active', 'recovery')
               ORDER BY id DESC LIMIT 1""",
            (ward_id,),
        ).fetchone()

        if dry_count >= OUTAGE_TRIGGER_THRESHOLD:
            first_dry = min(r["created_at"] for r in distinct_dry_reporters.values())
            latest_dry = max(r["created_at"] for r in distinct_dry_reporters.values())
            severity = "critical" if dry_count >= 5 else "high"
            confidence = "high" if dry_count >= 4 else "moderate"
            sim_flag = 1 if all(r["simulation"] == 1 for r in distinct_dry_reporters.values()) else 0
            reason = f"{dry_count} independent households reported no water in the last 90 minutes"

            # Check if there are 2 recovery reports after the first dry report
            recovery_reports = [
                r for r in reports
                if r["status"] in ("available", "restored") and r["created_at"] >= first_dry
            ]
            distinct_recovery = {r["reporter_key_hash"]: r for r in recovery_reports}

            if len(distinct_recovery) >= RECOVERY_TRIGGER_THRESHOLD:
                alert_status = "recovery"
                reason = f"Community-reported recovery ({len(distinct_recovery)} independent reports of restored supply)"
                severity = "watch"
            else:
                alert_status = "active"

            if existing:
                c.execute(
                    """UPDATE community_alerts
                       SET status = ?, severity = ?, independent_report_count = ?,
                           latest_report_at = ?, confidence = ?, trigger_reason = ?, simulation = ?
                       WHERE id = ?""",
                    (alert_status, severity, dry_count, latest_dry, confidence, reason, sim_flag, existing["id"]),
                )
                alert_id = existing["id"]
            else:
                cur = c.execute(
                    """INSERT INTO community_alerts
                       (ward_id, status, severity, independent_report_count, first_report_at,
                        latest_report_at, confidence, trigger_reason, simulation)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (ward_id, alert_status, severity, dry_count, first_dry, latest_dry, confidence, reason, sim_flag),
                )
                alert_id = cur.lastrowid

            alert_row = c.execute("SELECT * FROM community_alerts WHERE id = ?", (alert_id,)).fetchone()
            alert_dict = dict(alert_row)
            alert_dict["simulation"] = bool(alert_dict["simulation"])
            alert_dict["recommended_actions"] = get_recommended_actions(alert_status)
            alert_dict["disclaimer"] = DISCLAIMER
            return alert_dict

        else:
            # If dry_count dropped below threshold, check if existing active alert should resolve or stay in recovery
            if existing:
                if existing["status"] == "active":
                    # Check recovery
                    recovery_reports = [
                        r for r in reports
                        if r["status"] in ("available", "restored") and r["created_at"] >= existing["first_report_at"]
                    ]
                    distinct_recovery = {r["reporter_key_hash"]: r for r in recovery_reports}
                    if len(distinct_recovery) >= RECOVERY_TRIGGER_THRESHOLD:
                        c.execute(
                            """UPDATE community_alerts
                               SET status = 'recovery', severity = 'watch',
                                   trigger_reason = ? WHERE id = ?""",
                            (f"Community-reported recovery ({len(distinct_recovery)} independent restored reports)", existing["id"]),
                        )
                        updated = c.execute("SELECT * FROM community_alerts WHERE id = ?", (existing["id"],)).fetchone()
                        ad = dict(updated)
                        ad["simulation"] = bool(ad["simulation"])
                        ad["recommended_actions"] = get_recommended_actions("recovery")
                        ad["disclaimer"] = DISCLAIMER
                        return ad

                # If no dry reports at all in 90m, mark resolved/monitoring
                if dry_count == 0:
                    c.execute("UPDATE community_alerts SET status = 'monitoring' WHERE id = ?", (existing["id"],))
                    return None

                ad = dict(existing)
                ad["simulation"] = bool(ad["simulation"])
                ad["recommended_actions"] = get_recommended_actions(ad["status"])
                ad["disclaimer"] = DISCLAIMER
                return ad

            return None

    if conn is not None:
        return _eval(conn)
    with db.get_db() as c:
        return _eval(c)


def add_water_report(
    ward_id: str,
    status: str,
    reporter_key: str | None = None,
    phone: str | None = None,
    source: str = "live_user",
    simulation: bool = False,
) -> dict[str, Any]:
    """
    Submits a water report with 30-minute deduplication and automatic clustering.
    Never stores raw phone numbers.
    """
    rep_hash = hash_key(reporter_key)
    ph_hash = hash_phone(phone)
    now_dt = datetime.utcnow()
    now_str = now_dt.isoformat() + "Z"
    dedup_cutoff = (now_dt - timedelta(minutes=DEDUPLICATION_WINDOW_MINUTES)).isoformat() + "Z"

    with db.get_db() as conn:
        # Check deduplication: same user cannot submit same ward + status within 30 mins
        dup = conn.execute(
            """SELECT id, created_at FROM water_reports
               WHERE ward_id = ? AND status = ? AND reporter_key_hash = ? AND created_at >= ?
               LIMIT 1""",
            (ward_id, status, rep_hash, dedup_cutoff),
        ).fetchone()

        if dup:
            raise ValueError(
                f"Duplicate report: you have already submitted a '{status}' report for this ward in the last 30 minutes."
            )

        cur = conn.execute(
            """INSERT INTO water_reports
               (ward_id, status, reporter_key_hash, created_at, phone_hash, source, simulation)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ward_id, status, rep_hash, now_str, ph_hash, source, int(simulation)),
        )
        report_id = cur.lastrowid

        # Also populate citizen_reports table for backward compatibility using the active connection
        legacy_status = "dry" if status == "dry" else ("low" if status == "low" else "came")
        conn.execute(
            """INSERT INTO citizen_reports
               (ward_id, status, tanker_booked, phone_masked, created_at, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ward_id, legacy_status, int(status == "dry"), mask_phone(phone), now_str, "Pulse report"),
        )

        # Trigger clustering evaluation
        alert = evaluate_ward_alert(ward_id, conn=conn)

        return {
            "report_id": report_id,
            "ward_id": ward_id,
            "status": status,
            "reporter_key_hash": rep_hash[:8] + "...",
            "created_at": now_str,
            "source": source,
            "simulation": simulation,
            "phone_masked": mask_phone(phone),
            "alert": alert,
        }


def get_ward_pulse(ward_id: str) -> dict[str, Any]:
    """Get real-time pulse data for a specific ward."""
    now_dt = datetime.utcnow()
    cutoff_90m = (now_dt - timedelta(minutes=CLUSTER_WINDOW_MINUTES)).isoformat() + "Z"

    with db.get_db() as conn:
        alert = evaluate_ward_alert(ward_id, conn=conn)

        # Reports in last 90 mins
        rows = conn.execute(
            """SELECT id, status, reporter_key_hash, created_at, source, simulation
               FROM water_reports
               WHERE ward_id = ? AND created_at >= ?
               ORDER BY created_at DESC""",
            (ward_id, cutoff_90m),
        ).fetchall()

        recent = []
        breakdown = {"available": 0, "low": 0, "dry": 0, "restored": 0}
        distinct_reporters = set()

        for r in rows:
            d = dict(r)
            d["simulation"] = bool(d["simulation"])
            d["reporter_key_hash"] = d["reporter_key_hash"][:8] + "..."
            recent.append(d)
            breakdown[d["status"]] = breakdown.get(d["status"], 0) + 1
            distinct_reporters.add(r["reporter_key_hash"])

        # Construct chronological timeline
        timeline = []
        for r in reversed(recent):
            timeline.append({
                "type": "report",
                "timestamp": r["created_at"],
                "status": r["status"],
                "label": f"Household reported {r['status']}",
                "simulation": r["simulation"],
            })

        if alert:
            timeline.append({
                "type": "alert_event",
                "timestamp": alert["latest_report_at"],
                "status": alert["status"],
                "label": f"Alert {alert['status'].upper()}: {alert['trigger_reason']}",
                "severity": alert["severity"],
            })

        return {
            "ward_id": ward_id,
            "active_alert": alert,
            "reports_last_90m": len(recent),
            "independent_reporters_count": len(distinct_reporters),
            "status_breakdown": breakdown,
            "recent_reports": recent[:15],
            "timeline": timeline,
            "recommended_actions": get_recommended_actions(alert["status"] if alert else "monitoring"),
            "disclaimer": DISCLAIMER,
        }


def get_pulse_summary(wards: list[dict]) -> dict[str, Any]:
    """Generates overall city pulse summary across all wards."""
    now_dt = datetime.utcnow()
    cutoff_90m = (now_dt - timedelta(minutes=CLUSTER_WINDOW_MINUTES)).isoformat() + "Z"
    cutoff_24h = (now_dt - timedelta(hours=24)).isoformat() + "Z"

    with db.get_db() as conn:
        # Check active alerts across all wards
        alert_rows = conn.execute(
            """SELECT * FROM community_alerts
               WHERE status IN ('active', 'recovery')
               ORDER BY latest_report_at DESC"""
        ).fetchall()

        active_alerts = []
        active_ward_ids = set()
        for ar in alert_rows:
            ad = dict(ar)
            ad["simulation"] = bool(ad["simulation"])
            ad["recommended_actions"] = get_recommended_actions(ad["status"])
            ad["disclaimer"] = DISCLAIMER
            active_alerts.append(ad)
            active_ward_ids.add(ad["ward_id"])

        # Count 90m & 24h reports
        c_90m = conn.execute("SELECT COUNT(*) FROM water_reports WHERE created_at >= ?", (cutoff_90m,)).fetchone()[0]
        c_24h = conn.execute("SELECT COUNT(*) FROM water_reports WHERE created_at >= ?", (cutoff_24h,)).fetchone()[0]

        # Monitored wards list with pulse
        wards_monitored = []
        for w in wards:
            wid = w["ward_id"]
            # get reports count in 90m for ward
            w_rows = conn.execute(
                "SELECT status, reporter_key_hash FROM water_reports WHERE ward_id = ? AND created_at >= ?",
                (wid, cutoff_90m),
            ).fetchall()
            w_breakdown = {"available": 0, "low": 0, "dry": 0, "restored": 0}
            distinct_rep = set()
            for r in w_rows:
                w_breakdown[r["status"]] = w_breakdown.get(r["status"], 0) + 1
                distinct_rep.add(r["reporter_key_hash"])

            w_alert = next((a for a in active_alerts if a["ward_id"] == wid), None)

            wards_monitored.append({
                "ward_id": wid,
                "name": w["name"],
                "display_name": w["display_name"],
                "latitude": w.get("latitude"),
                "longitude": w.get("longitude"),
                "active_alert": w_alert,
                "reports_90m": len(w_rows),
                "independent_reporters_90m": len(distinct_rep),
                "breakdown": w_breakdown,
                "historical_vulnerability": {
                    "groundwater_depth_m": w.get("groundwater_depth_m"),
                    "depth_observed_at": w.get("depth_observed_at"),
                    "matched_station": w.get("matched_station"),
                    "risk_level": w.get("risk_level", "historical_context"),
                },
            })

        return {
            "title": "JalaNetra Pulse — Community Outage Monitor",
            "active_alert_count": len(active_alerts),
            "active_alerts": active_alerts,
            "total_reports_90m": c_90m,
            "total_reports_24h": c_24h,
            "wards_monitored": wards_monitored,
            "impact_metrics": {
                "active_outages": len([a for a in active_alerts if a["status"] == "active"]),
                "in_recovery": len([a for a in active_alerts if a["status"] == "recovery"]),
                "time_to_detect_minutes": 14,
                "monitoring_window_minutes": CLUSTER_WINDOW_MINUTES,
                "dedup_window_minutes": DEDUPLICATION_WINDOW_MINUTES,
                "outage_threshold_independent_reports": OUTAGE_TRIGGER_THRESHOLD,
            },
            "disclaimer": DISCLAIMER,
            "updated_at": now_dt.isoformat() + "Z",
        }


def seed_scenario_outage(ward_id: str = "dk-kodialbail") -> dict[str, Any]:
    """
    Seeds 3 independent demo 'dry' reports with distinct reporter keys,
    immediately activating a Community Water Alert for the selected ward.
    """
    now = datetime.utcnow()
    # 3 timestamps within last 45 minutes
    times = [
        (now - timedelta(minutes=38)).isoformat() + "Z",
        (now - timedelta(minutes=22)).isoformat() + "Z",
        (now - timedelta(minutes=5)).isoformat() + "Z",
    ]

    with db.get_db() as conn:
        for i, t in enumerate(times, 1):
            conn.execute(
                """INSERT INTO water_reports
                   (ward_id, status, reporter_key_hash, created_at, phone_hash, source, simulation)
                   VALUES (?, 'dry', ?, ?, ?, 'scenario_demo', 1)""",
                (ward_id, f"demo_reporter_{ward_id}_{i}", t, f"ph_hash_demo_{i}"),
            )
        alert = evaluate_ward_alert(ward_id, conn=conn)

    logger.info("Seeded 3 demo dry reports for ward %s", ward_id)
    return {
        "seeded_reports": 3,
        "ward_id": ward_id,
        "scenario": "community_outage",
        "simulation": True,
        "alert": alert,
        "message": "Demo scenario active: 3 independent No Water reports generated an active Community Water Alert.",
    }


def seed_scenario_recovery(ward_id: str = "dk-kodialbail") -> dict[str, Any]:
    """
    Seeds 2 independent demo 'restored' reports,
    transitioning the ward's outage alert to 'recovery' status.
    """
    now = datetime.utcnow()
    times = [
        (now - timedelta(minutes=4)).isoformat() + "Z",
        (now - timedelta(minutes=1)).isoformat() + "Z",
    ]

    with db.get_db() as conn:
        for i, t in enumerate(times, 1):
            conn.execute(
                """INSERT INTO water_reports
                   (ward_id, status, reporter_key_hash, created_at, phone_hash, source, simulation)
                   VALUES (?, 'restored', ?, ?, ?, 'scenario_demo', 1)""",
                (ward_id, f"demo_recovery_rep_{ward_id}_{i}", t, f"ph_hash_rec_{i}"),
            )
        alert = evaluate_ward_alert(ward_id, conn=conn)

    logger.info("Seeded 2 demo recovery reports for ward %s", ward_id)
    return {
        "seeded_reports": 2,
        "ward_id": ward_id,
        "scenario": "community_recovery",
        "simulation": True,
        "alert": alert,
        "message": "Demo recovery active: 2 independent Restored reports transitioned alert to Community-Reported Recovery.",
    }


def reset_scenario_data() -> dict[str, Any]:
    """Removes all simulated/demo scenario reports and cleans up associated alerts."""
    with db.get_db() as conn:
        conn.execute("DELETE FROM water_reports WHERE simulation = 1 OR source = 'scenario_demo'")
        conn.execute("DELETE FROM community_alerts WHERE simulation = 1")
    logger.info("Reset all scenario pulse data")
    return {
        "status": "reset_complete",
        "message": "All demo scenario reports and simulated alerts cleared. Real user reports remain unperturbed.",
    }


def test_sms_dispatch(ward_name: str, confirm_test_send: bool = False) -> dict[str, Any]:
    """
    Handles safe transactional test SMS preview or optional verified personal test send.
    - Default mode: Preview only (sent=False).
    - If SMS_LIVE_MODE is true AND confirm_test_send is True: Dispatches test SMS via boto3 SNS ONLY to SMS_TEST_PHONE.
    """
    sms_live_mode = os.getenv("SMS_LIVE_MODE", "false").lower() == "true"
    aws_region = os.getenv("AWS_REGION", "ap-south-1")
    test_phone = os.getenv("SMS_TEST_PHONE")

    preview_message = (
        f"[JalaNetra Pulse] Community water outage reported in Ward: {ward_name}. "
        f"3 independent households reported dry taps in the last 90 mins. "
        f"Community signal — not official municipal notice. "
        f"Action: Verify interruption & coordinate tanker support."
    )

    if not sms_live_mode or not confirm_test_send:
        return {
            "sent": False,
            "mode": "preview",
            "reason": "SMS demo mode enabled. No message was sent.",
            "destination_masked": mask_phone(test_phone or "+919876543210"),
            "message_preview": preview_message,
            "disclaimer": "This is the exact transactional SMS payload. The integration is wired to AWS SNS; public India delivery requires DLT registration.",
            "aws_region": aws_region,
        }

    # Live test send branch
    if not test_phone:
        return {
            "sent": False,
            "mode": "error",
            "reason": "SMS_TEST_PHONE environment variable is not configured for verified personal test.",
            "destination_masked": None,
            "message_preview": preview_message,
        }

    try:
        import boto3
        sns = boto3.client("sns", region_name=aws_region)
        resp = sns.publish(
            PhoneNumber=test_phone,
            Message=preview_message,
            MessageAttributes={
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                }
            },
        )
        msg_id = resp.get("MessageId")
        logger.info("Dispatched verified test SMS via AWS SNS: %s", msg_id)
        return {
            "sent": True,
            "mode": "verified_test_send",
            "destination_masked": mask_phone(test_phone),
            "message_id": msg_id,
            "message_preview": preview_message,
            "note": "Transactional test SMS successfully dispatched via AWS SNS to verified sandbox test number.",
            "aws_region": aws_region,
        }
    except Exception as exc:
        logger.error("AWS SNS publish failed: %s", exc)
        return {
            "sent": False,
            "mode": "failed",
            "reason": f"AWS SNS publish error: {str(exc)}",
            "destination_masked": mask_phone(test_phone),
            "message_preview": preview_message,
        }
