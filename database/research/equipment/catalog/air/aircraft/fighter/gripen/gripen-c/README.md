# JAS 39 Gripen C

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/gripen/gripen-c/README.md`
Owner: `database/equipment-data`
Content status: Variant-specific current-era parameter draft; bounded estimates are labelled and are not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-se-air-gripenc` |
| Family / variant | JAS 39 Gripen / Gripen C |
| Role | Single-seat multirole fighter |
| Configuration boundary | Swedish Gripen C baseline; Gripen A, D and E/F are excluded |

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Swedish Air Force | In service | `p5-se-air-gripenc-fm`; `p5-se-air-gripenc-saab` |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 14.10 m length; 8.40 m span; 4.50 m height | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-fm` | A | Gripen C single-seat airframe |
| Empty mass | 6,800 kg | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-wikipedia` | A/C | Basic aircraft, no stores |
| Maximum takeoff mass | 14,000 kg | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-fm` | A | C-series structural maximum |
| Internal fuel mass | 2,268 kg | `p5-se-air-gripenc-wikipedia` | C | Approximate internal capacity converted to fuel mass; external tanks excluded |
| Powerplant | 1 x Volvo RM12 afterburning turbofan | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-fm` | A | RM12 is the Gripen C engine fit |
| Thrust | 54.0 kN dry / 80.5 kN afterburning | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-wikipedia` | A/C | Static reference thrust |
| Flight performance | Mach 2.0 (about 2,130 km/h); service ceiling 15,240 m; takeoff run about 400 m | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-fm` | A | Public maxima and short-field figure; stores and runway state affect results |
| Range | Ferry about 3,000 km; combat radius 800 km | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-wikipedia` | A/C | Combat radius is a bounded open-source estimate for air-to-air loadout |
| Crew | 1 | `p5-se-air-gripenc-fm`; `p5-se-air-gripenc-saab` | A | Single-seat C cockpit |
| Radar | Ericsson PS-05/A pulse-Doppler radar; open detection bound about 120 km | `p5-se-air-gripenc-fm`; `p5-se-air-gripenc-wikipedia` | A/C | Mk 3/4 software and antenna upgrades vary; range is a specialist estimate |
| Avionics / EW | Integrated digital avionics, helmet-mounted cueing and Link 16/tactical datalink; 1 radar, 1 HMD and 1 datalink terminal | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-fm` | A | C-series software block and national datalink crypto are not normalized |
| Armament | 1 x 27 mm Mauser BK-27 cannon, 120 rounds; 8 external stations; about 5,300 kg stores | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-wikipedia` | A/C | AIM-120, IRIS-T, Meteor and guided bomb fits depend on operator clearance |
| Mission systems | Networked multirole fire-control and rapid road-base operations; 8 stores stations and approximately 400 m takeoff run | `p5-se-air-gripenc-saab`; `p5-se-air-gripenc-fm` | A | Road-base figure is a public operational characteristic, not a universal runway requirement |
| Signature / protection | Conventional compact airframe; clean frontal RCS estimated 0.5-2 m2; 1 RWR/ECM suite plus BOL chaff/flare rails, about 120-180 cartridges | `p5-se-air-gripenc-wikipedia`; `p5-se-air-gripenc-fm` | A/C | RCS and cartridge count are bounded estimates; exact Swedish fit is not public |

## Source References

- `p5-se-air-gripenc-saab`: `raw/sources/saab/p5-se-air-gripenc-saab/manifest.md`
- `p5-se-air-gripenc-fm`: `raw/sources/swedish_armed_forces/p5-se-air-gripenc-fm/manifest.md`
- `p5-se-air-gripenc-wikipedia`: `raw/sources/wikipedia/p5-se-air-gripenc-wikipedia/manifest.md`
