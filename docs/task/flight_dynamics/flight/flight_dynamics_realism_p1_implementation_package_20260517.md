<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/flight/flight_dynamics_realism_p1_implementation_package_20260517.zh.md. Review before treating this file as authoritative. -->

# Flight Dynamics Realism P1 Implementation Package

Status: `2026-05-17` Draft.

Related Inputs:

- [Flight Dynamics Reality Analysis and Air Combat Prerequisite](flight_dynamics_realism_analysis_20260516.zh.md)
- [Flight Dynamics Realism P0 Implementation Package](flight_dynamics_realism_p0_implementation_package_20260516.zh.md)
- [Realism Task Master List](../program/realism_program_taskboard_20260516.zh.md)
- [P0 Gate Tests](../../../../tests/runtime/test_flight_dynamics_p0_runtime_guards.py)

Document Purpose:

- After `P0` has laid the minimal skeleton, converge the flight dynamics direction into a `P1` package that can be directly scheduled and implemented.
- Clarify that `P1` does not mean "directly implement more complex formulas", but rather first wrap up the integration leftovers from `P0`, then move into deeper realism semantics.
- Provide recommended file scope, minimal test checklist, data source landing approach, and acceptance criteria.

---

## 1. P1 Overall Goal

The goal of `P1` is not "to achieve per-aircraft high fidelity", but to transform the existing flight dynamics skeleton into:

1. Something that can be driven by a database, instead of relying only on code defaults.
2. Something that can be consistently read by instruments, fuel consumption, observations, and tests, rather than each system interpreting it separately.
3. Something that can begin to support more realistic `Mach / compressibility / propulsion transient / stall semantics`, instead of staying at the "trend barely usable" state.

Therefore, `P1` is divided into two layers:

1. `P1 Prerequisite Integration Wrap-up`
2. `P1 Deepened Realism`

The first layer is a prerequisite for the second, and it is not recommended to skip.

---

## 2. P1 Layers and Priorities

### 2.1 Must Do First: P1 Prerequisite Integration Wrap-up

The goal of this layer is to properly integrate the `P0` skeleton into the mainline, instead of remaining in a state where "fields exist in code, defaults work at runtime, but database and interfaces are not yet connected".

Reasons why this must be done first:

- Currently, `AeroTuning / EngineTuning / StallState` have not yet gone through the formal `unit_definition -> loader -> factory` path.
- Currently, propulsion state and stall state have not yet formed a unified source of truth for `instrument / logistics / observation / reward`.
- Currently, `propulsion_system` is still in helper semantics, not yet formally registered as a system boundary.
- Currently, the local `ef_py` / `SimulationKernel` lifecycle in runtime tests still exposes process exit `SIGABRT` issues, and the test infrastructure is not yet stable enough.

### 2.2 Subsequent Priority: P1 Deepened Realism

This layer enters more realistic physical semantics:

- More complete `Mach / compressibility` scheduling
- More realistic engine transients and afterburner semantics
- More realistic stall / post-stall semantics
- Aircraft parameterization and data tables

It is not recommended to proceed directly without completing the first layer, otherwise:

- Parameters can be written but cannot be connected via the database
- Instruments and fuel consumption still do not read from the same state
- Tests can only be written around private default paths, making it impossible to form stable acceptance criteria

---

## 3. P1 Prerequisite Integration Wrap-up

### 3.1 Goal

This layer only addresses the issue of "how to formally connect the P0 skeleton into the mainline".

Acceptance criteria:

1. `AeroTuning / EngineTuning / StallState` can be loaded from the database and attached to entities.
2. `ForceSystem / LogisticsSystem / InstrumentSystem / Observation` interpret propulsion state and stall state consistently.
3. The runtime update boundary of `propulsion` is clear, with `ForceSystem` no longer monopolizing all propulsion logic.
4. Runtime tests no longer rely on subprocess exit workarounds to run stably.

### 3.2 Must-Do Items

#### A. Formalize Tuning Configuration Path

Recommended file scope:

