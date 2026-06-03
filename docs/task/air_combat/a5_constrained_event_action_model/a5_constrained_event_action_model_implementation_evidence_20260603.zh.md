# A5 Implementation Evidence

状态：`2026-06-03`，partial implementation evidence。`A5-EAM-D Runtime State
Machine` 与 `A5-EAM-E Policy Event Head` 均返回 `pass`，并经主线程 focused tests
验收。A5 整体尚未 accepted；reward/config cleanup、diagnostics、learned evidence
和 closure 仍开放。

父级：[README.zh.md](README.zh.md)。合同：
[event contract](a5_constrained_event_action_model_event_contract_20260603.zh.md)。

## Worker Packets

| Cluster | Worker | Status | Touched files | Accepted scope |
| --- | --- | --- | --- | --- |
| `A5-EAM-D Runtime State Machine` | `Noether`（`019e8d45-a81e-7d10-93b2-3e16095b094e`） | pass | `gym_envs/universal_env_parts/air_combat_event_action.py`、`gym_envs/universal_env.py`、`gym_envs/universal_env_parts/__init__.py`、`tests/runtime/air_combat/test_air_combat_a5_event_action_runtime.py` | 窄 UniversalEnv hybrid C2/ROE event gate：`fire_mask`、`engagement_state`、request/accept/reject fields、post-launch suppression、显式 reattack readiness。 |
| `A5-EAM-E Policy Event Head` | `Hume`（`019e8d45-f5ed-77d2-9316-d54415e142a0`） | pass | `python/rl/policy_algo/policies.py`、`tests/hmoe/test_hmoe_policy.py` | `air_combat_hybrid_v1` 的 policy-side masked `hold/fire_once` event semantics：stochastic sampling、deterministic argmax、log-prob 和 entropy 均遵守 fire mask。 |
| main-thread integration | main thread | pass | `train.py`、`tests/hmoe/test_hmoe_policy.py` | 将 safe-action-bias initialization 更新到新的 20 参数 hybrid layout。 |

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

- World-batch runtime 尚未接收 runtime-authored `event_action_mask`；当前 policy 在缺少
  explicit mask fields 时，会从 20D C2/ROE mission observation 推导窄 fire mask。
- diagnostics 仍需要 A5 pass，统一暴露 masked event probabilities 与
  requested/accepted/rejected/suppressed event fields。
- reward/config cleanup 仍开放：约束应由 state/mask 负责，reward 保留 outcome 和 timing
  preference。
- event-action changes 后尚未重跑 learned-policy evidence。
