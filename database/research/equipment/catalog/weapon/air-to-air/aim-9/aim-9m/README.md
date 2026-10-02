# AIM-9M Sidewinder

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/air-to-air/aim-9/aim-9m/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-weapon-aim9m` |
| Family / variant | AIM-9 Sidewinder / AIM-9M |
| Role | Short-range, infrared-guided air-to-air missile |
| Configuration boundary | U.S. AIM-9M production configuration; AIM-9X and non-U.S. derivative values are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 85.3 kg (188 lb), all-up missile | `p5-us-weapon-aim9m-navair`; `p5-us-weapon-aim9m-wikipedia` | A/C | Public family value applied to the AIM-9M airframe; captive and training rounds excluded |
| Dimensions | 3.02 m length; 127 mm body diameter; 279 mm fin span | `p5-us-weapon-aim9m-wikipedia` | C | Stable AIM-9D-to-M envelope; folded/uncaged fin geometry is not represented |
| Propulsion / motor | Hercules/Bermite Mk 36 solid-fuel rocket motor | `p5-us-weapon-aim9m-navair`; `p5-us-weapon-aim9m-wikipedia` | A/C | AIM-9M motor family; motor lot impulse and burn-time curve are not public |
| Guidance / seeker | Cooled all-aspect infrared homing seeker with proportional-navigation terminal guidance; no AIM-9X imaging-array behavior | `p5-us-weapon-aim9m-navair`; `p5-us-weapon-aim9m-wikipedia` | A/C | Seeker block and counter-countermeasure settings vary by retrofit; modeled as AIM-9M IR track |
| Range / flight envelope | Effective engagement 1-18 km (bounded employment estimate); high-altitude, high-speed kinematic upper bound about 35 km; speed Mach 2.5+ | `p5-us-weapon-aim9m-wikipedia` | C | Range is launch-condition dependent and is not a guaranteed single-shot probability range |
| Warhead | WDU-17/B annular blast-fragmentation warhead, about 9.4 kg filling | `p5-us-weapon-aim9m-navair`; `p5-us-weapon-aim9m-wikipedia` | A/C | AIM-9M baseline; exact fragment pattern and explosive composition are not inferred |
| Fuze / trigger | Infrared proximity fuze; simulation trigger is proximity-threshold crossing with a bounded terminal-impact backup | `p5-us-weapon-aim9m-wikipedia` | C | Exact fuze electronics and threshold are not public; backup behavior is a conservative functional estimate |

## Source References

- `p5-us-weapon-aim9m-navair`: `raw/sources/us_navy/p5-us-weapon-aim9m-navair/manifest.md`
- `p5-us-weapon-aim9m-wikipedia`: `raw/sources/wikipedia/p5-us-weapon-aim9m-wikipedia/manifest.md`