- `/home/void0312/Workshop/CMO/src/content/unit_definition.h`
- `/home/void0312/Workshop/CMO/src/content/unit_definition_loader.cpp`
- `/home/void0312/Workshop/CMO/src/models/core/default_unit_factory.h`
- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`

What needs to be done:

1. Add optional realism fields to `Airframe / Engine / UnitDefinition`.
2. Clarify the mapping of `engine_ref` and `airframe` fields to `EngineTuning / AeroTuning`.
3. Factory mounts during spawn:
   - `AeroTuning`
   - `EngineTuning`
   - `StallState`
4. Maintain backward compatibility:
   - When no new fields exist, still fall back to the current default path.

Acceptance criteria:

- The same aircraft type can be successfully spawned both with and without a tuning configuration.
- No crash when configuration is missing, and current `P0` default behavior is preserved.

#### B. Propulsion State Becomes the Official Shared Source of Truth

Recommended file scope:

- `/home/void0312/Workshop/CMO/src/systems/physics/propulsion_system.h`
- `/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_systems.cpp`
- `/home/void0312/Workshop/CMO/src/systems/physics/force_system.h`
- `/home/void0312/Workshop/CMO/src/systems/systems/logistics_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/instrument_system.h`

What needs to be done:

1. Decide whether `propulsion_system` is formally registered as an independent system.
2. If formally registered:
   - `PropulsionSystem` is responsible for `throttle -> propulsion state`
   - `ForceSystem` only consumes `current_thrust_n`
3. `LogisticsSystem` reads:
   - `current_thrust_n`
   - `current_tsfc`
   - `afterburner_active`
4. `InstrumentSystem` reads the actual propulsion state instead of re-guessing fuel flow and RPM.

Acceptance criteria:

- Thrust, fuel flow rate, and engine RPM all respond consistently to the same throttle step.
- `AB on/off` is consistently observable in thrust, fuel consumption, and RPM.

#### C. Observation / Runtime Test Consistency

Recommended file scope:

- `/home/void0312/Workshop/CMO/src/systems/physics/instrument_system.h`
- `/home/void0312/Workshop/CMO/src/interfaces/python/bindings_core.cpp`
- `/home/void0312/Workshop/CMO/src/core/mission/runtime/execution_observation_runtime.cpp`
- `/home/void0312/Workshop/CMO/tests/runtime/test_flight_dynamics_realism_guards.py`
- `/home/void0312/Workshop/CMO/tests/runtime/test_flight_dynamics_p0_runtime_guards.py`

What needs to be done:

1. Decide which `P1` runtime quantities need observation:
   - `alpha_dot`
   - `stall_progress`
   - `pitch_break_active`
   - `throttle_state`
   - `ab_state`
2. Clarify whether they go only into debugging/instruments or also into training observation.
3. Investigate and fix the current process exit anomaly in runtime tests related to `ef_py` / `SimulationKernel`.
4. Get `P0` new tests back to running as normal in-process, no longer relying on `os._exit(0)` to avoid teardown.

Acceptance criteria:

- Runtime tests can execute stably within the same pytest process.
- The semantics of fields read by instruments, Python bindings, reward/observation are consistent.

### 3.3 Deferrable Items

These are extensions of the prerequisite wrap-up but don't need to block the first batch of implementation:

1. Whether `StallState` enters agent observation.
2. Whether `current_tsfc` directly enters training observation.
3. Whether `propulsion_system` is completely extracted from `force_system` code as a helper.

---

## 4. P1 Deepened Realism

### 4.1 Goal

After the prerequisite integration wrap-up is complete, the `P1` deepening layer advances the current "trend-correct but coarse semantic" parts to the next level:

1. Compressibility and drag rise are no longer just coarse segment compensation.
2. Engine transients and afterburner are no longer just a single first-order lag.
3. Stall and recovery are no longer just `smoothstep + pitch-break surrogate`.
4. At least an initial configurable parameter table for the first batch of aircraft types is formed, not just global defaults.

### 4.2 Must-Do Items

#### A. Deepen Mach / Compressibility Scheduling

Recommended file scope:

- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aero_state_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aerodynamics_system.h`
- If needed:
  `/home/void0312/Workshop/CMO/src/models/environment/default_environment_model.cpp`

Proposed content:

1. Deepen from current one-dimensional scaling to clearer per-term scheduling:
   - `Cl_alpha(M)`
   - `Cd0(M)`
   - `k_induced(M)`
   - `Cm_alpha(M)`
   - `alpha_stall(M)`
2. Expand the "transonic drag rise" from a single `cd0_add_vs_mach` to a more explicit `drag rise schedule`.
3. Clarify whether to introduce segments:
   - Subsonic
   - Transonic
   - Supersonic

