# C2 Communication and Command Chain Roadmap

This document records the plan and current implementation for command links and
communication constraints.

## Current Implementation (Minimum Viable)
- `CommandLink`: command latency and packet-loss rate at the unit level.
- `PendingCommand`: queues commands and delivers them at the scheduled time.
- Supports both `MovementCommand` and `ActionCommand`.

Relevant code entry points:
- Data structures: `src/components/action.h`
- Link system: `src/systems/command_link_system.h`
- Delivery logic: `src/core/simulation_kernel.cpp`

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
