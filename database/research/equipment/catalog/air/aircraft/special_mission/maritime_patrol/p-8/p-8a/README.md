# P-8A Poseidon / Poseidon MRA1

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/special_mission/maritime_patrol/p-8/p-8a/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-22`
Equipment ID: `eq-uk-air-p8a`
Content status: parameter table complete for the UK Poseidon MRA1/P-8A; Boeing common performance values and RAF-specific mission-system rows remain separated.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United Kingdom | In service | `p5-uk-air-p8a-raf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Thrust | 27,000 lb each | `p5-uk-air-p8a-raf` | A |
| Powerplant | Two CFM56-7B/7BE turbofan engines | `p5-uk-air-p8a-raf`; `p5-uk-air-p8a-boeing` | A/B |
| Length | 39.47 m | `p5-uk-air-p8a-raf` | A |
| Height | 13.03 m | `p5-uk-air-p8a-raf` | A |
| Wingspan | 37.64 m | `p5-uk-air-p8a-raf` | A |
| Maximum speed | 490 kt | `p5-uk-air-p8a-raf` | A |
| Maximum altitude | 41,000 ft | `p5-uk-air-p8a-raf` | A |
| Aircrew | 2 pilots, 1 tactical coordinator, 5 weapon-system operators | `p5-uk-air-p8a-raf` | A |
| Maximum gross takeoff weight | 189,200 lb (85,820 kg) | `p5-uk-air-p8a-boeing` | B |
| Range / station time | 1,200+ nmi with more than four hours on station | `p5-uk-air-p8a-boeing` | B (conditioned) |
| Weapon systems | Anti-shipping missiles and Mk54 torpedoes; compatibility includes Harpoon, Mk54 and up to 129 A-size sonobuoys | `p5-uk-air-p8a-raf`; `p5-uk-air-p8a-boeing` | A/B |
| Sensors / mission system | APY-10 radar; AN/AQQ-2(V)1 sonobuoy processor; MX-20 HD EO/IR; acoustics, ESM and ISAR mission suite | `p5-uk-air-p8a-raf`; `p5-uk-air-p8a-boeing` | A/B |
| Defensive aids | Directed-infrared countermeasure, missile approach warning and countermeasure dispenser | `p5-uk-air-p8a-raf` | A |

## Configuration Boundary

The RAF page is the source of record for the UK MRA1's crew, sensors, defensive aids and mission weapons. Boeing supplies the common P-8A engine designation, maximum gross takeoff weight and the range figure, whose more-than-four-hours-on-station condition is retained. No fixed UK mission loadout or software increment is inferred.

## Source References

- `p5-uk-air-p8a-raf`: `raw/sources/royal_air_force/p5-uk-air-p8a-raf/manifest.md` — RAF-specific configuration, crew, sensors, weapons and defensive aids
- `p5-uk-air-p8a-boeing`: `raw/sources/boeing/p5-uk-air-p8a-boeing/manifest.md` — common P-8A dimensions, mass, propulsion, performance and store compatibility
