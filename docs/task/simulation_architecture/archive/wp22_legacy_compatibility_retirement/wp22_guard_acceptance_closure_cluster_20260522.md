# WP22-F Guardrail And Acceptance Closure

Status: `2026-05-22` not eligible; serial closure only after B-E evidence exists.
The latest preflight returned guard hardening only: repo-level `batch_runtime`
consumer scans are stronger, but no acceptance review is authorized while
public escape hatches, default-factory typed control-state replacement,
aggregate DTO retirement, and broad binding/service debt remain open.
The eighth-wave verification did not change this gate: Banach and Planck are
scoped passes, Harvey is `partial`, and the local focused sweep passed while
the closure audit still reports `0` canonical WP22 acceptance reviews.

Inputs:

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.md)
- [WP22-B Python business bypass retirement](wp22_python_business_bypass_retirement_cluster_20260522.md)
- [WP22-C runtime escape-hatch closure](wp22_runtime_escape_hatch_closure_cluster_20260522.md)
- [WP22-D command DTO legacy retirement](wp22_command_dto_legacy_surface_retirement_cluster_20260522.md)
- [WP22-E structural decomposition](wp22_structural_god_file_decomposition_cluster_20260522.md)
- [WP22 dispatch queue](wp22_subagent_dispatch_queue_20260522.md)

## Purpose

Close WP22 only if forced retirement actually happened. This stream owns
guards, validation rollup, index sync, bilingual closure, and the acceptance
draft after implementation evidence exists.

## Owned Scope

- Architecture guard tests for legacy/default access
- Validation rollup and kill-list closure notes
- README and review index sync
- Required bilingual companions
- Acceptance review draft after implementation evidence exists

## Required Output

| Area | Requirement |
|------|-------------|
| Guard pack | Tests fail on new default `loader.sim.*`, `.runtime(`, `batch_runtime`, silent `legacy` mode, raw mission-cmd consumers, and unowned legacy command usage outside allowlists. |
| Kill-list closure | Every WP22-A item is `retired`, `quarantined with opt-in`, or `blocked with failing guard`; no item is "accepted residual". |
| Validation rollup | Commands and outcomes are recorded after B-E implementation evidence exists. |
| Publication | README/review indexes, Chinese companions, and acceptance review are synchronized only after implementation gates pass. |

## Gate

Fail closure if any maintained default path still uses a legacy surface without
an explicit opt-in compatibility boundary and a failing guard for new callers.

Preflight-only note: the current WP22-C guard hardening tightens the
maintained Python scan to include repo-level non-test entrypoints, but it does
not change the not-eligible closure state or retire any public escape hatch.
The Pauli/Ramanujan guard-and-quarantine passes are also not closure evidence:
they mark DTO transport shells and binding helper roles, but do not remove the
remaining compatibility surfaces.
Banach closes the maintained binding raw-entity seam for this slice, and Planck
extracts one visual-binding service helper, but those results still leave broad
bindings, diagnostics/legacy raw ECS, public escape hatches, and the
default-factory typed control-state blocker open.

Latest local preflight:

- `python3 -m pytest -q tests/architecture/platform_spawn/test_default_factory_legacy_seed_guard.py tests/architecture/structural_boundaries tests/architecture/runtime_facade -k "wp22 or bindings or world_batch_runtime or gpu_visual_binding or visual_binding_raw_world_access or escape_hatch or batch_runtime"` -> `32 passed, 16 deselected`
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP22 --summary` -> `0` canonical acceptance reviews; required zh peers present
- `git diff --check` -> pass

This is guard/preflight evidence only. It must not be converted into an
acceptance review.

## Suggested Validation

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP22 --summary
python -m pytest -q tests/architecture -k "legacy or facade or runtime or tasking or command"
python -m pytest -q tests/runtime/facade
python -m pytest -q tests/world_batch
python -m pytest -q tests/scenario
```

## Stop Rules

- Do not create acceptance from planned docs alone.
- Do not mark a path complete because it is compatibility-preserving.
- Do not hide blockers in prose; blockers must have owner, guard, and next
  command.
