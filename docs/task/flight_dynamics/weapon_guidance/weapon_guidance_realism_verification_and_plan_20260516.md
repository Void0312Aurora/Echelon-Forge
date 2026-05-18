<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_verification_and_plan_20260516.zh.md. Review before treating this file as authoritative. -->

# Verification and Implementation Plan for Realistic Weapon Systems and Guidance Loops

Status: `2026-05-16` Direction 3 Verification and Implementation Plan Version.

Related Inputs:

- [Realism Analysis of Weapon Systems and Guidance Loops](weapon_guidance_realism_analysis_20260516.zh.md)
- [DefaultGuidanceModel](../../../../src/models/weapons/default_guidance_model.cpp)
- [DefaultEffectsModel](../../../../src/models/weapons/default_effects_model.cpp)
- [DamageSystem / ProximityFuze](../../../../src/systems/combat/damage_system.h)
- [SimulationKernel Weapon API](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [DefaultSensorModel](../../../../src/models/systems/default_sensor_model.cpp)
- [EW System](../../../../src/systems/systems/ew_system.h)

Document Purpose:

- Verify which conclusions from the existing Direction 3 investigation are true, and which need correction or supplementation.
- Provide an implementation plan that is achievable within the current ECS / model / system boundaries.
- Organize available reference data sources for missiles, seekers, proximity fuzes, and damage.
- Provide recommended priorities as an entry point for subsequent realistic development.

---

## A. Verification Conclusions

### A.1 Verified True Conclusions

1. `"PN is currently not 'acceleration guidance + autopilot'"; rather, it is "velocity vector rotation driven by LOS angular rate".`
   - Code location: [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
   - Specific behavior:
     - `omega = (R x Vrel) / |R|^2` then directly forms `rate_x/y/z`.
     - Uses Rodrigues rotation to update velocity direction.
     - After rotation, the velocity magnitude is forcibly normalized to `missile.max_speed`.
   - This means the current model lacks the layer: "normal acceleration command -> load factor constraint -> airframe response."

2. `"Missile energetics are currently largely missing"; is true, and even more explicit than the original document stated.`
   - Code location: [default_guidance_model.cpp:266](../../../../src/models/weapons/default_guidance_model.cpp:266)
   - The current missile lacks:
     - Boost / sustain / glide phases
     - Drag varying with speed / altitude
     - Induced drag from turns
     - Mass variation with propellant consumption
   - Although it inherits the carrier aircraft's initial speed upon launch, this is reset to `max_speed` at the next guidance tick.

3. `"Guidance calculations still directly use target truth values"; is true.`
   - Code location: [default_guidance_model.cpp:117](../../../../src/models/weapons/default_guidance_model.cpp:117)
   - Currently, although the target is first selected from the missile's own `ContactList`, the PN calculation stage still directly reads the target's `Transform` and `Velocity`.
   - Thus, the current implementation is "the sensor determines who is seen, but truth determines how to engage," not truly seeker-only guidance.

4. `"Decoys / jamming are currently crude approximations"; is true.`
   - Seeker side:
     - [default_guidance_model.cpp:93](../../../../src/models/weapons/default_guidance_model.cpp:93) only selects the strongest target by `signal_strength`.
   - Sensor side:
     - [default_sensor_model.cpp:252](../../../../src/models/systems/default_sensor_model.cpp:252) applies only a simple burn-through range threshold against noise blanking jamming.
     - [default_sensor_model.cpp:268](../../../../src/models/systems/default_sensor_model.cpp:268) treats thermal decoys only by `Lifetime` as "flare-like high IR source."
   - Deployment side:
     - [ew_system.h](../../../../src/systems/systems/ew_system.h) only generates a low-speed, high-RCS chaff entity or a velocity-inheriting flare entity, lacking time-intensity curves, angular separation logic, and kinematic rejection.

5. `"Proximity fuze is currently a closest-point heuristic, not a directional/predictive fuze"; is true.`
   - Code location: [damage_system.h](../../../../src/systems/combat/damage_system.h)
   - Current logic:
     - Tracks minimum distance.
     - Once the target starts moving away and the closest distance is less than `fuse_distance`, it is considered detonable.
     - Then a probability based on `quality * evasion` is superimposed.
   - This does not differentiate forward fragmentation cone, relative bearing, or range-rate lead trigger.

6. `"Damage model is currently a dual-track model combining HP and geometric hitboxes"; is true.`
   - Code location: [default_effects_model.cpp:116](../../../../src/models/weapons/default_effects_model.cpp:116)
   - The HP path can directly destroy an entity; the geometric path performs further system-level damage.
   - The physical meaning of these two paths is inconsistent.

7. `"Coordinate transformation of hitbox body axes exhibits attitude approximation"; is true.`
   - The current repository already has a shared transformation utility [common.h](../../../../src/components/basic/common.h) supporting complete `world_to_body` with `heading/pitch/roll`.
   - [default_effects_model.cpp:32](../../../../src/models/weapons/default_effects_model.cpp:32) still uses a local simplified `world_to_body()`, and `local_z = dz` ignores pitch/roll.

8. `"Launch envelope currently essentially does not exist"; is true.`
   - Code location: [simulation_kernel_weapon_api.cpp:79](../../../../src/core/engine/simulation_kernel_weapon_api.cpp:79)
   - Current requirements only:
     - Has contact
     - Has missile
     - Not in cooldown
   - No LAR, LOBL/LOAL distinction, minimum range, maximum powered range, off-boresight angle limitation, or energy reachability judgment.

### A.2 Conclusions That Need Correction or Narrowing

1. `"Seeker is a complete airborne radar clone"` needs narrowing.
   - A more accurate description should be:
     - The current missile seeker reuses the generic `Sensor` / `ContactList` pipeline;
     - This pipeline already includes simplified capabilities such as FoV, scan period, detection probability, noise, Doppler notch, noise jamming suppression, etc.;
     - However, it does not model the missile seeker's operating modes specifically.

2. `"Completely uses truth for guidance"` should be corrected to a more precise description.
   - A more accurate description should be:
     - `target selection / lock retention` depends on the seeker `ContactList`;
     - `relative geometry / LOS rate / closing speed for PN` still directly reads target truth.

3. `"Missile has no countermeasure/decoy resistance capability"` should be restated as a layered statement.
   - Radar perception side already has:
     - Doppler notch
     - simple burn-through
   - Infrared/decoy side lacks:
     - flare rise/decay
     - centroid tracking
     - kinematic rejection
     - track gate memory / seduction hysteresis

4. `"Lock range and FOV are completely unrealistic"` should be supplemented with "This is the current default tuning, not necessarily structurally inexpressible."
   - Current default values are indeed exaggerated:
     - `seeker_fov_deg = 180`
     - `seeker_lock_range = 30000`
   - But these values come from the default tuning in [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp), not hardcoded unchangeably in the framework.

### A.3 New Conclusions That Need Supplementation

1. `"The current code already has some common foundation required for missile realism, which can be reused without rewriting the physics kernel."`
   - Directly reusable:
     - `dynamic_pressure` / `Mach` from [aero_state_system.h](../../../../src/systems/physics/aero_state_system.h)
     - atmosphere access from [force_system.h](../../../../src/systems/physics/force_system.h)
     - body/world coordinate transformations from [common.h](../../../../src/components/basic/common.h)
     - detection noise / track memory / EW hooks from [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
   - Therefore, a full 6DoF missile body dynamics is not needed first; a `3DoF + acceleration/autopilot surrogate + seeker state` can significantly improve credibility.

2. `"The current Missile component fields are insufficient to carry realistic parameters."`
   - Code location: [weapon.h](../../../../src/components/combat/weapon.h)
   - Missing key states include:
     - Boost phase duration / thrust / mass
     - Current seeker mode
     - Seeker track state / filtered LOS
     - Autopilot commanded / achieved lateral acceleration
     - Warhead / fuze type
     - Proximity prediction state

3. `"The current test tree already has appropriate hooks, but there are no realism gate tests."`
   - Existing weapon chain tests are mainly in:
     - [test_air_combat_1v1_fire_missile.py](../../../../tests/runtime/test_air_combat_1v1_fire_missile.py)
     - [test_air_combat_1v1_fixture.py](../../../../tests/runtime/test_air_combat_1v1_fixture.py)
   - Currently they mainly cover "can launch, can see, can roughly kill", but not:
     - Energy decay
     - PN load factor constraints
     - Seeker noise / filter
     - Flare/chaff seduction trends
     - Near miss / fuze timing / damage-layer consistency

---

## B. Implementation Plan

### B.1 Overall Implementation Principles

1. Phase 1 does not pursue a full 6DoF missile rigid body model; adopt `3DoF particle + acceleration command + first-order autopilot + dynamic pressure/load factor limitation`.
2. Seeker and sensor are not rewritten separately; instead, add missile seeker-specific states within the existing `Sensor -> ContactList -> GuidanceModel` chain.
3. Hit/proximity/damage are decomposed into three layers:
   - `intercept / miss geometry`
   - `fuze / warhead effectiveness`
   - `damage / subsystem consequences`
4. All new parameters should preferably go into `MissileTuning` and `Missile` components, rather than scattering state across multiple system private variables.

### B.2 Component and Configuration Extensions

#### 1. Extend `MissileTuning`

File location:

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)

Proposed new fields:

- Dynamics / Energy
  - `boost_time_s`
  - `sustain_time_s`
  - `boost_thrust_n`
  - `sustain_thrust_n`
  - `reference_area_m2`
  - `cd0_subsonic`
  - `cd0_supersonic`
  - `induced_drag_k`
  - `lift_slope_per_rad`
  - `max_lateral_g`
  - `autopilot_tau_s`
  - `max_accel_response_g_per_s`
- Seeker
  - `seeker_type`
  - `seeker_activation_range_m`
  - `seeker_gimbal_limit_deg`
  - `seeker_ifov_deg`
  - `bearing_filter_tau_s`
  - `range_filter_tau_s`
  - `track_break_time_s`
  - `countermeasure_reject_gain`
- Fuze / Warhead
  - `warhead_type`
  - `warhead_mass_kg`
  - `fragment_cone_half_angle_deg`
  - `fragment_velocity_mps`
  - `fuse_arm_time_s`
  - `fuse_sensor_fov_deg`
  - `fuse_delay_s`
  - `impact_fuze_enabled`
- Launch Conditions
  - `min_launch_range_m`
  - `max_launch_off_boresight_deg`
  - `lobl_required`
  - `midcourse_datalink_supported`

#### 2. Extend `Missile` Runtime Component

File location:

- [weapon.h](../../../../src/components/combat/weapon.h)

Proposed new runtime states:

- `double burnout_time_s`
- `double current_speed_mps`
- `double achieved_lateral_accel_mps2`
- `double commanded_lateral_accel_mps2`
- `double filtered_bearing_deg`
- `double filtered_elevation_deg`
- `double filtered_range_m`
- `double bearing_rate_deg_s`
- `double elevation_rate_deg_s`
- `double track_age_s`
- `double last_valid_track_time_s`
- `int seeker_mode`
- `bool seeker_has_range`
- `bool fuze_armed`
- `double predicted_time_to_go_s`
- `double closest_approach_time_s`

### B.3 Missile Energy/Dynamics

#### 1. Use Existing Environment Model for 3DoF Energy Integration

Primary files to modify:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)

Implementation approach:

1. On launch, set:
   - Initial total mass `Mass{empty, fuel, stores=0}`
   - `burnout_time_s = launch_time + boost + sustain`
   - `current_speed_mps = |v0|`
2. During each guidance tick, compute based on current time and altitude:
   - `rho`, `speed_of_sound`
   - `q_bar = 0.5 * rho * V^2`
   - `Mach = V / a`
3. Thrust segments:
   - `t < boost_time_s` -> `boost_thrust_n`
   - `boost <= t < boost+sustain` -> `sustain_thrust_n`
   - After that, `0`
4. Drag segments:
   - `Cd = Cd0(Mach) + induced_drag_k * Cl_equiv^2`
   - In the first-order version, `Cl_equiv` can be approximated by inverting from the current normal acceleration
5. Speed integration:
   - Along the velocity direction: `a_tangential = (T - D)/m`
6. Mass integration:
   - During powered flight, reduce `fuel_mass_kg` at a constant mass flow rate

#### 2. Replace Fixed Turn Rate with Load Factor Constraints

Core substitution:

- The existing `missile.turn_rate` becomes a compatibility field, but the realistic path primarily uses `max_lateral_g`.

Calculation method:

1. PN first computes `a_cmd_lat`
2. Compute achievable normal acceleration based on dynamic pressure and limits:
   - `a_avail = min(max_lateral_g * g, q_bar_based_limit)`
3. Then through first-order autopilot:
   - `a_achieved += (a_cmd_clamped - a_achieved) * dt / tau`
4. Use `omega_turn = a_achieved / max(V, eps)` to update velocity direction

### B.4 Change PN from Velocity Rotation to Acceleration/Approximate Load Factor Constraints

Primary files to modify:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)

