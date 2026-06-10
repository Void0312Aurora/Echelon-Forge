# WP20-E Compatibility And Schema Guard

状态：`2026-05-21` pass / validation-first guard accepted。

语言版本：

- 英文主文：[wp20_compatibility_schema_guard_cluster_20260521.md](wp20_compatibility_schema_guard_cluster_20260521.md)
- 中文辅文：`wp20_compatibility_schema_guard_cluster_20260521.zh.md`

输入：

- [WP20 主计划](public_capability_platform_composition_wp20_20260521.zh.md)
- [WP14 boundary guards](../wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.zh.md)
- `tests/architecture/platform_spawn/test_boundary_guards.py`

## 目的

把 WP14 的 "typed requests are additive and not auto-materialized" guard 替换为
WP20 的 validation-first publicization guards。

## 范围

范围内：

- architecture tests：只允许 typed request 通过 WP20 validated path materialize；
- 保护 `spawn_unit(type_name)`、`WorldSpawnRequest.type_name` 与 scenario/example
  compatibility；
- 阻止 platform capability semantics 进入 backend `RuntimeCapabilities`；
- behavior-change 与 schema-migration anti-regression checks。

范围外：

- runtime materialization；
- 超出表达 guard expectations 所需范围的 DTO design。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `E1` | WP14 guard transition | 旧的 "must not materialize" assertions 被替换或收窄为 WP20 语义。 |
| `E2` | Validation-first guard | typed materialization 只有在 validation 与 result evidence 存在时允许。 |
| `E3` | Compatibility guard | type-name 与 scenario/example compatibility 仍被保护。 |
| `E4` | Naming separation | Platform capability contracts 继续与 backend `RuntimeCapabilities` 分离。 |

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/platform_spawn/test_boundary_guards.py tests/architecture/runtime_facade
```

## 交付

返回 touched tests、changed guard rationale、commands run、blockers，以及 B/C/D 必须满足的 contract assumptions。

当前返回：

- Status: `pass`
- Guard 范围只保留在 architecture tests。
- `WP20-C` 必须通过 validation/result evidence 路由 typed setup，且不得把 typed
  materialization 直接加到 `WorldBatchRuntime` public mainline API。
- `WP20-D` 必须保留 backend `RuntimeCapabilities` 命名分离和 legacy setup
  compatibility。
