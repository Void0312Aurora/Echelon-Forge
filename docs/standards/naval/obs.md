# Naval Observation Contract

Language:
- English canonical: `obs.md`
- Chinese companion: [obs.zh.md](obs.zh.md)

Status: `2026-06-10` specialization baseline for maintained naval mission observation.

This document defines the maintained naval mission-observation contract exposed
through the current mode-based observation surface. It describes the runtime
contract already present in `python/mission_obs_taxonomy.py`; it does not create
a broader naval sensor, fire-control, or fleet-command ontology.

## Scope

The maintained contract here is the `naval_screen_station_v1` vector used by
naval screen/station runtime and tests.

Primary references:

- [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py)
- [gym_envs/scenario_loader/mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py)
- [tests/runtime/mission/test_mission_obs_taxonomy.py](../../../tests/runtime/mission/test_mission_obs_taxonomy.py)
- [tests/runtime/naval/test_naval_station_policy_surface.py](../../../tests/runtime/naval/test_naval_station_policy_surface.py)

This document does not define:

- a generic cross-service observation ontology
- ship sensor contacts beyond the maintained station/screen fields
- naval weapons-outcome or fire-control acceptance
- a replacement for the Navy service profile

## Mode-Based Contract

The maintained naval mission-observation mode is:

| Mode | Dim | Purpose |
| :--- | ---: | :--- |
| `naval_screen_station_v1` | 23 | naval screen/station guidance with contact, report-chain, ROE, assignment, and relative-slot fields |

Field order is part of the contract.

## Naval Screen/Station Fields

`naval_screen_station_v1` has these fields:

- `command_code`
- `target_heading_deg`
- `target_speed_mps`
- `station_radius_m`
- `station_bearing_deg`
- `station_error_m`
- `station_error_norm`
- `screen_separation_m`
- `screen_separation_error_m`
- `own_relative_x_m`
- `own_relative_y_m`
- `desired_relative_x_m`
- `desired_relative_y_m`
- `target_contact_present`
- `support_track_present`
- `report_chain_seen`
- `roe_state`
- `authorization_to_fire`
- `assigned_target_id`
- `assigned_target_source_id`
- `self_role_code`
- `relative_slot_code`
- `reference_relative_slot_code`

## Field Groups

Command-following anchors:

- `command_code`
- `target_heading_deg`
- `target_speed_mps`

Station and screen geometry:

- `station_radius_m`
- `station_bearing_deg`
- `station_error_m`
- `station_error_norm`
- `screen_separation_m`
- `screen_separation_error_m`
- `own_relative_x_m`
- `own_relative_y_m`
- `desired_relative_x_m`
- `desired_relative_y_m`

Contact, report-chain, and assignment state:

- `target_contact_present`
- `support_track_present`
- `report_chain_seen`
- `roe_state`
- `authorization_to_fire`
- `assigned_target_id`
- `assigned_target_source_id`

Relative role and slot fields:

- `self_role_code`
- `relative_slot_code`
- `reference_relative_slot_code`

## Runtime Rules

- Mode length stays fixed at 23 fields.
- Field order is defined by
  [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py).
- Missing contact or support-track state is represented in the declared fields;
  the mode does not grow ad hoc contact arrays.
- This mode is Python-owned in the current runtime taxonomy and is assembled
  by the scenario-loader mission-observation path.

## Ownership Boundary

Keep in common core:

- command and authority carrier shapes
- reusable assignment identifiers
- cross-service role/slot hooks

Keep in Navy service profile:

- task-group and task-unit interpretation
- officer-in-tactical-command semantics
- Navy warfare-role vocabulary

Keep in naval specialization:

- screen/station geometry
- maritime station-keeping error terms
- support-track/report-chain readiness as used by the current naval screen
  runtime
- relative-slot fields as naval formation execution data

## Non-Goals

This document does not standardize:

- full ship sensor pages
- a generic maritime track-fusion model
- naval weapon effects
- fleet-level command-and-control behavior
- air-style altitude, runway, or sortie-phase fields
