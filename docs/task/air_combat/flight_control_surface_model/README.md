# Flight Control Surface Model

Status: `2026-06-20` `implemented / validation green` — platform-level FDM
mechanism completion: the broken
`stick -> actuator -> control-surface deflection -> aerodynamic control moment`
causal chain is closed for the maintained runtime. Not combat-specific; placed
here because `air_combat/` is the active air/execution task entry per the task
root.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; high-churn implementation slice.

Inputs:

- [air_combat task track](../README.md)
- [task root](../../README.md)
- [Gradient Realism Principles](../../../standards/foundation/gradient_realism_principles.md)
- [Realism Authority Boundary](../../../standards/foundation/realism_authority_boundary.zh.md)
- Code entries:
  - `src/models/domains/air/default_control_model.cpp` (FBW law, now writes
    physical surface commands)
  - `src/systems/domains/air/aerodynamics_system.h` (aero moments)
  - `src/components/domains/air/platform/flight_dynamics_tuning.h` (`AeroTuning`)
  - `src/components/physics/control_law.h` (`ControlLawState`)
  - `src/components/domains/air/combat/damage_air.h` (`AircraftDamageState`
    `*_control_integrity`)
  - `src/core/engine/simulation_kernel_systems.cpp` (pipeline order)
- Tests:
  - `tests/runtime/air_combat/test_control_surface_mechanism.py`
  - `src/tests/test_control_surface_damage_coupling.cpp`
  - `tests/runtime/air_combat/test_flight_dynamics_realism_guards.py`
  - `tests/runtime/air_combat/test_flight_dynamics_runtime.py`

## Purpose

The maintained flight model already integrated real 6DOF rigid-body dynamics
with stability derivatives, but before this subproject the *control* path
bypassed aerodynamics: the FBW law in `default_control_model.cpp` converted
stick demand into a body-rate command and emitted a control torque directly as
`M = q_bar * K * (rate_cmd - rate)`. There was no control-surface state, no
actuator dynamics, and no control-power derivatives (`Cm_delta_e`,
`Cl_delta_a`, `Cn_delta_r`).

This was a genuine causal-structure gap, not a data-calibration gap. The damage
system already computed `roll/pitch/yaw_control_integrity`, but the aero side
could only scale a synthesized torque magnitude because there was no physical
surface to carry the effect.

This subproject restored the causal chain so control authority is produced by
surface deflection acting through dynamic pressure and Mach, and so control
degradation has a physical carrier. Per
[Gradient Realism Principles](../../../standards/foundation/gradient_realism_principles.md),
this strengthens causal structure and consequence chains; it does not by itself
raise any scenario's claimed gradient level.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Control torque causal chain | `pass` | `default_control_model.cpp` writes `ControlSurfaceState` commands; `aerodynamics_system.h` consumes actual deflection | Does not claim flight-test calibration |
| Control-power derivatives | `pass` | `AeroTuning` has `Cm_delta_e`, `Cl_delta_a`, `Cn_delta_r`, deflection limits, Mach scaling | Proxy values; not flight-test calibrated |
| Actuator dynamics | `pass` | `actuator_system.h`, pipeline order before aero | First-order proxy only |
| Damage -> control coupling | `pass` | M5 doctest: 4 cases / 7 assertions | Damage reduces surface effectiveness, not direct kill authority |
| Flight-dynamics regression | `pass` | realism guards + runtime suite: 19 Python tests passed | Does not raise scenario gradient level |

## Scope

In scope:

- Add a `ControlSurfaceState` component (commanded + actual deflection per axis).
- Add control-power derivatives to `AeroTuning` with Mach scaling, reusing the
  existing `mach_breakpoints` mechanism.
- Add an actuator-dynamics system (first-order lag + rate/position limit) between
  Control and Aerodynamics in the pipeline.
- Route control moments through `Cm_delta_e * delta_e` etc. in the aero system,
  modulated by `q_bar`, Mach, and `*_control_integrity`.
- RED-first tests asserting the new mechanism.

Out of scope:

- Flight-test-calibrated control derivatives (proxy values only; no precision
  authority claim).
- Per-surface geometry, hinge moments, aeroelastic coupling.
- Raising any scenario gradient claim.
- Changing weapon, sensor, or damage-effect chains.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope/authority and confirm gap is real. | gap verified by symbol search | this README accepted | `complete` |
| `P1 Evidence` | RED tests encode the missing mechanism. | P0 | tests fail for the right reason | `complete` |
| `P2 Implementation` | Add component, tuning, actuator system, aero moment terms. | P1 | code compiles (`ef_core`+`ef_py`) | `complete` |
| `P3 Integration` | Wire pipeline order and binding/spawn defaults. | P2 | RED tests pass | `complete` |
| `P4 Validation` | Re-run realism guards + runtime suite; record baseline impact. | P3 | guards pass without threshold relaxation | `complete` |
| `P5 Closure` | Sync docs/index; record residuals. | P4 | subproject docs synced; parent promotion optional | `complete` |

## Task Clusters

- Task cluster plan: `flight_control_surface_model_task_clusters_20260619.md`

## Outputs And Evidence

- New: `src/components/physics/control_surface.h`.
- Modified: `flight_dynamics_tuning.h`, `aerodynamics_system.h`,
  `default_control_model.cpp`, `simulation_kernel_systems.cpp`.
- New tests: `tests/runtime/air_combat/test_control_surface_mechanism.py`,
  `src/tests/test_control_surface_damage_coupling.cpp`.

## Acceptance Gate

This subproject can be marked accepted only when:

- the control-surface causal chain exists and is exercised by the runtime;
- control moment provably scales with dynamic pressure and Mach via surface
  deflection (test evidence);
- `*_control_integrity` reduces control moment through the surface, not a
  synthesized magnitude;
- existing flight-dynamics realism guards pass, or any changed threshold is
  re-justified as a mechanism improvement, not a regression;
- documentation claims no flight-test calibration authority for the proxy
  derivatives.

## Residuals And Next Steps

- Calibrate control-power derivatives against published F-16 control response
  envelopes (held; proxy values until then).
- Velocity-Verlet second force evaluation, lift-axis transform, gyroscopic /
  thrust-offset moments remain separate FDM-mechanism residuals.

## Archive

No superseded records yet.
