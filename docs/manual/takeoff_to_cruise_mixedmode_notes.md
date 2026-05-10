# Takeoff-To-Cruise Mixed-Mode Notes

This document records the current active takeoff-to-cruise mixed-mode task and
the route-generation fix that restored coherent training behavior.

## Active Artifacts

- Active experiment:
  `/home/void0312/CMO/experiments_tmp/20260316_p3_takeoff_to_cruise_mixedmode_worldyawroutefix_retrain_v1`
- Maintained training config:
  `/home/void0312/CMO/examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json`
- Historical artifact-provenance config:
  `/home/void0312/CMO/examples/config/Archive/training/pre_freeze_experiments/p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json`
- Active training scenario:
  `/home/void0312/CMO/scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
- Active eval scenario:
  `/home/void0312/CMO/scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json`
- Archived bridge-only experiment outputs:
  `/home/void0312/CMO/experiments_tmp/archive_takeoff_to_cruise_bridge_20260316`

## Root Cause Fixed On 2026-03-16

Observed failure:

- Some bridge runs looked dramatically worse than older checkpoints.
- In visualization, the aircraft could appear to ignore the cruise route and fail to meaningfully capture the first waypoint.
- Reward traces showed large waypoint-progress and cross-track penalties even in runs that otherwise survived and stabilized.

Confirmed root cause:

- `world_yaw` rotated the airport, runway, spawn state, and mission heading.
- Dynamically generated route waypoints did not rotate with that same world transform when `rotate_mission_heading_with_world=true`.
- This made the first cruise leg inconsistent with the rotated departure geometry.
- The resulting task was no longer "takeoff, depart, then join cruise", but often "takeoff, then immediately recover toward a globally fixed leg at a large angle".

Code fix:

- File:
  `/home/void0312/CMO/gym_envs/scenario_loader.py`
- Change:
  dynamically generated route waypoints are now passed through `_rotate_waypoints_inplace(...)` whenever mission heading is configured to rotate with world yaw.

Regression coverage:

- `/home/void0312/CMO/tests/test_route_generator_world_yaw_alignment.py`
- `/home/void0312/CMO/tests/test_route_generator_rotates_with_world_heading.py`
- `/home/void0312/CMO/tests/test_route_generator_multileg_eval_distribution.py`
- `/home/void0312/CMO/tests/test_flyby_sequence_past_fix_guard.py`

## Latest Outcome

After the route-rotation fix and retraining from the latest mixed-mode checkpoint:

- Seed set `123-126`: `100%` success, `100%` survival, mean reward `14356.41`
- Seed set `1001-1004`: `100%` success, `100%` survival, mean reward `13987.14`

This is the active bridge baseline until a newer takeoff-to-cruise checkpoint
explicitly replaces it.

## Visualization

Example command:

```bash
.venv/bin/python examples/viz/viz_runner.py \
  --scenario scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json \
  --model experiments_tmp/20260316_p3_takeoff_to_cruise_mixedmode_worldyawroutefix_retrain_v1/final_model.zip \
  --algo AdaptiveKLPPO \
  --train_config examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json \
  --seed 123 \
  --port 5000
```
