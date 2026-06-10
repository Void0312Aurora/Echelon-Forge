<!-- Machine-translated draft generated on 2026-05-18 from docs/task/common_air_naval/common_air_naval_modular_split_plan_20260515.md. Review before treating this file as authoritative. -->

<!-- 机器翻译草稿生成于2026-05-18，来自 docs/task/common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md。在以该文件为权威来源之前请进行审阅。 -->

# 通用 / 空中 / 海军模块拆分冻结计划

状态：`2026-05-15` 冻结执行版本；`WP0 / WP1 / WP2 / WP3` 已完成，`WP4` 已完成第一阶段共享基础 / 空中适配器 / 分发接缝以及第二阶段 profile 回连 / 兼容性落地并通过聚焦验收，`WP5` 已完成，`WP6` 已完成，`WP7` 已启动并完成前两批骨架 / 契约 / 公共 DTO 绑定往返落地，`WP8` 已完成 `MissionCommand 通用 + 空中` 兼容拆分、消费者/json 对称收束及聚焦回归验收。
文档定位：

- 本文档冻结围绕 `通用 / 空中 / 海军` 的模块拆分计划。
- 本轮目标是首先稳定边界、兼容层和验证面，而不直接引入完整的海军作战运行时。
- 本文档未授权超出工作包范围的语义重写；所有实现须按工作包验收。

