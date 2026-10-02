# Tornado IDS

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/ground-attack/tornado/tornado-ids/README.md`
Owner: `database/equipment-data`
Content status: Multinational IDS parameter draft; bounded estimates are labelled and are not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-eu-air-tornadoids` |
| Family / variant | Panavia Tornado / IDS (Interdictor/Strike) |
| Role | Two-seat low-level strike and interdiction aircraft |
| Configuration boundary | Baseline RAF/German/Italian IDS family; ADV/F3 and GR4 upgrade-specific systems are excluded |

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Royal Air Force | Retired IDS/GR1 reference operator | `p5-uk-air-tornadoids-raf` |
| German Air Force | Retired IDS reference operator | `p5-de-air-tornadoids-bundeswehr` |
| Italian Air Force | IDS reference operator | `p5-it-air-tornadoids-ami` |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 16.72 m length; 8.60 m span swept / 13.91 m span extended; 5.95 m height | `p5-uk-air-tornadoids-raf`; `p5-de-air-tornadoids-bundeswehr` | A | Variable-sweep wing; span is explicitly given at both end positions |
| Empty mass | 14,500 kg | `p5-de-air-tornadoids-bundeswehr`; `p5-eu-air-tornadoids-wikipedia` | A/C | Basic IDS aircraft, no national pods or stores |
| Maximum takeoff mass | 28,000 kg | `p5-uk-air-tornadoids-raf`; `p5-eu-air-tornadoids-wikipedia` | A/C | IDS structural maximum; GR4 and export fits can differ |
| Internal fuel mass | 5,300-5,500 kg | `p5-eu-air-tornadoids-wikipedia` | C | Approximate tank capacity converted to fuel mass; usable fuel and national plumbing vary |
| Powerplant | 2 x Turbo-Union RB199 Mk103 afterburning turbofans | `p5-uk-air-tornadoids-raf`; `p5-de-air-tornadoids-bundeswehr` | A | IDS engine fit |
| Thrust | 2 x 40.5 kN dry / 71.5 kN afterburning; 143 kN total afterburning | `p5-eu-air-tornadoids-wikipedia` | C | Static reference values; engine block and inlet conditions affect output |
| Flight performance | Mach 2.2 high altitude; Mach 1.1 low level; service ceiling 15,240 m | `p5-uk-air-tornadoids-raf`; `p5-eu-air-tornadoids-wikipedia` | A/C | Public maxima; low-level speed is the relevant IDS mission limit |
| Range | Ferry about 3,900 km; combat radius 1,200-1,400 km | `p5-eu-air-tornadoids-wikipedia` | C | Bounded strike estimate; terrain-following profile and stores dominate spread |
| Crew | 2 | `p5-uk-air-tornadoids-raf`; `p5-de-air-tornadoids-bundeswehr` | A | Pilot and weapon systems officer |
| Radar | Terrain-following radar plus ground-mapping radar; effective mapping/detection bound about 80-160 km | `p5-uk-air-tornadoids-raf`; `p5-eu-air-tornadoids-wikipedia` | A/C | Exact GMR set varies by national block; range is a bounded specialist estimate |
| Avionics / EW | Inertial/Doppler navigation, terrain-following radar and radar-warning receiver; 1 TFR, 1 nav suite and 1 RWR suite | `p5-de-air-tornadoids-bundeswehr`; `p5-eu-air-tornadoids-wikipedia` | A/C | IDS baseline; German Cerberus and Italian/RAF fits are not normalized as identical |
| Armament | 2 x 27 mm Mauser BK-27 cannon, 180 rounds per gun (360 total); 9 external stations; about 9,000 kg stores | `p5-uk-air-tornadoids-raf`; `p5-it-air-tornadoids-ami`; `p5-eu-air-tornadoids-wikipedia` | A/C | JP233, Paveway, anti-radiation and conventional bomb/missile fits vary by operator |
| Mission systems | Variable-sweep 25/45/67 degree wing schedule, automatic terrain-following to about 60-200 ft (18-61 m), and two-seat strike cockpit | `p5-uk-air-tornadoids-raf`; `p5-de-air-tornadoids-bundeswehr` | A | Altitude bound is an open-source operating estimate; avoid treating it as an all-weather guarantee |
| Signature / protection | Conventional strike airframe; clean frontal RCS estimated 10-20 m2; 1 ECM suite plus 2 external chaff/flare dispenser pods, about 90-180 cartridges | `p5-eu-air-tornadoids-wikipedia` | C | RCS and countermeasure capacity are bounded specialist estimates; pod fit is operator-dependent |

## Source References

- `p5-uk-air-tornadoids-raf`: `raw/sources/royal_air_force/p5-uk-air-tornadoids-raf/manifest.md`
- `p5-de-air-tornadoids-bundeswehr`: `raw/sources/bundeswehr/p5-de-air-tornadoids-bundeswehr/manifest.md`
- `p5-it-air-tornadoids-ami`: `raw/sources/aeronautica_militare/p5-it-air-tornadoids-ami/manifest.md`
- `p5-eu-air-tornadoids-wikipedia`: `raw/sources/wikipedia/p5-eu-air-tornadoids-wikipedia/manifest.md`
