# MLF-6 Structural Failure — Dispatch Queue

Status: `2026-06-18` v10 queue closed for implementation. P1/P2, P3, P4, P5, P6 focused validation, P7 broad regression, and near-field continuous-rod / cumulative wing-loss calibration are complete. Archive movement remains withheld until explicit user instruction.

Parent task clusters: [missile_lethality_structural_failure_task_clusters_20260617.md](missile_lethality_structural_failure_task_clusters_20260617.md)

## Queue

| Packet | Cluster | Suggested owner | Write set | Goal | Status |
| --- | --- | --- | --- | --- | --- |
| `MLF-6B-X1` | `MLF-6B Component Inventory` | main thread | docs inventory packet only | Inventory every `ComponentDamageState` field, every F-16C component name, and every `structural_integrity` write site MLF-6 must NOT touch. | complete |
| `MLF-6C-X1` | `MLF-6C Break-Mode Mapping` | main thread | design doc only | Classify every F-16C component into structural groups; define integrity thresholds per group. | complete |
| `MLF-6D-W1` | `MLF-6D State Machine` | main thread | `src/components/combat/structural_failure.h`, `src/systems/combat/structural_failure_system.h`, `src/core/engine/simulation_kernel_systems.cpp`, `src/tests/test_structural_failure_system.cpp`, CMakeLists.txt | Implement `StructuralFailureUpdate` ECS system: read `ComponentDamageState`, track `breakup_state` and `break_mode`. No event writing. | complete |
| `MLF-6E-W1` | `MLF-6E Event Writer` | implementation worker (same as 6D preferred) | `src/systems/combat/structural_failure_system.h`, `src/core/interfaces/engagement_event_recorder.h`, `src/core/engine/simulation_kernel_engagement_event_store.*`, `src/runtime/facade/runtime_facade.cpp`, `src/tests/test_structural_failure_system.cpp` | Write `StructuralBreakupEvent` rows on state transitions or new break modes. | complete |
| `MLF-6F-W1` | `MLF-6F Diagnostics Export` | diagnostics worker | `tools/diagnostics/structural_breakup_export.py`, `tests/tools/test_structural_breakup_export.py` | Thin Python probe on existing `StructuralBreakupEvent` bindings (`bindings_runtime.cpp:449-457`, `bindings_core.cpp`). No new binding surface. | complete |
| `MLF-6G-W1` | `MLF-6G Focused Tests` | main thread or test worker | `src/tests/test_structural_failure_system.cpp`, `CMakeLists.txt` | Focused C++ tests for every break mode. | complete |
| `MLF-6H-C1` | `MLF-6H Zero-Regression Smoke` | main thread | test execution and obsolete-oracle updates | Run full air_combat and world_batch suites; confirm zero regressions. Current lane: `447 passed`. | complete |
| `MLF-6I-C1` | `MLF-6I Acceptance And Archive` | main thread | docs/index only; no archive movement | Summarize evidence, update status, sync parent READMEs; keep archive movement out until explicit instruction. | complete / no archive |

## Dispatch Notes

- `MLF-6B-X1` is read-only. Must return before any implementation dispatch.
- `MLF-6C-X1` is design doc only. Must be approved before 6D starts.
- `MLF-6D-W1` and `MLF-6E-W1` are preferably the same worker: the event writer
  is a thin extension of the state machine's internal tracking.
- `MLF-6F-W1` and `MLF-6G-W1` can run in parallel after 6E completes (different
  write surfaces: Python tools vs C++ tests).
- `MLF-6H-C1` was executed after 6E + 6F + 6G and now has a clean full-suite
  pass for the P7 lane.
- `MLF-6I-C1` keeps no-archive status until explicit user instruction.
- Each cluster has a round cap in the task cluster table. If exceeded, stop and
  re-scope.
- Follow [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md).
- This queue only covers MLF-6. Do not enter MLF-7 (aerodynamics bridging,
  loss-state integration), MLF-8 (debris/wreck lifecycle), or MLF-9 (Pk).

## MLF-6D/6E Worker-Specific Requirements

In addition to the standard worker packet checklist, the 6D/6E worker must:

- Confirm every `ComponentDamageState` field read is documented with rationale.
- Confirm no `structural_integrity`, `FlightModel`, `Propulsion`, `Health`, or
  `PlatformDamageState` field is modified.
- Confirm `StructuralFailureUpdate` registers after `AircraftDamageStateUpdate`.
- Confirm state machine is irreversible and cumulative per D4.
- Confirm `detached_part_ref` is a string label, not an entity reference per D3.
- Confirm `airframe_breakup` is `true` only when `breakup_state == full_breakup`.

## Worker Packet Checklist

- status
- touched files
- commands/outcomes
- remaining paths
- behavior risks
- integration notes
