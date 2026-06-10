# WP15-C Counterfactual Request Admission

状态：`2026-05-21` mergeable / first slice complete。

语言版本：

- 英文主文：[wp15_counterfactual_admission_cluster_20260521.md](wp15_counterfactual_admission_cluster_20260521.md)
- 中文辅文：`wp15_counterfactual_admission_cluster_20260521.zh.md`

输入：

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.zh.md)
- [WP15-A replay envelope and branch point](wp15_replay_envelope_branch_point_cluster_20260521.zh.md)
- [WP15-B worldline branch metadata](wp15_worldline_branch_metadata_gate_cluster_20260521.zh.md)
- [WP12 information and agency enforcement](../wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.zh.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.zh.md)

## 1. 目的

`WP15-C` 把 replay 与 worldline metadata 转成 counterfactual experiment request 的
fail-closed admission gate。请求可以作为 metadata 被接受、被拒绝，或因 unsupported
restore/runtime capability 被阻断，但绝不能静默修改 authoritative simulation state。

## 2. 范围

范围内：

- `CounterfactualExperimentRequest` 与 admission result vocabulary；
- baseline worldline、branch point、replay envelope、intervention kind、source、
  authority、backend/fidelity、capability 与 evidence refs；
- 稳定 allowed intervention/source labels；
- 对缺失 ancestry、unsupported intervention、missing authority、unsupported
  backend/fidelity/capability refs 与 raw state mutation 的 fail-closed rejection reasons；
- 若添加 public runtime surface，则提供 facade/binding proof。

范围外：

- 执行 counterfactual branch；
- broad experiment orchestration；
- public generator runtime；
- 从 experiment results 晋级 capability 或 backend support。

## 3. 候选实现接缝

编辑前检查：

- `WP15-A` 与 `WP15-B` 的输出；
- `src/runtime/contracts/backend_profile_contracts.h`；
- `src/runtime/contracts/fidelity_profile_contracts.h`；
- `src/runtime/contracts/platform_capability_contracts.h`；
- `src/runtime/facade/runtime_facade_types.h`；
- 若暴露 bindings，检查 `src/interfaces/python/bindings_runtime.cpp`。

首选方式：

- admission 先落在 contract/helpers；
- 只有 DTO 可证明 additive 且 fail-closed 时，才暴露到 facade/bindings；
- 要求显式 evidence refs，而不是从 profiles 或 capabilities 推断 support；
- admission result 中保持 unsupported restore 可见。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Ancestry required | Request 必须引用 replay envelope、branch point 与 worldline metadata。 |
| Authority required | Request 必须命名 source，并携带符合 WP12 的 authority/provenance evidence。 |
| Backend/capability guarded | Backend/fidelity/capability refs 是 evidence constraints，不是 support promotion。 |
| Raw mutation rejected | 要求 raw authoritative state mutation 的 request 必须 fail closed。 |

## 5. 验收测试

最低测试：

- 有效 admission fixture 接受 metadata-only counterfactual request；
- 缺失 replay envelope、branch point、worldline id、intervention、source、authority 或
  evidence refs 时以稳定 reason 拒绝；
- unsupported restore 阻断 executable branch claims，同时保留 diagnostics；
- raw state mutation request 被拒绝。

建议命令：

```bash
git diff --check
python -m pytest -q tests/architecture/causal_runtime/test_counterfactual_admission.py
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or replay or experiment"
```

## 6. Handoff Contract

返回：

- touched admission files；
- request/result field names；
- rejection reason vocabulary；
- tests added or updated；
- exact commands run and outcomes；
- `WP15-E` 的 blockers。
