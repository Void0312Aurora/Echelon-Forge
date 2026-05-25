# Air Combat

Status: active `1v1` workline; default entry converged on `2026-05-18`;
`2026-05-25` opened the staged `1v1` realism-gradient curriculum.

## Current Status

- Phase-1 `1v1` work has landed on the maintained `execution` / HMoE path.
- The current smoke baseline is `F-16C_Block50 vs F-16C_Block50` with a
  scripted red opponent and scenario-level ammo override.
- The missile launch bridge, minimal combat termination fields, and basic smoke
  training entry are all connected.
- In the `2026-05-24` 8k HMoE probe, early episodes were not dominated by
  `failfast_deep_stall`; termination concentrated on `combat_loss`.
- The main blocker is now training reachability rather than entry wiring:
  weapon switch actions start effectively unreachable, the smoke red fighter
  opens fire immediately, and HMoE routing still concentrates on `nav/vector`
  under `mission_obs_mode=basic`.
- The first training entry should move to the staged curriculum under
  [a1_1v1_realism_gradient/README.md](a1_1v1_realism_gradient/README.md)
  instead of the historical smoke fixture.

## Active Follow-On Focus

- tighten early-flight stability and action-surface protection for `1v1`
- freeze a dedicated `1v1` eval JSON schema and maintained eval entry
- refine reward and termination shaping beyond the minimum win/loss hooks
- strengthen scripted or frozen-opponent baselines
- split diagnostics for `combat_loss`, killed-entity inactive state, and terminal
  crash penalty semantics
- promote the high-fidelity air-combat damage model: remove the HP-first kill
  bypass from the authoritative effects path, and make kill states derive from
  weapon events, local subsystem damage, and platform loss state
- close the Phase 0 damage-model preflight gates before any Phase 1 code move
  lands
- keep `2v2` and bilateral self-play out of scope until `1v1` metrics stabilize
- validate the staged `1v1` scenarios in
  `scenarios/air_combat/1v1/` from weapon employment through limited reciprocal
  weapons

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
- Current staged curriculum:
  [a1_1v1_realism_gradient/README.md](a1_1v1_realism_gradient/README.md)
- High-fidelity damage-system baseline:
  [air_combat_damage_model_evaluation_20260522.md](../../forward/air_combat_damage_model_evaluation_20260522.md)

Historical dated snapshots now live under [archive/README.md](archive/README.md).
