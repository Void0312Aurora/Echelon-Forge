# Task Archive and Convergence Plan

Status: `2026-05-18` planning version.
Scope: `docs/task/*`
Reference pattern: [flight_dynamics archive](./flight_dynamics/archive/README.md)

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

## Assessment by Area

### Archive Now

- `code_redundancy/`: the
  [follow-up freeze](./code_redundancy/code_redundancy_followup_freeze_20260516.md)
  says `WP-A / WP-B / WP-C` are all closed and no active implementation items
  remain. Future work should start from a new freeze doc.
- `diagnostics_eval/`: the
  [diagnostics modularization](./diagnostics_eval/diagnostics_modularization_20260515.md),
  [eval entrypoint convergence](./diagnostics_eval/eval_entrypoint_convergence_20260515.md),
  and
  [benchmark CLI convergence](./diagnostics_eval/diagnostics_benchmark_cli_convergence_20260515.md)
  all mark their phases completed; only incremental cleanup remains.
- `python_rl/`: these docs are convergence records for migrations that are
  already completed or closed. The top-level task index already describes them
  as trace records rather than the default active plan.
- `review/`: the
  [architecture review](./review/architecture_review_20260516.md) is complete
  and the
  [follow-up freeze](./review/architecture_review_followup_freeze_20260516.md)
  records implemented work plus a "later, but out of scope" list that must use
  a new task sheet.

### Converge First, Then Partially Archive

- `air_combat/`: keep the thread active, but stop exposing seven sibling dated
  docs as peers. The docs show landed first-phase work, but still open gaps
  around reward, eval, opponent baselines, stall follow-up, and training-signal
  interpretation. Action: add `README.md` or
  `air_combat_1v1_current_status_20260518.md`, keep that plus at most one
  active freeze or status doc, and move the older snapshots into
  `air_combat/archive/`.
- `common_air_naval/`: most work packages are completed, but the freeze plan
  still lists unfinished follow-ons around broader contract migration and
  naval/runtime/eval expansion. Action: add a convergence entry doc that splits
  "completed foundation" from "unfinished carry-over", then archive the pure
  analysis snapshot and any no-longer-primary execution notes.
- `viz/`: the design plan records first usable closure for `WP-V4` and
  `WP-V5`, but the area still lacks a clear active `README` or pause-state
  checkpoint. Action: add one local entry doc before archiving the large
  freeze/design snapshot.

### Keep Active

- `naval/`: the
  [progress checkpoint](./naval/naval_progress_checkpoint_20260517.md) and
  [delegated backlog](./naval/naval_delegated_execution_backlog_20260517.md)
  still drive next implementation work.
- `performance_runtime/`: explicitly active planning/execution as of
  `2026-05-18`.
- `flight_dynamics/`: keep the current pattern. It already separates active
  entry points from archived packages, especially in `program/`,
  `c2_command_chain/`, and `archive/`.

## Proposed Waves

### Wave 1: Immediate Archive Candidates

1. Add `README.md` and `README.zh.md` to `code_redundancy`,
   `diagnostics_eval`, `python_rl`, and `review`.
2. Create local `archive/` subdirectories and move dated docs there without
   renaming them.
3. Update `docs/task/README*` to point to the new subproject `README`s instead
   of directly to dated snapshots.

### Wave 2: Converge Mixed Areas

1. `air_combat`: write one current-status or convergence entry, then archive
   the sibling snapshots.
2. `common_air_naval`: write one carry-over status entry, then archive the
   analysis doc first; archive the freeze plan only after unfinished carry-over
   items are either moved elsewhere or closed.
3. `viz`: write a pause-state or current-status entry, then decide whether the
   freeze plan stays active or moves to archive.

### Wave 3: No Move Now

1. Keep `naval`, `performance_runtime`, `flight_dynamics/program`, and
   `flight_dynamics/c2_command_chain` on the active path.
2. Continue using `README + current status + archive/` as the default lifecycle
   pattern for new task lines.

## Acceptance Criteria

1. `docs/task/README.md` and `README.zh.md` stop using stale dated snapshots as
   the default entry for areas that already have a better local entry page.
2. Each archived subproject keeps one root `README` plus a local `archive/`
   index.
3. New work does not continue by expanding an already closed freeze doc; it
   starts from a new freeze, taskboard, or current-status doc with a fresh
   date.
4. Historical links remain readable after moves with only minimal relative-link
   adjustment.

## Immediate Recommendation

- Start with `code_redundancy` and `review` as the safest first wave.
- Treat `air_combat` as convergence-first rather than full archive.
- Use `flight_dynamics/archive/` as the template for the rest of `docs/task/`.
