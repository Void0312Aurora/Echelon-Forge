# C2/ROE 代码表面扫描 - 2026-06-02

状态：`2026-06-02` A3 planning code-surface scan。本文只记录当前代码基础与后续切入点；
未声明 A3 已实现，也不改变当前 runtime 行为。

## 总结

当前 C2/ROE 字段已经存在，并能从场景进入 kernel / world-batch / episode codec。
但空战训练路径没有专用 mission observation 可观察面，也没有“单发后等待评估”、
`shot_budget`、`salvo_authorized` 或 `reattack_authorized` 状态机。现有 release gating
可以阻止部分未授权首次发射；一旦授权目标可用，策略再次触发 fire 且冷却结束后仍可复射。

关键结论：

- 多发问题不再主要是“连续高电平每步发射”：`air_combat_hybrid_v1` 已把
  `fire_weapon` 做成 rising-edge pulse，kernel 侧也有成功释放后的 held-trigger
  consumption。
- 仍缺的是命令语义：授权只表达“可向目标开火”，没有表达“只授权一发并等待评估”、
  “授权齐射”或“授权再攻击”。
- 因此 A3 的第一实现切入点应是 policy-visible C2/ROE observation、reward/diagnostic
  分类和 S1 probe，而不是马上改导弹物理、弹药或 sequence-native policy。

## MissionCommand 字段流

| Surface | Current evidence | A3 implication |
| --- | --- | --- |
| 字段定义 | `src/components/command/common/mission_command_core.h` 定义 `roe_state`、`engagement_authority_holder_id`、`engagement_authority_grantor_id`、`assigned_target_id`、`threat_state`、`assigned_target_track_id`、`assigned_target_source_id`、`assigned_target_snapshot_time_s`、`authorization_to_fire`。 | A3 可复用现有字段，并补充 shot policy / assessment 语义。 |
| Python 绑定 | `src/interfaces/python/bindings_command.cpp` 暴露 `ef_py.MissionCommand` 字段。 | Python scenario/diagnostics 可读写现有 ROE 字段。 |
| 场景加载 | `gym_envs/scenario_loader/loading.py` 的 `_resolve_primary_target()` 会把 `assigned_target_name/id` 解析为 runtime `assigned_target_id`。 | A3 场景可继续使用 `assigned_target_name`，但需要显式 ROE/shot 字段。 |
| runtime state | `gym_envs/scenario_loader/runtime_state.py` 将 `assigned_target_id`、`roe_state`、authority ids、track/source/snapshot、`authorization_to_fire` 合入 runtime mission command dict。 | 观测和 reward 可通过 `mission_command_view()` / mission dict 消费这些字段。 |
| episode codec | `src/core/mission/episode/detail/mission_command_codec.cpp` 写入并读回 ROE/授权/目标字段。 | A3 不需要先新建 episode codec 路径。 |
| world-batch contract | `src/runtime/contracts/world_batch_contracts.h` 和 world-batch runtime 合约传播 shared core fields。 | A3 world-batch probe 可沿用现有 mission command 合同。 |

## 当前空战场景与配置缺口

| Surface | Current evidence | Gap |
| --- | --- | --- |
| S1 场景 | `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json` 只设置 `assigned_target_name="Red_Target"` 与 `authorization_to_fire=true`。 | 没有显式 `roe_state`、WCS、target identity、shot policy 或 assessment window。 |
| shaped S1 场景 | `air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json` 有 first-release bonus、repeat-release penalty、invalid-fire penalty。 | 奖励能惩罚重复发射，但无法区分授权齐射、再攻击和违规第二发。 |
| active config | `examples/config/training/active/air_combat/*stage1*probe*.json` 仍使用 `mission_obs_mode=basic`。 | 策略看不到 ROE/授权/目标分配/shot policy。 |
| training-entry test | `tests/training/test_air_combat_active_training_entries.py` 当前断言 Stage-1 mission mode 仍是 `basic`，并检查 release shaping。 | A3 需要新增 C2/ROE config 测试，而不是直接破坏既有 M1 对照入口。 |

