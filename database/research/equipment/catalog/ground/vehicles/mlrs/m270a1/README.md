# M270A1 Multiple Launch Rocket System

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/mlrs/m270a1/README.md`
Owner: `database/equipment-data`
Content status: post-Cold-War variant parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-m270a1` |
| Family / variant | Multiple Launch Rocket System / M270A1 |
| Service state | Improved MLRS launcher with IFCS/ILMS, fielded from 2002; M270A0 and M270A2 are separate configurations |
| Role | Tracked precision rocket and tactical-missile artillery launcher |
| Configuration scope | US Army M270A1 on M993A1 Bradley-derived carrier with M269 launcher-loader; European EFCS and M270A2 common-fire-control upgrades excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | Approximately 6.90 m length x 2.97 m width x 2.60 m height | `p5-us-ground-m270a1-armyguide` | C | Army Guide public M270A1 table; launcher elevation/stowage and antenna convention not itemized |
| Mass semantics | 20,494 kg launcher curb/empty; 25,214 kg curb with payload and crew; alternate Army handbook combat figure 57,544 lb (26,100 kg) | `p5-us-ground-m270a1-wsh2011` / `p5-us-ground-m270a1-wsh2020` | A | Curb, payloaded and combat conventions are distinct; handbook revisions differ and are retained as a 25.2-26.1 t loaded bound |
| Powerplant | Cummins VTA-903T500 turbocharged diesel, approximately 500 hp | `p5-us-ground-m270a1-armyguide` / `p5-us-ground-m270a1-fas` | C | Bradley-derived carrier engine family; exact serial/block rating not published in A1 public table |
| Transmission | HMPT-500 hydromechanical automatic, 3 forward / 1 reverse range | `p5-us-ground-m270a1-armyguide` | C | Army Guide parts table; detailed ratios and control software are not public |
| Road / terrain mobility | Up to 65 km/h; 60 deg slope and 1 m vertical wall; pivot steering | `p5-us-ground-m270a1-wsh2011` / `p5-us-ground-m270a1-fas` | A/B | Government handbook gives 65 km/h and obstacles; FAS gives the same 60 deg/1 m bounds |
| Operational range | Approximately 483 km (300 mi) at 25 mph; 640 km appears in a later Army handbook as a revised maximum-cruising figure | `p5-us-ground-m270a1-wsh2011` / `p5-us-ground-m270a1-wsh2020` | A | Retain 483-640 km public range interval pending fuel/mission-load normalization |
| Crew | 3 launcher crew | `p5-us-ground-m270a1-wsh2011` / `p5-us-ground-m270a1-fas` | A/B | Crew is vehicle complement; ammunition resupply and command-post staff excluded |
| Launcher payload | Two launch pods (LP/C); each pod holds six 227 mm GMLRS/MLRS rockets or one ATACMS missile, for 12 rockets or 2 missiles total | `p5-us-ground-m270a1-wsh2011` / `p5-us-ground-m270a1-fas` | A/B | Mutually exclusive pod states; exact rocket/missile block and warhead are munition-level records |
| Mission systems | Improved Fire Control System with GPS-aided position/navigation, meteorological sensor, digital launcher interface and embedded-munition support; Improved Launcher Mechanical System reduces aim/reload time; onboard self-loading crane | `p5-us-ground-m270a1-fas` / `p5-us-ground-m270a1-armyguide` | B/C | IFCS/ILMS functions are direct program descriptions; exact processing latency and targeting network are not disclosed |
| Fire mission performance | 12-rocket ripple in approximately 1 minute; ILMS aim time about 16 s and reload about 3 minutes; engagement envelope 8-300 km depending munition | `p5-us-ground-m270a1-wsh2011` / `p5-us-ground-m270a1-armyguide` | A/C | Rates and ranges are munition/sequence dependent; not weapon flight-performance claims for every MFOM round |
| Protection | Armored Bradley-derived carrier cab/hull against small arms and fragments; blast panels protect exposed launcher areas during firing; no calibrated armor thickness public | `p5-us-ground-m270a1-fas` / `p5-us-ground-m270a1-redstone` | B | Qualitative protection only; M270A2 improved armored cab is excluded |
| Amphibious / fording | Not amphibious; M270 carrier operator data bounds water fording at approximately 1.02 m without swimming capability | `p5-us-ground-m270a1-tm9142564610` | C | Legacy operator-manual carrier value; A1 suspension/armor updates may alter practical depth and require technical-manual cross-check |

All target fields contain direct values or explicitly bounded estimates. Curb, payloaded and combat mass, plus 483/640 km range conventions, remain explicit rather than collapsed.

## Source References

- `p5-us-ground-m270a1-wsh2020`
- `p5-us-ground-m270a1-wsh2011`
- `p5-us-ground-m270a1-fas`
- `p5-us-ground-m270a1-armyguide`
- `p5-us-ground-m270a1-tm9142564610`
- `p5-us-ground-m270a1-redstone`
