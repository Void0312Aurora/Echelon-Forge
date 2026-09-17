# AGM-114L Longbow Hellfire

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/anti-armor/agm-114/agm-114l/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-weapon-agm114l` |
| Family / variant | AGM-114 Hellfire / AGM-114L Longbow |
| Role | Air-to-surface millimeter-wave fire-and-forget anti-armor missile |
| Configuration boundary | U.S. AGM-114L/L-5 Longbow with MMW seeker and tandem anti-armor warhead; SAL Hellfire II, JAGM and naval launcher integration are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 50 kg all-up missile (bounded 49-50 kg public range) | `p5-us-weapon-agm114l-army`; `p5-us-weapon-agm114l-designationsystems` | A/C | L-model is heavier than 45.7 kg K-model; launcher and canister excluded |
| Dimensions | 1.78 m length; 178 mm body diameter; 320-340 mm stabilizer span | `p5-us-weapon-agm114l-designationsystems` | C | Public drawings vary by 1-2 cm; span bound covers the common Hellfire fin envelope |
| Propulsion / motor | Thiokol TX-657 / U.S. Army M120E1 low-smoke single-stage solid rocket motor | `p5-us-weapon-agm114l-army`; `p5-us-weapon-agm114l-designationsystems` | A/C | Motor designation is family-level; exact grain and thrust curve are not public |
| Guidance / seeker | Active millimeter-wave radar seeker (93-95 GHz band), inertial midcourse with lock-before-launch or lock-after-launch terminal homing; fire-and-forget | `p5-us-weapon-agm114l-army`; `p5-us-weapon-agm114l-designationsystems` | A/C | Seeker frequency and autonomous modes are specialist values; software blocks vary |
| Range / flight envelope | 0.5-8.0 km public employment envelope; Mach 1.3 class; helicopter launch, low-altitude direct or lofted trajectory | `p5-us-weapon-agm114l-army`; `p5-us-weapon-agm114l-designationsystems` | A/C | 8 km is an upper bound from Longbow/Hellfire family data, not guaranteed hit range; launch altitude/aspect dominate |
| Warhead | Tandem shaped-charge anti-armor warhead, 8-10 kg combined precursor/main explosive assemblies | `p5-us-weapon-agm114l-army`; `p5-us-weapon-agm114l-designationsystems` | A/C | Exact L-model fill is not fully public; 8-10 kg is a bounded Hellfire II tandem-warhead estimate |
| Fuze / trigger | Electronic safe-and-arm with impact fuze; L-7/L-5 rounds may add proximity/fragmentation options | `p5-us-weapon-agm114l-designationsystems` | C | Base L leaf models safe-arm plus terminal impact; variant-specific proximity details remain unresolved |

## Source References

- `p5-us-weapon-agm114l-army`: `raw/sources/us_army/p5-us-weapon-agm114l-army/manifest.md`
- `p5-us-weapon-agm114l-designationsystems`: `raw/sources/designation_systems/p5-us-weapon-agm114l-designationsystems/manifest.md`
