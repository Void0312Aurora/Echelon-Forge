# F-15EX Eagle II

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-15/f-15ex/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-22`
Equipment ID: `eq-us-air-f15ex`
Content status: parameter table complete for the USAF F-15EX Eagle II; the empty-weight conflict remains explicit and no F-15QA/F-15SA values are merged.

## Identity

- Family: F-15 Eagle
- Variant: F-15EX Eagle II
- Role: Multirole combat aircraft
- Manufacturer: Boeing, with BAE Systems for the electronic warfare suite and Raytheon for the radar
- Configuration scope: the F-15EX as ordered by the United States Air Force, derived from the F-15QA built for Qatar. The F-15C, F-15E and F-15QA are separate configurations and no value is carried between them.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Air Force | In service | `p5-us-air-f15ex-usaf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Variant | F-15EX Eagle II | `p5-us-air-f15ex-usaf` | A |
| Length | 19.4 m (63.8 ft) | `p5-us-air-f15ex-boeing` | B |
| Wingspan | 13.0 m (42.8 ft) | `p5-us-air-f15ex-boeing` | B |
| Height | 5.6 m (18.5 ft) | `p5-us-air-f15ex-boeing` | B |
| Wing area | 56.5 m² (608 sq ft) | `p5-us-air-f15ex-lincs` | C |
| Empty weight (reading one) | 31,700 lb (14,400 kg) | `p5-us-air-f15ex-lincs` | C |
| Empty weight (reading two) | 35,501 lb (16,103 kg) | `p5-us-air-f15ex-globalmilitary` | C |
| Empty weight (third page, same value as reading one) | 31,700 lb (14,400 kg) | `p5-us-air-f15ex-f16net` | C |
| Maximum takeoff weight | 81,000 lb (36,741 kg) | `p5-us-air-f15ex-boeing` | B |
| Powerplant | Two General Electric F110-GE-129 afterburning turbofans | `p5-us-air-f15ex-f16net` | C |
| Powerplant (second page naming the same engine) | Two General Electric F110-GE-129 at 129 kN each | `p5-us-air-f15ex-globalmilitary` | C |
| Powerplant thrust | 29,500 lbf (131 kN) each with afterburner; 17,155 lbf (76.31 kN) dry | `p5-us-air-f15ex-f16net` | C |
| Payload | 29,500 lb (13,381 kg); 13,300 kg on the same page's capability text | `p5-us-air-f15ex-boeing` | B |
| Armament / carriage | Up to 12 AIM-120 AMRAAMs, or an equivalent mix of large ordnance | `p5-us-air-f15ex-boeing` | B |
| Mission system | Advanced AESA radar, EPAWSS electronic-warfare suite, digital fly-by-wire, all-glass cockpit and open mission-systems architecture | `p5-us-air-f15ex-boeing` | B |
| Maximum speed | Mach 2.5 | `p5-us-air-f15ex-boeing` | B |
| Service ceiling | 50,000 ft (15,240 m) | `p5-us-air-f15ex-boeing` | B |
| Service life | 20,000+ hours | `p5-us-air-f15ex-boeing` | B |
| Crew | One or two, pilot and weapon systems officer | `p5-us-air-f15ex-globalmilitary` | C |
| Ejection seat | McDonnell Douglas ACES II | `p5-us-air-f15ex-globalmilitary` | C |
| First flight | 2 February 2021 | `p5-us-air-f15ex-afsf` | C |
| Delivered | 11 March 2021 onward | `p5-us-air-f15ex-afsf` | C |
| Initial operational capability | July 2024 | `p5-us-air-f15ex-afsf` | C |
| Contractors | Boeing; BAE Systems for EPAWSS; Raytheon for the AESA radar | `p5-us-air-f15ex-afsf` | C |
| Production planned | 100 | `p5-us-air-f15ex-afsf` | C |
| Inventory | 13 | `p5-us-air-f15ex-afsf` | C |
| Operators | Air Combat Command, Air Force Materiel Command and the Air National Guard | `p5-us-air-f15ex-afsf` | C |
| Aircraft locations | Eglin AFB and Portland Airport, with Fresno ANGB, Kadena AB, Klamath Falls, NAS JRB New Orleans and Selfridge ANGB planned | `p5-us-air-f15ex-afsf` | C |

