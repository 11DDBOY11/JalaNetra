"""
JalaNetra Data Pipeline - Schema Normalizer
Maps arbitrary CSV column names to the canonical JalaNetra schema.
All synthetic/sample data is explicitly labeled.
"""
from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical column names
# ---------------------------------------------------------------------------
GROUNDWATER_CANONICAL = [
    "observation_date",
    "station_id",
    "district",
    "groundwater_depth_m",
    "latitude",
    "longitude",
    "source",
]

RAINFALL_CANONICAL = [
    "observation_date",
    "district",
    "rainfall_mm",
    "source",
]

# ---------------------------------------------------------------------------
# Column alias maps — add more as real data is encountered
# ---------------------------------------------------------------------------
GW_ALIAS: dict[str, str] = {
    # canonical -> canonical (passthrough)
    "observation_date": "observation_date",
    "station_id": "station_id",
    "district": "district",
    "groundwater_depth_m": "groundwater_depth_m",
    "latitude": "latitude",
    "longitude": "longitude",
    "source": "source",
    # common alternative names from WRIS exports
    "date": "observation_date",
    "obs_date": "observation_date",
    "measurement_date": "observation_date",
    "data_acquisition_time": "observation_date",
    "well_id": "station_id",
    "well_no": "station_id",
    "station": "station_id",
    "state_district": "district",
    "depth": "groundwater_depth_m",
    "water_level_m": "groundwater_depth_m",
    "gwl_m": "groundwater_depth_m",
    "wl_m_bgl": "groundwater_depth_m",
    "groundwater_level_quarterly_manual_(meter)": "groundwater_depth_m",
    "groundwater_level_quarterly_manual_meter": "groundwater_depth_m",
    "groundwater_level_quarterly_manual": "groundwater_depth_m",
    "lat": "latitude",
    "lon": "longitude",
    "long": "longitude",
    "data_source": "source",
}

RAINFALL_ALIAS: dict[str, str] = {
    "observation_date": "observation_date",
    "district": "district",
    "rainfall_mm": "rainfall_mm",
    "source": "source",
    # common alternatives
    "date": "observation_date",
    "obs_date": "observation_date",
    "dist": "district",
    "district_name": "district",
    "rain_mm": "rainfall_mm",
    "rainfall": "rainfall_mm",
    "precip_mm": "rainfall_mm",
    "precipitation_mm": "rainfall_mm",
    "data_source": "source",
}


def _normalize_col(col: str) -> str:
    """Lowercase, strip, replace spaces/hyphens with underscores."""
    return col.strip().lower().replace(" ", "_").replace("-", "_")


