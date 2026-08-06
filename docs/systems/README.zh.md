# 跨领域系统

语言：英文为规范页；[中文配套](README.md)。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/README.md`
Owner: `cross-domain simulation systems`
Last verified: `2026-08-07`

本目标区域拥有跨任务领域复用的 environment、physics、sensing、command/tasking、
weapons、effects/damage 文档，避免共享机制被重复塞入 air、naval、ground。
迁移期间，当前规范和任务来源仍位于 [standards](../standards/README.zh.md)
和有界任务 owner。

## 当前 Owner 路由

- Command/tasking issues：[C2 通信](command-tasking/work/issues/c2_communication.zh.md)与[操作层](command-tasking/work/issues/operation_layer.zh.md)。
- Physics issues：[物理引擎路线图](physics/work/issues/physics_engine_roadmap.zh.md)。
- Sensing issues：[传感器与态势计划](sensing/work/issues/sensor_situation.zh.md)。
- Weapons issues：[交战路线图](weapons/work/issues/weapons_engagement.zh.md)、[实现笔记](weapons/work/issues/weapons_engagement_impl.zh.md)和[终止逻辑](weapons/work/issues/engagement_termination.zh.md)。
- Effects reviews：[毁伤模型评估](effects/reviews/air_combat_damage_model_evaluation_20260522.md)与[交叉评估](effects/reviews/air_combat_damage_model_cross_eval_20260522.md)（仅英文）。

`work/issues` 页面是规划输入，不是实施权威。带日期评审保留原证据边界，不能视为
对当前状态的重新核验。

新增 system 本地 standard、reference、work 或 review 时，使用
[共享文档结构](../engineering/documentation/structure_examples.zh.md)。
