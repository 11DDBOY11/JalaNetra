# Data Sources - verify before agents build ingestion
Freshness MUST be stated honestly in the demo (organizers explicitly reward this).

## India WRIS (no API key needed)
- API catalog (Swagger): https://indiawris.gov.in/swagger-ui/index.html - has a Ground Water
  Level dataset endpoint. Try it first for Dakshina Kannada wells.
- Manual fallback (guaranteed to work tonight): DataDownload module
  https://indiawris.gov.in/wris/#/DataDownload -> Groundwater Level -> station-wise,
  one year at a time. Save CSV to data/raw/groundwater/.
- HONEST CADENCE NOTE: CGWB national observation wells are measured ~4x/year
  (Jan, Mar-May, Aug, Nov). Say "quarterly government observations" in the demo.
  Karnataka state wells may be denser - check what the data shows.

## IMD district rainfall (needs account)
- Portal: https://api.imd.gov.in - register, generate a DEV API key (bound to your
  laptop's public IP!) and a JWT token.
- District-wise rainfall: GET https://api.imd.gov.in/api/v1/districtrainfall
  (find Dakshina Kannada's id from the portal's Try API console).
- PROBLEM TO KNOW: IMD keys are bound to a static public IP - a deployed Lambda has
  dynamic IPs. Plan: use IMD API from laptop/dev for the demo pull, OR use a
  data.gov.in rainfall resource instead.
- data.gov.in alternative: register at data.gov.in, generate API key in My Account,
  find a "district rainfall" resource ID (36-char) and call
  https://api.data.gov.in/resource/<id>?api-key=...&format=json

## Tonight's success criterion
At least ONE groundwater CSV and ONE rainfall CSV in data/raw/ with columns you
understand. Put a short note of the actual columns in this file.
