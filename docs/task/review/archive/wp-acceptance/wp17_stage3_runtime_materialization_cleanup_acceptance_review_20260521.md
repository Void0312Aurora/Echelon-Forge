# WP17 Stage 3 Runtime Materialization And Cleanup Acceptance Review

Status: `2026-05-21` accepted / selected-slice implementation mergeable.

Language:

- English canonical:
  `wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.md`
- Chinese companion:
  [wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.zh.md](wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.zh.md)

Inputs:

- [WP17 Stage 3 Runtime Materialization And Cleanup](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [WP17-A Fact Ledger And Boundary Freeze](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_fact_ledger_and_boundary_freeze_cluster_20260521.md)
- [WP17-B Facade Business Migration And Compatibility Cleanup](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_facade_business_migration_cleanup_cluster_20260521.md)
- [WP17-C Multi-Rate Runtime Example](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_multirate_runtime_example_cluster_20260521.md)
- [WP17-D Fidelity Provider Runtime](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_fidelity_provider_runtime_cluster_20260521.md)
- [WP17-E Capability Spawn Runtime Promotion](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.md)
- [WP17-F Counterfactual Runtime Slice And Closure](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_counterfactual_runtime_closure_cluster_20260521.md)
- [WP17 dispatch queue](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/wp17_subagent_dispatch_queue_20260521.md)
- [WP16 acceptance review](wp16_runtime_spine_consolidation_acceptance_review_20260521.md)

## 1. Verdict

WP17 is accepted as the final Stage 3 selected-slice runtime-materialization and
cleanup increment. It turns the remaining WP16 handoff surfaces into bounded
runtime behavior for facade-shaped batch reads, selected cadence evidence,
reference CPU fidelity admission, capability-gated spawn materialization, and
one explicit-setup selected-entity counterfactual branch/compare path.

This is intentionally not a global rewrite:

- no global scheduler rewrite;
- no exact GPU, resident-state, shadow, or adaptive multi-fidelity promotion;
- no mandatory public `spawn_platform` schema;
- no deletion of `WorldBatchRuntime`, `batch_runtime`, or
  `RuntimeFacade.runtime()`;
- no arbitrary live-world clone, full snapshot/restore, arbitrary-depth
  worldline tree, or full counterfactual experiment orchestration.

The accepted runtime boundary is the selected slice recorded by WP17: maintained
callers can use facade-shaped adapter/env methods for execution-episode
readiness and state export, the runtime-window selected slice emits cadence
trace evidence, reference CPU exact evaluation can be admitted through the
facade while unsupported providers fail closed, the default unit factory
consumes resolved platform spawn plans internally, and
`RuntimeFacade::run_counterfactual_branch()` can compare parent and branch worlds
created from an explicit setup for one selected entity.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP17-A Fact Ledger And Boundary Freeze` | pass | The WP17 main plan reconciles current code facts for runtime capabilities, provider dispatch, capability composition, counterfactual runtime, multi-rate scheduling, and training/batch business paths before implementation claims are made. |
| `WP17-B Facade Business Migration And Compatibility Cleanup` | pass | `python/rl/runtime/world_batch/adapter.py`, `python/rl/runtime/world_batch_vec_env.py`, and `tests/architecture/runtime_facade/test_layering.py` expose and guard facade-shaped execution-episode ready/state reads while retaining `batch_runtime` as a compatibility view. |
| `WP17-C Multi-Rate Runtime Example` | pass | `src/runtime/facade/runtime_window_coordinator.h`, `src/runtime/contracts/stage_node_manifest_registry.h`, `tests/runtime/facade/test_runtime_facade_window_loop_injection.py`, and `tests/world_batch/test_single_world_batch_runtime.py` prove the selected cadence slice with hold/expiry/barrier evidence and the stable `selected_slice_cadence_trace_runtime_window_wp17c` reason. |
| `WP17-D Fidelity Provider Runtime` | pass | `src/runtime/facade/runtime_facade.h`, `src/runtime/facade/runtime_facade.cpp`, `src/interfaces/python/bindings_runtime.cpp`, `tests/runtime/facade/test_runtime_facade.py`, and `tests/test_gpu_runtime_bindings.py` expose `admit_fidelity_request()`, accept reference CPU exact evaluation, and reject resident/exact-GPU/shadow requests. |
| `WP17-E Capability Spawn Runtime Promotion` | pass | `src/models/core/default_unit_factory.h`, `tests/architecture/platform_spawn/test_resolved_spawn_plan_evidence.py`, `tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py`, `tests/runtime/engagement/test_air_launch_adapter.py`, and `tests/runtime/naval/test_naval_ship_database.py` preserve type-name compatibility while routing maintained materialization through resolved platform spawn-plan evidence. |
| `WP17-F Counterfactual Runtime Slice And Closure` | pass | `src/runtime/facade/runtime_facade_types.h`, `src/runtime/facade/runtime_facade.h`, `src/runtime/facade/runtime_facade.cpp`, `src/interfaces/python/bindings_runtime.cpp`, and `tests/runtime/facade/test_runtime_facade.py` add snapshot/branch/compare DTOs and prove explicit setup, selected-entity causal deltas, raw-mutation rejection, and narrow replay/fidelity evidence. |

## 3. Validation Commands

Focused implementation validation reported for the WP17 merge set:

```bash
git diff --check
cmake --build build-workshop --target ef_py -j4
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or replay or fidelity or provider"
python -m pytest -q tests/architecture/causal_runtime/test_replay_envelope_contracts.py tests/architecture/causal_runtime/test_worldline_branch_metadata.py tests/architecture/causal_runtime/test_counterfactual_admission.py
python -m pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "cadence or hold or barrier or clock or window"
python -m pytest -q tests/world_batch/test_single_world_batch_runtime.py -k "runtime_window_evidence or cadence_reason or single"
python -m pytest -q tests/test_gpu_runtime_bindings.py -k "capabilities or fidelity or provider"
python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "spawn or world_setup"
python -m pytest -q tests/runtime/engagement/test_air_launch_adapter.py -k accepted_legacy_fire_missile_outcome_fits_launch_request_and_event_shape
python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "ddg or spawn"
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or shadow_compare or compatibility_view"
```

Observed outcomes recorded before this review:

- `git diff --check`: passed.
- `cmake --build build-workshop --target ef_py -j4`: passed.
- Runtime facade counterfactual/fidelity/provider batch: `6 passed`.
- WP15 replay/worldline/counterfactual architecture batch: `18 passed`.
- Focused WP17-B/C/D/E regression batches passed as reported in the task
  handoff records.

Final closure validation was run after the review package and index sync were
added:

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP17
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or replay or fidelity or provider"
python -m pytest -q tests/architecture/causal_runtime/test_replay_envelope_contracts.py tests/architecture/causal_runtime/test_worldline_branch_metadata.py tests/architecture/causal_runtime/test_counterfactual_admission.py
```

Observed outcome:

- `git diff --check`: passed.
- WP17 closure audit: passed with no issues.
- Runtime facade counterfactual/fidelity/provider batch: `6 passed, 12
  deselected`.
- WP15 replay/worldline/counterfactual architecture batch: `18 passed`.

## 4. Runtime Surface Summary

- `RuntimeFacade::admit_fidelity_request()` is the maintained facade-owned
  admission point for the accepted reference CPU fidelity slice.
- `RuntimeFacade::snapshot_counterfactual_entity()` and
  `RuntimeFacade::run_counterfactual_branch()` are accepted only for explicit
  setup and selected-entity branch/compare behavior.
- `RuntimeCounterfactualSnapshot`, `RuntimeCounterfactualBranchRequest`,
  `RuntimeCounterfactualBranchResult`, and `RuntimeWorldlineComparison` are
  additive DTO surfaces exposed through Python bindings.
- `ActionHoldPolicy` cadence semantics are consumed by the selected runtime
  window slice, with hold, interpolation, expiry, skip, and barrier evidence
  visible to tests.
- `DefaultUnitFactory::spawn()` now consumes resolved platform spawn plans
  internally, while `spawn_unit(type_name)` remains the compatibility contract.
- `WorldBatchRuntime`, `batch_runtime`, and `RuntimeFacade.runtime()` remain
  compatibility surfaces, not removed or newly promoted frontend contracts.

## 5. Residuals And Next Plan

Residuals intentionally carried forward:

- global scheduler rewrite and independent wall-clock domain merge success;
- exact GPU, resident-state, shadow, learned, or adaptive multi-fidelity
  promotion;
- public `spawn_platform` setup schema and broad scenario schema migration;
- arbitrary live-world reflection/clone, full snapshot/restore, arbitrary-depth
  worldline trees, and full counterfactual experiment orchestration;
- deletion of retained compatibility APIs before replacement evidence and
  caller migration are complete.

The accepted WP17 increment closes the Stage 3 selected-slice
runtime-materialization lane. Any future work should start from the residuals
above rather than reopening WP17 as if the global runtime rewrite had already
been completed.
