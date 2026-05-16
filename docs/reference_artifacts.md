# Reference Artifacts

This document replaces the older per-phase `active_*_artifacts.md` notes.

Its purpose is narrower:

- record the maintained config/scenario entrypoints that still exist in the workspace
- preserve minimal provenance notes for historical lines
- avoid pointing readers at experiment outputs that have already been cleaned from the repo workspace

Retention boundary:

- `scenarios/` and maintained config files remain versioned repo inputs.
- `experiments/`, `datasets/`, and `output/` are not the canonical source of truth and may be cleaned from the active workspace.
- When a run directory or generated dataset is removed, keep only the minimal surviving provenance pointers here or in task/report documents.

## Takeoff-To-Cruise Bridge

- Maintained training config:
  [p3_takeoff_to_cruise_retrain_v1.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json)
- Historical artifact-provenance config:
  [p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json](/home/void0312/Workshop/CMO/examples/config/Archive/training/pre_freeze_experiments/p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json)
- Training scenario:
  [takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json](/home/void0312/Workshop/CMO/scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json)
- Eval scenario:
  [takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json](/home/void0312/Workshop/CMO/scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json)

Status:

- Historical bridge experiment outputs were cleaned from the active workspace.
- Use the maintained config and scenarios above as the surviving reference entrypoints.

## Cruise

- Maintained execution config used for the historical bridge/cruise lineage:
  [p3_takeoff_to_cruise_retrain_v1.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json)
- Historical artifact-provenance config:
  [p2_autopilot_residual_navv2_paramroute_turnaware_long_v1.json](/home/void0312/Workshop/CMO/examples/config/Archive/training/pre_freeze_experiments/p2_autopilot_residual_navv2_paramroute_turnaware_long_v1.json)
- Training scenario:
  [cruise_waypoints_paramroute_navv2_train_v1.json](/home/void0312/Workshop/CMO/scenarios/cruise/cruise_waypoints_paramroute_navv2_train_v1.json)
- Cooperative training scenario:
  [cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json](/home/void0312/Workshop/CMO/scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json)
- Active cooperative training config:
  [cooperative_cruise_nav_v2_formation_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_cruise_nav_v2_formation_v1.json)
- Eval scenarios:
  [cruise_waypoints_stresswind_rewardbalance_v1.json](/home/void0312/Workshop/CMO/scenarios/cruise/cruise_waypoints_stresswind_rewardbalance_v1.json)
  [cruise_waypoints_ood_geometry_v1.json](/home/void0312/Workshop/CMO/scenarios/cruise/cruise_waypoints_ood_geometry_v1.json)
  [cruise_waypoints_ood_profile_v1.json](/home/void0312/Workshop/CMO/scenarios/cruise/cruise_waypoints_ood_profile_v1.json)
  [cruise_waypoints_ood_wind_v1.json](/home/void0312/Workshop/CMO/scenarios/cruise/cruise_waypoints_ood_wind_v1.json)

Status:

- Earlier cruise experiment outputs were cleaned from the active workspace.
- The dataset still retained for this line is
  [datasets/cruise_waypoints_full_visual_proprio_v1](/home/void0312/Workshop/CMO/datasets/cruise_waypoints_full_visual_proprio_v1).

## Takeoff

- Training scenario:
  [takeoff_stage1_runway45_stresswind.json](/home/void0312/Workshop/CMO/scenarios/takeoff/takeoff_stage1_runway45_stresswind.json)

Status:

- The previously referenced takeoff experiment output and training config were cleaned from the workspace.
- This line should now be treated as historical-only unless a new maintained config is reintroduced.

## Landing

- Maintained training config:
  [p4_landing_retrain_v1.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/p4_landing_retrain_v1.json)
- Historical artifact-provenance config:
  [p4_landing_full_visual_ils_smoke_v1.json](/home/void0312/Workshop/CMO/examples/config/Archive/training/pre_freeze_experiments/p4_landing_full_visual_ils_smoke_v1.json)
- Training scenario:
  [landing_ils_final_train_v1.json](/home/void0312/Workshop/CMO/scenarios/landing/landing_ils_final_train_v1.json)
- Eval scenario:
  [landing_ils_final_eval_v1.json](/home/void0312/Workshop/CMO/scenarios/landing/landing_ils_final_eval_v1.json)
- Archived landing smoke runs:
  [archive/20260317_landing_cleanup](/home/void0312/Workshop/CMO/archive/20260317_landing_cleanup)

Status:

- The older active landing smoke experiment directory was cleaned from the workspace.
- The retained landing archive remains the only surviving run-level provenance marker for this line.

## Continuous Takeoff-Cruise-Landing

- Maintained training config:
  [p5_continuous_retrain_v1.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/p5_continuous_retrain_v1.json)
- Historical artifact-provenance config:
  [p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json](/home/void0312/Workshop/CMO/examples/config/Archive/training/pre_freeze_experiments/p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json)
- Training scenario:
  [takeoff_to_landing_continuous_train_v1.json](/home/void0312/Workshop/CMO/scenarios/combined/takeoff_to_landing_continuous_train_v1.json)
- Eval scenario:
  [takeoff_to_landing_continuous_eval_v1.json](/home/void0312/Workshop/CMO/scenarios/combined/takeoff_to_landing_continuous_eval_v1.json)

Runtime note:

- The maintained training config keeps exact world stepping on CPU and uses
  `batch_observation_backend=compiled` and `batch_visual_backend=compiled`.
- The older mixed `gpu_host` visual line remains a diagnostics-only historical branch.

Latest retained diagnostics:

- Successful recovered seed:
  [model_gatefix_retrain_seed124.png](/home/void0312/Workshop/CMO/artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed124.png)
- Failure seed after retrain:
  [model_gatefix_retrain_seed125.png](/home/void0312/Workshop/CMO/artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed125.png)
- Reference gate-fix success before retrain:
  [model_seed123_gatefix_v2.png](/home/void0312/Workshop/CMO/artifacts/takeoff_to_landing_continuous/model_seed123_gatefix_v2.png)
- Remaining-failure repair marker before final retrain:
  [model_gatefix_retrain_seed126_v3.png](/home/void0312/Workshop/CMO/artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed126_v3.png)
- Active final-retrain success marker:
  [model_v3_retrain_seed126.png](/home/void0312/Workshop/CMO/artifacts/takeoff_to_landing_continuous/model_v3_retrain_seed126.png)

Status:

- The older active continuous experiment directory and model checkpoint were cleaned from the workspace.
- The maintained reference now lives at the config/scenario layer plus the retained diagnostics above.
