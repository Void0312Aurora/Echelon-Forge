# Takeoff-To-Cruise Mixed-Mode Notes

This document records the historical P3 takeoff-to-cruise mixed-mode baseline
and the route-generation fix that restored coherent training behavior. The
config and scenario paths below are maintained repository inputs where noted;
experiment directories are local/retained artifacts and are not current
authority unless a newer task or reference-artifact page promotes them.

## Artifact References

- Historical/local experiment artifact:
  `experiments_tmp/20260316_p3_takeoff_to_cruise_mixedmode_worldyawroutefix_retrain_v1`
- Maintained training config:
  `examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json`
- Historical artifact-provenance config:
  `examples/config/Archive/training/pre_freeze_experiments/p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json`
- Maintained training scenario:
  `scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
- Maintained eval scenario:
  `scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json`
- Historical/local bridge-only experiment outputs:
  `experiments_tmp/archive_takeoff_to_cruise_bridge_20260316`

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

- Current implementation entries:
  `gym_envs/scenario_loader/route_generation.py` and
  `gym_envs/scenario_loader/core.py`
- Change:
  dynamically generated route waypoints are now passed through `_rotate_waypoints_inplace(...)` whenever mission heading is configured to rotate with world yaw.

Regression coverage:

- `tests/world_batch/test_world_batch_runtime.py`
- `tests/world_batch/test_world_batch_vec_env.py`
- `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`
- `tests/scenario/test_scenario_compiler.py`

## Historical Outcome Captured By This Note

After the route-rotation fix and retraining from the latest mixed-mode checkpoint:

- Seed set `123-126`: `100%` success, `100%` survival, mean reward `14356.41`
- Seed set `1001-1004`: `100%` success, `100%` survival, mean reward `13987.14`

Treat this as a historical bridge baseline. Newer takeoff-to-cruise work should
promote its own frozen config, artifact record, or task status before replacing
the maintained scenario/config references above.

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