Suggested two-phase approach:

#### Phase 1: Vector PN + Acceleration Proxy

1. Keep `omega = (R x Vrel) / |R|^2`
2. Use a more stable vector PN form:
   - `a_cmd = N * Vc * (omega x v_hat_m)`
3. Remove the dominance of direct geometric rotation via Rodrigues, change to:
   - First integrate `a_achieved`
   - Then use `a_achieved` to change `v_hat`

#### Phase 2: Add Approximate Autopilot

1. First-order acceleration response:
   - `a_achieved_dot = (a_cmd_sat - a_achieved) / tau`
2. Rate limiting:
   - `|da/dt| <= max_accel_response`
3. Reduce effective navigation ratio at large off-boresight angles:
   - `N_eff = N0 * clamp(Vc / V, 0, 1) * clamp(cos(gamma), 0, 1)`

### B.5 Seeker Measurement and Filtering

Primary files to modify:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [sensor.h](../../../../src/components/systems/sensor.h)

#### 1. First, Break Guidance Dependency on Truth Position/Velocity

Implementation principle:

- Guidance only reads `best_det`
- No longer reads target entity's `Transform/Velocity`

#### 2. Use Lightweight Filters to Estimate LOS and LOS Rate

First-order achievable approach:

- Use `alpha-beta` or exponential smoothing difference for bearing/elevation
- Radar seeker uses noisy range directly
- IR seeker defaults to `seeker_has_range = false`

