# MLF-8 当前状态

状态：`2026-06-19` accepted / archived。P0 setup、P1 inventory、P2 lifecycle
contract、P3 focused runtime representation、P4 diagnostics/facade exposure、
P5 focused validation、P6 broader smoke 和 P7 acceptance/archive 均已完成；
验收范围是 diagnostics-only MLF-8 切片。

英文规范页：
[missile_lethality_debris_wreck_lifecycle_current_status_20260619.md](missile_lethality_debris_wreck_lifecycle_current_status_20260619.md)。

## 摘要

MLF-8 已承接 MLF-6、MLF-7 和 A8 明确后置的残骸/碎片生命周期工作。
P1 确认第一版 runtime 切片应是很薄的生命周期事件层，而不是新的飞机毁伤模型。
P2 接受 `LifecycleTransitionEvent` 作为基础载体，并禁止基础切片创建一等
debris/wreck 实体。P3 已增加 diagnostics-only lifecycle event 写入和 reward non-leakage。
P4/P5 已通过 facade/binding/diagnostic 表面暴露这些行，并覆盖已验收生命周期验证路径。
P6 broader smoke 已通过，P7 已完成验收和物理归档。

## 状态表

| 区域 | 状态 | 证据 | 下一步 |
| --- | --- | --- | --- |
| 子项目壳层 | complete / archived | README、任务簇、契约表面、派发队列、acceptance record、archive 占位和父级导航存在 | 通过 registry 保持同步 |
| 上游事实 | complete / inventory-pass | MLF-6 `StructuralBreakupEvent` 和 MLF-7 diagnostics-only `PlatformConsequenceEvent` 可复用 | 已被 accepted contract 消费 |
| Runtime 表达 | complete / focused-pass | recorder/store lifecycle writer 已存在；structural breakup 会写 detached-part lifecycle rows；链路关联 terminal wreck helper 会写 diagnostics-only terminal rows | accepted base slice |
| 生命周期事件 | complete / focused-pass | runtime 可发出 diagnostics-only detached-part lifecycle rows，并支持 terminal wreck rows；不 spawn entity | 纳入 acceptance evidence |
| Diagnostics/facade 暴露 | complete / focused-pass | facade packet 会 append/sort lifecycle rows；binding/contract shape 覆盖 terminal 字段；diagnostics probe 会投影 `LifecycleTransitionEvent` rows 和 snapshot 字段 | accepted base slice |
| Validation | complete / focused-pass | 聚焦 C++/Python lane 覆盖 no-breakup、单部件和 multi-axis detached-part lifecycle rows、terminal wreck helper、facade/binding/probe 暴露和 reward non-leakage | accepted base slice |
| Reward 边界 | complete / focused-pass | reward 在 terminal/reward projection 前忽略 diagnostics-only lifecycle transition events | 纳入 acceptance evidence |
| Broader smoke | complete / smoke-pass | Full CTest 通过；focused P4/P5 lanes 通过；geometry/edge smoke 通过；broader air-combat+engagement smoke 通过 | 已记录到 acceptance |
| 校准权威 | refused | Debris evidence gates 仍 fail-closed | 保持在 MLF-8 验收之外 |

## 推荐下一步

1. 将 MLF-9 Pk / 统计趋势投影和 MLF-10 校准门保持为独立 follow-on 子项目。
2. 只有在明确限定范围时才重开 MLF-8 follow-on，例如一等 debris entity contract、
   debris-to-secondary-damage interaction 或可视化碎片渲染。

## 当前风险

- 未来工作可能混淆原实体退役和一等残骸/碎片对象。
- 如果未来不经新契约提升 visibility，diagnostics-only lifecycle facts 不应进入 reward shaping。
- 未来工作可能把 `detached_part_ref` 标签误当作校准碎片物理。
- 未来工作可能继续修改已归档 MLF-6 或 MLF-7，而不是消费其 accepted outputs。
- 未来工作可能通过新 lifecycle 行重复计算已有 ground-crash reward 行为。

## 保留项

- Pk / 统计投影：MLF-9。
- 校准和 selected debris-output 证据准入：MLF-10 或后续阶段。
- 可视化碎片渲染：未来 visual/runtime 工作。
