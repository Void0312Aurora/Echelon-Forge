# Common / Air / Naval 模块拆分冻结计划

状态：`2026-05-15` 冻结执行版；`WP0 / WP1 / WP2 / WP3` 已完成，`WP4` 已完成第一阶段 shared base / air adapter / dispatch seam 与第二阶段 profile 回接 / compatibility 落地并通过聚焦验收，`WP5` 已完成，`WP6` 已完成，`WP7` 已启动并完成前两批骨架 / contract / public DTO-binding-roundtrip 落地，`WP8` 已完成 `MissionCommand common + air` 兼容拆分、consumer/json 对称性收尾与聚焦回归验收。
文档定位：

- 本文档冻结一次围绕 `common / air / naval` 的模块拆分计划。
- 本轮目标是先稳固边界、兼容层和验证面，不直接引入完整海战运行时。
- 本文档不授权超出工作包范围的语义重写；所有实现应按工作包逐项验收。

验证口径：涉及 Python / nanobind / runtime 的实现时，默认使用仓库虚拟环境与本地构建产物进行验收，即：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest
```

不要用系统 Python 作为最终验收口径。

## 一、目标

本计划的目标不是“立刻做出海战训练主线”，而是为后续空战与海战并行开发建立可合并的结构基础。

本轮要解决的核心问题：

1. 把 `joint/common core` 与 `air specialization` 从当前混合 DTO 中剥离出来。
2. 建立 future `naval profile` 的落点，但不强行在本轮实现完整 naval runtime。
3. 把 `tasking/command -> Python runtime -> contracts/tests` 这条链的兼容拆分路线冻结下来。
4. 避免继续在当前 `air-first` 结构中通过 `if Navy` 叠加新语义。

## 二、当前判断

根据配套分析文档 [Common / Air / Naval 模块拆分分析](/home/void0312/Workshop/CMO/docs/task/common_air_naval/common_air_naval_modular_split_analysis_20260515.zh.md)，当前仓库已具备以下条件：

- 标准文档层已经能支撑 `joint/common core + service profile + specialization` 的建模路线；
- `ServiceProfile::Navy` 与 `UnitType::Ship` 等入口已存在；
- DTO、Python helper、contract runner、tests 和工具层仍然明显偏 `air-first`；
- `TaskOrder / LeaderIntent / PilotReport` 适合作为首批结构拆分对象；
- `MissionCommand` 属于高风险 tight-loop 结构，应后置处理。

## 三、非目标

本轮不做：

- 重写空气动力或控制律。
- 直接引入完整 naval mission runtime。
- 批量修改所有 scenario / training config 为多军种格式。
- 一次性废弃旧 struct 名、旧头文件名或旧 Python 绑定导出名。
- 把 `MissionCommand` 改造成全新嵌套对象并同时改写所有下游 consumer。
- 重写现有 cooperative takeoff / cruise / landing 主线行为。

本轮允许：

- 新增 `common/air/naval` 目标目录与 README。
- 新增 compatibility umbrella headers。
- 新增 Python dispatch/helper 模块。
- 对 `tests/contracts` 做结构性拆分。
- 对 `docs/standards`、`docs/task` 和必要的 `README` 做边界回填。

## 四、总体策略

### 4.1 拆分顺序

采用以下顺序：

1. 文档与 schema 边界冻结
2. C++ common enum / DTO core 抽取
3. `TaskOrder / LeaderIntent / PilotReport` 的 air 拆分
4. Python profile / loader / env dispatch 拆分
5. `tests/contracts` 迁移
6. `tests/runtime`、`tools/eval`、`tools/diagnostics`、scenarios/configs 迁移
7. `naval` profile 骨架与最小 contract 落地
8. `MissionCommand` 延后重构

### 4.2 兼容策略

首批阶段默认保留：

- 旧头文件路径
- 旧 struct 名
- 旧 Python 绑定导出名
- 旧 scenario / contract 的兼容解释层

兼容策略的目的不是长期维持双轨，而是降低每一阶段的合并风险。

### 4.3 目录策略

目标结构采用三层：

```text
common
air
naval
```

不采用：

```text
air
ship
```

原因：

- `tasking/command` 层描述的是军种/任务组织语义，而不是单个平台物理模型；
- `ship` 更适合平台/执行层语义；
- `naval` 才是与 `air` 对齐的任务/控制 profile 层。

## 五、冻结工作包

### WP0：文档与字段归属冻结

目标：

- 先把 `common / air / naval` 边界写清楚；
- 明确哪些字段和枚举必须归属 `common`，哪些必须归属 `air`；
- 明确 `naval` 本轮只建立骨架，不直接承诺完整 runtime。

冻结范围：

- `docs/task` 本主题分析/计划文档
- `docs/standards/joint/*`
- `docs/standards/services/*`
- `docs/standards/document_alignment_map.md`
- 必要的 `src/components/*/README.md`

明确不做：

- 任何行为性代码迁移
- 任何 runtime 语义变更

交付物：

- 分析文档
- 冻结计划文档
- 字段/枚举归属表

验收标准：

- `common` 与 `air` 字段归属明确
- `naval` 本轮边界明确
- 后续代码实现无需重新争论字段归属

当前状态：

- 已完成：`docs/task` 分析与计划文档落地
- 已完成：`docs/standards/document_alignment_map.md`、`docs/standards/joint/command_and_modeling_baseline.md`、`docs/standards/services/navy.md`、`docs/standards/naval/README.md` 边界回填
- 已完成：`src/components/tasking/README.md` 与 `src/components/command/README.md` 的目录边界说明

### WP1：抽取 common enum 与中性通信层

目标：

- 把真正的联合层共通枚举从 `tasking_enums.h` 中剥离；
- 将 `CommMsgType` 从 `pilot_report.h` 中迁到中性通信层。

冻结范围：

- `ServiceProfile`
- `TaskFamily`
- `TacticalUnitType`
- `CommandRelationship`
- `AuthorityScope`
- `AssigneeKind`
- `CoordinationMode`
- `CommMsgType`

建议目标结构：

```text
src/components/tasking/common/core_tasking_enums.h
src/components/command/common/comm_message.h
```

兼容要求：

- 保留 `src/components/tasking/tasking_enums.h`
- 保留 `src/components/tasking/pilot_report.h` 对旧 include 的兼容

明确不做：

- 在本阶段迁移 `TaskOrder` / `LeaderIntent` / `MissionCommand` 的全部字段

验收标准：

- C++ 构建通过
- `ef_py` 绑定构建通过
- 旧 include path 仍可工作
- 不改变现有 runtime 行为

风险备注：

- 需要同步 `bindings_command.cpp`
- 需要注意 `legacy_command.h`、datalink、track manager 对 `CommMsgType` 的依赖

当前状态：

- 已完成：`src/components/tasking/common/core_tasking_enums.h` 抽取共通枚举
- 已完成：`src/components/command/common/comm_message.h` 承载中性 `CommMsgType`
- 已完成：兼容 include 仍由 `tasking_enums.h`、`pilot_report.h`、`comm.h` 对外保持
- 已完成：`ef_core` / `ef_py` 构建与 focused pytest 验证

### WP2：抽取 `TaskOrder / LeaderIntent / PilotReport` 的 common core

目标：

- 在不破坏 public struct 名称和大部分下游调用方式的前提下，建立 common/air 的文件边界；
- 为后续 `naval` 扩展预留干净落点。

冻结范围：

- [src/components/tasking/task_order.h](/home/void0312/Workshop/CMO/src/components/tasking/task_order.h)
- [src/components/tasking/leader_intent.h](/home/void0312/Workshop/CMO/src/components/tasking/leader_intent.h)
- [src/components/tasking/pilot_report.h](/home/void0312/Workshop/CMO/src/components/tasking/pilot_report.h)

建议目标结构：

```text
src/components/tasking/common/
  task_order_core.h
  leader_intent_core.h
  pilot_report_core.h

