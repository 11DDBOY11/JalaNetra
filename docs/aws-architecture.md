# JalaNetra Pulse — AWS Cloud Architecture

**Project:** JalaNetra Pulse (Mangaluru Community Water Outage Detection)  
**Track:** WeMakeDevs x AWS Environmental Hacks — Heat & Water Track  
**Infrastructure as Code:** AWS CDK v2 (Python, located in `infra/`)  

---

## Architecture Diagram

```
[ PWA Residents & Responders ] (AWS Amplify Hosting / Local Vite)
             │
             │ HTTPS / REST (JSON)
             ▼
[ Amazon API Gateway ] (HTTP API v2, CORS-enabled)
             │
             │ Payload Proxy ($default / {proxy+})
             ▼
[ AWS Lambda: ApiHandler ] (Python 3.11 / FastAPI ASGI Adapter)
       │                 │                      │
       ▼                 ▼                      ▼
[ DynamoDB: water_reports ] [ DynamoDB: community_alerts ] [ DynamoDB: subscriptions ]
 (Partition: ward_id,       (Partition: ward_id,           (Partition: ward_id,
  Sort: created_at)          Sort: alert_id)                Sort: phone_hash)
       ▲
       │ 90-Minute Outage Clustering & Recovery Evaluation
       ▼
[ AWS Lambda: AlertEvaluator ] ◄── [ Amazon EventBridge ] (Rate: 6 Hours / Incident Cron)
       │
       │ Alert Dispatches & Transactional Sandbox Test
       ▼
[ Amazon SNS ] (Topic: jalanetra-alerts / SMS Sandbox)
       │
       ▼
[ Verified Personal Test Phone ] (SMS_TEST_PHONE via E.164, zero unsolicited messages)
```

---

## AWS Services Utilized in Architecture

1. **Amazon API Gateway (HTTP API):**
   - High-throughput, low-latency entry point with integrated CORS preflight.
   - Proxies incoming citizen reports and pulse summary requests to Lambda.

2. **AWS Lambda:**
   - `ApiHandler` (512 MB, Python 3.11): Runs FastAPI application endpoints.
   - `AlertEvaluatorHandler` (512 MB, Python 3.11): EventBridge-driven evaluator that recalculates rolling 90-minute clusters and transitions alert states.
   - `IngestHandler` (1024 MB, Python 3.11): Periodic ingestion of CGWB open datasets from S3.

3. **Amazon DynamoDB (Pay-Per-Request Serverless):**
   - `water_reports`: Time-series reports partitioned by `ward_id`, sorted by `created_at`. TTL enabled for 30-day historical data rotation.
   - `community_alerts`: State store for active, recovery, and resolved neighborhood alerts.
   - `subscriptions`: Alert notification preferences partitioned by `ward_id`, sorted by `phone_hash`.

4. **Amazon S3:**
   - Raw data lake for historical Central Ground Water Board (CGWB) quarterly CSVs and IMD precipitation baselines, with Glacier archival lifecycle rules after 90 days.

5. **Amazon EventBridge:**
   - Scheduled cron rules for automated ward status evaluation and daily data lake refresh.

6. **Amazon SNS & SMS Sandbox:**
   - Transactional SMS integration for emergency ward alerts.
   - Strictly configured in sandbox mode: sends only to verified owner test number upon explicit user confirmation (`confirm_test_send: true`).

7. **AWS Amplify:**
   - Responsive PWA hosting for mobile residents and ward responders.

---

## Cloud Deployment Status & Truthfulness Notice
> **Transparency Notice:**  
> This AWS architecture is fully codified with AWS CDK in `infra/app.py`.  
> For this hackathon submission, the system runs locally using SQLite persistence.  
> **No AWS resources were deployed, no cloud billing incurred, and no public SMS messages dispatched.**
