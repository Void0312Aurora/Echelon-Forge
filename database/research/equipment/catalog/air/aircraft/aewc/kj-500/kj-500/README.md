# KJ-500

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/aewc/kj-500/kj-500/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-cn-air-kj500`
Content status: parameter table present with per-field source and confidence. Status is `cataloged`, not `parameter_complete`, because every parameter row is Tier C secondary and the dimensions conflict between sources.

## Identity

- Family: KJ-500 (Y-9W)
- Variant: KJ-500
- Role: Airborne early warning and control
- Manufacturer: Shaanxi Aircraft Corporation, on the Y-9 airframe
- Configuration scope: the KJ-500 and KJ-500H are both listed as active variants by one cited source. This leaf records the base KJ-500.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Air Force | In service | `p5-cn-air-kj500-mnd` |
| PLA Navy | In service | `p5-cn-air-kj500-pla-navy` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Initial operating capability | 2015 | `p5-cn-air-kj500-mitchell` | C |
| Length | 118.1 ft (approximately 36.0 m) per one source; 34 m per another | `p5-cn-air-kj500-mitchell`; `p5-cn-air-kj500-armyrecognition` | C |
| Wingspan | 131.2 ft (approximately 40.0 m) per one source; 38 m per another | `p5-cn-air-kj500-mitchell`; `p5-cn-air-kj500-armyrecognition` | C |
| Height | 37.7 ft (approximately 11.5 m) | `p5-cn-air-kj500-mitchell` | C |
| Empty weight | 88,185 lb (approximately 40,000 kg) | `p5-cn-air-kj500-mitchell` | C |
| Powerplant | Four Zhushou Wojiang-6C (FWJ-6C) turboprops | `p5-cn-air-kj500-mitchell` | C |
| Maximum speed | 297 kt | `p5-cn-air-kj500-mitchell` | C |
| Maximum range | 3,078 nm per one source; 5,700 km per another, which is the same distance | `p5-cn-air-kj500-mitchell`; `p5-cn-air-kj500-armyrecognition` | C |
| Endurance | 12 hours | `p5-cn-air-kj500-armyrecognition` | C |

## Configuration Boundary

The official sources held here establish service presence with both the PLA Air Force and the PLA Navy but disclose no dimensions, mass or performance. Every parameter row is therefore Tier C secondary.

Source attribution was corrected in this revision. An earlier version cited the Mitchell Institute package for the 34 m by 38 m dimensions, the 5,700 km range and the 12-hour endurance. The Mitchell page does not state those values; it gives 118.1 ft by 131.2 ft by 37.7 ft with a range of 3,078 nm. Those four values come from the Army Recognition package, which is now named on the rows that depend on it, so the conflict is traceable to two identifiable sources rather than to one source and an unnamed cross-check.

The two dimension readings differ by roughly 2 m on each axis. They may describe different measurement conventions, such as the airframe alone against the airframe with the radome and antennas fitted, but neither source states which, so no reconciliation is attempted. The range readings do agree once converted: 3,078 nm is approximately 5,700 km.

The operator table previously listed only the PLA Air Force while the parameter block recorded PLAAF and PLANAF, which contradicted it. PLA Navy operation is now supported by an official tier A source and the table lists both services.

The KJ-500H is a separate active variant and is not merged into this record.

## Source References

- `p5-cn-air-kj500-mitchell`: `raw/sources/mitchell_institute/p5-cn-air-kj500-mitchell/manifest.md`
- `p5-cn-air-kj500-armyrecognition`: `raw/sources/army_recognition/p5-cn-air-kj500-armyrecognition/manifest.md`
- `p5-cn-air-kj500-pla-navy`: `raw/sources/china_military_online/p5-cn-air-kj500-pla-navy/manifest.md` — operator row only, no parameter rows
- `p5-cn-air-kj500-mnd`: `raw/sources/prc_ministry_of_national_defense/p5-cn-air-kj500-mnd/manifest.md` — service presence only