Recommended implementation:

1. For each tick's `bearing/elevation/range`, unwrap and then filter
2. Estimate angular rate using previous filtered value
3. `Vc` for radar can be approximated by range-rate or closing_speed
4. `IR` without range uses a weakened angular PN / lead pursuit

#### 3. Seeker Mode Segmentation

Suggest supporting three states within the current structure:

- `Midcourse`
- `TerminalActive`
- `TerminalIR`

Suggested rules:

- `ARH`: Midcourse guidance relies on launch track memory; upon entering `seeker_activation_range_m`, transition to terminal active
- `SARH`: If shooter track is lost or illumination is insufficient, fails
- `IR`: If `lobl_required` before launch, the missile seeker must have a valid detection at launch

### B.6 Simplified Decoys / Jamming

Primary files to modify:

- [ew_system.h](../../../../src/systems/systems/ew_system.h)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [ew.h](../../../../src/components/systems/ew.h)

#### 1. Flare Simplification

Proposed new `DecoySignature` component:

- `type = flare/chaff`
- `rise_time_s`
- `peak_strength`
- `decay_tau_s`
- `drag_scale`

Behavior:

- Flare initially inherits carrier aircraft speed
- Rapidly rises to peak within 0.2-0.5s
- Then decays exponentially
- Speed decreases rapidly due to drag

