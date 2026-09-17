# F-35B Lightning II

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-35/f-35b/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`
Equipment ID: `eq-uk-air-f35b`
Content status: parameter table present with per-field source and confidence. Retrieval status is recorded per package in each manifest's `Retrieval:` block rather than asserted here. The maximum weight row carries the `class` qualifier its sources publish, and the internal fuel conflict is retained.

## Identity

- Family: F-35 Lightning II
- Variant: F-35B
- Role: Short take-off and vertical landing multirole combat aircraft
- Manufacturer: Lockheed Martin, with BAE Systems and Northrop Grumman as principal partners
- Configuration scope: the short take-off and vertical landing mark, as operated by the United Kingdom and the United States Marine Corps. The F-35A and F-35C are separate configurations and no value is carried between the marks.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United Kingdom | In service | `p5-uk-air-f35b-raf-aircraft` |
| United States Marine Corps | In service | `p5-us-air-f35b-1stmaw` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Length | 15.6 m | `p5-uk-air-f35b-raf-aircraft` | A |
| Length (comparison table reading) | 15.5 m (51.2 ft) | `p5-uk-air-f35b-raf-comparison` | A |
| Length (Marine Corps reading) | 15.6 m (51.2 ft) | `p5-us-air-f35b-1stmaw` | A |
| Length (manufacturer reading) | 15.6 m (51.2 ft) | `p5-uk-air-f35b-bae-compiled` | B |
| Length (prime contractor sheet) | 15.6 m (51.2 ft) | `p5-us-air-f35b-lockheed` | B |
| Wingspan | 10.7 m | `p5-uk-air-f35b-raf-aircraft` | A |
| Wingspan (prime contractor sheet) | 10.7 m (35 ft) | `p5-us-air-f35b-lockheed` | B |
| Wing area | 42.7 m² | `p5-uk-air-f35b-raf-comparison` | A |
| Wing area (prime contractor sheet) | 42.7 m² (460 sq ft) | `p5-us-air-f35b-lockheed` | B |
| Height | 4.36 m (14.3 ft) | `p5-uk-air-f35b-raf-aircraft` | A |
| Maximum speed | Mach 1.6 | `p5-uk-air-f35b-raf-aircraft` | A |
| Maximum speed (Marine Corps reading) | Mach 1.6, approximately 1,200 mph | `p5-us-air-f35b-1stmaw` | A |
| Maximum altitude | 50,000 ft | `p5-uk-air-f35b-raf-aircraft` | A |
| Air-to-air refuelling | Probe and drogue | `p5-uk-air-f35b-raf-aircraft` | A |
| Aircrew | One pilot | `p5-uk-air-f35b-raf-aircraft` | A |
| Combat radius on internal fuel | More than 833 km (450 n.mi) | `p5-uk-air-f35b-raf-comparison` | A |
| Combat radius on internal fuel (Marine Corps reading) | More than 833 km (450 nautical miles) | `p5-us-air-f35b-1stmaw` | A |
| Range on internal fuel | More than 1,667 km (900 n.mi) | `p5-uk-air-f35b-raf-comparison` | A |
| Range on internal fuel (Marine Corps reading) | More than 1,667 km (900 nautical miles) | `p5-us-air-f35b-1stmaw` | A |
| Internal fuel | 13,100 lb (5,942 kg) | `p5-uk-air-f35b-raf-comparison` | A |
| Internal fuel (prime contractor sheet) | 13,500 lb (6,125 kg) | `p5-us-air-f35b-lockheed` | B |
| Internal fuel (Marine Corps band) | 13,100 to 13,500 lb (5,942 to 6,123 kg) | `p5-us-air-f35b-1stmaw` | A |
| Max G rating | 7.0 | `p5-uk-air-f35b-raf-comparison` | A |
| Max G rating (Marine Corps reading) | 7.0 | `p5-us-air-f35b-1stmaw` | A |
| Empty weight | 32,300 lb (14,651 kg) | `p5-us-air-f35b-1stmaw` | A |
| Maximum weight | 60,000 lb class | `p5-us-air-f35b-lockheed` | B |
| Maximum gross weight (Marine Corps reading) | 60,000 lb class (27,216 kg) | `p5-us-air-f35b-1stmaw` | A |
| Maximum thrust | 38,000 lb with afterburner | `p5-us-air-f35b-1stmaw` | A |
| Vertical lift thrust | 40,500 lb | `p5-us-air-f35b-1stmaw` | A |

## Configuration Boundary

Two Royal Air Force artifacts are held for this leaf and they are separate packages with separate ids: `p5-uk-air-f35b-raf-aircraft` is the F-35B aircraft page, and `p5-uk-air-f35b-raf-comparison` is a news article whose two-column table compares the F-35A and the F-35B. The aircraft page states length, height, wingspan, speed, altitude, powerplant, thrust, refuelling method, aircrew, weapons and sensors; it states no wing area, no combat radius, no range, no internal fuel and no g limit. The comparison article states the wing area, the combat radius, the range, the internal fuel and the g limit. An earlier revision of this leaf drew from both under one id; that is why the packages were split.

The maximum weight row states 60,000 lb as a class figure, which is how both the prime contractor sheet and the Marine Corps fact page publish it. It is not recorded as a precise limit. The Marine Corps page adds its own 27,216 kg conversion, recorded on that page's row as a separate reading rather than as the leaf's conversion of the class figure.

The empty weight is the Marine Corps page's 32,300 lb. The page does not publish a metric equivalent for that row, so the 14,651 kg beside it is this tree's arithmetic at 0.45359237 kg per pound, and it is labelled as a derived value on the manifest. A Tier C compilation independently gives the same value, 32,300 lb (14,650 kg), and is recorded on `p5-uk-air-f35b-migflug`.

Two readings are retained for the length. The aircraft page, the Marine Corps page, BAE Systems and the prime contractor sheet all give 15.6 m; the comparison table prints 15.5 m beside the same 51.2 ft, so its metric figure disagrees with its own imperial figure, which is 15.6 m. The readings are recorded side by side and neither is preferred.

The internal fuel carries three readings and a conflict that is left open. The comparison table gives 13,100 lb (5,942 kg); the prime contractor sheet gives 13,500 lb (6,125 kg); the Marine Corps page publishes the band 13,100 to 13,500 lb (5,942 to 6,123 kg), which contains both. A Tier C compilation gives approximately 13,500 lb. No reading is selected and none is averaged.

The Royal Air Force and the Marine Corps state the combat radius and the range independently and agree: more than 450 nautical miles and more than 900 nautical miles on internal fuel. The two are recorded as separate rows because the two services publish them separately, and the leaf notes that the Marine Corps page converts 900 nautical miles to 1,667 km while the exact conversion is 1,667 km to the nearest kilometre.

The maximum g rating of 7.0 now rests on two independent official publishers, the comparison article and the Marine Corps page. The comparison article gives 9.0 for the F-35A, which is not carried on this leaf.

A Tier C compilation gives the B mark maximum take-off weight as 27,200 kg (60,000 lb), which agrees with the class figure and supplies a metric equivalent. It remains recorded on `p5-uk-air-f35b-migflug` as a cross-check and as the locator for the mark-by-mark separation, but it is not the source of record for any row here.

The B variant sacrifices roughly a third of the A variant's fuel volume to accommodate the Rolls-Royce LiftSystem and is limited to 7 g. Those two facts are variant-specific and are recorded here rather than shared with the A or C marks.

## Source References

- `p5-uk-air-f35b-raf-aircraft`: `raw/sources/royal_air_force/p5-uk-air-f35b-raf-aircraft/manifest.md` — RAF aircraft page: dimensions, speed, altitude, powerplant, weapons, sensors
- `p5-uk-air-f35b-raf-comparison`: `raw/sources/royal_air_force/p5-uk-air-f35b-raf-comparison/manifest.md` — RAF A/B comparison table: wing area, radius, range, internal fuel, g rating
- `p5-us-air-f35b-1stmaw`: `raw/sources/us_marine_corps/p5-us-air-f35b-1stmaw/manifest.md` — Marine Corps facts table: empty weight, weight class, fuel band, g rating, thrust
- `p5-us-air-f35b-lockheed`: `raw/sources/lockheed_martin/p5-us-air-f35b-lockheed/manifest.md` — prime contractor variant table, maximum weight class
- `p5-uk-air-f35b-bae-compiled`: `raw/sources/bae_systems/p5-uk-air-f35b-bae-compiled/manifest.md` — manufacturer dimensions; retrieval not confirmed
- `p5-uk-air-f35b-migflug`: `raw/sources/migflug/p5-uk-air-f35b-migflug/manifest.md` — Tier C cross-check on empty weight and weight class
