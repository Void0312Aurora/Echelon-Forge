<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_p1_implementation_package_20260517.zh.md. Review before treating this file as authoritative. -->

# Weapon/Guidance Realism P1 Implementation Package

Status: `2026-05-17` P1 Draft; progress has been verified against current code/test status.

Related Documents:

- [Weapon System and Guidance Loop Realism Analysis](weapon_guidance_realism_analysis_20260516.zh.md)
- [Weapon System and Guidance Loop Realism Verification and Implementation Plan](weapon_guidance_realism_verification_and_plan_20260516.zh.md)
- [Weapon/Guidance Realism P0 Implementation Package](weapon_guidance_realism_p0_implementation_package_20260516.zh.md)
- [Realism Task Master List](../program/realism_program_taskboard_20260516.zh.md)

Related Code:

- [Missile Component](../../../../src/components/combat/weapon.h)
- [SimulationKernel Configuration Interface](../../../../src/core/engine/simulation_kernel.h)
- [SimulationKernel Launch Implementation](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [Default Guidance Model](../../../../src/models/weapons/default_guidance_model.cpp)
- [Default Sensor Model](../../../../src/models/systems/default_sensor_model.cpp)
- [Default Hit Effect Model](../../../../src/models/weapons/default_effects_model.cpp)
- [DamageSystem / ProximityFuze](../../../../src/systems/combat/damage_system.h)
- [DataLinkSystem](../../../../src/systems/systems/data_link_system.h)
- [TrackManagerSystem](../../../../src/systems/systems/track_manager_system.h)
- [Python Bindings](../../../../src/interfaces/python/bindings_core.cpp)

Document Purpose:

- After P0 has achieved seeker-only guidance, minimal 3DoF trends, and guard tests, this document consolidates weapon/guidance efforts into a concrete P1 package for continued work.
- Clarifies which P0 shared cleanup items should be completed in P1, which deeper realism items belong to this phase, and which should be deferred to P2.
- Incorporates shared integration issues actually exposed during P0 acceptance into the task package, rather than only ideal models.

---

## 0. P0 Acceptance Snapshot

Minimum results achieved in current P0:

1. Guidance has cut direct dependency on target truth `Transform/Velocity`.
2. Missile has minimal `boost/coast + drag + mass depletion` trends.
3. PN main loop has been switched to "acceleration command + first-order autopilot surrogate + lateral load limit".
4. Guard test [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py) currently passes.
5. Existing weapon chain regression [test_air_combat_1v1_fire_missile.py](../../../../tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py) key hit use cases have been restored to pass.
6. `MissileTuning` shared fields, Python round-trip, launch runtime initialization, and missile runtime debug observation surface have been implemented.
7. `missile_tuning` in weapon definitions can enter the launch chain via loader/weapon station and can be overridden by global tuning overlay.

However, P0 still retains several obvious temporary practices, which are the entry points for P1:

1. `MissileTuning` has been formally extended to include the first batch of P0/P1 shared fields, but some default fallback constants remain in guidance private defaults and have not yet been fully type‑specific calibrated.
2. Launch phase already initializes missile dry mass/propellant mass and `MassProperties`, but guidance still retains a lazy fallback for compatibility with old launch paths.
3. Python/debug exposes major missile runtime state, but the observation/facade interface is still debug‑style and not yet a stable observation surface.
5. Missile attitude/trajectory reference frames still have shared semantic gaps:
   - `MissileGuidance` runs before translational integration;
   - Current main translational path uses `LeapfrogIntegrate`, while old `UpdatePosition` is deprecated;
   - Missile `Transform.heading` is not necessarily synchronized with current velocity track.
6. Seeker/missile/launch parameters have partially entered the database and loader chain, but midcourse/datalink/countermeasure/fuze-damage layering have not yet formed a complete type‑specific configuration surface.
7. Full engineering build may still be blocked by ongoing parallel shared modifications; therefore P1 must address shared API alignment and parallel integration risk together.

After this verification, items 1/2/3/6 above should be regarded as "partially completed but not fully closed", not as "not yet started".

---

## 1. P1 Overall Objective

The goal of P1 is not to "complete full missile weapon science", but to elevate the partial modifications of P0 from guidance‑private workarounds to shareable, parameterizable, and continuously extendable system capabilities.

More precisely, P1 must accomplish two layers of work:

1. **P1 Pre‑integration Cleanup**
   - Consolidate P0's temporary constants, lazy initialization, and debug‑only observation surfaces into formal capabilities of shared runtime / config / binding / database.

2. **P1 Deeper Realism**
   - On the shared basis, complete the first version of seeker type differentiation, midcourse/datalink, parameterized 3DoF, fuze/damage layering, and countermeasure interaction.

---

## 2. P1 Scope Layering

### 2.1 P1 Pre‑integration Cleanup

The criterion for this layer is not "more like a real missile", but "make current P0 logic no longer rely on private patches".

#### A. `MissileTuning` Formal Extension and Shared API Alignment

Must be included in P1.

Reasons:

1. Currently `boost_time / drag / induced drag / propellant fraction / autopilot tau / track memory` are hard‑coded in guidance private headers.
2. Unless these quantities enter shared tuning, subsequent seeker types, database parameters, and model differences cannot be implemented.

Suggested File Scope:

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)

