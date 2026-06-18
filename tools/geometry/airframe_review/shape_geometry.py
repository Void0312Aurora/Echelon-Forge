"""Shared shape and airframe-containment geometry helpers."""

from __future__ import annotations

import math
from typing import Any

from tools.geometry.airframe_review import bounds_ops, contours, projection_geometry
from tools.geometry.airframe_review.constants import SILHOUETTE_VIEW_AXES
from tools.geometry.airframe_review.primitives import _round, _round_points, _round_vec


def _axis_index(axis_name: str | None) -> int:
  return {"x": 0, "y": 1, "z": 2}.get(axis_name or "x", 0)


def _bounds_from_center_half_extents(
  center: list[float],
  half_extents: list[float],
) -> dict[str, list[float]]:
  return bounds_ops.bounds_from_min_max(
    [center[index] - half_extents[index] for index in range(3)],
    [center[index] + half_extents[index] for index in range(3)],
  )


def _polygon_area_2d(points: list[list[float]]) -> float:
  if len(points) < 3:
    return 0.0
  area = 0.0
  previous = points[-1]
  for current in points:
    area += previous[0] * current[1] - current[0] * previous[1]
    previous = current
  return abs(area) * 0.5


def _footprint_bounds(
  points: list[list[float]],
  *,
  z_center: float,
  z_half_extent: float,
) -> dict[str, list[float]]:
  return bounds_ops.bounds_from_min_max(
    [
      min(point[0] for point in points),
      min(point[1] for point in points),
      z_center - z_half_extent,
    ],
    [
      max(point[0] for point in points),
      max(point[1] for point in points),
      z_center + z_half_extent,
    ],
  )


def _rule_footprint_points_for_center(
  rule: dict[str, Any],
  center: list[float],
) -> list[list[float]]:
  points = [
    [float(point[0]), float(point[1])]
    for point in rule.get("footprint_points_m", [])
  ]
  if not points:
    return []
  footprint_center_x = (min(point[0] for point in points) + max(point[0] for point in points)) * 0.5
  footprint_center_y = (min(point[1] for point in points) + max(point[1] for point in points)) * 0.5
  shift_x = float(center[0]) - footprint_center_x
  shift_y = float(center[1]) - footprint_center_y
  return _round_points([[point[0] + shift_x, point[1] + shift_y] for point in points])


def _shape_half_extents(
  *,
  rule: dict[str, Any],
  component_bounds: dict[str, list[float]],
) -> tuple[list[float], dict[str, Any]]:
  shape = rule["shape"]
  if shape == "thin_prism" and rule.get("footprint_points_m"):
    points = [
      [float(point[0]), float(point[1])]
      for point in rule["footprint_points_m"]
    ]
    z_span = (
      float(rule["dimensions_m"][2])
      if "dimensions_m" in rule and len(rule["dimensions_m"]) >= 3
      else max(float(component_bounds["span"][2]), 0.02)
    )
    half_extents = [
      (max(point[0] for point in points) - min(point[0] for point in points)) * 0.5,
      (max(point[1] for point in points) - min(point[1] for point in points)) * 0.5,
      max(z_span * 0.5, 0.01),
    ]
    return half_extents, {
      "shape": "thin_prism",
      "footprint_points_m": _round_points(points),
      "footprint_area_m2": _round(_polygon_area_2d(points)),
      "thickness_axis": "z",
      "thickness_m": _round(z_span),
    }
  if "dimensions_m" in rule:
    scaled_span = [max(float(value), 0.02) for value in rule["dimensions_m"]]
  else:
    span_scale = rule.get("span_scale", [0.78, 0.78, 0.78])
    scaled_span = [
      max(component_bounds["span"][index] * float(span_scale[index]), 0.02)
      for index in range(3)
    ]
  if shape == "sphere":
    radius = max(min(scaled_span) * 0.5, 0.02)
    return [radius, radius, radius], {
      "shape": "sphere",
      "radius_m": _round(radius),
    }

  if shape in {"cylinder", "capsule"}:
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    radius = max(min(scaled_span[index] for index in radial_axes) * 0.5, 0.02)
    half_extents = [radius, radius, radius]
    if shape == "capsule":
      half_extents[axis] = max(scaled_span[axis] * 0.5, radius)
    else:
      half_extents[axis] = max(scaled_span[axis] * 0.5, 0.01)
    payload = {
      "shape": shape,
      "axis": ["x", "y", "z"][axis],
      "radius_m": _round(radius),
      "axis_half_extent_m": _round(half_extents[axis]),
    }
    if shape == "capsule":
      payload["cylinder_half_length_m"] = _round(
        max(half_extents[axis] - radius, 0.0)
      )
    return half_extents, payload

  half_extents = [value * 0.5 for value in scaled_span]
  if shape == "ellipsoid":
    return half_extents, {
      "shape": "ellipsoid",
      "radii_m": _round_vec(half_extents),
    }
  if shape == "frustum":
    axis = _axis_index(rule.get("axis"))
    negative_radius = float(
      rule.get("negative_axis_radius_m", max(half_extents[index] for index in range(3) if index != axis))
    )
    positive_radius = float(
      rule.get("positive_axis_radius_m", max(half_extents[index] for index in range(3) if index != axis))
    )
    return half_extents, {
      "shape": "frustum",
      "axis": ["x", "y", "z"][axis],
      "axis_half_extent_m": _round(half_extents[axis]),
      "negative_axis_radius_m": _round(negative_radius),
      "positive_axis_radius_m": _round(positive_radius),
    }
  if shape == "thin_prism":
    return half_extents, {
      "shape": "thin_prism",
      "footprint_points_m": [],
      "footprint_area_m2": _round((2.0 * half_extents[0]) * (2.0 * half_extents[1])),
      "thickness_axis": "z",
      "thickness_m": _round(2.0 * half_extents[2]),
    }
  return half_extents, {
    "shape": "obb",
    "half_extents_m": _round_vec(half_extents),
  }


