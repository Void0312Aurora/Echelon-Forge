# A7 Event-Value / Advantage Credit Head

Status: `2026-06-04` active implementation subproject. A7 is the follow-on to
the A6 root-cause re-scope: implement an event-value / advantage-credit
mechanism for the masked `hold/fire_once` action before any more launch-window
tuning. `A7-EVC-A/B` are closed by the objective contract, `A7-EVC-C` has
landed the zero-safe policy-head prototype, and `A7-EVC-D` has wired focused
PPO auxiliary credit. `A7-EVC-E` has added the active config and diagnostics
surface, `A7-EVC-F` has passed the focused validation sweep, and `A7-EVC-G`
has produced valid short learned evidence as a held outcome. The credit-training
path is active, but launch-window timing acceptance is not met.
`A7-EVC-I` has now traced the held outcome to missing shadow-quality target
repair after early stochastic accepted release. `A7-EVC-J` has repaired that
label-censoring path and passed focused tests plus a 32k repair probe, but the
learned-policy outcome remains held: deterministic probing still records `0`
releases, stochastic probing still fires too early, and quality-window advantage
remains negative. `A7-EVC-K` has now closed the post-repair structural audit:
the remaining blocker is legal-state projection / value-to-policy coupling.
`A7-EVC-L` selected a projection contract, `A7-EVC-M` has implemented the
projected legal-open credit prototype with focused validation, and `A7-EVC-N`
has now run the short projection learned-policy probe. N is valid evidence, but
the behavior remains held: deterministic probing still records `0` releases,
stochastic probing still fires too early, and projection metrics show
`a7/evc_proj_active_count_mean=0.0` despite projection being enabled. The next
bounded slice is a projection-eligibility root-cause audit, not longer blind
training.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task: [../README.md](../README.md)
- A3 C2/ROE release discipline pointer:
  [../a3_c2_roe_release_discipline/README.md](../a3_c2_roe_release_discipline/README.md)
- A5 constrained event action model:
  [../a5_constrained_event_action_model/README.md](../a5_constrained_event_action_model/README.md)
- A6 event-value / first-event timing:
  [../a6_event_value_first_event_timing/README.md](../a6_event_value_first_event_timing/README.md)
- A6 root-cause re-scope:
  [../a6_event_value_first_event_timing/a6_event_value_first_event_timing_root_cause_rescope_20260604.md](../a6_event_value_first_event_timing/a6_event_value_first_event_timing_root_cause_rescope_20260604.md)
- HMoE hierarchical computation gap:
  [../../issues/hmoe_hierarchical_computation_gap/README.md](../../issues/hmoe_hierarchical_computation_gap/README.md)
- A6 launch-window label-density issue:
  [../../issues/a6_launch_window_label_imbalance/README.md](../../issues/a6_launch_window_label_imbalance/README.md)
- Subproject creation standard:
  [../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)

## Purpose

A6 showed that the `hold/fire_once` event head can be trained, but per-step
hazard labels do not solve first-event timing. Once stochastic exploration
fires early, A5 transitions to `FiredAssess` and later quality-window evidence
is censored. The missing mechanism is counterfactual credit for "hold now so a
better fire action is available later".

A7 turns that diagnosis into an implementation line. The core object is an
event-value or advantage head that learns a signed preference between
`fire_once` and `hold` under the A5 event mask:

```text
A_event(s_t) = Q_fire_once(s_t) - Q_hold(s_t)
```

