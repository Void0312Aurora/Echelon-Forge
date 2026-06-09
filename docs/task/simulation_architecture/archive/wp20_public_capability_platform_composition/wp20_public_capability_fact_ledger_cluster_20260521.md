# WP20-A Public Capability Fact Ledger

Status: `2026-05-21` pass / source-backed facts accepted.

Language:

- English canonical: `wp20_public_capability_fact_ledger_cluster_20260521.md`
- Chinese companion:
  [wp20_public_capability_fact_ledger_cluster_20260521.zh.md](wp20_public_capability_fact_ledger_cluster_20260521.zh.md)

Inputs:

- [WP20 main plan](public_capability_platform_composition_wp20_20260521.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.md)
- [WP17 capability spawn runtime promotion](../wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.md)

## Purpose

Freeze the current source-backed facts before WP20 promotes any public
capability-platform setup surface.

This ledger is intentionally narrow: it records what the repository already
contains, what the tests already enforce, and where the public gap still
remains.

## Scope

In scope:

- source/test inventory for `Capability`, `CapabilityBundle`,
  `ResolvedPlatformSpawnPlan`, `TypedPlatformSpawnRequest`, validation helpers,
  factory resolution, facade setup, world-batch setup, and bindings;
- facts about what is public, additive-only, consumed, ignored, or explicitly
  blocked today;
- the smallest safe implementation seam for the B/C/D streams;
- residuals and blockers that remain source-backed.

Out of scope:

- code changes;
- acceptance review;
- runtime behavior edits;
- inferred future behavior that is not already encoded in source or tests.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `A1` | Source ledger | Exact source/test files and current behavior are listed with no inferred facts. |
| `A2` | Public gap map | The gap between DTO exposure, validation, facade setup, and materialization is named. |
| `A3` | Compatibility boundary | Type-name compatibility, scenario-schema stability, and backend capability separation are frozen. |
| `A4` | Implementation recommendation | A minimal B/C/D implementation seam is recommended, or a blocker is named. |

## Source-Backed Facts

### 1) Platform capability contracts exist as a dedicated platform namespace

`src/runtime/contracts/platform_capability_contracts.h` defines the platform
vocabulary under `namespace runtime::platform_capabilities` rather than under
`RuntimeCapabilities`.

Evidence:

- families and request/materialization kinds at
  [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:12)
  and [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:20)
- `Capability`, `CapabilityBundle`, and `ResolvedPlatformSpawnPlan` structs at
  [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:105)
  , [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:117)
  , and [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:127)
- fail-closed validation helpers at
  [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:246)
  , [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:286)
  , and [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:337)

Current fact:

- the contract header already carries compatibility-preserving and typed-request
  vocabulary such as `type_name_compatibility`, `typed_platform_request`, and
  `resolved_spawn_plan_bridge`.
- `RuntimeCapabilities` is not defined in this header, which matches the WP14
  boundary that keeps backend/fidelity capability projection separate from
  platform capability composition.

### 2) `world_batch_contracts.h` exposes typed setup DTOs, but its public runtime
setup still carries the legacy `WorldSpawnRequest` path

`src/runtime/contracts/world_batch_contracts.h` defines `TypedPlatformSpawnRequest`
and the batch setup request now contains both legacy and typed arrays.

Evidence:

- `WorldSpawnRequest` remains the legacy surface at
  [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:46)
- typed-request rejection constants and the typed DTO are at
  [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:69)
  and [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:88)
- `BatchWorldSetupRequest` carries both `spawn_requests` and
  `typed_platform_spawn_requests` at
  [runtime_facade_types.h](../../../../src/runtime/facade/runtime_facade_types.h:112)
  and [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:88)
- `validate_typed_platform_spawn_request()` is declarative/fail-closed and only
  checks DTO shape plus bundle/plan validation at
  [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:140)

Current fact:

