# F-15C Eagle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-15/f-15c/README.md`
Owner: `database/equipment-data`
Content status: Variant-specific post-Cold-War parameter draft; bounded estimates are labelled and are not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-air-f15c` |
| Family / variant | F-15 / F-15C Eagle |
| Role | Air-superiority fighter |
| Configuration boundary | USAF single-seat C baseline; F-15J, F-15E and F-15EX are excluded |

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Air Force | Retired from regular fighter inventory; legacy reference configuration | `p5-us-air-f15c-usaf` |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 19.44 m length; 13.05 m span; 5.63 m height | `p5-us-air-f15c-usaf` | A | F-15C/D common airframe dimensions |
| Empty mass | 12,700 kg (28,000 lb) | `p5-us-air-f15c-usaf`; `p5-us-air-f15c-wikipedia` | A/C | Basic aircraft mass; no conformal tanks or stores |
| Maximum takeoff mass | 30,845 kg (68,000 lb) | `p5-us-air-f15c-wikipedia` | C | Public F-15C/D structural limit; load and fuel state vary |
| Internal fuel mass | 6,100 kg (13,455 lb) | `p5-us-air-f15c-wikipedia` | C | Approximate internal tank capacity converted at aviation-fuel density; external tanks excluded |
| Powerplant | 2 x Pratt & Whitney F100-PW-220 afterburning turbofans | `p5-us-air-f15c-usaf` | A | Later C fleet commonly used -220; earlier -100 aircraft excluded |
| Thrust | 2 x 23,770 lbf (105.7 kN) afterburning; 211.4 kN total | `p5-us-air-f15c-usaf` | A | Static military reference thrust |
| Flight performance | Mach 2.5 (about 2,660 km/h); service ceiling 19,800 m; climb about 254 m/s | `p5-us-air-f15c-usaf`; `p5-us-air-f15c-wikipedia` | A/C | Clean/high-altitude maxima; stores and temperature change performance |
| Range | Ferry about 5,550 km; combat radius 1,060-1,300 km | `p5-us-air-f15c-wikipedia` | C | Bounded open-source estimate; mission profile, CFTs and tanks drive spread |
| Crew | 1 | `p5-us-air-f15c-usaf` | A | Single-seat C cockpit |
| Radar | AN/APG-63 pulse-Doppler radar; open detection bound 100-160 km | `p5-us-air-f15c-usaf`; `p5-us-air-f15c-wikipedia` | A/C | Baseline mechanically scanned APG-63; APG-63(V)1/V2 upgrades are not merged |
| Avionics / EW | AN/ASN-109-class INS, APX-76 IFF and AN/ALQ-135 Tactical Electronic Warfare System; 1 Link-16 terminal on upgraded aircraft | `p5-us-air-f15c-usaf`; `p5-us-air-f15c-wikipedia` | A/C | Navigation and self-protection fit changed through MSIP; terminal count is a bounded configuration statement |
| Armament | 1 x M61A1 20 mm cannon, 940 rounds; 8 external stations; about 7,300 kg stores | `p5-us-air-f15c-usaf`; `p5-us-air-f15c-wikipedia` | A/C | AIM-7/AIM-9/AIM-120 family fit is loadout-dependent |
| Mission systems | Air-superiority fire-control system with track-while-scan and beyond-visual-range employment; 8 stores stations | `p5-us-air-f15c-usaf`; `p5-us-air-f15c-wikipedia` | A/C | Functional description, not a claim of a particular software block |
| Signature / protection | Conventional non-stealth airframe; clean frontal RCS estimated 10-25 m2; 1 internal ECM suite plus 4 chaff/flare dispenser units, about 60-120 cartridges | `p5-us-air-f15c-wikipedia` | C | RCS and cartridge count are bounded specialist estimates, not USAF protection specifications |

## Source References

- `p5-us-air-f15c-usaf`: `raw/sources/us_air_force/p5-us-air-f15c-usaf/manifest.md`
- `p5-us-air-f15c-wikipedia`: `raw/sources/wikipedia/p5-us-air-f15c-wikipedia/manifest.md`
