# Common / Air / Naval 模块拆分分析

状态：分析完成，代码拆分尚未开始。
日期：`2026-05-15`

## 1. 背景

项目当前的执行主线仍以空战/飞行任务为主，但目标已经明确扩展为联合作战，且海战是第二优先级方向。

现状问题不在于“缺少 Navy 枚举”，而在于：

- `joint/common core` 的设计意图已经存在；
- 具体 DTO、运行时 helper、测试与工具链仍然大量采用 `air-first` 语义；
- 若继续在当前结构上直接叠加海战逻辑，后续很容易形成第二套平行空战栈，而不是可合并的多军种主线。

因此，在正式实现海战/联合层并行开发之前，必须先完成一次面向 `common + air + naval` 的模块拆分分析。

## 2. 本文档范围

本文聚焦以下链路的拆分前分析：

- `src/components/tasking/*`
- `src/components/command/*`
- `src/interfaces/python/bindings_command.cpp`
- `python/rl/common_core_profile.py`
- `python/rl/leader_tasking.py`
- `gym_envs/scenario_loader.py`
- `gym_envs/leader_env.py`
- `python/testing/scenario_contract_runner.py`
- `tests/contracts/*`
- `tests/runtime/*`
- `tools/eval/*`
- `tools/diagnostics/*`

本文不直接授权代码实现；后续实现应以配套冻结计划文档为准。

## 3. 已确认发现

### 3.1 `tasking/command` 层目前仍是混合 DTO

当前最核心的 C++ DTO 层虽然已按目录拆出 `tasking` 与 `command`，但其中大量结构仍把 `common core` 与 `air specialization` 混在同一份头文件中：

- [src/components/tasking/tasking_enums.h](../../../../../src/components/tasking/tasking_enums.h)
- [src/components/tasking/task_order.h](../../../../../src/components/tasking/task_order.h)
- [src/components/tasking/leader_intent.h](../../../../../src/components/tasking/leader_intent.h)
- [src/components/tasking/pilot_report.h](../../../../../src/components/tasking/pilot_report.h)
- [src/components/command/mission_command.h](../../../../../src/components/command/mission_command.h)

典型混合信号：

- `ServiceProfile / TaskFamily / TacticalUnitType / CommandRelationship` 这类字段具备联合层共性；
- `LeaderPhase / RecoveryApproachType / Takeoff* / RunwaySlotPosition / FormationRole / WingmanSlot` 明显属于空战专用语义；
- `TaskOrder`、`LeaderIntent`、`MissionCommand` 同时承载了共通关系字段与空战任务执行细节。

### 3.2 `MissionCommand` 是当前最高风险拆分点

[src/components/command/mission_command.h](../../../../../src/components/command/mission_command.h) 不只是一个被动 DTO，它已经直接进入：

- 空气动力/自动驾驶控制解释
  - [src/models/air/default_control_model.cpp](../../../../../src/models/air/default_control_model.cpp)
- 仪表与任务运行时
  - [src/systems/physics/instrument_system.h](../../../../../src/systems/physics/instrument_system.h)
  - [src/core/mission/episode/detail/episode_transition_runtime.cpp](../../../../../src/core/mission/episode/detail/episode_transition_runtime.cpp)
- 批量运行时与 facade 导出
  - [src/runtime/contracts/world_batch_contracts.h](../../../../../src/runtime/contracts/world_batch_contracts.h)
  - [src/runtime/facade/runtime_facade_types.h](../../../../../src/runtime/facade/runtime_facade_types.h)

这意味着 `MissionCommand` 不能作为首刀直接重构，否则极易同时扰动：

- 控制行为
- episode state / codec
- runtime facade
- Python 绑定
- 下游训练/评估脚本

### 3.3 `TaskOrder / LeaderIntent / PilotReport` 更适合作为首批拆分对象

相比 `MissionCommand`，下列结构虽然使用面广，但当前更多承担“设置/导出/同步”的职责，行为耦合低于 `MissionCommand`：

- [src/components/tasking/task_order.h](../../../../../src/components/tasking/task_order.h)
- [src/components/tasking/leader_intent.h](../../../../../src/components/tasking/leader_intent.h)
- [src/components/tasking/pilot_report.h](../../../../../src/components/tasking/pilot_report.h)

它们已经进入：

- `SimulationKernel` / `WorldBatchRuntime` 设置与读取 API
- Python bindings
- runtime facade
- `leader_env`、`scenario_loader`、`scenario_contract_runner`

但当前主要风险仍是字段归属和语义混合，而不是 tight-loop 控制逻辑本身。因此，它们更适合承担第一批“结构层拆分”。

### 3.4 Python “common” 语义层目前仍然 `air-first`

以下 Python 模块名义上带有 `common` 或承担 loader/runtime glue 职责，但实现里仍明显偏空战：

