# Task Docs

This directory is the repo-local navigation hub for task-oriented working
documents.

Language note:

- The stable task navigation surface is moving toward English canonical `.md`
  files with optional Chinese `.zh.md` companions.
- High-churn dated task docs under `docs/task/**` are English-canonical by
  default unless a narrower slice is explicitly promoted into the maintained
  bilingual surface.
- The policy lives in
  [docs/standards/governance/bilingual_documentation_policy.md](../standards/governance/bilingual_documentation_policy.md).
- The rollout plan lives in
  [docs/plan/documentation_bilingual_migration_plan_20260518.md](../plan/documentation_bilingual_migration_plan_20260518.md).

Most files here are dated snapshots of a specific analysis, freeze plan,
taskboard, checkpoint, or convergence pass. For the latest context in an area,
start from that area's `README.md` when it exists. Treat deeper dated docs as
supporting records, not as stable root-level entrypoints.

For lifecycle cleanup across this tree, see the
[task archive and convergence plan](task_archive_convergence_plan_20260518.md).

## Area Navigation

- [flight_dynamics/](flight_dynamics/README.md): realism-track task navigation.
  Start from the local README and then continue into the active subproject
  README pages such as `flight/`, `sensor_situation/`, `weapon_guidance/`,
  `naval/`, and `c2_command_chain/`.
- [performance_runtime/](performance_runtime/README.md): runtime-performance
  follow-on after the current realism freeze. Start from the local README for
  the current ladder, taskboard provenance, and active entry boundaries.
- [viz/](viz/README.md): active visualization unified-entry workline.
  Start from the local README; treat the archived freeze/design snapshot as
  traceability material rather than a root-level stable entrypoint.
- [naval/](naval/README.md): active naval-realism workline. Start from the
  local README for the current interpretation of archived checkpoints and
  backlog material.
- [review/](review/README.md): archived architecture review workline.
- [air_combat/](air_combat/README.md): active `1v1` air-combat workline.
  Start from the local README for the current status, then use the linked
  archive snapshots only for traceability.
- [common_air_naval/](common_air_naval/README.md): converged entry for the
  common/air/naval split workline. The local README separates the still-active
  carry-over plan from the superseded pre-implementation analysis in archive.
- [ground/](ground/README.md): planning entry for the future ground-domain
  bootstrap. Start here to align naming, scope, and cross-cutting additions
  before any dedicated ground implementation begins.
- [simulation_architecture/](simulation_architecture/README.md): active
  simulation-system architecture workline. Start here before turning the
  canonical pipeline design into broad weapon, naval, sensor/track, facade, or
  backend work.
- [model/](model/README.md): active model-side planning line for temporal
  HMoE/sequence policy work. Start here when RL behavior needs policy memory
  rather than environment-side tactical memory boards.
- [issues/](issues/README.md): active cross-cutting issue board for problems
  that should remain visible across domain, runtime, model, training, and eval
  worklines.
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
