"""
JalaNetra Database Layer — SQLite
Uses SQLite for local demo persistence.
No DynamoDB required locally; this is a local-first demo.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# SQLite DB file location
DB_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "demo"
DB_PATH = DB_DIR / "jalanetra.db"


def _mask_phone(phone: str | None) -> str | None:
    """Mask phone number: +91 98765 XXXXX → +91-987XX-XXXXX."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 10:
        return "+XX-" + digits[-10:-5] + "XXXXX"
    return "MASKED"


@contextmanager
def get_db():
    """Context manager for SQLite connection."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS citizen_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ward_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('came', 'low', 'dry')),
                tanker_booked INTEGER NOT NULL DEFAULT 0,
                phone_masked TEXT,
                created_at TEXT NOT NULL,
                note TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_reports_ward ON citizen_reports(ward_id);
            CREATE INDEX IF NOT EXISTS idx_reports_status ON citizen_reports(status);

            CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_masked TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en-IN',
                ward_ids TEXT NOT NULL,
                created_at TEXT NOT NULL,
                demo_only INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS ward_state_cache (
                ward_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

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
    logger.info("Database initialized at %s", DB_PATH)


# ---------------------------------------------------------------------------
# Citizen Reports
# ---------------------------------------------------------------------------

def insert_report(
    ward_id: str,
    status: str,
    tanker_booked: bool,
    phone: str | None,
    note: str | None = None,
) -> dict[str, Any]:
    """Insert a citizen report. Phone is masked before storage."""
    now = datetime.utcnow().isoformat() + "Z"
    phone_masked = _mask_phone(phone)
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO citizen_reports
               (ward_id, status, tanker_booked, phone_masked, created_at, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ward_id, status, int(tanker_booked), phone_masked, now, note),
        )
        return {
            "id": cur.lastrowid,
            "ward_id": ward_id,
            "status": status,
            "tanker_booked": tanker_booked,
            "created_at": now,
        }


def get_reports(ward_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Get recent citizen reports for a ward."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, ward_id, status, tanker_booked, created_at, note
               FROM citizen_reports
               WHERE ward_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (ward_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_reports_all(limit: int = 200) -> list[dict[str, Any]]:
    """Get all recent citizen reports across wards."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, ward_id, status, tanker_booked, created_at
               FROM citizen_reports
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Alert Subscriptions
# ---------------------------------------------------------------------------

def insert_subscription(
    phone: str,
    language: str,
    ward_ids: list[str],
) -> dict[str, Any]:
    """Insert an alert subscription. Phone is masked immediately."""
    now = datetime.utcnow().isoformat() + "Z"
    phone_masked = _mask_phone(phone)
    ward_ids_json = json.dumps(ward_ids)
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO alert_subscriptions
               (phone_masked, language, ward_ids, created_at, demo_only)
               VALUES (?, ?, ?, ?, 1)""",
            (phone_masked, language, ward_ids_json, now),
        )
        return {
            "id": cur.lastrowid,
            "phone_masked": phone_masked,
            "language": language,
            "ward_ids": ward_ids,
            "created_at": now,
            "demo_only": True,
            "note": "No real SMS will be sent. This is a demo subscription.",
        }


# ---------------------------------------------------------------------------
# Ward state cache
# ---------------------------------------------------------------------------

def cache_ward_states(ward_states: list[dict]) -> None:
    """Cache ward states in SQLite for fast API reads."""
    now = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        for ws in ward_states:
            conn.execute(
                """INSERT OR REPLACE INTO ward_state_cache (ward_id, state_json, updated_at)
                   VALUES (?, ?, ?)""",
                (ws["ward_id"], json.dumps(ws, default=str), now),
            )


def get_cached_ward_states() -> list[dict] | None:
    """Get all ward states from cache, or None if empty."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT state_json FROM ward_state_cache ORDER BY ward_id"
        ).fetchall()
    if not rows:
        return None
    return [json.loads(r["state_json"]) for r in rows]


def get_cached_ward_state(ward_id: str) -> dict | None:
    """Get a single ward state from cache."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT state_json FROM ward_state_cache WHERE ward_id = ?",
            (ward_id,),
        ).fetchone()
    return json.loads(row["state_json"]) if row else None
