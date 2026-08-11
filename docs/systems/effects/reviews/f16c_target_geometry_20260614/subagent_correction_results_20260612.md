# TG-P6-R10 Subagent Correction Results

Status: `2026-06-12` subagent correction applied / review-only / `TG-P7`
still held. Chinese canonical:
[subagent_correction_results_20260612.zh.md](subagent_correction_results_20260612.zh.md).

Superseded by the R11 main-thread repair record:
[geometry_repair_results_20260612.md](geometry_repair_results_20260612.md).
The side-sign and missing-receiver blockers below describe the R10 snapshot,
not the current regenerated packet.

This records the correction pass that followed
[subagent_independent_review_findings_20260612.md](subagent_independent_review_findings_20260612.md).
Two write-scoped subagents were used: one repaired the F-16 component source
boxes, and one repaired review semantics and tests. The pass did not create a
new Codex session and did not integrate runtime near-fuze projection.

## Corrections Applied

| Area | Result | Boundary |
| --- | --- | --- |
| Nose radar/IFF source boxes | `apg68_radar_array` and `iff_interrogator` now bind cleanly to `nose_radome` with `component_overlap_fraction=1.0` and no component anomalies. | Review-only component geometry; not true F-16 internal layout. |
| Engine nozzle source box | `afterburner_nozzle` now binds cleanly to `engine_nozzle`; the previous `vertical_tail` binding is gone and `invalid_region_binding_blocked_count=0`. | Surface handoff remains review-only. |
| Cross-region components | `engine_core` is `review_only_cross_region_boundary_candidate`; `wing_spar_center` is `review_only_cross_region_semantic_hold`. Their low-overlap observations are retained as suppressed observations, not bad-box blockers. | Held/review-only semantics, not runtime acceptance. |
| Side-sign mismatch | Wing and wing-root components still emit `side_sign_mismatch_hard_blocker` and preserve side-sign details. | Still blocks `TG-P7`. |
| Missing runtime receivers | Canopy, intake, left horizontal tail, and right horizontal tail emit `missing_runtime_link/held`. | Still blocks runtime handoff. |

## Regenerated Packet Summary

- Component binding: `22` components, `16` bound components, `6`
  `needs_review` hard blockers, `6` side-sign blockers, `2` cross-region
  semantic candidates, and `0` geometry-review-required bad boxes.
- Surface component candidates: `14` surfaces, `10` still need human review,
  `4` missing runtime receiver relations, `4` side-sign surface blockers, `3`
  cross-region semantic surface holds/candidates, and `1` clean candidate
  surface.
- Isolated review views: `83` pages total: `22` component pages, `44`
  surface-handoff or missing-link pages, and `17` review-point candidate pages.

## Remaining Holds

- Resolve the left/right sign convention before accepting wing or wing-root
  handoffs.
- Add explicit runtime receiver components for canopy, intake, and both
  horizontal tails, or record a deliberate held decision.
- Keep `engine_core` and `wing_spar_center` as review-only cross-region
  semantics until ownership is accepted.
- Continue reviewing `surface_nose_radome` and `surface_vertical_tail_skin`
  because they still have expected components bound elsewhere, even though the
  radar/IFF and nozzle source boxes were repaired.

## Validation

```bash
python tools/geometry/airframe_geometry_review.py --out docs/systems/effects/reviews/f16c_target_geometry_20260614/review_packets/f16c_20260611
pytest -q tests/tools/test_airframe_geometry_review.py
git diff --check -- docs/systems/effects/reviews/f16c_target_geometry_20260614 tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py examples/config/database/aircraft/units/f16c_block50.json
```

Result: generator completed, focused pytest reported `2 passed`, and
`git diff --check` reported no whitespace errors.
