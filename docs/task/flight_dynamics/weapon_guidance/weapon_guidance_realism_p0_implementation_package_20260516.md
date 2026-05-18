<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_p0_implementation_package_20260516.zh.md. Review before treating this file as authoritative. -->

# Weapon/Guidance Realism P0 Implementation Package

Status: `2026-05-16` P0 start package.

Related documents:

- [Weapon System and Guidance Loop Realism Analysis](weapon_guidance_realism_analysis_20260516.zh.md)
- [Weapon System and Guidance Loop Realism Verification and Implementation Plan](weapon_guidance_realism_verification_and_plan_20260516.zh.md)

Related code:

- [Missile component](../../../../src/components/combat/weapon.h)
- [SimulationKernel weapon interface](../../../../src/core/engine/simulation_kernel.h)
- [SimulationKernel launch implementation](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [Default guidance model](../../../../src/models/weapons/default_guidance_model.cpp)
- [Default sensor model](../../../../src/models/systems/default_sensor_model.cpp)
- [Weapon chain regression test](../../../../tests/runtime/test_air_combat_1v1_fire_missile.py)

Document purpose:

- Converge direction 3 into a single P0 package ready for implementation.
- Cover only the three most critical things:
  - Cutting guidance's direct dependency on target truth
  - 3DoF `boost/coast + drag + mass`
  - `PN acceleration command + first-order autopilot surrogate`

---

## 1. Goals

The goal of P0 is not to "build a complete missile simulator", but to advance the current weapon chain from "obviously distorted" to "trend credible, capable of supporting higher-level air combat simulation".

This package requires completion of:

1. `Guidance truth cut`
   - `DefaultGuidanceModel` no longer directly reads target `Transform/Velocity` for PN.
   - The main guidance loop only consumes seeker `Detection` and the missile's own historical state.

2. `3DoF missile energy model`
   - Missile speed is no longer forcibly normalized to `max_speed` every frame.
   - At minimum, include:
     - boost
     - sustain/coast
     - drag
     - propulsion mass depletion

3. `PN accel command + first-order autopilot`
   - Guidance law output changes from "angular rate/velocity rotation" to "normal acceleration command".
   - Use first-order response to approximate missile autopilot, without introducing a full 6DoF rigid body.

4. `P0 realism guard tests`
   - Add initial guard tests for these three items to ensure no regression during subsequent modifications.

---

## 2. Non-Goals

P0 explicitly will not do:

1. Full 6DoF missile rigid body, control surfaces, angular rates, and attitude closure.
2. Complete SARH / HOJ / DRFM / RGPO / VGPO details.
3. Complete proximity directionality, fragmentation cone, and subsystem damage rework.
4. Aircraft-level high-precision parameter replication.
5. Large-scale database restructuring or unified weapon content system.

Approximations allowed in P0:

1. `Detection` still uses the current `Sensor -> ContactList` pipeline.
2. The IR seeker can continue to reuse `bearing/elevation/closing_speed` in the first version, but must not continue to borrow target truth position.
3. The autopilot only does first-order acceleration tracking, without an inner angular rate controller.

---

## 3. P0 Scope and Deliverables

### 3.1 In Scope

1. `MissileTuning` extended to express the dynamics and seeker parameters required by P0.
2. `Missile` runtime state extended to store:
   - filtered track
   - current energy state
   - commanded/achieved lateral acceleration
3. `fire_missile()` initializes new fields.
4. `DefaultGuidanceModel` changed to:
   - seeker-only track update
   - PN accel command
   - first-order autopilot
   - thrust/drag/mass integration
5. New set of weapon realism guard tests added.

### 3.2 Out of Scope

1. `DefaultEffectsModel` and `DamageSystem` are only kept compatible, not included in this P0 main implementation.
2. EW only does minimal interface compatibility strongly related to seeker selection, not a full decoy overhaul.
3. The `Sensor` general model is not heavily modified, only complemented minimally when necessary.

---

## 4. Specific Files to Add/Modify

### 4.1 Mandatory Files

1. [src/components/combat/weapon.h](../../../../src/components/combat/weapon.h)
   - Extend `Missile` runtime state.
   - If necessary, add seeker/guidance mode enums.

2. [src/core/engine/simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
   - Extend `MissileTuning`.

3. [src/core/engine/simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
   - Initialize fields required by P0.
   - Keep default parameters compatible with existing tests.

4. [src/models/weapons/default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
   - Main P0 modification file.
   - Replace truth PN, constant-speed normalization, and fixed turn-rate main logic.

5. [tests/runtime/test_weapon_guidance_realism_guards.py](../../../../tests/runtime/test_weapon_guidance_realism_guards.py)
   - New P0 guard test file.

### 4.2 Optional New Files

If `default_guidance_model.cpp` grows too large, allow adding:

1. [src/models/weapons/missile_guidance_math.h](../../../../src/models/weapons/missile_guidance_math.h)
   - Vector tools
   - Alpha-beta filter helpers
   - Thrust/drag helpers

2. [src/models/weapons/missile_guidance_types.h](../../../../src/models/weapons/missile_guidance_types.h)
   - Small internal structs/enums

P0 does not recommend adding new ECS systems; the main logic should remain in `DefaultGuidanceModel`.

---

## 5. Field Design

### 5.1 `MissileTuning` P0 Minimum Field Set

File:

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)

Suggested additions:

```cpp
int seeker_type = 0;                 // 0=ARH, 1=IR, 2=SARH (P0 mostly uses 0/1)
double seeker_activation_range_m;
double bearing_filter_tau_s;
double elevation_filter_tau_s;
double range_filter_tau_s;
double track_break_time_s;

double boost_time_s;
double sustain_time_s;
double boost_thrust_n;
double sustain_thrust_n;
double reference_area_m2;
double cd0_subsonic;
double cd0_supersonic;
double induced_drag_k;
double propellant_mass_kg;

double max_lateral_g;
double autopilot_tau_s;
double max_accel_response_g_per_s;
```

Explanation:

1. `seeker_type` uses `int` instead of a new enum exposed to the facade, reducing the scope of changes in this round.
2. `range_filter_tau_s` can be ignored for the first version of IR, but the field is reserved.
3. `propellant_mass_kg` is placed in tuning rather than the default `Mass` value, to facilitate future database usage.
4. `cd0_subsonic/cd0_supersonic` are sufficient for P0; no full Mach table is built.

### 5.2 `Missile` P0 Minimum Runtime State

File:

- [weapon.h](../../../../src/components/combat/weapon.h)

Suggested additions:

```cpp
int seeker_mode = 0;                 // 0=Track, 1=Memory, 2=Terminal

double filtered_bearing_deg = 0.0;
double filtered_elevation_deg = 0.0;
double filtered_range_m = 0.0;
double bearing_rate_deg_s = 0.0;
double elevation_rate_deg_s = 0.0;
double last_track_time_s = -1.0;

double current_speed_mps = 0.0;
double commanded_lateral_accel_mps2 = 0.0;
double achieved_lateral_accel_mps2 = 0.0;
double burnout_time_s = -1.0;
```

Optional additions:

```cpp
bool seeker_has_valid_track = false;
bool seeker_has_range = true;
```

P0 deliberately avoids stuffing many unused fields into `Missile`, to prevent bringing in content from the second stage prematurely.

### 5.3 `Mass` Usage Convention

File:

- [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)

P0 does not modify the `Mass` structure, only agrees on the following initialization method for missile entities:

1. `empty_mass_kg` = airframe + warhead + electronics
2. `fuel_mass_kg` = propellant mass
3. `stores_mass_kg` = `0`

This way, within the guidance model, `mass.get_total_kg()` can be used directly without adding a missile-specific mass component.

---

## 6. Core Implementation Design

### 6.1 Cutting Guidance's Direct Dependency on Target Truth

Main file:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)

P0 constraints:

1. Delete or disable the following paths:
   - `world.entity(missile.target_id).get<Transform>()`
   - `world.entity(missile.target_id).get<Velocity>()`
2. Guidance only constructs LOS from `best_det` and the missile's own historical state.
3. Must allow "brief track loss but continued guidance via memory":
   - `current_time - last_track_time_s <= track_break_time_s`

P0 recommended approach:

1. Each guidance tick:
   - First select the best detection from `ContactList`
   - If found:
     - Update `filtered_bearing/elevation/range`
     - Update `bearing_rate/elevation_rate`
     - `last_track_time_s = now`
   - If not found but still within `track_break_time_s`:
     - Enter `Memory` mode
     - Maintain last filtered state, do not update measurements
   - If timeout:
     - Exit active guidance, continue flying at current velocity direction

The result of this approach:

1. Truth lock is cut.
2. Seeker noise and scan period genuinely enter the guidance loop.
3. Later, flares/chaff will truly have a chance to alter guidance behavior.

### 6.2 3DoF `boost/coast + drag + mass`

Main file:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)

P0 suggested state advancement:

1. `V = |velocity|`
2. Obtain from environment:
   - `rho`
   - `speed_of_sound`
3. Calculate:
   - `Mach`
   - `q_bar = 0.5 * rho * V^2`
4. Thrust:
   - `t < boost_time_s`: `boost_thrust_n`
   - `boost <= t < boost+sustain`: `sustain_thrust_n`
   - else `0`
5. Drag:
   - `cd0 = lerp(cd0_subsonic, cd0_supersonic, mach_blend)`
   - `D = q_bar * reference_area_m2 * (cd0 + induced_drag_term)`
6. Mass:
   - Linearly deplete `fuel_mass_kg` during boost+sustain time
7. Speed:
   - Integrate `(T - D) / m` along the flight path

P0 allowed approximations:

1. Do not explicitly integrate the gravity component along the flight path if it would significantly complicate things; it can be temporarily omitted.
2. `induced_drag_term` can be initially approximated using `achieved_lateral_accel`, rather than strictly derived from `Cl`.

### 6.3 PN Acceleration Command + First-Order Autopilot Surrogate

Main file:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)

