# `src/systems/domains/naval` Boundary

`systems/domains/naval` contains the per-tick progression logic for ship,
submarine, and embarked aviation token-level runtime. It consumes
`components/domains/naval/platform`, `components/command`, and foundational
movement components, but does not own mission/tasking orchestration or facades.

This is an active naval runtime slice, not a placeholder. It is still bounded to
platform motion, embarked-air tokens, OTH relay, and naval weapon-release hooks;
tasking/contact evidence is surfaced through contracts/facade packets rather
than owned here as a full N4 mission runtime.

## Allowed

- Updates to ship/submarine motion, heading, speed, and depth.
- Per-frame mutation for naval platforms such as sea-state response, seakeeping, and station keeping.
- Token-level runtime scheduling for launch/recovery of embarked aircraft and OTH relay behavior.
- Naval mission-command weapon-release hooks that call the shared weapon release service.

## Forbidden

- Defining naval platform components or command/tasking DTOs.
- Mission rewards, termination, scenario compilation, or episode transitions.
- Python bindings, facades, training scripts, or multi-world owners.
- Expanding the embarked aviation MVP runtime into a large, unfrozen mission orchestration layer.
- Owning N4 contact evidence, tasking packets, or pre-fire diagnostics exports.

## Current Files

- [ship_motion_system.h](ship_motion_system.h)
  - Updates ship speed, heading, sea-state drag, and station keeping.
- [submarine_motion_system.h](submarine_motion_system.h)
  - Updates submarine speed, heading, and depth envelopes.
- [embarked_air_ops_system.h](embarked_air_ops_system.h)
  - Token-level runtime for launch/recovery of embarked helicopters and OTH relay behavior.
- [naval_mission_weapon_release_system.h](naval_mission_weapon_release_system.h)
  - Naval mission-command weapon-release bridge into the shared weapon release service.
- [naval_logistics_system.h](naval_logistics_system.h)
  - Naval underway replenishment progression for abstract stores transfer.

## Dependency Direction

This directory may consume `components/domains/naval/platform`,
`components/command`, `components/basic`, and the required pieces of
`core/interfaces`. It should not depend on `runtime/facade`,
`interfaces/python`, or training/scenario glue.
