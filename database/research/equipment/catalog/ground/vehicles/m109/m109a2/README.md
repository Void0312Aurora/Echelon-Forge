# M109A2 155 mm Self-Propelled Howitzer

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/m109/m109a2/README.md`
Owner: `database/equipment-data`
Content status: Cold-War variant parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-m109a2` |
| Family / variant | M109 / M109A2 |
| Service state | US Army M109A2 RAM-improved Cold-War baseline, fielded from 1979; A3/A4/A5/A6/A7 are separate leaves |
| Role | Self-propelled 155 mm artillery system |
| Configuration scope | M109A2 with M185 cannon in M178 mount, standard US Army powerpack and six-person section; export K55 and national upgrades excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 9.12-9.13 m length with gun forward x 3.15 m width x 3.06-3.28 m height; hull-only length 6.19 m | `p5-us-ground-m109a2-tm92350311` / `p5-us-ground-m109a2-tm9235031134` | A | TM operator/maintenance tables differ on height convention (120.43 in overall versus 10 ft 9 in with ADMG); both retained |
| Mass semantics | 23,586 kg empty (less crew, fuel and stowage); 24,948 kg combat loaded; 25,000 kg travel-weight handbook convention | `p5-us-ground-m109a2-tm9235031134` / `p5-us-ground-m109a2-tm92350311` | A/B | Empty, combat and travel semantics are kept distinct; no single mass is silently substituted |
| Powerplant | Detroit Diesel/GM 8V71T 2-stroke turbocharged diesel, 405 hp at 2,300 rpm; low-heat-rejection 440 hp engine is an alternate maintenance fit | `p5-us-ground-m109a2-tm92350311` | A | Standard M109A2 engine is 405 hp; 440 hp LHR option is retained as an alternate, not blended |
| Transmission | Allison XTG-411-2A cross-drive, 4 forward / 2 reverse speeds | `p5-us-ground-m109a2-historynet` | C | Public historical specification; TM describes mechanically/hydraulically operated 4-forward/2-reverse transmission |
| Road / cross-country mobility | 56 km/h (35 mph) governed road speed; approximately 19 km/h cross-country bound; 60% grade, 1.83 m trench, 0.53 m vertical wall | `p5-us-ground-m109a2-tm92350311` / `p5-us-ground-m109a2-historynet` | A/C | Cross-country value is a bounded historical estimate; road speed and obstacles are manual data |
| Operational range | 349-354 km (217-220 mi) at standard fuel load | `p5-us-ground-m109a2-tm92350311` / `p5-us-ground-m109a2-tm9235031134` | A | Public manual revisions differ by 5 km; fuel and terrain state drive the interval |
| Crew / section payload | 6 crew (commander, gunner, driver, 3 ammunition servers); normal section size 8 | `p5-us-ground-m109a2-historynet` / `p5-us-ground-m109a2-tm9235031134` | A/C | Crew is vehicle complement; section size includes support personnel outside the vehicle |
| Main armament | 155 mm/39-cal M185 rifled howitzer in M178 mount; -3 to +75 deg elevation, 360 deg traverse | `p5-us-ground-m109a2-tm92350311` / `p5-us-ground-m109a2-tm9235031134` | A | M185/M178 is the A2 configuration; M284/M182 belongs to A5+ and is excluded |
| Main-gun ammunition payload | 36 complete 155 mm rounds, typically 22 long-wheelbase and 12 conventional plus 2 Copperhead in the historical breakdown | `p5-us-ground-m109a2-historynet` / `p5-us-ground-m109a2-armyhandbook` | B/C | 36-round M109A2 bustle capacity is direct; exact natures vary by fire mission |
| Secondary armament / ammunition | Flexible turret-mounted .50 cal M2HB; 500-round public load | `p5-us-ground-m109a2-historynet` | C | Historical specification; M2HB stowage can vary by unit issue |
| Mission systems | M117/M117A2 panoramic telescope, M118A2/M118A3 elbow telescope, M15 quadrant, M140/M140A1 boresight alignment device, ballistic telescope cover and hydraulic gun-laying system | `p5-us-ground-m109a2-tm92350311` | A | Sighting equipment is named in the operator and fire-control manuals; no digital GPS fire-control is assumed for baseline A2 |
| Protection | Light-alloy armored hull/turret (approximately 20 mm maximum public value), ballistic shield for panoramic telescope, NBC/collective-protection and fire-suppression provisions | `p5-us-ground-m109a2-armyhandbook` / `p5-us-ground-m109a2-tm92350311` | B/A | Public armor thickness is a broad value, not an arc-calibrated RHAe figure; kit state is configuration-sensitive |
| Amphibious / fording | Not amphibious in normal configuration; fording depth approximately 1.0-1.14 m, with flotation-airbag kits historically enabling deeper emergency crossing | `p5-us-ground-m109a2-tm92350311` / `p5-us-ground-m109a2-armyhandbook` | A/B | Manual gives 3 ft 6 in (1.07 m); handbook gives 1.14 m and notes flotation airbags; no swimming performance assumed |

All target fields contain direct values or explicitly bounded estimates. M109A2/A3/A4 shared manual values are restricted to the A2 configuration semantics above; later Paladin values are not backfilled.

## Source References

- `p5-us-ground-m109a2-tm92350311`
- `p5-us-ground-m109a2-tm9235031134`
- `p5-us-ground-m109a2-historynet`
- `p5-us-ground-m109a2-armyhandbook`
