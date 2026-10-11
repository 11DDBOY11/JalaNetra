"""
Tests for JalaNetra Pulse:
- 3 distinct dry reporters within 90 minutes triggers active alert
- Duplicate same reporter report does not count twice
- Reports outside 90 minutes do not cluster
- Recovery requires 2 distinct restored/available reports
- Scenario seed records have simulation=True
- Real/current user reports have simulation=False
- SMS default mode never sends (preview only)
- Live SMS requires SMS_LIVE_MODE=true, confirm_test_send=true, and configured test number
- Raw phone numbers never appear in returned response
- Historical CGWB stale-data guardrail remains intact
"""
import os
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend import db, pulse


@pytest.fixture
def client():
    db.init_db()
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_pulse_db():
    db.init_db()
    with db.get_db() as conn:
        conn.execute("DELETE FROM water_reports")
        conn.execute("DELETE FROM community_alerts")
        conn.execute("DELETE FROM subscriptions")
    yield
    with db.get_db() as conn:
        conn.execute("DELETE FROM water_reports")
        conn.execute("DELETE FROM community_alerts")
        conn.execute("DELETE FROM subscriptions")


class TestPulseClustering:
    def test_three_distinct_dry_reports_triggers_active_alert(self, client):
        ward = "dk-kodialbail"
        # Reporter 1
        r1 = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "dry", "reporter_key": "user_a"
        })
        assert r1.status_code == 200
        assert r1.json()["alert"] is None

        # Reporter 2
        r2 = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "dry", "reporter_key": "user_b"
        })
        assert r2.status_code == 200
        assert r2.json()["alert"] is None

        # Reporter 3 (Threshold met!)
        r3 = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "dry", "reporter_key": "user_c"
        })
        assert r3.status_code == 200
        alert = r3.json()["alert"]
        assert alert is not None
        assert alert["status"] == "active"
        assert alert["ward_id"] == ward
        assert alert["independent_report_count"] == 3
        assert alert["severity"] in ("high", "critical")
        assert "3 independent households reported no water" in alert["trigger_reason"]
        assert "Community-reported issue" in alert["disclaimer"]

    def test_duplicate_same_reporter_rejected_within_30_minutes(self, client):
        ward = "dk-kodialbail"
        r1 = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "dry", "reporter_key": "user_same"
        })
        assert r1.status_code == 200

        # Duplicate submit within 30 min
        r2 = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "dry", "reporter_key": "user_same"
        })
        assert r2.status_code == 429
        assert "already submitted" in r2.json()["detail"]

    def test_reports_outside_90_minutes_do_not_cluster(self, client):
        ward = "dk-kodialbail"
        now = datetime.utcnow()
        old_time = (now - timedelta(minutes=100)).isoformat() + "Z"

        # Insert 2 old dry reports directly into DB
        with db.get_db() as conn:
            conn.execute(
                """INSERT INTO water_reports
                   (ward_id, status, reporter_key_hash, created_at, phone_hash, source, simulation)
                   VALUES (?, 'dry', 'old_rep_1', ?, NULL, 'live_user', 0)""",
                (ward, old_time)
            )
            conn.execute(
                """INSERT INTO water_reports
                   (ward_id, status, reporter_key_hash, created_at, phone_hash, source, simulation)
                   VALUES (?, 'dry', 'old_rep_2', ?, NULL, 'live_user', 0)""",
                (ward, old_time)
            )

        # Add 1 current dry report now
        r = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "dry", "reporter_key": "current_rep_3"
        })
        assert r.status_code == 200
        # Alert should NOT trigger because the old 2 reports are outside 90m
        assert r.json()["alert"] is None

    def test_recovery_requires_two_distinct_reports(self, client):
        ward = "dk-kodialbail"
        # Seed 3 dry reports to trigger outage
        s = client.post("/api/pulse/scenario/seed-outage", json={"ward_id": ward})
        assert s.status_code == 200
        alert = s.json()["alert"]
        assert alert["status"] == "active"

        # First restored report
        r1 = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "restored", "reporter_key": "rec_user_1"
        })
        assert r1.status_code == 200
        # Still active (needs 2 distinct)
        assert r1.json()["alert"]["status"] == "active"

        # Second restored report
        r2 = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "restored", "reporter_key": "rec_user_2"
        })
        assert r2.status_code == 200
        # Now recovery!
        assert r2.json()["alert"]["status"] == "recovery"
        assert "recovery" in r2.json()["alert"]["trigger_reason"].lower()

    def test_scenario_seed_is_simulation_true_and_user_is_simulation_false(self, client):
        ward = "dk-kodialbail"
        # Seed scenario
        s = client.post("/api/pulse/scenario/seed-outage", json={"ward_id": ward})
        assert s.status_code == 200
        assert s.json()["simulation"] is True

        # User report
        u = client.post("/api/pulse/reports", json={
            "ward_id": ward, "status": "available", "reporter_key": "live_user_xyz"
        })
        assert u.status_code == 200
        assert u.json()["simulation"] is False
        assert u.json()["source"] == "live_user"


