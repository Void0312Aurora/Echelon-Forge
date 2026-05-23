# WP16-C Facade And Batch Path Spine Migration

Status: `2026-05-21` complete / facade and batch migration accepted.

Language:

- English canonical: `wp16_facade_batch_spine_migration_cluster_20260521.md`
- Chinese companion:
  [wp16_facade_batch_spine_migration_cluster_20260521.zh.md](wp16_facade_batch_spine_migration_cluster_20260521.zh.md)

Inputs:

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.md)
- [WP7.5 training path facade bridge](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md)
- [WP15 counterfactual experiment generation](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md)

## 1. Purpose

`WP16-C` moves maintained consumers toward the runtime spine. The key target is
not API churn; it is making facade, world-batch, training, scenario, and
experiment consumers receive the same barrier/event/provenance/cadence evidence
instead of reaching through raw runtime or private state.

## 2. Scope

In scope:

- migrate selected maintained facade or batch calls to the runtime-window spine;
- preserve compatibility wrappers where caller migration is not safe yet;
- ensure observation/facade exports retain provenance, authority, capability,
  backend/fidelity, replay, and cadence evidence required by their consumers;
- update Python adapter or binding-facing tests when public surfaces are touched;
- record fallback paths that must remain compatibility-only.

Out of scope:

- deleting raw runtime access globally;
- changing scenario schemas broadly;
- promoting public experiment orchestration;
- implementing clock-domain enforcement owned by WP16-B.

## 3. Deliverables

- A migrated maintained path or wrapper that routes through the runtime-window
  spine.
- Tests proving the migrated consumer receives barrier/event/provenance/cadence
  evidence.
- Compatibility fallback records for callers that cannot migrate in this slice.
- Notes for WP16-D on which legacy paths can be deprecated or retained.

## 4. Gate Rules

| Gate item | Pass condition |
|-----------|----------------|
| Maintained consumer | At least one selected facade/batch/training consumer uses the spine or an explicit wrapper around it. |
| Evidence continuity | Consumer-visible data carries barrier, event, provenance, authority, capability, backend/fidelity, replay, or cadence evidence as applicable. |
| Compatibility | Existing maintained tests continue to pass or fallback behavior is explicitly documented and tested. |
| No raw-state regression | Migrated path does not regain raw runtime or direct ECS ownership. |

## 5. Suggested Validation

```bash
git diff --check
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py
python -m pytest -q tests/world_batch/test_world_batch_runtime.py tests/runtime/execution/test_execution_episode_batch_prepare.py -k "facade or window or evidence or batch"
```

## 6. Handoff Contract

Return:

- touched files;
- migrated consumer paths;
- compatibility fallback paths;
- exact validation commands and outcomes;
- residual raw/bypass access;
- notes for WP16-D and WP16-F.
