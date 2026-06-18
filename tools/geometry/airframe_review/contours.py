"""2D contour builders for airframe geometry review reports."""

from __future__ import annotations

import math
from typing import Any, Iterable

from tools.geometry.airframe_review import optional_deps
from tools.geometry.airframe_review.constants import (
  SILHOUETTE_VIEW_AXES,
  WHOLE_AIRFRAME_ALPHA_AXIS_FRACTION,
)
from tools.geometry.airframe_review.primitives import _round


def _cross_2d(
  origin: tuple[float, float],
  first: tuple[float, float],
  second: tuple[float, float],
) -> float:
  return (
    (first[0] - origin[0]) * (second[1] - origin[1])
    - (first[1] - origin[1]) * (second[0] - origin[0])
  )


def convex_hull_2d(points: Iterable[tuple[float, float]]) -> list[list[float]]:
  unique = sorted({(_round(point[0]), _round(point[1])) for point in points})
  if len(unique) <= 2:
    return [[point[0], point[1]] for point in unique]

  lower: list[tuple[float, float]] = []
  for point in unique:
    while len(lower) >= 2 and _cross_2d(lower[-2], lower[-1], point) <= 0.0:
      lower.pop()
    lower.append(point)

  upper: list[tuple[float, float]] = []
  for point in reversed(unique):
    while len(upper) >= 2 and _cross_2d(upper[-2], upper[-1], point) <= 0.0:
      upper.pop()
    upper.append(point)

  hull = lower[:-1] + upper[:-1]
  return [[point[0], point[1]] for point in hull]


def alpha_shape_2d(
  points: Iterable[tuple[float, float]],
  alpha: float,
) -> tuple[list[list[float]], str]:
  """Return (ring_points, status) for the 2D alpha-shape of ``points``."""
  optional_deps.require_geometry_deps()
  import numpy as _np

  point_list = list(points)
  if len(point_list) < 4:
    return convex_hull_2d(point_list), "convex_hull"

  coords = _np.array(
    [(float(p[0]), float(p[1])) for p in point_list],
    dtype=float,
  )
  triangulation = optional_deps.Delaunay(coords)
  alpha_radius = 1.0 / alpha if alpha > 0.0 else float("inf")
  edge_count: dict[tuple[int, int], int] = {}
  kept_triangle_count = 0
  for simplex in triangulation.simplices:
    ia, ib, ic = int(simplex[0]), int(simplex[1]), int(simplex[2])
    pa, pb, pc = coords[ia], coords[ib], coords[ic]
    a = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
    b = math.hypot(pc[0] - pb[0], pc[1] - pb[1])
    c = math.hypot(pa[0] - pc[0], pa[1] - pc[1])
    semi = (a + b + c) * 0.5
    area_sq = semi * (semi - a) * (semi - b) * (semi - c)
    if area_sq <= 1.0e-24:
      continue
    circumradius = (a * b * c) / (4.0 * math.sqrt(area_sq))
    if circumradius >= alpha_radius:
      continue
    kept_triangle_count += 1
    for i, j in ((ia, ib), (ib, ic), (ic, ia)):
      key = (min(i, j), max(i, j))
      edge_count[key] = edge_count.get(key, 0) + 1

  if kept_triangle_count == 0:
    return convex_hull_2d(point_list), "convex_hull"

  boundary_edges = [edge for edge, count in edge_count.items() if count == 1]
  boundary_lines = [
    _shapely_line_string((coords[i], coords[j])) for i, j in boundary_edges
  ]
  if not boundary_lines:
    return convex_hull_2d(point_list), "convex_hull"
  merged = optional_deps.shapely_unary_union(boundary_lines)
  geometries = (
    list(merged.geoms) if hasattr(merged, "geoms") else [merged]
  )
  polygons = list(optional_deps.shapely_polygonize(geometries))
  if not polygons:
    return convex_hull_2d(point_list), "convex_hull"
  largest = max(polygons, key=lambda polygon: polygon.area)
  if largest.area < 1.0e-9:
    return convex_hull_2d(point_list), "convex_hull"
  exterior = list(largest.exterior.coords)
  if len(exterior) > 1 and exterior[0] == exterior[-1]:
    exterior = exterior[:-1]
  return [[float(x), float(y)] for x, y in exterior], "alpha_shape"


def _shapely_line_string(coords: Any) -> Any:
  from shapely.geometry import LineString

  return LineString([(float(x), float(y)) for x, y in coords])


