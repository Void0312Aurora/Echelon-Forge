# F-15EX Eagle II

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-15/f-15ex/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-us-air-f15ex`
Content status: parameter table present with per-field source and confidence. Every row names the package that states it. The empty weight is recorded as two separate source readings rather than one merged row.

## Identity

- Family: F-15 Eagle
- Variant: F-15EX Eagle II
- Role: Multirole combat aircraft
- Manufacturer: Boeing, with BAE Systems for the electronic warfare suite
- Configuration scope: the F-15EX as ordered by the United States Air Force, derived from the F-15QA built for Qatar. The F-15C, F-15E and F-15QA are separate configurations and no value is carried between them.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Air Force | In service | `p5-us-air-f15ex-usaf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Variant | F-15EX Eagle II | `p5-us-air-f15ex-usaf` | A |
| Length | 19.4 m (63.7 ft) | `p5-us-air-f15ex-globalmilitary` | C |
| Wingspan | 13.1 m (42.8 ft) | `p5-us-air-f15ex-globalmilitary` | C |
| Height | 5.7 m (18.7 ft) | `p5-us-air-f15ex-globalmilitary` | C |
| Wing area | 56.5 m² (608.2 sq ft) | `p5-us-air-f15ex-globalmilitary` | C |
| Empty weight (reading one) | 31,700 lb (14,400 kg) | `p5-us-air-f15ex-lincs` | C |
| Empty weight (reading two) | 35,501 lb (16,103 kg) | `p5-us-air-f15ex-globalmilitary` | C |
| Empty weight (third page, same value as reading one) | 31,700 lb (14,400 kg) | `p5-us-air-f15ex-f16net` | C |
| Maximum takeoff weight | 81,000 lb (36,741 kg) | `p5-us-air-f15ex-globalmilitary` | C |
| Powerplant | Two General Electric F110-GE-129 afterburning turbofans | `p5-us-air-f15ex-f16net` | C |
| Powerplant thrust | 129 kN each | `p5-us-air-f15ex-globalmilitary` | C |
| Maximum speed | 2,655 km/h | `p5-us-air-f15ex-globalmilitary` | C |
| Range | 3,889 km | `p5-us-air-f15ex-globalmilitary` | C |
| Crew | One or two, pilot and weapon systems officer | `p5-us-air-f15ex-globalmilitary` | C |
| First flight | 2 February 2021 | `p5-us-air-f15ex-afsf` | C |
| Initial operational capability | July 2024 | `p5-us-air-f15ex-afsf` | C |
| Contractors | Boeing, with BAE Systems for EPAWSS and Raytheon for the AESA radar | `p5-us-air-f15ex-afsf` | C |
| Production planned | 100 | `p5-us-air-f15ex-afsf` | C |
| Inventory | 13 | `p5-us-air-f15ex-afsf` | C |
| Operators | Air Combat Command, Air Force Materiel Command and the Air National Guard | `p5-us-air-f15ex-afsf` | C |
| Basing | Eglin AFB and Portland Airport, with Fresno ANGB, Kadena AB, Klamath Falls, NAS JRB New Orleans and Selfridge ANGB planned | `p5-us-air-f15ex-afsf` | C |
| Programme lineage | Derived from the F-15QA ordered by Qatar; planned replacement for the F-15C/D | `p5-us-air-f15ex-airvectors` | C |

## Configuration Boundary

Every technical row on this leaf is Tier C. The service package held for this aircraft is a photographic news item and carries no specification block, and no Boeing document for the F-15EX is held in this tree. The leaf therefore records open-source compilations and says so on every row.

The empty weight is carried as three rows rather than one. Two independently published pages give 31,700 lb (14,400 kg) and one gives 35,501 lb (16,103 kg). The spread is 3,801 lb, which is far larger than rounding error, and the three packages were produced independently. They are not averaged and no reading is discarded; the row text states which reading belongs to which package rather than presenting a merged claim.

The dimensions, wing area and maximum takeoff weight agree across the three compilation packages, and the powerplant type agrees across all of them. The thrust is recorded from one package because the others state no per-engine figure.

The programme rows rest on a single recognised aerospace association page and are labelled accordingly. They are programme facts rather than measured values, so they carry no measurement uncertainty.

## Source References

- `p5-us-air-f15ex-usaf`: `raw/sources/us_air_force/p5-us-air-f15ex-usaf/manifest.md` — operator and variant identity only
- `p5-us-air-f15ex-globalmilitary`: `raw/sources/globalmilitary/p5-us-air-f15ex-globalmilitary/manifest.md` — dimensions, wing area, masses, thrust, speed, range
- `p5-us-air-f15ex-lincs`: `raw/sources/lincs_military_aviation/p5-us-air-f15ex-lincs/manifest.md` — empty weight reading one
- `p5-us-air-f15ex-f16net`: `raw/sources/f16net/p5-us-air-f15ex-f16net/manifest.md` — dimensions, wing area, powerplant, empty weight reading one repeated
- `p5-us-air-f15ex-afsf`: `raw/sources/air_and_space_forces/p5-us-air-f15ex-afsf/manifest.md` — programme facts
- `p5-us-air-f15ex-airvectors`: `raw/sources/airvectors/p5-us-air-f15ex-airvectors/manifest.md` — programme lineage
