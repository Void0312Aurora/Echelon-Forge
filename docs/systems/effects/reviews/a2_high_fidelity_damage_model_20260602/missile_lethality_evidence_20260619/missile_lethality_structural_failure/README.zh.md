# MLF-6 结构失效与机体断裂

状态：`2026-06-18` accepted / archived MLF-6 v10 证据。P1/P2 设计、
P3 状态机、P4 事件 writer、P5 诊断导出、P6 聚焦验证和 P7 更广回归
均已实现并有证据。P7 旧 oracle 更新后，完整 `tests/runtime/air_combat/` +
`tests/world_batch/` lane 已通过。v10 进一步修正 close continuous-rod
近场模型，让结构性 cut-mode severity 能被断裂状态机消费；保留的 proxy
standoff 报告现在显示 beam 侧 `0.5/1/2/4 m` 会产生 wing_loss，`8/14 m`
不产生断裂。该包已按用户明确指令物理归档到本地 A2 注册表下。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- 父级 A2 任务索引：[../../README.zh.md](../../README.zh.md)
- MLF-1 杀伤链合同（MLF 阶段权威定义和边界）：
  [../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md](../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md)
- MLF-5 部件脆弱性归档（上游输出，MLF-6 唯一消费面）：
  [../missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/README.zh.md](../missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/README.zh.md)
- A2 目标几何 retained follow-on（F-16C 32 部件 receiver 地图）：
  [../../missile_lethality_target_geometry/README.zh.md](../../../../../../../README.zh.md)
- A8 损伤效果链（已有 fire/fuel/sensor/engine 传播，MLF-7 将扩展）：
  [../../../archive/a8_damage_effect_chain/README.zh.md](../../../../../../../README.zh.md)
- F-16C unit database（MLF-6 必须分类的当前部件定义）：
  [../../../../../../examples/config/database/aircraft/units/f16c_block50.json](../../../../../../../examples/config/database/aircraft/units/f16c_block50.json)
