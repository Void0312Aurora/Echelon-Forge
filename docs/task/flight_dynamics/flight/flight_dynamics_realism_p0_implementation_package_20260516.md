<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/flight/flight_dynamics_realism_p0_implementation_package_20260516.zh.md. Review before treating this file as authoritative. -->

# Flight Dynamics Realism P0 Implementation Package

Status: `2026-05-16` P0 kickoff package.

Associated inputs:

- [Flight Dynamics Realism Analysis and Air Combat Prerequisites](flight_dynamics_realism_analysis_20260516.zh.md)
- [AeroStateSystem](../../../../src/systems/physics/aero_state_system.h)
- [AerodynamicsSystem](../../../../src/systems/physics/aerodynamics_system.h)
- [ForceSystem](../../../../src/systems/physics/force_system.h)
- [DefaultControlModel](../../../../src/models/air/default_control_model.cpp)
- [LogisticsSystem](../../../../src/systems/systems/logistics_system.h)
- [DefaultEnvironmentModel](../../../../src/models/environment/default_environment_model.cpp)
- [Flight Dynamics Rough Realism Gate Tests](../../../../tests/runtime/test_flight_dynamics_realism_guards.py)

Document objectives:

- Converge the flight dynamics realism direction into a directly actionable `P0` implementation package.
- Clarify that this round only implements the parameter skeleton, state skeleton, propulsion skeleton, and minimal realism verification.
- Avoid premature expansion into broad aircraft-specific models or full-envelope high-fidelity implementation.

---

## 1. P0 Goals

P0 only solves the problem of "whether subsequent realism can proceed on the correct skeleton", not "whether it is already high-fidelity".

Goals that must be achieved in this round:

1. Establish a stable parameter entry point for aerodynamics and propulsion realism:
   - `aero_tuning`
   - `engine_tuning`
2. Establish minimal runtime state for stall / high-alpha recovery:
   - `alpha_dot`
   - `stall_state`
   - `stall_progress`
3. Establish an independent skeleton for engine transients:
   - `propulsion_system`
   - Thrust state and time constants
   - Consistent interface with fuel system / instruments
4. Establish the first batch of minimal verification tests:
   - Throttle step response
   - Basic observability of `AoA_dot / stall_state`
   - Stall entry and recovery trend gates
   - Parameter default fallback path does not break existing mainline

---

## 2. Non-Goals

The following items are explicitly not part of P0:

1. No full aircraft-level `Cl/Cd/Cm/Cn(M, alpha, beta)` lookup tables.
2. No complete control surface dynamics, control allocation, or `g-command` FBW.
3. No full post-stall/spin/wing rock modeling.
4. No mass property recalculation coupled with external stores release and fuel distribution.
5. No atmospheric enhancements like turbulence, gusts, or microbursts.
6. No air combat strategy retraining; only minimal realism gate tests.

The success criterion for P0 is not "flies like an F-16", but "subsequent P1/P2 can continue working forward without reworking the data structures".

---

## 3. Implementation Scope

### 3.1 Files to Add

Recommended additions:

1. [src/components/physics/flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)
   - Contains `AeroTuning`
   - Contains `EngineTuning`
   - Contains `StallState`
2. [src/systems/physics/propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)
   - Responsible for the propulsion transient from throttle -> thrust state
3. [tests/runtime/test_flight_dynamics_p0_runtime_guards.py](../../../../tests/runtime/test_flight_dynamics_p0_runtime_guards.py)
   - New P0 skeleton tests

### 3.2 Files to Modify

Recommended modifications:

1. [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)
   - Extend `Propulsion`
2. [src/components/physics/forces.h](../../../../src/components/physics/forces.h)
   - Extend `AeroState`
3. [src/content/unit_definition.h](../../../../src/content/unit_definition.h)
   - Add optional realism fields for `Airframe` / `Engine`