Suggested Minimum Field Set:

```cpp
int seeker_type;
double seeker_activation_range_m;
double seeker_gimbal_limit_deg;
double seeker_ifov_deg;
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

double min_launch_range_m;
double max_launch_off_boresight_deg;
bool lobl_required;
bool midcourse_datalink_supported;
```

Acceptance Criteria:

1. Python can round‑trip set and read these fields.
2. The shared launch path can actually pass tuning to the missile entity, rather than guidance falling back to default constants.
3. Existing tests are not broken by field extension due to aggregate initialization.

#### B. Launch Initialization and Mass Semantic Cleanup

Must be included in P1.

Reasons:

1. The current initialization `Mass{80,0,0}` is still an unrealistic placeholder.
2. The propellant split done in P0 within guidance is a transitional measure that should not remain long‑term.

Suggested File Scope:

- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [dynamics.h](../../../../src/components/physics/dynamics.h)
- [weapon.h](../../../../src/components/combat/weapon.h)

P0 workarounds to remove:

1. Lazy `fuel_mass_kg` assignment inside guidance
2. Lazy `MassProperties` creation inside guidance
3. Runtime default value fallback inside guidance

Expected Shared Semantics:

1. `fire_missile()` directly generates:
   - `Mass{empty_mass_kg, fuel_mass_kg, stores_mass_kg=0}`
   - `MassProperties`
   - Initial `Missile` runtime values
2. At launch, explicitly set:
   - `burnout_time_s`
   - `current_speed_mps`
   - Initial seeker mode

Acceptance Criteria:

1. `debug_get_mass_state()` shows a reasonable dry/fuel split immediately after missile launch.
2. After removing guidance lazy split, existing P0 guard tests still pass.
3. Launch implementation no longer depends on "P0 guidance first‑frame patch" to run.

#### C. Python / Binding / Observation / Debug Exposure Cleanup

Must be included in P1.

Reasons:

1. Currently P0's main acceptance relies on black‑box trend tests; shared API exposes insufficient internal missile state.
2. Subsequent seeker / midcourse / fuze / damage testing will require a more stable observation surface.

Suggested File Scope:

