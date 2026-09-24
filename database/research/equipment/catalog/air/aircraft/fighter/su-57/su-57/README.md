# Su-57

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/su-57/su-57/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-24`
Equipment ID: `eq-ru-air-su57`
Content status: parameter-complete research record for the Russian Su-57; numeric values are an explicitly bounded public baseline, not lot-specific certification.

## Identity

- Family: Su-57
- Variant: Su-57
- Role: Fifth-generation multirole fighter
- Configuration scope: Russian service model; Su-57E export and unnamed prototype-only values are excluded.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Russian Aerospace Forces | Serial production / in service | `p5-ru-air-su57-uac` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Crew | 1 | `p5-ru-air-su57-redstar` | C |
| Length | 20.9 m | `p5-ru-air-su57-redstar` | C |
| Wingspan | 14.0 m | `p5-ru-air-su57-redstar` | C |
| Height | 4.65 m | `p5-ru-air-su57-redstar` | C |
| Wing area | 90 m² | `p5-ru-air-su57-redstar` | C |
| Empty mass | 17,500 kg | `p5-ru-air-su57-redstar` | C |
| Takeoff mass at 63% fuel plus missiles | 26,510 kg | `p5-ru-air-su57-redstar` | C |
| Takeoff mass at 100% fuel plus missiles | 30,610 kg | `p5-ru-air-su57-redstar` | C |
| Maximum takeoff mass | 35,480 kg | `p5-ru-air-su57-redstar` | C |
| Internal fuel | 11,000 kg | `p5-ru-air-su57-redstar` | C |
| Powerplant | Two izdeliye 117 turbofans | `p5-ru-air-su57-redstar` | C |
| Engine thrust | 14,500 kgf each; page also shows a 15,500 kgf value | `p5-ru-air-su57-redstar` | C |
| Maximum speed at altitude | 2,600 km/h | `p5-ru-air-su57-redstar` | C |
| Maximum speed at low altitude | 1,300 km/h | `p5-ru-air-su57-redstar` | C |
| Service ceiling | 20,000 m | `p5-ru-air-su57-redstar` | C |
| Range | 4,300–5,500 km | `p5-ru-air-su57-redstar` | C |
| Maximum overload | +10–11 g | `p5-ru-air-su57-redstar` | C |
| Warload | 10,000 kg | `p5-ru-air-su57-redstar` | C |
| Radar and mission systems | AESA/radar, electro-optical and digitised cockpit systems are described; no universal detection range asserted | `p5-ru-air-su57-redstar` | C |
| Gun armament | One 30 mm GSh-301 cannon, 150 rounds | `p5-ru-air-su57-redstar` | C |
| Weapon carriage | Two internal fuselage bays plus two wing-root compartments; named air-to-air, anti-ship, guided-bomb and air-to-surface stores are listed | `p5-ru-air-su57-redstar` | C |

## Configuration Boundary

The UAC page supplies the Russian Su-57 role and serial-production context. The RedStar table is a named Su-57 technical profile, but it is a public baseline and includes an alternate engine-thrust value; both are retained rather than silently reconciled. No Su-57E export value, prototype-only test value or universal combat-radius claim is added. The weapon list describes compatible stores, not simultaneous carriage.

## Source References

- `p5-ru-air-su57-uac`: `raw/sources/uac/p5-ru-air-su57-uac/manifest.md` — role and programme status
- `p5-ru-air-su57-redstar`: `raw/sources/redstar/p5-ru-air-su57-redstar/manifest.md` — bounded public numeric and weapon profile
