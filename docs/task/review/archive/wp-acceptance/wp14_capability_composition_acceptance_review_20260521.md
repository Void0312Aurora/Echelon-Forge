# WP14 Capability Composition Acceptance Review

Status: `2026-05-21` accepted / implementation mergeable.

Language:

- English canonical:
  `wp14_capability_composition_acceptance_review_20260521.md`
- Chinese companion:
  [wp14_capability_composition_acceptance_review_20260521.zh.md](wp14_capability_composition_acceptance_review_20260521.zh.md)

Inputs:

- [WP14 Capability Composition](../simulation_architecture/wp14_capability_composition/capability_composition_wp14_20260521.md)
- [WP14-A Capability Bundle Contract](../simulation_architecture/wp14_capability_composition/wp14_capability_bundle_contract_cluster_20260521.md)
- [WP14-B Content Definition Lowering](../simulation_architecture/wp14_capability_composition/wp14_content_definition_lowering_cluster_20260521.md)
- [WP14-C Spawn Resolution Bridge](../simulation_architecture/wp14_capability_composition/wp14_spawn_resolution_bridge_cluster_20260521.md)
- [WP14-D Additive Facade Setup DTO](../simulation_architecture/wp14_capability_composition/wp14_additive_facade_setup_dto_cluster_20260521.md)
- [WP14-E Capability Effects Materialization](../simulation_architecture/wp14_capability_composition/wp14_capability_effects_materialization_cluster_20260521.md)
- [WP14-F Compatibility Validation And Acceptance Handoff](../simulation_architecture/wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.md)
- [WP13 acceptance review](wp13_backend_fidelity_expansion_acceptance_review_20260520.md)

## 1. Verdict

WP14 is accepted as the bounded Phase 5 capability-composition increment. It
introduces platform capability vocabulary, deterministic type-name lowering,
resolved spawn-plan evidence, compatibility-preserving spawn resolution, and
additive typed setup DTOs without turning this slice into a broad spawn rewrite.

The accepted boundary is intentionally narrow:

- `spawn_unit(type_name)` remains compatible.
- `WorldSpawnRequest.type_name` remains a maintained setup surface.
- `RuntimeCapabilities` remains backend/fidelity vocabulary and is not reused
  for platform composition semantics.
- `typed_platform_spawn_requests` is accepted as additive DTO vocabulary, not a
  mandatory replacement for existing world setup.
- Public `spawn_platform({capabilities...})`, scenario-schema migration,
  backend/fidelity promotion, and new tactical behavior remain out of scope.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP14-A Capability Bundle Contract` | pass | `src/runtime/contracts/platform_capability_contracts.h` and `tests/architecture/platform_spawn/test_platform_capability_contracts.py` define platform-semantic `Capability`, `CapabilityBundle`, resolved-plan evidence, validation helpers, and naming separation from backend `RuntimeCapabilities`. |
| `WP14-B Content Definition Lowering` | pass | `src/models/core/default_unit_factory.h` and `tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py` define deterministic `type_name -> CapabilityBundle template -> ResolvedPlatformSpawnPlan` lowering for existing platform/factory evidence without requiring caller migration. |
| `WP14-C Spawn Resolution Bridge` | pass | `DefaultUnitFactory::spawn()` resolves before materialization, `src/core/engine/world_batch_runtime.cpp` shares the `spawn_from_request(...)` setup path, and `tests/world_batch/test_world_batch_runtime.py` plus focused architecture tests preserve type-name setup behavior. |
| `WP14-D Additive Facade Setup DTO` | pass | `src/runtime/contracts/world_batch_contracts.h`, `src/runtime/facade/runtime_facade_types.h`, `src/interfaces/python/bindings_runtime.cpp`, `tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py`, and `tests/runtime/bindings/test_typed_platform_spawn_bindings.py` expose typed platform spawn DTO vocabulary additively while keeping legacy setup valid. |
| `WP14-E Capability Effects Materialization` | pass | `src/models/core/default_unit_factory.h`, `tests/architecture/platform_spawn/test_platform_capability_contracts.py`, and `tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py` bind capability families to existing component/materialization evidence and unsupported-effect reasons without adding new tactical behavior. |
| `WP14-F Compatibility Validation And Acceptance Handoff` | pass | This review records A-E status, exact validation outcomes, compatibility boundaries, residuals, route/README/review index sync, and bilingual closure. |

## 3. Validation Commands

Passed on the Windows local checkout before this review:

```powershell
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_platform_capability_contracts.py tests\architecture\test_wp14_additive_platform_spawn_dto.py tests\architecture\test_wp14_capability_effects_materialization.py
python -m pytest -q tests\architecture\test_wp14_boundary_guards.py tests\architecture\test_wp14_content_definition_lowering.py tests\architecture\test_wp14_resolved_spawn_plan_evidence.py
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py tests\runtime\bindings\test_typed_platform_spawn_bindings.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup or capabilities or observation_packet"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\test_gpu_runtime_bindings.py -k "runtime_capabilities"
git diff --check
```

Observed outcomes:

- Build: passed.
- WP14 architecture batch 1: `12 passed`.
- WP14 architecture batch 2: `12 passed`.
- Runtime facade layering guard: `13 passed`.
- Runtime binding DTO batch: `19 passed`.
- World-batch spawn/setup slice: `5 passed, 16 deselected`.
- Runtime facade world-setup/capability/observation slice: `3 passed, 9 deselected`.
- Facade engagement export: `6 passed`.
- GPU runtime capability binding guard: `1 passed, 8 deselected`.
- `git diff --check`: passed with line-ending warnings only.

Final closure validation for this acceptance packet:

```powershell
python tools\maintenance\wp_doc_closure_audit.py --wp WP14
git diff --check
```

## 4. Runtime Surface Summary

- `platform_capability_contracts.h` owns the platform composition vocabulary,
  validation helpers, resolved spawn-plan evidence, and unsupported-effect
  reasons.
- `DefaultUnitFactory` now exposes capability-bundle template and resolved
  spawn-plan helpers, and materializes after resolution rather than escaping
  directly from `type_name` to ECS entity construction.
- `WorldBatchRuntime` preserves setup compatibility while sharing one internal
  spawn path that carries `WorldSpawnRequest.type_name`, ammo overrides, and
  cooldown overrides.
- `TypedPlatformSpawnRequest`, `TypedPlatformSpawnValidationResult`, and
  `BatchWorldSetupRequest.typed_platform_spawn_requests` provide additive
  facade/setup DTO vocabulary for future typed platform spawning.
- Python bindings expose the additive DTO surface without forcing existing
  Python callers to migrate.

## 5. Compatibility Statement

The accepted WP14 slice is a compatibility bridge, not a public spawn-platform
replacement. Existing type-name setup and existing world-batch setup remain the
maintained path. Typed platform spawn requests are present as additive contract
vocabulary and validation surface; they do not require scenario JSON migration
or caller migration in this slice.

## 6. Residuals And Next Plan

Residuals intentionally carried forward:

- Public `spawn_platform({capabilities...})` needs a later gate before it can be
  declared maintained.
- Scenario/Python schema migration is not part of WP14 and must not be inferred
  from the additive DTOs.
- Full materialization of arbitrary typed capability bundles requires future
  platform catalog, validation, and behavior-equivalence evidence.
- Backend/fidelity capability claims remain governed by WP13 profile and parity
  gates, not by platform composition vocabulary.
- Counterfactual and experiment generation remain the next route consumer after
  the accepted capability evidence is stable.

Recommended next route: open the counterfactual / experiment-generation phase
only after the accepted WP14 compatibility bridge remains stable on mainline.