- [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)
- [simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
- [observation.h](../../../../src/core/interfaces/observation.h)

Suggested new or enhanced exports:

1. Full missile tuning fields
2. Missile runtime debug/state view
   - seeker mode
   - has_valid_track
   - filtered bearing/elevation/range
   - commanded / achieved lateral accel
   - current speed
   - burnout time
3. If needed, add an explicit debug API instead of continuing to implicitly reuse other interfaces

Acceptance Criteria:

1. Tests no longer need to infer missile state from implementation details.
2. Seeker memory, activation, and autopilot lag can be verified via Python.

#### D. Shared Reference Frame and Phase Semantic Alignment

Must be included in P1.

This is one of the most critical shared issues exposed during this acceptance.

Problem Description:

1. `MissileGuidance` currently runs before translational integration.
2. The main translational path uses `LeapfrogIntegrate`; old `UpdatePosition` is no longer the main path.
3. The semantics of missile `Transform.heading` for guidance / seeker / debug are unstable.

Consequences:

1. Interpretation of seeker relative bearing easily depends on stale attitude.
2. Guidance internally can only continue with an engineering approximation dominated by current velocity track.
3. To implement seeker gimbal, look angle, and datalink midcourse later, a shared interface must be unified first.

Suggested File Scope:

- [simulation_kernel_systems.cpp](../../../../src/core/engine/simulation_kernel_systems.cpp)
- [guidance_system.h](../../../../src/systems/combat/guidance_system.h)
- [common.h](../../../../src/components/basic/common.h)
- [movement_system.h](../../../../src/systems/physics/movement_system.h)
- [leapfrog_system.h](../../../../src/systems/physics/leapfrog_system.h)

P1 Recommended Goal:

1. Clearly specify that missile guidance uses:
   - `body attitude reference`
   - or `velocity track reference`
2. Ensure that shared runtime has at least one consistent "current missile trajectory/attitude" semantic available.
3. Document the interpretation of seeker relative angle in code and tests, not left in implicit convention.

Acceptance Criteria:

1. The relationship between missile `heading` / `ground track` / seeker relative bearing can be explained by a unit test.
2. Under identical input, guidance does not diverge due to system order or attitude caching differences.

#### E. Database / Loader / Default Parameter Chain

Must be included in P1.

Reasons:

1. Currently missile parameters are mostly stuck in `fire_missile()` default values and a small amount of Python tuning.
2. Without entering the database, subsequent seeker type differences, model differences, and parameter source auditing cannot be stably advanced.

Suggested File Scope:

- [unit_definition.h](../../../../src/content/unit_definition.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)
- `examples/config/database/**`

P1 Goal: Not to build a full weapon library, but to first get the chain working:

1. `Database -> UnitDefinition -> SimulationKernel -> MissileTuning -> fire_missile()`
2. Support at least 1–2 representative air‑to‑air missile parameter templates

Acceptance Criteria:

1. Seeker / mass / thrust / drag basic parameters can be switched via database without changing code constants.
2. Old and new scenarios remain compatible under default configuration.

### 2.2 P1 Deeper Realism

This layer targets "with shared capabilities in place, add a first decent version of weapon physics behavior".

#### A. Seeker Type Differentiation

Should be included in P1.

Rationale:

1. Currently the seeker goes through `Sensor -> ContactList`, but is essentially a unified seeker.
2. `ARH / IR / SARH` at least need different operating modes, activation conditions, and countermeasure resilience.

P1 Minimum Differentiation Goals:

1. `ARH`
   - Support activation range
   - Support midcourse to terminal switching
2. `IR`
   - No range requirement to continue terminal track
   - Support shorter track memory and narrower IFOV
3. `SARH`
   - First version only requires the logic "needs external illumination/data link authorization"

Suggested File Scope:

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

#### B. Midcourse / Datalink / Activation Range

Should be included in P1.

This is the most valuable step between P0 and "BVR air combat ready".

P1 Minimum Goals:

1. Before terminal seeker activation, the missile may use:
   - inertial hold
   - or simplified midcourse guidance via datalink/track cueing
2. Support `seeker_activation_range_m`
3. Support `midcourse_datalink_supported`
4. Support memory / ballistic degradation after terminal switching failure

Suggested File Scope:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)
- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)

Acceptance Focus:

1. ARH missiles do not run in terminal seeker mode from launch throughout flight.
2. When datalink is lost, guidance degrades rather than continuing to enjoy truth‑style midcourse.

#### C. More Realistic 3DoF Parameterization

Should be included in P1, but only to the level of "parameterized + distinguishable by seeker/type", not pursuing P2‑level type replication.

P1 Goals:

1. Switch from guidance private constants to tuning/database parameters.
2. Support different missile:
   - propellant mass
   - boost/sustain duration
   - thrust
   - reference area
   - `Cd0_subsonic / Cd0_supersonic`
   - induced drag
   - max lateral g
3. Keep current `3DoF + accel surrogate` path; do not enter 6DoF.

Suggested File Scope:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- `examples/config/database/**`

#### D. Fuze / Hit / Damage Layering

Should be included in P1, but only the first layer of separation.

The goal of this phase is not full fragment directionality, but to separate the three layers of "intercept, fuze, damage" from the current mixed state.

P1 Minimum Goals:

1. `intercept / miss geometry`
2. `fuze decision`
3. `warhead / damage application`

Recommended First Version:

1. Proximity fuze can still be simplified, but add:
   - arm time
   - impact / proximity distinction
   - more explicit closest point / range‑rate condition