The policy event-logit delta should be encouraged to agree with that advantage:
pre-window states should prefer `hold`, quality-window states should prefer
`fire_once`, and early stochastic samples must not erase the future target that
would have rewarded holding.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A3 legality | accepted; archived pointer | A3 evidence packet is archived under `archive/a3_c2_roe_release_discipline`, while the original path remains a pointer. | A3 owns legal release discipline; A7 must not weaken masks or state transitions. |
| A5 event surface | held but usable input | `hold/fire_once` masked event action, post-launch suppression, and one-shot stochastic discipline exist. | A5 did not solve deterministic first-shot learning. |
| A6 first-event labels | held after root-cause analysis | Hazard/deadline/launch-window labels are live, but L evidence leaves deterministic at `0` requests and stochastic early release risk high. | Further L tuning is paused. |
| A6-N root cause | pass | Per-step stochastic hazard accumulation plus absorbing first-event censoring explains the held outcome. | The next mechanism needs counterfactual credit, not just label weighting. |
| HMoE gap | open issue | Subexperts do not see family-head output, and C2/ROE combat routing collapses to one family. | A7 should account for this risk, but it does not redesign HMoE in this slice. |
| A7 objective contract | pass | [Objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.md) selects a counterfactual event-value head, window balancing, policy-logit coupling, and cumulative hazard diagnostics. | This authorizes a focused A7 prototype, not M2, HMoE redesign, or missile/doctrine authority. |
| A7 policy head prototype | pass | `hybrid_event_credit_head` exposes `Q_hold`, `Q_fire_once`, and event advantage with zero initialization, a dedicated optimizer lane, default-disabled behavior, A6 coexistence tests, and load smoke coverage. | A7-C exposes credit only; it does not train the head or write credit into event logits. |
| A7 PPO auxiliary credit | pass | `compute_first_event_credit_loss()` and `AdaptiveKLPPO._first_event_credit_loss()` train the A7 head, optionally align event-logit delta, enable first-event label collection for A7-only coeffs, and pass focused PPO/gradient tests. | No learned-policy claim. |
| A7 config and diagnostics | pass | [Config and diagnostics evidence](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md) adds the A7 active config, callback event-credit/early-hazard metrics, and process-probe summary metrics. | No learned-policy claim by itself; G has now evaluated the learned behavior as held. |
| A7 focused validation | pass | [Focused validation sweep](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md) re-runs JSON, compileall, HMoE policy/PPO, config, callback, active-entry, process-probe, and diff checks. | No learned-policy claim. |
| A7 short learned evidence | pass; held outcome | [Short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md) validates r3 after nonfinite-probe fixes: `a7/event_credit_loss` is live, deterministic still fires `0` times, and stochastic releases at steps `14`, `47`, and `2`. | A7 credit training is active, but quality-window event advantage remains negative and A7 is not accepted. |
| A7 target construction audit | pass; repaired by J | [Target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.md) reconstructs current labels: stochastic r3 has `19` active labels, `0` positives, and more than `1000` post-early-release shadow quality states per episode. | The fault was target construction, not runtime legality, disabled training, or HMoE as the primary blocker; J has repaired the censoring path. |
| A7 shadow-quality target repair | pass; held outcome | [Shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md) adds post-early `shadow_quality` positives, preserves early-accepted negatives, masks shadow rows out of delta alignment, and validates the repaired active config. | The label-censoring bug is fixed, but learned timing is still not accepted. The next question is how repaired shadow credit reaches legal-open quality states. |
| A7 legal-state projection audit | pass; held outcome | [Legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md) proves post-J positives exist but mostly live on closed-mask `FiredAssess` observations; direct policy alignment remains dominated by legal-open negatives. | K is docs/diagnostics evidence only. It does not accept A7 or justify closed-mask delta alignment. |
| A7 legal-state projection contract | pass; implemented by M | [Legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md) selects projected legal-open credit: raw shadow rows become projection/opportunity evidence, while positive delta alignment is allowed only on projected legal-open observations. | The contract does not weaken A3/A5 masks and is now implemented as a focused prototype; it still does not prove learned-policy behavior. |
| A7 projected legal-open credit prototype | pass; held after N | [Projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md) adds `first_event_projection.py`, projection coeffs, PPO projected-distribution loss, projection metrics, active config knobs, and focused tests. | M proves the mechanism and focused gradient path only; N shows learned behavior still held. |
| A7 short projection learned evidence | pass; held outcome | [Short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md) validates r3 after projection-logger repairs: projection is enabled, ordinary A7 event-credit remains live, deterministic probing records `0` releases, stochastic probing releases at steps `2`, `47`, and `5`, and projected active rows remain `0.0`. | A7 is not accepted; the next question is why shadow-quality evidence does not reach active projected rows in the learned rollout/loss path. |

## Scope

In scope:

- Define an action-conditional event-value / advantage target for masked
  `hold/fire_once`.
- Add a bounded policy head or auxiliary head that can estimate
  `Q_hold`, `Q_fire_once`, or their advantage.
