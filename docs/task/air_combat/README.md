# Air Combat

Status: active `1v1` workline; default entry converged on `2026-05-18`.

## Current Status

- Phase-1 `1v1` work has landed on the maintained `execution` / HMoE path.
- The current baseline is `F-16C_Block50 vs F-16C_Block50` with a scripted red
  opponent and scenario-level ammo override.
- The missile launch bridge, minimal combat termination fields, and basic smoke
  training entry are all connected.
- In the `2026-05-24` 8k HMoE probe, early episodes were not dominated by
  `failfast_deep_stall`; termination concentrated on `combat_loss`.
- The main blocker is still training-signal quality rather than entry wiring:
  the `combat_loss` plus `crash_penalty` terminal combination, ammo-depletion
  warnings, invalid entity ID warnings, and HMoE routing still concentrated on
  `nav/vector` under `mission_obs_mode=basic`.

## Active Follow-On Focus

- tighten early-flight stability and action-surface protection for `1v1`
- freeze a dedicated `1v1` eval JSON schema and maintained eval entry
- refine reward and termination shaping beyond the minimum win/loss hooks
- strengthen scripted or frozen-opponent baselines
- split diagnostics for `combat_loss`, killed-entity inactive state, and terminal
  crash penalty semantics
- keep `2v2` and bilateral self-play out of scope until `1v1` metrics stabilize

## Recommended Reading Order

- Scope and first-phase boundary:
  [air_combat_1v1_entry_analysis_20260516.md](archive/air_combat_1v1_entry_analysis_20260516.md)
- Execution freeze:
  [air_combat_1v1_freeze_plan_20260516.md](archive/air_combat_1v1_freeze_plan_20260516.md)
- Landed baseline and weapon path:
  [air_combat_1v1_f16c_baseline_progress_20260516.md](archive/air_combat_1v1_f16c_baseline_progress_20260516.md),
  [air_combat_1v1_weapon_chain_progress_20260516.md](archive/air_combat_1v1_weapon_chain_progress_20260516.md),
  [air_combat_scenario_level_ammo_design_20260516.md](archive/air_combat_scenario_level_ammo_design_20260516.md)
- Training signal and current blocker:
  [air_combat_1v1_training_smoke_progress_20260516.md](archive/air_combat_1v1_training_smoke_progress_20260516.md),
  [air_combat_1v1_stall_rootcause_followup_20260516.md](archive/air_combat_1v1_stall_rootcause_followup_20260516.md)

Historical dated snapshots now live under [archive/README.md](archive/README.md).
