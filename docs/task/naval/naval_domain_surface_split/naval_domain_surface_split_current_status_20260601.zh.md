# 海军领域执行面拆分当前状态

状态：`2026-06-12` P3/P4 维护刷新；`P1-A/P1-B/P2-A/P3-A/P3-B/P4-A`
已验收；面向 [海军领域执行面拆分](README.zh.md) 的 inventory 快照。

## 已确认实现事实

| 事实 | 证据 | 状态 |
| --- | --- | --- |
| Active naval 条目仍指向 `action_mode=naval_station3` 和 `mission_obs_mode=naval_screen_station_v1`。 | `examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json:37-45`，以及同目录的 hold / recovery 条目；再加上 `python/training/bootstrap.py:212-223` 的入口校验。 | 第一切片已接受 |
| Naval tasking profile 会拒绝非海军动作模式。 | `gym_envs/universal_env_parts/naval_actions.py:28-36`。 | 第一切片已接受 |
| Active naval action 已暴露 `_naval_station3_command_surface`，但 legacy assignment 仍经由中性的 `PilotAction` carrier 传输。 | `gym_envs/universal_env_parts/actions.py`；`gym_envs/universal_env_parts/naval_actions.py`；`tests/runtime/naval/test_naval_station_policy_surface.py`。 | command surface 已接受；carrier 仍是 compatibility adapter |
| `naval_screen_station_v1` 已被正式收束为 maintained Python adapter。 | `python/mission_obs_taxonomy.py`；`gym_envs/scenario_loader/mission_observation.py`；`python/rl/runtime/world_batch/observation_batching.py`；`tests/runtime/mission/test_mission_obs_taxonomy.py`。 | accepted maintained adapter |
| `MissionCommand` 仍是 flat compatibility shell。 | `src/components/command/mission_command.h:11-18`；`src/runtime/contracts/world_batch_contracts.h:549-599`。 | compatibility adapter |
| World-batch 仍暴露 `WorldPilotActionAssignment`。 | `src/runtime/contracts/world_batch_contracts.h:543-547`。 | blocker |
| N4 contracts 仍禁止 weapon / damage proof。 | `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json:1-64` 与 `tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json:1-64`。 | 必须保留的边界 |
| `naval_station3` 已有 `naval_station_command` action family、maintained command-surface diagnostic，以及 compatibility-only `PilotAction` transport adapter。 | `gym_envs/universal_env_parts/naval_actions.py`；`python/rl/runtime/world_batch/adapter.py:341-408`；`tests/runtime/naval/test_naval_station_policy_surface.py`。 | 第二切片已接受；action 侧维护已收紧 |
| Active naval config 已使用 domain-neutral `shaping_backend` alias，并在 env settings 中归一到 canonical `flight_shaping_backend`。 | `python/env_config.py:60-76, 120-125`；`examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json:43`；`tests/runtime/core/test_env_config.py:73-102`。 | 第二切片已接受 |
| Active naval eval 现在输出 `surface_gate`，覆盖 action command surface、legacy transport adapter 与 maintained naval observation adapter。 | `tools/eval/naval_station_policy_eval.py`；`tests/eval/test_evaluation_cli_contracts.py`。 | integration gate 已接受 |

## 剩余依赖清单

这里的“已接受的共享基础设施”指 naval 路径可以复用但不拥有的通用 runtime / reward plumbing。`compatibility adapter` 指仍然保留的 air-shaped 或 flat 兼容表面。`blocker` 指仍然阻止 maintained naval packet 边界成立的残余。

