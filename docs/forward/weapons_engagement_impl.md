# Weapons and Engagement Rules Implementation Notes

This document records the weapons and engagement-rule behavior currently
implemented in code so it can be compared against the roadmap.

## Implemented Items

### Missile Guidance Delay and Update Period
- `Missile.guidance_delay_s` controls the delay before guidance starts after
  launch.
- `Missile.guidance_update_period_s` controls how often guidance updates run.
- Related fields:
  - `Missile.launch_time`
  - `Missile.last_guidance_time`

### Seeker Lock Conditions
- FOV limit: `Missile.seeker_fov_deg`.
- Lock range: `Missile.seeker_lock_range`.
- If the conditions are not met, the missile keeps its current velocity
  direction (inertial flight).

### Guidance Model
- Current guidance uses 2D PN (proportional navigation):
  - LOS angular rate drives the turn rate.
  - `Missile.nav_gain` is the PN gain.
  - Turn rate is limited by `Missile.turn_rate`.

## Code Entry Points
- Missile parameter setup: `src/core/simulation_kernel.cpp`
- Guidance logic: `src/models/default_guidance_model.cpp`
- Guidance system: `src/systems/guidance_system.h`
- Data structures: `src/components/weapon.h`

## Follow-Up Plan (Aligned with the Roadmap)
- Guidance G-limit constraints (from `max_g` or missile-model limits).
- Target-tracking delay and break-lock logic for guidance / sensors.
- Layered hit outcomes: `Hit` / `MissionKill` / `MobilityKill` /
  `SensorKill`.
- Launch-envelope estimation and scenario-level rule configuration.
