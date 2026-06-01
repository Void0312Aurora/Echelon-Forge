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
  [p3_takeoff_to_cruise_retrain_v1.json](../examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json)
- Historical artifact-provenance config:
  [p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json](../examples/config/Archive/training/pre_freeze_experiments/p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json)
- Training scenario:
  [takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json](../scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json)
- Eval scenario:
  [takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json](../scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json)

Status:

- Historical bridge experiment outputs were cleaned from the active workspace.
- Use the maintained config and scenarios above as the surviving reference entrypoints.

## Cruise

- Maintained execution config used for the historical bridge/cruise lineage:
  [p3_takeoff_to_cruise_retrain_v1.json](../examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json)
- Historical artifact-provenance config:
  [p2_autopilot_residual_navv2_paramroute_turnaware_long_v1.json](../examples/config/Archive/training/pre_freeze_experiments/p2_autopilot_residual_navv2_paramroute_turnaware_long_v1.json)
- Training scenario:
  [cruise_waypoints_paramroute_navv2_train_v1.json](../scenarios/cruise/cruise_waypoints_paramroute_navv2_train_v1.json)
- Cooperative training scenario:
  [cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json](../scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json)
- Active cooperative training config:
  [cooperative_cruise_nav_v2_formation_v1.json](../examples/config/training/active/cooperative_cruise_nav_v2_formation_v1.json)
- Eval scenarios:
  [cruise_waypoints_stresswind_rewardbalance_v1.json](../scenarios/cruise/cruise_waypoints_stresswind_rewardbalance_v1.json)
  [cruise_waypoints_ood_geometry_v1.json](../scenarios/cruise/cruise_waypoints_ood_geometry_v1.json)
  [cruise_waypoints_ood_profile_v1.json](../scenarios/cruise/cruise_waypoints_ood_profile_v1.json)
  [cruise_waypoints_ood_wind_v1.json](../scenarios/cruise/cruise_waypoints_ood_wind_v1.json)

Status:

- Earlier cruise experiment outputs were cleaned from the active workspace.
- The dataset still retained for this line is
  `datasets/cruise_waypoints_full_visual_proprio_v1`, if retained outside the
  active workspace.

## Takeoff

- Maintained frozen execution config:
  [p2_takeoff_retrain_v1.json](../examples/config/training/frozen/execution/p2_takeoff_retrain_v1.json)
- Training scenario:
  [takeoff_stage1_runway45_stresswind.json](../scenarios/takeoff/takeoff_stage1_runway45_stresswind.json)

Status:

- The previously referenced takeoff experiment output was cleaned from the workspace.
- The surviving maintained reference is the frozen execution `p2` config plus the canonical takeoff scenarios under `scenarios/takeoff/`.

## Landing

- Maintained training config:
  [p4_landing_retrain_v1.json](../examples/config/training/frozen/execution/p4_landing_retrain_v1.json)
- Historical artifact-provenance config:
  [p4_landing_full_visual_ils_smoke_v1.json](../examples/config/Archive/training/pre_freeze_experiments/p4_landing_full_visual_ils_smoke_v1.json)
- Training scenario:
  [landing_ils_final_train_v1.json](../scenarios/landing/landing_ils_final_train_v1.json)
- Eval scenario:
  [landing_ils_final_eval_v1.json](../scenarios/landing/landing_ils_final_eval_v1.json)
- Archived landing smoke runs:
  `archive/20260317_landing_cleanup`, if retained outside the active workspace.

Status:

- The older active landing smoke experiment directory was cleaned from the workspace.
- The retained landing archive remains the only surviving run-level provenance marker for this line.

## Continuous Takeoff-Cruise-Landing

- Maintained training config:
  [p5_continuous_retrain_v1.json](../examples/config/training/frozen/execution/p5_continuous_retrain_v1.json)
- Maintained cold-start/full-route config:
  [p5_continuous_coldstart_retrain_v2.json](../examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json)
- Historical artifact-provenance config:
  [p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json](../examples/config/Archive/training/pre_freeze_experiments/p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json)
- Training scenario:
  [takeoff_to_landing_continuous_train_v1.json](../scenarios/combined/takeoff_to_landing_continuous_train_v1.json)
- Eval scenario:
  [takeoff_to_landing_continuous_eval_v1.json](../scenarios/combined/takeoff_to_landing_continuous_eval_v1.json)

Runtime note:

- The maintained training config keeps exact world stepping on CPU and uses
  `batch_observation_backend=compiled` and `batch_visual_backend=compiled`.
- The older mixed `gpu_host` visual line remains a diagnostics-only historical branch.

Latest retained diagnostics:

