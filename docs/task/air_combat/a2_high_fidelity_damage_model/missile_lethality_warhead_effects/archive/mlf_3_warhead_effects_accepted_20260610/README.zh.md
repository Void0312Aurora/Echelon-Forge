# A2 MLF-3 战斗部作用与通用破片/爆风载荷

状态：`2026-06-10` MLF-3 标准载荷链 focused accepted；高保真导弹杀伤模型仍未完成。MLF-2 已归档；本子项目单独展开第三阶段，不继续写入 MLF-1 或 MLF-2 已归档目录。

语言：

- 英文辅文：[README.md](README.md)
- 中文主文：`README.zh.md`

输入：

- 当前 MLF-3 指针：[../../README.zh.md](../../README.zh.md)
- A2 指针：[../../../README.zh.md](../../../README.zh.md)
- MLF-1 链路合同归档：[../../../missile_lethality_model_foundation/README.zh.md](../../../missile_lethality_model_foundation/README.zh.md)
- MLF-2 接近几何与引信评估归档：[../../../missile_lethality_geometry_fuze/README.zh.md](../../../missile_lethality_geometry_fuze/README.zh.md)
- 历史 A2 研究包：[../../../../archive/a2_high_fidelity_damage_model/README.zh.md](../../../../archive/a2_high_fidelity_damage_model/README.zh.md)
- 战斗部参数入口：[../../../../../../../src/components/combat/common/weapon_common.h](../../../../../../../src/components/combat/common/weapon_common.h)
- 事件合同入口：[../../../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h)
- 现有效果模型入口：[../../../../../../../src/models/weapons/default_effects_model.cpp](../../../../../../../src/models/weapons/default_effects_model.cpp)
- 战斗部/空间投影实现片段：[../../../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc)、[../../../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc)
- 诊断投影入口：[../../../../../../../tools/diagnostics/air_combat_stage0_process_probe.py](../../../../../../../tools/diagnostics/air_combat_stage0_process_probe.py)

## 目的

MLF-3 的目标是回答“引信已经起爆以后，战斗部给目标施加了什么作用”。它把起爆事实转成可解释的机制载荷：破片能量、破片面密度、爆风超压、冲量、缩尺距离、方向性权重、空间覆盖和部件受载。

本阶段不直接回答目标是否击毁、是否碎裂、是否坠毁，也不声明真实 AIM-120C 或任何具体弹种的杀伤概率。它只给后续目标脆弱性、部件失效、结构断裂、残骸和训练消费提供上游事实。

## Research 数据口径

MLF-3 只接纳通用、未校准、可替换的 research 数据。默认模型可以使用公开方法、通用爆风/破片公式、工程量级和 CMO-DB 等代理资料的类别提示，但不得把这些值写成 AIM-120C、MQ-9 或任何具体型号的真实参数。

所有默认参数都必须保留后续替换空间：来源类别、证据等级、适用范围、单位、置信度或不确定性、替换规则，以及是否只用于测试/研究。若缺少这些标注，该值只能留在文档候选或测试夹具里，不得成为运行时默认权威。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| MLF-2 起爆输入 | accepted / archived | [MLF-2 归档](../../../missile_lethality_geometry_fuze/README.zh.md) | 只说明最近点、引信评估和起爆 handoff |
| 战斗部 profile 数据 | active scaffold | `WarheadProfile`、`WarheadEffectProfile`、`WarheadSpatialProjectionProfile` | 不是真实战斗部参数权威 |
| 标准事件 DTO | live writer / diagnostics / no-detonation gate focused pass | `WarheadMechanismEvent`、`SpatialCoverageEvent`、`ComponentLoadEvent` 已在合同、绑定、event-store writer、真实起爆路径测试和诊断投影中存在 | 参数未校准；不输出击毁结论 |
| 现有效果模型 | generic load-shape + spatial-component projection focused pass | `default_effects_model` 已有 mechanism / spatial / component 字段；`test_warhead_blast_fragmentation_loads.py` 钉住 range / direction / family 会改变标准载荷事实；`test_warhead_spatial_component_projection.py` 钉住空间覆盖会改变标准部件受载事实 | 仍主要折叠进 `EffectsEvent`；默认常量缺少完整 source category / scope / unit / uncertainty / replacement-rule runtime metadata |
| 历史 Phase 3 测试 | retained scaffold evidence | `tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py` | 不等于新的 MLF-3 accepted |

## 范围

纳入：

- 盘点现有战斗部、空间投影和部件受载字段，确认哪些可以迁到标准事件。
- 为起爆后的战斗部作用写入 `WarheadMechanismEvent`。
- 为近炸空间覆盖写入 `SpatialCoverageEvent`，至少覆盖样本数、覆盖比例、能量/方向权重和投影命中数。
- 为部件受载写入 `ComponentLoadEvent`，把机制载荷交给后续脆弱性/结构模型。
- 建立一个通用、未校准的 blast-fragmentation 预制模型，并给所有默认值标注证据等级。
- 让诊断按一枚弹输出 warhead / spatial_coverage / component_load 行。

