# A2 MLF-5 目标部件脆弱性与失效

状态：`2026-06-11` 归档指针。已验收的 MLF-5 证据包已移入
archive/mlf_5_component_failure_accepted_20260611 (`git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/README.zh.md`)。

语言：

- 英文辅文：[README.md](README.md)
- 中文主文：`README.zh.md`

本路径仅保留为已完成第五阶段的导航入口。MLF-5 已完成目标部件脆弱性与失效事实链：
起爆后的部件受载/切割曝光事实可以转成同链路的部件损伤事实，包含部件名、系统、冗余组、
失效概率、随机样本、失效模式、严重度、完整度前后值和诊断摘要。

MLF-5 不判断飞机是否坠毁、不生成结构解体或残骸、不计算 Pk，也不校准真实 AIM-120C/MQ-9
或任何具体弹种/目标组合。部件状态变化只交给已有损伤、飞行动力学、推进和传感器系统继续传播。

当前归档证据包：
`git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/README.zh.md`。

后续若要让部件失效进一步发展成结构解体、残骸生命周期、Pk 或具体弹种校准，必须按
`docs/agent` 标准另建子项目，不能继续写入这个已完成的 MLF-5 子项目。

可复用结论：系统现在可以解释“哪个部件因何受损、失效概率和抽样结果如何、状态前后变化如何”，
并能把这些部件状态变化交给已有系统；这些事实仍然不直接说明目标碎裂、坠毁或被击毁。
