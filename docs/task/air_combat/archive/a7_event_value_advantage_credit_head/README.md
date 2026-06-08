# A7 Event-Value / Advantage Credit Head

Status: `closed on 2026-06-08 / historical event-credit line superseded`.
A7 keeps the event-value / advantage-credit investigation as retained evidence,
but it is no longer the active firing-closure task. The launch gate that matters
for continuing training is now closed by the M3-S2 bounded firing-gate package:
[../../model/archive/m3_s2_fire_timing_learnability_audit/README.md](../../../model/archive/m3_s2_fire_timing_learnability_audit/README.md).
A7 did not accept its own quality-window timing gate; that is historical timing
research evidence, not proof that the current model still cannot fire.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task: [../README.md](../../README.md)
- A3 C2/ROE release discipline pointer:
  [../a3_c2_roe_release_discipline/README.md](../a3_c2_roe_release_discipline/README.md)
- A5 constrained event action model:
  [../a5_constrained_event_action_model/README.md](../a5_constrained_event_action_model/README.md)
- A6 event-value / first-event timing:
  [../a6_event_value_first_event_timing/README.md](../a6_event_value_first_event_timing/README.md)
- A6 root-cause re-scope:
  [../a6_event_value_first_event_timing/a6_event_value_first_event_timing_root_cause_rescope_20260604.md](../a6_event_value_first_event_timing/a6_event_value_first_event_timing_root_cause_rescope_20260604.md)
- HMoE hierarchical computation gap:
  [../../issues/hmoe_hierarchical_computation_gap/README.md](../../../issues/hmoe_hierarchical_computation_gap/README.md)
- A6 launch-window label-density issue:
  [../../issues/a6_launch_window_label_imbalance/README.md](../../../issues/a6_launch_window_label_imbalance/README.md)
- Subproject creation standard:
  [../../../agent/rules/subproject_creation_standard.md](../../../../agent/rules/subproject_creation_standard.md)

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

