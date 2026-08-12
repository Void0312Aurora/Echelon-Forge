# Air Mission Command and Tasking Contract

Language:
- English canonical: `mission_command_and_tasking_contract.md`
- Chinese companion: [mission_command_and_tasking_contract.zh.md](mission_command_and_tasking_contract.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/air/standards/mission_command_and_tasking_contract.md`
Owner: `domains/air`
Last verified: `2026-08-08`

Status: maintained specialization baseline for air tasking and executable
command semantics.

This document defines the maintained air-side contract for:

- `TaskOrderAir`
- `LeaderIntentAir`
- air-specialized fields carried by `MissionCommand`

It replaces earlier descriptions that treated air mission command as a generic
project-wide command standard.

## Scope

Primary references:

- [src/components/domains/air/tasking/task_order_air.h](../../../../src/components/domains/air/tasking/task_order_air.h)
- [src/components/domains/air/tasking/leader_intent_air.h](../../../../src/components/domains/air/tasking/leader_intent_air.h)
- [src/components/command/common/mission_command_core.h](../../../../src/components/command/common/mission_command_core.h)
- [src/components/domains/air/command/mission_command_air.h](../../../../src/components/domains/air/command/mission_command_air.h)
- [gym_envs/scenario_loader/runtime_state.py](../../../../gym_envs/scenario_loader/runtime_state.py)
- [tests/runtime/mission/test_mission_command_air_fields_roundtrip.py](../../../../tests/runtime/mission/test_mission_command_air_fields_roundtrip.py)

## Layer Split

The maintained split is:

- common core:
  - `TaskOrderCore`
  - `LeaderIntentCore`
  - `MissionCommandCore`
- air specialization:
  - `TaskOrderAir`
  - `LeaderIntentAir`
  - `MissionCommandAir`

The type names may still be composed together in code, but ownership stays
layered.

## Common-Core Command Fields Used By Air

Air runtime still depends on the shared `MissionCommandCore` fields:

- `command_code`
- `cmd_heading_deg`
- `cmd_altitude_m`
- `cmd_speed_mps`
- `route_ref_id`
- `roe_state`
- `engagement_authority_holder_id`
- `engagement_authority_grantor_id`
- `assigned_target_id`
- `threat_state`
- `assigned_target_track_id`
- `assigned_target_source_id`
- `assigned_target_snapshot_time_s`
- `authorization_to_fire`
- `active`

These fields are not air-only. Air uses them, but does not own them.

## Air-Specialized `MissionCommand` Fields

The maintained air extension fields are:

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

These fields are air-specific execution/tasking semantics. They must not be
promoted into common core just because they currently appear in a shared runtime
carrier.

## Air Tasking Fields

`TaskOrderAir` currently carries the upstream air tasking surface, including:

- package/element/lead identifiers
- station anchor and station geometry
- altitude/speed block and target values
- recovery configuration
- takeoff procedure and runway slot
- formation template/contract/role linkage
- support-sector and mutual-support metadata

This is tasking-side air organization semantics, not the final executable
command object.

## Air Leader-Intent Fields

`LeaderIntentAir` currently carries the leader-side air decision surface,
including:

- `phase_id`
- `element_phase_id`
- `route_ref_id`
- recovery and approach fields
- takeoff procedure/clearance/interval/runway slot
- formation mode and offsets
- join/rejoin/split flags
- support anchor and slot offsets
- approach-arm, commit-to-land, and abort flags

This is the air leader's intermediate decision surface before final mapping into
`MissionCommand`.

## Maintained `command_code` Semantics

The Air runtime and tests use the following maintained base command values:

- `0`: idle / hold
- `1`: takeoff
- `2`: vector / cruise / direct command-following
- `3`: waypoint or LNAV-style route navigation
- `4`: landing / final approach

This is the Air-consumed base set, not an exhaustive project-wide command-code
catalog. Other domain owners may define separately tested extensions; this Air
standard neither owns nor forbids those codes. Untested Air macro-command
catalogs must not be presented here as stable runtime behavior.

## Roundtrip Requirements

The maintained air command contract must survive:

- JSON mission-command backfill/export
- execution-episode state import/export
- post-waypoint transition handoff
- mission-observation assembly for takeoff/formation modes

That is why fields such as `recovery_*`, `takeoff_*`, `runway_slot_*`, and
`formation_*` are tested for roundtrip preservation.

## Ownership Boundary

Keep in common core:

- command carrier shape
- authority and ROE fields
- neutral target-heading/altitude/speed references

Keep in air specialization:

- runway and recovery
- takeoff procedure and runway slot
- formation offsets and air formation identifiers
- approach/landing-specific leader intent

## Non-Goals

This document does not attempt to standardize a complete air-task doctrine
catalog, a full CAP/BARCAP/TARCAP taxonomy, or every future leader behavior.
It only describes the maintained contract the current runtime and tests already
treat as stable.
