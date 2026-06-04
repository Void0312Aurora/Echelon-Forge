# A7 Event-Value / Advantage Credit Head

Status: `2026-06-04` active implementation subproject. A7 is the follow-on to
the A6 root-cause re-scope: implement an event-value / advantage-credit
mechanism for the masked `hold/fire_once` action before any more launch-window
tuning. `A7-EVC-A/B` are closed by the objective contract, and `A7-EVC-C` has
landed the zero-safe policy-head prototype. PPO auxiliary credit is not wired
yet.

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
| `P4 PPO Integration` | Train the head and connect auxiliary credit to PPO updates. | P3 head available. | Loss, stats, finite behavior, and mask handling are tested. | planned next |
| `P5 Config And Diagnostics` | Add active config and cumulative hazard diagnostics. | P4 integration passes. | Config and callback/process-probe tests expose A7 metrics. | planned |
| `P6 Learned Evidence` | Run short learned-policy probe. | P5 tests pass. | Deterministic/stochastic timing, release counts, and cumulative early hazard are recorded. | planned |
| `P7 Closure` | Accept, hold, or re-scope A7. | P6 evidence exists. | Parent/A6/issues docs reflect evidence without overclaim. | planned |

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

Planned implementation outputs:

- PPO auxiliary-loss implementation.
- Focused tests for loss masks, diagnostics, and active config.
- Short learned-policy evidence comparing against A6-EVT-M.

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

- Immediate next step: dispatch `A7-EVC-D PPO Auxiliary Credit` using the stable
  `hybrid_event_credit_head` API from `A7-EVC-C`.
- Adaptive label weight scheduling remains a guardrail candidate, not the
  primary repair.
- HMoE hierarchical computation remains an issue-board item unless A7 evidence
  proves it blocks advantage-credit learning.

## Archive

No A7 artifacts are archived yet. Historical A7 records move to
[archive/README.md](archive/README.md) only after a replacement current-status
or closeout surface exists.
