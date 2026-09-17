# FGM-148F Javelin

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/anti-armor/javelin/fgm-148f/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-weapon-javelin` |
| Family / variant | Javelin / FGM-148F |
| Role | Man-portable, fire-and-forget anti-armor missile |
| Configuration boundary | U.S. FGM-148F missile in launch tube with original or lightweight CLU; older warhead variants and vehicle integration kits are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 15.9 kg missile in launch tube; 22.3 kg ready-to-fire system including CLU | `p5-us-weapon-javelin-lockheedmartin`; `p5-us-weapon-javelin-wikipedia` | C | F-model missile mass uses public Javelin specification; exact lot and CLU battery/accessory mass vary |
| Dimensions | 1.1 m missile length; 1.2 m launch-tube length; 127 mm diameter | `p5-us-weapon-javelin-wikipedia` | C | F-model composite mid-body remains within the public Javelin tube envelope; sight and bipod geometry excluded |
| Propulsion / motor | Soft-launch eject motor followed by a solid-fuel main rocket motor; main motor ignition occurs after operator standoff | `p5-us-weapon-javelin-lockheedmartin`; `p5-us-weapon-javelin-wikipedia` | C | Two-stage functional model; propellant grain, thrust curve, and burn time are not public |
| Guidance / seeker | Imaging infrared focal-plane-array seeker, fire-and-forget; selectable top-attack or direct-attack flight | `p5-us-weapon-javelin-lockheedmartin`; `p5-us-weapon-javelin-wikipedia` | C | FGM-148F seeker is represented functionally; exact focal-plane resolution, cooling, and target-class logic are not inferred |
| Range / flight envelope | 2.5 km with original CLU; 4.0 km with lightweight CLU; 4.75 km vehicle-employment bound; top-attack ceiling about 150 m and direct-attack ceiling about 60 m | `p5-us-weapon-javelin-lockheedmartin`; `p5-us-weapon-javelin-wikipedia` | C | Range varies with CLU, target aspect, and profile; vehicle value is an integration bound, not an F-model missile-only guarantee |
| Warhead | F-model multi-purpose warhead: tandem shaped-charge anti-armor effect with a naturally fragmenting steel case for enhanced personnel effect | `p5-us-weapon-javelin-lockheedmartin`; `p5-us-weapon-javelin-wikipedia` | C | Exact explosive fill and penetration rating are not public in the retained source; older HEAT-only warhead values excluded |
| Fuze / trigger | Electronic Safe, Arm and Fire (ESAF) system with terminal impact/target-event trigger; modeled as safe-arm distance plus impact detonation | `p5-us-weapon-javelin-wikipedia` | C | Exact arming distance, sensor logic, and redundancy are not public; functional trigger is a bounded estimate |

## Source References

- `p5-us-weapon-javelin-lockheedmartin`: `raw/sources/lockheed_martin/p5-us-weapon-javelin-lockheedmartin/manifest.md`
- `p5-us-weapon-javelin-wikipedia`: `raw/sources/wikipedia/p5-us-weapon-javelin-wikipedia/manifest.md`
