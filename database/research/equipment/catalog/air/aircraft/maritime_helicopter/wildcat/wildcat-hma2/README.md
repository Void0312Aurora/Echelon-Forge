# Wildcat HMA2

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/maritime_helicopter/wildcat/wildcat-hma2/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-23`
Equipment ID: `eq-uk-air-wildcat-hma2`
Content status: parameter table complete for the Royal Navy Wildcat HMA2 research record. Royal Navy operating values and HMA2 weapon-role evidence are separated from platform-level Leonardo data.

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
| Standard internal fuel | 798 kg (262 US gal) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Overall length (manufacturer) | 15.24 m (50 ft) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Overall height | 3.73 m (12 ft 3 in) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum cruise speed | 264 km/h (143 kt) at sea level, maximum continuous power | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Rate of climb | 10 m/s (2,000 ft/min) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum density altitude | 4,572 m (15,000 ft) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum pressure altitude | 3,657 m (12,000 ft) | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Hover in ground effect | 2,267 m (7,440 ft) at ISA, maximum gross weight | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Hover out of ground effect | 1,307 m (4,290 ft) at ISA, maximum gross weight | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum range | 518 km (280 nm) at 5,000 ft, ISA, maximum gross weight | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Maximum endurance | 3 hours at 5,000 ft, ISA, maximum gross weight | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Royal Navy headline length | 15 m | `p5-uk-air-wildcat-hma2-royalnavy` | A |
| Royal Navy headline speed | 160 kt | `p5-uk-air-wildcat-hma2-royalnavy` | A |
| Royal Navy headline range | 250 nmi | `p5-uk-air-wildcat-hma2-royalnavy` | A |
| Royal Navy lifting capacity | 1 tonne | `p5-uk-air-wildcat-hma2-royalnavy` | A |
| Crew | One pilot and one observer; six additional crashworthy troop seats | `p5-uk-air-wildcat-hma2-royalnavy` | A |
| Roles | ISTAR, maritime interdiction, anti-surface warfare, anti-submarine warfare, logistics support, search and rescue | `p5-uk-air-wildcat-aw159-leonardo` | B |
| Sensors and mission displays | Four multifunction displays and a nose-mounted MX-15 Wescam electro-optical device; the HMA2 sensor suite extends ship situational awareness | `p5-uk-air-wildcat-hma2-royalnavy`; `p5-uk-air-wildcat-hma2-815nas` | A |
| Armament | Sting Ray torpedoes; 12.7 mm M3M machine gun; Martlet and Sea Venom missiles | `p5-uk-air-wildcat-hma2-royalnavy`; `p5-uk-air-wildcat-hma2-815nas` | A |
| HMA2 operational role | Air-to-surface, air-to-air and air-to-sub-surface fires; frigate/destroyer small-deck operation | `p5-uk-air-wildcat-hma2-815nas` | A |
| Integration role | Air-defence sensor-network contributor: identifies activity with radar and electro-optical sensors and relays it into RAF and allied command networks, including to Typhoon and F-35B | `p5-uk-air-wildcat-hma2-raf` | A |
| Deck operations | Certified for embarked operations from single-spot combatants; deck lock (harpoon) system and negative thrust capability, sea state up to 6 | `p5-uk-air-wildcat-aw159-leonardo` | B |

## Source Attribution Boundary

Field-level attribution matters on this leaf because the sources do not cover the same ground. Leonardo supplies platform-level AW159 geometry, mass, engine, fuel and defined performance conditions. The Royal Navy pages supply the HMA2 operating statistics, crew, sensors and weapon roles. The RAF source remains limited to the operator/integration row. An earlier revision attributed the generic platform role list to the RAF article; that attribution remains corrected.

## Configuration Boundary

The technical data above combines platform-level AW159 figures with Royal Navy HMA2 operating and integration statements. Leonardo does not separate the Royal Navy HMA2 from the Army AH1 in its technical table, so those rows remain platform-level. The Royal Navy pages do not publish empty mass or a station-by-station loadout; no such values are inferred.

## Source References

- `p5-uk-air-wildcat-hma2-raf`: `raw/sources/royal_air_force/p5-uk-air-wildcat-hma2-raf/manifest.md`
- `p5-uk-air-wildcat-aw159-leonardo`: `raw/sources/leonardo/p5-uk-air-wildcat-aw159-leonardo/manifest.md`
- `p5-uk-air-wildcat-hma2-royalnavy`: `raw/sources/royal_navy/p5-uk-air-wildcat-hma2-royalnavy/manifest.md`
- `p5-uk-air-wildcat-hma2-815nas`: `raw/sources/royal_navy/p5-uk-air-wildcat-hma2-815nas/manifest.md`
