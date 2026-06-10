# A2 MLF-4 连续杆切割机制

状态：`2026-06-11` active planning / `MLF-4A-X1` 盘点、`MLF-4B-W1-R2` 标准 rod 事件面、`MLF-4C-W1` 通用 rod 几何与 `MLF-4D-W1` 部件切割投影已验收。本子项目规划连续杆和切割机制事实链，不声明部件失效、结构解体、残骸、Pk 或具体弹种杀伤结论。

语言：

- 英文辅文：[README.md](README.md)
- 中文主文：`README.zh.md`

输入：

- A2 指针：[../README.zh.md](../README.zh.md)
- MLF-2 引信 handoff 指针：[../missile_lethality_geometry_fuze/README.zh.md](../missile_lethality_geometry_fuze/README.zh.md)
- MLF-3 战斗部载荷指针：[../missile_lethality_warhead_effects/README.zh.md](../missile_lethality_warhead_effects/README.zh.md)
- MLF-3 已验收证据包：[../missile_lethality_warhead_effects/archive/mlf_3_warhead_effects_accepted_20260610/README.zh.md](../missile_lethality_warhead_effects/archive/mlf_3_warhead_effects_accepted_20260610/README.zh.md)
- 战斗部参数入口：[../../../../../src/components/combat/common/weapon_common.h](../../../../../src/components/combat/common/weapon_common.h)
- 事件合同入口：[../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../src/runtime/contracts/engagement_contracts.h)
- 现有效果模型：[../../../../../src/models/weapons/default_effects_model.cpp](../../../../../src/models/weapons/default_effects_model.cpp)
- 当前 rod/cut 实现片段：[../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc](../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc)、[../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc](../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc)
- 历史 rod 测试：[../../../../../tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py](../../../../../tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py)

## 目的

MLF-4 回答“如果已起爆战斗部属于连续杆或切割机制，它产生了什么切割曝光”。它把 MLF-2 的起爆几何和 MLF-3 的载荷事实转成可解释的切割事实：杆/切割机制、切割余量、方向权重、投影切割带、部件切割曝光和可诊断 rod 字段。

本阶段不判断机翼、控制线路、发动机或机体已经失效。它只为后续目标脆弱性、部件失效、结构解体、残骸和训练消费提供上游切割事实。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| MLF-2 起爆输入 | accepted / archived | MLF-2 指针 | 只证明最近点、引信评估和起爆 handoff |
| MLF-3 载荷事实 | accepted / archived | MLF-3 指针与已验收包 | 提供通用 warhead/spatial/component 载荷事实，不提供失效判断 |
| MLF-4A 盘点 | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.zh.md](missile_lethality_continuous_rod_inventory_20260610.zh.md) | 只验收只读盘点，不验收 runtime 行为 |
| rod 字段 | accepted event surface | `WarheadMechanismEvent::rod_cut_margin`、`ComponentLoadEvent::rod_cut_margin`、`EffectsEvent::mechanism_rod_cut_margin`、component primary rod 字段；[test_mlf4_standard_rod_event_surface.py](../../../../../tests/runtime/air_combat/test_mlf4_standard_rod_event_surface.py) | 只验收标准切割事实，不验收失效 |
| 通用 continuous-rod 几何 | accepted slice | [test_mlf4_generic_rod_geometry.py](../../../../../tests/runtime/air_combat/test_mlf4_generic_rod_geometry.py) | 只作为通用趋势证据，不提供真实 rod count/velocity |
| 部件切割投影 | accepted slice | [test_mlf4_component_cut_projection.py](../../../../../tests/runtime/air_combat/test_mlf4_component_cut_projection.py) | 只验收 component-load 切割事实，不做部件损伤、integrity 修改或失效 |
| 数据权威 | held | 公开/代理来源最多识别宽泛机制类别 | 不提供 AIM-120C 或其他具体弹种 rod 参数 |

## 范围

纳入：

- 盘点并标准化现有 continuous-rod 分支与 `rod_cut_margin` 字段。
- 决定 MLF-4 是否复用 `WarheadMechanismEvent` 和 `ComponentLoadEvent` 中的 rod 字段，或是否需要新增标准事件。
- 从起爆几何、方向轴、距离和空间覆盖中建立通用、未校准的连续杆切割曝光模型。
- 将切割曝光投影到 hitbox/component，形成部件受载事实。
- 让诊断显示 rod/cutting 行，但不把它转换成击毁或坠毁声明。
- 保持未起爆和非 rod 门：未起爆没有 rod cut；非 rod 战斗部不应输出正的 rod-cut 事实。

