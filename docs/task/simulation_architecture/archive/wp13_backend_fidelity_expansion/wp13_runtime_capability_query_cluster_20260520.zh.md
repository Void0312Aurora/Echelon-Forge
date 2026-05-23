# WP13-A Runtime Capability Query And Rejection Surface

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp13_runtime_capability_query_cluster_20260520.md](wp13_runtime_capability_query_cluster_20260520.md)
- 中文辅文：`wp13_runtime_capability_query_cluster_20260520.zh.md`

输入：

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP7 runtime capability projection](../wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.zh.md)
- [WP6 backend profile registry](../wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)
- [WP6 resident-state boundary rules](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)
- 当前 `src/runtime/facade/runtime_facade_types.h`
- 当前 `src/runtime/facade/runtime_facade.cpp`
- 当前 `src/interfaces/python/bindings_runtime.cpp`
- 当前 `tests/runtime/facade/test_runtime_facade.py`
- 当前 `tests/test_gpu_runtime_bindings.py`
- 当前 `tests/architecture/test_runtime_facade_layering.py`

## 1. 目的

`WP13-A` 让 capability answer 可检查，但不制造新的 capability claim。调用方应能查询
什么 backend/fidelity capability 是 maintained、哪个 profile 或 budget 支撑它，以及
unsupported claim 为什么被拒绝。

第一轮验收结果仍应保持：

```yaml
supports_device_observation_view: false
supports_resident_state: false
supports_exact_gpu_backend: false
supports_shadow_compare: false
```

本切片改变的是 query/rejection evidence，不是 support promotion。

## 2. 范围

范围内：

- 在 `RuntimeCapabilities` 内或旁边添加保守 query metadata；
- 暴露 maintained baseline profile 与 budget references；
- 暴露 exact GPU、resident-state、device observation、shadow 与 multi-fidelity
  claim 的 unsupported/rejected reasons；
- 让 GPU helper/probe availability 只作为 deployment fact 或 diagnostics；
- 为新增字段或 helper DTO 更新 Python binding/tests。

范围外：

- 把 unsupported support booleans 改成 true；
- backend selection；
- adaptive fidelity scheduling；
- 从 facade/core capability projection 直接调用 GPU helper/probe；
- profile registry row ownership，除非与 `WP13-B` 协调极小 shared DTO 名称。

## 3. 候选实现缝

编辑前检查：

- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/facade/test_runtime_facade.py`
- `tests/test_gpu_runtime_bindings.py`
- `tests/architecture/test_runtime_facade_layering.py`

首选做法：

- 保持既有 boolean support fields 稳定，避免破坏兼容；
- 只在测试能证明默认值时新增 `maintained_backend_profile_id`、
  `maintained_parity_budget_ref` 或 `*_rejection_reason` 等 metadata 字段；
- rejection reasons 使用适合 Python 测试的稳定 string constants 或 enum-like values；
- 保持 facade/core 不依赖 `src/gpu` helper 或 probe implementation。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Conservative support | 现有 unsupported backend/fidelity booleans 保持 false。 |
| Queryability | Maintained baseline 与 unsupported reason metadata 可通过 maintained facade/binding surface 看到。 |
| Probe separation | GPU helper/probe bindings 可以存在，但不能影响 maintained support claims。 |
| Rejection evidence | Unsupported exact GPU、resident-state、shadow、device-observation 与 multi-fidelity claims 产出稳定 reasons。 |

## 5. 验收测试

最低测试：

- `RuntimeFacade.capabilities()` 暴露任何新增 metadata fields，且默认值稳定保守；
- Python bindings 暴露相同字段或 helper DTO；
- GPU helper/probe binding availability 不会翻转 exact GPU、resident-state、
  device-observation 或 shadow support；
- architecture layering test 仍拒绝 facade/core 依赖 GPU helper implementation；
- unsupported reason values 指向 missing maintained profile、missing budget 或 blocked
  candidate status，而不是泛化失败。

建议命令：

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_runtime_facade_layering.py
```

## 6. 交接契约

返回：

- touched DTO/projection files；
- 新增 capability metadata fields 或 helper names；
- rejection reason vocabulary；
- 新增或更新的 tests；
- 精确 commands 与 outcomes；
- 给 `WP13-E` 的 blockers 和 residuals；
- 如果 shared struct names 变化，给 `WP13-B` / `WP13-C` 的 integration notes。
