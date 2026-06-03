# A6 Event-Head Optimization Lane

Status: `2026-06-03` `A6-EVT-K` pass for implementation, active config wiring,
and short learned evidence; A6 remains held on timing quality.

Parent: [README.md](README.md). Prior audit:
[a6_event_value_first_event_timing_event_head_update_audit_20260603.md](a6_event_value_first_event_timing_event_head_update_audit_20260603.md).

## Scope

This slice adds a bounded optimizer-owned path for the A5/A6 masked
`hold/fire_once` event logits. It does not change A3/A5 legality, missile
physics, damage authority, `2v2`, self-play, or M2 release status.

The implementation deliberately keeps the existing `action_net` interface
intact. That preserves compatibility with existing safe-action initialization,
tests, and saved-policy constructor behavior.

## Implementation

Code:

- `HierarchicalMoEExecutionPolicy` now accepts
  `hybrid_event_head_lr_scale`.
- When `hybrid_action_spec="air_combat_hybrid_v1"` and
  `hybrid_event_head_lr_scale > 0`, the policy creates a zero-initialized
  `hybrid_event_head`.
- The head outputs two additive deltas, one for the event `hold` logit and one
  for the event `fire_once` logit.
- The head has a dedicated optimizer group named `hybrid_event_head`, with
  `lr_scale=hybrid_event_head_lr_scale`.
- Route diagnostics expose:
  - `a6/event_head_enabled`
  - `a6/event_head_lr_scale`
  - `a6/event_head_delta_abs_mean`
  - `a6/event_head_delta_hold_mean`
  - `a6/event_head_delta_fire_mean`
- Parameter diagnostics expose:
  - `a6/event_head_params/enabled`
  - `a6/event_head_params/lr_scale`
  - `a6/event_head_params/weight_norm`
  - `a6/event_head_params/bias_norm`
  - `a6/event_head_params/max_abs`

Active config:

- Added
  `air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json`.
- It keeps the deadline-bootstrap C2/ROE temporal shaped surface and adds only
  `policy_kwargs.hybrid_event_head_lr_scale=10.0`.
- The previous deadline-bootstrap config remains unchanged for comparison.

## Evidence

Focused tests show:

- The event head is zero-initialized, so initial policy behavior is unchanged.
- The event head receives a dedicated optimizer group and LR scale.
- At the same base LR, the event-head lane moves event delta more than five
  times faster than the current shared/HMoE-only path in the focused hazard-only
  probe.
- The active config is separate from the deadline baseline and bootstraps through
  `train.py --test_only`.

Validation commands:

```bash
.venv/bin/python -m pytest -q tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_policy.py
```

Observed: `28 passed`.

```bash
.venv/bin/python -m pytest -q tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py
```

Observed: `15 passed, 10 subtests passed`.

Broader focused validation:

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_event_head_update_strength.py \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  tests/diagnostics/test_air_combat_process_probe.py
```

Observed: `77 passed, 10 subtests passed`.

Compile/check:

```bash
python -m compileall -q python/rl/policy_algo tests/hmoe tests/training
git diff --check -- python/rl/policy_algo tests/hmoe tests/training docs/task/air_combat examples/config/training/active/air_combat
```

Observed: pass.

Learned-policy evidence:

- [Event-head short learned-policy probe](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.md)
  completed `32768` training steps.
- Deterministic probe: first release at step `2`, `1` request, `1` accepted
  authorized release, `0` rejected, `0` violation/repeat/budget issues.
- Stochastic probe: release steps `4`, `42`, `2`; `3/3` accepted authorized
  releases; `0` rejected, violation, repeat, or budget issues.
- Event-head training diagnostics crossed deterministic event argmax around
  `30720` timesteps, with open-window fire probability about `67.9%`.

## Residual

This slice proves the event decision is trainable under the current A3/A5
surface. It is still not full A6 acceptance because the learned policy fires
almost immediately after authorization/contact. That vacates most
deadline/open-window diagnostics and leaves first-event timing quality
unproven.

The next repair should define a launch-window / engagement-quality timing
contract rather than simply increasing event-head LR again.

## Worker Packet

```md
status: pass; held timing residual
touched files:
- python/rl/policy_algo/policies.py
- tests/hmoe/test_a6_event_head_update_strength.py
- tests/hmoe/test_hmoe_policy.py
- tests/training/test_a6_event_value_active_config.py
- tests/training/test_air_combat_active_training_entries.py
- examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json
- examples/config/training/active/air_combat/README.md
- examples/config/training/active/air_combat/README.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_optimization_lane_20260603.zh.md
commands/outcomes:
- .venv/bin/python -m pytest -q tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_policy.py -> 28 passed
- .venv/bin/python -m pytest -q tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -> 15 passed, 10 subtests passed
- .venv/bin/python -m pytest -q tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_a6_event_value_diagnostics_callback.py tests/diagnostics/test_a6_event_value_process_probe.py tests/training/test_air_combat_active_training_entries.py tests/training/test_cooperative_diagnostics_callback.py tests/diagnostics/test_air_combat_process_probe.py -> 77 passed, 10 subtests passed
- python -m compileall -q python/rl/policy_algo tests/hmoe tests/training -> pass
- git diff --check -- python/rl/policy_algo tests/hmoe tests/training docs/task/air_combat examples/config/training/active/air_combat -> pass
- event-head 32k train plus deterministic/stochastic probes -> deterministic crossing and one-shot authorized releases; held timing residual
remaining paths:
- Define launch-window / engagement-quality timing contract.
behavior risks:
- The higher event-head LR crosses deterministic argmax and preserves one-shot discipline in short probes, but it can learn immediate release unless label/window semantics distinguish authorization from good launch timing.
integration notes:
- Previous deadline-bootstrap config remains available as the direct A6-EVT-I comparison baseline.
```
