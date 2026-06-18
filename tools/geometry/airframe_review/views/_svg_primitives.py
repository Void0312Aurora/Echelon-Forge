"""Shared SVG primitives for airframe geometry review views."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import projection_geometry


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
        f"<title>{escaped_label}</title></rect>"
        f"{text}"
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
        f"<title>{escaped_label}</title></polygon>"
    )
    if not label_visible:
        return polygon
    return (
        polygon + "\n"
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
        f"F-16 outer-region candidate {view} view</text>",
        f'<text x="24" y="58" font-size="12" font-family="monospace" fill="#555555">'
        f"{label_x}; {label_y}; review-only boxes, component overlays, and review points</text>",
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
                    bounds=projection_geometry.project_bounds(
                        row["component_bounds"], (axis_x, axis_y)
                    ),
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
            "Legend: black envelope, colored outer regions, orange dashed legacy boxes, "
            "purple/red component boxes, numbered review points</text>",
            '<text x="24" y="736" font-size="11" font-family="monospace" fill="#555555">'
            "Review-only geometry; not a runtime collision mesh or real F-16 engineering model</text>",
        ]
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
        'viewBox="0 0 1200 760">\n' + "\n".join(elements) + "\n</svg>\n"
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
        f"<title>{escaped_label}</title>"
    )
    shape = child["prior_shape"]
    if shape in {"sphere", "ellipsoid"}:
        body = (
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
            f'height="{rect_height:.2f}" '
            f'rx="{rect_width * 0.5:.2f}" ry="{rect_height * 0.5:.2f}" '
            f"{common}</rect>"
        )
    elif shape == "capsule":
        radius = min(rect_width, rect_height) * 0.5
        body = (
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
            f'height="{rect_height:.2f}" rx="{radius:.2f}" ry="{radius:.2f}" '
            f"{common}</rect>"
        )
    else:
        body = (
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
            f'height="{rect_height:.2f}" {common}</rect>'
        )
    if not label_visible:
        return body
    return (
        body + "\n"
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
    point_text = " ".join(f"{point[0]:.2f},{point[1]:.2f}" for point in screen_points)
    return (
        f'<defs><clipPath id="{html.escape(clip_id)}" clipPathUnits="userSpaceOnUse">'
        f'<polygon points="{point_text}"/></clipPath></defs>'
    )
