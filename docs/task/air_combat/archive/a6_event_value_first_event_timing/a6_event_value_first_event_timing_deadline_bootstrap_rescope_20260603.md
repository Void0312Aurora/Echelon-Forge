# A6 Deadline-Bootstrap Re-scope

Status: `2026-06-03` active implementation wave after held first learned evidence.

Parent: [README.md](README.md). Prior evidence:
[a6_event_value_first_event_timing_short_learned_probe_20260603.md](a6_event_value_first_event_timing_short_learned_probe_20260603.md).

## Decision

The first A6 objective proved that first-event labels, rollout buffers, PPO loss,
diagnostics, and world-batch runtime plumbing are live. It did not move
deterministic `fire_once`: the deterministic probe still made `0` requests over
`1840` open-window steps, with fire probability around `0.25%`.

The next wave stays inside A6 and adds a deadline bootstrap:

- keep A3/A5 legality as mask/state-machine authority;
- keep the `hold/fire_once` event head and A6 hazard loss path;
- add a sustained positive first-event target after an authorized open-window
  reaches a configured age threshold;
- use a separate active config for this probe, so the first hazard/curriculum
  evidence remains reproducible.

## Rejected Paths For This Wave

| Path | Decision | Reason |
| --- | --- | --- |
| M2 release vote | rejected for this wave | The failure is now narrowed to event-logit credit under the existing A3/A5 event surface; sequence-native modeling has not yet been proven necessary. |
| Plain hazard/curriculum hyperparameter tuning | rejected as main path | The first run already showed one short decaying seed is too weak. Merely scaling the same transient signal is unlikely to be a durable mechanism. |
| Full event-value head | deferred | It remains the stronger long-term candidate, but adding a new value surface before testing sustained labels would mix bootstrapping and architecture risk. |
| Reward-only legality penalties | rejected | A3/A5 legality is mask/state-owned, and A4 reward-only attempts did not make deterministic fire. |

## Objective Contract

For each first authorized open window `W`, define `age_t` as the 1-based age
inside the window. If an accepted release exists, accepted-release labels keep
priority. If no accepted release exists:

```text
deadline_t = age_t >= a6_first_event_deadline_min_window_age_steps
target_t = 1 if deadline_t else inactive
weight_t = a6_first_event_deadline_weight if deadline_t else 0
source_t = deadline when target_t is active
```

This is not a doctrine claim that firing at the fixed age is tactically optimal.
It is a bounded bootstrap that asks a simpler question: can the current event
head and PPO stack move deterministic masked argmax when the positive signal is
sustained through the open window instead of appearing once and decaying away?

## Implementation Surface

- `python/rl/policy_algo/first_event_hazard.py`
  - adds `A6_FIRST_EVENT_SOURCE_DEADLINE`;
  - adds deadline label arguments;
  - emits sustained positive labels at or after the configured window age.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - accepts `a6_first_event_deadline_weight` and
    `a6_first_event_deadline_min_window_age_steps`;
  - passes deadline knobs to label construction;
  - logs `a6/deadline_weight`.
- `python/rl/support/nonfinite_probe.py`
  - preserves deadline-enabled A6 logging in the traced PPO path.
- `python/training_callbacks.py`
  - records deadline-positive label counts when label diagnostics are present.
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json`
  - provides a separate deadline-bootstrap training entry.

## Acceptance Gate

This wave may produce an accepted A6 result only if:

- focused tests pass for deadline label/source/config/logging behavior;
- deterministic probe produces at least one authorized `fire_once` request and
  release, or event probability moves materially with a precise blocker;
- stochastic probe keeps A5 discipline: one authorized release per episode, zero
  rejected requests, zero violation releases, and zero repeat/budget violations;
- documentation remains explicit that deadline bootstrap is not a real tactics,
  M2, missile physics, Pk, fuze, damage authority, `2v2`, or self-play release.

## Next Evidence

Run the deadline-bootstrap short training entry, then deterministic/stochastic
probes against its `final_model.zip`. Record the result in a dedicated learned
evidence note before changing A6 acceptance status.
