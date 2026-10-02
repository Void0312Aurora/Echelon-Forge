# Merlin HM2

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/maritime_helicopter/merlin/merlin-hm2/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-23`
Equipment ID: `eq-uk-air-merlin-hm2`
Content status: parameter table complete for the Royal Navy Merlin HM2 research record. Royal Navy Mk2 mission, crew and weapon rows are separated from platform-level AW101 performance and the HM1-heading secondary engine block.

## Identity

- Family: AW101 / Merlin
- Variant: HM2
- Role: Maritime airborne surveillance and anti-submarine warfare platform, feeding contacts into command networks
- Manufacturer: Leonardo Helicopters (formerly AgustaWestland)
- Configuration scope: Royal Navy maritime variant. The manufacturer technical data is platform-level and is not separated by mark or customer.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Royal Navy | In service | `p5-uk-air-merlin-hm2-raf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Maximum gross weight | 15,600 kg (34,390 lb) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Royal Navy headline length | 23 m | `p5-uk-air-merlin-hm2-royalnavy` | A |
| Royal Navy headline speed | 160 kt | `p5-uk-air-merlin-hm2-royalnavy` | A |
| Royal Navy headline range | 750 nmi | `p5-uk-air-merlin-hm2-royalnavy` | A |
| Royal Navy lifting capacity | 3.8 tonnes | `p5-uk-air-merlin-hm2-royalnavy` | A |
| Overall length | 22.83 m (74 ft 11 in) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Overall height | 6.66 m (21 ft 10 in) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Rotor diameter | 18.60 m (61 ft 0 in) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Powerplant | GE CT7-8E turboshafts with FADEC per the manufacturer page; three Rolls-Royce Turbomeca RTM322-01 turboshafts per the naval reference for the Royal Navy Merlin, at 1,566 kW (2,100 hp) each take-off power | `p5-uk-air-merlin-aw101-leonardo`; `p5-uk-air-merlin-hm2-seaforces` | B/C | The divergence is now directional rather than open: the manufacturer page publishes the platform-level GE option and does not list the RTM322, while the Royal Navy Merlin is documented with three RTM322-01. The RTM322 reading rests on a specification block the page itself heads `Specifications (Merlin HM1)`, so the engine type is attested for the Royal Navy Merlin while the power figure is an HM1 reading carried on an HM2 page |
| UK HM2 engine direction | Royal Navy Merlin fleet is documented with three Rolls-Royce Turbomeca RTM322-01 engines; the Leonardo GE CT7-8E row is retained as a platform/export option | `p5-uk-air-merlin-hm2-seaforces`; `p5-uk-air-merlin-aw101-leonardo` | C/B |
| Engine power (Royal Navy reading) | 1,566 kW (2,100 hp) each take-off power, three engines | `p5-uk-air-merlin-hm2-seaforces` | C | From the HM1-headed block on the Royal Navy Merlin page. This is the first HM-specific power figure on the leaf and it is not a manufacturer rating |
| Maximum cruise speed | 277 km/h (150 kt) at ISA, maximum gross weight, sea level, maximum continuous power | `p5-uk-air-merlin-aw101-leonardo` | B |
| Rate of climb | 9.5 m/s (1,880 ft/min) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Hover in ground effect | 3,307 m (10,850 ft) at ISA, maximum gross weight | `p5-uk-air-merlin-aw101-leonardo` | B |
| Maximum range | 1,500 km (810 nm) at 5,000 ft per the section heading, or 6,000 ft per the footnote; ISA, maximum gross weight, twin-engine cruise, no reserves, standard fuel tanks | `p5-uk-air-merlin-aw101-leonardo` | B | The source states two different altitudes for the same figure; both are retained and the field is not settled |
| Maximum endurance | 7 h 40 min under the same conflicting reference condition | `p5-uk-air-merlin-aw101-leonardo` | B | Twin-engine cruise, no reserves, standard tanks; not an operational endurance and not a three-engine figure |
| Capacity | Two pilots, one air crewman and 25-plus troops on crashworthy seating, stated for the platform; up to 38 lightly equipped troops or 16 stretcher casualties in the battlefield and personnel-recovery fits | `p5-uk-air-merlin-aw101-leonardo` | B |
| HM2 anti-submarine crew | Four: two pilots, one observer/mission commander responsible for navigation, weapons and radar, and one sonar aircrewman | `p5-uk-air-merlin-hm2-royalnavy` | A |
| HM2 armament | Sting-Ray torpedoes and M3M .50 calibre machine guns | `p5-uk-air-merlin-hm2-weapons` | A |
| HM2 mission system | Active sonar/sonar operator; powerful radar for airborne surveillance and control; anti-submarine, anti-surface, maritime patrol and search-and-rescue roles | `p5-uk-air-merlin-hm2-royalnavy`; `p5-uk-air-merlin-hm2-weapons` | A |
| Role in air defence | Airborne surveillance platform detecting and tracking maritime and air contacts and feeding them into RAF and allied command networks | `p5-uk-air-merlin-hm2-raf` | A |

## Configuration Boundary

The technical data above combines platform-level AW101 figures with Royal Navy Mk2 operating and mission statements. Three boundaries follow.

First, the manufacturer page states the powerplant as the GE CT7-8E, while the Royal Navy Merlin is documented with the Rolls-Royce Turbomeca RTM322-01 on the HM2 page's HM1-headed specification block. The UK direction is now recorded explicitly, but the exact HM2 power rating remains marked as a secondary HM1-heading reading. Generic AW101 performance rows are not silently re-labelled as RTM322-specific test results.

Second, the page contradicts itself on the reference altitude for range and endurance: the section heading says 5,000 ft and the footnote says 6,000 ft cruise. Both are retained and the field is not settled.

Third, the range and endurance values are quoted for twin-engine cruise with no reserves and standard tanks, which is a defined reference condition and not an operational radius.

The Royal Air Force source already held for this leaf is a news article about air-defence integration; it states the role and sensor-network contribution but no dimensions, mass or performance figures, and it is cited only for the role row. The Royal Navy packages supply the Mk2 crew, weapons and mission-system rows.

## Source References

- `p5-uk-air-merlin-hm2-raf`: `raw/sources/royal_air_force/p5-uk-air-merlin-hm2-raf/manifest.md`
- `p5-uk-air-merlin-aw101-leonardo`: `raw/sources/leonardo/p5-uk-air-merlin-aw101-leonardo/manifest.md`
- `p5-uk-air-merlin-hm2-seaforces`: `raw/sources/seaforces/p5-uk-air-merlin-hm2-seaforces/manifest.md` — RTM322 direction and HM1-heading secondary dimensions/masses
- `p5-uk-air-merlin-hm2-royalnavy`: `raw/sources/royal_navy/p5-uk-air-merlin-hm2-royalnavy/manifest.md` — Mk2 statistics, crew and mission role
- `p5-uk-air-merlin-hm2-weapons`: `raw/sources/royal_navy/p5-uk-air-merlin-hm2-weapons/manifest.md` — Mk2 weapons and radar role
