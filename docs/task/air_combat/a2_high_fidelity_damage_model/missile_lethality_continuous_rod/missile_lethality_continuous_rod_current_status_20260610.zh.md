# A2 MLF-4 当前状态

状态：`2026-06-11` active planning。MLF-4 已作为独立连续杆/切割子项目存在；`MLF-4A-X1`、`MLF-4B-W1-R2`、`MLF-4C-W1` 与 `MLF-4D-W1` 已验收。`MLF-4E-W1` 可派发。

英文辅文：[missile_lethality_continuous_rod_current_status_20260610.md](missile_lethality_continuous_rod_current_status_20260610.md)

## 本次变化

- 创建独立于已归档 MLF-2 和 MLF-3 的 MLF-4 planning surface。
- 记录当前代码已经有可复用 rod/cut 字段和候选 `continuous_rod` 分支。
- 通过主线程异常恢复复核验收 `MLF-4A-X1` 只读盘点包。
- 主线程本地复验后，验收 `MLF-4B-W1-R2` test-first 标准事件面。
- 主线程本地复验后，验收 `MLF-4C-W1` 通用 rod 几何。
- 主线程本地复验后，验收 `MLF-4D-W1` 部件切割投影。
- 保持部件失效、结构解体、残骸、Pk 和真实弹种校准在本阶段之外。

## 成熟度矩阵

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 子项目文档 | active planning | README、任务簇、当前状态、派发队列、archive index | 不是 runtime acceptance |
| 4A 只读盘点 | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.zh.md](missile_lethality_continuous_rod_inventory_20260610.zh.md) | 只证明盘点完成，不证明 runtime 行为已验收 |
| 现有 rod 字段 | accepted standard event surface | 标准事件/effects 记录里的 `rod_cut_margin` 字段，以及 [test_mlf4_standard_rod_event_surface.py](../../../../../tests/runtime/air_combat/test_mlf4_standard_rod_event_surface.py) | 只验收切割事实，不验收失效 |
| 现有 continuous_rod 行为 | accepted for event-surface, generic-geometry, and component-projection slices | MLF-4B/4C/4D 聚焦测试与保留的历史测试 | 诊断和最终收口仍未完成 |
| 标准 rod 事件面 | accepted slice | `MLF-4B-W1-R2` 本地复验 | 没有新增事件字段或默认常量 |
| 通用 rod 几何 | accepted slice | [test_mlf4_generic_rod_geometry.py](../../../../../tests/runtime/air_combat/test_mlf4_generic_rod_geometry.py) | 没有真实弹种参数 |
| 部件切割投影 | accepted slice | [test_mlf4_component_cut_projection.py](../../../../../tests/runtime/air_combat/test_mlf4_component_cut_projection.py) | 不做部件失效概率或 integrity 修改 |
| 诊断和 gate | ready for dispatch | 4E cluster | 不做击毁/坠毁/结构结论 |

## 残余登记

- 需要由 4E 让诊断从标准事件解释 rod/cut 事实。

## 建议行动顺序

1. 派发 `MLF-4E-W1 Diagnostics And Gates`。
2. 让诊断解释标准 rod/cut 事实，且不产生虚假 rod 行。
3. MLF-4 只按切割事实链收口，不按失效或解体收口。

## 禁止过度声明

- 不因 `rod_cut_margin` 为正就声明目标被切断。
- MLF-5 之前不声明部件失效。
- MLF-6 之前不声明结构解体。
- MLF-8 之前不声明残骸/wreck。
- 后续校准门之前不声明 Pk 或真实 AIM-120C/MQ-9 杀伤结论。
