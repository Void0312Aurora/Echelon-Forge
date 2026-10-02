# Nimitz-Class Nuclear-Powered Aircraft Carrier

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/naval/ships/aircraft-carrier/nimitz/nimitz-class/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-13`
Content status: extracted class-baseline simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-naval-nimitz` |
| Family / variant | Nimitz / CVN-68 class baseline |
| Configuration boundary | Ten CVN-68 through CVN-77 carriers. Geometry and nuclear plant are class-level; defensive weapons and sensors use a representative late-service fit. Ford-class carriers and individual ship refits are excluded. |
| Role | Nuclear-powered fleet aircraft carrier and mobile aviation base |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Hull dimensions | 333 m overall length x 76.8 m flight-deck beam x approximately 11.3 m draft | `p5-us-naval-nimitz-factfile`; `p5-us-naval-nimitz-navaltechnology` | A/B | Flight-deck beam is distinguished from waterline beam (approximately 40.8 m); draft changes with load. |
| Displacement (standard proxy) | Approximately 88,000-90,000 long tons | `p5-us-naval-nimitz-navaltechnology`; `p5-us-naval-nimitz-globalsecurity` | B/C | Navy material generally reports full-load displacement. Standard proxy is a bounded light/normal-load estimate for simulation. |
| Displacement (full load) | Approximately 97,000-100,000 long tons | `p5-us-naval-nimitz-factfile` | A | Early ships cluster near 97,000 LT; later refits and stores approach 100,000 LT. |
| Propulsion / power | Two Westinghouse A4W pressurized-water reactors, four shafts, approximately 260,000 shp | `p5-us-naval-nimitz-factfile`; `p5-us-naval-nimitz-navaltechnology` | A/B | Plant rating is class public data; reactor availability and shaft loading are operational state variables. |
| Speed / endurance | 30+ knots; nuclear range between refuelling; conservative operational range bound of 10,000+ nmi per deployment; approximately 90 days stores endurance and about 20 years between planned refuelling overhauls | `p5-us-naval-nimitz-factfile`; `p5-us-naval-nimitz-globalsecurity` | A/C | 30+ knots is the public threshold. The 10,000+ nmi figure is a lower-bound planning estimate; stores and maintenance, not reactor fuel, limit deployment duration. |
| Crew / aviation | Approximately 3,000 ship's company plus 2,000-2,500 air-wing personnel; 60-90 embarked aircraft depending carrier air wing | `p5-us-naval-nimitz-factfile`; `p5-us-naval-nimitz-navaltechnology` | A/B | Air-wing count is a bounded deployment range including fighters, tankers, AEW, helicopters, and logistics aircraft; exact CVW composition is scenario data. |
| Sensors / combat system | AN/SPS-48E 3-D air-search, AN/SPS-49 2-D air-search, AN/SPQ-9B surface/gunfire radar, AN/SPN-41/46 precision-approach systems, AN/SLQ-32 EW, Ship Self-Defense System with Cooperative Engagement Capability where refitted | `p5-us-naval-nimitz-factfile`; `p5-us-naval-nimitz-globalsecurity` | A/C | Radar and SSDS baselines vary by ship and modernization; the named suite is a late-service representative fit. |
| Weapons / payload | Two Mk 29 Sea Sparrow launchers; two RAM launchers on refitted ships; three to four Phalanx CIWS mounts; two Mk 38 25 mm mounts; embarked air wing carries the primary strike payload | `p5-us-naval-nimitz-factfile`; `p5-us-naval-nimitz-navaltechnology` | A/B | Early ships had different CIWS/RAM counts. Aircraft weapons are not counted as fixed ship magazines. |
| Protection / survivability | Compartmented high-strength-steel hull, armored flight-deck and hangar fire boundaries, Kevlar/splinter protection around vital spaces, multiple redundant fire-main and electrical zones, four separated machinery rooms | `p5-us-naval-nimitz-factfile`; `p5-us-naval-nimitz-globalsecurity` | A/C | Public sources do not release an armor schedule. Simulation bound for localized splinter/armor protection is 25-75 mm steel-equivalent; explicit engineering estimate, not a published thickness. |

## Source References

- `p5-us-naval-nimitz-factfile`
- `p5-us-naval-nimitz-navaltechnology`
- `p5-us-naval-nimitz-globalsecurity`
