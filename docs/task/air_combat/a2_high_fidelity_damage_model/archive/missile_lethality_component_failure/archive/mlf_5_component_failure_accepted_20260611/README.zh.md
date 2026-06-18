# A2 MLF-5 目标部件脆弱性与失效

状态：`2026-06-11` MLF-5 目标部件脆弱性与失效事实链 accepted / archived。MLF-5A 只读盘点、MLF-5B 标准部件损伤事件面、MLF-5C 通用部件失效概率、MLF-5D 部件状态交接、MLF-5E 诊断/gate 与 MLF-5F 收口归档已验收。本证据包不声明结构解体、坠毁、残骸、Pk 或具体弹种杀伤结论。

语言：

- 英文辅文：[README.md](README.md)
- 中文主文：`README.zh.md`

输入：

- A2 指针：[../../../README.zh.md](../../../README.zh.md)
- MLF-1 链路合同归档：[../../../missile_lethality_model_foundation/README.zh.md](../../../missile_lethality_model_foundation/README.zh.md)
- MLF-3 战斗部载荷归档：[../../../missile_lethality_warhead_effects/README.zh.md](../../../missile_lethality_warhead_effects/README.zh.md)
- MLF-4 连续杆/切割事实归档：[../../../missile_lethality_continuous_rod/README.zh.md](../../../missile_lethality_continuous_rod/README.zh.md)
- 事件合同入口：[../../../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../../src/runtime/contracts/engagement_contracts.h)
- 效果模型结果入口：[../../../../../../../src/core/interfaces/effects_model.h](../../../../../../../../src/core/interfaces/effects_model.h)
- 默认部件失效候选实现：[../../../../../../../src/models/weapons/detail/default_effects_system_effect_detail.inc](../../../../../../../../src/models/weapons/detail/default_effects_system_effect_detail.inc)
- 空战损伤传播入口：[../../../../../../../src/systems/combat/damage_system_air.h](../../../../../../../../src/systems/combat/damage_system_air.h)

## 目的

MLF-5 回答“某个部件收到了载荷或切割曝光以后，这个部件是否受损、以什么方式受损、状态变化有多大”。它消费 MLF-3 的部件受载事实和 MLF-4 的 rod/cut 切割曝光事实，输出部件级的失效概率、随机样本、失效模式、严重度、完整度前后值和证据来源。

本阶段不单独判断“飞机还能不能飞”。如果发动机、液压、控制面、传感器、燃油或灭火系统被损坏，影响应通过现有 `ComponentDamageState`、`AircraftDamageState`、飞行动力学、推进和传感器系统传播。MLF-5 不写直接坠毁规则，也不把一次部件失效直接变成实体删除。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| MLF-3 部件受载 | accepted / archived | MLF-3 证据包 | 只说明部件受到了什么载荷，不判断失效 |
| MLF-4 切割曝光 | accepted / archived | MLF-4 证据包 | 只说明切割曝光，不判断部件是否坏掉 |
| `ComponentDamageEvent` | accepted writer and diagnostics surface | `engagement_contracts.h` 已定义 component before/after、failure mode、probability/sample；5B 已补齐 writer/export/focused tests；5D 已把 before/after 连接到真实受载行；5E 已接入诊断事实表 | 不输出坠毁、解体、残骸或 Pk |
| 现有效果模型 | accepted MLF-5C/5D surface | `EffectsResult`、`ComponentMechanismLoadRow`、默认效果细节已有 failure probability、sample、evidence、primary integrity、redundancy 和 before/after 字段 | 仍不是结构解体、坠毁、残骸或 Pk 模型 |
| 损伤传播 | active maintained runtime | `damage_system_air.h` 已把部件/飞机损伤传播到控制、液压、推进、传感器、燃油和飞行性能 | MLF-5 只负责把部件失效状态交过去，不重新定义飞行动力学 |
| 历史测试 | retained scaffold | `weapon_guidance_realism/component_damage.py`、`vulnerability_authority.py`、`vulnerability_scaffold.py` | 未拆入本阶段聚焦测试的历史测试仍只作脚手架，不作为验收证据 |
| MLF-5A 盘点 | accepted | [missile_lethality_component_failure_inventory_20260611.zh.md](missile_lethality_component_failure_inventory_20260611.zh.md) | 只验收字段/候选实现/缺口盘点，不验收 runtime |
| MLF-5B 标准事件面 | accepted | `ComponentDamageEvent` recorder / store / export；`test_component_damage_event_surface.py` | 只在样本触发时导出部件损伤事件；不改变概率模型、状态 handoff 或诊断 |
| MLF-5C 通用失效概率 | accepted | `test_component_failure_probability_surface.py`；`default_effects_system_effect_detail.inc` | 通用、未校准、可替换；不等于真实弹种 Pk |
| MLF-5D 状态前后值 | accepted | `ComponentMechanismLoadRow` before/after 字段；`test_component_damage_event_surface.py` | 暴露已有状态写入结果，不单独判断飞机是否坠毁 |
| MLF-5E 诊断和禁止声明 | accepted | `air_combat_weapon_employment_process_probe.py`；`test_diagnostics_probe_contracts.py` | 解释部件损伤事实，不把部件损伤提升为坠毁/解体/Pk |

