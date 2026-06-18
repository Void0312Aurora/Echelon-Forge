"""Internal component prior review views."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import projection_geometry
from tools.geometry.airframe_review.constants import CROSS_REGION_REVIEW_SEMANTICS
from tools.geometry.airframe_review._svg_primitives import _svg_polygon_projected, _svg_rect
from tools.geometry.airframe_review._view_shared import (
    _component_rows_by_name,
    _relative_to,
    _review_slug,
    _triage_list,
)


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
            bounds=projection_geometry.project_bounds(
                prior_row["constrained_geometry"]["bounds"], axes
            ),
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
        "orange=parent support, gray=constraint, purple=old AABB, cyan=constrained prior, blue=mesh</text>"
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
        f"{shape}:{count}" for shape, count in prior_report["summary"]["shape_counts"].items()
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
    proxies_by_region = {proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]}
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
                1
                for row in prior_report["rows"]
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
