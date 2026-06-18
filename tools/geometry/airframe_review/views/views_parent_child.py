"""Semantic parent-child layout review views."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import projection_geometry
from ._svg_primitives import (
    _svg_clip_path_for_hull,
    _svg_polygon_projected,
    _svg_projected_prior_shape,
)
from ._view_shared import _relative_to, _review_slug, _triage_list


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
            projected.append(
                projection_geometry.project_bounds(segment["geometry"]["bounds"], axes)
            )
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
                        projected_bounds=projection_geometry.project_bounds(
                            segment["geometry"]["bounds"], axes
                        ),
                        label_visible=False,
                    )
                )
            continue
        projected_bounds = projection_geometry.project_bounds(
            child["constrained_geometry"]["bounds"], axes
        )
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
                label=(f'{child["component_name"]} ' f'{child["prior_shape"]} {role_label}'),
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
                projected_bounds=projection_geometry.project_bounds(
                    segment["geometry"]["bounds"], axes
                ),
                label_visible=False,
            )
        )
    elements.extend(child_elements)
    elements.append(
        f'<text x="12" y="{height - 12}" font-size="10" font-family="monospace" fill="#475569">'
        "gray=whole-airframe wireframe; blue=parent semantic region; green/cyan=actual-size receiver prior; red=held split segment</text>"
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
    proxies_by_region = {proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]}
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
                "cross_region_held_receiver_names": row["cross_region_held_receiver_names"],
                "cross_region_held_segment_overlay_ids": [
                    segment["segment_id"] for segment in row["cross_region_held_segment_overlays"]
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
            "extra_receiver_slot_count": layout_report["summary"]["extra_receiver_slot_count"],
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