- the typed DTO is already public in contracts and Python bindings.
- the validation helper does not materialize runtime behavior.
- the mainline setup path still uses legacy spawn requests for execution.

### 3) `RuntimeFacade` setup surface still consumes legacy world-spawn requests

`RuntimeFacade` exposes `BatchWorldSetupRequest` and forwards setup through the
legacy `spawn_requests` vector.

Evidence:

- facade setup declarations at
  [runtime_facade.h](../../../../src/runtime/facade/runtime_facade.h:47)
  and [runtime_facade.h](../../../../src/runtime/facade/runtime_facade.h:52)
- setup forwarding at [runtime_facade.cpp](../../../../src/runtime/facade/runtime_facade.cpp:1312)
  and [runtime_facade.cpp](../../../../src/runtime/facade/runtime_facade.cpp:1330)
- Python binding exposure for `apply_world_setup_batch` and `apply_world_setup`
  at [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:1340)
  and [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:1350)

Current fact:

- `RuntimeFacade::apply_world_setup()` copies `request.spawn_requests` into the
  runtime batch call.
- there is no public `spawn_platform` surface in this file family.
- `RuntimeFacade::runtime()` remains a compatibility escape hatch for legacy or
  diagnostic consumers, not the preferred mainline setup surface.

### 4) `WorldBatchRuntime` consume path still materializes only `WorldSpawnRequest`

`src/core/engine/world_batch_runtime.cpp` does not consume typed requests in its
mainline setup path.

Evidence:

- `spawn_units_batch(const std::vector<WorldSpawnRequest>&)` at
  [world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp:514)
- `apply_world_setup_batch(...)` also accepts only `const std::vector<WorldSpawnRequest>&`
  at [world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp:526)
- the setup loop groups and spawns only `WorldSpawnRequest` entries at
  [world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp:538)
  through [world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp:577)

Current fact:

- typed platform requests are not auto-materialized in `WorldBatchRuntime`.
- the explicit public gap is the missing consume bridge from typed requests to
  the legacy world-materialization path.

### 5) `DefaultUnitFactory` already resolves type-name compatibility through a
bundle template and resolved plan before materialization

`src/models/core/default_unit_factory.h` already contains the internal bridge that
WP20 wants to publicize, not replace.

Evidence:

- bundle lowering at [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:329)
- capability-family evidence coverage for sensing, mobility, communication,
  launching, survivability, command, and doctrine at
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:347)
  through [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:560)
- resolved-plan construction at
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:573)
- type-name fallback rejection for unknown definitions at
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:619)
  through [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:640)
- spawn gate validates the resolved plan before materialization at
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:656)
  through [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:684)

Current fact:

- the factory already computes `CapabilityBundle`, `ResolvedPlatformSpawnPlan`,
  and evidence refs from `type_name`.
- the spawn path remains compatibility-preserving and still materializes through
  the legacy unit-definition lookup after plan validation.

### 6) Python bindings expose the new platform DTOs, but not a public consume bridge

`src/interfaces/python/bindings_runtime.cpp` exposes the platform DTOs and the
batch setup request fields, which means the DTO surface is already public to
Python.

Evidence:

- `CapabilityBundle` and `ResolvedPlatformSpawnPlan` bindings at
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:302)
  and [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:336)
- `TypedPlatformSpawnRequest` binding at
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:406)
- `BatchWorldSetupRequest.typed_platform_spawn_requests` binding at
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:725)
- `RuntimeFacade.apply_world_setup` binding at
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:1341)

Current fact:

- Python can construct typed DTOs today.
- Python cannot yet exercise a separate typed consume bridge from the facade
  because the facade still forwards only the legacy spawn-request array.

### 7) WP14 boundary guards explicitly freeze the first public gap

`tests/architecture/platform_spawn/test_boundary_guards.py` and related WP14 tests are the
current proof that the public gap is intentional, not accidental.

Evidence:

- no public `spawn_platform` surface in runtime/bindings/scenario compatibility
  layers at [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:26)
