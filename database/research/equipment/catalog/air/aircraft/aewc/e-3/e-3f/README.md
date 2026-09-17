# E-3F SDCA

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/aewc/e-3/e-3f/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`
Equipment ID: `eq-fr-air-e3f`
Content status: parameter table present with per-field source and confidence. Retrieval status is recorded per package in each manifest's `Retrieval:` block. This leaf previously carried no parameter table at all; the table below was built on 2026-09-17, and every technical row is a family reading rather than an E-3F measurement.

## Identity

- Family: Boeing E-3 Sentry
- Variant: E-3F SDCA (Système de Détection et de Commandement Aéroporté)
- Role: Airborne early warning, detection and command and control
- Manufacturer: Boeing Aerospace, on a modified Boeing 707-320B airframe
- Configuration scope: the E-3F as operated by the French Air and Space Force. The E-3G and the NATO and other national E-3 marks are separate configurations.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| French Air and Space Force | In service | `p5-fr-air-e3f` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Role | Airborne detection and command aircraft with active and passive sensors | `p5-fr-air-e3f` | A |
| Variant identification | E-3F is the production aircraft for the French Air and Space Force | `p5-fr-air-e3f-encyclopedic` | C |
| Contractor | Boeing Aerospace Co. | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Length | 46.61 m (152 ft 11 in) | `p5-fr-air-e3f-encyclopedic` | C |
| Wingspan | 44.42 m (145 ft 9 in) | `p5-fr-air-e3f-encyclopedic` | C |
| Height | 12.60 m (41 ft 4 in) | `p5-fr-air-e3f-encyclopedic` | C |
| Wing area | 283 m² (3,050 sq ft) | `p5-fr-air-e3f-encyclopedic` | C |
| Rotodome | 9.1 m (30 ft) diameter, 1.8 m (6 ft) thick, mounted 3.35 m (11 ft) above the fuselage | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Empty weight (family reading) | 83,915 kg (185,000 lb) | `p5-fr-air-e3f-encyclopedic` | C |
| Gross weight (family reading) | 156,036 kg (344,000 lb) | `p5-fr-air-e3f-encyclopedic` | C |
| Maximum takeoff weight (family reading) | 157,397 kg (347,000 lb) | `p5-fr-air-e3f-encyclopedic` | C |
| Zero fuel weight (family reading) | 92,986 kg (205,000 lb) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Family maximum takeoff weight (fact sheet reading) | 147,418 kg (325,000 lb) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Powerplant (family reading) | Four Pratt and Whitney TF33-PW-100A turbofans | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Thrust (fact sheet reading) | 20,500 lb each at sea level | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Thrust (encyclopedic reading) | 21,500 lbf (96 kN) each | `p5-fr-air-e3f-encyclopedic` | C |
| Thrust (programme-page reading, United States and NATO fit) | 21,000 lb each | `p5-fr-air-e3f-airforcetechnology` | C |
| Powerplant (non-United States and non-NATO fit) | Four CFM-56-2 turbofans at 24,000 lb thrust each | `p5-fr-air-e3f-airforcetechnology` | C |
| Optimum cruise speed | 360 mph (Mach 0.48) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Speed (programme-page reading) | Over 800 km/h (500 mph) | `p5-fr-air-e3f-airforcetechnology` | C |
| Ceiling | Above 29,000 ft (8,788 m) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Ceiling (programme-page reading) | Over 10,670 m (35,000 ft) | `p5-fr-air-e3f-airforcetechnology` | C |
| Endurance | More than eight hours unrefuelled | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Crew | Flight crew of four, plus a mission crew of 13 to 19 specialists | `p5-us-air-e3sentry-usaf-factsheet` | A |

## Configuration Boundary

This leaf carried no parameter table before 2026-09-17. The official French source held for it states the operator and the role and no dimension, mass or performance figure.

Every technical row on this leaf is a family reading, not an E-3F measurement. No package held here states a fitted weight, an engine fit or a performance figure for the French aircraft specifically, so the rows are labelled as family values and the leaf does not present them as the E-3F's own. Three consequences follow.

First, the engine fit is unresolved rather than chosen. The United States Air Force fact sheet and the encyclopedic block both describe the TF33-powered airframe, while the programme page states that the non-United States and non-NATO aircraft are CFM-56-2 powered at 24,000 lb thrust and the United States and NATO aircraft are TF33-powered. The leaf records the TF33 family reading and the CFM-56-2 reading side by side with their sources and does not assert which is fitted to the E-3F.

Second, the three thrust readings for the TF33 fit are 20,500 lb, 21,000 lb and 21,500 lb. They are different roundings of one rating from three publishers and are all retained.

Third, the maximum take-off weight carries two family readings that differ by more than 10 percent: 325,000 lb from the fact sheet and 347,000 lb from the encyclopedic block. Both are retained and the leaf does not select one. The fact sheet's 205,000 lb zero fuel weight and the encyclopedic 344,000 lb gross weight are recorded as separate rows rather than reconciled into a single mass.

The E-3F is not the E-3G. The E-3G leaf carries the Block 40/45 mission-system modernization and none of its values are carried here.

## Source References

- `p5-fr-air-e3f`: `raw/sources/ministere_des_armees/p5-fr-air-e3f/manifest.md` — operator and role only, no technical rows
- `p5-us-air-e3sentry-usaf-factsheet`: `raw/sources/us_air_force/p5-us-air-e3sentry-usaf-factsheet/manifest.md` — family masses, powerplant, cruise, ceiling, endurance, crew, rotodome
- `p5-fr-air-e3f-encyclopedic`: `raw/sources/wikipedia/p5-fr-air-e3f-encyclopedic/manifest.md` — variant identification, masses, dimensions, second thrust reading
- `p5-fr-air-e3f-airforcetechnology`: `raw/sources/airforce_technology/p5-fr-air-e3f-airforcetechnology/manifest.md` — engine-fit split by operator group
