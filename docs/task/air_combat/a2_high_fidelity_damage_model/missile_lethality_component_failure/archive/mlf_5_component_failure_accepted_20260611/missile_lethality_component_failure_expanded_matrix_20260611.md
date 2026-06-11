# A2 MLF-5 Expanded Aspect/Distance Matrix

Status: `2026-06-11` retained evidence. Chinese main text: [missile_lethality_component_failure_expanded_matrix_20260611.zh.md](missile_lethality_component_failure_expanded_matrix_20260611.zh.md).

This record covers component-level failure probability and sampling only. It does
not claim aircraft crash, structural breakup, wreck/debris, Pk, or
weapon-specific lethality.

## Probe Scope

- Warhead families: `blast_fragmentation`, `continuous_rod`.
- Aspects: right beam, left beam, nose, tail, top, bottom, right-high, right-low.
- Distance points: four to six points per main aspect; `88` scenario points total.
- Random samples: `64` reset seeds per point.
- Metric convention: `model_p` is the primary component failure probability; `actual_fail_rate` is the rate where at least one component sampled a failure.
- Direct-hit points are marked with `D` in the heatmaps. They should not be read as the same monotonic distance curve as ordinary proximity or grazing points.

## Blast/Fragmentation

| Aspect | Representative distance | Primary model probability | Any-component trigger rate | Observation |
| --- | ---: | ---: | ---: | --- |
| Right beam | 6 m | `0.351680` | `0.734375` | Good beam-side proximity is dangerous; multi-component loading raises any-component trigger rate above the single primary probability |
| Right beam | 10 m | `0.006144` | `0.031250` | Edge case drops quickly |
| Right beam | 16 m | `0.000022` | `0.000000` | Near ineffective |
| Left beam | 6 m | `0.351680` | `0.671875` | Same order as right beam |
| Nose | 8 m | `0.352240` | `0.531250` | Nose components still respond clearly |
| Nose | 14 m | `0.001862` | `0.000000` | Far case decays quickly |
| Tail | 8 m | `0.351680` | `0.671875` | Tail control/propulsion components respond clearly |
| Tail direct hit | 6 m | `0.686314` | `0.703125` | After the repair, direct hit is no longer weaker than 8 m proximity; the primary component is the engine core |
| Top | 2 m | `0.352240` | `0.921875` | Very close top aspect covers multiple center-body components |
| Top | 10 m | `0.001648` | `0.000000` | Far case is near ineffective |
| Right-high | 8 m | `0.005133` | `0.015625` | Diagonal off-axis geometry is much weaker |

Conclusion: blast/fragmentation responds across most aspects, but falls quickly with distance. Close multi-component coverage can make the any-component trigger rate higher than the primary component probability.

## Continuous Rod

| Aspect | Representative distance | Primary model probability | Any-component trigger rate | Observation |
| --- | ---: | ---: | ---: | --- |
| Right beam | 6 m | `0.347818` | `0.562500` | Good beam-side exposure reaches the expected high-risk scale |
| Right beam | 8 m | `0.203751` | `0.250000` | Mid distance remains meaningful |
| Right beam | 12 m | `0.015949` | `0.031250` | Edge case drops clearly |
| Right beam | 16 m | `0.000000` | `0.000000` | Outside case has no effect |
| Left beam | 8 m | `0.335794` | `0.531250` | Left beam also remains high response |
| Nose, non-direct | 4 m | `0.000007` | `0.000000` | This point does not enter the target hitbox; it is axial grazing |
| Nose direct hit | 6 m | `0.950000` | `1.000000` | This point enters the target hitbox and should not be compared to 4 m grazing as an ordinary distance falloff |
| Nose, non-direct | 8 m | `0.000003` | `0.000000` | Non-direct axial grazing is near ineffective |
| Tail, non-direct | 8 m | `0.037570` | `0.031250` | Tail is weaker than beam/top/bottom |
| Top | 6 m | `0.351680` | `0.609375` | Top cut exposure is strong |
| Bottom | 8 m | `0.347390` | `0.671875` | Bottom cut exposure is strong |
| Right-high | 8 m | `0.262566` | `0.484375` | Diagonal exposure remains meaningful |
| Right-high | 12 m | `0.000000` | `0.000000` | Off-axis outside case has no effect |

Conclusion: continuous rod is more aspect-sensitive. Beam, top, bottom, and diagonal cut exposure are much stronger than non-direct axial grazing; the nose 4 m to 6 m jump comes from a grazing-vs-direct-hit category change, not an anomalous proximity distance curve. This matches the expected sweep/cut behavior.

## Boundary

- These results only say whether component failure sampled.
- They do not say that the target crashes or breaks up in the air.
- Later structural, wreck/debris, or whole-aircraft kill probability stages should consume these component damage facts.
