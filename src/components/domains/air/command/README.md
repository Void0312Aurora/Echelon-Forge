# `src/components/domains/air/command` Boundary

`components/domains/air/command` stores command extensions for the current air execution surface. It carries air-specific command semantics such as routes, recovery, runway handling, and low-level control input resolution.

## Allowed

- Air-execution-surface extension fields such as `MissionCommandAir`.
- Command interpretation helper types reused by the current air runtime.
- Lightweight helpers in `PilotAction -> legacy command` parsing that truly belong to the air surface.

## Forbidden

- Cross-domain shared command core; those go into `common/`.
- Tasking DTOs such as `TaskOrder`, `LeaderIntent`, and `PilotReport`.
- Control-law logic, physics integration, mission transitions, or reward logic.
- Python bindings or facade request/result types.

## Current Files

- [mission_command_air.h](mission_command_air.h)
  - Air extension fields for routes, recovery, takeoff/landing, and similar semantics.
- [control_input_resolution.h](control_input_resolution.h)
  - Helpers for resolving low-level air control inputs.

## Dependency Direction

This directory may depend on `components/command/common`. It must not depend on `systems/`, `core/mission`, or `interfaces/python`.
