# MLF-6 Structural Failure — Dispatch Queue

Status: `2026-06-17` v2 planning queue, corrected per P0 self-review. No packets
dispatched yet.

Parent task clusters: [missile_lethality_structural_failure_task_clusters_20260617.md](missile_lethality_structural_failure_task_clusters_20260617.md)

## Queue

| Packet | Cluster | Suggested owner | Write set | Goal | Status |
| --- | --- | --- | --- | --- | --- |
| `MLF-6B-X1` | `MLF-6B Component Inventory` | read-only worker | docs inventory packet only | Inventory every `ComponentDamageState` field, every F-16C component name, and every `structural_integrity` write site MLF-6 must NOT touch. | planned |
| `MLF-6C-X1` | `MLF-6C Break-Mode Mapping` | main thread | design doc only | Classify every F-16C component into structural groups; define integrity thresholds per group. | planned |
| `MLF-6D-W1` | `MLF-6D State Machine` | implementation worker | `src/systems/combat/structural_failure_system.h`, `src/systems/combat/structural_failure_system.cpp`, CMakeLists.txt | Implement `StructuralFailureUpdate` ECS system: read `ComponentDamageState`, track `breakup_state` and `break_mode`. No event writing. | planned |
| `MLF-6E-W1` | `MLF-6E Event Writer` | implementation worker (same as 6D preferred) | `src/systems/combat/structural_failure_system.*`, `src/core/engine/simulation_kernel_engagement_event_store.*` | Write `StructuralBreakupEvent` rows on state transitions or new break modes. | planned |
| `MLF-6F-W1` | `MLF-6F Diagnostics Export` | diagnostics worker | `tools/diagnostics/structural_breakup_export.py` | Thin Python probe on existing `StructuralBreakupEvent` bindings (`bindings_runtime.cpp:449-457`, `bindings_core.cpp`). No new binding surface. | planned |
| `MLF-6G-W1` | `MLF-6G Focused Tests` | main thread or test worker | `tests/runtime/air_combat/test_structural_failure_break_modes.cpp`, `tests/runtime/air_combat/test_structural_failure_regression.cpp` | Focused C++ tests for every break mode. | planned |
| `MLF-6H-C1` | `MLF-6H Zero-Regression Smoke` | main thread | test execution only | Run full air_combat and world_batch suites; confirm zero regressions. | planned |
| `MLF-6I-C1` | `MLF-6I Acceptance And Archive` | main thread | docs/index/archive | Summarize evidence, update status, sync parent READMEs. | planned |

## Dispatch Notes

- `MLF-6B-X1` is read-only. Must return before any implementation dispatch.
- `MLF-6C-X1` is design doc only. Must be approved before 6D starts.
- `MLF-6D-W1` and `MLF-6E-W1` are preferably the same worker: the event writer
  is a thin extension of the state machine's internal tracking.
- `MLF-6F-W1` and `MLF-6G-W1` can run in parallel after 6E completes (different
  write surfaces: Python tools vs C++ tests).
- `MLF-6H-C1` is serial after 6E + 6F + 6G.
- `MLF-6I-C1` is last, serial.
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
