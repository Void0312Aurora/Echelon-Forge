# A8-W4 Public Failure Mode Rows

Status: `2026-06-07` integration slice for `A8-DEC-C/D`.

## Public Row Shape

`ComponentMechanismLoadRow` now exposes the internal A8 part-failure mode
assessment as binding-friendly row fields:

- `component_failure_primary_mode`
- `component_failure_primary_mode_severity`
- `component_failure_mode_names`
- `component_failure_mode_severities`
- `component_failure_mode_source`
- `component_failure_mode_authority`

Names and severities are parallel vectors. The source is either
`synthetic_inferred_part_failure_modes` for inferred mode assessments or
`component_failure_mode_weights` when a component explicitly weights the
simulated vocabulary. `component_failure_mode_authority` remains false; these
fields name the simulated damage path, not real-world lethality or calibrated
probability of kill.

## Vocabulary

The public rows can expose the W2 vocabulary already used by the internal
effects path:

- `puncture`
- `cut`
- `blast_deformation`
- `fuel_leak`
- `hydraulic_pressure_loss`
- `electrical_loss`
- `data_loss`
- `fire_source`
- `structural_weakening`

## Boundary

This slice does not add flight, aerodynamic, propulsion, or direct crash
behavior. No MQ-9 special rule, deterministic fuze authority, Pk claim, or
independent can-fly verdict is introduced. No-detonation shots still have no
component rows and therefore no fabricated failure modes.

## Acceptance

Validated on `2026-06-07` with:

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain src/runtime/contracts/engagement_contracts.h src/interfaces/python/bindings_runtime.cpp src/models/weapons/detail/default_effects_component_damage_detail.inc src/models/weapons/detail/default_effects_system_effect_detail.inc tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py tests/runtime/air_combat/weapon_guidance_realism/component_damage.py
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/engagement/test_engagement_contract_shape.py
```

Outcomes: diff check pass, build pass, `165 passed` for the realism guards,
`11 passed` for 1v1 fire-missile tests, and `4 passed` for engagement contract
shape tests.
