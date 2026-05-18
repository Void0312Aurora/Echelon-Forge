<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/program/realism_program_taskboard_20260516.zh.md. Review before treating this file as authoritative. -->

# Realism Task Master Table

Status: `2026-05-16` main thread convergence edition.

Related documents:

- [Flight Dynamics Realism Analysis, Distortion Inventory, and Air Combat Pre-requisites](../flight/flight_dynamics_realism_analysis_20260516.zh.md)
- [Flight Dynamics Realism P0 Implementation Package](../flight/flight_dynamics_realism_p0_implementation_package_20260516.zh.md)
- [Sensor/Situational Awareness Realism Verification and Implementation Plan](../sensor_situation/sensor_situation_realism_verification_and_implementation_plan_20260516.zh.md)
- [Sensor/Situational Realism P0 Implementation Package](../sensor_situation/sensor_situation_realism_p0_implementation_package_20260516.zh.md)
- [Weapon System and Guidance Loop Realism Verification and Deployment Plan](../weapon_guidance/weapon_guidance_realism_verification_and_plan_20260516.zh.md)
- [Weapon/Guidance Realism P0 Implementation Package](../weapon_guidance/weapon_guidance_realism_p0_implementation_package_20260516.zh.md)

Purpose of this document:

- Converge the verification findings, implementation suggestions, data sources, and `P0` packages of the three directions into a single entry point.
- Clarify the recommended order of realism advancement, dependencies, and stopping criteria.
- Provide a single task board for subsequent branching, PRs, data supplementation, and test additions.

---

## I. Overall Assessment

The current repository's air combat main line is no longer a shell with "no physics at all", but it still has significant gaps for a "credible tactical simulation".

These three gaps are not independent issues but coupled problems:

1. `Flight Dynamics`
   - Determines whether platform energy management, attitude recovery, and high-angle-of-attack behavior are credible
2. `Sensors/Situational Awareness`
   - Determines whether targets can be reasonably detected, confirmed, shared, and classified
3. `Weapons/Guidance`
   - Determines whether missiles rely on reasonable seeker, energy, and fuze logic, rather than "see and hit"

If only one line is fixed, the other two will still skew training results.

Therefore, a more appropriate advancement approach is not "go deep into one direction first", but rather:

- First push all three lines to `P0 usable and testable`
- Then decide which line to enter `P1`

---

## II. Recommended Priorities

### 2.1 P0-A: Freeze field skeleton and test skeleton first

This step precedes any "formula upgrade".

Reasoning:

- Flight dynamics needs `aero_tuning / engine_tuning / stall_state`
- Sensors need `SNR/Pd / M-of-N / track quality`
- Weapons need `missile tuning / seeker state / autopilot surrogate`

If the field skeleton is not fixed first, every subsequent line will require rework repeatedly.

### 2.2 P0-B: First address the three things that most contaminate training signals

These three tasks are recommended as the first batch of code work to be advanced in parallel:

1. `High-angle-of-attack recovery trend`
   - From the flight dynamics direction
   - Goal: No longer rely solely on failfast end-of-step to "handle stall"
2. `DataLink no longer directly shares ground-truth-style contacts`
   - From the sensor/situational awareness direction
   - Goal: Cut the most obvious god-view leak
3. `Guidance cuts direct dependency on target truth`
   - From the weapon/guidance direction
   - Goal: No longer allow missiles to "see via seeker but compute using truth"

### 2.3 P0-C: Then fill energy and tracking consistency

Next batch to follow:

1. Engine transients + fuel/altimeter consistency
2. SNR/Pd approximation + M-of-N
3. 3DoF missile boost/coast + drag + mass

The goal of this layer is not to "match every number from public manuals", but first to restore the input-output causal chain to a reasonable direction.

---

## III. Dependencies

### 3.1 Flight Dynamics -> Weapons/Guidance

Although missile 3DoF energetics and seeker geometry can be advanced independently initially, the following depend on the basic physics framework from flight dynamics:

- High-altitude/high-speed air density, speed of sound, drag trends
- Platform high-angle-of-attack behavior
- Closure rate and firing timing

Therefore:

- The weapon direction can start with `truth cut + seeker state + 3DoF skeleton`
- But before actual parameter calibration, flight dynamics must at least stabilize the atmosphere/propulsion/stall recovery framework

### 3.2 Sensors/Situational Awareness -> Weapons/Guidance

The weapon direction has direct dependencies on the sensor direction:

- Seeker contact quality
- Track confirmation after M-of-N
- Mid-course guidance via data link
- State evolution after jamming and decoys enter seeker field of view

Therefore:

- The sensor direction must at least deliver `track quality / confirm state / datalink track report` first
- Then the weapon direction can hook into seeker state and lock memory

### 3.3 Flight Dynamics -> Sensors/Situational Awareness

This dependency is weakest but still exists:

- Platform attitude and velocity affect Doppler, beam aspect, line-of-sight geometry
- RCS aspect, boresight angle, and sun background all depend on attitude

Therefore:

- The sensor direction can proceed with most of its `P0` first
- But certain advanced validation must wait for flight dynamics attitude semantics to converge further

---

## IV. P0 Task Package Summary for Three Lines

### 4.1 Flight Dynamics P0

Main document:

- [flight_dynamics_realism_p0_implementation_package_20260516.zh.md](../flight/flight_dynamics_realism_p0_implementation_package_20260516.zh.md)

Core objectives:

1. Establish `aero_tuning / engine_tuning` parameter skeleton
2. Establish `stall_state / alpha_dot / propulsion_state`
3. Lay foundation for subsequent compressibility, engine transients, pitch break

