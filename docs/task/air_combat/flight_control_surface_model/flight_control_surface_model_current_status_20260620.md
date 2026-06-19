# Flight Control Surface Model — Current Status

Status: `2026-06-20` fixed / validation green. M1-M5 surface mechanism GREEN;
the lateral-directional stability regression and high-attitude recovery
regression are fixed without threshold relaxation.

Parent: [README.md](README.md)

Inputs:

- [Gradient realism principles](../../../standards/foundation/gradient_realism_principles.md)
  (regression rule: a scenario that still runs but is dominated by departure
  must not claim flight-stability realism until restored).
- Mechanism tests: `tests/runtime/air_combat/test_control_surface_mechanism.py`
  (M1-M4), `src/tests/test_control_surface_damage_coupling.cpp` (M5).
- Regression tests: `tests/runtime/air_combat/test_flight_dynamics_realism_guards.py`,
  `tests/runtime/air_combat/test_flight_dynamics_runtime.py`.

## Summary

The control-surface mechanism is functionally complete and its own mechanism
tests pass. Rebuilding `ef_core`+`ef_py` and running the existing flight-dynamics
regression suite revealed that the physical control-surface path exposed a
**manual/RL lateral-directional sign error** that was masked under the old
direct-torque control law. The fix keeps the mission/autopilot coordinated-turn
convention for cruise guards, but uses the physical-surface beta-correcting sign
for manual/RL roll commands. The remaining high-attitude recovery failure was
fixed by extending the existing pitch-attitude protection when the pilot/policy
explicitly commands forward stick.

## What Passes (Accepted Within Scope)

| Area | Status | Evidence |
| --- | --- | --- |
| `ControlSurfaceState` component (cmd vs realized pos) | pass | `src/components/physics/control_surface.h` |
| Actuator first-order lag + finite travel | pass | M3/M4 in `test_control_surface_mechanism.py` |
| Surface deflection observable via debug view | pass | M1 (`elevator_deflection` etc. in `bindings_core.cpp`) |
| Sustained pitch cmd drives elevator deflection | pass | M2 |
| Damage acts on surface effectiveness (pitch/roll/yaw) | pass | M5 doctest (4 cases, 7 assertions) |
| Pipeline registration order (actuator @ 3.45, before aero 3.5) | pass | `simulation_kernel_systems.cpp` |
| Build (`ef_core`+`ef_py`) | pass | clean incremental build |
| Flight-dynamics regression suite | pass | `19 passed` |

## Cleared Regression

Before the fix, four flight-dynamics guard tests failed after the rebuild:

- `test_flight_dynamics_realism_guards::test_roll_response_is_left_right_symmetric`
  — `max_abs_beta = 23.6°` (gate `< 2.0°`).
- `test_flight_dynamics_realism_guards::test_moderate_probes_remain_in_coarse_substall_region`
  — AoA `89.4°` (gate `< 5.0°`).
- `test_flight_dynamics_runtime::test_default_moderate_path_remains_substall_and_finite`
  — `max_aoa = 90.0°` (gate `< 10.0°`).
- `test_flight_dynamics_runtime::test_high_aoa_entry_and_recovery_show_observable_trend`
  — recovered pitch `43.7°` (gate `< entry_pitch − 40`).

These were NOT threshold drift. They were a genuine departure: a moderate stick
input (`pitch 0.25 + roll 0.2`, or `roll 0.3`) drove the airframe out of
controlled flight.

After the fix:

```bash
cmake --build build-workshop --target ef_core ef_py -j4
PYTHONPATH=build-workshop:. python -m pytest -q \
  tests/runtime/air_combat/test_control_surface_mechanism.py \
  tests/runtime/air_combat/test_flight_dynamics_realism_guards.py \
  tests/runtime/air_combat/test_flight_dynamics_runtime.py
# 19 passed

build-workshop/ef_test --test-case=M5*
# 4 passed / 7 assertions

ctest --test-dir build-workshop -R ef_test_all --output-on-failure
# 100% tests passed, 0 tests failed out of 1
```

## Root Cause (Isolated)

### Divergence trace (input `pitch 0.25 + roll 0.2`, ScenarioLoader spawn)

```
step  roll    beta     rud_d     note
30    16.5    -2.92    +0.138    pitch stable, AoA ~4°
40    25.4    -6.20    +0.209    beta growing, rudder not saturated
50    37.8    -9.81    +0.383    beta worsening monotonically
60    56.8    -20.15   +0.720    departs; AoA then couples and blows up
70   101.1    -22.73   +0.982    full departure
```

Pitch axis is stable up to step ~50 (AoA ~4°). The driver is **lateral-
directional**: roll induces sideslip, the coordination loop fails to null it,
sideslip diverges, then couples into pitch and departs.

### Decisive isolation experiment (no recompile)

Pure-rudder step with `roll ≈ 0`:

