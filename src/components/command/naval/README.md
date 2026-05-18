<!-- Machine-translated draft generated on 2026-05-18 from src/components/command/naval/README.md. Review before treating this file as authoritative. -->

# `src/components/command/naval` Boundary

`components/command/naval` holds command extensions for naval/maritime execution surfaces. It hosts naval-specific execution intents, such as carrier aircraft launch/recovery, formation station-keeping, and OTH relay control, rather than cross-domain shared command core.

## Allowed

- `MissionCommandNaval` and similar naval extension fields.
- Command code constants and lightweight helpers that serve only the naval/maritime execution surface.
- Naval execution DTOs consumable by `systems/naval` and `core/mission`.

## Prohibited

- Cross-domain shared command transport/core; those go into `common/`.
- Tasking DTOs such as `TaskOrder`, `LeaderIntent`, `PilotReport`.
- Tick logic for vessel movement, carrier aircraft scheduling, data link timing, etc.; those belong to `systems/naval` or `systems/systems`.
- Python bindings, facade request/result, or environment glue.

## Current Files

- [mission_command_naval.h](mission_command_naval.h)
  - Naval extension fields and command codes for carrier aircraft launch/recovery, OTH relay, station radius/azimuth, etc.

## Dependency Direction

This directory may depend on `components/command/common`. It must not depend on implementation details of `systems/`, `core/mission`, `runtime/facade`, or `interfaces/python`.