src/components/tasking/air/
  task_order_air.h
  leader_intent_air.h
  pilot_report_air.h
```

兼容策略：

1. 先建立目标文件与 umbrella include。
2. 保持 `TaskOrder`、`LeaderIntent`、`PilotReport` 名称不变。
3. 保持 flat DTO 对下游的兼容期。

明确不做：

- 立刻把 struct 改成深层嵌套对象
- 同步改写所有 Python consumer

验收标准：

- `SimulationKernel` / `WorldBatchRuntime` / `RuntimeFacade` 构建通过
- `bindings_command.cpp` 导出保持兼容
- `tests/leader/test_common_core_semantics.py`
- `tests/world_batch/test_world_batch_runtime.py`
  的相关字段 smoke 通过

风险备注：

- `runtime facade`、`world_batch_contracts` 会直接暴露这些 DTO
- 旧字段迁移时必须控制 include 依赖方向

当前状态：

- 已完成：`TaskOrder`、`LeaderIntent`、`PilotReport` 拆分为 `common/*_core.h` 与 `air/*_air.h`
- 已完成：旧 umbrella header 继续对外暴露原 struct 名，并通过 `Core + Air` 兼容壳保持 flat 字段访问
- 已完成：`bindings_command.cpp` 兼容导出验证
- 已完成：`tests/leader/test_common_core_semantics.py`、`tests/runtime/test_runtime_facade.py` 与 `tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` 聚焦验收

### WP3：抽取 air-only enum 与 air extension

目标：

- 把空战专有任务族、phase、回收、起飞、跑道、编队字段从 common 结构中明确下沉到 `air`。

冻结范围：

- `TaskType`
- `StationType`
- `LeaderPhase`
- `RecoveryApproachType`
- `TakeoffProcedureType`
- `TakeoffClearanceState`
- `RunwaySlotPosition`
- `FormationRole`
- `WingmanSlot`
- `FormationMode`
- `WingmanCommandMode`

以及以下 air-only 字段的归属明确化：

- `recovery_runway_id`
- `recovery_base_id`
- `takeoff_*`
- `runway_slot_id`
- `lead_aircraft_id`
- `formation_*`
- `wingman_*`
- `support_sector_id`

明确不做：

- 新增 naval 对等实现
- 改变 cooperative air 主线行为

验收标准：

- `tasking_enums.h` 退化为 umbrella / compatibility header
- 新增 `air_tasking_enums.h`
- 现有空战 runtime 行为保持不变

风险备注：

- `tests/runtime` 中大量 formation / takeoff / landing 测试依赖这些枚举

当前状态：

- 已完成：新增 `src/components/tasking/air/air_tasking_enums.h` 作为 air-only enum owner
- 已完成：`tasking_enums.h` 退化为 `common + air` compatibility umbrella
- 已完成：`task_order_air.h`、`leader_intent_air.h`、`mission_command.h` 与 `bindings_command.cpp` 改为显式依赖 air enum owner
- 已完成：`ef_core` / `ef_py` 构建通过，且 `tests/leader/test_common_core_semantics.py`、`tests/leader/test_two_ship_contract_fields.py`、`tests/runtime/test_runtime_facade.py`、`tests/runtime/test_mission_runtime.py`、`tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` 聚焦验收通过

### WP4：Python profile/dispatch 拆分

目标：

- 让 Python 侧从“伪 common、实 air-first”过渡到显式 dispatch。

冻结范围：

- `python/rl/common_core_profile.py`
- `python/rl/leader_tasking.py`
- `gym_envs/scenario_loader.py`
- `gym_envs/leader_env.py`
- `python/rl/multi_agent_runtime.py`
- `python/testing/scenario_contract_runner.py`

建议目标结构：

```text
python/rl/profile/common_core_base.py
python/rl/profile/air_profile.py
python/rl/tasking_bridge.py
python/rl/tasking_air_adapter.py
gym_envs/tasking_runtime_dispatch.py
gym_envs/leader_semantics_adapter.py
```

阶段内拆分策略：

1. 先抽 enum/default/plumbing 的 shared base。
2. 再抽 air profile helper。
3. 再为 loader / env 引入 dispatch seam。
4. 暂不引入完整 naval adapter，只保留接口。

明确不做：

- 立刻修改 mission observation 向量结构
- 立刻让现有 checkpoint 转成新语义

验收标准：

- `common_core_profile` 的 shared / air 逻辑分离
- `leader_tasking` 中 shared bridge 与 air adapter 分离
- `scenario_loader` / `leader_env` 能通过 adapter/dispatch 使用 air profile
- 现有 air scenarios smoke 不退化

风险备注：

- mission observation 维度和 command code 兼容最敏感
- 旧 checkpoint / eval 工具链依赖现有 air-first 解释

当前状态：

- 已完成：新增 `python/rl/profile/common_core_base.py`，承载 shared enum/default/plumbing helper
- 已完成：新增 `python/rl/profile/common_core_defaults.py`，承载 shared common-core default/inference helper
- 已完成：新增 `python/rl/profile/air_profile.py`，承载 air task-family/task-type、route/recovery 与 kernel mission-command helper
- 已完成：新增 `python/rl/tasking_air_adapter.py` 与 `python/rl/tasking_bridge.py`，建立默认 air adapter 与 profile dispatch seam
- 已完成：`gym_envs/scenario_loader.py`、`gym_envs/leader_env.py`、`python/testing/scenario_contract_runner.py` 改为经由 dispatch 使用默认 air profile
- 已完成：`python/rl/common_core_profile.py` 的 air 语义与 shared default/inference 改为经由 `profile` 子模块承载，同时保留旧导出面作为 compatibility shell
- 已完成：`python/rl/leader_tasking.py` 的 `infer_route_ref_id`、`infer_recovery_*`、`build_kernel_mission_command` 改为经由 `air_profile` 承载，同时保持旧入口与 `ef_py` patch 兼容
- 已完成：`python/rl/tasking_air_adapter.py` 明确汇聚 `common_core_profile` 的 common-core defaults/spec 与 `air_profile` 的 air semantics
- 已完成：`./.venv/bin/python -m py_compile` 覆盖 `common_core_profile.py`、`leader_tasking.py`、`tasking_air_adapter.py`、`tasking_bridge.py` 与 `python/rl/profile/*`
- 已完成：`tests/leader/test_common_core_semantics.py`、`tests/leader/test_task_order_randomization.py`、`tests/leader/test_two_ship_contract_fields.py`、`tests/runtime/test_leader_tasking_runtime.py`、`tests/runtime/test_runtime_facade.py`、`tests/runtime/test_mission_runtime.py` 与 `tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` 聚焦验收通过（`53 passed` + `1 passed`）
- 未完成：`RuleBasedLeaderPhaseManager` / `ScriptedC2TaskManager` 与 `_apply_task_order_overrides` 的进一步物理迁移；`multi_agent_runtime.py` 与更广泛 contract/runtime 入口的 dispatch 化

### WP5：`tests/contracts` 迁移为 common-first

目标：

- 把 `tests/contracts` 变成首个真正按 `common / air / future naval` 组织的可执行验证面。

冻结范围：

- `python/testing/scenario_contract_runner.py`
- `tests/contracts/unit/comm/*`
- `tests/contracts/chain/*`

建议方向：

- `common core` 契约只验证：
  - `service_profile`
  - `task_family`
  - `tactical_unit_type`
  - `command_relationship`
  - `authority_scope`
  - `task_group_id`
  - `supported/supporting`
  - `role_code`
  - `coordination_mode`
  - `recovery_site_id`
- air-specific 契约继续保留在 `air` 语义集合中

明确不做：

- 在本阶段迁移所有 runtime tests

验收标准：

- `scenario_contract_runner` 支持 common-core 契约与 air 契约分流
- `tests/contracts/unit/comm/*` 中存在不依赖 runway/takeoff/formation 的 common-core 基线
- 现有 air contracts 继续通过

当前状态：

- 已完成：`python/testing/scenario_contract_runner.py` 为 `task_order_and_mission_link` 内部引入 common-core / air-specific 断言分层，旧 `check_kind` 与旧 spec 路径继续保持兼容
- 已完成：`python/testing/scenario_contract_runner.py` 新增 `task_order_common_core` 与 `scenario_loader_common_core_semantics` 两个 common-first unit contract 入口
- 已完成：`scenario_loader_mission_semantics` 支持 `expected_task_order_common_core`、`expected_task_order_air` 与 `expected_post_transition_air` 分流写法，同时继续兼容旧 `expected_task_order` / `expected_post_transition`
- 已完成：新增 `tests/contracts/unit/comm/task_order_common_core_defaults.json`，提供不依赖 runway/takeoff/formation 的 common-core 默认传播基线
- 已完成：新增 `tests/contracts/unit/comm/scenario_loader_common_core_semantics.json`，提供 scenario loader common-core 归一化基线
- 已完成：`tests/runners/test_contract_batches.py --group same_process` 纳入两份 common-first contract，并继续覆盖旧 `task_order_and_mission_link.json` 与 `scenario_loader_mission_semantics.json`
- 已完成：`./.venv/bin/python -m py_compile python/testing/scenario_contract_runner.py tests/runners/test_contract_batches.py`
- 已完成：`tests/runners/test_contract_batches.py --group same_process` 聚焦验收通过（4 contracts passed）
- 已完成：`tests/leader/test_common_core_semantics.py` 与 `tests/leader/test_two_ship_contract_fields.py` 聚焦回归通过（9 passed）
- 未完成：`tests/contracts/unit/comm/` 下 air-only contract 的物理迁移与 `unit/air` / `unit/naval` 目录族建立；更广泛 unit/runtime 合同仍待继续 common-first 化

### WP6：`tests/runtime`、`tools/eval`、`tools/diagnostics` 适配

目标：

- 在 common/air 拆分稳定后，再让 runtime tests 与工具层跟着结构化。

冻结范围：

- `tests/runtime/*`
- `tools/eval/*`
- `tools/diagnostics/*`

阶段策略：

- 先适配共享 CLI / common helper
- 再适配 air-specific taxonomy
- 本阶段不要求新增 naval eval/diagnostic 主线

明确不做：

- 立刻增加海战任务评测族
- 批量重写 cooperative diagnostics 图表语义

验收标准：

- `eval_task.py` / `eval_sb3.py` 仍能跑 air 主线
- `diagnostics` 共享底座保持不回退
- runtime tests 对 common/air 拆分后的字段路径适配完成

当前状态：

- 已完成：新增 [python/mission_obs_taxonomy.py](/home/void0312/Workshop/CMO/python/mission_obs_taxonomy.py)，统一 mission observation mode 的名称、`mode_code`、维度与字段名 taxonomy
- 已完成：[python/env_config.py](/home/void0312/Workshop/CMO/python/env_config.py)、[gym_envs/universal_env.py](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)、[gym_envs/scenario_loader/core.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)、[tools/eval/sb3_eval_base.py](/home/void0312/Workshop/CMO/tools/eval/sb3_eval_base.py)、[tools/diagnostics/analyze_cooperative_observation_scales.py](/home/void0312/Workshop/CMO/tools/diagnostics/analyze_cooperative_observation_scales.py) 接入共享 taxonomy，同时保留原有 CLI cooperative gating 与 runtime 行为
- 已完成：新增 [tests/runtime/test_mission_obs_taxonomy.py](/home/void0312/Workshop/CMO/tests/runtime/test_mission_obs_taxonomy.py)，锁定 shared taxonomy 与 runtime 入口之间的 `mode_code` / dim / field layout 一致性
- 已完成：`mission_obs_taxonomy` 新增字段名到索引的 shared helper，且 [tests/runtime/test_mission_runtime.py](/home/void0312/Workshop/CMO/tests/runtime/test_mission_runtime.py)、[tests/runtime/test_cooperative_world_batch_vec_env.py](/home/void0312/Workshop/CMO/tests/runtime/test_cooperative_world_batch_vec_env.py)、[tests/runtime/test_multi_agent_runtime.py](/home/void0312/Workshop/CMO/tests/runtime/test_multi_agent_runtime.py) 的核心 mission 断言已从 magic index 收敛到 shared taxonomy
- 已完成：`./.venv/bin/python -m py_compile` 覆盖 WP6 新增与改动文件
- 已完成：`tests/runtime/test_mission_obs_taxonomy.py`、`tests/runtime/test_mission_runtime.py`、`tests/runtime/test_multi_agent_runtime.py`、`tests/runtime/test_multi_agent_benchmark.py` 聚焦回归通过（`34 passed`）
- 已完成：`tests/runtime/test_cooperative_world_batch_vec_env.py`、`tests/runtime/test_scenario_loader_execution_step_runtime.py`、`tests/runtime/test_execution_episode_batch_prepare.py`、`tests/runtime/test_execution_episode_controller.py` 扩展回归通过（`37 passed, 8 subtests passed`）
- 已完成：第二段第一批回归中，`tests/runtime/test_mission_obs_taxonomy.py`、`tests/runtime/test_mission_runtime.py`、`tests/runtime/test_multi_agent_runtime.py`、`tests/runtime/test_cooperative_world_batch_vec_env.py` 通过（`51 passed`）
- 已完成：第二段关联回归中，`tests/runtime/test_scenario_loader_execution_step_runtime.py`、`tests/runtime/test_execution_episode_batch_prepare.py`、`tests/runtime/test_execution_episode_controller.py`、`tests/runtime/test_multi_agent_benchmark.py` 通过（`20 passed, 8 subtests passed`）
- 已完成：`tests/contracts/unit/config/env_config_resolution.json` 合同直跑通过
- 已完成：`python/rl/multi_agent_benchmark.py`、`tools/diagnostics/benchmarks/visual_resolution.py` 与 `tools/diagnostics/benchmarks/world_batch_vec_env.py` 的 `mission_obs_mode` CLI 选择集已统一接入 shared taxonomy
- 已完成：WP6 范围内 mission observation taxonomy 的 config / runtime / tests / eval / diagnostics 共享收敛已闭环
- 未完成：若后续进入 `WP7`，仍需为 naval-specific runtime/eval/diagnostics 增加新的 profile-aware 断言与入口，但这已超出 WP6

### WP7：`naval` profile 骨架与最小 contract 落地

目标：

- 在 common/air 边界稳定后，为后续海战并行开发建立真正可落地的 `naval` 模块入口。

冻结范围：

- `docs/standards/services/navy.md`
- `docs/standards/naval/*`（若新增）
- `src/components/tasking/naval/*`
- `tests/contracts/unit/naval/*`（若新增）

本阶段建议只做：

- `naval` 枚举与 DTO 扩展骨架
- minimal naval contract schema
- minimal contract runner dispatch

明确不做：

- 完整舰队/编队 runtime
- 完整 naval leader env
- 完整 naval eval/diagnostic 套件

验收标准：

- `naval` 目录与 README 落地
- 至少一组 profile-specific contract 可执行
- 不影响现有 air 主线

当前状态：

- 已完成：新增 `src/components/tasking/naval/README.md` 与 `naval_tasking_enums.h` / `task_order_naval.h` / `leader_intent_naval.h` / `pilot_report_naval.h` 骨架，作为 future naval DTO 扩展落点
- 已完成：新增 `python/rl/profile/naval_profile.py` 与 `python/rl/tasking/naval_adapter.py`，并让 `python/rl/tasking/bridge.py` 能对 `tasking_profile = naval` / `service_profile = Navy` 做 profile-aware dispatch
- 已完成：`python/rl/tasking/common_core_profile.py` 已具备 naval-aware 的 common-core 默认化路径，可为 `task_order / leader_intent / pilot_report` 保持 `Navy + Escort + Screen + CommandNode` 这类最小 naval 语义
- 已完成：新增 `tests/contracts/unit/naval/task_order_naval_profile_defaults.json` 与 `tests/contracts/unit/naval/scenario_loader_naval_common_core_semantics.json`，两条最小 naval contract 均可执行通过
- 已完成：新增 `tests/leader/test_naval_profile_semantics.py`，并与既有 common-core / runtime 回归共同验收通过
- 已完成：`TaskOrder / LeaderIntent / PilotReport` 已正式接入 `TaskOrderNaval / LeaderIntentNaval / PilotReportNaval`，不再只是独立骨架头文件
- 已完成：`bindings_command.cpp` 已导出 `NavalWarfareRole` / `NavalStationType`，并暴露 `warfare_role_code` / `officer_in_tactical_command` / `naval_station_type` 等 naval 字段
- 已完成：`gym_envs/leader_env.py` clone 白名单、`tests/leader/test_naval_contract_fields.py`、`tests/world_batch/test_world_batch_runtime.py` 已补齐 naval 字段的 binding / clone / roundtrip 验证
- 未完成：完整 naval leader/runtime/eval/diagnostics 仍未开始，后续应在此骨架之上逐步扩展

### WP8：`MissionCommand` 延后重构

目标：

- 在 common/air/naval 结构层和 Python dispatch 稳定之后，再处理 `MissionCommand` 的 common/air 分层。

冻结范围：

- `src/components/command/mission_command.h`
- `src/models/air/default_control_model.cpp`
- `src/core/mission/episode/detail/*`
- `src/systems/physics/instrument_system.h`
- `bindings_command.cpp`

建议方向：

- `mission_command_core.h`
- `mission_command_air.h`
- 兼容 `mission_command.h`

明确不做：

- 在本阶段同时引入完整 naval execution command

验收标准：

- `MissionCommand` 的 common / air 边界清晰
- 现有 air control / episode / instrument 语义不退化
- codec / equality / facade export 兼容期明确

风险备注：

- 本阶段是全链路最高风险阶段
- 必须在前序工作包都稳定后再进入

当前状态：

- 已完成：新增 `src/components/command/common/mission_command_core.h`，承载 `cmd_heading_deg`、`cmd_altitude_m`、`cmd_speed_mps`、`command_code`、`route_ref_id`、`assigned_target_id`、`authorization_to_fire`、`active` 等 common 字段
- 已完成：新增 `src/components/command/air/mission_command_air.h`，承载 recovery / takeoff / formation offset 等 air-only 字段
- 已完成：`src/components/command/mission_command.h` 改为兼容 umbrella header，继续对外暴露 flat `MissionCommand` 名称与字段访问
- 已完成：`bindings_command.cpp` 无需改动导出名即可继续暴露既有 `MissionCommand` flat 字段，Python 侧保持兼容
- 已完成：新增 `tests/runtime/test_mission_command_split_semantics.py`，覆盖 binding 字段暴露与 direct-kernel roundtrip
- 已完成：`gym_envs/scenario_loader/runtime_state.py`、`src/core/mission/episode/detail/mission_command_codec.cpp`、`src/core/mission/episode/detail/episode_transition_runtime.cpp` 已补齐 `MissionCommand` 的 consumer/json 对称性，`formation_*`、`assigned_target_id`、`authorization_to_fire`、`recovery_approach_type` 等 common/air 字段在 episode/runtime-state roundtrip 中保持保真
- 已完成：`python/rl/profile/air_profile.py` 已修正零值 `leader_intent` 对 mission-level `MissionCommand` 字段的意外覆盖，保持 loader mission command 与 kernel command 构建一致
- 已完成：`tests/runtime/test_leader_tasking_runtime.py`、`tests/world_batch/test_world_batch_runtime.py`、`tests/runtime/test_execution_episode_state.py`、`tests/runtime/test_execution_episode_controller.py`、`tests/runtime/test_runtime_facade.py`、`tests/runtime/test_mission_runtime.py`、`tests/runtime/test_cooperative_world_batch_vec_env.py`、`tests/world_batch/test_world_batch_vec_env.py` 聚焦回归通过
- 未完成：`MissionCommand` 尚未进入 `naval` execution command 分层；当前阶段仅冻结 `common + air` 结构与兼容层

## 六、阶段依赖关系

依赖顺序：

```text
WP0
 -> WP1
 -> WP2
 -> WP3
 -> WP4
 -> WP5
 -> WP6
 -> WP7
 -> WP8
```

说明：

- `WP2` 与 `WP3` 可以部分交错，但必须先完成字段归属冻结；
- `WP4` 不应早于 `WP2/WP3`，否则 Python dispatch 会失去稳定落点；
- `WP8` 必须最后做。

## 七、统一验收要求

每个代码阶段默认应完成以下一项或多项验证：

- `cmake --build build-workshop --target ef_core ef_py -j2`
- `./.venv/bin/python -m py_compile ...`
- `./.venv/bin/python -m pytest -q tests/contracts ...`
- `./.venv/bin/python -m pytest -q tests/runtime ...`

若某阶段只涉及文档，可跳过代码验证，但必须明确写明“未触及代码”。

## 八、文档约束

本文件是本主题唯一的阶段计划文档。

后续推进要求：

- 优先回填本文件的对应工作包状态
- 若需补充专项调研，可新增辅助文档
- 辅助文档不得再次承担并列阶段计划职责

## 九、当前冻结结论

当前冻结结论如下：

1. 本主题采用 `common + air + naval`，不采用 `air + ship`。
2. `TaskOrder / LeaderIntent / PilotReport` 先拆，`MissionCommand` 后拆。
3. Python 层采用 dispatch / adapter 路线，不继续叠加 `if Navy`。
4. `tests/contracts` 先于 `tests/runtime` 迁移。
5. `naval` 首批只做 schema / contract 骨架，不直接承诺完整 runtime。
