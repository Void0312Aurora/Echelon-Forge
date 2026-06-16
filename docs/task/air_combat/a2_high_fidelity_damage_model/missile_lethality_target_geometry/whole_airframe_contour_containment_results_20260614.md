# Whole-Airframe Projected Mesh Contour Containment Results

Status: `2026-06-14` tooling upgrade / retained diagnostic. The F-16C
fine-geometry engineering proxy acceptance (`accepted / retained`) is
unchanged. This record upgrades the silhouette-containment test method inside
`airframe_geometry_review.py` to project the audit glTF mesh triangles into
each view, union the projected faces, and test receiver samples against that
projected mesh silhouette.

Chinese canonical:
[whole_airframe_contour_containment_results_20260614.zh.md](whole_airframe_contour_containment_results_20260614.zh.md).

## Why This Upgrade

The previous containment tests hid or distorted protrusions:

1. The legacy "whole-airframe silhouette" was a per-view list of independent
   per-region convex hulls, evaluated as a set union.
2. The temporary vertex alpha-shape contour used all audit vertices, but it
   could bridge empty space between wings, tail, fuselage, and stores, making
   the aircraft outline visually wrong.
3. Each receiver must be sampled by its projected shape, not only by a sparse
   AABB point set.

The final diagnostic now uses the audit mesh faces directly:

- Contour method: `projected_mesh_triangle_union`.
- Source mesh: `4,504` audit glTF triangles per view.
- Per-view contours: `top=222`, `side=159`, and `front=201` contour points;
  each view produced one union polygon.
- Receiver sampling: AABB/OBB use the 9-point projected box grid; ellipsoid
  receivers use a 24-point projected perimeter ring; capsule receivers use
  projected cap rings plus centerline endpoints; thin-prism receivers use
  their planform footprint edges and frustum receivers use end rings plus
  centerline samples.
- Tolerance: `0.05 m`, recorded as an engineering review margin for mesh /
  proxy quantization noise, not a physical clearance.

## Generated Evidence

- [review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json)
- [review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.csv](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.csv)
- [review_packets/f16c_20260611/whole_airframe_contour_top.svg](review_packets/f16c_20260611/whole_airframe_contour_top.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_side.svg](review_packets/f16c_20260611/whole_airframe_contour_side.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_front.svg](review_packets/f16c_20260611/whole_airframe_contour_front.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html)

Each SVG draws the gray projected audit-mesh silhouette and overlays only the
26 current receiver priors in green when inside tolerance and red when the max
outside distance exceeds the `0.05 m` tolerance. The 8 review-only held split
segments are excluded from the final result surface so the experimental split
receivers are not mistaken for real components.

## Result

`item_count = 26` (current receiver priors only).
`excluded_review_only_split_segment_count = 8`.
`exceeds_tolerance_item_count = 0`. `max_outside_distance_m = 0.0`.

All `26` receiver priors are inside the projected mesh contour within
tolerance. The previously exposed wing fuel cells are now swept thin-prism
planform footprints, `wing_spar_center` is a symmetric thin-prism carry-through
strip, and `afterburner_nozzle` is a tapered frustum rather than a closed
ellipsoid.

## Difference From The Previous Conclusion

The previous projected-mesh pass recorded side/front protrusions on
`engine_core`, `cockpit_crew_station`, `afterburner_nozzle`, and
`inertial_navigation_unit`; those placement-height issues were fixed earlier
without changing nominal sizes. A later top-view review identified poor shape
proxies for the wing fuel cells, wing spar, and nozzle. R22 replaces those
proxies with shape-aware thin-prism/frustum geometry while preserving the
review-only boundary. The current final result surface excludes the `8`
review-only held split segments that do not carry real component meaning and
leaves no receiver prior outside the projected mesh contour.

## Boundary

- This is a tooling-method upgrade for the silhouette-containment test. It does
  not change the default F-16 unit damage database, TG-P7 opt-in training proxy,
  runtime activation, training benefit, Pk, structural breakup, debris, or
  weapon-specific lethality.
- The projected mesh contour is a review-only diagnostic, not a runtime
  collision mesh and not true F-16C engineering geometry.
- The `0.05 m` tolerance is an engineering review margin for mesh / proxy
  quantization noise, not a physical clearance.

## Validation

```bash
.\.venv\Scripts\python.exe -m py_compile tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py
.\.venv\Scripts\python.exe -m ruff check tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py
.\.venv\Scripts\python.exe -m pytest -q tests/tools/test_airframe_geometry_review.py
.\.venv\Scripts\python.exe tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
git diff --check -- tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry
```
