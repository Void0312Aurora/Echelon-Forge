"""Projected geometry helpers for airframe review contours and views."""

from __future__ import annotations

import math
from typing import Any

from tools.geometry.airframe_review.constants import SILHOUETTE_CONTAINMENT_TOLERANCE_M
from tools.geometry.airframe_review.primitives import _round


_PERIMETER_SAMPLE_STEP_RAD = math.radians(15.0)


def axis_index(axis_name: str | None) -> int:
  return {"x": 0, "y": 1, "z": 2}.get(axis_name or "x", 0)


def project_bounds(bounds: dict[str, list[float]], axes: tuple[int, int]) -> tuple[float, float, float, float]:
  x_axis, y_axis = axes
  return (
    bounds["min"][x_axis],
    bounds["min"][y_axis],
    bounds["max"][x_axis],
    bounds["max"][y_axis],
  )


def projected_bounds_sample_points(
  bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  return [
    (min_x, min_y),
    (center_x, min_y),
    (max_x, min_y),
    (min_x, center_y),
    (center_x, center_y),
    (max_x, center_y),
    (min_x, max_y),
    (center_x, max_y),
    (max_x, max_y),
  ]


def projected_ellipse_sample_points(
  bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  return [
    (center_x, center_y),
    (min_x, center_y),
    (max_x, center_y),
    (center_x, min_y),
    (center_x, max_y),
  ]


def projected_capsule_sample_points(
  bounds: tuple[float, float, float, float],
  *,
  projected_axis_position: int | None,
) -> list[tuple[float, float]]:
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  if projected_axis_position == 0:
    return [
      (center_x, center_y),
      (min_x, center_y),
      (max_x, center_y),
      (center_x, min_y),
      (center_x, max_y),
      ((min_x + center_x) * 0.5, min_y),
      ((min_x + center_x) * 0.5, max_y),
      ((max_x + center_x) * 0.5, min_y),
      ((max_x + center_x) * 0.5, max_y),
    ]
  if projected_axis_position == 1:
    return [
      (center_x, center_y),
      (center_x, min_y),
      (center_x, max_y),
      (min_x, center_y),
      (max_x, center_y),
      (min_x, (min_y + center_y) * 0.5),
      (max_x, (min_y + center_y) * 0.5),
      (min_x, (max_y + center_y) * 0.5),
      (max_x, (max_y + center_y) * 0.5),
    ]
  return projected_ellipse_sample_points(bounds)


def projected_shape_sample_points(
  bounds: tuple[float, float, float, float],
  *,
  axes: tuple[int, int],
  shape: str,
  axis: str,
) -> list[tuple[float, float]]:
  if shape in {"sphere", "ellipsoid"}:
    return projected_ellipse_sample_points(bounds)
  if shape in {"cylinder", "capsule"}:
    shape_axis_index = axis_index(axis)
    projected_axis_position = (
      axes.index(shape_axis_index) if shape_axis_index in axes else None
    )
    if shape == "capsule":
      return projected_capsule_sample_points(
        bounds,
        projected_axis_position=projected_axis_position,
      )
    if projected_axis_position is None:
      return projected_ellipse_sample_points(bounds)
    return projected_bounds_sample_points(bounds)
  return projected_bounds_sample_points(bounds)


def projected_ellipse_perimeter_samples(
  bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
  """Dense perimeter samples of the ellipse inscribed in ``bounds``.

  Used for whole-airframe contour containment so a tilted ellipsoid receiver
  cannot hide a corner protrusion behind the legacy 5-point axis cross.
  """
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  radius_x = (max_x - min_x) * 0.5
  radius_y = (max_y - min_y) * 0.5
  samples: list[tuple[float, float]] = [(center_x, center_y)]
  angle = 0.0
  while angle < 2.0 * math.pi - 1.0e-9:
    samples.append(
      (center_x + radius_x * math.cos(angle), center_y + radius_y * math.sin(angle))
    )
    angle += _PERIMETER_SAMPLE_STEP_RAD
  return samples


def projected_capsule_perimeter_samples(
  bounds: tuple[float, float, float, float],
  *,
  axes: tuple[int, int],
  axis: str,
) -> list[tuple[float, float]]:
  """Dense perimeter samples for a capsule projected into ``axes``.

  The capsule is modeled as a centerline segment (length 2*half_extent along
  ``axis``) with hemispherical end caps of radius equal to the radial
  half-extent. Samples: center, both end points, plus dense half-rings around
  each cap (the outer-facing semicircle, since the inner-facing semicircle is
  covered by the centerline span).
  """
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  half_x = (max_x - min_x) * 0.5
  half_y = (max_y - min_y) * 0.5
  shape_axis_index = axis_index(axis)
  if shape_axis_index not in axes:
    return projected_ellipse_perimeter_samples(bounds)
  if shape_axis_index == axes[0]:
    # Capsule long axis is the projected x axis.
    length = half_x
    radius = half_y
    end_a = (center_x - length, center_y)
    end_b = (center_x + length, center_y)
    # end_a faces -x (outer semicircle: angles pi/2..3pi/2);
    # end_b faces +x (outer semicircle: -pi/2..pi/2).
    end_a_start = math.pi * 0.5
    end_b_start = -math.pi * 0.5
  else:
    length = half_y
    radius = half_x
    end_a = (center_x, center_y - length)
    end_b = (center_x, center_y + length)
    # end_a faces -y, end_b faces +y.
    end_a_start = math.pi
    end_b_start = 0.0
  samples: list[tuple[float, float]] = [(center_x, center_y), end_a, end_b]
  angle = 0.0
  while angle < math.pi - 1.0e-9:
    offset_x = radius * math.cos(end_a_start + angle)
    offset_y = radius * math.sin(end_a_start + angle)
    samples.append((end_a[0] + offset_x, end_a[1] + offset_y))
    offset_x = radius * math.cos(end_b_start + angle)
    offset_y = radius * math.sin(end_b_start + angle)
    samples.append((end_b[0] + offset_x, end_b[1] + offset_y))
    angle += _PERIMETER_SAMPLE_STEP_RAD
  return samples


def polygon_samples(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
  if not points:
    return []
  samples = list(points)
  for first, second in zip(points, points[1:] + points[:1]):
    samples.append(((first[0] + second[0]) * 0.5, (first[1] + second[1]) * 0.5))
  samples.append(
    (
      sum(point[0] for point in points) / len(points),
      sum(point[1] for point in points) / len(points),
    )
  )
  return samples


def projected_thin_prism_samples(
  geometry: dict[str, Any],
  axes: tuple[int, int],
) -> list[tuple[float, float]]:
  footprint = geometry.get("footprint_points_m", [])
  if footprint and set(axes) == {0, 1}:
    axis_x, axis_y = axes
    index_by_axis = {0: 0, 1: 1}
    points = [
      (float(point[index_by_axis[axis_x]]), float(point[index_by_axis[axis_y]]))
      for point in footprint
    ]
    return polygon_samples(points)
  return projected_bounds_sample_points(project_bounds(geometry["bounds"], axes))


def projected_frustum_samples(
  geometry: dict[str, Any],
  axes: tuple[int, int],
) -> list[tuple[float, float]]:
  bounds = geometry["bounds"]
  axis = geometry.get("axis", "x")
  shape_axis_index = axis_index(axis)
  if shape_axis_index not in axes:
    return projected_ellipse_perimeter_samples(project_bounds(bounds, axes))
  projected_bounds = project_bounds(bounds, axes)
  min_x, min_y, max_x, max_y = projected_bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  negative_radius = float(geometry.get("negative_axis_radius_m", 0.0))
  positive_radius = float(geometry.get("positive_axis_radius_m", negative_radius))
  if shape_axis_index == axes[0]:
    points = [
      (min_x, center_y - negative_radius),
      (max_x, center_y - positive_radius),
      (max_x, center_y + positive_radius),
      (min_x, center_y + negative_radius),
    ]
  else:
    points = [
      (center_x - negative_radius, min_y),
      (center_x - positive_radius, max_y),
      (center_x + positive_radius, max_y),
      (center_x + negative_radius, min_y),
    ]
  return polygon_samples(points)


def shape_projected_containment_samples(
  bounds: dict[str, list[float]],
  *,
  axes: tuple[int, int],
  shape: str,
  axis: str,
  geometry: dict[str, Any] | None = None,
) -> list[tuple[float, float]]:
  """Shape-aware containment samples for a receiver projected into ``axes``.

  Ellipsoid and capsule receivers use dense projected perimeter samples.
  AABB/OBB receivers use the projected 3x3 box grid (four projected corners,
  four projected edge midpoints, and center). This is the sample set used
  against the whole-airframe contour.
  """
  projected_bounds = project_bounds(bounds, axes)
  if shape == "thin_prism" and geometry is not None:
    return projected_thin_prism_samples(geometry, axes)
  if shape == "frustum" and geometry is not None:
    return projected_frustum_samples(geometry, axes)
  if shape in {"sphere", "ellipsoid"}:
    return projected_ellipse_perimeter_samples(projected_bounds)
  if shape in {"cylinder", "capsule"}:
    return projected_capsule_perimeter_samples(
      projected_bounds,
      axes=axes,
      axis=axis,
    )
  # AABB / OBB: projected 3x3 grid = four corners, four edge midpoints,
  # and center.
  min_x, min_y, max_x, max_y = projected_bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  return [
    (min_x, min_y),
    (center_x, min_y),
    (max_x, min_y),
    (min_x, center_y),
    (center_x, center_y),
    (max_x, center_y),
    (min_x, max_y),
    (center_x, max_y),
    (max_x, max_y),
  ]


def projected_hull_bounds(
  hull_points: list[list[float]],
) -> tuple[float, float, float, float] | None:
  if len(hull_points) < 3:
    return None
  return (
    min(point[0] for point in hull_points),
    min(point[1] for point in hull_points),
    max(point[0] for point in hull_points),
    max(point[1] for point in hull_points),
  )


def fit_bounds_inside_parent_projection(
  bounds: tuple[float, float, float, float],
  parent_bounds: tuple[float, float, float, float],
  *,
  hull_points: list[list[float]] | None = None,
  child_index: int = 0,
  child_count: int = 1,
) -> tuple[float, float, float, float]:
  min_x, min_y, max_x, max_y = bounds
  parent_min_x, parent_min_y, parent_max_x, parent_max_y = parent_bounds
  parent_width = max(parent_max_x - parent_min_x, 1.0e-6)
  parent_height = max(parent_max_y - parent_min_y, 1.0e-6)
  max_ratio = 0.34 if child_count <= 2 else 0.24
  width = min(max(max_x - min_x, parent_width * 0.08), parent_width * max_ratio)
  height = min(max(max_y - min_y, parent_height * 0.08), parent_height * max_ratio)
  raw_center_x = (min_x + max_x) * 0.5
  raw_center_y = (min_y + max_y) * 0.5
  center_x = min(
    max(raw_center_x, parent_min_x + width * 0.5),
    parent_max_x - width * 0.5,
  )
  center_y = min(
    max(raw_center_y, parent_min_y + height * 0.5),
    parent_max_y - height * 0.5,
  )
  if hull_points:
    safe_center_x, safe_center_y, safe_distance = projected_polygon_safe_point(
      hull_points,
      parent_bounds,
    )
    raw_candidate = (center_x, center_y)
    raw_distance = (
      distance_to_projected_polygon_edges(raw_candidate, hull_points)
      if point_in_projected_polygon(raw_candidate, hull_points)
      else 0.0
    )
    if child_count > 1:
      offset_slots = [
        (-0.42, 0.0),
        (0.42, 0.0),
        (0.0, -0.42),
        (0.0, 0.42),
        (0.0, 0.0),
      ]
      offset_x, offset_y = offset_slots[child_index % len(offset_slots)]
      candidate_center = (
        safe_center_x + safe_distance * offset_x,
        safe_center_y + safe_distance * offset_y,
      )
    elif raw_distance >= safe_distance * 0.35:
      candidate_center = raw_candidate
    else:
      candidate_center = (safe_center_x, safe_center_y)
    if not point_in_projected_polygon(candidate_center, hull_points):
      candidate_center = (safe_center_x, safe_center_y)
    center_x, center_y = candidate_center
    edge_distance = distance_to_projected_polygon_edges(
      (center_x, center_y),
      hull_points,
    )
    safe_half_diagonal = max(edge_distance * 0.62, 1.0e-6)
    safe_axis_span = max(safe_half_diagonal * math.sqrt(2.0), 1.0e-6)
    width = min(width, safe_axis_span)
    height = min(height, safe_axis_span)
  return (
    center_x - width * 0.5,
    center_y - height * 0.5,
    center_x + width * 0.5,
    center_y + height * 0.5,
  )


def shift_bounds_inside_parent_projection_preserve_size(
  bounds: tuple[float, float, float, float],
  parent_bounds: tuple[float, float, float, float],
  *,
  hull_points: list[list[float]] | None = None,
  child_index: int = 0,
  child_count: int = 1,
) -> tuple[float, float, float, float]:
  min_x, min_y, max_x, max_y = bounds
  width = max(max_x - min_x, 1.0e-6)
  height = max(max_y - min_y, 1.0e-6)
  parent_min_x, parent_min_y, parent_max_x, parent_max_y = parent_bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  if hull_points:
    safe_center_x, safe_center_y, safe_distance = projected_polygon_safe_point(
      hull_points,
      parent_bounds,
    )
    candidate_center = (center_x, center_y)
    if not point_in_projected_polygon(candidate_center, hull_points):
      candidate_center = (safe_center_x, safe_center_y)
    if child_count > 1 and safe_distance > 1.0e-6:
      offset_slots = [
        (-0.35, 0.0),
        (0.35, 0.0),
        (0.0, -0.35),
        (0.0, 0.35),
        (0.0, 0.0),
      ]
      offset_x, offset_y = offset_slots[child_index % len(offset_slots)]
      offset_candidate = (
        safe_center_x + safe_distance * offset_x,
        safe_center_y + safe_distance * offset_y,
      )
      if point_in_projected_polygon(offset_candidate, hull_points):
        candidate_center = offset_candidate
    center_x, center_y = candidate_center
  if width <= parent_max_x - parent_min_x:
    center_x = min(
      max(center_x, parent_min_x + width * 0.5),
      parent_max_x - width * 0.5,
    )
  if height <= parent_max_y - parent_min_y:
    center_y = min(
      max(center_y, parent_min_y + height * 0.5),
      parent_max_y - height * 0.5,
    )
  return (
    center_x - width * 0.5,
    center_y - height * 0.5,
    center_x + width * 0.5,
    center_y + height * 0.5,
  )


def projected_polygon_safe_point(
  points: list[list[float]],
  bounds: tuple[float, float, float, float],
) -> tuple[float, float, float]:
  min_x, min_y, max_x, max_y = bounds
  centroid = projected_polygon_centroid(points)
  candidates: list[tuple[float, float]] = [
    centroid,
    ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5),
  ]
  steps = (0.18, 0.30, 0.42, 0.50, 0.58, 0.70, 0.82)
  for x_fraction in steps:
    for y_fraction in steps:
      candidates.append(
        (
          min_x + (max_x - min_x) * x_fraction,
          min_y + (max_y - min_y) * y_fraction,
        )
      )
  best_point = centroid
  best_distance = -1.0
  for candidate in candidates:
    if not point_in_projected_polygon(candidate, points):
      continue
    distance = distance_to_projected_polygon_edges(candidate, points)
    if distance > best_distance:
      best_point = candidate
      best_distance = distance
  if best_distance >= 0.0:
    return best_point[0], best_point[1], best_distance
  return centroid[0], centroid[1], 0.0


def projected_polygon_centroid(
  points: list[list[float]],
) -> tuple[float, float]:
  if not points:
    return 0.0, 0.0
  return (
    sum(point[0] for point in points) / len(points),
    sum(point[1] for point in points) / len(points),
  )


def point_in_projected_polygon(
  point: tuple[float, float],
  polygon: list[list[float]],
) -> bool:
  if len(polygon) < 3:
    return False
  x, y = point
  inside = False
  previous = polygon[-1]
  for current in polygon:
    x1, y1 = previous[0], previous[1]
    x2, y2 = current[0], current[1]
    crosses = (y1 > y) != (y2 > y)
    if crosses:
      x_intersection = (x2 - x1) * (y - y1) / (y2 - y1 + 1.0e-12) + x1
      if x < x_intersection:
        inside = not inside
    previous = current
  return inside


def distance_to_projected_polygon_edges(
  point: tuple[float, float],
  polygon: list[list[float]],
) -> float:
  if len(polygon) < 2:
    return 0.0
  point_x, point_y = point
  distances: list[float] = []
  previous = polygon[-1]
  for current in polygon:
    x1, y1 = previous[0], previous[1]
    x2, y2 = current[0], current[1]
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq <= 1.0e-12:
      distances.append(math.hypot(point_x - x1, point_y - y1))
    else:
      t = max(
        0.0,
        min(1.0, ((point_x - x1) * dx + (point_y - y1) * dy) / length_sq),
      )
      closest_x = x1 + t * dx
      closest_y = y1 + t * dy
      distances.append(math.hypot(point_x - closest_x, point_y - closest_y))
    previous = current
  return min(distances) if distances else 0.0


def point_in_contour(
  point: tuple[float, float],
  contour_points: list[list[float]],
  *,
  tolerance_m: float = SILHOUETTE_CONTAINMENT_TOLERANCE_M,
) -> tuple[bool, float]:
  """Test a projected point against a single whole-airframe contour ring.

  Returns ``(inside, outside_distance_m)``. ``inside`` is True when the point
  is inside the contour polygon or within ``tolerance_m`` of a contour edge.
  ``outside_distance_m`` is ``0.0`` when inside, otherwise the minimum
  distance from the point to any contour edge.

  ``tolerance_m`` is an engineering review margin for mesh / proxy
  quantization noise, not a physical clearance.
  """
  if len(contour_points) < 3:
    return False, 0.0
  hull_bounds = projected_hull_bounds(contour_points)
  if hull_bounds is None:
    return False, 0.0
  min_x, min_y, max_x, max_y = hull_bounds
  # Broad-phase: far outside the AABB cannot be inside even with tolerance.
  if (
    point[0] < min_x - tolerance_m
    or point[0] > max_x + tolerance_m
    or point[1] < min_y - tolerance_m
    or point[1] > max_y + tolerance_m
  ):
    edge_distance = distance_to_projected_polygon_edges(point, contour_points)
    return False, _round(edge_distance, 5)
  if point_in_projected_polygon(point, contour_points):
    return True, 0.0
  edge_distance = distance_to_projected_polygon_edges(point, contour_points)
  if edge_distance <= tolerance_m:
    return True, 0.0
  return False, _round(edge_distance, 5)