- Successful recovered seed:
  `artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed124.png`, if retained outside the active workspace.
- Failure seed after retrain:
  `artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed125.png`, if retained outside the active workspace.
- Reference gate-fix success before retrain:
  `artifacts/takeoff_to_landing_continuous/model_seed123_gatefix_v2.png`, if retained outside the active workspace.
- Remaining-failure repair marker before final retrain:
  `artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed126_v3.png`, if retained outside the active workspace.
- Active final-retrain success marker:
  `artifacts/takeoff_to_landing_continuous/model_v3_retrain_seed126.png`, if retained outside the active workspace.

Status:

- The older active continuous experiment directory and model checkpoint were cleaned from the workspace.
- The maintained reference now lives at the config/scenario layer plus the retained diagnostics above.

## Active Cooperative / Combined Mainline

- Maintained active index:
  [examples/config/training/active/README.md](../examples/config/training/active/README.md)
- Config families:
  cooperative cruise, cooperative interval takeoff/departure, cooperative takeoff-to-cruise, cooperative takeoff-cruise-landing, and `p4b` cruise-to-landing reopen entries under `examples/config/training/active/`.
- Scenario families:
  [scenarios/cruise](../scenarios/README.md), [scenarios/takeoff](../scenarios/README.md), and [scenarios/combined](../scenarios/README.md).

Status:

- These entries are active forward-moving lanes, not frozen acceptance artifacts.
- The cooperative/HMoE A/B controls are documented in the active README; configs do not embed a universal `scenario_path`, so launch commands still provide the scenario explicitly.

## Air Combat 1v1 Active Probes

- Maintained active index:
  [examples/config/training/active/air_combat/README.md](../examples/config/training/active/air_combat/README.md)
- Scripted-red smoke/probe scenario:
  [air_combat_1v1_headon_sensor_smoke_v1.json](../scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)
- Stage-0 drone probe scenario:
  [air_combat_1v1_stage0_drone_weapon_employment_v1.json](../scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json)
- Runtime evidence:
  [test_air_combat_1v1_fixture.py](../tests/runtime/air_combat/test_air_combat_1v1_fixture.py)

Status:

- The active `1v1` configs are HMoE execution probes and smoke entries, not frozen baselines or self-play evidence.
- Stage-1 through Stage-3 `scenarios/air_combat/1v1` files are maintained curriculum scenarios, but no active training config is paired to them yet.

## Naval N4 Active Gate

- Maintained active index:
  [examples/config/training/active/naval/README.md](../examples/config/training/active/naval/README.md)
- Active configs:
  `naval_contact_report_threat_roe_smoke_v1.json`,
  `naval_screen_station_hold_threat_aware_smoke_v1.json`, and
  `naval_screen_station_recovery_threat_aware_smoke_v1.json`.
- Scenarios:
  [ddg51_take1_screen_threat_roe_v1.json](../scenarios/naval/ddg51_take1_screen_threat_roe_v1.json) and
  [ddg51_take1_screen_threat_roe_offstation_recovery_v1.json](../scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json).
- Contracts:
  [naval_screen_threat_roe_geometry.json](../tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json) and
  [naval_screen_threat_roe_offstation_recovery.json](../tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json).
- Eval/test evidence:
  [test_eval_naval_n4_baseline.py](../tests/eval/test_eval_naval_n4_baseline.py) and
  [test_naval_active_training_entries.py](../tests/training/test_naval_active_training_entries.py).

Status:

- This is an accepted pre-fire/tasking/contact gate only.
- It does not expose weapon release, damage, kill rewards, or trained naval-policy claims.

## Ground Bootstrap

- Scenario fixtures:
  [ground_platoon_tasking_smoke_v1.json](../scenarios/ground/ground_platoon_tasking_smoke_v1.json),
  [ground_platoon_static_occupy_v1.json](../scenarios/ground/ground_platoon_static_occupy_v1.json), and
  [ground_platoon_support_relationship_v1.json](../scenarios/ground/ground_platoon_support_relationship_v1.json).
- Native schema evidence:
  [ground_platoon_mvp.json](../examples/config/database/ground/units/ground_platoon_mvp.json) and
  [CAPABILITY_NOTE.md](../examples/config/database/ground/units/CAPABILITY_NOTE.md).
- Runtime/contract evidence:
  [tests/runtime/ground](../tests/runtime/ground) and
  [tests/contracts/unit/ground](../tests/contracts/unit/ground).

Status:

- Ground is not an active RL training line yet.
- Current evidence is limited to tasking/common-core, native platform-schema/bootstrap, and lifecycle bridge coverage. Movement, terrain, sensing, fires, damage, and full ground runtime behavior remain held.