## Historical Evidence State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Lifecycle | closed; superseded | M3-S2 later accepts the bounded firing gate for the active scenario/config pair. | A7 is not the current launch blocker. |
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
| A7 projection eligibility audit | pass; spawned P | [Projection eligibility root-cause audit](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.md) shows N training diagnostics have no accepted release, while stochastic probe reconstruction produces `3280` `shadow_quality` positives. | M projection is candidate-starved because it depends on early accepted release; next work should define legal-open opportunity credit that does not depend on sampling the failure mode. |
| A7 legal-open opportunity contract | pass; spawned Q | [Legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md) selects `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` as a real legal-open quality-window positive source. | P is docs-only; implementation, training, and learned behavior remain held until Q focused gates pass. |
| A7 legal-open opportunity prototype | pass; evaluated by R | [Legal-open opportunity credit prototype](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md) implements direct legal-open quality positives, source metrics, active config knobs, and focused tests. | Q proves the source/loss/diagnostic path only; R now evaluates learned behavior as held. |
| A7 short opportunity learned evidence | pass; held outcome | [Short opportunity learned evidence](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md) records the r1 32k train and deterministic/stochastic probes after direct legal-open opportunity credit. | Source starvation is fixed, but deterministic remains `0` releases, stochastic still fires early, and quality-window advantage remains negative. |
| A7 explicit state completion | pass; held outcome | [Explicit state completion probe](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.md) adds `air_combat_c2_roe_v2`, exposes legal/window age and readiness fields, and runs a 32k learned probe. | Observability is improved, but deterministic remains `0` releases and quality-window advantage remains negative. |
| A7 value/policy coupling audit | pass; breakpoint verified | [Value/policy coupling audit](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.md) adds an offline fixed-batch credit-head fit probe and shows `1356` legal-open positives can be fit from negative to positive advantage with the credit head alone. | The label/value object is locally fit-able; the remaining blocker is online joint-training/update coupling. |
| A7 online update-path isolation | pass; blocker localized | [Online update-path isolation](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.md) adds a gradient/update diagnostic showing PPO-alone credit-head gradient is `0.0`, while PPO+A7 global clipping reduces credit-head effective norm from about `0.4855` to `0.00689`; A7 value and delta-align also conflict in shared actor/features. | The next fix should decouple A7 credit updates from shared PPO clipping and representation drift; this is not acceptance. |
| A7 online credit update contract | pass; held outcome | [Online credit update contract](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.md) adds detached-latent credit values, a separate credit-head-only value update, separate clip budget, positive-only delta alignment, active config flags, and nonfinite-probe parity. | The update contract is repaired, but 8k evidence still ends with deterministic `0` releases and negative legal-open advantage. |
| A7 active update-window diagnosis | pass; spawned X | [Active update-window diagnosis](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.md) shows a 512-step stochastic episode contains `231` `shadow_quality` positives, but the same trajectory split into `128` step training chunks has only `5` early negative labels and then `0` active labels. | The remaining blocker is rollout-boundary credit-state loss, not another coefficient sweep. |
| A7 cross-rollout first-event state | pass; evaluated by Y | [Cross-rollout first-event credit state](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.md) adds A7-only per-env rollout history, same-episode carried-prefix label construction, reset on episode advance, nonfinite-probe parity, and focused chunk-vs-full regression coverage. | Focused repair only; Y shows behavior remains held after the repair. |
| A7 post-X learned observation | pass; held outcome | [Post-X learned observation](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.md) records a 32k post-X train, deterministic/stochastic probes, and a longer stochastic probe. | X's signal is live, but deterministic stays `hold`; stochastic samples exactly one authorized release but still fires too early and produces no effects/damage chain. |
| A7 execution breakpoint analysis | pass; held outcome | [Execution breakpoint analysis](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.md) reconstructs fixed-batch labels, credit-head fit, and event-logit fit after Y. | The root fault is the value-to-policy contract: tiny detached credit advantages plus positive-only delta alignment do not create a robust signed actor timing discriminator. |
| A7 event-policy margin repair | pass; held outcome | [Event-policy margin repair](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.md) adds a direct signed event-logit margin and a bounded actor/event separate update lane, then rejects A7-only safe-bias relaxation as label starvation. | The startup fire prior is conservative again; A7 still needs a learned timing discriminator that preserves low prewindow hazard. |

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
| `P7 Closure` | Accept, hold, or re-scope A7. | P6 evidence exists. | Parent/A6/issues docs reflect evidence without overclaim. | pass; historical sync |
| `P8 Target Audit` | Diagnose the negative quality-window credit sign. | P7 sync complete. | Target/loss construction names the failing link and next repair. | pass; repaired by J |
| `P9 Shadow Target Repair` | Implement and test shadow-quality counterfactual targets. | P8 audit exists. | Early stochastic release no longer censors future quality evidence from target credit, and learned-policy probe evidence records the residual behavior. | pass; held outcome |
| `P10 Projection Audit` | Diagnose why repaired positives do not move legal-open quality states. | P9 repair probe exists. | Projection/coupling failure is separated from missing positives, HMoE redesign, and coefficient-only tuning. | pass; spawned L contract |
| `P11 Projection Contract` | Define the legal-state projection mechanism before implementation. | P10 audit exists. | Contract selects projected legal-open positive alignment and names implementation gates. | pass; implemented by M |
| `P12 Projection Prototype` | Implement projected legal-open credit from the L contract. | P11 contract exists. | Focused tests prove projection whitelist, unsupported-layout refusal, no raw closed-mask delta alignment, and projected positive delta pressure. | pass; N evaluated learned behavior |
| `P13 Projection Learned Evidence` | Run short projected-credit learned-policy probe. | P12 focused gates pass. | Projection metrics, deterministic/stochastic timing, and one-shot discipline are recorded. | pass; held outcome |
| `P14 Projection Eligibility Audit` | Diagnose why projection active rows remain zero in the learned run. | P13 evidence exists. | Rollout/loss handoff from shadow-quality labels to projected legal-open rows is explained before another training wave. | pass; spawned P |
| `P15 Opportunity Credit Contract` | Define legal-open positive opportunity credit that does not depend on early accepted release. | P14 evidence exists. | Contract names target source, loss split, diagnostics, and rollback gates. | pass; spawned Q |
| `P16 Opportunity Credit Prototype` | Implement legal-open opportunity credit from the P contract. | P15 contract exists. | Focused tests prove source construction, loss routing, diagnostics, and A3/A5 legality boundaries before training. | pass; spawned R |
| `P17 Short Opportunity Learned Evidence` | Run a bounded learned-policy probe after Q and compare source counts/timing against N. | P16 focused gates pass. | Evidence records legal-open quality source counts, deterministic/stochastic timing, one-shot discipline, and advantage signs. | pass; held outcome |
| `P18 Explicit State Completion` | Test whether missing Markov state explains the held A7/R outcome. | P17 evidence exists. | V2 observation contract, tests, 32k train, and deterministic/stochastic probes are recorded. | pass; held outcome |
| `P19 Coupling Audit` | Explain why non-starved visible positives move probability but not deterministic mode or advantage sign. | P18 evidence exists. | The breakpoint is verified: the fixed S batch is separable by the credit head, so the residual fault is online joint-training/update coupling. | pass; spawned update-path isolation |
| `P20 Online Update-Path Isolation` | Isolate which online update component blocks the locally fit-able credit signal. | P19 evidence exists. | The blocker is localized to shared PPO global clipping plus shared actor/feature coupling; direct PPO credit-head overwrite is excluded. | pass; spawned update-contract work |
| `P21 Online Credit Update Contract` | Decouple A7 credit value learning from shared PPO clipping and representation drift. | P20 blocker localized. | Separate credit-head-only update, positive-only delta alignment, active config wiring, nonfinite-probe parity, and short learned observation are recorded. | pass; held outcome |
| `P22 Active Update Window Diagnosis` | Determine why protected A7 updates go inactive after early training. | P21 evidence exists. | Rollout-local first-event labels are shown not to equal full-episode labels when early accepted release and quality window cross a rollout boundary. | pass; spawned X |
| `P23 Cross-Rollout First-Event State` | Restore episode-level first-event credit across PPO rollout boundaries. | P22 evidence exists. | Chunked `128` step labels recover full-episode `shadow_quality` positives under the early-release/late-quality-window regression. | pass; evaluated by Y |
| `P24 Post-X Learned Observation` | Re-observe learned behavior after cross-rollout first-event state repair. | P23 focused gates pass. | Training/probe evidence records active labels, advantage signs, deterministic release behavior, stochastic one-shot discipline, and effects/damage status. | pass; held outcome |
| `P25 Execution Breakpoint Analysis` | Explain why post-X labels and credit still do not cross deterministic event-mode selection. | P24 held evidence exists. | Fixed-batch probes separate label presence, credit-head fit, event-head fit, and actor-representation capacity. | pass; spawned event-policy contract work |
| `P26 Event-Policy Margin Repair` | Give the actor/event path a direct signed margin instead of relying on tiny detached credit advantage. | P25 breakpoint exists. | Focused tests and 8k before/after probes record whether the actor event surface changes and whether learned behavior reaches acceptance. | pass; historical held outcome |
| `P27 Closure` | Stop treating A7 as the active firing-closure task. | M3-S2 firing closure evidence exists. | Parent docs and this README point current launch closure to M3-S2 while retaining A7 as timing research history. | closed; superseded by M3-S2 |

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
- Projection eligibility root-cause audit:
  [a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.md](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.md)
