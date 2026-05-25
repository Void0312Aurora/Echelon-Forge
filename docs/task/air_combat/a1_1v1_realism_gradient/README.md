# A1 1v1 Realism Gradient

Status: opened on `2026-05-25` to replace the single hard `1v1` smoke entry
with a staged air-combat training curriculum.

## Purpose

The current `F-16C_Block50 vs F-16C_Block50` scripted-red smoke fixture proves
that the weapon bridge and combat terminal hooks are connected, but it is too
steep for first RL training:

- the HMoE policy starts with radar and weapon switch actions near zero, making
  `master_arm` plus `fire_weapon` effectively unreachable under early PPO
  exploration;
- the scripted red fighter starts inside its `9000 m` fire window and can fire
  immediately;
- even forced blue weapon release does not reliably produce a win before red's
  shots kill blue.

This subproject defines a four-stage curriculum that increases realism only
when the previous learning loop is reachable and measurable.

## Four Stages

### Stage 0: Weapon Employment On A Flying Drone

Goal: make the fire chain reachable.

Scenario shape:

- blue F-16C starts airborne with authorization to fire;
- red target is a non-maneuvering, unarmed drone surrogate already in flight;
- initial range is close to intermediate, about `8-15 km`;
- success means the policy discovers radar/weapon switches, launches a missile,
  and receives `combat_win`.

Realism scope:

- true runtime weapon release, ammo consumption, missile flight, damage, and
  target inactive termination;
- no evasive target behavior, no red weapons, no tactical BVR decision-making.

### Stage 1: Range Expansion Against A Non-Maneuvering Target

Goal: extend the same fire chain to first BVR-like distances.

Scenario shape:

- red target remains unarmed and non-maneuvering;
- initial range expands to about `20-40 km`;
- episode length is long enough for contact tracking, missile time of flight,
  and terminal effects.

Realism scope:

- launch-range, contact persistence, and missile time-of-flight pressure begin
  to matter;
- target defense and reciprocal threat are still deferred.

### Stage 2: Evasive Fighter With Weapons Locked

Goal: introduce kinematic tactics without reciprocal missile pressure.

Scenario shape:

- red becomes a fighter controlled by the scripted opponent behavior;
- red can offset, beam, accelerate, and hold altitude;
- red has no usable missiles;
- initial range is about `40-70 km`.

Realism scope:

- blue must maintain geometry and choose better launch timing against a moving
  fighter;
- no red weapon release yet, so failures are attributable to pursuit, launch
  timing, sensor/contact handling, or flight control.

### Stage 3: Fighter With Limited Weapon Unlock

Goal: introduce bounded reciprocal threat before full peer `1v1`.

Scenario shape:

- red is an armed fighter, but with limited ammo and a reduced/controlled fire
  window;
- initial range is about `70-120 km` as the maintained sensor model permits;
- the first release should use delayed or range-gated red fire, not an immediate
  all-aspect salvo at episode start.

Realism scope:

- first defensive and offensive trade-offs;
- limited reciprocal weapons, no full self-play, no multi-ship tactics.

## Gates

Each stage should pass these gates before the next stage is used for training:

- blue weapon switches are observable in diagnostics: radar, master arm, fire
  command, and weapon selection;
- at least one seeded policy or scripted baseline can produce a positive
  `combat_win` sample;
- terminal reward remains exclusive: `combat_win`, `combat_loss`, or
  `combat_draw` should not stack unrelated crash or objective bonuses;
- no non-finite report is emitted by the training probe;
- HMoE route and action diagnostics are recorded at enough resolution to explain
  failed rollouts.

## Scenario Directory

The staged scenario fixtures live under:

`scenarios/air_combat/1v1/`

Initial files:

- `air_combat_1v1_stage0_drone_weapon_employment_v1.json`
- `air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json`
- `air_combat_1v1_stage2_evasive_fighter_no_weapons_v1.json`
- `air_combat_1v1_stage3_limited_weapons_fighter_v1.json`

The older `scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json`
remains a smoke/bridge fixture, not the first training curriculum entry.

## Visualization Convention

In this project, air-combat `viz` refers to the interactive `examples/viz`
entrypoint, not TensorBoard or one-off diagnostic plots. The first Stage 0
profile is:

`examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json`

Use it to inspect target contact, ammo decrement, missile flyout, target damage,
and `combat_win` under a fixed fire action. This is a process-alignment view, not
an RL policy acceptance test. To inspect a trained policy, launch `examples/viz`
with `--model` and without the fixed-action profile.

## Residuals

- Add a real UAV/drone database platform instead of the current generic
  unarmed airborne target surrogate.
- Add combat-specific mission observation fields and HMoE routing once the
  action reachability problem is fixed.
- Add fire-chain shaping and diagnostics so the curriculum can report why a
  rollout did or did not launch.
- Validate the long-range scenarios against current sensor and missile runtime
  limits before treating `100+ km` engagements as realistic rather than only a
  planning target.
