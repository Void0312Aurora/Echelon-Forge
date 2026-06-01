# Default Effects Modularization Current Status

Status: `2026-06-01 active / implementation split pass / fixture hardening planned`.

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

## Maturity Matrix

| Area | State | Evidence | Residual |
| --- | --- | --- | --- |
| Translation-unit split | accepted-for-structure | `ef_core` build passed. | `.inc` files must be tracked with the source change. |
| Existing runtime guard | accepted-for-current-guard | `150 passed` in `test_weapon_guidance_realism_guards.py`. | Guard is broad, not a golden path-by-path fixture. |
| Direct/spatial helper equivalence | active-pass | Subagent read-only review plus build/test. | Add fixed-RNG fixtures. |
| Air-platform internals | active-partial | Mechanism-load, scale, finalize helpers extracted. | Consequence blocks can still be split later. |
| C++ test harness | deferred | No project-level C++ unit suite exists. | Separate project-wide initiative needed. |

## Evidence

```bash
cmake --build build --target ef_core -j2
# passed

CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
# 150 passed in 41.18s

git diff --check -- src/models/weapons/default_effects_model.cpp src/models/weapons/detail src/models/weapons/README.md src/models/weapons/README.zh.md
# passed
```

## Residual Register

Immediate:

- Track `src/models/weapons/detail/` together with `default_effects_model.cpp`.
- Re-run `ef_core` build after any follow-up helper extraction.

Near-term:

- Add fixed-RNG direct component hit fixture.
- Add fixed-RNG direct protected-system fallback fixture.
- Add broad spatial projection near-miss fixture.
- Add non-broad component spatial near-miss fixture.
- Add structured air-platform loss early-return fixture.

Held:

- C++ unit-test framework adoption.
- Public `IEffectsModel` or plugin boundary redesign.
- Formula, authority string, and calibration behavior changes.

## Recommended Next Action Order

1. Decide whether to continue `DFM-P3` consequence-block splitting or freeze it
   until fixtures exist.
2. Start `DFM-P4` with a small fixed-RNG runtime fixture set.
3. Run `DFM-P6` closure sync after implementation and fixture status is stable.

## Explicitly Refused Overclaims

- Do not state that A2 high-fidelity damage modeling is fully mature.
- Do not state that the blast-fragmentation candidate package is authoritative.
- Do not state that Pk, deterministic fuze behavior, or industrial source
  admission has been released.
- Do not state that broad runtime coverage is equivalent to path-specific golden
  regression coverage.
