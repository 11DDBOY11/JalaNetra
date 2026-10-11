"""
JalaNetra Backend Tests
Run with: python -m pytest tests/ -v
"""
import io
import json
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.ingest.normalizer import (
    normalize_groundwater_df,
    normalize_rainfall_df,
)
from backend.ingest.ward_builder import (
    build_all_ward_states,
    WARDS,
)
from backend.alerts.forecast import compute_forecast, _classify_risk
from backend.alerts.generator import (
    generate_sms_text,
    build_alert_preview,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_gw_df():
    """Minimal synthetic groundwater DataFrame."""
    return pd.DataFrame({
        "observation_date": ["2026-01-15", "2026-05-15", "2026-10-01"],
        "station_id": ["DK-WELL-001", "DK-WELL-001", "DK-WELL-001"],
        "district": ["Dakshina Kannada"] * 3,
        "groundwater_depth_m": [8.2, 11.4, 9.8],
        "latitude": [12.87] * 3,
        "longitude": [74.88] * 3,
        "source": ["SYNTHETIC_SAMPLE"] * 3,
    })


@pytest.fixture
def sample_rain_df():
    """Minimal synthetic rainfall DataFrame."""
    return pd.DataFrame({
        "observation_date": ["2026-06-01", "2026-07-01", "2026-10-01"],
        "district": ["Dakshina Kannada"] * 3,
        "rainfall_mm": [312.5, 341.2, 45.2],
        "source": ["SYNTHETIC_SAMPLE"] * 3,
    })


# ---------------------------------------------------------------------------
# A. Normalizer Tests
# ---------------------------------------------------------------------------

class TestNormalizer:
    def test_groundwater_canonical_passthrough(self, sample_gw_df):
        df, warnings = normalize_groundwater_df(sample_gw_df)
        assert list(df.columns) == [
            "observation_date", "station_id", "district",
            "groundwater_depth_m", "latitude", "longitude", "source",
        ]
        assert len(df) == 3
        assert df["groundwater_depth_m"].iloc[0] == pytest.approx(8.2)

    def test_groundwater_alias_mapping(self):
        """Test that alternative column names are mapped to canonical."""
        df_raw = pd.DataFrame({
            "date": ["2026-01-15"],
            "well_no": ["DK-001"],
            "state_district": ["Dakshina Kannada"],
            "wl_m_bgl": [10.5],
            "lat": [12.87],
            "lon": [74.88],
        })
        df, warnings = normalize_groundwater_df(df_raw, file_source="test")
        assert "groundwater_depth_m" in df.columns
        assert df["groundwater_depth_m"].iloc[0] == pytest.approx(10.5)

    def test_groundwater_drops_missing_depth(self):
        df_raw = pd.DataFrame({
            "observation_date": ["2026-01-15", "2026-02-01"],
            "station_id": ["W1", "W2"],
            "district": ["Dakshina Kannada"] * 2,
            "groundwater_depth_m": [None, 9.5],
            "latitude": [12.87] * 2,
            "longitude": [74.88] * 2,
            "source": ["test"] * 2,
        })
        df, warnings = normalize_groundwater_df(df_raw)
        assert len(df) == 1
        assert any("Dropped" in w for w in warnings)

    def test_rainfall_canonical_passthrough(self, sample_rain_df):
        df, warnings = normalize_rainfall_df(sample_rain_df)
        assert list(df.columns) == [
            "observation_date", "district", "rainfall_mm", "source"
        ]
        assert len(df) == 3

    def test_rainfall_alias_mapping(self):
        df_raw = pd.DataFrame({
            "obs_date": ["2026-06-01"],
            "district_name": ["Dakshina Kannada"],
            "precip_mm": [250.0],
        })
        df, warnings = normalize_rainfall_df(df_raw, file_source="test")
        assert "rainfall_mm" in df.columns
        assert df["rainfall_mm"].iloc[0] == pytest.approx(250.0)

    def test_unknown_columns_produce_warnings(self):
        df_raw = pd.DataFrame({
            "observation_date": ["2026-01-15"],
            "station_id": ["DK-001"],
            "district": ["DK"],
            "groundwater_depth_m": [10.0],
            "latitude": [12.87],
            "longitude": [74.88],
            "source": ["test"],
            "totally_unknown_col": ["value"],
        })
        df, warnings = normalize_groundwater_df(df_raw)
        assert any("totally_unknown_col" in w for w in warnings)

    def test_real_cgwb_schema_mapping(self):
        """Test mapping exact columns from gwl_manual_quarterly_cgwb_ka_1991_2020.csv."""
        df_raw = pd.DataFrame({
            "Data Acquisition Time": ["05-01-2013 06:00"],
            "Station": ["Surathkal"],
            "District": ["Dakshin Kannada"],
            "Groundwater Level Quarterly Manual (meter)": [8.75],
            "Latitude": [12.9944],
            "Longitude": [74.8000],
        })
        df, warnings = normalize_groundwater_df(df_raw, file_source="cgwb_test")
        assert "groundwater_depth_m" in df.columns
        assert "station_id" in df.columns
        assert df["station_id"].iloc[0] == "Surathkal"
        assert df["groundwater_depth_m"].iloc[0] == pytest.approx(8.75)
        assert df["district"].iloc[0] == "Dakshina Kannada"

    def test_dakshina_kannada_filtering(self):
        """Test that Dakshin Kannada rows are filtered from a multi-district dataset."""
        df_raw = pd.DataFrame({
            "Data Acquisition Time": ["05-01-2013 06:00", "05-01-2013 06:00"],
            "Station": ["Surathkal", "Abbigere"],
            "District": ["Dakshin Kannada", "Koppal"],
            "Groundwater Level Quarterly Manual (meter)": [8.75, 2.23],
            "Latitude": [12.9944, 15.4305],
            "Longitude": [74.8000, 76.1141],
        })
        df, warnings = normalize_groundwater_df(df_raw)
        assert len(df) == 1
        assert df["station_id"].iloc[0] == "Surathkal"
        assert df["district"].iloc[0] == "Dakshina Kannada"


# ---------------------------------------------------------------------------
# B. Ward Builder Tests
# ---------------------------------------------------------------------------

class TestWardBuilder:
    def test_builds_all_wards(self, sample_gw_df, sample_rain_df):
        # Convert dates
        sample_gw_df["observation_date"] = pd.to_datetime(sample_gw_df["observation_date"])
        sample_rain_df["observation_date"] = pd.to_datetime(sample_rain_df["observation_date"])
        states = build_all_ward_states(sample_gw_df, sample_rain_df)
        assert len(states) == len(WARDS)

    def test_ward_state_has_required_fields(self, sample_gw_df, sample_rain_df):
        sample_gw_df["observation_date"] = pd.to_datetime(sample_gw_df["observation_date"])
        sample_rain_df["observation_date"] = pd.to_datetime(sample_rain_df["observation_date"])
        states = build_all_ward_states(sample_gw_df, sample_rain_df)
        required = {"ward_id", "name", "groundwater_depth_m", "synthetic", "data_mode"}
        for ws in states:
            assert required.issubset(ws.keys()), f"Missing fields in {ws['ward_id']}"

    def test_empty_data_falls_back_to_synthetic(self):
        """When no real data, ward builder must produce synthetic fallback."""
        empty_gw = pd.DataFrame(columns=["observation_date", "station_id", "district",
                                          "groundwater_depth_m", "latitude", "longitude", "source"])
        empty_rain = pd.DataFrame(columns=["observation_date", "district", "rainfall_mm", "source"])
        states = build_all_ward_states(empty_gw, empty_rain, data_mode="demo")
        for ws in states:
            assert ws["synthetic"] is True

    def test_ward_ids_match_expected(self, sample_gw_df, sample_rain_df):
        sample_gw_df["observation_date"] = pd.to_datetime(sample_gw_df["observation_date"])
        sample_rain_df["observation_date"] = pd.to_datetime(sample_rain_df["observation_date"])
        states = build_all_ward_states(sample_gw_df, sample_rain_df)
        ids = {ws["ward_id"] for ws in states}
        expected = {"dk-kodialbail", "dk-kankanady", "dk-kadri", "dk-surathkal", "dk-moodbidri"}
        assert ids == expected


# ---------------------------------------------------------------------------
# C. Forecast Engine Tests
# ---------------------------------------------------------------------------

class TestForecastEngine:
    def _make_ward(self, depth, trend=None, rain=20.0, synthetic=True, age=30, obs=2):
        return {
            "ward_id": "test-ward",
            "name": "Test Ward",
            "display_name": "Test Ward",
            "groundwater_depth_m": depth,
            "depth_trend_m_per_month": trend,
            "rainfall_rainfall_7d_mm": rain,
            "synthetic": synthetic,
            "data_mode": "demo" if synthetic else "real",
            "data_age_days": age,
            "observations_count": obs,
        }

    def test_worsening_depth_raises_risk(self):
        """Deep water table with worsening trend → high or critical."""
        ws = self._make_ward(depth=14.0, trend=1.0)
        fc = compute_forecast(ws)
        assert fc["risk_level"] in ("high", "critical")

    def test_heavy_rainfall_reduces_urgency(self):
        """Heavy rainfall should slow depletion estimate."""
        ws_dry = self._make_ward(depth=12.0, trend=0.8, rain=2.0)
        ws_wet = self._make_ward(depth=12.0, trend=0.8, rain=150.0)
        fc_dry = compute_forecast(ws_dry)
        fc_wet = compute_forecast(ws_wet)
        # Days to dry should be more for wet scenario
        if fc_dry["days_to_dry_estimate"] and fc_wet["days_to_dry_estimate"]:
            assert fc_wet["days_to_dry_estimate"] >= fc_dry["days_to_dry_estimate"]

    def test_no_observations_gives_low_confidence(self):
        """No real observations → confidence must be low."""
        ws = self._make_ward(depth=9.0, trend=None, synthetic=True, obs=0, age=None)
        fc = compute_forecast(ws)
        assert fc["confidence"] == "low"

    def test_sparse_data_gives_low_confidence(self):
        """Only 1 observation, 200-day-old data → low confidence."""
        ws = self._make_ward(depth=9.0, trend=None, synthetic=False, obs=1, age=200)
        fc = compute_forecast(ws)
        assert fc["confidence"] == "low"

    def test_citizen_dry_report_elevates_risk(self):
        """A recent 'dry' citizen report should raise risk from low."""
        ws = self._make_ward(depth=7.0, trend=-0.2, rain=80.0, synthetic=True)
        today_str = (date.today()).isoformat() + "T00:00:00Z"
        reports = [{"status": "dry", "created_at": today_str}]
        fc = compute_forecast(ws, citizen_reports=reports)
        assert fc["risk_level"] not in ("low",)
        assert fc["citizen_dry_report"] is True

    def test_high_risk_produces_book_tanker_by(self):
        """High risk must produce a book_tanker_by date."""
        ws = self._make_ward(depth=15.0, trend=0.9)
        fc = compute_forecast(ws)
        if fc["risk_level"] in ("high", "critical"):
            assert fc["book_tanker_by"] is not None

    def test_forecast_does_not_claim_certainty(self):
        """Explanation must not contain absolute certainty language."""
        ws = self._make_ward(depth=12.0, trend=0.5, synthetic=True)
        fc = compute_forecast(ws)
        expl = fc["explanation"].lower()
        # Should use hedged language
        forbidden = ["will definitely", "guaranteed", "100%"]
        for phrase in forbidden:
            assert phrase not in expl

    def test_risk_classification(self):
        assert _classify_risk(6.0, None) == "low"
        assert _classify_risk(10.0, None) == "moderate"
        assert _classify_risk(13.0, None) == "high"
        assert _classify_risk(15.0, None) == "critical"

    def test_risk_worsens_with_trend(self):
        # With strong worsening trend, moderate → high
        assert _classify_risk(10.0, 0.6) == "high"


# ---------------------------------------------------------------------------
# D. Alert Generator Tests
# ---------------------------------------------------------------------------

class TestAlertGenerator:
    def _make_forecast(self, risk="high", synthetic=True):
        return {
            "ward_id": "dk-test",
            "ward_name": "Test Ward",
            "risk_level": risk,
            "days_to_dry_estimate": 14,
            "book_tanker_by": str(date.today() + timedelta(days=7)),
            "confidence": "low" if synthetic else "medium",
            "synthetic": synthetic,
            "data_mode": "demo" if synthetic else "real",
        }

    def test_sms_contains_ward_name(self):
        fc = self._make_forecast()
        sms = generate_sms_text(fc, "en-IN")
        assert "Test Ward" in sms

    def test_sms_labels_demo_data(self):
        fc = self._make_forecast(synthetic=True)
        sms = generate_sms_text(fc, "en-IN")
        assert "DEMO" in sms

    def test_hindi_sms_generated(self):
        fc = self._make_forecast()
        sms = generate_sms_text(fc, "hi-IN")
        # Hindi SMS should contain Devanagari script
        assert any("\u0900" <= c <= "\u097f" for c in sms)

    def test_preview_contains_all_fields(self):
        fc = self._make_forecast()
        preview = build_alert_preview(fc)
        required = {
            "demo_only", "no_sms_sent", "sms_text_en",
            "sms_text_hi", "voice_text_en", "voice_text_hi", "disclaimer"
        }
        assert required.issubset(preview.keys())

    def test_preview_no_sms_flag(self):
        fc = self._make_forecast()
        preview = build_alert_preview(fc)
        assert preview["no_sms_sent"] is True
        assert preview["demo_only"] is True

    def test_high_risk_triggers_alert(self):
        fc = self._make_forecast(risk="high")
        preview = build_alert_preview(fc)
        assert preview["alert_triggered"] is True

    def test_low_risk_does_not_trigger_alert(self):
        fc = self._make_forecast(risk="low")
        preview = build_alert_preview(fc)
        assert preview["alert_triggered"] is False


# ---------------------------------------------------------------------------
# E. API Endpoint Tests
# ---------------------------------------------------------------------------

class TestAPI:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "data_mode" in data

    def test_list_wards(self, client):
        r = client.get("/api/wards")
        assert r.status_code == 200
        data = r.json()
        assert "wards" in data
        assert "data_mode" in data
        assert len(data["wards"]) == 5

    def test_ward_fields(self, client):
        r = client.get("/api/wards")
        wards = r.json()["wards"]
        for w in wards:
            assert "ward_id" in w
            assert "risk_level" in w
            assert w["risk_level"] in ("low", "moderate", "high", "critical", "historical_context")
            assert "confidence" in w

    def test_get_ward_detail(self, client):
        r = client.get("/api/wards/dk-kodialbail")
        assert r.status_code == 200
        data = r.json()
        assert "ward" in data
        assert data["ward"]["ward_id"] == "dk-kodialbail"

    def test_get_ward_not_found(self, client):
        r = client.get("/api/wards/nonexistent-ward")
        assert r.status_code == 404

    def test_get_forecast(self, client):
        r = client.get("/api/forecast?ward_id=dk-kodialbail")
        assert r.status_code == 200
        data = r.json()
        assert "forecast" in data
        fc = data["forecast"]
        assert fc["risk_level"] in ("low", "moderate", "high", "critical", "historical_context")
        assert "explanation" in fc
        assert "recommended_action" in fc

    def test_submit_report_valid(self, client):
        r = client.post("/api/reports", json={
            "ward_id": "dk-kodialbail",
            "status": "dry",
            "tanker_booked": False,
        })
        assert r.status_code == 201
        assert r.json()["ok"] is True

    def test_submit_report_invalid_status(self, client):
        r = client.post("/api/reports", json={
            "ward_id": "dk-kodialbail",
            "status": "invalid_status",
        })
        assert r.status_code == 422

    def test_get_reports(self, client):
        r = client.get("/api/reports?ward_id=dk-kodialbail")
        assert r.status_code == 200
        assert "reports" in r.json()

    def test_alert_subscribe(self, client):
        r = client.post("/api/alerts/subscribe", json={
            "phone": "+919876543210",
            "language": "en-IN",
            "ward_ids": ["dk-kodialbail"],
        })
        assert r.status_code == 201
        data = r.json()
        assert data["ok"] is True
        assert data["no_sms_will_be_sent"] is True

    def test_alert_preview(self, client):
        r = client.post("/api/alerts/preview", json={
            "ward_id": "dk-kodialbail",
            "language": "en-IN",
        })
        assert r.status_code == 200
        data = r.json()
        preview = data["preview"]
        assert preview["no_sms_sent"] is True
        assert "sms_text_en" in preview

    def test_data_quality_endpoint(self, client):
        r = client.get("/api/data-quality")
        assert r.status_code == 200
        assert "quality_report" in r.json()

    def test_synthetic_flag_present(self, client):
        """All responses should include synthetic flag."""
        r = client.get("/api/wards")
        assert "synthetic" in r.json()

    def test_no_real_phone_in_response(self, client):
        """Phone numbers should not appear in API responses."""
        r = client.post("/api/alerts/subscribe", json={
            "phone": "+919876543210",
            "language": "en-IN",
            "ward_ids": ["dk-kodialbail"],
        })
        response_text = r.text
        # Real number should not appear verbatim
        assert "9876543210" not in response_text


# ---------------------------------------------------------------------------
# F. Integrity & Honesty Audit Tests
# ---------------------------------------------------------------------------

class TestAuditIntegrity:
    def test_data_mode_valid_enum(self, client):
        """data_mode must be one of real_historical, hybrid, or demo."""
        r = client.get("/health")
        assert r.status_code == 200
        data_mode = r.json().get("data_mode")
        assert data_mode in ("real_historical", "hybrid", "demo")

    def test_real_csv_detection_when_present(self):
        """If real CGWB CSV is in data/raw/groundwater/, data_mode must be hybrid or real_historical."""
        from pathlib import Path
        from backend.ingest.ward_builder import load_or_generate_ward_states
        raw_gw = Path("data/raw/groundwater")
        csv_files = list(raw_gw.glob("*.csv")) if raw_gw.exists() else []
        if csv_files:
            wards, q_report = load_or_generate_ward_states()
            assert q_report["data_mode"] in ("hybrid", "real_historical")
            assert q_report["groundwater"]["rows"] > 0
            assert q_report["groundwater"]["wells"] > 0

    def test_synthetic_false_requires_source_data(self, client):
        """synthetic cannot be False unless derived from verified source rows."""
        r = client.get("/api/wards")
        data = r.json()
        wards = data.get("wards", [])
        for w in wards:
            # If a ward has 0 real observations, it must be marked synthetic
            if w.get("observations_count") == 0:
                assert w.get("synthetic") is True
                assert w.get("groundwater_synthetic") is True
            # If groundwater_synthetic is False, observations_count must be > 0
            if w.get("groundwater_synthetic") is False:
                assert w.get("groundwater_depth_m") is not None

    def test_edge_output_contains_simulated_true(self):
        """All demo edge telemetry must carry simulated: true and notice."""
        from edge.simulator import generate_reading, WARDS
        reading = generate_reading(WARDS[0])
        assert reading["simulated"] is True
        assert reading["synthetic"] is True
        assert "Simulated edge telemetry" in reading["notice"]

    def test_alert_previews_never_send_notifications(self, client):
        """Alert previews must guarantee zero real dispatches."""
        r = client.post("/api/alerts/preview", json={
            "ward_id": "dk-kodialbail",
            "language": "en-IN",
        })
        assert r.status_code == 200
        preview = r.json().get("preview", {})
        assert preview.get("no_sms_sent") is True
        assert preview.get("no_call_made") is True
        assert preview.get("demo_only") is True

    def test_hybrid_mode_consistency(self, client):
        """In hybrid mode, top-level synthetic must be False and source modes must be present."""
        r = client.get("/api/wards")
        assert r.status_code == 200
        data = r.json()
        assert data["data_mode"] == "hybrid"
        assert data["synthetic"] is False
        assert data["groundwater_source_mode"] == "real_historical"
        assert data["rainfall_source_mode"] == "synthetic_baseline"
        assert data["ward_estimate_mode"] == "model_assisted"
        
        # Verify each ward with verified CGWB source rows has synthetic: False
        for w in data["wards"]:
            if w.get("matched_station"):
                assert w["synthetic"] is False
                assert w["groundwater_synthetic"] is False

    def test_health_source_modes(self, client):
        """Health check returns accurate data_mode and source mode metadata."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["data_mode"] == "hybrid"
        assert data["synthetic"] is False
        assert data["groundwater_source_mode"] == "real_historical"
        assert data["rainfall_source_mode"] == "synthetic_baseline"
        assert data["ward_estimate_mode"] == "model_assisted"

    def test_stale_data_guardrail_applied_to_historical_observation(self, client):
        """A 2020 source observation on current date must produce historical_context guardrail."""
        r = client.get("/api/forecast?ward_id=dk-kodialbail")
        assert r.status_code == 200
        fc = r.json()["forecast"]
        assert fc["forecast_current"] is False
        assert fc["risk_level"] == "historical_context"
        assert fc["forecast_status"] == "historical_context_only"
        assert fc["book_tanker_by"] is None
        assert fc["days_to_dry_estimate"] is None
        assert fc["weeks_to_dry"] is None
        assert "This record is historical" in fc["recommended_action"]
        assert "too old for a current household water forecast" in fc["explanation"]

    def test_fresh_observation_produces_active_forecast(self):
        """A fresh observation within 180 days produces an active forecast."""
        from datetime import date, timedelta
        from backend.alerts.forecast import compute_forecast
        fresh_ward = {
            "ward_id": "test-fresh",
            "name": "Fresh Ward",
            "groundwater_depth_m": 12.5,
            "depth_observed_at": str(date.today() - timedelta(days=30)),
            "data_age_days": 30,
            "observations_count": 5,
            "synthetic": False,
            "depth_trend_m_per_month": 0.4,
            "rainfall_rainfall_7d_mm": 15.0,
            "data_mode": "hybrid",
        }
        fc = compute_forecast(fresh_ward)
        assert fc["forecast_current"] is True
        assert fc["forecast_status"] == "current_active"
        assert fc["risk_level"] in ("low", "moderate", "high", "critical")
        assert fc["days_to_dry_estimate"] is not None
        assert fc["book_tanker_by"] is not None

    def test_scenario_simulation_labeled_and_preserves_source(self, client):
        """Scenario simulation must be visibly labeled and never alter real historical source fields."""
        r = client.get("/api/forecast?ward_id=dk-kodialbail&scenario=dry")
        assert r.status_code == 200
        fc = r.json()["forecast"]
        assert fc["is_scenario_simulation"] is True
        assert fc["risk_level"] == "critical"
        assert fc["days_to_dry_estimate"] == 7
        assert fc["book_tanker_by"] is not None
        assert "Scenario simulation" in fc["explanation"]
        assert "Scenario simulation" in fc["recommended_action"]
        # Source depth remains historical CGWB source row
        assert fc["groundwater_depth_m"] == pytest.approx(10.73)
