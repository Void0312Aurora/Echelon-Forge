"""Final HTML review packet writer."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any


def _html_table(headers: list[str], rows: list[list[Any]]) -> str:
  header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
  row_html = []
  for row in rows:
    row_html.append(
      "<tr>"
      + "".join(f"<td>{html.escape(str(value))}</td>" for value in row)
      + "</tr>"
    )
  return (
    '<table>\n<thead><tr>'
    + header_html
    + "</tr></thead>\n<tbody>\n"
    + "\n".join(row_html)
    + "\n</tbody>\n</table>"
  )


def write_review_packet(
  *,
  manifest: dict[str, Any],
  mapping: dict[str, Any],
  component_report: dict[str, Any],
  diagnostics: dict[str, Any],
  fine_proxy: dict[str, Any] | None = None,
  surface_report: dict[str, Any] | None = None,
  semantic_report: dict[str, Any] | None = None,
  internal_prior_report: dict[str, Any] | None = None,
  held_segment_report: dict[str, Any] | None = None,
  airframe_constraint_report: dict[str, Any] | None = None,
  whole_airframe_contour_report: dict[str, Any] | None = None,
  ownership_split_report: dict[str, Any] | None = None,
  runtime_activation_report: dict[str, Any] | None = None,
  runtime_behavior_report: dict[str, Any] | None = None,
  training_proxy_report: dict[str, Any] | None = None,
  shape_placement_report: dict[str, Any] | None = None,
  parent_child_layout_report: dict[str, Any] | None = None,
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  html_path = output_dir / "scene.html"
  if whole_airframe_contour_report is not None:
    contour = whole_airframe_contour_report
    contours_summary = "; ".join(
      f'{view}: {meta["status"]} triangles={meta.get("source_triangle_count", 0)} '
      f'polygons={meta.get("polygon_count", 0)} pts={meta["contour_point_count"]}'
      for view, meta in contour["summary"]["contours"].items()
    )
    contour_rows = [
      [
        row["item_id"],
        row["record_type"],
        row["prior_shape"],
        ",".join(row["outside_views"]) or "-",
        row["outside_sample_count"],
        row["max_outside_distance_m"],
      ]
      for row in contour["rows"]
      if row["exceeds_tolerance"]
    ]
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Final Geometry Contour Result</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #202124;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    section {{
      margin: 0 0 24px;
      padding: 18px;
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px 16px;
      font-family: monospace;
      font-size: 13px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
      margin: 12px 0;
      border: 1px solid #cdd3dd;
      background: #ffffff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid #d8dde6;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #eef2f7;
    }}
    .note {{
      color: #4b5563;
      font-size: 13px;
    }}
  </style>
</head>
<body>
<main>
  <section>
    <h1>F-16 Final Geometry Contour Result</h1>
    <p class="note">Current final visual result only. Retired intermediate component, semantic, prior, parent-child, placement, triage, and proxy-dashboard visual pages are not generated in the current packet.</p>
    <div class="meta">
      <div>generated_on: {html.escape(mapping["generated_on"])}</div>
      <div>source_uid: {html.escape(manifest["source"]["uid"])}</div>
      <div>contour_method: {html.escape(contour["contour_method"])}</div>
      <div>tolerance_m: {contour["tolerance_m"]:g}</div>
      <div>exceeds_tolerance: {contour["summary"]["exceeds_tolerance_item_count"]}/{contour["summary"]["item_count"]}</div>
      <div>max_outside_m: {contour["summary"]["max_outside_distance_m"]:g}</div>
    </div>
  </section>
  <section>
    <h2>Whole-Airframe Projected Mesh Contour Containment</h2>
    <p class="note">Review-only diagnostic built from the full audit glTF mesh by projecting triangle faces into each view and unioning those projected faces. Tolerance is an engineering review margin, not physical clearance. Contours: {html.escape(contours_summary)}.</p>
    <p><a href="whole_airframe_contour_dashboard.html">Open final contour dashboard</a></p>
    <img src="whole_airframe_contour_top.svg" alt="whole-airframe contour top view">
    <img src="whole_airframe_contour_side.svg" alt="whole-airframe contour side view">
    <img src="whole_airframe_contour_front.svg" alt="whole-airframe contour front view">
    {_html_table(
      [
        "item",
        "type",
        "shape",
        "outside_views",
        "outside_samples",
        "max_outside_m",
      ],
      contour_rows,
    )}
  </section>
</main>
</body>
</html>
"""
    html_path.write_text(
      "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
      encoding="utf-8",
    )
    return html_path
  component_rows = [
    [
      row["component_name"],
      row["system"],
      row["bound_region_id"],
      row["review_status"],
      ";".join(row["anomalies"]),
    ]
    for row in component_report["rows"]
  ]
  diagnostic_rows = [
    [
      row["point_index"],
      row["point_id"],
      row["point_m"],
      row["nearest_outer_region_id"],
      row["nearest_outer_distance_m"],
      row["nearest_component_name"],
      row["nearest_component_distance_m"],
      row["candidate_component_count"],
      row["interpretation"],
    ]
    for row in diagnostics["rows"]
  ]
  surface_component_section = ""
  if surface_report is not None:
    surface_rows = [
      [
        row["surface_component_id"],
        row["source_region_id"],
        row["surface_role"],
        row["proxy_kind"],
        row["linked_internal_component_count"],
        row["clean_direct_link_count"],
        ",".join(row["clean_direct_component_names"]),
        ",".join(row["cross_region_semantic_component_names"]),
        ",".join(row["blocked_component_names"]),
        row["runtime_relation_status"],
        row["review_status"],
        row["review_semantics"],
        ";".join(row["review_flags"]),
      ]
      for row in surface_report["rows"]
    ]
    surface_component_section = f"""
  <section>
    <h2>Surface Component Candidates</h2>
    <p class="note">Review-only handoff layer from outer-shape hits to current component damage records. It does not replace the runtime damage model.</p>
    {_html_table(
      [
        "surface_component",
        "outer_region",
        "surface_role",
        "proxy_kind",
        "linked_components",
        "clean_direct_links",
        "clean_direct_components",
        "cross_region_components",
        "blocked_components",
        "runtime_relation_status",
        "status",
        "semantics",
        "flags",
      ],
      surface_rows,
    )}
  </section>
"""
  semantic_damage_geometry_section = ""
  if semantic_report is not None:
    semantic_rows = [
      [
        row["semantic_component_id"],
        row["source_region_id"],
        row["volume_component_role"],
        row["geometry_primitive"],
        ",".join(row["direct_receiver_components"]),
        ",".join(row["cross_region_receiver_components"]),
        row["receiver_handoff_status"],
        row["runtime_projection_status"],
      ]
      for row in semantic_report["rows"]
    ]
    semantic_damage_geometry_section = f"""
  <section>
    <h2>Semantic Damage Geometry Volumes</h2>
    <p class="note">Parse-ready outer-shell volume component candidates generated from TG-P6 mesh proxies and TG-P6 surface handoffs. These are not activated in the current runtime damage model.</p>
    <p class="note">Intermediate semantic volume pages are retained only as raw audit evidence.</p>
    {_html_table(
      [
        "semantic_component",
        "outer_region",
        "volume_role",
        "primitive",
        "direct_receivers",
        "cross_region_receivers",
        "handoff_status",
        "runtime_status",
      ],
      semantic_rows,
    )}
  </section>
"""
  internal_component_prior_section = ""
  if internal_prior_report is not None:
    internal_rows = [
      [
        row["component_name"],
        row["system"],
        row["prior_shape"],
        row["prior_axis"],
        row["bound_region_id"],
        ",".join(row["constraint_region_ids"]),
        row["constraint_status"],
        row["constraint_adjustment"]["pre_constraint_outside_fraction"],
        row["constraint_adjustment"]["post_constraint_outside_fraction"],
        row["runtime_projection_status"],
      ]
      for row in internal_prior_report["rows"]
    ]
    internal_component_prior_section = f"""
  <section>
    <h2>Internal Component Prior Geometry</h2>
    <p class="note">Review-only synthetic receiver geometry generated from simple priors such as sphere, cylinder, capsule, and ellipsoid, then constrained inside parent shell support bounds.</p>
    <p class="note">Intermediate receiver-prior pages are retained only as raw audit evidence.</p>
    {_html_table(
      [
        "component",
        "system",
        "prior_shape",
        "axis",
        "bound_region",
        "constraint_regions",
        "constraint_status",
        "pre_outside",
        "post_outside",
        "runtime_status",
      ],
      internal_rows,
    )}
  </section>
"""
  held_segment_section = ""
  if held_segment_report is not None:
    held_segment_rows = [
      [
        row["parent_component_name"],
        row["segment_id"],
        row["segment_role"],
        ",".join(row["owner_region_ids"]),
        row["segment_shape"],
        row["segment_axis"],
        ",".join(str(value) for value in row["nominal_dimensions_m"]),
        row["inside_whole_airframe_bounds"],
        row["runtime_projection_status"],
      ]
      for row in held_segment_report["rows"]
    ]
    held_segment_section = f"""
  <section>
    <h2>Cross-Region Held Split Segments</h2>
    <p class="note">Review-only split of held receivers (`engine_core`, `wing_spar_center`) into smaller owner-region segments. These red segments replace the monolithic held block in the parent-child visual views; runtime behavior is unchanged.</p>
    {_html_table(
      [
        "parent_component",
        "segment",
        "role",
        "owner_regions",
        "shape",
        "axis",
        "dims_m",
        "inside_airframe",
        "runtime_status",
      ],
      held_segment_rows,
    )}
  </section>
"""
  airframe_constraint_section = ""
  if airframe_constraint_report is not None:
    correction_rows = [
      [
        row["item_id"],
        row["record_type"],
        row["prior_shape"],
        row["size_evidence_level"],
        ",".join(row["current_silhouette"]["outside_views"]),
        row["current_silhouette"]["outside_sample_count"],
        row["candidate_silhouette"]["outside_sample_count"],
        row["candidate_center_shift_m"],
        row["triage_status"],
        row["recommended_action"],
      ]
      for row in airframe_constraint_report["rows"]
      if (
        row["current_silhouette"]["outside_sample_count"] > 0
        or row["triage_status"] == "inside_airframe_low_confidence_size_review"
      )
    ]
    airframe_constraint_section = f"""
  <section>
    <h2>Airframe Constraint Correction Candidates</h2>
    <p class="note">Review-only R16 diagnostics for actual-size receiver priors and held split segments. The tool samples each item's top/side/front projected shape against the whole-airframe silhouette union and records whether a center shift alone can reduce exposure. It does not shrink dimensions or activate runtime components.</p>
    {_html_table(
      [
        "item",
        "type",
        "shape",
        "size_evidence",
        "outside_views",
        "outside_samples",
        "candidate_outside_samples",
        "candidate_shift_m",
        "triage_status",
        "recommended_action",
      ],
      correction_rows,
    )}
  </section>
"""
  whole_airframe_contour_section = ""
  if whole_airframe_contour_report is not None:
    contour = whole_airframe_contour_report
    contour_rows = [
      [
        row["item_id"],
        row["record_type"],
        row["prior_shape"],
        ",".join(row["outside_views"]) or "-",
        row["outside_sample_count"],
        row["max_outside_distance_m"],
        "YES" if row["exceeds_tolerance"] else "no",
      ]
      for row in contour["rows"]
      if row["exceeds_tolerance"]
    ]
    contours_summary = "; ".join(
      f'{view}: {meta["status"]} triangles={meta.get("source_triangle_count", 0)} '
      f'polygons={meta.get("polygon_count", 0)} pts={meta["contour_point_count"]}'
      for view, meta in contour["summary"]["contours"].items()
    )
    whole_airframe_contour_section = f"""
  <section>
    <h2>Whole-Airframe Projected Mesh Contour Containment</h2>
    <p class="note">Review-only diagnostic built from the full audit glTF mesh by projecting triangle faces into each view and unioning those projected faces, then testing receiver samples with shape-aware projected sampling (9-point AABB/OBB grid, ellipsoid 24-point ring, capsule cap rings). Tolerance {contour["tolerance_m"]:g} m is an engineering review margin, not physical clearance. Method: {contour["contour_method"]}. Contours: {contours_summary}. Items exceeding tolerance: <strong>{contour["summary"]["exceeds_tolerance_item_count"]}</strong> of {contour["summary"]["item_count"]}; max outside distance <strong>{contour["summary"]["max_outside_distance_m"]:g} m</strong>.</p>
    <p><a href="whole_airframe_contour_dashboard.html">Open interactive dashboard</a></p>
    <img src="whole_airframe_contour_top.svg" style="width:100%;max-width:1200px;border:1px solid #ccc" alt="whole-airframe contour top view"/>
    <img src="whole_airframe_contour_side.svg" style="width:100%;max-width:1200px;border:1px solid #ccc" alt="whole-airframe contour side view"/>
    <img src="whole_airframe_contour_front.svg" style="width:100%;max-width:1200px;border:1px solid #ccc" alt="whole-airframe contour front view"/>
    {_html_table(
      [
        "item",
        "type",
        "shape",
        "outside_views",
        "outside_samples",
        "max_outside_m",
        "exceeds",
      ],
      contour_rows,
    )}
  </section>
"""
  ownership_split_section = ""
  if ownership_split_report is not None:
    ownership_rows = [
      [
        row["parent_component_name"],
        row["recommended_ownership_decision"],
        row["segment_count"],
        ",".join(row["candidate_runtime_component_names"]),
        ",".join(row["owner_region_ids"]),
        row["silhouette_exposure_segment_count"],
        row["parent_receiver_runtime_policy"],
        row["runtime_activation_status"],
      ]
      for row in ownership_split_report["rows"]
    ]
    ownership_split_section = f"""
  <section>
    <h2>Cross-Region Ownership Split Candidates</h2>
    <p class="note">Review-only R22 ownership decision packet for the two held cross-region receivers. Candidate payloads are parse-ready AABB fallback receiver records with preserved shape metadata; no split receiver is runtime active.</p>
    {_html_table(
      [
        "parent_component",
        "recommended_decision",
        "segments",
        "candidate_receivers",
        "owner_regions",
        "silhouette_exposure_segments",
        "parent_runtime_policy",
        "runtime_status",
      ],
      ownership_rows,
    )}
  </section>
"""
  runtime_activation_section = ""
  if runtime_activation_report is not None:
    activation_rows = [
      [
        row["candidate_component_name"],
        row["parent_component_name"],
        row["segment_role"],
        ",".join(row["owner_region_ids"]),
        row["geometry_primitive"],
        row["runtime_loader_contract_status"],
        row["runtime_activation_status"],
        row["behavior_test_status"],
        row["feature_flag"],
      ]
      for row in runtime_activation_report["rows"]
    ]
    runtime_activation_section = f"""
  <section>
    <h2>TG-P7 Runtime Activation Candidate</h2>
    <p class="note">TG-P7-R1 unit-database patch candidate for the eight R22 split receivers. The payload uses fields already parsed by the runtime unit loader, but it is not applied to the repository unit database and still requires behavior regression before activation.</p>
    <p class="note">parse-ready candidates: {runtime_activation_report["summary"]["runtime_schema_parse_ready_component_count"]}; patch additions: {runtime_activation_report["summary"]["unit_database_patch_component_count"]}; runtime active: {runtime_activation_report["summary"]["runtime_active_component_count"]}</p>
    {_html_table(
      [
        "candidate_component",
        "parent_component",
        "segment_role",
        "owner_regions",
        "primitive",
        "loader_contract",
        "runtime_status",
        "behavior_status",
        "feature_flag",
      ],
      activation_rows,
    )}
  </section>
"""
  runtime_behavior_section = ""
  if runtime_behavior_report is not None:
    behavior_rows = [
      [
        row["parent_component_name"],
        row["target_hitbox_index"],
        row["target_path"],
        row["base_hitbox_component_count"],
        row["patched_hitbox_component_count"],
        row["parent_absent_after_patch"],
        ",".join(row["split_component_names"]),
        row["split_component_present_count"],
        row["duplicate_component_name_count"],
        row["behavior_status"],
      ]
      for row in runtime_behavior_report["rows"]
    ]
    runtime_behavior_section = f"""
  <section>
    <h2>TG-P7 Runtime Behavior Regression Candidate</h2>
    <p class="note">TG-P7-R2 in-memory patch regression: parent receiver components are removed from their current hitbox component arrays and the eight split receiver candidates are appended to those same component arrays. The repository unit database is not modified.</p>
    <p class="note">base components: {runtime_behavior_report["summary"]["base_component_count"]}; projected components: {runtime_behavior_report["summary"]["projected_component_count"]}; retired parents: {runtime_behavior_report["summary"]["retired_parent_component_count"]}; split additions: {runtime_behavior_report["summary"]["split_component_added_count"]}; duplicate names: {runtime_behavior_report["summary"]["duplicate_component_name_count"]}; pass: {runtime_behavior_report["summary"]["behavior_regression_pass"]}</p>
    {_html_table(
      [
        "parent_component",
        "hitbox",
        "target_path",
        "base_hitbox_components",
        "patched_hitbox_components",
        "parent_absent_after_patch",
        "split_components",
        "split_present",
        "duplicates",
        "status",
      ],
      behavior_rows,
    )}
  </section>
"""
  training_proxy_section = ""
  if training_proxy_report is not None:
    proxy_rows = [
      [
        "default_database_component_count",
        training_proxy_report["summary"]["default_database_component_count"],
      ],
      [
        "proxy_database_component_count",
        training_proxy_report["summary"]["proxy_database_component_count"],
      ],
      [
        "split_receiver_component_count",
        training_proxy_report["summary"]["split_receiver_component_count"],
      ],
      [
        "proxy_database_materialized",
        training_proxy_report["summary"]["proxy_database_materialized"],
      ],
      [
        "database_path",
        training_proxy_report["runtime_database"]["proxy_database_path"],
      ],
    ]
    training_proxy_section = f"""
  <section>
    <h2>TG-P7 Training Proxy Database</h2>
    <p class="note">TG-P7-R3 materialized opt-in runtime database for initial training with the split-receiver proxy. The default repository database remains unchanged.</p>
    <p class="note">default components: {training_proxy_report["summary"]["default_database_component_count"]}; proxy components: {training_proxy_report["summary"]["proxy_database_component_count"]}; split receivers: {training_proxy_report["summary"]["split_receiver_component_count"]}</p>
    {_html_table(["field", "value"], proxy_rows)}
  </section>
"""
  shape_placement_section = ""
  if shape_placement_report is not None:
    shape_rows = [
      [
        row["item_id"],
        row["record_type"],
        row["current_shape"],
        row["candidate_shape_family"],
        row["candidate_evaluation_shape"],
        row["current_silhouette"]["outside_sample_count"],
        row["candidate_silhouette"]["outside_sample_count"],
        row["centerline_candidate_silhouette"]["outside_sample_count"],
        row["latest_candidate_silhouette"]["outside_sample_count"],
        row["outside_sample_reduction"],
        row["centerline_incremental_outside_sample_reduction"],
        row["latest_incremental_outside_sample_reduction"],
        row["candidate_center_shift_m"],
        row["centerline_candidate_shift_m"],
        row["latest_candidate_status"],
      ]
      for row in shape_placement_report["rows"]
    ]
    shape_placement_section = f"""
  <section>
    <h2>Subcomponent Shape Placement Candidates</h2>
    <p class="note">Review-only latest subcomponent candidates for the exposed items. Nominal public or declared dimensions are preserved; older current/shape/centerline layers are trace data only, and all candidates remain inactive at runtime.</p>
    <p class="note">latest resolved candidates: {shape_placement_report["summary"]["latest_candidate_resolves_exposure_count"]}; latest unresolved candidates: {shape_placement_report["summary"]["latest_candidate_unresolved_exposure_count"]}; latest outside samples: {shape_placement_report["summary"]["latest_candidate_total_outside_sample_count"]}</p>
    <p class="note">Intermediate placement pages are retained only as raw audit evidence.</p>
    {_html_table(
      [
        "item",
        "type",
        "current_shape",
        "candidate_family",
        "eval_shape",
        "current_outside",
        "shape_outside",
        "centerline_outside",
        "latest_outside",
        "shape_reduction",
        "centerline_incremental_reduction",
        "latest_incremental_reduction",
        "shape_shift_m",
        "centerline_shift_m",
        "latest_status",
      ],
      shape_rows,
    )}
  </section>
"""
  parent_child_layout_section = ""
  if parent_child_layout_report is not None:
    parent_child_rows = [
      [
        row["parent_semantic_component_id"],
        row["source_region_id"],
        row["geometry_primitive"],
        row["bound_receiver_count"],
        row["extra_receiver_slot_count"],
        row["primary_receiver_component_name"],
        ",".join(row["extra_receiver_component_names"]),
        ",".join(row["cross_region_held_receiver_names"]),
        row["cross_region_held_segment_overlay_count"],
        row["runtime_projection_status"],
      ]
      for row in parent_child_layout_report["rows"]
    ]
    parent_child_layout_section = f"""
  <section>
    <h2>Semantic Parent-Child Component Layout</h2>
    <p class="note">Primary visual review surface: `14` mesh-derived parent shell parts with all `26` current receiver priors overlaid inside their parent region; the `12` extra receiver slots are display overlays, not accepted runtime ownership.</p>
    <p class="note">Intermediate parent-child layout pages are retained only as raw audit evidence.</p>
    {_html_table(
      [
        "parent_component",
        "outer_region",
        "primitive",
        "receiver_overlays",
        "extra_slots",
        "primary_receiver",
        "extra_receivers",
        "held_receivers",
        "external_held_segments",
        "runtime_status",
      ],
      parent_child_rows,
    )}
  </section>
"""
  fine_proxy_section = ""
  if fine_proxy is not None:
    fine_proxy_rows = [
      [
        row["point_id"],
        row["nearest_source_aabb_region_id"],
        row["nearest_source_aabb_distance_m"],
        row["nearest_fine_proxy_region_id"],
        row["nearest_fine_proxy_kind"],
        row["nearest_fine_proxy_distance_m"],
        row["fine_minus_source_distance_delta_m"],
      ]
      for row in fine_proxy["review_point_distance_deltas"]
    ]
    fine_proxy_section = f"""
  <section>
    <h2>Fine Geometry Proxy Overlay</h2>
    <p class="note">TG-P6 review-only proxy candidates. Dashed rectangles show source AABB regions, dotted rectangles show support bounds, and solid polygons show mesh-derived silhouettes from filtered audit-glTF vertices.</p>
    <p class="note">Intermediate review HTML pages are retained only as raw audit evidence; the current visual result entrypoint is the whole-airframe projected mesh contour dashboard.</p>
    <div class="views">
      <img src="fine_proxy_top.svg" alt="Top view fine proxy overlay">
      <img src="fine_proxy_side.svg" alt="Side view fine proxy overlay">
      <img src="fine_proxy_front.svg" alt="Front view fine proxy overlay">
    </div>
  </section>
  <section>
    <h2>Fine Proxy Distance Deltas</h2>
    {_html_table(
      [
        "point",
        "source_region",
        "source_dist_m",
        "fine_region",
        "fine_kind",
        "fine_dist_m",
        "delta_m",
      ],
      fine_proxy_rows,
    )}
  </section>
"""
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Target Geometry Review Packet</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #202124;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
      font-weight: 700;
    }}
    section {{
      margin: 0 0 24px;
      padding: 18px;
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 8px 16px;
      font-family: monospace;
      font-size: 13px;
    }}
    .views {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
    }}
    img {{
      width: 100%;
      height: auto;
      border: 1px solid #cdd3dd;
      background: #ffffff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid #d8dde6;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #eef2f7;
    }}
    .note {{
      color: #4b5563;
      font-size: 13px;
    }}
  </style>
