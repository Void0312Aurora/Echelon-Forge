# A5 Constrained Event Action Model

Status: `2026-06-03` held after short learned-policy evidence. A5 has accepted
the surface audit, event contract, runtime state machine, policy event head,
reward/config cleanup, and diagnostics implementation. A5 remains not accepted:
the short A5 post-change run fixed stochastic release discipline but did not
make deterministic policy request `fire_once`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task: [../README.md](../README.md)
- A3 C2/ROE release discipline:
  [../a3_c2_roe_release_discipline/README.md](../a3_c2_roe_release_discipline/README.md)
- A4 authorized first-shot training signal:
  [../a4_authorized_first_shot_training_signal/README.md](../a4_authorized_first_shot_training_signal/README.md)
- M1 action interface split:
  [../../model/m1_action_interface_split/README.md](../../model/m1_action_interface_split/README.md)
- Subproject creation standard:
  [../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)
- Research notes used as non-authoritative design input:
  [temp-01](../../../temp/6/6·3/temp-01.md),
  [temp-02](../../../temp/6/6·3/temp-02.md), and
  [temp-03](../../../temp/6/6·3/temp-03.md)

## Purpose

A3 made C2/ROE release discipline observable and testable. A4 then showed that
reward shaping, a combat-weapons HMoE route, binary diagnostics, and a bounded
fire-opportunity penalty still do not make deterministic policy fire. The
retained diagnosis is now structural: `fire_weapon` is being treated too much
like a per-step binary or thresholded control, while missile release is a
constrained first-event decision.

This subproject defines and implements the long-range correction: a constrained
semi-MDP event-action architecture where legality is handled by C2/ROE/weapon
state and masks, while policy learns `hold` versus `fire_once` only inside valid
engagement windows.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A3 C2/ROE constraints | accepted | A3 exposes authorization, shot budget, pending assessment, salvo, and reattack fields. | It classifies and constrains release discipline; it does not make learned deterministic release happen. |
| A4 reward/routing repair | held | A4 binary diagnostics show authorized-window `fire_weapon` remains near `0.22%` probability / `-6.11` max logit; opportunity penalty was rejected. | Reward magnitude and route selection are not sufficient root fixes. |
| M1 hybrid action interface | accepted | `air_combat_hybrid_v1` separates continuous flight axes from switches, selectors, and pulse commands. | The fire pulse still needs event support, post-launch suppression, and deterministic evaluation semantics. |
| External design notes | design input | `docs/temp/6/6·3/temp-01..03.md` converge on state machine + mask + event head. | These notes are not authority; A5 turns the decision into maintained task scope. |
| Event-action architecture | held after evidence | A5 contract, runtime state machine, policy event head, active S1 C2/ROE reward/config cleanup, diagnostics implementation, and short learned-policy evidence are recorded. | Deterministic `fire_once` remains below hold; event-value / first-event timing follow-on is needed before acceptance. |

## Scope

In scope:

- Define `engagement_state` and `fire_mask` as policy-visible event-action
  support, not reward preferences.
- Replace policy-facing `fire_weapon` threshold semantics in S1 C2/ROE training
  with an event head such as `MaskedCategorical([hold, fire_once])`.
- Enforce `AuthorizedReady + fire_once -> FiredAssess` and default post-launch
  fire suppression until an explicit `ReattackReady` or other authorized
  follow-on state exists.
- Keep training and deterministic evaluation on the same event-action structure.
- Preserve diagnostics for requested, accepted, rejected, authorized, violation,
  repeated, and post-launch fire attempts.
- Decide whether the first implementation uses masked categorical, event Q-head,
  or a staged path where masked categorical is accepted first and Q/hazard is
  deferred.

Out of scope:

- Missile physics, guidance, Pk authority, deterministic fuze authority, or
  high-fidelity damage authority changes.
- Real-world BVR doctrine, classified ROE, or claims about actual fighter release
  authorization practice.
- M2 Causal Transformer release, `2v2`, self-play, or sequence-native policy
  implementation before A5 acceptance evidence exists.
- Treating pure reward tuning or global pulse-prior relaxation as the main
  remedy.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Convert the A4 held diagnosis and temp research notes into durable task scope. | A4 deterministic fire remains 0 and reward/routing trials are held. | README, current status, acceptance, dispatch queue, archive boundary, and task clusters exist. | pass |
