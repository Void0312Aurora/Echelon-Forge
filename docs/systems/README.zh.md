# 跨领域系统

语言：英文为规范页；[中文配套](README.md)。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/README.md`
Owner: `cross-domain simulation systems`
Last verified: `2026-08-08`

本目标区域拥有跨任务领域复用的 environment、physics、sensing、command/tasking、
weapons、effects/damage 文档，避免共享机制被重复塞入 air、naval、ground。
当前规范位于本 owner 的 `standards/` 表面；范围化工作由适用的嵌套 owner
维护。当前跨域真实性门控见[梯度真实性原则](standards/gradient_realism_principles.zh.md)。

## 当前 Owner 路由

- Environment owner：[环境系统](environment/README.zh.md)，包括 G0 与 Arnis
  验收边界。
- Command/tasking issues：[C2 通信](command-tasking/work/issues/c2_communication.md)与[操作层](command-tasking/work/issues/operation_layer.md)。
- Command/tasking reference：[agency authority 清单](command-tasking/reference/agency_authority_census_20260721.zh.md)与[authority representation 裁决](command-tasking/reference/t9_authority_representation_adjudication_20260726.zh.md)。
- Physics issues：[物理引擎路线图](physics/work/issues/physics_engine_roadmap.md)。
- Sensing issues：[传感器与态势计划](sensing/work/issues/sensor_situation.md)。
- Weapons issues：[交战路线图](weapons/work/issues/weapons_engagement.md)、[实现笔记](weapons/work/issues/weapons_engagement_impl.md)和[终止逻辑](weapons/work/issues/engagement_termination.md)；保留 guidance 证据位于[制导机制评审](weapons/reviews/kill_chain_guidance_mechanism_20260715/README.zh.md)。
- Effects issues：[毁伤模型校准残差](effects/work/issues/damage_model_calibration_residuals.md)、[毁伤/控制权威耦合](effects/work/issues/damage_control_authority_coupling_gap/README.zh.md)与[杀伤/几何保真度](effects/work/issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)。
- Effects reviews：[F-16C 目标几何](effects/reviews/f16c_target_geometry_20260614/README.zh.md)、[开火时机窗口诊断](effects/reviews/fire_timing_window_position_effect_20260615/README.zh.md)与[kill-chain 机制解耦](effects/reviews/kill_chain_mechanism_decoupling_20260621/README.zh.md)。

`work/issues` 页面是规划输入，不是实施权威。带日期评审保留原证据边界，不能视为
对当前状态的重新核验。

新增 system 本地 standard、reference、work 或 review 时，使用
[共享文档结构](../engineering/documentation/structure_examples.zh.md)。
