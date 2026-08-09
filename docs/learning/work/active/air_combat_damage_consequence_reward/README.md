# A2 Damage Consequence Reward Surface

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/learning/work/active/air_combat_damage_consequence_reward/README.md`
Owner: `learning/air-combat-reward`
Last verified: `2026-08-08`

Status: `2026-06-11` active A2 follow-on / DCR-A-D validated; DCR-E probe
export and diagnostics-only bridge are ready. The controlled fixed-fire bridge
reports release/effects/damage timing, but DCR totals remain zero because the
current damage report does not expose DCR-readable consequence fields. `DCR-E-R1`
re-scoped the next evidence step to a controlled consequence fixture probe;
DCR-E is still partial.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Learning owner: [../../../README.md](../../../README.md)
- A2 sealed package: [../../archive/a2_high_fidelity_damage_model/README.md](../../../../task/air_combat/archive/a2_high_fidelity_damage_model/README.md)
- A8 damage-effect chain: [../../archive/a8_damage_effect_chain/README.md](../../../../systems/effects/reviews/damage_effect_chain_20260608/README.md)
- Air execution owner: [../../../../domains/air/README.md](../../../../domains/air/README.md)
- Reward runtime entry: [../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py](../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py)
- Focused reward tests: [../../../../../tests/runtime/air_combat/test_air_combat_reward_surface.py](../../../../../tests/runtime/air_combat/test_air_combat_reward_surface.py)

## Purpose

Extend air-combat training feedback beyond `kill` or inactive target outcomes.
Higher-value training signal can come from what the shot actually caused:
mission-system loss, sensor/data-link degradation, mobility degradation, fuel
leak, fire growth, loss of control, severe ground impact, or crash.

This belongs under A2 rather than a new A9 because the first question is damage
model fidelity and consequence interpretation; reward design comes after that.
This follow-on consumes existing runtime consequences as training signal. It
does not reopen the sealed A2 archive package, declare stock AIM-120C / MQ-9
lethality authority, or promote A8's bounded damage-effect chain into real-world
weapon-outcome authority.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A2 high-fidelity damage model | archived / sealed | A2 archive retains research/candidate evidence | Does not release Pk, deterministic fuze, or stock weapon-outcome authority |
| A8 damage-effect chain | accepted bounded slice | Detonation can be inspected as concrete part damage and maintained-system response | Does not add direct crash rules, MQ-9 special kill rules, or debris/residue objects |
| Current training feedback | active extension | Nonterminal damage reports already provide one-shot system/capability/loss-state shaping; delayed fire, fuel, ground contact, crash, and aircraft internal consequences are being added as a bounded follow-on | Legacy `Health` or one `kill` flag must not be treated as the complete kill-chain evaluation |

## Scope

In scope:

- Maintain a task-cluster plan before runtime changes.
- Add configurable reward terms that read already observable damage consequences.
- Prefer delta/transition rewards for delayed consequences, so waiting beside a
  burning or crashed target is not rewarded repeatedly by default.
- Keep training synthetic reward calibration separate from real weapon/target
  authority.
- Preserve a minimal witness through unit tests, controlled kill-chain probes,
  and later Stage-2 training metrics.

Out of scope:

- No A9 creation.
- No reopening of the sealed A2 archive package.
- No real Pk, real fuze, real AIM-120C lethality, or MQ-9 special-kill claim.
- No direct-crash rule as a substitute for the damage chain.
- No training-speed work; multi-world scaling remains a separate performance
  topic.
- No acceptance claim until repeated training/evaluation evidence exists.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Idea Seed` | Freeze the location and boundary. | Current discussion. | This README exists and is linked from the A2 pointer. | pass |
| `P1 Boundary` | Define rewardable consequences, observable fields, and forbidden claims. | User asks to return to reward extension. | Task-cluster document exists. | pass |
| `P2 Runtime Surface` | Add bounded reward consumption of existing consequence state. | P1 boundary held. | Focused unit tests cover delta/transition semantics. | pass |
| `P3 Consequence Probe` | Prepare reporting for controlled kill-chain probes and future Stage-2 training consumers. | P2 tests pass. | Stage-2 opt-in exists and process probe can report consequence terms separately from firing terms. | partial |
| `P4 Closure` | Record accepted slice or residuals. | P3 evidence exists. | README/status and parent pointers are consistent. | planned |

## Task Clusters

- Task cluster plan:
  [damage_consequence_reward_surface_task_clusters_20260609.md](damage_consequence_reward_surface_task_clusters_20260609.md)
- Active dispatch queue:
  [damage_consequence_reward_surface_dispatch_queue_20260609.md](damage_consequence_reward_surface_dispatch_queue_20260609.md)

## Outputs And Evidence

- Active task-cluster plan for bounded reward extension.
- `gym_envs/scenario_loader/reward_runtime/air_combat.py` now has optional
  consequence-delta shaping for aircraft damage and severe ground-contact
  transitions.
- `tests/runtime/air_combat/test_air_combat_reward_surface.py` covers target
  progress, self penalty, no-repeat static damage, and safe-ground-contact
  refusal.
- `scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json`
  explicitly opts in low-weight consequence shaping for synthetic training
  feedback only.
- `tools/diagnostics/air_combat_weapon_employment_process_probe.py` can now export
  per-step and per-episode DCR reward totals by target/self prefix.
- `tools/diagnostics/air_combat_weapon_employment_process_probe.py --diagnostic_dcr_bridge`
  overlays DCR reward terms inside the diagnostics probe only and emits compact
  `controlled_consequence_bridge_records`; the current fixed-fire record still
  has `damage_consequence_reward_total=0.0`.
- On `2026-06-09`,
  `experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/final_model.zip`
  was used for a 2 episode x 512 step model-mode probe. The model kept radar and
  master arm enabled but never fired; release/effects/damage/DCR reward stayed
  at 0, so it is not consequence evidence.
- DCR-E-P2 is accepted only as an implementation bridge / blocker record, not
  as consequence evidence.
- DCR-E-R1 is accepted as read-only re-scope evidence. It recommends
  `DCR-E-P3 Controlled Consequence Fixture Probe` as the next implementation
  packet inside the existing DCR-E cluster.

## Acceptance Gate

This follow-on can be marked accepted only when:

- damage-consequence fields are stably observable and do not rely on legacy
  `Health` as the main truth;
- consequence reward weights do not encourage obvious simulation exploits;
- training synthetic calibration is kept separate from real weapon/target
  authority;
- sealed A2 and accepted A8 boundaries are not overclaimed;
- a controlled consequence-chain probe, replay artifact, or later Stage-2 run
  reports the new consequence terms separately from launch/firing terms.

## Residuals And Next Steps

- First slice: reward runtime reads aircraft damage and ground-contact debug
  state as configurable delta/transition shaping.
- Stage-2 now opts in with conservative weights as a future training consumer;
  the current candidate model does not fire, so it is not kill-chain evidence.
- Next evidence step: dispatch `DCR-E-P3 Controlled Consequence Fixture Probe`
  to produce a nonzero DCR-readable aircraft/ground consequence snapshot through
  the diagnostics/probe surface. Reward mapping from damage-report projections
  remains held as a separate semantic packet if fixture evidence cannot close
  the gap.
- Later: build a continuous consequence diagnostics table for mission, mobility,
  sensor, survivability, aircraft internal damage, fuel/fire, ground-contact
  lifecycle, and inactive transitions.

## Archive

Superseded planning records move under a local `archive/` directory only after a
replacement current-status or closeout surface exists.
