# TG-P7-R2 Runtime Behavior Regression Results

Status: `2026-06-13` pass as in-memory behavior regression candidate; the
repository F-16 unit database remains unchanged.

Chinese canonical:
[target_geometry_runtime_behavior_regression_results_20260613.zh.md](target_geometry_runtime_behavior_regression_results_20260613.zh.md).

## What Changed

TG-P7-R2 corrects the TG-P7 patch contract to the actual unit-definition shape:
split receiver records are component records under
`damage_model.hitboxes[].components`, not top-level hitbox records. The report
applies the TG-P7-R1 candidate in memory only:

1. Remove `engine_core` from hitbox `2` and append its `3` split receivers.
2. Remove `wing_spar_center` from hitbox `3` and append its `5` split receivers.
3. Verify the projected component list for duplicate names, missing split
   receivers, and retired parent receivers.

New packet artifacts:

- [target_geometry_runtime_behavior_regression_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.json)
- [target_geometry_runtime_behavior_regression_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.csv)
- [scene.html](review_packets/f16c_20260611/scene.html), now with a
  `TG-P7 Runtime Behavior Regression Candidate` section.

## Acceptance Gate

| Gate | Result |
| --- | --- |
| Base component count | `26` |
| Expected projected component count | `32` |
| Projected component count | `32` |
| Retired parent components absent after patch | `2` |
| Split component additions present after patch | `8` |
| Duplicate component names after patch | `0` |
| Runtime active components | `0` |
| Behavior regression pass | `true` |

## Boundary

This is still an in-memory patch regression, not an active runtime change. It
does not edit [f16c_block50.json](/home/void0312/Workshop/CMO/examples/config/database/aircraft/units/f16c_block50.json),
does not wire a training feature flag, and does not claim real F-16 internal
engineering geometry.

## Follow-On

TG-P7-R3 has since materialized this projection as an opt-in training proxy
database:
[target_geometry_training_proxy_results_20260613.md](target_geometry_training_proxy_results_20260613.md).
R3 also completed a local `64`-step runtime/training smoke. The next step is
active 8k proxy versus baseline comparison while preserving the default `26`
component control path.

## Validation

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py src/tests/test_components_basic.cpp
```

Current focused result: Python geometry review tests `2 passed`; C++ loader
smoke `24 passed`; review packet regenerated.
