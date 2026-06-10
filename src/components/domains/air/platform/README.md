# `src/components/domains/air/platform` Boundary

`components/domains/air/platform` holds air-domain ECS value types and tuning state. It is the
component-side owner for flight-dynamics tuning that is specific to fixed-wing
aircraft behavior and should not be treated as shared physics state.

## Allowed

- Air-domain data components, tuning structs, and lightweight value helpers.
- Flight dynamics tuning consumed by `systems/domains/air` and air models.

## Forbidden

- System registration, per-tick update logic, integrators, or control-model execution.
- Naval or ground component ownership.
- Python bindings, facades, scenario loading, or runtime orchestration.

## Current Files

- [flight_dynamics_tuning.h](flight_dynamics_tuning.h)
  - `AeroTuning`, `EngineTuning`, `StallState`, and air flight-dynamics helper functions.

## Removed Legacy Entry

The old `components/physics/flight_dynamics_tuning.h` include path has been
removed. Code that needs air flight-dynamics tuning must include
`components/domains/air/platform/flight_dynamics_tuning.h` directly.
