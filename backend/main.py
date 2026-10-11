"""
JalaNetra FastAPI Backend
Run with: python -m uvicorn backend.main:app --reload --port 8000

DEMO MODE: No real SMS, no real credentials, no real data required.
"""
from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from backend import db
from backend.alerts.forecast import compute_forecast
from backend.alerts.generator import build_alert_preview
from backend.ingest.ward_builder import load_or_generate_ward_states

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("jalanetra")

# ---------------------------------------------------------------------------
# App-level state
# ---------------------------------------------------------------------------
_ward_states: list[dict] = []
_quality_report: dict = {}
_data_mode: str = "demo"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB and load ward states."""
    global _ward_states, _quality_report, _data_mode
    logger.info("JalaNetra startup — loading ward data...")
    db.init_db()

    try:
        ward_states, quality_report = load_or_generate_ward_states()
        _ward_states = ward_states
        _quality_report = quality_report
        _data_mode = quality_report.get("data_mode", "demo")
        db.cache_ward_states(ward_states)
        logger.info(
            "Loaded %d wards in %s mode (synthetic=%s)",
            len(ward_states), _data_mode, quality_report.get("synthetic", True)
        )
    except Exception as exc:
        logger.error("Ward data load failed: %s — serving empty state", exc)
        _ward_states = []
        _quality_report = {"error": str(exc)}

    yield
    logger.info("JalaNetra shutdown.")


app = FastAPI(
    title="JalaNetra API",
    description=(
        "Mangaluru Water Security Early Warning System. "
        "DEMO MODE: No real SMS, no real data required to run locally."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow local Vite dev server and any Amplify domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.amplifyapp.com",
    ],
    allow_origin_regex=r"https://.*\.amplifyapp\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _demo_envelope(data: Any, synthetic: bool | None = None) -> dict:
    """Wrap response with standard demo metadata."""
    if _data_mode == "hybrid":
        is_synth = False if synthetic is None else bool(synthetic)
        gw_mode = "real_historical"
        rain_mode = "synthetic_baseline"
        est_mode = "model_assisted"
    elif _data_mode == "real_historical":
        is_synth = False if synthetic is None else bool(synthetic)
        gw_mode = "real_historical"
        rain_mode = "real_historical"
        est_mode = "model_assisted"
    else:
        is_synth = True if synthetic is None else bool(synthetic)
        gw_mode = "synthetic_fallback"
        rain_mode = "synthetic_baseline"
        est_mode = "demo_heuristic"

    env = {
        "data_mode": _data_mode,
        "synthetic": is_synth,
        "groundwater_source_mode": gw_mode,
        "rainfall_source_mode": rain_mode,
        "ward_estimate_mode": est_mode,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    env.update(data)
    return env


def _get_ward_state(ward_id: str) -> dict:
    """Retrieve ward state from in-memory list."""
    for ws in _ward_states:
        if ws["ward_id"] == ward_id:
            return ws
    raise HTTPException(status_code=404, detail=f"Ward '{ward_id}' not found")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class CitizenReportCreate(BaseModel):
    ward_id: str
    status: str
    tanker_booked: bool = False
    phone: Optional[str] = None
    note: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"came", "low", "dry"}
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        # Accept Indian format only
        cleaned = re.sub(r"\D", "", v)
        if len(cleaned) not in (10, 12):
            raise ValueError("Phone must be 10 or 12 digits (Indian format)")
        return v  # Store original, masking happens in DB layer


class AlertSubscribeCreate(BaseModel):
    phone: str
    language: str = "en-IN"
    ward_ids: list[str]

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        valid = {"en-IN", "hi-IN"}
        if v not in valid:
            raise ValueError(f"language must be one of {valid}")
        return v

    @field_validator("ward_ids")
    @classmethod
    def validate_ward_ids(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("ward_ids must not be empty")
        return v


class AlertPreviewRequest(BaseModel):
    ward_id: str
    language: str = "en-IN"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "jalanetra-backend",
        "version": "1.0.0",
        "data_mode": _data_mode,
        "synthetic": _data_mode == "demo",
        "groundwater_source_mode": "real_historical" if _data_mode in ("hybrid", "real_historical") else "synthetic_fallback",
        "rainfall_source_mode": "synthetic_baseline" if _data_mode == "hybrid" else ("real_historical" if _data_mode == "real_historical" else "synthetic_baseline"),
        "ward_estimate_mode": "model_assisted" if _data_mode in ("hybrid", "real_historical") else "demo_heuristic",
        "wards_loaded": len(_ward_states),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/wards", tags=["wards"])
def list_wards():
    """
    List all wards with current water stress summary.
    Returns demo metadata when synthetic data is in use.
    """
    wards_summary = []
    for ws in _ward_states:
        # Get cached citizen reports to elevate risk if needed
        try:
            reports = db.get_reports(ws["ward_id"], limit=20)
        except Exception:
            reports = []

        forecast = compute_forecast(ws, citizen_reports=reports)

        wards_summary.append({
            "ward_id": ws["ward_id"],
            "name": ws["name"],
            "display_name": ws["display_name"],
            "latitude": ws["latitude"],
            "longitude": ws["longitude"],
            "groundwater_depth_m": ws.get("groundwater_depth_m"),
            "depth_observed_at": ws.get("depth_observed_at"),
            "rainfall_7d_mm": ws.get("rainfall_rainfall_7d_mm"),
            "risk_level": forecast["risk_level"],
            "forecast_status": forecast.get("forecast_status", "historical_context_only"),
            "forecast_current": forecast.get("forecast_current", False),
            "observation_age_days": forecast.get("observation_age_days"),
            "days_to_dry_estimate": forecast["days_to_dry_estimate"],
            "weeks_to_dry": forecast.get("weeks_to_dry"),
            "book_tanker_by": forecast["book_tanker_by"],
            "confidence": forecast["confidence"],
            "recommended_action": forecast.get("recommended_action"),
            "explanation": forecast.get("explanation"),
            "synthetic": ws.get("synthetic", False),
            "groundwater_synthetic": ws.get("groundwater_synthetic", False),
            "matched_station": ws.get("matched_station"),
            "freshness_disclosure": ws.get("freshness_disclosure", "Historical quarterly government groundwater observations; not live groundwater sensor data."),
            "data_mode": _data_mode,
        })

    return _demo_envelope(
        {"wards": wards_summary, "total": len(wards_summary)},
        synthetic=False if _data_mode in ("hybrid", "real_historical") else True,
    )


@app.get("/api/wards/{ward_id}", tags=["wards"])
def get_ward(ward_id: str):
    """Get full details for a single ward."""
    ws = _get_ward_state(ward_id)
    try:
        reports = db.get_reports(ward_id, limit=20)
    except Exception:
        reports = []
    forecast = compute_forecast(ws, citizen_reports=reports)

    return _demo_envelope(
        {
            "ward": {
                **ws,
                "forecast": forecast,
                "recent_reports_count": len(reports),
            }
        },
        synthetic=False if _data_mode in ("hybrid", "real_historical") else ws.get("synthetic", True),
    )


@app.get("/api/forecast", tags=["forecast"])
def get_forecast(
    ward_id: str = Query(..., description="Ward ID to forecast"),
    scenario: Optional[str] = Query(None, description="Hypothetical scenario: 'normal', 'low', or 'dry'"),
):
    """
    Get risk forecast for a ward.
    Forecast is computed from a rule-based heuristic engine.
    If observations are older than 180 days, returns historical context with forecast_current: false.
    If a scenario is specified, returns an illustrative what-if simulation advisory.
    """
    ws = _get_ward_state(ward_id)
    try:
        reports = db.get_reports(ward_id, limit=20)
    except Exception:
        reports = []
    forecast = compute_forecast(ws, citizen_reports=reports, scenario=scenario)
    return _demo_envelope(
        {"forecast": forecast},
        synthetic=False if _data_mode in ("hybrid", "real_historical") else ws.get("synthetic", True),
    )


@app.get("/api/reports", tags=["reports"])
def get_reports(ward_id: str = Query(..., description="Ward ID")):
    """Get citizen water reports for a ward."""
    try:
        reports = db.get_reports(ward_id, limit=50)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return _demo_envelope(
        {"ward_id": ward_id, "reports": reports, "count": len(reports)},
        synthetic=False,
    )


@app.post("/api/reports", status_code=201, tags=["reports"])
def create_report(report: CitizenReportCreate):
    """
    Submit a citizen water supply report.
    Phone number is masked before storage.
    """
    try:
        result = db.insert_report(
            ward_id=report.ward_id,
            status=report.status,
            tanker_booked=report.tanker_booked,
            phone=report.phone,
            note=report.note,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {
        "ok": True,
        "received_at": result["created_at"],
        "report_id": result["id"],
        "note": "Phone number was masked before storage. No real SMS sent.",
    }


@app.post("/api/alerts/subscribe", status_code=201, tags=["alerts"])
def subscribe_alert(sub: AlertSubscribeCreate):
    """
    Register for water-stress alerts.
    DEMO MODE: Phone is masked. No real SMS will ever be sent.
    """
    # Validate ward IDs exist
    valid_ids = {ws["ward_id"] for ws in _ward_states}
    invalid = [w for w in sub.ward_ids if w not in valid_ids]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown ward_ids: {invalid}")

    try:
        result = db.insert_subscription(
            phone=sub.phone,
            language=sub.language,
            ward_ids=sub.ward_ids,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "ok": True,
        "demo_only": True,
        "no_sms_will_be_sent": True,
        "subscription": result,
        "message": (
            "Demo subscription recorded. In production, you would receive "
            "alerts via AWS SNS and Amazon Polly voice notes when water stress "
            "is detected. No real SMS is sent in demo mode."
        ),
    }


@app.post("/api/alerts/preview", tags=["alerts"])
def alert_preview(req: AlertPreviewRequest):
    """
    Preview the alert message that WOULD be sent for a ward.
    Returns SMS text, English voice text, and Hindi voice text.
    DEMO ONLY — no message is sent.
    """
    ws = _get_ward_state(req.ward_id)
    try:
        reports = db.get_reports(req.ward_id, limit=20)
    except Exception:
        reports = []
    forecast = compute_forecast(ws, citizen_reports=reports)
    preview = build_alert_preview(forecast, language=req.language)
    return _demo_envelope({"preview": preview}, synthetic=forecast.get("synthetic", True))


@app.get("/api/data-quality", tags=["meta"])
def data_quality():
    """Return the data quality report for the current session."""
    return _demo_envelope({"quality_report": _quality_report})


from backend import db, pulse


class PulseReportCreate(BaseModel):
    ward_id: str
    status: str
    reporter_key: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_pulse_status(cls, v: str) -> str:
        valid = {"available", "low", "dry", "restored"}
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v


class PulseResolveReport(BaseModel):
    reporter_key: Optional[str] = None
    note: Optional[str] = None


class PulseScenarioSeed(BaseModel):
    ward_id: str = "dk-kodialbail"


class PulseSmsTestRequest(BaseModel):
    ward_id: str = "dk-kodialbail"
    confirm_test_send: bool = False


# ---------------------------------------------------------------------------
# JalaNetra Pulse Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/pulse/summary", tags=["pulse"])
def pulse_summary():
    """Real-time community water-outage detection summary across all wards."""
    return pulse.get_pulse_summary(_ward_states)


@app.get("/api/pulse/wards/{ward_id}", tags=["pulse"])
def pulse_ward_detail(ward_id: str):
    """Real-time pulse and incident timeline for a specific ward."""
    _get_ward_state(ward_id)  # validate ward exists
    return pulse.get_ward_pulse(ward_id)


@app.post("/api/pulse/reports", tags=["pulse"])
def pulse_submit_report(req: PulseReportCreate, request: Request):
    """
    Submit a real-time water status report.
    Enforces 30-minute deduplication and triggers 90-minute clustering engine.
    """
    # Use client provided reporter_key, or generate from request header/IP
    client_key = req.reporter_key or request.headers.get("x-reporter-key") or request.client.host if request.client else None
    try:
        res = pulse.add_water_report(
            ward_id=req.ward_id,
            status=req.status,
            reporter_key=client_key,
            phone=req.phone,
            source="live_user",
            simulation=False,
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=429, detail=str(val_err))


@app.get("/api/pulse/alerts", tags=["pulse"])
def pulse_list_alerts():
    """List active and recovery community water alerts."""
    with db.get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM community_alerts
               WHERE status IN ('active', 'recovery')
               ORDER BY latest_report_at DESC"""
        ).fetchall()
    alerts = []
    for r in rows:
        d = dict(r)
        d["simulation"] = bool(d["simulation"])
        d["recommended_actions"] = pulse.get_recommended_actions(d["status"])
        d["disclaimer"] = pulse.DISCLAIMER
        alerts.append(d)
    return {"alerts": alerts, "count": len(alerts), "disclaimer": pulse.DISCLAIMER}


