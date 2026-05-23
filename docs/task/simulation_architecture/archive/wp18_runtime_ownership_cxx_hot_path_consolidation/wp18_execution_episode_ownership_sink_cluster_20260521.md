# WP18-B Execution Episode Ownership Sink

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp18_execution_episode_ownership_sink_cluster_20260521.md`
- Chinese companion:
  [wp18_execution_episode_ownership_sink_cluster_20260521.zh.md](wp18_execution_episode_ownership_sink_cluster_20260521.zh.md)

Inputs:

- [WP18 main plan](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.md)
- [WP18-A ownership fact ledger](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)
- [WP17 facade business migration](../wp17_stage3_runtime_materialization_cleanup/wp17_facade_business_migration_cleanup_cluster_20260521.md)

## Purpose

Move one maintained execution-episode state/export/consume slice behind
C++/facade-owned results so Python wrappers stop acting as authoritative runtime
owners for that slice.

## Scope

In scope:

- one narrow execution-episode ownership slice selected from WP18-A;
- facade or adapter methods that expose C++/runtime-owned state/results;
- focused tests proving the selected maintained caller no longer requires raw
  compatibility world reads;
- compatibility preservation for existing batch/runtime tests.

Out of scope:

- full VecEnv rewrite;
- deleting `WorldBatchRuntime`, `batch_runtime`, or `RuntimeFacade.runtime()`;
- splitting `ScenarioLoader` structure; WP18-C owns that.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `B1` | Select first ownership slice | Chosen slice has source/test anchors, limited write scope, and direct business value. |
| `B2` | Facade/runtime-owned export | Maintained caller can receive state/result through facade-shaped runtime evidence. |
| `B3` | Python mirror demotion | Python path is a mirror or consumer for the slice, not the authoritative owner. |
| `B4` | Compatibility proof | Existing compatibility tests still pass and direct raw reads remain explicitly classified. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "execution or episode or batch"
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view"
python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "execution_episode"
```

## Handoff

Return selected slice, touched files, new facade/runtime evidence, compatibility
paths retained, commands run, blockers, and residual ownership still in Python.