4. [src/content/unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
   - Read tuning fields
5. [src/models/core/default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)
   - Mount `AeroTuning` / `EngineTuning` / `StallState`
6. [src/systems/physics/aero_state_system.h](../../../../src/systems/physics/aero_state_system.h)
   - Generate `alpha_dot`
7. [src/systems/physics/aerodynamics_system.h](../../../../src/systems/physics/aerodynamics_system.h)
   - Read `AeroTuning`
   - Update `stall_state / stall_progress`
8. [src/systems/physics/force_system.h](../../../../src/systems/physics/force_system.h)
   - Switch from "directly calculate thrust" to "consume propulsion state"
9. [src/systems/systems/logistics_system.h](../../../../src/systems/systems/logistics_system.h)
   - Fuel consumption reads actual thrust state
10. [src/systems/physics/instrument_system.h](../../../../src/systems/physics/instrument_system.h)
    - Instruments read actual engine state
11. [src/core/engine/simulation_kernel_systems.cpp](../../../../src/core/engine/simulation_kernel_systems.cpp)
    - Register `propulsion_system`

---

## 4. Field Design

### 4.1 `AeroTuning`

Location recommendation:

- [src/components/physics/flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)

P0 only uses 1D piecewise segments and a few scalars; no 2D lookup tables.

Recommended fields:

```cpp
struct AeroTuning {
    bool enabled = false;

    double cl_alpha_per_deg = 0.1;
    double cl0 = 0.0;
    double cd0_clean = 0.02;
    double induced_drag_k = 0.1;
    double cm_alpha_per_rad = -0.8;
    double cm_q = -12.0;

    double alpha_stall_clean_deg = 15.0;
    double alpha_stall_flaps_full_deg = 21.0;
    double alpha_peak_offset_deg = 8.0;
    double alpha_deep_offset_deg = 18.0;

    double cl_peak_clean = 1.25;
    double cl_peak_flaps_full = 1.70;
    double cl_deep_clean = 0.22;
    double cl_deep_flaps_full = 0.32;

    double pitch_break_onset_deg = 16.0;
    double pitch_break_full_deg = 28.0;
    double pitch_break_cm_nose_down = -0.35;

    double post_stall_damp_floor = 0.25;

    std::vector<double> mach_breakpoints;
    std::vector<double> cl_alpha_scale_vs_mach;
    std::vector<double> cd0_add_vs_mach;
    std::vector<double> induced_drag_scale_vs_mach;
    std::vector<double> cm_alpha_scale_vs_mach;
    std::vector<double> stall_alpha_delta_deg_vs_mach;
};
```

Design intent:

- When `enabled=false`, keep current default behavior to avoid impacting the entire repository at once.
- `mach_breakpoints + values` are sufficient to support compressibility corrections in P1 without introducing a complex table engine first.
- `pitch_break_*` is critical for P0 because it determines whether the subsequent recovery trend can emerge from aerodynamics rather than being forced by FBW.

### 4.2 `EngineTuning`

Location recommendation:

- [src/components/physics/flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)

Recommended fields:

```cpp
struct EngineTuning {
    bool enabled = false;

    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;

    double throttle_ab_threshold = 0.9;
    double throttle_idle_bias = 0.1;

    double tau_spool_up_s = 2.5;
    double tau_spool_down_s = 1.5;
    double tau_ab_light_s = 1.0;
    double tau_ab_extinguish_s = 0.5;

    double ram_rise_gain = 0.3;
    double ram_rise_mach_cap = 1.2;
    double ram_decay_start_mach = 1.5;
    double ram_decay_gain = 0.2;

    double thrust_sigma_exponent = 1.0;
    double thrust_theta_exponent = -0.5;

    double tsfc_mil_kg_per_ns = 0.0;
    double tsfc_ab_kg_per_ns = 0.0;
};
```

Design intent:

- `tau_spool_*` are the most important new physical time constants in P0.
- `ram_*` allows moving the existing `1 + 0.3M` from hardcoded to a configurable layer.
- `sigma/theta` reserve entry points for temperature effects, but P0 only requires the fields to be in place.

### 4.3 `Propulsion` Runtime State

Modification location:

- [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)

Recommended new fields:

```cpp
double throttle_command = 0.0;
double throttle_state = 0.0;
double dry_thrust_command_n = 0.0;
double dry_thrust_state_n = 0.0;
double ab_command = 0.0;
double ab_state = 0.0;
double current_tsfc = 0.0;
```

Notes:

- Keep `current_thrust_n` and `afterburner_active` to avoid affecting existing external interfaces.
- `throttle_state` and `ab_state` let `ForceSystem / LogisticsSystem / InstrumentSystem` share the same source of truth.

### 4.4 `AeroState` and `StallState`

Modification locations:

- [src/components/physics/forces.h](../../../../src/components/physics/forces.h)
- [src/components/physics/flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)

Recommended new fields:

```cpp
struct StallState {
    double stall_progress = 0.0;
    double time_in_stall_s = 0.0;
    bool is_stalled = false;
    bool pitch_break_active = false;
};
```

```cpp
// in AeroState
double angle_of_attack_rate_dps = 0.0;
double previous_angle_of_attack = 0.0;
```

Notes:

- P0 does not introduce a complex stall memory model, but at least allows observation of "whether stall has been entered" and "how fast alpha is changing".
- `pitch_break_active` is for testing and debugging, and also reserves an exit for future instruments and failfast fallback logic.

---

## 5. System and Code Placement

### 5.1 `propulsion_system`

New file:

- [src/systems/physics/propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)

Responsibility boundary:

1. Read the throttle command after control input processing.
2. Read `EngineTuning`.
3. Integrate:
   - `throttle_command -> throttle_state`
   - `dry_thrust_command -> dry_thrust_state_n`
   - `ab_command -> ab_state`
4. Calculate:
   - `current_thrust_n`
   - `afterburner_active`
   - `current_tsfc`
5. Do not directly apply force to `ForceAccumulator`.

Recommended registration order:

`AeroStateSystem -> PropulsionSystem -> ForceSystem -> AerodynamicsSystem`

This way `PropulsionSystem` can read the same frame's atmospheric and Mach data without overlapping responsibilities with `ForceSystem`.

### 5.2 `force_system`

Modification principles:

- Keep gravity application.
- Keep nose-direction thrust projection.
- Remove the main logic that directly computes thrust from throttle instantaneously.
- Change to consuming `Propulsion.current_thrust_n`.

This step is the most critical boundary convergence in P0:

- `ForceSystem` is responsible for "applying the existing thrust state to the airframe".
- `PropulsionSystem` is responsible for "determining this thrust state".

### 5.3 `aero_state_system`

P0 adds only one core capability:

- `angle_of_attack_rate_dps`

Implementation:

1. Compute `alpha_raw` each frame.
2. Differentiate as `alpha_raw - previous_angle_of_attack`.
3. Apply minimal unwrap / clamping.
4. Update `previous_angle_of_attack`.

Not done in P0:

- `beta_dot`
- Complex filters
- Dynamic stall models

### 5.4 `aerodynamics_system`

P0 does only three things:

1. When `AeroTuning.enabled=false`, keep current default logic.
2. When `enabled=true`:
   - Use `mach_breakpoints` for 1D scheduling of `Cl_alpha/Cd0/k/Cm_alpha/stall_alpha`.
3. Update `StallState`:
   - `stall_progress`
   - `is_stalled`
   - `pitch_break_active`

P0 recommends adding only a minimal `pitch_break` term:

```text
Cm_total = Cm_baseline + Cm_pitch_break(alpha, stall_progress)
```

Not done in P0:

- `Cm_alpha_dot`
- `Cn_p`
- Asymmetric negative-alpha stall
- Second-order coupling of `beta` on lift and stall

### 5.5 `logistics_system` and `instrument_system`

Both must keep pace with the `Propulsion` state synchronously, otherwise internal inconsistencies arise:

1. [logistics_system.h](../../../../src/systems/systems/logistics_system.h)
   - Change from "burn fuel based on throttle" to "burn fuel based on `current_tsfc * current_thrust_n`".
2. [instrument_system.h](../../../../src/systems/physics/instrument_system.h)
   - `fuel_flow_kg_h`, `engine_rpm_pct` should read `throttle_state / ab_state / current_tsfc`.

---

## 6. External Data Placement

### 6.1 Data Source Hierarchy

P0 only requires opening the data entry point; not all fields need official values.

Priority recommendations:

1. `Primary official/research`
   - NASA TP-1538
   - US Standard Atmosphere 1976
   - FAA Jet Aircraft Flight Manuals
2. `Open simulation baselines`
   - AeroBenchVVPython / AeroBenchVV
   - JSBSim / FlightGear F-16
3. `Community references`
   - EM diagrams, manual excerpts, forum summaries

### 6.2 In-Repository Placement

P0 does not create a new data directory; reuse the existing database structure:

1. Engine parameters:
   - `examples/config/database/aircraft/modules/engines/*.json`
2. Aerodynamic / airframe parameters:
   - First phase: place in `examples/config/database/aircraft/units/*.json`
   - If multi-aircraft sharing is needed later, extract to `modules/aero/`

### 6.3 Recommended JSON Form

Engine module should support:

```json
{
  "name": "f110_ge_129",
  "type": "Engine",
  "mil_thrust_n": 76000.0,
  "ab_thrust_n": 129000.0,
  "sfc_mil": 0.0,
  "sfc_ab": 0.0,
  "engine_tuning": {
    "enabled": true,
    "tau_spool_up_s": 2.5,
    "tau_spool_down_s": 1.5,
    "tau_ab_light_s": 1.0,
    "tau_ab_extinguish_s": 0.5,
    "ram_rise_gain": 0.3,
    "ram_rise_mach_cap": 1.2,
    "ram_decay_start_mach": 1.5,
    "ram_decay_gain": 0.2
  }
}
```

Airframe should support:

```json
{
  "name": "f16c_block50",
  "type": "Aircraft",
  "airframe": {
    "empty_mass_kg": 8570.0,
    "max_fuel_kg": 3100.0,
    "reference_area": 27.87,
    "wingspan_m": 9.45,
    "length_m": 15.06,
    "height_m": 4.88
  },
  "aero_tuning": {
    "enabled": true,
    "alpha_stall_clean_deg": 15.0,
    "pitch_break_onset_deg": 16.0,
    "pitch_break_full_deg": 28.0,
    "pitch_break_cm_nose_down": -0.35,
    "mach_breakpoints": [0.0, 0.6, 0.9, 1.1, 1.5, 2.0],
    "cl_alpha_scale_vs_mach": [1.0, 1.0, 1.12, 0.95, 0.75, 0.60],
    "cd0_add_vs_mach": [0.0, 0.0, 0.01, 0.035, 0.02, 0.015]
  }
}
```

### 6.4 P0 Data Usage Principles

1. Prefer "approximation with clear provenance" over continuing to hardcode key effects in the system.
2. All non-official parameters must annotate the source level:
   - `official`
   - `research-derived`
   - `community-reference`
3. Documentation or comments must indicate whether a value is a "trend-constrained value" or a "fitted/approximate working value".

---

## 7. Test Checklist

### 7.1 Mandatory New P0 Tests

Recommended new file:

- [tests/runtime/test_flight_dynamics_p0_runtime_guards.py](../../../../tests/runtime/test_flight_dynamics_p0_runtime_guards.py)

Cover the following items:

1. `throttle_step_response_is_not_instant`
   - `idle -> mil`
   - `mil -> ab`
   - Verify that `current_thrust_n` does not jump to full value in one step.
2. `fuel_flow_tracks_actual_thrust_state`
   - Verify that changes in thrust state cause synchronous changes in fuel flow.
3. `aoa_dot_is_reported_and_finite`
   - Under a basic pitch-up probe, `AoA_dot` is finite and has a reasonable sign.
4. `stall_state_enters_before_failfast_like_departure`
   - Verify that under high alpha, the system enters `stall_state` first.
   - Not only triggering departure logic at extreme attitudes.
5. `pitch_break_adds_nose_down_recovery_trend`
   - Under the same initial conditions, enabling `pitch_break` should produce an earlier nose-down recovery trend.
6. `disabled_tuning_preserves_legacy_behavior_envelope`
   - When `enabled=false`, basic contracts should not be significantly broken.

### 7.2 Recommended Expansion of Existing Gate Tests

Add two types of assertions to [test_flight_dynamics_realism_guards.py](../../../../tests/runtime/test_flight_dynamics_realism_guards.py):

1. Record peak `AoA_dot`.
2. Record whether `stall_state` was triggered.

This way the newly added P0 states immediately enter the existing gate perspective.

### 7.3 Tests Not Required for P0

The following tests are deferred to P1/P2:

1. Quantitative transonic envelope verification.
2. Full EM diagram trend verification.
3. High-altitude high-speed acceleration time calibration.
4. Multi-aircraft parameter regression matrix.

---

## 8. Recommended Implementation Sequence

Proceed in 6 steps.

### Step 1. Land Component and Configuration Skeleton First

Goals:

- Add `flight_dynamics_tuning.h`.
- Extend `Propulsion`.
- Extend `AeroState`.
- Extend `UnitDefinition` and loader.

Completion criteria:

- Runtime logic unchanged.
- Existing tests behave identically with default values.

### Step 2. Mount Default Factory and Database Reading

Goals:

- `default_unit_factory` attaches `AeroTuning` / `EngineTuning` / `StallState` to entities.
- `f16c_block50` / `f110_ge_129` each get a minimal tuning entry.

Completion criteria:

- Entities can read configuration.
- But when not enabled, the dynamics mainline remains unchanged.

### Step 3. Add `propulsion_system`

Goals:

- Implement throttle state / AB state / current thrust skeleton.
- Register in the system ordering.

Completion criteria:

- `ForceSystem` still runs.
- `current_thrust_n` is now generated by the new system.

### Step 4. Connect Fuel and Instrument Consistency

- `logistics_system` reads actual thrust state
- `instrument_system` reads actual engine state

Completion criteria:

- Thrust, fuel, and RPM are on the same state chain

### Step 5. Engage `AoA_dot / StallState / minimal pitch break`

Objective:

- `aero_state_system` outputs `AoA_dot`
- `aerodynamics_system` updates `stall_state`
- Add a minimal `pitch_break` torque term

Completion criteria:

- No pursuit of high fidelity
- Only requirement: after high angle of attack entry, a more decent recovery trend can be observed

### Step 6. Add P0 tests and regression

Objective:

- Supplement `test_flight_dynamics_p0_runtime_guards.py`
- Run existing `test_flight_dynamics_realism_guards.py`

Completion criteria:

- New P0 test passes
- Existing gate tests are not significantly broken

---

## 9. Startup Notes

1. The biggest risk of P0 is not that the formulas are insufficiently accurate, but that the state is scattered across multiple systems, causing rework every time a realism addition is needed later.
2. `propulsion_system` must first settle who is responsible for computing the thrust state.
3. `stall_state` must first be placed into an observable layer; otherwise it is difficult later to distinguish between "true insufficient recovery" and "the controller is merely suppressing symptoms."
4. All tuning must allow `disabled=false/true` fallback to ensure coexistence with the existing training pipeline.

---

## 10. P0 Completion Criteria

P0 is considered complete when the following conditions are met:

1. `AeroTuning / EngineTuning / StallState / Propulsion state` have entered the repository main structure.
2. `Force / Logistics / Instruments` already operate based on the same propulsion state chain.
3. `AoA_dot` and `stall_state` can already be observed in runtime tests.
4. The newly added minimal P0 gate test passes.
5. Existing flight dynamics coarse realism gate tests show no significant regression.

After P0 is complete, P1 is suitable for further advancement:

- More complete compressibility corrections
- Finer stall / recovery curves
- Aircraft-specific engine thrust tables
- More credible FBW envelope scheduling
