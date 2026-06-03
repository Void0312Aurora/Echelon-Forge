# A6 Event Value And First-Event Timing

Status: `2026-06-03` held after event-head learned-policy evidence. A6 proved
the hazard/curriculum and deadline-bootstrap training paths are live, the audit
shows event-head gradients are routed correctly, and A6-EVT-K now proves the
dedicated event-head optimizer lane can cross deterministic `fire_once` argmax.
A6 remains held because the learned release collapses to near-immediate
authorization/contact timing rather than a mature launch-window decision.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task: [../README.md](../README.md)
- A3 C2/ROE release discipline:
  [../a3_c2_roe_release_discipline/README.md](../a3_c2_roe_release_discipline/README.md)
- A4 authorized first-shot training signal:
  [../a4_authorized_first_shot_training_signal/README.md](../a4_authorized_first_shot_training_signal/README.md)
- A5 constrained event-action model:
  [../a5_constrained_event_action_model/README.md](../a5_constrained_event_action_model/README.md)
- M1 temporal-window HMoE:
  [../../model/m1_temporal_window_hmoe/README.zh.md](../../model/m1_temporal_window_hmoe/README.zh.md)
- M2 causal Transformer HMoE:
  [../../model/m2_causal_transformer_hmoe/README.zh.md](../../model/m2_causal_transformer_hmoe/README.zh.md)
- Subproject creation standard:
  [../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)
- Subagent usage policy:
  [../../../standards/governance/subagent_usage_policy.md](../../../standards/governance/subagent_usage_policy.md)

## Purpose

A5 converted first missile release from per-step binary threshold control into a
masked `hold/fire_once` event action. The retained short probe shows that this
fixed the structural stochastic multi-fire failure: stochastic probing now gets
one authorized release per episode with no repeat or budget violations.

The same probe also shows the residual: deterministic policy observes many
`AuthorizedReady` / fire-mask-open steps but keeps `fire_once` probability near
zero, so masked argmax remains `hold`. A6 treats that residual as an event-value
and first-event timing problem. The next durable fix should move event logits by
giving the policy an explicit value, hazard, or first-event objective, rather
than reopening reward-only legality penalties.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A3 C2/ROE discipline | accepted | Authorization, shot budget, pending assessment, salvo, and reattack fields are observable and tested. | It constrains legality; it does not create event-value credit. |
| A4 reward/routing | held | Reward, HMoE route, binary diagnostics, and opportunity-penalty trials did not make deterministic fire. | Reward-only tuning is no longer the active default. |
| A5 event-action support | held after evidence | Event mask/state machine/policy event head are implemented; stochastic probing executes disciplined authorized releases. | Deterministic learned policy still makes zero `fire_once` requests. |
| A5 retained observation | pass as A6 input | Deterministic: `1880` fire-mask-open steps, `0` fire requests; stochastic: `3` authorized releases over `3` episodes, `0` violations. | This is short-run evidence under retained artifacts, not final policy acceptance. |
| A6 model direction | held after event-head learned evidence | A6 labels/loss enter PPO and diagnostics; deadline bootstrap doubles event probability but deterministic policy still makes zero `fire_once` requests. Event-head audit shows gradients reach shared and HMoE heads; A6-EVT-K then crosses deterministic argmax and executes one authorized release. | The release is near-immediate after authorization/contact, so timing quality remains unresolved. M2 remains held. |

## Scope

In scope:

- Reframe S1 C2/ROE weapon release as a first-event timing problem under a
  constrained semi-MDP event surface.
- Design an explicit event-value mechanism, such as an auxiliary
  action-conditional event value head, first-event hazard objective, or bounded
  first-shot curriculum that directly affects `hold/fire_once` logits.
- Define first-event labels, masks, windows, and diagnostics from A5 event state
  rather than from raw `fire_weapon` thresholds.
- Keep A3/A5 legality and post-launch suppression as constraints, not learned
  penalty preferences.
- Produce short training/probe evidence that compares deterministic event mode,
  event probability, request/accept/release counts, and violations.
- Keep the design compatible with M1 temporal windows and future M2 sequence
  modeling, without releasing M2 in this slice.

Out of scope:

- Reopening broad invalid-fire, pending-assessment, or shot-budget penalties as
  the main legality mechanism.
- Removing A5 masks or state-machine suppression to make fire easier.
- Missile physics, Pk, fuze, damage authority, or stock-weapon authority
  changes.
