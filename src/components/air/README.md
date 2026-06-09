# `src/components/air` Boundary

`components/air` holds air-domain ECS value types and tuning state. It is the
component-side owner for flight-dynamics tuning that is specific to fixed-wing
aircraft behavior and should not be treated as shared physics state.

## Allowed

- Air-domain data components, tuning structs, and lightweight value helpers.
- Flight dynamics tuning consumed by `systems/air` and air models.

## Forbidden

- System registration, per-tick update logic, integrators, or control-model execution.
- Naval or ground component ownership.
- Python bindings, facades, scenario loading, or runtime orchestration.

## Current Files

- [flight_dynamics_tuning.h](flight_dynamics_tuning.h)
  - `AeroTuning`, `EngineTuning`, `StallState`, and air flight-dynamics helper functions.

## Compatibility

The old `components/physics/flight_dynamics_tuning.h` header remains as an
include-only wrapper. New code should include `components/air/flight_dynamics_tuning.h`.
