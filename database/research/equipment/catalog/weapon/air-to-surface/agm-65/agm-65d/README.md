# AGM-65D Maverick

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/air-to-surface/agm-65/agm-65d/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-weapon-agm65d` |
| Family / variant | AGM-65 Maverick / AGM-65D |
| Role | Air-to-surface electro-optical infrared guided missile |
| Configuration boundary | U.S. AGM-65D with imaging-infrared seeker and WDU-20/B warhead; laser-guided and penetrating-warhead Maverick variants are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 210 kg (463 lb), bounded D-model estimate at the lower end of the 210-304 kg Maverick family range | `p5-us-weapon-agm65d-usaf`; `p5-us-weapon-agm65d-designationsystems` | A/C | D-model warhead and seeker fit; carriage adapter mass excluded |
| Dimensions | 2.49 m length; 305 mm body diameter; 710 mm fin span | `p5-us-weapon-agm65d-usaf`; `p5-us-weapon-agm65d-designationsystems` | A/C | Common AGM-65 airframe dimensions; folded fin and launcher shoe geometry excluded |
| Propulsion / motor | Thiokol SR114-TC-1 solid-propellant rocket motor in WPU-4/B or WPU-8/B propulsion section | `p5-us-weapon-agm65d-designationsystems` | C | D/F/G motor group; exact motor lot and thrust curve are not public |
| Guidance / seeker | Imaging infrared (IIR) seeker with lock-on-before-launch target tracking; contrast-seeker and laser-guided modes excluded | `p5-us-weapon-agm65d-usaf`; `p5-us-weapon-agm65d-designationsystems` | A/C | D-model seeker is represented as cooled electro-optical IR tracking; seeker software details are not public |
| Range / flight envelope | Published range greater than 12 nmi (22 km); practical launch envelope bounded at 12-22 km for a subsonic carrier, with about 620 kt class missile speed | `p5-us-weapon-agm65d-designationsystems` | C | Launch altitude, aspect, and target contrast dominate range; 22 km is a public lower-bound reference, not a guaranteed hit range |
| Warhead | WDU-20/B shaped-charge warhead, about 57 kg (126 lb) | `p5-us-weapon-agm65d-usaf`; `p5-us-weapon-agm65d-designationsystems` | A/C | A/B/C/D/H shaped-charge group; E/F/G/J/K penetrating blast-fragmentation warheads excluded |
| Fuze / trigger | Nose impact fuze, modeled as instantaneous impact trigger on target contact | `p5-us-weapon-agm65d-designationsystems` | C | Public D-specific fuze designation is not retained; instantaneous impact behavior is a bounded functional estimate, not a claimed component number |

## Source References

- `p5-us-weapon-agm65d-usaf`: `raw/sources/us_air_force/p5-us-weapon-agm65d-usaf/manifest.md`
- `p5-us-weapon-agm65d-designationsystems`: `raw/sources/designation_systems/p5-us-weapon-agm65d-designationsystems/manifest.md`
