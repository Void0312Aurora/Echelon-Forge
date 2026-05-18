<!-- Machine-translated draft generated on 2026-05-18 from src/components/command/common/README.md. Review before treating this file as authoritative. -->

# `src/components/command/common` Boundary

`components/command/common` holds cross-domain shared command infrastructure. What is placed here are
"command shells, transport semantics, and shared fields that multiple execution domains may reuse", rather than the control or recycling semantics specific to the current air execution surface.

## Allowed

- `MissionCommand`'s shared core fields.
- Command-level common enums or value types reused by the communication/message layer.
- Command payload shells not bound to a specific platform.

## Forbidden

- Runway, approach, takeoff, formation and other clearly air-specific fields.
- `TaskOrder`, `LeaderIntent`, `PilotReport` and other tasking/C2 DTOs.
- Tick logic for command delivery, delay, and effective timing; these belong to `systems/`.
- Python binding or facade adaptation logic.

## Current Files

- [mission_command_core.h](mission_command_core.h)
  - Shared core semantics of `MissionCommand`.
- [comm_message.h](comm_message.h)
  - Shared communication message types.

## Dependency Direction

This directory can only depend on lower-level value types and component headers. `air/` or future `naval/`
extension layers can compose the core structures here; this directory should not depend on specific domains in reverse.