## Configuration Boundary

The manufacturer page is the source of record for the dimensions, maximum takeoff weight, payload, maximum speed, ceiling and service life. Those rows are Tier B. It states no engine, no thrust, no empty weight, no crew and no ejection seat, and no such row is attributed to it.

It does state the representative carriage and mission-system context recorded above: up to 12 AMRAAMs or an equivalent large-ordnance mix, plus the AESA radar, EPAWSS, digital flight controls, all-glass cockpit and open mission-systems architecture. These are capability descriptions, not a universal combat load or a claim that every software or weapon configuration is identical.

The powerplant and thrust rows rest on the Tier C pages. This is a correction: the powerplant row previously pointed at the manufacturer page, which does not name an engine at all. The engine designation, 2 × General Electric F110-GE-129, and the dry and afterburner thrust pair come from `p5-us-air-f15ex-f16net`, which states them explicitly, and the same engine model is named by `p5-us-air-f15ex-globalmilitary`. Those two pages are the only packages in this tree that state an engine for this aircraft.

The empty weight is carried as three rows rather than one. Two pages carry the same specification block and give 31,700 lb (14,400 kg); a third gives 35,501 lb (16,103 kg). The spread is 3,801 lb, which is far larger than rounding error. The two 31,700 lb rows are not two independent measurements: the F-16.net post states that it reproduces the Wikipedia specification block, and the Lincs page carries the same block, so both trace to one origin. The 35,501 lb reading is from a different compilation. The three are recorded side by side, none is averaged, and no reading is discarded.

The maximum speed is recorded as the manufacturer's Mach 2.5. The Tier C pages give 2,655 km/h, about Mach 2.65, which is a different reading rather than a rounding of the same one. Both are recorded and the manufacturer's is the row of record.

A maximum altitude of 60,000 ft is given by the two Tier C pages, against the manufacturer's 50,000 ft ceiling. The manufacturer's figure is the row of record and the higher reading is recorded as an alternative rather than adopted.

The payload is stated twice on the manufacturer page, as 29,500 lb (13,381 kg) and as 29,500 lb (13,300 kg). The imperial value is identical on both and only the metric rounding differs. Both roundings are recorded rather than one being selected as the page's own conversion.

The programme rows rest on a single recognised aerospace association page and are labelled accordingly. That page's own aircraft-count narrative does not reconcile with the inventory figure it prints, and the figure of 100 planned is the value the page's technical data block states.

The worldwide operator counts published by the Tier C compilation page are not carried on this leaf at all. That page credits Saudi Arabia and Qatar with F-15EX aircraft, which are F-15SA and F-15QA airframes rather than F-15EX, and its totals do not reconcile with its own United States figure. Only the United States Air Force operates this variant among the packages held here.

## Source References

- `p5-us-air-f15ex-usaf`: `raw/sources/us_air_force/p5-us-air-f15ex-usaf/manifest.md` — locator and variant identity only; no retrieval record
- `p5-us-air-f15ex-boeing`: `raw/sources/boeing/p5-us-air-f15ex-boeing/manifest.md` — manufacturer dimensions, masses, payload, speed, ceiling, service life
- `p5-us-air-f15ex-lincs`: `raw/sources/lincs_military_aviation/p5-us-air-f15ex-lincs/manifest.md` — wing area, airfoil, empty weight reading one, performance block, production and squadron history
- `p5-us-air-f15ex-f16net`: `raw/sources/f16net/p5-us-air-f15ex-f16net/manifest.md` — powerplant and thrust, carrier of the specification block, empty weight reading one repeated
- `p5-us-air-f15ex-globalmilitary`: `raw/sources/globalmilitary/p5-us-air-f15ex-globalmilitary/manifest.md` — empty weight reading two, second page naming the engine, crew, ejection seat, altitude reading
- `p5-us-air-f15ex-afsf`: `raw/sources/air_and_space_forces/p5-us-air-f15ex-afsf/manifest.md` — programme facts
