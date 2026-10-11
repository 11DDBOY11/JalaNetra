# JalaNetra Infrastructure

> ⚠️ **DO NOT DEPLOY during the hackathon unless you understand AWS charges.**  
> `cdk synth` validates the template only — no AWS resources are created.

## Architecture Summary

JalaNetra uses a serverless, event-driven AWS architecture designed for low cost and high reliability.

| Layer | AWS Service | Purpose |
|---|---|---|
| Storage | S3 | Raw CSV data (WRIS, IMD) |
| Database | DynamoDB (3 tables) | Ward state, reports, subscriptions |
| Compute | Lambda (3 functions) | API, ingestion, alert evaluation |
| API | API Gateway HTTP | Public REST API |
| Scheduler | EventBridge | 6-hourly alert checks, daily data refresh |
| Alerts | SNS | SMS dispatch to subscribers |
| Voice | Amazon Polly | en-IN / hi-IN voice notes |
| Frontend | AWS Amplify | React app hosting |

## Local Setup (CDK Synth Only)

```powershell
# From infra/ directory
pip install -r requirements.txt
npm install -g aws-cdk        # if not installed
cdk synth                     # validates template, NO deploy
```

## Actual Deployment (future, requires AWS account)

```powershell
# Prerequisites: AWS CLI configured, cdk bootstrapped
cdk bootstrap aws://<ACCOUNT>/ap-south-1
cdk deploy JalaNetraStack
```

## Destroy

```powershell
cdk destroy JalaNetraStack
```

## Cost Notes

- All tables use PAY_PER_REQUEST billing — zero cost when idle.
- Lambda free tier: 1M requests/month free.
- SNS: first 100 SMS in sandbox are free; production SMS has per-message cost.
- Polly: 5M characters/month free tier.
- Estimated hackathon cost: **$0–$2** if kept within free tier.
