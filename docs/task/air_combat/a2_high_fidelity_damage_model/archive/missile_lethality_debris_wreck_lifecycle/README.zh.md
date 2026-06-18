# MLF-8 残骸和碎片生命周期

状态：`2026-06-19` accepted / archived。P0 边界、P1 盘点、P2 生命周期契约、
P3 runtime 表达、P4 诊断/facade 暴露、P5 聚焦验证、P6 broader smoke 和
P7 acceptance/archive 均已完成；验收范围是有边界的 diagnostics-only MLF-8 切片。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- A2 follow-on 父索引：[../../README.zh.md](../../README.zh.md)
- MLF-6 结构失效事实写入器：
  [../missile_lethality_structural_failure/README.zh.md](../missile_lethality_structural_failure/README.zh.md)
- MLF-7 二次后果耦合：
  [../missile_lethality_secondary_consequence_coupling/README.zh.md](../missile_lethality_secondary_consequence_coupling/README.zh.md)
- A8 损伤效果链：
  [../../../archive/a8_damage_effect_chain/README.zh.md](../../../archive/a8_damage_effect_chain/README.zh.md)
- 子项目创建标准：
  [../../../../../agent/rules/subproject_creation_standard.zh.md](../../../../../agent/rules/subproject_creation_standard.zh.md)
- 真实性权威边界：
  [../../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../../standards/foundation/realism_authority_boundary.zh.md)
- 结构断裂状态和事件字段：
  [../../../../../../src/components/combat/structural_failure.h](../../../../../../src/components/combat/structural_failure.h)、
  [../../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../src/runtime/contracts/engagement_contracts.h)
- 地面撞击生命周期和当前 active-state API：
  [../../../../../../src/components/systems/logistics.h](../../../../../../src/components/systems/logistics.h)、
  [../../../../../../src/core/engine/simulation_kernel_observation_api.cpp](../../../../../../src/core/engine/simulation_kernel_observation_api.cpp)

## 目的

MLF-8 是 Missile Lethality Framework 的第八阶段。它把之前后置的“脱落部件”
以及终端残骸/碎片问题，整理成一个可恢复、可派发、可验收的有边界执行面。

MLF-6 记录哪个结构部件脱落。MLF-7 将这种断裂投影到维护中的 aircraft damage、
platform damage、loss state 和诊断。MLF-8 继续回答下一层问题：如何把脱落部件标签
和终端机体表达为生命周期事实、残骸记录或碎片记录，同时不声明真实碎片抛散、Pk
或库存武器杀伤权威？

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 结构断裂事实 | accepted 上游输入 | MLF-6 已提供 `StructuralBreakupEvent.detached_part_ref`、`detached_part_count`、`break_mode` 和 `airframe_breakup` | 这些标签仍只是事实，不是一等世界对象 |
| 二次后果桥接 | accepted 上游输入 | MLF-7 已写入有边界 aircraft/platform consequence state 和诊断 | MLF-7 明确保留一等残骸/碎片生命周期到 MLF-8 |
| 原目标终端生命周期 | active 维护行为 | 火油导致 lost 的飞机可在空中保持可观察，触地后退役；`is_unit_active()` 已跟随 `is_alive()` | 原实体退役不等于完整残骸/碎片对象模型 |
| 生命周期事件契约 | accepted / archived | `LifecycleTransitionEvent` 以 diagnostics-only visibility 承载脱落部件和 terminal-wreck lifecycle facts | 基础切片写 lifecycle facts，不创建一等 debris/wreck 实体 |
| 外部 debris 证据 | fail-closed retained material | 现有 TP-21/debris admission 工件是 hash/evidence gate，不是已放行校准数据 | 本子项目创建不释放 selected debris-output 权威 |

## 范围

范围内：

- 盘点现有结构断裂输出、终端飞机生命周期、地面接触状态、event-store 支持、Python
  绑定、facade 导出、诊断和 reward 消费者。
- 定义原机体退役、终端残骸事实、脱落部件碎片事实和未来可选碎片实体的生命周期契约。
- 决定 MLF-8 何时复用现有 `LifecycleTransitionEvent` 字段，何时需要新增内部组件或实体类型。
- 契约验收后，只实现有边界的脱落部件和终端残骸生命周期表达。
- MLF-8 lifecycle event 在后续训练或校准门明确提升之前保持 diagnostics-only。
- 增加 no-breakup、单脱落部件、多部件断裂、终端残骸、事件链路、active-state 语义和
  reward non-leakage 的聚焦测试。
- 同步父级 README、任务簇、当前状态、派发队列和验收记录。

范围外：

