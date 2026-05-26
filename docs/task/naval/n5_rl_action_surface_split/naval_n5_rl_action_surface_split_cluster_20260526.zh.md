# 海军 N5 RL 动作面拆分簇

状态：`2026-05-26` 已实现第一段海军动作面拆分，并已通过聚焦验收。同一修复线现在包含
`N5-E`，也就是第一段海军观测面拆分。虽然目录名为 `N5`，本簇释放的行为仍保持在已接受的
`N4_pre_fire_bridge` 边界内；它只是通过移除空军动作和空军观测依赖，为后续 N5 工作清障。

簇轮次上限：

- 一轮实现，最多一轮修复。

## 边界决定

以下复用被接受：

- 共享训练启动、PPO 策略类、world-batch runtime、compiled observation backend、奖励管线和 facade-shaped 同步；
- 通过 `python.rl.tasking.bridge` 的 common tasking profile 分发；
- 在架构线仍把 `MissionCommand` 视为聚合兼容点期间，继续使用兼容 `MissionCommand`。

以下复用不再接受为 active naval RL 入口：

- 把空军缩减起飞动作面当作海军任务动作；
- 围绕起飞油门偏置初始化海军训练；
- 让非中性的杆、舵、油门通过舰艇手动接管绕开海军站位命令路径。
- 把空军 formation-role 任务观测当作 active naval 策略输入。

## 任务簇

| Stream | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Parallel / dependency | Round cap | Status |
|--------|-------|-------------------|------|-----------|-----------|------------|--------------|-----------------------|-----------|--------|
| `N5-A Evidence and boundary` | main-thread integration | current main thread | 记录为什么必须把 air `takeoff4` surface 从 naval active RL 中拆出，同时保留共享基础设施复用。 | `docs/task/naval/n5_rl_action_surface_split/**`, naval README index | broad naval doctrine, new scenario, weapon release | `git diff --check -- docs/task/naval` | 文档命名可接受复用、拒绝复用和残留项 | implementation 前串行 | 1 + 1 repair | implemented |
| `N5-B Naval station action mode` | main-thread integration | current main thread | 新增 `naval_station3`：方位增量、半径增量、速度偏置映射到海军站位指令意图。 | `gym_envs/universal_env_parts/**`, `gym_envs/universal_env.py`, `python/rl/runtime/world_batch_vec_env.py`, `python/env_config.py`, `python/training/cli.py`, `train.py`, maintained eval/benchmark CLIs | weapon switches, damage, full helm/autopilot, cooperative promotion | env-config pytest, runtime naval pytest | 零动作保持中性；非零动作改变海军 task/command 意图；pilot action 保持中性 | 依赖 N5-A | 1 + 1 repair | implemented |
| `N5-C Active entry migration` | main-thread integration | current main thread | 将 active N4 naval training config 从 `takeoff4` 迁移到 `naval_station3`。 | `examples/config/training/active/naval/**`, training entry tests | new trained-policy claim, larger curriculum | training-entry pytest, bootstrap `--test_only` gate | active 入口不再使用空军起飞动作面，并保持开火前边界 | 依赖 N5-B | 1 + 1 repair | implemented |
| `N5-D Focused acceptance` | main-thread integration | current main thread | 证明第一段拆分没有重新打开 N4 交战/毁伤语义。 | tests and validation notes in this doc | broad regression suite, formal training claim | focused pytest plus naval contract runner | 聚焦测试通过；残留项保持显式 | N5-B/C 后 | 1 + 1 repair | passed |
| `N5-E Naval observation mode` | main-thread integration | current main thread | 新增 `naval_screen_station_v1`，让 active naval RL 接收站位/接触/ROE/报告字段，而不是空军 formation-role 字段。 | `python/mission_obs_taxonomy.py`, `gym_envs/scenario_loader/mission_observation.py`, `python/rl/runtime/world_batch/**`, active naval configs/docs, mission/naval/training tests | weapon release, damage/kill observation, cooperative packet schema | taxonomy pytest, runtime naval pytest, training-entry pytest | active 入口使用海军模式；world-batch 让 C++ mission batching 留在安全 fallback，并将策略可见 mission vector 替换为海军字段 | N5-D 后、新正式训练前 | 1 + 1 repair | implemented |

