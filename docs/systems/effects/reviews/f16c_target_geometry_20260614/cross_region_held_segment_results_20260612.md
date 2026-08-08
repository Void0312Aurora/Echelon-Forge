# Cross-Region Held Segment Results - 2026-06-12

R15 splits the two red cross-region held receiver priors into smaller
owner-region review segments so the parent-child geometry preview no longer
shows one monolithic held block.

## Outputs

| Artifact | Result |
| --- | --- |
| Segment report | [cross_region_held_component_segments_20260611.json](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json), [CSV](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv) |
| Parent-child report | [semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json), [CSV](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv) |
| Review pages | Retired intermediate parent-child views; current visual result is [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) |

## Counts

| Measure | Value |
| --- | ---: |
| held parent components | `2` |
| held split segments | `8` |
| `engine_core` segments | `3` |
| `wing_spar_center` segments | `5` |
| outside whole-airframe segments | `0` |
| runtime active segments | `0` |

## Segment Policy

- `engine_core` remains held, but is displayed as
  `engine_core_afterburner_segment`, `engine_core_hot_section_segment`, and
  `engine_core_forward_compressor_segment`.
- `wing_spar_center` remains held, but is displayed as left inner wing, left
  root, center carry-through, right root, and right inner wing spar segments.
- Red now means held split segment. Green/cyan still mean ordinary actual-size
  receiver priors. Grey is the whole-airframe wireframe and blue is the parent
  semantic region.

## Boundary

This is review-only geometry. It does not activate runtime components, does not
accept cross-region ownership, and does not claim true F-16 internal engineering
geometry.
