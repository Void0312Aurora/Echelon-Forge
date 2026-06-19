# A2 导弹杀伤归档注册表

状态：`2026-06-19` 本地注册表，用于登记已完成或失效的 A2 missile-lethality
follow-on。物理记录保存在 [archive/](archive/README.zh.md)；父目录只保留仍有效、
仍需保留在根面的项目。

| 记录 | 物理路径 | 状态 | 保留边界 |
| --- | --- | --- | --- |
| MLF-1 杀伤链合同基础 | [archive/missile_lethality_model_foundation/README.zh.md](archive/missile_lethality_model_foundation/README.zh.md) | accepted / archived | 定义阶段字段和权限边界；自身不释放 runtime 权威 |
| MLF-2 几何 / 引信 | [archive/missile_lethality_geometry_fuze/README.zh.md](archive/missile_lethality_geometry_fuze/README.zh.md) | accepted / archived | 只保留接近几何、最近点、引信评估和起爆 handoff 证据 |
| 近炸引信现实性 | [archive/missile_lethality_proximity_fuze_realism/README.zh.md](archive/missile_lethality_proximity_fuze_realism/README.zh.md) | accepted-with-residuals / archived | 公开资料 surrogate realism 切片；不提供 deterministic fuze、Pk 或 stock weapon truth |
| MLF-3 战斗部作用 | [archive/missile_lethality_warhead_effects/README.zh.md](archive/missile_lethality_warhead_effects/README.zh.md) | accepted / archived | 通用破片/爆风载荷和诊断证据；不声明部件失效或结构解体 |
| MLF-4 连续杆 | [archive/missile_lethality_continuous_rod/README.zh.md](archive/missile_lethality_continuous_rod/README.zh.md) | accepted / archived | rod/cut 暴露事实和部件受载投影；不声明结构解体或 Pk |
| MLF-5 部件失效 | [archive/missile_lethality_component_failure/README.zh.md](archive/missile_lethality_component_failure/README.zh.md) | accepted / archived | 部件失效概率、失效模式和状态变化证据；不声明坠毁、解体或 Pk |
| MLF-6 结构失效 | [archive/missile_lethality_structural_failure/README.zh.md](archive/missile_lethality_structural_failure/README.zh.md) | accepted / archived | 通过 `StructuralBreakupState` 和 `StructuralBreakupEvent` 记录具名断裂事实；不释放气动、失能状态、残骸或 Pk 权威 |
| MLF-7 二次后果耦合 | [archive/missile_lethality_secondary_consequence_coupling/README.zh.md](archive/missile_lethality_secondary_consequence_coupling/README.zh.md) | accepted / archived | 通过维护中的 aircraft damage、platform damage、loss-state 和诊断承接有边界断裂后果；不释放残骸/碎片、Pk 或校准权威 |
| MLF-8 残骸/碎片生命周期 | [archive/missile_lethality_debris_wreck_lifecycle/README.zh.md](archive/missile_lethality_debris_wreck_lifecycle/README.zh.md) | accepted / archived | 与 MLF-6/MLF-7 证据链路关联的 diagnostics-only 脱落部件和终端残骸生命周期事实；不释放一等 debris/wreck 实体、碎片物理、reward 权威、Pk 或校准权威 |
| MLF-9 Pk / 统计趋势 | [archive/missile_lethality_pk_statistical_trends/README.zh.md](archive/missile_lethality_pk_statistical_trends/README.zh.md) | accepted / archived | 基于显式杀伤链 rows 的确定性 simulation trend reports；不释放现实 Pk、具体武器/目标杀伤率、reward 权威或校准权威 |
| MLF-10 校准门 | [archive/missile_lethality_calibration_gates/README.zh.md](archive/missile_lethality_calibration_gates/README.zh.md) | accepted / archived | Fail-closed evidence admission contract、当前 manifest 和零 admitted records 的确定性 report；不释放现实 Pk、deterministic fuze、stock weapon/target lethality、reward 权威、entity-deletion 权威或 runtime 参数重调 |
