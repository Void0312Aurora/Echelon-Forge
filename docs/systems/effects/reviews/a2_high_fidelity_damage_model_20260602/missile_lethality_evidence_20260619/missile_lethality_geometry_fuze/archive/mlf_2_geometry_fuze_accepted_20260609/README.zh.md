# A2 MLF-2 导弹接近几何与引信评估

状态：`2026-06-09` 已归档 / MLF-2 accepted。MLF-2B 受控几何、MLF-2C 最近接近事件、MLF-2D 引信评估事件、MLF-2E 诊断投影、MLF-2F runtime handoff gate 和 MLF-2G closeout 已验收。

语言：

- 英文辅文：[README.md](README.md)
- 中文主文：`README.zh.md`

输入：

- 当前 MLF-2 指针：[../../README.zh.md](../../README.zh.md)
- A2 指针：[../../../README.zh.md](../../../README.zh.md)
- MLF-1 归档指针：[../../../missile_lethality_model_foundation/README.zh.md](../../../missile_lethality_model_foundation/README.zh.md)
- MLF-1 已验收证据包：[../../../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md](../../../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md)
- A2 封存包：[../../../../archive/a2_high_fidelity_damage_model/README.zh.md](../../../../../archive/a2_high_fidelity_damage_model/README.zh.md)
- 武器生命周期入口：[../../../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp](../../../../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp)
- 武器和引信参数入口：`../../../../../../../src/components/combat/weapon.h`
- 事件合同入口：[../../../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../../src/runtime/contracts/engagement_contracts.h)
- 事件记录入口：[../../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp](../../../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)
- 诊断 probe 入口：[../../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py](../../../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py)

## 目的

MLF-2 的目标是把“导弹接近目标后发生了什么”拆成两个可解释步骤：第一，记录最近接近几何；第二，记录引信评估。给定距离、方位、闭合速度、高度差和目标姿态后，系统应能说明为什么触发、未触发、延迟触发或触发失败。

本子项目不直接回答 AIM-120C 打 MQ-9 会不会碎裂，也不直接给击毁结论。它只把起爆状态、起爆位置、触发原因和失败原因交给后续战斗部作用模型。破片、连续杆、结构解体、残骸对象、Pk 和具体弹种校准必须在后续独立子项目中处理。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| MLF-1 杀伤链合同 | accepted / archived | MLF-1 证据包已归档 | 只定义链路和消费边界，不实现几何/引信物理 |
| 当前近炸逻辑 | active legacy surface | 武器生命周期和效果事件已有近炸/命中字段 | 仍不能完整解释未触发、延迟、失败和接触/近炸差异 |
| MLF-2 子项目 | accepted / archived | 本 README、任务簇、状态、派发队列、`MLF-2B`/`MLF-2C`/`MLF-2D`/`MLF-2E`/`MLF-2F` 聚焦测试和 `MLF-2G` closeout | 已验收最近接近、引信评估、诊断投影和 runtime handoff gate；不含战斗部效果 |

## 范围

纳入：

- 构造受控接近场景或测试夹具，能固定距离、方位、闭合速度、高度差和目标姿态。
- 标准化 `NearestApproachEvent`：最近点时间、距离、目标局部坐标、相对速度、方位、置信度和失败原因。
- 标准化 `FuzeEvaluationEvent`：解保状态、触发类型、触发时间、触发/未触发/延迟/失败原因、接触判定和近炸判定。
- 让诊断输出能区分“没有起爆但有原因”和“没有事件”。
- 为默认引信半径、延迟、可靠性、目标签名等假设保留来源、证据等级和适用范围。

不纳入：

