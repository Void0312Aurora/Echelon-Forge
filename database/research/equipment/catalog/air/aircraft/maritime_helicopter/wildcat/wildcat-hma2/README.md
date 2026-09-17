# Wildcat HMA2

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/maritime_helicopter/wildcat/wildcat-hma2/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-uk-air-wildcat-hma2`
Content status: model-level draft with parameter coverage from two sources; the original RAF source supplies role and integration context only, and the manufacturer source supplies the technical data.

## Identity

- Family: AW159 / Wildcat
- Variant: HMA2
- Role: Maritime multi-role helicopter for ISTAR, anti-surface warfare, anti-submarine warfare, logistics support and search and rescue
- Manufacturer: Leonardo Helicopters (formerly AgustaWestland); evolution of the Lynx
- Configuration scope: Royal Navy maritime variant. The manufacturer technical data is platform-level and is not separated by mark.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Royal Navy | In service | `p5-uk-air-wildcat-hma2-raf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | Two LHTEC CTS800-4N turboshafts with FADEC | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Rotor diameter | 12.80 m (42 ft 0 in) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum gross weight (MTOW) | 6,050 kg (13,338 lb) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum cruise speed | 264 km/h (143 kt) at sea level, maximum continuous power | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Rate of climb | 10 m/s (2,000 ft/min) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum density altitude | 4,572 m (15,000 ft) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum pressure altitude | 3,657 m (12,000 ft) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Hover in ground effect | 2,267 m (7,440 ft) at ISA, maximum gross weight | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Hover out of ground effect | 1,307 m (4,290 ft) at ISA, maximum gross weight | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum range | 518 km (280 nm) at 5,000 ft, ISA, maximum gross weight | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum endurance | 3 hours at 5,000 ft, ISA, maximum gross weight | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Roles | ISTAR, maritime interdiction, anti-surface warfare, anti-submarine warfare, logistics support, search and rescue | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Integration role | Air-defence sensor-network contributor: identifies activity with radar and electro-optical sensors and relays it into RAF and allied command networks, including to Typhoon and F-35B | `p5-uk-air-wildcat-hma2-raf` | A |
| Deck operations | Certified for embarked operations from single-spot combatants; deck lock (harpoon) system and negative thrust capability, sea state up to 6 | `p5-uk-air-wildcat-aw159-leonardo` | B |

## Source Attribution Boundary

Field-level attribution matters on this leaf because the two sources do not cover the same ground. Every dimension, mass, performance, sensor and defensive-aid row rests on the Leonardo platform page and is Tier B. The Royal Air Force source is a news article about Merlin and Wildcat air-defence integration; the only rows it supports are the operator status and the integration-role row, and those are the only rows citing it. An earlier revision of this leaf attributed the generic platform role list to the RAF article, which was wrong and is corrected.

## Configuration Boundary

The technical data above comes from the manufacturer page, which publishes platform-level AW159 figures and does not separate the Royal Navy HMA2 from the Army AH1. No mass empty, length or height, ceiling or weapon-load figure is recorded, because neither source states one for this variant.

## Source References

- `p5-uk-air-wildcat-hma2-raf`: `raw/sources/royal_air_force/p5-uk-air-wildcat-hma2-raf/manifest.md`
- `p5-uk-air-wildcat-aw159-leonardo`: `raw/sources/leonardo/p5-uk-air-wildcat-aw159-leonardo/manifest.md`
