# Default Effects Modularization Current Status

Status: `2026-06-02 paused / DFM-P3F structure-spatial helper pass / debug early-return snapshot guard pass`.

Subproject:

- [README.md](README.md)
- [Task clusters](default_effects_modularization_task_clusters_20260601.md)

## Changes Since Baseline

- `default_effects_model.cpp` was reduced to an orchestration entry point that
  includes private implementation fragments.
- Direct-hit, spatial-projection, system-effect, air-platform-resolution, state,
  result, warhead, geometry, component-damage, and legacy helpers now live under
  `src/models/weapons/detail/`.
- Shared helpers now cover component scale calculation and warhead sample /
  mechanism load scratch aggregation.
- Air-platform resolution now has named helpers for vulnerability mechanism-load
  fallback, air spatial scale aggregation, and platform finalize / early return.
- Read-only subagent review found no behavior-equivalence issue in the latest
  extraction pass.
- First-round `DFM-P4` fixture implementation was dispatched to Ohm
  (`019e83ce-25d8-7170-82c0-b3c856cea1d3`) with write ownership limited to a
  new `default_effects_modularization.py` runtime test module and the guard
  mixin collector.
- First-round `DFM-P5` diagnostics was dispatched to Lovelace
  (`019e83ce-b49b-7773-a449-71e916f89d7f`) as a read-only fixture-design and
  behavior-risk review.
- Ohm returned `pass`; integration adjusted the most brittle sample/count
  assertions per Lovelace's diagnostics, then local verification passed.
- A follow-on `DFM-P3` slice extracted the platform-only air consequence and
  clamp block into `apply_default_effects_platform_air_consequence_blocks`
  without changing coefficients, formula inputs, RNG handling, result fields,
  authority strings, or public contracts.
- `DFM-P6` closure sync updated the README, task-cluster status, residuals, and
  current validation evidence.
- Follow-on subagent dispatch is active: Gibbs owns the source-only `DFM-P3`
  continuation, and Cicero owns the tests-only held early-return fixture probe.
- Gibbs returned `pass`; integration accepted the fire-zone aircraft
  consequence helper extraction.
- Cicero returned `pass`; integration accepted the structured air-platform
  loss/destruct early-return runtime fixture.
- Curie returned `pass`; integration accepted the propulsion/fuel aircraft
  consequence helper extraction after full local runtime guard verification.
- Feynman returned `pass` for read-only diagnostics and recommended that any
  further helper extraction use a re-baselined `DFM-P3B` lane rather than
  extending the spent `DFM-P3` implementation budget.
- Ramanujan returned `pass`; integration accepted the sensor/avionics aircraft
  consequence helper extraction after full local runtime guard verification.
- Darwin returned `pass` for read-only `DFM-P3B` diagnostics and confirmed no
  new fixture was needed for the pure sensor-only extraction.
- Ramanujan returned `pass` for `DFM-P3C`; integration accepted the aircraft
  control/hydraulic consequence helper extraction after full local runtime guard
  verification.
- Darwin returned `pass` for read-only `DFM-P3C` diagnostics and confirmed that
  platform-level control consequences remain outside the aircraft-only helper.
- Ramanujan returned `pass` for `DFM-P3D`; integration accepted the aircraft
  crew-role consequence helper extraction after full local runtime guard
  verification.
- Darwin returned `pass` for read-only `DFM-P3D` diagnostics and confirmed that
  mission/combat and platform-level crew consequences remain outside the
  aircraft-only helper.
- Ramanujan returned `pass` for `DFM-P3E`; integration accepted the aircraft
  mission/combat consequence helper extraction after source review and
  validation.
- Darwin returned `pass` for read-only `DFM-P3E` diagnostics and confirmed that
  the aircraft structure-spatial block and platform-level mission/combat
  consequence remain outside the aircraft-only helper.
- `DFM-P3F` resumed the paused line on the main thread and verified that the
  current source already contains the aircraft structure-spatial consequence
  helper `apply_default_effects_aircraft_structure_spatial_consequence_block`,
  with coefficients, formula inputs, RNG handling, result fields, authority
  strings, and public contracts preserved.
