# KJ-500

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/aewc/kj-500/kj-500/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-cn-air-kj500`
Content status: parameter table present with per-field source and confidence. Status is `cataloged`, not `parameter_complete`, because all parameter rows rest on Tier C secondary sources and the dimensions conflict between them.

## Identity

- Family: KJ-500 (Y-9W)
- Variant: KJ-500
- Role: Airborne early warning and control
- Manufacturer: Shaanxi Aircraft Corporation, on the Y-9 airframe
- Configuration scope: the KJ-500 and KJ-500H are both listed as active variants by the cited source. This leaf records the base KJ-500.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Air Force | In service | `p5-cn-air-kj500-mnd` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Initial operating capability | 2015 | `p5-cn-air-kj500-mitchell` | C |
| Operators | PLAAF and PLANAF | `p5-cn-air-kj500-mitchell` | C |
| Length | 118.1 ft (approximately 36.0 m) per one source; 34 m per another | `p5-cn-air-kj500-mitchell` | C |
| Wingspan | 131.2 ft (approximately 40.0 m) per one source; 38 m per another | `p5-cn-air-kj500-mitchell` | C |
| Height | 37.7 ft (approximately 11.5 m) | `p5-cn-air-kj500-mitchell` | C |
| Empty weight | 88,185 lb (approximately 40,000 kg) | `p5-cn-air-kj500-mitchell` | C |
| Powerplant | Four Zhushou Wojiang-6C (FWJ-6C) turboprops | `p5-cn-air-kj500-mitchell` | C |
| Maximum speed | 297 kt | `p5-cn-air-kj500-mitchell` | C |
| Maximum range | 3,078 nm (5,700 km), agreeing with a second source's 5,700 km | `p5-cn-air-kj500-mitchell` | C |
| Endurance | 12 hours | `p5-cn-air-kj500-mitchell` | C |

## Configuration Boundary

The official source held here confirms service presence and states that variant-level dimensions and performance are not officially disclosed. Every parameter row is therefore Tier C secondary.

Two dimension readings conflict and both are recorded: 118.1 ft by 131.2 ft against 34 m by 38 m, a spread of roughly 2 m on each axis. The two may describe different measurement conventions, such as the airframe alone against the airframe with the radome and antennas, but neither source states which, so no reconciliation is attempted.

The range readings do agree once converted: 3,078 nm is approximately 5,700 km, which is the figure the second source gives.

The KJ-500H is a separate active variant and is not merged into this record.

## Source References

- `p5-cn-air-kj500-mitchell`: `raw/sources/mitchell_institute/p5-cn-air-kj500-mitchell/manifest.md`
- `p5-cn-air-kj500-mnd`: `raw/sources/prc_ministry_of_national_defense/p5-cn-air-kj500-mnd/manifest.md` — service presence only
