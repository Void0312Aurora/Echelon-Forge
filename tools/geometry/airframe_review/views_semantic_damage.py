"""Semantic damage geometry review views."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any

from tools.geometry.airframe_review._view_shared import (
    _component_rows_by_name,
    _write_isolated_review_entry,
)


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
    proxies_by_region = {proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]}
    rows_by_component = _component_rows_by_name(component_report)
    entries: list[dict[str, Any]] = []
    for row in semantic_report["rows"]:
        proxy = proxies_by_region[row["source_region_id"]]
        receiver_names = row["direct_receiver_components"] + row["cross_region_receiver_components"]
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
                    "direct receivers: " + (", ".join(row["direct_receiver_components"]) or "none"),
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
                1 for row in semantic_report["rows"] if row["cross_region_receiver_components"]
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
