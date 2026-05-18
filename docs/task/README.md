# Task Docs

This directory is the repo-local navigation hub for task-oriented working
documents.

Language note:

- Active task docs are moving toward English canonical `.md` files with
  optional Chinese `.zh.md` companions.
- The policy lives in
  [docs/standards/governance/bilingual_documentation_policy.md](../standards/governance/bilingual_documentation_policy.md).
- The rollout plan lives in
  [docs/plan/documentation_bilingual_migration_plan_20260518.md](../plan/documentation_bilingual_migration_plan_20260518.md).

Most files here are dated snapshots of a specific analysis, freeze plan,
taskboard, checkpoint, or convergence pass. For the latest context in an area,
start from that area's `README.md` when it exists, or from the newest `current
status`, `taskboard`, or `progress checkpoint` document linked below.

For lifecycle cleanup across this tree, see the
[task archive and convergence plan](task_archive_convergence_plan_20260518.md).

## Area Navigation

- [flight_dynamics/](flight_dynamics/README.md): realism-track task navigation.
  Start with
  [current program status](flight_dynamics/program/realism_program_current_status_20260517.zh.md)
  and the
  [P1 taskboard](flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md).
- [performance_runtime/](performance_runtime/README.md): runtime-performance
  follow-on after the current realism freeze. Start from the local README for
  the current ladder, taskboard, and active Level-2 entry boundaries.
- [viz/](viz/README.md): active visualization unified-entry workline.
  Start from the local README, then continue into the active freeze/design
  plan for implementation boundaries and landed `WP-V4` / `WP-V5` status.
- [naval/](naval/README.md): active naval-realism workline. Start from the
  local README for the latest checkpoint, scenario-bound plan, and delegated
  backlog entrypoints.
- [review/](review/README.md): archived architecture review workline.
- [air_combat/](air_combat/README.md): active `1v1` air-combat workline.
  Start from the local README for the current status, then use the linked
  archive snapshots for the entry analysis, freeze, baseline progress, weapon
  chain, training smoke, and stall follow-up records.
- [common_air_naval/](common_air_naval/README.md): converged entry for the
  common/air/naval split workline. The active plan stays at the subproject
  root, while the superseded pre-implementation analysis now lives in the
  local archive.
- [code_redundancy/](code_redundancy/README.md): archived code-redundancy workline.
- [diagnostics_eval/](diagnostics_eval/README.md): archived diagnostics/eval convergence records.
- [python_rl/](python_rl/README.md): archived `python/rl` convergence records.

## Document Types

- `analysis` / `audit`: capture findings and rationale for a specific slice.
- `plan` / `freeze`: record the scoped implementation plan for that slice.
- `taskboard`: record the staged work breakdown for a line of work.
- `current status` / `progress checkpoint`: best entry points for the latest
  status captured in this tree.
- `convergence`: mostly implementation records kept for traceability rather
  than the default active plan.
- `archive`: superseded snapshots moved out of the default active path while
  still kept for traceability.
