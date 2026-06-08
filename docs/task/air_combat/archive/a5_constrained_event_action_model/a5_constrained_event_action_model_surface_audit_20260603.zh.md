# A5 Surface Audit

状态：`2026-06-03`，pass。当前会话内 subagent `Lagrange`
（`019e8d3a-ae5a-7641-a153-7e3691d27dd2`）返回的只读 worker packet 已由主线程抽样复核并验收。

父级：[README.zh.md](README.zh.md)。

## Worker Packet Summary

```md
status: pass
cluster: A5-EAM-B Surface Audit
model/reasoning: inherited model / xhigh
scope: read-only surface audit
commands/outcomes:
  读取必需 A5/A3/A4/M1 文档，并用 rg/nl 扫描代码。
  未运行测试；这是只读审计。
touched files: none
```

worker 没有编辑文件。主线程在验收前抽样复核了 action、mission observation、
reward runtime 和 policy surface。

## Surface Map

| Surface | Files and symbols | A5 relevance |
| --- | --- | --- |
| Action space | `gym_envs/universal_env_parts/spaces.py`：`AIR_COMBAT_HYBRID_V1_ACTION_MODE`、`AIR_COMBAT_HYBRID_V1_ACTION_DIM`、`make_action_space()` | 当前 accepted S1 action transport 仍是 12D flat `air_combat_hybrid_v1`。 |
| Action adapter | `gym_envs/universal_env_parts/actions.py`：`air_combat_hybrid_effective_action()`、`build_pilot_action()`、`radar_active`、`tms_up`、`master_arm`、`fire_weapon`、`fire_gun`、`weapon_select_id` | 当前 `fire_weapon` 在 adapter 层是 rising-edge pulse，但 policy-facing 语义仍是 binary threshold/logit。 |
| Single/world-batch runtime | `gym_envs/universal_env.py`、`python/rl/runtime/world_batch_vec_env.py` | 这些路径在 `PilotAction` 前应用 hybrid rising-edge 语义；A5 event support 必须和两者对齐。 |
| C++ release latch | `src/systems/combat/pilot_weapon_release_system.h`、`src/core/engine/simulation_kernel_weapon_release_service.cpp` | 现有 release latch 能防 held-trigger success repeat，但 low-high-low 仍可再次尝试；A5 不能把它当作 event contract。 |
| Mission observation taxonomy | `python/mission_obs_taxonomy.py`：`MISSION_OBS_AIR_COMBAT_C2_ROE_V1`、`authorization_to_fire`、`shot_policy_state`、`shot_budget_remaining`、`pending_assessment`、`own_missiles_in_flight_count` | 现有 20D C2/ROE vector 已携带核心 mask components 和 post-launch state hints。 |
| Mission observation builder | `gym_envs/scenario_loader/mission_observation.py`：`_air_combat_c2_roe_vector()` | 会根据 observed release 动态递减 `shot_budget_remaining`，并设置 `pending_assessment` / `own_missiles_in_flight_count`。 |
| HMoE routing | `python/rl/policy_algo/hmoe_routing.py` | 将 20D C2/ROE obs route 到 `combat_weapons` subexperts；routing 不是 action support。 |
| Reward/runtime release classification | `gym_envs/scenario_loader/reward_runtime/air_combat.py`：`air_combat_c2_roe_state_from_mapping()`、`classify_air_combat_c2_roe_event()`、`_c2_roe_authorized_action_window()`、`_apply_c2_roe_release_discipline()` | buckets 适合诊断，但 A5 合法性必须转为 mask/state-machine support，而不是 penalty learning。 |
| Policy distribution | `python/rl/policy_algo/policies.py`：`_HybridActionLayout`、`_HybridActionDistribution`、`HierarchicalMoEExecutionPolicy` | Hybrid params 当前是 continuous + Bernoulli + categorical；deterministic binary action 使用 `logit >= 0`。A5 event mask 应接入这里，而不只在 runtime。 |
| Diagnostics | `tools/diagnostics/air_combat_stage0_process_probe.py`、`python/training_callbacks.py` | 后续扩展为报告 event state、mask、request/accept/reject、suppression 和 policy event probabilities。 |
| Active configs/tests | `examples/config/training/active/air_combat/*c2_roe*_probe_v1.json`；`tests/runtime`、`tests/hmoe`、`tests/training`、`tests/diagnostics` | 首版实现应只瞄准 active S1 C2/ROE shaped configs。 |

## Implementation Risks

- 现有 adapter/runtime latch 解决 held-trigger repeat，不解决 C2/ROE event legality。
  low-high-low command 仍可再次尝试。
- `authorized_first_shot` 等 HMoE route label 不是 action support。如果把 route selection
  当合同，binary `fire_weapon` 仍没有改变。
- mission observation field order 在 routing 和 tests 中硬编码。新增字段需要同步 taxonomy、
  observation、batching、routing 和 tests。
- 如果 `WorldBatchVecEnv` 之外的 runtime paths 进入 A5 training/eval route，仍需要 follow-up。

## Contract Recommendations

A5-EAM-C 应冻结这些名称：

- `engagement_state`
- `fire_mask`
- `event_action = {hold, fire_once}`
- `fire_once_requested`
- `fire_once_accepted`
- `fire_once_rejected_reason`
- `release_executed`
- `post_launch_suppressed`
- `reattack_ready`

推荐 `engagement_state` values：

- `Hold`
- `AuthorizedReady`
- `FiredAssess`
- `ReattackReady`
- `Winchester`

冻结 mask components，而不是只有 final bit：

- C2 authorization
- target present
- shot budget
- pending assessment
- weapon/ammo readiness
- reattack permission

## Acceptance Result

`A5-EAM-B Surface Audit` 验收为 `pass`。它解锁 A5-EAM-C event contract draft。
在 contract names 冻结前，不授权 runtime 或 policy implementation。
