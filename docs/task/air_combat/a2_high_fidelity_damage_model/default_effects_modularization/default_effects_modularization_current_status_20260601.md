# Default Effects Modularization Current Status

Status: `2026-06-02 paused / DFM-P3E mission-combat helper pass / DFM-P4 early-return fixture pass`.

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

## Maturity Matrix

| Area | State | Evidence | Residual |
| --- | --- | --- | --- |
| Translation-unit split | accepted-for-structure | `ef_core` build passed. | `.inc` files must be tracked with the source change. |
| Existing runtime guard | accepted-for-current-guard | `155 passed` in `test_weapon_guidance_realism_guards.py`. | Guard is broad, not a golden path-by-path fixture. |
| Direct/spatial helper equivalence | accepted-for-round-1 | Subagent read-only review plus build/test plus DFM-P4 fixtures. | Platform-loss early-return fixture is now covered by the accepted DFM-P4 fixture. |
| Air-platform internals | paused-partial | Mechanism-load, scale, platform-only consequence, aircraft sensor/avionics consequence, aircraft propulsion/fuel consequence, aircraft control/hydraulic consequence, aircraft crew-role consequence, aircraft mission/combat consequence, aircraft fire-zone consequence, and finalize helpers extracted. | Aircraft structure-spatial consequence block remains inline and held for later dispatch. |
| DFM-P4 fixture hardening | pass | 5 targeted fixtures integrated; `dfm_p4` selector passed. | None for current fixture scope. |
| DFM-P5 diagnostics | pass | Lovelace packet reviewed and applied to assertion style. | None for round 1. |
| DFM-P6 closure sync | pass | [closure sync](default_effects_modularization_closure_sync_20260602.md) | Subproject remains active because DFM-P3 and early-return fixture residuals remain. |
| C++ test harness | deferred | No project-level C++ unit suite exists. | Separate project-wide initiative needed. |

## Evidence

```bash
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

git diff --check -- src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc tests/runtime/air_combat/weapon_guidance_realism/default_effects_modularization.py docs/task/air_combat/a2_high_fidelity_damage_model/default_effects_modularization src/models/weapons/README.md src/models/weapons/README.zh.md docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md
# passed; LF/CRLF conversion warnings only
```

## Residual Register

Immediate:

- Keep the accepted DFM-P3 / DFM-P3B / DFM-P3C / DFM-P3D / DFM-P3E platform,
  sensor/avionics, propulsion/fuel, control/hydraulic, crew-role,
  mission/combat, and fire-zone helpers plus the DFM-P4 early-return fixture
  covered by build and runtime guard verification.
- Do not continue the current `DFM-P3`, `DFM-P3B`, `DFM-P3C`, `DFM-P3D`, or
  `DFM-P3E` rows with more implementation workers; the current task is paused
  with the structure-spatial block held.

Near-term:

- If this line resumes, create a new `DFM-P3F` row for the aircraft
  structure-spatial helper slice only if build and runtime guard remain green.

Held:

- C++ unit-test framework adoption.
- Public `IEffectsModel` or plugin boundary redesign.
- Formula, authority string, and calibration behavior changes.

## Recommended Next Action Order

1. Pause after `DFM-P3E` and commit the accepted DFM changes.
2. On a later resume, consider `DFM-P3F` for the aircraft structure-spatial
   block only.

## Explicitly Refused Overclaims

- Do not state that A2 high-fidelity damage modeling is fully mature.
- Do not state that the blast-fragmentation candidate package is authoritative.
- Do not state that Pk, deterministic fuze behavior, or industrial source
  admission has been released.
- Do not state that broad runtime coverage is equivalent to path-specific golden
  regression coverage.
