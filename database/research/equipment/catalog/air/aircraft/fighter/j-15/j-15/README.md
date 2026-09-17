# J-15

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/j-15/j-15/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-cn-air-j15`
Content status: parameter table present with per-field source and confidence. Status is `cataloged`, not `parameter_complete`, because all parameter rows rest on Tier C secondary sources and the engine fit is batch-dependent.

## Identity

- Family: J-15 (Flying Shark)
- Variant: J-15, baseline
- Role: Carrier-based multirole fighter
- Seat configuration: single-seat baseline
- Manufacturer: Shenyang Aircraft Corporation (AVIC)
- Related variants, none merged into this record: J-15S is the twin-seat derivative; J-15T is the catapult-capable derivative, described in official material as a modification of the baseline J-15.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Navy | In service | `p5-cn-air-j15-mnd` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Length | 21.9 m | `p5-cn-air-j15-tni` | C |
| Height | 5.9 m | `p5-cn-air-j15-tni` | C |
| Wingspan | 14.7 m | `p5-cn-air-j15-tni` | C |
| Empty weight | Approximately 17,500 kg per one source; 17,700 kg per another | `p5-cn-air-j15-tni`; `p5-cn-air-j15-deagel` | C |
| Maximum takeoff weight | 33,000 kg per one source; 32,500 kg per another | `p5-cn-air-j15-tni`; `p5-cn-air-j15-deagel` | C |
| Powerplant | Batch and production dependent. One source states two Shenyang WS-10; another gives WS-10H and notes Saturn AL-31F on early airframes; earlier public reporting describes the then-serving J-15 as AL-31 powered, while the newer J-15T is presented with a domestic turbofan | `p5-cn-air-j15-tni`; `p5-cn-air-j15-deagel` | C |
| Thrust | 12,800 kgf each in one source's units | `p5-cn-air-j15-tni` | C |
| Maximum speed | Mach 2.4 | `p5-cn-air-j15-tni` | C |
| Range | 3,500 km with external fuel tanks per one source; another states 3,500 km as a combat radius | `p5-cn-air-j15-tni`; `p5-cn-air-j15-deagel` | C |
| Hardpoints | 12, with a 30 mm cannon | `p5-cn-air-j15-deagel` | C |

## Configuration Boundary

Every parameter row is Tier C secondary. The Chinese Ministry of National Defense release held here confirms service presence and discloses no dimensions, mass or performance, so no row can be raised above secondary confidence from the held material.

Seat configuration is a corrected field. An earlier revision of this leaf described the baseline J-15 as a twin-seat aircraft. That was wrong: the baseline is single-seat and the twin-seat derivative is the J-15S. A Tier C database entry states a crew of two for the J-15, which is most likely that database inheriting a two-seat value from the Su-27UB-derived family; the value is recorded in its package but is not used on this leaf.

The engine fit is written as batch and production dependent rather than as a single value, because the held sources describe different fits at different times, and no source states when the change occurred.

Range is recorded as two readings rather than one, because one source's 3,500 km figure is a radius and another's is a range with external tanks. Those are different quantities and neither is converted into the other.

The J-15S and J-15T are separate derivatives. No value is shared with them.

## Source References

- `p5-cn-air-j15-tni`: `raw/sources/the_national_interest/p5-cn-air-j15-tni/manifest.md`
- `p5-cn-air-j15-deagel`: `raw/sources/deagel/p5-cn-air-j15-deagel/manifest.md`
- `p5-cn-air-j15-mnd`: `raw/sources/prc_ministry_of_national_defense/p5-cn-air-j15-mnd/manifest.md` — service presence only, no parameter rows
