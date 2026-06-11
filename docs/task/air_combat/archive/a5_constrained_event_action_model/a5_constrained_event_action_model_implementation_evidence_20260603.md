# A5 Implementation Evidence

Status: `2026-06-03` partial implementation evidence. `A5-EAM-D Runtime State
Machine`, `A5-EAM-E Policy Event Head`, `A5-EAM-F Reward And Config Cleanup`,
and `A5-EAM-G Diagnostics And Evidence` returned `pass` and were accepted by
the main thread after focused test validation. Short learned-policy evidence is
now recorded as a held outcome: stochastic release discipline is fixed, but
deterministic `fire_once` remains absent.

Parent: [README.md](README.md). Contract:
[event contract](a5_constrained_event_action_model_event_contract_20260603.md).

## Worker Packets

| Cluster | Worker | Status | Touched files | Accepted scope |
| --- | --- | --- | --- | --- |
| `A5-EAM-D Runtime State Machine` | `Noether` (`019e8d45-a81e-7d10-93b2-3e16095b094e`) | pass | `gym_envs/universal_env_parts/air_combat_event_action.py`, `gym_envs/universal_env.py`, `gym_envs/universal_env_parts/__init__.py`, `tests/runtime/air_combat/test_fire_action_release_gate.py` | Narrow UniversalEnv hybrid C2/ROE event gate: `fire_mask`, `engagement_state`, request/accept/reject fields, post-launch suppression, explicit reattack readiness. |
| `A5-EAM-E Policy Event Head` | `Hume` (`019e8d45-f5ed-77d2-9316-d54415e142a0`) | pass | `python/rl/policy_algo/policies.py`, `tests/policy/test_execution_policy_surface.py` | Policy-side masked `hold/fire_once` event semantics for `air_combat_hybrid_v1`: stochastic sampling, deterministic argmax, log-prob, and entropy respect fire mask. |
| `A5-EAM-F Reward And Config Cleanup` | `Noether` (`019e8d45-a81e-7d10-93b2-3e16095b094e`) | pass | `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`, `tests/runtime/air_combat/test_air_combat_reward_surface.py`, `tests/training/test_air_combat_training_entry_contracts.py` | Active S1 C2/ROE reward/config no longer uses invalid-fire, pending-assessment, premature-second-shot, or shot-budget violation penalties as the primary legality mechanism; repeat release remains a small timing/ammo cost. |
| `A5-EAM-G Diagnostics And Evidence` | `Hume` (`019e8d45-f5ed-77d2-9316-d54415e142a0`) | pass | `tools/diagnostics/air_combat_weapon_employment_process_probe.py`, `python/training_callbacks.py`, `tests/runtime/air_combat/test_diagnostics_probe_contracts.py`, `tests/training/test_diagnostics_callback_contracts.py` | Probe rows, episode summaries, and training callback diagnostics report A5 event state, fire mask, request/accept/reject/reason, release execution, post-launch suppression, rejection/state counts, and masked event policy probabilities. |
| main-thread integration | main thread | pass | `train.py`, `tests/policy/test_execution_policy_surface.py` | Updated safe-action-bias initialization for the new 20-parameter hybrid layout. |

## Accepted Behavior

- Runtime info now exposes:
  `engagement_state`, `fire_mask`, `event_action_mask`, `fire_mask_components`,
  `fire_once_requested`, `fire_once_accepted`, `fire_once_rejected_reason`,
  `release_executed`, `post_launch_suppressed`, and `reattack_ready`.
- UniversalEnv hybrid C2/ROE runtime gates an existing `fire_weapon` pulse as
  `fire_once_requested`, suppressing it when `fire_mask=0`.
- A valid first shot enters `FiredAssess` and suppresses immediate repeat fire
  unless explicit `ReattackReady` conditions are present.
- Hybrid policy output is now 20 parameters:
  6 continuous means, 5 compatibility binary logits, 1 fire-event hold logit,
  and 8 weapon-select logits.
- Policy deterministic evaluation for the fire event uses masked hold/fire
  argmax instead of raw `fire_logit >= 0`.
- Non-event binary heads remain Bernoulli-style.
- Active S1 C2/ROE reward/config keeps positive first-release and authorized
  weapon-chain shaping, but sets legality-enforcement penalties to zero so
  legality is handled by A5 mask/state-machine support instead of reward.
- Diagnostics now expose masked `policy_event_prob_fire_once`,
  `policy_event_mode`, and `policy_event_mask_fire_once` while retaining legacy
  `policy_prob_fire_weapon` only as a compatibility field.
- Probe summaries distinguish structural multi-fire, invalid requests,
  learned hold/fire behavior, post-launch suppression, and rejection reasons.

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_fire_action_release_gate.py \
  tests/runtime/core/test_air_combat_hybrid_action.py \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/air_combat/test_weapon_roe_runtime.py \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_diagnostics_callback_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py
# 60 passed, 8 subtests passed in 17.62s
```

Reward/config cleanup validation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/training/test_air_combat_training_entry_contracts.py
# 21 passed, 8 subtests passed in 14.93s

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/policy/test_execution_policy_surface.py
# 28 passed in 3.62s
```

Diagnostics implementation validation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  tests/training/test_diagnostics_callback_contracts.py
# 14 passed in 2.23s
```

Integrated focused validation after `A5-EAM-G`:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_fire_action_release_gate.py \
  tests/runtime/core/test_air_combat_hybrid_action.py \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/air_combat/test_weapon_roe_runtime.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  tests/training/test_diagnostics_callback_contracts.py
# 75 passed, 8 subtests passed in 17.97s
```

## Residuals

- World-batch runtime does not yet receive runtime-authored `event_action_mask`;
  policy currently derives a narrow fire mask from the 20D C2/ROE mission
  observation when explicit mask fields are absent.
- Existing A3/A4/M1 checkpoints use the old 19-parameter hybrid policy head and
  cannot be direct A5 learned-policy evidence after the 20-parameter event-action
  layout change.
- Short learned-policy evidence is recorded in
  [a5_constrained_event_action_model_short_learned_probe_20260603.md](a5_constrained_event_action_model_short_learned_probe_20260603.md).
  Deterministic release remains held; the next package should target
  event-value / first-event timing rather than reward-only legality tuning.
