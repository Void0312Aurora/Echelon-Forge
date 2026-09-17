# CV90 Mk IV

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/cv90/cv90mk4/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-eu-ground-cv90mk4` |
| Family / variant | CV90 / Mk IV (representative D35/CV9035 IFV fit) |
| Role | Tracked infantry fighting vehicle |
| Configuration scope | Mk IV hull/electronic/mobility baseline from ODIN and BAE Systems; representative European 35 mm D35/CV9035 turret selected for firepower/payload. 30 mm E30, Swedish 40 mm and 50 mm demonstrator/customer fits are alternatives, not merged |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 6.47 m length x 3.19 m width x 2.50 m height | `p5-eu-ground-cv90mk4-odin` | B | ODIN Mk IV card; antenna, sight mast and gun-forward state may increase envelope |
| Mass semantics | 35 t baseline to 38 t Mk IV gross-vehicle-weight rating; representative combat mass bounded at 35-37 t | `p5-eu-ground-cv90mk4-bae` / `p5-eu-ground-cv90mk4-cv90cz` | A/C | BAE states GVWR increased from 35 to 38 t and 3 t payload growth; 35-37 t is an explicit simulation bound for turret/armor/load state, not a published universal curb mass |
| Powerplant | Scania diesel, up to 1,000 hp | `p5-eu-ground-cv90mk4-bae` | A | New Mk IV engine; exact Scania model and governed output depend on customer |
| Transmission | Upgraded X300 heavy-duty automatic transmission | `p5-eu-ground-cv90mk4-bae` | A | BAE Mk IV statement; gear ratios and software variant are not public |
| Road / tactical speed | 70 km/h road; active damping is intended to preserve higher terrain speeds | `p5-eu-ground-cv90mk4-odin` / `p5-eu-ground-cv90mk4-bae` | B/A | 70 km/h is ODIN Mk IV maximum; no official cross-country maximum is published, so simulation uses a bounded 35-55 km/h tactical range |
| Operational range | 350 km road planning value; older CV90 family brochures quote up to 900 km | `p5-eu-ground-cv90mk4-odin` / `p5-eu-ground-cv90mk4-baebrochure` | B/C | 350 km is Mk IV ODIN value; 900 km belongs earlier/light CV90 family fuel configuration and is not substituted |
| Crew / payload | 3 crew + 8 infantry (ODIN Mk IV); representative D35/CV9035 load 203 x 35 mm rounds, approximately 70 ready (35 per feed) | `p5-eu-ground-cv90mk4-odin` / `p5-eu-ground-cv90mk4-defensie` / `p5-eu-ground-cv90mk4-czdefence` | B/A/C | Passenger count is Mk IV card; Dutch MoD 3+7 applies CV9035NL Mk III hull; 203/70 ammunition is export 35 mm turret data and must be rechecked for each Mk IV customer |
| Main armament | Representative 35 mm Bushmaster III automatic cannon in D35/CV9035 turret; programmable airburst and AP ammunition families | `p5-eu-ground-cv90mk4-defensie` / `p5-eu-ground-cv90mk4-czdefence` | A/C | Mk IV accepts 30/35/40/50 mm and larger customer weapons; 35 mm is selected only as the European baseline fit |
| Secondary armament | 7.62 mm coaxial machine gun; smoke/fragmentation grenade launchers; optional ATGM/APS turret modules | `p5-eu-ground-cv90mk4-defensie` / `p5-eu-ground-cv90mk4-bae` | A | Dutch MoD weapon statement is CV9035NL-specific; Mk IV D-series supports ATGM and APS modules, customer fit unresolved |
| Secondary ammunition payload | 7.62 mm coaxial load 2,000-3,000 rounds (simulation bound); smoke stores represented as 2 banks, count customer-dependent | `p5-eu-ground-cv90mk4-defensie` | A/C | No Mk IV public counted load; bound follows comparable NATO IFV stowage and is explicitly estimated |
| Mission systems | Fourth-generation electronic architecture/NGVA backbone, iFighting 360-degree cameras and decision aids, stabilized day/thermal sights, laser rangefinder, hunter-killer FCS, digital BMS/C4I; active damping and optional Iron Fist APS | `p5-eu-ground-cv90mk4-bae` / `p5-eu-ground-cv90mk4-cv90cz` | A/C | Sensor/AI functions are architecture claims; detection ranges, latency and radio fit are not published |
| Protection | Modular ballistic armor; representative Mk IV customer package STANAG 4569 Level 5 ballistic and Level 4A/4B mine/IED context; qualified active-protection system available | `p5-eu-ground-cv90mk4-bae` / `p5-eu-ground-cv90mk4-cv90cz` | A/C | Exact armor arrays and customer kit are not public; Czech offer and older BAE brochure describe different protection levels, so no single RHAe or arc thickness is inferred |
| Water crossing | Fording approximately 1.5 m for CV90 family; no swimming capability claimed for Mk IV | `p5-eu-ground-cv90mk4-baebrochure` | C | Brochure family value; Mk IV customer-specific sealing/deep-fording kit requires cross-check |

All target fields contain a direct value or an explicitly bounded estimate. CV90 Mk IV has a genuine configuration spread: customer turrets (30/35/40/50/120 mm), passenger counts (7-8), 35-38 t mass states, and APS/armor kits must not be collapsed into one universal record.

## Source References

- `p5-eu-ground-cv90mk4-odin`
- `p5-eu-ground-cv90mk4-bae`
- `p5-eu-ground-cv90mk4-baebrochure`
- `p5-eu-ground-cv90mk4-defensie`
- `p5-eu-ground-cv90mk4-czdefence`
- `p5-eu-ground-cv90mk4-cv90cz`
