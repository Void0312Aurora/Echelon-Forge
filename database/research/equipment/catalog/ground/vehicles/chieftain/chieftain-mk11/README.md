# Chieftain Mk 11

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/chieftain/chieftain-mk11/README.md`
Owner: `database/equipment-data`
Content status: Cold-War variant parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-gb-ground-chieftainmk11` |
| Family / variant | Chieftain / FV4201 Mk 11 (late Mk 5-derived standard) |
| Service state | Late British Army Chieftain upgrade, retained into the early 1990s; Mk 11C museum vehicle is the reference configuration |
| Role | Main battle tank |
| Configuration scope | British Mk 11 with Improved Fire Control System (IFCS), TOGS and Stillbrew turret/driver-hatch armor; export Shir/Khalid and experimental 1,000 hp conversions excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | Approximately 10.8 m gun-forward length x 3.5 m width x 2.9 m height; hull length approximately 7.5 m | `p5-gb-ground-chieftainmk11-netmaquettes` / `p5-gb-ground-chieftainmk11-wikipedia` | C | Specialist Mk11 dimensional table; stowage, antenna and gun orientation conventions vary |
| Combat mass | 55 long tons (approximately 55.9 t); Stillbrew-equipped Mk11C is commonly reported at approximately 56 t | `p5-gb-ground-chieftainmk11-tankmuseum` / `p5-gb-ground-chieftainmk11-netmaquettes` | B/C | Tank Museum lists 55 tons for Chieftain Mk11C; Net-Maquettes reports 56 t combat-loaded with Stillbrew; retained as a bounded 55-56 t interval |
| Powerplant | Leyland L60 multifuel opposed-piston two-stroke diesel, approximately 750 hp | `p5-gb-ground-chieftainmk11-wikipedia` | C | Mk11 is Mk5-derived and uses the uprated L60 family; exact Mk11 engine sub-mark and derated service output require a British manual cross-check |
| Transmission | David Brown TN12 cross-drive, 6 forward / 2 reverse, triple-differential steering | `p5-gb-ground-chieftainmk11-tankmuseum` | B | Tank Museum family description; exact Mk11 gear-ratio set not published |
| Road / cross-country mobility | Up to 48 km/h public Mk11 value; practical cross-country speed bounded at 20-35 km/h | `p5-gb-ground-chieftainmk11-tankmuseum` / `p5-gb-ground-chieftainmk11-wikipedia` | B/C | Museum lists 48 kph; Wikipedia family table lists 43 km/h for Mk5, so the 43-48 km/h range is retained as a configuration uncertainty |
| Operational range | Approximately 500 km on roads | `p5-gb-ground-chieftainmk11-wikipedia` | C | Public family figure; fuel state, terrain and Stillbrew load change realized range |
| Crew | 4 (commander, gunner, loader, driver) | `p5-gb-ground-chieftainmk11-tankmuseum` | B | Museum Chieftain Mk11C fact panel |
| Main armament | 120 mm L11A5 rifled gun with separate projectile and bagged-charge ammunition | `p5-gb-ground-chieftainmk11-wikipedia` / `p5-gb-ground-chieftainmk11-netmaquettes` | C | L11A5 is the Mk11 baseline; ammunition natures and charge stowage are not normalized |
| Main-gun ammunition payload | Up to 64 projectiles; propellant charges are carried separately and not included in this count | `p5-gb-ground-chieftainmk11-wikipedia` | C | Public Chieftain stowage figure; exact Mk11 ready/stowed split and charge quantity require manual cross-check |
| Secondary armament | 2 x 7.62 mm L7 machine guns (coaxial and ranging/anti-aircraft fit) | `p5-gb-ground-chieftainmk11-wikipedia` | C | Family baseline; exact Mk11 mount/stowage arrangement is configuration-sensitive |
| Secondary ammunition payload | 3,000-5,000 x 7.62 mm rounds (bounded estimate, midpoint 4,000) | `p5-gb-ground-chieftainmk11-netmaquettes` | C | Specialist community load estimate from comparable British MBT belt stowage; no counted Mk11 inventory publicly located |
| Mission systems | Improved Fire Control System (IFCS), Thermal Observation and Gunnery System (TOGS), laser rangefinder, stabilized gun sighting and Clansman VHF radios | `p5-gb-ground-chieftainmk11-tankmuseum` / `p5-gb-ground-chieftainmk11-wikipedia` | B/C | Tank Museum confirms IFCS/TOGS on Mk11C; sensor detection and tracking performance are not published |
| Protection | Steel/composite Chieftain armor with additional Stillbrew applique on turret front and around driver hatch; NBC protection and smoke dischargers | `p5-gb-ground-chieftainmk11-tankmuseum` / `p5-gb-ground-chieftainmk11-wikipedia` | B/C | Museum explicitly identifies Stillbrew; public family table quotes up to 388 mm armor but this is not a calibrated Mk11 arc value |
| Amphibious / fording | Not amphibious; prepared/unprepared fording capability bounded at 1.2 m without deep-fording equipment and approximately 2.4 m with kit | `p5-gb-ground-chieftainmk11-wikipedia` | C | Historical family engineering bound; Mk11 kit state and preparation time require British service-manual cross-check |

All target fields contain direct values or explicitly bounded estimates. Mk11C museum configuration, generic Mk5-derived dimensions and public ammunition figures remain separated rather than silently merged.

## Source References

- `p5-gb-ground-chieftainmk11-tankmuseum`
- `p5-gb-ground-chieftainmk11-wikipedia`
- `p5-gb-ground-chieftainmk11-netmaquettes`
