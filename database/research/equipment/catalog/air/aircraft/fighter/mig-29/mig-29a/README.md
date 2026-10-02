# MiG-29A Fulcrum

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/mig-29/mig-29a/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-air-mig29a` |
| Family / variant | MiG-29 / MiG-29A (9.12A) |
| Role | Single-seat multirole air-superiority fighter |
| Configuration scope | Baseline 9.12A; MiG-29B/SE/SMT/M/M2 upgrades excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Length | 17.37 m | `p5-ru-air-mig29a-armyrecognition` | C | Army Recognition overall dimension |
| Wingspan | 11.4 m | `p5-ru-air-mig29a-armyrecognition` | C | Army Recognition overall dimension |
| Height | 4.73 m | `p5-ru-air-mig29a-armyrecognition` | C | Grounded configuration |
| Maximum take-off mass | 18,500 kg | `p5-ru-air-mig29a-armyrecognition` | C | Public maximum; fuel/store fit can shift about +/-1 t |
| Engines / thrust | 2 x RD-33; 81.4 kN afterburning thrust each | `p5-ru-air-mig29a-armyrecognition` | C | Page maximum thrust value |
| Flight envelope | 2,445 km/h maximum at altitude; 18,000 m ceiling; 1,500 km/h near-ground bound | `p5-ru-air-mig29a-armyrecognition` | C | Page values; low-level limit is configuration/temperature dependent |
| Range | 1,430 km maximum; 700 km near-ground bound; combat radius 550-700 km estimate | `p5-ru-air-mig29a-armyrecognition` | C | Ferry/radius separated explicitly |
| Crew | 1 | `p5-ru-air-mig29a-armyrecognition` | C | Single-seat A variant |
| Radar | N019/RP-29 Rubin coherent pulse-Doppler look-down/shoot-down; 70-102 km search bound, 70 km track bound | `p5-ru-air-mig29a-armyrecognition` | C | Target-size and aspect drive range |
| Avionics / EW | OEPS-29 IRST/laser ranger, HUD, Shchel-3UM helmet cueing, SPO-15-class RWR and active jamming station; 60-120 countermeasure cartridges (bound) | `p5-ru-air-mig29a-armyrecognition` | C | 9.12A/9.12B IFF and ECM blocks vary |
| Mission systems | Ts100 digital computer, OEPrNK-29 targeting/navigation complex, radio and IFF | `p5-ru-air-mig29a-armyrecognition` | C | Detailed software and datalink behavior not public |
| Main gun | 30 mm GSh-30-1, 150 rounds (simulation load) | `p5-ru-air-mig29a-armyrecognition` | C | Gun identity direct; ammunition is common baseline estimate |
| Air-to-air weapons | Up to 2 x R-27 and 4 x R-73 on six hardpoints | `p5-ru-air-mig29a-armyrecognition` | C | Baseline page load; later variants carry additional stores |
| Air-to-ground weapons | S-8/S-24 rockets and up to 2,000 kg bombs | `p5-ru-air-mig29a-armyrecognition` | C | Original A lacks later precision-guided integration |
| Signature / protection | Conventional metal/composite airframe; clean frontal RCS 3-5 m2 bound; RWR/ECM and chaff/flare self-protection | `p5-ru-air-mig29a-armyrecognition` | C | RCS is specialist estimate, not a Russian specification |

All target fields contain direct values or bounded estimates; no MiG-29 family value is silently substituted.

## Source References

- `p5-ru-air-mig29a-armyrecognition`
