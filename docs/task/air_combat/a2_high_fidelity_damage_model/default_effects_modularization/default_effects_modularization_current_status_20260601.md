# Default Effects Modularization Current Status

Status: `2026-06-01 active / implementation split pass / DFM-P4 round 1 accepted`.

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

## Maturity Matrix

| Area | State | Evidence | Residual |
| --- | --- | --- | --- |
| Translation-unit split | accepted-for-structure | `ef_core` build passed. | `.inc` files must be tracked with the source change. |
| Existing runtime guard | accepted-for-current-guard | `154 passed` in `test_weapon_guidance_realism_guards.py`. | Guard is broad, not a golden path-by-path fixture. |
| Direct/spatial helper equivalence | accepted-for-round-1 | Subagent read-only review plus build/test plus DFM-P4 fixtures. | Platform-loss early-return fixture remains held. |
| Air-platform internals | active-partial | Mechanism-load, scale, finalize helpers extracted. | Consequence blocks remain frozen until the accepted fixtures are committed. |
| DFM-P4 fixture hardening | pass | 4 targeted fixtures integrated; `dfm_p4` selector passed. | Platform-loss early-return deferred. |
| DFM-P5 diagnostics | pass | Lovelace packet reviewed and applied to assertion style. | None for round 1. |
| C++ test harness | deferred | No project-level C++ unit suite exists. | Separate project-wide initiative needed. |

## Evidence

```bash
cmake --build build --target ef_core -j2
# passed

CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
# 154 passed in 33.71s

CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k dfm_p4
# 4 passed, 150 deselected in 0.38s

git diff --check -- src/models/weapons/default_effects_model.cpp src/models/weapons/detail src/models/weapons/README.md src/models/weapons/README.zh.md
# passed
```

## Residual Register

Immediate:

- Keep `DFM-P3` frozen until the new fixtures are available on the branch.
- Prepare `DFM-P6` closure sync after this acceptance commit.

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
- Structured air-platform loss/destruct early-return fixture, until a stable
  debug setter or non-cumulative fixture exists.

## Recommended Next Action Order

1. Run `DFM-P6` closure sync after the acceptance commit.
2. Decide whether to keep platform-loss early-return held or create a dedicated
   stable debug fixture surface.
3. Keep `DFM-P3` frozen until the new fixture state is available on the branch.

## Explicitly Refused Overclaims

- Do not state that A2 high-fidelity damage modeling is fully mature.
- Do not state that the blast-fragmentation candidate package is authoritative.
- Do not state that Pk, deterministic fuze behavior, or industrial source
  admission has been released.
- Do not state that broad runtime coverage is equivalent to path-specific golden
  regression coverage.
