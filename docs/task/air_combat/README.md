# Air Combat

Status: active `1v1` workline; default entry converged on `2026-05-18`;
`2026-05-25` opened the staged `1v1` realism-gradient curriculum; `2026-06-03`
accepted the bounded A3 C2/ROE release-discipline layer. `2026-06-08` closes
A4-A7 as historical firing-learning lines, not as current blockers. The current
bounded firing gate is accepted by the model-side M3-S2 package after the A5
weapon-arm action-frame fix:
[../model/archive/m3_s2_fire_timing_learnability_audit/README.md](../model/archive/m3_s2_fire_timing_learnability_audit/README.md).
`2026-06-08` also accepted A8 for the bounded damage-effect-chain slice: missile
effects can now be inspected as concrete part damage and maintained-system
responses, while calibrated weapon truth, aircraft-specific control laws,
platform-family expansion, real-world lethality authority, and first-class
debris/residue objects remain separate follow-up work. On the same date, A1
added the Stage-2 C2/ROE training entry and completed the first 8k
init-from-Stage-1 short train. Single-seed deterministic/stochastic probes
preserved one authorized release, but had no effects/damage/kill, so Stage-2 is
still not accepted.

## Current Status

- Phase-1 `1v1` work has landed on the maintained `execution` / HMoE path.
- The current smoke baseline is `F-16C_Block50 vs F-16C_Block50` with a
  scripted red opponent and scenario-level ammo override.
- The missile launch bridge, minimal combat termination fields, and basic smoke
  training entry are all connected.
- In the `2026-05-24` 8k HMoE probe, early episodes were not dominated by
  `failfast_deep_stall`; termination concentrated on `combat_loss`.
- The old training-reachability blocker is no longer the current firing status.
  M3-S2 batch validation accepts the bounded firing gate for the active
  scenario/config pair: the learned policy requests and executes one authorized
  `fire_once` release with zero rejected requests, violations, or
  repeat-before-assessment releases.
- The first training entry should move to the staged curriculum under
  [a1_1v1_realism_gradient/README.md](a1_1v1_realism_gradient/README.md)
  instead of the historical smoke fixture.
- A1's current progression point is the Stage-2 C2/ROE maneuvering-target entry:
  [a1_stage2_c2_roe_entry_and_short_train_20260608.md](a1_1v1_realism_gradient/a1_stage2_c2_roe_entry_and_short_train_20260608.md).
  It runs, transfers one authorized release from the Stage-1 M3-S2 final model,
  and has one 8k short-train record; this is evidence for entering the next
  training stage, not Stage-2 outcome or batch firing acceptance.
- The repeated-launch issue routes through the accepted bounded
  C2/ROE layer in
  [a3_c2_roe_release_discipline/README.md](a3_c2_roe_release_discipline/README.md):
  policy-visible weapons-control status, target identity, fire authorization,
  single-shot-then-assess / salvo / reattack permission, and mission-observation
  constraints are wired. A3 remains the legality/discipline authority, not the
  current firing-closure package.
- Closed historical firing-learning line:
  [a4_authorized_first_shot_training_signal/README.md](a4_authorized_first_shot_training_signal/README.md):
  A4 is closed in place. Its retained conclusion is that reward shaping,
  routing, diagnostics, and an opportunity penalty did not solve firing.
- Closed historical structural event-action line:
  [a5_constrained_event_action_model/README.md](a5_constrained_event_action_model/README.md):
  A5 is closed in place. It contributed the constrained `hold/fire_once` surface
  and the later weapon-arm action-frame fix used by M3-S2.
- Closed historical first-event timing line:
  [a6_event_value_first_event_timing/README.md](a6_event_value_first_event_timing/README.md):
  A6 is closed in place. Its retained conclusion is that hazard/deadline/window
  labels exposed useful timing evidence but did not become the current firing
  authority.
- Closed historical event-credit/timing line:
  [a7_event_value_advantage_credit_head/README.md](a7_event_value_advantage_credit_head/README.md):
  A7 is closed in place. Its retained conclusion is that event-credit work is
  timing-quality research history, while current launch closure belongs to M3-S2.
- The high-fidelity damage-model line now has a lightweight pointer at
  [a2_high_fidelity_damage_model/README.md](a2_high_fidelity_damage_model/README.md);
  the full package lives under
  [archive/a2_high_fidelity_damage_model/](archive/a2_high_fidelity_damage_model/README.md).
  It is archived as a sealed research/candidate record: its
  structured-aircraft damage/effects runtime is on a maintained path, the
  blast-fragmentation package is accepted as non-authoritative evidence, and
  G4/G5 research packets are closed. Stock authority, Pk, and deterministic
  fuze authority are still not released.
