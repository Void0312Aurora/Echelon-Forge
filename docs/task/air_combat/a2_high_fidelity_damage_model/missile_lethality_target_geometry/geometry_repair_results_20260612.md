# TG-P6-R11 Geometry Repair Results

Status: `2026-06-12` applied / review-only / `TG-P7` runtime interface still
requires an explicit ownership decision for cross-region components. Chinese
canonical: [geometry_repair_results_20260612.zh.md](geometry_repair_results_20260612.zh.md).

This round repairs the blockers left after the R10 subagent correction:
side-sign mismatch, missing surface receiver components, and the exposed wing
component box placement issues that became visible once the left/right mapping
was corrected.

## Applied Repairs

| Slice | Repair | Boundary |
| --- | --- | --- |
| Left/right outer regions | Swapped curated audit-mesh source nodes for wings, wing roots, and horizontal tails so `left_*` maps to negative-y and `right_*` maps to positive-y, matching existing component naming. | Corrects the review mapping; does not claim real F-16 engineering station data. |
| Wing and wing-root components | Moved wing fuel cells and aileron actuators onto the mesh-derived wing thin prisms; moved leading-edge flap actuators into the wing-root fairing boxes. | Synthetic runtime component boxes remain review-only geometry. |
| Runtime surface receivers | Added explicit receiver components for canopy, intake, left horizontal tail, and right horizontal tail in `f16c_block50.json`. | Adds damage-model components; does not accept the surface proxy into near-fuze runtime projection. |
| Surface handoff rules | Replaced missing-runtime held relations with expected existing receiver components, and narrowed direct surface expectations for radome, canopy, and vertical tail. | Cross-region paths stay review-only until ownership is explicit. |
| Stage-C guard sync | Updated the Stage-C component-probability surface probe gate to accept the repaired beam-side geometry's `surface_incidence_cos=0.0`, restoring component-specific row selection instead of `global-fallback`. | Keeps the Stage-C candidate non-authoritative; it only aligns the test-local guard with the repaired geometry. |

## Regenerated Packet Summary

- Component binding: `26` components, `26` bound components, `0`
  `needs_review`, `0` side-sign blockers, `0` hard blockers, `0`
  geometry-review-required bad boxes.
- Surface component candidates: `14` surfaces, `0` `needs_review`, `0`
  missing runtime receiver relations, `0` side-sign surface blockers, `8`
  cross-region semantic holds/candidates.
- Isolated review views: `75` pages total: `26` component pages, `29`
  surface handoff pages, and `20` review-point candidate-component pages.

## Remaining Boundary

- `engine_core` remains `review_only_cross_region_boundary_candidate` across
  intake, aft engine bay, and nozzle semantics.
- `wing_spar_center` remains `review_only_cross_region_semantic_hold` across
  center fuselage, wing roots, and wing skins.
- `TG-P7` should not treat the outer proxy as runtime projection geometry until
  those ownership semantics are accepted, split, or deliberately held.

## Verification

```bash
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
pytest -q tests/tools/test_airframe_geometry_review.py
pytest -q tests/architecture/damage_model
```

Focused test result: `2 passed`; architecture damage-model result:
`177 passed`.
