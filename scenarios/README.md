# Scenarios README

`scenarios/` stores canonical mission/scenario JSON files grouped by task domain instead of mixing every variant at the top level.

Maintained configs, tools, and tests should continue to reference canonical scenarios with repo-relative `scenarios/...` paths. `examples/scenarios/` is reserved for lightweight example fixtures unless a future migration adds compatibility for both locations and updates all references deliberately.

`scenarios/` is part of the maintained repository input surface and is expected to stay versioned in git. This differs from `experiments/`, `datasets/`, and `output/`, which remain runtime/artifact workspaces and are ignored by default.

## Layout

- `scenarios/takeoff/`
  - Runway takeoff, departure, and ground-roll focused tasks.
- `scenarios/stable_flight/`
  - Airborne hold and command-tracking tasks for heading, altitude, and speed stabilization.
- `scenarios/cruise/`
  - Waypoint-navigation and cruise-route tasks, including OOD evaluation variants.
- `scenarios/air_combat/`
  - Early `1v1` air-combat bootstrap fixtures and maintained combat-task smoke scenarios.
- `scenarios/naval/`
  - Maintained naval bootstrap fixtures focused on ship spawning, escort geometry, contact management, and future surface-warfare regression coverage.
- `scenarios/ground/`
  - Maintained ground bootstrap fixtures focused on tasking-chain smoke coverage before real ground platform/runtime behavior exists.
- `scenarios/landing/`
  - Landing-specific tasks such as ILS final and rollout evaluation.
- `scenarios/combined/`
  - Multi-phase missions that bridge takeoff, cruise, and landing in one scenario.
- `scenarios/templates/`
  - Generic scenario templates for authoring new tasks.
- `scenarios/test/`
  - Lightweight kernel or physics validation scenarios that are not training tasks.

## Naming Guidance

- Keep the existing scenario filename when moving it between category folders.
- Prefer putting new scenarios under the task domain they primarily evaluate.
- Use `combined/` when a mission intentionally spans multiple operational phases.
- Reserve `test/` for minimal validation scenarios rather than train/eval content.

## Maintenance Notes

- Update all script, contract, and artifact references when moving a scenario.
- Prefer referencing scenarios with full repo-relative paths such as `scenarios/combined/takeoff_to_landing_continuous_eval_v1.json`.
- Keep artifact-local OOD scenarios under `artifacts/.../ood_scenarios/` when they are generated experiment inputs rather than canonical shared scenarios.

## Retention Policy

- `scenarios/` should keep only canonical maintained tasks, active regression fixtures, and historical scenarios that are still referenced by maintained docs or frozen artifact manifests.
- Do not keep one-off tuning variants here once they are no longer the maintained train/eval entry, not covered by a contract, and not needed for artifact provenance.
- When a scenario is superseded by a newer canonical variant, update references first and then remove the stale file instead of letting multiple near-duplicate entrypoints accumulate.
- If a scenario is needed only for one experiment directory or generated OOD batch, keep it near that artifact lineage and record the retained path in documentation rather than promoting it into `scenarios/`.

## Maintained Canonical Set

- `takeoff/`
  - `takeoff.json`
  - `takeoff_stage1.json`
  - `takeoff_stage1_runway45.json`
  - `takeoff_stage1_runway45_stresswind.json`
  - `cooperative_interval_takeoff_departure_navv2_train_v1.json`
- `stable_flight/`
  - `stable_flight.json`
  - `stable_flight_stresswind.json`
  - `stable_flight_stresswind_rewardbalance_v3.json`
- `cruise/`
  - `cruise_waypoints_paramroute_navv2_train_v1.json`
  - `cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json`
  - `cruise_waypoints_stresswind_rewardbalance_v1.json`
  - `cruise_waypoints_ood_geometry_v1.json`
  - `cruise_waypoints_ood_profile_v1.json`
  - `cruise_waypoints_ood_wind_v1.json`
- `air_combat/`
  - `air_combat_1v1_headon_sensor_smoke_v1.json`
    - Canonical symmetric `F-16C_Block50 vs F-16C_Block50` `1v1` bootstrap fixture with scenario-level ammo overrides and minimal kill-objective termination.
- `naval/`
  - `ddg51_take1_screen_contact_report_v1.json`
- `ground/`
  - `ground_platoon_tasking_smoke_v1.json`
    - Minimal Army/ground tasking smoke fixture. It uses the current runtime-compatible `Aircraft` spawn shell and validates only the shared loader plus `TaskOrder -> LeaderIntent -> PilotReport` status chain.
- `landing/`
  - `landing_ils_final_train_v1.json`
  - `landing_ils_final_eval_v1.json`
- `combined/`
  - `cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json`
  - `cooperative_takeoff_to_cruise_landing_continuous_train_v1.json`
  - `cooperative_takeoff_to_cruise_landing_continuous_eval_v1.json`
  - `cruise_to_landing_continuous_train_v1.json`
  - `takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
  - `takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json`
  - `takeoff_to_cruise_paramroute_navv2_multileg_eval_v1.json`
  - `takeoff_to_cruise_paramroute_navv2_train_v1.json`
  - `takeoff_to_landing_c2_task_demo_fasttrain_v1.json`
  - `takeoff_to_landing_c2_task_demo_v1.json`
  - `takeoff_to_landing_c2_task_only_demo_v1.json`
  - `takeoff_to_landing_c2_task_only_train_v1.json`
  - `takeoff_to_landing_continuous_train_v1.json`
  - `takeoff_to_landing_continuous_eval_v1.json`
- `test/`
  - `test_aero.json`
    - Minimal airborne aerodynamics fixture with explicit zero wind so kernel realism checks stay isolated from scenario-default wind behavior.
  - `test_free_fall.json`
    - Minimal zero-velocity airborne fixture with explicit zero wind for gravity-dominant plausibility checks.
- `templates/`
  - `template.json`
