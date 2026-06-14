# Whole-Airframe Alpha-Shape Contour Containment Results

Status: `2026-06-14` tooling upgrade / retained diagnostic. The F-16C
fine-geometry engineering proxy acceptance (`accepted / retained`) is
unchanged. This record upgrades the silhouette-containment test method
inside `airframe_geometry_review.py` from a per-region convex-hull union
with sparse 9-point sampling to a whole-airframe alpha-shape contour with
dense perimeter sampling, then records the receivers that the stricter test
exposes.

Chinese canonical:
[whole_airframe_contour_containment_results_20260614.zh.md](whole_airframe_contour_containment_results_20260614.zh.md).

## Why This Upgrade

The previous containment test held three assumptions that hid real
protrusion:

1. The "whole-airframe silhouette" was a per-view list of up to 14
   independent per-region convex hulls, evaluated as a set union. A receiver
   passed when it landed inside *any* hull, so concave junctions (wing root,
   intake, center fuselage) were treated as filled.
2. Each receiver was sampled with at most 9 axis-aligned points (AABB 3x3
   grid, ellipsoid 5-point axis cross). A tilted or elongated receiver could
   hide a corner that poked through the contour.
3. The tolerance was `0.02 m`, set as a polygon-edge soft margin.

All three are replaced:

- The contour is now a single alpha-shape per view, built from all
  `13,415` audit glTF mesh vertices, so concavities are preserved.
- Each receiver is sampled with a dense perimeter (AABB 8 corners + edge
  midpoints + center, ellipsoid 24-point ring, capsule two 12-point cap
  rings).
- The tolerance is `0.05 m`, recorded explicitly as an engineering review
  margin for mesh / proxy quantization noise, not a physical clearance.

## Method

- Contour: `scipy.spatial.Delaunay` triangulation of the projected mesh
  vertices, filtered by circumradius `R < 1/alpha`, edges kept via
  `shapely.ops.polygonize` + `unary_union`, largest polygon exterior ring
  taken as the view contour.
- Per-view alpha: `1 / (longer_projected_axis_span * 0.35)`. For the F-16
  this gives `alpha ~= 0.19` (top/side) and `alpha ~= 0.30` (front),
  preserving wing-root and intake concavities without shattering thin
  surfaces.
- Fallback: when a view cannot produce a closed alpha-shape (too few
  surviving triangles, degenerate polygon) it records
  `status="convex_hull"`. All three views produced a true alpha-shape for
  the F-16; no fallback was used.
- Dependencies: scipy and shapely are declared in the new
  `.[geometry]` optional dependency group. Every other path in the tool
  stays zero-dependency.

## Inputs

- Manifest:
  [review_packets/f16c_20260611/manifest.json](review_packets/f16c_20260611/manifest.json)
- Audit glTF vertices: `13,415` (position accessor vertex count).
- Airframe constraint report (source of per-item geometry):
  [review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json)

## Generated Evidence

- [review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json)
- [review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.csv](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.csv)
- [review_packets/f16c_20260611/whole_airframe_contour_top.svg](review_packets/f16c_20260611/whole_airframe_contour_top.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_side.svg](review_packets/f16c_20260611/whole_airframe_contour_side.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_front.svg](review_packets/f16c_20260611/whole_airframe_contour_front.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html)

Each SVG draws the gray whole-airframe alpha-shape wireframe, overlays the
34 receiver priors plus held split segments in green when inside the contour
and red when the max outside distance exceeds the `0.05 m` tolerance, and
labels each protrusion with its max outside distance.

## Result

`item_count = 34` (26 receiver priors + 8 held split segments).
`exceeds_tolerance_item_count = 3`. `max_outside_distance_m = 0.21036`.

| item_id | type | shape | outside views | max outside (m) | notes |
| --- | --- | --- | --- | ---: | --- |
| `engine_core` | receiver_prior | capsule / x | side | `0.210` | Cross-region parent capsule; its `1.1811 m` radius tail extends past the aft airframe contour on the side view. The `engine_core_afterburner_segment` split stays inside the contour, confirming the R22 split resolves the parent exposure. |
| `cockpit_crew_station` | receiver_prior | ellipsoid | side | `0.075` | The `1.25 x 0.508 x 1.15 m` crew envelope pokes just above the canopy contour on the side view; a conformal canopy-following prior would clear it. |
| `inertial_navigation_unit` | receiver_prior | ellipsoid | side | `0.051` | Just past the `0.05 m` tolerance on the side view; within mesh-quantization noise but recorded honestly. |

The remaining `31` of `34` items (24 single-region priors + 8 split
segments, including `engine_core_afterburner_segment`,
`engine_core_hot_section_segment`,
`engine_core_forward_compressor_segment`, and all five
`wing_spar_center_*` segments) are inside the contour within tolerance.

### Difference From The Previous Conclusion

The previous airframe-constraint report recorded
`silhouette_exposure_item_count = 0` for all `34` items. The upgraded test
records `silhouette_exposure_item_count = 3`. The three newly exposed items
are the same receivers the legacy sparse-sampling per-region-hull-union
test could not see, not new geometry. The shape-placement report
(`build_subcomponent_shape_placement_candidate_report`) now actively
generates shape / centerline / latest candidates for the three exposed
items instead of being an empty queue; none of those candidates is promoted
into runtime rules.

## Boundary

- This is a tooling-method upgrade for the silhouette-containment test. It
  does not change the F-16C fine-geometry engineering proxy acceptance
  (`accepted / retained`), the default F-16 unit damage database, the
  TG-P7 opt-in training proxy, runtime activation, training benefit, Pk,
  structural breakup, debris, or weapon-specific lethality.
- The alpha-shape contour is a review-only diagnostic, not a runtime
  collision mesh and not true F-16C engineering geometry.
- The `0.05 m` tolerance is an engineering review margin for mesh / proxy
  quantization noise, not a physical clearance.
- `engine_core`, `cockpit_crew_station`, and `inertial_navigation_unit`
  protrusion are recorded as follow-on evidence; resolving them (e.g. a
  conformal canopy prior, a tapered engine tail, a tighter INU box) is a
  later standalone geometry refinement, not a closure gate for this
  diagnostic.

## Validation

```bash
pip install scipy shapely
python -m py_compile tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py
python -m pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py
git diff --check -- tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry
```

Current focused result: `pytest -q tests/tools/test_airframe_geometry_review.py`
reports `5 passed`, including the new
`test_alpha_shape_2d_preserves_concavities_and_degrades_gracefully`,
`test_whole_airframe_contour_report_structure`, and
`test_geometry_optional_dependencies_advertised` cases.
