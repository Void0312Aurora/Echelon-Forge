# WP15-E Experiment Evidence And Capability Profiling Bridge

状态：`2026-05-21` mergeable / first slice complete。

语言版本：

- 英文主文：[wp15_experiment_evidence_bridge_cluster_20260521.md](wp15_experiment_evidence_bridge_cluster_20260521.md)
- 中文辅文：`wp15_experiment_evidence_bridge_cluster_20260521.zh.md`

输入：

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.zh.md)
- [WP15-C counterfactual admission](wp15_counterfactual_admission_cluster_20260521.zh.md)
- [WP15-D scenario and adversary generation request surface](wp15_scenario_adversary_generation_surface_cluster_20260521.zh.md)
- [WP8 learning face](../wp8_learning_face/learning_face_wp8_20260520.zh.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.zh.md)

## 1. 目的

`WP15-E` 把 experiment runs 与 comparison evidence 连接到 counterfactual admission、
generated inputs、backend/fidelity profiles、platform capabilities 与 WP8 capability
profiling vocabulary。该桥接应让 evidence ancestry 可查询，但不把 experimental scores
变成 maintained support 或 truth claims。

## 2. 范围

范围内：

- experiment run、comparison、generated-input 与 profile-observation evidence vocabulary；
- replay envelope、branch point、worldline、counterfactual admission、generation request、
  backend profile、fidelity profile、parity budget、capability bundle 与 resolved spawn plan
  evidence references；
- non-truth-claim 与 non-promotion validation gates；
- focused tests，证明缺失 ancestry 与 unsupported promotions fail closed。

范围外：

- training 或 evaluation loop rewrites；
- broad experiment scheduler/orchestrator；
- 从 scores 晋级 backend、fidelity、capability 或 policy support；
- 改变 WP8 capability profile semantics。

## 3. 候选实现接缝

编辑前检查：

- `WP15-C` 与 `WP15-D` 的输出；
- `docs/task/simulation_architecture/wp8_learning_face/*capability*`；
- `src/runtime/contracts/backend_profile_contracts.h`；
- `src/runtime/contracts/parity_budget_contracts.h`；
- `src/runtime/contracts/fidelity_profile_contracts.h`；
- `src/runtime/contracts/platform_capability_contracts.h`；
- `tests/architecture/test_wp14_*.py`。

首选方式：

- 第一切片先做 evidence contracts/helpers 与 focused tests；
- 要求显式 ancestry refs，而不是读取 ambient runtime state；
- 包含阻止 score-to-support promotion 的 validation flag 或 reason；
- learning/profile labels 保持 observational。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Experiment ancestry | Experiment run 在适用时引用 replay、branch、admission、generation、backend/fidelity 与 capability evidence。 |
| Comparison evidence | Baseline 与 variant comparisons 保留 branch/worldline ids 以及 seed/version metadata。 |
| Profile observation | Capability profile outputs 仍是带 evidence refs 的 observations，不是 support claims。 |
| Promotion blocked | Scores 不能在没有 accepted gates 的情况下晋级 backend/fidelity/capability support。 |

## 5. 验收测试

最低测试：

- 有效 experiment evidence fixture 连接 counterfactual admission 与 generated inputs；
- validation 拒绝缺失 run id、comparison id、branch ancestry、generation ref、
  backend/fidelity ref 或必要 capability evidence；
- profile observation 不能把 support/truth 标为 maintained；
- score-to-support promotion 以稳定 reason 被拒绝。

建议命令：

```bash
git diff --check
python -m pytest -q tests/architecture/causal_runtime/test_experiment_evidence_bridge.py
python -m pytest -q tests/architecture/platform_spawn/test_platform_capability_contracts.py
```

## 6. Handoff Contract

返回：

- touched evidence bridge files；
- experiment/profile field names；
- validation helper names 与 rejection reasons；
- tests added or updated；
- exact commands run and outcomes；
- `WP15-F` 的 blockers。
