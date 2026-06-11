# A2 MLF-4 当前状态

状态：`2026-06-11` accepted / archived。MLF-4 已作为独立连续杆/切割子项目收口；`MLF-4A-X1`、`MLF-4B-W1-R2`、`MLF-4C-W1`、`MLF-4D-W1`、`MLF-4E-W1` 与 `MLF-4F-C1` 已验收。

英文辅文：[missile_lethality_continuous_rod_current_status_20260610.md](missile_lethality_continuous_rod_current_status_20260610.md)

## 本次变化

- 创建独立于已归档 MLF-2 和 MLF-3 的 MLF-4 planning surface。
- 记录当前代码已经有可复用 rod/cut 字段和候选 `continuous_rod` 分支。
- 通过主线程异常恢复复核验收 `MLF-4A-X1` 只读盘点包。
- 主线程本地复验后，验收 `MLF-4B-W1-R2` test-first 标准事件面。
- 主线程本地复验后，验收 `MLF-4C-W1` 通用 rod 几何。
- 主线程本地复验后，验收 `MLF-4D-W1` 部件切割投影。
- 主线程本地实现和复验后，验收 `MLF-4E-W1` 诊断和 gate。
- 主线程收口 `MLF-4F-C1`，归档 accepted/held 状态、测试证据和后续阶段边界。
- 保持部件失效、结构解体、残骸、Pk 和真实弹种校准在本阶段之外。

## 成熟度矩阵

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 子项目文档 | accepted / archived | README、任务簇、当前状态、派发队列、archive index、收口验收 | 只验收 MLF-4 切割事实链 |
| 4A 只读盘点 | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.zh.md](missile_lethality_continuous_rod_inventory_20260610.zh.md) | 只证明盘点完成，不证明 runtime 行为已验收 |
| 现有 rod 字段 | accepted standard event surface | 标准事件/effects 记录里的 `rod_cut_margin` 字段，以及 [test_continuous_rod_event_surface.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_event_surface.py) | 只验收切割事实，不验收失效 |
| 现有 continuous_rod 行为 | accepted for event-surface, generic-geometry, component-projection, diagnostic, and closeout slices | MLF-4B/4C/4D/4E 聚焦测试与收口验收 | 不直接声明失效或结构后果 |
| 标准 rod 事件面 | accepted slice | `MLF-4B-W1-R2` 本地复验 | 没有新增事件字段或默认常量 |
| 通用 rod 几何 | accepted slice | [test_continuous_rod_geometry_response.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_geometry_response.py) | 没有真实弹种参数 |
| 部件切割投影 | accepted slice | [test_continuous_rod_component_cut_projection.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_component_cut_projection.py) | 不做部件失效概率或 integrity 修改 |
| 诊断和 gate | accepted slice | [test_continuous_rod_diagnostic_projection.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py) | 不做击毁/坠毁/结构结论 |

## 残余登记

- MLF-5：消费 rod/cut 事实，建立部件失效概率。
- MLF-6：消费部件失效，建立结构解体。
- MLF-8/MLF-9：残骸生命周期和 Pk/统计趋势仍需后续独立子项目。

## 建议行动顺序

1. 不再在 MLF-4 内继续派发。
2. 如要进入部件失效，按 `docs/agent` 标准新建 MLF-5。
3. MLF-4 只按切割事实链归档，不按失效或解体归档。

## 禁止过度声明

- 不因 `rod_cut_margin` 为正就声明目标被切断。
- MLF-5 之前不声明部件失效。
- MLF-6 之前不声明结构解体。
- MLF-8 之前不声明残骸/wreck。
- 后续校准门之前不声明 Pk 或真实 AIM-120C/MQ-9 杀伤结论。
