# WP13-B Backend Profile Registry Runtime Gate

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp13_backend_profile_registry_gate_cluster_20260520.md](wp13_backend_profile_registry_gate_cluster_20260520.md)
- 中文辅文：`wp13_backend_profile_registry_gate_cluster_20260520.zh.md`

输入：

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP6 backend profile policy](../wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.zh.md)
- [WP6 backend profile registry](../wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)
- [WP6 resident-state boundary rules](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP7 registry materialization](../wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.zh.md)
- [WP7 promotion evidence gates](../wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.zh.md)

## 1. 目的

`WP13-B` 把已验收的 backend profile 文档注册表转成最小 code-owned gate。profile
records 应在任何 runtime capability surface 引用它们之前变得可检查、可机器校验。

第一版 runtime registry 可以很小，应包含已验收 seed records：

- `cpu_exact.reference`
- `gpu_helpers.diagnostics_only`
- `gpu_exact.unmaintained_candidate`
- `resident_state.unmaintained_candidate`
- `shadow_compare.unmaintained_candidate`

初始 gate 中只有 `cpu_exact.reference` 是 maintained。

## 2. 范围

范围内：

- 添加 backend profile records 或 schema 的 C++ contract/header/helper；
- 编码 maintained profiles 的 required fields；
- 校验 maintained、candidate 与 diagnostics-only 边界；
- 为 A/C/D consumers 暴露 profile lookup 与 rejection reason helpers；
- 添加测试证明 candidate 与 diagnostics-only rows 不会成为 maintained support。

范围外：

- 除 `parity_budget_ref` 外的 parity budget row implementation；
- 把 `RuntimeCapabilities` support booleans 改为 true；
- GPU helper/probe implementation；
- backend selection 或 execution dispatch；
- resident-state ownership promotion。

## 3. 候选实现缝

编辑前检查：

- `src/runtime/contracts/`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `tests/architecture/`
- `tests/runtime/facade/test_runtime_facade.py`
- `tests/test_gpu_runtime_bindings.py`

首选做法：

- 若没有合适 owner，则在 `src/runtime/contracts/` 下创建小型 backend profile
  contract surface；
- row data 靠近 compile-time constants 或 simple functions；
- 提供 `is_maintained_backend_profile(...)` 或
  `validate_backend_profile_for_capability(...)` 这类 validators；
- 对 unmaintained candidates 与 diagnostics rows 返回稳定 rejection reasons；
- Python exposure 留给 `WP13-E`，除非 A/E 决定现在绑定 helper。

## 4. 必需 Profile 字段

gate 必须保留 WP6 required metadata：

| Field | Required behavior |
|-------|-------------------|
| `backend_profile_id` | 稳定 id。 |
| `profile_class` | `reference`、`accelerated_exact`、`resident_state`、`approximate` 或 `diagnostics_only`。 |
| `comparison_reference` | Maintained semantic comparison anchor 或显式 non-maintained marker。 |
| `host_state_owner` | Host-owned state 或 output scope。 |
| `backend_state_owner` | Backend-owned state 或显式 absence。 |
| `sync_policy` | Host-owned、backend-owned、partial-sync、observation-only、export-only 或 blocked。 |
| `state_scope` | 覆盖 state family 或 candidate scope。 |
| `parity_budget_ref` | Profile-owned budget reference。 |
| `observability_scope` | Maintained 或 diagnostics-only export scope。 |
| `compatibility_rule` | Legacy/helper projection rule。 |
| `deprecation_rule` | Removal、narrowing 或 promotion condition。 |
| `validation_gate` | Maintained use 前必需的 review/test gate。 |

## 5. 验收测试

最低测试：

- registry 暴露所有已验收 seed profile ids；
- 只有 `cpu_exact.reference` 是 maintained；
- candidate exact GPU、resident-state 与 shadow rows 返回 fail-closed rejection reasons；
- diagnostics-only GPU helper row 不能授权 maintained exact GPU、resident-state 或 shadow support；
- maintained-row validator 在必需字段缺失或为空时失败。

建议命令：

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py
```

## 6. 交接契约

返回：

- touched registry/contract files；
- 已编码 profile ids 与 profile classes；
- validation helper names 与 rejection reason values；
- 新增或更新 tests；
- 精确 commands 与 outcomes；
- 给 `WP13-C` budget binding 或 `WP13-A` capability projection 的 blockers；
- 文档比第一版 code-owned registry 更丰富之处的 residuals。
