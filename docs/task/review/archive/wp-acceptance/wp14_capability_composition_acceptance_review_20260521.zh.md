# WP14 Capability Composition 验收审查

状态：`2026-05-21` accepted / implementation mergeable。

语言版本：

- 英文主文：
  [wp14_capability_composition_acceptance_review_20260521.md](wp14_capability_composition_acceptance_review_20260521.md)
- 中文辅文：`wp14_capability_composition_acceptance_review_20260521.zh.md`

输入：

- [WP14 Capability Composition](../simulation_architecture/wp14_capability_composition/capability_composition_wp14_20260521.zh.md)
- [WP14-A Capability Bundle Contract](../simulation_architecture/wp14_capability_composition/wp14_capability_bundle_contract_cluster_20260521.zh.md)
- [WP14-B Content Definition Lowering](../simulation_architecture/wp14_capability_composition/wp14_content_definition_lowering_cluster_20260521.zh.md)
- [WP14-C Spawn Resolution Bridge](../simulation_architecture/wp14_capability_composition/wp14_spawn_resolution_bridge_cluster_20260521.zh.md)
- [WP14-D Additive Facade Setup DTO](../simulation_architecture/wp14_capability_composition/wp14_additive_facade_setup_dto_cluster_20260521.zh.md)
- [WP14-E Capability Effects Materialization](../simulation_architecture/wp14_capability_composition/wp14_capability_effects_materialization_cluster_20260521.zh.md)
- [WP14-F Compatibility Validation And Acceptance Handoff](../simulation_architecture/wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.zh.md)
- [WP13 验收审查](wp13_backend_fidelity_expansion_acceptance_review_20260520.zh.md)

## 1. 结论

WP14 验收通过，可作为 Phase 5 capability-composition 的有边界实现增量合入。它添加
platform capability vocabulary、确定性的 type-name lowering、resolved spawn-plan
evidence、保持兼容的 spawn resolution，以及 additive typed setup DTOs，但不把本切片
扩大成 broad spawn rewrite。

已验收边界必须保持：

- `spawn_unit(type_name)` 保持兼容。
- `WorldSpawnRequest.type_name` 仍是维护中的 setup surface。
- `RuntimeCapabilities` 仍属于 backend/fidelity vocabulary，不复用为 platform
  composition semantics。
- `typed_platform_spawn_requests` 被验收为 additive DTO vocabulary，不是现有 world
  setup 的强制替代。
