# WP13-C Parity Budget Evidence Gate

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp13_parity_budget_evidence_gate_cluster_20260520.md](wp13_parity_budget_evidence_gate_cluster_20260520.md)
- 中文辅文：`wp13_parity_budget_evidence_gate_cluster_20260520.zh.md`

输入：

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP6 parity budget registry](../wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.zh.md)
- [WP6 backend profile registry](../wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)
- [WP7 promotion evidence gates](../wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.zh.md)
- [WP5 validation harness](../wp5_validation_harness/validation_harness_wp5_20260519.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)

## 1. 目的

`WP13-C` 把 parity budgets 转成 code-owned evidence gates。backend profile 只有在
其 profile-owned parity budget 存在、class-compatible，且已为请求能力通过 acceptance
时，才能被视作 maintained。

第一版实现应继续保留 `cpu_exact.reference` 作为唯一 maintained exact baseline budget。
Candidate exact GPU、resident-state 与 shadow budgets 仍不能用于 maintained promotion。

## 2. 范围

范围内：

- 在 runtime contract owner 下添加小型 parity budget record/schema/helper；
- 编码第一版 profile gate 需要的已验收 budget ids；
- 校验 profile/budget class compatibility；
- 校验 comparison domains、sync barriers、diagnostics requirements、mismatch policy 与
  acceptance gate presence；
- 对 missing、candidate、diagnostics-only 或 incompatible budgets 返回稳定 rejection reasons。

范围外：

- 实现 numeric comparator engines；
- 执行 backend comparisons；
- 把 backend support booleans 改成 true；
- adaptive fidelity scheduling；
- 编写 `WP13-B` 所属 backend profile registry rows，除非已约定 integration。

## 3. 候选实现缝

编辑前检查：

- `src/runtime/contracts/`
- `src/runtime/contracts/stage_node_manifest_registry.h`
- `src/runtime/facade/runtime_facade_types.h`
- `tests/architecture/`
- `tests/runtime/facade/test_runtime_facade.py`

首选做法：

- 第一版 budget gate 保持 deterministic 与 data-driven；
- 使用 `parity_budget.cpu_exact.reference.v1` 这类稳定 id；
- 将 comparison domains 表示为 named fields 或 string vectors，而不是自由散文；
- 显式表示 `acceptance_gate`，让 candidate budgets 不能因存在 row 就通过；
- future comparator execution 作为 residual，而不是隐藏 claim。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Budget ownership | Maintained capability 必须引用 backend profile 拥有的 budget。 |
| Class compatibility | Profile class 与 budget class 必须匹配或显式兼容。 |
| Acceptance evidence | Maintained use 需要 accepted gate，而不是仅有 budget row。 |
| Comparison domains | Event order 与 snapshot versions 仍是 exact identity domains。 |
| Diagnostics split | Diagnostics prose 与 report-only helper outputs 不能成为 maintained truth。 |

## 5. 验收测试

最低测试：

- `parity_budget.cpu_exact.reference.v1` 存在，且对 `cpu_exact.reference` accepted；
- candidate exact GPU、resident-state 与 shadow budgets 拒绝 maintained capability promotion；
- missing budget ref 以稳定 reason 拒绝；
- incompatible profile/budget class 以稳定 reason 拒绝；
- comparison-domain data 包含 event order、snapshot versions、observation export、
  diagnostics trace、sync barriers、mismatch policy 与 acceptance gate。

建议命令：

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture tests/runtime/facade/test_runtime_facade.py
```

## 6. 交接契约

返回：

- touched parity budget contract/helper files；
- 已编码 budget ids；
- validator names 与 rejection reason values；
- 新增或更新 tests；
- 精确 commands 与 outcomes；
- 给 `WP13-A` projection 或 `WP13-D` fidelity request binding 的 blockers；
- future comparator execution residuals。
