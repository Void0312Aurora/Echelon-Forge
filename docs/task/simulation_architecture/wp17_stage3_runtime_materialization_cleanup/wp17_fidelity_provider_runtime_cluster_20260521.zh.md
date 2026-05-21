# WP17-D Fidelity Provider Runtime

状态：`2026-05-21` implemented / focused validation passed for reference CPU facade admission and fail-closed provider rejection。

英文主文：[wp17_fidelity_provider_runtime_cluster_20260521.md](wp17_fidelity_provider_runtime_cluster_20260521.md)

输入：

- [WP17 主计划](stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP6 backend profile policy](../wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.md)

## 目标

从 query-only capability metadata 推进到一个 runtime fidelity/provider slice。第一切片必须保守：CPU exact 仍是 maintained baseline，不支持的 accelerated/exact profiles 要明确拒绝，并由 runtime evidence 选择一个 provider family。

## 范围

范围内：

- facade-level fidelity profile request/admission 与明确 rejection；
- 一个最小 provider-family enum 或等价 runtime-owned discriminator；
- 一个 stage-node/provider-family proof；
- facade/bindings 可见 profile、parity-budget 与 fallback evidence。

范围外：

- exact GPU promotion；
- resident-state promotion；
- learned model rollout；
- capability composition 或 spawn schema changes。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `D1` | Fidelity request surface | Request 通过 facade 被接受/拒绝，并返回 `required_profile_class`、`profile_id` 与原因。 |
| `D2` | Provider-family discriminator | 一个 runtime-owned provider family 可被选择，且不改变 semantic output contracts。 |
| `D3` | Conservative fallback | Reference CPU exact 保持默认；unsupported profiles 拒绝，而非无证据静默 fallback。 |
| `D4` | Binding/test proof | Python-facing tests 可查询 capabilities 并观察 request result/rejection metadata。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "capabilities or fidelity"
python -m pytest -q tests/test_gpu_runtime_bindings.py -k "capabilities"
python -m pytest -q tests/architecture/test_wp13_*.py
```

## 交接

返回 touched capability/provider files、request/rejection behavior、exact validation outcomes，以及仍 blocked 的 backend profiles。
