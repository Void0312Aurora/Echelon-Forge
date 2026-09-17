# MiG-31B Foxhound

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/mig-31/mig-31b/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-air-mig31b` |
| Family / variant | MiG-31 / MiG-31B |
| Role | Two-seat long-range interceptor |
| Configuration scope | MiG-31B Zaslon-M/digital-datalink context; BM/D/E and later missile refits excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Length | 22.69 m | `p5-ru-air-mig31b-armyrecognition` | C | Army Recognition overall dimension |
| Wingspan | 13.46 m | `p5-ru-air-mig31b-armyrecognition` | C | Army Recognition overall dimension |
| Height | 6.15 m | `p5-ru-air-mig31b-armyrecognition` | C | Grounded configuration |
| Maximum take-off mass | 41,000 kg | `p5-ru-air-mig31b-armyrecognition` | C | Fully loaded public figure |
| Engines / thrust | 2 x D-30F6; 152-155 kN afterburning thrust each (bound) | `p5-ru-air-mig31b-armyrecognition` | C | Named engine and specialist thrust bound |
| Flight envelope | 3,000 km/h maximum; Mach 2.35-2.83 high-altitude bound; low-altitude speed about Mach 1.23 | `p5-ru-air-mig31b-armyrecognition` | C | Page reports 3,000 km/h and Mach values in separate sections |
| Range | 3,300 km maximum; combat radius 720-1,000 km estimate | `p5-ru-air-mig31b-armyrecognition` | C | Ferry/radius separated explicitly |
| Crew | 2 | `p5-ru-air-mig31b-armyrecognition` | C | Pilot and radar/intercept officer |
| Radar | Zaslon PESA/SBI-16; about 200 km detection and 120 km track for 16 m2 target; B-model Zaslon-M upgrade bound to 300-400 km large-target detection | `p5-ru-air-mig31b-armyrecognition` | C | Target-size and B/BM block differences are explicit |
| Avionics / EW | RK-RLDN ground link, APD-518 four-aircraft datalink, TWS radar, IRST, RWR and digital mission computer; 120-240 countermeasure cartridges (bound) | `p5-ru-air-mig31b-armyrecognition` | C | Group coverage and EW fit vary by modernization |
| Mission systems | Four-aircraft cooperative intercept, automatic target prioritization, navigation/situation monitoring and long-range missile mid-course updates | `p5-ru-air-mig31b-armyrecognition` | C | APD-518 group sharing direct; network latency is estimated 0.5-2 s |
| Main gun | 23 mm GSh-6-23; 260-round common baseline, 800-round page upper bound | `p5-ru-air-mig31b-armyrecognition` | C | Source discrepancy preserved as a bounded load, not hidden |
| Air-to-air weapons | 4 x R-33 under-fuselage; R-60/R-73 wing missiles; R-77 integration as later refit only | `p5-ru-air-mig31b-armyrecognition` | C | MiG-31B baseline separated from BM missile refits |
| Air-to-ground weapons | Not a baseline mission; limited stores are excluded from the B leaf | `p5-ru-air-mig31b-armyrecognition` | C | Interceptor configuration |
| Signature / protection | Large conventional metal airframe; clean frontal RCS 15-25 m2 bound; RWR/ECM, IRST and chaff/flare self-protection | `p5-ru-air-mig31b-armyrecognition` | C | RCS is specialist estimate, not a Russian specification |

All target fields contain direct values or bounded estimates; no MiG-31 family value is silently substituted.

## Source References

- `p5-ru-air-mig31b-armyrecognition`
