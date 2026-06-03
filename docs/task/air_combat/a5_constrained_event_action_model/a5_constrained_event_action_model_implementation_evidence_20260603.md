# A5 Implementation Evidence

Status: `2026-06-03` partial implementation evidence. `A5-EAM-D Runtime State
Machine` and `A5-EAM-E Policy Event Head` returned `pass` and were accepted by
the main thread after focused test validation. A5 as a whole is not accepted
yet; reward/config cleanup, diagnostics, learned evidence, and closure remain
open.

Parent: [README.md](README.md). Contract:
[event contract](a5_constrained_event_action_model_event_contract_20260603.md).

## Worker Packets

| Cluster | Worker | Status | Touched files | Accepted scope |
| --- | --- | --- | --- | --- |
| `A5-EAM-D Runtime State Machine` | `Noether` (`019e8d45-a81e-7d10-93b2-3e16095b094e`) | pass | `gym_envs/universal_env_parts/air_combat_event_action.py`, `gym_envs/universal_env.py`, `gym_envs/universal_env_parts/__init__.py`, `tests/runtime/air_combat/test_air_combat_a5_event_action_runtime.py` | Narrow UniversalEnv hybrid C2/ROE event gate: `fire_mask`, `engagement_state`, request/accept/reject fields, post-launch suppression, explicit reattack readiness. |
| `A5-EAM-E Policy Event Head` | `Hume` (`019e8d45-f5ed-77d2-9316-d54415e142a0`) | pass | `python/rl/policy_algo/policies.py`, `tests/hmoe/test_hmoe_policy.py` | Policy-side masked `hold/fire_once` event semantics for `air_combat_hybrid_v1`: stochastic sampling, deterministic argmax, log-prob, and entropy respect fire mask. |
| main-thread integration | main thread | pass | `train.py`, `tests/hmoe/test_hmoe_policy.py` | Updated safe-action-bias initialization for the new 20-parameter hybrid layout. |

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

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_a5_event_action_runtime.py \
  tests/runtime/core/test_air_combat_hybrid_action.py \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/air_combat/test_weapon_roe_runtime.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/diagnostics/test_air_combat_process_probe.py
# 60 passed, 8 subtests passed in 17.62s
```

## Residuals

- World-batch runtime does not yet receive runtime-authored `event_action_mask`;
  policy currently derives a narrow fire mask from the 20D C2/ROE mission
  observation when explicit mask fields are absent.
- Diagnostics still need an A5 pass to expose masked event probabilities and
  requested/accepted/rejected/suppressed event fields coherently.
- Reward/config cleanup remains open: constraints should be state/mask
  responsibilities, with reward retained for outcome and timing preference.
- Learned-policy evidence has not been rerun after the event-action changes.
