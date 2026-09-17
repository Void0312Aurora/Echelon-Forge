# Project 956 Sovremenny

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/naval/ships/surface-combatant/sovremenny/project-956/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-naval-sovremenny` |
| Family / variant | Sovremenny / Project 956 Sarych guided-missile destroyer |
| Role | Anti-ship and area air-defence surface combatant; complementary surface escort and gunfire-support platform |
| Configuration scope | Russian Navy Project 956 baseline as tabulated by Forecast International (November 2016); Project 956A, 956E/EM export ships, Chinese refits and Project 956U are excluded |
| Service context | Cold-War Soviet/Russian design; Russian ships are retained as a historical baseline rather than a current active-inventory claim |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Length overall | 155.7 m; waterline 145.0 m | `p5-ru-naval-sovremenny-forecastinternational` | C | Forecast International technical table; Naval Encyclopedia gives 156.5 m overall, so retain a 155.7-156.5 m geometry cross-check band |
| Beam | 16.8 m overall; 12.2 m waterline | `p5-ru-naval-sovremenny-forecastinternational` | C | Project 956 baseline; later export/refit geometry is excluded |
| Draft | 6.0 m normal; 8.8 m maximum | `p5-ru-naval-sovremenny-forecastinternational` | C | Loading-condition semantics are preserved; Naval Encyclopedia reports about 5.96 m average draft |
| Standard displacement | 6,500 t | `p5-ru-naval-sovremenny-forecastinternational` | C | Standard/light operating condition in the source table; not interchangeable with full-load or maximum displacement |
| Full-load displacement | 7,940 t | `p5-ru-naval-sovremenny-forecastinternational` | C | Full-load condition in the source table |
| Maximum displacement | 8,480 t | `p5-ru-naval-sovremenny-forecastinternational` | C | Source's maximum/overload stability limit; do not use as routine combat load |
| Propulsion | Two-shaft steam-turbine plant; four high-pressure boilers; two four-bladed fixed-pitch propellers | `p5-ru-naval-sovremenny-forecastinternational`; `p5-ru-naval-sovremenny-navalencyclopedia` | C | Russian Project 956 steam plant; gas-turbine and export 956E/EM machinery are excluded |
| Propulsion power | 2 x 37,000 kW, about 74 MW total (about 100,000 hp) | `p5-ru-naval-sovremenny-navalencyclopedia` | C | Naval Encyclopedia reports each turbine at 37,000 kW; horsepower is a unit conversion, not a separate rating |
| Cruising speed | 18 kt | `p5-ru-naval-sovremenny-forecastinternational` | C | Forecast table value |
| Maximum speed | 32 kt | `p5-ru-naval-sovremenny-forecastinternational` | C | Forecast table value; Naval Encyclopedia describes below 33 kt officially and up to 35 kt on some trials, retained only as a cross-check |
| Range | 3,920 nmi at 18 kt; 1,345 nmi at 32 kt | `p5-ru-naval-sovremenny-forecastinternational` | C | Two speed/load points are retained instead of one blended range |
| Endurance | 30 days | `p5-ru-naval-sovremenny-forecastinternational` | C | Stores/autonomy statement in the technical table |
| Crew | 326 (30 officers + 296 enlisted) | `p5-ru-naval-sovremenny-forecastinternational` | C | Naval Encyclopedia reports a 296-person standard service complement and up to 358 in wartime; simulation crew bound is 296-358 pending a Russian complement table |
| Aviation payload | One Ka-27 Helix or Ka-25 Hormone helicopter; one helipad and telescopic hangar | `p5-ru-naval-sovremenny-forecastinternational`; `p5-ru-naval-sovremenny-navalencyclopedia` | C | One embarked helicopter; Ka-27/Ka-25 alternatives are configuration choices, not simultaneous load |
| Sensors and combat systems | MR-760 Fregat-MP air/surface-search radar; P-80/P-270 Ekran anti-ship fire-control; Orekh/Smerch fire control; MR-184 Uragan 130 mm fire-control radar; MR-105 Turem CIWS fire-control radar; MR-212 Volga navigation radar; MG-335 Platina hull sonar; MP-405M Start and MR-407 ESM/EW | `p5-ru-naval-sovremenny-forecastinternational` | C | Named Soviet fit from the Project 956 table; exact software modes and detection envelopes are not public. Use a 30-300 km radar/engagement envelope only where a system-specific source is added |
| Main weapons | 2 x twin AK-130 130 mm L/70 multipurpose gun mounts | `p5-ru-naval-sovremenny-forecastinternational`; `p5-ru-naval-sovremenny-navalencyclopedia` | C | Four barrels total; naval gun ammunition count is not stated in the retained table |
| Anti-ship weapons | 8 x Raduga Moskit 3M80 surface-to-surface missiles | `p5-ru-naval-sovremenny-forecastinternational`; `p5-ru-naval-sovremenny-navalencyclopedia` | C | Two twin launchers per side, four missiles per launcher pair; 956A's 3M80M and Chinese YJ-series replacements are excluded |
| Air-defence weapons | 48 x 9M38M1 Smerch / SA-N-7 family SAMs in two 24-round single-arm launchers | `p5-ru-naval-sovremenny-forecastinternational` | C | Original Russian Project 956 load; later SA-N-12 and Chinese VLS fits are excluded |
| Close-in and ASW weapons | 4 x AK-630 30 mm CIWS; 4 x 533 mm torpedo tubes (4 TEST-71ME anti-ship + 4 TEST-96 ASW torpedoes listed); 2 x six-round RBU-1000 launchers | `p5-ru-naval-sovremenny-forecastinternational` | C | Source table also lists two mine rails and 40 mines/depth charges; tube/round counts are retained as loadout metadata |
| Protection / survivability | Roll stabilizer and controlled rudders for heavy-weather control; emergency auxiliary propulsion and four backup diesel generators (2,400 kW total); MP-405M/MR-407 EW/decoy suite; no public homogeneous armour thickness | `p5-ru-naval-sovremenny-navalencyclopedia`; `p5-ru-naval-sovremenny-forecastinternational` | C | Directly stated ship-control, power-backup and EW features. For simulation, use a bounded categorical `medium surface-combatant survivability` envelope, not an inferred armour-equivalent value; sea-state and damage-control performance remain cross-check items |

All target fields contain a direct value or an explicitly bounded estimate. Russian Project 956 values are not silently substituted for Project 956A/956E/956EM or Chinese refit configurations.

## Source References

- `p5-ru-naval-sovremenny-forecastinternational`
- `p5-ru-naval-sovremenny-navalencyclopedia`
