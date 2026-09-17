# BGM-71F TOW 2B

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/anti-armor/tow/tow-2b/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-weapon-tow2b` |
| Family / variant | TOW / BGM-71F TOW 2B (including TOW 2B Aero functional envelope) |
| Role | Tube-launched, optically tracked, wire-guided top-attack anti-armor missile |
| Configuration boundary | U.S. BGM-71F TOW 2B baseline; Aero/F-3 extended-wire range is recorded as a bound, while TOW 2A, Bunker Buster and wireless RF derivatives are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 22.6 kg missile (public BGM-71F family value) | `p5-us-weapon-tow2b-army`; `p5-us-weapon-tow2b-designationsystems` | A/C | Container, launcher and guidance set excluded; Aero lot differences not resolved |
| Dimensions | 1.17 m body length (nose probe retracted); 152 mm body diameter; 450 mm wing span; 343 mm fin span | `p5-us-weapon-tow2b-designationsystems` | C | Extended ogive/probe geometry and folding surfaces vary by drawing |
| Propulsion / motor | Hercules M114 double-base solid-fuel flight motor with separate launch/ejection motor | `p5-us-weapon-tow2b-designationsystems` | C | Exact burn schedule and thrust are not public; functional two-stage launch/flight model |
| Guidance / seeker | Command guidance over wire from optical tracker; fly-over-shoot-down preset height; dual-mode optical laser profilometer plus magnetic target sensor | `p5-us-weapon-tow2b-army`; `p5-us-weapon-tow2b-designationsystems` | A/C | Missile has no onboard imaging seeker; sensor logic is target-profile based |
| Range / flight envelope | 0.2-3.75 km BGM-71F effective range; TOW 2B Aero extends upper bound to 4.5 km; missile flies 2.1-2.4 m above gunner line of sight | `p5-us-weapon-tow2b-army`; `p5-us-weapon-tow2b-designationsystems` | A/C | Wire length, tracker line-of-sight, terrain and target crossing constrain range; Aero value is an upper bound |
| Warhead | Two downward-directed 5-inch tantalum explosively formed penetrators (EFP), 5.8-6.4 kg combined warhead assembly | `p5-us-weapon-tow2b-army`; `p5-us-weapon-tow2b-designationsystems` | A/C | Individual fill and penetration are not publicly specified; not a tandem HEAT warhead |
| Fuze / trigger | Active dual-mode optical laser profilometer and magnetic influence fuze; sequential downward firing over target, with nose crush switch for direct-impact backup | `p5-us-weapon-tow2b-army`; `p5-us-weapon-tow2b-designationsystems` | A/C | Exact sensor thresholds/timing are not public; direct-attack backup is retained as bounded function |

## Source References

- `p5-us-weapon-tow2b-army`: `raw/sources/us_army/p5-us-weapon-tow2b-army/manifest.md`
- `p5-us-weapon-tow2b-designationsystems`: `raw/sources/designation_systems/p5-us-weapon-tow2b-designationsystems/manifest.md`
