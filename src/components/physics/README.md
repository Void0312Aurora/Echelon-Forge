# `src/components/physics` Boundaries

`components/physics` saves shared physical state components, including dynamic
state, control law parameters, forces, instruments, and performance data. It
should no longer absorb command/tasking concepts or air-specific tuning owners.

## Allowed

- Physical states such as attitude, velocity, acceleration, angular velocity, force, and mass.
- Control law parameters, performance envelope, instrument state.
- ECS components that directly read/write with the physical system.
- Include-only compatibility wrappers for air-specific tuning during migration.

## Prohibited

- Adding new types of pilot action, mission command, task order, leader intent, or pilot report.
- System tick, integrator, control law execution logic.
- Mission transition, episode runtime, or Python binding.

## Migration Notes

`action.h` is a historical aggregation header file, now degraded to a compatibility umbrella header. Real type definitions have been migrated to:

- `components/command/`
- `components/tasking/`

`flight_dynamics_tuning.h` is now a compatibility wrapper around
`components/air/flight_dynamics_tuning.h`. New physical components can continue
to be placed in this directory; new command or task semantics cannot continue to
be placed in this directory, and new air-specific tuning owners belong in
`components/air`.
