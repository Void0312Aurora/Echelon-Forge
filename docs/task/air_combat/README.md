# Air Combat

Status: active `1v1` workline; default entry converged on `2026-05-18`;
`2026-05-25` opened the staged `1v1` realism-gradient curriculum; `2026-06-03`
accepted the bounded A3 C2/ROE release-discipline layer with M2 still held.

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
- The repeated-launch issue now routes first through the accepted bounded
  C2/ROE layer in
  [a3_c2_roe_release_discipline/README.md](a3_c2_roe_release_discipline/README.md):
  policy-visible weapons-control status, target identity, fire authorization,
  single-shot-then-assess / salvo / reattack permission, and mission-observation
  constraints are wired. P4 probes can split authorized release from violation
  release. The `2026-06-03` 32k A3 learned-policy probe shows that the
  deterministic model does not fire and stochastic probing still produces
  violation releases; post-launch mission observation now dynamically exposes
  `shot_budget_remaining=0` / `pending_assessment=1`, but learned-policy weapon
  employment and M2 release remain held.
- The high-fidelity damage-model line now has a lightweight pointer at
  [a2_high_fidelity_damage_model/README.md](a2_high_fidelity_damage_model/README.md);
  the full package lives under
  [archive/a2_high_fidelity_damage_model/](archive/a2_high_fidelity_damage_model/README.md).
  It is archived as a sealed research/candidate record: its
  structured-aircraft damage/effects runtime is on a maintained path, the
  blast-fragmentation package is accepted as non-authoritative evidence, and
  G4/G5 research packets are closed. Stock authority, Pk, and deterministic
  fuze authority are still not released.

## Active Follow-On Focus

- tighten early-flight stability and action-surface protection for `1v1`
- freeze a dedicated `1v1` eval JSON schema and maintained eval entry
- refine reward and termination shaping beyond the minimum win/loss hooks
- strengthen scripted or frozen-opponent baselines
- split diagnostics for `combat_loss`, killed-entity inactive state, and terminal
  crash penalty semantics
- treat the A2 high-fidelity air-combat damage model as a sealed retained
  record; only explicit follow-on requests should open `G4/G5 authority` or new
  research expansion work
- preserve the non-authoritative boundary of the current blast-fragmentation
  candidate package; test-local descriptor exercises are not stock authority
- keep `2v2` and bilateral self-play out of scope until `1v1` metrics stabilize
- validate the staged `1v1` scenarios in
  `scenarios/air_combat/1v1/` from weapon employment through limited reciprocal
  weapons
- run reactive/temporal learned-policy comparison against the A3 C2/ROE probe
  config after the dynamic post-launch observation fix; do not release M2 from
  process-probe classification or a single failed 32k learned-policy run alone

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
- C2/ROE release-discipline accepted layer:
  [a3_c2_roe_release_discipline/README.md](a3_c2_roe_release_discipline/README.md)
- High-fidelity damage-model sealed record:
  [a2_high_fidelity_damage_model/README.md](a2_high_fidelity_damage_model/README.md)
  and full archive
  [archive/a2_high_fidelity_damage_model/README.md](archive/a2_high_fidelity_damage_model/README.md)
- High-fidelity damage-system baseline:
  [air_combat_damage_model_evaluation_20260522.md](../../forward/air_combat_damage_model_evaluation_20260522.md)

Historical dated snapshots now live under [archive/README.md](archive/README.md).