def _shape_payload_from_half_extents(
  *,
  rule: dict[str, Any],
  half_extents: list[float],
  center: list[float] | None = None,
) -> dict[str, Any]:
  shape = rule["shape"]
  if shape == "thin_prism" and rule.get("footprint_points_m"):
    points = _rule_footprint_points_for_center(
      rule,
      center if center is not None else list(_footprint_bounds(
        [[float(point[0]), float(point[1])] for point in rule["footprint_points_m"]],
        z_center=0.0,
        z_half_extent=half_extents[2],
      )["center"]),
    )
    return {
      "shape": "thin_prism",
      "footprint_points_m": points,
      "footprint_area_m2": _round(_polygon_area_2d(points)),
      "thickness_axis": "z",
      "thickness_m": _round(half_extents[2] * 2.0),
    }
  if shape == "thin_prism":
    points: list[list[float]] = []
    if center is not None:
      center_x = float(center[0])
      center_y = float(center[1])
      points = _round_points(
        [
          [center_x - half_extents[0], center_y - half_extents[1]],
          [center_x + half_extents[0], center_y - half_extents[1]],
          [center_x + half_extents[0], center_y + half_extents[1]],
          [center_x - half_extents[0], center_y + half_extents[1]],
        ]
      )
    area = (
      _polygon_area_2d(points)
      if points
      else (2.0 * half_extents[0]) * (2.0 * half_extents[1])
    )
    return {
      "shape": "thin_prism",
      "footprint_points_m": points,
      "footprint_area_m2": _round(area),
      "thickness_axis": "z",
      "thickness_m": _round(half_extents[2] * 2.0),
    }
  if shape == "sphere":
    return {
      "shape": "sphere",
      "radius_m": _round(min(half_extents)),
    }
  if shape in {"cylinder", "capsule"}:
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    radius = min(half_extents[index] for index in radial_axes)
    payload = {
      "shape": shape,
      "axis": ["x", "y", "z"][axis],
      "radius_m": _round(radius),
      "axis_half_extent_m": _round(half_extents[axis]),
    }
    if shape == "capsule":
      payload["cylinder_half_length_m"] = _round(
        max(half_extents[axis] - radius, 0.0)
      )
    return payload
  if shape == "ellipsoid":
    return {
      "shape": "ellipsoid",
      "radii_m": _round_vec(half_extents),
    }
  if shape == "frustum":
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    default_radius = max(half_extents[index] for index in radial_axes)
    return {
      "shape": "frustum",
      "axis": ["x", "y", "z"][axis],
      "axis_half_extent_m": _round(half_extents[axis]),
      "negative_axis_radius_m": _round(
        float(rule.get("negative_axis_radius_m", default_radius))
      ),
      "positive_axis_radius_m": _round(
        float(rule.get("positive_axis_radius_m", default_radius))
      ),
    }
  return {
    "shape": "obb",
    "half_extents_m": _round_vec(half_extents),
  }


