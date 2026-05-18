<!-- Machine-translated draft generated on 2026-05-18 from docs/task/README.md. Review before treating this file as authoritative. -->

# 任务文档

本目录是面向任务的工作文档的仓库本地导航中心。

语言说明：

- 当前任务文档正朝着以英文规范 `.md` 文件为主、可选中文 `.zh.md` 配套文件的方向发展。
- 该策略位于 [docs/standards/bilingual_documentation_policy.md](../standards/bilingual_documentation_policy.md)。
-  rollout 计划位于 [docs/plan/documentation_bilingual_migration_plan_20260518.md](../plan/documentation_bilingual_migration_plan_20260518.md)。

此处大部分文件是特定分析、冻结计划、任务板、检查点或收敛过程的带日期快照。如需某个领域的最新上下文，请从该领域的 `README.md`（如果存在）开始，或从下方链接的最新“当前状态”、“任务板”或“进度检查点”文档开始。

## 领域导航

- [飞行动力学/](./flight_dynamics/README.md)：真实度跟踪任务导航。从[当前程序状态](./flight_dynamics/program/realism_program_current_status_20260517.zh.md)和[P1 任务板](./flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md)开始。
- [可视化/](./viz/viz_unified_entry_session_profile_plan_20260516.zh.md)：统一可视化入口及面向会话的重构冻结计划。
- [海军/](./naval/naval_progress_checkpoint_20260517.zh.md)：最新状态始于[海军进度检查点](./naval/naval_progress_checkpoint_20260517.zh.md)；相关计划位于[海军真实度分层与下一步计划](./naval/naval_realism_layering_and_next_step_plan_20260516.zh.md)和[委托执行积压](./naval/naval_delegated_execution_backlog_20260517.zh.md)。
- [审查/](./review/architecture_review_20260516.zh.md)：架构审查入口；后续范围冻结位于[架构审查后续冻结](./review/architecture_review_followup_freeze_20260516.zh.md)。
- [空战/](./air_combat/air_combat_1v1_entry_analysis_20260516.zh.md)：空战 `1v1` 入口分析，附带兄弟文档：[冻结计划](./air_combat/air_combat_1v1_freeze_plan_20260516.zh.md)、[武器链进展](./air_combat/air_combat_1v1_weapon_chain_progress_20260516.zh.md)、[F-16C 基线切换与最小决斗契约进展](./air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)、[失速根本原因跟进](./air_combat/air_combat_1v1_stall_rootcause_followup_20260516.zh.md)、[训练烟雾进展](./air_combat/air_combat_1v1_training_smoke_progress_20260516.zh.md)及[场景级弹药设计](./air_combat/air_combat_scenario_level_ammo_design_20260516.zh.md)。
- [通用空海军/](./common_air_naval/common_air_naval_modular_split_analysis_20260515.zh.md)：模块化拆分分析及[冻结计划](./common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md)。
- [代码冗余/](./code_redundancy/code_redundancy_duplication_audit_20260516.zh.md)：冗余审计及[后续冻结计划](./code_redundancy/code_redundancy_followup_freeze_20260516.zh.md)。
- [诊断评估/](./diagnostics_eval/diagnostics_modularization_20260515.zh.md)：诊断/评估入口收敛文档，包括[诊断模块化计划](./diagnostics_eval/diagnostics_modularization_20260515.zh.md)、[基准 CLI 收敛计划](./diagnostics_eval/diagnostics_benchmark_cli_convergence_20260515.zh.md)和[评估/诊断入口收敛主计划](./diagnostics_eval/eval_entrypoint_convergence_20260515.zh.md)。
- [Python 强化学习/](./python_rl/python_rl_tasking_domain_convergence_20260515.zh.md)：`python/rl` 子域收敛记录。多视为实现追踪记录，而非默认的活跃计划。

## 文档类型

- `分析` / `审计`：捕捉特定片段的发现和理由。
- `计划` / `冻结`：记录该片段的范围化实现计划。
- `任务板`：记录某条工作线的分阶段工作分解。
- `当前状态` / `进度检查点`：进入此树中最新状态的最佳入口点。
- `收敛`：主要为保持可追溯性而保留的实现记录，而非默认的活跃计划。
