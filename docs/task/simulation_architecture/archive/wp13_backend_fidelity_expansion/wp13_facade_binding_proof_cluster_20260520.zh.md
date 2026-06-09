# WP13-E Facade And Binding Proof

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp13_facade_binding_proof_cluster_20260520.md](wp13_facade_binding_proof_cluster_20260520.md)
- 中文辅文：`wp13_facade_binding_proof_cluster_20260520.zh.md`

输入：

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP13-A runtime capability query](wp13_runtime_capability_query_cluster_20260520.zh.md)
- [WP13-B backend profile registry gate](wp13_backend_profile_registry_gate_cluster_20260520.zh.md)
- [WP13-C parity budget evidence gate](wp13_parity_budget_evidence_gate_cluster_20260520.zh.md)
- [WP13-D fidelity profile request gate](wp13_fidelity_profile_request_gate_cluster_20260520.zh.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)
- [WP12 information and agency enforcement](../wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.zh.md)

## 1. 目的

`WP13-E` 证明 backend/fidelity query 与 rejection 行为可通过 maintained facade 与
Python binding surfaces 看到。它是 proof lane，不拥有 registry、budget 或 fidelity
semantics。

理想证据是“无聊但可靠”的：调用方可以检查 supported baseline metadata，提交或验证
unsupported backend/fidelity requests，并在不触碰 raw runtime 或 GPU helper path 的情况下
收到稳定 fail-closed reasons。

## 2. 范围

范围内：

- 通过 `RuntimeFacade` 和/或 Python bindings 暴露 A-D surfaces；
- 为新增 DTO、fields 或 helper functions 添加 binding smoke tests；
- 添加 facade proof tests 覆盖 query、rejection 与 evidence visibility；
- 保持现有围绕 GPU helper/probe implementation 的 layering guards；
- 如果某个 C++ helper 有意不绑定，记录 residual。

范围外：

- 创建 B/C 拥有的 profile 或 budget records；
- 定义 D 拥有的新 fidelity request semantics；
- backend selection、execution dispatch、adaptive scheduling 或 promotion；
- raw `WorldBatchRuntime` escape hatches。

## 3. 候选实现缝

A-D 落地后检查：

- `src/runtime/facade/runtime_facade.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/facade/test_runtime_facade.py`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/runtime/bindings/test_bindings_policy_surface.py`
- `tests/architecture/runtime_facade/test_layering.py`

首选做法：

- 只绑定可被测试立即覆盖的稳定 DTO/helper；
- 让所有 unsupported capability requests fail closed；
- binding names 尽量贴近 C++ names，降低维护成本；
- 优先使用 facade-shaped proof，而不是 raw helper invocation。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Facade visibility | Query 与 rejection evidence 可通过 maintained facade APIs 或 DTOs 访问。 |
| Binding visibility | Python callers 可检查相同的稳定 fields 或 helper results。 |
| Layering | Facade/core 不为 capability answers 调用 GPU helper/probe implementation。 |
| No raw backend path | Proof 不需要直接访问 `WorldBatchRuntime` 或 GPU helper path。 |
| Conservative support | 现有 unsupported support booleans 保持 false。 |

## 5. 验收测试

最低测试：

- Python binding smoke 覆盖任何新增 capability/profile/budget/fidelity DTO 或 helper；
- facade test 证明 baseline profile/budget evidence 可查询；
- facade 或 binding test 证明 unsupported exact GPU、resident-state、shadow 与
  multi-fidelity/adaptive requests 以稳定 reasons 拒绝；
- 既有 GPU helper tests 仍证明 helper/probe availability 不会晋级 support；
- architecture layering test 仍通过。

建议命令：

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade/test_runtime_facade.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py
CMO_BUILD_DIR=build-workshop pytest -q tests/test_gpu_runtime_bindings.py tests/architecture/runtime_facade/test_layering.py
```

## 6. 交接契约

返回：

- touched facade and binding files；
- exposed DTOs、fields 与 helper names；
- 新增或更新 proof tests；
- 精确 commands 与 outcomes；
- acceptance closure blockers；
- unbound helpers 或 intentionally deferred runtime wiring residuals。
