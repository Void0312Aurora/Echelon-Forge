# Weapons and Engagement Rules Implementation Notes

Language:
- English canonical: `weapons_engagement_impl.md`
- Chinese companion: [weapons_engagement_impl.zh.md](weapons_engagement_impl.zh.md)

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/weapons/work/issues/weapons_engagement_impl.md`
Owner: `systems/weapons`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

This document records the weapons and engagement-rule behavior currently
implemented in code so it can be compared against the roadmap.

## Implemented Items

### Launch Setup and Runtime Tuning
- `SimulationKernel::fire_missile(...)` resolves the selected munition and
  builds launch-time missile state in
  `src/core/engine/simulation_kernel_weapon_api.cpp`.
- Launch-time setup currently fills:
  - `Missile.guidance_delay_s` and `Missile.guidance_update_period_s`
  - `Missile.max_flight_time_s` and `Missile.nav_gain`
  - seeker limits such as `Missile.seeker_fov_deg` and
    `Missile.seeker_lock_range`
  - track-memory, seeker-activation, and optional midcourse-datalink fields
  - boost/sustain, drag, and autopilot-related tuning fields

### Seeker Screening and Track Memory
- Guidance starts only after `Missile.guidance_delay_s` and can be rate-limited
  by `Missile.guidance_update_period_s`.
- Candidate detections are filtered by alliance, assigned target, seeker FOV,
  seeker lock range, and whether terminal guidance has a local sensor hit.
- If direct detections disappear, the missile can continue on filtered track
  memory for `Missile.track_memory_timeout_s`; if no valid track remains, it
  falls back to ballistic flight.
- `Missile.midcourse_datalink_supported` allows non-local detections to feed
  guidance before terminal seeker handoff.

### Guidance and Flight Dynamics
- The current guidance model lives in
  `src/models/weapons/default_guidance_model.cpp`.
- Guidance blends a capture term with PN-style commands derived from filtered
  LOS bearing/elevation rates.
- Lateral acceleration is limited by `Missile.guidance_max_lateral_g` and
  shaped by autopilot response terms, rather than by a simple
  `Missile.turn_rate` clamp.
- `Missile.turn_rate` still exists as a tuning input and is used as a fallback
  when deriving the lateral-G limit if that value is otherwise unset.
- The runtime also updates boost/sustain thrust, drag, fuel burn, and
  `Missile.max_flight_time_s` self-destruct behavior.

## Code Entry Points
- Missile launch and tuning: `src/core/engine/simulation_kernel_weapon_api.cpp`
- Guidance model: `src/models/weapons/default_guidance_model.cpp`
- Guidance system registration: `src/systems/combat/guidance_system.h`
- Missile data structures and runtime state: `src/components/combat/weapon.h`

## Follow-Up Plan (Aligned with the Roadmap)
- Refine launch-envelope estimation and scenario-level rule configuration.
- Expand seeker break-lock / countermeasure behavior beyond the current
  track-memory model.
- Layered hit outcomes: `Hit` / `MissionKill` / `MobilityKill` /
  `SensorKill`.
- Evaluate whether additional guidance models or higher-fidelity terminal
  logic are needed.
