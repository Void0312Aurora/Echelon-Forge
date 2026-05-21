# WP21-A Fact Ledger And Residual Freeze

状态：`2026-05-21` pass / source-backed facts accepted。

Language:

- English canonical:
  [wp21_fact_ledger_residual_freeze_cluster_20260521.md](wp21_fact_ledger_residual_freeze_cluster_20260521.md)
- Chinese companion: `wp21_fact_ledger_residual_freeze_cluster_20260521.zh.md`

## 目的

在任何 WP21 实现波次开始前冻结 source-backed 事实。这里是最后的安全护栏：
真实 residual 必须命名，超出重构路线的内容必须明确保留为 compatibility。

## 范围

范围内：

- 盘点 counterfactual contracts、selected-slice runtime、Python bindings、
  scenario generation requests、experiment evidence bridge、`ScenarioLoader`
  mirror residuals、typed setup baseline 与 backend/resident-state boundary
  的 source/test ledger；
- final residual register，并为每项指定 owner stream 与 pass/block criteria；
- `WP21-B` 与 `WP21-D` 第一波能否并行的 readiness decision。

范围外：

- 修改 runtime behavior；
- 创建 acceptance review；
- 无 source facts 地改变 final-stage scope；
- 新增阶段来吸收剩余工作。

## 源证据事实

| 领域 | 当前事实 | 证据 | 当前支持状态 |
|---|---|---|---|
| counterfactual contracts | `src/runtime/contracts/counterfactual_replay_contracts.h` 持有 replay envelope、branch point、worldline branch metadata、counterfactual request/admission、scenario-generation metadata、experiment evidence bridge vocabulary。验证会保持 restore unsupported、拒绝 raw mutation，并对 truth/support promotion fail closed。 | `src/runtime/contracts/counterfactual_replay_contracts.h`；`tests/architecture/test_wp15_replay_envelope_contracts.py`；`tests/architecture/test_wp15_worldline_branch_metadata.py`；`tests/architecture/test_wp15_experiment_evidence_bridge.py`；`tests/architecture/test_wp15_counterfactual_admission.py` | source-backed，metadata-only restore boundary，fail-closed。 |
| selected-slice runtime | `RuntimeFacade::snapshot_counterfactual_entity()` 和 `RuntimeFacade::run_counterfactual_branch()` 已公开。`RuntimeFacade::capabilities()` 保持 resident-state、exact-GPU、shadow 为 false；branch 路径从 explicit setup 构建 parent/branch world，只接受 maintained reference CPU fidelity 请求，拒绝 raw mutation，并在 `counterfactual_selected_slice` 上比较 snapshot。 | `src/runtime/facade/runtime_facade.h`；`src/runtime/facade/runtime_facade.cpp`；`tests/runtime/facade/test_runtime_facade.py` | 已实现的 bounded selected-slice runtime。 |
| Python bindings | `bindings_runtime.cpp` 暴露 `RuntimeCapabilities`、fidelity request/admission、`RuntimeCounterfactualSnapshot`、`RuntimeWorldlineComparison`、`DeviceResidentOutputDescriptor`，以及 counterfactual snapshot/branch 和 setup 的 `RuntimeFacade` 方法。 | `src/interfaces/python/bindings_runtime.cpp` | Python 公共面已存在，但没有晋级后的 counterfactual mainline consume bridge。 |
| scenario generation request surface | `python/scenario/compiler/generation_request.py` 定义 `wp15.scenario_generation_request.v1`、允许的 kinds/sources/evidence kinds、fail-closed validation、metadata-only artifact cloning。测试保证请求是 deterministic 的，拒绝缺失/不支持字段，并证明 artifact 不会 mutate baseline。 | `python/scenario/compiler/generation_request.py`；`tests/scenario/test_wp15_generation_request_surface.py` | 已验证的 metadata surface，不是维护中的 generator/runtime。 |
| experiment evidence bridge | WP15 contracts 把 counterfactual admission、generated input metadata 和 profile observations 串成 experiment evidence bridge 词汇。该 bridge 只允许 non-truth-claim，并拒绝 support promotion 与 generated-input drift。 | `src/runtime/contracts/counterfactual_replay_contracts.h`；`tests/architecture/test_wp15_experiment_evidence_bridge.py` | 已实现为 evidence bridge，不做 truth/support promotion。 |
| ScenarioLoader / runtime mirror residual | WP18 仍把 `gym_envs/scenario_loader/core.py` 归为 `frontend helper + runtime mirror`；`python/rl/runtime/world_batch/adapter.py` 和 `python/rl/runtime/world_batch_vec_env.py` 仍是 frontend/compatibility mirrors，raw runtime escape hatch 也保持很窄。 | `docs/task/simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md`；`tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`；`tests/architecture/test_runtime_facade_layering.py` | retained compatibility，不是 WP21 的实现目标。 |
| typed setup baseline | WP20 已把 typed platform spawn requests 公开：`TypedPlatformSpawnRequest`、`ResolvedPlatformSpawnPlan`、`BatchWorldSetupRequest.typed_platform_spawn_requests` 和 facade/binding surface 都存在。当前路径仍然是 compatibility-preserving，还是通过 legacy setup materialization 路由，而不是替换它。 | `docs/task/simulation_architecture/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.md`；`src/runtime/facade/runtime_facade.cpp`；`tests/runtime/facade/test_runtime_facade.py` | additive compatibility seam，不是强制的 scenario-schema migration。 |
| backend / resident-state boundary | `RuntimeFacade::capabilities()` 把 `supports_resident_state`、`supports_exact_gpu_backend`、`supports_shadow_compare` 都写死为 false，同时仍提供 candidate id 和 rejection reason。`RuntimeFacade.runtime()` 是 compatibility/diagnostics-only。WP19 继续把 maintained truth 维持为 host-owned，并把 resident-state 作为 blocked candidate。 | `src/runtime/facade/runtime_facade.cpp`；`src/runtime/facade/runtime_facade.h`；`docs/task/simulation_architecture/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md`；`tests/runtime/facade/test_runtime_facade.py` | 明确 fail-closed，不晋级 exact GPU 或 resident-state support。 |

