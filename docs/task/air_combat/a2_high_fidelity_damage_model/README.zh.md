# A2 高真实度空战毁伤模型

状态：`2026-06-11` 归档指针 / active follow-on 导航。完整项目包已移入
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
- [missile_lethality_target_geometry/README.zh.md](missile_lethality_target_geometry/README.zh.md)：
  active follow-on，从命中盒几何缺口 issue 提升而来，先为 F-16 构建可审阅的外壳区域、部件绑定和
  距离诊断，再决定是否把外壳代理接入近炸投影；它不声明真实 F-16 工程几何、结构解体、残骸、
  Pk 或具体弹种杀伤结论。

当前几何保真度缺口已记录到 issue 板：
[杀伤链命中盒几何保真度缺口](../../issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)。
该 issue 的第一轮主线执行入口已提升为
[missile_lethality_target_geometry/README.zh.md](missile_lethality_target_geometry/README.zh.md)。

后续结构解体、碎裂/残骸、Pk 或具体弹种校准需要按 `docs/agent` 标准另建子项目，
不能继续写入已归档的 MLF-2、MLF-3 或 MLF-4 包。连续杆事实链已经归档，后续部件失效从
上面的 MLF-5 归档指针追溯；结构解体、残骸、Pk 或具体弹种校准仍需另建后续子项目。MLF-3/MLF-4
已归档，不重开已封存 A2 包。

这些 follow-on 不重开已封存 A2 包，也不创建 A9。

只有在明确 authority-promotion 或新 research 请求下才重开本线。默认空战工作继续从
[../README.zh.md](../README.zh.md) 进入。