## 范围

纳入：

- 盘点已有部件失效概率、失效模式、证据标签、冗余组和完整度字段。
- 稳定 `ComponentDamageEvent` 或等价标准事件面，使每个受影响部件有可诊断的前后状态。
- 将 MLF-3/MLF-4 的载荷事实转换成通用、未校准、可替换的部件失效概率。
- 记录失效模式，例如控制、液压、推进、传感器、燃油、火灾/烟热、结构局部削弱等部件级影响。
- 将部件状态写入已有损伤状态，让现有飞行动力学和系统模型自然传播后果。
- 保持证据等级：通用工程假设、测试合成、公开/代理数据、未校准数据必须清楚标注。

不纳入：

- 不做结构解体、机体断裂、空中碎裂；这些属于 MLF-6。
- 不做残骸/wreck 或碎片生命周期；这些属于 MLF-8。
- 不做 Pk、训练胜负或实体删除；这些属于后续统计/消费层。
- 不校准真实 AIM-120C/MQ-9 或任何具体弹种/目标组合。
- 不写“若某部件坏了则直接坠毁”的捷径规则。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `MLF-5A Boundary And Inventory` | 固定范围，盘点已有字段、候选实现、历史测试和缺口 | MLF-4 archived | 当前状态记录可复用字段和缺口 | accepted |
| `MLF-5B Component Damage Event Surface` | 稳定部件损伤标准事件 | 5A accepted | live 路径能写出同链路 `ComponentDamageEvent` 或等价标准行 | accepted |
| `MLF-5C Generic Vulnerability Probability` | 建立通用部件失效概率模型和证据标签 | 5B accepted | 概率随载荷、切割曝光、部件脆弱性、冗余和方位变化 | accepted |
| `MLF-5D Component State Handoff` | 把部件失效写入已有损伤状态 | 5C accepted | 标准事件能导出真实 `integrity_before` / `integrity_after`，并保持已有损伤状态传播 | accepted |
| `MLF-5E Diagnostics And Gates` | 诊断解释部件失效且保护禁止声明 | 5B-D pass | probe 能输出部件损伤行，且不声明坠毁/解体/Pk | accepted |
| `MLF-5F Acceptance And Archive Prep` | 汇总 accepted/held 状态并同步索引 | 5B-E pass | README/status/task cluster/dispatch/archive 一致 | accepted |

## 任务簇

- 任务簇计划：[missile_lethality_component_failure_task_clusters_20260611.zh.md](missile_lethality_component_failure_task_clusters_20260611.zh.md)
- 当前状态：[missile_lethality_component_failure_current_status_20260611.zh.md](missile_lethality_component_failure_current_status_20260611.zh.md)
- 派发队列：[missile_lethality_component_failure_dispatch_queue_20260611.zh.md](missile_lethality_component_failure_dispatch_queue_20260611.zh.md)
- 收口验收：[missile_lethality_component_failure_acceptance_20260611.zh.md](missile_lethality_component_failure_acceptance_20260611.zh.md)
- 扩大方位/距离矩阵：[missile_lethality_component_failure_expanded_matrix_20260611.zh.md](missile_lethality_component_failure_expanded_matrix_20260611.zh.md)

## 输出和证据

预期输出：

