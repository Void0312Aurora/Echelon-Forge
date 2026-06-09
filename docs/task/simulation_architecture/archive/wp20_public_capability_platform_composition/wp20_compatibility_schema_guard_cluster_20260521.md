# WP20-E Compatibility And Schema Guard

Status: `2026-05-21` pass / validation-first guard accepted.

Language:

- English canonical: `wp20_compatibility_schema_guard_cluster_20260521.md`
- Chinese companion:
  [wp20_compatibility_schema_guard_cluster_20260521.zh.md](wp20_compatibility_schema_guard_cluster_20260521.zh.md)

Inputs:

- [WP20 main plan](public_capability_platform_composition_wp20_20260521.md)
- [WP14 boundary guards](../wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.md)
- `tests/architecture/platform_spawn/test_boundary_guards.py`

## Purpose

Replace the WP14 "typed requests are additive and not auto-materialized" guard
with WP20 validation-first publicization guards.

## Scope

In scope:

- architecture tests that permit typed request materialization only through the
  WP20 validated path;
- guards preserving `spawn_unit(type_name)`, `WorldSpawnRequest.type_name`, and
  scenario/example compatibility;
- guards preventing platform capability semantics from moving into backend
  `RuntimeCapabilities`;
- behavior-change and schema-migration anti-regression checks.

Out of scope:

- runtime materialization;
- DTO design beyond what is needed to express guard expectations.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `E1` | WP14 guard transition | Old "must not materialize" assertions are replaced or narrowed for WP20. |
| `E2` | Validation-first guard | Typed materialization is allowed only when validation and result evidence are present. |
| `E3` | Compatibility guard | Type-name and scenario/example compatibility remain protected. |
| `E4` | Naming separation | Platform capability contracts stay separate from backend `RuntimeCapabilities`. |

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/platform_spawn/test_boundary_guards.py tests/architecture/runtime_facade/test_layering.py
```

## Handoff

Return touched tests, changed guard rationale, commands run, blockers, and any
contract assumptions B/C/D must satisfy.

Current return:

- Status: `pass`
- Guard scope stayed in architecture tests only.
- `WP20-C` must route typed setup through validation/result evidence and must
  not add typed materialization directly to the `WorldBatchRuntime` public
  mainline API.
- `WP20-D` must preserve backend `RuntimeCapabilities` naming separation and
  legacy setup compatibility.
