# JalaNetra Data Notes & Real Dataset Audit
Freshness MUST be stated honestly in the demo (organizers explicitly reward this).

## 1. Verified Real Groundwater Dataset
- **Exact File Name:** `gwl_manual_quarterly_cgwb_ka_1991_2020.csv`
- **Location:** `data/raw/groundwater/gwl_manual_quarterly_cgwb_ka_1991_2020.csv`
- **Origin Agency:** Central Ground Water Board (CGWB) via NWDP / NWIC portal
- **Data Freshness Statement:**
  > **“Quarterly government observations; not live groundwater sensor data.”**
  CGWB national observation wells are measured ~4 times per year (January post-monsoon, May pre-monsoon, August peak monsoon, November post-monsoon).

### Ingestion Audit & Row Counts
- **Total Rows in File:** 104,781 rows (covering 30 Karnataka districts)
- **District Column Found:** `District` (contains `"Dakshin Kannada"`)
- **Row Count After Filtering for Dakshina Kannada:** **4,962 rows**
- **Unique Wells / Stations in Dakshina Kannada:** **115 stations**
- **Date Range Detected:** `1996-01-05` to `2020-11-30`

### Actual Source Columns Identified
- `SlNo`: Observation record index
- `Station`: Well station name (e.g. `Surathkal`, `Kankanadi`, `Mangalore Lalbhag`, `Padil`, `Mukka`, `Bala`, `Garadi`)
- `Agency`: `CGWB`
- `District`: `Dakshin Kannada` (mapped to canonical `Dakshina Kannada`)
- `Latitude`: Decimal degrees (e.g. `12.9944`, `12.8694`)
- `Longitude`: Decimal degrees (e.g. `74.8000`, `74.8792`)
- `Data Acquisition Time`: DD-MM-YYYY HH:MM (e.g. `05-01-2013 06:00`) -> mapped to canonical `observation_date`
- `Groundwater Level Quarterly Manual (meter)`: Float -> mapped to canonical `groundwater_depth_m`

## 2. IMD Rainfall Data
- Coastal Karnataka annual rainfall average: ~3,800 mm.
- Real precipitation baselines calibrated to historical seasonal curves (monsoon peak in July at ~800-1,000 mm/month; dry post-monsoon trough in January-April at <10 mm/month).
- If real IMD daily station API exports are pending or IP-restricted, synthetic seasonal samples in `data/sample/SYNTHETIC_rainfall_sample.csv` are used with `"synthetic": true`.

## 3. Data Honesty & Provenance Principles
- Real historical data is **never** presented as live streaming sensor data.
- The UI and API clearly distinguish between historical government quarterly observations and simulated real-time edge telemetry.
- Where a ward has insufficient historical well coverage, the deterministic seasonal model fills gaps and labels them as synthetic.
