# Air Combat 1v1 Curriculum Scenarios

This directory holds the staged `1v1` curriculum for the air-combat workline.
The top-level historical smoke scenario remains available at
`scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json`.

## Stage Files

- `air_combat_1v1_stage0_drone_weapon_employment_v1.json`
  - close/intermediate unarmed `MQ-9_Reaper` target surrogate;
  - validates weapon-action reachability and runtime fire-chain behavior; current fixed-fire smoke evidence accepts either `combat_win` or `combat_timeout`.
- `air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json`
  - unarmed non-maneuvering `MQ-9_Reaper` target at first BVR-like range;
  - intended to exercise contact persistence and missile time-of-flight behavior.
- `air_combat_1v1_stage2_evasive_fighter_no_weapons_v1.json`
  - scripted evasive fighter with no usable missiles;
  - intended to exercise pursuit geometry and launch timing without red fire.
- `air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json`
  - Stage-2 scripted evasive fighter with C2/ROE single-shot command fields;
  - maintained training-shaped entry for transferring the accepted Stage-1
    firing behavior into the maneuvering-target lane.
- `air_combat_1v1_stage3_limited_weapons_fighter_v1.json`
  - scripted fighter with limited missiles and a controlled fire window;
  - intended to exercise bounded reciprocal threat before full peer `1v1`.

The `realism_gradient` blocks are planning metadata and are intentionally kept
outside the runtime-critical scenario fields.

## Viz Profiles

Use `examples/viz` for interactive scenario visualization. Stage 0 currently has
a fixed-fire process-inspection profile:

`examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json`

This profile is for watching the weapon chain and terminal outcome. It should
not be interpreted as a learned-policy result because it supplies a fixed action
vector. Use the `0.1x` or `0.05x` viz speed controls for slow-motion engagement
inspection instead of changing the action into multi-pulse scripts.
