# Su-27S Flanker-B

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/su-27/su-27s/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-air-su27s` |
| Family / variant | Su-27 / Su-27S (Flanker-B) |
| Role | Single-seat air-superiority fighter |
| Configuration scope | Initial-production Su-27S; Su-27P/UB/SK and Su-35 derivatives excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Length | 21.9 m | `p5-ru-air-su27s-armyrecognition` | C | Army Recognition overall dimension |
| Wingspan | 14.7 m | `p5-ru-air-su27s-armyrecognition` | C | Army Recognition overall dimension |
| Height | 5.92 m | `p5-ru-air-su27s-armyrecognition` | C | Grounded configuration; stores/antennas excluded |
| Maximum take-off mass | 30,450 kg | `p5-ru-air-su27s-armyrecognition` | C | Public maximum; fuel/store fit can shift about +/-1.5 t |
| Engines / thrust | 2 x AL-31F; 122-125 kN afterburning thrust each (bound) | `p5-ru-air-su27s-armyrecognition` | C | Engine name direct; thrust is a named-engine engineering bound |
| Flight envelope | 2,500 km/h maximum; service ceiling 18,500 m (simulation bound) | `p5-ru-air-su27s-armyrecognition` | C | Speed direct; ceiling is a Su-27S specialist bound |
| Range | 3,530 km maximum ferry range; combat radius 1,000-1,500 km bound | `p5-ru-air-su27s-armyrecognition` | C | Ferry/radius are not interchangeable; radius is an explicit estimate |
| Crew | 1 | `p5-ru-air-su27s-armyrecognition` | C | Single-seat S variant |
| Radar | N001 Zhuk coherent pulse-Doppler, look-down/shoot-down and track-while-scan; 80-100 km fighter-class detection bound | `p5-ru-air-su27s-armyrecognition` | C | Range is a target-size/configuration estimate |
| Avionics / EW | OLS-27 IRST/laser rangefinder, SPO-15-class RWR and self-protection ECM; 96-192 chaff/flare cartridges (bound) | `p5-ru-air-su27s-armyrecognition` | C | ECM/dispenser fit varies by S/P production block |
| Mission systems | Analog/digital weapons-control suite, helmet-cued IR missile employment and air-superiority datalink/radio | `p5-ru-air-su27s-armyrecognition` | C | Detailed software and datalink message set not public |
| Main gun | 30 mm GSh-30-1, approximately 150 rounds (simulation load) | `p5-ru-air-su27s-armyrecognition` | C | Gun direct; ammunition is common baseline estimate |
| Air-to-air weapons | R-27 family and R-73; up to 10 external stations | `p5-ru-air-su27s-armyrecognition` | C | Station count direct; exact tactical mix varies |
| Air-to-ground weapons | 100/250/500 kg bombs, RBK cluster bombs, S-8/S-13/S-25 rockets | `p5-ru-air-su27s-armyrecognition` | C | Legacy Su-27S wiring and role limits apply |
| Signature / protection | Conventional non-stealth metal/titanium airframe; clean frontal RCS 10-15 m2 bound; RWR/ECM and chaff/flare self-protection | `p5-ru-air-su27s-armyrecognition` | C | RCS is a specialist estimate, not a Russian specification |

All target fields contain direct values or bounded estimates; no Su-27 family value is silently substituted.

## Source References

- `p5-ru-air-su27s-armyrecognition`
