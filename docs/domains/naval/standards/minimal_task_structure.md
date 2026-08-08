# Naval Minimal Task Structure

Language:
- English canonical: `minimal_task_structure.md`
- Chinese companion: [minimal_task_structure.zh.md](minimal_task_structure.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/standards/minimal_task_structure.md`
Owner: `domains/naval`
Last verified: `2026-08-08`

Status: maintained specialization baseline for the minimal naval tasking
structure.

This note freezes the smallest useful naval tasking structure that the current runtime and task plan must support.

It is intentionally narrow, but it is no longer a generic placeholder. It captures the minimum semantics needed to connect the shared contract, the Navy service profile, and the dedicated `naval` layer.

## Scope

Supported starter task shapes:

- `TASK_SCREEN`
- `TASK_SUPPORT`
- `TASK_PATROL`
- `TASK_RECOVER`

These are the minimal entries that can express the current maritime task plan without importing air-specific formation language.

## Layered Structure Rules

When `tasking_profile = naval` or `service_profile = Navy`:

- `task_group_id` is the primary organization anchor.
- `parent_node_id` is the next fallback organization anchor.
- `task_group` is the naval mission grouping that owns the task.
- `task_unit` is the subordinate tactical unit within the task group.
- `officer_in_tactical_command` defaults to the `task_group` owner, then the `parent_node_id` fallback.
- `tactical_unit_type` remains a shared type label and can still default to `CommandNode` when the mission is group-owned.

The [Navy service profile](../../joint/service_profiles/standards/navy_profile.md)
owns how `task_group`, `task_unit`, `warfare_role_code`, and
`officer_in_tactical_command` interpret the Joint common core. This standard
owns the naval execution mapping layered on those service-profile meanings.

## Minimal Semantic Map

The minimal execution vocabulary owned by the naval specialization is:

- `screen`
- `support`
- `station`
- `recover`

### `TASK_SCREEN`

- `task_family = Escort`
- `coordination_mode = Screen`
- `warfare_role_code = ScreenCommander`
- `naval_station_type = Screen`
- `officer_in_tactical_command` is the screen-owning task group or unit.

### `TASK_SUPPORT`

- `task_family = Escort`
- `coordination_mode = Support`
- `warfare_role_code = SupportCoordinator`
- `naval_station_type = Support`
- `officer_in_tactical_command` is the supporting task group or unit.

### `TASK_PATROL`

- `task_family = Patrol`
- `warfare_role_code = SeaControlCommander`
- `naval_station_type = PatrolStation`
- `officer_in_tactical_command` is the patrol-owning task group or unit.

### `TASK_RECOVER`

- `task_family = Recover`
- `coordination_mode = Detached`
- `warfare_role_code = Unspecified` unless supplied explicitly or by an override.
- `naval_station_type = Unspecified` unless supplied explicitly or by an override.
- `officer_in_tactical_command` is the recovery-owning task group or unit.

## Semantic Notes

- `screen` means relative protection around a higher-value force.
- `support` means enabling, escort, or sustainment relationship.
- `station` means a relative position that must be held or restored.
- `recover` means return-to-control or recovery behavior, including ship/aircraft recovery context where applicable.

## Non-goals

This document does not define:

- fleet maneuver logic
- station-keeping controllers
- naval-specific mission command hierarchy beyond the minimal ownership rule
- replenishment runtime
- full carrier or surface-action workflow

It exists to freeze the minimum useful contract, not to describe the whole doctrine.

## Verification Evidence

- [Naval tasking profile](../../../../python/rl/profile/naval_profile.py)
- [Tasking profile contract tests](../../../../tests/leader/test_tasking_profile_contracts.py)

## Related Documents

- [Naval owner entrypoint](../README.md)
- [Naval Observation Contract](observation_contract.md)
- [Navy service profile](../../joint/service_profiles/standards/navy_profile.md)
