# A2 MLF-4 当前状态

状态：`2026-06-10` active planning。MLF-4 已作为独立连续杆/切割子项目存在；`MLF-4A-X1` 只读盘点已验收，尚无 implementation slice 被验收。

英文辅文：[missile_lethality_continuous_rod_current_status_20260610.md](missile_lethality_continuous_rod_current_status_20260610.md)

## 本次变化

- 创建独立于已归档 MLF-2 和 MLF-3 的 MLF-4 planning surface。
- 记录当前代码已经有可复用 rod/cut 字段和候选 `continuous_rod` 分支。
- 通过主线程异常恢复复核验收 `MLF-4A-X1` 只读盘点包。
- 保持部件失效、结构解体、残骸、Pk 和真实弹种校准在本阶段之外。

## 成熟度矩阵

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 子项目文档 | active planning | README、任务簇、当前状态、派发队列、archive index | 不是 runtime acceptance |
| 4A 只读盘点 | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.zh.md](missile_lethality_continuous_rod_inventory_20260610.zh.md) | 只证明盘点完成，不证明 runtime 行为已验收 |
| 现有 rod 字段 | reusable scaffold | 标准事件和 effects 记录里的 `rod_cut_margin` 字段 | 语义尚未被 MLF-4B 验收 |
| 现有 continuous_rod 行为 | candidate scaffold | default effects `continuous_rod` 分支和历史测试 | 历史测试仅为 retained scaffold |
| 标准 rod 事件面 | ready for dispatch | 4B cluster | 未实现/未验收 |
| 通用 rod 几何 | planned | 4C cluster | 没有真实弹种参数 |
| 部件切割投影 | planned | 4D cluster | 不做部件失效概率 |
| 诊断和 gate | planned | 4E cluster | 不做击毁/坠毁/结构结论 |

## 残余登记

- 需要在 4B 中固定现有 `rod_cut_margin` 字段的标准事件语义；4A 建议先复用现有字段，暂不新增事件。
- 需要把 MLF-4 聚焦测试和历史 Phase 3 retained scaffold 测试分开。
- 需要对正 rod/cut 事实建立未起爆和非 rod guard。

## 建议行动顺序

1. 派发 `MLF-4B-W1 Standard Rod Event Surface`。
2. 先决定事件面形状，再改 runtime 逻辑。
3. 先验证通用 rod 几何，再做部件投影。
4. 标准事件面稳定后再加诊断和 guard 测试。
5. MLF-4 只按切割事实链收口，不按失效或解体收口。

## 禁止过度声明

- 不因 `rod_cut_margin` 为正就声明目标被切断。
- MLF-5 之前不声明部件失效。
- MLF-6 之前不声明结构解体。
- MLF-8 之前不声明残骸/wreck。
- 后续校准门之前不声明 Pk 或真实 AIM-120C/MQ-9 杀伤结论。
