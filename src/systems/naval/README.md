# `src/systems/naval` Boundary

`systems/naval` contains the per-tick progression logic for ship, submarine, and embarked aviation token-level runtime. It consumes `components/naval`, `components/command`, and foundational movement components, but does not own mission/tasking orchestration or facades.

## Allowed

- Updates to ship/submarine motion, heading, speed, and depth.
- Per-frame mutation for naval platforms such as sea-state response, seakeeping, and station keeping.
- Token-level runtime scheduling for launch/recovery of embarked aircraft and OTH relay behavior.

## Forbidden

- Defining naval platform components or command/tasking DTOs.
- Mission rewards, termination, scenario compilation, or episode transitions.
- Python bindings, facades, training scripts, or multi-world owners.
- Expanding the embarked aviation MVP runtime into a large, unfrozen mission orchestration layer.

## Current Files

- [ship_motion_system.h](ship_motion_system.h)
  - Updates ship speed, heading, sea-state drag, and station keeping.
- [submarine_motion_system.h](submarine_motion_system.h)
  - Updates submarine speed, heading, and depth envelopes.
- [embarked_air_ops_system.h](embarked_air_ops_system.h)
  - Token-level runtime for launch/recovery of embarked helicopters and OTH relay behavior.

## Dependency Direction

This directory may consume `components/naval`, `components/command`, `components/basic`, and the required pieces of `core/interfaces`. It should not depend on `runtime/facade`, `interfaces/python`, or training/scenario glue.
