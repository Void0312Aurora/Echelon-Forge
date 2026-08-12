# C2 Communication and Command Chain Roadmap

Language:
- English canonical: `c2_communication.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/command-tasking/work/issues/c2_communication.md`
Owner: `systems/command-tasking`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

This document records the plan and current implementation for command links and
communication constraints.

## Current Implementation (Minimum Viable)
- `CommandLink`: command latency and packet-loss rate at the unit level.
- Deferred delivery is represented by the concrete pending command components
  in `command_link.h`: `PendingMovementCommand`, `PendingActionCommand`, and
  `PendingMissionCommand`. There is no generic `PendingCommand` type.
- Supports `MissionCommand` delivery plus the maintained compatibility bridge
  for legacy `MovementCommand` and `ActionCommand` surfaces.

Relevant code entry points:
- Link state and pending command data:
  `src/components/command/command_link.h`
- Legacy movement/action compatibility DTOs:
  `src/components/command/legacy_command.h`
- Link system:
  `src/systems/systems/command_link_system.h`
- Command API queueing:
  `src/core/engine/simulation_kernel_command_api.cpp`

## Design Goals
1) Introduce realistic command-link limits (latency, packet loss, bandwidth).
2) Support hierarchical command flow (high-level objective -> mid-level task ->
   low-level action).
3) Simulate communications damage and link degradation during training.

## Future Extensions
- Bandwidth and frequency limits: throttle or downsample high-rate commands.
- Multi-hop links: relay latency and packet loss between command nodes.
- Task-style commands: issue target points or patrol areas instead of continuous
  control signals.
- C2 node destruction: link failure and transition to autonomous modes.
