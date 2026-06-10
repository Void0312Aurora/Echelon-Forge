# WP18-D Facade Contract Hardening

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp18_facade_contract_hardening_cluster_20260521.md`
- Chinese companion:
  [wp18_facade_contract_hardening_cluster_20260521.zh.md](wp18_facade_contract_hardening_cluster_20260521.zh.md)

Inputs:

- [WP18 main plan](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.md)
- [WP18-A ownership fact ledger](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)
- [WP17 acceptance review](../../review/wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.md)

## Purpose

Harden the facade-shaped frontend contract after WP17 so maintained callers do
not regress to raw runtime/world handles while compatibility surfaces remain
available and explicitly bounded.

## Scope

In scope:

- architecture guards for maintained raw runtime/world-handle reads;
- facade/adapter method shape checks for selected execution ownership seams;
- compatibility allowlist updates with explicit reasons;
- regression tests proving `batch_runtime` and `RuntimeFacade.runtime()` remain
  compatibility-only.

Out of scope:

- public API deletion;
- broad facade redesign;
- CUDA/resident-state or `spawn_platform` work.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `D1` | Maintained path guard | New maintained raw runtime/world reads fail architecture tests unless allowlisted as compatibility. |
| `D2` | Facade shape check | Selected WP18-B/C/E replacement surfaces have stable method/DTO expectations. |
| `D3` | Compatibility retention | Compatibility surfaces remain callable through named tests and are not silently promoted. |
| `D4` | Residual routing | Any guard exceptions are routed to WP18 residuals or later WP19/WP21 prerequisites. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_facade
python -m pytest -q tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "compatibility_view"
```

## Handoff

Return guard changes, allowlist entries and reasons, compatibility tests run,
blocked raw reads, and integration notes for B/C/E.
