# MLF-7 Secondary Consequence Coupling — Coupling Contract

Status: `2026-06-18` accepted for the initial runtime bridge. The contract is
engineering-proxy authority only; it is not real-world lethality, Pk, or
platform-specific calibration authority.

## Contract Decision

MLF-7 uses `StructuralBreakupState` as the runtime fact source. The bridge runs
after `StructuralFailureUpdate`, writes bounded values to maintained aircraft
damage and platform-damage surfaces, then calls `sync_platform_damage_loss_state`.

The bridge does not change the existing `AircraftDamageStateUpdate` order.
Therefore aircraft damage and loss-state fields update in the same tick, while
`FlightModel`, `Propulsion`, `Sensor`, `Mass`, and `FuelSystem` consume the new
damage state on the next tick.

For diagnostics, MLF-7 stores the last emitted structural-breakup event id on
`StructuralBreakupState` and emits a `PlatformConsequenceEvent` only when the
bridge materially changes maintained aircraft/platform state. That event uses
the structural-breakup event as `parent_event_id` and preserves the same
`chain_id`.

## Mode Mapping

| Break mode | Aircraft consequence | Platform consequence | Loss-state rule |
| --- | --- | --- | --- |
| no breakup / `Intact` | no write | no write | no change |
| `wing_loss` | `structural_integrity <= 0.70`, `flight_control_integrity <= 0.72`, `roll_control_integrity <= 0.55`, `hydraulic_pressure_availability <= 0.82`, `control_asymmetry >= 0.35`, forced landing | `mobility_capability <= 0.35`, `survivability_margin <= 0.70`; forced landing projects mobility to `<= 0.25` through maintained helper path | `MobilityKill` if maintained threshold is crossed |
| `tail_loss` | `flight_control_integrity <= 0.60`, `pitch_control_integrity <= 0.45`, `yaw_control_integrity <= 0.50`, `hydraulic_integrity <= 0.78`, `hydraulic_pressure_availability <= 0.76`, `control_asymmetry >= 0.20`, forced landing | `mobility_capability <= 0.30`, `survivability_margin <= 0.75`; forced landing projects mobility to `<= 0.25` | `MobilityKill` if maintained threshold is crossed |
| `engine_detach` | `propulsion_integrity <= 0.30`, `fuel_system_integrity <= 0.72`, `fuel_leak_severity >= 0.30`, `flammable_fluid_exposure >= 0.25`, `ignition_source_severity >= 0.20`, forced landing | `mobility_capability <= 0.30`, `survivability_margin <= 0.72`; forced landing projects mobility to `<= 0.25` | `MobilityKill` if maintained threshold is crossed |
| `fuselage_rupture` | `structural_integrity <= 0.50`, `fuel_system_integrity <= 0.65`, `crew_effectiveness <= 0.85`, `pilot_effectiveness <= 0.88`, `fuel_leak_severity >= 0.45`, `fire_severity >= 0.15`, `fuselage_fire_zone_severity >= 0.20`, forced landing | `mission_capability <= 0.65`, `survivability_margin <= 0.50`; forced landing projects mobility to `<= 0.25` | maintained helper may set `MobilityKill`; no direct deletion |
| `multi_axis` | `structural_integrity <= 0.20`, control axes `<= 0.25-0.30`, hydraulic availability `<= 0.30`, propulsion `<= 0.25`, command/navigation `<= 0.45`, `control_asymmetry >= 0.65`, `structural_overstress >= 0.75`, forced landing | `mobility_capability <= 0.0`, `mission_capability <= 0.25`, `sensor_capability <= 0.50`, `survivability_margin <= 0.0` | `Lost` through `sync_platform_damage_loss_state(..., force_lost=true)` when `airframe_breakup` is true |

## Guards

- All writes are idempotent floors or ceilings; the same irreversible breakup
  state cannot accumulate duplicate runaway deltas.
- The bridge ignores non-aircraft entities.
- The bridge does not write HP.
- The bridge does not create debris/wreck entities.
- The bridge does not delete entities.
- The bridge does not create Pk, stock-weapon truth, or training-reward outputs.
- `PlatformConsequenceEvent` output is a diagnostics-only engineering proxy and
  is not a calibrated lethality or reward authority.

## Evidence

- Implementation:
  [src/systems/combat/structural_consequence_system.h](../../../../../../../src/systems/combat/structural_consequence_system.h)
- Focused validation:
  [src/tests/test_structural_failure_system.cpp](../../../../../../../src/tests/test_structural_failure_system.cpp)
- Passing commands:
  `cmake --build build-workshop --target ef_test -j 2`
- Passing commands:
  `ctest --test-dir build-workshop -R 'structural_consequence|structural_failure' --output-on-failure`
- Passing commands:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
- Passing commands:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py`