验收标准：对于涉及 Python / nanobind / 运行时的实现，默认使用仓库虚拟环境和本地构建产物进行验收，即：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest
```

不将系统 Python 作为最终验收标准。

## I. 目标

本计划的目标不是“立即创建海军训练主线”，而是为后续空中与海军作战并行开发建立可合并的结构基础。

本轮要解决的核心问题：

1. 从当前混杂的 DTO 中分离出 `联合/通用核心` 与 `空中特化`。
2. 为未来的 `海军 profile` 建立落脚点，但不在本轮强制实现完整海军运行时。
3. 冻结 `任务/指挥 -> Python 运行时 -> 契约/测试` 链路的兼容拆分路线。
4. 避免在当前的 `空中优先` 结构中通过 `if Navy` 继续堆积新语义。

## II. 当前评估

根据支持分析文档 [Common / Air / Naval Module Split Analysis](./archive/common_air_naval_modular_split_analysis_20260515.zh.md)，当前仓库已具备以下条件：

- 标准文档层已能支持 `联合/通用核心 + 服务 profile + 特化` 的建模路线；
- 入口点如 `ServiceProfile::Navy` 和 `UnitType::Ship` 已存在；
- DTO、Python 辅助模块、契约运行器、测试及工具层仍显著 `空中优先`；
- `TaskOrder / LeaderIntent / PilotReport` 适合作为第一批结构化拆分目标；
- `MissionCommand` 是高风险的紧耦合结构，应延后处理。

## III. 非目标

本轮不做：

- 重写气动力学或控制律。
- 直接引入完整的海军任务运行时。
- 批量将所有场景/训练配置修改为多服务格式。
- 一次性处理旧结构体名称、旧头文件名或旧 Python 绑定导出名。
- 将 `MissionCommand` 重构为全新的嵌套对象并同时重写所有下游消费者。
- 重写现有的协同起飞 / 巡航 / 着陆主线行为。

本轮允许：

- 创建新的 `通用/空中/海军` 目标目录及 README。
- 创建新的兼容性伞状头文件。
- 创建新的 Python 分发/辅助模块。
- 结构化拆分 `tests/contracts`。
- 回填 `docs/standards`、`docs/task` 及必要的 `README` 文件的边界。

## IV. 总体策略

### 4.1 拆分顺序

采用以下顺序：

1. 文档与模式边界冻结
2. C++ 通用枚举 / DTO 核心提取
3. `TaskOrder / LeaderIntent / PilotReport` 空中拆分
4. Python profile / loader / env 分发拆分
5. `tests/contracts` 迁移
6. `tests/runtime`、`tools/eval`、`tools/diagnostics`、场景/配置迁移
7. `海军` profile 骨架及最小契约落地
8. `MissionCommand` 延迟重构

### 4.2 兼容性策略

第一批次默认保留：

- 旧头文件路径
- 旧结构体名称
- 旧 Python 绑定导出名
- 旧场景/契约的兼容解释层

兼容性策略的目的不是长期维持双轨，而是降低每个阶段的合并风险。

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

- `任务/指挥` 层描述的是服务/任务组织语义，而非单一平台物理模型；
- `ship` 更适合平台/执行层语义；
- `naval` 是与 `air` 对齐的任务/控制 profile 层。

## V. 冻结工作包

### WP0：文档与字段归属冻结

目标：

- 首先明确界定 `通用 / 空中 / 海军` 的边界；
- 明确哪些字段和枚举必须属于 `通用`，哪些必须属于 `空中`；
- 明确对于 `海军`，本轮仅建立骨架，不直接承诺完整运行时。

冻结范围：

- `docs/task` 本主题分析/计划文档
- `docs/standards/joint/*`
- `docs/standards/services/*`
- `docs/standards/document_alignment_map.md`
- 必要的 `src/components/*/README.md`

明确不做：

- 任何行为性代码迁移
- 任何运行时语义变更

可交付物：

- 分析文档
- 冻结计划文档
- 字段/枚举归属表

验收标准：

- `通用` 和 `空中` 字段归属清晰
- `海军` 本轮边界明确
- 后续代码实现无需重新争论字段归属

当前状态：

- 已完成：`docs/task` 分析与计划文档已落地
- 已完成：`docs/standards/document_alignment_map.md`、`docs/standards/joint/command_and_modeling_baseline.md`、`docs/standards/services/navy.md`、`docs/standards/naval/README.md` 边界回填
- 已完成：`src/components/tasking/README.md` 和 `src/components/command/README.md` 目录边界描述

### WP1：提取通用枚举与中立通信层

目标：

- 从 `tasking_enums.h` 中提取真正的联合层通用枚举；
- 将 `CommMsgType` 从 `pilot_report.h` 移入中立通信层。

冻结范围：

- `ServiceProfile`
- `TaskFamily`
- `TacticalUnitType`
- `CommandRelationship`
- `AuthorityScope`
- `AssigneeKind`
- `CoordinationMode`
- `CommMsgType`

建议的目标结构：

```text
src/components/tasking/common/core_tasking_enums.h
src/components/command/common/comm_message.h
```

兼容性要求：

- 保留 `src/components/tasking/tasking_enums.h`
- 在 `src/components/tasking/pilot_report.h` 中保留对旧包含的兼容性

明确不做：

- 本阶段不迁移 `TaskOrder` / `LeaderIntent` / `MissionCommand` 的所有字段

验收标准：

- C++ 构建通过
- `ef_py` 绑定构建通过
- 旧包含路径仍可工作
- 不改变现有运行时行为

风险说明：

- 需要同步 `bindings_command.cpp`
- 需注意 `CommMsgType` 在 `legacy_command.h`、数据链路、航迹管理器中的依赖

当前状态：

- 已完成：`src/components/tasking/common/core_tasking_enums.h` 提取了通用枚举
- 已完成：`src/components/command/common/comm_message.h` 承载中立的 `CommMsgType`
- 已完成：兼容性包含仍通过 `tasking_enums.h`、`pilot_report.h`、`comm.h` 在外部维护
- 已完成：`ef_core` / `ef_py` 构建及聚焦 pytest 验证

### WP2：提取 `TaskOrder / LeaderIntent / PilotReport` 通用核心

目标：

- 在不破坏公共结构体名称及大部分下游调用方式的前提下，建立通用/空中文件边界；
- 为后续 `海军` 扩展预留干净的落脚点。

冻结范围：

- [src/components/tasking/task_order.h](../../../src/components/tasking/task_order.h)
- [src/components/tasking/leader_intent.h](../../../src/components/tasking/leader_intent.h)
- [src/components/tasking/pilot_report.h](../../../src/components/tasking/pilot_report.h)

建议的目标结构：

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

兼容性策略：

1. 先创建目标文件与伞状包含。
2. 保持 `TaskOrder`、`LeaderIntent`、`PilotReport` 名称不变。
3. 为下游保留平坦 DTO 兼容期。

明确不做：

- 立即将结构体改为深层嵌套对象
- 同时重写所有 Python 消费者

验收标准：

- `SimulationKernel` / `WorldBatchRuntime` / `RuntimeFacade` 构建通过
- `bindings_command.cpp` 导出保持兼容性
- `tests/leader/test_tasking_profile_contracts.py`
- `tests/world_batch/test_world_batch_runtime.py`
  相关字段冒烟通过

风险说明：

- `runtime facade`、`world_batch_contracts` 直接暴露这些 DTO
- 迁移旧字段时需控制包含依赖方向

当前状态：

- 已完成：`TaskOrder`、`LeaderIntent`、`PilotReport` 拆分为 `common/*_core.h` 和 `air/*_air.h`
- 已完成：旧伞状头文件继续通过 `Core + Air` 兼容壳对外暴露原结构体名称，并维护平坦字段访问
- 已完成：`bindings_command.cpp` 兼容性导出已验证
- 已完成：`tests/leader/test_tasking_profile_contracts.py`、`tests/runtime/facade/test_runtime_facade.py` 及 `tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` 聚焦验收

### WP3：提取仅空中枚举与空中扩展

目标：

- 将空战专用的任务族、阶段、回收、起飞、跑道、编队字段从通用结构中明确下沉到 `空中`。

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

以及以下仅空中字段的归属澄清：

- `recovery_runway_id`
- `recovery_base_id`
- `takeoff_*`
- `runway_slot_id`
- `lead_aircraft_id`
- `formation_*`
- `wingman_*`
- `support_sector_id`

明确不做：

- 添加海军对应实现
- 改变协同空中主线行为

验收标准：

- `tasking_enums.h` 降级为伞状/兼容头文件
- 新增 `air_tasking_enums.h`
- 现有空中作战运行时行为保持不变

风险说明：

- `tests/runtime` 中许多编队 / 起飞 / 着陆测试依赖于这些枚举

当前状态：

- 已完成：添加 `src/components/tasking/air/air_tasking_enums.h` 作为仅空中枚举所有者
- 已完成：`tasking_enums.h` 降级为 `通用 + 空中` 兼容伞状头文件
- 已完成：`task_order_air.h`、`leader_intent_air.h`、`mission_command.h` 及 `bindings_command.cpp` 已改为显式依赖空中枚举所有者
- 已完成：`ef_core` / `ef_py` 构建通过，并通过 `tests/leader/test_tasking_profile_contracts.py`、`tests/leader/test_command_field_projection_contracts.py`、`tests/runtime/facade/test_runtime_facade.py`、`tests/runtime/mission/test_mission_runtime.py`、`tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` 聚焦验收

### WP4：Python Profile/分发拆分

目标：

- 将 Python 侧从“伪通用，实空中优先”转变为显式分发。

冻结范围：

- `python/rl/common_core_profile.py`
- `python/rl/leader_tasking.py`
- `gym_envs/scenario_loader.py`
- `gym_envs/leader_env.py`
- `python/rl/multi_agent_runtime.py`
- `python/testing/scenario_contract_runner.py`

建议的目标结构：

```text
python/rl/profile/common_core_base.py
python/rl/profile/air_profile.py
python/rl/tasking_bridge.py
python/rl/tasking_air_adapter.py
gym_envs/tasking_runtime_dispatch.py
gym_envs/leader_semantics_adapter.py
```

同相拆分策略：

1.  首先提取用于枚举/默认值/基础设施的共享基类。
2.  然后提取空中任务简介助手。
3.  然后为加载器/环境引入分发接口。
4.  暂时不引入完整的海军适配器，只保留接口。

明确不做：

-   立即修改任务观察向量结构
-   立即将现有检查点转换为新语义

验收标准：

-   `common_core_profile` 中的共享/空中逻辑分离
-   `leader_tasking` 中的共享桥接器和空中适配器分离
-   `scenario_loader` / `leader_env` 能够通过适配器/分发使用空中任务简介
-   现有空中场景冒烟测试不退化

风险说明：

-   任务观测维度和命令代码兼容性最为敏感
-   旧的检查点/评估工具链依赖于现有的空中优先解释

当前状态：

-   已完成：添加了 `python/rl/profile/common_core_base.py`，托管共享的枚举/默认值/基础设施助手
-   已完成：添加了 `python/rl/profile/common_core_defaults.py`，托管共享通用核心默认值/推理助手
-   已完成：添加了 `python/rl/profile/air_profile.py`，托管空中任务族/任务类型、航路/回收和核心任务命令助手
-   已完成：添加了 `python/rl/tasking_air_adapter.py` 和 `python/rl/tasking_bridge.py`，建立了默认空中适配器和任务简介分发接口
-   已完成：`gym_envs/scenario_loader.py`、`gym_envs/leader_env.py`、`python/testing/scenario_contract_runner.py` 已更改为通过分发使用默认空中任务简介
-   已完成：`python/rl/common_core_profile.py` 中的空中语义和共享默认值/推理现通过 `profile` 子模块托管，同时保留旧的导出表面作为兼容性外壳
-   已完成：`python/rl/leader_tasking.py` 中的 `infer_route_ref_id`、`infer_recovery_*`、`build_kernel_mission_command` 现通过 `air_profile` 托管，同时维护旧的入口点和 `ef_py` 补丁兼容性
-   已完成：`python/rl/tasking_air_adapter.py` 清晰地从 `common_core_profile` 聚合通用核心默认值/规格，并从 `air_profile` 聚合空中语义
-   已完成：`./.venv/bin/python -m py_compile` 覆盖了 `common_core_profile.py`、`leader_tasking.py`、`tasking_air_adapter.py`、`tasking_bridge.py` 和 `python/rl/profile/*`
-   已完成：`tests/leader/test_tasking_profile_contracts.py`、`tests/leader/test_tasking_phase_control_contracts.py`、`tests/leader/test_command_field_projection_contracts.py`、`tests/runtime/mission/test_leader_tasking_runtime.py`、`tests/runtime/facade/test_runtime_facade.py`、`tests/runtime/mission/test_mission_runtime.py` 和 `tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` 重点验收通过（`53 passed` + `1 passed`）
-   未完成：进一步物理迁移 `RuleBasedLeaderPhaseManager` / `ScriptedC2TaskManager` 和 `_apply_task_order_overrides`；`multi_agent_runtime.py` 以及更广泛的合约/运行时入口点的分发转换

### 工作包5：将 `tests/contracts` 迁移至通用优先

目标：

-   将 `tests/contracts` 转变为第一个真正按 `common / air / future naval` 组织的可执行验证表面。

冻结范围：

-   `python/testing/scenario_contract_runner.py`
-   `tests/contracts/unit/comm/*`
-   `tests/contracts/chain/*`

建议方向：

-   `common core` 合约仅验证：
    -   `service_profile`
    -   `task_family`
    -   `tactical_unit_type`
    -   `command_relationship`
    -   `authority_scope`
    -   `task_group_id`
    -   `supported/supporting`
    -   `role_code`
    -   `coordination_mode`
    -   `recovery_site_id`
-   空中特定合约继续保留在 `air` 语义集中

明确不做：

-   在此阶段迁移所有运行时测试

验收标准：

-   `scenario_contract_runner` 支持通用核心合约和空中合约分支
-   `tests/contracts/unit/comm/*` 包含不依赖于跑道/起飞/编队的通用核心基线
-   现有空中合约继续通过

当前状态：

-   已完成：`python/testing/scenario_contract_runner.py` 在 `task_order_and_mission_link` 内部引入了通用核心/空中特定断言分层，旧的 `check_kind` 和旧规范路径保持兼容
-   已完成：`python/testing/scenario_contract_runner.py` 添加了两个通用优先单元合约入口点：`task_order_common_core` 和 `scenario_loader_common_core_semantics`
-   已完成：`scenario_loader_mission_semantics` 支持分支写入 `expected_task_order_common_core`、`expected_task_order_air` 和 `expected_post_transition_air`，同时继续与旧的 `expected_task_order` / `expected_post_transition` 保持兼容
-   已完成：添加了 `tests/contracts/unit/comm/task_order_common_core_defaults.json`，提供了一个独立于跑道/起飞/编队的通用核心默认传播基线
-   已完成：添加了 `tests/contracts/unit/comm/scenario_loader_common_core_semantics.json`，提供了场景加载器通用核心规范化基线
-   已完成：`tests/runners/test_contract_batches.py --group same_process` 包含了这两个通用优先合约，并继续覆盖旧的 `task_order_and_mission_link.json` 和 `scenario_loader_mission_semantics.json`
-   已完成：`./.venv/bin/python -m py_compile python/testing/scenario_contract_runner.py tests/runners/test_contract_batches.py`
-   已完成：`tests/runners/test_contract_batches.py --group same_process` 重点验收通过（4个合约通过）
-   已完成：`tests/leader/test_tasking_profile_contracts.py` 和 `tests/leader/test_command_field_projection_contracts.py` 重点回归通过（9个通过）
-   未完成：将纯空中合约物理迁移到 `tests/contracts/unit/comm/` 下，以及建立 `unit/air` / `unit/naval` 目录体系；更广泛的单元/运行时合约仍待继续通用优先转换

### 工作包6：`tests/runtime`、`tools/eval`、`tools/diagnostics` 的适配

目标：

-   在 `common/air` 拆分稳定后，让运行时测试和工具层遵循结构化方法。

冻结范围：

-   `tests/runtime/*`
-   `tools/eval/*`
-   `tools/diagnostics/*`

阶段策略：

-   首先适配共享 CLI / 通用助手
-   然后适配空中特定分类
-   此阶段不需要新的海军评估/诊断主线

明确不做：

-   立即添加海军任务评估体系
-   批量重写协同诊断图表语义

验收标准：

-   `eval_task.py` / `eval_sb3.py` 仍运行空中主线
-   `diagnostics` 共享基础保持非回归
-   运行时测试适配到 common/air 拆分后的字段路径

当前状态：

-   已完成：添加了 [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py)，统一了任务观察模式的名称、`mode_code`、维度和字段名分类。
-   已完成：[python/env_config.py](../../../python/env_config.py)、[gym_envs/universal_env.py](../../../gym_envs/universal_env.py)、[gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)、[tools/eval/sb3_eval_base.py](../../../tools/eval/sb3_eval_base.py)、[tools/diagnostics/analyze_cooperative_observation_scales.py](../../../tools/diagnostics/analyze_cooperative_observation_scales.py) 集成了共享分类，同时保留了原始的 CLI 协同门控和运行时行为。
-   已完成：添加了 [tests/runtime/mission/test_mission_obs_taxonomy.py](../../../tests/runtime/mission/test_mission_obs_taxonomy.py)，锁定了共享分类与运行时入口点之间的 `mode_code` / 维度 / 字段布局一致性。
-   已完成：`mission_obs_taxonomy` 添加了一个共享助手，将字段名映射到索引；[tests/runtime/mission/test_mission_runtime.py](../../../tests/runtime/mission/test_mission_runtime.py)、[tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py](../../../tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py)、[tests/runtime/multi_agent/test_multi_agent_runtime.py](../../../tests/runtime/multi_agent/test_multi_agent_runtime.py) 中的核心任务断言已从魔法索引收敛到共享分类。
-   已完成：`./.venv/bin/python -m py_compile` 覆盖了 WP6 的新文件和修改文件。
-   已完成：`tests/runtime/mission/test_mission_obs_taxonomy.py`、`tests/runtime/mission/test_mission_runtime.py`、`tests/runtime/multi_agent/test_multi_agent_runtime.py`、`tests/runtime/multi_agent/test_multi_agent_benchmark.py` 重点回归通过（`34 passed`）。
-   已完成：`tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`、`tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`、`tests/runtime/execution/test_execution_episode_batch_prepare.py`、`tests/runtime/execution/test_execution_episode_controller.py` 扩展回归通过（`37 passed, 8 subtests passed`）。
-   已完成：在第二批首次回归中，`tests/runtime/mission/test_mission_obs_taxonomy.py`、`tests/runtime/mission/test_mission_runtime.py`、`tests/runtime/multi_agent/test_multi_agent_runtime.py`、`tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py` 通过（`51 passed`）。
-   已完成：在第二批关联回归中，`tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`、`tests/runtime/execution/test_execution_episode_batch_prepare.py`、`tests/runtime/execution/test_execution_episode_controller.py`、`tests/runtime/multi_agent/test_multi_agent_benchmark.py` 通过（`20 passed, 8 subtests passed`）。
-   已完成：`tests/contracts/unit/config/env_config_resolution.json` 合约直接运行通过。
-   已完成：`python/rl/multi_agent_benchmark.py`、`tools/diagnostics/benchmarks/visual_resolution.py`、`tools/diagnostics/benchmarks/world_batch_vec_env.py` 中的 `mission_obs_mode` CLI 选择集已统一集成到共享分类中。
-   已完成：在 WP6 范围内，针对任务观察分类的配置/运行时/测试/评估/诊断共享收敛已完成。
-   未完成：如果后续进入 `WP7`，仍然需要为海军特定运行时/评估/诊断添加新的 profile 感知断言和入口点，但这超出了 WP6 的范围。

### 工作包7：海军任务简介骨架和最小合约实现

目标：

-   在 common/air 边界稳定后，建立一个真正可实现的海军模块入口点，以便并行开发海军操作。

冻结范围：

-   `docs/standards/services/navy.md`
-   `docs/standards/naval/*`（如果新增）
-   `src/components/tasking/naval/*`
-   `tests/contracts/unit/naval/*`（如果新增）

此阶段仅建议：

-   海军枚举和 DTO 扩展骨架
-   最小海军合约模式
-   最小合约运行时分发

明确不做：

-   完整的舰队/编队运行时
-   完整的海军 leader 环境
-   完整的海军评估/诊断套件

验收标准：

-   `naval` 目录和 README 已就位
-   至少一组 profile 特定合约可执行
-   不影响现有空中主线

当前状态：

- 完成：为 `src/components/tasking/naval/README.md`、`naval_tasking_enums.h`、`task_order_naval.h`、`leader_intent_naval.h`、`pilot_report_naval.h` 添加了骨架，作为未来海军 DTO 扩展的着陆点。
- 完成：添加了 `python/rl/profile/naval_profile.py` 和 `python/rl/tasking/naval_adapter.py`，并使 `python/rl/tasking/bridge.py` 能够对 `tasking_profile = naval` / `service_profile = Navy` 进行 profile 感知的派发。
- 完成：`python/rl/tasking/common_core_profile.py` 现在拥有海军感知的公共核心默认路径，能够维护最小海军语义，例如 `Navy + Escort + Screen + CommandNode` 用于 `task_order / leader_intent / pilot_report`。
- 完成：添加了 `tests/contracts/unit/naval/task_order_naval_profile_defaults.json` 和 `tests/contracts/unit/naval/scenario_loader_naval_common_core_semantics.json`；两个最小海军合约均通过执行。
- 完成：添加了 `tests/leader/test_tasking_profile_contracts.py`，该测试与现有的公共核心/运行时回归一起通过验收。
- 完成：`TaskOrder / LeaderIntent / PilotReport` 已正式集成 `TaskOrderNaval / LeaderIntentNaval / PilotReportNaval`，不再仅仅是独立的骨架头文件。
- 完成：`bindings_command.cpp` 现在导出 `NavalWarfareRole` / `NavalStationType`，并公开海军字段，如 `warfare_role_code`、`officer_in_tactical_command`、`naval_station_type`。
- 完成：`gym_envs/leader_env.py`、`tests/leader/test_command_field_projection_contracts.py`、`tests/world_batch/test_world_batch_runtime.py` 中的克隆白名单已完成海军字段的绑定/克隆/往返验证。
- 未完成：海军 leader/运行时/评估/诊断尚未开始；后续工作应在此骨架上逐步扩展。

### WP8：MissionCommand 重构推迟

目标：

- 在公共/空中/海军结构层和 Python 派发稳定后，再处理 `MissionCommand` 的公共/空中分层。

冻结范围：

- `src/components/command/mission_command.h`
- `src/models/air/default_control_model.cpp`
- `src/core/mission/episode/detail/*`
- `src/systems/physics/instrument_system.h`
- `bindings_command.cpp`

建议方向：

- `mission_command_core.h`
- `mission_command_air.h`
- 与 `mission_command.h` 兼容

明确未完成：

- 在此阶段不引入完整的海军执行命令

验收标准：

- `MissionCommand` 的公共/空中边界清晰
- 现有的空中控制 / 回合 / 仪器语义不退化
- 编解码 / 相等性 / 外观导出兼容期明确

风险说明：

- 此阶段是整个链条中风险最高的阶段
- 只允许在前一个工作包稳定后方可进入

当前状态：

- 完成：添加了 `src/components/command/common/mission_command_core.h`，包含通用字段：`cmd_heading_deg`、`cmd_altitude_m`、`cmd_speed_mps`、`command_code`、`route_ref_id`、`assigned_target_id`、`authorization_to_fire`、`active`。
- 完成：添加了 `src/components/command/air/mission_command_air.h`，包含仅限空中的字段：recovery、takeoff、formation offset 等。
- 完成：`src/components/command/mission_command.h` 改为兼容性雨伞头文件，继续暴露扁平的 `MissionCommand` 名称和字段访问。
- 完成：`bindings_command.cpp` 可以继续暴露现有的扁平 `MissionCommand` 字段，而不改变导出名称；Python 端保持兼容。
- 完成：添加了 `tests/runtime/mission/test_mission_command_split_semantics.py`，涵盖绑定字段暴露和直接内核往返。
- 完成：`gym_envs/scenario_loader/runtime_state.py`、`src/core/mission/episode/detail/mission_command_codec.cpp`、`src/core/mission/episode/detail/episode_transition_runtime.cpp` 完成了 `MissionCommand` 的消费者/JSON 对称性；诸如 `formation_*`、`assigned_target_id`、`authorization_to_fire`、`recovery_approach_type` (公共/空中) 等字段在回合/运行时往返中保持保真度。
- 完成：`python/rl/profile/air_profile.py` 纠正了任务级 `MissionCommand` 字段被零值 `leader_intent` 意外覆盖的问题，确保加载器任务命令与内核命令构建之间的一致性。
- 完成：重点回归测试通过：`tests/runtime/mission/test_leader_tasking_runtime.py`、`tests/world_batch/test_world_batch_runtime.py`、`tests/runtime/execution/test_execution_episode_state.py`、`tests/runtime/execution/test_execution_episode_controller.py`、`tests/runtime/facade/test_runtime_facade.py`、`tests/runtime/mission/test_mission_runtime.py`、`tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`、`tests/world_batch/test_world_batch_vec_env.py`。
- 未完成：`MissionCommand` 尚未进入 `naval` 执行命令分层；此阶段仅冻结 `common + air` 结构和兼容层。

## VI. 阶段依赖关系

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

- `WP2` 和 `WP3` 可以部分交错，但字段所有权冻结必须首先完成。
- `WP4` 不应早于 `WP2/WP3`；否则 Python 派发将缺乏稳定的着陆点。
- `WP8` 必须最后完成。

## VII. 统一验收要求

每个代码阶段默认应完成以下一项或多项验证：

- `cmake --build build-workshop --target ef_core ef_py -j2`
- `./.venv/bin/python -m py_compile ...`
- `./.venv/bin/python -m pytest -q tests/contracts ...`
- `./.venv/bin/python -m pytest -q tests/runtime ...`

如果某个阶段仅涉及文档，可以跳过代码验证，但必须明确注明“未触及代码”。

## VIII. 文档约束

本文档是本主题唯一的阶段规划文档。

后续推进要求：

- 优先回填本文档中相应工作包的状态。
- 如果需要补充专项研究，可以添加辅助文档。
- 辅助文档不得再次承担并行阶段规划的责任。

## IX. 当前冻结结论

当前冻结结论如下：

1. 本主题采用 `common + air + naval`，而非 `air + ship`。
2. `TaskOrder / LeaderIntent / PilotReport` 先拆分，`MissionCommand` 后拆分。
3. Python 层采用派发/适配器路线，不继续堆积 `if Navy`。
4. `tests/contracts` 先迁移，`tests/runtime` 后迁移。
5. `naval` 第一批仅做模式/合约骨架，不直接承诺完整运行时。
