# WP20-D Facade And Binding Public Surface

Status: `2026-05-21` accepted / focused pass.

Language:

- English canonical: `wp20_facade_binding_public_surface_cluster_20260521.md`
- Chinese companion:
  [wp20_facade_binding_public_surface_cluster_20260521.zh.md](wp20_facade_binding_public_surface_cluster_20260521.zh.md)

Inputs:

- [WP20 main plan](public_capability_platform_composition_wp20_20260521.md)
- [WP20-B public typed platform spawn contract](wp20_public_typed_platform_spawn_contract_cluster_20260521.md)
- [WP20-C runtime setup consume bridge](wp20_runtime_setup_consume_bridge_cluster_20260521.md)
- `src/runtime/facade/runtime_facade.*`
- `src/interfaces/python/bindings_runtime.cpp`

## Purpose

Expose the validated typed platform setup path through maintained facade and
Python binding surfaces without breaking legacy setup calls.

## Scope

In scope:

- binding exposure for any B result/admission DTOs;
- facade method/result propagation for the C consume bridge;
- Python tests proving valid, rejected, and legacy setup behavior;
- public-surface docs in the task handoff.

Out of scope:

- runtime materialization semantics;
- scenario schema migration;
- public convenience `spawn_platform` if the B/C contract does not justify it.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `D1` | DTO bindings | B result/admission DTOs are visible from Python with stable fields/defaults. |
| `D2` | Facade propagation | `RuntimeFacade.apply_world_setup(...)` returns typed result evidence when C consumes typed requests. |
| `D3` | Fail-closed proof | Invalid typed requests reject visibly rather than being ignored or partially materialized. |
| `D4` | Legacy proof | Existing setup calls remain compatible. |

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "world_setup or capability or spawn"
```

## Handoff

Return touched files, public field list, behavior summary, tests run, and
remaining docs/compatibility residuals.

Current unblock note:

- `WP20-B` has provided the additive `TypedPlatformSpawnResult` contract and
  `BatchWorldSetupResult.typed_platform_spawn_results`.
- `WP20-C` has validated the C++ facade consume bridge and leaves Python
  visibility as this stream's remaining public-surface task.
- This stream must expose the result vector and every result field through
  bindings without changing runtime materialization semantics.

## 2026-05-21 Status Update

- `src/interfaces/python/bindings_runtime.cpp` now binds
  `TypedPlatformSpawnResult` and
  `BatchWorldSetupResult.typed_platform_spawn_results` while preserving legacy
  `entity_ids`.
- Focused Python surface tests were extended under
  `tests/runtime/bindings/test_bindings_runtime_dto_surface.py` to guard the
  DTO field list for both `TypedPlatformSpawnResult` and
  `BatchWorldSetupResult`.
- Focused facade tests under `tests/runtime/facade/test_runtime_facade.py`
  now assert Python-visible admitted/materialized typed setup evidence and
  fail-closed rejected typed setup evidence.
- Focused validation passed for binding DTOs, facade typed setup evidence, and
  WP20 B/C architecture regressions.
