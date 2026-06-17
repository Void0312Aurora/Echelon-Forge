# A2 高真实度空战毁伤模型

状态：`2026-06-17` 归档指针 / active follow-on 导航，MLF-6 已建立。完整项目包已移入
[archive/a2_high_fidelity_damage_model](../archive/a2_high_fidelity_damage_model/README.zh.md)。

本路径仅保留为轻量工作说明和导航入口。

已归档的 A2 包关闭了空战高真实度毁伤模型的 research/candidate profile。它保留
非权威 blast-fragmentation 证据、已接受的 G1-G5 research packets，以及 structured
aircraft damage/effects runtime 记录。它不释放 stock authority、Pk authority、
deterministic fuze authority 或更广的 weapon-outcome authority。

当前 A2 follow-on：

- [damage_consequence_reward_surface/README.zh.md](damage_consequence_reward_surface/README.zh.md)：
  将“按损伤后果而非单一 kill 给训练奖励”的方向升级为有边界奖励扩展切片。
- [missile_lethality_model_foundation/README.zh.md](missile_lethality_model_foundation/README.zh.md)：
  已归档的 MLF-1 杀伤链合同基础，只作为后续阶段的字段和边界证据。
- [missile_lethality_geometry_fuze/README.zh.md](missile_lethality_geometry_fuze/README.zh.md)：
  已归档的 MLF-2 导弹接近几何与引信评估证据包；它证明最近点、引信评估和起爆 handoff 可观察，但不实现破片、结构解体、Pk 或具体弹种击毁结论。
- [missile_lethality_proximity_fuze_realism/README.zh.md](missile_lethality_proximity_fuze_realism/README.zh.md)：
  accepted-with-residuals follow-on，已把当前最近距离式近炸引信 proxy 替换为公开资料驱动、
  非权威的 surrogate evidence 切片并完成聚焦矩阵验证。它不授权 deterministic fuze authority、Pk、
  stock weapon truth 或具体弹种杀伤声明。
- [missile_lethality_warhead_effects/README.zh.md](missile_lethality_warhead_effects/README.zh.md)：
  已归档的 MLF-3 证据包，聚焦起爆后的通用战斗部作用、破片/爆风载荷、空间覆盖、部件受载、
  诊断，以及“未起爆不产生载荷”的运行门；它不实现连续杆、部件失效概率、结构解体、残骸、Pk
  或具体弹种击毁结论。
- [missile_lethality_continuous_rod/README.zh.md](missile_lethality_continuous_rod/README.zh.md)：
  已归档的 MLF-4 证据包，聚焦连续杆和切割机制事实；它证明 rod/cut 曝光事实链可观察、
  可诊断并能投影到部件受载行，但不声明部件失效、结构解体、残骸、Pk 或具体弹种击毁结论。
- [missile_lethality_component_failure/README.zh.md](missile_lethality_component_failure/README.zh.md)：
  已归档的 MLF-5 证据包，聚焦目标部件脆弱性和失效事实；它将 MLF-3/MLF-4 的部件受载/切割曝光
  转成部件失效概率、失效模式和状态变化，再交给已有损伤/飞行系统传播后果，但不声明坠毁、
  结构解体、残骸、Pk 或具体弹种杀伤结论。
- [missile_lethality_structural_failure/README.zh.md](missile_lethality_structural_failure/README.zh.md)：
  **active MLF-6 子项目**，消费 MLF-5 部件失效输出（ECS `ComponentDamageState`），
  写入 `StructuralBreakupEvent` 行并产生具名断裂事实；不修改 `structural_integrity`、
  飞行动力学或失能状态（属于 MLF-7）。不声明 Pk、残骸生命周期或具体弹种杀伤结论。
- [missile_lethality_target_geometry/README.zh.md](missile_lethality_target_geometry/README.zh.md)：
  accepted / retained follow-on，从命中盒几何缺口 issue 提升而来，已为 F-16C 构建可审阅的外壳区域、
  部件绑定、距离诊断、精细几何代理、表面/内部 receiver 先验和跨区 split receiver handoff
  证据；它不声明真实 F-16 工程几何、默认 runtime replacement、训练收益、结构解体、残骸、Pk
  或具体弹种杀伤结论。

当前几何保真度缺口已记录到 issue 板：
[杀伤链命中盒几何保真度缺口](../../issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)。
该 issue 的第一轮主线执行入口已提升并按 geometry-only 验收门收口为
[missile_lethality_target_geometry/README.zh.md](missile_lethality_target_geometry/README.zh.md)。

MLF-6（结构失效/机体断裂）已按 `docs/agent` 标准建立活跃子项目：
[missile_lethality_structural_failure/README.zh.md](missile_lethality_structural_failure/README.zh.md)。
MLF-7（二次后果耦合）、MLF-8（残骸/碎片生命周期）、MLF-9（Pk/统计层）和 MLF-10（校准门）
仍需后续独立子项目。不得继续写入已归档的 MLF-2、MLF-3 或 MLF-4 包。MLF-3/MLF-4
已归档，不重开已封存 A2 包。

这些 follow-on 不重开已封存 A2 包，也不创建 A9。

只有在明确 authority-promotion 或新 research 请求下才重开本线。默认空战工作继续从
[../README.zh.md](../README.zh.md) 进入。
