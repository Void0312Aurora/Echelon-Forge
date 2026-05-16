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
