# WP13-D Fidelity Profile Request Gate

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp13_fidelity_profile_request_gate_cluster_20260520.md](wp13_fidelity_profile_request_gate_cluster_20260520.md)
- 中文辅文：`wp13_fidelity_profile_request_gate_cluster_20260520.zh.md`

输入：

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP13-B backend profile registry gate](wp13_backend_profile_registry_gate_cluster_20260520.zh.md)
- [WP13-C parity budget evidence gate](wp13_parity_budget_evidence_gate_cluster_20260520.zh.md)
- [WP7 multi-fidelity entry conditions](../wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)
- [WP8 SCAL learning face](../wp8_learning_face/learning_face_wp8_20260520.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)

## 1. 目的

`WP13-D` 让 fidelity profiles 作为 requests 可 admission，而不是作为 support claims。
`fast_training` 或 `sensor_heavy` 这类 label 只有在绑定 maintained backend profile、
accepted parity/tolerance budget、model-family scope、validation gate 与 facade-visible
evidence 时才能被接受。

第一版实现应支持保守 baseline request，例如 `cpu_exact.reference` 上的
`exact_evaluation`，并对 unsupported multi-fidelity、adaptive、approximate、
resident-state 或 learned-provider requests 返回稳定拒绝原因。

## 2. 范围

范围内：

- 定义 fidelity profile request DTO/helper 或 admission function；
- 支持 WP7-D 的 request labels，但仅作为 labels；
- 要求 backend profile id、budget ref、model-family scope、validation gate 与
  evidence fields；
- 当 B/C gates 通过时接受保守 CPU exact baseline request；
- 拒绝 unsupported `fast_training`、`sensor_heavy`、adaptive scheduling、learned
  provider、exact GPU、resident-state 与 shadow-backed claims，除非对应 gates 存在。

范围外：

- adaptive fidelity scheduling；
- backend selection；
- learned `ModelProvider` runtime interface；
- approximate execution；
- 把 runtime capability support booleans 改为 true。

## 3. 候选实现缝

编辑前检查：

- `src/runtime/contracts/runtime_dto_contracts.h`
- `src/runtime/contracts/world_batch_contracts.h`
- `src/runtime/contracts/policy_contracts.h`
- `WP13-B` / `WP13-C` 产生的新 backend profile 或 parity budget helper
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/runtime/facade/test_runtime_facade.py`

首选做法：

- 第一切片把 fidelity request admission 保持为 pure validator/helper；
- 不把它接入 execution dispatch，除非后续 WP 明确负责 scheduling 或 backend selection；
- 保留 `WP13-E` 可通过 bindings 暴露的 request/evidence fields；
- 使用稳定 rejection reasons，例如 `fidelity_profile_requires_maintained_backend_profile`、
  `fidelity_profile_requires_accepted_budget` 与
  `adaptive_fidelity_scheduling_not_implemented`。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Request label | Label 只是描述，不能单独暗示 support。 |
| Backend binding | Accepted request 必须引用 maintained backend profile。 |
| Budget binding | Accepted request 必须引用 accepted parity 或 tolerance budget。 |
| Model scope | Request 必须命名覆盖的 lifecycle stages 或 model families。 |
| Evidence | Request 必须携带 facade-visible evidence ids 或 required evidence fields。 |
| Unsupported paths | Adaptive、learned、approximate、exact GPU、resident-state 与 shadow-backed requests fail closed。 |

## 5. 验收测试

最低测试：

- 使用 `cpu_exact.reference` 与 `parity_budget.cpu_exact.reference.v1` 的 baseline
  `exact_evaluation` request 通过 admission；
- 缺少 backend profile id 拒绝；
- 缺少或 non-accepted budget 拒绝；
- `fast_training` 与 `sensor_heavy` 在缺少 accepted gates 时不暗示 maintained
  multi-fidelity support；
- adaptive scheduling 与 learned provider requests 以稳定 reasons 拒绝；
- exact GPU、resident-state 与 shadow-backed fidelity requests 在 B/C gates 报告
  maintained evidence 前拒绝。

建议命令：

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/facade/test_runtime_facade.py
```

## 6. 交接契约

返回：

- touched request DTO/helper files；
- fidelity labels 与 admission helper names；
- accepted baseline request fixture；
- rejection reason vocabulary；
- 新增或更新 tests；
- 精确 commands 与 outcomes；
- 给 `WP13-E` binding/facade proof 的 blockers；
- later adaptive fidelity 或 `ModelProvider` work residuals。
