# `src/components/command/common` Boundary

`components/command/common` holds cross-domain shared command infrastructure. What is placed here are
"command shells, transport semantics, and shared fields that multiple execution domains may reuse", rather than the control or recycling semantics specific to the current air execution surface.

This directory is shared by the maintained air and naval command slices. It is not a dumping ground for unowned land-domain behavior: ground-specific movement, sensing, fires, and damage command semantics remain held until a native ground command schema is introduced.

## Allowed

- `MissionCommand`'s shared core fields.
- Command-level common enums or value types reused by the communication/message layer.
- Command payload shells not bound to a specific platform.

## Forbidden

- Runway, approach, takeoff, formation and other clearly air-specific fields.
- Naval stationing, embarked helo, OTH relay, or surface-engagement fields; those belong in `naval/`.
- Ground movement, sensing, fires, or damage fields; those are not maintained here yet.
- `TaskOrder`, `LeaderIntent`, `PilotReport` and other tasking/C2 DTOs.
- Tick logic for command delivery, delay, and effective timing; these belong to `systems/`.
- Python binding or facade adaptation logic.

## Current Files

- [mission_command_core.h](mission_command_core.h)
  - Shared core semantics of `MissionCommand`.
- [comm_message.h](comm_message.h)
  - Shared communication message types.

## Dependency Direction

This directory can only depend on lower-level value types and component headers. `air/` and `naval/`
extension layers can compose the core structures here; this directory should not depend on specific domains in reverse.