- Couple the head to the event-logit delta through a documented auxiliary loss
  or regularizer.
- Preserve A3/A5 legality masks and post-launch state-machine suppression.
- Add cumulative pre-window hazard diagnostics:
  `P_early = 1 - product(1 - h_t)`.
- Treat adaptive label weighting only as a supporting guard, not the core
  mechanism.
- Include HMoE issue evidence in the design: the A7 head should not rely solely
  on a hard-routed subexpert boundary to learn hold/fire credit.

Out of scope:

- HMoE hierarchical-computation redesign, soft routing, or M2 release.
- Missile physics, Pk, fuze, damage authority, stock weapon authority, `2v2`,
  self-play, or real BVR doctrine claims.
- Weakening A3/A5 masks to make release easier.
- Another L-only training run before the A7 objective contract is accepted.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze A7 as counterfactual event-credit work. | A6-N root-cause note exists. | README and task clusters reject L tuning and M2 release as defaults. | pass |
| `P1 Evidence And HMoE Risk` | Reconcile A6-N, issue-board findings, and policy code entry points. | A7 exists. | Objective contract records how HMoE gap affects head placement and diagnostics. | pass |
| `P2 Objective Contract` | Select value/advantage targets, label sources, losses, and rollback gates. | P1 evidence accepted. | Contract is specific enough for implementation. | pass |
| `P3 Policy Head Prototype` | Add the bounded event-value / advantage head. | P2 contract accepted. | Focused policy tests cover shape, initialization, serialization, and event-logit coupling. | pass |
| `P4 PPO Integration` | Train the head and connect auxiliary credit to PPO updates. | P3 head available. | Loss, stats, finite behavior, and mask handling are tested. | pass |
| `P5 Config And Diagnostics` | Add active config and cumulative hazard diagnostics. | P4 integration passes. | Config and callback/process-probe tests expose A7 metrics. | pass |
| `P6 Learned Evidence` | Run short learned-policy probe. | P5 tests pass and F validation sweep is clean. | Deterministic/stochastic timing, release counts, and cumulative early hazard are recorded. | pass; held outcome |
| `P7 Closure` | Accept, hold, or re-scope A7. | P6 evidence exists. | Parent/A6/issues docs reflect evidence without overclaim. | pass; held sync |
| `P8 Target Audit` | Diagnose the negative quality-window credit sign. | P7 sync complete. | Target/loss construction names the failing link and next repair. | pass; repaired by J |
| `P9 Shadow Target Repair` | Implement and test shadow-quality counterfactual targets. | P8 audit exists. | Early stochastic release no longer censors future quality evidence from target credit, and learned-policy probe evidence records the residual behavior. | pass; held outcome |
| `P10 Projection Audit` | Diagnose why repaired positives do not move legal-open quality states. | P9 repair probe exists. | Projection/coupling failure is separated from missing positives, HMoE redesign, and coefficient-only tuning. | pass; spawned L contract |
| `P11 Projection Contract` | Define the legal-state projection mechanism before implementation. | P10 audit exists. | Contract selects projected legal-open positive alignment and names implementation gates. | pass; implemented by M |
| `P12 Projection Prototype` | Implement projected legal-open credit from the L contract. | P11 contract exists. | Focused tests prove projection whitelist, unsupported-layout refusal, no raw closed-mask delta alignment, and projected positive delta pressure. | pass; N evaluated learned behavior |
| `P13 Projection Learned Evidence` | Run short projected-credit learned-policy probe. | P12 focused gates pass. | Projection metrics, deterministic/stochastic timing, and one-shot discipline are recorded. | pass; held outcome |
| `P14 Projection Eligibility Audit` | Diagnose why projection active rows remain zero in the learned run. | P13 evidence exists. | Rollout/loss handoff from shadow-quality labels to projected legal-open rows is explained before another training wave. | planned next |

## Task Clusters

- Task cluster plan:
  [a7_event_value_advantage_credit_head_task_clusters_20260604.md](a7_event_value_advantage_credit_head_task_clusters_20260604.md)
- Current status:
  [a7_event_value_advantage_credit_head_current_status_20260604.md](a7_event_value_advantage_credit_head_current_status_20260604.md)