不纳入：

- 不做部件失效概率；它属于 MLF-5。
- 不做结构解体、机体被切断结论、残骸或 wreck 对象；它们属于后续结构/残骸阶段。
- 不做 Pk、训练胜负投影或实体删除。
- 不做真实弹种/目标校准，包括 AIM-120C/MQ-9 结论。
- 不把历史 Phase 3 rod 测试直接提升为 accepted 证据，除非通过新的 MLF-4 验证。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `MLF-4A Boundary And Inventory` | 固定范围，盘点现有 rod 字段/分支/测试 | MLF-3 archived | 当前状态记录可复用字段和缺口 | accepted |
| `MLF-4B Standard Rod Event Surface` | 决定并稳定标准 rod/cut 字段 | 4A accepted | `continuous_rod` 起爆输出同链路正 rod 事实；非 rod 和未起爆无正 rod 事实 | accepted |
| `MLF-4C Generic Rod Geometry` | 新增或确认通用切割带/方向投影 | 4B accepted | 距离、侧向/方位、方向轴可预测地改变 rod cut margin | accepted |
| `MLF-4D Component Cut Projection` | 把 rod 切割曝光投影到部件 | 4C accepted | 部件行能标出受影响部件与 rod cut margin，但不输出失效 | accepted |
| `MLF-4E Diagnostics And Gates` | 诊断优先读取标准 rod 事实，并保护未起爆/非 rod 路径 | 4D accepted | probe 能解释 rod/cut 事实，且不会出现虚假 rod 行 | ready |
| `MLF-4F Acceptance And Archive Prep` | 汇总 accepted/held 状态并同步索引 | 4B-E pass | README/status/task cluster/dispatch/archive 一致 | planned |

## 任务簇

- 任务簇计划：[missile_lethality_continuous_rod_task_clusters_20260610.zh.md](missile_lethality_continuous_rod_task_clusters_20260610.zh.md)
- 当前状态：[missile_lethality_continuous_rod_current_status_20260610.zh.md](missile_lethality_continuous_rod_current_status_20260610.zh.md)
- 派发队列：[missile_lethality_continuous_rod_dispatch_queue_20260610.zh.md](missile_lethality_continuous_rod_dispatch_queue_20260610.zh.md)
- MLF-4A 盘点包：[missile_lethality_continuous_rod_inventory_20260610.zh.md](missile_lethality_continuous_rod_inventory_20260610.zh.md)

## 输出和证据

预期输出：

- 现有 rod 字段、分支行为和历史测试的只读盘点。
- `continuous_rod` 起爆后的标准 rod/cutting 事实，已由 [test_mlf4_standard_rod_event_surface.py](../../../../../tests/runtime/air_combat/test_mlf4_standard_rod_event_surface.py) 验收。
- 聚焦测试证明距离、侧向/方位、方向轴和 family 会改变 rod/cut 事实，包括 [test_mlf4_generic_rod_geometry.py](../../../../../tests/runtime/air_combat/test_mlf4_generic_rod_geometry.py)。
- 部件受载行能暴露每个受影响部件的 rod cut margin，已由 [test_mlf4_component_cut_projection.py](../../../../../tests/runtime/air_combat/test_mlf4_component_cut_projection.py) 验收。
- 诊断行能解释 rod/cut 事实，但不声明失效。

## 验收门

本子项目只有在以下条件满足后才能标记为 accepted：

- `continuous_rod` 起爆能产生同链路、可诊断的 rod/cut 事实。
- 非 rod 战斗部和未起爆路径不会产生正的 rod/cut 事实。
- rod/cut 事实会随距离、侧向/方位、方向轴和部件投影变化。
- 部件行暴露切割曝光，但不声明失效、解体、坠毁或实体删除。
- 所有默认 rod 常量继续保持通用 research 假设，并带证据等级和替换路径。

## 残余和下一步

- MLF-5 在建模部件失效概率时消费 rod/cut 事实。
- MLF-6 在建模结构解体时消费部件失效输出。
- MLF-8 在建模残骸生命周期时消费结构解体输出。
- MLF-9 消费可回放的高细节链路，用于 Pk/统计趋势工作。

## Archive

归档索引：[archive/README.zh.md](archive/README.zh.md)

被替代或已验收的证据记录只有在出现新的 current-status 或 closeout surface 后才移入 archive。