P0 recommended formulas:

1. Construct the unit line-of-sight direction using filtered LOS.
2. Approximate the LOS rotation rate using angular rates.
3. Calculate:

```cpp
a_cmd_lat = N * Vc * lambda_dot_equiv;
```

Or its vector form approximation:

```cpp
a_cmd_vec = N * Vc * (omega_los x v_hat);
```

4. Saturate to:

```cpp
a_cmd_sat = clamp(|a_cmd|, max_lateral_g * g)
```

5. First-order autopilot:

```cpp
a_achieved += (a_cmd_sat - a_achieved) * dt / autopilot_tau_s;
```

6. Add a rate limit:

```cpp
|da/dt| <= max_accel_response_g_per_s * g
```

7. Use:

```cpp
omega_turn = a_achieved / V
```

to update the velocity direction.

The focus of P0 is not which textbook version of the PN formula is chosen, but:

1. Guidance output is in acceleration dimensions.
2. There is g-force saturation.
3. There is response lag.
4. High/low speed is coupled with the energy model.

---

## 7. Test Checklist

### 7.1 New Test File

- [tests/runtime/test_weapon_guidance_realism_guards.py](../../../../tests/runtime/test_weapon_guidance_realism_guards.py)

### 7.2 P0 Mandatory Tests

1. `test_missile_speed_profile_boost_then_decay`
   - Speed increases in the first few seconds after launch.
   - Speed begins to decrease after burnout.

