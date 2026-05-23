# WP18-C ScenarioLoader Adapter Split

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp18_scenario_loader_adapter_split_cluster_20260521.md`
- Chinese companion:
  [wp18_scenario_loader_adapter_split_cluster_20260521.zh.md](wp18_scenario_loader_adapter_split_cluster_20260521.zh.md)

Inputs:

- [WP18 main plan](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.md)
- [WP18-A ownership fact ledger](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)
- [Simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.md)

## Purpose

Stop treating `ScenarioLoader` as one undifferentiated owner. WP18-C must split
or pre-gate the loader responsibilities so scenario/content adaptation remains
legitimate while maintained runtime state ownership moves toward C++/facade
surfaces.

## Scope

In scope:

- identify `ScenarioLoader` responsibilities that are static scenario/content
  adaptation, frontend helper behavior, runtime state mirror, or maintained
  owner candidate;
- introduce narrow adapter boundaries or tests that enforce those categories;
- migrate one low-risk call site or add guards that block new authoritative
  runtime fields in `ScenarioLoader`.

Out of scope:

- changing C++ runtime reward/termination logic;
- deleting loader APIs used by existing scenarios;
- changing public scenario schemas.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `C1` | Responsibility map | Loader fields/methods are classified by scenario adapter, frontend helper, runtime mirror, or owner candidate. |
| `C2` | Adapter/pre-gate seam | A narrow split or guard exists so new maintained runtime ownership cannot silently land in the loader. |
| `C3` | Compatibility preservation | Existing scenario and world-batch loader tests still pass. |
| `C4` | Handoff to B/E | Runtime-owned fields that should move to B or E are named with candidate tests. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py
python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "scenario_loader or route"
python -m pytest -q tests/runtime/naval/test_naval_screen_scenario.py -k "scenario"
```

## Handoff

Return responsibility map, adapter/guard changes, touched files, commands run,
compatibility risks, and fields that should move to C++/facade ownership later.