2. Damage layer at minimum:
   - HP path
   - subsystem damage path
   - The relationship between the two no longer conflicts

Suggested File Scope:

- [damage_system.h](../../../../src/systems/combat/damage_system.h)
- [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)

#### E. Countermeasure Interaction

Should be included in P1, but only in simplified form.

P1 Minimum Goals:

1. Flare / chaff are no longer just "strongest signal replacer".
2. Introduce minimal:
   - seduction hysteresis
   - track memory interaction
   - kinematic rejection or angular separation threshold
3. Do not implement full DRFM / RGPO / VGPO / HOJ.

Suggested File Scope:

- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [ew_system.h](../../../../src/systems/systems/ew_system.h)

---

## 3. Items Explicitly Not in P1, Deferred to P2

The following are recommended to be deferred to P2:

1. Full 6DoF missile rigid body, control surfaces, angular velocity and attitude closure
2. Full seeker estimator refactoring to Kalman / IMM or other higher‑order filters
3. Full SARH / HOJ / DRFM / RGPO / VGPO behavior details
4. Full fragment directionality, fragment cone, warhead effectiveness geometric model
5. Full dynamic launch envelope:
   - no‑escape zone
   - loft profile
   - dynamic LAR
6. Type‑level high‑precision parameter replication and performance calibration
7. More complex propulsion models such as dual‑pulse, multi‑stage rocket, ramjet

The boundary of `P1` should always maintain:

- "Shareable, parameterizable, stably testable, capable of explaining trends"
- Rather than "Plug in a high-level model first, then go back and patch the interfaces"

---

## 4. Suggested File Scope

### 4.1 `P1 Pre‑Integration Wrap‑Up`

Suggested main files:

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [weapon.h](../../../../src/components/combat/weapon.h)
- [dynamics.h](../../../../src/components/physics/dynamics.h)
- [simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
- [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)
- [simulation_kernel_systems.cpp](../../../../src/core/engine/simulation_kernel_systems.cpp)
- [guidance_system.h](../../../../src/systems/combat/guidance_system.h)
- [unit_definition.h](../../../../src/content/unit_definition.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)

### 4.2 `P1 Deepening Realism`

Suggested main files:

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)
- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
- [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)
- [damage_system.h](../../../../src/systems/combat/damage_system.h)
- [ew_system.h](../../../../src/systems/systems/ew_system.h)

---

## 5. Minimal Test Checklist

### 5.1 `P1 Pre‑Integration Wrap‑Up`

Suggested minimal tests:

1. `test_missile_tuning_roundtrip_python_to_launch`
   - After setting tuning in Python, the launched entity can obtain the same parameters.
2. `test_missile_mass_is_initialized_at_spawn`
   - Immediately after launch, reasonable dry/fuel mass is visible, not patched only after the first guidance frame.
3. `test_missile_runtime_state_initialized_at_spawn`
   - `burnout_time/current_speed/seeker_mode` exist at launch.
4. `test_missile_heading_or_track_reference_semantics`
   - Explicitly verify against which shared reference frame the seeker bearing is interpreted.
5. `test_missile_runtime_debug_surface_exposed`
   - Python can read seeker memory, accel command, energy state.

### 5.2 `P1 Deepening Realism`

Suggested minimal tests:

1. `test_arh_midcourse_then_terminal_activation`
2. `test_ir_seeker_operates_without_range_measurement_dependency`
3. `test_sarh_requires_external_support_or_degrades`
4. `test_datalink_loss_degrades_midcourse_guidance`
5. `test_parameterized_boost_sustain_profiles_diverge_by_tuning`
6. `test_proximity_vs_impact_fuze_paths_are_distinct`
7. `test_countermeasure_seduction_requires_persistence_or_separation`
8. `test_weapon_p0_guards_still_pass`
9. `test_air_combat_1v1_fire_missile_regression_still_pass`

At acceptance, at least the following must be run:

