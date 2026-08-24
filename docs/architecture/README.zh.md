# 架构文档

语言：[英文规范页](README.md)；本页为中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-23`

本 owner 覆盖跨领域系统架构、runtime 分层、contracts、后端和架构决策。
维护中的 standards、reference、issues 与 reviews 现均位于本 owner；旧 plan
packet 只作为归档 provenance。

## Standards

- [仿真约定](standards/simulation_conventions.zh.md)：维护中的引擎中立坐标、单位、观测、
  array、action 与确定性约定。
- [Runtime workflow 与 contract 基线](standards/runtime_workflow_and_contract_baseline.zh.md)：
  维护 loader 到 runtime 的阶段归属与 roundtrip seam，并服从严格仿真架构基线。
- [仿真系统架构设计](standards/simulation_system_architecture_design.zh.md)：
  严格维护中的分层、权威与 runtime 基线。
- [Runtime composition 基线](standards/runtime_composition_baseline.zh.md)：维护中的默认
  CPU-exact Cordis/owner/native 权威链、单一构造真值、兼容规则、证据 gate 与 held 残余。

## Reference

- [Truth-leak 清单](reference/t8_g4_truth_leak_inventory.zh.md)：当前 declared/open
  权威泄漏及其验证边界。

## 已完成工作

- [Cordis 仿真组合内核](work/archive/cordis_simulation_composition_kernel/README.zh.md)：
  已接受的有界默认 CPU-exact composition 计划与历史实现证据。当前权威是上面的
  runtime composition standard；Node、CUDA、更广 profile/provider、外部 plugin 与完整
  replay 继续作为 held 残余。

## 开放问题

- [系统模块化 issue](work/issues/modularization_plan.zh.md)：draft residual 分析；
  目录位置不授权实施。
- [系统分层与引擎封装](work/issues/system_layering_and_engine_encapsulation_plan.zh.md)
- [架构与性能研究后续](work/issues/architecture_and_performance_research_followup.zh.md)
- [Runtime facade contract](work/issues/runtime_facade_contract_plan.zh.md)
- [C++ 依赖与 DTO 残差](work/issues/cpp_dependency_and_dto_residuals.zh.md)
- [Exact-runtime refactor](work/issues/exact_runtime/cpp_exact_runtime_refactor_plan.zh.md)
- [GPU 主线集成检查表](work/issues/exact_runtime/gpu_execution_mainline_integration_checklist.zh.md)

## 评审

- [Cordis 仿真组合计划架构审阅 — 2026-08-17](reviews/cordis_simulation_composition_program_review_20260817.zh.md)：
  总体咨询性审阅；保留原生 composition 方向，但要求在后续 system/plugin/host
  阶段前修订权威与计划边界。
- [Cordis 仿真组合计划架构审阅回复 — 2026-08-17](reviews/cordis_simulation_composition_program_review_response_20260817.zh.md)：
  active owner 的正式处置；吸收权威、typed admission、capability、evidence timing 与
  独立切片 finding，同时保留 Cordis 作为必需战略组合目标，并让 Node 保持 conditional。
- [架构评审 — 2026-06-03](reviews/architecture_review_20260603.zh.md)
- [架构规范性与正确性评审 — 2026-06-03](reviews/architecture_norms_correctness_review_20260603.zh.md)
- [架构重构审计 — 2026-05-22](reviews/architecture_refactoring_audit_20260522.zh.md)
- [UniversalEnv caller 存续表 — 2026-06-12（仅中文）](reviews/universal_env_runtime_compatibility_caller_survival_table_20260612.zh.md)

这些文档是保留的评审快照，不能替代当前 standards、plans、实现或可执行证据。

未来架构 standard、reference、work 和 review 使用
[共享文档结构](../engineering/documentation/structure_examples.zh.md)。
