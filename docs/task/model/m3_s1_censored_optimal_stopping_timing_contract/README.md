# M3-S1 Censored Optimal-Stopping Timing Contract

Status: `2026-06-05` P5 short-training evidence pass after nonfinite-probe
training-path repair; no learned-policy acceptance claim.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent model task index: [Model Tasks](../README.md)
- M3 model-selection synthesis:
  [m3_model_selection_synthesis_20260605.md](../m3_optimal_stopping_model_selection/m3_model_selection_synthesis_20260605.md)
- Current architecture boundary map:
  [m3_s1_model_architecture_boundary_map_20260605.md](m3_s1_model_architecture_boundary_map_20260605.md)
- A7 current empirical blocker:
  [A7 Current Status](../../air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_current_status_20260604.md)
- Subproject standard:
  [Subproject Creation Standard](../../../agent/rules/subproject_creation_standard.md)

## Purpose

M3-S1 turns the M3 model-selection decision into an implementation-facing
contract. The target is not another A7 coefficient repair. The target is a
clear model boundary for one-shot timing: an agent observes a sequence, may stop
at most once under a legal mask, must preserve low early-event mass, and must
choose inside a desirable window when evidence supports it.

This subproject also isolates the current model spine and branches before code
changes. Rewards, legality gates, policy heads, rollout labels, and auxiliary
losses must have separate ownership so future edits do not keep mixing reward
shaping, PPO losses, and first-event supervision in one patch surface.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| M1 action surface | accepted input | `air_combat_hybrid_v1` is a flat 12D transport with policy-side hybrid semantics. | Does not prove learned fire discipline. |
| A6/A7 first-event branch | held input | A7 supplies event heads, credit heads, label plumbing, and diagnostics, but learned behavior remains blocked. | A7 stays an evidence source, not the main contract. |
| M3 model selection | pass input | M3 recommends censored optimal stopping with wait-preserving data and survival/event-time calibration. | M3 did not open implementation. |
| Architecture separation | pass contract | This README and the boundary map name model trunk, branches, rewards, and auxiliary losses. | No runtime refactor is accepted yet. |
| Implementation | pass | P4 adds independent stopping-head, grouped evidence/loss helper, and PPO-side grouped auxiliary pass. | No learned-policy success claim. |
| Validation dispatch | evidence pass | P5 diagnostics, bounded 8k training, and deterministic/stochastic post-run probes are recorded. | Learned executable fire timing remains held. |

## Scope

In scope:

- Write the model trunk/branch ownership contract before training edits.
- Define the data/censoring route for wait-preserving timing evidence.
- Replace flattened per-row first-event objectives with grouped
  episode/window stopping objectives where needed.
- Define a deterministic stop-vs-continue boundary and survival/event-time
  diagnostics.
- Separate environment rewards from auxiliary training losses and from C2/ROE
  legality gates.

Out of scope:

- Broad M2 release or sequence-native PPO rewrite as the first move.
- Reward-only fixes for first-event timing.
- Weakening C2/ROE, action masks, missile legality, or one-shot gates to make
  training easier.