| `P1 Contract Audit` | Map the current action, observation, reward, policy, diagnostic, and config surfaces. | P0 complete. | A precise implementation write set and risk map exist. | pass |
| `P2 Event Contract` | Define `engagement_state`, `fire_mask`, event actions, state transitions, and deterministic evaluation semantics. | P1 facts available. | Contract docs freeze event support independently of reward; focused implementation tests remain in P3/P4. | pass |
| `P3 Runtime Integration` | Implement the constrained state machine and event action adapter for S1 C2/ROE. | P2 contract accepted. | Runtime rejects structural multi-fire and exposes post-launch state. | pass |
| `P4 Policy Integration` | Add event action distribution or event Q-head with correct PPO log-prob/eval semantics. | P2/P3 stable. | Policy tests prove mask, log-prob, entropy/stats, and deterministic event behavior. | pass |
| `P5 Scenario And Reward Cleanup` | Move S1 C2/ROE active entries to event-action semantics and simplify reward responsibilities. | P3/P4 available. | Config tests and reward tests show constraints are not being learned via penalties. | pass |
| `P6 Validation` | Run focused tests plus learned-policy probes. | Implementation paths pass unit tests. | Deterministic policy either executes one authorized first shot or residual is evidence-backed. | held after evidence |
| `P7 Closure` | Sync A3/A4/M1/M2 and parent indexes. | P6 evidence complete. | A5 is accepted or held with an explicit residual map. | held closure pending cross-doc sync |

## Task Clusters

- Task cluster plan:
  [a5_constrained_event_action_model_task_clusters_20260603.md](a5_constrained_event_action_model_task_clusters_20260603.md)
- Current status:
  [a5_constrained_event_action_model_current_status_20260603.md](a5_constrained_event_action_model_current_status_20260603.md)
- Dispatch queue:
  [a5_constrained_event_action_model_dispatch_queue_20260603.md](a5_constrained_event_action_model_dispatch_queue_20260603.md)
- Acceptance gate:
  [a5_constrained_event_action_model_acceptance_20260603.md](a5_constrained_event_action_model_acceptance_20260603.md)
- Surface audit:
  [a5_constrained_event_action_model_surface_audit_20260603.md](a5_constrained_event_action_model_surface_audit_20260603.md)
- Event action contract:
  [a5_constrained_event_action_model_event_contract_20260603.md](a5_constrained_event_action_model_event_contract_20260603.md)
- Implementation evidence:
  [a5_constrained_event_action_model_implementation_evidence_20260603.md](a5_constrained_event_action_model_implementation_evidence_20260603.md)
- Short learned-policy evidence:
  [a5_constrained_event_action_model_short_learned_probe_20260603.md](a5_constrained_event_action_model_short_learned_probe_20260603.md)

## Outputs And Evidence

Expected outputs:

- Event-action contract for `engagement_state`, `fire_mask`, and
  `hold/fire_once`:
  [a5_constrained_event_action_model_event_contract_20260603.md](a5_constrained_event_action_model_event_contract_20260603.md)
- Read-only surface audit accepted as A5-EAM-B:
  [a5_constrained_event_action_model_surface_audit_20260603.md](a5_constrained_event_action_model_surface_audit_20260603.md)
- Runtime state-machine and action-mask tests.
- Policy distribution or event Q-head tests covering stochastic sampling and
  deterministic evaluation.
- Runtime/policy implementation evidence:
  [a5_constrained_event_action_model_implementation_evidence_20260603.md](a5_constrained_event_action_model_implementation_evidence_20260603.md)
- Updated S1 C2/ROE training/eval config entries.
- Diagnostics proving requested versus executed release and post-launch
  suppression.
- Learned-policy evidence comparing deterministic and stochastic behavior.
  The short A5 learned-policy probe is now recorded, but it is a held outcome.

## Acceptance Gate

This subproject can be marked accepted only when:

- `fire_weapon` is no longer a policy-facing per-frame continuous threshold or
  unconstrained Bernoulli for the accepted S1 C2/ROE training entry.
- Illegal fire is unavailable by action support or state-machine transition, not
  primarily discouraged through reward penalties.
- `fire_once` is consumed as an event and immediately transitions the engagement
  flow into a no-fire assessment state unless explicit reattack authorization is
  present.
- Training-time stochastic exploration and deterministic evaluation use the same
  masked event action structure.
- Focused tests cover mask behavior, post-launch suppression, repeated-fire
  rejection, policy log-prob/eval semantics, and active config wiring.
- Learned-policy evidence shows a deterministic authorized first shot, or the
  remaining blocker is explicitly assigned to a later policy/optimization
  package without reopening reward-only tuning. The current evidence is the
  latter: stochastic release discipline is fixed, deterministic release remains
  held.
- Documentation still refuses missile physics, Pk, fuze, true BVR doctrine, and
  M2 release overclaims.

## Residuals And Next Steps

- First implementation should prefer explicit state machine + masked event
  categorical because it fixes the structural multi-fire and eval mismatch while
  staying compatible with the current PPO stack.
- Event Q-head, first-shot curriculum, or hazard / first-event objective is the
  preferred follow-on because deterministic timing remains held after the short
  A5 run. That follow-on is now tracked as
  [../a6_event_value_first_event_timing/README.md](../a6_event_value_first_event_timing/README.md).
- Hazard / first-event likelihood and hierarchical options are deferred until
  window boundaries, event datasets, and state transitions are stable.
- M2 remains held until A5 evidence shows the event-action surface is coherent.

## Archive

Current A5 records are live. Superseded design notes, rejected variants, and
dated probe records move to [archive/README.md](archive/README.md) after a
replacement current-status or closeout record exists.