- `RuntimeCapabilities` remains backend/fidelity-only at
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:43)
- legacy `WorldSpawnRequest.type_name` surfaces remain present at
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:94)
- typed requests are explicitly additive and not auto-materialized at
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:140)
- typed DTO validation stays declarative/fail-closed at
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:176)
- contract header tests keep `RuntimeCapabilities` out of
  `platform_capability_contracts.h` at
  [test_wp14_platform_capability_contracts.py](../../../../tests/architecture/test_wp14_platform_capability_contracts.py:51)
- content-lowering tests confirm type-name plan resolution before materialization
  at [test_wp14_content_definition_lowering.py](../../../../tests/architecture/test_wp14_content_definition_lowering.py:48)
  and [test_wp14_resolved_spawn_plan_evidence.py](../../../../tests/architecture/test_wp14_resolved_spawn_plan_evidence.py:60)
- Python DTO tests confirm typed DTO construction while preserving the legacy
  `WorldSpawnRequest` surface at
  [test_wp14_additive_platform_spawn_bindings.py](../../../../tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py:75)

Current fact:

- the repository already expects `typed_platform_spawn_requests` to exist in the
  DTO layer, while the runtime path remains explicitly non-materializing.

## Public Gap

The current public gap is not in DTO declaration; it is in consumption.

What exists:

- public typed DTOs in contracts and Python bindings;
- fail-closed validation helpers for typed DTOs and resolved plans;
- internal factory resolution from `type_name` to bundle and plan evidence;
- legacy setup execution through `WorldSpawnRequest`.

What is missing:

- a public typed setup consume bridge that admits typed requests, validates
  them, and then routes them through the compatibility-preserving resolved-plan
  path;
- explicit result evidence for that consume path;
- any facade/runtime surface that makes typed setup the mainline execution path.

## Compatibility Boundary

Source-backed compatibility facts:

- `WorldSpawnRequest.type_name` remains the legacy public setup field.
- scenario and example schema files are guarded by tests to stay on the legacy
  request shape for this slice.
- `RuntimeCapabilities` is reserved for backend/fidelity projection, not
  platform composition.
- `DefaultUnitFactory` already uses the type-name compatibility chain and
  materializes after plan validation.
- `spawn_platform` is still absent from the runtime/facade/binding surfaces.

## Safe Seam Recommendation

Recommended first implementation seam for B/C/D:

1. keep `DefaultUnitFactory::resolve_platform_spawn_plan_for_type_name()` as the
   source of resolved-plan evidence;
2. add a typed-request consume bridge at the facade boundary that validates
   `TypedPlatformSpawnRequest` and then forwards only admitted requests through
   the compatibility-preserving plan path;
3. let `WorldBatchRuntime` remain the materialization owner for legacy spawn
   requests until the bridge is explicit and test-covered;
4. expose only the admitted typed surface in Python after the consume bridge is
   stable.

Why this seam is safe:

- it reuses already-tested source facts instead of introducing a parallel spawn
  schema;
- it preserves the compatibility path and the legacy `type_name` surface;
- it keeps backend capability projection out of platform composition;
- it avoids changing `SimulationKernel` materialization semantics before the
  typed consume bridge is proven.

## Residuals

- `WorldBatchRuntime` still consumes only `WorldSpawnRequest` in its mainline
  setup path.
- `RuntimeFacade::apply_world_setup()` still forwards only `spawn_requests`.
- there is no public typed setup result/admission surface yet.
- no source-backed evidence shows `typed_platform_spawn_requests` being consumed
  by runtime materialization in the current slice.

## Continuation State

- Original A-slice entry gate: `WP20-B` and `WP20-E` may continue because the
  typed request DTO, boundary facts, and backend/platform separation are
  source-backed.
- Post-B/C update: `WP20-C` has been released and accepted after the public
  admission/result contract returned.
