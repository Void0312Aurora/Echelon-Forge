# WP14-C Spawn Resolution Bridge

Status: `2026-05-21` planned / second-wave implementation candidate.

Language:

- English canonical: `wp14_spawn_resolution_bridge_cluster_20260521.md`
- Chinese companion:
  [wp14_spawn_resolution_bridge_cluster_20260521.zh.md](wp14_spawn_resolution_bridge_cluster_20260521.zh.md)

Inputs:

- [WP14 capability composition](capability_composition_wp14_20260521.md)
- [WP14-B content definition lowering](wp14_content_definition_lowering_cluster_20260521.md)
- Current `src/core/engine/simulation_kernel.*`
- Current `src/core/engine/world_batch_runtime.*`
- Current `src/runtime/facade/runtime_facade.*`

## 1. Purpose

`WP14-C` bridges existing spawn entry points through resolution before
materialization. It preserves `spawn_unit(type_name)`, `WorldSpawnRequest`, and
facade setup compatibility while making resolved-plan evidence inspectable.

## 2. Scope

In scope:

- route kernel/world-batch/facade spawn paths through the resolver from B;
- preserve public type-name surfaces and existing Python behavior;
- expose enough diagnostics/evidence to prove the bridge was used;
- add compatibility regression tests for world batch and facade setup.

Out of scope:

- migrating all call sites to `CapabilityBundle`;
- deleting `WorldSpawnRequest.type_name`;
- direct public `spawn_platform` promotion;
- changing entity/component behavior.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/core/engine/simulation_kernel.h`
- `src/core/engine/simulation_kernel.cpp`
- `src/core/engine/world_batch_runtime.cpp`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_core.cpp`
- `src/interfaces/python/bindings_runtime.cpp`

Preferred approach:

- keep caller-facing signatures stable;
- insert a narrow resolution step before factory materialization;
- preserve old behavior on success and add explicit rejection/evidence on
  resolver failure;
- avoid broad search-and-replace over tests or scenarios.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Public compatibility | Existing `spawn_unit(type_name)` and batch setup callers still work. |
| Resolution before materialization | Kernel/batch/facade setup paths use the resolved plan before factory creation. |
| Evidence | Tests can inspect that a type name resolved to a capability plan. |
| No broad migration | No all-repo caller rewrite is required for acceptance. |

## 5. Acceptance Tests

Minimum tests:

- direct `SimulationKernel::spawn_unit` compatibility fixture still passes;
- `WorldBatchRuntime::spawn_units_batch` keeps current `type_name` behavior;
- facade world setup uses type-name compatibility and exposes resolution
  evidence or stable diagnostics;
- invalid type names fail closed with inspectable reason.

Suggested commands:

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup or observation_packet"
```

## 6. Handoff Contract

Return:

- kernel/world-batch/facade files touched;
- compatibility behavior preserved;
- resolution evidence exposed;
- tests added or updated;
- exact commands run and outcomes;
- residuals for additive facade DTO or materialization work.
