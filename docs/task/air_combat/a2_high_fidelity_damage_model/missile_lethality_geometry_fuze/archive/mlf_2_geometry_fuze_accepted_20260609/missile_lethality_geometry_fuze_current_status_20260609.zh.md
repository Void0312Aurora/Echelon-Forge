# A2 MLF-2 当前状态

状态：`2026-06-09` MLF-2 accepted / archived。`MLF-2B` 受控几何测试夹具已验收；`MLF-2C` 最近接近事件 writer 已验收；`MLF-2D` 引信评估事件 writer 已验收；`MLF-2E` 诊断投影已验收；`MLF-2F` runtime handoff gate 已验收；`MLF-2G` 收尾归档已完成。

英文辅文：[missile_lethality_geometry_fuze_current_status_20260609.md](missile_lethality_geometry_fuze_current_status_20260609.md)

## 成熟度矩阵

| 区域 | 状态 | 证据 | 不能证明什么 |
| --- | --- | --- | --- |
| MLF-1 链路合同 | accepted / archived | [MLF-1 证据包](../../../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md) | 不证明几何/引信已经高保真 |
| MLF-2 子项目边界 | pass | README、任务簇、派发队列、archive 索引 | 不证明 runtime 已改 |
| 受控几何场景 | pass | `MLF-2B-X1` pass；`MLF-2B-W1` pass；主线程复验 2 个聚焦测试 | 不证明目标姿态全量可控 |
| 最近接近事件 | pass | `MLF-2C-X1` pass；`MLF-2C-W1` pass；主线程复验 `ef_py` 构建、3 个导弹几何/引信聚焦测试和 7 个 engagement event capture 回归 | 不证明引信触发、未触发、延迟和失败已标准化 |
| 引信评估事件 | pass | `MLF-2D-X1` pass；`MLF-2D-W1` pass；主线程复验 `ef_py` 构建、4 个导弹几何/引信聚焦测试和 7 个 engagement event capture 回归 | 不证明诊断 probe 已消费该事件 |
| 诊断投影 | pass | `MLF-2E-X1` pass；`MLF-2E-W1` pass；主线程复验 `tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q` 17 个测试通过 | 不证明效果模型或奖励语义已变 |
| runtime handoff | pass | `MLF-2F-I1` pass；`MLF-2F-W1` pass；主线程复验 3 个引信 gate 聚焦测试通过 | 不证明战斗部效果或结构解体已完成 |
| 验收收尾 | pass | 本归档包、当前指针 README、archive 索引和 A2/MLF-1 导航已同步 | 不证明 MLF-3+ 已完成 |

## 当前结论

MLF-2 已完成验收，但它仍不是完整杀伤能力。任何“导弹应当击毁目标”“目标应当碎裂”“某弹种真实 Pk 如何”的表述都不在当前状态支持范围内。

当前可说的是：live missile 受控几何夹具已经可以不用训练策略发射而改变距离、闭合速度、方位和高度差；最近接近标准事件已经能从 live 路径写出，错过目标和未起爆路径也能记录最近点与原因。最近点时间已从“终端判定帧”修正为“实际刷新最近点的时间”。引信评估事件也已经能记录解保/触发、未触发和失败原因，并与同一枚弹的最近接近事件相连。诊断 probe 现在优先消费标准最近接近/引信评估事件，旧 `EffectsEvent` 投影只作为缺省回退。runtime gate 已由测试钉住：触发路径才进入现有效果/损伤记录；接触近失没有效果/损伤记录；可靠性失败只有零伤害过渡记录。

## 后续路线

1. 本子项目已归档，不再继续派发。
2. 下一阶段应单独创建战斗部/作用机制子项目，不在 MLF-2 目录里追加。
3. 破片、连续杆、结构解体、残骸、Pk 和具体弹种结论继续保留为后续阶段。

## 保留缺口

- timed fuze 标准事件覆盖仍 held。
- max-flight-time / guidance expiry 仍缺 recorder access。
- 零伤害过渡 `EffectsEvent` / `DamageReport` 仍保留，后续删除需等下游消费面迁移。
- 更细目标姿态、延迟路径和 warhead-effect 机制仍在 MLF-3+。

## 保持的边界

- 不进入破片/连续杆/结构解体。
- 不做 AIM-120C/MQ-9 个案结论。
- 不把引信触发等同于击毁。
- 不让训练 reward 反向制造杀伤事实。
