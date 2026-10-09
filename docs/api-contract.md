# JalaNetra API Contract v1
All endpoints via API Gateway -> Lambda. JSON only. CORS: allow Amplify domain.

## GET /api/wards
Response: { "wards": [ {
  "ward_id": "dk-mangaluru-w12",
  "name": "Ward 12 - Kodialbail",
  "groundwater_depth_m": 12.4,
  "depth_observed_at": "2026-05-20",      # WRIS observation date (state honestly)
  "rainfall_7d_mm": 41.2,
  "days_to_dry_estimate": 21,             # null when confidence low
  "book_tanker_by": "2026-10-24",         # the headline output
  "confidence": "medium"                   # low|medium|high
} ] }

## GET /api/forecast?ward_id=...
Response: { "ward_id": "...", "series": [ { "date": "2026-10-15", "predicted_depth_m": 12.6 } ],
  "weeks_to_dry": 3, "model": "gbr-baseline", "trained_on": "wris-wells+imd-rainfall" }

## POST /api/reports
Request: { "ward_id": "...", "status": "came|low|dry", "tanker_booked": false, "phone": "+91..." }
Response: 201 { "ok": true, "received_at": "..." }

## GET /api/reports?ward_id=...
Response: { "reports": [ { "status": "dry", "ts": "...", "tanker_booked": false } ] }

## POST /api/alerts/subscribe
Request: { "phone": "+91...", "language": "en-IN|hi-IN", "ward_ids": ["..."] }
Response: 201 { "ok": true }

Notes:
- DynamoDB tables: ward_state (pk ward_id), citizen_reports (pk ward_id, sk ts),
  alert_subscriptions (pk phone).
- Any simulated/synthetic value must carry "synthetic": true in the JSON.
