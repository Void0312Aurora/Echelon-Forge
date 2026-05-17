# Active Training Entries

This directory holds maintained in-progress training configs that are not frozen yet.

Status for this directory is `Active Mainline`.

## Cooperative Cruise Line

- [cooperative_cruise_nav_v2_formation_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_cruise_nav_v2_formation_v1.json)
  - Single-policy cruise baseline for the current P8 cooperative-execution line.
  - Uses `nav_v2_formation_role_v1` so the policy can receive formation and role/reference semantics from the mission command chain.
  - Scenario pairing is `scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json`, with a true cooperative roster and formation offsets carried in the mission command instead of adding a synthetic policy-only input family.

## Cooperative Takeoff Line

- [cooperative_interval_takeoff_departure_nav_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_interval_takeoff_departure_nav_v1.json)
  - First-stage dual-ship interval takeoff/departure baseline for cooperative execution.
  - Uses `nav_v2_cooperative_takeoff_v1` so each slot receives takeoff procedure, clearance, interval, runway slot, and roster semantics through the maintained mission-command chain.
  - Scenario pairing is `scenarios/takeoff/cooperative_interval_takeoff_departure_navv2_train_v1.json`.

- [cooperative_takeoff_to_cruise_nav_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_takeoff_to_cruise_nav_v1.json)
  - Second-stage dual-ship cooperative bridge baseline: interval takeoff, departure climb, then multileg route capture.
  - Keeps the same `nav_v2_cooperative_takeoff_v1` observation contract so takeoff semantics and roster/formation semantics remain visible while the mission command already carries the cruise route.
  - Scenario pairing is `scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json`.

- [cooperative_takeoff_to_cruise_landing_nav_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_takeoff_to_cruise_landing_nav_v1.json)
  - Third-stage dual-ship cooperative closed-loop baseline: interval takeoff, structured cruise/return, then individual ILS landing on the home field.
  - Keeps the same `nav_v2_cooperative_takeoff_v1` observation contract so roster, takeoff, and formation semantics remain visible while the maintained mission command chain carries the return route and landing transition.
  - The landing segment now re-opens a small residual budget over the scripted `landing_ils` baseline so the policy can correct final/rollout errors instead of being hard-clamped to pure scripted landing.
  - Scenario pairing is `scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json`.

- [cooperative_takeoff_to_cruise_nav_hmoe_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_takeoff_to_cruise_nav_hmoe_v1.json)
  - HMoE experiment entry for the same takeoff-to-cruise bridge, using `HierarchicalMoEExecutionPolicy` with a shared backbone, shared action head baseline, and semantically routed residual experts.
  - Keeps the same `nav_v2_cooperative_takeoff_v1` observation contract and still follows the realistic input boundary: only maintained pilot-receivable mission semantics are exposed to the policy.
  - Scenario pairing remains `scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json`, so baseline vs HMoE stays directly comparable.

- [cooperative_takeoff_to_cruise_nav_shared_fair_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_takeoff_to_cruise_nav_shared_fair_v1.json)
  - Fair-control shared baseline for continuing the takeoff-to-cruise HMoE comparison.
  - Aligns curriculum, wrappers, runtime, diagnostics, and optimizer-side KL controls with the HMoE line so the main difference stays at the policy architecture boundary.

- [cooperative_takeoff_to_cruise_nav_hmoe_fair_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_takeoff_to_cruise_nav_hmoe_fair_v1.json)
  - Paired HMoE config for the same fair-control line.
  - Use this pair when you want a stricter shared-vs-HMoE A/B comparison than the earlier exploratory configs.

## Air Combat 1v1 Line

- [air_combat/README.md](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/README.md)
  - Maintained `1v1` execution-layer HMoE entries for the current air-combat line.
  - Keeps the first opponent frozen as a scenario-declared scripted red fighter, so we can validate the combat task contract and HMoE runtime chain before moving to self-play or `2v2`.

## Notes

- This is the current forward-moving training line, not a frozen acceptance set.
- Keep the entry realistic: only fields a pilot can receive belong in policy-facing inputs.
- Do not promote this config into `frozen/` until the cooperative execution path and scenario contract are stable.
- The cooperative cruise line is an opt-in cooperative benchmark line, alongside the frozen leader/execution baselines.
- For direct HMoE control experiments on the cooperative takeoff-to-cruise bridge, prefer the `*_shared_fair_v1` and `*_hmoe_fair_v1` pair so non-policy hyperparameters stay aligned.
- Do not point active configs at `examples/config/Archive/**`; if an older setup is still needed for maintained use, re-express it under `frozen/` or another maintained compatibility location first.