Recommended first files to modify:

- `src/content/unit_definition.h`
- `src/content/unit_definition_loader.cpp`
- `src/models/core/default_unit_factory.h`
- `src/components/physics/dynamics.h`
- `src/components/physics/forces.h`
- New `src/components/physics/flight_dynamics_tuning.h`

Minimum gate tests:

- `throttle_step_response`
- `stall_pitch_break_and_recovery`
- `mach_drag_rise_trend`
- `level_accel_vs_alt_mach`

### 4.2 Sensor/Situational P0

Main document:

- [sensor_situation_realism_p0_implementation_package_20260516.zh.md](../sensor_situation/sensor_situation_realism_p0_implementation_package_20260516.zh.md)

Core objectives:

1. Introduce `SNR/Pd` approximation
2. Introduce `M-of-N` confirmation
3. Add minimal `alpha-beta` filter to `TrackManager`
4. Make `DataLink` transmit `track/report` instead of writing directly to `ContactList`

Recommended first files to modify:

- `src/components/systems/sensor.h`
- `src/components/systems/track_management.h`
- `src/components/systems/comm.h`
- `src/components/command/common/comm_message.h`
- `src/models/systems/default_sensor_model.cpp`
- `src/systems/systems/sensor_system.h`
- `src/systems/systems/track_manager_system.h`
- `src/systems/systems/data_link_system.h`

Minimum gate tests:

- `Pd` trend for marginal targets
- `2-of-3` track confirmation
- Track smoothness after filtering
- Data link sharing no longer directly generates local contacts

### 4.3 Weapon/Guidance P0

Main document:

- [weapon_guidance_realism_p0_implementation_package_20260516.zh.md](../weapon_guidance/weapon_guidance_realism_p0_implementation_package_20260516.zh.md)

Core objectives:

1. Guidance cuts direct dependency on target truth
2. Upgrade missile from "constant-speed Rodrigues rotation" to `3DoF boost/coast + drag + mass`
3. Upgrade PN from geometric rotation to "acceleration command + first-order autopilot surrogate"

Recommended first files to modify:

- `src/core/engine/simulation_kernel.h`
- `src/core/engine/simulation_kernel_weapon_api.cpp`
- `src/components/combat/weapon.h`
- `src/models/weapons/default_guidance_model.cpp`
- `src/models/weapons/default_effects_model.cpp`
- `src/systems/combat/damage_system.h`

Minimum gate tests:

- Seeker-only lock / break / reacquire
- 3DoF velocity decay and boost-phase trend
- PN g-load/acceleration bounded
- Near miss / fuze / damage layering

---

## V. Data Source Strategy

All three lines have confirmed: the current local database and parameter configuration are insufficient to support realism; an external round of reference data is necessary.

Principles:

1. `Primary sources first`
   - Public data from NASA / NOAA / FAA / ITU / NATO etc.
2. `Secondary engineering documentation next`
   - AeroBench, JSBSim, MathWorks documentation, public simulation textbooks
3. `Community/unofficial data can be used, but only as initial values or sanity checks`
   - DCS/BMS/forum excerpts / CMANO database

---

## VI. Recommended Implementation Order

It is recommended to follow this order, rather than starting all three lines independently out of sequence.

### Phase 1: Only freeze fields and configuration paths

Goal:

- Add required `P0` fields for all three lines
- Loader / factory / API can read the data
- Do not rush to integrate complete runtime logic

### Phase 2: Cut the most obvious god-view loops

Goal:

1. DataLink no longer directly shares `ContactList`
2. Guidance no longer directly reads target truth for PN
3. IFF/classification and track quality at least have a "fuzzy layer" first

### Phase 3: Fill in the most valuable dynamic behaviors

Goal:

1. Stall / pitch break / high-angle-of-attack recovery
2. Propulsion transient
3. Seeker track state + missile 3DoF
4. SNR/Pd + M-of-N + alpha-beta

### Phase 4: Then proceed to P1

Only then is it appropriate to continue:

- Deeper compressibility corrections
- More complete IFF/data link semantics
- Finer layering of proximity fuzing and damage
- Gust, turbulence, complex decoys/jamming

---

## VII. Suggested Stopping Criteria

Before `P0` completion, it is not recommended to treat the following results as "credible air combat conclusions":

- Energy-maneuverability comparisons between different aircraft types
- Real tactical value comparisons of certain radar / seeker / data link types
- Hit probability and launch envelope comparisons for specific missile models
- Whether high-angle-of-attack dogfight strategies are "realistically effective"

Only after `P0` completion is it recommended to re-evaluate:

1. Whether to restart more in-depth 1v1 training
2. Whether to begin P1-level realism work
3. Whether existing reward and termination logic needs recalibration

---

## VIII. Current Main Thread Recommendation

If work is to start now, I recommend the first round not to overhaul all three lines simultaneously, but to follow this order:

1. `fields-only PR`
   - Freeze `P0` fields and configuration paths uniformly across all three lines
2. `anti-cheat PR`
   - First cut the most obvious god-view loops: `DataLink truth leak` and `guidance truth dependence`
3. `dynamics PR`
   - `stall_state + propulsion_state` for flight dynamics
4. `tracking PR`
   - `SNR/Pd + M-of-N + alpha-beta`
5. `missile PR`
   - `3DoF + PN accel surrogate + fuse layering`

Benefits of this advancement:

- Each round can be validated separately
- Each round has clear realism gains
- No single line will drag the other two into rework if it goes halfway
