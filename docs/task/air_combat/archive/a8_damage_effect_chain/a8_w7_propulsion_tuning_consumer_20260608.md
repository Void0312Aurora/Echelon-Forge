# A8-W7 Propulsion Tuning Consumer

Status: `2026-06-08` narrow implementation slice for `A8-DEC-E`.

## Runtime Change

`ComputePropulsion` now receives the aircraft damage state when resolving runtime
engine tuning. If an aircraft has explicit engine tuning with authored thrust
values, propulsion damage scales those tuned thrust values before spool/thrust
calculation. This closes the W5 risk where active tuning could overwrite the
damaged `Propulsion` limits computed by `AircraftDamageStateUpdate`.

The slice keeps the effect inside the maintained propulsion path:

```text
part damage -> AircraftDamageState.propulsion_integrity
-> runtime engine tuning thrust cap
-> Propulsion.current_thrust_n
-> force integration
```

## Boundary

This does not add a direct crash, disappearance, target-specific kill rule,
probability-of-kill claim, deterministic fuze claim, or independent can-fly
verdict. The aircraft still flies, slows, burns fuel, leaks, or eventually loses
control only through the maintained systems.

## Test Evidence

A focused A8 test now creates a test-only F-16 variant with explicit engine
tuning, applies a profiled hit to `engine_core`, and checks that both the thrust
limit and actual current thrust drop after damage.

Validated on `2026-06-08` with:

```bash
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_a8_engine_damage_scales_actual_thrust_with_explicit_engine_tuning
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
```

Outcomes: build pass, focused A8 propulsion consumer test `1 passed`, weapon
guidance realism guards `166 passed, 239 subtests passed`, and flight dynamics
tuning runtime `3 passed`, 1v1 fire-missile tests `11 passed, 2 subtests
passed`, and flight dynamics realism guards `4 passed`.

## Residuals

The next `A8-DEC-E` slice should target one wing/control aerodynamic response:
control-surface or structural damage should become visible in forces, moments,
or axis authority without adding a shortcut crash rule.