class TestPulseSMSAndPrivacy:
    def test_sms_default_mode_never_sends_and_masks_destination(self, client):
        # By default SMS_LIVE_MODE is unset or false
        os.environ["SMS_LIVE_MODE"] = "false"
        r = client.post("/api/pulse/sms/test", json={
            "ward_id": "dk-kodialbail",
            "confirm_test_send": False
        })
        assert r.status_code == 200
        data = r.json()
        assert data["sent"] is False
        assert data["mode"] == "preview"
        assert "SMS demo mode enabled" in data["reason"]
        assert "+XX-" in data["destination_masked"]
        assert "JalaNetra Pulse" in data["message_preview"]

    def test_sms_confirm_false_even_if_live_mode_true_does_not_send(self, client):
        os.environ["SMS_LIVE_MODE"] = "true"
        r = client.post("/api/pulse/sms/test", json={
            "ward_id": "dk-kodialbail",
            "confirm_test_send": False  # Not confirmed
        })
        assert r.status_code == 200
        assert r.json()["sent"] is False
        assert r.json()["mode"] == "preview"

    def test_raw_phone_never_returned_or_stored_in_plain_text(self, client):
        raw_phone = "+919876543210"
        r = client.post("/api/pulse/reports", json={
            "ward_id": "dk-kodialbail",
            "status": "low",
            "phone": raw_phone,
            "reporter_key": "privacy_user_1"
        })
        assert r.status_code == 200
        resp_text = r.text
        # Raw phone number MUST NOT appear anywhere in response text
        assert "9876543210" not in resp_text
        assert r.json()["phone_masked"] == "+XX-98765XXXXX"

        # Verify DB does not contain raw phone
        with db.get_db() as conn:
            row = conn.execute("SELECT phone_hash FROM water_reports WHERE id = ?", (r.json()["report_id"],)).fetchone()
            assert row["phone_hash"] is not None
            assert "9876543210" not in row["phone_hash"]


class TestPulseSummaryAndGuardrail:
    def test_pulse_summary_endpoint(self, client):
        r = client.get("/api/pulse/summary")
        assert r.status_code == 200
        data = r.json()
        assert "active_alert_count" in data
        assert "wards_monitored" in data
        assert len(data["wards_monitored"]) >= 5
        assert "disclaimer" in data

    def test_historical_cgwb_stale_data_guardrail_intact(self, client):
        # Confirm that /api/wards historical endpoint still returns historical context only
        r = client.get("/api/wards/dk-kodialbail")
        assert r.status_code == 200
        data = r.json()
        fc = data["ward"]["forecast"]
        assert fc["risk_level"] == "historical_context"
        assert fc["forecast_status"] == "historical_context_only"
        assert fc["forecast_current"] is False
        assert fc["book_tanker_by"] is None
