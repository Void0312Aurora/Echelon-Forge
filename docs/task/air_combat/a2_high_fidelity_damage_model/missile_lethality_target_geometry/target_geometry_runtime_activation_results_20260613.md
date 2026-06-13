# TG-P7-R1 Runtime Activation Candidate Results

Status: `2026-06-13` pass as parse-ready runtime activation candidate; the
unit database has not been modified and no split receiver is runtime active.

Chinese canonical:
[target_geometry_runtime_activation_results_20260613.zh.md](target_geometry_runtime_activation_results_20260613.zh.md).

## What Changed

TG-P7-R1 converts the R22 ownership split payload into a unit-database component
patch candidate for the initial F-16C training geometry proxy. The patch shape
is explicitly aimed at `damage_model.hitboxes[].components`, uses fields already
parsed by the current unit loader, and keeps activation behind an explicit
feature flag.

New packet artifacts:

- [target_geometry_runtime_activation_candidate_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json)
- [target_geometry_runtime_activation_candidate_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.csv)
- [scene.html](review_packets/f16c_20260611/scene.html), now with a
  `TG-P7 Runtime Activation Candidate` section.

## Acceptance Gate

| Gate | Result |
| --- | --- |
| Candidate receiver count | `8` |
| Runtime loader parse-ready count | `8` |
| Unit-database patch additions | `8` |
| Parent receiver retirement plans | `2` |
| Parent receiver retirements applied | `0` |
| Runtime active split components | `0` |
| Behavior tests required before activation | `8` |
| Activation blocker count in this parse-ready layer | `0` |
| C++ unit-definition loader parse smoke | pass |

## Candidate Receivers

- `engine_core_afterburner_segment`
- `engine_core_hot_section_segment`
- `engine_core_forward_compressor_segment`
- `wing_spar_center_left_inner_wing_segment`
- `wing_spar_center_left_root_segment`
- `wing_spar_center_carrythrough_segment`
- `wing_spar_center_right_root_segment`
- `wing_spar_center_right_inner_wing_segment`

## Boundary

This is a real TG-P7 activation package, but it is not yet an applied runtime
change. The JSON contains `unit_database_patch_candidate.add_components`
records that can be appended to the matching
`F-16C_Block50.damage_model.hitboxes[].components` arrays after the next
acceptance step. The current authority flags remain:

- `unit_database_modified=false`;
- `runtime_active_component=false`;
- `runtime_damage_model=false`;
- `parent_receiver_retirement_accepted=false`;
- `training_proxy_feature_flag_required=true`.

## Follow-On

TG-P7-R2 has since confirmed the parent-retirement versus split-addition
projection, and TG-P7-R3 has materialized it as an opt-in training proxy
database:
[target_geometry_training_proxy_results_20260613.md](target_geometry_training_proxy_results_20260613.md).
R3 also completed a local `64`-step proxy training smoke, and R4 completed the
active 8k proxy-versus-baseline comparison. The next step is targeted
damage-event trace inspection, not further patch-shape design.

## Validation

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
```

Current focused result: Python geometry review tests `2 passed`; C++ loader
smoke `24 passed`; review packet regenerated.
