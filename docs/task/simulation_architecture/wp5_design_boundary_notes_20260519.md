# WP5-B Design And Boundary Notes

Status: `2026-05-19` focused design/boundary gate pass.

Language:

- English canonical: `wp5_design_boundary_notes_20260519.md`
- Chinese companion: [wp5_design_boundary_notes_20260519.zh.md](wp5_design_boundary_notes_20260519.zh.md)

Inputs:

- [WP5-B design/boundary cluster](wp5_design_boundary_cluster_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP4 facade alignment acceptance review](../review/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP4-I compatibility guard notes](wp4_compat_guard_notes_20260519.md)
- `tests/architecture/test_runtime_facade_layering.py`

## Added Gates

`tests/architecture/test_wp5_design_boundary_gates.py` adds focused checks that:

1. maintained facade request/result headers do not include `core/engine/*` or
   `world_batch_runtime` owner headers;
2. facade contract/type headers do not name `WorldBatchRuntime` or
   `SimulationKernel`;
3. `runtime_facade.h` limits `WorldBatchRuntime` exposure to the documented
   `runtime()` escape hatch and private owner pointer;
4. facade README files keep raw runtime access documented as
   compatibility/diagnostics-only;
5. architecture tests do not encode a broad direct `sim.*` ban before
   allowlists and provenance labels exist.

## Smoke Candidate Recommendation

Recommended WP5-E smoke candidates:

```bash
python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp5_design_boundary_gates.py
```

These are cheap static/design gates and should run before heavier runtime
facade or engagement evidence tests.

Do not edit `tests/smoke/ci_smoke_suite.json` in WP5-B. Smoke membership should
be handled by the serial WP5-E integration owner.

## Deferred Boundary Work

Do not add a repository-wide direct `sim.*` ban yet. Current legacy Gym,
scenario, oracle, diagnostics, and test paths intentionally use direct
simulation access as `compatibility_adapter` or `diagnostics_only`. A safe
guard requires a narrow maintained-path allowlist plus observation provenance
labels.
