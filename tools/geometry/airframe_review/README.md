# Airframe Review Subdomain

This package contains internal subdomain modules for the F-16C airframe
geometry review tool. The command orchestration entry point remains
`tools/geometry/airframe_geometry_review.py`; low-level review mechanics live
in this package.

Current layers:

- `constants.py`: schema ids, default paths, geometry review rule tables, and
  glTF accessor constants.
- `optional_deps.py`: scipy/shapely import guard for projected-contour
  diagnostics.
- `primitives.py`: shared bounds, rounding, and serialization helpers.
- `gltf_io.py`: glTF JSON/buffer/accessor parsing, node traversal, and scene
  summary generation.
- `manifest_builder.py`: source metadata, public-dimension, registry, and
  current-damage manifest construction.
- `asset_projection.py`: projection from glTF asset coordinates into
  simulation-frame review points, triangles, and bounds.
- `contours.py`: alpha-shape and projected-triangle contour builders.
- `component_model.py`: damage component name collection helpers.
- `component_binding.py`: runtime damage component binding and review-point
  diagnostic report builders.
- `bounds_ops.py`: reusable AABB, volume, containment, and intersection
  helpers for report builders.
- `filesystem.py`: repo-relative path display and file hashing helpers.
- `geometry_mapping.py`: outer-region mapping and curated mesh-source
  candidate generation.
- `fine_proxy.py`: mesh-derived fine geometry proxy candidates and review-point
  distance deltas.
- `surface_semantic.py`: surface component candidates and parse-ready semantic
  damage geometry reports.
- `shape_geometry.py`: shared primitive-shape, projected-containment, and
  whole-airframe silhouette helper geometry.
- `internal_prior.py`: constrained internal component prior geometry candidates.
- `held_segments.py`: review-only splits for held cross-region internal
  component receivers.
- `airframe_constraint.py`: silhouette-based airframe containment diagnostics
  and correction candidates.
- `contour_containment.py`: projected whole-airframe mesh contour containment
  report generation.
- `subcomponent_shape.py`: subcomponent shape, centerline, and latest-placement
  review candidates.
- `parent_child_layout.py`: semantic shell to receiver-prior layout grouping.
- `projection_geometry.py`: projected-bounds, projected-shape sampling, and
  polygon containment helpers shared by builders and views.
- `report_writers.py`: JSON/CSV artifact writers for review reports.
- `review_views.py`: HTML/SVG review dashboards and isolated review pages.
- `review_packet.py`: final `scene.html` review packet writer.
- `runtime_activation.py`: cross-region ownership split, runtime activation,
  behavior regression, and training proxy report builders.

Boundary rule: these modules support review-only geometry evidence generation.
They are not runtime collision mesh, vulnerability calibration, or real weapon
Pk authority surfaces.
