# Task Archive and Convergence Plan

Status: `2026-06-02` audited lifecycle update; original planning version was
`2026-05-18`.
Scope: `docs/task/*`
Reference pattern: [flight_dynamics archive](../../flight_dynamics/archive/README.md)

Audit update: `2026-06-02` read-only subagent lifecycle check completed. A
follow-up physical archive move reduced selected completed evidence-package
paths to lightweight pointers.

Positioning:

- This document evaluates which task-doc subprojects should remain active, be
  converged to a single entry point, or be moved to archive.
- This is a documentation-lifecycle plan only. It does not itself authorize
  file moves or content rewrites.

## Goals

1. Reduce the number of stale dated snapshots exposed as default entry points.
2. Keep one clear active entry doc per live area.
3. Preserve traceability by moving historical snapshots instead of deleting
   them.

## Decision Rules

- Keep active: the area has a recent `current status`, `progress checkpoint`,
  or `taskboard`, and that doc still drives next implementation work.
- Converge first: the area still has open work, but multiple dated docs are
  competing as entry points. Add a local `README.md` or a single
  `current_status` doc first, then archive older siblings.
- Archive now: the area's docs explicitly say phases are completed, all scoped
  work packages are closed, or future work must restart from a new freeze doc
  rather than extending the old one.

## Archive Pattern

- Reuse the `flight_dynamics/archive/` pattern before inventing a repo-wide
  cold-storage tree.
- Prefer a local `<subproject>/archive/` directory so existing relative links
  survive with minimal churn.
- Keep a small `<subproject>/README.md` at the subproject root as the only
  active entry point for archived or mostly archived areas.
- Do not rewrite historical judgments inside archived dated docs. Add a new
  convergence or current-status doc instead.

## 2026-06-02 Subagent Audit Update

Four read-only diagnostics subagents checked the current `docs/task` subproject
set against the local `README`, status, closure, acceptance, and archive-index
files. The audit treated maintained `README` files and executable/acceptance
evidence as higher authority than older dated planning text.

Outcome:

- Already archived in place: `code_redundancy/`, `diagnostics_eval/`, and
  `python_rl/` now have archived-record root entries plus local `archive/`
  indexes. No further move is needed.
- Physically moved to local archive with lightweight pointers left behind:
  `air_combat/a2_high_fidelity_damage_model/`,
  `naval/n4_threat_roe_bridge/`, `naval/n5_rl_action_surface_split/`, and the
  accepted `ground/g0` through `g6` evidence records.
- Completed or accepted but intentionally retained in place:
  `model/m1_action_interface_split/` and
  `issues/rl_policy_hold_baseline_drift/`. These are retained because parent
  task entries, current gates, or follow-on evidence chains still cite them.
- Active or mixed, not archive-ready as whole areas: `air_combat/` and
  `air_combat/a1_1v1_realism_gradient/`, `common_air_naval/`,
  `flight_dynamics/` and its live analysis subdirs, `viz/`, `game/`,
  `ground/`, `model/`, `model/m1_temporal_window_hmoe/`,
  `model/m2_causal_transformer_hmoe/`, `naval/`,
  `naval/naval_domain_surface_split/`, `performance_runtime/`,
  `simulation_architecture/`, `review/`, and `issues/`.

Archive decision:

- The selected completed evidence directories now live under their parent
  `archive/` directories. Their original paths contain brief work statements
  and pointers to the full archived packet.
- Future archive work should follow the same shape: first add or update the
  local archive index, then update parent entry links, and only then replace
  evidence-package roots with lightweight pointers.

## Assessment by Area

### Archived In Place

- `code_redundancy/`: the
  [follow-up freeze](../code_redundancy/archive/code_redundancy_followup_freeze_20260516.md)
  says `WP-A / WP-B / WP-C` are all closed and no active implementation items
  remain. The area now has a root `README` and local `archive/` index; future
  work should start from a new freeze doc.
- `diagnostics_eval/`: the
  [diagnostics modularization](../diagnostics_eval/archive/diagnostics_modularization_20260515.md),
  [eval entrypoint convergence](../diagnostics_eval/archive/eval_entrypoint_convergence_20260515.md),
  and
  [benchmark CLI convergence](../diagnostics_eval/archive/diagnostics_benchmark_cli_convergence_20260515.md)
  all mark their phases completed. The area now has a root `README` and local
  `archive/` index.
- `python_rl/`: these docs are convergence records for migrations that are
  already completed or closed. The area now has a root `README` and local
  `archive/` index, and the top-level task index describes it as trace records
  rather than the default active plan.