- The A9 high-fidelity weapon system subproject has been created at
  [a9_high_fidelity_weapon_system/README.md](a9_high_fidelity_weapon_system/README.md).
  It upgrades six weapon subsystems (guidance, seeker, autopilot, fuze,
  aerodynamics, warhead) from engineering-proxy fidelity toward research-grade
  fidelity, while keeping all authority boundaries sealed. Status:
  `accepted_with_residuals` — 15 clusters pass, 3 open residuals, zero
  regressions vs main.
- The A8 damage-effect chain now has a lightweight pointer at
  [a8_damage_effect_chain/README.md](a8_damage_effect_chain/README.md); the
  full package lives under
  [archive/a8_damage_effect_chain/](archive/a8_damage_effect_chain/README.md).
  It is archived as an accepted bounded slice that turns detonation effects into
  concrete aircraft part damage and then routes those effects through existing
  propulsion, fuel, sensor, fire, and flight consumers. Accepted evidence covers
  propulsion, one wing/control aerodynamic response, fuel-leak/mass response,
  broader-fire consequence checks, data-link mission/sensor consequence, and a
  narrow ground-contact lifecycle state with debris/residue objects deferred.
  It still does not add a direct crash rule, special MQ-9 kill rule, Pk claim,
  deterministic fuze claim, or stock AIM-120C lethality claim.

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
- read
  [A8 damage-effect chain](a8_damage_effect_chain/README.md) as an archived
  accepted record for concrete damage propagation through maintained aircraft
  systems, without adding direct crash or special-target kill rules; reopen only
  for explicit calibration, platform expansion, or debris/residue object work
- preserve the non-authoritative boundary of the current blast-fragmentation
  candidate package; test-local descriptor exercises are not stock authority
- keep `2v2` and bilateral self-play out of scope until `1v1` metrics stabilize
- validate the staged `1v1` scenarios in
  `scenarios/air_combat/1v1/` from weapon employment through limited reciprocal
  weapons; the next immediate step is Stage-2 firing-retention batch validation,
  not Stage-3 or self-play
- treat A4-A7 as closed historical records; current launch closure is the M3-S2
  bounded firing gate, and new timing-quality work should open as a separate
  model follow-on

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
- A1 Stage-2 C2/ROE entry and short train:
  [a1_stage2_c2_roe_entry_and_short_train_20260608.md](a1_1v1_realism_gradient/a1_stage2_c2_roe_entry_and_short_train_20260608.md)
- C2/ROE release-discipline accepted layer:
  [a3_c2_roe_release_discipline/README.md](a3_c2_roe_release_discipline/README.md)
- Current bounded firing closure:
  [M3-S2 fire-timing learnability archive](../model/archive/m3_s2_fire_timing_learnability_audit/README.md)
- Closed historical firing-learning records:
  [a4_authorized_first_shot_training_signal/README.md](a4_authorized_first_shot_training_signal/README.md),
  [a5_constrained_event_action_model/README.md](a5_constrained_event_action_model/README.md),
  [a6_event_value_first_event_timing/README.md](a6_event_value_first_event_timing/README.md),
  and
  [a7_event_value_advantage_credit_head/README.md](a7_event_value_advantage_credit_head/README.md)
- A4 reward/routing evidence:
  [a4_authorized_first_shot_training_signal/README.md](a4_authorized_first_shot_training_signal/README.md)
  and reward evidence:
  [a4_authorized_first_shot_reward_probe_20260603.md](archive/a4_authorized_first_shot_training_signal/a4_authorized_first_shot_reward_probe_20260603.md)
  plus routing evidence:
  [a4_authorized_first_shot_routing_probe_20260603.md](archive/a4_authorized_first_shot_training_signal/a4_authorized_first_shot_routing_probe_20260603.md)
  and binary diagnostics:
  [a4_authorized_first_shot_binary_diagnostics_20260603.md](archive/a4_authorized_first_shot_training_signal/a4_authorized_first_shot_binary_diagnostics_20260603.md)
- High-fidelity damage-model sealed record:
  [a2_high_fidelity_damage_model/README.md](a2_high_fidelity_damage_model/README.md)
  and full archive
  [archive/a2_high_fidelity_damage_model/README.md](archive/a2_high_fidelity_damage_model/README.md)
- High-fidelity weapon system (new subproject):
  [a9_high_fidelity_weapon_system/README.md](a9_high_fidelity_weapon_system/README.md)
- Damage-effect chain follow-on:
  [a8_damage_effect_chain/README.md](a8_damage_effect_chain/README.md)
- High-fidelity damage-system baseline:
  [air_combat_damage_model_evaluation_20260522.md](../../forward/air_combat_damage_model_evaluation_20260522.md)

Historical dated snapshots now live under [archive/README.md](archive/README.md).
