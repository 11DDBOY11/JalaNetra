#!/usr/bin/env bash
# JalaNetra repo bootstrap — run from repo root: bash bootstrap.sh
set -e

mkdir -p backend/ingest backend/alerts backend/reports ml edge infra web docs data/raw .antigravity/knowledge

cat > .gitignore <<'EOF'
__pycache__/
*.pyc
.venv/
venv/
node_modules/
dist/
.env
*.pem
*.crt
*.key
edge/certs/
edge/.env
ml/artifacts/
.amplify/
.aws-sam/
cdk.out/
*.pkl
.DS_Store
EOF

cat > .env.example <<'EOF'
# Copy to .env and fill in. NEVER commit .env.
AWS_REGION=ap-south-1
DATA_GOV_IN_KEY=your_data_gov_in_api_key
IMD_API_KEY=your_imd_api_key
IMD_JWT_TOKEN=your_imd_jwt_token
S3_BUCKET=jalanetra-raw-<yourname>
WARD_TABLE=ward_state
SUBSCRIPTION_TABLE=alert_subscriptions
REPORTS_TABLE=citizen_reports
EOF

cat > README.md <<'EOF'
# JalaNetra
Mangaluru water-security early warning system — Environmental Hacks (WeMakeDevs x AWS), Heat & Water track.

India's rainiest coast is running out of water. JalaNetra fuses India WRIS groundwater data,
IMD rainfall, citizen water reports, and a simulated edge node (AWS IoT Greengrass v2 in
Docker) into one actionable alert: "Your ward's tank runs dry in ~3 weeks — book the tanker
by <date>."

See docs/ARCHITECTURE.md and docs/demo-script.md. Setup: cp .env.example .env, fill keys,
then see backend/README.md and web/README.md.
EOF

cat > docs/api-contract.md <<'EOF'
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
EOF

cat > docs/data-notes.md <<'EOF'
# Data Sources — verify before agents build ingestion
Freshness MUST be stated honestly in the demo (organizers explicitly reward this).

## India WRIS (no API key needed)
- API catalog (Swagger): https://indiawris.gov.in/swagger-ui/index.html — has a Ground Water
  Level dataset endpoint. Try it first for Dakshina Kannada wells.
- Manual fallback (guaranteed to work tonight): DataDownload module
  https://indiawris.gov.in/wris/#/DataDownload -> Groundwater Level -> station-wise,
  one year at a time. Save CSV to data/raw/groundwater/.
- HONEST CADESNCE NOTE: CGWB national observation wells are measured ~4x/year
  (Jan, Mar-May, Aug, Nov). Say "quarterly government observations" in the demo,
  not "monthly". Karnataka state wells may be denser — check what the data shows.

## IMD district rainfall (needs account)
- Portal: https://api.imd.gov.in — register, generate a DEV API key (bound to your
  laptop's public IP!) and a JWT token.
- District-wise rainfall: GET https://api.imd.gov.in/api/v1/districtrainfall
  (find Dakshina Kannada's id from the portal's Try API console).
- PROBLEM TO KNOW: IMD keys are bound to a static public IP — a deployed Lambda has
  dynamic IPs. Plan: use IMD API from laptop/dev for the demo pull, OR use a
  data.gov.in rainfall resource instead.
- data.gov.in alternative: register at data.gov.in, generate API key in My Account,
  find a "district rainfall" resource ID (36-char) and call
  https://api.data.gov.in/resource/<id>?api-key=...&format=json

## Tonight's success criterion
At least ONE groundwater CSV and ONE rainfall CSV in data/raw/ with columns you
understand. Put a short note of the actual columns in this file.
EOF

cat > .antigravity/knowledge/PROJECT.md <<'EOF'
JalaNetra is a water-security early-warning system for Mangaluru, Karnataka, built for the
WeMakeDevs x AWS "Environmental Hacks" hackathon (Heat & Water track), deadline Sunday
Oct 11, 2026. Core loop: India WRIS groundwater + IMD rainfall + citizen water reports +
laptop edge node (Greengrass v2 in Docker, SIMULATED telemetry — no Jetson hardware) ->
per-ward forecast -> actionable alerts (SNS SMS + Polly voice notes) + React app on Amplify.
Judging priority: what CHANGES for a person — demo must show a household receiving a
"book your tanker by <date>" alert in time. Never fabricate data; label synthetic/simulated
data explicitly. All infra in AWS CDK under infra/. No secrets in code — env vars only.
EOF

echo "Scaffold created:"
find . -maxdepth 2 -not -path './.git*' | sort
echo ""
echo "Next: cp .env.example .env  (fill keys), then commit:"
echo "  git add -A && git commit -m 'chore: scaffold repo' && git push"
