# A5 Implementation Evidence

状态：`2026-06-03`，partial implementation evidence。`A5-EAM-D Runtime State
Machine`、`A5-EAM-E Policy Event Head`、`A5-EAM-F Reward And Config Cleanup`
与 `A5-EAM-G Diagnostics And Evidence` 均返回 `pass`，并经主线程 focused tests
验收。短训 learned-policy evidence 已记录为 held outcome：stochastic release
discipline 已修复，但 deterministic `fire_once` 仍缺失。

父级：[README.zh.md](README.zh.md)。合同：
[event contract](a5_constrained_event_action_model_event_contract_20260603.zh.md)。

## Worker Packets

| Cluster | Worker | Status | Touched files | Accepted scope |
| --- | --- | --- | --- | --- |
| `A5-EAM-D Runtime State Machine` | `Noether`（`019e8d45-a81e-7d10-93b2-3e16095b094e`） | pass | `gym_envs/universal_env_parts/air_combat_event_action.py`、`gym_envs/universal_env.py`、`gym_envs/universal_env_parts/__init__.py`、`tests/runtime/air_combat/test_air_combat_a5_event_action_runtime.py` | 窄 UniversalEnv hybrid C2/ROE event gate：`fire_mask`、`engagement_state`、request/accept/reject fields、post-launch suppression、显式 reattack readiness。 |
| `A5-EAM-E Policy Event Head` | `Hume`（`019e8d45-f5ed-77d2-9316-d54415e142a0`） | pass | `python/rl/policy_algo/policies.py`、`tests/policy/test_execution_policy_surface.py` | `air_combat_hybrid_v1` 的 policy-side masked `hold/fire_once` event semantics：stochastic sampling、deterministic argmax、log-prob 和 entropy 均遵守 fire mask。 |
| `A5-EAM-F Reward And Config Cleanup` | `Noether`（`019e8d45-a81e-7d10-93b2-3e16095b094e`） | pass | `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`、`tests/runtime/air_combat/test_air_combat_reward_surface.py`、`tests/training/test_air_combat_training_entry_contracts.py` | active S1 C2/ROE reward/config 不再把 invalid-fire、pending-assessment、premature-second-shot 或 shot-budget violation penalties 当作主要合法性机制；repeat release 保留为小的 timing/ammo cost。 |
| `A5-EAM-G Diagnostics And Evidence` | `Hume`（`019e8d45-f5ed-77d2-9316-d54415e142a0`） | pass | `tools/diagnostics/air_combat_stage0_process_probe.py`、`python/training_callbacks.py`、`tests/runtime/air_combat/test_diagnostics_probe_contracts.py`、`tests/training/test_diagnostics_callback_contracts.py` | probe rows、episode summaries 和 training callback diagnostics 报告 A5 event state、fire mask、request/accept/reject/reason、release execution、post-launch suppression、rejection/state counts 与 masked event policy probabilities。 |
| main-thread integration | main thread | pass | `train.py`、`tests/policy/test_execution_policy_surface.py` | 将 safe-action-bias initialization 更新到新的 20 参数 hybrid layout。 |

## Accepted Behavior

- runtime info 现在暴露：
  `engagement_state`、`fire_mask`、`event_action_mask`、`fire_mask_components`、
  `fire_once_requested`、`fire_once_accepted`、`fire_once_rejected_reason`、
  `release_executed`、`post_launch_suppressed` 和 `reattack_ready`。
- UniversalEnv hybrid C2/ROE runtime 将既有 `fire_weapon` pulse 解释为
  `fire_once_requested`，并在 `fire_mask=0` 时 suppress。
- 合法首发进入 `FiredAssess`，并禁止 immediate repeat fire，除非存在显式
  `ReattackReady` 条件。
- Hybrid policy output 现在是 20 参数：
  6 个 continuous means、5 个 compatibility binary logits、1 个 fire-event hold logit、
  8 个 weapon-select logits。
- fire event 的 deterministic evaluation 使用 masked hold/fire argmax，而不是 raw
  `fire_logit >= 0`。
- 非 event binary heads 继续保持 Bernoulli 语义。
- active S1 C2/ROE reward/config 保留 positive first-release 和 authorized weapon-chain
  shaping，但将 legality-enforcement penalties 置零，使合法性由 A5 mask/state-machine
  support 处理，而不是由 reward 处理。
- diagnostics 现在暴露 masked `policy_event_prob_fire_once`、`policy_event_mode` 与
  `policy_event_mask_fire_once`，并仅将旧 `policy_prob_fire_weapon` 作为 compatibility
  field 保留。
- probe summaries 能区分 structural multi-fire、invalid requests、learned hold/fire
  behavior、post-launch suppression 和 rejection reasons。

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_a5_event_action_runtime.py \
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

Reward/config cleanup validation：

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

Diagnostics implementation validation：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  tests/training/test_diagnostics_callback_contracts.py
# 14 passed in 2.23s
```

`A5-EAM-G` 后 integrated focused validation：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_a5_event_action_runtime.py \
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

- World-batch runtime 尚未接收 runtime-authored `event_action_mask`；当前 policy 在缺少
  explicit mask fields 时，会从 20D C2/ROE mission observation 推导窄 fire mask。
- 既有 A3/A4/M1 checkpoint 使用旧 19 参数 hybrid policy head；在 20 参数 event-action
  layout 变更后，不能直接作为 A5 learned-policy evidence。
- 短训 learned-policy evidence 已记录在
  [a5_constrained_event_action_model_short_learned_probe_20260603.zh.md](a5_constrained_event_action_model_short_learned_probe_20260603.zh.md)。
  deterministic release 仍 held；下一包应针对 event-value / first-event timing，而不是
  reward-only legality tuning。
