# A2 MLF-2 Current Status

Status: `2026-06-09` MLF-2 accepted / archived. `MLF-2B` controlled geometry fixtures are accepted; `MLF-2C` nearest-approach writer is accepted; `MLF-2D` fuze-evaluation writer is accepted; `MLF-2E` diagnostics projection is accepted; `MLF-2F` runtime handoff gate is accepted; `MLF-2G` closeout and archive sync are complete.

Chinese main text: [missile_lethality_geometry_fuze_current_status_20260609.zh.md](missile_lethality_geometry_fuze_current_status_20260609.zh.md)

## Maturity Matrix

| Area | Status | Evidence | What This Does Not Prove |
| --- | --- | --- | --- |
| MLF-1 chain contract | accepted / archived | [MLF-1 evidence package](../../../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md) | Geometry/fuze is not high-fidelity yet |
| MLF-2 subproject boundary | pass | README, task clusters, dispatch queue, archive index | Runtime has not changed |
| Controlled geometry scenarios | pass | `MLF-2B-X1` pass; `MLF-2B-W1` pass; main thread revalidated 2 focused tests | Full target attitude control is not proven |
| Nearest-approach event | pass | `MLF-2C-X1` pass; `MLF-2C-W1` pass; main thread revalidated `ef_py` build, 3 missile geometry/fuze focused tests, and 7 engagement event capture regressions | Fuze trigger/no-trigger/delay/failure is not standardized yet |
| Fuze-evaluation event | pass | `MLF-2D-X1` pass; `MLF-2D-W1` pass; main thread revalidated `ef_py` build, 4 missile geometry/fuze focused tests, and 7 engagement event capture regressions | Diagnostics probe consumption is not proven yet |
| Diagnostic projection | pass | `MLF-2E-X1` pass; `MLF-2E-W1` pass; main thread revalidated `tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q` with 17 tests | Effects model or reward semantics have not changed |
| Runtime handoff | pass | `MLF-2F-I1` pass; `MLF-2F-W1` pass; main thread revalidated 3 focused fuze gate tests | Warhead effects or structural breakup are not complete |
| Acceptance closeout | pass | This archive package, current pointer READMEs, archive index, and A2/MLF-1 navigation are synchronized | MLF-3+ is not complete |

## Current Conclusion

MLF-2 is accepted, but it is still not a complete lethality capability. The current evidence does not support claims that a missile should destroy a target, that a target should fragment, or that a specific real weapon Pk is known.

What can be said now: a live missile controlled-geometry fixture can vary range, closure, aspect, and altitude offset without relying on learned firing behavior. Standard nearest-approach events are now live-written, and miss/no-detonation paths record the nearest point and reason. Nearest-point time now comes from the point-update moment instead of the later terminal decision frame. Fuze-evaluation events now record armed/triggered, no-trigger, and failure reasons, and link back to the same munition's nearest-approach event. The diagnostics probe now prioritizes standard nearest-approach/fuze-evaluation events, with old `EffectsEvent` projection retained only as fallback. Runtime gate behavior is pinned by tests: triggered paths enter existing effects/damage records, contact near-miss has no effects/damage record, and reliability failure has only a zero-damage transitional record.

## Follow-On Route

1. This subproject is archived; no further dispatch continues here.
2. The next phase should be created as a separate warhead/effect-mechanism subproject.
3. Fragmentation, continuous rod, structural breakup, debris/wreck, Pk, and weapon-specific conclusions remain later phases.

## Retained Gaps

- Timed-fuze standard event coverage remains held.
- Max-flight-time / guidance expiry still lacks recorder access.
- Zero-damage transitional `EffectsEvent` / `DamageReport` records remain until downstream consumers migrate.
- Finer target-attitude, delay-path, and warhead-effect mechanisms remain MLF-3+.

## Held Boundary

- No fragmentation / continuous-rod / structural breakup.
- No AIM-120C/MQ-9 case conclusion.
- No equivalence between fuze trigger and kill.
- No training reward path that creates lethality facts.
