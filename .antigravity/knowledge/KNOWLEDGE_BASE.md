# JalaNetra — Antigravity Knowledge Base
Save entries into .antigravity/knowledge/ so every agent shares the same context.

## project-context.md
JalaNetra is a water-security early-warning system for Mangaluru, Karnataka, built for
the WeMakeDevs x AWS "Environmental Hacks" hackathon (Heat & Water track), deadline
Sunday Oct 11, 2026. Core loop: government water data (India WRIS groundwater wells,
IMD rainfall) + citizen water reports + a laptop edge node (Greengrass v2 in Docker,
SIMULATED telemetry — no Jetson hardware exists) -> per-ward forecast -> actionable
alerts (SMS/WhatsApp/Polly voice) + React web app on Amplify. The judging criterion
that matters most: not measurement, but WHAT CHANGES for a person — the demo must show
a household receiving a 'book your tanker by <date>' alert in time.

## data-sources.md
- India WRIS (indiawris.gov.in): district observation-well groundwater levels,
  Dakshina Kannada; MONTHLY cadence — say this plainly in the demo.
- IMD / data.gov.in: daily district rainfall; requires a free API key.
- Registry of Open Data on AWS (registry.opendata.aws): check for hosted hydrology
  datasets before building scrapers.
- Citizen water reports: collected via the web app during the hackathon — REAL local
  human data; label as hackathon-collected, never present as long-term statistics.
- Fallback: download a CSV snapshot once, seed S3 with it, label it as historical
  seed data. Never present seeded data as live.

## aws-constraints.md
- Mandatory: AWS must be VISIBLY USED in the demo video (console, code, or service),
  not just mentioned in the writeup.
- AWS IoT Greengrass v2 is open source — running it (in Docker on the laptop) satisfies
  eligibility twice (open source + AWS service). Build the Docker image from the
  aws-greengrass/aws-greengrass-docker repo; the amazon/aws-iot-greengrass Docker Hub
  image is deprecated.
- Amazon Polly supports en-IN (Aditi, Kajal, Raveena) and hi-IN, but NOT Kannada —
  Kannada voice requires a local TTS model, if attempted at all.
- Keep everything free-tier-safe; the project uses $25 hackathon credits, not more.

## demo-script.md
- 3 minutes max. Beat structure: street-level problem (25s) -> data sources (25s) ->
  architecture with AWS console visible (50s) -> the alert moment: phone receives SMS +
  Polly voice note with a concrete action date (40s) -> who it changes what for (30s) ->
  honest limits + roadmap (10s).
- Record real local footage: the building sump/tank, the laptop edge node with live
  AWS console on screen, a tanker delivery or dry-season tap.
- Honesty wins points: say "simulated edge telemetry" and "hackathon-collected citizen
  reports" explicitly. Judges explicitly reward saying plainly where data comes from.
