# MLF-7 Secondary Consequence Coupling — Current Status

Status: `2026-06-18` accepted / archived MLF-7 slice complete. P1
inventory, P2 coupling contract, P3 structural consequence bridge, P4
chain-linked event diagnostics, P5 focused C++ validation, P6 broad
Python/runtime smoke, and P7 acceptance are complete.

## Opened Scope

- MLF-7 is now represented as a distinct A2 follow-on subproject:
  [README.md](README.md).
- The phase plan, task clusters, expanded dispatch queue, inventory, contract,
  acceptance draft, and parent archive registration exist.
- Parent navigation will point future agents to this package instead of asking
  them to extend MLF-6.
- Runtime now includes
  [structural_consequence_system.h](../../../../../../src/systems/combat/structural_consequence_system.h),
  registered after `StructuralFailureUpdate`.
- Focused C++ validation has passed for no-breakup, each break mode, multi-axis
  loss state, idempotence, ECS same-tick bridge behavior, and chain-linked
  `platform_consequence` diagnostics.
- Broad Python smoke and adjacent engagement/facade/binding/tool lanes pass for
  this slice.

## Current Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| P0 boundary/index | complete | README, task clusters, current status, dispatch queue, acceptance draft, parent archive registration, parent navigation | Navigation exists |
| P1 consequence inventory | complete | [consequence inventory](missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md) | Authorizes only the initial bridge |
| P2 coupling contract | complete | [coupling contract](missile_lethality_secondary_consequence_coupling_contract_20260618.md) | Engineering proxy; no calibration/Pk authority |
| Runtime bridge | complete / focused-pass | [structural_consequence_system.h](../../../../../../src/systems/combat/structural_consequence_system.h), [simulation_kernel_systems.cpp](../../../../../../src/core/engine/simulation_kernel_systems.cpp) | Writes only approved aircraft/platform/loss-state surfaces |
| Diagnostics / events | complete / event-pass | `StructuralBreakupEvent` parent id is retained in `StructuralBreakupState::last_breakup_event_id`; `PlatformConsequenceEvent` records before/after consequence deltas | Diagnostic event only; no Pk, debris, or direct lifecycle |
| Focused validation | complete / focused-pass | [test_structural_failure_system.cpp](../../../../../../src/tests/test_structural_failure_system.cpp), `structural_consequence` CTest | Covers bridge, no false positives, and chain-linked consequence diagnostics |
| Broad regression | complete / broad-pass | `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/` -> 447 passed | No MLF-7 broad runtime regression observed |
| Adjacent event/facade tests | complete / pass | `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py` -> 160 passed | Covers event-store/facade/binding edge touched by P4 |
| Acceptance | complete | acceptance record updated with completed and held items | Accepted only as engineering-proxy MLF-7 slice |

## Entry Facts

- MLF-6 provides `StructuralBreakupState` and `StructuralBreakupEvent` facts, but
  it intentionally does not change `structural_integrity`, flight dynamics, or
  loss state.
- A8 provides accepted evidence that aircraft damage can propagate through
  maintained propulsion, flight, fuel, fire, sensor, and ground-contact paths.
- `AircraftDamageStateUpdate` currently runs before `StructuralFailureUpdate`;
  MLF-7 must explicitly handle that execution-order constraint.

## Residual Register

| ID | Description | Severity | Status |
| --- | --- | --- | --- |
| MLF7-R1 | P1 consequence inventory is complete for the initial bridge. | medium | closed |
| MLF7-R2 | Coupling contract and approved write surfaces are defined for the initial bridge. | high | closed |
| MLF7-R3 | Execution order is decided: bridge runs after `StructuralFailureUpdate`; downstream physics projections consume on the next tick. | high | closed |
| MLF7-R4 | Runtime bridge and focused C++ tests exist and pass. | high | closed |
| MLF7-R5 | Debris/wreck lifecycle remains deferred to MLF-8. | medium | intentionally held |
| MLF7-R6 | Pk/statistical trend authority remains deferred to MLF-9. | medium | intentionally held |
| MLF7-R7 | Dedicated structural-consequence event/diagnostic export now records a chain-linked `platform_consequence` event for material consequence deltas. | medium | closed |
| MLF7-R8 | Broad `tests/runtime/air_combat/` and `tests/world_batch/` smoke passed for this slice. | medium | closed |

## Recommended Next Actions

1. Keep MLF-8 debris/wreck lifecycle, MLF-9 Pk/statistical trend projection, and
   MLF-10 calibration gates as explicit follow-ons.
2. Open MLF-8/9/10 only as separate follow-on subprojects; do not extend the
   archived MLF-7 packet unless a regression or authority correction is found.

## Forbidden Claims

- [x] MLF-7 runtime behavior is limited to the approved structural consequence
  bridge.
- [x] No direct crash/deletion rule exists.
- [x] No debris/wreck lifecycle exists.
- [x] No Pk authority exists.
- [x] No real weapon, stock AIM-120C, MQ-9, or F-16C lethality authority exists.
- [x] No naval or ground structural consequence model exists.
