# F-16 Semantic Parent-Child Component Layout Results (R14, 2026-06-12)

## Conclusion

R14 changes the primary visual review surface from `26` isolated receiver views to `14` geometry-modeled parent shell views.

Each parent part corresponds to one model region / semantic shell volume. The current `26` receiver priors are no longer presented as independent top-level views; they are overlaid on their parent shell by `bound_region_id`. Since `26 - 14 = 12`, the packet now records `12` extra receiver slots.

This layer is still review-only visualization and review data. It does not accept runtime damage ownership.

## New Artifacts

- [review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json)
- [review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv)
- Retired intermediate parent-child layout views.
- Current visual result: [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html)

## Legend

- Blue: mesh-derived geometry background for the 14 parent shell/model regions.
- Green: primary or single receiver prior for the parent part.
- Cyan: extra receiver prior on the same parent part.
- Red: cross-region held split segment; currently from `engine_core` and
  `wing_spar_center`.

The final R14 preview no longer shows source bounds, support bounds, old AABBs,
review points, or other auxiliary review layers. It keeps only the parent
geometry background and child components. R15 keeps actual-size receiver priors
under whole-airframe constraints and draws the two red held receivers as smaller
split segments instead of a single monolithic red block.

## Counts

- Parent geometry parts: `14`
- Overlaid receiver priors: `26`
- Extra receiver slots: `12`
- Cross-region held receivers: `2`
- Cross-region held split segments: `8`
- Active runtime components: `0`

## Boundary

- R14 changes only the review view and data grouping; it does not activate the runtime damage model.
- Green, cyan, and red shapes are synthetic receiver priors, not true F-16 internal engineering structure.
- Red held receivers still need ownership split or explicit acceptance before runtime activation.
