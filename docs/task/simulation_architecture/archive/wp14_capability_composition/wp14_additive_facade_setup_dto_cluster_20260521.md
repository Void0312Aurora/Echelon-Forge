# WP14-D Additive Facade Setup DTO

Status: `2026-05-21` planned / additive surface candidate. This slice must
stay open/planned until typed DTOs are additive and not mistaken for accepted
public spawn replacement.

Language:

- English canonical: `wp14_additive_facade_setup_dto_cluster_20260521.md`
- Chinese companion:
  [wp14_additive_facade_setup_dto_cluster_20260521.zh.md](wp14_additive_facade_setup_dto_cluster_20260521.zh.md)

Inputs:

- [WP14 capability composition](capability_composition_wp14_20260521.md)
- [WP14-A capability bundle contract](wp14_capability_bundle_contract_cluster_20260521.md)
- [WP14-C spawn resolution bridge](wp14_spawn_resolution_bridge_cluster_20260521.md)
- Current `src/runtime/contracts/world_batch_contracts.h`
- Current `src/runtime/facade/runtime_facade_types.h`
- Current `src/interfaces/python/bindings_runtime.cpp`

## 1. Purpose

`WP14-D` prepares the future `spawn_platform({capabilities...})` surface by
adding typed setup DTOs as an additive path. It does not replace current
`WorldSpawnRequest.type_name` or batch setup behavior.

## 2. Scope

In scope:

- typed platform spawn request/result DTO vocabulary;
- Python-visible DTO shape if the runtime surface is added;
- validation helpers that fail closed for incomplete bundles;
- compatibility tests proving the old setup path remains maintained.

Out of scope:

- forcing callers to use typed platform spawn;
- exposing an unvalidated `SimulationKernel::spawn_platform` as the new main
  public API;
- broad scenario JSON migration;
- backend/fidelity capability claims.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/world_batch_contracts.h`
- any new contract header from `WP14-A`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`

Preferred approach:

- keep the DTO additive and clearly experimental/bridge-shaped until C proves
  resolution;
- expose validation/rejection rather than direct unchecked materialization;
- preserve the `type_name` path as the maintained compatibility path.

Parallel rule:

- Keep this slice disjoint from B/C writer scopes.
- Subagents may own DTO shape or bindings, but the main thread keeps the
  integration/gate lane serial in F.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Additive only | New DTOs do not remove or supersede `WorldSpawnRequest.type_name`. |
| Validation | Incomplete capability requests fail closed with stable reasons. |
| Binding shape | Python DTO fields are visible only after the C++ contract is stable. |
| Facade boundary | Proof uses facade/setup contracts, not raw kernel-only shortcuts. |

## 5. Acceptance Tests

Minimum tests:

- DTO fields and defaults are visible in C++ and Python where bound;
- incomplete typed spawn requests reject with stable reasons;
- legacy `WorldSpawnRequest.type_name` setup tests still pass;
- facade layering tests do not acquire new raw kernel escape hatches.

Suggested commands:

```powershell
git diff --check
cmake --build build-local-win -j4
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup"
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
```

Minimum acceptance gates for this slice:

- `git diff --check` passes;
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py` passes;
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_typed_platform_spawn_bindings.py` passes;
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup"` passes;
- `python -m pytest -q tests\architecture\test_runtime_facade_layering.py` passes;
- `WorldSpawnRequest.type_name` stays in place and no mandatory public `spawn_platform` is introduced.

## 6. Handoff Contract

Return:

- DTO files touched;
- binding fields and helper names;
- validation/rejection vocabulary;
- compatibility tests run;
- exact commands and outcomes;
- residuals for future public `spawn_platform` promotion.
