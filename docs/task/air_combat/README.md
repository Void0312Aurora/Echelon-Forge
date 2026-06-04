# Air Combat

Status: active `1v1` workline; default entry converged on `2026-05-18`;
`2026-05-25` opened the staged `1v1` realism-gradient curriculum; `2026-06-03`
accepted the bounded A3 C2/ROE release-discipline layer with M2 still held.
`2026-06-03` also opened A4 as the authorized-first-shot training-signal
follow-on; after A4 reward/routing evidence remained held, A5 opened the
constrained event-action model track and is now held after short learned-policy
evidence. A6 has completed its first event-value / first-event timing evidence
wave, deadline-bootstrap re-scope wave, event-head update-strength audit, and
event-head optimization learned evidence; it remains held on launch-window
timing quality. `2026-06-04` opened A7 as the counterfactual event-value /
advantage-credit head follow-on; its policy-head prototype and focused PPO
auxiliary-credit integration are now complete, with config/diagnostics next.

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
  `shot_budget_remaining=0` / `pending_assessment=1`. The post-fix
  reactive/temporal comparison shows temporal stochastic probing can remove
  violation releases, but deterministic weapon employment still does not fire;
  M2 release remains held.
- The immediate follow-on was
  [a4_authorized_first_shot_training_signal/README.md](a4_authorized_first_shot_training_signal/README.md):
  reward shaping and policy-routing evidence must make an authorized first shot
  trainable before M2 is reconsidered. The first A4 reward-side probe shows
  once-per-episode weapon-chain shaping is not enough: deterministic still does
  not fire, while stochastic probing still produces violation releases. The
  subsequent routing probe adds an explicit `combat_weapons` HMoE family.
  The retained routed 32k evidence modestly improves stochastic discipline
  but still leaves deterministic at 0 fire/release. A naive A4-only
  pulse-prior relaxation was tested and rejected because it increased violation
  releases without making deterministic policy fire. Binary diagnostics then
  showed authorized-window `fire_weapon` remains near `0.22%` probability /
  `-6.11` max logit; a bounded fire-opportunity penalty trial was also rejected
  because it did not move deterministic fire and worsened stochastic release
  discipline. A4 is therefore held as evidence that reward/routing repair is
  not the root fix.
- The active model-level follow-on is
  [a5_constrained_event_action_model/README.md](a5_constrained_event_action_model/README.md):
  convert weapon release from a per-step binary/threshold control into a
  constrained event action with explicit engagement state, action mask,
  `hold/fire_once` semantics, post-launch `FiredAssess` suppression, and an
  explicit reattack gate. The A5 short learned-policy probe fixes stochastic
  release discipline to one authorized release per episode with no violations,
  but deterministic policy still makes zero `fire_once` requests. A5 remains
  held; the next fix should target event-value / first-event timing rather than
  reward-only legality tuning. M2 remains held.
- The new follow-on is
  [a6_event_value_first_event_timing/README.md](a6_event_value_first_event_timing/README.md):
  the first masked first-event hazard / bounded curriculum implementation now
  has live PPO labels and diagnostics, but short learned evidence still leaves
  deterministic policy at `0` `fire_once` requests with event probability near
  `0.25%`. The deadline-bootstrap re-scope then doubles deterministic
  open-window probability to about `0.49%`, but deterministic requests remain
  `0`; stochastic probing keeps `3/3` authorized releases and zero
  violation/repeat/budget issues, with one `weapon_not_ready` rejected request.
  The event-head update audit then shows A6 gradients are live but current
  optimizer/head scaling leaves the event delta near `-5`. The bounded
  event-head lane fixes that narrow blocker: deterministic probing now executes
  one authorized release, and stochastic probing preserves `3/3` one-shot
  authorized releases with zero rejected/violation/repeat/budget issues. A6 is
  still held because release timing collapses to near-immediate
  authorization/contact. The launch-window contract then suppressed early
  deterministic fire without producing accepted timing, and the root-cause
  re-scope assigns the current blocker to on-policy first-event censoring plus
  missing counterfactual hold/fire credit. The active follow-on is
  [a7_event_value_advantage_credit_head/README.md](a7_event_value_advantage_credit_head/README.md).
- A7
  [event-value / advantage-credit head](a7_event_value_advantage_credit_head/README.md)
  is now the implementation line for the first-event timing residual: the
  policy-level event-credit head API and focused PPO auxiliary-credit loss are
  in place, while active config, callback/process-probe diagnostics, cumulative
  early-fire diagnostics, and learned evidence remain the next implementation
  work. A3/A5 legality stays authoritative, and HMoE redesign/M2 remain held.
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
- advance
  [A7 event-value / advantage-credit head](a7_event_value_advantage_credit_head/README.md)
  through config/diagnostics and focused validation before any new
  learned-policy probe or M2 reconsideration

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
- Authorized first-shot training-signal follow-on:
  [a4_authorized_first_shot_training_signal/README.md](a4_authorized_first_shot_training_signal/README.md)
  and reward evidence:
  [a4_authorized_first_shot_reward_probe_20260603.md](a4_authorized_first_shot_training_signal/a4_authorized_first_shot_reward_probe_20260603.md)
  plus routing evidence:
  [a4_authorized_first_shot_routing_probe_20260603.md](a4_authorized_first_shot_training_signal/a4_authorized_first_shot_routing_probe_20260603.md)
  and binary diagnostics:
  [a4_authorized_first_shot_binary_diagnostics_20260603.md](a4_authorized_first_shot_training_signal/a4_authorized_first_shot_binary_diagnostics_20260603.md)
- Constrained event-action model follow-on:
  [a5_constrained_event_action_model/README.md](a5_constrained_event_action_model/README.md)
- Event-value / first-event timing follow-on:
  [a6_event_value_first_event_timing/README.md](a6_event_value_first_event_timing/README.md)
- Event-value / advantage-credit head implementation contract:
  [a7_event_value_advantage_credit_head/README.md](a7_event_value_advantage_credit_head/README.md)
- High-fidelity damage-model sealed record:
  [a2_high_fidelity_damage_model/README.md](a2_high_fidelity_damage_model/README.md)
  and full archive
  [archive/a2_high_fidelity_damage_model/README.md](archive/a2_high_fidelity_damage_model/README.md)
- High-fidelity damage-system baseline:
  [air_combat_damage_model_evaluation_20260522.md](../../forward/air_combat_damage_model_evaluation_20260522.md)

Historical dated snapshots now live under [archive/README.md](archive/README.md).