- Legal-open opportunity credit contract:
  [a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md)
- Legal-open opportunity credit prototype:
  [a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md)
- Short opportunity learned evidence:
  [a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md)
- Explicit state completion probe:
  [a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.md](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.md)
- Value/policy coupling audit:
  [a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.md](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.md)
- Online update-path isolation:
  [a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.md](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.md)
- Online credit update contract:
  [a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.md](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.md)
- Active update-window diagnosis:
  [a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.md](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.md)
- Cross-rollout first-event credit state:
  [a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.md](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.md)
- Post-X learned observation:
  [a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.md](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.md)
- Execution breakpoint analysis:
  [a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.md](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.md)
- Event-policy margin repair:
  [a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.md](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.md)

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
- Projection eligibility root-cause audit:
  [a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.md](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.md).
- Legal-open opportunity credit contract:
  [a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md).
- Legal-open opportunity credit prototype:
  [a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md).
- Short opportunity learned evidence:
  [a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md).
- Explicit state completion probe:
  [a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.md](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.md).
- Value/policy coupling audit:
  [a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.md](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.md).
- Online update-path isolation:
  [a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.md](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.md).
- Online credit update contract:
  [a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.md](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.md).
- Active update-window diagnosis:
  [a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.md](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.md).
- Cross-rollout first-event credit state:
  [a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.md](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.md).
- Post-X learned observation:
  [a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.md](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.md).
- Execution breakpoint analysis:
  [a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.md](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.md).
- Event-policy margin repair:
  [a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.md](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.md).

## Acceptance Gate

This was the historical A7 timing-quality acceptance gate. A7 is now closed, not
accepted as the current firing solution.

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

## Closeout

- A7 is closed in place as historical event-credit/timing evidence.
- The retained conclusion is that A7 investigated the timing-credit path but did
  not become the current firing-closure authority.
- Do not reopen A7 as the default explanation for current launch behavior. Use
  M3-S2 for the accepted bounded firing gate.
- If timing quality is reopened later, start it as a new model follow-on with
  explicit acceptance gates rather than keeping A7 live.

## Archive

This full A7 package is archived under `docs/task/air_combat/archive/`. The
original task path is now a lightweight pointer README.
