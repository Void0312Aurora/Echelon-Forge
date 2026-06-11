# WP20-D Facade And Binding Public Surface

状态：`2026-05-21` accepted / focused pass。

语言版本：

- 英文主文：[wp20_facade_binding_public_surface_cluster_20260521.md](wp20_facade_binding_public_surface_cluster_20260521.md)
- 中文辅文：`wp20_facade_binding_public_surface_cluster_20260521.zh.md`

输入：

- [WP20 主计划](public_capability_platform_composition_wp20_20260521.zh.md)
- [WP20-B public typed platform spawn contract](wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md)
- [WP20-C runtime setup consume bridge](wp20_runtime_setup_consume_bridge_cluster_20260521.zh.md)
- `src/runtime/facade/runtime_facade.*`
- `src/interfaces/python/bindings_runtime.cpp`

## 目的

通过 maintained facade 与 Python binding surfaces 暴露 validated typed platform setup
path，同时不破坏 legacy setup calls。

## 范围

范围内：

- B result/admission DTO 的 binding exposure；
- C consume bridge 的 facade method/result propagation；
- Python tests 证明 valid、rejected 与 legacy setup behavior；
- task handoff 中的 public-surface docs。

范围外：

- runtime materialization semantics；
- scenario schema migration；
- 如果 B/C contract 不足以证明，则不添加 public convenience `spawn_platform`。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `D1` | DTO bindings | B result/admission DTOs 在 Python 可见，字段/默认值稳定。 |
| `D2` | Facade propagation | C 消费 typed requests 时，`RuntimeFacade.apply_world_setup(...)` 返回 typed result evidence。 |
| `D3` | Fail-closed proof | invalid typed requests 可见地 reject，而不是被忽略或部分 materialize。 |
| `D4` | Legacy proof | 既有 setup calls 继续兼容。 |

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_typed_platform_spawn_bindings.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "world_setup or capability or spawn"
```

## 交付

返回 touched files、public field list、behavior summary、tests run 与剩余 docs/compatibility residuals。

当前解除阻塞说明：

- `WP20-B` 已提供 additive `TypedPlatformSpawnResult` contract 与
  `BatchWorldSetupResult.typed_platform_spawn_results`。
- `WP20-C` 已验收 C++ facade consume bridge，Python visibility 是本流剩余的
  public-surface task。
- 本流必须通过 bindings 暴露 result vector 与全部 result fields，且不改变 runtime
  materialization semantics。

## 2026-05-21 状态更新

- `src/interfaces/python/bindings_runtime.cpp` 已绑定
  `TypedPlatformSpawnResult` 与
  `BatchWorldSetupResult.typed_platform_spawn_results`，同时保留 legacy
  `entity_ids`。
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py` 已补充
  Python DTO surface 守卫，覆盖 `TypedPlatformSpawnResult` 与
  `BatchWorldSetupResult` 字段列表。
- `tests/runtime/facade/test_runtime_facade.py` 已补充 facade 路径断言，验证
  Python 可见的 admitted/materialized typed setup evidence，以及 fail-closed
  rejected typed setup evidence。
- binding DTO、facade typed setup evidence 与 WP20 B/C architecture regression
  的 focused validation 均已通过。
