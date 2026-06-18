# A2 高真实度空战毁伤模型

状态：`2026-06-19` active follow-on 索引 + 本地 archive 注册表。已封存的
A2 基础 research/candidate 包仍保留在外层空战归档：
[archive/a2_high_fidelity_damage_model](../archive/a2_high_fidelity_damage_model/README.zh.md)。
已完成或失效的本地 MLF follow-on 已物理移动到本目录
[archive/](archive/README.zh.md)，并统一登记在
[archive_registry.zh.md](archive_registry.zh.md)。

本根目录只保留仍有效、仍需保留在根面的项目，避免完成项目长期堆平。

## 当前有效 / 保留入口

- [damage_consequence_reward_surface/README.zh.md](damage_consequence_reward_surface/README.zh.md)：
  active 的有边界训练反馈工作，按损伤后果而不是单一 kill flag 给训练信号。
- [missile_lethality_target_geometry/README.zh.md](missile_lethality_target_geometry/README.zh.md)：
  accepted / retained follow-on，从命中盒几何缺口 issue 提升而来，保留
  F-16C 外壳区域、部件绑定、距离诊断、精细几何代理、表面/内部 receiver
  先验和跨区 split receiver handoff 证据。它不声明真实 F-16 工程几何、
  默认 runtime replacement、训练收益、结构解体、残骸、Pk 或具体弹种杀伤结论。

## 已归档 / 已注册入口

简表见 [archive_registry.zh.md](archive_registry.zh.md)。物理证据包保存在
[archive/](archive/README.zh.md)：

- [archive/missile_lethality_model_foundation/README.zh.md](archive/missile_lethality_model_foundation/README.zh.md)：
  MLF-1 杀伤链合同基础与阶段边界证据。
- [archive/missile_lethality_geometry_fuze/README.zh.md](archive/missile_lethality_geometry_fuze/README.zh.md)：
  MLF-2 导弹接近几何和引信评估证据。
- [archive/missile_lethality_proximity_fuze_realism/README.zh.md](archive/missile_lethality_proximity_fuze_realism/README.zh.md)：
  accepted-with-residuals 的近炸引信现实性证据切片。
- [archive/missile_lethality_warhead_effects/README.zh.md](archive/missile_lethality_warhead_effects/README.zh.md)：
  MLF-3 通用战斗部作用、破片/爆风载荷和诊断证据。
- [archive/missile_lethality_continuous_rod/README.zh.md](archive/missile_lethality_continuous_rod/README.zh.md)：
  MLF-4 连续杆和切割机制事实证据。
- [archive/missile_lethality_component_failure/README.zh.md](archive/missile_lethality_component_failure/README.zh.md)：
  MLF-5 部件脆弱性和失效事实证据。
- [archive/missile_lethality_structural_failure/README.zh.md](archive/missile_lethality_structural_failure/README.zh.md)：
  accepted / archived 的 MLF-6 结构失效与机体断裂事实写入器。
- [archive/missile_lethality_secondary_consequence_coupling/README.zh.md](archive/missile_lethality_secondary_consequence_coupling/README.zh.md)：
  accepted / archived 的 MLF-7 二次后果耦合。runtime bridge 已消费归档的
  MLF-6 断裂事实，把有边界后果写入维护中的 aircraft damage、platform damage
  和 loss-state 表面，并发出链路关联的 `platform_consequence` 诊断。
- [archive/missile_lethality_debris_wreck_lifecycle/README.zh.md](archive/missile_lethality_debris_wreck_lifecycle/README.zh.md)：
  accepted / archived 的 MLF-8 残骸和碎片生命周期证据。runtime 记录与已验收
  MLF-6/MLF-7 证据链路关联的 diagnostics-only 脱落部件和终端残骸生命周期事实；
  一等 debris/wreck 实体、碎片物理、reward 权威、Pk 和校准权威仍保持拒绝。

当前几何保真度缺口已记录到 issue 板：
[杀伤链命中盒几何保真度缺口](../../issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)。
该 issue 的第一轮主线执行入口已按 geometry-only 验收门收口为
[missile_lethality_target_geometry/README.zh.md](missile_lethality_target_geometry/README.zh.md)。

MLF-8（残骸/碎片生命周期）已验收并归档：
[archive/missile_lethality_debris_wreck_lifecycle/README.zh.md](archive/missile_lethality_debris_wreck_lifecycle/README.zh.md)。
旧 active 路径仅保留兼容指针：
[missile_lethality_debris_wreck_lifecycle/README.zh.md](missile_lethality_debris_wreck_lifecycle/README.zh.md)。
MLF-9（Pk/统计趋势）和 MLF-10（校准门）仍需后续独立子项目。不得继续写入
已归档的 MLF-1 到 MLF-8 或近炸引信现实性包。这些 follow-on 不重开已封存
A2 包，也不创建 A9。

只有在明确 authority-promotion 或新 research 请求下才重开本线。默认空战工作继续从
[../README.zh.md](../README.zh.md) 进入。
