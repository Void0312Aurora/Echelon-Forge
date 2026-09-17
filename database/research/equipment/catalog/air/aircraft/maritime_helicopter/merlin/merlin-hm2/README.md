# Merlin HM2

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/maritime_helicopter/merlin/merlin-hm2/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-uk-air-merlin-hm2`
Content status: model-level draft with parameter coverage from two sources; an engine conflict between the UK operator context and the manufacturer page is recorded rather than resolved.

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
| Overall length | 22.83 m (74 ft 11 in) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Overall height | 6.66 m (21 ft 10 in) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Rotor diameter | 18.60 m (61 ft 0 in) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Powerplant | GE CT7-8E turboshafts with FADEC per the manufacturer page; three Rolls-Royce Turbomeca RTM322-01 turboshafts per the naval reference for the Royal Navy Merlin, at 1,566 kW (2,100 hp) each take-off power | `p5-uk-air-merlin-aw101-leonardo`; `p5-uk-air-merlin-hm2-seaforces` | B/C | The divergence is now directional rather than open: the manufacturer page publishes the platform-level GE option and does not list the RTM322, while the Royal Navy Merlin is documented with three RTM322-01. The RTM322 reading rests on a specification block the page itself heads `Specifications (Merlin HM1)`, so the engine type is attested for the Royal Navy Merlin while the power figure is an HM1 reading carried on an HM2 page |
| Engine power (Royal Navy reading) | 1,566 kW (2,100 hp) each take-off power, three engines | `p5-uk-air-merlin-hm2-seaforces` | C | From the HM1-headed block on the Royal Navy Merlin page. This is the first HM-specific power figure on the leaf and it is not a manufacturer rating |
| Maximum cruise speed | 277 km/h (150 kt) at ISA, maximum gross weight, sea level, maximum continuous power | `p5-uk-air-merlin-aw101-leonardo` | B |
| Rate of climb | 9.5 m/s (1,880 ft/min) | `p5-uk-air-merlin-aw101-leonardo` | B |
| Hover in ground effect | 3,307 m (10,850 ft) at ISA, maximum gross weight | `p5-uk-air-merlin-aw101-leonardo` | B |
| Maximum range | 1,500 km (810 nm) at 5,000 ft per the section heading, or 6,000 ft per the footnote; ISA, maximum gross weight, twin-engine cruise, no reserves, standard fuel tanks | `p5-uk-air-merlin-aw101-leonardo` | B | The source states two different altitudes for the same figure; both are retained and the field is not settled |
| Maximum endurance | 7 h 40 min under the same conflicting reference condition | `p5-uk-air-merlin-aw101-leonardo` | B | Twin-engine cruise, no reserves, standard tanks; not an operational endurance and not a three-engine figure |
| Capacity | Two pilots, one air crewman and 25-plus troops on crashworthy seating, stated for the platform; up to 38 lightly equipped troops or 16 stretcher casualties in the battlefield and personnel-recovery fits | `p5-uk-air-merlin-aw101-leonardo` | B |
| Role in air defence | Airborne surveillance platform detecting and tracking maritime and air contacts and feeding them into RAF and allied command networks | `p5-uk-air-merlin-hm2-raf` | A |

## Configuration Boundary

The technical data above comes from the manufacturer AW101 page, which publishes platform-level figures and does not separate marks or customers. Three boundaries follow.

First, the page states the powerplant as the GE CT7-8E, while the UK Merlin fleet is associated with the Rolls-Royce Turbomeca RTM322; that divergence is recorded rather than resolved, and no engine is asserted as the HM2 fit. Every performance row above is therefore a generic AW101 figure whose applicability to the RTM322-powered HM2 is not established by any source held here.

Second, the page contradicts itself on the reference altitude for range and endurance: the section heading says 5,000 ft and the footnote says 6,000 ft cruise. Both are retained and the field is not settled.

Third, the range and endurance values are quoted for twin-engine cruise with no reserves and standard tanks, which is a defined reference condition and not an operational radius.

The Royal Air Force source already held for this leaf is a news article about air-defence integration; it states the role and the sensor-network contribution but no dimensions, mass or performance figures, and it is cited only for the role row.

## Source References

- `p5-uk-air-merlin-hm2-raf`: `raw/sources/royal_air_force/p5-uk-air-merlin-hm2-raf/manifest.md`
- `p5-uk-air-merlin-aw101-leonardo`: `raw/sources/leonardo/p5-uk-air-merlin-aw101-leonardo/manifest.md`
