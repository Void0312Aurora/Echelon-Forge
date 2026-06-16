"""HTML and SVG review-view writers for airframe geometry reports."""

from __future__ import annotations

import html
import json
import math
import shutil
from pathlib import Path
from typing import Any, Iterable

from tools.geometry.airframe_review import contours, projection_geometry
from tools.geometry.airframe_review.constants import CROSS_REGION_REVIEW_SEMANTICS


def _svg_color(index: int) -> str:
  palette = [
    "#2f6f9f",
    "#b24d3e",
    "#4f8a4b",
    "#8a5a9f",
    "#b27a2f",
    "#2f827d",
    "#6f6f6f",
  ]
  return palette[index % len(palette)]


def _svg_project_point(
  *,
  point: tuple[float, float],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
) -> tuple[float, float]:
  value_x, value_y = point
  view_min_x, view_min_y, view_max_x, view_max_y = view_bounds
  span_x = view_max_x - view_min_x
  span_y = view_max_y - view_min_y
  x = ((value_x - view_min_x) / span_x) * width
  y = height - ((value_y - view_min_y) / span_y) * height
  return x, y


def _svg_rect(
  *,
  bounds: tuple[float, float, float, float],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.18,
  stroke_width: float = 1.2,
  stroke_dasharray: str = "",
  label_visible: bool = True,
) -> str:
  min_x, min_y, max_x, max_y = bounds
  x, y = _svg_project_point(
    point=(min_x, max_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  max_screen_x, min_screen_y = _svg_project_point(
    point=(max_x, min_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  rect_width = max(max_screen_x - x, 1.0)
  rect_height = max(min_screen_y - y, 1.0)
  text_x = x + 4.0
  text_y = y + 13.0
  dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
  escaped_label = html.escape(label)
  text = ""
  if label_visible:
    text = (
      f'\n<text x="{text_x:.2f}" y="{text_y:.2f}" font-size="10" '
      f'font-family="monospace" fill="{color}">{escaped_label}</text>'
    )
  fill_attr = (
    'fill="none"'
    if fill_opacity <= 0.0
    else f'fill="{color}" fill-opacity="{fill_opacity:.2f}"'
  )
  return (
    f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
    f'height="{rect_height:.2f}" {fill_attr} '
    f'stroke="{color}" stroke-width="{stroke_width:.2f}"{dash_attr}>'
    f'<title>{escaped_label}</title></rect>'
    f'{text}'
  )


def _svg_point(
  *,
  point: list[float],
  axes: tuple[int, int],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  index: int,
) -> str:
  screen_x, screen_y = _svg_project_point(
    point=(point[axes[0]], point[axes[1]]),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  escaped_label = html.escape(label)
  return (
    f'<circle cx="{screen_x:.2f}" cy="{screen_y:.2f}" r="4.5" fill="{color}" '
    f'stroke="#ffffff" stroke-width="1.2"><title>{escaped_label}</title></circle>\n'
    f'<text x="{screen_x + 6.0:.2f}" y="{screen_y - 6.0:.2f}" font-size="10" '
    f'font-family="monospace" fill="{color}">{index}</text>'
  )


def _svg_polygon(
  *,
  points: list[list[float]],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.22,
  stroke_width: float = 1.5,
  label_visible: bool = True,
) -> str:
  if len(points) < 3:
    return ""
  screen_points = [
    _svg_project_point(
      point=(point[0], point[1]),
      view_bounds=view_bounds,
      width=width,
      height=height,
    )
    for point in points
  ]
  point_text = " ".join(f"{point[0]:.2f},{point[1]:.2f}" for point in screen_points)
  centroid_x = sum(point[0] for point in screen_points) / len(screen_points)
  centroid_y = sum(point[1] for point in screen_points) / len(screen_points)
  escaped_label = html.escape(label)
  fill_attr = (
    'fill="none"'
    if fill_opacity <= 0.0
    else f'fill="{color}" fill-opacity="{fill_opacity:.2f}"'
  )
  polygon = (
    f'<polygon points="{point_text}" {fill_attr} '
    f'stroke="{color}" stroke-width="{stroke_width:.2f}">'
    f'<title>{escaped_label}</title></polygon>'
  )
  if not label_visible:
    return polygon
  return (
    polygon
    + "\n"
    f'<text x="{centroid_x + 4.0:.2f}" y="{centroid_y + 4.0:.2f}" '
    f'font-size="10" font-family="monospace" fill="{color}">{escaped_label}</text>'
  )


def _svg_polygon_projected(
  *,
  points: list[list[float]],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.24,
  stroke_width: float = 1.5,
  label_visible: bool = True,
) -> str:
  return _svg_polygon(
    points=points,
    view_bounds=view_bounds,
    width=width,
    height=height,
    color=color,
    label=label,
    fill_opacity=fill_opacity,
    stroke_width=stroke_width,
    label_visible=label_visible,
  )


def _legacy_hitbox_rows(component_report: dict[str, Any] | None) -> list[dict[str, Any]]:
  if component_report is None:
    return []
  rows: dict[int, dict[str, Any]] = {}
  for row in component_report["rows"]:
    rows.setdefault(
      int(row["hitbox_index"]),
      {
        "hitbox_index": int(row["hitbox_index"]),
        "bounds": row["parent_hitbox_bounds"],
      },
    )
  return [rows[index] for index in sorted(rows)]


def _svg_for_view(
  mapping: dict[str, Any],
  view: str,
  *,
  component_report: dict[str, Any] | None = None,
  diagnostics: dict[str, Any] | None = None,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x forward (m)", "y lateral (m)"),
    "side": (0, 2, "x forward (m)", "z up (m)"),
    "front": (1, 2, "y lateral (m)", "z up (m)"),
  }
  axis_x, axis_y, label_x, label_y = axes_by_view[view]
  width, height = 1200, 760
  envelope = mapping["outer_envelope"]["bounds"]
  view_bounds_raw = projection_geometry.project_bounds(envelope, (axis_x, axis_y))
  margin_x = max((view_bounds_raw[2] - view_bounds_raw[0]) * 0.08, 0.5)
  margin_y = max((view_bounds_raw[3] - view_bounds_raw[1]) * 0.08, 0.5)
  view_bounds = (
    view_bounds_raw[0] - margin_x,
    view_bounds_raw[1] - margin_y,
    view_bounds_raw[2] + margin_x,
    view_bounds_raw[3] + margin_y,
  )
  elements = [
    '<rect x="0" y="0" width="1200" height="760" fill="#ffffff"/>',
    f'<text x="24" y="34" font-size="18" font-family="monospace" fill="#202020">'
    f'F-16 outer-region candidate {view} view</text>',
    f'<text x="24" y="58" font-size="12" font-family="monospace" fill="#555555">'
    f'{label_x}; {label_y}; review-only boxes, component overlays, and review points</text>',
    _svg_rect(
      bounds=view_bounds_raw,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#111111",
      label="outer_envelope",
      fill_opacity=0.03,
      stroke_width=1.5,
    ),
  ]
  for legacy in _legacy_hitbox_rows(component_report):
    elements.append(
      _svg_rect(
        bounds=projection_geometry.project_bounds(legacy["bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#c47a00",
        label=f'legacy_hitbox_{legacy["hitbox_index"]}',
        fill_opacity=0.02,
        stroke_width=1.2,
        stroke_dasharray="5 4",
        label_visible=False,
      )
    )
  for index, region in enumerate(mapping["outer_regions"]):
    elements.append(
      _svg_rect(
        bounds=projection_geometry.project_bounds(region["bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=_svg_color(index),
        label=region["id"],
      )
    )
  if component_report is not None:
    for row in component_report["rows"]:
      color = "#9b1c31" if row["review_status"] == "needs_review" else "#5b3f93"
      elements.append(
        _svg_rect(
          bounds=projection_geometry.project_bounds(row["component_bounds"], (axis_x, axis_y)),
          view_bounds=view_bounds,
          width=width,
          height=height,
          color=color,
          label=f'{row["component_name"]} -> {row["bound_region_id"]}',
          fill_opacity=0.05,
          stroke_width=0.9,
          label_visible=False,
        )
      )
  if diagnostics is not None:
    for row in diagnostics["rows"]:
      elements.append(
        _svg_point(
          point=row["point_m"],
          axes=(axis_x, axis_y),
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#0f172a",
          label=f'{row["point_index"]}: {row["point_id"]}',
          index=int(row["point_index"]),
        )
      )
  elements.extend(
    [
      '<text x="24" y="716" font-size="11" font-family="monospace" fill="#555555">'
      'Legend: black envelope, colored outer regions, orange dashed legacy boxes, '
      'purple/red component boxes, numbered review points</text>',
      '<text x="24" y="736" font-size="11" font-family="monospace" fill="#555555">'
      'Review-only geometry; not a runtime collision mesh or real F-16 engineering model</text>',
    ]
  )
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
    'viewBox="0 0 1200 760">\n'
    + "\n".join(elements)
    + "\n</svg>\n"
  )


def write_svg_views(
  mapping: dict[str, Any],
  output_dir: Path,
  *,
  component_report: dict[str, Any] | None = None,
  diagnostics: dict[str, Any] | None = None,
) -> list[Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths: list[Path] = []
  for view in ("top", "side", "front"):
    path = output_dir / f"{view}.svg"
    path.write_text(
      _svg_for_view(
        mapping,
        view,
        component_report=component_report,
        diagnostics=diagnostics,
      ),
      encoding="utf-8",
    )
    paths.append(path)
  return paths


def _svg_for_fine_proxy_view(fine_proxy: dict[str, Any], view: str) -> str:
  axes_by_view = {
    "top": (0, 1, "x forward (m)", "y lateral (m)"),
    "side": (0, 2, "x forward (m)", "z up (m)"),
    "front": (1, 2, "y lateral (m)", "z up (m)"),
  }
  axis_x, axis_y, label_x, label_y = axes_by_view[view]
  width, height = 1200, 760
  envelope = fine_proxy["outer_envelope"]["bounds"]
  view_bounds_raw = projection_geometry.project_bounds(envelope, (axis_x, axis_y))
  margin_x = max((view_bounds_raw[2] - view_bounds_raw[0]) * 0.08, 0.5)
  margin_y = max((view_bounds_raw[3] - view_bounds_raw[1]) * 0.14, 0.75)
  view_bounds = (
    view_bounds_raw[0] - margin_x,
    view_bounds_raw[1] - margin_y,
    view_bounds_raw[2] + margin_x,
    view_bounds_raw[3] + margin_y,
  )
  elements = [
    '<rect x="0" y="0" width="1200" height="760" fill="#ffffff"/>',
    f'<text x="24" y="34" font-size="18" font-family="monospace" fill="#202020">'
    f'F-16 mesh-derived fine geometry proxy candidate {view} view</text>',
    f'<text x="24" y="58" font-size="12" font-family="monospace" fill="#555555">'
    f'{label_x}; {label_y}; dashed source AABB, dotted support bounds, solid mesh-derived silhouette</text>',
    _svg_rect(
      bounds=view_bounds_raw,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#111111",
      label="outer_envelope",
      fill_opacity=0.0,
      stroke_width=1.5,
      label_visible=False,
    ),
  ]
  for index, proxy in enumerate(fine_proxy["proxies"]):
    color = _svg_color(index)
    elements.append(
      _svg_rect(
        bounds=projection_geometry.project_bounds(proxy["source_region_bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=color,
        label=f'{proxy["source_region_id"]} source_aabb',
        fill_opacity=0.0,
        stroke_width=0.9,
        stroke_dasharray="6 4",
        label_visible=False,
      )
    )
    elements.append(
      _svg_rect(
        bounds=projection_geometry.project_bounds(proxy["support_bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=color,
        label=f'{proxy["source_region_id"]} support_bounds',
        fill_opacity=0.0,
        stroke_width=0.9,
        stroke_dasharray="2 3",
        label_visible=False,
      )
    )
    hull = proxy.get("mesh_derived_review_geometry", {}).get("hulls", {}).get(view, {})
    hull_points = hull.get("points_m", [])
    if len(hull_points) >= 3:
      elements.append(
        _svg_polygon(
          points=hull_points,
          view_bounds=view_bounds,
          width=width,
          height=height,
          color=color,
          label=f'{proxy["source_region_id"]} {proxy["proxy_kind"]} mesh_silhouette',
          label_visible=False,
        )
      )
    else:
      elements.append(
        _svg_rect(
          bounds=projection_geometry.project_bounds(proxy["support_bounds"], (axis_x, axis_y)),
          view_bounds=view_bounds,
          width=width,
          height=height,
          color=color,
          label=f'{proxy["source_region_id"]} {proxy["proxy_kind"]} support_bounds_no_mesh_silhouette',
          fill_opacity=0.15,
          stroke_width=1.4,
        )
      )
  for index, row in enumerate(fine_proxy["review_point_distance_deltas"], start=1):
    elements.append(
      _svg_point(
        point=row["point_m"],
        axes=(axis_x, axis_y),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#0f172a",
        label=f'{index}: {row["point_id"]}',
        index=index,
      )
    )
  elements.extend(
    [
      '<text x="24" y="716" font-size="11" font-family="monospace" fill="#555555">'
      'Legend: dashed boxes are TG-P2 source AABBs; dotted boxes are support bounds; solid polygons are mesh-derived silhouettes</text>',
      '<text x="24" y="736" font-size="11" font-family="monospace" fill="#555555">'
      'Review-only fine proxy candidates; not a runtime collision mesh or real F-16 engineering model</text>',
    ]
  )
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
    'viewBox="0 0 1200 760">\n'
    + "\n".join(elements)
    + "\n</svg>\n"
  )


def write_fine_proxy_svg_views(
  fine_proxy: dict[str, Any],
  output_dir: Path,
) -> list[Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths: list[Path] = []
  for view in ("top", "side", "front"):
    path = output_dir / f"fine_proxy_{view}.svg"
    path.write_text(_svg_for_fine_proxy_view(fine_proxy, view), encoding="utf-8")
    paths.append(path)
  return paths


def _projected_shape_polygon(
  geometry: dict[str, Any],
  axes: tuple[int, int],
) -> list[list[float]]:
  """Project a receiver geometry into ``axes`` as a 2D polygon outline.

  AABB/OBB -> 4-corner rectangle. Ellipsoid/capsule/cylinder -> a dense
  perimeter ring (reuses the containment sampler and dedupes for SVG).
  """
  bounds = geometry["bounds"]
  shape = geometry.get("shape", "obb")
  axis = geometry.get("axis", "")
  samples = projection_geometry.shape_projected_containment_samples(
    bounds,
    axes=axes,
    shape=shape,
    axis=axis,
    geometry=geometry,
  )
  if not samples:
    projected = projection_geometry.project_bounds(bounds, axes)
    min_x, min_y, max_x, max_y = projected
    return [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]
  return contours.convex_hull_2d(samples)


def _svg_for_whole_airframe_contour_view(
  report: dict[str, Any],
  view: str,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x forward (m)", "y lateral (m)"),
    "side": (0, 2, "x forward (m)", "z up (m)"),
    "front": (1, 2, "y lateral (m)", "z up (m)"),
  }
  axis_x, axis_y, label_x, label_y = axes_by_view[view]
  width, height = 1200, 760
  contours = report.get("contours", {})
  contour_record = contours.get(view, {})
  contour_points = contour_record.get("points_m", [])
  contour_polygons = contour_record.get("polygons_m") or (
    [contour_points] if contour_points else []
  )
  rows = report["rows"]
  # View bounds from the contour ring (fall back to envelope of all geometry).
  candidate_bounds: list[tuple[float, float, float, float]] = []
  for polygon in contour_polygons:
    if len(polygon) >= 3:
      bounds = projection_geometry.projected_hull_bounds(polygon)
      if bounds is not None:
        candidate_bounds.append(bounds)
  for row in rows:
    candidate_bounds.append(
      projection_geometry.project_bounds(row["current_geometry"]["bounds"], (axis_x, axis_y))
    )
  view_bounds_raw = (
    (
      min(b[0] for b in candidate_bounds),
      min(b[1] for b in candidate_bounds),
      max(b[2] for b in candidate_bounds),
      max(b[3] for b in candidate_bounds),
    )
    if candidate_bounds
    else (-8.0, -6.0, 8.0, 6.0)
  )
  margin_x = max((view_bounds_raw[2] - view_bounds_raw[0]) * 0.08, 0.5)
  margin_y = max((view_bounds_raw[3] - view_bounds_raw[1]) * 0.08, 0.5)
  view_bounds = (
    view_bounds_raw[0] - margin_x,
    view_bounds_raw[1] - margin_y,
    view_bounds_raw[2] + margin_x,
    view_bounds_raw[3] + margin_y,
  )
  tolerance = report["tolerance_m"]
  contour_meta = report["summary"]["contours"].get(view, {})
  elements: list[str] = [
    '<rect x="0" y="0" width="1200" height="760" fill="#ffffff"/>',
    f'<text x="24" y="34" font-size="18" font-family="monospace" fill="#202020">'
    f'F-16 projected audit-mesh contour - {view} view</text>',
    f'<text x="24" y="58" font-size="12" font-family="monospace" fill="#555555">'
    f'{label_x}; {label_y}; method={report["contour_method"]}; '
    f'triangles={contour_meta.get("source_triangle_count", 0)}; '
    f'polygons={contour_meta.get("polygon_count", 0)}; '
    f'tolerance={tolerance:g}m; review-only</text>',
  ]
  # Gray whole-airframe mesh projection silhouette.
  for index, polygon in enumerate(contour_polygons):
    if len(polygon) < 3:
      continue
    elements.append(
      _svg_polygon_projected(
        points=polygon,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#94a3b8",
        label=f"whole_airframe_projected_mesh_contour_{index}",
        fill_opacity=0.10,
        stroke_width=1.2,
        label_visible=False,
      )
    )
  # Components: green = inside contour within tolerance, red = exceeds
  # tolerance. The exceeding component is drawn in solid red with a
  # protrusion-distance label so a reviewer can see at a glance which
  # receiver sticks out and by how much.
  for row in rows:
    geometry = row["current_geometry"]
    polygon = _projected_shape_polygon(geometry, (axis_x, axis_y))
    if len(polygon) < 3:
      continue
    max_outside = row["max_outside_distance_m"]
    exceeds = row["exceeds_tolerance"]
    base_color = "#dc2626" if exceeds else "#16a34a"
    base_opacity = 0.32 if exceeds else 0.12
    base_stroke = 2.0 if exceeds else 1.0
    label = (
      f'{row["component_name"]} protrusion {max_outside:g}m'
      if exceeds
      else row["component_name"]
    )
    elements.append(
      _svg_polygon_projected(
        points=polygon,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=base_color,
        label=label,
        fill_opacity=base_opacity,
        stroke_width=base_stroke,
        label_visible=exceeds,
      )
    )
  legend_y = 716
  elements.extend(
    [
      f'<text x="24" y="{legend_y}" font-size="11" font-family="monospace" fill="#555555">'
      f'Legend: gray=projected audit-mesh silhouette; '
      f'green=receiver inside contour; red=receiver exceeds {tolerance:g}m tolerance; '
      f'red fill=protruding portion</text>',
      f'<text x="24" y="{legend_y + 20}" font-size="11" font-family="monospace" fill="#555555">'
      'Review-only diagnostic; not a runtime collision mesh, not real F-16 engineering geometry</text>',
    ]
  )
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
    'viewBox="0 0 1200 760">\n'
    + "\n".join(elements)
    + "\n</svg>\n"
  )


def write_whole_airframe_contour_svg_views(
  report: dict[str, Any],
  output_dir: Path,
) -> list[Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths: list[Path] = []
  for view in ("top", "side", "front"):
    path = output_dir / f"whole_airframe_contour_{view}.svg"
    path.write_text(
      _svg_for_whole_airframe_contour_view(report, view), encoding="utf-8"
    )
    paths.append(path)
  return paths


def write_whole_airframe_contour_dashboard(
  report: dict[str, Any],
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "whole_airframe_contour_dashboard.html"
  tolerance = report["tolerance_m"]
  exceeders = [row for row in report["rows"] if row["exceeds_tolerance"]]
  table_rows = "\n".join(
    "<tr>"
    f"<td>{html.escape(row['item_id'])}</td>"
    f"<td>{html.escape(row['record_type'])}</td>"
    f"<td>{html.escape(row['prior_shape'])}</td>"
    f"<td>{';'.join(html.escape(r) for r in row['outside_views']) or '-'}</td>"
    f"<td>{row['outside_sample_count']}</td>"
    f"<td>{row['max_outside_distance_m']:g}</td>"
    f"<td>{'YES' if row['exceeds_tolerance'] else 'no'}</td>"
    "</tr>"
    for row in report["rows"]
  )
  svg_blocks = "\n".join(
    f'<section><h2>{view} view</h2>'
    f'<img src="whole_airframe_contour_{view}.svg" '
    f'style="width:100%;max-width:1200px;border:1px solid #ccc"/></section>'
    for view in ("top", "side", "front")
  )
  triangle_count = max(
    (meta.get("source_triangle_count", 0) for meta in report["summary"]["contours"].values()),
    default=0,
  )
  method_label = (
    "projected audit glTF triangle union"
    if report["contour_method"] == "projected_mesh_triangle_union"
    else report["contour_method"]
  )
  body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>F-16 Whole-Airframe Projected Mesh Contour Containment</title>
<style>
body {{ font-family: monospace; margin: 24px; color: #202020; }}
h1 {{ font-size: 20px; }}
h2 {{ font-size: 16px; margin-top: 28px; }}
table {{ border-collapse: collapse; margin-top: 12px; width: 100%; }}
th, td {{ border: 1px solid #999; padding: 4px 8px; font-size: 12px; text-align: left; }}
th {{ background: #eee; }}
tr.exceeds {{ background: #fee2e2; }}
section {{ margin-top: 20px; }}
.note {{ color: #666; font-size: 12px; }}
</style>
</head>
<body>
<h1>F-16 Whole-Airframe Projected Mesh Contour Containment</h1>
<p class="note">
Method: {method_label} ({triangle_count} audit triangles per view).
Tolerance: {tolerance:g} m (engineering review margin, not physical clearance).
Items exceeding tolerance: <strong>{len(exceeders)}</strong> of {report['summary']['item_count']}.
Max outside distance: <strong>{report['summary']['max_outside_distance_m']:g} m</strong>.
</p>
<table>
<thead><tr><th>item_id</th><th>type</th><th>shape</th><th>outside views</th><th>outside samples</th><th>max outside (m)</th><th>exceeds</th></tr></thead>
<tbody>
{table_rows}
</tbody>
</table>
{svg_blocks}
<p class="note">Review-only diagnostic. The gray outline is a projected audit-mesh silhouette, not a runtime collision mesh, not real F-16 engineering geometry, not a weapon Pk authority.</p>
</body>
</html>
"""
  output_path.write_text(body, encoding="utf-8")
  return output_path


def _component_rows_for_region(
  component_report: dict[str, Any],
  region_id: str,
) -> list[dict[str, Any]]:
  return [
    row for row in component_report["rows"] if row["bound_region_id"] == region_id
  ]


def _fine_proxy_review_flags(
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
) -> list[str]:
  geometry = proxy["mesh_derived_review_geometry"]
  hull_counts = [
    view["point_count"] for view in geometry.get("hulls", {}).values()
  ]
  flags: list[str] = []
  if geometry.get("status") == "insufficient_region_vertices_for_closed_silhouette":
    flags.append("insufficient_mesh_silhouette")
  if hull_counts and min(hull_counts) <= 4:
    flags.append("low_hull_point_count")
  if any(row["review_status"] == "needs_review" for row in component_rows):
    flags.append("component_binding_needs_review")
  if "wing" in proxy["source_region_id"] or "tail" in proxy["source_region_id"]:
    flags.append("surface_sign_or_thickness_review")
  if not flags:
    flags.append("candidate_accept_visual_check")
  return flags


def _fine_proxy_review_status(flags: list[str]) -> str:
  if "insufficient_mesh_silhouette" in flags:
    return "hold_for_human_review"
  if "component_binding_needs_review" in flags or "low_hull_point_count" in flags:
    return "needs_human_review"
  return "candidate_accept_after_visual_check"


def _projected_view_bounds_for_proxy(
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  axes: tuple[int, int],
  extra_points: list[list[float]] | None = None,
) -> tuple[float, float, float, float]:
  projected: list[tuple[float, float, float, float]] = [
    projection_geometry.project_bounds(proxy["source_region_bounds"], axes),
    projection_geometry.project_bounds(proxy["support_bounds"], axes),
  ]
  geometry = proxy["mesh_derived_review_geometry"]
  if "selection_bounds" in geometry:
    projected.append(projection_geometry.project_bounds(geometry["selection_bounds"], axes))
  for row in component_rows:
    projected.append(projection_geometry.project_bounds(row["component_bounds"], axes))
  for view_record in geometry.get("hulls", {}).values():
    points = view_record.get("points_m", [])
    if points:
      projected.append(
        (
          min(point[0] for point in points),
          min(point[1] for point in points),
          max(point[0] for point in points),
          max(point[1] for point in points),
        )
      )
  for point in extra_points or []:
    projected.append((point[axes[0]], point[axes[1]], point[axes[0]], point[axes[1]]))
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.12,
    min_y - span_y * 0.12,
    max_x + span_x * 0.12,
    max_y + span_y * 0.12,
  )


def _fine_proxy_review_mini_svg(
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  view: str,
  review_points: list[dict[str, Any]] | None = None,
  component_labels_visible: bool = False,
  width: int = 420,
  height: int = 260,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  point_values = [row["point_m"] for row in review_points or []]
  view_bounds = _projected_view_bounds_for_proxy(
    proxy,
    component_rows,
    axes,
    extra_points=point_values,
  )
  geometry = proxy["mesh_derived_review_geometry"]
  color = "#2563eb"
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    f'<text x="12" y="20" font-size="13" font-family="monospace" fill="#111827">{view} ({view_label})</text>',
    _svg_rect(
      bounds=projection_geometry.project_bounds(proxy["source_region_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#f59e0b",
      label="source_region_bounds",
      fill_opacity=0.02,
      stroke_width=1.1,
      stroke_dasharray="6 4",
      label_visible=False,
    ),
    _svg_rect(
      bounds=projection_geometry.project_bounds(proxy["support_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#64748b",
      label="support_bounds",
      fill_opacity=0.02,
      stroke_width=1.1,
      stroke_dasharray="2 3",
      label_visible=False,
    ),
  ]
  for row in component_rows:
    component_color = "#be123c" if row["review_status"] == "needs_review" else "#7c3aed"
    elements.append(
      _svg_rect(
        bounds=projection_geometry.project_bounds(row["component_bounds"], axes),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=component_color,
        label=f'{row["component_name"]} {row["review_status"]}',
        fill_opacity=0.08,
        stroke_width=0.9,
        label_visible=component_labels_visible,
      )
    )
  hull_points = geometry.get("hulls", {}).get(view, {}).get("points_m", [])
  if len(hull_points) >= 3:
    elements.append(
      _svg_polygon_projected(
        points=hull_points,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=color,
        label="mesh_silhouette",
        fill_opacity=0.28,
        stroke_width=1.6,
      )
    )
  for index, row in enumerate(review_points or [], start=1):
    elements.append(
      _svg_point(
        point=row["point_m"],
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#0f172a",
        label=f'{row.get("point_id", "review_point")}',
        index=int(row.get("point_index", index)),
      )
    )
  elements.append(
    f'<text x="12" y="{height - 14}" font-size="10" font-family="monospace" fill="#475569">'
    'orange=source, gray=support, purple/red=components, blue=mesh, black=point</text>'
  )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _component_rows_by_name(
  component_report: dict[str, Any],
) -> dict[str, dict[str, Any]]:
  return {row["component_name"]: row for row in component_report["rows"]}


def _triage_mini_view_grid(
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  review_points: list[dict[str, Any]] | None = None,
) -> str:
  return (
    '<div class="mini-views">'
    + "".join(
      _fine_proxy_review_mini_svg(
        proxy,
        component_rows,
        view,
        review_points=review_points,
        component_labels_visible=True,
      )
      for view in ("top", "side", "front")
    )
    + "</div>"
  )


def _triage_list(items: Iterable[Any]) -> str:
  values = [str(item) for item in items if str(item)]
  if not values:
    return "<ul><li>none</li></ul>"
  return "<ul>" + "".join(f"<li>{html.escape(value)}</li>" for value in values) + "</ul>"


def _triage_card(
  *,
  title: str,
  subtitle: str,
  question: str,
  look_at: str,
  decision: str,
  details: list[str],
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  severity: str,
  review_points: list[dict[str, Any]] | None = None,
) -> str:
  return f"""
    <article class="triage-card {html.escape(severity)}">
      <div class="triage-head">
        <h3>{html.escape(title)}</h3>
        <span>{html.escape(subtitle)}</span>
      </div>
      <div class="decision-box">
        <div><strong>Review question</strong><p>{html.escape(question)}</p></div>
        <div><strong>Look at</strong><p>{html.escape(look_at)}</p></div>
        <div><strong>Decision needed</strong><p>{html.escape(decision)}</p></div>
      </div>
      {_triage_list(details)}
      {_triage_mini_view_grid(proxy, component_rows, review_points=review_points)}
    </article>
  """


def _review_slug(value: str) -> str:
  cleaned = [
    char.lower() if char.isalnum() else "-"
    for char in value.replace("_", "-")
  ]
  slug = "".join(cleaned).strip("-")
  while "--" in slug:
    slug = slug.replace("--", "-")
  return slug or "item"


def _relative_to(path: Path, parent: Path) -> str:
  return path.relative_to(parent).as_posix()


def _isolated_view_page(
  *,
  title: str,
  subtitle: str,
  question: str,
  look_at: str,
  decision: str,
  details: list[str],
  svg_filenames: dict[str, str],
  back_href: str,
  banner_html: str = "",
) -> str:
  banner_css = (
    """    .stale-banner {
      background: #fff7ed;
      border: 1px solid #fed7aa;
      border-left: 5px solid #ea580c;
      border-radius: 6px;
      color: #7c2d12;
      line-height: 1.4;
      margin-top: 14px;
      padding: 10px 12px;
    }
    .stale-banner a {
      color: #9a3412;
      font-weight: 700;
    }
"""
    if banner_html
    else ""
  )
  banner_section = f"{banner_html.rstrip()}\n" if banner_html else ""
  return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)} isolated geometry view</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 25px;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    .decision-box {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 10px;
      margin-top: 14px;
    }}
    .decision-box strong {{
      display: block;
      color: #0f172a;
      font-size: 12px;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .decision-box p {{
      color: #1f2937;
      font-size: 13px;
      line-height: 1.35;
      margin: 4px 0 0;
    }}
{banner_css}    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    .views {{
      display: grid;
      gap: 18px;
    }}
    figure {{
      margin: 0;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="{html.escape(back_href)}">Back to isolated review index</a></p>
    <h1>{html.escape(title)}</h1>
    <p class="subtitle">{html.escape(subtitle)}</p>
{banner_section}    <div class="decision-box">
      <div><strong>Review question</strong><p>{html.escape(question)}</p></div>
      <div><strong>Look at</strong><p>{html.escape(look_at)}</p></div>
      <div><strong>Decision needed</strong><p>{html.escape(decision)}</p></div>
    </div>
  </header>
  <section>
    <h2>Trace Details</h2>
    {_triage_list(details)}
  </section>
  <section class="views">
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(title)} {html.escape(view)} view"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def _write_isolated_review_entry(
  *,
  root_dir: Path,
  category: str,
  slug: str,
  title: str,
  subtitle: str,
  question: str,
  look_at: str,
  decision: str,
  details: list[str],
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  review_points: list[dict[str, Any]] | None = None,
  priority: str,
  banner_html: str = "",
) -> dict[str, Any]:
  category_dir = root_dir / category
  category_dir.mkdir(parents=True, exist_ok=True)
  safe_slug = _review_slug(slug)
  svg_filenames: dict[str, str] = {}
  for view in ("top", "side", "front"):
    svg_filename = f"{safe_slug}_{view}.svg"
    svg_path = category_dir / svg_filename
    svg_path.write_text(
      _fine_proxy_review_mini_svg(
        proxy,
        component_rows,
        view,
        review_points=review_points,
        component_labels_visible=True,
        width=960,
        height=620,
      ),
      encoding="utf-8",
    )
    svg_filenames[view] = svg_filename
  html_path = category_dir / f"{safe_slug}.html"
  html_path.write_text(
    "\n".join(
      line.rstrip()
      for line in _isolated_view_page(
        title=title,
        subtitle=subtitle,
        question=question,
        look_at=look_at,
        decision=decision,
        details=details,
        svg_filenames=svg_filenames,
        back_href="../index.html",
        banner_html=banner_html,
      ).splitlines()
    )
    + "\n",
    encoding="utf-8",
  )
  return {
    "category": category,
    "slug": safe_slug,
    "title": title,
    "subtitle": subtitle,
    "priority": priority,
    "html": _relative_to(html_path, root_dir),
    "svg": {
      view: _relative_to(category_dir / filename, root_dir)
      for view, filename in svg_filenames.items()
    },
    "details": details,
    "component_names": [row["component_name"] for row in component_rows],
    "review_point_ids": [row["point_id"] for row in review_points or []],
    "source_region_id": proxy["source_region_id"],
    "review_question": question,
    "decision_needed": decision,
  }


def _write_semantic_damage_geometry_index(
  root_dir: Path,
  entries: list[dict[str, Any]],
  semantic_report: dict[str, Any],
) -> Path:
  index_path = root_dir / "index.html"
  cards = "".join(
    f"""
    <article class="{html.escape(entry["priority"])}">
      <h2><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h2>
      <p>{html.escape(entry["subtitle"])}</p>
      <p>{html.escape(entry["decision_needed"])}</p>
    </article>
    """
    for entry in entries
  )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Semantic Damage Geometry Views</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      font-size: 18px;
    }}
    p {{
      color: #475569;
      line-height: 1.35;
      margin: 8px 0 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #2563eb;
      border-radius: 6px;
      padding: 12px;
      background: #f8fbff;
    }}
    article.warning {{
      border-left-color: #d97706;
      background: #fffdf7;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Semantic Damage Geometry Views</h1>
    <p>Each page isolates one semantic outer-shell volume, its mesh-proxy geometry, and the current direct or held receiver components. These pages are parse-ready candidates, not active runtime damage components.</p>
    <div class="summary">
      <div>semantic volumes: {semantic_report["summary"]["semantic_volume_component_count"]}</div>
      <div>runtime parse-ready candidates: {semantic_report["summary"]["runtime_parse_ready_component_count"]}</div>
      <div>runtime active components: {semantic_report["summary"]["runtime_active_component_count"]}</div>
      <div>cross-region held handoffs: {semantic_report["summary"]["cross_region_handoff_held_count"]}</div>
      <div><a href="../scene.html">overview packet</a></div>
      <div><a href="../fine_proxy_review_dashboard.html">region dashboard</a></div>
    </div>
  </header>
  <section>
    <div class="entry-grid">
      {cards}
    </div>
  </section>
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def write_semantic_damage_geometry_review_views(
  *,
  semantic_report: dict[str, Any],
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "semantic_damage_geometry_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = _component_rows_by_name(component_report)
  entries: list[dict[str, Any]] = []
  for row in semantic_report["rows"]:
    proxy = proxies_by_region[row["source_region_id"]]
    receiver_names = (
      row["direct_receiver_components"] + row["cross_region_receiver_components"]
    )
    component_rows = [
      rows_by_component[name] for name in receiver_names if name in rows_by_component
    ]
    has_cross_region_receivers = bool(row["cross_region_receiver_components"])
    entries.append(
      _write_isolated_review_entry(
        root_dir=root_dir,
        category="volumes",
        slug=row["semantic_component_id"],
        title=row["semantic_component_id"],
        subtitle=f'semantic volume -> {row["source_region_id"]}',
        question=(
          f'Can {row["semantic_component_id"]} be promoted from mesh-proxy candidate to an active damage component?'
        ),
        look_at=(
          "Compare the blue mesh silhouette/support volume with the linked receiver component boxes in all three views."
        ),
        decision=(
          "Keep cross-region receivers held or split them before runtime activation."
          if has_cross_region_receivers
          else "Candidate is parse-ready; activation still needs explicit damage-model review."
        ),
        details=[
          f'semantic component: {row["semantic_component_id"]}',
          f'surface component: {row["surface_component_id"]}',
          f'outer region: {row["source_region_id"]}',
          f'volume role: {row["volume_component_role"]}',
          f'geometry primitive: {row["geometry_primitive"]}',
          f'runtime system candidate: {row["runtime_system"]}',
          "direct receivers: "
          + (", ".join(row["direct_receiver_components"]) or "none"),
          "cross-region receivers: "
          + (", ".join(row["cross_region_receiver_components"]) or "none"),
          f'receiver handoff: {row["receiver_handoff_status"]}',
          f'runtime projection: {row["runtime_projection_status"]}',
          f'mesh region vertices: {row["mesh_region_vertex_count"]}',
          f'surface review semantics: {row["surface_review_semantics"]}',
        ],
        proxy=proxy,
        component_rows=component_rows,
        priority="warning" if has_cross_region_receivers else "info",
      )
    )

  index_path = _write_semantic_damage_geometry_index(
    root_dir,
    entries,
    semantic_report,
  )
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_semantic_damage_geometry_views.v1",
    "status": "semantic_damage_geometry_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "runtime_schema_parse_ready_candidate": True,
      "true_internal_component_geometry": False,
    },
    "summary": {
      "entry_count": len(entries),
      "semantic_volume_entry_count": len(entries),
      "cross_region_receiver_entry_count": sum(
        1
        for row in semantic_report["rows"]
        if row["cross_region_receiver_components"]
      ),
    },
    "index_html": "index.html",
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _projected_view_bounds_for_internal_prior(
  proxy: dict[str, Any],
  component_row: dict[str, Any],
  prior_row: dict[str, Any],
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  projected = [
    projection_geometry.project_bounds(proxy["source_region_bounds"], axes),
    projection_geometry.project_bounds(proxy["support_bounds"], axes),
    projection_geometry.project_bounds(component_row["component_bounds"], axes),
    projection_geometry.project_bounds(prior_row["constraint_bounds"], axes),
    projection_geometry.project_bounds(prior_row["constrained_geometry"]["bounds"], axes),
  ]
  geometry = proxy["mesh_derived_review_geometry"]
  for view_record in geometry.get("hulls", {}).values():
    points = view_record.get("points_m", [])
    if points:
      projected.append(
        (
          min(point[0] for point in points),
          min(point[1] for point in points),
          max(point[0] for point in points),
          max(point[1] for point in points),
        )
      )
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.12,
    min_y - span_y * 0.12,
    max_x + span_x * 0.12,
    max_y + span_y * 0.12,
  )


def _internal_prior_mini_svg(
  proxy: dict[str, Any],
  component_row: dict[str, Any],
  prior_row: dict[str, Any],
  view: str,
  *,
  width: int = 960,
  height: int = 620,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  view_bounds = _projected_view_bounds_for_internal_prior(
    proxy,
    component_row,
    prior_row,
    axes,
  )
  geometry = proxy["mesh_derived_review_geometry"]
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    f'<text x="12" y="20" font-size="13" font-family="monospace" fill="#111827">{view} ({view_label})</text>',
    _svg_rect(
      bounds=projection_geometry.project_bounds(proxy["support_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#f59e0b",
      label="parent_surface_support_bounds",
      fill_opacity=0.02,
      stroke_width=1.1,
      stroke_dasharray="6 4",
      label_visible=False,
    ),
    _svg_rect(
      bounds=projection_geometry.project_bounds(prior_row["constraint_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#64748b",
      label="shell_constraint_bounds",
      fill_opacity=0.02,
      stroke_width=1.2,
      stroke_dasharray="2 3",
      label_visible=True,
    ),
    _svg_rect(
      bounds=projection_geometry.project_bounds(component_row["component_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#7c3aed",
      label=f'{prior_row["component_name"]} old_aabb',
      fill_opacity=0.08,
      stroke_width=0.9,
      label_visible=True,
    ),
    _svg_rect(
      bounds=projection_geometry.project_bounds(prior_row["constrained_geometry"]["bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#0891b2",
      label=f'{prior_row["component_name"]} constrained_{prior_row["prior_shape"]}',
      fill_opacity=0.18,
      stroke_width=1.4,
      label_visible=True,
    ),
  ]
  hull_points = geometry.get("hulls", {}).get(view, {}).get("points_m", [])
  if len(hull_points) >= 3:
    elements.append(
      _svg_polygon_projected(
        points=hull_points,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#2563eb",
        label="mesh_silhouette",
        fill_opacity=0.24,
        stroke_width=1.4,
      )
    )
  elements.append(
    f'<text x="12" y="{height - 14}" font-size="10" font-family="monospace" fill="#475569">'
    'orange=parent support, gray=constraint, purple=old AABB, cyan=constrained prior, blue=mesh</text>'
  )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _write_internal_component_prior_index(
  root_dir: Path,
  entries: list[dict[str, Any]],
  prior_report: dict[str, Any],
) -> Path:
  index_path = root_dir / "index.html"
  cards = "".join(
    f"""
    <article class="{html.escape(entry["priority"])}">
      <h2><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h2>
      <p>{html.escape(entry["subtitle"])}</p>
      <p>{html.escape(entry["decision_needed"])}</p>
    </article>
    """
    for entry in entries
  )
  shape_counts = ", ".join(
    f"{shape}:{count}"
    for shape, count in prior_report["summary"]["shape_counts"].items()
  )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Internal Component Prior Views</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      font-size: 18px;
    }}
    p {{
      color: #475569;
      line-height: 1.35;
      margin: 8px 0 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #0891b2;
      border-radius: 6px;
      padding: 12px;
      background: #f7fdff;
    }}
    article.warning {{
      border-left-color: #d97706;
      background: #fffdf7;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Internal Component Prior Views</h1>
    <p>Each page isolates one current receiver component, its old AABB placement, and a constrained synthetic prior shape. These are review-only internal geometry priors, not true engineering structure.</p>
    <div class="summary">
      <div>component priors: {prior_report["summary"]["internal_component_prior_count"]}</div>
      <div>post-constraint outside: {prior_report["summary"]["post_constraint_outside_count"]}</div>
      <div>cross-region held priors: {prior_report["summary"]["cross_region_held_prior_count"]}</div>
      <div>shape counts: {html.escape(shape_counts)}</div>
      <div><a href="../scene.html">overview packet</a></div>
      <div><a href="../semantic_damage_geometry_views/index.html">semantic shell views</a></div>
    </div>
  </header>
  <section>
    <div class="entry-grid">
      {cards}
    </div>
  </section>
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def _internal_prior_view_page(
  *,
  row: dict[str, Any],
  svg_filenames: dict[str, str],
) -> str:
  return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(row["component_name"])} internal prior view</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    figure {{
      margin: 0 0 18px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="../index.html">Back to internal prior index</a></p>
    <h1>{html.escape(row["component_name"])}</h1>
    <p class="subtitle">{html.escape(row["prior_shape"])} prior -> {html.escape(row["bound_region_id"])}; constraint status {html.escape(row["constraint_status"])}</p>
  </header>
  <section>
    <h2>Trace Details</h2>
    {_triage_list([
      f'component: {row["component_name"]}',
      f'system: {row["system"]}',
      f'role: {row["component_role"]}',
      f'prior shape: {row["prior_shape"]} axis={row["prior_axis"] or "none"}',
      f'bound region: {row["bound_region_id"]}',
      "constraint regions: " + ", ".join(row["constraint_region_ids"]),
      f'constraint mode: {row["constraint_mode"]}',
      f'constraint status: {row["constraint_status"]}',
      f'old AABB containment: {row["original_aabb_containment_fraction"]}',
      "adjustment: " + json.dumps(row["constraint_adjustment"], sort_keys=True),
      f'component review semantics: {row["component_review_semantics"]}',
      f'rationale: {row["prior_rationale"]}',
      f'runtime projection: {row["runtime_projection_status"]}',
    ])}
  </section>
  <section>
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(row["component_name"])} {html.escape(view)} view"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def write_internal_component_prior_review_views(
  *,
  prior_report: dict[str, Any],
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "internal_component_prior_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  component_dir = root_dir / "components"
  component_dir.mkdir(parents=True, exist_ok=True)
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = _component_rows_by_name(component_report)
  entries: list[dict[str, Any]] = []
  for row in prior_report["rows"]:
    component_row = rows_by_component[row["component_name"]]
    proxy = proxies_by_region[row["bound_region_id"]]
    safe_slug = _review_slug(row["component_name"])
    svg_filenames: dict[str, str] = {}
    for view in ("top", "side", "front"):
      svg_filename = f"{safe_slug}_{view}.svg"
      svg_path = component_dir / svg_filename
      svg_path.write_text(
        _internal_prior_mini_svg(
          proxy,
          component_row,
          row,
          view,
        ),
        encoding="utf-8",
      )
      svg_filenames[view] = svg_filename
    html_path = component_dir / f"{safe_slug}.html"
    html_path.write_text(
      "\n".join(
        line.rstrip()
        for line in _internal_prior_view_page(
          row=row,
          svg_filenames=svg_filenames,
        ).splitlines()
      )
      + "\n",
      encoding="utf-8",
    )
    entries.append(
      {
        "category": "components",
        "slug": safe_slug,
        "title": row["component_name"],
        "subtitle": (
          f'{row["prior_shape"]} prior constrained by '
          f'{",".join(row["constraint_region_ids"])}'
        ),
        "priority": (
          "warning"
          if row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
          else "info"
        ),
        "html": _relative_to(html_path, root_dir),
        "svg": {
          view: _relative_to(component_dir / filename, root_dir)
          for view, filename in svg_filenames.items()
        },
        "component_name": row["component_name"],
        "prior_shape": row["prior_shape"],
        "constraint_status": row["constraint_status"],
        "decision_needed": (
          "Keep held until multi-region ownership is split or accepted."
          if row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
          else "Review constrained prior before replacing the old AABB receiver."
        ),
      }
    )

  index_path = _write_internal_component_prior_index(
    root_dir,
    entries,
    prior_report,
  )
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_internal_component_prior_views.v1",
    "status": "internal_component_prior_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
    },
    "summary": {
      "entry_count": len(entries),
      "component_prior_entry_count": len(entries),
      "cross_region_held_entry_count": sum(
        1 for row in prior_report["rows"]
        if row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
      ),
    },
    "index_html": "index.html",
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _projected_view_bounds_for_shape_placement(
  *,
  fine_proxy: dict[str, Any],
  row: dict[str, Any],
  view: str,
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  projected = [
    projection_geometry.project_bounds(row["latest_candidate_geometry"]["bounds"], axes),
  ]
  for proxy in fine_proxy["proxies"]:
    hull_points = (
      proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(hull_points) >= 3:
      hull_bounds = projection_geometry.projected_hull_bounds(hull_points)
      if hull_bounds is not None:
        projected.append(hull_bounds)
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.08,
    min_y - span_y * 0.08,
    max_x + span_x * 0.08,
    max_y + span_y * 0.08,
  )


def _projected_view_bounds_for_shape_placement_overview(
  *,
  fine_proxy: dict[str, Any],
  rows: list[dict[str, Any]],
  view: str,
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  projected = [
    projection_geometry.project_bounds(row["latest_candidate_geometry"]["bounds"], axes)
    for row in rows
  ]
  for proxy in fine_proxy["proxies"]:
    hull_points = (
      proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(hull_points) >= 3:
      hull_bounds = projection_geometry.projected_hull_bounds(hull_points)
      if hull_bounds is not None:
        projected.append(hull_bounds)
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.08,
    min_y - span_y * 0.08,
    max_x + span_x * 0.08,
    max_y + span_y * 0.08,
  )


def _svg_shape_label_badge(
  *,
  label: str,
  bounds: dict[str, list[float]],
  axes: tuple[int, int],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  offset_index: int,
) -> str:
  projected_bounds = projection_geometry.project_bounds(bounds, axes)
  min_x, min_y, max_x, max_y = projected_bounds
  screen_x, screen_y = _svg_project_point(
    point=((min_x + max_x) * 0.5, (min_y + max_y) * 0.5),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  offsets = [
    (0.0, 0.0),
    (12.0, -12.0),
    (-12.0, -12.0),
    (12.0, 12.0),
    (-12.0, 12.0),
  ]
  delta_x, delta_y = offsets[offset_index % len(offsets)]
  badge_x = min(max(screen_x + delta_x, 18.0), width - 18.0)
  badge_y = min(max(screen_y + delta_y, 34.0), height - 42.0)
  escaped_label = html.escape(label)
  return (
    f'<circle cx="{badge_x:.2f}" cy="{badge_y:.2f}" r="12" '
    f'fill="#ffffff" fill-opacity="0.92" stroke="#1e3a8a" '
    f'stroke-width="1.6"><title>{escaped_label}</title></circle>\n'
    f'<text x="{badge_x:.2f}" y="{badge_y + 4.2:.2f}" '
    f'text-anchor="middle" font-size="11" font-weight="700" '
    f'font-family="monospace" fill="#1e3a8a">{escaped_label}</text>'
  )


def _projected_view_bounds_for_latest_component_zoom(
  row: dict[str, Any],
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  min_x, min_y, max_x, max_y = projection_geometry.project_bounds(
    row["latest_candidate_geometry"]["bounds"],
    axes,
  )
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  component_span_x = max(max_x - min_x, 1.0e-6)
  component_span_y = max(max_y - min_y, 1.0e-6)
  span_x = max(component_span_x * 1.35, 0.08)
  span_y = max(component_span_y * 1.35, 0.08)
  return (
    center_x - span_x * 0.5,
    center_y - span_y * 0.5,
    center_x + span_x * 0.5,
    center_y + span_y * 0.5,
  )


def _fit_view_bounds_to_screen_aspect(
  bounds: tuple[float, float, float, float],
  *,
  width: int,
  height: int,
) -> tuple[float, float, float, float]:
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  span_x = max(max_x - min_x, 1.0e-6)
  span_y = max(max_y - min_y, 1.0e-6)
  target_aspect = width / max(height, 1)
  current_aspect = span_x / span_y
  if current_aspect < target_aspect:
    span_x = span_y * target_aspect
  else:
    span_y = span_x / target_aspect
  return (
    center_x - span_x * 0.5,
    center_y - span_y * 0.5,
    center_x + span_x * 0.5,
    center_y + span_y * 0.5,
  )


def _svg_scale_bar(
  *,
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
) -> str:
  span_x = max(view_bounds[2] - view_bounds[0], 1.0e-6)
  target = span_x * 0.24
  candidates = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
  scale_m = candidates[0]
  for candidate in candidates:
    if candidate <= target:
      scale_m = candidate
  pixel_length = max((scale_m / span_x) * width, 18.0)
  x0 = width - pixel_length - 16.0
  x1 = width - 16.0
  y = height - 18.0
  label = f"{scale_m:g} m"
  return (
    f'<line x1="{x0:.2f}" y1="{y:.2f}" x2="{x1:.2f}" y2="{y:.2f}" '
    f'stroke="#111827" stroke-width="2"/>\n'
    f'<line x1="{x0:.2f}" y1="{y - 4:.2f}" x2="{x0:.2f}" y2="{y + 4:.2f}" '
    f'stroke="#111827" stroke-width="2"/>\n'
    f'<line x1="{x1:.2f}" y1="{y - 4:.2f}" x2="{x1:.2f}" y2="{y + 4:.2f}" '
    f'stroke="#111827" stroke-width="2"/>\n'
    f'<text x="{(x0 + x1) * 0.5:.2f}" y="{y - 7:.2f}" '
    f'text-anchor="middle" font-size="10" font-family="monospace" '
    f'fill="#111827">{label}</text>'
  )


def _subcomponent_latest_overview_svg(
  *,
  fine_proxy: dict[str, Any],
  shape_report: dict[str, Any],
  view: str,
  width: int = 1500,
  height: int = 860,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  rows = shape_report["rows"]
  view_bounds = _projected_view_bounds_for_shape_placement_overview(
    fine_proxy=fine_proxy,
    rows=rows,
    view=view,
    axes=axes,
  )
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    (
      f'<text x="18" y="28" font-size="18" font-weight="700" '
      f'font-family="Arial, sans-serif" fill="#111827">'
      f'R20 latest subcomponent candidates / {view} ({view_label})</text>'
    ),
    (
      f'<text x="18" y="52" font-size="12" font-family="monospace" '
      f'fill="#475569">gray=whole-airframe wireframe; '
      f'blue=latest subcomponent candidate; numbers match the item list</text>'
    ),
  ]
  for proxy in fine_proxy["proxies"]:
    hull_points = (
      proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(hull_points) >= 3:
      elements.append(
        _svg_polygon_projected(
          points=hull_points,
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#94a3b8",
          label="whole_airframe_region",
          fill_opacity=0.0,
          stroke_width=1.0,
          label_visible=False,
        )
      )
  for index, row in enumerate(rows, start=1):
    child = {
      "prior_shape": row["candidate_evaluation_shape"],
      "constrained_geometry": row["latest_candidate_geometry"],
    }
    elements.append(
      _svg_projected_prior_shape(
        child=child,
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#2563eb",
        fill_opacity=0.28,
        stroke_width=2.4,
        stroke_color="#1e3a8a",
        label=f'{index}. {row["item_id"]}',
        label_visible=False,
      )
    )
  for index, row in enumerate(rows, start=1):
    elements.append(
      _svg_shape_label_badge(
        label=str(index),
        bounds=row["latest_candidate_geometry"]["bounds"],
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        offset_index=index,
      )
    )
  item_lines = [
    f'{index}. {row["item_id"]}'
    for index, row in enumerate(rows, start=1)
  ]
  line_height = 15
  start_y = height - 18 - line_height * len(item_lines)
  for index, item_line in enumerate(item_lines):
    elements.append(
      f'<text x="18" y="{start_y + index * line_height:.2f}" '
      f'font-size="11" font-family="monospace" fill="#334155">'
      f'{html.escape(item_line)}</text>'
    )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _subcomponent_latest_tile_elements(
  *,
  fine_proxy: dict[str, Any],
  row: dict[str, Any],
  view: str,
  width: int,
  height: int,
  label: str,
) -> list[str]:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  view_bounds = _projected_view_bounds_for_latest_component_zoom(
    row,
    axes,
  )
  view_bounds = _fit_view_bounds_to_screen_aspect(
    view_bounds,
    width=width,
    height=height,
  )
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" '
    f'fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>',
    (
      f'<text x="8" y="18" font-size="12" font-family="monospace" '
      f'fill="#334155">{html.escape(view)} local zoom ({view_label})</text>'
    ),
  ]
  latest_child = {
    "prior_shape": row["candidate_evaluation_shape"],
    "constrained_geometry": row["latest_candidate_geometry"],
  }
  component_shape = (
    _svg_projected_prior_shape(
      child=latest_child,
      axes=axes,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#2563eb",
      fill_opacity=0.72,
      stroke_width=4.0,
      stroke_color="#1e3a8a",
      label=f'{label}. {row["item_id"]}',
      label_visible=False,
    )
  )
  elements.append(component_shape)
  elements.append(
    _svg_scale_bar(
      view_bounds=view_bounds,
      width=width,
      height=height,
    )
  )
  return elements


def _subcomponent_latest_by_component_atlas_svg(
  *,
  fine_proxy: dict[str, Any],
  rows: list[dict[str, Any]],
  start_index: int,
  part_label: str,
  width: int = 1880,
  label_width: int = 430,
  tile_width: int = 460,
  tile_height: int = 250,
  header_height: int = 78,
  row_gap: int = 18,
  gutter: int = 12,
) -> str:
  row_height = tile_height + row_gap
  height = header_height + len(rows) * row_height + 26
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    (
      f'<text x="18" y="28" font-size="18" font-weight="700" '
      f'font-family="Arial, sans-serif" fill="#111827">'
      f'R20 latest subcomponents by component / {html.escape(part_label)}</text>'
    ),
    (
      f'<text x="18" y="52" font-size="12" font-family="monospace" '
      f'fill="#475569">one row = one latest subcomponent; '
      f'columns = top / side / front local zoom; '
      f'blue=that row latest candidate; each panel includes a meter scale bar; '
      f'airframe context is omitted here so the subcomponent body is visible</text>'
    ),
  ]
  for row_offset, row in enumerate(rows):
    item_index = start_index + row_offset
    row_y = header_height + row_offset * row_height
    elements.append(
      f'<rect x="12" y="{row_y - 8}" width="{width - 24}" '
      f'height="{tile_height + 12}" fill="#f8fafc" '
      f'stroke="#e2e8f0" stroke-width="1"/>'
    )
    label_y = row_y + 24
    elements.extend(
      [
        (
          f'<text x="22" y="{label_y}" font-size="15" font-weight="700" '
          f'font-family="monospace" fill="#111827">'
          f'{item_index}. {html.escape(row["item_id"])}</text>'
        ),
        (
          f'<text x="22" y="{label_y + 22}" font-size="11" '
          f'font-family="monospace" fill="#475569">'
          f'shape={html.escape(row["candidate_evaluation_shape"])}; '
          f'outside={row["latest_candidate_silhouette"]["outside_sample_count"]}</text>'
        ),
        (
          f'<text x="22" y="{label_y + 40}" font-size="11" '
          f'font-family="monospace" fill="#475569">'
          f'dims_m={html.escape(str(row["nominal_dimensions_m"]))}</text>'
        ),
        (
          f'<text x="22" y="{label_y + 58}" font-size="11" '
          f'font-family="monospace" fill="#475569">'
          f'center={html.escape(str(row["latest_candidate_geometry"]["center_m"]))}</text>'
        ),
        (
          f'<text x="22" y="{label_y + 76}" font-size="11" '
          f'font-family="monospace" fill="#475569">'
          f'{html.escape(row["latest_candidate_stage"])}</text>'
        ),
      ]
    )
    for view_index, view in enumerate(("top", "side", "front")):
      tile_x = label_width + view_index * (tile_width + gutter)
      tile_elements = _subcomponent_latest_tile_elements(
        fine_proxy=fine_proxy,
        row=row,
        view=view,
        width=tile_width,
        height=tile_height,
        label=str(item_index),
      )
      elements.append(
        f'<g transform="translate({tile_x},{row_y})">'
        + "\n".join(tile_elements)
        + "</g>"
      )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>\n"
  )


def _subcomponent_shape_placement_mini_svg(
  *,
  fine_proxy: dict[str, Any],
  row: dict[str, Any],
  view: str,
  width: int = 960,
  height: int = 620,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  view_bounds = _projected_view_bounds_for_shape_placement(
    fine_proxy=fine_proxy,
    row=row,
    view=view,
    axes=axes,
  )
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    (
      f'<text x="12" y="20" font-size="13" font-family="monospace" fill="#111827">'
      f'{html.escape(row["item_id"])} latest subcomponent candidate / {view} ({view_label})</text>'
    ),
  ]
  for proxy in fine_proxy["proxies"]:
    hull_points = (
      proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(hull_points) >= 3:
      elements.append(
        _svg_polygon_projected(
          points=hull_points,
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#94a3b8",
          label="whole_airframe_region",
          fill_opacity=0.0,
          stroke_width=1.0,
          label_visible=False,
        )
      )
  latest_child = {
    "prior_shape": row["candidate_evaluation_shape"],
    "constrained_geometry": row["latest_candidate_geometry"],
  }
  latest_color = "#2563eb"
  elements.append(
    _svg_projected_prior_shape(
      child=latest_child,
      axes=axes,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color=latest_color,
      fill_opacity=0.34,
      stroke_width=3.0,
      stroke_color="#1e3a8a",
      label=(
        f'{row["item_id"]} latest '
        f'{row["latest_candidate_stage"]}'
      ),
      label_visible=False,
    )
  )
  elements.append(
    f'<text x="12" y="{height - 28}" font-size="10" font-family="monospace" fill="#475569">'
    f'latest outside={row["latest_candidate_silhouette"]["outside_sample_count"]}; '
    f'latest stage={html.escape(row["latest_candidate_stage"])}; '
    f'total offset={row["latest_candidate_total_center_offset_m"]}</text>'
  )
  elements.append(
    f'<text x="12" y="{height - 12}" font-size="10" font-family="monospace" fill="#475569">'
    'gray=whole-airframe wireframe; blue=latest subcomponent candidate</text>'
  )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _write_subcomponent_shape_placement_index(
  root_dir: Path,
  entries: list[dict[str, Any]],
  shape_report: dict[str, Any],
  overview_triptych_svg: Path,
  latest_component_atlas_svgs: list[Path],
) -> Path:
  index_path = root_dir / "index.html"
  atlas_images = "\n".join(
    f'<img src="{html.escape(path.name)}" '
    f'alt="R20 latest subcomponent candidates by component {index}">'
    for index, path in enumerate(latest_component_atlas_svgs, start=1)
  )
  if atlas_images:
    atlas_note = (
      "Each row is one R20 latest subcomponent candidate, with top, side, "
      "and front local-zoom views shown separately. Historical current/shape/"
      "centerline layers are intentionally absent here."
    )
  else:
    atlas_note = (
      "R21 promotion leaves no remaining subcomponent shape-placement rows; "
      "top, side, and front overview views are retained as the audit trace."
    )
  cards = "".join(
    f"""
    <article class="{html.escape(entry["priority"])}">
      <h2><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h2>
      <p>{html.escape(entry["subtitle"])}</p>
      <p>{html.escape(entry["decision_needed"])}</p>
    </article>
    """
    for entry in entries
  )
  if not cards:
    cards = (
      '<p>No remaining subcomponent shape-placement candidates after '
      'R21 review-only rule promotion.</p>'
    )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Subcomponent Shape Placement Candidates</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    p {{
      color: #475569;
      line-height: 1.35;
      margin: 8px 0 0;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
      border: 1px solid #cbd5e1;
      margin-top: 12px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #d97706;
      border-radius: 6px;
      padding: 12px;
      background: #fffdf7;
    }}
    article.resolved {{
      border-left-color: #16a34a;
      background: #f8fff9;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Subcomponent Shape Placement Candidates</h1>
    <p>Review-only latest subcomponent candidates for items that previously exposed samples outside the whole-airframe top/side/front silhouettes. Nominal dimensions are preserved; older current/shape/centerline layers are retained only as trace data, and none are active runtime damage components.</p>
    <div class="summary">
      <div>shape candidates: {shape_report["summary"]["shape_placement_candidate_count"]}</div>
      <div>latest resolved candidates: {shape_report["summary"]["latest_candidate_resolves_exposure_count"]}</div>
      <div>latest unresolved candidates: {shape_report["summary"]["latest_candidate_unresolved_exposure_count"]}</div>
      <div>latest outside samples: {shape_report["summary"]["latest_candidate_total_outside_sample_count"]}</div>
      <div>latest total reduction: {shape_report["summary"]["latest_candidate_total_outside_sample_reduction"]}</div>
      <div>runtime active: {shape_report["summary"]["runtime_active_component_count"]}</div>
      <div><a href="../scene.html">overview packet</a></div>
    </div>
  </header>
  <section>
    <h2>Latest Candidate Atlas</h2>
    <p>{html.escape(atlas_note)}</p>
    {atlas_images}
  </section>
  <section>
    <div class="entry-grid">
      {cards}
    </div>
  </section>
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def _subcomponent_shape_placement_view_page(
  *,
  row: dict[str, Any],
  svg_filenames: dict[str, str],
) -> str:
  return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(row["item_id"])} shape placement candidate</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    figure {{
      margin: 0 0 18px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="../index.html">Back to shape placement index</a></p>
    <h1>{html.escape(row["item_id"])}</h1>
    <p class="subtitle">{html.escape(row["current_shape"])} -> {html.escape(row["candidate_shape_family"])}; {html.escape(row["shape_design_status"])}</p>
  </header>
  <section>
    <h2>Candidate Details</h2>
    {_triage_list([
      f'item: {row["item_id"]}',
      f'type: {row["record_type"]}',
      f'system: {row["system"]}',
      f'role: {row["component_role"]}',
      f'current shape: {row["current_shape"]} axis={row["current_axis"] or "none"}',
      f'candidate evaluation shape: {row["candidate_evaluation_shape"]} axis={row["candidate_evaluation_axis"] or "none"}',
      f'nominal dimensions m: {row["nominal_dimensions_m"]}',
      f'dimension policy: {row["dimension_policy"]}',
      f'placement policy: {row["placement_policy"]}',
      f'current outside samples: {row["current_silhouette"]["outside_sample_count"]}',
      f'candidate outside samples: {row["candidate_silhouette"]["outside_sample_count"]}',
      f'candidate center shift m: {row["candidate_center_shift_m"]}',
      f'centerline candidate offset m: {row["centerline_candidate_center_offset_m"]}',
      f'centerline candidate center m: {row["centerline_candidate_geometry"]["center_m"]}',
      f'centerline candidate outside samples: {row["centerline_candidate_silhouette"]["outside_sample_count"]}',
      f'centerline candidate status: {row["centerline_candidate_status"]}',
      f'centerline candidate action: {row["centerline_candidate_recommended_action"]}',
      f'latest candidate stage: {row["latest_candidate_stage"]}',
      f'latest candidate center m: {row["latest_candidate_geometry"]["center_m"]}',
      f'latest candidate outside samples: {row["latest_candidate_silhouette"]["outside_sample_count"]}',
      f'latest candidate status: {row["latest_candidate_status"]}',
      f'latest candidate action: {row["latest_candidate_recommended_action"]}',
      f'recommended action: {row["recommended_action"]}',
      f'rationale: {row["design_rationale"]}',
      f'centerline rationale: {row["centerline_candidate_rationale"]}',
      f'latest rationale: {row["latest_candidate_rationale"]}',
    ])}
  </section>
  <section>
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(row["item_id"])} {html.escape(view)} shape candidate"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def write_subcomponent_shape_placement_review_views(
  *,
  shape_report: dict[str, Any],
  fine_proxy: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "subcomponent_shape_placement_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  component_dir = root_dir / "components"
  component_dir.mkdir(parents=True, exist_ok=True)
  overview_svg_paths: dict[str, Path] = {}
  for view in ("top", "side", "front"):
    overview_svg_path = root_dir / f"overview_latest_{view}.svg"
    overview_svg_path.write_text(
      _subcomponent_latest_overview_svg(
        fine_proxy=fine_proxy,
        shape_report=shape_report,
        view=view,
      ),
      encoding="utf-8",
    )
    overview_svg_paths[view] = overview_svg_path
  overview_width = 1500
  overview_height = 860
  overview_triptych_path = root_dir / "overview_latest_triptych.svg"
  triptych_width = overview_width * 3
  triptych_parts = [
    f'<rect x="0" y="0" width="{triptych_width}" height="{overview_height}" fill="#ffffff"/>',
  ]
  for index, view in enumerate(("top", "side", "front")):
    svg_text = overview_svg_paths[view].read_text(encoding="utf-8")
    body_start = svg_text.find(">") + 1
    body_end = svg_text.rfind("</svg>")
    triptych_parts.append(
      f'<g transform="translate({index * overview_width},0)">'
      + svg_text[body_start:body_end]
      + "</g>"
    )
  overview_triptych_path.write_text(
    (
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{triptych_width}" '
      f'height="{overview_height}" viewBox="0 0 {triptych_width} {overview_height}">'
      + "\n".join(triptych_parts)
      + "</svg>\n"
    ),
    encoding="utf-8",
  )
  latest_component_atlas_paths: list[Path] = []
  atlas_part_size = 5
  for part_index, start in enumerate(
    range(0, len(shape_report["rows"]), atlas_part_size),
    start=1,
  ):
    part_rows = shape_report["rows"][start:start + atlas_part_size]
    atlas_path = root_dir / f"overview_latest_by_component_part{part_index}.svg"
    atlas_path.write_text(
      _subcomponent_latest_by_component_atlas_svg(
        fine_proxy=fine_proxy,
        rows=part_rows,
        start_index=start + 1,
        part_label=f"part {part_index}",
      ),
      encoding="utf-8",
    )
    latest_component_atlas_paths.append(atlas_path)
  entries: list[dict[str, Any]] = []
  for row in shape_report["rows"]:
    safe_slug = _review_slug(row["item_id"])
    svg_filenames: dict[str, str] = {}
    for view in ("top", "side", "front"):
      svg_filename = f"{safe_slug}_{view}.svg"
      svg_path = component_dir / svg_filename
      svg_path.write_text(
        _subcomponent_shape_placement_mini_svg(
          fine_proxy=fine_proxy,
          row=row,
          view=view,
        ),
        encoding="utf-8",
      )
      svg_filenames[view] = svg_filename
    html_path = component_dir / f"{safe_slug}.html"
    html_path.write_text(
      "\n".join(
        line.rstrip()
        for line in _subcomponent_shape_placement_view_page(
          row=row,
          svg_filenames=svg_filenames,
        ).splitlines()
      )
      + "\n",
      encoding="utf-8",
    )
    resolved = row["latest_candidate_silhouette"]["outside_sample_count"] == 0
    entries.append(
      {
        "category": "subcomponent_shape_candidates",
        "slug": safe_slug,
        "title": row["item_id"],
        "subtitle": (
          f'{row["latest_candidate_stage"]}; '
          f'latest outside {row["latest_candidate_silhouette"]["outside_sample_count"]}'
        ),
        "priority": "resolved" if resolved else "warning",
        "html": _relative_to(html_path, root_dir),
        "svg": {
          view: _relative_to(component_dir / filename, root_dir)
          for view, filename in svg_filenames.items()
        },
        "item_id": row["item_id"],
        "candidate_shape_family": row["candidate_shape_family"],
        "shape_design_status": row["shape_design_status"],
        "centerline_candidate_status": row["centerline_candidate_status"],
        "latest_candidate_status": row["latest_candidate_status"],
        "decision_needed": row["latest_candidate_recommended_action"],
      }
    )
  index_path = _write_subcomponent_shape_placement_index(
    root_dir,
    entries,
    shape_report,
    overview_triptych_path,
    latest_component_atlas_paths,
  )
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_subcomponent_shape_placement_views.v1",
    "status": "subcomponent_shape_placement_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
    },
    "summary": {
      "entry_count": len(entries),
      "overview_view_count": len(overview_svg_paths),
      "latest_component_atlas_entry_count": len(shape_report["rows"]),
      "latest_component_atlas_part_count": len(latest_component_atlas_paths),
      "resolved_entry_count": sum(
        1 for row in shape_report["rows"]
        if row["latest_candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "unresolved_entry_count": sum(
        1 for row in shape_report["rows"]
        if row["latest_candidate_silhouette"]["outside_sample_count"] > 0
      ),
      "shape_candidate_resolved_entry_count": sum(
        1 for row in shape_report["rows"]
        if row["candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "centerline_candidate_resolved_entry_count": sum(
        1 for row in shape_report["rows"]
        if row["centerline_candidate_silhouette"]["outside_sample_count"] == 0
      ),
    },
    "index_html": "index.html",
    "overview_svg": {
      view: _relative_to(path, root_dir)
      for view, path in overview_svg_paths.items()
    },
    "overview_triptych_svg": _relative_to(overview_triptych_path, root_dir),
    "latest_component_atlas_svg": [
      _relative_to(path, root_dir) for path in latest_component_atlas_paths
    ],
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _projected_view_bounds_for_parent_child_layout(
  proxy: dict[str, Any],
  row: dict[str, Any],
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  projected = [
    projection_geometry.project_bounds(proxy["source_region_bounds"], axes),
    projection_geometry.project_bounds(proxy["support_bounds"], axes),
    projection_geometry.project_bounds(row["source_region_bounds"], axes),
    projection_geometry.project_bounds(row["support_bounds"], axes),
    projection_geometry.project_bounds(row["whole_airframe_bounds"], axes),
  ]
  for child in row["child_receiver_priors"]:
    projected.append(
      projection_geometry.project_bounds(child["constrained_geometry"]["bounds"], axes)
    )
    for segment in child.get("held_segments", []):
      projected.append(projection_geometry.project_bounds(segment["geometry"]["bounds"], axes))
  for segment in row.get("cross_region_held_segment_overlays", []):
    projected.append(projection_geometry.project_bounds(segment["geometry"]["bounds"], axes))
  geometry = proxy["mesh_derived_review_geometry"]
  for view_record in geometry.get("hulls", {}).values():
    points = view_record.get("points_m", [])
    if points:
      projected.append(
        (
          min(point[0] for point in points),
          min(point[1] for point in points),
          max(point[0] for point in points),
          max(point[1] for point in points),
        )
      )
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.12,
    min_y - span_y * 0.12,
    max_x + span_x * 0.12,
    max_y + span_y * 0.12,
  )


def _svg_projected_prior_shape(
  *,
  child: dict[str, Any],
  axes: tuple[int, int],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.2,
  stroke_width: float = 1.5,
  stroke_color: str | None = None,
  projected_bounds: tuple[float, float, float, float] | None = None,
  label_visible: bool = True,
) -> str:
  bounds = projected_bounds or projection_geometry.project_bounds(
    child["constrained_geometry"]["bounds"],
    axes,
  )
  min_x, min_y, max_x, max_y = bounds
  x, y = _svg_project_point(
    point=(min_x, max_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  max_screen_x, min_screen_y = _svg_project_point(
    point=(max_x, min_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  rect_width = max(max_screen_x - x, 1.0)
  rect_height = max(min_screen_y - y, 1.0)
  center_x = x + rect_width * 0.5
  center_y = y + rect_height * 0.5
  escaped_label = html.escape(label)
  fill = f'fill="{color}" fill-opacity="{fill_opacity:.2f}"'
  stroke = stroke_color or color
  common = (
    f'{fill} stroke="{stroke}" stroke-width="{stroke_width:.2f}">'
    f'<title>{escaped_label}</title>'
  )
  shape = child["prior_shape"]
  if shape in {"sphere", "ellipsoid"}:
    body = (
      f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
      f'height="{rect_height:.2f}" '
      f'rx="{rect_width * 0.5:.2f}" ry="{rect_height * 0.5:.2f}" '
      f'{common}</rect>'
    )
  elif shape == "capsule":
    radius = min(rect_width, rect_height) * 0.5
    body = (
      f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
      f'height="{rect_height:.2f}" rx="{radius:.2f}" ry="{radius:.2f}" '
      f'{common}</rect>'
    )
  else:
    body = (
      f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
      f'height="{rect_height:.2f}" {common}</rect>'
    )
  if not label_visible:
    return body
  return (
    body
    + "\n"
    f'<text x="{x + 4.0:.2f}" y="{y + 13.0:.2f}" font-size="10" '
    f'font-family="monospace" fill="{color}">{escaped_label}</text>'
  )


def _svg_clip_path_for_hull(
  *,
  clip_id: str,
  hull_points: list[list[float]],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
) -> str:
  screen_points = [
    _svg_project_point(
      point=(point[0], point[1]),
      view_bounds=view_bounds,
      width=width,
      height=height,
    )
    for point in hull_points
  ]
  point_text = " ".join(
    f"{point[0]:.2f},{point[1]:.2f}" for point in screen_points
  )
  return (
    f'<defs><clipPath id="{html.escape(clip_id)}" clipPathUnits="userSpaceOnUse">'
    f'<polygon points="{point_text}"/></clipPath></defs>'
  )


def _semantic_parent_child_layout_mini_svg(
  proxy: dict[str, Any],
  airframe_proxies: list[dict[str, Any]],
  row: dict[str, Any],
  view: str,
  *,
  width: int = 960,
  height: int = 620,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  view_bounds = _projected_view_bounds_for_parent_child_layout(
    proxy,
    row,
    axes,
  )
  geometry = proxy["mesh_derived_review_geometry"]
  hull_points = geometry.get("hulls", {}).get(view, {}).get("points_m", [])
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    (
      f'<text x="12" y="20" font-size="13" font-family="monospace" fill="#111827">'
      f'{html.escape(row["source_region_id"])} parent + receiver priors / {view} ({view_label})</text>'
    ),
  ]
  for airframe_proxy in airframe_proxies:
    airframe_hull_points = (
      airframe_proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(airframe_hull_points) >= 3:
      elements.append(
        _svg_polygon_projected(
          points=airframe_hull_points,
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#94a3b8",
          label="whole_airframe_region",
          fill_opacity=0.0,
          stroke_width=1.0,
          label_visible=False,
        )
      )
  if len(hull_points) >= 3:
    elements.append(
      _svg_polygon_projected(
        points=hull_points,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#2563eb",
        label="parent_mesh_region",
        fill_opacity=0.0,
        stroke_width=2.5,
        label_visible=False,
      )
    )
  child_elements: list[str] = []
  child_count = len(row["child_receiver_priors"])
  for child_index, child in enumerate(row["child_receiver_priors"]):
    if child["is_cross_region_held"]:
      color = "#be123c"
      role_label = "held-segment"
    elif child["layout_role"] in {
      "single_receiver_overlay",
      "primary_receiver_overlay",
    }:
      color = "#16a34a"
      role_label = "primary"
    else:
      color = "#0891b2"
      role_label = "extra"
    if child["is_cross_region_held"] and child.get("held_segments"):
      for segment in child["held_segments"]:
        segment_child = {
          "prior_shape": segment["segment_shape"],
          "constrained_geometry": segment["geometry"],
        }
        child_elements.append(
          _svg_projected_prior_shape(
            child=segment_child,
            axes=axes,
            view_bounds=view_bounds,
            width=width,
            height=height,
            color=color,
            fill_opacity=0.78,
            stroke_width=3.0,
            stroke_color="#7f1d1d",
            label=(
              f'{child["component_name"]}:{segment["segment_id"]} '
              f'{segment["segment_shape"]} {role_label}'
            ),
            projected_bounds=projection_geometry.project_bounds(segment["geometry"]["bounds"], axes),
            label_visible=False,
          )
        )
      continue
    projected_bounds = projection_geometry.project_bounds(child["constrained_geometry"]["bounds"], axes)
    child_elements.append(
      _svg_projected_prior_shape(
        child=child,
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=color,
        fill_opacity=0.92,
        stroke_width=2.2,
        label=(
          f'{child["component_name"]} '
          f'{child["prior_shape"]} {role_label}'
        ),
        projected_bounds=projected_bounds,
        label_visible=False,
      )
    )
  for segment in row.get("cross_region_held_segment_overlays", []):
    segment_child = {
      "prior_shape": segment["segment_shape"],
      "constrained_geometry": segment["geometry"],
    }
    child_elements.append(
      _svg_projected_prior_shape(
        child=segment_child,
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#be123c",
        fill_opacity=0.52,
        stroke_width=2.6,
        stroke_color="#7f1d1d",
        label=(
          f'{segment["parent_component_name"]}:{segment["segment_id"]} '
          "external held-segment"
        ),
        projected_bounds=projection_geometry.project_bounds(segment["geometry"]["bounds"], axes),
        label_visible=False,
      )
    )
  elements.extend(child_elements)
  elements.append(
    f'<text x="12" y="{height - 12}" font-size="10" font-family="monospace" fill="#475569">'
    'gray=whole-airframe wireframe; blue=parent semantic region; green/cyan=actual-size receiver prior; red=held split segment</text>'
  )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _write_semantic_parent_child_layout_index(
  root_dir: Path,
  entries: list[dict[str, Any]],
  layout_report: dict[str, Any],
) -> Path:
  index_path = root_dir / "index.html"
  cards = "".join(
    f"""
    <article class="{html.escape(entry["priority"])}">
      <h2><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h2>
      <p>{html.escape(entry["subtitle"])}</p>
      <p>{html.escape(entry["decision_needed"])}</p>
    </article>
    """
    for entry in entries
  )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Semantic Parent-Child Component Layout Views</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      font-size: 18px;
    }}
    p {{
      color: #475569;
      line-height: 1.35;
      margin: 8px 0 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #16a34a;
      border-radius: 6px;
      padding: 12px;
      background: #f8fff9;
    }}
    article.warning {{
      border-left-color: #be123c;
      background: #fff7f7;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Semantic Parent-Child Component Layout Views</h1>
    <p>Primary review view: 14 mesh-derived parent shell parts, with actual-size receiver priors overlaid where public dimensions or explicitly graded engineering proxies exist. The extra receiver slots are visual overlays, not accepted runtime ownership.</p>
    <div class="summary">
      <div>parent shell parts: {layout_report["summary"]["parent_semantic_component_count"]}</div>
      <div>receiver priors overlaid: {layout_report["summary"]["bound_receiver_component_count"]}</div>
      <div>extra receiver slots: {layout_report["summary"]["extra_receiver_slot_count"]}</div>
      <div>cross-region held receivers: {layout_report["summary"]["cross_region_held_receiver_count"]}</div>
      <div>held split segments: {layout_report["summary"]["cross_region_held_segment_count"]}</div>
      <div>external held segment overlays: {layout_report["summary"]["cross_region_held_segment_overlay_count"]}</div>
      <div>runtime active components: {layout_report["summary"]["runtime_active_component_count"]}</div>
      <div><a href="../scene.html">overview packet</a></div>
      <div><a href="../semantic_damage_geometry_views/index.html">semantic shell views</a></div>
      <div><a href="../internal_component_prior_views/index.html">receiver prior views</a></div>
    </div>
  </header>
  <section>
    <div class="entry-grid">
      {cards}
    </div>
  </section>
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def _semantic_parent_child_layout_view_page(
  *,
  row: dict[str, Any],
  svg_filenames: dict[str, str],
) -> str:
  child_lines = [
    (
      f'{child["layout_role"]}: {child["component_name"]} '
      f'{child["prior_shape"]} dims={child["nominal_dimensions_m"]}m '
      f'evidence={child["size_evidence_level"]} '
      f'segments={child["held_segment_count"]} -> {child["constraint_status"]}'
    )
    for child in row["child_receiver_priors"]
  ]
  external_segment_lines = [
    (
      f'{segment["parent_component_name"]}:{segment["segment_id"]} '
      f'{segment["segment_shape"]} owners={segment["owner_region_ids"]} '
      f'dims={segment["nominal_dimensions_m"]}m'
    )
    for segment in row["cross_region_held_segment_overlays"]
  ]
  return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(row["parent_semantic_component_id"])} parent-child layout view</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    figure {{
      margin: 0 0 18px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="../index.html">Back to parent-child layout index</a></p>
    <h1>{html.escape(row["parent_semantic_component_id"])}</h1>
    <p class="subtitle">{html.escape(row["geometry_primitive"])} parent -> {html.escape(row["source_region_id"])}; receiver overlays {row["bound_receiver_count"]}; extra slots {row["extra_receiver_slot_count"]}</p>
  </header>
  <section>
    <h2>Trace Details</h2>
    {_triage_list([
      f'parent semantic component: {row["parent_semantic_component_id"]}',
      f'parent surface component: {row["parent_surface_component_id"]}',
      f'outer model region: {row["source_region_id"]}',
      f'volume role: {row["volume_component_role"]}',
      f'geometry primitive: {row["geometry_primitive"]}',
      f'primary receiver: {row["primary_receiver_component_name"] or "none"}',
      "extra receivers: " + (", ".join(row["extra_receiver_component_names"]) or "none"),
      "cross-region held receivers: " + (", ".join(row["cross_region_held_receiver_names"]) or "none"),
      "external held split segments: " + (
        ", ".join(
          segment["segment_id"]
          for segment in row["cross_region_held_segment_overlays"]
        )
        or "none"
      ),
      f'parent handoff: {row["parent_receiver_handoff_status"]}',
      f'layout policy: {row["layout_policy"]}',
      f'runtime projection: {row["runtime_projection_status"]}',
      "child overlays:",
      *child_lines,
      "external held segment overlays:",
      *external_segment_lines,
    ])}
  </section>
  <section>
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(row["parent_semantic_component_id"])} {html.escape(view)} view"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def write_semantic_parent_child_layout_review_views(
  *,
  layout_report: dict[str, Any],
  fine_proxy: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "semantic_parent_child_layout_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  parent_dir = root_dir / "parents"
  parent_dir.mkdir(parents=True, exist_ok=True)
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  entries: list[dict[str, Any]] = []
  for row in layout_report["rows"]:
    proxy = proxies_by_region[row["source_region_id"]]
    safe_slug = _review_slug(row["parent_semantic_component_id"])
    svg_filenames: dict[str, str] = {}
    for view in ("top", "side", "front"):
      svg_filename = f"{safe_slug}_{view}.svg"
      svg_path = parent_dir / svg_filename
      svg_path.write_text(
        _semantic_parent_child_layout_mini_svg(
          proxy,
          fine_proxy["proxies"],
          row,
          view,
        ),
        encoding="utf-8",
      )
      svg_filenames[view] = svg_filename
    html_path = parent_dir / f"{safe_slug}.html"
    html_path.write_text(
      "\n".join(
        line.rstrip()
        for line in _semantic_parent_child_layout_view_page(
          row=row,
          svg_filenames=svg_filenames,
        ).splitlines()
      )
      + "\n",
      encoding="utf-8",
    )
    entries.append(
      {
        "category": "parent_shells",
        "slug": safe_slug,
        "title": row["parent_semantic_component_id"],
        "subtitle": (
          f'{row["source_region_id"]}: '
          f'{row["bound_receiver_count"]} receiver overlays, '
          f'{row["extra_receiver_slot_count"]} extra, '
          f'{row["cross_region_held_segment_overlay_count"]} external held segments'
        ),
        "priority": (
          "warning"
          if (
            row["cross_region_held_receiver_names"]
            or row["cross_region_held_segment_overlay_count"] > 0
          )
          else "info"
        ),
        "html": _relative_to(html_path, root_dir),
        "svg": {
          view: _relative_to(parent_dir / filename, root_dir)
          for view, filename in svg_filenames.items()
        },
        "parent_semantic_component_id": row["parent_semantic_component_id"],
        "source_region_id": row["source_region_id"],
        "bound_receiver_count": row["bound_receiver_count"],
        "extra_receiver_slot_count": row["extra_receiver_slot_count"],
        "child_receiver_component_names": [
          child["component_name"] for child in row["child_receiver_priors"]
        ],
        "cross_region_held_receiver_names": row[
          "cross_region_held_receiver_names"
        ],
        "cross_region_held_segment_overlay_ids": [
          segment["segment_id"]
          for segment in row["cross_region_held_segment_overlays"]
        ],
        "decision_needed": (
          "Review red held overlays before runtime ownership decisions."
          if (
            row["cross_region_held_receiver_names"]
            or row["cross_region_held_segment_overlay_count"] > 0
          )
          else "Review receiver overlays inside this parent before activation."
        ),
      }
    )

  index_path = _write_semantic_parent_child_layout_index(
    root_dir,
    entries,
    layout_report,
  )
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_semantic_parent_child_layout_views.v1",
    "status": "semantic_parent_child_layout_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "parent_child_damage_ownership": False,
    },
    "summary": {
      "entry_count": len(entries),
      "parent_entry_count": len(entries),
      "bound_receiver_component_count": layout_report["summary"][
        "bound_receiver_component_count"
      ],
      "extra_receiver_slot_count": layout_report["summary"][
        "extra_receiver_slot_count"
      ],
      "cross_region_held_receiver_count": layout_report["summary"][
        "cross_region_held_receiver_count"
      ],
      "cross_region_held_segment_count": layout_report["summary"][
        "cross_region_held_segment_count"
      ],
      "cross_region_held_segment_overlay_count": layout_report["summary"][
        "cross_region_held_segment_overlay_count"
      ],
    },
    "index_html": "index.html",
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _surface_component_rows(
  surface_row: dict[str, Any],
  rows_by_component: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for link in surface_row["linked_internal_components"]:
    row = rows_by_component.get(link["component_name"])
    if row is not None:
      rows.append(row)
  return rows


def _component_triage_prompts(row: dict[str, Any]) -> tuple[str, str, str]:
  anomalies = row["anomalies"]
  component_name = row["component_name"]
  region_id = row["bound_region_id"]
  semantics = row.get("review_semantics", "")
  if semantics == "side_sign_mismatch_hard_blocker":
    return (
      f"Does {component_name} belong on the opposite side from the {region_id} proxy, or are the left/right region labels flipped?",
      "In the top and front views, compare the red component box label with the blue mesh silhouette and orange source bounds for the wing or wing root.",
      "Choose one before TG-P7: swap/fix the coordinate-side convention, move the component box, or hold wing/root runtime use.",
    )
  if semantics == "invalid_region_binding_blocked":
    return (
      f"Why did {component_name} rank against blocked region {region_id}?",
      "Check whether the red component box is detached from its expected engine/nozzle surface and incorrectly overlapping a tail surface.",
      "Do not use this binding; repair the component box or mapping before runtime handoff.",
    )
  if semantics == "cross_region_boundary_candidate_review_only":
    return (
      f"Is {component_name} acceptable as a review-only cross-region boundary candidate?",
      "Check whether the red box center remains in the aft engine bay while its span crosses neighboring intake/nozzle semantics.",
      "Keep as review-only candidate or split it; do not treat this as accepted runtime integration.",
    )
  if semantics == "cross_region_structural_semantic_hold":
    return (
      f"Should {component_name} remain a held cross-region structural semantic candidate?",
      "Check the broad thin box across center fuselage and wing-root surfaces before assigning a single receiver.",
      "Hold or split the semantic receiver before runtime projection; low overlap alone is not a bad-box verdict.",
    )
  if "no_outer_region_overlap" in anomalies:
    return (
      f"Why does {component_name} not overlap its assigned outer region {region_id}?",
      "In all three views, check whether the red component box sits outside the blue silhouette or merely misses the orange source AABB due to height/axis drift.",
      "Decide whether to repair the current component box, change the outer-region mapping, or keep this component out of runtime handoff.",
    )
  if "low_outer_region_overlap" in anomalies:
    return (
      f"Is the low overlap for {component_name} intentional multi-region coverage or stale component geometry?",
      "Check whether the red box straddles a sensible neighboring surface or is visibly detached from the blue mesh silhouette.",
      "Accept only if the overlap is explainable; otherwise split/move the component box or mark the handoff held.",
    )
  return (
    f"Does {component_name} visibly match its assigned outer region {region_id}?",
    "Compare red component box, orange source bounds, gray support bounds, and blue mesh silhouette.",
    "Accept, repair component placement, or hold runtime use for this region.",
  )


def _surface_triage_prompts(row: dict[str, Any]) -> tuple[str, str, str]:
  flags = row["review_flags"]
  surface_id = row["surface_component_id"]
  region_id = row["source_region_id"]
  missing = ", ".join(row["missing_existing_runtime_component_relations"]) or "none"
  semantics = row.get("review_semantics", "")
  if semantics == "missing_runtime_link/held":
    return (
      f"What runtime component should receive a hit on {surface_id}?",
      "The blue silhouette shows the outer surface; red/purple boxes show current internal components, if any. Empty or offset boxes mean the handoff is not explicit.",
      f"Add/identify the missing runtime relation ({missing}), or explicitly hold this surface from runtime projection.",
    )
  if semantics == "side_sign_mismatch_hard_blocker":
    return (
      f"Are the linked components for {surface_id} on the correct aircraft side?",
      "Use the top and front views to compare linked red boxes with the surface proxy side and the left/right names.",
      "Resolve side naming before accepting this surface handoff.",
    )
  if semantics == "invalid_region_binding_blocked":
    return (
      f"Which invalid component binding is polluting {surface_id}?",
      "Look for any red component linked through a blocked rule rather than a clean direct receiver.",
      "Block that relation in the review handoff and repair the source component or region mapping separately.",
    )
  if semantics in {
    "cross_region_semantic_hold",
    "cross_region_boundary_candidate_review_only",
  }:
    return (
      f"Which links for {surface_id} are clean direct receivers versus review-only cross-region semantics?",
      "Compare clean purple/red boxes with the cross-region component names listed in the trace details.",
      "Keep clean direct links separate, and keep cross-region links held or review-only until runtime ownership is explicit.",
    )
  if "linked_component_needs_review" in flags:
    return (
      f"Can {surface_id} hand off to its linked components while those component boxes still need review?",
      "Look for red labels inside or near the blue silhouette; red means the linked component's own binding is not clean.",
      "Fix or accept the linked component boxes first, then revisit this surface handoff.",
    )
  if "no_direct_component_bound_to_surface_region" in flags:
    return (
      f"Should {surface_id} have a direct internal component bound to {region_id}?",
      "Check whether any red/purple component box is actually colocated with the surface proxy.",
      "Accept an empty/non-direct surface only if damage should intentionally bypass current component records.",
    )
  return (
    f"Is {surface_id} a clean surface-to-component handoff?",
    "Confirm the surface proxy and linked component boxes occupy the same plausible aircraft area.",
    "Accept visually, or mark the handoff held.",
  )


def _point_triage_prompts(row: dict[str, Any]) -> tuple[str, str, str]:
  point_id = row["point_id"]
  if "beam" in point_id:
    return (
      f"Does {point_id} expose a left/right coordinate-sign problem?",
      "The black point is the review point; compare its lateral side with the nearest wing silhouette and the red candidate component labels.",
      "Do not use beam/wing projection at runtime until point side, wing side, and component names agree.",
    )
  if point_id.startswith("nose_axis"):
    return (
      f"Does {point_id} explain the nose close-to-shape behavior without relying on direct-hit boxes?",
      "The black point should be read against the nose/forward-fuselage blue silhouette and nearby red component boxes.",
      "Decide whether this point has a valid candidate-component path, or whether nose proximity must remain held.",
    )
  return (
    f"Does {point_id} have a plausible outer-surface and component interpretation?",
    "Compare the black point with the blue silhouette and any nearby red/purple component boxes.",
    "Accept as diagnostic-only, add missing component candidates, or hold runtime use.",
  )


def write_human_review_triage_dashboard(
  *,
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  diagnostics: dict[str, Any],
  surface_report: dict[str, Any],
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  path = output_dir / "human_review_triage.html"
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = _component_rows_by_name(component_report)
  surface_rows_by_region = {
    row["source_region_id"]: row for row in surface_report["rows"]
  }
  fine_rows_by_point = {
    row["point_id"]: row for row in fine_proxy["review_point_distance_deltas"]
  }

  sign_cards: list[str] = []
  placement_cards: list[str] = []
  for row in component_report["rows"]:
    if row["review_status"] == "candidate_binding":
      continue
    proxy = proxies_by_region.get(row["bound_region_id"])
    if proxy is None:
      continue
    details = [
      f'component: {row["component_name"]}',
      f'system: {row["system"]}',
      f'bound outer region: {row["bound_region_id"]}',
      f'review semantics: {row["review_semantics"]}',
      f'review severity: {row["review_severity"]}',
      f'component center distance to region: {row["center_distance_m"]} m',
      "anomalies: " + ", ".join(row["anomalies"]),
      "geometry observations: " + ", ".join(row["geometry_observations"]),
      "suppressed anomalies: " + (", ".join(row["suppressed_anomalies"]) or "none"),
      "semantic regions: " + (", ".join(row["semantic_region_ids"]) or "none"),
      "side relation: " + json.dumps(row["side_sign_relation"], sort_keys=True),
      "blocked region binding: "
      + json.dumps(row["blocked_region_binding"], sort_keys=True),
      "review notes: " + " | ".join(row["review_notes"]),
    ]
    question, look_at, decision = _component_triage_prompts(row)
    severity = (
      "critical"
      if row["review_severity"] == "hard_blocker"
      else "warning"
      if row["review_status"] == "needs_review"
      else "info"
    )
    card = _triage_card(
      title=row["component_name"],
      subtitle=f'component binding -> {row["bound_region_id"]}',
      question=question,
      look_at=look_at,
      decision=decision,
      details=details,
      proxy=proxy,
      component_rows=[row],
      severity=severity,
    )
    if row["review_semantics"] == "side_sign_mismatch_hard_blocker":
      sign_cards.append(card)
    else:
      placement_cards.append(card)

  surface_cards: list[str] = []
  for row in surface_report["rows"]:
    if row["review_status"] == "candidate_surface_component":
      continue
    proxy = proxies_by_region.get(row["source_region_id"])
    if proxy is None:
      continue
    component_rows = _surface_component_rows(row, rows_by_component)
    details = [
      f'surface component: {row["surface_component_id"]}',
      f'outer region: {row["source_region_id"]}',
      f'surface role: {row["surface_role"]}',
      f'proxy kind: {row["proxy_kind"]}',
      f'linked current components: {row["linked_internal_component_count"]}',
      f'clean direct links: {row["clean_direct_link_count"]}',
      f'review semantics: {row["review_semantics"]}',
      f'runtime relation status: {row["runtime_relation_status"]}',
      "clean direct components: "
      + (", ".join(row["clean_direct_component_names"]) or "none"),
      "cross-region semantic components: "
      + (", ".join(row["cross_region_semantic_component_names"]) or "none"),
      "blocked components: " + (", ".join(row["blocked_component_names"]) or "none"),
      "bad geometry components: "
      + (", ".join(row["bad_geometry_component_names"]) or "none"),
      "review flags: " + ", ".join(row["review_flags"]),
      "missing runtime links: "
      + (", ".join(row["missing_existing_runtime_component_relations"]) or "none"),
      "linked components: "
      + (
        ", ".join(link["component_name"] for link in row["linked_internal_components"])
        or "none"
      ),
    ]
    severity = (
      "critical"
      if row["review_semantics"]
      in {
        "missing_runtime_link/held",
        "side_sign_mismatch_hard_blocker",
        "invalid_region_binding_blocked",
      }
      else "warning"
    )
    question, look_at, decision = _surface_triage_prompts(row)
    surface_cards.append(
      _triage_card(
        title=row["surface_component_id"],
        subtitle=f'surface handoff -> {row["source_region_id"]}',
        question=question,
        look_at=look_at,
        decision=decision,
        details=details,
        proxy=proxy,
        component_rows=component_rows,
        severity=severity,
      )
    )

  point_focus_ids = {
    "nose_axis_4m",
    "nose_axis_6m",
    "right_beam_4m",
    "left_beam_4m",
    "above_4m",
    "below_4m",
  }
  point_cards: list[str] = []
  for row in diagnostics["rows"]:
    if row["point_id"] not in point_focus_ids:
      continue
    fine_row = fine_rows_by_point.get(row["point_id"], {})
    region_id = row["nearest_outer_region_id"]
    proxy = proxies_by_region.get(region_id)
    if proxy is None:
      continue
    component_rows = [
      rows_by_component[item["component_name"]]
      for item in row["candidate_components"]
      if item["component_name"] in rows_by_component
    ]
    details = [
      f'point: {row["point_id"]} at {row["point_m"]}',
      f'nearest outer region: {row["nearest_outer_region_id"]}',
      f'nearest outer distance: {row["nearest_outer_distance_m"]} m',
      "nearest fine proxy: "
      + str(fine_row.get("nearest_fine_proxy_region_id", "unknown")),
      f'nearest component: {row["nearest_component_name"]}',
      f'nearest component distance: {row["nearest_component_distance_m"]} m',
      f'candidate component count: {row["candidate_component_count"]}',
      f'interpretation: {row["interpretation"]}',
    ]
    question, look_at, decision = _point_triage_prompts(row)
    point_cards.append(
      _triage_card(
        title=row["point_id"],
        subtitle="review point geometry sanity",
        question=question,
        look_at=look_at,
        decision=decision,
        details=details,
        proxy=proxy,
        component_rows=component_rows,
        severity="critical" if "beam" in row["point_id"] else "warning",
        review_points=[row],
      )
    )

  def section(title: str, intro: str, cards: list[str]) -> str:
    return f"""
      <section>
        <h2>{html.escape(title)} <span>{len(cards)}</span></h2>
        <p>{html.escape(intro)}</p>
        <div class="card-stack">
          {"".join(cards) if cards else '<p class="empty">No current items.</p>'}
        </div>
      </section>
    """

  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Human Review Triage</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1500px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2, h3 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      font-size: 20px;
      margin-bottom: 8px;
    }}
    h2 span {{
      color: #475569;
      font-family: monospace;
      font-size: 15px;
    }}
    p {{
      color: #475569;
      margin: 8px 0 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .triage-card {{
      border: 2px solid #d97706;
      border-radius: 6px;
      margin: 0 0 16px;
      padding: 14px;
      background: #fffdf7;
    }}
    .triage-card.critical {{
      border-color: #be123c;
      background: #fff7f7;
    }}
    .triage-card.warning {{
      border-color: #d97706;
    }}
    .triage-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 8px;
    }}
    .triage-head span {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
    }}
    .decision-box {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 10px;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 10px;
      margin: 0 0 12px;
    }}
    .decision-box strong {{
      display: block;
      color: #0f172a;
      font-size: 12px;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .decision-box p {{
      color: #1f2937;
      font-size: 13px;
      line-height: 1.35;
      margin: 4px 0 0;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 5px 12px;
      margin: 0 0 12px;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    .mini-views {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 12px;
    }}
    svg {{
      width: 100%;
      height: auto;
      border: 1px solid #cbd5e1;
      background: #ffffff;
    }}
    .empty {{
      color: #64748b;
      font-family: monospace;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
	  <header>
	    <h1>F-16 Human Review Triage</h1>
	    <p>Answer the review question at the top of each card. The local top, side, and front overlays show exactly where to inspect before accepting, repairing, or holding the item.</p>
    <div class="summary">
      <div>component binding issues: {len(sign_cards) + len(placement_cards)}</div>
      <div>coordinate sign issues: {len(sign_cards)}</div>
      <div>surface handoff issues: {len(surface_cards)}</div>
      <div>focused review points: {len(point_cards)}</div>
      <div><a href="scene.html">overview packet</a></div>
      <div><a href="fine_proxy_review_dashboard.html">region dashboard</a></div>
    </div>
  </header>
  {section(
    "Coordinate Sign Review",
    "These cards are the left/right naming versus local-coordinate cases. Resolve them before trusting wing or wing-root handoff.",
    sign_cards,
  )}
  {section(
    "Component Box Placement Review",
    "These current internal components have low or missing overlap with the corrected outer region.",
    placement_cards,
  )}
  {section(
    "Surface Handoff Review",
    "These outer-surface candidates do not yet have clean, explicit links to current runtime damage components.",
    surface_cards,
  )}
  {section(
    "Review Point Geometry Sanity",
    "These points are the geometry cases that should be understood before any near-fuze, rod, or fragment runtime interface decision.",
    point_cards,
  )}
</main>
</body>
</html>
"""
  path.write_text("\n".join(line.rstrip() for line in body.splitlines()) + "\n", encoding="utf-8")
  return path


def write_fine_proxy_review_dashboard(
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  output_dir: Path,
  surface_report: dict[str, Any] | None = None,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  path = output_dir / "fine_proxy_review_dashboard.html"
  surface_rows_by_region = {
    row["source_region_id"]: row for row in (surface_report or {}).get("rows", [])
  }
  cards: list[str] = []
  for proxy in fine_proxy["proxies"]:
    region_id = proxy["source_region_id"]
    components = _component_rows_for_region(component_report, region_id)
    surface_row = surface_rows_by_region.get(region_id)
    flags = _fine_proxy_review_flags(proxy, components)
    status = _fine_proxy_review_status(flags)
    geometry = proxy["mesh_derived_review_geometry"]
    hull_counts = {
      view: record["point_count"] for view, record in geometry["hulls"].items()
    }
    component_list = ", ".join(
      f'{row["component_name"]}:{row["review_status"]}/{row["review_semantics"]}'
      for row in components
    ) or "none"
    if surface_row is None:
      surface_line = "surface component: not generated"
      surface_flags = "surface flags: not generated"
      surface_missing = "missing links: not generated"
    else:
      surface_line = (
        "surface component: "
        f'{surface_row["surface_component_id"]} ({surface_row["surface_role"]})'
      )
      surface_flags = (
        "surface flags: " + ", ".join(surface_row["review_flags"])
      )
      surface_missing = (
        "missing links: "
        + (
          ", ".join(surface_row["missing_existing_runtime_component_relations"])
          or "none"
        )
      )
      surface_line += f' semantics={surface_row["review_semantics"]}'
    card_class = "hold" if status == "hold_for_human_review" else (
      "review" if status == "needs_human_review" else "candidate"
    )
    cards.append(
      f"""
      <section class="region-card {card_class}">
        <div class="region-head">
          <h2>{html.escape(region_id)} <span>{html.escape(proxy["proxy_kind"])}</span></h2>
          <strong>{html.escape(status)}</strong>
        </div>
        <div class="metrics">
          <div>strategy: {html.escape(geometry.get("selection_strategy", ""))}</div>
          <div>fallback: {html.escape(geometry.get("fallback_policy", ""))}</div>
          <div>vertices: {geometry.get("region_vertex_count", 0)}</div>
          <div>source nodes: {html.escape(", ".join(geometry.get("source_node_names", [])) or "all")}</div>
          <div>hull points: top {hull_counts.get("top", 0)} / side {hull_counts.get("side", 0)} / front {hull_counts.get("front", 0)}</div>
          <div>flags: {html.escape(", ".join(flags))}</div>
          <div>components: {html.escape(component_list)}</div>
          <div>{html.escape(surface_line)}</div>
          <div>{html.escape(surface_flags)}</div>
          <div>{html.escape(surface_missing)}</div>
        </div>
        <div class="mini-views">
          {_fine_proxy_review_mini_svg(proxy, components, "top")}
          {_fine_proxy_review_mini_svg(proxy, components, "side")}
          {_fine_proxy_review_mini_svg(proxy, components, "front")}
        </div>
      </section>
      """
    )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Fine Proxy Human Review Dashboard</title>
  <style>
    body {{
      margin: 0;
      background: #f8fafc;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1 {{
      margin: 0 0 8px;
    }}
    .summary {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      padding: 14px 16px;
      margin-bottom: 18px;
      font-family: monospace;
      font-size: 13px;
    }}
    .region-card {{
      background: #ffffff;
      border: 2px solid #cbd5e1;
      margin: 0 0 18px;
      padding: 14px;
    }}
    .region-card.hold {{
      border-color: #dc2626;
    }}
    .region-card.review {{
      border-color: #d97706;
    }}
    .region-card.candidate {{
      border-color: #16a34a;
    }}
    .region-head {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: baseline;
      margin-bottom: 8px;
    }}
    h2 {{
      margin: 0;
      font-size: 18px;
    }}
    h2 span {{
      color: #475569;
      font-size: 13px;
      font-family: monospace;
      font-weight: 400;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 6px 12px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
      margin-bottom: 12px;
    }}
    .mini-views {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 12px;
    }}
    svg {{
      width: 100%;
      height: auto;
      border: 1px solid #cbd5e1;
      background: #ffffff;
    }}
  </style>
</head>
<body>
<main>
  <h1>F-16 Fine Proxy Human Review Dashboard</h1>
  <div class="summary">
    schema: {html.escape(fine_proxy["schema_version"])}<br>
    proxy_count: {fine_proxy["summary"]["proxy_count"]};
    mesh_silhouettes: {fine_proxy["summary"]["mesh_derived_silhouette_count"]};
    source_vertices: {fine_proxy["summary"]["mesh_source_vertex_count"]};
    review_status: {html.escape(fine_proxy["summary"]["review_status"])}<br>
    Review-only visual diagnostics. This is not a runtime collision mesh, not true F-16 engineering geometry, and not weapon lethality evidence.
  </div>
  {"".join(cards)}
</main>
</body>
</html>
"""
  body = "\n".join(line.rstrip() for line in body.splitlines()) + "\n"
  path.write_text(body, encoding="utf-8")
  return path