- Public `spawn_platform({capabilities...})`、scenario-schema migration、
  backend/fidelity promotion 与新战术行为仍不在范围内。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP14-A Capability Bundle Contract` | pass | `src/runtime/contracts/platform_capability_contracts.h` 与 `tests/architecture/platform_spawn/test_platform_capability_contracts.py` 定义 platform-semantic `Capability`、`CapabilityBundle`、resolved-plan evidence、validation helpers，并与 backend `RuntimeCapabilities` 保持命名分域。 |
| `WP14-B Content Definition Lowering` | pass | `src/models/core/default_unit_factory.h` 与 `tests/architecture/platform_spawn/test_content_definition_lowering.py` 定义确定性的 `type_name -> CapabilityBundle template -> ResolvedPlatformSpawnPlan` lowering，覆盖既有 platform/factory evidence，且不要求 caller 迁移。 |
| `WP14-C Spawn Resolution Bridge` | pass | `DefaultUnitFactory::spawn()` 在 materialization 前 resolution，`src/core/engine/world_batch_runtime.cpp` 共享 `spawn_from_request(...)` setup path，`tests/world_batch/test_world_batch_runtime.py` 与 focused architecture tests 保持 type-name setup 行为。 |
| `WP14-D Additive Facade Setup DTO` | pass | `src/runtime/contracts/world_batch_contracts.h`、`src/runtime/facade/runtime_facade_types.h`、`src/interfaces/python/bindings_runtime.cpp`、`tests/architecture/platform_spawn/test_additive_platform_spawn_dto.py` 与 `tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py` 以 additive 方式暴露 typed platform spawn DTO vocabulary，同时保持 legacy setup 有效。 |
| `WP14-E Capability Effects Materialization` | pass | `src/models/core/default_unit_factory.h`、`tests/architecture/platform_spawn/test_capability_effects_materialization.py` 与 `tests/architecture/platform_spawn/test_resolved_spawn_plan_evidence.py` 把 capability families 绑定到现有 component/materialization evidence 与 unsupported-effect reasons，不添加新战术行为。 |
| `WP14-F Compatibility Validation And Acceptance Handoff` | pass | 本审查记录 A-E 状态、精确 validation outcomes、兼容边界、residuals、route/README/review index sync 与中英文收口。 |

## 3. 验证命令

本审查前已在 Windows 本地 checkout 通过：

```powershell
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_platform_capability_contracts.py tests\architecture\test_wp14_additive_platform_spawn_dto.py tests\architecture\test_wp14_capability_effects_materialization.py
python -m pytest -q tests\architecture\test_wp14_boundary_guards.py tests\architecture\test_wp14_content_definition_lowering.py tests\architecture\test_wp14_resolved_spawn_plan_evidence.py
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py tests\runtime\bindings\test_wp14_additive_platform_spawn_bindings.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup or capabilities or observation_packet"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\test_gpu_runtime_bindings.py -k "runtime_capabilities"
git diff --check
```

观察结果：

- Build：通过。
- WP14 architecture batch 1：`12 passed`。
- WP14 architecture batch 2：`12 passed`。
- Runtime facade layering guard：`13 passed`。
- Runtime binding DTO batch：`19 passed`。
- World-batch spawn/setup slice：`5 passed, 16 deselected`。
- Runtime facade world-setup/capability/observation slice：`3 passed, 9 deselected`。
- Facade engagement export：`6 passed`。
- GPU runtime capability binding guard：`1 passed, 8 deselected`。
- `git diff --check`：通过，仅有 line-ending warnings。

本验收包最终 closure validation：

```powershell
python tools\maintenance\wp_doc_closure_audit.py --wp WP14
git diff --check
```

## 4. Runtime Surface 摘要

- `platform_capability_contracts.h` 拥有 platform composition vocabulary、
  validation helpers、resolved spawn-plan evidence 与 unsupported-effect reasons。
- `DefaultUnitFactory` 暴露 capability-bundle template 与 resolved spawn-plan helpers，
  并在 resolution 后再 materialize，而不是直接从 `type_name` 跳到 ECS entity
  construction。
- `WorldBatchRuntime` 保持 setup 兼容，同时共享一个 internal spawn path，继续携带
  `WorldSpawnRequest.type_name`、ammo overrides 与 cooldown overrides。
- `TypedPlatformSpawnRequest`、`TypedPlatformSpawnValidationResult` 与
  `BatchWorldSetupRequest.typed_platform_spawn_requests` 为未来 typed platform spawning
  提供 additive facade/setup DTO vocabulary。
- Python bindings 暴露 additive DTO surface，但不强制既有 Python callers 迁移。

## 5. 兼容性声明

WP14 已验收切片是 compatibility bridge，不是 public spawn-platform replacement。
既有 type-name setup 与 world-batch setup 仍是维护中路径。Typed platform spawn requests
作为 additive contract vocabulary 与 validation surface 存在；本切片不要求 scenario JSON
迁移，也不要求 caller 迁移。

## 6. 剩余工作与下一步

有意后移的 residuals：

- Public `spawn_platform({capabilities...})` 需要后续 gate，才能声明为 maintained。
- Scenario/Python schema migration 不属于 WP14，不能从 additive DTOs 推断出来。
- 任意 typed capability bundles 的完整 materialization 需要未来 platform catalog、
  validation 与 behavior-equivalence evidence。
- Backend/fidelity capability claims 仍由 WP13 profile 与 parity gates 管理，而不是由
  platform composition vocabulary 管理。
- Counterfactual and experiment generation 仍是 accepted capability evidence 稳定后的下一
  route consumer。

建议下一路线：只有在 WP14 compatibility bridge 于 mainline 保持稳定后，才开启
counterfactual / experiment-generation phase。
