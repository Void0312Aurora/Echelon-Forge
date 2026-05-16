# Naval Minimal Task Structure

This note freezes the smallest useful naval tasking structure that WP7 supports.

## Scope

These rules are intentionally narrow. They are meant to support early joint-development seams, not a full fleet runtime.

Supported starter task shapes:

- `TASK_SCREEN`
- `TASK_SUPPORT`
- `TASK_PATROL`
- `TASK_RECOVER`

## Minimal structure rules

When `tasking_profile = naval` or `service_profile = Navy`:

- `task_group_id` is the primary minimal organization anchor.
- `parent_node_id` is the next fallback organization anchor.
- `officer_in_tactical_command` defaults to `task_group_id`, then `parent_node_id`.
- `tactical_unit_type` defaults to `CommandNode` when `task_group_id` is present.

## Minimal semantic mapping

`TASK_SCREEN`

- `task_family = Escort`
- `coordination_mode = Screen`
- `warfare_role_code = ScreenCommander`
- `naval_station_type = Screen`

`TASK_SUPPORT`

- `task_family = Escort`
- `coordination_mode = Support`
- `warfare_role_code = LogisticsCoordinator`
- `naval_station_type = Support`

`TASK_PATROL`

- `task_family = Patrol`
- `warfare_role_code = SeaControlCommander`
- `naval_station_type = PatrolStation`

`TASK_RECOVER`

- `task_family = Recover`
- `coordination_mode = Detached`

## Non-goals

This document does not define:

- fleet maneuver logic
- station-keeping controllers
- naval-specific mission command hierarchy
- replenishment runtime
- full carrier or surface-action workflow
