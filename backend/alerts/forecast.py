"""
JalaNetra Risk / Forecast Engine
Rule-based, transparent heuristic. No black-box ML.
Confidence is explicitly reduced when data is sparse, old, or synthetic.
Never implies certainty. Never fabricates values.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# Risk level thresholds (groundwater depth in metres below ground level)
# Greater depth = water table is lower = worse situation
# ---------------------------------------------------------------------------
# Depth-based decision support bands (metres below ground level)
DEPTH_THRESHOLDS = {
    "low": 8.0,        # < 8 m depth: relatively shallow
    "moderate": 8.0,   # 8–11 m: moderate stress
    "high": 11.0,      # 11–14 m: high stress
    "critical": 14.0,  # >= 14 m: elevated water stress
}

# Configurable demonstration water-stress threshold (16 m depth-below-ground-level).
# It is a decision-support parameter, not a universal official dry-well standard.
CONFIGURABLE_WATER_STRESS_THRESHOLD_M = 16.0
CRITICAL_DEPTH_M = CONFIGURABLE_WATER_STRESS_THRESHOLD_M

# Configurable stale-data guardrail threshold: observations older than 180 days
# cannot produce a current household water forecast.
MAX_CURRENT_FORECAST_AGE_DAYS = 180

# Seasonal monsoon flag: June–September
MONSOON_MONTHS = {6, 7, 8, 9}

# Post-monsoon recharge months: October–November
RECHARGE_MONTHS = {10, 11}


def _classify_risk(depth_m: float, trend_m_per_month: float | None) -> str:
    """Classify risk level from groundwater depth and trend."""
    if depth_m >= DEPTH_THRESHOLDS["critical"]:
        base = "critical"
    elif depth_m >= DEPTH_THRESHOLDS["high"]:
        base = "high"
    elif depth_m >= DEPTH_THRESHOLDS["moderate"]:
        base = "moderate"
    else:
        base = "low"

    # Worsen one level if strongly declining trend (> 0.5 m/month deepening)
    if trend_m_per_month is not None and trend_m_per_month > 0.5:
        if base == "low":
            base = "moderate"
        elif base == "moderate":
            base = "high"
        elif base == "high":
            base = "critical"

    return base


def _estimate_days_to_dry(
    depth_m: float,
    trend_m_per_month: float | None,
    rainfall_7d_mm: float,
    month: int,
) -> int | None:
    """
    Estimate days until water level reaches CRITICAL_DEPTH_M.
    Returns None when confidence is too low.
    """
    headroom = CRITICAL_DEPTH_M - depth_m
    if headroom <= 0:
        return 0

    # Monthly deepening rate: use trend if available, else seasonal heuristic
    if trend_m_per_month is not None and trend_m_per_month > 0:
        rate = trend_m_per_month
    elif month in MONSOON_MONTHS:
        rate = -0.5  # water table rising during monsoon
    elif month in RECHARGE_MONTHS:
        rate = 0.2   # slight deepening as recharge slows
    else:
        rate = 0.8   # dry season deepening

    # Rainfall modifier: above-average rain slows depletion
    seasonal_7d = {
        1: 0.3, 2: 0.5, 3: 2.0, 4: 5.0, 5: 14.0,
        6: 70.0, 7: 77.5, 8: 57.5, 9: 30.0,
        10: 11.0, 11: 4.5, 12: 1.25,
    }
    baseline = seasonal_7d.get(month, 10.0)
    if rainfall_7d_mm > baseline * 1.5:
        rate = max(0.1, rate * 0.5)

    if rate <= 0:
        return 180  # Rising water table — no dry-out risk soon

    days = int((headroom / rate) * 30)
    return min(days, 365)


def _compute_confidence(
    data_age_days: int | None,
    observations_count: int,
    is_synthetic: bool,
    trend_available: bool,
) -> str:
    """Compute confidence level based on data quality."""
    if is_synthetic:
        return "low"
    if data_age_days is None or data_age_days > 180:
        return "low"
    if observations_count < 2:
        return "low"
    if data_age_days > 60 or not trend_available:
        return "medium"
    return "high"


def _build_explanation(
    ward_name: str,
    depth_m: float,
    trend: float | None,
    rainfall_7d_mm: float,
    is_synthetic: bool,
    data_age_days: int | None,
    month: int,
    citizen_dry_report: bool = False,
) -> str:
    """Build a plain-English explanation of the forecast."""
    parts = []

    if is_synthetic:
        parts.append(
            "⚠️ Demo mode: values below are based on synthetic seasonal patterns, "
            "not live sensor readings."
        )

    # Depth context
    if depth_m < 6:
        parts.append(
            f"Groundwater depth is {depth_m:.1f} m — relatively shallow, "
            "indicating good monsoon recharge."
        )
    elif depth_m < 11:
        parts.append(
            f"Groundwater depth is {depth_m:.1f} m, within a moderate range "
            "for this season in Dakshina Kannada."
        )
    else:
        parts.append(
            f"Groundwater depth is {depth_m:.1f} m below ground level — "
            "deeper than average, indicating reduced aquifer storage."
        )

    # Trend context
    if trend is not None:
        direction = "deepening" if trend > 0 else "recovering"
        parts.append(
            f"The water table is {direction} at {abs(trend):.2f} m/month "
            "based on recent observations."
        )
    else:
        parts.append(
            "Trend data is unavailable (only one observation on record); "
            "confidence is low."
        )

    # Rainfall context
    if month in MONSOON_MONTHS:
        if rainfall_7d_mm > 50:
            parts.append(
                f"Recent 7-day rainfall of {rainfall_7d_mm:.0f} mm is typical for "
                "southwest monsoon — aquifer recharge is ongoing."
            )
        else:
            parts.append(
                f"7-day rainfall of {rainfall_7d_mm:.0f} mm is below monsoon baseline — "
                "recharge may be slower than usual."
            )
    else:
        if rainfall_7d_mm < 5:
            parts.append(
                f"Rainfall in the last 7 days is {rainfall_7d_mm:.1f} mm — "
                "dry-season conditions; groundwater is the primary source."
            )
        else:
            parts.append(
                f"Rainfall in the last 7 days is {rainfall_7d_mm:.1f} mm, "
                "providing limited recharge outside the monsoon window."
            )

    # Data age warning
    if data_age_days and data_age_days > 60:
        parts.append(
            f"Note: The most recent government observation is {data_age_days} days old "
            "(CGWB wells are typically measured quarterly)."
        )

    # Citizen report
    if citizen_dry_report:
        parts.append(
            "A citizen in this ward recently reported no water supply. "
            "This raises alert urgency."
        )

    return " ".join(parts)


def compute_forecast(
    ward_state: dict[str, Any],
    citizen_reports: list[dict] | None = None,
    scenario: str | None = None,
) -> dict[str, Any]:
    """
    Compute a risk forecast for a single ward.
    
    If the latest observation is older than MAX_CURRENT_FORECAST_AGE_DAYS (180 days),
    applies a strict stale-data guardrail:
    - risk_level = "historical_context"
    - forecast_status = "historical_context_only"
    - forecast_current = False
    - days_to_dry_estimate = None
    - weeks_to_dry = None
    - book_tanker_by = None
    - confidence = "low"
    
    Parameters
    ----------
    ward_state : dict from ward_builder.build_all_ward_states()
    citizen_reports : list of recent citizen report dicts for this ward
    scenario : optional hypothetical signal ('dry', 'low', 'normal') for what-if simulation
    """
    today = date.today()
    month = today.month

    depth_m = ward_state.get("groundwater_depth_m", 10.0) or 10.0
    trend = ward_state.get("depth_trend_m_per_month")
    rainfall_7d = ward_state.get("rainfall_rainfall_7d_mm") or ward_state.get("rainfall_7d_mm") or 0.0
    is_synthetic = ward_state.get("synthetic", True)
    data_age_days = ward_state.get("data_age_days")
    obs_date_str = str(ward_state.get("depth_observed_at") or "")
    if data_age_days is None and obs_date_str:
        try:
            obs_d = datetime.strptime(obs_date_str[:10], "%Y-%m-%d").date()
            data_age_days = (today - obs_d).days
        except Exception:
            pass

    obs_count = ward_state.get("observations_count", 0)
    ward_name = ward_state.get("name", "this ward")
    data_mode = ward_state.get("data_mode", "demo")

    # 1. SCENARIO SIMULATION MODE
    if scenario in ("dry", "low", "normal"):
        scenario_map = {
            "dry": ("critical", 7, 1, 3),
            "low": ("moderate", 21, 3, 14),
            "normal": ("low", 90, 13, None),
        }
        s_risk, s_days, s_weeks, book_delay = scenario_map[scenario]
        book_tanker_by = str(today + timedelta(days=book_delay)) if book_delay else None
        return {
            "ward_id": ward_state.get("ward_id"),
            "ward_name": ward_name,
            "risk_level": s_risk,
            "forecast_status": "scenario_simulation",
            "forecast_current": False,
            "is_scenario_simulation": True,
            "scenario_selected": scenario,
            "observation_age_days": data_age_days,
            "days_to_dry_estimate": s_days,
            "weeks_to_dry": s_weeks,
            "book_tanker_by": book_tanker_by,
            "confidence": "low",
            "explanation": f"Scenario simulation — based on your selected hypothetical '{scenario}' water report, not a live groundwater reading.",
            "recommended_action": f"Scenario simulation — based on your selected current water report, not a live groundwater reading. {'Consider booking a tanker by ' + book_tanker_by + ' as a precautionary drill.' if book_tanker_by else 'Household supply assumed stable under this scenario.'}",
            "groundwater_depth_m": round(depth_m, 2),
            "depth_trend_m_per_month": trend,
            "rainfall_7d_mm": float(rainfall_7d),
            "forecast_series": _generate_forecast_series(depth_m, trend, month, days=60),
            "model": "scenario-what-if-v1",
            "data_mode": data_mode,
            "synthetic": is_synthetic,
            "computed_at": datetime.utcnow().isoformat() + "Z",
            "citizen_dry_report": (scenario == "dry"),
            "scenario_label": "Scenario simulation — based on your selected current water report, not a live groundwater reading.",
        }

    # 2. STALE-DATA GUARDRAIL: Latest observation older than MAX_CURRENT_FORECAST_AGE_DAYS
    is_stale = (data_age_days is not None and data_age_days > MAX_CURRENT_FORECAST_AGE_DAYS)

    if is_stale:
        obs_label = obs_date_str if obs_date_str else "historical government records"
        return {
            "ward_id": ward_state.get("ward_id"),
            "ward_name": ward_name,
            "risk_level": "historical_context",
            "forecast_status": "historical_context_only",
            "forecast_current": False,
            "is_scenario_simulation": False,
            "observation_age_days": data_age_days,
            "days_to_dry_estimate": None,
            "weeks_to_dry": None,
            "book_tanker_by": None,
            "confidence": "low",
            "explanation": (
                f"The latest verified CGWB groundwater observation for this matched station is from {obs_label}. "
                "It is useful for historical context but too old for a current household water forecast."
            ),
            "recommended_action": (
                "This record is historical. Report today’s water availability or connect a recent "
                "ward measurement before making a tanker-booking decision."
            ),
            "groundwater_depth_m": round(depth_m, 2),
            "depth_trend_m_per_month": trend,
            "rainfall_7d_mm": float(rainfall_7d),
            "forecast_series": _generate_forecast_series(depth_m, trend, month, days=60),
            "model": "historical-context-v1",
            "data_mode": data_mode,
            "synthetic": is_synthetic,
            "computed_at": datetime.utcnow().isoformat() + "Z",
            "citizen_dry_report": False,
        }

    # 3. FRESH ACTIVE FORECAST (< 180 days)
    # Check citizen reports
    citizen_dry = False
    if citizen_reports:
        recent = [
            r for r in citizen_reports
            if r.get("status") == "dry"
            and _is_recent(r.get("created_at"), days=7)
        ]
        citizen_dry = len(recent) > 0

    # Risk classification
    risk_level = _classify_risk(depth_m, trend)
    if citizen_dry and risk_level in ("low", "moderate"):
        risk_level = "high"

    days_to_dry = _estimate_days_to_dry(depth_m, trend, float(rainfall_7d), month)
    weeks_to_dry = round(days_to_dry / 7) if days_to_dry is not None else None
    if days_to_dry is not None and days_to_dry > 0:
        alert_trigger_days = max(3, days_to_dry - 7)
        book_by = today + timedelta(days=alert_trigger_days)
        book_tanker_by = str(book_by)
    else:
        book_tanker_by = str(today + timedelta(days=3)) if days_to_dry == 0 else None

    confidence = _compute_confidence(data_age_days, obs_count, is_synthetic, trend is not None)
    explanation = _build_explanation(
        ward_name, depth_m, trend, float(rainfall_7d),
        is_synthetic, data_age_days, month, citizen_dry
    )
    recommended_action = _build_recommended_action(
        risk_level, days_to_dry, book_tanker_by, confidence, is_synthetic
    )
    series = _generate_forecast_series(depth_m, trend, month, days=60)

    return {
        "ward_id": ward_state.get("ward_id"),
        "ward_name": ward_name,
        "risk_level": risk_level,
        "forecast_status": "current_active",
        "forecast_current": True,
        "is_scenario_simulation": False,
        "observation_age_days": data_age_days,
        "days_to_dry_estimate": days_to_dry,
        "weeks_to_dry": weeks_to_dry,
        "book_tanker_by": book_tanker_by,
        "confidence": confidence,
        "explanation": explanation,
        "recommended_action": recommended_action,
        "groundwater_depth_m": round(depth_m, 2),
        "depth_trend_m_per_month": trend,
        "rainfall_7d_mm": float(rainfall_7d),
        "forecast_series": series,
        "model": "rule-based-heuristic-v1",
        "data_mode": data_mode,
        "synthetic": is_synthetic,
        "computed_at": datetime.utcnow().isoformat() + "Z",
        "citizen_dry_report": citizen_dry,
    }


def _is_recent(ts_str: str | None, days: int = 7) -> bool:
    """Check if a timestamp string is within the last N days."""
    if not ts_str:
        return False
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return (datetime.utcnow() - ts.replace(tzinfo=None)).days <= days
    except Exception:
        return False


def _build_recommended_action(
    risk_level: str,
    days_to_dry: int | None,
    book_tanker_by: str | None,
    confidence: str,
    is_synthetic: bool,
) -> str:
    """Generate a plain-language recommended household action."""
    prefix = "[Demo mode — synthetic data] " if is_synthetic else ""
    uncertainty = " Note: confidence is low due to data limitations." if confidence == "low" else ""

    if risk_level == "critical":
        return (
            f"{prefix}⛔ Critical water stress. Contact your ward office immediately. "
            f"Book an emergency water tanker now.{uncertainty}"
        )
    elif risk_level == "high":
        d = f" by {book_tanker_by}" if book_tanker_by else ""
        return (
            f"{prefix}🚨 High water stress likely in approximately "
            f"{days_to_dry or '?'} days. Book a water tanker{d}.{uncertainty}"
        )
    elif risk_level == "moderate":
        d = f" by {book_tanker_by}" if book_tanker_by else ""
        return (
            f"{prefix}⚠️ Moderate stress expected. Monitor your supply. "
            f"Pre-book a tanker{d} as a precaution.{uncertainty}"
        )
    else:
        return (
            f"{prefix}✅ Water supply appears stable for now. "
            f"No immediate action needed. Stay informed.{uncertainty}"
        )


def _generate_forecast_series(
    current_depth: float,
    trend: float | None,
    month: int,
    days: int = 60,
) -> list[dict]:
    """Simple linear extrapolation for forecast chart."""
    rate_per_day = (trend or 0.5) / 30
    today = date.today()
    series = []
    for i in range(0, days, 7):
        forecast_date = today + timedelta(days=i)
        predicted = current_depth + rate_per_day * i
        series.append({
            "date": str(forecast_date),
            "predicted_depth_m": round(max(0.0, predicted), 2),
            "synthetic": True,  # Forecast is always extrapolated
        })
    return series