2. `test_missile_mass_decreases_during_propulsion`
   - `fuel_mass_kg` decreases during the propulsion phase.
   - It does not decrease after burnout.

3. `test_guidance_no_longer_reads_target_truth`
   - By constructing seeker contacts and tampering with/isolating the target truth access path, verify that guidance can still operate.
   - A more realistic approach is to compare: "missile trajectory changes when there are detection updates; enters memory/straight-fly when there are no detections."

4. `test_pn_outputs_bounded_lateral_accel`
   - Commanded accel can exceed achievable values.
   - Achieved accel is constrained by `max_lateral_g` and `autopilot_tau_s`.

5. `test_large_turn_costs_speed`
   - Terminal speed for a large off-boresight intercept is lower than for a small off-boresight direct pursuit.

6. `test_track_memory_timeout_reverts_to_ballistic_or_hold`
   - After seeker track loss, continue memory guidance within `track_break_time_s`.
   - After timeout, no longer update guidance.

### 7.3 P0 Optional Tests

1. `test_high_altitude_turn_authority_differs_from_low_altitude`
2. `test_scan_period_and_noise_affect_terminal_error_trend`

---

## 8. External Data Integration Approach

### 8.1 P0 Does Not Directly Perform Database System Restructuring

P0 suggests a two-layer approach:

