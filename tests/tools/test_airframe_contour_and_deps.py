from __future__ import annotations

from pathlib import Path

from tools.geometry.airframe_review import contours
from tests.tools.airframe_review_fixtures import (
  build_airframe_review_bundle,
  require_airframe_geometry_extra,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_alpha_shape_2d_preserves_concavities_and_degrades_gracefully() -> None:
  """The whole-airframe contour builder must keep real concavities (the whole
  point of choosing alpha-shape over convex hull) and must fall back to the
  convex hull when there are too few points or no triangle survives the
  circumradius filter."""
  require_airframe_geometry_extra()

  import math

  # A dense "dumbbell": two disks joined by a narrow neck. A convex hull
  # would span both disks as a single blob; an alpha-shape should carve the
  # neck concavity and produce more boundary points than the convex hull.
  dumbbell: list[tuple[float, float]] = []
  for cx in (-4.0, 4.0):
    for i in range(64):
      angle = i / 64.0 * 2.0 * math.pi
      dumbbell.append((cx + 2.5 * math.cos(angle), 2.5 * math.sin(angle)))
  alpha = 1.0 / (13.0 * 0.35)
  ring, status = contours.alpha_shape_2d(dumbbell, alpha)
  assert status == "alpha_shape"
  convex = contours.convex_hull_2d(dumbbell)
  # The alpha-shape must keep strictly more boundary detail than the convex
  # hull (the hull collapses the neck).
  assert len(ring) > len(convex)

  # Too few points => graceful convex-hull fallback, never an exception.
  ring_few, status_few = contours.alpha_shape_2d(
    [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], alpha
  )
  assert status_few == "convex_hull"
  assert len(ring_few) >= 3

  # Empty input is rejected by the whole-airframe builder, not by the
  # alpha-shape helper (which returns an empty hull).
  ring_empty, status_empty = contours.alpha_shape_2d(
    [], alpha
  )
  assert status_empty == "convex_hull"
  assert ring_empty == []


def test_whole_airframe_contour_report_structure() -> None:
  """The whole-airframe contour containment report records the contour method,
  tolerance, per-view contour metadata, and per-item outside distances built
  on top of the airframe constraint report."""
  require_airframe_geometry_extra()

  contour_report = build_airframe_review_bundle()["contour_report"]
  assert contour_report["schema_version"] == (
    "a2.target_geometry_whole_airframe_contour_containment.v1"
  )
  assert contour_report["contour_method"] == "projected_mesh_triangle_union"
  assert contour_report["tolerance_m"] == 0.05
  assert contour_report["summary"]["item_count"] == 26
  assert contour_report["summary"]["excluded_review_only_split_segment_count"] == 8
  # Shape-aware thin-prism/frustum receiver projections now fit inside the
  # projected mesh contour. Review-only split segments are still excluded from
  # this final-result surface.
  assert contour_report["summary"]["exceeds_tolerance_item_count"] == 0
  assert contour_report["summary"]["exceeding_item_ids"] == []
  assert contour_report["summary"]["max_outside_distance_m"] == 0.0
  # Every view produced a triangle-union contour from the audit mesh.
  for view in ("top", "side", "front"):
    meta = contour_report["summary"]["contours"][view]
    assert meta["status"] == "projected_mesh_triangle_union"
    assert meta["source_triangle_count"] == 4504
    assert meta["polygon_count"] == 1
    assert meta["contour_point_count"] >= 100
    assert len(contour_report["contours"][view]["points_m"]) == meta[
      "contour_point_count"
    ]
  # The rows stay deterministic even with no exceeders.
  row_ids = [row["item_id"] for row in contour_report["rows"]]
  assert row_ids[0] == "afterburner_nozzle"
  exceeder_ids = {
    row["item_id"] for row in contour_report["rows"] if row["exceeds_tolerance"]
  }
  assert exceeder_ids == set()
  assert "engine_core_afterburner_segment" not in row_ids
  assert contour_report["authority_boundary"][
    "projected_mesh_contour_diagnostic_only"
  ] is True
  assert contour_report["authority_boundary"][
    "tolerance_is_engineering_review_margin_not_physical_clearance"
  ] is True


def test_geometry_optional_dependencies_advertised() -> None:
  """The geometry dependency group must be declared so contour diagnostics are
  installable from a fresh checkout."""
  pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
  assert 'geometry = [' in pyproject
  assert '"scipy"' in pyproject
  assert '"shapely"' in pyproject