| 面向 | 证据 | 分类 | 当前判断 |
| --- | --- | --- | --- |
| naval 动作路径上的 `PilotAction` carrier | `gym_envs/universal_env_parts/actions.py`；`gym_envs/universal_env_parts/naval_actions.py`；`tests/runtime/naval/test_naval_station_policy_surface.py` | bounded compatibility adapter | Naval station 模式现在把 policy-visible 站位指令真值记录到 `_naval_station3_command_surface`；中性 `PilotAction` 只作为 legacy assignment carrier 保留，直到 `WorldPilotActionAssignment` 被替换或包裹。 |
| `MissionCommand` shell 与 world-batch 投影 | `src/components/command/mission_command.h:11-18`；`src/runtime/contracts/world_batch_contracts.h:563-599` | compatibility adapter | 这个 shell 仍是 `core + air + naval`，而 maintained batch projection 还带着 air recovery / takeoff / formation 子段。 |
| `flight_shaping` runtime 和 backend selector | `python/env_config.py:99-149`；`gym_envs/scenario_loader/core.py:273-283`；`gym_envs/scenario_loader/step_evaluation.py:311-323`；`gym_envs/scenario_loader/execution_runtime/mainline.py:530-578`；`gym_envs/scenario_loader/reward_runtime/shaping_inputs.py:4-60, 174-213`；`src/core/mission/runtime/reward_runtime.cpp:208-471` | 已接受的共享基础设施，`flight_shaping_backend` selector 仍是 compatibility adapter | reward math 本身是共享 runtime。naval 条目仍通过 `flight_shaping_backend` 命名 backend，但 naval profile 会用 `domain_flight_shaping_enabled = not naval_runtime_profile` 把它挡在 naval policy surface 之外。 |
| runway / takeoff / formation 字段 | `src/components/command/air/mission_command_air.h:7-49`；`src/runtime/contracts/world_batch_contracts.h:563-599`；`gym_envs/scenario_loader/mission_observation.py:93-147` | compatibility adapter | 这些仍是 shared shell 上的 air-shaped command / observation 字段，不是 naval policy truth。 |
| gear / ILS / runway math | `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py:4-60, 174-213`；`src/core/mission/runtime/reward_runtime.cpp:262-471` | 已接受的共享基础设施 | 通用安全 / approach 数学仍会使用 gear、runway 和 ILS 术语，但 naval runtime 把它们当作共享支撑数学，而不是 naval-owned 语义。 |
| `naval_screen_station_v1` observation adapter | `python/mission_obs_taxonomy.py`；`gym_envs/scenario_loader/mission_observation.py`；`python/rl/runtime/world_batch/observation_batching.py`；`tests/runtime/naval/test_naval_station_policy_surface.py` | accepted bounded adapter | policy-visible vector 由 `naval_screen_station_v1_maintained_adapter` 生成；compiled batch 输入仍以 `basic` 作为有界 fallback，且不是 policy truth。 |
| `WorldPilotActionAssignment` | `src/runtime/contracts/world_batch_contracts.h:543-547` | blocker | World-batch 仍暴露旧的 policy-action assignment contract，因此 naval-owned policy truth 还没有就位。 |

## 就绪矩阵

| 面向 | 当前等级 | 下一步 |
| --- | --- | --- |
| Action | N4 pre-fire station-order command surface，加 explicit legacy carrier | 继续把 `PilotAction` carrier 从更广的 maintained path 中退休，或保持测试约束为 compatibility-only |
| Command | 带 naval owner slice 的 shared shell | 增加 projection guard，并收窄 command / action packet 边界 |
| Observation | bounded maintained naval adapter | 后续可选提升为 C++ packet；保持 adapter diagnostic 测试 |
| Config | active naval config 使用 naval modes 与 `shaping_backend` alias | 保持 legacy `flight_shaping_backend` 兼容，并避免中性 alias 破坏 CLI / canonical override 优先级 |
| Eval | zero-action / offstation N4 gates | 在迁移到新 surface 时保持这些 gate |
| Runtime math | 共享的 `flight_shaping` terms | 保持通用数学共享，但不要把它重命名成 naval-owned 行为 |

## 残余风险

- 如果移除 `_naval_station3_command_surface` 检查，中性的 `PilotAction` carrier 会再次掩盖真实的 naval action-transport 缺口。
- 如果继续把 `MissionCommand` 当作主要聚合点，N5 fire-control 工作很容易继承 air recovery、takeoff、formation 和 altitude 假设。
- maintained Python observation adapter 已有边界和测试；如果后续 batch/device ownership 需要，仍可替换为 C++ packet。
- 如果在没有 compatibility alias 的情况下重命名配置，会破坏 air 和现有训练条目；拆分必须先保持增量兼容。
- `flight_shaping` 本身是共享 runtime，但 air-labeled selector 仍然应该从 naval-facing surface 上退场。

## 下一步

`P3-A` 与 `P4-A` 已作为 bounded observation adapter 和 active/eval integration gate
验收。下一步是 `P2-B` command projection；如果它会触及 `src/runtime/contracts/**`，
仍保持串行分发。
