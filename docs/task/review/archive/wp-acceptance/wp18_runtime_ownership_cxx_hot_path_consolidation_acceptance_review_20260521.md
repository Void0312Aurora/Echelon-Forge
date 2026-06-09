# WP18 Runtime Ownership And C++ Hot Path Consolidation Acceptance Review

Status: `2026-05-21` accepted / bounded ownership and hot-path consolidation mergeable.

Language:

- English canonical:
  `wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.md`
- Chinese companion:
  [wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.zh.md](wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.zh.md)

Inputs:

- [WP18 Runtime Ownership And C++ Hot Path Consolidation](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.md)
- [WP18-A Ownership Fact Ledger And Hot-Path Map](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)
- [WP18-B Execution Episode Ownership Sink](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_execution_episode_ownership_sink_cluster_20260521.md)
- [WP18-C ScenarioLoader Adapter Split](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_scenario_loader_adapter_split_cluster_20260521.md)
- [WP18-D Facade Contract Hardening](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_facade_contract_hardening_cluster_20260521.md)
- [WP18-E C++ Hot Path Migration Matrix](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_cxx_hot_path_migration_matrix_cluster_20260521.md)
- [WP18-F Integration And Handoff](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_integration_handoff_cluster_20260521.md)
- [WP18 dispatch queue](../simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_subagent_dispatch_queue_20260521.md)
- [WP17 acceptance review](wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.md)

## 1. Verdict

WP18 is accepted as a bounded runtime-ownership and C++ hot-path consolidation
increment after WP17. It moved one maintained execution-episode state/export
slice behind facade/runtime-owned batch results, classified the
`ScenarioLoader` state shell as an ownership contract, tightened facade-layer
raw-runtime guardrails, and moved the default compiled reward-breakdown
metadata path toward C++ authority.

This acceptance does not claim a broad runtime rewrite. The following remain
out of scope for WP18:

- deleting `WorldBatchRuntime`, `batch_runtime`, or `RuntimeFacade.runtime()`;
- full `ScenarioLoader` behavioral split or public scenario-schema rewrite;
- request-build / consume loop migration;
- route/approach/post-transition metadata handoff;
- CUDA/resident-state mainline alignment, which belongs to WP19;
- public capability platform composition, which belongs to WP20;
- full counterfactual/experiment runtime, which belongs to WP21.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP18-A Ownership Fact Ledger And Hot-Path Map` | pass | The fact ledger selected the execution-episode ownership sink as the first safe implementation slice and explicitly rejected a broad `ScenarioLoader` or VecEnv rewrite as the first move. |
| `WP18-B Execution Episode Ownership Sink` | pass | `ExecutionBatchStepResult.execution_episode_states` is exposed through the facade/runtime batch result and consumed by `WorldBatchVecEnv` before legacy `step_result.controller_state`; compatibility payloads remain. |
| `WP18-C ScenarioLoader Adapter Split` | pass | `ScenarioLoaderStateShell` fields now have immutable responsibility classifications, import-time validation, and an architecture-level classification contract. Public loader behavior is preserved. |
| `WP18-D Facade Contract Hardening` | pass | Architecture guards prevent new maintained `.batch_runtime.` and `RuntimeFacade.runtime()` consumers outside named compatibility/diagnostic allowlists, and vec-env tests prove facade-owned batch fields win over poisoned legacy payloads. |
| `WP18-E C++ Hot Path Migration Matrix` | pass | The first reward/termination metadata slice is complete: default compiled path prefers C++ reward-breakdown metadata, the migration matrix records residuals, and the batch-prepare `-k` selector now maps to real coverage. |
| `WP18-F Integration And Handoff` | pass | Worker returns, validation results, residual routing, bilingual docs, README/review index sync, and this acceptance review are recorded. |

## 3. Validation Commands

Main-thread validation after implementation and guard waves:

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

Observed outcomes recorded before this review:

- `cmake --build build-workshop --target ef_core ef_py -j4`: passed.
- `git diff --check`: passed.
- WP18 summary audit: passed with all required Chinese companions present while
  the acceptance review was intentionally absent during active work.
- Runtime facade layering: `18 passed`.
- WP16 legacy path gates: `6 passed`.
- Execution episode state: `5 passed`.
- Scenario-loader state/runtime/reward/termination slice: `11 passed, 8
  subtests passed`.
- Runtime facade execution/episode/batch slice: `4 passed, 14 deselected`.
- Facade step evidence gate: `1 passed`.
- World-batch vec-env focused slice: `11 passed, 27 deselected`.
- World-batch runtime execution-episode slice: `3 passed, 18 deselected`.
- Runtime DTO surface: `17 passed`.
- Execution step runtime: `14 passed`.
- Scenario-loader C++ reward metadata slice: `3 passed, 8 deselected, 4
  subtests passed`.
- Batch prepare full file: `2 passed`.
- Batch prepare narrow reward/termination/breakdown anchor: `1 passed, 1
  deselected`.

Final closure validation was run after this review and index sync:

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_layering.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view or facade"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"
```

Observed outcome:

- `git diff --check`: passed.
- WP18 closure audit: passed with no issues.
- Runtime facade layering: `18 passed`.
- World-batch vec-env focused slice: `11 passed, 27 deselected`.
- Batch prepare narrow reward/termination/breakdown anchor: `1 passed, 1
  deselected`.

## 4. Runtime Surface Summary

- `ExecutionBatchStepResult.execution_episode_states` is now a maintained
  facade/runtime-owned post-step episode-state export.
- `WorldBatchVecEnv` exposes facade-shaped execution-episode readiness and state
  export helpers and consumes facade-owned batch fields before legacy payloads.
- `ScenarioLoaderStateShell` has explicit responsibility buckets:
  scenario-content adapter state, runtime mirror only, transitional behavior
  mirror, and blocked owner candidates.
- `RuntimeFacade.runtime()`, `batch_runtime`, and `WorldBatchRuntime` remain
  compatibility surfaces with guardrails, not deleted APIs.
- `ef_py.build_episode_reward_breakdown_json` exposes C++ reward-breakdown
  metadata to the maintained compiled path.

## 5. Residuals And Next Plan

Residuals intentionally carried forward:

- route/approach/post-transition metadata handoff is the next safe migration
  candidate, but it needs a narrow metadata-preference preflight test before
  runtime edits;
- request build/consume loop migration remains deferred because it is high
  value but high ownership risk;
- Python reward metadata fallback remains for compatibility while the maintained
  default path prefers C++ metadata;
- compatibility APIs remain until replacement evidence and caller migration are
  complete;
- CUDA/resident-state alignment moves to WP19 rather than being reopened inside
  WP18.

WP18 is therefore closed as a bounded consolidation increment. Later work
should start from the residuals above instead of interpreting WP18 as a completed
global runtime rewrite.
