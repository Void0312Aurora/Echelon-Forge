# Panzerhaubitze 2000

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/pzh-2000/pzh-2000/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-de-ground-pzh2000` |
| Family / variant | Panzerhaubitze 2000 / PzH 2000 |
| Role | Tracked self-propelled howitzer |
| Configuration scope | German Bundeswehr PzH 2000 reference configuration; export-specific upgrades excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Combat mass | 57 t | `p5-de-ground-pzh2000-bundeswehr` | B | Bundeswehr page Gefechtsgewicht; retrofit/munition fit can shift mass by roughly +/-1.7 t (simulation bound) |
| Length | 11.7 m | `p5-de-ground-pzh2000-bundeswehr` | B | Bundeswehr technical-data figure; Army Recognition gives 11.66 m |
| Width | 3.6 m | `p5-de-ground-pzh2000-bundeswehr` | B | Bundeswehr technical-data figure; Army Recognition gives 3.58 m |
| Height | 3.5 m | `p5-de-ground-pzh2000-bundeswehr` | B | Bundeswehr technical-data figure; Army Recognition gives 3.46 m |
| Engine | MTU 881 Ka-500 diesel, 1,000 hp (735-736 kW) | `p5-de-ground-pzh2000-bundeswehr` | B | Government page and Army Recognition agree on nominal output |
| Transmission | HSWL284C/Renk HSWL 284 automatic hydromechanical steering/transmission, 4 forward + 2 reverse gears | `p5-de-ground-pzh2000-bundeswehr` | B | Army Recognition supplies gear count; shift logic and torque curve are bounded for simulation, not measured |
| Road speed | 60 km/h | `p5-de-ground-pzh2000-bundeswehr` | B | Maximum road speed; tactical cross-country model uses a bounded 15-45 km/h range |
| Operational range | 420 km | `p5-de-ground-pzh2000-bundeswehr` | B | Approximate range at around 1,000 L fuel; simulation reserve bound is 10-20% |
| Crew | 5 nominal; 3-person degraded automatic-loading operation | `p5-de-ground-pzh2000-bundeswehr` | B | Bundeswehr page states five-person regular crew and three-person degraded operation |
| Ammunition payload | 60 x 155 mm artillery projectiles | `p5-de-ground-pzh2000-bundeswehr` | B | Bundeswehr page states 60-round magazine/combat load |
| Primer magazine | 32 standard primers | `p5-de-ground-pzh2000-armyrecognition` | C | Army Recognition technical description |
| Propellant charge payload | 60 complete charge sets; 60-360 individual modular-charge bound | `p5-de-ground-pzh2000-armyrecognition` | C | One charge set per shell; 1-6 modules per 155 mm round is an explicit simulation bound, not a counted vehicle load |
| Main armament | Rheinmetall 155 mm L/52 cannon, 360 deg traverse, +65/-2.5 deg elevation; 30 km standard / 40 km base-bleed range | `p5-de-ground-pzh2000-armyrecognition` | C | Direct Army Recognition technical data; firing-rate ceiling 10 rounds/min |
| Secondary armament | 7.62 mm MG3 anti-aircraft machine gun | `p5-de-ground-pzh2000-armyrecognition` | C | Mount location and caliber are direct; ammunition represented as a bound below |
| Secondary ammunition payload | 500-2,000 x 7.62 mm rounds, nominal simulation value 1,000 | `p5-de-ground-pzh2000-armyrecognition` | C | Bounded load estimate for vehicle MG; exact German fit is not published on the cited pages |
| Mission systems | Digital fire-control computer with NABK, panoramic day/night sight, laser rangefinder, direct-fire sight, muzzle-velocity measurement, GPS/INS, data-radio link and automatic loader | `p5-de-ground-pzh2000-armyrecognition` | C | Page lists autonomous ballistic/navigation functions; reaction time modeled with a 5-15 s command-to-lay bound |
| Protection | Welded steel hull/turret against small arms and artillery fragments; NBC protection/ventilation; 8 x 76 mm smoke dischargers | `p5-de-ground-pzh2000-bundeswehr` | B | Bundeswehr protection statement and smoke-system detail; equivalent armour thickness is intentionally modeled categorically |
| Amphibious capability | No swimming capability; tracked land vehicle, prepared crossing only | `p5-de-ground-pzh2000-bundeswehr` | B | Simulation sets water propulsion to zero and treats unprepared water crossing as unavailable |

All target fields now contain a direct value or an explicitly bounded simulation estimate; export retrofit and family values are not silently substituted.

## Source References

- `p5-de-ground-pzh2000-bundeswehr`
- `p5-de-ground-pzh2000-armyrecognition`
