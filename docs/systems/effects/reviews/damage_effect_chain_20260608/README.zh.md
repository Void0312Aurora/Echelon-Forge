# A8 损伤效果链

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/effects/reviews/damage_effect_chain_20260608/README.md`
Owner: `systems/effects`
Last verified: `2026-08-09`
Review basis: 已接受的有限 A8 damage/effects evidence 与 deferred residuals。

状态：保留的已接受切片。证据解释从引爆到机体部件损伤，再到 propulsion、
fuel、sensor、fire、flight 与 ground-contact response 的有限路径；不声明
现实 Pk、deterministic fuze truth、机型控制律标定或 debris authority。

输入：

- [Systems owner](../../../README.zh.md)
- [F-16 target-geometry review](../f16c_target_geometry_20260614/README.zh.md)
- [Lethality geometry issue](../../work/issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)
- [通用 damage component](../../../../../src/components/combat/common/damage_common.h)
- [Air damage component](../../../../../src/components/domains/air/combat/damage_air.h)
- [Air damage system](../../../../../src/systems/combat/damage_system_air.h)
- [Effects model](../../../../../src/models/weapons/default_effects_model.cpp)

验证边界：保留当前 engineering-proxy runtime 行为与 MQ-9/AIM-120C-like
聚焦检查；标定级 weapon/target truth 与 first-class debris/residue 仍 deferred。
