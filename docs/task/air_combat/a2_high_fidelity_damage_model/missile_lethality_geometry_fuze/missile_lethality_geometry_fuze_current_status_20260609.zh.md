# A2 MLF-2 当前状态

状态：`2026-06-09` MLF-2E accepted / MLF-2F next。`MLF-2B` 受控几何测试夹具已验收；`MLF-2C` 最近接近事件 writer 已验收；`MLF-2D` 引信评估事件 writer 已验收；`MLF-2E` 诊断投影已验收。下一步进入 runtime handoff gate 审计。

英文辅文：[missile_lethality_geometry_fuze_current_status_20260609.md](missile_lethality_geometry_fuze_current_status_20260609.md)

## 成熟度矩阵

| 区域 | 状态 | 证据 | 不能证明什么 |
| --- | --- | --- | --- |
| MLF-1 链路合同 | accepted / archived | [MLF-1 证据包](../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md) | 不证明几何/引信已经高保真 |
| MLF-2 子项目边界 | pass | README、任务簇、派发队列、archive 索引 | 不证明 runtime 已改 |
| 受控几何场景 | pass | `MLF-2B-X1` pass；`MLF-2B-W1` pass；主线程复验 2 个聚焦测试 | 不证明目标姿态全量可控 |
| 最近接近事件 | pass | `MLF-2C-X1` pass；`MLF-2C-W1` pass；主线程复验 `ef_py` 构建、3 个导弹几何/引信聚焦测试和 7 个 engagement event capture 回归 | 不证明引信触发、未触发、延迟和失败已标准化 |
| 引信评估事件 | pass | `MLF-2D-X1` pass；`MLF-2D-W1` pass；主线程复验 `ef_py` 构建、4 个导弹几何/引信聚焦测试和 7 个 engagement event capture 回归 | 不证明诊断 probe 已消费该事件 |
| 诊断投影 | pass | `MLF-2E-X1` pass；`MLF-2E-W1` pass；主线程复验 `tests/diagnostics/test_air_combat_process_probe.py -q` 17 个测试通过 | 不证明效果模型或奖励语义已变 |
| runtime handoff | planned / ready for audit | 任务簇 `MLF-2F` | 不证明未触发路径已被效果调用 gate 保护 |

## 当前结论

MLF-2 当前仍不是完整杀伤能力。任何“导弹应当击毁目标”“目标应当碎裂”“某弹种真实 Pk 如何”的表述都不在当前状态支持范围内。

当前可说的是：live missile 受控几何夹具已经可以不用训练策略发射而改变距离、闭合速度、方位和高度差；最近接近标准事件已经能从 live 路径写出，错过目标和未起爆路径也能记录最近点与原因。最近点时间已从“终端判定帧”修正为“实际刷新最近点的时间”。引信评估事件也已经能记录解保/触发、未触发和失败原因，并与同一枚弹的最近接近事件相连。诊断 probe 现在优先消费标准最近接近/引信评估事件，旧 `EffectsEvent` 投影只作为缺省回退。

## 下一步

1. 下一步派发 `MLF-2F-I1`，只读审计起爆状态和现有效果模型调用之间的 gate。
2. 审计通过后再决定是否实现 runtime handoff gate，不提前进入战斗部效果或击毁结论。

## 保持的边界

- 不进入破片/连续杆/结构解体。
- 不做 AIM-120C/MQ-9 个案结论。
- 不把引信触发等同于击毁。
- 不让训练 reward 反向制造杀伤事实。
