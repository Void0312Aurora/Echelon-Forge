# A6 Event Value And First-Event Timing

Status: `closed on 2026-06-08 / historical first-event timing line superseded`.
A6 records why hazard, deadline, and launch-window labels did not make a stable
standalone timing solution. The current executable firing gate is closed by the
later M3-S2 package:
[../../model/archive/m3_s2_fire_timing_learnability_audit/README.md](../../../model/archive/m3_s2_fire_timing_learnability_audit/README.md).
A6 residuals are retained as timing-quality research history, not as the current
launch-closure status.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task: [../README.md](../../README.md)
- A3 C2/ROE release discipline:
  [../a3_c2_roe_release_discipline/README.md](../a3_c2_roe_release_discipline/README.md)
- A4 authorized first-shot training signal:
  [../a4_authorized_first_shot_training_signal/README.md](../a4_authorized_first_shot_training_signal/README.md)
- A5 constrained event-action model:
  [../a5_constrained_event_action_model/README.md](../a5_constrained_event_action_model/README.md)
- M1 temporal-window HMoE:
  [../../model/m1_temporal_window_hmoe/README.zh.md](../../../model/m1_temporal_window_hmoe/README.zh.md)
- M2 causal Transformer HMoE:
  [../../model/m2_causal_transformer_hmoe/README.zh.md](../../../model/m2_causal_transformer_hmoe/README.zh.md)
- Subproject creation standard:
  [../../../agent/rules/subproject_creation_standard.md](../../../../agent/rules/subproject_creation_standard.md)
- Subagent usage policy:
  [../../../standards/governance/subagent_usage_policy.md](../../../../standards/governance/subagent_usage_policy.md)

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

## Historical Evidence State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Lifecycle | closed; superseded | M3-S2 later accepts the bounded firing gate for the active scenario/config pair. | A6 timing experiments are no longer the active launch blocker. |
| A3 C2/ROE discipline | accepted | Authorization, shot budget, pending assessment, salvo, and reattack fields are observable and tested. | It constrains legality; it does not create event-value credit. |
| A4 reward/routing | held | Reward, HMoE route, binary diagnostics, and opportunity-penalty trials did not make deterministic fire. | Reward-only tuning is no longer the active default. |
| A5 event-action support | held after evidence | Event mask/state machine/policy event head are implemented; stochastic probing executes disciplined authorized releases. | Deterministic learned policy still makes zero `fire_once` requests. |
| A5 retained observation | pass as A6 input | Deterministic: `1880` fire-mask-open steps, `0` fire requests; stochastic: `3` authorized releases over `3` episodes, `0` violations. | This is short-run evidence under retained artifacts, not final policy acceptance. |
| A6 model direction | closed historical evidence | A6 labels/loss enter PPO and diagnostics; deadline bootstrap doubles event probability but deterministic policy still makes zero `fire_once` requests. Event-head audit shows gradients reach shared and HMoE heads; A6-EVT-K then crosses deterministic argmax and executes one authorized release. A6-EVT-L adds launch-window gated labels. A6-EVT-M deterministic probe reaches `34.6% / 35.0%` open-window fire probability but still makes zero requests; stochastic releases at steps `7`, `43`, and `4`. A6-EVT-N shows per-step stochastic hazard accumulation, absorbing first-event censoring, and missing counterfactual hold/fire credit. | This is retained timing research history. M3-S2, not A6, is the current firing-closure authority. |

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
| `P6 Closure/Re-scope` | Sync A3/A4/A5/M1/M2 and choose the next objective wave. | P5 evidence is complete. | Historical A6 residual is recorded and the next wave is bounded to deadline bootstrap rather than M2 release. | pass; historical re-scope |
| `P7 Deadline Bootstrap` | Add sustained open-window deadline labels and a separate active config. | P6 re-scope decision exists. | Focused tests prove label/source/config/logging behavior while A3/A5 masks remain authoritative. | pass |
| `P8 Deadline Short Evidence` | Run short train/probe comparison for the deadline wave. | P7 tests pass. | Deterministic/stochastic probes record whether event logits finally cross masked argmax. | pass; held outcome |
| `P9 Event-Head Update Audit` | Audit whether optimizer/head scaling prevents A6 positives from moving event logits. | P8 held evidence exists. | Focused update probe explains why sustained positives only move probability to about `0.5%`. | pass; held outcome |
| `P10 Event-Head Optimization Lane` | Give `hold/fire_once` event rows a bounded stronger update path. | P9 identifies update strength as the blocker. | Short learned evidence tests whether deterministic argmax can cross without weakening A3/A5 masks. | pass; held timing residual |
| `P11 Launch-Window Timing Contract` | Separate authorization from good first-release timing. | P10 proves event argmax can cross but releases too early. | A bounded contract defines engagement-quality/window labels without weakening A3/A5 masks, and focused tests cover the implementation surface. | pass |
| `P12 Launch-Window Short Evidence` | Test the L contract in learned-policy probes. | P11 focused tests pass. | Deterministic/stochastic outcomes record release timing and discipline. | pass; held outcome |
| `P13 Root-Cause Re-scope` | Stop L tuning and identify the mechanism blocker. | P12 held evidence exists. | Root-cause note explains stochastic hazard accumulation, absorbing first-event censoring, and missing counterfactual hold/fire credit; next contract is re-scoped before more training. | pass; closed by M3-S2 migration |

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
- Launch-window timing contract:
  [a6_event_value_first_event_timing_launch_window_timing_contract_20260604.md](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.md)
