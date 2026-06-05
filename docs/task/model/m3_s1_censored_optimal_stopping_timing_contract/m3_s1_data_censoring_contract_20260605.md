# M3-S1 Data/Censoring Contract

Status: `2026-06-05` pass; P1 contract accepted from D1/D2/D3 diagnostics
packets and local review.

Parent: [M3-S1 Censored Optimal-Stopping Timing Contract](README.md).

Evidence packets:

- `M3S1-D1 Data Censoring Evidence`: pass.
- `M3S1-D2 Group Preservation Evidence`: pass.
- `M3S1-D3 Reward/Loss Boundary Evidence`: pass.

## Decision

M3-S1 will use a wait-preserving data route before changing PPO losses.

Near-term route:

```text
ordinary on-policy rollout:
  use as executed prefix evidence only
  if fire is accepted early, treat the suffix as action-induced censored

wait-preserving probe rollout:
  force continue / suppress executable fire request at the data route boundary
  keep C2/ROE masks authoritative
  reconstruct desirable windows from mission C2/ROE V2 fields

future optional route:
  counterfactual replay branch from the same prefix, if simulator ownership and
  tooling are explicit
```

Low-hazard exploration is not enough as the first contract because it may still
undersample delayed desirable windows.

## Current Evidence

The rollout path already collects event state:

- `AdaptiveKLPPO.collect_rollouts()` records engagement state, fire mask,
  accepted fire, episode id, and launch-window state from policy observations
  and env info.
- Labels are attached after the rollout, before returns/advantages are
  computed.
- The event-action gate accepts only requested fires that pass the fire mask.
  Accepted fire switches local state to `FiredAssess` and closes the fire mask.
- Mission observation V2 already exposes `fire_mask_open`,
  `launch_window_open`, `quality_window_ready`, legal/launch window ages,
  target range, and target track age.
- The first-event buffer already stores active, target, weight, source,
  window age, window id, and had-accepted flags.

This is enough to start a narrow wait-preserving evidence route, but not enough
to define grouped stopping loss safely.

## Censoring Semantics

Let `tau_fire` be the first accepted executable fire event in an episode/window.

If `tau_fire` occurs before the desirable window:

```text
observed prefix:     rows t <= tau_fire
unobserved suffix:   rows t > tau_fire on the no-fire path
training meaning:    prefix survival/no-stop evidence plus early-event penalty
not allowed:         treating the unobserved suffix as ordinary negative rows
```

If a wait-preserving probe reaches a desirable window:

```text
observed window:     legal-open / launch-open / quality-ready rows
training meaning:    positive support for stop mass inside the desirable window
not allowed:         using a closed-mask shadow row to train executable fire
                     logits without projection/source metadata
```

If no desirable window appears before the horizon:

```text
training meaning:    no-event / survival evidence to the observed end
not allowed:         inventing positive stop labels from reward magnitude
```

## Required Metadata

Every M3-S1 timing evidence row or group must identify:

| Field | Purpose |
| --- | --- |
| `row_index` | Stable flattened row id for joining observations/actions/labels. |
| `step_idx` | Ordered timestep inside the rollout fragment. |
| `env_idx` | Environment slot. |
| `episode_id` | Stable episode id across rollout fragments. |
| `window_id` | Stable timing-window id. |
| `window_age` | Age within the current legal/open window. |
| `route_source` | `on_policy`, `forced_hold_probe`, `counterfactual_replay`, or later supported route. |
| `forced_hold` | Whether executable fire was suppressed for data collection. |
| `policy_fire_requested` | Raw policy intent, before execution suppression. |
| `policy_fire_logit_delta` | Optional support diagnostic for the candidate boundary. |
| `fire_mask_open` | Executable legal fire mask. |
| `launch_window_open` | Desirable launch geometry / track freshness mask. |
| `quality_window_ready` | Desirable window indicator used by timing objective. |
| `fire_once_accepted` | Executed accepted event. |
| `censoring_kind` | `none`, `early_event_prefix`, `forced_hold`, `timeout`, or `unsupported`. |
| `censor_step` | First accepted fire or route-specific censor boundary. |
| `group_start_row` / `group_end_row` | Ordered group extent for survival/stopping loss. |
| `support_horizon` | Last observed row supporting candidate stop/no-stop decisions. |

The current A6/A7 labels do not carry all of these fields into minibatch loss.
M3-S1 implementation must add a sidecar grouped evidence object or equivalent
group-preserving view.

## Ownership Clauses

- `air_combat_event_action.py` remains the execution legality owner.
- `reward_runtime/air_combat.py` remains scalar environment reward owner.
- `ppo_adaptive_kl.py::collect_rollouts()` and first-event label attachment are
  the initial data handoff surface.
- First-event label helpers may construct evidence, but M3-S1 grouped
  objectives own the event-time target interpretation.
- No P1 implementation may weaken C2/ROE masks, missile authority, one-shot
  gates, or action transport thresholds to create data.

## Accepted Worker Findings

The D1/D2/D3 packets are accepted for P1 because local review confirmed:

- ordinary accepted fire changes the future state, so later no-fire suffixes are
  not observed on the same trajectory;
- mission V2 already exposes the window features required for desirable-window
  reconstruction;
- PPO minibatches flatten and shuffle first-event fields, so grouped timing
  evidence needs a sidecar or grouped view;
- reward shaping observes C2/ROE categories for scalar return but does not own
  legality or event-time labels.

## Next Contract

P2 must define the grouped stopping objective and its carrier. It must not rely
on ordinary `rollout_buffer.get(batch_size)` samples for grouped likelihoods.
