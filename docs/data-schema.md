# JalaNetra Data Schema & Real CGWB Dataset Specifications

## 1. Primary Groundwater Dataset Details
- **Exact File Name:** `gwl_manual_quarterly_cgwb_ka_1991_2020.csv`
- **Location:** `data/raw/groundwater/gwl_manual_quarterly_cgwb_ka_1991_2020.csv`
- **Origin Agency:** Central Ground Water Board (CGWB) / National Water Development Agency (NWIC)
- **Data Freshness Statement:**
  > **“Quarterly government observations (1996–2020); not live groundwater sensor data.”**

## 2. Row Counts & Spatial Filtering
- **Row count before filtering:** 104,781 rows (Entire State of Karnataka across 30 districts)
- **Filtering Column:** `District` (matched for case-insensitive `"Dakshin"`)
- **Row count after filtering:** **4,962 rows**
- **Unique Monitoring Stations in Dakshina Kannada:** **115 stations**
- **Date Range Detected:** `1996-01-05` to `2020-11-30` (Quarterly observations: Jan, May, Aug, Nov)

## 3. Actual Source Columns vs. Canonical JalaNetra Schema

| Source CSV Column Name | Canonical Schema Field | Data Type | Notes |
|---|---|---|---|
| `Data Acquisition Time` | `observation_date` | `datetime64[ns]` | Parsed with `dayfirst=True` (e.g. `05-01-2013 06:00`) |
| `Station` | `station_id` | `string` | Station/well name (e.g., `Surathkal`, `Kankanadi`, `Mangalore Lalbhag`) |
| `District` | `district` | `string` | Filtered and normalized to `Dakshina Kannada` |
| `Groundwater Level Quarterly Manual (meter)` | `groundwater_depth_m` | `float64` | Depth to water table below ground level in metres |
| `Latitude` | `latitude` | `float64` | Geodetic latitude (WGS84, e.g. `12.8694`) |
| `Longitude` | `longitude` | `float64` | Geodetic longitude (WGS84, e.g. `74.8792`) |
| *(File path)* | `source` | `string` | Stamped as `gwl_manual_quarterly_cgwb_ka_1991_2020.csv` |

### Additional CSV Attributes Present (Metadata Passthrough)
- `SlNo`: Numeric sequential identifier
- `Agency`: `CGWB`
- `State LGD Code`: `29` (Karnataka)
- `District LGD Code`: `531`
- `Tehsil` / `Block` / `Village` / `River` / `Basin` / `RL_MSL`

## 4. Ward Spatial Association in Mangaluru

| Ward ID | Ward Name | Predefined Coordinates | Associated CGWB Wells (Nearest) | Real Obs Count |
|---|---|---|---|---|
| `dk-kodialbail` | Kodialbail | 12.8700, 74.8800 | `Kankanadi`, `Padil` | 55 |
| `dk-kankanady` | Kankanady | 12.9100, 74.8600 | `Kankanadi`, `Padil`, `Kenjaru` | 81 |
| `dk-kadri` | Kadri | 12.8800, 74.8500 | `Mangalore Lalbhag`, `Mangalore Attawara`, `Mangalore Bandaru` | 77 |
| `dk-surathkal` | Surathkal | 13.0000, 74.7900 | `Surathkal`, `Mukka`, `Bala` | 148 |
| `dk-moodbidri` | Moodbidri | 12.9600, 74.9900 | `Garadi`, `Kinni Kambala`, `Perar` | 82 |

## 5. Synthetic Fallback Policy
- For wards without sufficient real local observations, synthetic seasonal benchmarks (`SEASONAL_BASELINE_DEPTH`) are used as fallback.
- In all API responses and UI panels, fallback values are clearly tagged with `"synthetic": true`.
- Real historical data is **never** presented as live real-time sensor streams; real historical records are marked with their true acquisition date and labeled as historical CGWB observations.

## 6. Stale-Data Guardrail Fields (`MAX_CURRENT_FORECAST_AGE_DAYS = 180`)
When a verified observation is older than 180 days:
- `forecast_current` (`boolean`): `false`
- `forecast_status` (`string`): `"historical_context_only"`
- `observation_age_days` (`integer`): Computed difference between `date.today()` and observation date
- `risk_level` (`string`): `"historical_context"`
- `days_to_dry_estimate` (`null`): Nullified to prevent false current alarms
- `book_tanker_by` (`null`): Nullified to prevent false tanker scheduling dates for historical records
- `recommended_action` (`string`): Guidance to record ground reports before making decisions

## 7. JalaNetra Pulse Real-Time Outage Entities

### `water_reports`
| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Autoincrement report ID |
| `ward_id` | `TEXT` | Target ward identifier (e.g. `dk-kodialbail`) |
| `status` | `TEXT` | `available` \| `low` \| `dry` \| `restored` |
| `reporter_key_hash` | `TEXT` | SHA-256 hash of anonymous client/device identity (16 chars) |
| `created_at` | `TEXT` | ISO-8601 UTC timestamp |
| `phone_hash` | `TEXT NULL` | Salted SHA-256 hash of optional phone number |
| `source` | `TEXT` | `live_user` \| `scenario_demo` |
| `simulation` | `INTEGER` | `0` for real user reports, `1` for demo scenarios |

### `community_alerts`
| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Alert incident identifier |
| `ward_id` | `TEXT` | Affected ward identifier |
| `status` | `TEXT` | `monitoring` \| `active` \| `recovery` |
| `severity` | `TEXT` | `watch` \| `high` \| `critical` |
| `independent_report_count` | `INTEGER` | Distinct reporters within rolling 90-minute window |
| `first_report_at` | `TEXT` | Timestamp of earliest contributing dry report |
| `latest_report_at` | `TEXT` | Timestamp of most recent dry report |
| `confidence` | `TEXT` | `moderate` (3 reports) \| `high` (4+ reports) |
| `trigger_reason` | `TEXT` | Human-readable explanation of cluster trigger |
| `simulation` | `INTEGER` | `1` if triggered exclusively by simulated scenario reports |

### `subscriptions`
| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Subscription ID |
| `ward_id` | `TEXT` | Target ward identifier |
| `phone_hash` | `TEXT` | Salted SHA-256 hash of subscriber phone |
| `notification_channel` | `TEXT` | `in_app` \| `sms` |
| `sms_verified` | `INTEGER` | `1` if verified in AWS SNS sandbox, `0` otherwise |
| `created_at` | `TEXT` | ISO-8601 UTC timestamp |
