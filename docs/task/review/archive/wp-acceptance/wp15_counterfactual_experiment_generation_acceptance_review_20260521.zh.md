# WP15 Counterfactual Experiment Generation 验收审查

状态：`2026-05-21` accepted / implementation mergeable。

语言版本：

- 英文主文：
  [wp15_counterfactual_experiment_generation_acceptance_review_20260521.md](wp15_counterfactual_experiment_generation_acceptance_review_20260521.md)
- 中文辅文：`wp15_counterfactual_experiment_generation_acceptance_review_20260521.zh.md`

输入：

- [WP15 Counterfactual Experiment Generation](../simulation_architecture/wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.zh.md)
- [WP15-A Replay Envelope And Branch Point Contract](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_replay_envelope_branch_point_cluster_20260521.zh.md)
- [WP15-B Worldline Branch Metadata Gate](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_worldline_branch_metadata_gate_cluster_20260521.zh.md)
- [WP15-C Counterfactual Request Admission](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_counterfactual_admission_cluster_20260521.zh.md)
- [WP15-D Scenario And Adversary Generation Request Surface](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_scenario_adversary_generation_surface_cluster_20260521.zh.md)
- [WP15-E Experiment Evidence And Capability Profiling Bridge](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_experiment_evidence_bridge_cluster_20260521.zh.md)
- [WP15-F Integration And Acceptance Handoff](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_integration_acceptance_cluster_20260521.zh.md)
- [WP14 Capability Composition 验收审查](wp14_capability_composition_acceptance_review_20260521.zh.md)

## 1. 结论

WP15 作为 Phase 6 的 counterfactual / experiment-generation 增量已验收。Replay envelopes、worldline branch metadata、counterfactual admission、generation request surface 与 experiment evidence ancestry 的第一切片已经由主线程验证；本收口 lane 只负责记录最终交接与验收边界。

已验收边界保持收窄：

- 不声明 full snapshot/restore；
- 不声明 maintained counterfactual rollout execution；
- 不声明 broad generator runtime 或 public experiment orchestrator；
- 不做 score-to-truth 或 score-to-support promotion；
- 不创建 causal/facade boundary 之外的第二条 semantic lifecycle。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP15-A Replay Envelope And Branch Point Contract` | pass | `tests/architecture/causal_runtime/test_replay_envelope_contracts.py` 已通过；该切片定义 deterministic replay envelope、branch point、seed、snapshot、barrier、event-order 与 facade provenance vocabulary。 |
| `WP15-B Worldline Branch Metadata Gate` | pass | `tests/architecture/causal_runtime/test_worldline_branch_metadata.py` 已通过；该切片命名 parent/child worldline、branch reason、mutation intent、provenance refs 与 unsupported-restore boundaries。 |
| `WP15-C Counterfactual Request Admission` | pass | `tests/architecture/causal_runtime/test_counterfactual_admission.py` 已通过；该切片用 fail-closed ancestry、authority、backend/fidelity 与 capability checks 接受或拒绝 metadata-only counterfactual request。 |
| `WP15-D Scenario And Adversary Generation Request Surface` | pass | `tests/scenario/test_wp15_generation_request_surface.py` 已通过，且 `tests/scenario/test_scenario_compiler.py -k "wp15 or branch or runtime"` 已通过；request surface 保持 additive 且 non-mutating。 |
| `WP15-E Experiment Evidence And Capability Profiling Bridge` | pass | `tests/architecture/causal_runtime/test_experiment_evidence_bridge.py` 已通过；experiment ancestry 保持可查询，但不会把 scores 晋级为 support claims。 |
| `WP15-F Integration And Acceptance Handoff` | pass | 本审查记录 A-E 状态、精确验证结果、residuals、README/route sync 与双语收口。 |

## 3. 验证命令

主线程在本次收口前已通过：

```bash
python -m pytest -q tests/architecture/causal_runtime/test_replay_envelope_contracts.py
python -m pytest -q tests/architecture/causal_runtime/test_worldline_branch_metadata.py
python -m pytest -q tests/architecture/causal_runtime/test_counterfactual_admission.py
python -m pytest -q tests/architecture/causal_runtime/test_experiment_evidence_bridge.py
python -m pytest -q tests/scenario/test_wp15_generation_request_surface.py
python -m pytest -q tests/scenario/test_scenario_compiler.py -k "wp15 or branch or runtime"
python -m pytest -q tests/architecture/platform_spawn/test_platform_capability_contracts.py
```

观察结果：

- 所有命令均通过。

本次收口 lane 的检查：

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP15
```

观察结果：

- 两条命令均通过。

## 4. 运行时表面摘要

- `ReplayEnvelope` 与 `BranchPoint` 保持 deterministic，并在缺少 ancestry 时 fail closed。
- `WorldlineBranchMetadata` 命名 parent/child worldline、mutation intent、provenance refs 与 unsupported-restore boundaries。
- `CounterfactualExperimentRequest` admission 仍是 metadata-only，并拒绝 raw authoritative state mutation。
- Scenario 与 adversary generation 仍是 request surface，而不是 authoritative runtime writer。
- Experiment evidence ancestry 保持可查询，但不会把 scores promotion 成 support 或 truth claims。

## 5. Residuals 与下一步

有意保留的 residuals：

- full snapshot/restore；
- maintained counterfactual rollout execution；
- broad generator runtime 与 public experiment orchestration；
- score-to-support 或 score-to-truth promotion；
- causal/facade boundary 之外的第二条 semantic lifecycle。

主线程现在可以使用本收口 packet 与已通过的 A-E 切片完成 WP15 最终验收。
