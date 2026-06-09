# WP18 Runtime Ownership And C++ Hot Path Consolidation 验收审查

状态：`2026-05-21` accepted / bounded ownership and hot-path consolidation mergeable。

语言版本：

- 英文主文：[wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.md](wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.md)
- 中文辅文：`wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.zh.md`

输入：

- [WP18 Runtime Ownership And C++ Hot Path Consolidation](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)
- [WP18-A Ownership Fact Ledger And Hot-Path Map](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)
- [WP18-B Execution Episode Ownership Sink](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_execution_episode_ownership_sink_cluster_20260521.zh.md)
- [WP18-C ScenarioLoader Adapter Split](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_scenario_loader_adapter_split_cluster_20260521.zh.md)
- [WP18-D Facade Contract Hardening](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_facade_contract_hardening_cluster_20260521.zh.md)
- [WP18-E C++ Hot Path Migration Matrix](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_cxx_hot_path_migration_matrix_cluster_20260521.zh.md)
- [WP18-F Integration And Handoff](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_integration_handoff_cluster_20260521.zh.md)
- [WP18 dispatch queue](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_subagent_dispatch_queue_20260521.zh.md)
- [WP17 验收审查](wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.zh.md)

## 1. 结论

WP18 已作为 WP17 之后有边界的 runtime ownership 与 C++ hot-path
consolidation 增量验收。它把一条 maintained execution-episode state/export
切片移到 facade/runtime-owned batch results 后面，把 `ScenarioLoader`
state shell 分类为 ownership contract，收紧 facade-layer raw-runtime
guardrails，并让默认 compiled reward-breakdown metadata path 转向 C++ 权威。

本验收不声明 broad runtime rewrite。以下内容不属于 WP18 已完成范围：

- 删除 `WorldBatchRuntime`、`batch_runtime` 或 `RuntimeFacade.runtime()`；
- 完整 `ScenarioLoader` behavioral split 或 public scenario-schema rewrite；
- request-build / consume loop migration；
- route/approach/post-transition metadata handoff；
- CUDA/resident-state mainline alignment，该项属于 WP19；
- public capability platform composition，该项属于 WP20；
- full counterfactual/experiment runtime，该项属于 WP21。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP18-A Ownership Fact Ledger And Hot-Path Map` | pass | Fact ledger 选择 execution-episode ownership sink 作为第一条安全实现切片，并明确拒绝把 broad `ScenarioLoader` 或 VecEnv rewrite 作为第一步。 |
| `WP18-B Execution Episode Ownership Sink` | pass | `ExecutionBatchStepResult.execution_episode_states` 已通过 facade/runtime batch result 暴露，并由 `WorldBatchVecEnv` 在 legacy `step_result.controller_state` 之前消费；compatibility payloads 保留。 |
| `WP18-C ScenarioLoader Adapter Split` | pass | `ScenarioLoaderStateShell` 字段已有不可变 responsibility classifications、import-time validation 与 architecture-level classification contract。Public loader behavior 保持兼容。 |
| `WP18-D Facade Contract Hardening` | pass | Architecture guards 阻止新的 maintained `.batch_runtime.` 与 `RuntimeFacade.runtime()` consumers 落到命名 compatibility/diagnostic allowlists 之外；vec-env 测试证明 facade-owned batch fields 会优先于被污染的 legacy payloads。 |
| `WP18-E C++ Hot Path Migration Matrix` | pass | 第一条 reward/termination metadata slice 已完成：默认 compiled path 优先使用 C++ reward-breakdown metadata，migration matrix 记录 residuals，batch-prepare `-k` selector 已映射到真实覆盖。 |
| `WP18-F Integration And Handoff` | pass | Worker returns、validation results、residual routing、双语文档、README/review index sync 与本验收审查已记录。 |

## 3. 验证命令

实现与 guard 波次后的主线程验证：

```bash
cmake --build build-workshop --target ef_core ef_py -j4
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18 --summary
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_layering.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_state.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "state or runtime or reward or termination"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "execution or episode or batch"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_facade_step_evidence_gates.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view or facade"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "execution_episode"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_step_runtime.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "cxx_reward_metadata or selected_paths_match_legacy_runtime or flight_shaping_backends_match_legacy_runtime"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"
```

本 review 之前记录的观察结果：

- `cmake --build build-workshop --target ef_core ef_py -j4`：通过。
- `git diff --check`：通过。
- WP18 summary audit：通过；active work 阶段 acceptance review 按规则保持缺席，所需中文辅文齐全。
- Runtime facade layering：`18 passed`。
- WP16 legacy path gates：`6 passed`。
- Execution episode state：`5 passed`。
- Scenario-loader state/runtime/reward/termination slice：`11 passed, 8 subtests passed`。
- Runtime facade execution/episode/batch slice：`4 passed, 14 deselected`。
- Facade step evidence gate：`1 passed`。
- World-batch vec-env 聚焦切片：`11 passed, 27 deselected`。
- World-batch runtime execution-episode slice：`3 passed, 18 deselected`。
- Runtime DTO surface：`17 passed`。
- Execution step runtime：`14 passed`。
- Scenario-loader C++ reward metadata slice：`3 passed, 8 deselected, 4 subtests passed`。
- Batch prepare full file：`2 passed`。
- Batch prepare narrow reward/termination/breakdown anchor：`1 passed, 1 deselected`。

补充本 review 与 index sync 后，已运行最终 closure validation：

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_layering.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view or facade"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"
```

观察结果：

- `git diff --check`：通过。
- WP18 closure audit：通过，无 issue。
- Runtime facade layering：`18 passed`。
- World-batch vec-env 聚焦切片：`11 passed, 27 deselected`。
- Batch prepare narrow reward/termination/breakdown anchor：`1 passed, 1 deselected`。

## 4. Runtime Surface 摘要

- `ExecutionBatchStepResult.execution_episode_states` 现在是 maintained
  facade/runtime-owned post-step episode-state export。
- `WorldBatchVecEnv` 暴露 facade-shaped execution-episode readiness 与 state
  export helpers，并在 legacy payloads 之前消费 facade-owned batch fields。
- `ScenarioLoaderStateShell` 具有显式 responsibility buckets：
  scenario-content adapter state、runtime mirror only、transitional behavior
  mirror 与 blocked owner candidates。
- `RuntimeFacade.runtime()`、`batch_runtime` 与 `WorldBatchRuntime` 仍是带护栏的
  compatibility surfaces，不是被删除的 API。
- `ef_py.build_episode_reward_breakdown_json` 把 C++ reward-breakdown metadata
  暴露给 maintained compiled path。

## 5. Residuals 与下一步

有意保留的 residuals：

- route/approach/post-transition metadata handoff 是下一条安全迁移候选，但在
  runtime edits 之前需要一条窄 metadata-preference preflight test；
- request build/consume loop migration 继续 deferred，因为价值高但 ownership 风险高；
- Python reward metadata fallback 为兼容性保留，同时 maintained default path 优先 C++ metadata；
- compatibility APIs 会保留到 replacement evidence 与 caller migration 完成；
- CUDA/resident-state alignment 进入 WP19，而不是在 WP18 内重开。

因此，WP18 作为有边界的 consolidation 增量关闭。后续工作应从上述 residuals
出发，而不是把 WP18 解释为已经完成 global runtime rewrite。