Seeker selection logic:

- No longer only selects the instantaneous strongest signal
- If angular separation between target and flare is less than `ifov`, track centroid
- If separation is sufficient, select track based on `signal_strength * kinematic_consistency_score`

#### 2. Chaff / Noise Jammer Simplification

Existing radar sensor already has:

- burn-through
- notch

Proposed additions:

- Chaff Doppler rapidly collapses toward 0
- Missile ARH seeker reduces weight for contacts with abnormally low `closing_speed` and abnormally high angular rate
- DRFM / RGPO / VGPO: not yet implementing full deceptive echoes, only:
  - False range pull-away
  - If the seeker filter does not reject it, cause terminal miss to increase

### B.7 Hit / Proximity / Damage Layering

#### 1. Proximity Layer

Primary file to modify:

- [damage_system.h](../../../../src/systems/combat/damage_system.h)

Proposed logic:

1. Before the closest approach, estimate `t_ca` based on relative position `r` and relative velocity `v_rel`
2. If `0 <= t_ca <= dt_window`, predict the closest point
3. If the closest point is less than `fuse_distance` and the fuze is unlocked/armed, detonate
4. Determine warhead effectiveness based on the angle between the missile forward axis and the target line-of-sight

#### 2. Warhead Effectiveness Layer

It is recommended to add this as an intermediate calculation before the existing `DefaultEffectsModel`, or directly cohesively within the effects model:

