# WP17 Stage 3 Runtime Materialization And Cleanup 验收审查

状态：`2026-05-21` accepted / selected-slice implementation mergeable。

语言版本：

- 英文主文：[wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.md](wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.md)
- 中文辅文：`wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.zh.md`

输入：

- [WP17 Stage 3 Runtime Materialization And Cleanup](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [WP17-A Fact Ledger And Boundary Freeze](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_fact_ledger_and_boundary_freeze_cluster_20260521.zh.md)
- [WP17-B Facade Business Migration And Compatibility Cleanup](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_facade_business_migration_cleanup_cluster_20260521.zh.md)
- [WP17-C Multi-Rate Runtime Example](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_multirate_runtime_example_cluster_20260521.zh.md)
- [WP17-D Fidelity Provider Runtime](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_fidelity_provider_runtime_cluster_20260521.zh.md)
- [WP17-E Capability Spawn Runtime Promotion](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.zh.md)
- [WP17-F Counterfactual Runtime Slice And Closure](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_counterfactual_runtime_closure_cluster_20260521.zh.md)
- [WP17 dispatch queue](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_subagent_dispatch_queue_20260521.zh.md)
- [WP16 验收审查](wp16_runtime_spine_consolidation_acceptance_review_20260521.zh.md)

## 1. 结论

WP17 已作为最后的 Stage 3 selected-slice runtime-materialization 与 cleanup
增量验收。它把 WP16 handoff 后仍然悬空的运行时表面，收束为有边界的 runtime
行为：facade-shaped batch reads、selected cadence evidence、reference CPU fidelity
admission、capability-gated spawn materialization，以及一条 explicit-setup
selected-entity counterfactual branch/compare path。

这里明确不是 global rewrite：

- 没有 global scheduler rewrite；
- 没有 exact GPU、resident-state、shadow 或 adaptive multi-fidelity 晋级；
- 没有强制 public `spawn_platform` schema；
- 没有删除 `WorldBatchRuntime`、`batch_runtime` 或 `RuntimeFacade.runtime()`；
- 没有 arbitrary live-world clone、full snapshot/restore、任意深度 worldline tree
  或 full counterfactual experiment orchestration。

已验收的 runtime 边界是 WP17 记录的 selected slice：维护中的 caller 可以使用
facade-shaped adapter/env 方法读取 execution-episode readiness 与 state export；
runtime-window selected slice 会发出 cadence trace evidence；reference CPU exact
evaluation 可以经由 facade admission；不支持的 provider fail closed；
default unit factory 会在内部消费 resolved platform spawn plans；并且
`RuntimeFacade::run_counterfactual_branch()` 可以基于 explicit setup，为一个
selected entity 创建 parent/branch worlds 并比较 causal deltas。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP17-A Fact Ledger And Boundary Freeze` | pass | WP17 主计划在声明实现前，已经按当前代码事实校正 runtime capabilities、provider dispatch、capability composition、counterfactual runtime、multi-rate scheduling 与 training/batch business paths。 |
| `WP17-B Facade Business Migration And Compatibility Cleanup` | pass | `python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch_vec_env.py` 与 `tests/architecture/runtime_facade` 暴露并守住 facade-shaped execution-episode ready/state reads，同时把 `batch_runtime` 保留为 compatibility view。 |
| `WP17-C Multi-Rate Runtime Example` | pass | `src/runtime/facade/runtime_window_coordinator.h`、`src/runtime/contracts/stage_node_manifest_registry.h`、`tests/runtime/facade/test_runtime_facade_window_loop_injection.py` 与 `tests/world_batch/test_single_world_batch_runtime.py` 证明 selected cadence slice、hold/expiry/barrier evidence，以及稳定的 `selected_slice_cadence_trace_runtime_window_wp17c` reason。 |
| `WP17-D Fidelity Provider Runtime` | pass | `src/runtime/facade/runtime_facade.h`、`src/runtime/facade/runtime_facade.cpp`、`src/interfaces/python/bindings_runtime.cpp`、`tests/runtime/facade/test_runtime_facade.py` 与 `tests/test_gpu_runtime_bindings.py` 暴露 `admit_fidelity_request()`，接受 reference CPU exact evaluation，并拒绝 resident/exact-GPU/shadow requests。 |
| `WP17-E Capability Spawn Runtime Promotion` | pass | `src/models/core/default_unit_factory.h`、`tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py`、`tests/runtime/bindings/test_typed_platform_spawn_bindings.py`、`tests/runtime/engagement/test_air_launch_adapter.py` 与 `tests/runtime/naval/test_naval_ship_database.py` 在保留 type-name 兼容的同时，让 maintained materialization 经过 resolved platform spawn-plan evidence。 |
| `WP17-F Counterfactual Runtime Slice And Closure` | pass | `src/runtime/facade/runtime_facade_types.h`、`src/runtime/facade/runtime_facade.h`、`src/runtime/facade/runtime_facade.cpp`、`src/interfaces/python/bindings_runtime.cpp` 与 `tests/runtime/facade/test_runtime_facade.py` 添加 snapshot/branch/compare DTOs，并证明 explicit setup、selected-entity causal deltas、raw-mutation rejection 与收窄的 replay/fidelity evidence。 |

## 3. 验证命令

WP17 merge set 已报告通过的聚焦实现验证：

```bash
git diff --check
cmake --build build-workshop --target ef_py -j4
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or replay or fidelity or provider"
python -m pytest -q tests/architecture/causal_runtime/test_replay_envelope_contracts.py tests/architecture/causal_runtime/test_worldline_branch_metadata.py tests/architecture/causal_runtime/test_counterfactual_admission.py
python -m pytest -q tests/architecture/runtime_facade tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "cadence or hold or barrier or clock or window"
python -m pytest -q tests/world_batch/test_single_world_batch_runtime.py -k "runtime_window_evidence or cadence_reason or single"
python -m pytest -q tests/test_gpu_runtime_bindings.py -k "capabilities or fidelity or provider"
python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "spawn or world_setup"
python -m pytest -q tests/runtime/engagement/test_air_launch_adapter.py -k accepted_legacy_fire_missile_outcome_fits_launch_request_and_event_shape
python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "ddg or spawn"
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or shadow_compare or compatibility_view"
```

本 review 之前记录的观察结果：

- `git diff --check`：通过。
- `cmake --build build-workshop --target ef_py -j4`：通过。
- Runtime facade counterfactual/fidelity/provider batch：`6 passed`。
- WP15 replay/worldline/counterfactual architecture batch：`18 passed`。
- WP17-B/C/D/E 聚焦回归批次已按任务 handoff 记录通过。

补充 review package 与 index sync 后，已运行最终 closure validation：

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP17
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or replay or fidelity or provider"
python -m pytest -q tests/architecture/causal_runtime/test_replay_envelope_contracts.py tests/architecture/causal_runtime/test_worldline_branch_metadata.py tests/architecture/causal_runtime/test_counterfactual_admission.py
```

观察结果：

- `git diff --check`：通过。
- WP17 closure audit：通过，无 issue。
- Runtime facade counterfactual/fidelity/provider batch：`6 passed, 12
  deselected`。
- WP15 replay/worldline/counterfactual architecture batch：`18 passed`。

## 4. Runtime Surface 摘要

- `RuntimeFacade::admit_fidelity_request()` 是已验收 reference CPU fidelity slice
  的 facade-owned admission point。
- `RuntimeFacade::snapshot_counterfactual_entity()` 与
  `RuntimeFacade::run_counterfactual_branch()` 只针对 explicit setup 与
  selected-entity branch/compare 行为验收。
- `RuntimeCounterfactualSnapshot`、`RuntimeCounterfactualBranchRequest`、
  `RuntimeCounterfactualBranchResult` 与 `RuntimeWorldlineComparison` 是通过
  Python bindings 暴露的 additive DTO surfaces。
- `ActionHoldPolicy` cadence semantics 已被 selected runtime window slice 消费，
  hold、interpolation、expiry、skip 与 barrier evidence 对测试可见。
- `DefaultUnitFactory::spawn()` 现在会在内部消费 resolved platform spawn plans，
  而 `spawn_unit(type_name)` 仍然是兼容契约。
- `WorldBatchRuntime`、`batch_runtime` 与 `RuntimeFacade.runtime()` 仍然是
  compatibility surfaces，不是已删除 API，也不是新晋级的 frontend contract。

## 5. Residuals 与下一步

有意保留的 residuals：

- global scheduler rewrite 与 independent wall-clock domain merge success；
- exact GPU、resident-state、shadow、learned 或 adaptive multi-fidelity 晋级；
- public `spawn_platform` setup schema 与大范围 scenario schema migration；
- arbitrary live-world reflection/clone、full snapshot/restore、任意深度 worldline
  trees 与 full counterfactual experiment orchestration；
- 在 replacement evidence 和 caller migration 完成之前删除保留的 compatibility APIs。

WP17 的 accepted 增量关闭了 Stage 3 selected-slice runtime-materialization lane。
后续工作应从上述 residuals 出发，而不是把 WP17 重新解释为已经完成了 global runtime
rewrite。