- Linux validation exposed a debug-only early-return fixture abort after target
  destruct; integration fixed `simulation_kernel_damage_debug_api.cpp` to build
  debug event records from pre-hit target `Transform` and `Velocity` snapshots
  instead of reading components from a destructed Flecs entity.

## Maturity Matrix

| Area | State | Evidence | Residual |
| --- | --- | --- | --- |
| Translation-unit split | accepted-for-structure | `ef_core` build passed. | `.inc` files must be tracked with the source change. |
| Existing runtime guard | accepted-for-current-guard | `155 passed` in `test_weapon_guidance_realism_guards.py`. | Guard is broad, not a golden path-by-path fixture. |
| Direct/spatial helper equivalence | accepted-for-round-1 | Subagent read-only review plus build/test plus DFM-P4 fixtures. | Platform-loss early-return fixture is now covered by the accepted DFM-P4 fixture. |
| Air-platform internals | accepted-for-current-structure | Mechanism-load, scale, platform-only consequence, aircraft sensor/avionics consequence, aircraft propulsion/fuel consequence, aircraft control/hydraulic consequence, aircraft crew-role consequence, aircraft mission/combat consequence, aircraft structure-spatial consequence, aircraft fire-zone consequence, and finalize helpers extracted. | No remaining aircraft consequence helper residual is held in this subproject. |
| DFM-P4 fixture hardening | pass | 5 targeted fixtures integrated; `dfm_p4` selector passed. | None for current fixture scope. |
| DFM-P5 diagnostics | pass | Lovelace packet reviewed and applied to assertion style. | None for round 1. |
| DFM-P3F structure-spatial split | pass | Source review found the helper already present; `ef_core`, `ef_py`, `dfm_p4`, and full runtime guard passed after the debug guard fix. | Further air-platform restructuring must be re-scoped as a new finite task. |
| Debug early-return snapshot guard | pass | Structured platform-loss/destruct fixture now passes on Linux. | Debug API change is limited to event-record snapshots; default effects formulas are unchanged. |
| DFM-P6 closure sync | pass / updated | [closure sync](default_effects_modularization_closure_sync_20260602.md) | Historical DFM-P6 sync is updated with DFM-P3F evidence; no authority claim added. |
| C++ test harness | deferred | No project-level C++ unit suite exists. | Separate project-wide initiative needed. |

## Evidence

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

git diff --check -- src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc src/core/engine/simulation_kernel_damage_debug_api.cpp docs/task/air_combat/a2_high_fidelity_damage_model/default_effects_modularization src/models/weapons/README.md src/models/weapons/README.zh.md docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md
# passed
```

## Residual Register

Immediate:

- Keep the accepted DFM-P3 / DFM-P3B / DFM-P3C / DFM-P3D / DFM-P3E / DFM-P3F platform,
  sensor/avionics, propulsion/fuel, control/hydraulic, crew-role,
  mission/combat, structure-spatial, and fire-zone helpers plus the DFM-P4
  early-return fixture covered by build and runtime guard verification.
- Do not continue the current `DFM-P3`, `DFM-P3B`, `DFM-P3C`, `DFM-P3D`,
  `DFM-P3E`, or `DFM-P3F` rows with more implementation workers; `DFM-P3F`
  has consumed the previously held structure-spatial split.

Near-term:

- No near-term default-effects air-platform consequence split remains in this
  subproject. Any further source split should be opened as a new finite row with
  a fresh validation budget.

Held:

- C++ unit-test framework adoption.
- Public `IEffectsModel` or plugin boundary redesign.
- Formula, authority string, and calibration behavior changes.

## Recommended Next Action Order

1. Pause after `DFM-P3F` and commit the accepted DFM changes.
2. Keep the structured early-return fixture green because it exercises the
   debug target snapshot guard.

## Explicitly Refused Overclaims

- Do not state that A2 high-fidelity damage modeling is fully mature.
- Do not state that the blast-fragmentation candidate package is authoritative.
- Do not state that Pk, deterministic fuze behavior, or industrial source
  admission has been released.
- Do not state that broad runtime coverage is equivalent to path-specific golden
  regression coverage.
