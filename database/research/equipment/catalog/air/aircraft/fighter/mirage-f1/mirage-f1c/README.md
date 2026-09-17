# Mirage F1C

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/mirage-f1/mirage-f1c/README.md`
Owner: `database/equipment-data`
Content status: Variant-specific Cold-War parameter draft; bounded estimates are labelled and are not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-fr-air-miragef1` |
| Family / variant | Mirage F1 / F1C |
| Role | Single-seat air-defence fighter |
| Configuration boundary | French F1C interceptor baseline; F1CR/F1CT strike-recce and export variants are excluded |

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| French Air Force | Retired from frontline service; Cold-War reference configuration | `p5-fr-air-miragef1-mindef` |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 15.30 m length; 8.40 m span; 4.50 m height | `p5-fr-air-miragef1-dassault` | A | F1C basic airframe |
| Empty mass | 7,400 kg | `p5-fr-air-miragef1-dassault`; `p5-fr-air-miragef1-wikipedia` | A/C | Basic aircraft, no stores |
| Maximum takeoff mass | 16,200 kg | `p5-fr-air-miragef1-dassault` | A | F1C structural maximum |
| Internal fuel mass | 3,500-4,000 kg | `p5-fr-air-miragef1-wikipedia` | C | 4,300 L class internal capacity converted to fuel mass; usable fraction varies |
| Powerplant | 1 x SNECMA Atar 9K-50 afterburning turbojet | `p5-fr-air-miragef1-dassault` | A | F1C engine fit |
| Thrust | 49.0 kN dry; 70.6 kN afterburning | `p5-fr-air-miragef1-dassault`; `p5-fr-air-miragef1-wikipedia` | A/C | Sea-level static reference thrust |
| Flight performance | Mach 2.20 (about 2,338 km/h); service ceiling 20,000 m; climb about 243 m/s | `p5-fr-air-miragef1-dassault`; `p5-fr-air-miragef1-wikipedia` | A/C | Clean/high-altitude maxima |
| Range | Ferry about 3,300 km; combat radius 500-650 km | `p5-fr-air-miragef1-wikipedia` | C | Bounded interceptor/strike estimate; external tanks and loiter change range |
| Crew | 1 | `p5-fr-air-miragef1-mindef` | A | Single-seat F1C cockpit |
| Radar | Thomson-CSF Cyrano IV-1 pulse-Doppler radar; open detection bound 40-50 km | `p5-fr-air-miragef1-mindef`; `p5-fr-air-miragef1-wikipedia` | A/C | F1C interceptor radar; Cyrano variants are not merged |
| Avionics / EW | Central navigation/attack computer, inertial platform and radar-warning receiver; 1 INS, 1 radar and 1 RWR receiver | `p5-fr-air-miragef1-mindef`; `p5-fr-air-miragef1-wikipedia` | A/C | Exact French block and later ECM retrofit vary |
| Armament | 2 x 30 mm DEFA 553 cannon, 150 rounds per gun (300 total); 7 external stations; about 6,300 kg stores | `p5-fr-air-miragef1-dassault`; `p5-fr-air-miragef1-wikipedia` | A/C | Matra Super 530F and R.550 Magic family fit is loadout-dependent |
| Mission systems | Air-intercept fire-control and navigation/attack system; 7 stores stations | `p5-fr-air-miragef1-mindef`; `p5-fr-air-miragef1-wikipedia` | A/C | Functional statement for F1C, not F1CR reconnaissance equipment |
| Signature / protection | Conventional metal airframe; clean frontal RCS estimated 5-10 m2; 1 RWR/ECM suite plus 2 chaff/flare dispenser banks, about 60-90 cartridges | `p5-fr-air-miragef1-wikipedia` | C | RCS and dispenser capacity are bounded specialist estimates, not French MoD specifications |

## Source References

- `p5-fr-air-miragef1-mindef`: `raw/sources/ministere_des_armees/p5-fr-air-miragef1-mindef/manifest.md`
- `p5-fr-air-miragef1-dassault`: `raw/sources/dassault_aviation/p5-fr-air-miragef1-dassault/manifest.md`
- `p5-fr-air-miragef1-wikipedia`: `raw/sources/wikipedia/p5-fr-air-miragef1-wikipedia/manifest.md`