- Input:
  - `closest_approach`
  - `relative_aspect`
  - `warhead_type`
  - `fragment_cone_half_angle`
- Output:
  - `structural_hit_score`
  - `subsystem_hit_candidates`
  - `blast_overpressure_score`

#### 3. Damage Layer

Primary files to modify:

- [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)
- [damage.h](../../../../src/components/combat/damage.h)

Suggested refactoring:

1. Reduce the dominance of `Health`
2. Change `SystemHealth` to continuous degradation
3. Change functional consequences to continuous as well
4. Unify hit box coordinate transformations using `Math::world_to_body` from [common.h](../../../../src/components/basic/common.h)

### B.8 Launch Envelope

Primary files to modify:

- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)

Phase 1 first implements 4 hard thresholds:

1. `range` must be within `[min_launch_range, seeker/kinematic max]`
2. `abs(bearing)` must be less than `max_launch_off_boresight_deg`
3. If `lobl_required`, the missile seeker must have a valid detection in the launch frame
4. If `midcourse_datalink_supported == false` and the target is outside the autonomous basket, prohibit launch

### B.9 Test Plan Landing Points

Suggested first batch of new test files:

- `tests/runtime/test_weapon_guidance_realism_guards.py`

Initial guard items:

1. `energy_profile_boost_coast`
2. `turn_costs_energy`
3. `lateral_accel_limit_respected`
4. `seeker_noise_filter_is_not_truth_lock`
5. `flare_can_seduce_ir_but_not_always`
6. `chaff_affects_radar_more_than_ir`
7. `closest_approach_fuze_timing`
8. `damage_layering_continuous`

---

## C. Data Source Recommendations

### C.1 Reliability Tiers

1. `Tier 1: Official / Manufacturer / Service Fact Pages`
2. `Tier 2: Long-maintained defense material sites / Congressional Research Service / Professional media fact sheets`
3. `Tier 3: Academic / Technical surveys / Textbooks`
4. `Tier 4: Simulation communities / Open-source game configs / Forum experience`

### C.2 Recommended Direct Sources

#### 1. Official / Manufacturer / Service Pages