- Claiming A7, M3-S1, or any learned policy is accepted before acceptance probes
  pass.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary Map` | Freeze model spine, branch, reward, and loss ownership. | M3 synthesis exists. | Boundary map names each owner, write surface, and forbidden coupling. | pass |
| `P1 Data/Censoring Contract` | Define wait-preserving timing evidence and rollout metadata. | P0 boundary map reviewed. | Contract explains how early events censor suffixes and how later desirable windows remain observable. | pass |
| `P2 Grouped Objective` | Specify grouped survival/stopping loss over episode/window IDs. | P1 data route exists. | Loss design keeps window structure instead of reducing to shuffled per-row BCE. | pass |
| `P3 Policy Head Contract` | Decide whether to reuse event-logit delta or add a survival/event-time head. | P2 objective exists. | Deterministic stop boundary and calibrated event-time diagnostics are defined. | pass |
| `P4 Integration Slice` | Implement only the minimum data/loss/head changes selected by P1-P3. | P1-P3 accepted. | Focused tests pass without reward or legality regressions. | pass |
| `P5 Validation` | Run diagnostic and short training gates. | P4 focused tests pass. | Boundary crossing, early mass, one-shot legality, and grouped labels are reported. | pass |
| `P6 Closure` | Sync status, residuals, and parent indexes. | Validation evidence exists. | Docs distinguish accepted code paths from held learned behavior. | held |

## Task Clusters

- Task cluster plan:
  [m3_s1_censored_optimal_stopping_timing_contract_task_clusters_20260605.md](m3_s1_censored_optimal_stopping_timing_contract_task_clusters_20260605.md)
- Dispatch queue:
  [m3_s1_censored_optimal_stopping_timing_contract_dispatch_queue_20260605.md](m3_s1_censored_optimal_stopping_timing_contract_dispatch_queue_20260605.md)

## Outputs And Evidence

- Architecture boundary map:
  [m3_s1_model_architecture_boundary_map_20260605.md](m3_s1_model_architecture_boundary_map_20260605.md)
- Data/censoring contract:
  [m3_s1_data_censoring_contract_20260605.md](m3_s1_data_censoring_contract_20260605.md)
- Grouped objective contract:
  [m3_s1_grouped_stopping_objective_contract_20260605.md](m3_s1_grouped_stopping_objective_contract_20260605.md)
- Policy head boundary contract:
  [m3_s1_policy_head_boundary_contract_20260605.md](m3_s1_policy_head_boundary_contract_20260605.md)
- P4 dispatch review:
  [m3_s1_p4_dispatch_review_20260605.md](m3_s1_p4_dispatch_review_20260605.md)
- P5 dispatch plan and short-training evidence:
  [m3_s1_p5_dispatch_plan_20260605.md](m3_s1_p5_dispatch_plan_20260605.md)
- Learned-policy acceptance evidence: held after P5 because deterministic
  executable release remains flat.

## Acceptance Gate

This subproject can be marked accepted only when:

- the model trunk/branch boundary is documented and reflected in code layout or
  adapter functions;
- first-event timing training is based on grouped episode/window objectives or
  an explicitly justified fallback, not accidental per-row classification;
- reward shaping remains an environment scalar signal and is not used as a
  substitute for legality, censoring, or event-time supervision;
- deterministic probes cross the stop boundary inside desirable windows on
  held-out wait-preserving trajectories;
- cumulative prewindow event mass remains below the configured budget;
- stochastic rollout remains one-shot legal and does not weaken C2/ROE masks;
- learned-policy success is not claimed until the validation gates pass.

## Residuals And Next Steps

- P3 selects an independent survival/stopping head as the long-term model
  object; executable fire logits are an adapter/action branch only.
- `P4 Minimal Integration` passed as a bounded implementation slice. It adds an
  independent stopping head, grouped evidence/loss helper, and PPO-side grouped
  auxiliary pass without changing reward or legality gates.
- `P5 Validation` is evidence-complete. It fixed a diagnostic-path drift in
  `--nonfinite_probe`, proved the independent M3 stopping head can receive
  grouped stopping updates, and recorded deterministic/stochastic probes.
- P5 did not accept learned executable fire timing: deterministic release remains
  flat, stochastic release remains sampling-driven, and the executable hybrid
  action branch is still separate from the M3 stopping head.
- Follow-up root-cause audit moved to
  [M3-S2 Fire-Timing Learnability Audit](../m3_s2_fire_timing_learnability_audit/README.md),
  which found release reachability but not legal timing identifiability in the
  current return/effects path.
- Treat M2 sequence memory as a later candidate if grouped stopping objectives
  still cannot represent the timing evidence.
- Keep A7 local repairs archived as evidence once M3-S1 supersedes the actor
  teaching path.

## Archive

No archive records exist yet.