def whole_airframe_alpha_contours(
  sim_vertex_records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
  optional_deps.require_geometry_deps()
  if not sim_vertex_records:
    raise ValueError("sim_vertex_records must not be empty")

  all_points = [record["point_m"] for record in sim_vertex_records]
  contours: dict[str, dict[str, Any]] = {}
  for view, axes in SILHOUETTE_VIEW_AXES.items():
    projected = [
      (float(point[axes[0]]), float(point[axes[1]])) for point in all_points
    ]
    if len(projected) < 4:
      ring = convex_hull_2d(projected)
      contours[view] = {
        "points_m": ring,
        "polygons_m": [ring],
        "status": "convex_hull",
        "alpha": 0.0,
        "alpha_radius_m": 0.0,
        "source_vertex_count": len(projected),
        "contour_point_count": len(ring),
      }
      continue
    span_x = max(p[0] for p in projected) - min(p[0] for p in projected)
    span_y = max(p[1] for p in projected) - min(p[1] for p in projected)
    span = max(span_x, span_y)
    if span <= 0.0:
      ring = convex_hull_2d(projected)
      contours[view] = {
        "points_m": ring,
        "polygons_m": [ring],
        "status": "convex_hull",
        "alpha": 0.0,
        "alpha_radius_m": 0.0,
        "source_vertex_count": len(projected),
        "contour_point_count": len(ring),
      }
      continue
    alpha = 1.0 / (span * WHOLE_AIRFRAME_ALPHA_AXIS_FRACTION)
    ring, status = alpha_shape_2d(projected, alpha)
    contours[view] = {
      "points_m": ring,
      "polygons_m": [ring],
      "status": status,
      "alpha": _round(alpha),
      "alpha_radius_m": _round(1.0 / alpha),
      "source_vertex_count": len(projected),
      "contour_point_count": len(ring),
    }
  return contours


def projected_mesh_triangle_union_contours(
  sim_triangle_records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
  optional_deps.require_geometry_deps()
  if not sim_triangle_records:
    raise ValueError("sim_triangle_records must not be empty")

  contours: dict[str, dict[str, Any]] = {}
  for view, axes in SILHOUETTE_VIEW_AXES.items():
    projected_triangles: list[Any] = []
    for record in sim_triangle_records:
      triangle = [
        (float(point[axes[0]]), float(point[axes[1]]))
        for point in record["points_m"]
      ]
      polygon = optional_deps.ShapelyPolygon(triangle)
      if not polygon.is_valid or polygon.area <= 1.0e-10:
        continue
      projected_triangles.append(polygon)

    if not projected_triangles:
      points = [
        (float(point[axes[0]]), float(point[axes[1]]))
        for record in sim_triangle_records
        for point in record["points_m"]
      ]
      ring = convex_hull_2d(points)
      contours[view] = {
        "points_m": ring,
        "polygons_m": [ring],
        "status": "convex_hull",
        "source_triangle_count": len(sim_triangle_records),
        "polygon_count": 1 if ring else 0,
        "contour_point_count": len(ring),
      }
      continue

    unioned = optional_deps.shapely_unary_union(projected_triangles)
    geometries = (
      list(unioned.geoms) if hasattr(unioned, "geoms") else [unioned]
    )
    polygons = [
      geometry
      for geometry in geometries
      if not geometry.is_empty and getattr(geometry, "area", 0.0) > 1.0e-9
    ]
    if not polygons:
      points = [
        (float(point[axes[0]]), float(point[axes[1]]))
        for record in sim_triangle_records
        for point in record["points_m"]
      ]
      ring = convex_hull_2d(points)
      contours[view] = {
        "points_m": ring,
        "polygons_m": [ring],
        "status": "convex_hull",
        "source_triangle_count": len(sim_triangle_records),
        "polygon_count": 1 if ring else 0,
        "contour_point_count": len(ring),
      }
      continue

    rings: list[list[list[float]]] = []
    for polygon in sorted(polygons, key=lambda item: item.area, reverse=True):
      exterior = list(polygon.exterior.coords)
      if len(exterior) > 1 and exterior[0] == exterior[-1]:
        exterior = exterior[:-1]
      rings.append([[float(x), float(y)] for x, y in exterior])

    contours[view] = {
      "points_m": rings[0],
      "polygons_m": rings,
      "status": "projected_mesh_triangle_union",
      "source_triangle_count": len(sim_triangle_records),
      "polygon_count": len(rings),
      "contour_point_count": sum(len(ring) for ring in rings),
    }
  return contours
