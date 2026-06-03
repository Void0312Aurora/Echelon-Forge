# A6 Current Status

Status: `2026-06-03` held after event-head learned-policy evidence. P0-P10 pass
as evidence-producing/re-scope/audit/implementation slices, but A6 is not
accepted because the first deterministic crossing collapses to near-immediate
authorization/contact release rather than mature first-event timing.

Parent: [README.md](README.md).

## Changed In This Checkpoint

- Created the A6 subproject as the explicit event-value / first-event timing
  follow-on to A5.
- Recorded A5 retained deterministic/stochastic observations in
  [a6_event_value_first_event_timing_observation_20260603.md](a6_event_value_first_event_timing_observation_20260603.md).
- Implemented and validated the A6 hazard/curriculum training path, including
  rollout-label attachment, non-finite probe parity, world-batch A5 event-info
  propagation, and active config diagnostics.
- Ran
  [A6 short learned evidence](a6_event_value_first_event_timing_short_learned_probe_20260603.md).
  A6 remains held: deterministic policy still makes zero `fire_once` requests.
- Completed `A6-EVT-G` closure/re-scope: M2 stays held, plain hyperparameter
  tuning is not the main repair path, and the next bounded wave is deadline
  bootstrap.
- Completed `A6-EVT-H` implementation with sustained deadline labels and a
  separate active config:
  `air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json`.
- Ran
  [deadline short learned evidence](a6_event_value_first_event_timing_deadline_short_learned_probe_20260603.md).
  A6 remains held: deterministic probability moved to `0.494%`, but requests
  remained `0`.
- Completed
  [event-head update-strength audit](a6_event_value_first_event_timing_event_head_update_audit_20260603.md).
  The audit shows A6 labels and gradients are live, but current event-head
  optimizer/head scaling is too weak to cross deterministic argmax from a
  roughly `-5.3` event delta.
- Implemented
  [event-head optimization lane](a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md).
  The policy now supports a zero-initialized dedicated `hybrid_event_head`
  optimizer group, and a separate event-head active config is present for the
  next learned-policy evidence run.
- Ran
  [event-head short learned evidence](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.md).
  The event head crosses deterministic argmax and preserves one-shot release
  discipline, but the first release occurs at step `2` in deterministic probing
  and at steps `4`, `42`, and `2` in stochastic probing. A6 remains held as a
  launch-window timing problem.

## Maturity Matrix

| Surface | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| P0 observation | pass | A6 observation note summarizes retained A5 probes. | Observation only; no implementation accepted. |
| Mathematical framing | pass | [Mathematical framing](a6_event_value_first_event_timing_mathematical_framing_20260603.md) defines the constrained semi-MDP, windows, labels, rejected labels, failure modes, and C questions. | Design only; no implementation accepted. |
| Objective contract | pass | [Objective contract](a6_event_value_first_event_timing_objective_contract_20260603.md) selects masked first-event hazard on the existing event logit delta, with bounded curriculum bootstrap. | Event-value head and sequence-native objectives remain deferred. |
| Training-kernel changes | pass | `python/rl/policy_algo/first_event_hazard.py`, A6 rollout buffers, event logit delta access, optional `AdaptiveKLPPO` hazard hook, and focused tests are present. | Label fields stay outside policy observations. |
| Config and diagnostics | pass | Active configs expose A6 knobs, `CMODiagnosticsCallback` and process probe expose A6 event metrics, non-finite probe keeps A6 loss, and world-batch emits A5 event info. | This is infrastructure, not learned-policy acceptance. |
| Learned-policy evidence | pass; held outcome | `32768`-step A6 run completed. Deterministic: `1840` open steps, `0` requests, event probability `0.247% / 0.248%`; stochastic: `3/3` authorized single releases, `0` violations. | First hazard/curriculum contract is insufficient; A6 remains held. |
| Re-scope | pass | [Deadline-bootstrap re-scope](a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.md) chooses sustained deadline labels before event-value head or M2. | This is a bootstrap/diagnostic bridge, not tactical doctrine. |
| Deadline implementation | pass | Deadline label/source/config/logging changes are covered by focused tests. | This proves wiring, not learned-policy acceptance. |
| Deadline learned evidence | pass; held outcome | `32768`-step deadline run completed. Deterministic: `1840` open steps, `0` requests, event probability `0.494% / 0.496%`; stochastic: `3/3` authorized releases, `1` rejected request, `0` violations. | Deadline bootstrap moves probability but still does not solve deterministic argmax. |
| Event-head update audit | pass; held outcome | [Event-head audit](a6_event_value_first_event_timing_event_head_update_audit_20260603.md) plus `tests/hmoe/test_a6_event_head_update_strength.py` show gradients reach shared/HMoE event heads, while current `3e-5` LR and damped residual lane move event delta too slowly. | Diagnostic evidence only; no learned-policy acceptance. |
| Event-head optimization lane | pass; held timing residual | [Event-head lane](a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md) plus [short evidence](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.md) show deterministic crossing and one authorized release; stochastic gives `3/3` authorized releases with zero rejected/violation/repeat/budget issues. | The release timing collapses to near-immediate authorization/contact; A6 remains held. |

## Residual Register

Immediate:

- Define a launch-window / engagement-quality timing contract that separates
  legal authorization from good release timing.
- Decide whether this stays as `A6-EVT-L` or becomes a new follow-on subproject
  once the contract surface is clear.

Held:

- M2 sequence-native release remains held.
- Missile physics, Pk, fuze, damage authority, `2v2`, and self-play remain out
  of scope.

## Recommended Action Order

1. Treat `A6-EVT-E/F` as completed evidence, not acceptance.
2. Treat `A6-EVT-G` as completed re-scope, not acceptance.
3. Treat `A6-EVT-H/I` as completed evidence, not acceptance.
4. Treat `A6-EVT-J` as completed audit evidence, not acceptance.
5. Treat `A6-EVT-K` as completed event-head evidence, not A6 acceptance.
6. Continue through a launch-window timing contract before any M2 release vote.

## Overclaim Refusals

- A6 is not accepted.
- A5 stochastic release discipline does not prove deterministic first-shot
  learning.
- The first A6 hazard/curriculum contract being held does not justify
  reward-only legality tuning as the default next fix.
- Deadline bootstrap is not a real-world tactics or doctrine claim.
- Event-head update audit is not learned-policy acceptance.
- Event-head deterministic crossing is not proof of mature launch timing.
- M2 remains held until A6 or later evidence justifies a release vote.