不纳入：

- 不实现连续杆切割模型；它应进入 MLF-4。
- 不实现结构断裂、空中解体、残骸对象；它们属于 MLF-6/MLF-8。
- 不校准具体 AIM-120C、MQ-9 或其它具体弹种/目标组合。
- 不把机制载荷直接变成 kill、crash、combat win 或实体删除。
- 不把历史 A2 blast-fragmentation 候选包提升为 stock authority。
- 不把通用 research 参数写成具体型号真值；具体型号补充只能以后以显式来源、证据等级和替换记录进入。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `MLF-3A Boundary And Inventory` | 固定 MLF-3 范围，盘点旧字段和 live 缺口 | MLF-2 archived | README、状态、任务簇和派发队列存在；旧字段/缺口清单可读 | accepted |
| `MLF-3B Event Writers` | 写入 warhead/spatial/component 标准事件 | MLF-3A | 起爆后有标准事件，且 parent 指向同链路 fuze/effects | live gate focused pass |
| `MLF-3C Generic Blast-Fragmentation` | 建立通用未校准破片/爆风机制载荷 | MLF-3B | 距离、方位、战斗部 family 会改变机制载荷 | focused pass |
| `MLF-3D Spatial Coverage` | 把机制载荷投影到目标 hitbox/component | MLF-3C | 空间覆盖和部件受载可由标准事件诊断 | focused pass |
| `MLF-3E Diagnostics Projection` | probe 输出 warhead/spatial/component 行 | MLF-3B-D | 不依赖旧 `EffectsEvent` 才能读出机制原因 | focused pass |
| `MLF-3F Runtime Handoff Gate` | 保证只有起爆进入战斗部作用，未起爆不产生载荷 | MLF-3B-E | 未起爆路径无 warhead load，起爆路径有一次标准载荷链 | focused pass |
| `MLF-3G Acceptance And Archive Prep` | 汇总证据、残余和后续阶段 | MLF-3B-F pass | accepted/held 状态与证据一致 | focused pass |

## 任务簇

- 任务簇计划：[missile_lethality_warhead_effects_task_clusters_20260609.zh.md](missile_lethality_warhead_effects_task_clusters_20260609.zh.md)
- 当前状态：[missile_lethality_warhead_effects_current_status_20260609.zh.md](missile_lethality_warhead_effects_current_status_20260609.zh.md)
- 派发队列：[missile_lethality_warhead_effects_dispatch_queue_20260609.zh.md](missile_lethality_warhead_effects_dispatch_queue_20260609.zh.md)
- 盘点验收：[missile_lethality_warhead_effects_inventory_20260609.zh.md](missile_lethality_warhead_effects_inventory_20260609.zh.md)
- 收口验收：[missile_lethality_warhead_effects_acceptance_20260610.zh.md](missile_lethality_warhead_effects_acceptance_20260610.zh.md)

## 输出和证据

本阶段预期输出：

- 起爆后的标准战斗部机制事件。
- 标准空间覆盖事件。
- 标准部件受载事件。
- 通用 blast-fragmentation 默认模型及证据等级。
- 诊断 probe 的 warhead / spatial_coverage / component_load 行。
- 聚焦测试证明同一几何下，不同距离、方位或 family 会改变机制载荷和覆盖结果。
- 聚焦测试证明空间覆盖/局部投影会改变标准部件受载事实。

## 验收门

本子项目只有在以下条件满足后才能标记为 accepted：

- 未起爆路径不会产生战斗部作用。
- 起爆路径能写出同一链路下的 warhead、spatial_coverage 和 component_load 标准事件。
- 破片/爆风载荷随距离、方向、空间覆盖和 family 变化，而不是单一扣血。
- 诊断能解释“哪些部件受到了什么载荷”，但不把它说成击毁。
- 所有默认值有 `synthetic`、`engineering_assumption`、`cmo_db_proxy`、`public_method_reference` 等证据等级。
- 结构解体、残骸、Pk 和具体弹种校准继续 held。

## 残余和下一步

- MLF-4：连续杆/切割机制。
- MLF-5：目标脆弱性和部件失效概率。
- MLF-6：结构断裂和空中解体。
- MLF-8：残骸和碎片对象生命周期。
- MLF-9：Pk/统计趋势层。

## Archive

归档索引：[../README.zh.md](../README.zh.md)

当前 [../../README.zh.md](../../README.zh.md) 只保留轻量指针。本证据包只证明通用起爆后载荷事实；
不证明部件失效、结构解体、残骸、Pk、坠毁或具体弹种杀伤结论。
