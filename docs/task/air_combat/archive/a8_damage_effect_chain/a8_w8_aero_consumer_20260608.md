# A8-W8 Wing/Control Aero Consumer

Status: `2026-06-08` narrow implementation slice for `A8-DEC-E`.

## Accepted Scope

This slice connects existing `AircraftDamageState` fields to the maintained
aerodynamic force and moment path:

- structural damage and overstress reduce effective lift and add drag;
- flight-control and hydraulic damage reduce roll, pitch, and yaw authority;
- control asymmetry adds a limited roll/yaw bias through aerodynamic moments.

The slice does not add a direct crash rule, a direct disappearance rule, a
special MQ-9 rule, a real-world lethality claim, or an independent "can fly"
decision. The later aircraft behavior is still produced by the existing flight
simulation.

## Runtime Evidence

- `src/systems/physics/aerodynamics_system.h` now reads
  `AircraftDamageState` and applies limited damage response in aerodynamic
  coefficients and moments.
- `tests/runtime/air_combat/weapon_guidance_realism/a8_aero_consumer.py`
  adds focused checks:
  - F-16 right-aileron damage changes neutral roll and beta response without
    requiring a kill verdict.
  - Fixed MQ-9/AIM-120C right-aileron damage leaves the target active, keeps
    the shot non-authoritative, and changes later roll/beta/speed response
    through the flight path.
  - A 300 s stabilized MQ-9 comparison keeps the clean target near level
    flight while the damaged target loses altitude, slows down, and reaches the
    near-ground response.
- `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py` collects
  the new A8 aero-consumer mixin.

## Validation

Commands run:

```bash
clang-format --dry-run -Werror src/systems/physics/aerodynamics_system.h
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_aero_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'a8_mq9_aim120_right_aileron_damage_changes_roll_response_through_aero_path or wing_control_damage_reaches_neutral_aero_response'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'right_aileron_damage_long_run_reaches_ground_response or right_aileron_damage_changes_roll_response_through_aero_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Outcomes:

- Changed C++ file clang-format gate: pass.
- Focused Python lint: pass.
- Build: pass.
- Focused W8 aero/MQ-9 short response checks: `2 passed, 166 deselected`.
- Focused W8 long-run MQ-9 response checks: `2 passed, 167 deselected`.
- Weapon guidance realism guards: `169 passed`.
- Flight dynamics realism guards: `4 passed`.
- Flight dynamics tuning runtime: `3 passed`.
- 1v1 fire-missile tests: `11 passed`.

## Long-Run Observation

With a stabilized MQ-9 target using `throttle=0.6`, the clean target remains in
level flight after 300 s (`alt_baro ~= 4992.7 m`, `ground_speed ~= 262.1 m/s`).
The fixed AIM-120C-like right-aileron hit leaves the immediate damage report
`destroyed=false`, but over the same 300 s the damaged target reaches near-ground
altitude (`alt_baro ~= 2.0 m`) and slows to about `18.3 m/s`.

This proves a long-run flight effect, not an immediate kill switch. Current
ground-contact handling still leaves the unit observable/active near the ground;
a maintained crash or ground-impact outcome remains a separate follow-up path.

## Residuals

- The control-asymmetry field is scalar. This slice proves a maintained
  response path, not left/right sign fidelity for every damaged surface.
- The coefficient changes are synthetic engineering behavior. They are not
  calibrated aircraft-specific control-law data.
- Full A8 acceptance still needs residual decisions for broader fuel/fire,
  sensor/data-link, and platform-specific consumer fidelity.
- Ground impact or crash-state propagation after a damaged aircraft reaches the
  ground is not yet modeled as a maintained outcome.
