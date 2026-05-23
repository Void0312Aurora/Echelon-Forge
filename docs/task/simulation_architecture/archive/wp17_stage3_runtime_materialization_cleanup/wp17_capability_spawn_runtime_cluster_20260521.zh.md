# WP17-E Capability Spawn Runtime Promotion

状态：`2026-05-21` implemented / focused validation passed while preserving type-name spawn compatibility。

英文主文：[wp17_capability_spawn_runtime_cluster_20260521.md](wp17_capability_spawn_runtime_cluster_20260521.md)

输入：

- [WP17 主计划](stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.zh.md)
- [WP14 compatibility validation](../wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.zh.md)

## 目标

在保留 type-name compatibility 的同时，把既有 internal capability-resolution chain 推向 maintained runtime spawn behavior。

## 范围

范围内：

- 在 materialization path 中使用 `CapabilityBundle` template 与 `ResolvedPlatformSpawnPlan` evidence；
- 证明一个 air 与一个 naval platform 通过同一 resolution chain materialize；
- 保留 `spawn_unit(type_name)` 与 `WorldSpawnRequest.type_name` compatibility；
- 添加 guards，防止 backend `RuntimeCapabilities` 吸收 platform capability semantics。

范围外：

- mandatory public `spawn_platform`；
- broad scenario schema migration；
- 删除 `spawn_unit`；
- backend/fidelity promotion。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `E1` | Resolution-chain promotion | Runtime spawn path 在 materialization 前记录 capability bundle/resolved-plan evidence。 |
| `E2` | Air/naval proof | F-16 与 DDG-51 或等价 fixtures 使用同一 resolver chain 和不同 bundles。 |
| `E3` | Compatibility preservation | 既有 type-name 与 batch spawn tests 通过。 |
| `E4` | Boundary guards | Tests 保持 platform capabilities 不进入 backend `RuntimeCapabilities`，并阻止过早 public schema claims。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp14_*.py
python -m pytest -q tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py
python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "ddg or spawn"
```

## 交接

返回 touched factory/setup files、compatibility risks、commands run，以及仍需要 direct type-name handling 的 platforms。
