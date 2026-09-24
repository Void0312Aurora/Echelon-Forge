# IJEAT — Armored Modular and Non-Modular Vehicle survey

Source ID: `p5-us-ground-stryker-family-ijeat-survey`
Tier: `C`
Publisher: Blue Eyes Intelligence Engineering and Sciences Publication (BEIESP)
Author / maintainer: Survey authors listed in the paper; no government provenance
Title: Armored Modular and Non-Modular Vehicle: A Survey
URL: https://www.ijeat.org/wp-content/uploads/papers/v8i3/C5700028319.pdf
Retrieval:
  attempted_at: 2026-09-24T16:55:44Z
  method: web_open
  status: success
  returned: IAV family description, C7 engine family baseline, approximate 100 km/h speed and 500 km operational coverage, and a list naming M1252 MCVV among DVH variants
  did_not_return: a parameter row assigning the 350 hp, 100 km/h or 500 km values specifically to M1252 MCVV
Domain: ground
Equipment: Stryker / IAV family and DVH variant context
Configuration: The paper's family-level Stryker discussion names the C7 engine and generic mobility values, then separately lists M1252 MCVV among DVH variants. The values are therefore retained as a low-tier family baseline only.
Estimate status: Yes; bounded family reference, not a M1252-specific parameter or runtime default.
Retention: manifest and extracted family-context note only

## Extracted parameter notes

- Family reference: Caterpillar C7, approximately 350 hp, approximately 100 km/h and approximately 500 km operational coverage.
- Variant context: M1252 MCVV is listed among the DVH variants.
- Boundary: the paper does not bind the generic mobility table to M1252 MCVV; no value is promoted into the M1252 `Propulsion / mobility` field.
