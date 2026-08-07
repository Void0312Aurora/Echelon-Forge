# Task Docs

This directory is the repo-local navigation hub for task-oriented working
documents. Use this root as an area selector, not as a chronological taskboard
or a single-domain roadmap.

The project narrative is now multi-domain. Air execution is currently the most
mature domain execution slice; cooperative/common integration is the current
shared-tasking convergence line that began with common/air/naval; naval N4 is a
closed pre-fire line; ground is an early tasking/runtime bootstrap with native
platform-schema evidence but no full land runtime; visualization and game work
are exploratory presentation surfaces; model work is the policy/world-model
planning surface; and `review/` plus `issues/` are the governance surface.
Older `flight_dynamics/` and dated `air_combat/` snapshots remain useful
records, but they are not the repo-wide center of gravity.

Language note:

- The stable task navigation surface is moving toward English canonical `.md`
  files with optional Chinese `.zh.md` companions.
- High-churn dated task docs under `docs/task/**` are English-canonical by
  default unless a narrower slice is explicitly promoted into the maintained
  bilingual surface.
- The policy lives in
  [docs/engineering/documentation/standards/bilingual_documentation_policy.md](../engineering/documentation/standards/bilingual_documentation_policy.md).

Most files here are dated snapshots of a specific analysis, freeze plan,
taskboard, checkpoint, or convergence pass. For the latest context in an area,
start from that area's `README.md` when it exists. Treat deeper dated docs as
supporting records, not as stable root-level entrypoints.

For lifecycle cleanup across this tree, see the
[task archive and convergence plan](task_archive_convergence_plan_20260518.md).

## Lifecycle Labels

- `active`: maintained implementation, integration, or review line with current
  entry gates.
- `planning`: scoped roadmap or bootstrap line before broad runtime release.
- `exploratory`: presentation, frontend, or prototype line whose output must
  not become authoritative simulation semantics by accident.
- `archived`: frozen, superseded, or historical material kept for traceability.
- `governance`: cross-cutting review, issue, or acceptance-control surface.

## Task-Area Layers

### Execution And Integration

- [air_combat/](air_combat/README.md): `active` air/execution entry and the
  current highest maturity domain execution slice. Start here for the maintained
  `execution` / HMoE `1v1` path, staged `1v1` curriculum, and air-combat damage
  runtime. Use linked archive snapshots only for traceability; do not treat old
  air-combat snapshots as the whole-project center.
- [common_air_naval/](archive/common_air_naval/common_air_naval_modular_split_plan_20260515.md): `archived` —
  WP0-WP8 complete (common/air/naval DTO split, profile dispatch seam,
  MissionCommand compatibility split). Residual naval runtime expansion and
  air-first helper migration continue via standalone task sheets.
  analysis in archive.
- [simulation_architecture/](simulation_architecture/README.md): `active`
  simulation-system architecture and runtime-lifecycle backbone. Start here
  before broad weapon, naval, sensor/track, facade, backend, or cross-domain
  runtime work. Closed temporary architecture lanes now live under its
  `archive/` index instead of as top-level task entries.
- [naval/](naval/README.md): `active` medium-high maturity naval workline. N4 is
  closed as a pre-fire threat/ROE bridge and active training-entry gate; the
  first RL action/observation repair is retained as an accepted N4 evidence
  record, while current surface-split work continues in the domain-surface
  package. Limited engagement remains a separate N5 package, not an excuse to
  reopen N4.
- [performance_runtime/](archive/performance_runtime/README.md): `archived` —
  optimization layering and benchmark-oriented analysis frozen; legacy planning
  chain treated as reference material.
  runtime-performance line. Use it for optimization ordering, benchmark
  boundaries, and hot-path analysis; archived planning chains are reference
  material, not active execution entrypoints.

### Bootstrap And Policy Planning

- [ground/](ground/README.md): `planning` / early `active` ground tasking and
  runtime bootstrap. G0-G6 accepted subprojects are sealed evidence records;
  movement, sensing, terrain, fires, damage, and broad runtime expansion remain
  explicitly held behind later gates.
- [model/](model/README.md): `planning` policy/world-model surface for temporal
  HMoE and sequence-policy work. Start here when behavior needs policy memory or
  world-model planning, rather than environment-side tactical memory boards.

### Exploratory Presentation

- [viz/](viz/README.md): `exploratory` / `active` visualization unified-entry
  surface. It is for display, asset registry, loader/session flow, and runtime
  inspection convenience, not realism or world-parameter authority.
- [game/](../../game/README.md): `exploratory` external-game frontend integration.
  Start here for simulation-backed gameplay shells, the tracked Arma proxy
  workspace boundary, local-only frontend archive rules, or
  authoritative-backend proxy experiments.

### Governance

- [review/](review/README.md): `governance` review and acceptance-record
  surface. Current reviews and roadmap records stay at the local README; the
  local archive holds completed or superseded review snapshots.
- [issues/](issues/README.md): `governance` cross-cutting issue board for
  problems that should remain visible across domain, runtime, model, training,
  and evaluation worklines. Closed-but-reusable findings live as retained
  tracking items rather than active issues.

### Reference And Archive

- [flight_dynamics/](flight_dynamics/README.md): `archived` / reference realism
  analysis navigation for flight, sensor/situation, weapon/guidance, naval, and
  C2 closure records. Use it for historical context and closure markers, not as
  the active root of project planning.
- [code_redundancy/](archive/code_redundancy/README.md): `archived` code-redundancy
  workline.
- [diagnostics_eval/](archive/diagnostics_eval/README.md): `archived` diagnostics/eval
  convergence records.
- [python_rl/](archive/python_rl/README.md): `archived` `python/rl` convergence records.
- [game/](archive/game/README.md): `archived` game frontend integration exploration.

For the full archived subproject catalog with work descriptions, see the
[Archive Registry](archive_registry.md).

## Working Rules

1. Start from the local `README.md` for the task area that matches the work.
2. Treat deeper dated docs as evidence, closure records, or supporting plans
   unless a local README explicitly promotes them.
3. When a task crosses domains, route the cross-cutting decision through
   `simulation_architecture/`, `review/`, or `issues/`
   instead of overloading an old air-first entry.
4. When an area's lifecycle changes, update that local README first, then adjust
   this root navigation.
5. Completed subprojects should be moved into that area's `archive/` when doing
   so does not break active gates; otherwise, demote them in the parent README
   to sealed, retained, or archived records and open follow-on work elsewhere.

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
