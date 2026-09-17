# T-72A

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/t-72/t-72a/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-ground-t72a` |
| Family / variant | T-72 / T-72A (Object 172A) |
| Role | Main battle tank |
| Configuration scope | Baseline Soviet serial T-72A, primarily 1979-1985 production; later T-72A modernization, T-72AB ERA refits, T-72M export armor, and T-72B are excluded unless stated as an alternate bound |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 9.53 m gun-forward length (6.86 m hull); 3.59 m width with side skirts (3.37 m without); 2.19 m turret-roof height | `p5-ru-ground-t72a-valka` | C | Valka serial-production dimensions; gun-rear length is 9.67 m; antenna/stowage excluded |
| Combat mass | 41,500 kg | `p5-ru-ground-t72a-valka` | C | Baseline combat-weight convention; Soviet production and export sources span about 41.0-41.5 t; ERA/refit and fuel state can add roughly 0-1.5 t (simulation bound) |
| Powerplant | V-46-6 12-cylinder multi-fuel diesel, 573 kW (about 780 hp) at 2,000 rpm | `p5-ru-ground-t72a-valka` | C | Baseline T-72A engine; late 1984-85 vehicles may receive 840 hp V-84 during overhaul, kept as a separate alternate package |
| Transmission | Mechanical synchronized gearbox, 7 forward + 1 reverse | `p5-ru-ground-t72a-valka` | C | Valka technical table; ratios and steering-control law are not published |
| Road / cross-country speed | 60 km/h road; 45 km/h cross-country | `p5-ru-ground-t72a-valka` | C | Dry-road/public maximum figures; tactical terrain model uses 20-45 km/h bounded range |
| Operational range | 460 km cross-country nominal; up to 700 km road with external fuel | `p5-ru-ground-t72a-valka` | C | Range varies with 1,200 L internal and external drums; retain 460 km as planning value and 700 km as road upper bound |
| Crew / payload | 3 crew (commander, gunner, driver); 44 x 125 mm rounds; no embarked infantry | `p5-ru-ground-t72a-valka` | C | Valka names 44 rounds; ready-carousel split is not stated for this leaf (simulation bound 22-24 carousel-ready, remainder stowed) |
| Main armament | 125 mm 2A46 smoothbore cannon, 2E28M two-axis stabilizer | `p5-ru-ground-t72a-valka` | C | Baseline T-72A gun; 2A46M replacement appears in later production and overhaul packages |
| Secondary armament / ammunition | 7.62 mm PKT coaxial (2,000 rounds); 12.7 mm NSVT anti-aircraft mount (300 rounds); 7.62 mm AKMS crew rifle (300 rounds) | `p5-ru-ground-t72a-valka` | C | Valka load table; national ammunition practices may differ |
| Mission systems | TPD-K1 laser rangefinder, TPN-3-49 active/passive gunner night sight, TNPO-168/TVNE-4B driver sights, TKN-3 commander sight, 902A Tucha smoke launchers, automatic fire suppression | `p5-ru-ground-t72a-valka` | C | Standard T-72A equipment description; sight detection/identification performance modeled as a 0.5-1.3 km night envelope, not a measured sensor limit |
| Protection | Cast turret with layered/composite frontal armor; thickened glacis; side skirts; 12-tube smoke system; anti-napalm and NBC/fire-protection systems; later Kontakt ERA is an alternate refit | `p5-ru-ground-t72a-valka` | C | Exact array/ballistic equivalence is not public; do not merge T-72M export armor or T-72AB ERA into baseline |
| Water crossing | Amphibious only as fording: 1.2 m underway, 1.8 m unprepared static, up to 5.0 m with deep-fording kit | `p5-ru-ground-t72a-valka` | C | Snorkel preparation and recovery time are configuration-dependent; vehicle does not swim |

All target fields contain a direct value or an explicitly bounded estimate. Source conflicts (41.0-41.5 t combat mass, 460 versus 700 km range, and 2A46 versus later 2A46M/840 hp overhaul packages) remain visible and are not silently normalized.

## Source References

- `p5-ru-ground-t72a-valka`
- `p5-ru-ground-t72a-mcia` (historical U.S. Marine Corps technical-study pointer; values require retrieval cross-check)