## Mission Observation 现状

| Surface | Current evidence | A3 cut-in |
| --- | --- | --- |
| taxonomy | `python/mission_obs_taxonomy.py` 的 `basic` 只有 `command_code`、`target_heading_deg`、`target_altitude_m`、`target_speed_mps`。 | 新增 `MISSION_OBS_AIR_COMBAT_C2_ROE_V1`。 |
| air basic vector | `gym_envs/scenario_loader/mission_observation.py` 对 `basic` 直接返回 4 维 mission vector。 | 增加 Python-owned air vector，避免先改 compiled mission-observation C++。 |
| spaces/observations | `gym_envs/universal_env_parts/spaces.py` 和 `observations.py` 已通过 taxonomy / loader 获取 mission dim/vector。 | taxonomy + loader vector 后，单 env 与 world-batch shape 应自然跟随。 |
| env config | `python/env_config.py` 使用 `VALID_MISSION_OBS_MODES` 校验。 | taxonomy 注册即可进入校验；CLI choice 可能还需同步。 |

首版字段建议：

| Field | Meaning |
| --- | --- |
| `command_code` | 保留当前任务命令码。 |
| `roe_state` / `wcs_state` | hold/tight/free 或现有整数状态。 |
| `authorization_to_fire` | 当前是否显式授权开火。 |
| `engagement_authority_holder_id` | 本机或授权 holder。 |
| `engagement_authority_grantor_id` | 授权来源。 |
| `assigned_target_id` | 当前分配/授权目标。 |
| `assigned_target_source_id` | 目标来源或 controller/source。 |
| `target_identity_state` | unknown/bogey/bandit/hostile/friendly 的简化状态。 |
| `engage_order_state` | none/commit/engage/hold_fire/cease/abort。 |
| `shot_policy_state` | weapons_hold/single_shot_then_assess/salvo_authorized/reattack_authorized。 |
| `shot_budget_remaining` | 当前授权剩余发射数或课程化预算。 |
| `pending_assessment` | 首发后是否处于等待效果/超时/再授权阶段。 |
| `own_missiles_in_flight_count` | 面向同目标的己方在飞弹计数；初版可作为 diagnostic 或 observation candidate。 |

## 海军 ROE 先例

| Surface | Current evidence | A3 reuse |
| --- | --- | --- |
| taxonomy fields | `python/mission_obs_taxonomy.py` 的 `naval_screen_station_v1` 包含 `roe_state`、`authorization_to_fire`、`assigned_target_id`、`assigned_target_source_id`。 | 空战 C2/ROE 可仿照 Python-owned mission obs 模式。 |
| vector builder | `gym_envs/scenario_loader/mission_observation.py` 的 `_naval_screen_station_vector()` 写入 ROE/授权字段。 | 新增 `_air_combat_c2_roe_vector()`。 |
| reward precedent | `gym_envs/scenario_loader/reward_runtime/naval.py` 有 `naval_pre_fire_roe_hold_bonus` 和授权状态相关项。 | 空战 reward 可增加 hold bonus、unauthorized fire penalty、premature second-shot penalty。 |
| tests | `tests/runtime/naval/test_naval_n4_reward_surface.py` 覆盖 obs/reward。 | A3 应增加空战对应 focused tests。 |

## Weapon Release Gating 现状

