"""Whole-airframe contour SVG and dashboard review views."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import contours, projection_geometry
from tools.geometry.airframe_review._svg_primitives import _svg_polygon_projected


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
        f"F-16 projected audit-mesh contour - {view} view</text>",
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
            f"Legend: gray=projected audit-mesh silhouette; "
            f"green=receiver inside contour; red=receiver exceeds {tolerance:g}m tolerance; "
            f"red fill=protruding portion</text>",
            f'<text x="24" y="{legend_y + 20}" font-size="11" font-family="monospace" fill="#555555">'
            "Review-only diagnostic; not a runtime collision mesh, not real F-16 engineering geometry</text>",
        ]
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
        'viewBox="0 0 1200 760">\n' + "\n".join(elements) + "\n</svg>\n"
    )


def write_whole_airframe_contour_svg_views(
    report: dict[str, Any],
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for view in ("top", "side", "front"):
        path = output_dir / f"whole_airframe_contour_{view}.svg"
        path.write_text(_svg_for_whole_airframe_contour_view(report, view), encoding="utf-8")
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
        f"<section><h2>{view} view</h2>"
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