```bash
CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Suggested additions:

- `tests/runtime/air_combat/test_weapon_guidance_tuning_plumbing.py`
- `tests/runtime/air_combat/test_weapon_guidance_midcourse_datalink.py`
- `tests/runtime/air_combat/test_weapon_fuze_damage_layering.py`

---

## 6. Data Source Implementation Approach

`P1` does not require every missile type to be made into a high‑precision database, but it must first establish a process for “where parameters come from, how trustworthy they are, and how they are implemented.”

A two‑layer storage approach is recommended:

### 6.1 Reference Surface Layer

A dedicated reference table document should be added, recording:

1. Parameter item
2. Value / range
3. Source URL
4. Source date
5. Trust level
6. Whether it is used as:
   - Direct database default value
   - Only for sanity range
   - Only for P2 preliminary research

Recommended source levels:

1. `Level A`
   - JHU APL guidance / flight control
   - NASA drag / atmosphere
   - Official product pages
2. `Level B`
   - Designation-Systems
   - DOT&E / Air & Space Forces and other secondary public sources
3. `Level C`
   - Simulation communities, unofficial databases, forum estimates

### 6.2 Database Implementation Layer

It is recommended to write `P1` parameters into:

- `examples/config/database/**`

And adhere to the following conventions:

1. The database only stores “currently adopted values”
2. The documentation stores “source and trust level”
3. If a value is only an engineering approximation, it must be explicitly labeled:
   - `engineering_approx`
   - `sanity_range_based`
   - `public_source_backed`

Data items recommended for priority implementation:

1. dry mass / propellant mass
2. boost / sustain duration
3. boost / sustain thrust
4. reference area
5. `Cd0_subsonic / Cd0_supersonic`
6. max lateral g
7. seeker activation range
8. seeker IFOV / gimbal / memory timeout
9. fuze distance / arm time / fuze type

---

## 7. Acceptance Criteria

Acceptance of `P1` should not only check “whether it can hit,” but also whether the shared integration is truly closed.

Recommended acceptance criteria:

### 7.1 Acceptance for `P1 Pre‑Integration Wrap‑Up`

1. The full shared launch path can directly initialize missile mass / runtime state, no longer relying on guidance lazy patches.
2. `MissileTuning` can be stably configured through Python and the database.
3. The shared runtime can clearly export key states of missile seeker / energy / autopilot.
4. The heading / track reference semantics on which missile guidance depends are clearly fixed at the system level.
5. `P0` guard tests and key weapon chain regressions still pass.

### 7.2 Acceptance for `P1 Deepening Realism`

1. At least two types of seeker operation modes show observable differences.
2. ARH midcourse guidance and terminal activation can be distinguished, no longer always terminal.
3. Different tunings produce stable differences in the 3DoF performance curves.
4. Countermeasure interaction no longer degenerates to “immediately switch to the strongest signal.”
5. The three layers of hit / fuze / damage are distinguishable in code and tests.

### 7.3 Engineering Acceptance

1. Priority is given to restoring a full build to a working state:

```bash
cmake --build build-workshop -j4
```

2. If parallel changes still block the full build, the blocking ownership and temporary verification path must be clearly identified in the `P1` task, avoiding reliance on partial relinking as a long‑term norm.

---

## 8. Recommended Implementation Order

It is recommended that `P1` proceed in the following order, rather than starting directly with seeker type or fuze.

1. `MissileTuning / launch init / binding` wrap‑up
   - First, make parameters and initialization shareable.
2. `heading / track reference / observation` wrap‑up
   - First, unify the shared semantics of seeker angle and guidance reference frame.
3. `database / loader` wiring
   - Let parameters truly leave guidance‑private constants.
4. `ARH midcourse + activation + datalink`
   - Implement the most critical mode differences in the BVR weapon chain.
5. `IR / SARH` baseline differentiation
   - Create seeker type differences, rather than using one set of logic for three weapon types.
6. `fuze / damage layering`
   - Complete the post‑hit chain.
7. `countermeasure interaction`
   - Finally, add the first version of anti‑jamming / anti‑decoy logic.

---

## 9. P1 Exit Conditions

When the following conditions are met, the weapon/guidance direction can be considered ready to move into `P2`:

1. `P0` workarounds are largely removed from the shared main path.
2. Missile tuning can be configured through the shared API and database.
3. Seeker types have at least completed a first‑version differentiation of `ARH / IR / SARH`.
4. The several modes — midcourse / terminal / memory / ballistic — are testable and observable.
5. Fuze / damage / countermeasure have a first‑version layered logic.
6. The bottleneck for subsequent higher‑level work begins to shift toward “model depth” rather than “shared interface gaps.”
