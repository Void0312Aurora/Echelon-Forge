# A2 高真实度空战毁伤模型

状态：`2026-06-23` active follow-on 索引 + 本地 archive 注册表。已封存的
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
- [kill_chain_guidance_lethality_calibration_20260621.zh.md](kill_chain_guidance_lethality_calibration_20260621.zh.md)：
  8 km / 30 度 AIM-120C 制导与近炸杀伤校准问题的保留研究记录，拆分当前工程
  代理行为、真实弹种/目标权威边界和建议的有界 follow-on 验收门。
- [kill_chain_expectation_standardization/README.zh.md](kill_chain_expectation_standardization/README.zh.md)：
  accepted / retained task-local docs-only 标准化 follow-on，在重调 runtime 参数前定义 AIM-120C-like
  工程代理的杀伤链期望合同、距离 x 偏置角 heatmap、采样密度估算、P3 指标映射和
  P4 harness plan。当前 P0-P5 均为 pass；P5 决策为保留 task-local docs-only
  standard，本轮不写入 `docs/standards`；P5 后已启动 initial before-report
  harness wrapper，已生成匀速目标 `78` case anchor before report、逐部件
  `component_detail` 共享投影保留、reviewable heatmap 可视化、first-review-stage
  归因和 component-response 局部诊断；KCES 不重新维护部件归因规则；仍不声明
  真实武器、真实目标、确定性引信、Pk 或校准 authority。
- [kill_chain_mechanism_decoupling_analysis_20260621.zh.md](kill_chain_mechanism_decoupling_analysis_20260621.zh.md)：
  已完成的杀伤链机制抽象与解耦分析，把 approach、fuze decision、
  warhead load field、component response 和 consequence projection 五段、
  只读诊断证据、P2 runtime facade、P3 默认关闭、P4 named load factors、P5
  response owner rows 和后续 P6 校准边界收口到同一入口。
- [kill_chain_decoupling_stage_abstraction_slice_20260621.zh.md](kill_chain_decoupling_stage_abstraction_slice_20260621.zh.md)：
  首个只读实现切片，在现有 lethality-chain rows 上增加 stage abstractions
  和 coupling-flag summary，不改 runtime 参数。
- [kill_chain_decoupling_probe_results_20260621.zh.md](kill_chain_decoupling_probe_results_20260621.zh.md)：
  可复用解耦诊断工具和 baseline 结果，覆盖 8 km / 30 度 AIM-120C 偏置场景
  与 blast-fragmentation 近炸距离 sweep，并通过五段视图报告。
- [kill_chain_scalar_coupling_ledger_20260621.zh.md](kill_chain_scalar_coupling_ledger_20260621.zh.md)：
  标量 producer / owner / consumer 账本切片，在调 runtime 参数或进入校准门之前，
  先标出 owner 泄漏和跨阶段复合标量消费。
- [kill_chain_effect_scale_decomposition_probe_20260621.zh.md](kill_chain_effect_scale_decomposition_probe_20260621.zh.md)：
  P1/P4 诊断切片，暴露 aggregate `effect_scale` 背后的 spatial、armor/exposure、
  threshold 和 vulnerability 因子；当前 P4 named load factors 已进入 runtime surface，
  但不改默认杀伤参数。
- [kill_chain_component_load_factor_view_20260621.zh.md](kill_chain_component_load_factor_view_20260621.zh.md)：
  P1-b/P4 诊断切片，增加逐部件 load-factor rows 和 residual proxy，用于继续拆解
  `component_load.effect_scale`；runtime named factors 已落地，但不改杀伤参数。
- [kill_chain_component_response_boundary_20260621.zh.md](kill_chain_component_response_boundary_20260621.zh.md)：
  P5 response owner 边界切片，确认 load row 只保留载荷/机制字段，response row
  承载概率、sample、failure mode 和 integrity。
- [kill_chain_decoupled_facade_20260621.zh.md](kill_chain_decoupled_facade_20260621.zh.md)：
  P2 历史只读诊断 facade 前置切片，把当前证据投影成 ApproachFact / FuzeDecision /
  WarheadLoadField / ComponentResponse / ConsequenceProjection 形状。
- [kill_chain_runtime_facade_slice_20260621.zh.md](kill_chain_runtime_facade_slice_20260621.zh.md)：
  P2/P5 runtime facade 清理切片，让 probe 从 runtime DTO-backed 结构读取
  component load named factors 与 component response owner rows。
- [kill_chain_fuze_damage_policy_slice_20260621.zh.md](kill_chain_fuze_damage_policy_slice_20260621.zh.md)：
  P3 清理切片，旧引信质量伤害倍率入口已从 runtime / DTO / binding / diagnostics 删除。
- [kill_chain_calibration_admission_gate_20260621.zh.md](kill_chain_calibration_admission_gate_20260621.zh.md)：
  P6 校准 admission 机器门切片，把 fuze、warhead、target response 和 consequence
  四类校准拆成互斥 layer admission；当前因缺少外部 evidence 而 fail-closed。

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
- [archive/missile_lethality_pk_statistical_trends/README.zh.md](archive/missile_lethality_pk_statistical_trends/README.zh.md)：
  accepted / archived 的 MLF-9 Pk / 统计趋势证据。它通过显式 metric contract
  消费可回放 MLF-5 到 MLF-8 仿真事实，并暴露有边界 diagnostics trend reports；
  真实弹种 Pk、具体目标杀伤率、reward 权威和校准权威仍保持拒绝。
- [archive/missile_lethality_calibration_gates/README.zh.md](archive/missile_lethality_calibration_gates/README.zh.md)：
  accepted / archived 的 MLF-10 校准门基础设施。它盘点现有 evidence，定义
  fail-closed admission contract，并保留一份零 admitted records 的确定性当前仓库报告。
  它不释放 real Pk、deterministic fuze、stock weapon/target lethality、reward
  authority、entity-deletion authority、calibration authority，也不执行 runtime
  参数重调。

当前几何保真度缺口已记录到 issue 板：
[杀伤链命中盒几何保真度缺口](../../issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)。
该 issue 的第一轮主线执行入口已按 geometry-only 验收门收口为
[missile_lethality_target_geometry/README.zh.md](missile_lethality_target_geometry/README.zh.md)。

MLF-8、MLF-9 和 MLF-10 均已验收并归档到 [archive/](archive/README.zh.md)；
旧 active 兼容指针目录已在 `2026-06-20` 移除，使根目录只保留 live 或 retained
follow-on。读取这些记录时使用本地 [archive registry](archive_registry.zh.md)。
不得继续写入已归档的 MLF-1 到 MLF-10 或近炸引信现实性包。这些 follow-on 不重开已封存
A2 包，也不创建 A9。

只有在明确 authority-promotion 或新 research 请求下才重开本线。默认空战工作继续从
[../README.zh.md](../README.zh.md) 进入。