</head>
<body>
<main>
  <section>
    <h1>F-16 Target Geometry Review Packet</h1>
    <p class="note">Review-only geometry. This packet is not a runtime collision mesh, not a real F-16 engineering model, and not a real-weapon lethality claim.</p>
    <div class="meta">
      <div>generated_on: {html.escape(mapping["generated_on"])}</div>
      <div>source_uid: {html.escape(manifest["source"]["uid"])}</div>
      <div>outer_regions: {len(mapping["outer_regions"])}</div>
      <div>components: {component_report["summary"]["component_count"]}</div>
      <div>review_points: {diagnostics["summary"]["review_point_count"]}</div>
      <div>needs_review_components: {component_report["summary"]["needs_review_count"]}</div>
    </div>
  </section>
  <section>
    <h2>Three-View Overlay</h2>
    <div class="views">
      <img src="top.svg" alt="Top view geometry overlay">
      <img src="side.svg" alt="Side view geometry overlay">
      <img src="front.svg" alt="Front view geometry overlay">
    </div>
  </section>
{fine_proxy_section}
{semantic_damage_geometry_section}
{internal_component_prior_section}
{held_segment_section}
{airframe_constraint_section}
{whole_airframe_contour_section}
{ownership_split_section}
{runtime_activation_section}
{runtime_behavior_section}
{training_proxy_section}
{shape_placement_section}
{parent_child_layout_section}
{surface_component_section}
  <section>
    <h2>Review Point Diagnostics</h2>
    {_html_table(
      [
        "index",
        "point",
        "local_m",
        "outer_region",
        "outer_dist_m",
        "nearest_component",
        "component_dist_m",
        "candidate_count",
        "interpretation",
      ],
      diagnostic_rows,
    )}
  </section>
  <section>
    <h2>Component Binding Summary</h2>
    {_html_table(
      ["component", "system", "bound_region", "status", "anomalies"],
      component_rows,
    )}
  </section>
</main>
</body>
</html>
"""
  html_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return html_path
