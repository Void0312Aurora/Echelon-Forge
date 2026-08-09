# Flight Control Surface Model Task Clusters

Status: `2026-06-20` complete. Finite task-cluster plan for
[`README.md`](README.md); implementation and regression validation are green.

## Boundary Decision

This subproject may add a control-surface state component, control-power
derivatives, an actuator-dynamics system, and the aero moment terms that route
control authority through surface deflection. It may modify the FBW law's output
target (from direct torque to surface command) and the kernel pipeline order.

It must not:

- claim flight-test calibration authority for proxy control derivatives;
- raise any scenario's gradient-realism level;
- alter weapon, sensor, or damage-effect chains beyond reading existing
  `*_control_integrity`;
- silently retune unrelated aero/propulsion constants.

## Finite Task Cluster List

| Cluster | Owner | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P1-A` | main thread | RED tests encoding control-surface mechanism | `tests/runtime/air_combat/test_control_surface_mechanism.py` | no impl | mechanism tests now GREEN | mechanism assertions retained | none | 2 | `complete` |
| `P2-A` | main thread | `ControlSurfaceState` component + `AeroTuning` control derivatives | `src/components/**`, `flight_dynamics_tuning.h` | no pipeline wiring | `ef_core` compiles | component/tuning defined | after P1-A | 2 | `complete` |
| `P2-B` | main thread | Actuator system + aero moment routing + FBW output change | `aerodynamics_system.h`, `default_control_model.cpp`, new actuator system header | no kernel order yet | `ef_core` compiles | logic implemented | after P2-A | 3 | `complete` |
| `INT-A` | main thread | Kernel pipeline order + spawn defaults + binding exposure | `simulation_kernel_systems.cpp`, factory/spawn | no new behavior | `ef_core`+`ef_py` build; mechanism tests GREEN | runtime mechanism exposed | after P2-B | 3 | `complete` |
| `P4-A` | main thread | Re-run realism guards + runtime suite; record baseline impact | control-law fix only; no threshold relaxation | no scope creep | guard + runtime suites | `19 passed` | after INT-A | 2 | `complete` |
| `CLOSE-A` | main thread | Sync README/index/residuals | this subproject docs | no impl | doc diff check | subproject docs synced | after P4-A | 1 | `complete` |

## Dispatch Rules

- Every worker packet maps to exactly one cluster above.
- Keep acceptance/closure clusters serial.
- If a cluster exceeds its round cap, stop and re-scope.
- Follow [Subagent Usage Policy](../../../../engineering/automation/standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
# Build first — new C++ component/system/tuning requires recompiled bindings.
cmake --build build-workshop --target ef_core ef_py -j4
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q \
  tests/runtime/air_combat/test_control_surface_mechanism.py \
  tests/runtime/air_combat/test_flight_dynamics_realism_guards.py \
  tests/runtime/air_combat/test_flight_dynamics_runtime.py

build-workshop/ef_test --test-case=M5*
ctest --test-dir build-workshop -R ef_test_all --output-on-failure
```

## Acceptance Criteria

- Control moment scales with `q_bar` and Mach via surface deflection (tested).
- `*_control_integrity` reduces moment through the surface (tested).
- Flight-dynamics realism guards pass or changed thresholds re-justified.
- No calibration-authority overclaim in docs.

## Residual Map

Immediate:

- Proxy control derivatives need F-16-magnitude anchoring.

Follow-on:

- Velocity-Verlet second force evaluation.
- Lift-axis (stability/wind axis) transform.

Deferred:

- Gyroscopic / thrust-offset moments; hinge moments; aeroelasticity.
