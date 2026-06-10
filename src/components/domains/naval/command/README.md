# `src/components/domains/naval/command` Boundary

`components/domains/naval/command` holds command extensions for naval/maritime execution surfaces. It hosts naval-specific execution intents, such as carrier aircraft launch/recovery, formation station-keeping, and OTH relay control, rather than cross-domain shared command core.

The current slice is maintained but intentionally narrow: it provides `MissionCommandNaval` fields and command codes used by naval systems and contracts. It does not by itself imply a complete naval mission runtime, N4 stack, or campaign-level maritime C2 model.

## Allowed

- `MissionCommandNaval` and similar naval extension fields.
- Command code constants and lightweight helpers that serve only the naval/maritime execution surface.
- Naval execution DTOs consumable by `systems/domains/naval` and `core/mission`.

## Prohibited

- Cross-domain shared command transport/core; those go into `common/`.
- Tasking DTOs such as `TaskOrder`, `LeaderIntent`, `PilotReport`.
- Tick logic for vessel movement, carrier aircraft scheduling, data link timing, etc.; those belong to `systems/domains/naval` or `systems/systems`.
- Python bindings, facade request/result, or environment glue.

## Current Files

- [mission_command_naval.h](mission_command_naval.h)
  - Naval extension fields and command codes for carrier aircraft launch/recovery, OTH relay, station radius/azimuth, etc.

## Held Scope

- Full naval mission/task orchestration remains outside this directory.
- Contact evidence, launch requests/events, and damage diagnostics are exported through runtime engagement contracts rather than owned here.
- Ground or amphibious command semantics should not be added here as a shortcut.

## Dependency Direction

This directory may depend on `components/command/common`. It must not depend on implementation details of `systems/`, `core/mission`, `runtime/facade`, or `interfaces/python`.
