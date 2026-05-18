# Pilot Observation Contract

Language:
- English canonical: `obs.md`
- Chinese companion: [obs.zh.md](obs.zh.md)

Status: `2026-05-18` specialization baseline for maintained air mission observation.

This document defines the maintained air observation contract exposed through
the mission-observation surface. It does not attempt to describe every raw
instrument, radar page, or pilot sensation in the full environment.

## Scope

The maintained contract here is the mode-based `mission_observation` vector used
by the current runtime and tests.

Primary references:

- [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py)
- [gym_envs/scenario_loader/mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py)
- [src/core/mission/runtime/mission_runtime.h](../../../src/core/mission/runtime/mission_runtime.h)
- [tests/runtime/mission/test_mission_obs_taxonomy.py](../../../tests/runtime/mission/test_mission_obs_taxonomy.py)

This document does not define:

- the full raw environment observation dictionary
- generic sensor contacts or RWR pages
- a joint/common-core observation ontology

## Mode-Based Contract

The maintained mission-observation modes are:

| Mode | Dim | Purpose |
| :--- | ---: | :--- |
| `basic` | 4 | command-following baseline |
| `nav_v1` | 11 | early waypoint navigation contract |
| `nav_v2` | 14 | maintained route/LNAV contract |
| `nav_v2_formation_v1` | 17 | `nav_v2` plus formation offsets |
| `nav_v2_formation_role_v1` | 21 | formation offsets plus role/slot fields |
| `nav_v2_cooperative_takeoff_v1` | 25 | route, takeoff, formation, and role fields |

Field order is part of the contract.

## Shared Core Fields

All modes begin with the same four fields:

1. `command_code`
2. `target_heading_deg`
3. `target_altitude_m`
4. `target_speed_mps`

These are the maintained command-following anchors for the air runtime.

## Navigation Fields

`nav_v1` adds:

- `active_wp_idx`
- `total_wps`
- `dist_m`
- `xtk_m`
- `dtg_m`
- `direct_bearing_deg`
- `desired_leg_track_deg`

`nav_v2` replaces that with the maintained LNAV-style set:

- `selected_steerpoint`
- `steerpoint_mode_code`
- `dist_m`
- `bearing_rel_deg`
- `altitude_delta_m`
- `cdi_norm`
- `track_angle_error_deg`
- `leg_distance_remaining_m`
- `next_turn_deg`
- `distance_to_turn_m`

The authoritative index labels for these fields are defined by
[python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py).

## Formation Fields

`nav_v2_formation_v1` adds:

- `form_offset_x_m`
- `form_offset_y_m`
- `form_offset_z_m`

These are air-specialization fields. They do not belong in common core.

`nav_v2_formation_role_v1` adds:

- `self_role_code`
- `self_formation_role_code`
- `relative_slot_code`
- `reference_relative_slot_code`

These fields bridge common/service role semantics into the air formation surface.

## Cooperative Takeoff Fields

`nav_v2_cooperative_takeoff_v1` adds the air takeoff/tasking fields:

- `takeoff_procedure_code`
- `takeoff_clearance_code`
- `takeoff_interval_s`
- `runway_slot_code`

plus the same formation/role fields listed above.

This mode is the maintained air contract for cooperative takeoff guidance, not a
generic cross-domain takeoff schema.

## Runtime Rules

- Mode length stays fixed even when route guidance is unavailable.
- When route guidance is unavailable, the navigation portion is zero-filled.
- Field visibility is mode-dependent.
- Formation and takeoff fields are not assumed to exist outside the modes that
  declare them.

## Ownership Boundary

Keep in common core:

- abstract command-following anchors
- role/slot semantics that survive across services

Keep in air specialization:

- runway- and takeoff-specific fields
- route/LNAV/ILS semantics
- formation offsets and air role details

## Non-Goals

This document does not standardize:

- `oat`
- `wind_vec`
- `rwr_state`
- `radar_contacts`
- `missile_count`

Those may exist elsewhere in the wider environment or future observation
surfaces, but they are not part of the maintained air mission-observation
contract defined here.