- [python/rl/tasking/common_core_profile.py](../../../../python/rl/tasking/common_core_profile.py)
- [python/rl/tasking/leader_tasking.py](../../../../python/rl/tasking/leader_tasking.py)
- [gym_envs/scenario_loader/core.py](../../../../gym_envs/scenario_loader/core.py)
- [gym_envs/leader_env.py](../../../../gym_envs/leader_env.py)

已确认问题包括：

- `common_core_profile.py` 默认推断 `AirForce`、`Aircraft`，并硬编码空战任务族、回收、起飞、跑道等字段；
- `leader_tasking.py` 同时混合了：
  - `TaskOrder / LeaderIntent / PilotReport` 的同步桥接
  - 空战 `MissionCommand` 翻译
  - 空战 phase/task manager
- `scenario_loader.py` 既负责加载/状态镜像，又直接承载空战任务运行时语义；
- `leader_env.py` 把 air-specific field list、phase mapping、reward/observation 语义写死在环境壳中。

这意味着 Python 层未来不应继续通过 `if Navy` 扩展，而应引入 profile dispatch / semantics adapter。

### 3.5 `tests/contracts` 是最适合先解耦的可执行面

分析显示，`tests/contracts` 比 `tests/runtime` 更适合作为首批拆分后的验证面。

原因：

- `scenario_contract_runner` 已经有一部分 common-core 字段校验与应用逻辑；
- 但当前 contract payload 仍大量带空战语义；
- 它们可以较低成本拆成：
  - `common core` 契约
  - `air` 契约
  - 未来 `naval` 契约

相比之下，`tests/runtime` 深度依赖：

- cooperative takeoff
- runway / recovery
- formation role
- mission observation vector
- landing / terminal 逻辑

因此 runtime tests 更适合作为后置迁移面。

### 3.6 `tools/eval` 与 `tools/diagnostics` 大多仍是 air 语义

`eval` / `diagnostics` 层已经在入口和公共底座上做过收敛，但任务语义仍然主要围绕空战/飞行任务：

- `eval_task.py` 当前任务族是 `stable_flight / takeoff_roll / centerline / waypoint_nav`
- `eval_sb3.py` 内含 cooperative formation role / final command code 等空战产物
- cooperative trajectory diagnostic 明显围绕起飞、航路、回收与编队

因此：

- 共享的 CLI / JSON / benchmark 底座可以保留并复用；
- 任务 taxonomy 与指标语义应在 profile 稳定后再拆。

### 3.7 现有 Naval hook 主要停留在 taxonomy 层

当前仓库已经存在一些可用的海战入口点，但大多仍是“类型入口”，不是运行时能力入口：

- [src/components/basic/common.h](../../../../../src/components/basic/common.h) 中已有 `UnitType::Ship`
- [src/components/tasking/tasking_enums.h](../../../../../src/components/tasking/tasking_enums.h) 中已有 `ServiceProfile::Navy`
- [docs/standards/services/navy.md](../../../standards/services/navy.md) 已有 US Navy profile 设计说明

但尚未发现成熟的 naval runtime consumer，说明海战目前更适合从：

- 文档
- schema
- common field contract
- profile-specific contract

开始建设，而不是直接改动空战 tight-loop runtime。

## 4. 拆分原则

### 4.1 按 `common + air + naval` 拆，不按 `air + ship` 拆

本主题最重要的结论之一是：

- `tasking` / `command` 层不是平台层；
- 它们描述的是联合层、军种层和任务组织层语义；
- 因此不应直接拆成 `air` 与 `ship`。

推荐层次应为：

1. `common core`
2. `air profile`
3. `naval profile`

其中：

- `ship` 更适合作为平台/执行层对象；
- `naval` 才适合作为任务组织与控制方式层的拆分单位。

### 4.2 先拆“归属”和“边界”，再拆行为

拆分第一阶段的重点应是：

- 文件归属
- 枚举归属
- 字段归属
- Python dispatch seam
- contract seam

而不是：

- 立刻重写控制律
- 立刻重写场景格式
- 立刻把 `MissionCommand` 改成全新嵌套对象

### 4.3 兼容层必须显式保留一段时间

当前很多路径依赖旧文件名、旧 struct 名和 Python 绑定符号。因此首批拆分必须默认保留：

- 兼容 umbrella headers
- 旧绑定导出名
- 旧 contract / JSON 字段的兼容解释层

否则拆分本身会被大量机械迁移噪声淹没。

### 4.4 先 contract-first，再 runtime/tooling

推荐顺序：

1. 文档/字段归属冻结
2. DTO / enum 拆分
3. Python common/profile dispatch
4. `tests/contracts`
5. `tests/runtime`
6. `tools/eval` / `tools/diagnostics`
7. maintained scenarios / training configs

