# WP21-F Final Cleanup And Acceptance Handoff

Status: `2026-05-21` planned; serial closure after A-E.

Language:

- English canonical: `wp21_final_cleanup_acceptance_cluster_20260521.md`
- Chinese companion:
  [wp21_final_cleanup_acceptance_cluster_20260521.zh.md](wp21_final_cleanup_acceptance_cluster_20260521.zh.md)

Inputs:

- [WP21 main plan](full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)

## Purpose

Close the final refactor stage after implementation streams return. This stream
does not create acceptance from plans; it verifies code evidence, closes or
guards legacy residuals, and publishes the final route status.

## Scope

In scope:

- integrate A-E handoff packets;
- run validation rollup and record exact commands;
- verify legacy-only counterfactual/generation/loader mirror paths are removed,
  guarded, or compatibility-only with tests;
- update README/indexes and bilingual companions;
- draft the final acceptance review.

Out of scope:

- changing implementation semantics except for narrow integration fixes;
- creating acceptance while any A-E implementation gate is blocked;
- hiding residuals to make the route look complete.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `F1` | Handoff integration | A-E returned status, touched files, validation, residuals, and closure impact are summarized. |
| `F2` | Legacy cleanup review | Legacy-only paths are removed, guarded, or retained as compatibility-only with tests. |
| `F3` | Validation rollup | Exact validation commands are run and recorded. |
| `F4` | Publication closure | README/index sync, bilingual docs, acceptance review, and audit output are complete. |
| `F5` | Final route verdict | The acceptance review names no unowned refactor-route residuals. |

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp15_*.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or worldline or experiment or setup"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/scenario -k "generation or counterfactual or scenario_loader"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py -k "counterfactual or experiment"
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP21 --summary
```

## Handoff

Return final validation table, acceptance decision draft, remaining retained
compatibility notes, touched files, and exact commit/push readiness.