@app.get("/api/pulse/alerts/{alert_id}", tags=["pulse"])
def pulse_get_alert(alert_id: int):
    """Get specific alert details and recent reports."""
    with db.get_db() as conn:
        row = conn.execute("SELECT * FROM community_alerts WHERE id = ?", (alert_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")
        d = dict(row)
        d["simulation"] = bool(d["simulation"])
        d["recommended_actions"] = pulse.get_recommended_actions(d["status"])
        d["disclaimer"] = pulse.DISCLAIMER

        reports = conn.execute(
            """SELECT id, status, reporter_key_hash, created_at, source, simulation
               FROM water_reports
               WHERE ward_id = ?
               ORDER BY created_at DESC LIMIT 20""",
            (d["ward_id"],),
        ).fetchall()
        d["associated_reports"] = [dict(r) for r in reports]
        return d


@app.post("/api/pulse/alerts/{alert_id}/resolve-report", tags=["pulse"])
def pulse_resolve_report(alert_id: int, req: PulseResolveReport, request: Request):
    """Submit a recovery report (water restored) for an open alert incident."""
    with db.get_db() as conn:
        row = conn.execute("SELECT * FROM community_alerts WHERE id = ?", (alert_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")
        ward_id = row["ward_id"]

    client_key = req.reporter_key or request.headers.get("x-reporter-key") or "resolver"
    try:
        res = pulse.add_water_report(
            ward_id=ward_id,
            status="restored",
            reporter_key=client_key,
            source="live_user",
            simulation=False,
        )
        return {"status": "recorded", "result": res}
    except ValueError as val_err:
        raise HTTPException(status_code=429, detail=str(val_err))


@app.post("/api/pulse/scenario/seed-outage", tags=["pulse-demo"])
def pulse_seed_outage(req: PulseScenarioSeed):
    """Demo scenario: Seed 3 independent 'no water' reports to activate Community Alert."""
    ws = _get_ward_state(req.ward_id)
    return pulse.seed_scenario_outage(ws["ward_id"])


@app.post("/api/pulse/scenario/seed-recovery", tags=["pulse-demo"])
def pulse_seed_recovery(req: PulseScenarioSeed):
    """Demo scenario: Seed 2 independent 'restored' reports to show Community Recovery."""
    ws = _get_ward_state(req.ward_id)
    return pulse.seed_scenario_recovery(ws["ward_id"])


@app.post("/api/pulse/scenario/reset", tags=["pulse-demo"])
def pulse_reset_scenario():
    """Reset all simulated/demo pulse records back to clean state."""
    return pulse.reset_scenario_data()


@app.post("/api/pulse/sms/test", tags=["pulse-sms"])
def pulse_test_sms(req: PulseSmsTestRequest):
    """
    Test transactional SMS dispatch.
    Safe by default: returns payload preview if SMS_LIVE_MODE is false.
    Only dispatches real SNS SMS if SMS_LIVE_MODE=true, confirm_test_send=true,
    and SMS_TEST_PHONE is configured.
    """
    ws = _get_ward_state(req.ward_id)
    return pulse.test_sms_dispatch(ws["display_name"], confirm_test_send=req.confirm_test_send)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url.path)},
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