- Current next stream: `WP20-D` is released for binding/public-surface work and
  should only publish what the C consume bridge actually uses.

## Commands Run

```bash
pwd && rg --files docs task . | rg 'wp20|wp14|wp17|platform_capability_contracts|world_batch_contracts|bindings_runtime|DefaultUnitFactory|RuntimeFacade|WorldBatchRuntime|boundary guards|test'
rg -n "TypedPlatformSpawnRequest|ResolvedPlatformSpawnPlan|typed_platform_spawn_requests|spawn_platform|RuntimeFacade::apply_world_setup|apply_world_setup\(|WorldBatchRuntime|DefaultUnitFactory::spawn|ResolvedSpawnPlan|CapabilityBundle|Capability" src tests
sed -n '1,240p' src/runtime/contracts/platform_capability_contracts.h
sed -n '1,260p' src/runtime/contracts/world_batch_contracts.h
sed -n '1,260p' src/interfaces/python/bindings_runtime.cpp
sed -n '1,260p' src/runtime/facade/runtime_facade.h
sed -n '1,360p' src/runtime/facade/runtime_facade.cpp
sed -n '1,260p' src/core/engine/world_batch_runtime.h
sed -n '1,260p' src/core/engine/world_batch_runtime.cpp
sed -n '1,260p' src/models/core/default_unit_factory.h
sed -n '1,240p' tests/architecture/test_wp14_platform_capability_contracts.py
sed -n '1,240p' tests/architecture/platform_spawn/test_boundary_guards.py
sed -n '1,260p' tests/architecture/test_wp14_additive_platform_spawn_dto.py
sed -n '1,260p' tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py
sed -n '1,260p' tests/world_batch/test_world_batch_runtime.py
sed -n '1,260p' tests/architecture/test_wp14_resolved_spawn_plan_evidence.py
sed -n '1,260p' tests/architecture/runtime_facade/test_layering.py
sed -n '1,220p' tests/architecture/test_wp14_content_definition_lowering.py
nl -ba src/runtime/facade/runtime_facade.cpp | sed -n '1310,1365p'
nl -ba src/core/engine/world_batch_runtime.cpp | sed -n '510,560p'
nl -ba src/models/core/default_unit_factory.h | sed -n '320,700p'
nl -ba src/interfaces/python/bindings_runtime.cpp | sed -n '280,440p'
nl -ba tests/architecture/platform_spawn/test_boundary_guards.py | sed -n '1,260p'
nl -ba tests/architecture/test_wp14_platform_capability_contracts.py | sed -n '1,260p'
nl -ba tests/architecture/test_wp14_content_definition_lowering.py | sed -n '1,220p'
nl -ba tests/architecture/test_wp14_resolved_spawn_plan_evidence.py | sed -n '1,220p'
nl -ba tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py | sed -n '1,220p'
nl -ba tests/world_batch/test_world_batch_runtime.py | sed -n '1,120p'
nl -ba src/runtime/contracts/platform_capability_contracts.h | sed -n '1,220p'
nl -ba src/runtime/contracts/platform_capability_contracts.h | sed -n '220,520p'
nl -ba src/runtime/contracts/world_batch_contracts.h | sed -n '1,260p'
nl -ba src/runtime/facade/runtime_facade_types.h | sed -n '1,180p'
nl -ba src/runtime/facade/runtime_facade.cpp | sed -n '200,260p'
nl -ba src/interfaces/python/bindings_runtime.cpp | sed -n '1328,1362p'
nl -ba src/core/engine/world_batch_runtime.cpp | sed -n '520,590p'
```

## Handoff

Return a source-backed fact ledger, safe seam recommendation, blockers,
residuals, and whether B/E may proceed.

Current return:

- Status: `pass`
- `WP20-B` and `WP20-E` proceeded from this ledger.
- `WP20-C` proceeded after `WP20-B` returned the public admission/result
  contract and has since passed focused validation.
- `WP20-D` is now the released next stream.
