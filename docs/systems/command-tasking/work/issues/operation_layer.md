# Operation Layer and Action Space

Language:
- English canonical: `operation_layer.md`
- Chinese companion: [operation_layer.zh.md](operation_layer.zh.md)

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/command-tasking/work/issues/operation_layer.md`
Owner: `systems/command-tasking`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

This document proposes the operation layer that bridges AI decisions and the
control model. It is a draft action-space reference pending owner verification.

## Position in the Stack
- AI/Policy produces actions.
- Operation layer maps actions to stable, bounded commands.
- Control model consumes commands and enforces physics limits.

Data flow:
AI action -> Operation layer -> MovementCommand -> ControlModel -> Velocity/Transform

## Action Levels
1) High-level targets (absolute)
- target_heading (deg, NAV)
- target_speed (m/s)
- target_altitude (m)
- fire (bool)
Pros: simple. Cons: policy must manage constraints explicitly.

2) Rate-level commands (normalized)
- turn_rate_cmd in [-1, 1] -> deg/s
- accel_cmd in [-1, 1] -> m/s^2
- climb_rate_cmd in [-1, 1] -> m/s
- fire_cmd in [0, 1]
Pros: stable training signal, easy to clamp.

3) Discrete tactical actions (optional)
- turn_left, turn_right, accelerate, decelerate, climb, dive, fire
- mapped to rate-level commands with fixed magnitudes.

## Default Action Space (Aircraft)
Use rate-level commands as the default control API for AI agents.

Parameters (per unit type or scenario):
- max_turn_rate_deg_s
- max_accel_mps2
- max_climb_rate_mps
- min_speed_mps, max_speed_mps
- min_alt_m, max_alt_m

Mapping (per tick):
1) turn_rate = turn_rate_cmd * max_turn_rate_deg_s
2) accel = accel_cmd * max_accel_mps2
3) climb_rate = climb_rate_cmd * max_climb_rate_mps
4) Integrate to targets:
   - target_heading += turn_rate * dt
   - target_speed += accel * dt
   - target_altitude += climb_rate * dt
5) Clamp targets to bounds and feed MovementCommand.

Notes:
- Use FlightModel limits to tighten bounds (stall + max_g).
- Clamp heading to [0, 360) in NAV degrees.
- Keep per-agent command state (heading/speed/alt) to integrate smoothly.

## Action Space Interfaces (Planned)
- ActionSpaceConfig: holds bounds and rate limits.
- AgentAction: normalized vector for a unit.
- ActionMapper: converts AgentAction -> MovementCommand.

## Logging
Record actions alongside observations in scenario logs:
- raw action vector
- mapped MovementCommand
- derived limits (effective min speed, g-limited turn rate)

## Next Steps
- Add ActionSpaceConfig to content/ or scenario files.
- Implement an ActionMapper that is used by Python gym environments.
- Add bindings to set/get action space from Python.

## Current Implementation Notes
- Components: `ActionCommand`, `ActionSpaceConfig`, `CommandLag`, `LaggedCommand`.
- Systems: `ActionMapping` (ActionCommand -> MovementCommand) and `CommandLag`.
- Control consumes `LaggedCommand`, so command lag applies to all commanded aircraft.
