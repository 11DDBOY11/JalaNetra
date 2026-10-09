JalaNetra is a water-security early-warning system for Mangaluru, Karnataka, built for the
WeMakeDevs x AWS "Environmental Hacks" hackathon (Heat & Water track), deadline Sunday
Oct 11, 2026. Core loop: India WRIS groundwater + IMD rainfall + citizen water reports +
laptop edge node (Greengrass v2 in Docker, SIMULATED telemetry - no Jetson hardware) ->
per-ward forecast -> actionable alerts (SNS SMS + Polly voice notes) + React app on Amplify.
Judging priority: what CHANGES for a person - demo must show a household receiving a
"book your tanker by <date>" alert in time. Never fabricate data; label synthetic/simulated
data explicitly. All infra in AWS CDK under infra/. No secrets in code - env vars only.
