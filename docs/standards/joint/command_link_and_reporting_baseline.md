# Joint Command Link and Reporting Baseline

Language:
- English canonical: `command_link_and_reporting_baseline.md`
- Chinese companion: [command_link_and_reporting_baseline.zh.md](command_link_and_reporting_baseline.zh.md)

Status: `2026-06-10` authoritative joint command-link contract aligned with active `MissionCommandCore` targeting metadata.

This document captures the minimum closed loop for `MissionCommand`, `CommandLink`, `DataLink`, and `ROE` in the joint/common core.

The goal is not to model every real-world C2 feature. The goal is to define the smallest contract that is already consistent with the current runtime and tests.

## 1. Minimum Closed Loop

The current joint command loop is:

`TaskOrder -> LeaderIntent -> MissionCommand -> CommandLink -> Execution -> Report -> DataLink`

This loop is the smallest useful boundary for the current codebase.

- `TaskOrder` starts the mission-level intent
- `LeaderIntent` refines the leader's tactical decision
- `MissionCommand` becomes the executable command state
- `CommandLink` carries delivery timing, backlog, and delivery order
- `Execution` consumes the command
- `Report` returns state and outcomes
- `DataLink` shares track and report data across the force

## 2. `MissionCommand` as the Executable Contract

`MissionCommand` is the runtime command object that consumers can execute directly.

The common portion currently includes:

- `command_code`
- `cmd_heading_deg`
- `cmd_altitude_m`
- `cmd_speed_mps`
- `route_ref_id`
- `active`

The mission command contract also carries authority-bearing fields:

- `roe_state`
- `engagement_authority_holder_id`
- `engagement_authority_grantor_id`
- `assigned_target_id`
- `authorization_to_fire`

It also carries command-context target provenance fields that support ROE and
assignment decisions without making the common core responsible for track
fusion:

- `threat_state`
- `assigned_target_track_id`
- `assigned_target_source_id`
- `assigned_target_snapshot_time_s`

The runtime tests show that these fields are round-tripped through Python bindings, episode state serialization, and controller import/export.

## 3. Common Command vs Service-Specific Command Fields

The common command layer should stay neutral and small.

Common examples:

- `command_code`
- `target_heading`
- `target_altitude`
- `target_speed`
- `roe_state`
- authority holder/grantor fields
- threat and assigned-target provenance fields

Service-specific examples:

- Air:
  - `recovery_base_id`
  - `recovery_runway_id`
  - `recovery_approach_type`
  - `takeoff_procedure_id`
  - `takeoff_clearance_id`
  - `takeoff_interval_s`
  - `runway_slot_id`
  - `formation_id`
  - `form_offset_x`
  - `form_offset_y`
  - `form_offset_z`
- Naval:
  - `reference_entity_id`
  - `station_radius_m`
  - `station_bearing_deg`
  - `embarked_helo_entity_id`
  - `launch_helo`
  - `recover_helo`
  - `relay_oth_targeting`

The tests already treat these service-specific fields as valid `MissionCommand` extensions, but they should not redefine the joint/common core naming boundary.

## 4. `CommandLink`

`CommandLink` is the delivery and ordering layer between command generation and command consumption.

The minimal semantics visible in the current runtime are:

- backlog can exist
- delivery can be delayed
- command order matters
- command arrival is not the same thing as command generation

That is enough to distinguish `CommandLink` from the command object itself.

What `CommandLink` should own in the common core:

- delivery delay
- pending queue behavior
- prioritization and reorder rules
- drop or loss handling at the transport boundary

What `CommandLink` should not own:

- platform motion logic
- weapon logic
- track fusion logic
- service-specific execution semantics

## 5. `DataLink`

`DataLink` is the shared information exchange layer for track and report data.

In this project, `DataLink` should mean:

- shared tracks
- shared reports
- shared tactical awareness data

It should not be treated as a generic raw-contact dump. The common core should prefer `track/report` semantics because that matches the current runtime direction and keeps the boundary cleaner.

## 6. `ROE`

`ROE` is part of the executable command contract.

The current tests show a minimal but real contract:

- `roe_state` is a state value, not just a boolean
- `authorization_to_fire` is a gate attached to the command
- engagement authority can be represented by holder and grantor IDs

The minimum useful interpretation is:

- `roe_state` tells the current rule state
- `engagement_authority_holder_id` tells who currently holds authority
- `engagement_authority_grantor_id` tells where that authority came from
- `assigned_target_id` tells which target is bound to the authority decision
- `threat_state` carries the command-context threat classification used by
  current runtime profiles
- `assigned_target_track_id` identifies the track record used for the assigned
  target when such provenance is available
- `assigned_target_source_id` identifies the source that supplied the assigned
  target or track context
- `assigned_target_snapshot_time_s` records the snapshot time for the assigned
  target context
- `authorization_to_fire` tells whether the command currently permits fire

This is a minimum contract, not a full doctrine model. It is enough to keep the runtime consistent and testable.

## 7. Shared Loop Semantics

The smallest closed loop should preserve these properties:

- command generation and command delivery are separate
- delivery order matters
- report data can be shared back through the data link
- ROE and authority travel with the command, not outside it

That is the practical line between a common core and a service-specific profile.

## 8. Boundary Summary

Use the following split:

- `joint/common core`
  - relationship vocabulary
  - authority scope
  - generic command contract
  - command delivery semantics
  - report sharing semantics
- `service profile`
  - air, naval, or early ground interpretation
- `platform/task specialization`
  - actual motion, stationing, recovery, and weapon execution