- RTX AIM-9X page:
  - [AIM-9X Sidewinder Missile](https://www.rtx.com/raytheon/what-we-do/sea/aim-9x-sidewinder-missile)
  - Can be used to verify:
    - `IR tracking`
    - `Block II LOAL`
    - `weapon datalink`
    - `redesigned fuze`

- MBDA Meteor page:
  - [Meteor](https://www.mbda-systems.com/products/air-dominance/meteor)
  - Can be used to verify:
    - Weight `190kg`
    - Length `3.7m`
    - Diameter `178mm`
    - `ramjet`
    - `active radar`
    - `large no-escape zone`

#### 2. Semi-official / Long-maintained Reference Sites

- Designation Systems AIM-120:
  - [AIM-120 AMRAAM](https://www.designation-systems.net/dusrm/m-120.html)
  - Can be used to verify:
    - `inertial autopilot`
    - `mid-course updates via data link`
    - `active radar terminal homing`
    - `WDU-33/B fragmentation warhead`
    - `FZU-49/B smart proximity fuze`
    - Typical range intervals, publicly cited minimum range values

- Designation Systems AIM-9:
  - [AIM-9 Sidewinder](https://www.designation-systems.net/dusrm/m-9.html)
  - Can be used to verify:
    - Changes across Sidewinder generations in seeker / warhead / proximity fuze
    - Typical values for earlier models: field of view, tracking rate, max G, effective kill radius, etc.

- Air & Space Forces AIM-120 data card:
  - [AIM-120](https://www.airandspaceforces.com/weapons/aim-120/)
  - Can be used to verify:
    - `boost-sustain solid-propellant rocket motor`
    - `active radar terminal / inertial midcourse`
    - `HE blast-fragmentation`
    - Differences among recent variants, e.g., D / D3 datalink, ECCM, range improvements

#### 3. Guidance / Control / Filtering Technical References

- JHU APL Technical Digest:
  - `Principles of Homing Guidance`
  - `Overview of Missile Flight Control Systems`
  - Suitable for:
    - Basic forms of PN
    - Effective navigation constant
    - Acceleration autopilot
    - Seeker / guidance / control layering

- Zarchan series of public references and related papers
  - Suitable for:
    - Implementation choices for vector PN
    - Sanity check using `a_cmd = N * Vc * (...)`

- Open-access papers on seeker LOS rate estimation / strapdown seeker
  - Suitable for:
    - Lightweight selection among `alpha-beta` / `Kalman` / `UKF`

### C.3 Recommended Priority Parameters for Collection

1. `Missile geometry and mass`
2. `Propulsion system`
3. `Guidance system`
4. `Seeker constraints`
5. `Warhead / fuze`

### C.4 Parameter Initialization Recommendations

For parameters where public precise values are unavailable, it is recommended to start with interval initialization:

1. `autopilot_tau_s`
   - Use `0.06 - 0.15 s` initially
2. `max_lateral_g`
   - For short-range dogfight missiles: use `25 - 40 g` initially
   - For medium-range air-to-air missiles: use `20 - 35 g` initially
3. `seeker_ifov_deg`
   - Use `1 - 3 deg` initially
4. `flare rise / decay`
   - `rise 0.1 - 0.3 s`
   - `strong phase 1 - 3 s`
5. `fragment cone half-angle`
   - Use `15 - 35 deg` initially

---

## D. Recommended Priorities

### D.1 P0: Must Do First

1. `Sever guidance's direct dependence on target truth`
2. `Replace constant speed rotation with "acceleration command + first-order autopilot + velocity integration"`
3. `Add a minimal missile dynamics / energy model`
4. `Add realism guard tests`

### D.2 P1: Should Follow Up Quickly

1. `Seeker filter and seeker mode`
2. `Simplified flare/chaff countermeasures`
3. `Hard launch envelope thresholds`

### D.3 P2: Refinements in Phase 2

1. `Proximity lead trigger + warhead directionality`
2. `Shift damage from HP-dominant to subsystem/structure-dominant`
3. `Continuous degradation of system functional consequences`
4. `Finer branches for HOJ / SARH / datalink`

### D.4 Items Not Recommended for Priority in This Phase

1. Full 6DoF missile rigid body + fins + body rates
2. Full DRFM deception chain
3. High-fidelity fragment ballistics and penetration
4. Reproduction of classified or overly detailed model parameters

---

## Recommended First Implementation Sequence

1. Extend `MissileTuning` / `Missile` components.
2. Rewrite the core state propagation of `DefaultGuidanceModel`:
   - seeker-only measurement
   - filtered LOS
   - PN accel command
   - autopilot lag
   - boost/coast + drag + mass
3. Add `test_weapon_guidance_realism_guards.py`.
4. Add minimum credible curves and rejection rules for flare/chaff to `EW` and `Sensor`.
5. Then modify `DamageSystem` and `DefaultEffectsModel` for proximity/damage layering.

If only one thing is done in this direction, do this first:

`"Remove truth guidance + adopt 3DoF acceleration/energy model"`

This is the prerequisite for correctly expressing all subsequent issues such as seeker, evasion, decoys, LAR, and hit probability.
