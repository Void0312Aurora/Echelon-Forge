# Default Effects Modularization Closure Sync

Status: `2026-06-02 DFM-P6 closure sync / Ramanujan mission-combat helper pass / paused`.

Subproject:

- [README.md](README.md)
- [Task clusters](default_effects_modularization_task_clusters_20260601.md)
- [Current status](default_effects_modularization_current_status_20260601.md)

## Scope Accepted In This Sync

This sync records a narrow continuation after the round-1 `DFM-P4` / `DFM-P5`
fixture hardening:

- `default_effects_air_platform_resolution_detail.inc` now has a named
  `apply_default_effects_platform_air_consequence_blocks` helper for the
  platform-only air consequence and clamp block.
- Gibbs (`019e840c-2ad1-75d0-97ff-d3f5b3121586`) returned `pass` for the
  source-only `DFM-P3` continuation, adding a named
  `apply_default_effects_aircraft_fire_zone_consequence_blocks` helper.
- Curie (`019e842a-9b61-7960-9d11-81763304e738`) returned `pass` for the
  next source-only `DFM-P3` continuation, adding a named
  `apply_default_effects_aircraft_propulsion_fuel_consequence_blocks` helper.
- Feynman (`019e842b-5927-7a92-ae65-fff4fab5f21d`) returned `pass` for
  read-only diagnostics and recommended that additional source extraction use a
  re-baselined `DFM-P3B` lane.
- Ramanujan (`019e8441-3a03-7012-8888-30f64fec5927`) returned `pass` for the
  source-only `DFM-P3B` continuation, adding a named
  `apply_default_effects_aircraft_sensor_consequence_block` helper.
- Darwin (`019e8441-ef53-7fe0-9707-03d9ce2daec1`) returned `pass` for
  read-only `DFM-P3B` diagnostics and confirmed that the platform sensor block
  remained outside the aircraft-only helper.
- Ramanujan returned `pass` for the source-only `DFM-P3C` continuation, adding
  a named `apply_default_effects_aircraft_control_hydraulic_consequence_blocks`
  helper.
- Darwin returned `pass` for read-only `DFM-P3C` diagnostics and confirmed that
  platform-level control consequences remained outside the aircraft-only helper.
- Ramanujan returned `pass` for the source-only `DFM-P3D` continuation, adding
  a named `apply_default_effects_aircraft_crew_role_consequence_blocks`
  helper.
- Darwin returned `pass` for read-only `DFM-P3D` diagnostics and confirmed that
  mission/combat and platform-level crew consequences remained outside the
  aircraft-only helper.
- Ramanujan returned `pass` for the source-only `DFM-P3E` continuation, adding
  a named `apply_default_effects_aircraft_mission_combat_consequence_block`
  helper.
- Darwin returned `pass` for read-only `DFM-P3E` diagnostics and confirmed that
  the aircraft structure-spatial block and platform-level mission/combat
  consequence remained outside the aircraft-only helper.
- Cicero (`019e840c-e0a9-7c91-937d-226f388d4912`) returned `pass` for the
  tests-only `DFM-P4` held-fixture probe, adding a structured air-platform
  loss/destruct early-return runtime fixture.
- The call order, coefficients, formula inputs, RNG handling, result fields,
  authority strings, and public model contracts were not changed.
- `DFM-P6` status, parent links, and residual wording were synchronized to the
  current verified state.

This does not close the whole subproject. `DFM-P3E` is accepted for the current
implementation budget, and the line is paused with the aircraft
structure-spatial consequence block held for any later `DFM-P3F` dispatch.

## Validation

```bash
cmake -S . -B build-local-win "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"
# passed; required because CMake 4 rejects vendored doctest's old policy floor

cmake --build build-local-win --target ef_core -j2
# passed

cmake --build build-local-win --target ef_py -j2
# passed

CMO_BUILD_DIR=D:\workshop\Research\Echelon-Forge\build-local-win \
PYTHONPATH=D:\workshop\Research\Echelon-Forge\build-local-win;D:\workshop\Research\Echelon-Forge \
.\.venv\Scripts\python.exe -m pytest -q tests\runtime\air_combat\test_weapon_guidance_realism_guards.py -k dfm_p4
# 5 passed, 150 deselected in 1.35s

CMO_BUILD_DIR=D:\workshop\Research\Echelon-Forge\build-local-win \
PYTHONPATH=D:\workshop\Research\Echelon-Forge\build-local-win;D:\workshop\Research\Echelon-Forge \
.\.venv\Scripts\python.exe -m pytest tests\runtime\air_combat\test_weapon_guidance_realism_guards.py --tb=short -ra
# 155 passed in 44.88s
```

## Residuals

- Pause after `DFM-P3E`; if this line resumes, extract the remaining
  aircraft-side structure-spatial helper stage only if the guard suite remains
  green.
- Keep the accepted structured platform-loss/destruct early-return fixture as a
  regression guard for future structure-only edits.
- Keep C++ unit-test framework adoption as a separate project-wide test-system
  task.

## Forbidden Claims

- Do not claim A2 high-fidelity damage-model maturity or authority promotion.
- Do not claim Pk, deterministic fuze, source-admission, or industrial-release
  readiness.
- Do not treat the private helper split as a public `IEffectsModel` API change.
