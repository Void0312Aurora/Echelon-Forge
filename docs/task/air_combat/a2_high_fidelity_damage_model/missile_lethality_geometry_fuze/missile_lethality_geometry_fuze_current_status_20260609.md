# A2 MLF-2 Current Status

Status: `2026-06-09` MLF-2D accepted / MLF-2E next. `MLF-2B` controlled geometry fixtures are accepted; `MLF-2C` nearest-approach writer is accepted; `MLF-2D` fuze-evaluation writer is accepted. Diagnostics projection is next.

Chinese main text: [missile_lethality_geometry_fuze_current_status_20260609.zh.md](missile_lethality_geometry_fuze_current_status_20260609.zh.md)

## Maturity Matrix

| Area | Status | Evidence | What This Does Not Prove |
| --- | --- | --- | --- |
| MLF-1 chain contract | accepted / archived | [MLF-1 evidence package](../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md) | Geometry/fuze is not high-fidelity yet |
| MLF-2 subproject boundary | pass | README, task clusters, dispatch queue, archive index | Runtime has not changed |
| Controlled geometry scenarios | pass | `MLF-2B-X1` pass; `MLF-2B-W1` pass; main thread revalidated 2 focused tests | Full target attitude control is not proven |
| Nearest-approach event | pass | `MLF-2C-X1` pass; `MLF-2C-W1` pass; main thread revalidated `ef_py` build, 3 missile geometry/fuze focused tests, and 7 engagement event capture regressions | Fuze trigger/no-trigger/delay/failure is not standardized yet |
| Fuze-evaluation event | pass | `MLF-2D-X1` pass; `MLF-2D-W1` pass; main thread revalidated `ef_py` build, 4 missile geometry/fuze focused tests, and 7 engagement event capture regressions | Diagnostics probe consumption is not proven yet |
| Diagnostic projection | planned / ready for audit | task cluster `MLF-2E` | Process probe is not readable yet |
| Runtime handoff | planned | task cluster `MLF-2F` | Effects model or reward semantics have not changed |

## Current Conclusion

MLF-2 is still not a complete lethality capability. The current evidence does not support claims that a missile should destroy a target, that a target should fragment, or that a specific real weapon Pk is known.

What can be said now: a live missile controlled-geometry fixture can vary range, closure, aspect, and altitude offset without relying on learned firing behavior. Standard nearest-approach events are now live-written, and miss/no-detonation paths record the nearest point and reason. Nearest-point time now comes from the point-update moment instead of the later terminal decision frame. Fuze-evaluation events now record armed/triggered, no-trigger, and failure reasons, and link back to the same munition's nearest-approach event.

## Next Step

1. Next dispatch should be `MLF-2E-X1`, a read-only audit of how the process probe/diagnostic export should consume nearest-approach and fuze-evaluation events.
2. After that audit passes, implement `MLF-2E-W1` without jumping to warhead effects or kill conclusions.

## Held Boundary

- No fragmentation / continuous-rod / structural breakup.
- No AIM-120C/MQ-9 case conclusion.
- No equivalence between fuze trigger and kill.
- No training reward path that creates lethality facts.
