"""Fine-proxy SVG review views for airframe geometry reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import projection_geometry
from tools.geometry.airframe_review._svg_primitives import (
    _svg_color,
    _svg_point,
    _svg_polygon,
    _svg_polygon_projected,
    _svg_rect,
)


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
        f"F-16 mesh-derived fine geometry proxy candidate {view} view</text>",
        f'<text x="24" y="58" font-size="12" font-family="monospace" fill="#555555">'
        f"{label_x}; {label_y}; dashed source AABB, dotted support bounds, solid mesh-derived silhouette</text>",
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
                bounds=projection_geometry.project_bounds(
                    proxy["source_region_bounds"], (axis_x, axis_y)
                ),
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
                bounds=projection_geometry.project_bounds(
                    proxy["support_bounds"], (axis_x, axis_y)
                ),
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
                    bounds=projection_geometry.project_bounds(
                        proxy["support_bounds"], (axis_x, axis_y)
                    ),
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
            "Legend: dashed boxes are TG-P2 source AABBs; dotted boxes are support bounds; solid polygons are mesh-derived silhouettes</text>",
            '<text x="24" y="736" font-size="11" font-family="monospace" fill="#555555">'
            "Review-only fine proxy candidates; not a runtime collision mesh or real F-16 engineering model</text>",
        ]
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
        'viewBox="0 0 1200 760">\n' + "\n".join(elements) + "\n</svg>\n"
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
        "orange=source, gray=support, purple/red=components, blue=mesh, black=point</text>"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        + "\n".join(elements)
        + "</svg>"
    )