| Surface | Current behavior | Boundary |
| --- | --- | --- |
| `mission_explicit_release_target_available()` | `src/core/engine/simulation_kernel_weapon_release_service.cpp` 要求 mission active、`authorization_to_fire=true`、`assigned_target_id` 非零、authority holder 匹配且目标在 contact list。 | 可阻止未授权目标；不表达发射次数和 assessment window。 |
| `fire_weapon_from_pilot_action()` | 有显式授权目标时向该目标发射；无显式目标时 `roe_state==0` 或 `roe_state>=3` 会 fallback 到 hostile contact，`roe_state=1/2` 更严格。 | 现有 `roe_state` gating 不是完整 WCS/shot policy。 |
| `fire_missile()` | 直接检查实体、冷却、航迹、包线、弹药，不检查 mission ROE。 | world-batch direct launch path 若用于测试，要避免绕过 ROE 结论。 |
| `PilotWeaponReleaseState` | `src/systems/combat/pilot_weapon_release_system.h` 在一次成功 release 后消费 held trigger。 | 防止持续按住 fire 时无限成功连发；不防止松开/再次 pulse 后复射。 |
| hybrid action | `gym_envs/universal_env_parts/actions.py` 将 hybrid `fire_weapon` 变为 rising-edge pulse。 | M1 动作接口已接受；A3 不应回到“连续阈值”作为主因。 |

## 诊断指标切入点

当前 `tools/diagnostics/air_combat_stage0_process_probe.py` 已记录：

- `can_fire`
- `missiles_remaining`
- `missile_release`
- `policy_action_fire_weapon_on`
- `action_fire_weapon_on`
- `fire_switch_steps`
- `invalid_fire_attempt_rate`
- `release_steps`
- `min_release_interval_steps`

A3 建议新增：

- `roe_state_at_fire`
- `authorization_to_fire_at_fire`
- `assigned_target_id_at_fire`
- `fire_under_hold_count`
- `tight_without_assigned_authorized_target_count`
- `first_authorized_step`
- `first_release_after_authorization_step`
- `release_count_by_authorization_state`
- `repeat_release_before_assessment_count`
- `pending_assessment_after_launch`
- `assessment_window_violation_count`
- `authorized_salvo_release_count`
- `authorized_reattack_release_count`

## 建议实现切入点

| File | Change type | Validation |
| --- | --- | --- |
| `python/mission_obs_taxonomy.py` | 注册 `air_combat_c2_roe_v1` 字段表和 Python-owned mode。 | taxonomy field/dim tests。 |
| `gym_envs/scenario_loader/mission_observation.py` | 增加 `_air_combat_c2_roe_vector()` 并返回 mission command / shot policy 字段。 | air-combat mission obs runtime test。 |
| `python/env_config.py` / `python/training/cli.py` | 如 CLI choices 不从 taxonomy 自动派生，则同步新 mode。 | env-config tests。 |
| `gym_envs/scenario_loader/reward_runtime/air_combat.py` | 增加 C2/ROE violation、hold、first-shot、premature-second-shot、salvo/reattack terms。 | `test_air_combat_reward_surface.py` 或新 focused test。 |
| `tools/diagnostics/air_combat_stage0_process_probe.py` | 增加 C2/ROE 发射纪律指标。 | process-probe JSON/CSV schema test。 |
| `scenarios/air_combat/1v1/*c2_roe*.json` | 新增 S1 C2/ROE 场景，显式 ROE、授权窗口、shot policy。 | runtime fixture + bootstrap tests。 |
| `examples/config/training/active/air_combat/*c2_roe*.json` | 新增 A3 probe configs，保留既有 M1 对照入口。 | `tests/training/test_air_combat_active_training_entries.py`。 |
| `src/core/engine/simulation_kernel_weapon_release_service.cpp` | 后续可选：只有在 observation/reward 证据不足后，再考虑 kernel-level shot-budget gate。 | 扩展 `test_weapon_roe_runtime.py`。 |

## 当前不建议立即修改的面

- 不先修改导弹冷却、弹药数或 Pk/毁伤模型。
- 不把第二发全部静默拦截；否则策略不会学习发射纪律，只会被环境隐藏错误。
- 不直接修改 M2；A3-aware evidence 形成前，sequence-native policy release 继续 held。
- 不把 `roe_state=0/3` legacy fallback 立刻重写为 fail-closed；先通过 A3 probe 和测试定义兼容迁移。