- 不做 Pk 或统计杀伤趋势，后置到 MLF-9。
- 不做真实碎片抛散分布、碎片射程或杀伤/损伤概率校准，后置到 MLF-10 或后续证据门。
- 不声明武器或飞机专用的权威碎片模型。
- 不重开已归档 MLF-1 到 MLF-7，除非修复上游事实 bug。
- 除非未来契约有意修改 `consumer_visibility`，MLF-8 诊断不产生训练 reward 权威。
- 不在本切片内建立海军或地面残骸生命周期模型。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 写入面 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `P0 Boundary` | 创建 MLF-8 子项目并冻结权威边界。 | 用户要求进入 MLF-8。 | README、任务簇、状态、派发队列、契约表面、archive 占位和父级导航存在。 | docs only | complete / link-pass |
| `P1 Inventory` | 盘点当前断裂、生命周期、事件、绑定、facade、reward 和诊断表面。 | P0 文档存在。 | inventory 标明可复用字段、缺口和禁止直接写入面。 | docs/tests docs | complete / inventory-pass |
| `P2 Lifecycle Contract` | 定义原机体、残骸、碎片和事件链语义。 | P1 完成。 | 契约表说明 producer、consumer、visibility 和验收检查。 | docs only | complete / contract-pass |
| `P3 Runtime Representation` | 实现有边界生命周期状态和事件写入。 | P2 验收。 | runtime 产生确定性生命周期事实，不引入 Pk、校准或 reward 泄漏。 | `src/**`、bindings、聚焦测试 | complete / focused-pass |
| `P4 Diagnostics And Facade` | 通过维护中的诊断/facade 表面检查 MLF-8 事实。 | P3 聚焦通过。 | recent events、facade packet 和 diagnostics probe 可导出链路关联 lifecycle 行。 | diagnostics/facade/tests | complete / focused-pass |
| `P5 Validation` | 验证 structural-to-lifecycle case 和零误报行为。 | P3/P4 完成。 | C++/Python 聚焦 lane 覆盖每条验收生命周期路径。 | tests | complete / focused-pass |
| `P6 Regression Smoke` | 确认空战、reward 和训练表面没有被意外改写。 | P5 通过。 | 维护 smoke lane 仍绿，diagnostics-only facts 不进入 reward。 | tests only | complete / smoke-pass |
| `P7 Acceptance` | 记录 accepted/held 声明和 archive 边界。 | P6 通过或 residual 明确保留。 | 验收页和父级索引说明 MLF-8 精确证明范围和后置到 MLF-9/10 的内容。 | docs only | complete |

## 任务簇

- 任务簇计划：
  [missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.zh.md)
- 当前状态：
  [missile_lethality_debris_wreck_lifecycle_current_status_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_current_status_20260619.zh.md)
- 盘点：
  [missile_lethality_debris_wreck_lifecycle_inventory_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_inventory_20260619.zh.md)
- 生命周期契约：
  [missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md)
- 派发队列：
  [missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.zh.md)
- 验收门：
  [missile_lethality_debris_wreck_lifecycle_acceptance_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_acceptance_20260619.zh.md)

## 输出和证据

已验收输出：

- 当前 accepted / archived MLF-8 evidence packet。
- 带 round cap 的有限任务簇列表。
- P1 对可复用和缺失 lifecycle 表面的盘点。
- 生命周期契约，保持 MLF-8 诊断与 reward/Pk 权威分离。
- P3 聚焦实现：为脱落部件和链路关联终端残骸事实写入 diagnostics-only lifecycle event。
- P4/P5 聚焦诊断和验证覆盖：facade packet export、Python binding/contract shape、
  diagnostics probe rows、no-breakup 行为、单部件和 multi-axis detached-part lifecycle rows、
  terminal wreck rows 以及 reward non-leakage。
- P6 broad smoke 证据：
  `ctest --test-dir build-workshop --output-on-failure` -> 6 passed；
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat tests/runtime/engagement`
  -> 386 passed。
- P7 验收包，明确 accepted lifecycle claims 和保留 MLF-9/MLF-10 后置项。
- A2 和 air-combat 父级导航更新，以及 archive registry 同步。

## 验收门

本子项目已按 diagnostics-only MLF-8 切片验收，因为：

- 脱落部件和终端残骸生命周期语义已有文档和测试。
- runtime lifecycle facts 与上游 structural/consequence 证据链路关联。
- 原实体在 terminal loss 后的 active-state 语义保持正确。
- MLF-8 诊断默认不产生训练 reward term。
- 父级索引和 archive registry 边界保持同步。
- Pk、真实碎片抛散、selected TP-21 output 权威和 weapon-specific lethality 继续被拒绝。

## 残余和下一步

计划中的后续：

- MLF-9：Pk / 统计趋势投影。
- MLF-10：特定武器/平台校准门和被准入的 debris 证据。

MLF-8 内暂时保留：

- 超过简单生命周期表达的一等碎片物理。
- 碎片对其他目标的二次损伤。
- 可视化碎片渲染或粒子系统。

## 归档

MLF-8 已物理归档到 A2 父级本地 archive 下，并登记在
[../../archive_registry.zh.md](../../archive_registry.zh.md)。原 active 路径现在只保留
轻量指针。本地 [archive/](archive/README.zh.md) 目录只用于此归档证据包内部未来
可能出现的 superseded records。
