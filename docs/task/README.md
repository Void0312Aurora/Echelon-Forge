# Task Docs

This directory is the repo-local navigation hub for task-oriented working
documents.

Language note:

- Active task docs are moving toward English canonical `.md` files with
  optional Chinese `.zh.md` companions.
- The policy lives in
  [docs/standards/bilingual_documentation_policy.md](../standards/bilingual_documentation_policy.md).
- The rollout plan lives in
  [docs/plan/documentation_bilingual_migration_plan_20260518.md](../plan/documentation_bilingual_migration_plan_20260518.md).

Most files here are dated snapshots of a specific analysis, freeze plan,
taskboard, checkpoint, or convergence pass. For the latest context in an area,
start from that area's `README.md` when it exists, or from the newest `current
status`, `taskboard`, or `progress checkpoint` document linked below.

## Area Navigation

- [flight_dynamics/](./flight_dynamics/README.md): realism-track task navigation.
  Start with
  [current program status](./flight_dynamics/program/realism_program_current_status_20260517.zh.md)
  and the
  [P1 taskboard](./flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md).
- [viz/](./viz/viz_unified_entry_session_profile_plan_20260516.zh.md):
  unified visualization entry and session-oriented refactor freeze plan.
- [naval/](./naval/naval_progress_checkpoint_20260517.zh.md): latest status starts at the
  [naval progress checkpoint](./naval/naval_progress_checkpoint_20260517.zh.md);
  related planning lives in the
  [naval realism layering and next-step plan](./naval/naval_realism_layering_and_next_step_plan_20260516.zh.md)
  and the
  [delegated execution backlog](./naval/naval_delegated_execution_backlog_20260517.zh.md).
- [review/](./review/architecture_review_20260516.zh.md): architecture review entrypoint;
  follow-on scope freeze lives in the
  [architecture review follow-up freeze](./review/architecture_review_followup_freeze_20260516.zh.md).
- [air_combat/](./air_combat/air_combat_1v1_entry_analysis_20260516.zh.md):
  air-combat `1v1` entry analysis, with sibling docs for the
  [freeze plan](./air_combat/air_combat_1v1_freeze_plan_20260516.zh.md),
  [weapon-chain progress](./air_combat/air_combat_1v1_weapon_chain_progress_20260516.zh.md),
  [F-16C baseline switch and minimum duel contract progress](./air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md),
  [stall root-cause follow-up](./air_combat/air_combat_1v1_stall_rootcause_followup_20260516.zh.md),
  [training smoke progress](./air_combat/air_combat_1v1_training_smoke_progress_20260516.zh.md),
  and
  [scenario-level ammo design](./air_combat/air_combat_scenario_level_ammo_design_20260516.zh.md).
- [common_air_naval/](./common_air_naval/common_air_naval_modular_split_analysis_20260515.zh.md):
  modular split analysis and
  [freeze plan](./common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md).
- [code_redundancy/](./code_redundancy/code_redundancy_duplication_audit_20260516.zh.md):
  redundancy audit and the
  [follow-up freeze plan](./code_redundancy/code_redundancy_followup_freeze_20260516.zh.md).
- [diagnostics_eval/](./diagnostics_eval/diagnostics_modularization_20260515.zh.md):
  diagnostics/eval entrypoint convergence docs, including the
  [diagnostics modularization plan](./diagnostics_eval/diagnostics_modularization_20260515.zh.md),
  [benchmark CLI convergence plan](./diagnostics_eval/diagnostics_benchmark_cli_convergence_20260515.zh.md),
  and
  [eval/diagnostic entry convergence main plan](./diagnostics_eval/eval_entrypoint_convergence_20260515.zh.md).
- [python_rl/](./python_rl/python_rl_tasking_domain_convergence_20260515.zh.md):
  `python/rl` subdomain convergence records. Treat these mostly as implementation
  trace records rather than the default active plan.

## Document Types

- `analysis` / `audit`: capture findings and rationale for a specific slice.
- `plan` / `freeze`: record the scoped implementation plan for that slice.
- `taskboard`: record the staged work breakdown for a line of work.
- `current status` / `progress checkpoint`: best entry points for the latest
  status captured in this tree.
- `convergence`: mostly implementation records kept for traceability rather
  than the default active plan.
