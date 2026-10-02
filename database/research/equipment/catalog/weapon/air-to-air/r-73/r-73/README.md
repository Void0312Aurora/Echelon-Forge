# Vympel R-73 (AA-11 Archer)

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/air-to-air/r-73/r-73/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-weapon-r73` |
| Family / variant | R-73 / baseline R-73A/E (AA-11 Archer) |
| Role | Short-range all-aspect infrared-guided air-to-air missile |
| Configuration boundary | Baseline R-73A/E geometry and seeker; R-73M/R-74M extended-range upgrades and export-specific electronics are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 105 kg launch mass | `p5-ru-weapon-r73-roe`; `p5-ru-weapon-r73-globalsecurity` | C | Export and domestic rounds are within a few kilograms; rail and launcher excluded |
| Dimensions | 2.90-2.93 m length; 170 mm body diameter; 510 mm stabilizer span; 375-395 mm control-surface span | `p5-ru-weapon-r73-roe`; `p5-ru-weapon-r73-globalsecurity` | C | Public references round diameter to 165-170 mm; 170 mm is used for simulation envelope |
| Propulsion / motor | Single-chamber high-impulse solid rocket motor with gas-dynamic thrust-vector control; 7.5-8.0 kN thrust bound | `p5-ru-weapon-r73-globalsecurity` | C | Motor burn time and exact thrust schedule are not public; thrust interval is a specialist estimate |
| Guidance / seeker | Passive cooled infrared seeker, all-aspect lock-before-launch, proportional navigation; high off-boresight cueing from helmet-mounted sight | `p5-ru-weapon-r73-roe`; `p5-ru-weapon-r73-globalsecurity` | C | Seeker gimbal/IRCCM block differs by R-73A/E lot; baseline functional behavior retained |
| Range / flight envelope | 0.3 km minimum rear-hemisphere launch; up to 30 km front-hemisphere aerodynamic bound; Mach 2.5 class; target altitude roughly 0.02-20 km and up to 12 g target maneuver | `p5-ru-weapon-r73-roe`; `p5-ru-weapon-r73-globalsecurity` | C | 30 km is a kinematic/public maximum, not a guaranteed hit range; aspect, closure and seeker lock dominate |
| Warhead | 7.4-8.0 kg continuous-rod high-explosive fragmentation warhead | `p5-ru-weapon-r73-roe`; `p5-ru-weapon-r73-globalsecurity` | C | Public export sheets round to 8 kg; rod geometry and explosive fill are not public |
| Fuze / trigger | Active radar proximity fuze with impact backup; R-73EL uses laser proximity variant | `p5-ru-weapon-r73-globalsecurity` | C | Baseline leaf uses radar proximity plus impact; laser-fuze export subvariant excluded |

## Source References

- `p5-ru-weapon-r73-roe`: `raw/sources/rosoboronexport/p5-ru-weapon-r73-roe/manifest.md`
- `p5-ru-weapon-r73-globalsecurity`: `raw/sources/globalsecurity/p5-ru-weapon-r73-globalsecurity/manifest.md`