- Real-world BVR doctrine claims, `2v2`, self-play, or M2 implementation.
- Treating stochastic one-shot behavior alone as deterministic learned-policy
  acceptance.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Observation` | Freeze the A5 retained phenomenon and residual diagnosis. | A5 short learned-policy probe exists. | A6 observation note records deterministic/stochastic contrast and rejects reward-only legality tuning as the next default. | pass |
| `P1 Mathematical Framing` | Abstract the problem as masked first-event timing with delayed sparse credit. | P0 observation is accepted as input. | A design note names the event state, objective target, label source, and failure modes. | pass |
| `P2 Objective Contract` | Choose the first A6 objective contract. | P1 framing exists. | Event-value, hazard, or curriculum target is specified with masks and diagnostics. | pass |
| `P3 Training Kernel Integration` | Implement the bounded auxiliary objective or head. | P2 contract accepted. | Focused policy/PPO tests prove shape, mask, loss, and eval semantics. | pass |
| `P4 Scenario And Config Probe` | Wire the maintained S1 C2/ROE probe to the A6 objective. | P3 tests pass. | Active config tests, diagnostics, and world-batch runtime info prove legality is still state/mask-owned. | pass |
| `P5 Short Learned Evidence` | Run short train/probe comparison. | P4 wiring is valid. | Deterministic `fire_once` mode/probability and release counts are recorded against A5 baseline. | pass; held outcome |
| `P6 Closure/Re-scope` | Sync A3/A4/A5/M1/M2 and choose the next objective wave. | P5 evidence is complete. | A6 remains held and the next wave is bounded to deadline bootstrap rather than M2 release. | pass; re-scoped |
| `P7 Deadline Bootstrap` | Add sustained open-window deadline labels and a separate active config. | P6 re-scope decision exists. | Focused tests prove label/source/config/logging behavior while A3/A5 masks remain authoritative. | pass |
| `P8 Deadline Short Evidence` | Run short train/probe comparison for the deadline wave. | P7 tests pass. | Deterministic/stochastic probes record whether event logits finally cross masked argmax. | pass; held outcome |
| `P9 Event-Head Update Audit` | Audit whether optimizer/head scaling prevents A6 positives from moving event logits. | P8 held evidence exists. | Focused update probe explains why sustained positives only move probability to about `0.5%`. | pass; held outcome |
| `P10 Event-Head Optimization Lane` | Give `hold/fire_once` event rows a bounded stronger update path. | P9 identifies update strength as the blocker. | Short learned evidence tests whether deterministic argmax can cross without weakening A3/A5 masks. | pass; held timing residual |
| `P11 Launch-Window Timing Contract` | Separate authorization from good first-release timing. | P10 proves event argmax can cross but releases too early. | A new bounded contract defines engagement-quality/window labels without weakening A3/A5 masks. | planned |

## Task Clusters

- Task cluster plan:
  [a6_event_value_first_event_timing_task_clusters_20260603.md](a6_event_value_first_event_timing_task_clusters_20260603.md)
- Current status:
  [a6_event_value_first_event_timing_current_status_20260603.md](a6_event_value_first_event_timing_current_status_20260603.md)
- Dispatch queue:
  [a6_event_value_first_event_timing_dispatch_queue_20260603.md](a6_event_value_first_event_timing_dispatch_queue_20260603.md)
- Acceptance gate:
  [a6_event_value_first_event_timing_acceptance_20260603.md](a6_event_value_first_event_timing_acceptance_20260603.md)
- Observation evidence:
  [a6_event_value_first_event_timing_observation_20260603.md](a6_event_value_first_event_timing_observation_20260603.md)
- Mathematical framing:
  [a6_event_value_first_event_timing_mathematical_framing_20260603.md](a6_event_value_first_event_timing_mathematical_framing_20260603.md)
- Objective contract:
  [a6_event_value_first_event_timing_objective_contract_20260603.md](a6_event_value_first_event_timing_objective_contract_20260603.md)
- Short learned evidence:
  [a6_event_value_first_event_timing_short_learned_probe_20260603.md](a6_event_value_first_event_timing_short_learned_probe_20260603.md)
- Deadline bootstrap re-scope:
  [a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.md](a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.md)
- Deadline short learned evidence:
  [a6_event_value_first_event_timing_deadline_short_learned_probe_20260603.md](a6_event_value_first_event_timing_deadline_short_learned_probe_20260603.md)
- Event-head update-strength audit:
  [a6_event_value_first_event_timing_event_head_update_audit_20260603.md](a6_event_value_first_event_timing_event_head_update_audit_20260603.md)
- Event-head optimization lane:
  [a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md](a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md)
- Event-head short learned evidence:
  [a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.md](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.md)

## Outputs And Evidence

Current outputs:

- A6 subproject scope and finite cluster plan.
- A5 retained observation summary for deterministic versus stochastic behavior.
- Mathematical framing accepted as `A6-EVT-B`.
- Objective contract accepted as `A6-EVT-C`: masked first-event hazard with
  bounded curriculum bootstrap.
- Training-kernel prototype accepted as `A6-EVT-D`: hazard label/loss helpers,
  event logit delta access, and focused tests.
- Config/diagnostics and runtime wiring accepted as `A6-EVT-E`: A6 active
  configs expose knobs, diagnostics report event probabilities, world-batch
  C2/ROE info is available, and A6 labels are attached outside policy
  observations.
- Short learned evidence completed as `A6-EVT-F`: deterministic still makes
  `0` requests with `1840` open-window steps and `0.247% / 0.248%` event
  probability; stochastic preserves `3/3` authorized single releases with no
  violations.
- Closure/re-scope completed as `A6-EVT-G`: M2 remains held, plain hyperparameter
  tuning is not the main path, and the next bounded mechanism is deadline
  bootstrap over the existing first-event hazard labels.
- Deadline-bootstrap implementation completed as `A6-EVT-H`: it adds a
  sustained positive target after an authorized open-window age threshold, with
  a separate probe config so the first A6 evidence remains reproducible.
- Deadline short evidence completed as `A6-EVT-I`: deterministic event
  probability moved from about `0.247%` to `0.494%`, but deterministic still made
  `0` requests. Stochastic produced `3/3` authorized releases with zero
  violation/repeat/budget issues, but had one `weapon_not_ready` rejected
  request.
- Event-head update-strength audit completed as `A6-EVT-J`: A6 labels and
  gradients are live, first-shot route gradients reach both shared and HMoE
  heads, and current `3e-5` / low-scale residual settings explain why event
  probability moves but deterministic argmax does not cross.
- Event-head optimization lane implementation completed under `A6-EVT-K`:
  `hybrid_event_head_lr_scale` adds a zero-initialized dedicated `hold/fire_once`
  event-logit head and optimizer group, with a separate active config for
  learned-policy evidence.
- Event-head short evidence completed as `A6-EVT-K`: deterministic now makes
  one accepted authorized release at step `2`; stochastic produces `3/3`
  accepted authorized releases with zero rejected, violation, repeat, or budget
  issues. This proves the event decision is trainable, but exposes an early
  launch-window residual.

Held output:

- The first hazard/curriculum objective is not enough.
- Deadline bootstrap moves the event probability but not deterministic argmax.
- Event-head optimization crosses deterministic argmax, but the learned release
  occurs immediately after authorization/contact rather than proving mature
  first-event timing.

## Acceptance Gate

This subproject can be marked accepted only when:

- The selected objective directly targets masked `hold/fire_once` event timing
  rather than raw `fire_weapon` thresholding.
- A3/A5 legality remains enforced by event mask and state-machine transition.
- Focused tests cover objective shape, mask handling, deterministic evaluation,
  and retained A5 no-repeat/no-budget-violation discipline.
- Short learned evidence shows deterministic `fire_once` probability/mode moves
  materially from A5 baseline and either executes an authorized first release or
  records a precise held blocker outside reward-only legality tuning.
- Documentation still refuses M2 release, real-world doctrine, missile physics,
  Pk, fuze, and damage-authority overclaims.

## Residuals And Next Steps

- Immediate next step: define a launch-window / engagement-quality timing
  contract that separates legal authorization from tactically useful release
  timing.
- Event-value remains a plausible long-term expansion, but the next narrow
  blocker is label/window semantics rather than raw event-head update strength.
- The bounded first-shot curriculum produced early gradient, then correctly
  decayed to zero; by itself it did not move deterministic argmax.
- M2 remains held until deterministic first-event behavior is trainable under
  the current A3/A5 constraints or the A6 residual explicitly justifies sequence
  modeling as the next release vote.

## Archive

Current A6 records are live. Superseded observation notes, rejected objectives,
and dated probe records move to [archive/README.md](archive/README.md) only
after a replacement current-status or closeout surface exists.
