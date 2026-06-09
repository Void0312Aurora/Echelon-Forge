# WP21-A Fact Ledger And Residual Freeze

状态：`2026-05-22` pass / source-backed facts accepted。

Language:

- English canonical:
  [wp21_fact_ledger_residual_freeze_cluster_20260521.md](wp21_fact_ledger_residual_freeze_cluster_20260521.md)
- Chinese companion: `wp21_fact_ledger_residual_freeze_cluster_20260521.zh.md`

## 目的

在任何 WP21 实现波次开始前冻结 source-backed 事实。这里是最后的安全护栏：
真实 residual 必须命名，超出重构路线的内容必须明确保留为 compatibility。
本文档是 `WP21-A` closure artifact；它不是实现工作，也不提升 runtime behavior。

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

## 冻结决定

- `WP21-A` 作为 docs-only source-backed freeze 通过。
- `WP21-B` 与 `WP21-D` 在此 ledger 之后可以进入第一波 dispatch。
- 本文件本身不接受任何 runtime、binding、scenario 或 test behavior；后续
  streams 仍需要实现证据和聚焦测试。
- exact GPU、resident-state、truth/support promotion、raw authoritative
  mutation、强制 scenario-schema migration 与 unbounded worldline trees 继续阻塞。

## 源证据事实

以下证据路径已在本次 freeze 中按当前工作树核对。它们刻意保持 repo-relative，
方便后续 workers 在编辑前重新执行聚焦 source/test probe。

| 领域 | 当前事实 | 证据 | 当前支持状态 |
|---|---|---|---|
| counterfactual contracts | `src/runtime/contracts/counterfactual_replay_contracts.h` 持有 replay envelope、branch point、worldline branch metadata、counterfactual request/admission、scenario-generation metadata、experiment evidence bridge vocabulary。验证会保持 restore unsupported、拒绝 raw mutation，并对 truth/support promotion fail closed。 | `src/runtime/contracts/counterfactual_replay_contracts.h`；`tests/architecture/test_wp15_replay_envelope_contracts.py`；`tests/architecture/test_wp15_worldline_branch_metadata.py`；`tests/architecture/test_wp15_experiment_evidence_bridge.py`；`tests/architecture/test_wp15_counterfactual_admission.py` | source-backed，metadata-only restore boundary，fail-closed。 |
| selected-slice runtime | `RuntimeFacade::snapshot_counterfactual_entity()` 和 `RuntimeFacade::run_counterfactual_branch()` 已公开。`RuntimeFacade::capabilities()` 保持 resident-state、exact-GPU、shadow 为 false；branch 路径从 explicit setup 构建 parent/branch world，只接受 maintained reference CPU fidelity 请求，拒绝 raw mutation，并在 `counterfactual_selected_slice` 上比较 snapshot。 | `src/runtime/facade/runtime_facade.h`；`src/runtime/facade/runtime_facade.cpp`；`tests/runtime/facade/test_runtime_facade.py` | 已实现的 bounded selected-slice runtime。 |
| Python bindings | `bindings_runtime.cpp` 暴露 `RuntimeCapabilities`、fidelity request/admission、`RuntimeCounterfactualSnapshot`、`RuntimeWorldlineComparison`、`RuntimeCounterfactualBranchRequest`、`RuntimeCounterfactualBranchResult`、`DeviceResidentOutputDescriptor`，以及 counterfactual snapshot/branch 和 setup 的 `RuntimeFacade` 方法。 | `src/interfaces/python/bindings_runtime.cpp`；`tests/runtime/bindings/test_bindings_runtime_dto_surface.py`；`tests/runtime/facade/test_runtime_facade.py` | Python 公共面已存在，但没有晋级后的 counterfactual mainline consume bridge。 |
| scenario generation request surface | `python/scenario/compiler/generation_request.py` 定义 `wp15.scenario_generation_request.v1`、允许的 kinds/sources/evidence kinds、fail-closed validation、metadata-only artifact cloning。测试保证请求是 deterministic 的，拒绝缺失/不支持字段，并证明 artifact 不会 mutate baseline。 | `python/scenario/compiler/generation_request.py`；`tests/scenario/test_wp15_generation_request_surface.py` | 已验证的 metadata surface，不是维护中的 generator/runtime。 |
| experiment evidence bridge | WP15 contracts 把 counterfactual admission、generated input metadata 和 profile observations 串成 experiment evidence bridge 词汇。该 bridge 只允许 non-truth-claim，并拒绝 support promotion 与 generated-input drift。 | `src/runtime/contracts/counterfactual_replay_contracts.h`；`tests/architecture/test_wp15_experiment_evidence_bridge.py` | 已实现为 evidence bridge，不做 truth/support promotion。 |
| ScenarioLoader / runtime mirror residual | WP18 仍把 `gym_envs/scenario_loader/core.py` 归为 `frontend helper + runtime mirror`；`python/rl/runtime/world_batch/adapter.py` 和 `python/rl/runtime/world_batch_vec_env.py` 仍是 frontend/compatibility mirrors，raw runtime escape hatch 保持很窄且显式 allowlisted；WP18 也把 broad counterfactual/experiment runtime migration 之前的 loader mirror split/pre-gate 命名为 `WP21-R2`。 | `docs/task/simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md`；`tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`；`tests/architecture/runtime_facade/test_layering.py` | retained compatibility，不是 WP21 的实现目标。 |
| typed setup baseline | WP20 已把 typed platform spawn requests 公开：`TypedPlatformSpawnRequest`、`ResolvedPlatformSpawnPlan`、`BatchWorldSetupRequest.typed_platform_spawn_requests` 和 facade/binding surface 都存在。当前路径仍然是 compatibility-preserving，会验证 `compatibility_path_preserved`，并继续把 admitted typed setup 路由到 legacy setup materialization，而不是替换它。 | `docs/task/simulation_architecture/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.md`；`src/runtime/facade/runtime_facade.cpp`；`src/interfaces/python/bindings_runtime.cpp`；`tests/runtime/facade/test_runtime_facade.py` | additive compatibility seam，不是强制的 scenario-schema migration。 |
| backend / resident-state boundary | `RuntimeFacade::capabilities()` 把 `supports_resident_state`、`supports_exact_gpu_backend`、`supports_shadow_compare` 都写死为 false，同时仍提供 candidate id 和 rejection reason。`RuntimeFacade.runtime()` 是 compatibility/diagnostics-only。WP19 继续把 maintained truth 维持为 host-owned，并把 resident-state 作为 blocked candidate。 | `src/runtime/facade/runtime_facade.cpp`；`src/runtime/facade/runtime_facade.h`；`docs/task/simulation_architecture/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md`；`tests/runtime/facade/test_runtime_facade.py` | 明确 fail-closed，不晋级 exact GPU 或 resident-state support。 |