- 已验收的只读盘点，列出可复用字段、候选实现和不能直接提升的历史测试。
- 标准部件损伤事实：部件名、系统、冗余组、完整度前后值、失效概率、样本、失效模式、严重度和证据来源。
- 通用部件失效概率模型，输入来自 MLF-3/MLF-4 的受载和切割事实，而不是单一扣血。
- 与已有损伤传播系统的对接证据，证明部件状态变化会通过已有飞行/系统模型传递。
- 诊断行能解释“哪个部件为什么坏、坏到什么程度”，但不直接说目标坠毁或解体。

## 验收门

本子项目只有在以下条件满足后才能标记为 accepted：

- 起爆后的 component-load / rod-cut 事实可以产生同链路的部件损伤事实。
- 部件损伤事实包含概率、样本、失效模式、完整度前后值和证据标签。
- 非受载、未起爆或无正载荷路径不会合成虚假部件失效。
- 部件状态能传给已有损伤/飞行系统，而不是 MLF-5 自己判断飞行是否还能维持。
- 结构解体、残骸、Pk、训练胜负和真实弹种杀伤结论继续 held。

## 残余和下一步

- MLF-5B 已闭合标准部件损伤事件面；5C/5D/5E 已由主线程本地推进并验收。
- 5C 已追加通用近炸概率重标定：理想近炸主受影响部件进入约三分之一的概率量级，远距/弱载荷仍显著更低；连续杆擦过关键部件时也进入可观察概率，而不是落回几乎为零。该估算仍是未校准脚手架，不是 Pk 或真实弹种数据。
- 35 m 配置下的边界观测：爆破/破片有效投影约 15.75 m，连续杆有效投影约 11 m。侧向良好暴露时，爆破/破片 y=6 m 为 `0.351680`、y=10 m 为 `0.006144`、y=22 m 无投影；连续杆 y=6 m 为 `0.347818`、y=12 m 为 `0.015949`、y=16 m 无投影。直接命中仍显著更高，例如连续杆 y=4.1 m 为 `0.555924`。
- 多种子场景统计已补做：修复前调试命中接口把合成导弹随机种子固定为常数，导致“理论概率变化、实际抽样不变”的假象；修复后 256 种子 sweep 显示连续杆直接右翼触发率 `0.546875`，良好侧向近炸任意部件触发率 `0.527344`，中等侧向 `0.359375`，边缘 `0.015625`，越界 `0.000000`。爆破/破片良好侧向近炸任意部件触发率 `0.644531`，中等侧向 `0.128906`，边缘 `0.015625`，越界 `0.000000`。
- 扩大方位/距离矩阵已补测：爆破/破片在鼻向、尾向、上下方都有明显响应，并随距离下降；连续杆对侧向、上下方和斜向更敏感，非直接轴向掠过接近无效，例如 nose 8 m 为 `0.000003`、tail 8 m 为 `0.037570`，而 top 6 m 为 `0.351680`、right-high 8 m 为 `0.262566`。这说明模型已经能区分方位和距离，而不是只按距离扣同一个概率。热力图中的灰格表示未设置/不适用场景，不代表 0；`D` 表示直接命中，不能和普通近炸点按同一条距离曲线读。
- 针对热力图异常已补验：连续杆鼻向 4 m 是非直接擦边，失效率 `0.000000`；鼻向 6 m 是直接命中，失效率 `1.000000`，不是几何穿模。爆破/破片尾向 6 m 直接命中先前会比 8 m 普通近炸更弱，现已用直接命中载荷下限修正，尾向 6 m 主部件概率 `0.686314`、任意部件触发率 `0.703125`，不再低于尾向 8 m 普通近炸。
- 5D 已补齐精确的 `integrity_before` / `integrity_after` 捕获：值来自同一次受载行的实际状态写入前后，不伪造前后值。
- 5E 已把 `component_damage` 加入诊断链路 schema v2，并验证未抽样触发时不会生成虚假部件损伤阶段。
- 5F 已完成收口和归档准备；当前 [../../README.zh.md](../../README.zh.md) 只保留轻量归档指针。
- MLF-6 将消费 MLF-5 的部件失效输出，建立结构解体/机体断裂。
- MLF-8 将消费 MLF-6 的结构结果，建立残骸和碎片对象生命周期。
- MLF-9 将消费可回放的高细节链路，处理 Pk/统计趋势。

## Archive

归档索引：[../README.zh.md](../README.zh.md)

本证据包只证明目标部件脆弱性与失效事实链；不证明结构解体、残骸、Pk、坠毁或具体弹种杀伤结论。
