"""
JalaNetra Ward State Builder
Builds per-ward water-stress state from normalized groundwater + rainfall data.
All synthetic values are explicitly labeled.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from backend.ingest.normalizer import (
    load_groundwater_csv,
    load_rainfall_csv,
    build_data_quality_report,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ward definitions for Mangaluru area
# ---------------------------------------------------------------------------
WARDS = [
    {
        "ward_id": "dk-kodialbail",
        "name": "Kodialbail",
        "display_name": "Kodialbail Ward",
        "latitude": 12.8700,
        "longitude": 74.8800,
        "population_approx": 18000,
        "area_sqkm": 3.2,
        "well_ids": ["Kankanadi", "Padil", "DK-WELL-001"],
    },
    {
        "ward_id": "dk-kankanady",
        "name": "Kankanady",
        "display_name": "Kankanady Ward",
        "latitude": 12.9100,
        "longitude": 74.8600,
        "population_approx": 22000,
        "area_sqkm": 4.1,
        "well_ids": ["Kankanadi", "Padil", "Kenjaru", "DK-WELL-002"],
    },
    {
        "ward_id": "dk-kadri",
        "name": "Kadri",
        "display_name": "Kadri Ward",
        "latitude": 12.8800,
        "longitude": 74.8500,
        "population_approx": 15000,
        "area_sqkm": 2.8,
        "well_ids": ["Mangalore Lalbhag", "Mangalore Attawara", "Mangalore Bandaru", "DK-WELL-003"],
    },
    {
        "ward_id": "dk-surathkal",
        "name": "Surathkal",
        "display_name": "Surathkal Ward",
        "latitude": 13.0000,
        "longitude": 74.7900,
        "population_approx": 19000,
        "area_sqkm": 5.6,
        "well_ids": ["Surathkal", "Mukka", "Bala", "DK-WELL-004"],
    },
    {
        "ward_id": "dk-moodbidri",
        "name": "Moodbidri",
        "display_name": "Moodbidri Ward",
        "latitude": 12.9600,
        "longitude": 74.9900,
        "population_approx": 12000,
        "area_sqkm": 7.2,
        "well_ids": ["Garadi", "Kinni Kambala", "Perar", "DK-WELL-005"],
    },
]

# Seasonal baseline groundwater depth (m) for Dakshina Kannada — synthetic reference
# Based on known monsoon recharge patterns: shallowest Aug, deepest Apr-May
SEASONAL_BASELINE_DEPTH: dict[int, float] = {
    1: 9.5,
    2: 10.2,
    3: 11.8,
    4: 13.1,
    5: 14.2,   # Pre-monsoon dry peak
    6: 10.1,
    7: 6.3,
    8: 5.0,    # Monsoon saturation low
    9: 5.8,
    10: 7.4,
    11: 8.6,
    12: 9.0,
}

# 7-day rainfall baseline (mm) — synthetic seasonal reference
SEASONAL_RAINFALL_7D: dict[int, float] = {
    1: 1.0, 2: 2.0, 3: 8.0, 4: 20.0, 5: 55.0,
    6: 280.0, 7: 310.0, 8: 230.0, 9: 120.0,
    10: 45.0, 11: 18.0, 12: 5.0,
}


def _get_ward_groundwater(ward: dict, gw_df: pd.DataFrame) -> dict[str, Any]:
    """Extract latest groundwater stats for a ward from its associated wells."""
    well_ids = ward.get("well_ids", [])
    ward_gw = gw_df[gw_df["station_id"].isin(well_ids)] if not gw_df.empty else pd.DataFrame()

    if ward_gw.empty:
        # No real data — use synthetic seasonal fallback
        month = date.today().month
        depth = SEASONAL_BASELINE_DEPTH[month] + (hash(ward["ward_id"]) % 30) / 10
        return {
            "groundwater_depth_m": round(depth, 2),
            "depth_observed_at": None,
            "depth_trend_m_per_month": None,
            "observations_count": 0,
            "synthetic": True,
            "groundwater_synthetic": True,
            "matched_station": None,
            "freshness_disclosure": "Synthetic seasonal fallback — no direct local government observation matched.",
            "data_age_days": None,
        }

    # Sort by date, get most recent
    ward_gw = ward_gw.sort_values("observation_date")
    latest = ward_gw.iloc[-1]
    latest_date = latest["observation_date"].date() if hasattr(latest["observation_date"], "date") else None
    data_age_days = (date.today() - latest_date).days if latest_date else None

    # Trend: slope of depth over last 2 observations
    trend = None
    if len(ward_gw) >= 2:
        prev = ward_gw.iloc[-2]
        days_diff = (
            (latest["observation_date"] - prev["observation_date"]).days
            if hasattr(latest["observation_date"], "days")
            else 30
        )
        if days_diff and days_diff > 0:
            depth_diff = float(latest["groundwater_depth_m"]) - float(prev["groundwater_depth_m"])
            trend = round(depth_diff / days_diff * 30, 3)  # per month

    is_synthetic = "SYNTHETIC" in str(latest.get("source", "")).upper()
    station_matched = str(latest["station_id"]) if not is_synthetic else None
    freshness = (
        "Historical quarterly government groundwater observations; not live groundwater sensor data."
        if not is_synthetic else "Synthetic seasonal fallback — no direct local government observation matched."
    )
    return {
        "groundwater_depth_m": round(float(latest["groundwater_depth_m"]), 2),
        "depth_observed_at": str(latest_date) if latest_date else None,
        "depth_trend_m_per_month": trend,
        "observations_count": len(ward_gw),
        "synthetic": is_synthetic,
        "groundwater_synthetic": is_synthetic,
        "matched_station": station_matched,
        "freshness_disclosure": freshness,
        "data_age_days": data_age_days,
    }


def _get_ward_rainfall(rainfall_df: pd.DataFrame) -> dict[str, Any]:
    """Get recent rainfall stats from district-level data."""
    if rainfall_df.empty:
        month = date.today().month
        return {
            "rainfall_7d_mm": round(SEASONAL_RAINFALL_7D[month] / 4, 1),
            "rainfall_30d_mm": round(SEASONAL_RAINFALL_7D[month], 1),
            "seasonal_baseline_7d_mm": SEASONAL_RAINFALL_7D[month] / 4,
            "synthetic": True,
        }

    df = rainfall_df.sort_values("observation_date")
    cutoff_7d = pd.Timestamp(date.today() - timedelta(days=7))
    cutoff_30d = pd.Timestamp(date.today() - timedelta(days=30))

    rain_7d = df[df["observation_date"] >= cutoff_7d]["rainfall_mm"].sum()
    rain_30d = df[df["observation_date"] >= cutoff_30d]["rainfall_mm"].sum()

    month = date.today().month
    baseline = SEASONAL_RAINFALL_7D[month]
    is_synthetic = "SYNTHETIC" in df["source"].str.upper().values.tolist()[0] if not df.empty else True

    return {
        "rainfall_7d_mm": round(float(rain_7d), 1),
        "rainfall_30d_mm": round(float(rain_30d), 1),
        "seasonal_baseline_7d_mm": baseline,
        "synthetic": is_synthetic,
    }


def _build_groundwater_series(ward: dict, gw_df: pd.DataFrame) -> list[dict]:
    """Build time-series for chart rendering."""
    well_ids = ward.get("well_ids", [])
    ward_gw = gw_df[gw_df["station_id"].isin(well_ids)] if not gw_df.empty else pd.DataFrame()

    if ward_gw.empty:
        # Generate synthetic series for the past 9 months
        series = []
        today = date.today()
        for i in range(9, -1, -1):
            obs_date = today.replace(day=1) - timedelta(days=30 * i)
            month = obs_date.month
            base = SEASONAL_BASELINE_DEPTH[month]
            noise = ((hash(ward["ward_id"] + str(i)) % 20) - 10) / 10
            series.append({
                "date": str(obs_date),
                "depth_m": round(base + noise, 2),
                "synthetic": True,
            })
        return series

    grouped = ward_gw.groupby("observation_date")["groundwater_depth_m"].mean().reset_index()
    is_synthetic = "SYNTHETIC" in str(ward_gw["source"].iloc[0]).upper() if not ward_gw.empty else True
    return [
        {
            "date": str(row["observation_date"].date()),
            "depth_m": round(float(row["groundwater_depth_m"]), 2),
            "synthetic": is_synthetic,
        }
        for _, row in grouped.iterrows()
    ]


def _build_rainfall_series(rainfall_df: pd.DataFrame) -> list[dict]:
    """Build rainfall time-series for chart rendering."""
    if rainfall_df.empty:
        series = []
        today = date.today()
        for i in range(9, -1, -1):
            obs_date = today.replace(day=1) - timedelta(days=30 * i)
            month = obs_date.month
            base = SEASONAL_RAINFALL_7D[month]
            noise = ((hash(str(i)) % 20) - 10) * 2
            series.append({
                "date": str(obs_date),
                "rainfall_mm": round(max(0.0, base + noise), 1),
                "synthetic": True,
            })
        return series

    df = rainfall_df.sort_values("observation_date")
    is_synthetic = "SYNTHETIC" in df["source"].str.upper().values.tolist()[0] if not df.empty else True
    return [
        {
            "date": str(row["observation_date"].date()),
            "rainfall_mm": round(float(row["rainfall_mm"]), 1),
            "synthetic": is_synthetic,
        }
        for _, row in df.iterrows()
    ]


def build_all_ward_states(
    gw_df: pd.DataFrame,
    rainfall_df: pd.DataFrame,
    data_mode: str = "demo",
) -> list[dict[str, Any]]:
    """
    Build ward-state records for all defined wards.
    Returns a list of ward state dicts.
    """
    rainfall_stats = _get_ward_rainfall(rainfall_df)
    rainfall_series = _build_rainfall_series(rainfall_df)

    ward_states = []
    for ward in WARDS:
        gw_stats = _get_ward_groundwater(ward, gw_df)
        gw_series = _build_groundwater_series(ward, gw_df)

        # Ward synthetic flag is false if groundwater depth comes from verified CGWB rows,
        # true only if that ward has no matched real source observation.
        is_synth = bool(gw_stats.get("synthetic", False))
        state: dict[str, Any] = {
            **ward,
            **gw_stats,
            **{f"rainfall_{k}": v for k, v in rainfall_stats.items() if k != "synthetic"},
            "rainfall_synthetic": bool(rainfall_stats["synthetic"]),
            "data_mode": data_mode,
            "synthetic": is_synth,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "groundwater_series": gw_series,
            "rainfall_series": rainfall_series,
        }
        ward_states.append(state)

    return ward_states


def load_or_generate_ward_states(
    gw_path: Path | None = None,
    rainfall_path: Path | None = None,
    output_path: Path | None = None,
) -> tuple[list[dict], dict]:
    """
    Load real data if available, else use synthetic samples.
    Always writes output to data/demo/ward_state.json.
    Returns (ward_states, quality_report).
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    sample_dir = project_root / "data" / "sample"
    raw_gw_dir = project_root / "data" / "raw" / "groundwater"
    raw_rain_dir = project_root / "data" / "raw" / "rainfall"
    output_path = output_path or project_root / "data" / "demo" / "ward_state.json"

    # Discover real data files
    real_gw_files = sorted(raw_gw_dir.glob("*.csv")) if raw_gw_dir.exists() else []
    real_rain_files = sorted(raw_rain_dir.glob("*.csv")) if raw_rain_dir.exists() else []

    all_gw_warnings: list[str] = []
    all_rain_warnings: list[str] = []

    if real_gw_files:
        gw_dfs = []
        for f in real_gw_files:
            df, warns = load_groundwater_csv(f)
            gw_dfs.append(df)
            all_gw_warnings.extend(warns)
        gw_df = pd.concat(gw_dfs, ignore_index=True)
        has_real_gw = True
    else:
        synthetic_gw = sample_dir / "SYNTHETIC_groundwater_sample.csv"
        gw_df, all_gw_warnings = load_groundwater_csv(synthetic_gw)
        has_real_gw = False

    if real_rain_files:
        rain_dfs = []
        for f in real_rain_files:
            df, warns = load_rainfall_csv(f)
            rain_dfs.append(df)
            all_rain_warnings.extend(warns)
        rainfall_df = pd.concat(rain_dfs, ignore_index=True)
        has_real_rain = True
    else:
        synthetic_rain = sample_dir / "SYNTHETIC_rainfall_sample.csv"
        rainfall_df, r_warns = load_rainfall_csv(synthetic_rain)
        all_rain_warnings.extend(r_warns)
        has_real_rain = False

    # Determine honest data mode
    if has_real_gw and has_real_rain:
        data_mode = "real_historical"
    elif has_real_gw or has_real_rain:
        data_mode = "hybrid"
    else:
        data_mode = "demo"

    quality_report = build_data_quality_report(gw_df, rainfall_df, all_gw_warnings, all_rain_warnings)

    ward_states = build_all_ward_states(gw_df, rainfall_df, data_mode=data_mode)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "data_mode": data_mode,
                "synthetic": data_mode == "demo",
                "groundwater_source_mode": "real_historical" if has_real_gw else "synthetic_fallback",
                "rainfall_source_mode": "real_historical" if has_real_rain else "synthetic_baseline",
                "ward_estimate_mode": "model_assisted" if data_mode != "demo" else "demo_heuristic",
                "wards": ward_states,
                "quality_report": quality_report,
            },
            f, indent=2, default=str
        )
    logger.info("Ward state written to %s (mode=%s)", output_path, data_mode)

    return ward_states, quality_report