```
rud_d = +0.222  ->  beta = -21.85°   (rud_d > 0 drives beta NEGATIVE)
rud_d = -0.222  ->  beta = +21.85°
```

Pure right-roll (`+0.3`, no pitch), observe the coordination loop's own output:

```
right roll (roll +)  ->  beta drifts NEGATIVE (adverse yaw)
coordination loop emits rud_d > 0 in response
```

Combine the two facts:

- Adverse yaw from a right roll pushes `beta` negative.
- The coordination loop responds with `rud_d > 0`.
- But `rud_d > 0` independently drives `beta` *more* negative.

=> The coordination rudder is **positive feedback on sideslip**: its sign is
inverted. This is a sign error, not a gain shortfall. Increasing the gain makes
it diverge faster (confirmed by the trace: `rud_d` climbs from 0.14 to 0.98 while
`beta` keeps worsening).

### Mechanism explanation

The control-surface refactor adopted a clean rudder convention in the
aerodynamics/tuning path:

- `cn_delta_r_per_rad = 0.13 > 0` with `rudder_pos > 0 -> positive sim yaw`.

Empirically, on manual/RL roll inputs the realized surface gives
`rud_d > 0 -> beta < 0`. The yaw coordination block in the control law
([default_control_model.cpp](../../../../src/models/domains/air/default_control_model.cpp)
lines ~366-387) was **not updated to the new surface sign** for that control
source. The manual/RL beta correction and ARI feed-forward were still written
against the pre-refactor torque-sign convention.

- coordinated-turn feed-forward `r_turn = (g/V)·sin(phi)·cos(theta)`
- sideslip damper `-beta_gain · beta_rad`
- yaw-rate-error damper `-yaw_rate_gain · (r − r_turn)`

and the aileron-rudder interconnect (ARI) feed-forward
`rudder_cmd += ari_gain · aileron_cmd` (`ari_rudder_cmd_per_aileron_cmd = 0.25`).

Their sign was consistent with each other but inverted relative to the realized
manual/RL control-surface yaw response, so the loop reinforced sideslip instead
of nulling it.

### Relevant default coefficients (F-16 JSON overrides none; all default)

| Coefficient | Default | Source |
| --- | --- | --- |
| `cn_delta_r_per_rad` | 0.13 | `flight_dynamics_tuning.h` |
| `rudder_max_deflection_deg` | 30.0 | `flight_dynamics_tuning.h` |
| `cl_delta_a_per_rad` | 0.10 | `flight_dynamics_tuning.h` |
| `ari_rudder_cmd_per_aileron_cmd` | 0.25 | `flight_dynamics_tuning.h` |
| `Cn_beta` (weathercock) | +0.15 | `aerodynamics_system.h` |
| `Cl_beta` (dihedral) | −0.1 | `aerodynamics_system.h` |
| `Cn_r` (yaw damp) | −0.25 | `aerodynamics_system.h` |

`Cn_beta=0.15` vs max rudder authority `0.13·0.524rad≈0.068` means static
directional stability alone offsets full rudder at only ~26° sideslip, so once
the loop pushes sideslip the wrong way there is little static margin to recover.

## Applied Fix

The applied fix is deliberately narrower than flipping the whole yaw
coordination block:

- manual/RL path: use physical-surface beta correction
  `r_cmd += beta_gain * beta - yaw_rate_gain * r`;
- manual/RL ARI: subtract aileron feed-forward so the rudder opposes observed
  adverse-yaw beta drift;
- mission/autopilot path: retain the existing coordinated-turn feed-forward and
  ARI sign used by cruise/heading guards;
- pitch recovery: extend airborne high-attitude protection to provide stronger
  nose-down q command when `pitch > 35°` and the pilot/policy commands forward
  stick.

This is a control-law correction only; the aerodynamics/tuning surface
convention (`cn_delta_r > 0`) remains unchanged.

### Verification answers

- Pure-stick roll now holds beta inside the regression guard (`max_beta < 2°`).
- The four failing guards returned to GREEN without threshold changes.
- M1-M5 mechanism tests remained GREEN.
- `fbw_off_for_rl` still bypasses this coordination path; relaxed mode shares the
  corrected manual/RL sign with reduced gains.

## Residuals

Follow-on:

- Re-validate frozen takeoff/cruise/landing RL baselines (control response
  changed; user has pre-authorized retraining).
- Sync `air_combat/README.md` index entry if this subproject is promoted into
  the parent current-priority list.

Deferred (separate structural gaps, not part of this fix):

- Axis transform (`V × body_right` lift-direction approximation).
- Velocity-Verlet second force evaluation.
- Gyroscopic / thrust-line offset moments.

## Overclaim Boundary

The lateral-directional and high-attitude recovery regressions are cleared by
the focused guard suite, so the air-combat flight-stability gate is no longer
treated as regressed for this slice. This still must NOT be claimed as
flight-test-calibrated control-surface fidelity, and it does not raise any
scenario gradient-realism level.
