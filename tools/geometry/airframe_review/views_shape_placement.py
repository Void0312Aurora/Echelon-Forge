"""Subcomponent shape-placement review views."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import projection_geometry
from tools.geometry.airframe_review._svg_primitives import (
    _fit_view_bounds_to_screen_aspect,
    _svg_polygon_projected,
    _svg_projected_prior_shape,
    _svg_scale_bar,
    _svg_shape_label_badge,
)
from tools.geometry.airframe_review._view_shared import _relative_to, _review_slug, _triage_list


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
            proxy["mesh_derived_review_geometry"].get("hulls", {}).get(view, {}).get("points_m", [])
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
            proxy["mesh_derived_review_geometry"].get("hulls", {}).get(view, {}).get("points_m", [])
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
            f"R20 latest subcomponent candidates / {view} ({view_label})</text>"
        ),
        (
            f'<text x="18" y="52" font-size="12" font-family="monospace" '
            f'fill="#475569">gray=whole-airframe wireframe; '
            f"blue=latest subcomponent candidate; numbers match the item list</text>"
        ),
    ]
    for proxy in fine_proxy["proxies"]:
        hull_points = (
            proxy["mesh_derived_review_geometry"].get("hulls", {}).get(view, {}).get("points_m", [])
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
    item_lines = [f'{index}. {row["item_id"]}' for index, row in enumerate(rows, start=1)]
    line_height = 15
    start_y = height - 18 - line_height * len(item_lines)
    for index, item_line in enumerate(item_lines):
        elements.append(
            f'<text x="18" y="{start_y + index * line_height:.2f}" '
            f'font-size="11" font-family="monospace" fill="#334155">'
            f"{html.escape(item_line)}</text>"
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">' + "\n".join(elements) + "</svg>"
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
    component_shape = _svg_projected_prior_shape(
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
            f"R20 latest subcomponents by component / {html.escape(part_label)}</text>"
        ),
        (
            f'<text x="18" y="52" font-size="12" font-family="monospace" '
            f'fill="#475569">one row = one latest subcomponent; '
            f"columns = top / side / front local zoom; "
            f"blue=that row latest candidate; each panel includes a meter scale bar; "
            f"airframe context is omitted here so the subcomponent body is visible</text>"
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
                f'<g transform="translate({tile_x},{row_y})">' + "\n".join(tile_elements) + "</g>"
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">' + "\n".join(elements) + "</svg>\n"
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
            proxy["mesh_derived_review_geometry"].get("hulls", {}).get(view, {}).get("points_m", [])
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
            label=(f'{row["item_id"]} latest ' f'{row["latest_candidate_stage"]}'),
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
        "gray=whole-airframe wireframe; blue=latest subcomponent candidate</text>"
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
            "<p>No remaining subcomponent shape-placement candidates after "
            "R21 review-only rule promotion.</p>"
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
        part_rows = shape_report["rows"][start : start + atlas_part_size]
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
                1
                for row in shape_report["rows"]
                if row["latest_candidate_silhouette"]["outside_sample_count"] == 0
            ),
            "unresolved_entry_count": sum(
                1
                for row in shape_report["rows"]
                if row["latest_candidate_silhouette"]["outside_sample_count"] > 0
            ),
            "shape_candidate_resolved_entry_count": sum(
                1
                for row in shape_report["rows"]
                if row["candidate_silhouette"]["outside_sample_count"] == 0
            ),
            "centerline_candidate_resolved_entry_count": sum(
                1
                for row in shape_report["rows"]
                if row["centerline_candidate_silhouette"]["outside_sample_count"] == 0
            ),
        },
        "index_html": "index.html",
        "overview_svg": {
            view: _relative_to(path, root_dir) for view, path in overview_svg_paths.items()
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