def normalize_groundwater_df(df: pd.DataFrame, file_source: str = "unknown") -> tuple[pd.DataFrame, list[str]]:
    """
    Normalize a raw groundwater DataFrame to the canonical schema.
    Returns (normalized_df, list_of_warnings).
    """
    warnings: list[str] = []
    col_map = {}
    for col in df.columns:
        norm = _normalize_col(col)
        canonical = GW_ALIAS.get(norm)
        if canonical:
            col_map[col] = canonical
        else:
            warnings.append(f"Unrecognized column skipped: '{col}'")

    df = df.rename(columns=col_map)

    # Add missing columns with defaults
    for c in GROUNDWATER_CANONICAL:
        if c not in df.columns:
            df[c] = None
            warnings.append(f"Column '{c}' missing — filled with None")

    if "source" in df.columns and df["source"].isnull().all():
        df["source"] = file_source

    # Standardize district and filter for Dakshina Kannada if present
    if "district" in df.columns and df["district"].notna().any():
        df["district"] = df["district"].astype(str).str.strip()
        dk_mask = df["district"].str.lower().str.contains("dakshin", na=False)
        df.loc[dk_mask, "district"] = "Dakshina Kannada"
        dk_count = int(dk_mask.sum())
        if dk_count > 0:
            df = df[df["district"] == "Dakshina Kannada"].copy()
            warnings.append(f"Filtered to Dakshina Kannada district ({len(df)} records)")
        else:
            warnings.append("Dakshina Kannada not found in district column — keeping Karnataka baseline")

    # Type coercions (dayfirst=True handles DD-MM-YYYY dates from CGWB)
    try:
        df["observation_date"] = pd.to_datetime(df["observation_date"], dayfirst=True, errors="coerce")
    except Exception:
        warnings.append("Could not parse observation_date")

    df["groundwater_depth_m"] = pd.to_numeric(df["groundwater_depth_m"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Drop rows missing critical fields
    before = len(df)
    df = df.dropna(subset=["observation_date", "groundwater_depth_m"])
    dropped = before - len(df)
    if dropped:
        warnings.append(f"Dropped {dropped} rows missing date or depth")

    return df[GROUNDWATER_CANONICAL], warnings


def normalize_rainfall_df(df: pd.DataFrame, file_source: str = "unknown") -> tuple[pd.DataFrame, list[str]]:
    """
    Normalize a raw rainfall DataFrame to the canonical schema.
    Returns (normalized_df, list_of_warnings).
    """
    warnings: list[str] = []
    col_map = {}
    for col in df.columns:
        norm = _normalize_col(col)
        canonical = RAINFALL_ALIAS.get(norm)
        if canonical:
            col_map[col] = canonical
        else:
            warnings.append(f"Unrecognized column skipped: '{col}'")

    df = df.rename(columns=col_map)

    for c in RAINFALL_CANONICAL:
        if c not in df.columns:
            df[c] = None
            warnings.append(f"Column '{c}' missing — filled with None")

    if "source" in df.columns and df["source"].isnull().all():
        df["source"] = file_source

    try:
        df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    except Exception:
        warnings.append("Could not parse observation_date")

    df["rainfall_mm"] = pd.to_numeric(df["rainfall_mm"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["observation_date", "rainfall_mm"])
    dropped = before - len(df)
    if dropped:
        warnings.append(f"Dropped {dropped} rows missing date or rainfall")

    return df[RAINFALL_CANONICAL], warnings


def load_groundwater_csv(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """Load and normalize a groundwater CSV file."""
    df = pd.read_csv(path, low_memory=False)
    is_synthetic = "SYNTHETIC" in path.name.upper()
    file_source = "SYNTHETIC_SAMPLE" if is_synthetic else str(path.name)
    df_norm, warnings = normalize_groundwater_df(df, file_source=file_source)
    if is_synthetic:
        df_norm["source"] = "SYNTHETIC_SAMPLE"
    return df_norm, warnings


def load_rainfall_csv(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """Load and normalize a rainfall CSV file."""
    df = pd.read_csv(path)
    is_synthetic = "SYNTHETIC" in path.name.upper()
    file_source = "SYNTHETIC_SAMPLE" if is_synthetic else str(path.name)
    df_norm, warnings = normalize_rainfall_df(df, file_source=file_source)
    if is_synthetic:
        df_norm["source"] = "SYNTHETIC_SAMPLE"
    return df_norm, warnings


def build_data_quality_report(
    gw_df: pd.DataFrame,
    rainfall_df: pd.DataFrame,
    gw_warnings: list[str],
    rainfall_warnings: list[str],
) -> dict[str, Any]:
    has_synth_gw = gw_df.empty or bool(gw_df["source"].str.contains("SYNTHETIC", na=False).any())
    has_synth_rain = rainfall_df.empty or bool(rainfall_df["source"].str.contains("SYNTHETIC", na=False).any())

    if not has_synth_gw and not has_synth_rain:
        data_mode = "real_historical"
    elif not has_synth_gw or not has_synth_rain:
        data_mode = "hybrid"
    else:
        data_mode = "demo"

    gw_source_mode = "synthetic_fallback" if has_synth_gw else "real_historical"
    rain_source_mode = "synthetic_baseline" if has_synth_rain else "real_historical"
    estimate_mode = "demo_heuristic" if data_mode == "demo" else "model_assisted"

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "data_mode": data_mode,
        "synthetic": data_mode == "demo",
        "groundwater_source_mode": gw_source_mode,
        "rainfall_source_mode": rain_source_mode,
        "ward_estimate_mode": estimate_mode,
        "groundwater": {
            "rows": len(gw_df),
            "date_range": [
                str(gw_df["observation_date"].min().date()) if not gw_df.empty else None,
                str(gw_df["observation_date"].max().date()) if not gw_df.empty else None,
            ],
            "wells": int(gw_df["station_id"].nunique()) if not gw_df.empty else 0,
            "warnings": gw_warnings,
        },
        "rainfall": {
            "rows": len(rainfall_df),
            "date_range": [
                str(rainfall_df["observation_date"].min().date()) if not rainfall_df.empty else None,
                str(rainfall_df["observation_date"].max().date()) if not rainfall_df.empty else None,
            ],
            "warnings": rainfall_warnings,
        },
    }
