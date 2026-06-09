# A2 高真实度空战毁伤模型

状态：`2026-06-02` 归档指针。完整项目包已移入
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
  MLF-2 当前子项目，聚焦受控接近几何和引信评估；它不实现破片、结构解体、Pk 或具体弹种击毁结论。

这些 follow-on 不重开已封存 A2 包，也不创建 A9。

只有在明确 authority-promotion 或新 research 请求下才重开本线。默认空战工作继续从
[../README.zh.md](../README.zh.md) 进入。