def _shape_volume_m3(rule: dict[str, Any], half_extents: list[float]) -> float:
  shape = rule["shape"]
  if shape == "sphere":
    radius = min(half_extents)
    return 4.0 * math.pi * radius**3 / 3.0
  if shape == "ellipsoid":
    return 4.0 * math.pi * half_extents[0] * half_extents[1] * half_extents[2] / 3.0
  if shape == "cylinder":
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    radius = min(half_extents[index] for index in radial_axes)
    return math.pi * radius**2 * (2.0 * half_extents[axis])
  if shape == "capsule":
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    radius = min(half_extents[index] for index in radial_axes)
    cylinder_half_length = max(half_extents[axis] - radius, 0.0)
    return (
      math.pi * radius**2 * (2.0 * cylinder_half_length)
      + 4.0 * math.pi * radius**3 / 3.0
    )
  if shape == "frustum":
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    default_radius = max(half_extents[index] for index in radial_axes)
    negative_radius = float(rule.get("negative_axis_radius_m", default_radius))
    positive_radius = float(rule.get("positive_axis_radius_m", default_radius))
    length = 2.0 * half_extents[axis]
    return (
      math.pi
      * length
      * (
        negative_radius**2
        + negative_radius * positive_radius
        + positive_radius**2
      )
      / 3.0
    )
  if shape == "thin_prism" and rule.get("footprint_points_m"):
    points = [
      [float(point[0]), float(point[1])]
      for point in rule["footprint_points_m"]
    ]
    return _polygon_area_2d(points) * (2.0 * half_extents[2])
  return 8.0 * half_extents[0] * half_extents[1] * half_extents[2]


def _whole_airframe_projection_hulls(
  airframe_contours: dict[str, dict[str, Any]],
) -> dict[str, list[list[float]]]:
  """Return per-view whole-airframe containment contours.

  The return type is ``dict[view, list[list[float]]]``: a single point ring
  per view (not a list of rings). Downstream containment helpers consume this
  single-ring form.
  """
  return {
    view: list(contour["points_m"])
    for view, contour in airframe_contours.items()
  }


def _projection_adjust_center_to_airframe_hulls(
  *,
  center: list[float],
  half_extents: list[float],
  airframe_projection_hulls: dict[str, list[list[float]]],
) -> dict[str, Any]:
  adjusted_center = [float(value) for value in center]
  for _ in range(2):
    for view, axes in SILHOUETTE_VIEW_AXES.items():
      contour_points = airframe_projection_hulls.get(view, [])
      if len(contour_points) < 3:
        continue
      projected_bounds = projection_geometry.project_bounds(
        _bounds_from_center_half_extents(adjusted_center, half_extents),
        axes,
      )
      current_center = (
        (projected_bounds[0] + projected_bounds[2]) * 0.5,
        (projected_bounds[1] + projected_bounds[3]) * 0.5,
      )
      hull_bounds = projection_geometry.projected_hull_bounds(contour_points)
      if hull_bounds is None:
        continue
      candidate_bounds = projection_geometry.shift_bounds_inside_parent_projection_preserve_size(
        projected_bounds,
        hull_bounds,
        hull_points=contour_points,
      )
      candidate_center = (
        (candidate_bounds[0] + candidate_bounds[2]) * 0.5,
        (candidate_bounds[1] + candidate_bounds[3]) * 0.5,
      )
      shift = math.hypot(
        candidate_center[0] - current_center[0],
        candidate_center[1] - current_center[1],
      )
      if shift < 1.0e-9:
        continue
      adjusted_center[axes[0]] = (candidate_bounds[0] + candidate_bounds[2]) * 0.5
      adjusted_center[axes[1]] = (candidate_bounds[1] + candidate_bounds[3]) * 0.5
  shift_m = math.sqrt(
    sum((adjusted_center[index] - center[index]) ** 2 for index in range(3))
  )
  return {
    "center_m": _round_vec(adjusted_center),
    "center_shift_m": _round(shift_m),
  }


def _airframe_silhouette_view_diagnostic(
  geometry: dict[str, Any],
  *,
  view: str,
  contour_points: list[list[float]],
  shape: str,
  axis: str,
) -> dict[str, Any]:
  bounds = geometry["bounds"]
  axes = SILHOUETTE_VIEW_AXES[view]
  sample_points = projection_geometry.shape_projected_containment_samples(
    bounds,
    axes=axes,
    shape=shape,
    axis=axis,
    geometry=geometry,
  )
  outside_distances: list[float] = []
  inside_count = 0
  for point in sample_points:
    inside, outside_distance = projection_geometry.point_in_contour(point, contour_points)
    if inside:
      inside_count += 1
    else:
      outside_distances.append(outside_distance)
  outside_count = len(sample_points) - inside_count
  max_outside_distance = max(outside_distances) if outside_distances else 0.0
  projected_bounds = projection_geometry.project_bounds(bounds, axes)
  return {
    "view": view,
    "projected_bounds": [_round(value) for value in projected_bounds],
    "sample_count": len(sample_points),
    "inside_sample_count": inside_count,
    "outside_sample_count": outside_count,
    "inside_sample_fraction": _round(inside_count / max(len(sample_points), 1), 5),
    "fully_inside_silhouette": outside_count == 0,
    "max_outside_distance_m": _round(max_outside_distance, 5),
    "exceeds_tolerance": max_outside_distance > 0.0,
  }