- Launch-window short learned evidence:
  [a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.md](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.md)
- Root-cause re-scope:
  [a6_event_value_first_event_timing_root_cause_rescope_20260604.md](a6_event_value_first_event_timing_root_cause_rescope_20260604.md)

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
- Launch-window timing contract implementation completed as `A6-EVT-L`:
  A6 labels now distinguish legal authorization from quality-window release,
  early accepted releases become negative labels, deadline/curriculum positives
  are gated by the quality window, PPO derives contact quality from policy
  observations, and an independent L active config is available.
- Launch-window short learned evidence completed as `A6-EVT-M`: deterministic
  no longer fires near-immediately, but also does not cross; open-window event
  probability reaches `34.6% / 35.0%` and `0` requests. Stochastic still samples
  one authorized release per episode at steps `7`, `43`, and `4`, with no
  rejected, violation, repeat, or budget issues.
- Root-cause re-scope completed as `A6-EVT-N`: additional L training and
  parameter tuning are paused. The current blocker is structural: per-step
  stochastic hazard accumulation can produce early first events before
  deterministic argmax crosses, and an accepted first event censors later
  quality-window evidence. A6 needs a counterfactual event-time/value contract
  before the next implementation or training wave.

Held output:

- The first hazard/curriculum objective is not enough.
- Deadline bootstrap moves the event probability but not deterministic argmax.
- Event-head optimization crosses deterministic argmax, but the learned release
  occurs immediately after authorization/contact rather than proving mature
  first-event timing.
- Launch-window short evidence suppresses deterministic early fire but does not
  yet prove launch-window timing.
- L parameter search is paused because the root cause is missing
  counterfactual hold/fire credit under on-policy absorbing first-event
  collection.

## Acceptance Gate

This was the historical A6 acceptance gate. A6 is now closed as timing-quality
research history, not accepted as the current firing solution.

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

## Closeout

- A6 is closed in place as historical timing evidence.
- The retained conclusion is that hazard/deadline/launch-window labels exposed
  useful gradients but did not provide a stable standalone firing/timing answer.
- Do not reopen A6 as the default explanation for current launch behavior. The
  current firing gate is closed by M3-S2; A6 evidence is only relevant if a new
  timing-quality research task is explicitly opened.
- M2/model-family questions remain outside this closed A6 package.

## Archive

This full A6 package is archived under `docs/task/air_combat/archive/`. The
original task path is now a lightweight pointer README.
