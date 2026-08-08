# `architecture/`

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

本目录存放严格仿真系统架构基线、架构主方案、性能路线调研与已归档的 `src/` 分层记录。

当前架构定位：

- Echelon Forge 被定位为语义-因果仿真编译器与学习平台。
- 维护中的 runtime kernel 按 SCAL 四面组织：semantic、causal、agentic 与 learning-facing architecture。
- temporal DAG 是更大 graph-of-graphs 模型中的执行投影；该模型还覆盖 semantic、causal、information、agency、evidence 与未来 learning graph。
- backend acceleration、resident-state 与 shadow 风格工作必须先引用已验收的
  WP6 backend profile registry 与 parity budget，才能成为维护中的 capability。
  WP6 证据已经是归档任务历史；参见
  [resident-state 边界规则](../../../../task/simulation_architecture/archive/wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)
  与 [WP6 验收审查](../../../../task/review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)。
- WP6 之后的实现准备证据是已归档的
  [WP7 后端能力物化](../../../../task/simulation_architecture/archive/wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.zh.md)
  线，覆盖可机器检查 registry materialization、保守 runtime capability
  projection、promotion evidence gate 与 multi-fidelity entry conditions，但不
  晋级候选能力；其
  [验收审查](../../../../task/review/archive/wp-acceptance/wp7_backend_capability_materialization_acceptance_review_20260519.zh.md)
  只验收文档与实现准备状态，当前 exact GPU、resident-state、shadow、device
  observation 与 multi-fidelity support 仍为 false。
- 将该定位转成实现工作的活跃任务线是
  [docs/task/simulation_architecture/](../../../../task/simulation_architecture/README.zh.md)。

推荐阅读顺序：

1. [simulation_system_architecture_design.md](../../../../architecture/standards/simulation_system_architecture_design.md)
2. [simulation_system_architecture_design.zh.md](../../../../architecture/standards/simulation_system_architecture_design.zh.md)
3. [system_layering_and_engine_encapsulation_plan.md](../../../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.md)
4. [system_layering_and_engine_encapsulation_plan.zh.md](../../../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md)
5. [architecture_and_performance_research_followup.md](../../../../architecture/work/issues/architecture_and_performance_research_followup.md)
6. [architecture_and_performance_research_followup.zh.md](../../../../architecture/work/issues/architecture_and_performance_research_followup.zh.md)
7. [archive/src_layered_refactor_freeze.zh.md](../../architecture/src_layered_refactor_freeze.zh.md)

使用规则：

- 本目录的目标稳态是“英文 `.md` 为主、中文 `.zh.md` 为辅”。
- 在迁移完成前，部分长文仍只有 `.zh.md`，它们可作为过渡输入使用，但应在后续批次中补齐英文 peer。
- 调研文档提供论据与路线排序，不直接授权实现。
- 冻结计划已完成部分视为执行记录；新增范围需另行冻结。
- 仿真系统设计是当前严格架构基线。大范围实现工作应先收敛为
  [docs/task/simulation_architecture/](../../../../task/simulation_architecture/README.zh.md)
  下的有边界任务单。
