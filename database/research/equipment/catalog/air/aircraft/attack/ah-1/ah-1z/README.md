# AH-1Z Viper

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/attack/ah-1/ah-1z/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-25`
Equipment ID: `eq-us-air-ah1z`
Content status: `parameter_complete`; research record only, not runtime authority.

## Identity

- Family: Bell AH-1
- Variant: AH-1Z Viper
- Role: USMC attack helicopter
- Manufacturer: Bell Helicopter / Bell Textron
- Configuration scope: named AH-1Z Viper variant; AH-1W, AH-1S and foreign customer configurations are excluded.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Marine Corps | In sustainment; IOC February 2011 and FOC 2020 stated by NAVAIR | `p5-us-air-ah1z-navair` |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Fuselage length | 13.67 m (44 ft 10 in) | `p5-us-air-ah1z-navair` | A | NAVAIR variant page; distinct from overall length |
| Overall length | 17.75 m (58 ft 3 in) | `p5-us-air-ah1z-navair` | A | Rotors-turning/overall program figure; do not merge with fuselage length |
| Height | 4.37 m (14 ft 4 in) | `p5-us-air-ah1z-navair` | A | NAVAIR variant page |
| Main rotor diameter | 14.63 m (48 ft) | `p5-us-air-ah1z-globalsecurity` | C | Secondary cross-check; NAVAIR does not state rotor diameter |
| Empty weight | 12,300 lb (approximately 5,579 kg) | `p5-us-air-ah1z-navair` | A | NAVAIR empty-weight figure; not a mission gross or operating weight |
| Maximum gross weight | 18,500 lb (approximately 8,391 kg) | `p5-us-air-ah1z-navair`; `p5-us-air-ah1z-bell` | A / B | Common value from program and manufacturer sources |
| Maximum useful load | 5,764 lb (approximately 2,614 kg) | `p5-us-air-ah1z-bell` | B | Bell product figure; load depends on fuel and stores |
| Internal fuel capacity | 412.5 US gal (approximately 1,561 L) | `p5-us-air-ah1z-bell` | B | Product capacity; not a fuel usable/mission-offload value |
| Powerplant | Two General Electric T700-GE-401C turboshaft engines | `p5-us-air-ah1z-navair`; `p5-us-air-ah1z-bell` | A / B | Named AH-1Z engine model |
| Engine output | 1,800 shp uninstalled per engine | `p5-us-air-ah1z-bell` | B | Bell fact-sheet rating; not an installed transmission or OEI rating |
| Crew | 2 pilots in tandem; pilot and co-pilot/gunner | `p5-us-air-ah1z-navair`; `p5-us-air-ah1z-bell` | A / B | Variant crew count |
| Maximum speed | 200 KIAS (Bell product figure) | `p5-us-air-ah1z-bell` | B | General product data; not a flight-manual limitation |
| Cruise speed | 139 KTAS | `p5-us-air-ah1z-bell` | B | Bell product figure; condition not further specified |
| Combat radius | 131 nm | `p5-us-air-ah1z-bell` | B | Mission-conditioned Bell figure; not interchangeable with maximum range |
| Maximum range | 420 km (227 nm) | `p5-us-air-ah1z-globalsecurity` | C | Older secondary reading; retained as a cross-check, not averaged with combat radius |
| Mission-conditioned range | 705 km CAS reading with 8 Hellfire, 14 rockets and 650 rounds at stated conditions | `p5-us-air-ah1z-globalsecurity` | C | Old secondary mission envelope; condition and source age remain explicit |
| Service ceiling | 6,100 m (20,013 ft) | `p5-us-air-ah1z-globalsecurity` | C | Secondary cross-check; no NAVAIR/Bell ceiling value in retained pages |
| Endurance | 3 h 18 min | `p5-us-air-ah1z-globalsecurity` | C | Secondary cross-check; mission/fuel condition not fully specified |
| Stores stations | 6 wing stores; four universal stations and 16 PGM context | `p5-us-air-ah1z-navair` | A | NAVAIR wording retained; station count is not treated as a universal loadout table |
| Armament context | 20 mm cannon, AGM-114 Hellfire, 70 mm rockets and AIM-9; up to 16 Hellfire and up to 76 rockets in the secondary list | `p5-us-air-ah1z-globalsecurity`; `p5-us-air-ah1z-bell` | C / B | Broad compatibility/context only; exact sortie loadouts and store clearances remain open |
| Mission systems | Integrated advanced fire control, digital cockpit, Target Sight System and electronic-warfare self-protection context | `p5-us-air-ah1z-navair`; `p5-us-air-ah1z-bell` | A / B | Capability description, not sensor range or EW performance |
| Rotor system | Four-bladed all-composite rotor system | `p5-us-air-ah1z-navair`; `p5-us-air-ah1z-bell` | A / B | Named AH-1Z upgrade feature |
| Maneuvering envelope | -0.5 to +2.5 g | `p5-us-air-ah1z-bell` | B | Bell product envelope; not a complete structural limitation set |

## Configuration Boundary

NAVAIR provides the named AH-1Z program identity and variant-level geometry,
weight, engine, crew and stores context. Bell provides general product
performance and fuel figures. GlobalSecurity is retained only for older
secondary range, endurance, ceiling and weapons cross-checks. The leaf does not
average combat radius with maximum range, does not turn the secondary mission
range into a default flight model, and does not treat broad weapon compatibility
as a certified sortie loadout.

## Source References

- `p5-us-air-ah1z-navair`: `raw/sources/us_navair/p5-us-air-ah1z-navair/manifest.md`
- `p5-us-air-ah1z-bell`: `raw/sources/bell/p5-us-air-ah1z-bell/manifest.md`
- `p5-us-air-ah1z-globalsecurity`: `raw/sources/globalsecurity/p5-us-air-ah1z-globalsecurity/manifest.md`