def _airframe_silhouette_diagnostics(
  geometry: dict[str, Any],
  airframe_projection_hulls: dict[str, list[list[float]]],
) -> dict[str, Any]:
  bounds = geometry["bounds"]
  shape = geometry.get("shape", "obb")
  axis = geometry.get("axis", "")
  views = {
    view: _airframe_silhouette_view_diagnostic(
      geometry,
      view=view,
      contour_points=airframe_projection_hulls.get(view, []),
      shape=shape,
      axis=axis,
    )
    for view in SILHOUETTE_VIEW_AXES
  }
  outside_views = [
    view
    for view, diagnostic in views.items()
    if not diagnostic["fully_inside_silhouette"]
  ]
  outside_sample_count = sum(
    diagnostic["outside_sample_count"] for diagnostic in views.values()
  )
  sample_count = sum(diagnostic["sample_count"] for diagnostic in views.values())
  max_outside_distance = max(
    (diagnostic["max_outside_distance_m"] for diagnostic in views.values()),
    default=0.0,
  )
  return {
    "views": views,
    "outside_views": outside_views,
    "outside_view_count": len(outside_views),
    "outside_sample_count": outside_sample_count,
    "sample_count": sample_count,
    "inside_sample_fraction": _round(
      (sample_count - outside_sample_count) / max(sample_count, 1),
      5,
    ),
    "fully_inside_all_views": outside_sample_count == 0,
    "max_outside_distance_m": _round(max_outside_distance, 5),
  }


def _silhouette_fit_candidate(
  *,
  geometry: dict[str, Any],
  airframe_projection_hulls: dict[str, list[list[float]]],
) -> dict[str, Any]:
  center = geometry["center_m"]
  half_extents = geometry["half_extents_m"]
  before = _airframe_silhouette_diagnostics(
    geometry,
    airframe_projection_hulls,
  )
  adjustment = _projection_adjust_center_to_airframe_hulls(
    center=center,
    half_extents=half_extents,
    airframe_projection_hulls=airframe_projection_hulls,
  )
  candidate_bounds = _bounds_from_center_half_extents(
    adjustment["center_m"],
    half_extents,
  )
  candidate_geometry = {
    **geometry,
    "center_m": adjustment["center_m"],
    "bounds": candidate_bounds,
  }
  after = _airframe_silhouette_diagnostics(
    candidate_geometry,
    airframe_projection_hulls,
  )
  return {
    "current_silhouette": before,
    "center_shift_candidate_m": adjustment["center_shift_m"],
    "candidate_center_m": adjustment["center_m"],
    "candidate_bounds": candidate_bounds,
    "candidate_silhouette": after,
    "outside_sample_reduction": (
      before["outside_sample_count"] - after["outside_sample_count"]
    ),
    "max_outside_distance_reduction_m": _round(
      before["max_outside_distance_m"] - after["max_outside_distance_m"], 5
    ),
  }


def _whole_airframe_containment_hulls(
  fine_proxy: dict[str, Any],
) -> dict[str, list[list[float]]]:
  """Per-view whole-airframe containment contours for silhouette testing.

  Builds projected mesh-triangle union contours from the cached triangle
  records when available and returns them in the single-ring-per-view form
  consumed by the silhouette diagnostics. If a fine_proxy was built before the
  triangle cache existed, the vertex alpha-shape cache is still accepted as a
  lower-fidelity contour source. A missing contour cache is a generation error.
  """
  sim_triangle_records = fine_proxy.get("_sim_triangle_records")
  if sim_triangle_records:
    airframe_contours = contours.projected_mesh_triangle_union_contours(
      sim_triangle_records
    )
    return _whole_airframe_projection_hulls(airframe_contours)
  sim_vertex_records = fine_proxy.get("_sim_vertex_records")
  if sim_vertex_records:
    airframe_contours = contours.whole_airframe_alpha_contours(sim_vertex_records)
    return _whole_airframe_projection_hulls(airframe_contours)
  raise ValueError(
    "fine_proxy must include glTF contour caches; build it with manifest and audit scene paths"
  )