1. `Code layer`
   - First place the screened parameters into `MissileTuning` default values and test-specific tunings.
2. `Document layer`
   - Create a traceable parameter table, recording sources and confidence levels.

### 8.2 Recommended Data Integration File

P0 suggests adding a lightweight reference table:

- `docs/task/flight_dynamics/weapon_guidance/weapon_guidance_p0_reference_table_20260516.md`

Suggested table fields:

| family | parameter | value | unit | source | confidence | note |
| --- | --- | --- | --- | --- | --- | --- |

Example parameters:

1. `aim_120_like`
   - `mass_total_kg`
   - `warhead_mass_kg`
   - `boost/sustain`
   - `guidance = inertial_midcourse + active_terminal`
2. `aim_9x_like`
   - `mass_total_kg`
   - `loal_supported`
   - `ir seeker`
   - `off_boresight class`

### 8.3 Data Source Usage Principles

1. Primary sources directly determine category and magnitude:
   - Manufacturer pages
   - Service fact sheets
2. Secondary sources supplement typical ranges:
   - Designation Systems
   - FAS
   - Air & Space Forces data cards
3. Academic materials are used only for:
   - PN / autopilot / filter structures
   - Not directly for specific model parameters

### 8.4 P0 Parameter Integration Strategy

P0 does not pursue "absolute realism of a specific missile type", only makes two class templates:

1. `arh_mraam_like`
   - Represents the trend of medium-range active missiles like AIM-120 / Meteor
2. `ir_wvraam_like`
   - Represents the trend of short-range infrared missiles like AIM-9X / IRIS-T

This reduces database pressure and first gets the simulation patterns working smoothly.

---

## 9. Recommended Implementation Order

Recommended to split into 6 steps:

1. `Extend fields`
   - Modify [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h) and [weapon.h](../../../../src/components/combat/weapon.h)
   - Only add P0 minimum fields, no logic.

2. `Supplement launch initialization`
   - Modify [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
   - Provide reasonable default values and initialization for new fields.
   - Ensure old tests do not break due to uninitialized fields.

3. `Cut truth guidance`
   - Modify [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
   - First remove the target truth reading path, replace with detection + memory state.
   - Do not implement complex energy model at this step.

4. `Add PN accel + autopilot surrogate`
   - Continue modifying the same file.
   - First make guidance output acceleration, with first-order tracking and G limits.

5. `Integrate boost/coast + drag + mass`
   - Still complete within the guidance model.
   - Remove the `velocity = max_speed normalized` path.

6. `Add guard tests`
   - Add new [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/test_weapon_guidance_realism_guards.py)
   - First guard truth cut, speed profile, mass depletion, accel saturation, track memory timeout.

The advantage of this order:

1. Each step can be tested independently.
2. After step 3, the biggest distortion source is already cut.
3. Steps 4-5 gradually add dynamic realism without mixing all issues together at once.

---

## 10. P0 Completion Criteria

P0 can be considered complete when the following conditions are met:

1. `DefaultGuidanceModel` no longer directly reads target `Transform/Velocity` for PN.
2. The missile speed profile exhibits the basic trend of "acceleration during propulsion, decay after burnout".
3. Guidance response demonstrates:
   - Acceleration saturation
   - First-order build-up lag
4. All newly added P0 guard tests pass.
5. Existing basic weapon chain tests do not show widespread regression.

If P0 only brings one change after completion, it should be:

`The missile finally misses the target because it cannot see clearly, cannot turn hard enough, or runs out of energy, rather than relying on truth values and constant speed to brute-force intercept.`
