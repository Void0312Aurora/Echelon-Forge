# Default Effects Modularization Closeout

Status: `2026-06-02` closed and archived as a bounded structure cleanup.

Parent:

- [Default Effects Modularization](../README.md)
- [Current status](../default_effects_modularization_current_status_20260601.md)
- [Task clusters](../default_effects_modularization_task_clusters_20260601.md)
- [Closure sync](../default_effects_modularization_closure_sync_20260602.md)

## Closed Scope

This closeout archives the `default_effects_model.cpp` structure-cleanup
subproject after `DFM-P3F` acceptance.

Closed:

- `default_effects_model.cpp` remains the local orchestration entry point.
- Private implementation fragments under `src/models/weapons/detail/` own the
  default-effects helper surfaces.
- Direct-hit, spatial-projection, system-effect, state/result, warhead,
  geometry, component, legacy/fallback, and air-platform resolution helper
  surfaces are split into local detail fragments.
- Air-platform consequence helpers now cover platform-only, aircraft
  sensor/avionics, propulsion/fuel, control/hydraulic, crew-role,
  mission/combat, structure-spatial, fire-zone, and finalize stages.
- `DFM-P4` runtime fixtures cover direct component, protected-system fallback,
  broad spatial near miss, non-broad component-limited near miss, and structured
  air-platform loss/destruct early return.
- The debug early-return validation path records from pre-hit target
  `Transform` and `Velocity` snapshots, so the accepted fixture does not read
  target components after target destruct.

## Validation Recorded

```bash
cmake --build build --target ef_core -j2
# passed

cmake --build build --target ef_py -j2
# passed

CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_dfm_p4_structured_air_platform_loss_early_return_populates_effect_fields --tb=short
# 1 passed in 0.17s

CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k dfm_p4
# 5 passed, 150 deselected in 0.42s

CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
# 155 passed in 33.24s
```

## Residuals

Closed inside this subproject:

- Remaining held aircraft structure-spatial helper extraction.
- Structured air-platform early-return fixture gap.
- Debug event construction crash after target destruct in the accepted fixture.

Still out of scope:

- A project-wide C++ golden/unit harness for the default effects model.
- Public `IEffectsModel` or plugin boundary redesign.
- Warhead physics formula tuning, vulnerability authority promotion, Pk
  authority, deterministic fuze release, or industrial source admission.
- Broader A2 high-fidelity damage-model maturity claims.

## Reopen Rule

Do not append more implementation waves to `DFM-P3`, `DFM-P3B`, `DFM-P3C`,
`DFM-P3D`, `DFM-P3E`, or `DFM-P3F`.

Any future default-effects work must open a new finite task row or subproject
with an explicit write set, validation budget, and forbidden-claim boundary.

## Final Claim Boundary

This archive record proves only a bounded structure cleanup with passing local
build/runtime guards. It does not prove formula correctness, evidence
authority, Pk calibration, deterministic fuze authority, or industrial
admission.