- 不实现破片、连续杆、爆风载荷、结构断裂、残骸对象或 Pk 层。
- 不把引信触发直接变成目标击毁。
- 不调 AIM-120C/MQ-9 个案杀伤阈值。
- 不新增 reward 规则来替代事件链事实。
- 不保留旧 `last_effect_*` 字段作为长期兼容面。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `MLF-2A Boundary` | 固定子项目目标、禁止声明和任务簇 | MLF-1 已归档 | README、状态、任务簇和父级导航存在 | pass |
| `MLF-2B Geometry Fixtures` | 设计受控接近场景 | MLF-2A | 能在测试中改变距离、方位、速度和姿态 | pass |
| `MLF-2C Nearest Approach` | 写入最近接近事件 | MLF-2B | 未起爆也能记录最近接近和原因 | pass |
| `MLF-2D Fuze Evaluation` | 写入引信评估事件 | MLF-2C | 接触、近炸、未解保、错过窗口、延迟和故障分开记录 | pass |
| `MLF-2E Diagnostics` | 导出可读诊断 | MLF-2C/2D | probe 能按一枚弹输出几何和引信阶段行 | pass |
| `MLF-2F Runtime Gate` | 对接现有发射/效果链 | MLF-2D/2E | 起爆状态传给后续效果模型，未触发不会沉默消失 | pass |
| `MLF-2G Closure` | 验收并同步父级导航 | MLF-2B-F 通过 | 当前状态、残余和 archive 边界一致 | pass |

## 任务簇

- 任务簇计划：[missile_lethality_geometry_fuze_task_clusters_20260609.zh.md](missile_lethality_geometry_fuze_task_clusters_20260609.zh.md)
- 当前状态：[missile_lethality_geometry_fuze_current_status_20260609.zh.md](missile_lethality_geometry_fuze_current_status_20260609.zh.md)
- 派发队列：[missile_lethality_geometry_fuze_dispatch_queue_20260609.zh.md](missile_lethality_geometry_fuze_dispatch_queue_20260609.zh.md)

## 输出和证据

当前已验收的 runtime 和诊断证据：

- 本 README 固定目标和边界。
- 任务簇文档限定有限工作包。
- 当前状态文档记录 MLF-2B 到 MLF-2G 已验收。
- 派发队列记录 MLF-2G-C1 已完成，当前没有继续派发包。
- 受控几何测试能改变距离、闭合速度、方位和高度差。
- 最近接近事件已经能从 live 路径写出；未起爆和错过目标路径也有最近点与原因。
- 最近点时间已从终端判定帧修正为最近点刷新时刻。
- 引信评估事件已经能记录解保/触发、未触发和失败原因，并与同一枚弹的最近接近事件相连。
- 诊断 probe 优先消费标准最近接近和引信评估事件；旧 `EffectsEvent` 投影只作为缺省回退。
- runtime handoff gate 已被聚焦测试覆盖：触发路径才产生现有效果/损伤记录，接触近失没有效果/损伤记录，可靠性失败只有零伤害过渡记录。

本包仍保留的 held 项：

- timed fuze 标准事件覆盖仍未做。
- max-flight-time / guidance expiry 仍缺 recorder access。
- 零伤害过渡 `EffectsEvent` / `DamageReport` 仍保留，后续删除必须等待下游消费面迁移。
- 受控几何测试仍可继续补足延迟和更细目标姿态路径。

## 验收门

本子项目按以下条件标记为 accepted：

- 同一枚弹的发射、最近接近、引信评估和后续效果事件能用稳定 id 串起来。
- 距离、方位、速度和姿态改变会改变触发/未触发/延迟/失败结果，并且诊断能说明原因。
- 接触命中和近炸触发被分开记录。
- 没有起爆时仍有可读原因，而不是只没有效果事件。
- 起爆状态只交给后续战斗部模型，不直接生成碎裂、坠毁或训练胜负。
- 证据等级和默认参数来源可追溯。

## 残余和下一步

- MLF-2 已完成归档，本目录不再继续派发。
- 破片、连续杆、结构断裂、残骸和 Pk 仍是 MLF-3 及以后阶段。
- 具体 AIM-120C/MQ-9 结论必须等 MLF-2 和至少一个后续战斗部作用模型通过后再讨论。

## Archive

归档索引：[../README.zh.md](../README.zh.md)

当前 [../../README.zh.md](../../README.zh.md) 只保留为轻量指针。本证据包只证明导弹接近几何和引信评估链路已经可观察、可诊断、可验收；它不证明战斗部效果、目标碎裂、坠毁、Pk 或具体弹种杀伤结论。
