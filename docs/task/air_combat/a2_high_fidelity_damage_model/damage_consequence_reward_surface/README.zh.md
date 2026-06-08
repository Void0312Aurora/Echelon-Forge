# A2 损伤后果奖励面想法

状态：`2026-06-08` idea seed / held。本文只记录方向，暂不展开为实现、派发或验收包。

语言：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- A2 指针：[../README.zh.md](../README.zh.md)
- A2 封存包：[../../archive/a2_high_fidelity_damage_model/README.zh.md](../../archive/a2_high_fidelity_damage_model/README.zh.md)
- A8 损伤效果链：[../../a8_damage_effect_chain/README.zh.md](../../a8_damage_effect_chain/README.zh.md)
- 空战当前入口：[../../README.zh.md](../../README.zh.md)

## 目的

记录一个后续方向：空战训练不应只等待 `kill` 或目标实体 inactive。更有训练价值的信号可能来自“造成了什么后果”：任务系统下降、传感/数据链下降、机动能力下降、燃油泄漏、火灾扩大、失控下降、触地或坠毁。

该方向放在 A2 下，而不是新建 A9，因为它首先是毁伤模型保真度与后果解释的问题，其次才是训练 reward 设计问题。本文不启动实现，不声明验收，不把 A8 的有边界效果链升级为 stock AIM-120C / MQ-9 杀伤权威。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A2 高真实度毁伤模型 | archived / sealed | A2 archive 保留 research/candidate 证据 | 不释放 Pk、deterministic fuze 或 stock weapon-outcome authority |
| A8 损伤效果链 | accepted bounded slice | 起爆后可观察具体部件损伤和维护中系统响应 | 不增加直接坠毁规则、MQ-9 特例击杀规则或碎片/残留对象 |
| 当前训练反馈 | suspected too narrow | 非终局损伤能给少量进度奖励；延迟火灾、触地、坠毁等后果尚未作为主反馈面 | 不能把旧 `Health` 或单个 `kill` flag 当作完整杀伤链评价 |

## 范围

暂定纳入：

- 只记录“按后果分层奖励”的想法。
- 将后续问题定位为 A2 的 research / calibration / consequence-fidelity follow-on。
- 保留后续可展开的最小 witness：例如 MQ-9 / AIM-120C-like 的 synthetic training calibration、连续后果观测和 reward surface。

暂不纳入：

- 不新增代码、场景、训练配置或 reward 权重。
- 不创建 A9。
- 不重开已封存的 A2 archive 包。
- 不声明真实 Pk、真实引信、真实 AIM-120C 杀伤或 MQ-9 特例击杀。
- 不用“直接坠毁规则”替代损伤链。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Idea Seed` | 固定问题位置和边界 | 当前讨论 | 本 README 存在并链接到 A2 指针 | held |
| `P1 Boundary` | 若后续明确展开，定义可奖励后果、观测字段和禁止声明 | 用户明确要求展开 | 形成 task cluster 文档 | not started |
| `P2 Evidence` | 验证延迟后果是否稳定可观测 | P1 完成 | 固定最小 witness 和诊断脚本 | not started |
| `P3 Reward Surface` | 设计训练奖励面 | P2 完成 | 有测试和训练配置候选 | not started |

## 输出和证据

- 当前唯一输出是本 idea seed README。
- 暂无 task cluster、dispatch、实现或验收记录。

## 验收门

本文不能被标记为 accepted。若未来展开，至少需要先证明：

- 损伤后果字段能稳定观测，且不依赖旧 `Health` 作为主真值。
- 不同后果的 reward 权重不会鼓励明显虚假的仿真漏洞。
- training synthetic calibration 与真实武器/目标 authority 明确分离。
- A2/A8 已封存或已验收边界不被误写成更高权威。

## 残余和下一步

- 是否将该 idea seed 升级为完整 A2 follow-on，由后续明确请求决定。
- 若升级，应先补 task cluster 文档，而不是直接改 reward。
- 最可能的第一步是“连续后果观测诊断”：把任务/机动/传感/生存能力、飞机内部损伤、燃油/火灾、触地生命周期和 inactive 变化放到同一张验收表中。

## Archive

若该方向被展开，本文应升级或被新的 current-status / task-cluster 文档替代；若放弃，则作为 held idea seed 移入 A2 局部 archive。