- `air_combat/a2_high_fidelity_damage_model/`: the full research/candidate
  package now lives under
  [air_combat/archive/a2_high_fidelity_damage_model/](../../air_combat/archive/a2_high_fidelity_damage_model/README.md),
  while the original path is a lightweight pointer.
- `naval/n4_threat_roe_bridge/` and `naval/n5_rl_action_surface_split/`: the
  full evidence packets now live under
  [naval/archive/](../../naval/archive/README.md), while the original paths are
  lightweight pointers.
- Accepted ground G0-G6 evidence records: the full packets now live under
  [ground/archive/](../../ground/archive/README.md), while the original phase paths
  are lightweight work statements.

`review/` is no longer treated as a whole-area archive candidate. Its pre-WP
[architecture review](../../review/archive/pre-wp/architecture_review_20260516.md)
and
[follow-up freeze](../../review/archive/pre-wp/architecture_review_followup_freeze_20260516.md)
are archived snapshots, while the `review/` root remains an active governance
record.

### Converge First, Then Partially Archive

- `air_combat/`: convergence entry and archive separation are now in place. The
  root remains active for the staged `1v1` workline; `a1_1v1_realism_gradient/`
  is active/planning; `a2_high_fidelity_damage_model/` is a pointer to a sealed
  archived research/candidate record. Do not archive the whole tree.
- `common_air_naval/`: convergence entry and archive separation are now in
  place. The foundation is complete, but broader runtime/tooling,
  `tests/contracts`, and future naval expansion carry-over remain active.
- `viz/`: local `README` is now the current entry. It intentionally promotes one
  plan under `archive/` as the active implementation boundary, so do not move it
  again without first replacing the promoted entry.

### Keep Active

- `naval/`: N4 and the first RL action/observation repair are closed or
  accepted and now physically archived with original-path pointers. Current
  follow-on work stays in `naval/naval_domain_surface_split/`, which is
  active/planning and explicitly not archive-ready.
- `performance_runtime/`: explicitly active planning/execution as of
  `2026-05-18`.
- `flight_dynamics/`: keep the current pattern. It is a reference hub with
  archived implementation packages plus live analysis subdirs where closure
  markers and unresolved realism issues are still useful.
- `ground/`: active planning root. G0-G6 records are accepted/sealed evidence
  and now physically archived with original-path pointers, but movement,
  sensing, terrain, fires, damage, combat, and full runtime release remain held.
- `model/`: active planning root. `m1_action_interface_split/` is accepted but
  retained in the M1 evidence chain; `m1_temporal_window_hmoe/` is still
  gathering evidence; `m2_causal_transformer_hmoe/` is held.
- `simulation_architecture/`, `review/`, and `issues/`: active governance or
  architecture roots with local archives for closed snapshots only.
- `game/`: active exploratory Arma proxy line, not archive-ready.

## Current Action State

### Wave 1: Complete

1. `code_redundancy`, `diagnostics_eval`, and `python_rl` have root README
   entries plus local archive indexes.
2. `review` has a root governance README plus local archive indexes for
   completed or superseded review snapshots.
3. `docs/task/README*` points at local task-area READMEs rather than stale
   dated snapshots for these areas.

### Wave 2: Complete For Selected Evidence Packages

1. `air_combat`, `common_air_naval`, and `viz` have local README entries and
   archive separation.
2. `a2_high_fidelity_damage_model/`, naval N4/N5 evidence packets, and ground
   G0-G6 phase packets have been moved to local archive directories with
   lightweight pointers left behind.
3. Do not move the promoted `viz/archive` plan unless a replacement active
   entry exists.

### Wave 3: No Move Now

1. Keep `naval`, `ground`, `model`, `performance_runtime`,
   `simulation_architecture`, `review`, `issues`, `game`, and the
   `flight_dynamics` reference hub on their current paths.
2. Continue using `README + current status + archive/` as the default lifecycle
   pattern for new task lines.

## Acceptance Criteria

1. `docs/task/archive/owner_migration_20260808/README.md` and `README.zh.md` stop using stale dated snapshots as
   the default entry for areas that already have a better local entry page.
2. Each archived subproject keeps one root `README` plus a local `archive/`
   index.
3. New work does not continue by expanding an already closed freeze doc; it
   starts from a new freeze, taskboard, or current-status doc with a fresh
   date.
4. Historical links remain readable after moves with only minimal relative-link
   adjustment.

## Immediate Recommendation

- Do not start an unscoped bulk file-move wave from this document.
- Treat remaining completed retained records as sealed evidence until their
  parent README and current gate links can be rewritten safely.
- Use `flight_dynamics/archive/` as the template for future per-area archive
  moves.
