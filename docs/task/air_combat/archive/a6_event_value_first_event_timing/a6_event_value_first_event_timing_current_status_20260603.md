# A6 Current Status

Status: `2026-06-04` held after launch-window short learned-policy evidence and
root-cause re-scope. P0-P13 pass as evidence-producing/re-scope/audit/
implementation/analysis slices, but A6 is not accepted because L suppresses
deterministic early fire without producing stable launch-window timing, and the
remaining blocker requires counterfactual event-time/value credit rather than
more L tuning.

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
- Implemented
  [launch-window timing contract](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.md).
  The label builder now gates accepted/curriculum/deadline positives through a
  quality window, early accepted releases become negative labels, PPO derives
  the window predicate from policy-observed contacts, diagnostics expose
  pre-window/early-accepted counts, and a separate L active config is present.
- Ran
  [launch-window short learned evidence](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.md).
  Deterministic probing made `0` requests and `0` releases, while open-window
  event probability reached `34.6% / 35.0%`. Stochastic probing preserved
  one-shot discipline but still sampled early authorized releases at steps `7`,
  `43`, and `4`.
- Completed
  [root-cause re-scope](a6_event_value_first_event_timing_root_cause_rescope_20260604.md).
  Further L training and parameter tuning are paused. The blocker is now framed
  as per-step stochastic hazard accumulation plus absorbing first-event
  censoring: stochastic collection can fire early with `0.25` to `0.35`
  per-step probability, while the accepted release removes later
  quality-window evidence that should teach the hold decision.

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
| Event-head update audit | pass; held outcome | [Event-head audit](a6_event_value_first_event_timing_event_head_update_audit_20260603.md) plus `tests/policy/test_event_head_update_contracts.py` show gradients reach shared/HMoE event heads, while current `3e-5` LR and damped residual lane move event delta too slowly. | Diagnostic evidence only; no learned-policy acceptance. |
| Event-head optimization lane | pass; held timing residual | [Event-head lane](a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md) plus [short evidence](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.md) show deterministic crossing and one authorized release; stochastic gives `3/3` authorized releases with zero rejected/violation/repeat/budget issues. | The release timing collapses to near-immediate authorization/contact; A6 remains held. |
| Launch-window timing contract | pass | [Launch-window contract](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.md), focused label/PPO/config/diagnostics tests, and independent L active config. | Implementation evidence only; learned-policy acceptance still depends on evidence. |
| Launch-window learned evidence | pass; held outcome | [Launch-window short evidence](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.md) shows deterministic `0` requests at `34.6% / 35.0%` open-window probability; stochastic `3/3` authorized releases at steps `7`, `43`, `4` with no rejected/violation/repeat/budget issues. | L reduces deterministic early fire but does not prove launch-window timing. |
| Root-cause re-scope | pass; training paused | [Root-cause re-scope](a6_event_value_first_event_timing_root_cause_rescope_20260604.md) records cumulative stochastic early-fire probabilities of `0.810`, `0.556`, and `0.625` before the sampled releases and identifies missing counterfactual hold/fire credit. | This is analysis and re-scope evidence, not a new learned-policy acceptance. |

## Residual Register

Immediate:

- Do not run more L short training or tune L weights until the A7
  [event-value / advantage-credit head](../a7_event_value_advantage_credit_head/README.md)
  implementation contract is in place and its focused implementation gates pass.
- The next design must handle cumulative pre-window hazard, absorbing
  first-event censoring, and explicit hold-vs-fire credit.
- Keep runtime legality unchanged while this is investigated.

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
6. Treat `A6-EVT-L/M` as completed evidence with a held outcome, not A6
   acceptance; re-scope launch-window shaping before any M2 release vote.
7. Treat `A6-EVT-N` as completed root-cause analysis and a pause on tuning, not
   acceptance. The next packet is A7
   [event-value / advantage-credit head](../a7_event_value_advantage_credit_head/README.md),
   design-first then implementation-gated.

## Overclaim Refusals

- A6 is not accepted.
- A5 stochastic release discipline does not prove deterministic first-shot
  learning.
- The first A6 hazard/curriculum contract being held does not justify
  reward-only legality tuning as the default next fix.
- Deadline bootstrap is not a real-world tactics or doctrine claim.
- Event-head update audit is not learned-policy acceptance.
- Event-head deterministic crossing is not proof of mature launch timing.
- Launch-window learned evidence is not A6 acceptance.
- Root-cause re-scope is not a license to loosen A3/A5 legality or release M2.
- M2 remains held until A6 or later evidence justifies a release vote.
