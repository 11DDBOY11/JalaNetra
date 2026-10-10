# JalaNetra Agent Rules

- This is a Sunday-deadline hackathon project. Prioritize a working end-to-end demo over refactoring or visual polish.
- Never commit .env files, AWS credentials, API keys, phone numbers, or certificates.
- Use environment variables for secrets and document required variables in .env.example.
- No Jetson hardware is available. Any edge-device values must be marked clearly as SIMULATED.
- Never fabricate environmental data. Label all sample, simulated, or synthetic data in the UI, API, README, and demo.
- Use real India WRIS and rainfall data wherever available.
- The core user outcome is an actionable alert: “Water stress is likely in your ward; book a tanker by <date>.”
- Keep AWS infrastructure in infra/ using AWS CDK. Do not depend on manual console changes.
- Before declaring work complete, run relevant tests/build commands and create a clear walkthrough in the README or docs.
- Do not overwrite existing files without first reading them.