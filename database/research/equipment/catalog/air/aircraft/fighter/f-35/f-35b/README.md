# F-35B Lightning II

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-35/f-35b/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-uk-air-f35b`
Content status: parameter table present with per-field source and confidence. The maximum weight row rests on the prime contractor document and keeps that document's `class` qualifier rather than converting it to a precise figure.

## Identity

- Family: F-35 Lightning II
- Variant: F-35B
- Role: Short take-off and vertical landing multirole combat aircraft
- Manufacturer: Lockheed Martin, with BAE Systems and Northrop Grumman as principal partners
- Configuration scope: the short take-off and vertical landing mark, as operated by the United Kingdom. The F-35A and F-35C are separate configurations and no value is carried between the marks.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United Kingdom | In service | `p5-uk-air-f35b-raf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Length | 15.5 m | `p5-uk-air-f35b-raf` | A |
| Length (manufacturer reading) | 15.6 m (51.2 ft) | `p5-uk-air-f35b-bae-compiled` | B |
| Wingspan | 10.7 m | `p5-uk-air-f35b-raf` | A |
| Wing area | 42.7 m^2 | `p5-uk-air-f35b-raf` | A |
| Height | 4.36 m (14.3 ft) | `p5-uk-air-f35b-bae-compiled` | B |
| Maximum speed | Mach 1.6 | `p5-uk-air-f35b-raf` | A |
| Combat radius on internal fuel | More than 833 km | `p5-uk-air-f35b-raf` | A |
| Range on internal fuel | More than 1,667 km | `p5-uk-air-f35b-raf` | A |
| Internal fuel | 5,942 kg | `p5-uk-air-f35b-raf` | A |
| Max G rating | 7.0 | `p5-uk-air-f35b-raf` | A |
| Maximum weight | 60,000 lb class | `p5-us-air-f35b-lockheed` | B |

## Configuration Boundary

The maximum weight row states 60,000 lb as a class figure, which is how the prime contractor document publishes it. It is not recorded as a precise limit and is not converted to a metric equivalent, because doing either would assert a precision the source does not state. The same document gives 70,000 lb class for the F-35A and 70,000 lb class for the F-35C; neither is carried on this leaf.

Two readings are retained for the length: 15.5 m from the Royal Air Force page and 15.6 m from the BAE Systems page. The two packages were produced independently and neither is preferred; the leaf does not average them. The 15.6 m reading also appears as 51.2 ft on both the BAE Systems page and the Tier C compilation.

A Tier C compilation gives the B mark maximum take-off weight as 27,200 kg (60,000 lb), which agrees with the prime contractor's class figure of 60,000 lb. It also gives 65,900 lb for the A mark, which is not carried on this leaf. The compilation remains recorded on `p5-uk-air-f35b-migflug` as a cross-check on the weight agreement and as the locator for the mark-by-mark separation.

The B variant sacrifices roughly a third of the A variant's fuel volume to accommodate the Rolls-Royce LiftSystem and is limited to 7 g. Those two facts are variant-specific and are recorded here rather than shared with the A or C marks.

## Source References

- `p5-uk-air-f35b-raf`: `raw/sources/royal_air_force/p5-uk-air-f35b-raf/manifest.md`
- `p5-uk-air-f35b-bae-compiled`: `raw/sources/bae_systems/p5-uk-air-f35b-bae-compiled/manifest.md` — manufacturer dimensions
- `p5-us-air-f35b-lockheed`: `raw/sources/lockheed_martin/p5-us-air-f35b-lockheed/manifest.md` — maximum weight class
- `p5-uk-air-f35b-migflug`: `raw/sources/migflug/p5-uk-air-f35b-migflug/manifest.md` — Tier C weight cross-check