## 非目标

- exact GPU support 继续被阻塞。
- resident-state support 继续被阻塞。
- experiment 输出、observation 或 comparison 不会变成 truth/support claim。
- 不引入 arbitrary unbounded worldline trees。
- 不强制 scenario schema migration。
- 不在 facade/request contracts 之外修改 authoritative runtime state。

## 最终 Residual Register

| Residual ID | Owner / disposition | 剩余工作 | Pass / block criteria |
|---|---|---|---|
| `WP21-A-R1` Counterfactual contract vocabulary | all WP21 streams | 消费或扩展 WP15 replay/envelope/branch/admission/generation/evidence vocabulary；不要另起 parallel schema。 | 下游代码引用并复用 contract vocabulary 就 pass；如果新 runtime schema 绕过 admission、replay 或 evidence bridge guards 就 block。 |
| `WP21-A-R2` Selected-slice runtime boundary | `WP21-B`，然后 `WP21-C` | 在现有 selected-slice runtime 上扩展成 bounded、facade-owned 的 snapshot/restore 和 worldline boundary，带明确 barrier、seed、provider 和 evidence refs。 | restore 仍然 bounded 且 fail closed 就 pass；如果宣称 full restore、exact GPU、resident-state 或 arbitrary unbounded worldline trees 就 block。 |
| `WP21-A-R3` Scenario generation request surface | `WP21-D` | 把 WP15 request surface 变成 deterministic 的 scenario/intervention generation，带 non-mutation guards 和 artifact lineage。 | generation 是 deterministic、metadata-backed 且 non-mutating 就 pass；若强制 scenario schema migration、mutate runtime state 或改 C++ rollout 就 block。 |
| `WP21-A-R4` Counterfactual rollout and causal difference | `WP21-C` | 在 B 完成后执行 parent/branch worldline 和 causal-difference runtime。 | rollout 消费 B 的 boundary 并保持 raw mutation outside facade/request contracts 就 pass；B 未完成前一直 block。 |
| `WP21-A-R5` Experiment evidence collection | `WP21-E` | 暴露维护中的 experiment facade，收集 observations/comparisons/traces，并保留 ancestry，而不做 truth/support promotion。 | evidence collection ancestry-safe 且 non-promotional 就 pass；C 和 D 未完成前 block。 |
| `WP21-A-R6` Final cleanup and acceptance handoff | `WP21-F` | 集成 A-E、关闭 legacy residual、同步 index/docs，并在有 implementation evidence 后准备最终 acceptance。 | 只有 A-E 完成后才能 pass；如果试图只凭 planned docs 接受就 block。 |
| `WP21-A-R7` ScenarioLoader/runtime mirror compatibility | retained compatibility | 保持 `ScenarioLoader` 和 Python world-batch mirrors 作为 frontend/compatibility surfaces，直到 WP18 split/gate residual 被处理，或在 final acceptance 中明确 retained。 | mirror 保持窄且受控就 pass；一旦变成 maintained truth 就 block。 |
| `WP21-A-R8` Typed setup compatibility baseline | retained compatibility | 保持 WP20 typed setup 路径 additive 且 compatibility-preserving；不要强制 scenario-schema migration，也不要整体替换 legacy setup path。 | typed setup 仍然 additive 就 pass；如果被晋级为 mandatory mainline schema change 就 block。 |
| `WP21-A-R9` Backend/resident-state boundary | retained compatibility | 保持 resident-state 和 exact-GPU support blocked，`RuntimeFacade.runtime()` 继续只是 diagnostics-only。 | capability projection 继续 fail-closed 就 pass；任何 resident-state 或 exact GPU 晋级都 block。 |