- 子项目创建标准：
  [../../../../../agent/rules/subproject_creation_standard.zh.md](../../../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- 真实性权限边界：
  ../../../../../standards/foundation/realism_authority_boundary.zh.md（`git show e8dc0b29~1:docs/standards/foundation/realism_authority_boundary.zh.md`）
- 结构断裂合同和运行时 writer：
  [../../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h)
  （`StructuralBreakupEvent`，第 213-221 行）
- 交战事件类型：
  [../../../../../../src/core/engine/engagement_event_types.h](../../../../../../../src/core/engine/engagement_event_types.h)
  （`RecentEngagementEvents::structural_breakup_events`）
- MLF-5 部件损伤状态（实时 ECS 组件，MLF-6 消费面）：
  [../../../../../../src/components/combat/common/damage_common.h](../../../../../../../src/components/combat/common/damage_common.h)
  （`ComponentDamageState`）
- 飞机损伤系统（MLF-6 系统注册位置）：
  [../../../../../../src/systems/combat/damage_system_air.h](../../../../../../../src/systems/combat/damage_system_air.h)
  （`AircraftDamageStateUpdate` — 第 344 行）

## 目的

MLF-6 是导弹杀伤框架的第六阶段。其唯一交付物是**结构断裂事实写入器**：
一个从实时 ECS 读取 MLF-5 累积部件损伤状态、并将 `StructuralBreakupEvent` 行
写入现有事件存储的机制，并通过 `cause_event_id` 保持可追溯因果关系。

当前仿真将所有结构损伤压缩为标量 `structural_integrity`（1.0 → 0.0）。
翼梁断裂和发动机核心断裂都从同一个标量中扣除，产生相同下游行为。
MLF-6 用具名、部件感知的断裂事实替换这种无差别衰减：哪个结构组失效了、
以什么模式、到什么程度。

### MLF-6 明确不做什么

MLF-1 合同将飞行动力学后果分配给 **MLF-7（二次后果耦合）**，其入口条件是 MLF-6 验收。
MLF-6 写入事实；MLF-7 消费事实。具体来说，MLF-6 不：

- 修改 `aerodynamics_system.h` 升力/阻力/俯仰/偏航/滚转/推力修正。
- 修改 `AircraftDamageState` 标量字段（`structural_integrity`、`flight_control_integrity`、`propulsion_integrity` 等）。
- 增加或修改失能状态分类规则。
- 以任何形式将断裂状态桥接到飞行动力学。

这些都属于 MLF-7，MLF-1 合同授权其写入面为 `damage/air`。MLF-6 的写入面仅为 `damage/physics`。

MLF-6 是同时解锁 MLF-7 和 MLF-8 的瓶颈阶段。没有具名断裂事实，
飞行动力学耦合和残骸/碎片生命周期都无法启动。

## 关键设计决策（P0 — 已冻结）

以下决策在 P0 自审期间辩论并冻结。任何修订必须重开 P0。

### D1：MLF-6 消费实时 ECS `ComponentDamageState`，不消费事件存储行

MLF-5 的 `ComponentDamageEvent` 是事后写入的诊断/记录制品。实时真值是每个飞机实体上的
`ComponentDamageState`，由 `AircraftDamageStateUpdate` 每步更新。MLF-6 直接读取此 ECS 组件。

理由：事件存储是日志，不是响应式信号。从事件行追踪累积损伤需要 MLF-6 重放历史。
读取实时 ECS 组件天然获得每步累积状态。

### D2：MLF-6 不修改任何*已有* ECS 组件；写入*新增*组件

现有 `structural_integrity` 标量完全不被 MLF-6 触及。它继续通过
`accumulate_aircraft_structural_envelope_damage` 和 `default_effects_air_domain.h` 衰减。
MLF-6 通过两个新输出增加平行的、部件感知的断裂事实流：`StructuralBreakupState` ECS 组件（D7）
和 `StructuralBreakupEvent` 行（事件存储）。

MLF-7 后续将决定：
- 读取断裂事件并将 `structural_integrity` 设为断裂状态的函数，或
- 直接读取断裂事件并绕过标量进行飞行动力学钳制。

### D3：`detached_part_ref` 是诊断字符串标签，不是世界实体引用

`StructuralBreakupEvent::detached_part_ref` 是稳定字符串标识符
（如 `"left_wing"`、`"right_stabilator"`、`"engine_core"`）。
MLF-6 不创建、销毁或分离 ECS 实体。MLF-8 后续将消费这些标签创建持久化残骸/碎片实体。

### D4：断裂状态机是 per-airframe、累积、不可逆的

结构只能向前衰减：`intact` → `partial_detachment` → `partial_breakup` → `full_breakup`。
断裂模式一旦断言即保持。多个断裂模式可以同时激活（如 wing_loss + engine_detach）。
若累积部件损伤足够，单个 timestep 可跨多个状态。

### D5：集成点 — 新 ECS system 注册在 `AircraftDamageStateUpdate` 之后

MLF-6 注册新的 `OnUpdate` 系统（`StructuralFailureUpdate`），在同一 phase 内运行于
`AircraftDamageStateUpdate` 之后。它读取 `ComponentDamageState`（已被损伤系统更新），
写入两个输出：新增的 `StructuralBreakupState` ECS 组件（D7）和
`RecentEngagementEvents` 中的 `StructuralBreakupEvent` 行。

### D6：失能状态交互推迟到 MLF-7

MLF-6 写入 `StructuralBreakupEvent` 事实和 `StructuralBreakupState`（D7）。
不触及 `PlatformDamageState::loss_state`、`Health::current_hp` 或
`sync_platform_damage_loss_state`。`full_breakup` 是否意味着 `Lost`
是 MLF-7 的决策，不是 MLF-6 的。

### D7：不可逆断裂状态存储在新增 ECS 组件 `StructuralBreakupState` 中

per-airframe 不可逆状态机（D4）持久化在一个**新增**
ECS 组件 `StructuralBreakupState` 中，挂载在飞机实体上。
该组件持有 `breakup_state` 和活跃 `break_mode` 位掩码，
每 tick 由 `StructuralFailureUpdate` 更新。

这是唯一满足所有需求的机制：
- **构造层面不可逆**：组件值只能向前转换；不存在 `full_breakup` → `intact` 的代码路径。
- **world-batch 序列化存活**：作为标准 ECS 组件，无需定制逻辑即可参与快照/恢复循环。
- **存档/恢复和回放存活**：组件是 ECS 世界状态的一部分。
- **下游系统可查询**：MLF-7 可直接 `get<StructuralBreakupState>()`，无需解析事件存储历史。
- **重置语义清晰**：实体销毁移除组件；实体创建从 `breakup_state = intact` 开始。

`StructuralBreakupState` 不是 `structural_integrity` 的替代品；该标量继续独立存在和衰减。
MLF-7 决定如何协调二者（D2）。

该组件应定义在新头文件 `src/components/combat/structural_failure.h`
（或与项目组件布局一致的相邻路径）中。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| MLF-5 部件损伤 | accepted / 已归档 | `ComponentDamageState` ECS 组件维护每部件累积完整度、冗余可用性和失效模式 | 不声明结构断裂 |
| `StructuralBreakupEvent` 合同 | 活跃 / writer 已接入 | `engagement_contracts.h` — `breakup_state`、`break_mode`、`detached_part_ref`、`detached_part_count`、`airframe_breakup`、`cause_event_id`；`structural_failure_system.h` 写入转换事件 | 仅写 MLF-6 事实；不做气动/失能耦合 |
| `structural_breakup_events` 向量 | 活跃 / 由 P4 writer 填充 | `engagement_event_types.h`；`simulation_kernel_engagement_event_store.cpp`；facade + Python 绑定已传递；`tools/diagnostics/structural_breakup_export.py` 导出 rows；`structural_failure_break_modes` 验证断裂模式覆盖 | 收集断裂事实；P7 更广回归已通过；MLF-6 不消费气动/失能状态权威 |
| 近场累计 wing_loss 规则 | 活跃 / v10 已校准 | `structural_failure_system.h`；`structural_failure_state`、`structural_failure_break_modes` 和 `test_continuous_rod_surface.py`；`target_geometry_proxy_standoff_grid_probe_20260615.json` 报告 43 条结构断裂记录：blast_fragmentation 3 条、continuous_rod 40 条；continuous_rod beam 侧 `0.5/1/2/4 m` 断裂，`8/14 m` 不断裂 | 仅工程代理；没有真实武器结构杀伤或 Pk 权威 |
| `structural_integrity` 标量 | 活跃 / MLF-6 不触及 | `damage_air.h:114`；通过 `accumulate_aircraft_structural_envelope_damage` 和 `default_effects_air_domain.h` 衰减 | MLF-6 不读不写此字段 |
| `ComponentDamageState`（ECS） | 活跃 / MLF-6 消费面 | `damage_common.h:171-` — `component_integrity`、`component_failure_mode`、`redundancy_group_availability`、`has_fire_suppression_components` | MLF-6 只读；不修改 |
| 飞行动力学 | 活跃 / 推迟到 MLF-7 | `aerodynamics_system.h:219` 按 `structural_integrity` 钳制 | MLF-6 不修改气动 |
| 失能状态分类 | 活跃 / 推迟到 MLF-7 | `damage_system_common.h:403-423` | MLF-6 不修改失能状态逻辑 |

## 范围

纳入：

- **盘点**所有 `ComponentDamageState` 字段、所有当前 F-16C 部件名称，以及所有 MLF-6
  必须避开的 `structural_integrity` 写入位置（只读）。
- **设计**部件→断裂模式映射表：哪些 F-16C 部件失效，在什么累积完整度阈值下，触发哪种断裂模式。
- **实现**结构断裂状态机为新 ECS 系统（`StructuralFailureUpdate`），读取 `ComponentDamageState`，
  写入新增的 `StructuralBreakupState` ECS 组件（D7），并将机体分类为
  `breakup_state` + 活跃 `break_mode` 集。
- **写入** `StructuralBreakupEvent` 行到 `RecentEngagementEvents`，用 `cause_event_id`
  引用每个贡献部件组最近的 `ComponentDamageEvent::event_id`。
- **填充** `breakup_state`、`break_mode`、`detached_part_ref`（字符串标签）、
  `detached_part_count`、`airframe_breakup`（布尔值）和 `cause_event_id`。
- **增加**每种断裂模式在受控 `ComponentDamageState` 输入下的聚焦 C++ 测试。
- **增加** `structural_breakup_events` 的 Python 诊断导出路径。
- **确保**零假阳性：未损伤机体产生零断裂事件。

不纳入：

- **不修改飞行动力学。** 升力/阻力/俯仰/偏航/滚转/推力对断裂的响应属于 MLF-7。
- **不修改 `structural_integrity`。** 标量路径保持不变；MLF-7 决定是否以及如何桥接。
- **不修改失能状态。** 断裂是否意味着 `Lost` 属于 MLF-7。
- **不做残骸/碎片生命周期。** 脱落部件是事件中的字符串标签；持久化世界实体属于 MLF-8。
- **不声明 Pk 权威、确定性击毁或真实武器校准。**
- **不包含海军或地面平台结构模型。** 仅空战。
- **不重开已封存的 MLF-1 至 MLF-5 包。**
- **不做二次后果建模。** 火灾/燃油/液压通过断裂路径传播属于 MLF-7。

## 阶段计划

阶段粒度对标 MLF-5 模式：每阶段一个聚焦关注点，每个都有窄写入面和可测试退出条件。

| 阶段 | 目标 | 入口条件 | 退出条件 | 写入面 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结范围、设计决策 D1-D7、禁止声明。 | 用户要求创建 MLF-6。 | README v2、任务簇、状态、派发队列、验收草案存在；父 README 链接 MLF-6。 | 仅文档 | complete |
| `P1 Inventory` | 盘点所有 `ComponentDamageState` 字段、所有 F-16C 部件名称，以及 MLF-6 不得触及的 `structural_integrity` 写入位置。 | P0 完成。 | 盘点文档列出所有消费字段、所有带结构组分类的 F-16C 部件名称，以及所有禁止写入位置。 | 仅文档 | complete |
| `P2 Break-Mode Mapping` | 设计部件→断裂模式分类表：哪些部件在什么完整度阈值下触发 wing_loss / tail_loss / engine_detach / fuselage_rupture。 | P1 盘点完成。 | 映射表存在；每个 F-16C 部件分类到恰好一个结构组或 `none`；阈值规则显式。 | 仅文档 | complete |
| `P3 State Machine` | 实现结构断裂状态机为新 ECS 系统（`StructuralFailureUpdate`）。 | P2 映射表批准。 | 系统读取 `ComponentDamageState`，应用 P2 映射规则，内部追踪 per-airframe `breakup_state` 和活跃 `break_mode` 集。暂不写入事件。 | `src/components/combat/structural_failure.h`、`src/systems/combat/structural_failure_system.h`、`src/tests/test_structural_failure_system.cpp` | complete |
| `P4 Event Writer` | 当状态转换或新断裂模式激活时，将 `StructuralBreakupEvent` 行写入 `RecentEngagementEvents`。 | P3 状态机通过聚焦测试。 | 事件行正确填充 `breakup_state`、`break_mode`、`detached_part_ref`、`detached_part_count`、`airframe_breakup` 和 `cause_event_id`。 | `src/systems/combat/structural_failure_system.h`、`src/core/engine/simulation_kernel_engagement_event_store.*`、`src/core/interfaces/engagement_event_recorder.h`、`src/runtime/facade/runtime_facade.cpp` | complete |
| `P5 Diagnostics` | 增加 `structural_breakup_events` 的 Python 导出路径。 | P4 事件 writer 通过聚焦测试。 | Python probe 按 `chain_id` 导出断裂事实。 | `tools/diagnostics/structural_breakup_export.py`、`tests/tools/test_structural_breakup_export.py` | complete |
| `P6 Validation` | 运行每种断裂模式的聚焦测试、完整回归 smoke 和 vs main 零回归检查。 | P4 + P5 通过。 | P2 每种断裂模式有聚焦 C++ 测试；无损伤基线产生零事件；`ctest -R structural_failure` 通过。完整 air_combat/world_batch 回归保留到 P7。 | `src/tests/test_structural_failure_system.cpp`、`CMakeLists.txt` | complete |
| `P7 Closure` | 同步文档、索引、归档边界和残余登记。 | P6 通过。 | P7 证据已记录；完整更广 lane 已通过；包已登记到本地 A2 archive。 | 仅文档 | complete / archived |

## 任务簇

- 任务簇计划：[missile_lethality_structural_failure_task_clusters_20260617.md](missile_lethality_structural_failure_task_clusters_20260617.md)

## 输出和证据

计划输出（每阶段一个）：

- `P1`：`missile_lethality_structural_failure_component_inventory_20260617.md` —
  所有 `ComponentDamageState` 字段、所有 F-16C 部件名称及结构组、所有 `structural_integrity` 写入位置（禁止触碰列表）。
- `P2`：`missile_lethality_structural_failure_break_mode_mapping_20260617.md` —
  部件→断裂模式分类表及完整度阈值。
- `P3`：`src/components/combat/structural_failure.h` 和
  `src/systems/combat/structural_failure_system.h` — 状态机实现，带聚焦
  doctest 覆盖。
- `P4`：P3 代码的事件 writer 扩展；事件存储集成；聚焦
  `structural_failure_events` doctest 覆盖。
- `P5`：`tools/diagnostics/structural_breakup_export.py` — Python probe。
- `P6`：`src/tests/test_structural_failure_system.cpp` —
  `structural_failure_break_modes` 聚焦 doctest suite 和命名 CTest lanes。

已消费现有证据（只读）：

| 来源 | MLF-6 读取什么 | 方式 |
| --- | --- | --- |
| `damage_common.h` `ComponentDamageState` | `component_integrity`、`component_failure_mode`、`redundancy_group_availability` | ECS `get<ComponentDamageState>()` 在 `StructuralFailureUpdate` 中 |
| `f16c_block50.json` | 部件名称、系统组、结构父区域 | P2 映射设计期间读取 |
| `engagement_contracts.h` | `StructuralBreakupEvent` 合同形状；规范 `structural_breakup` 杀伤链阶段 | P4 事件 schema |
| `engagement_event_types.h` | `RecentEngagementEvents::structural_breakup_events` 向量 | P4 追加/存储目标 |

MLF-6 刻意不读不写：

| 字段 / 系统 | 为何排除 |
| --- | --- |
| `AircraftDamageState::structural_integrity` | MLF-7 决策面 |
| `AircraftDamageState::flight_control_integrity` | MLF-7 决策面 |
| `AircraftDamageState::propulsion_integrity` | MLF-7 决策面 |
| `FlightModel`（max_g、min_g 等） | MLF-7 写入面 |
| `Propulsion`（mil_thrust_n、ab_thrust_n） | MLF-7 写入面 |
| `PlatformDamageState::loss_state` | MLF-7 决策面 |
| `Health::current_hp` | MLF-7 决策面 |

## 验收门

本子项目只有在以下条件满足后才能标记为 accepted：

**P2 映射**：
- F-16C 每个部件（来自 `f16c_block50.json` 和 TG-P7 split receiver）分类到结构组：
  `wing_left`、`wing_right`、`tail_left`、`tail_right`、`vertical_tail`、
  `engine_left`、`engine_right`、`fuselage` 或 `none`。
- 每个结构组有显式完整度下降阈值触发对应断裂模式。

**P3 状态机**：
- `StructuralFailureUpdate` 系统读取 `ComponentDamageState` 并产生正确 `breakup_state` 转换。
- 状态不可逆且累积（per D4）。
- 同一 timestep 可激活多种断裂模式。
- `StructuralBreakupState`（新增 ECS 组件，D7）写入正确的 `breakup_state` 和
  `break_mode` 位掩码；值只能向前转换。
- `StructuralBreakupEvent` 行在状态转换或新断裂模式激活时写入。

**P4 事件 writer**：
- 受控部件失效输入产生正确 `StructuralBreakupEvent` 行：`break_mode` 匹配 P2 分类，
  `breakup_state` 反映累积严重度，`detached_part_ref` 是稳定字符串标签，
  `cause_event_id` 引用最近相关部件损伤事件。
- 无损伤基线产生零事件（无假阳性）。
- `airframe_breakup = true` 仅当 `breakup_state == full_breakup`。

**P5 诊断**：
- Python probe 按 `chain_id` 导出断裂事实及所有事件字段。
- `pytest -q tests/tools/test_structural_breakup_export.py` 通过。

**P6 验证**：
- 聚焦 C++ 测试覆盖：wing_loss、tail_loss、engine_detach、fuselage_rupture、multi_axis 和无损伤零事件。
- `ctest --test-dir build-workshop -R structural_failure --output-on-failure`
  通过。
- 完整 `tests/runtime/air_combat/` 与 `tests/world_batch/` 已在 P7 执行。
  P7 旧 oracle 更新后，完整 lane 现为 `447 passed`。

**P7 收口**：
- P7 证据已记录，且更广回归 lane 已通过。
- 残余地图显式将气动桥接、失能状态集成、残骸/碎片生命周期和 Pk 推迟到 MLF-7 / MLF-8 / MLF-9。
- 已按用户明确指令完成 archive 移动；该包登记在本地 A2 archive 注册表。
- 所有禁止声明保持拒绝。

## 残余和下一步

Immediate：

- **P7 Accepted / Archived**：MLF-6 聚焦 lanes 与更广
  `tests/runtime/air_combat/` + `tests/world_batch/` lane 均为 green，且该包已归档到本地 A2 注册表下。

Follow-on（MLF-6 证据现在作为已归档输入）：

- **MLF-7**：二次后果耦合 — 读取 `StructuralBreakupEvent` 事实，将其桥接到
  `structural_integrity` / 飞行动力学 / 失能状态。授权写入面：`damage/air/physics/tests`。
- **MLF-8**：残骸/碎片生命周期 — 从 `detached_part_ref` 标签创建持久化世界实体。
  授权写入面：`runtime/tests`。

Deferred：

- Pk/统计校准（MLF-9）。
- AIM-120C/MQ-9 结构杀伤校准（MLF-10）。
- 海军/地面平台结构失效。

## Archive

本子项目自身现在就是一个本地 A2 归档记录。父级 archive 注册入口为
[../README.zh.md](../README.zh.md)，本子项目自己的嵌套 archive 占位仍为
[archive/README.md](archive/README.md)。