本实现轮没有分发 subagent。任务簇仍然是有限且符合治理规则的；未来若分发，应先映射到下方某个残留簇。

## 已实现切片

`naval_station3` 动作向量：

- `0`：站位方位增量，归一化 `[-1, 1]`，映射到 `+/-25 deg`；
- `1`：站位半径增量，归一化 `[-1, 1]`，映射到 `+/-1800 m`；
- `2`：站位速度偏置，归一化 `[-1, 1]`，在任务速度带存在时映射到 `+/-1.25 m/s`。

运行行为：

- `WorldBatchVecEnv` 在 batch world step 前，将海军站位动作应用到 loader-owned naval task/mission intent；
- 维护中的 command-chain 同步随后把更新后的站位指令投射进 runtime；
- 该动作模式发送的低层 `PilotAction` 保持中性：rudder/stick-roll 为 `0.0`，throttle 为 `0.5`，武器触发关闭；
- legacy `takeoff4` 仍可用于聚焦的低层舰艇手动接管诊断，但 active naval training 入口不再使用它。

`naval_screen_station_v1` 任务观测向量：

- 站位/指令：command code、目标航向/速度、站位半径/方位、站位误差、归一化站位误差、屏护距离与距离误差；
- 几何：本舰相对支援舰 x/y、期望相对 x/y；
- 接触/报告：目标接触可见、支援舰轨迹可见、报告链已见；
- 权限/来源：ROE 状态、开火授权、指定目标 id 和来源 id；
- 角色：自身角色、相对槽位、参考相对槽位。

运行行为：

- Active naval 配置现在请求 `mission_obs_mode=naval_screen_station_v1`。
- 该模式在第一段切片中由 Python 侧拥有。World-batch 仍使用 compiled observation backend 计算仪表、接触和 RWR，但给 compiled mission-observation batcher 一个安全的 `basic` fallback，然后把策略可见 mission vector 替换成海军向量。
- 这样可以避免在 packet/ownership 拆分就绪前，把新的 mode code 送进旧 C++ mission-observation surface。

## 验证

本切片验证命令：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/core/test_env_config.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_n4_reward_surface.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
git diff --check -- docs/task/naval examples/config/training/active/naval gym_envs/scenario_loader gym_envs/universal_env.py gym_envs/universal_env_parts python/env_config.py python/mission_obs_taxonomy.py python/training/cli.py python/rl/runtime/world_batch python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py train.py tools/eval tools/diagnostics/benchmarks/world_batch_vec_env.py tests/runtime/core/test_env_config.py tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/naval/test_naval_n4_reward_surface.py tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
```

聚焦结果：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/core/test_env_config.py
# 8 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py
# 3 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_n4_reward_surface.py
# 7 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
# 7 passed, 6 subtests passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS: naval screen threat/ROE pre-fire contract passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/core/test_env_config.py tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/naval/test_naval_n4_reward_surface.py tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
# 25 passed, 6 subtests passed

git diff --check -- docs/task/naval examples/config/training/active/naval gym_envs/scenario_loader gym_envs/universal_env.py gym_envs/universal_env_parts python/env_config.py python/mission_obs_taxonomy.py python/training/cli.py python/rl/runtime/world_batch python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py train.py tools/eval tools/diagnostics/benchmarks/world_batch_vec_env.py tests/runtime/core/test_env_config.py tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/naval/test_naval_n4_reward_surface.py tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
# passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json --output_base /tmp/cmo_naval_n5_smoke --run_name naval_station3_smoke
# completed 512 timesteps with action_mode=naval_station3 and saved final_model

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json --output_base /tmp/cmo_naval_n5e_obs_smoke --run_name naval_screen_station_v1_smoke
# completed 512 timesteps with action_mode=naval_station3, mission_obs_mode=naval_screen_station_v1, and saved final_model
```

## 残留簇

后续 `N5-F` packet 拆分：

- 架构线释放对应 surface 后，用更窄 command/tasking packet 替换兼容 `MissionCommand` 站位指令聚合。

后续 `N5-G` cooperative promotion：

- 在 active naval 入口提升到 cooperative execution 前，处理非 agent 支援舰 roster 计数。

后续 `N5-H` training evidence：

- 只有在动作面和观测面都被接受后再跑正式训练，并把学习行为作为证据汇报，而不是把 config bootstrap 当作策略声明。