## 非目标

- exact GPU support 继续被阻塞。
- resident-state support 继续被阻塞。
- experiment 输出、observation 或 comparison 不会变成 truth/support claim。
- 不引入 arbitrary unbounded worldline trees。
- 不强制 scenario schema migration。
- 不在 facade/request contracts 之外修改 authoritative runtime state。

## 最终 Residual Register

| Residual | Owner / disposition | 剩余工作 | Pass / block criteria |
|---|---|---|---|
| `WP21-B` Snapshot Restore And Worldline Boundary | `WP21-B` | 在现有 selected-slice runtime 上扩展成 bounded、facade-owned 的 snapshot/restore 和 worldline boundary，带上明确 barrier、seed、provider 和 evidence refs。 | 只要 restore 仍然 bounded 且 fail closed 就 pass；如果开始宣称 full restore、exact GPU、resident-state 或 arbitrary unbounded worldline trees 就 block。 |
| `WP21-C` Counterfactual Rollout And Causal Difference | `WP21-C` | 在 B 完成后执行 parent/branch worldline 和 causal-difference runtime。 | 只要 rollout 消费 B 的 boundary 并保持 raw mutation  बाहर 就 pass；B 未完成前一直 block。 |
| `WP21-D` Scenario Intervention Generation Runtime | `WP21-D` | 把 WP15 request surface 变成 deterministic 的 scenario/intervention generation，带 non-mutation guards 和 artifact lineage。 | 只要 generation 是 deterministic、metadata-backed 且 non-mutating 就 pass；若强制 scenario schema migration 或改 C++ rollout 就 block。 |
| `WP21-E` Experiment Facade And Evidence Collection | `WP21-E` | 暴露维护中的 experiment facade，收集 observations/comparisons/traces，并保留 ancestry，而不做 truth/support promotion。 | 只要 evidence collection ancestry-safe 且 non-promotional 就 pass；C 和 D 未完成前 block。 |
| `WP21-F` Final Cleanup And Acceptance Handoff | `WP21-F` | 集成 A-E、关闭 legacy residual、同步 index/docs，并在有 implementation evidence 后准备最终 acceptance。 | 只有 A-E 完成后才能 pass；如果试图只凭 planned docs 接受就 block。 |
| `Retained compatibility: ScenarioLoader mirror` | retained compatibility | 保持 `ScenarioLoader` 和 Python world-batch mirrors 作为 frontend/compatibility surfaces，直到 WP18 split/gate 完成。 | mirror 保持窄且受控就 pass；一旦变成 maintained truth 就 block。 |
| `Retained compatibility: typed setup baseline` | retained compatibility | 保持 WP20 typed setup 路径 additive 且 compatibility-preserving；不要强制 scenario-schema migration，也不要整体替换 legacy setup path。 | typed setup 仍然 additive 就 pass；如果被晋级为 mandatory mainline schema change 就 block。 |
| `Retained compatibility: backend/resident-state boundary` | retained compatibility | 保持 resident-state 和 exact-GPU support blocked，`RuntimeFacade.runtime()` 继续只是 diagnostics-only。 | capability projection 继续 fail-closed 就 pass；任何 resident-state 或 exact GPU 晋级都 block。 |

## 首波 Readiness

| Stream | Ready 状态 | 前置条件 | 阻塞点 |
|---|---|---|---|
| `WP21-B` | A 后即可开始 | `WP21-A` 已冻结 selected-slice 事实；现有 selected-slice runtime 证据和 fail-closed restore boundary 已经存在。 | 不能声称 full restore、exact GPU、resident-state 或 arbitrary unbounded worldline trees。 |
| `WP21-D` | A 后即可开始，并且可与 B 并行 | `WP21-A` 已冻结 request-surface 事实；WP15 request/artifact surface 已存在，而且是 metadata-only。 | 不能强制 scenario schema migration、不能修改 authoritative runtime state、不能改 C++ rollout。 |

结论：`WP21-B` 和 `WP21-D` 在 `WP21-A` 之后可以并行启动。它们的写入面是分离的，唯一共同依赖是 frozen fact ledger 和同一组 non-goal 边界。

## 建议验证

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP21 --summary
```

## 交接

返回 fact table、residual IDs、first-wave dispatch recommendation、touched files、
commands run 和 outcomes、blockers/residuals，并确认没有 revert 与本任务无关的
改动。
