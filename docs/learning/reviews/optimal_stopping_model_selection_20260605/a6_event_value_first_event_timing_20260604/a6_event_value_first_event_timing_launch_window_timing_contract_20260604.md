# A6 Launch-Window Timing Contract

Status: `2026-06-04` contract and focused implementation pass; learned-policy
evidence completed separately with held outcome.

Parent: [README.md](README.md).

## Scope

`A6-EVT-K` proved that the masked `hold/fire_once` event decision can cross
deterministic argmax under the dedicated event-head optimizer lane. Its learned
release happened almost immediately after authorization/contact, so `A6-EVT-L`
separates legal authorization from launch-window timing quality.

This contract changes A6 training labels only. It does not change the A3/A5
runtime legality mask, shot budget, pending-assessment suppression, weapon
release kernel, missile physics, Pk, fuze, damage authority, M2, `2v2`, or
self-play.

## Contract Decision

Legal support and timing quality are now distinct predicates:

- Legal window: A3/A5 `AuthorizedReady` plus the policy-facing `fire_once` mask.
- Launch window: a legal-window step whose policy observation contains a recent
  target contact inside the configured range gate, and whose legal-window age is
  above the configured minimum.

The maintained L probe config uses:

- range gate: `8000 m <= target_range <= 30000 m`;
- max track age: `5 s`;
- minimum legal-window age: `32` steps;
- pre-window hold weight: `0.3`;
- early accepted negative weight: `1.0`.

These numbers are bounded bootstrap settings for the current S1 training probe.
They are not a real BVR doctrine, missile launch zone, Pk model, or weapon
authority claim.

## Label Semantics

When no launch-window input is supplied, the previous A6 hazard/deadline label
behavior is unchanged.

When launch-window input is supplied:

- accepted `fire_once` inside the quality window remains a positive first-event
  label;
- accepted `fire_once` before the quality window becomes an explicit negative
  early-accepted label instead of a positive teacher;
- legal-open steps before the quality window can receive weighted hold labels;
- curriculum positives are seeded only inside the quality window;
- deadline positives are emitted only after both the launch-window gate and the
  deadline age condition are satisfied.

This means A3/A5 may still legally accept an early fire request at runtime, but
the A6 objective no longer teaches that "legal" means "fire now."

## Implementation Surface

Code/config changes:

- `python/rl/policy_algo/first_event_hazard.py`
  - Adds launch-window gated label generation.
  - Adds source ids `PREWINDOW=5` and `EARLY_ACCEPTED=6`.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - Adds launch-window PPO knobs.
  - Extracts contact quality from `contacts` or the latest `contacts_history`
    frame in the same policy observation used for action selection.
- `python/rl/support/nonfinite_probe.py`
  - Keeps non-finite probe rollout collection in parity with PPO.
- `python/training_callbacks.py`
  - Logs launch-window enabled state, pre-window hold count, and early accepted
    count.
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json`
  - Adds the independent L active probe entry.

## Validation

Focused validation:

```bash
.venv/bin/python -m compileall -q \
  python/rl/policy_algo/first_event_hazard.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  python/training_callbacks.py
```

Observed: pass.

```bash
.venv/bin/python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  >/dev/null
```

Observed: pass.

```bash
.venv/bin/python -m pytest \
  tests/policy/test_first_event_timing_contracts.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_diagnostics_callback_contracts.py \
  tests/training/test_event_timing_training_config_contracts.py \
  -q
```

Observed: `28 passed`.

## Acceptance And Rollback

`A6-EVT-L` can be considered implementation-complete for the contract surface,
but it is not learned-policy acceptance. `A6-EVT-M` completed the short
train/probe comparison and held the line because deterministic mode did not
cross while stochastic probing still sampled early authorized releases.

Acceptance requires evidence that deterministic release no longer collapses to
near-immediate authorization/contact while preserving A5 invariants:

- one accepted release at most per episode in the S1 single-shot surface;
- zero unauthorized releases;
- zero repeat or shot-budget violations;
- launch-window diagnostics show pre-window negatives and quality-window
  positives are live.

Rollback condition: if follow-on L variants remove deterministic fire entirely
or break A5 release discipline, revert to the K event-head config and re-scope
the label window or value-credit mechanism before changing runtime legality.