## 首波 Readiness

| Stream | Ready 状态 | 前置条件 | 阻塞点 |
|---|---|---|---|
| `WP21-B` | A 后即可开始 | `WP21-A` 已冻结 selected-slice 事实；现有 selected-slice runtime 证据和 fail-closed restore boundary 已经存在。 | 不能声称 full restore、exact GPU、resident-state 或 arbitrary unbounded worldline trees。 |
| `WP21-D` | A 后即可开始，并且可与 B 并行 | `WP21-A` 已冻结 request-surface 事实；WP15 request/artifact surface 已存在，而且是 metadata-only。 | 不能强制 scenario schema migration、不能修改 authoritative runtime state、不能改 C++ rollout。 |

结论：`WP21-B` 和 `WP21-D` 在 `WP21-A` 之后可以并行启动。它们的写入面是分离的，唯一共同依赖是 frozen fact ledger 和同一组 non-goal 边界。

## 集成说明

- `WP21-B` 必须从 `WP21-A-R2` 开始，并把 restore proof 限定在
  facade-owned、host-visible state。
- `WP21-D` 必须从 `WP21-A-R3` 开始，并留在 Python
  scenario/intervention generation；不得编辑 C++ rollout behavior。
- `WP21-C` 等待 B，并消费 B 的 boundary，而不是创造第二条 branch execution path。
- `WP21-E` 等待 C 和 D，并通过 experiment evidence bridge 保留
  non-truth-claim ancestry。
- `WP21-F` 是唯一可以关闭 retained compatibility residuals 的 stream，并且必须等
  implementation evidence 存在之后。

## Closure Impact

`WP21-A` 关闭第一波入口 gate，但不关闭 WP21 route。直接影响是 `WP21-B`
和 `WP21-D` ready for dispatch；持续影响是后续每个 WP21 stream 都拥有针对
contracts、selected runtime、generation、loader mirrors、typed setup 与 backend
support boundaries 的具名 pass/block criterion。

## 建议验证

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP21 --summary
```

## 交接

返回 fact table、residual IDs、first-wave dispatch recommendation、touched files、
commands run 和 outcomes、blockers/residuals，并确认没有 revert 与本任务无关的
改动。