Acceptance criteria:

- Drag rises significantly for `M 0.8 -> 1.2`.
- High altitude speed of sound and Mach calculations are consistent with the environment model.
- High Mach/high altitude conditions under the same IAS no longer behave like low-speed linear aerodynamics.

#### B. Deepen Engine Transients / AB Semantics

Recommended file scope:

- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/propulsion_system.h`
- `/home/void0312/Workshop/CMO/src/systems/systems/logistics_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/instrument_system.h`

Proposed content:

1. Model dry thrust and afterburner separately, not just a single `ab_state`.
2. Clarify:
   - idle -> mil
   - mil -> AB light
   - AB stages / partial AB
   - throttle chop / spool down
3. Advance `theta` temperature term from field placeholder to actual usage.
4. If data allows, add simple `installed thrust vs altitude/mach` tables.

Acceptance criteria:

- Time constants differ for idle-to-mil and mil-to-AB transitions.
- Fuel consumption growth is consistent with `AB` state, no longer just a binary multiplier.
- Ram benefit at high Mach has an upper limit, optionally enters decay.

#### C. Deepen Stall / Post-Stall Semantics

Recommended file scope:

- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aerodynamics_system.h`
- `/home/void0312/Workshop/CMO/src/models/air/default_control_model.cpp`
- Optional:
  `/home/void0312/Workshop/CMO/src/systems/physics/control_system.h`

Proposed content:

1. Beyond `stall_progress`, add minimal semantics:
   - onset
   - developed stall
   - recovery
2. Introduce minimal hysteresis, instead of entry/recovery sharing the same static curve.
3. Advance the effect of `alpha_dot` on `Cm` from a simple additive term to a more explicit `Cm_alpha_dot` surrogate.
4. Clarify whether "FBW protection making deep stall difficult to enter" is a design goal or a current distortion.

Acceptance criteria:

- High AoA entry and recovery show reproducible but not fully symmetric trajectories in `AoA / pitch / VVI / g`.
- Recovery semantics are clearer: "reduce AoA first, then restore energy/attitude".
- "Protected high-pitch climb" is no longer mistaken for "post-stall realism".

### 4.3 Deferrable Deepening Items

The following can be clearly deferred to the latter half of `P1` or `P2`:

1. Full `Cl/Cd/Cm/Cn(alpha, beta, M)` 2D/3D tables.
2. `wing rock / spin entry / departure`.
3. Full control surface derivatives and control allocation.
4. Inertia coupling with external stores release and fuel transfer.
5. Turbulence, gusts, wind shear.

---

## 5. Recommended File Scope

### 5.1 P1 Prerequisite Integration Wrap-up

Recommended priority files:

- `/home/void0312/Workshop/CMO/src/content/unit_definition.h`
- `/home/void0312/Workshop/CMO/src/content/unit_definition_loader.cpp`
- `/home/void0312/Workshop/CMO/src/models/core/default_unit_factory.h`
- `/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_systems.cpp`
- `/home/void0312/Workshop/CMO/src/systems/physics/propulsion_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/force_system.h`
- `/home/void0312/Workshop/CMO/src/systems/systems/logistics_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/instrument_system.h`
- `/home/void0312/Workshop/CMO/src/interfaces/python/bindings_core.cpp`

### 5.2 P1 Deepened Realism

Recommended priority files:

- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`
- `/home/void0312/Workshop/CMO/src/components/physics/dynamics.h`
- `/home/void0312/Workshop/CMO/src/components/physics/forces.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aero_state_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aerodynamics_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/propulsion_system.h`
- `/home/void0312/Workshop/CMO/src/models/air/default_control_model.cpp`

---

## 6. Minimal Test Checklist

### 6.1 P1 Prerequisite Integration Wrap-up Tests

Must have:

1. `loader_factory_mounts_flight_dynamics_tuning`
   - Verify `AeroTuning / EngineTuning / StallState` can enter the entity from the database.
2. `propulsion_state_drives_force_logistics_instrument_consistently`
   - Verify thrust, fuel consumption, and RPM are consistent for the same step command.
3. `python_runtime_guards_no_abort_on_kernel_teardown`
   - Verify runtime tests no longer need subprocesses or `os._exit(0)`.

### 6.2 P1 Deepened Realism Tests

Should at least have:

1. `mach_drag_rise_trend`
   - Drag rise clearly visible between `M 0.8~1.2`.
2. `level_accel_vs_altitude_and_mach`
   - Level acceleration capability across altitudes/Mach shows reasonable trends.
3. `engine_spool_and_ab_transition`
   - idle/mil/AB three stages have different responses.
4. `high_aoa_entry_recovery_hysteresis`
   - Entry/recovery are no longer exactly the same path.
5. `default_fallback_still_safe_without_tuning`
   - Missing new fields does not break existing paths.

---

## 7. Data Source Landing Approach

### 7.1 Primary Sources First

Recommended priority:

1. `U.S. Standard Atmosphere 1976`
   - For `rho / T / a / Mach` and high-altitude fallback
2. `FAA Airplane Flying Handbook`
   - For stall/recovery trends and acceptance semantics
3. NASA/NACA public high-AoA, compressibility, stability derivative materials
   - Uplifted to parameter basis only when title, PDF, relevant chapters/tables can be confirmed

### 7.2 Secondary Engineering Materials

Recommended usage:

1. `JSBSim`
   - For engine state machine structure, FDM field organization, trend sanity
2. `AeroBench`
   - For F-16 style state organization, test scenarios, regression sanity

### 7.3 Community/Non-Official Materials

Can be used, but only as initial values or sanity:

1. `BMS / DCS / forum extracted tables`
2. `CMANO / Harpoon / player-compiled databases`
3. Unofficial manual excerpts

Principle:

- Only enter the database when a source link, aircraft context, and unit description are available.
- Values of unverifiable origin do not directly enter default tuning, only candidate reference tables.

### 7.4 Data Landing Form

Recommended new or expanded:

1. `aircraft/modules/engines/*.json`
   - For engine time constants, AB thresholds, TSFC, installed thrust schedule
2. `aircraft/modules/airframes/*.json`
   - For `Cl/Cd/Cm` 1D segments, stall schedule, pitch-break parameters
3. `docs/task/flight_dynamics/<direction>/*.md`
   - Keep a reference table and calibration notes for "data source -> parameter field" in each direction sub-project directory

---

## 8. Acceptance Criteria

### 8.1 P1 Prerequisite Integration Wrap-up Acceptance

Pass criteria:

1. New tuning fields can drive entities via the database.
2. `propulsion` state becomes the consistent source for thrust, fuel consumption, and instruments.
3. Runtime test infrastructure has no known teardown aborts.

### 8.2 P1 Deepened Realism Acceptance

Pass criteria:

1. Trends of `Mach / drag rise / high-altitude speed of sound` are repeatably verifiable.
2. Engine transients show observable stage differences, not a single approximation.
3. High AoA entry/recovery semantics are closer to the real "reduce AoA first, then recover" flow than `P0`.
4. At least 1 aircraft type can be driven by external reference data to produce an explicit tuning, not just eating defaults.

---

## 9. Corrections to P0 Document Wording

It is recommended to use the following unified wording when referencing `P0` results in the future:

1. Do not describe `P0` as "already achieving stall/post-stall realism".
   - More accurate phrasing:
     `P0 has established high-AoA observability, minimal stall progression and a pitch-break surrogate`
2. Do not directly write `NASA TP-1538` as the basis for `P0` numerical fields.
   - More accurate phrasing:
     `Currently usable only as a candidate reference for high-AoA/post-stall phenomena; upgrade after precise title and chapter/table are added`
3. Do not express current `P0` high-AoA behavior as "already possessing deep-stall realism".
   - More accurate phrasing:
     `Current behavior is closer to a protected high-pitch high-AoA trend under FBW/control laws, rather than full post-stall semantics`

---

## 10. Recommended Implementation Sequence

It is recommended to advance `P1` in the following order:

1. First complete the `loader / factory / system registration / instrument / logistics` wrap-up.
2. Then fix runtime tests and `ef_py` lifecycle issues.
3. Then advance `Mach / drag rise / propulsion transient` deepening.
4. Finally enter `stall / post-stall / hysteresis / per-aircraft tables`.

The core reason for this order is:

- First get "how data comes in, how state is shared, how tests are stable" correct,
- Then push forward to "make formulas more realistic",
- This significantly reduces rework and semantic drift.
