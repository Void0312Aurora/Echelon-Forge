# TG-P6-R22 Cross-Region Ownership Split Candidate Results

Status: `2026-06-13` pass as review-only ownership split candidate; `TG-P7`
runtime activation remains held pending ownership acceptance and runtime tests.

Chinese canonical:
[cross_region_ownership_split_results_20260613.zh.md](cross_region_ownership_split_results_20260613.zh.md).

## What Changed

R22 converts the two remaining cross-region held receivers into an explicit
ownership decision packet. It does not accept the proposed split, retire any
parent receiver, or activate any runtime component.

New packet artifacts:

- [cross_region_ownership_split_candidate_20260611.json](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.json)
- [cross_region_ownership_split_candidate_20260611.csv](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.csv)
- [scene.html](review_packets/f16c_20260611/scene.html), now with a
  `Cross-Region Ownership Split Candidates` section.

## Candidate Decisions

| Parent receiver | Proposed decision | Candidate receivers | Runtime status |
| --- | --- | --- | --- |
| `engine_core` | `split_into_engine_section_receivers_and_keep_intake_duct_receiver_separate` | `engine_core_afterburner_segment`, `engine_core_hot_section_segment`, `engine_core_forward_compressor_segment` | not active |
| `wing_spar_center` | `split_into_center_carrythrough_root_and_inner_wing_spar_receivers` | `wing_spar_center_left_inner_wing_segment`, `wing_spar_center_left_root_segment`, `wing_spar_center_carrythrough_segment`, `wing_spar_center_right_root_segment`, `wing_spar_center_right_inner_wing_segment` | not active |

## Counts

- Parent decisions: `2`.
- Split receiver candidates: `8`.
- Runtime parse-ready split candidates: `8`.
- Runtime active split components: `0`.
- Split candidates with sampled whole-airframe silhouette exposure: `0`.
- Split candidates outside whole-airframe bounds: `0`.
- Parent receiver retirement required before activation: `2`.

## Boundary

The split candidate payloads are AABB fallback receiver records with preserved
source shape metadata. They are parse-ready for a future `TG-P7` schema/runtime
test, but the packet keeps these authority flags false:

- runtime damage ownership;
- runtime split receiver activation;
- parent receiver retirement acceptance;
- cross-region receiver ownership acceptance;
- true internal component geometry.

## Next Step

1. Accept, reject, or keep held the proposed parent receiver retirement for
   `engine_core` and `wing_spar_center`.
2. Add `TG-P7` parse and behavior tests for the split candidates before any
   activation.
3. Keep the payloads as AABB fallback candidates until exact capsule/ellipsoid
   runtime intersection support is separately accepted.

## Validation

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
```

Current focused result: `2 passed`; review packet regenerated.