- Dispatch queue:
  [a7_event_value_advantage_credit_head_dispatch_queue_20260604.md](a7_event_value_advantage_credit_head_dispatch_queue_20260604.md)
- Acceptance gate:
  [a7_event_value_advantage_credit_head_acceptance_20260604.md](a7_event_value_advantage_credit_head_acceptance_20260604.md)
- Objective contract:
  [a7_event_value_advantage_credit_head_objective_contract_20260604.md](a7_event_value_advantage_credit_head_objective_contract_20260604.md)
- Legal-state projection contract:
  [a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md)
- Projected legal-open credit prototype:
  [a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md)
- Short projection learned evidence:
  [a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md)

## Outputs And Evidence

Current outputs:

- Event-value / advantage objective contract:
  [a7_event_value_advantage_credit_head_objective_contract_20260604.md](a7_event_value_advantage_credit_head_objective_contract_20260604.md).
- Policy-head prototype:
  `hybrid_event_credit_head_lr_scale`,
  `HierarchicalMoEExecutionPolicy.get_hybrid_event_credit()`, and
  `_HybridActionDistribution.fire_event_q_values()` / `fire_event_advantage()`
  in `python/rl/policy_algo/policies.py`, covered by
  `tests/hmoe/test_hmoe_policy.py`.
- PPO auxiliary-credit coupling:
  `compute_first_event_credit_loss()` and
  `first_event_credit_batch_from_rollout_data()` in
  `python/rl/policy_algo/first_event_hazard.py`, plus
  `AdaptiveKLPPO._first_event_credit_loss()` in
  `python/rl/policy_algo/ppo_adaptive_kl.py`, covered by
  `tests/hmoe/test_a6_event_head_update_strength.py` and
  `tests/hmoe/test_hmoe_ppo_warmup.py`.
- Config and diagnostics:
  [a7_event_value_advantage_credit_head_config_diagnostics_20260604.md](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md),
  the A7 active config under `examples/config/training/active/air_combat/`,
  callback event-credit diagnostics in `python/training/diagnostics.py`, and
  process-probe A7 summary metrics in
  `tools/diagnostics/air_combat_stage0_process_probe.py`.
- Focused validation:
  [a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md).
- Short learned evidence:
  [a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md).
- Target construction and credit-sign audit:
  [a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.md](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.md).
- Shadow-quality target repair:
  [a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md).
- Legal-state projection and coupling audit:
  [a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md).
- Legal-state projection contract:
  [a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md).
- Projected legal-open credit prototype:
  [a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md).
- Short projection learned evidence:
  [a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md).

Planned follow-on outputs:

- Projection eligibility root-cause audit.

## Acceptance Gate

A7 can be accepted only when:

- deterministic probing executes one authorized first release inside the
  configured quality window;
- stochastic probing does not accumulate high pre-window release probability;
- A3/A5 one-shot discipline remains intact: zero unauthorized releases, repeat
  releases, and shot-budget violations;
- diagnostics show the event advantage has the expected sign:
  `Q_hold > Q_fire_once` pre-window and `Q_fire_once > Q_hold` in the quality
  window;
- HMoE gap implications are either shown not to block A7 or recorded as a
  separate held architecture follow-on;
- M2, missile authority, Pk/fuze/damage authority, `2v2`, self-play, and real
  doctrine remain held.

## Residuals And Next Steps

- Immediate next step: run `A7-EVC-O Projection Eligibility Root-Cause Audit`.
  `A7-EVC-N` shows projection is enabled but active projected rows stay at
  `0.0`; the remaining question is why shadow-quality evidence does not enter
  the projected legal-open loss path in the learned run.
- The repair direction is legal-state counterfactual projection with a stronger
  separation between raw shadow opportunity learning and legal-state policy
  distillation, not another blind coefficient-only training run.
- Adaptive label weight scheduling remains a guardrail candidate, not the
  primary repair.
- HMoE hierarchical computation remains an issue-board item unless A7 evidence
  proves it blocks policy coupling after correct credit signs are learned.

## Archive

No A7 artifacts are archived yet. Historical A7 records move to
[archive/README.md](archive/README.md) only after a replacement current-status
or closeout surface exists.
