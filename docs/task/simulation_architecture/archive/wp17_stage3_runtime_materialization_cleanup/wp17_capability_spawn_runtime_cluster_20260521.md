# WP17-E Capability Spawn Runtime Promotion

Status: `2026-05-21` implemented / focused validation passed while preserving
type-name spawn compatibility.

Inputs:

- [WP17 main plan](stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.md)
- [WP14 compatibility validation](../wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.md)

## Purpose

Promote the existing internal capability-resolution chain toward maintained
runtime spawn behavior while preserving type-name compatibility.

## Scope

In scope:

- use `CapabilityBundle` template and `ResolvedPlatformSpawnPlan` evidence in
  the materialization path;
- prove one air and one naval platform materialize through the same resolution
  chain;
- keep `spawn_unit(type_name)` and `WorldSpawnRequest.type_name` compatible;
- add guards that prevent backend `RuntimeCapabilities` from absorbing platform
  capability semantics.

Out of scope:

- mandatory public `spawn_platform`;
- broad scenario schema migration;
- removing `spawn_unit`;
- backend/fidelity promotion.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `E1` | Resolution-chain promotion | Runtime spawn path records capability bundle/resolved-plan evidence before materialization. |
| `E2` | Air/naval proof | F-16 and DDG-51 or equivalent fixtures use the same resolver chain with different bundles. |
| `E3` | Compatibility preservation | Existing type-name and batch spawn tests pass. |
| `E4` | Boundary guards | Tests keep platform capabilities out of backend `RuntimeCapabilities` and block premature public schema claims. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp14_*.py
python -m pytest -q tests/runtime/bindings/test_typed_platform_spawn_bindings.py
python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "ddg or spawn"
```

## Handoff

Return touched factory/setup files, compatibility risks, commands run, and any
platforms that still need direct type-name handling.
