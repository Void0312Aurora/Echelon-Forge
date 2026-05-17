# Task Docs

This directory is the repo-local navigation hub for task-oriented working
documents.

Most files here are dated snapshots of a specific analysis, freeze plan,
taskboard, checkpoint, or convergence pass. For the latest context in an area,
start from that area's `README.md` when it exists, or from the newest `current
status`, `taskboard`, or `progress checkpoint` document linked below.

## Area Navigation

- [flight_dynamics/](./flight_dynamics/README.md): 主线真实性任务导航。总览从
  [真实化主线与关联子项目当前状态](./flight_dynamics/program/realism_program_current_status_20260517.zh.md)
  和
  [真实化 P1 任务总表](./flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md)
  开始。
- [viz/](./viz/viz_unified_entry_session_profile_plan_20260516.zh.md):
  可视化统一入口与会话化重构冻结计划。
- [naval/](./naval/naval_progress_checkpoint_20260517.zh.md): 当前状态入口为
  [海战推进检查点](./naval/naval_progress_checkpoint_20260517.zh.md)；相关规划见
  [海战现实性分层清单与当前场景下一步计划](./naval/naval_realism_layering_and_next_step_plan_20260516.zh.md)
  和
  [海战后续委派执行单](./naval/naval_delegated_execution_backlog_20260517.zh.md)。
- [review/](./review/architecture_review_20260516.zh.md): 架构审查入口，后续范围冻结见
  [架构评审后续冻结计划](./review/architecture_review_followup_freeze_20260516.zh.md)。
- [air_combat/](./air_combat/air_combat_1v1_entry_analysis_20260516.zh.md): 空战
  `1v1` 入口分析；同目录下还包括
  [冻结计划](./air_combat/air_combat_1v1_freeze_plan_20260516.zh.md)、
  [武器链进展](./air_combat/air_combat_1v1_weapon_chain_progress_20260516.zh.md)、
  [F-16C 基线切换与最小对战合同进展](./air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)、
  [stall 根因后续跟进](./air_combat/air_combat_1v1_stall_rootcause_followup_20260516.zh.md)、
  [training smoke 进展](./air_combat/air_combat_1v1_training_smoke_progress_20260516.zh.md)
  和
  [空战场景级 Ammo 设计与落地](./air_combat/air_combat_scenario_level_ammo_design_20260516.zh.md)。
- [common_air_naval/](./common_air_naval/common_air_naval_modular_split_analysis_20260515.zh.md):
  模块拆分分析与
  [冻结计划](./common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md)。
- [code_redundancy/](./code_redundancy/code_redundancy_duplication_audit_20260516.zh.md):
  代码冗余审计与
  [优化后续冻结计划](./code_redundancy/code_redundancy_followup_freeze_20260516.zh.md)。
- [diagnostics_eval/](./diagnostics_eval/diagnostics_modularization_20260515.zh.md):
  Diagnostics / Eval 入口收敛相关文档，包括
  [Diagnostics 收敛与模块化计划](./diagnostics_eval/diagnostics_modularization_20260515.zh.md)、
  [Diagnostics Benchmark CLI 收敛计划](./diagnostics_eval/diagnostics_benchmark_cli_convergence_20260515.zh.md)
  和
  [Eval 与 Diagnostic 入口收敛主计划](./diagnostics_eval/eval_entrypoint_convergence_20260515.zh.md)。
- [python_rl/](./python_rl/python_rl_tasking_domain_convergence_20260515.zh.md):
  `python/rl` 子域收敛记录导航；这些文档主要是实现收敛记录，不应默认视为当前活跃计划。

## Document Types

- `analysis` / `audit`: capture findings and rationale for a specific slice.
- `plan` / `freeze`: record the scoped implementation plan for that slice.
- `taskboard`: record the staged work breakdown for a line of work.
- `current status` / `progress checkpoint`: best entry points for the latest
  status captured in this tree.
- `convergence`: mostly implementation records kept for traceability rather
  than the default active plan.
