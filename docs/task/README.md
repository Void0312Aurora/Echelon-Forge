# Task Docs

This directory stores short-lived task documents that freeze scope, record
findings, and track the implementation status of focused cleanup or feature
work.

Rules for documents here:

- Prefer one task per document.
- Record the concrete problem statement and the trusted findings first.
- Freeze a narrow implementation scope before editing code.
- Mark what is intentionally deferred so cleanup work does not sprawl.
- Keep links pointing to the relevant code and follow-up plans.

Current task documents:

- `flight_dynamics/`
  [flight_dynamics 文档导航](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/README.md)
  [真实化主线与关联子项目当前状态](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_current_status_20260517.zh.md)
  [真实化 P1 任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md)
  [program 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/README.md)
  [flight 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/flight/README.md)
  [sensor_situation 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/sensor_situation/README.md)
  [weapon_guidance 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/weapon_guidance/README.md)
  [naval 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/naval/README.md)
  [c2_command_chain 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/README.md)
- `viz/`
  [可视化统一入口与会话化重构冻结计划](/home/void0312/Workshop/CMO/docs/task/viz/viz_unified_entry_session_profile_plan_20260516.zh.md)
- `naval/`
  [海战现实性分层清单与当前场景下一步计划](/home/void0312/Workshop/CMO/docs/task/naval/naval_realism_layering_and_next_step_plan_20260516.zh.md)
  [海战后续委派执行单](/home/void0312/Workshop/CMO/docs/task/naval/naval_delegated_execution_backlog_20260517.zh.md)
  [海战推进检查点](/home/void0312/Workshop/CMO/docs/task/naval/naval_progress_checkpoint_20260517.zh.md)
- `review/`
  [项目结构与架构设计审查报告](/home/void0312/Workshop/CMO/docs/task/review/architecture_review_20260516.zh.md)
  [架构评审后续冻结计划](/home/void0312/Workshop/CMO/docs/task/review/architecture_review_followup_freeze_20260516.zh.md)
- `air_combat/`
  [空战 1v1 切入分析](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_entry_analysis_20260516.zh.md)
  [空战 1v1 冻结计划](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_freeze_plan_20260516.zh.md)
  [空战 1v1 武器链进展](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_weapon_chain_progress_20260516.zh.md)
  [空战 1v1 F-16C 基线切换与最小对战合同进展](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)
  [空战场景级 Ammo 设计与落地](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_scenario_level_ammo_design_20260516.zh.md)
- `common_air_naval/`
  [Common / Air / Naval 模块拆分分析](/home/void0312/Workshop/CMO/docs/task/common_air_naval/common_air_naval_modular_split_analysis_20260515.zh.md)
  [Common / Air / Naval 模块拆分冻结计划](/home/void0312/Workshop/CMO/docs/task/common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md)
- `code_redundancy/`
  [代码冗余与重复逻辑审计报告](/home/void0312/Workshop/CMO/docs/task/code_redundancy/code_redundancy_duplication_audit_20260516.zh.md)
  [代码冗余优化后续冻结计划](/home/void0312/Workshop/CMO/docs/task/code_redundancy/code_redundancy_followup_freeze_20260516.zh.md)
- `diagnostics_eval/`
  [Diagnostics 收敛与模块化计划](/home/void0312/Workshop/CMO/docs/task/diagnostics_eval/diagnostics_modularization_20260515.zh.md)
  [Diagnostics Benchmark CLI 收敛计划](/home/void0312/Workshop/CMO/docs/task/diagnostics_eval/diagnostics_benchmark_cli_convergence_20260515.zh.md)
  [Eval 与 Diagnostic 入口收敛主计划](/home/void0312/Workshop/CMO/docs/task/diagnostics_eval/eval_entrypoint_convergence_20260515.zh.md)
- `python_rl/`
  [python/rl Tasking 子域收敛分析与第一阶段实现冻结](/home/void0312/Workshop/CMO/docs/task/python_rl/python_rl_tasking_domain_convergence_20260515.zh.md)
  [python/rl tasking 子域入箱收敛记录](/home/void0312/Workshop/CMO/docs/task/python_rl/python_rl_tasking_subfolder_convergence_20260515.zh.md)
  [python/rl runtime 子域第一阶段收敛记录](/home/void0312/Workshop/CMO/docs/task/python_rl/python_rl_runtime_subfolder_convergence_20260516.zh.md)
  [python/rl runtime 子域第二阶段收敛记录](/home/void0312/Workshop/CMO/docs/task/python_rl/python_rl_runtime_phase2_convergence_20260516.zh.md)
  [python/rl 根级 shim 调用点收敛记录](/home/void0312/Workshop/CMO/docs/task/python_rl/python_rl_root_shim_callsite_convergence_20260516.zh.md)
  [python/rl control 子域入箱收敛记录](/home/void0312/Workshop/CMO/docs/task/python_rl/python_rl_control_subfolder_convergence_20260516.zh.md)
  [python/rl planning 与 support 子域收敛记录](/home/void0312/Workshop/CMO/docs/task/python_rl/python_rl_planning_support_subfolder_convergence_20260516.zh.md)
  [python/rl policy_algo 子域收敛记录](/home/void0312/Workshop/CMO/docs/task/python_rl/python_rl_policy_algo_subfolder_convergence_20260516.zh.md)

Guidance:

- `analysis` / `audit` documents capture findings and rationale.
- `plan` / `freeze` documents define the frozen implementation scope for a line of work.
- `convergence` documents are mostly completed implementation records; keep them for traceability, but do not treat them as current active plans unless a new task explicitly reopens that line.
