"""Human and fine-proxy triage dashboards for airframe review."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from ._view_shared import _component_rows_by_name, _triage_card
from .views_fine_proxy import _fine_proxy_review_mini_svg


def _component_rows_for_region(
    component_report: dict[str, Any],
    region_id: str,
) -> list[dict[str, Any]]:
    return [row for row in component_report["rows"] if row["bound_region_id"] == region_id]


def _fine_proxy_review_flags(
    proxy: dict[str, Any],
    component_rows: list[dict[str, Any]],
) -> list[str]:
    geometry = proxy["mesh_derived_review_geometry"]
    hull_counts = [view["point_count"] for view in geometry.get("hulls", {}).values()]
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
    proxies_by_region = {proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]}
    rows_by_component = _component_rows_by_name(component_report)
    surface_rows_by_region = {row["source_region_id"]: row for row in surface_report["rows"]}
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
            "blocked region binding: " + json.dumps(row["blocked_region_binding"], sort_keys=True),
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
            "nearest fine proxy: " + str(fine_row.get("nearest_fine_proxy_region_id", "unknown")),
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
        hull_counts = {view: record["point_count"] for view, record in geometry["hulls"].items()}
        component_list = (
            ", ".join(
                f'{row["component_name"]}:{row["review_status"]}/{row["review_semantics"]}'
                for row in components
            )
            or "none"
        )
        if surface_row is None:
            surface_line = "surface component: not generated"
            surface_flags = "surface flags: not generated"
            surface_missing = "missing links: not generated"
        else:
            surface_line = (
                "surface component: "
                f'{surface_row["surface_component_id"]} ({surface_row["surface_role"]})'
            )
            surface_flags = "surface flags: " + ", ".join(surface_row["review_flags"])
            surface_missing = "missing links: " + (
                ", ".join(surface_row["missing_existing_runtime_component_relations"]) or "none"
            )
            surface_line += f' semantics={surface_row["review_semantics"]}'
        card_class = (
            "hold"
            if status == "hold_for_human_review"
            else ("review" if status == "needs_human_review" else "candidate")
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