## 5. 建议的目标归属

### 5.1 可视为 `common core` 的字段/枚举

建议归属到 `common`：

- `ServiceProfile`
- `TaskFamily`
- `TacticalUnitType`
- `CommandRelationship`
- `AuthorityScope`
- `AssigneeKind`
- `CoordinationMode`
- `task_group_id`
- `supported_node_id`
- `supporting_node_id`
- `role_code`
- `relative_slot_code`
- `recovery_site_id`
- `authority / issuer / assignee / parent node` 相关字段

### 5.2 应归属 `air` 的字段/枚举

建议归属到 `air`：

- `TaskType` 的当前空战任务族
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
- `recovery_runway_id`
- `recovery_base_id` 的当前解释方式
- `takeoff_*`
- `runway_slot_id`
- `lead_aircraft_id`
- `formation_*`
- `wingman_*`
- `support_sector_id`

### 5.3 `CommMsgType` 适合单独抽成中性通信层

`CommMsgType` 当前定义在 [src/components/tasking/pilot_report.h](../../../../../src/components/tasking/pilot_report.h)，但同时被 `ActionCommand`、datalink 和 track 系统使用。

因此建议后续迁移到中性位置，例如：

- `src/components/command/comm_message.h`
或
- `src/components/common/comm_message.h`

避免形成 `command` 反向依赖 `tasking` 的结构异味。

## 6. 建议的目标目录结构

以下结构是推荐方向，不要求在第一阶段一次性落完：

```text
src/components/tasking/common/
  core_tasking_enums.h
  task_order_core.h
  leader_intent_core.h
  pilot_report_core.h

src/components/tasking/air/
  air_tasking_enums.h
  task_order_air.h
  leader_intent_air.h
  pilot_report_air.h

src/components/tasking/naval/
  naval_tasking_enums.h
  task_order_naval.h
  leader_intent_naval.h
  pilot_report_naval.h

src/components/command/common/
  comm_message.h
  mission_command_core.h

src/components/command/air/
  mission_command_air.h
  pilot_action_air.h
  legacy_command_air.h
```

兼容期可保留：

- `src/components/tasking/tasking_enums.h`
- `src/components/tasking/task_order.h`
- `src/components/tasking/leader_intent.h`
- `src/components/tasking/pilot_report.h`
- `src/components/command/mission_command.h`

作为 umbrella / compatibility headers。

## 7. 风险与约束

### 7.1 绑定与 Python API 风险

[src/interfaces/python/bindings_command.cpp](../../../../../src/interfaces/python/bindings_command.cpp) 当前是平坦绑定面。若直接改 struct 名、字段名或枚举导出名，会同时打断：

- Python runtime
- tests
- tools
- contract runner

因此首批拆分默认不应改用户可见绑定名。

### 7.2 `MissionCommand` 的 tight-loop 风险

`MissionCommand` 当前直接进入控制律和 mission runtime，属于高风险行为面。它适合后拆，不适合作为第一阶段重构目标。

### 7.3 mission observation / checkpoint 兼容风险

`scenario_loader`、`universal_env`、`leader_env` 等路径已经固化：

- mission observation 向量维度
- cooperative slot / formation role 解释
- command code 含义

若 profile dispatch 没设计好，就会直接影响：

- 现有 checkpoint
- 现有训练配置
- 现有 smoke/runtime tests

### 7.4 contract runner 兼容风险

`scenario_contract_runner` 当前名义上支撑 common-core 字段，但仍默认使用 air-shaped runtime fixture 和 mission semantics。拆分时必须同步清理 contract runner 的 profile 假设。

## 8. 拆分优先级总结

最高优先级：

- 文档和字段归属冻结
- `tasking_enums` common/air 拆分设计
- `TaskOrder / LeaderIntent / PilotReport` 拆分设计
- `common_core_profile.py` 与 `leader_tasking.py` 的 dispatch seam 设计

中优先级：

- `scenario_loader.py`
- `leader_env.py`
- `scenario_contract_runner.py`
- `tests/contracts/unit/comm/*`

后置优先级：

- `MissionCommand`
- `tests/runtime/*`
- `tools/eval/*`
- `tools/diagnostics/*`
- `scenarios/*`
- `examples/config/*`

## 9. 当前结论

本次主题不适合直接从“实现海战模块”入手，而应先完成：

1. `common / air / naval` 的结构层边界冻结；
2. `tasking/command -> Python profile/loader -> contracts/tests` 这条链的拆分设计；
3. 明确 `MissionCommand` 后置、`TaskOrder/LeaderIntent/PilotReport` 前置的迁移顺序。

配套冻结计划见：

- [Common / Air / Naval 模块拆分冻结计划](../common_air_naval_modular_split_plan_20260515.zh.md)
