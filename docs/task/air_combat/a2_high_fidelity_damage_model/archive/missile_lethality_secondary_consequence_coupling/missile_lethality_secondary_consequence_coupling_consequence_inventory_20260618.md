# MLF-7 Secondary Consequence Coupling — Consequence Inventory

Status: `2026-06-18` complete for the initial MLF-7 runtime bridge. This
inventory authorizes only the narrow bridge implemented in
[structural_consequence_system.h](../../../../../../src/systems/combat/structural_consequence_system.h).

## Read Inputs

| Surface | Fields MLF-7 may read | Runtime use |
| --- | --- | --- |
| [StructuralBreakupState](../../../../../../src/components/combat/structural_failure.h) | `breakup_state`, `active_break_modes`, `active_structural_groups`, `detached_part_count`, `airframe_breakup`, `last_breakup_event_id` | Primary runtime fact source for consequence projection; `last_breakup_event_id` links consequence diagnostics to the structural parent event |
| [StructuralBreakupEvent](../../../../../../src/runtime/contracts/engagement_contracts.h) | `header.chain_id`, `header.parent_event_id`, `header.event_id`, `breakup_state`, `break_mode`, `detached_part_ref`, `detached_part_count`, `airframe_breakup`, `cause_event_id` | Diagnostic/export input only; not used as the reactive runtime control signal in this slice |
| [KeyEntity](../../../../../../src/components/basic/common.h) | `type` | Limits runtime bridge to `UnitType::Aircraft` |

## Approved Runtime Writes

| Surface | Fields | Owner | MLF-7 rule |
| --- | --- | --- | --- |
| [AircraftDamageState](../../../../../../src/components/domains/air/combat/damage_air.h) | `structural_integrity`, `flight_control_integrity`, `hydraulic_integrity`, `hydraulic_pressure_availability`, `roll_control_integrity`, `pitch_control_integrity`, `yaw_control_integrity`, `control_asymmetry`, `propulsion_integrity`, `fuel_system_integrity`, `crew_effectiveness`, `pilot_effectiveness`, `fire_severity`, `fuel_leak_severity`, `flammable_fluid_exposure`, `ignition_source_severity`, `fuselage_fire_zone_severity`, `structural_overstress`, `forced_landing_required` | Air damage model | Write only bounded floors/ceilings through `apply_structural_breakup_consequence`; no additive runaway |
| [PlatformDamageState](../../../../../../src/components/combat/common/damage_common.h) | `mission_capability`, `mobility_capability`, `sensor_capability`, `survivability_margin`, kill flags, `loss_state` | Common platform damage model | Capabilities are bounded and then synchronized through `sync_platform_damage_loss_state` |
| [Health](../../../../../../src/components/combat/health.h) | `mission_kill`, `mobility_kill`, `sensor_kill` | Common loss-state mirror | Updated only by `sync_platform_damage_loss_state`; MLF-7 does not reduce HP |
| [PlatformConsequenceEvent](../../../../../../src/runtime/contracts/engagement_contracts.h) | `header`, before/after capability fields, kill flags, aircraft-damage before/after/delta strings, `loss_state_from`, `loss_state_to` | Engagement event diagnostics | Recorded only when structural consequence projection changes maintained state and an upstream structural event id exists |

## Maintained Downstream Consumers

| Surface | Owner | Cadence |
| --- | --- | --- |
| [FlightModel](../../../../../../src/components/physics/performance.h) | `AircraftDamageStateUpdate` in [damage_system_air.h](../../../../../../src/systems/combat/damage_system_air.h) | Consumes MLF-7 aircraft damage state on the next update tick because the bridge runs after `AircraftDamageStateUpdate` |
| [Propulsion](../../../../../../src/components/physics/dynamics.h) | `AircraftDamageStateUpdate` | Same next-tick projection |
| [Sensor](../../../../../../src/components/systems/sensor.h) | `AircraftDamageStateUpdate` | Same next-tick projection |
| [Mass](../../../../../../src/components/physics/dynamics.h) and `FuelSystem` | `AircraftDamageStateUpdate` | Same next-tick fuel leak projection |

## Execution Order

Current registration in
[simulation_kernel_systems.cpp](../../../../../../src/core/engine/simulation_kernel_systems.cpp):

1. `register_damage_system_common`
2. `register_aircraft_damage_system` / `AircraftDamageStateUpdate`
3. `register_structural_failure_system` / `StructuralFailureUpdate`
4. `register_structural_consequence_system` / `StructuralConsequenceUpdate`

Result: `StructuralConsequenceUpdate` writes `AircraftDamageState`,
`PlatformDamageState`, and loss-state mirrors in the same tick as the structural
breakup fact. Flight-model, propulsion, mass, and sensor projections see those
aircraft-damage fields on the next tick.

## Forbidden Writes

- No `e.destruct()` or target entity deletion.
- No debris/wreck entity creation or detached ECS lifecycle.
- No HP reduction by MLF-7 itself.
- No Pk/statistical lethality projection.
- No training reward changes.
- No weapon-specific, MQ-9, F-16C, AIM-120C, naval, or ground lethality claim.

## Evidence

- Runtime bridge:
  [src/systems/combat/structural_consequence_system.h](../../../../../../src/systems/combat/structural_consequence_system.h)
- Registration:
  [src/core/engine/simulation_kernel_systems.cpp](../../../../../../src/core/engine/simulation_kernel_systems.cpp)
- Focused tests:
  [src/tests/test_structural_failure_system.cpp](../../../../../../src/tests/test_structural_failure_system.cpp)
- Validation:
  `cmake --build build-workshop --target ef_test -j 2`
- Validation:
  `ctest --test-dir build-workshop -R 'structural_consequence|structural_failure' --output-on-failure`
- Validation:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
- Validation:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py`
