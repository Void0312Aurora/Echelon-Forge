# E-2D Advanced Hawkeye

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/aewc/e-2/e-2d/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-23`
Equipment ID: `eq-us-air-e2d`
Content status: parameter-complete research record combining two official U.S. Navy sources with explicit common-family boundaries.

## Identity

- Family: E-2 Hawkeye
- Variant: E-2D Advanced Hawkeye
- Role: Carrier-based airborne early warning, command and control and battle-space management
- Manufacturer: Northrop Grumman

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Navy | In service | `p5-us-navy-e2d-navair` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | 2 × Rolls-Royce T56-A-427A turboprops | `p5-us-navy-e2d-navair`; `p5-us-navy-e2d-airpac` | A |
| Power | 5,100 shp per engine | `p5-us-navy-e2d-navair`; `p5-us-navy-e2d-airpac` | A |
| Length | 17.5 m common-family reading; NAVAIR E-2D page gives 57 ft 8.75 in | `p5-us-navy-e2d-navair`; `p5-us-navy-e2d-airpac` | A |
| Height | 5.6 m common E-2 reading | `p5-us-navy-e2d-airpac` | A |
| Wingspan | 28 m common E-2 reading | `p5-us-navy-e2d-airpac` | A |
| Empty mass | 40,484 lb | `p5-us-navy-e2d-navair` | A |
| Basic mass | 18,090 kg common E-2 reading | `p5-us-navy-e2d-airpac` | A |
| Maximum gross mass | 23,850 kg common E-2 reading | `p5-us-navy-e2d-airpac` | A |
| Speed | 300+ kt | `p5-us-navy-e2d-navair`; `p5-us-navy-e2d-airpac` | A |
| Ceiling | 37,000 ft / approximately 9,100 m | `p5-us-navy-e2d-navair`; `p5-us-navy-e2d-airpac` | A |
| Crew | 5; two pilots and three mission-systems operators, with fourth-operator option | `p5-us-navy-e2d-navair` | A |
| Mission system | Fully integrated open architecture; AN/APY-9 radar, IFF, electronic support and networked battle-management functions | `p5-us-navy-e2d-navair` | A |
| Carrier / refuelling role | Carrier-based platform; aerial refuelling increases persistence | `p5-us-navy-e2d-navair` | A |

## Configuration Boundary

The AirPAC brief supplies common E-2 geometry and gross-mass readings; it is not treated as an E-2D-only certification. NAVAIR supplies the E-2D-specific sensor, crew and software context. Neither source publishes fuel quantity, range or weapon stations, so those are not inferred.

## Source References

- `p5-us-navy-e2d-navair`: `raw/sources/us_navy/p5-us-navy-e2d-navair/manifest.md`
- `p5-us-navy-e2d-airpac`: `raw/sources/us_navy/p5-us-navy-e2d-airpac/manifest.md`
