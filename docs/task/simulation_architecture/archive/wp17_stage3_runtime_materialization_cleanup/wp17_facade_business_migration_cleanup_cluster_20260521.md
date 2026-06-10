# WP17-B Facade Business Migration And Compatibility Cleanup

Status: `2026-05-21` implemented / focused validation passed.

Inputs:

- [WP17 main plan](stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [WP16 facade/batch migration](../wp16_runtime_spine_consolidation/wp16_facade_batch_spine_migration_cluster_20260521.md)
- [WP7.5 training path facade bridge](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)

## Purpose

Compress old business access without deleting compatibility APIs. The immediate
target is maintained training/batch code and tests that still read runtime state
through `vec_env.batch_runtime` instead of facade-shaped adapter or environment
methods.

## Scope

In scope:

- add or expose facade-shaped `WorldBatchVecEnv` methods for execution episode
  readiness and state export when needed;
- migrate maintained tests and business-facing call sites away from direct
  `batch_runtime` reads;
- keep `batch_runtime` as an explicit compatibility view;
- extend architecture guards so direct `batch_runtime` reads are allowed only
  in named compatibility tests or adapters.

Out of scope:

- removing `WorldBatchRuntime`, `RuntimeFacade.runtime()`, or `batch_runtime`;
- changing scenario schemas;
- scheduler, fidelity, capability, or counterfactual implementation.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `B1` | Facade-shaped env accessors | Maintained env callers can query execution readiness/state without direct `batch_runtime`. |
| `B2` | Business/test migration | Mainline tests use env/adapter facade methods; compatibility test remains explicit. |
| `B3` | Guard tightening | Architecture guard prevents new mainline `batch_runtime.export_execution_episode_states_batch` and `execution_episode_controller_ready` reads. |
| `B4` | Compatibility proof | Existing compatibility view tests still pass and document retained legacy behavior. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_facade
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view"
python -m pytest -q tests/world_batch/test_single_world_batch_runtime.py
```

## Handoff

Return migrated call sites, retained compatibility paths, guard changes,
commands run, and residual legacy accesses.
