# M3-S1 Grouped Stopping Objective Contract

Status: `2026-06-05` pass; P2 objective contract accepted for design, with
implementation now tracked by the P4 dispatch queue.

Parent: [M3-S1 Censored Optimal-Stopping Timing Contract](README.md).

Inputs:

- [P1 Data/Censoring Contract](m3_s1_data_censoring_contract_20260605.md)
- [M3 Model-Selection Synthesis](../optimal_stopping_model_selection_20260605/m3_model_selection_synthesis_20260605.md)
- [Architecture Boundary Map](m3_s1_model_architecture_boundary_map_20260605.md)

## Decision

M3-S1 will not compute the stopping objective from ordinary shuffled PPO
minibatches. The first implementation route must use a grouped evidence carrier
and a rollout-level auxiliary pass, while leaving base PPO minibatches unchanged.

Recommended first implementation shape:

```text
collect_rollouts()
  -> ordinary PPO rollout buffer
  -> M3S1 grouped timing evidence sidecar

train()
  -> base PPO minibatch loop unchanged
  -> M3S1 auxiliary grouped pass over complete windows/groups
```

If memory pressure appears, chunk by complete groups, not random rows.

## Mathematical Object

For each group `g` with ordered rows `t = 1..T_g`:

```text
M_t       = legal executable stop mask
Q_t       = desirable quality-window indicator
z_t       = stop logit / boundary score
lambda_t  = M_t * sigmoid(z_t)
S_t       = product_{k < t} (1 - lambda_k)
p_t       = S_t * lambda_t
p_none    = S_{T_g + 1}
```

The grouped loss must reason about event mass over the whole group:

```text
P_window = sum_{t: Q_t = 1} p_t
P_early  = sum_{t: Q_t = 0 and before first desirable row} p_t
```

The default grouped objective is:

```text
L_group =
  - log(P_window + eps)                 for groups with supported desirable window
  + alpha * max(0, P_early - rho)^2     early stop mass budget
  + beta  * censor_or_no_event_term
  + gamma * optional ranking/margin auxiliary
```

For no-window groups:

```text
L_none = -log(p_none + eps)
```

For early-event censored prefixes:

```text
L_prefix =
  -log(S_tau + eps)
  + alpha * max(0, P_before_tau - rho_prefix)^2
```

The early-event prefix loss does not create labels for the unobserved suffix.

## Required Carrier

The grouped evidence carrier must be available before `rollout_buffer.get()`
destroys `(step, env)` layout.

Required group-level fields:

| Field | Meaning |
| --- | --- |
| `group_id` | Unique group id for the loss pass. |
| `episode_id` | Episode id for cross-rollout/censor accounting. |
| `route_source` | `on_policy`, `forced_hold_probe`, or future supported source. |
| `row_indices` | Ordered row indices in the group. |
| `step_indices` | Ordered step indices. |
| `env_indices` | Env slots for row reconstruction. |
| `legal_mask` | Executable legal stop mask `M_t`. |
| `quality_mask` | Desirable window mask `Q_t`. |
| `accepted_event` | Executed first event indicator. |
| `censoring_kind` | Group censoring type. |
| `censor_step` | Censor boundary, if any. |
| `support_horizon` | Last observed support row. |

Optional diagnostic fields:

- policy fire request;
- event-logit delta at collection time;
- fire probability at collection time;
- target range / track age / launch-window age;
- reward breakdown reference only, not target ownership.

## Loss Integration Rule

Allowed:

- compute base PPO losses from normal minibatches;
- compute M3-S1 grouped loss from complete groups or complete-group chunks;
- backpropagate the grouped loss through current policy observations for the
  selected group rows;
- log grouped diagnostics independently from A6/A7 legacy losses.

Not allowed:

- use `rollout_buffer.get(batch_size)` shuffled samples to compute
  `P_window`, `P_early`, survival products, or no-event mass;
- rely on `window_id` inside a random minibatch as proof that a full group is
  present;
- apply group mass caps only to minibatch fragments and call that a grouped
  event-time objective;
- train executable event logits from closed-mask shadow rows without an
  explicit projection/source contract.

## Relationship To A6/A7

A6 hazard, A7 credit, and A7 policy-margin losses remain support/diagnostic
branches:

- A6 row-wise BCE can remain a legacy local signal.
- A7 `Q_fire_once - Q_hold` can remain a ranking/value diagnostic.
- A7 event-policy margin can support boundary shaping only when fed legal-open
  or explicitly projected evidence.

M3-S1 acceptance depends on grouped survival/stopping metrics, not on A6/A7 loss
activity alone.

## Diagnostics Required Before Short Training

Before any short learned run is used as evidence, log:

- grouped active group count;
- grouped row count;
- groups with desirable window;
- groups with early-event censoring;
- mean/quantile `P_window`;
- mean/quantile `P_early`;
- no-event mass;
- deterministic boundary crossing step;
- boundary crossing relative to first desirable row;
- closed-mask executable-logit training count, expected `0`;
- one-shot legality count.

## Next Contract

P3 selects an independent survival/stopping head as `z_t`, not the existing
hybrid event-logit delta. P3 also defines deterministic deployment:

```text
stop iff M_t = 1 and z_t >= threshold
```

Implementation has passed through `M3S1-P4 Minimal Integration`; the grouped
objective remains constrained to complete groups or complete-group chunks.
