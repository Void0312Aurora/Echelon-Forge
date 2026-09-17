# F-35B Lightning II

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-35/f-35b/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-uk-air-f35b`
Content status: parameter table present with per-field source and confidence. Every source package on this leaf was retrieved and every manifest records what the retrieval returned. The maximum weight row rests on two independent publishers of the same class figure and keeps that figure's `class` qualifier.

## Identity

- Family: F-35 Lightning II
- Variant: F-35B
- Role: Short take-off and vertical landing multirole combat aircraft
- Manufacturer: Lockheed Martin, with BAE Systems and Northrop Grumman as principal partners
- Configuration scope: the short take-off and vertical landing mark, as operated by the United Kingdom and the United States Marine Corps. The F-35A and F-35C are separate configurations and no value is carried between the marks.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United Kingdom | In service | `p5-uk-air-f35b-raf` |
| United States Marine Corps | In service | `p5-us-air-f35b-1stmaw` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Length | 15.5 m | `p5-uk-air-f35b-raf` | A |
| Length (Marine Corps reading) | 15.6 m (51.2 ft) | `p5-us-air-f35b-1stmaw` | A |
| Length (manufacturer reading) | 15.6 m (51.2 ft) | `p5-uk-air-f35b-bae-compiled` | B |
| Length (prime contractor sheet) | 15.6 m (51.2 ft) | `p5-us-air-f35b-lockheed` | B |
| Wingspan | 10.7 m | `p5-uk-air-f35b-raf` | A |
| Wingspan (prime contractor sheet) | 10.7 m (35 ft) | `p5-us-air-f35b-lockheed` | B |
| Wing area | 42.7 m^2 | `p5-uk-air-f35b-raf` | A |
| Wing area (prime contractor sheet) | 42.7 m² (460 sq ft) | `p5-us-air-f35b-lockheed` | B |
| Height | 4.36 m (14.3 ft) | `p5-us-air-f35b-lockheed` | B |
| Maximum speed | Mach 1.6 | `p5-uk-air-f35b-raf` | A |
| Maximum speed (Marine Corps reading) | Mach 1.6, approximately 1,200 mph | `p5-us-air-f35b-1stmaw` | A |
| Combat radius on internal fuel | More than 833 km | `p5-uk-air-f35b-raf` | A |
| Combat radius on internal fuel (Marine Corps reading) | More than 450 nautical miles (833 km) | `p5-us-air-f35b-1stmaw` | A |
| Range on internal fuel | More than 1,667 km | `p5-uk-air-f35b-raf` | A |
| Range on internal fuel (Marine Corps reading) | More than 900 nautical miles (1,667 km) | `p5-us-air-f35b-1stmaw` | A |
| Internal fuel | 5,942 kg | `p5-uk-air-f35b-raf` | A |
| Max G rating | 7.0 | `p5-uk-air-f35b-raf` | A |
| Empty weight | 32,300 lb (14,651 kg) | `p5-us-air-f35b-1stmaw` | A |
| Maximum weight | 60,000 lb class | `p5-us-air-f35b-lockheed` | B |
| Maximum gross weight (Marine Corps reading) | 60,000 lb class (27,216 kg) | `p5-us-air-f35b-1stmaw` | A |

## Configuration Boundary

The maximum weight row states 60,000 lb as a class figure, which is how both the prime contractor sheet and the Marine Corps fact page publish it. It is not recorded as a precise limit. The Marine Corps page adds its own 27,216 kg conversion, which is recorded on that page's row as a separate reading rather than as the leaf's conversion of the class figure.

The Royal Air Force page and the Marine Corps page were produced independently and agree on the maximum speed, on the combat radius in excess of 450 nautical miles and on the range in excess of 900 nautical miles. Those agreements are recorded as separate rows rather than merged, because the two services publish them against the same aircraft in different units.

Three readings are retained for the length: 15.5 m from the Royal Air Force page and 15.6 m from the Marine Corps page, from BAE Systems and from the prime contractor sheet. The service page and the manufacturer sheets were produced independently and neither is preferred; the leaf does not average them. The 15.6 m reading also appears as 51.2 ft on the prime contractor sheet.

The empty weight rests on the Marine Corps page, which is the only package held here that states one for this mark. A Tier C compilation gives the same value, 32,300 lb (14,650 kg), and is recorded on `p5-uk-air-f35b-migflug`.

A Tier C compilation gives the B mark maximum take-off weight as 27,200 kg (60,000 lb), which agrees with the 60,000 lb class figure and supplies a metric equivalent. It also gives 65,900 lb for the A mark, which is not carried on this leaf. The compilation remains recorded on `p5-uk-air-f35b-migflug` as a cross-check and as the locator for the mark-by-mark separation, but it is not the source of record for any row here.

The B variant sacrifices roughly a third of the A variant's fuel volume to accommodate the Rolls-Royce LiftSystem and is limited to 7 g. Those two facts are variant-specific and are recorded here rather than shared with the A or C marks.

## Source References

- `p5-uk-air-f35b-raf`: `raw/sources/royal_air_force/p5-uk-air-f35b-raf/manifest.md` — Royal Air Force block
- `p5-us-air-f35b-1stmaw`: `raw/sources/us_marine_corps/p5-us-air-f35b-1stmaw/manifest.md` — Marine Corps block, empty weight, maximum weight class
- `p5-us-air-f35b-lockheed`: `raw/sources/lockheed_martin/p5-us-air-f35b-lockheed/manifest.md` — prime contractor variant table, maximum weight class
- `p5-uk-air-f35b-bae-compiled`: `raw/sources/bae_systems/p5-uk-air-f35b-bae-compiled/manifest.md` — manufacturer dimensions
- `p5-uk-air-f35b-migflug`: `raw/sources/migflug/p5-uk-air-f35b-migflug/manifest.md` — Tier C cross-check on empty weight and weight class
