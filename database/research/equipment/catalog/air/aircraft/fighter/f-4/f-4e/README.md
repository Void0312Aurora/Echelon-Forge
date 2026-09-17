# F-4E Phantom II

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-4/f-4e/README.md`
Owner: `database/equipment-data`
Content status: Variant-specific Cold-War parameter draft; bounded estimates are labelled and are not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-air-f4e` |
| Family / variant | F-4 Phantom II / F-4E |
| Role | Multirole fighter and strike aircraft |
| Configuration boundary | USAF F-4E with fixed internal gun; Navy F-4B/J and export F-4E fits are excluded |

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Air Force | Retired; Cold-War reference configuration | `p5-us-air-f4e-usaf` |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 19.20 m length; 11.77 m span; 5.02 m height | `p5-us-air-f4e-usaf` | A | F-4E basic airframe with folded wing tips excluded from span |
| Empty mass | 13,757 kg (30,328 lb) | `p5-us-air-f4e-usaf`; `p5-us-air-f4e-wikipedia` | A/C | Basic aircraft, no external stores |
| Maximum takeoff mass | 28,030 kg (61,850 lb) | `p5-us-air-f4e-wikipedia` | C | Public F-4E structural maximum; combat loading varies |
| Internal fuel mass | 6,900-7,300 kg | `p5-us-air-f4e-wikipedia` | C | 1,994 US gal class capacity converted to fuel mass; uncertainty reflects fuel density and tank usable fraction |
| Powerplant | 2 x General Electric J79-GE-17A afterburning turbojets | `p5-us-air-f4e-usaf` | A | USAF F-4E engine fit |
| Thrust | 2 x 17,900 lbf (79.6 kN) afterburning; 159.2 kN total | `p5-us-air-f4e-usaf` | A | Static military reference thrust |
| Flight performance | Mach 2.23 (about 2,370 km/h); service ceiling 18,300 m; climb about 210 m/s | `p5-us-air-f4e-usaf`; `p5-us-air-f4e-wikipedia` | A/C | Clean/high-altitude maxima; store and temperature effects not modelled |
| Range | Ferry about 2,600 km; combat radius 650-750 km | `p5-us-air-f4e-wikipedia` | C | Bounded estimate for strike profile; tanker and external-tank use excluded |
| Crew | 2 | `p5-us-air-f4e-usaf` | A | Pilot and radar intercept officer |
| Radar | AN/APQ-120 pulse-Doppler radar; open detection bound 70-100 km | `p5-us-air-f4e-usaf`; `p5-us-air-f4e-wikipedia` | A/C | F-4E radar fit; late upgrade sets are excluded |
| Avionics / EW | AN/ASQ-91 weapons-delivery computer, AN/ASN-63 inertial/navigation set and APX-80 IFF; 1 radar and 1 INS set | `p5-us-air-f4e-usaf`; `p5-us-air-f4e-wikipedia` | A/C | Block and national retrofit differences remain outside this baseline |
| Armament | 1 x M61A1 20 mm cannon, 639 rounds; 9 external stations; about 7,300 kg stores | `p5-us-air-f4e-usaf`; `p5-us-air-f4e-wikipedia` | A/C | AIM-7/AIM-9/AGM-65 and bomb fits are loadout-dependent |
| Mission systems | Two-seat radar-intercept and strike workflow with computer-aided bombing/navigation; 9 stores stations | `p5-us-air-f4e-usaf`; `p5-us-air-f4e-wikipedia` | A/C | Functional statement; no specific software block inferred |
| Signature / protection | Conventional non-stealth airframe; clean frontal RCS estimated 10-20 m2; 1 ECM suite plus 2 chaff/flare dispenser units, about 60 cartridges | `p5-us-air-f4e-wikipedia` | C | RCS and dispenser capacity are bounded specialist estimates; armor thickness is not public |

## Source References

- `p5-us-air-f4e-usaf`: `raw/sources/us_air_force/p5-us-air-f4e-usaf/manifest.md`
- `p5-us-air-f4e-wikipedia`: `raw/sources/wikipedia/p5-us-air-f4e-wikipedia/manifest.md`
