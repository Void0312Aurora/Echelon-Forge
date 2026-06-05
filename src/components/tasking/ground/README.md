# `src/components/tasking/ground` Boundary

This directory is the maintained C++ owner-slice home for early ground tasking
DTOs. It covers G0/G1 static task and status infrastructure only.

## Allowed

- `TaskOrderGround`, `LeaderIntentGround`, and `PilotReportGround` owner slices.
- Ground static task/status enums such as `GroundTaskMode` and
  `GroundStatusPhase`.
- Objective/area references, static occupy/support task mode, tactical
  commander ID, and the 1 Hz tasking cadence baseline.
- Projection helpers used by the flat compatibility shells and maintained batch
  contracts.

## Not Allowed

- Route movement, terrain passability, sensing, fires, damage, suppression,
  logistics, or combat outcome semantics.
- Ground-only runtime loops or private command/status pipelines.
- Python binding code; bindings live under `src/interfaces/python`.

## Current Slice

The current fields are intentionally static:

- `ground_task_mode`
- `ground_status_phase`
- `objective_area_id`
- `objective_node_id`
- `ground_commander_id`
- `tactical_cadence_hz`
- `readiness_ratio` on `PilotReportGround`

They make the G0/G1 ground task/status chain addressable from C++ and Python
without releasing G2 movement.
