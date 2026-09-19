# F-35C Lightning II

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-35/f-35c/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-19`
Equipment ID: `eq-us-air-f35c`
Content status: parameter table completed from a variant-specific manufacturer sheet, a Navy carrier-integration source and a specialist secondary reference for the remaining public crew/ceiling fields.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| U.S. Navy | In service | `p5-us-air-f35c-navair` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Variant | Carrier-suitable F-35C | `p5-us-air-f35c-navair` | A |
| Role | Carrier-based multirole stealth strike fighter | `p5-us-air-f35c-navair` | A |
| Powerplant | One Pratt & Whitney F135-PW-100 afterburning turbofan | `p5-us-air-f35c-lockheed` | B |
| Thrust | 40,000 lb maximum / 25,000 lb military power (uninstalled rating) | `p5-us-air-f35c-lockheed` | B |
| Length | 51.5 ft (15.7 m) | `p5-us-air-f35c-lockheed` | B |
| Height | 14.7 ft (4.48 m) | `p5-us-air-f35c-lockheed` | B |
| Wingspan | 43 ft (13.1 m), against 35 ft on the A and B | `p5-us-air-f35c-lockheed` | B |
| Wing area | 668 sq ft (62.1 m²), against 460 sq ft on the A and B | `p5-us-air-f35c-lockheed` | B |
| Horizontal tail span | 26.3 ft (8.02 m) | `p5-us-air-f35c-lockheed` | B |
| Empty weight | 34,800 lb (15,786 kg) | `p5-us-air-f35c-lockheed` | B |
| Maximum weight | 70,000 lb class | `p5-us-air-f35c-lockheed` | B |
| Internal fuel capacity | 19,750 lb (8,960 kg), against 18,250 lb on the A | `p5-us-air-f35c-lockheed` | B |
| Weapons payload | 18,000 lb (8,160 kg) | `p5-us-air-f35c-lockheed` | B |
| Standard internal weapons load | Two AIM-120C/D air-to-air missiles and two 2,000-pound GBU-31 JDAM guided bombs | `p5-us-air-f35c-lockheed` | B |
| Maximum speed | Mach 1.6 (approximately 1,200 mph) with full internal weapons load | `p5-us-air-f35c-lockheed` | B |
| Combat radius | More than 600 nmi (1,100 km) on internal fuel | `p5-us-air-f35c-lockheed` | B |
| Range | More than 1,200 nmi (2,200 km) on internal fuel | `p5-us-air-f35c-lockheed` | B |
| Service ceiling | 15,000 m (50,000 ft), specialist secondary reading | `p5-us-air-f35c-hiwars` | C |
| Crew | One | `p5-us-air-f35c-hiwars` | C |
| Armament | Internal and external carriage; the cited standard internal load is two AIM-120C/D and two GBU-31; external and mission-specific stores vary | `p5-us-air-f35c-lockheed`; `p5-us-air-f35c-hiwars` | B/C |

## Configuration Boundary

The numerical airframe, fuel and performance rows come from the F-35C column of the Lockheed Martin Fast Facts sheet; no F-35A or F-35B value is substituted. NAVAIR supplies the carrier-variant and shipboard-integration context. The crew and service-ceiling rows are retained as Tier C specialist readings because the cited manufacturer sheet does not state those fields for the C column. They are complete collection values, not a claim that the secondary readings have been cross-checked.

## Source References

- `p5-us-air-f35c-navair`: `raw/sources/us_navy/p5-us-air-f35c-navair/manifest.md` — carrier variant and Navy integration
- `p5-us-air-f35c-lockheed`: `raw/sources/lockheed_martin/p5-us-air-f35c-lockheed/manifest.md` — variant-specific dimensions, mass, fuel, propulsion and performance
- `p5-us-air-f35c-hiwars`: `raw/sources/hiwars/p5-us-air-f35c-hiwars/manifest.md` — crew and service ceiling secondary readings
