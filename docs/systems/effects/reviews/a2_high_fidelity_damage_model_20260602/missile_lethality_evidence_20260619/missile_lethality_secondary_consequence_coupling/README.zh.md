# MLF-7 二次后果耦合

状态：`2026-06-18` accepted / archived。有边界 MLF-7
切片的 P1 inventory、P2 contract、P3 bridge、P4 链路关联后果诊断、P5 聚焦
C++ 验证、P6 更广 runtime smoke 和 P7 验收均已完成。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- A2 follow-on 父索引：[../../README.zh.md](../../README.zh.md)
- MLF-1 杀伤链契约和阶段边界：
  `git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md`
- MLF-6 结构失效事实写入器（accepted / archived 上游证据）：
  [../missile_lethality_structural_failure/README.zh.md](../missile_lethality_structural_failure/README.zh.md)
- MLF-6 验收门和后置权限：
  [../missile_lethality_structural_failure/missile_lethality_structural_failure_acceptance_20260617.md](../missile_lethality_structural_failure/missile_lethality_structural_failure_acceptance_20260617.md)
- A8 损伤效果链验收证据：
  [../../../archive/a8_damage_effect_chain/README.zh.md](../../../../../../../README.zh.md)
- 子项目创建标准：
  [../../../../../agent/rules/subproject_creation_standard.zh.md](../../../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- 真实性权威边界：
  ../../../../../standards/foundation/realism_authority_boundary.zh.md（`git show e8dc0b29~1:docs/standards/foundation/realism_authority_boundary.zh.md`）
- 结构断裂状态：
  [../../../../../../src/components/combat/structural_failure.h](../../../../../../../src/components/combat/structural_failure.h)
- 飞机损伤与维护中消费者：
  [../../../../../../src/systems/combat/damage_system_air.h](../../../../../../../src/systems/combat/damage_system_air.h)
- 失能状态 helper：
  [../../../../../../src/systems/combat/damage_system_common.h](../../../../../../../src/systems/combat/damage_system_common.h)
- pipeline 注册：
  [../../../../../../src/core/engine/simulation_kernel_systems.cpp](../../../../../../../src/core/engine/simulation_kernel_systems.cpp)

## 目的

MLF-7 是 Missile Lethality Framework 的第七阶段。它的任务是消费 MLF-6
产生的具名断裂事实，并通过维护中的仿真路径，把这些事实耦合为有边界的飞机后果。

MLF-6 回答：“哪个结构部位以什么模式断裂，原因可追溯到哪里？” MLF-7 回答下一层问题：
“这种断裂应该如何影响飞机结构包线、飞行/操纵/动力能力、平台失能状态和后续诊断记录？”

这不是新的直接击杀开关。除非未来阶段明确替换契约，后果必须继续通过已有飞机损伤、
飞行、动力、平台损伤和诊断表面传播。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| MLF-6 结构断裂事实 | accepted / archived 上游输入 | `StructuralBreakupState` ECS 组件和 `StructuralBreakupEvent` 行已存在；MLF-6 聚焦和更广验证已绿 | MLF-6 不修改气动、`structural_integrity` 或失能状态 |
| `StructuralBreakupState` | active input | `src/components/combat/structural_failure.h` 保存不可逆断裂状态、激活断裂模式、激活结构组、脱落数量、`airframe_breakup` 和最后发出的断裂事件 id | 状态是事实来源；MLF-7 通过有边界 bridge 消费它，而不是走直接 kill 路径 |
| `StructuralBreakupEvent` | active diagnostic input | MLF-6 event writer 导出带 `chain_id`、`parent_event_id`、`cause_event_id`、断裂模式和脱落部位标签的事件 | 事件是记录，不是单独的反应式控制信号 |
| 飞机损伤标量路径 | active maintained consumer | `damage_system_air.h` 将 `AircraftDamageState` 映射到 `FlightModel`、`Propulsion`、`Sensor`、`Mass` 和 `PlatformDamageState` | 当前标量响应仍是合成工程代理，不是飞机专用飞控律校准 |
| 失能状态路径 | active maintained consumer | `sync_platform_damage_loss_state` 将平台能力和 HP 映射为 `CombatCapable`、任务/传感/机动 kill 或 `Lost` | MLF-7 不得静默创建新的直接实体删除路径 |
| A8 损伤效果链 | archived accepted evidence | 动力、翼面/操纵气动、燃油/质量、火灾、传感/数据链和原实体触地响应可观察 | A8 明确后置一等碎片/残留对象和真实杀伤权威 |

## 范围

范围内：

- 盘点 MLF-7 可能读写的当前表面：`StructuralBreakupState`、
  `StructuralBreakupEvent`、`AircraftDamageState`、`FlightModel`、
  `Propulsion`、`PlatformDamageState`、`Health` 和维护中的诊断。
- 为 MLF-6 的每个断裂模式定义有边界的后果契约：`wing_loss`、`tail_loss`、
  `engine_detach`、`fuselage_rupture` 和 `multi_axis`。
- 决定从断裂事实到飞机后果状态的节拍和注册位置，包括当前
  `AircraftDamageStateUpdate` 早于 `StructuralFailureUpdate` 的顺序问题。
- 通过维护中的飞机损伤路径实现后果耦合，而不是单独写一个 kill 规则。
- 增加 no-breakup、各单一断裂模式、multi-axis、不可逆状态、失能升级和零误报的
  聚焦 C++ 测试。
- 增加能按 `chain_id` 和目标实体查看后果交接的诊断。
- 在没有新校准证据进入之前，验收语言维持在工程代理层级。

范围外：

- 不做残骸/碎片实体生命周期。`detached_part_ref` 标签变成世界实体属于 MLF-8。
- 不做 Pk 或统计杀伤趋势权威。那属于 MLF-9。
- 不做武器或飞机专用校准权威。那属于 MLF-10 或后续校准门。
- 不重开已封存的 MLF-1 到 MLF-5 归档包。
- 不扩展 MLF-6，除非是修复上游事实 bug。
- 不在维护中的平台损伤/失能路径之外直接 `e.destruct()` 或删除目标。
- 不声明 stock AIM-120C、MQ-9、F-16C、海军或地面平台杀伤权威。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 写入面 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `P0 Boundary` | 打开 MLF-7 子项目、冻结非目标并接入父级导航。 | 用户要求开始考虑 MLF-7 并构建子项目。 | README、任务簇、当前状态、派发队列、验收记录和 archive 占位存在；父 README 链接 MLF-7。 | docs only | complete |
| `P1 Consequence Inventory` | 盘点全部输入事实和候选后果表面。 | P0 文档存在。 | inventory 列出读写候选、当前 owner、执行顺序和禁止直接写入面。 | docs only | complete |
| `P2 Coupling Contract` | 定义断裂模式到后果的映射和执行节拍。 | P1 inventory 完成。 | 契约表说明每个断裂模式可如何影响飞机损伤标量、平台能力和失能状态。 | docs only | complete |
| `P3 Runtime Bridge` | 实现从结构断裂事实到飞机后果状态的有边界桥接。 | P2 契约验收。 | runtime 消费 `StructuralBreakupState`，只更新批准的维护中后果表面。 | `src/systems/combat/*`、`src/core/engine/simulation_kernel_systems.cpp`、聚焦 C++ 测试 | complete / focused-pass |
| `P4 Consequence Events And Diagnostics` | 让交接在 recent events/probes 中可见，不创造新权威。 | P3 bridge 聚焦测试通过。 | 诊断通过 `PlatformConsequenceEvent` 显示断裂事实、后果 delta、失能状态转移和链路关联。 | event store / diagnostics / tests | complete / event-pass |
| `P5 Focused Validation` | 验证每个断裂模式和零误报守卫。 | P3 完成。 | 命名 CTest lane 覆盖 no-breakup、wing loss、multi-axis、幂等、same-tick bridge 和无直接实体生命周期。 | focused tests | complete / focused-pass |
| `P6 Regression Smoke` | 确认更广空战和 world-batch 行为没有被意外改写。 | P5 聚焦 lane 通过。 | 维护中的 smoke lane 全绿，且相邻 engagement/facade/binding 测试全绿。 | tests only | complete / broad-pass |
| `P7 Acceptance` | 同步文档、父级导航、残余和 archive 边界。 | P6 完成或 residual 被明确保留。 | 验收包说明 MLF-7 证明了什么，并把剩余内容明确后置到 MLF-8/9/10。 | docs only | complete |

## 任务簇

- 任务簇计划：
  [missile_lethality_secondary_consequence_coupling_task_clusters_20260618.zh.md](missile_lethality_secondary_consequence_coupling_task_clusters_20260618.zh.md)
- 当前状态：
  [missile_lethality_secondary_consequence_coupling_current_status_20260618.zh.md](missile_lethality_secondary_consequence_coupling_current_status_20260618.zh.md)
- 后果盘点：
  [missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.zh.md](missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.zh.md)
- 耦合契约：
  [missile_lethality_secondary_consequence_coupling_contract_20260618.zh.md](missile_lethality_secondary_consequence_coupling_contract_20260618.zh.md)
- 派发队列：
  [missile_lethality_secondary_consequence_coupling_dispatch_queue_20260618.zh.md](missile_lethality_secondary_consequence_coupling_dispatch_queue_20260618.zh.md)
- 验收门：
  [missile_lethality_secondary_consequence_coupling_acceptance_20260618.zh.md](missile_lethality_secondary_consequence_coupling_acceptance_20260618.zh.md)

## 输出和证据

当前输出：

- P1 inventory，覆盖当前事实输入、后果写入候选和注册顺序约束。
- P2 coupling contract，覆盖每个断裂模式和 loss-state 升级条件。
- P3 runtime bridge，通过
  [structural_consequence_system.h](../../../../../../../src/systems/combat/structural_consequence_system.h)
  消费 `StructuralBreakupState`。
- P4 事件诊断，将结构断裂父事件关联到带 before/after 后果 delta 的
  `platform_consequence` 记录。
- P5 聚焦 C++ 测试和 `structural_consequence` CTest lane。
- P6 更广 runtime smoke 证据：
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
  -> 447 passed。
- 相邻 event/facade/binding/tool 证据：
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py`
  -> 160 passed。
- P7 acceptance package，已将 residual 明确后置到 MLF-8、MLF-9 和 MLF-10。

剩余输出只属于后续阶段：MLF-8 残骸/碎片生命周期、MLF-9 Pk / 统计趋势投影、
MLF-10 校准门。

## 验收门

本子项目已按工程代理 MLF-7 切片验收，原因是：

- MLF-6 accepted / archived 证据仍作为上游事实来源可用。
- P1 inventory 和 P2 coupling contract 完成并内部链接一致。
- 如有 runtime 改动，必须消费 MLF-6 事实并且只写入批准的后果表面。
- 聚焦测试证明每个断裂模式产生预期的有边界后果，no-breakup case 保持不变。
- 更广 air_combat/world_batch smoke 仍然全绿，或 residual 记录为 MLF-7 范围外。
- 文档继续拒绝残骸/碎片生命周期、Pk 权威、武器专用校准和真实世界杀伤声明。

## 残余和下一步

后续：

- MLF-8：从 `detached_part_ref` 标签建立残骸/碎片生命周期。
- MLF-9：Pk / 统计趋势投影。
- MLF-10：特定武器/平台校准门。

后置：

- 海军和地面结构后果模型。
- 维护中平台损伤生命周期之外的直接坠毁/删除规则。

## 归档

MLF-7 已物理移动到父级 A2 本地归档，并登记在
`git show 095fdd5c:docs/task/review/archive/phase3c_closeout_20260808/archive_registry.zh.md`。
