"""Surface component and semantic damage geometry candidates."""

from __future__ import annotations

from typing import Any

from tools.geometry.airframe_review.constants import (
  CROSS_REGION_REVIEW_SEMANTICS,
  GEOMETRY_REVIEW_SEMANTICS,
  HARD_BLOCKER_REVIEW_SEMANTICS,
  SEMANTIC_DAMAGE_GEOMETRY_SCHEMA_VERSION,
  SEMANTIC_DAMAGE_VOLUME_RULES,
  SURFACE_COMPONENT_RULES,
  SURFACE_COMPONENT_SCHEMA_VERSION,
)


def _surface_rule_for_region(region: dict[str, Any]) -> dict[str, Any]:
  rule = SURFACE_COMPONENT_RULES.get(region["id"])
  if rule is not None:
    return rule
  return {
    "surface_component_id": f'surface_{region["id"]}',
    "surface_role": region["role"],
    "expected_damage_modes": ["perforation", "skin_tearing"],
    "expected_internal_components": [],
    "missing_existing_runtime_component_relations": [],
  }


def _candidate_region_rank(
  component_row: dict[str, Any],
  region_id: str,
) -> dict[str, Any] | None:
  for rank, candidate in enumerate(component_row["candidate_regions"], start=1):
    if candidate["region_id"] == region_id:
      return {
        "rank": rank,
        "component_overlap_fraction": candidate["component_overlap_fraction"],
        "region_overlap_fraction": candidate["region_overlap_fraction"],
        "center_inside_region": candidate["center_inside_region"],
        "center_distance_m": candidate["center_distance_m"],
      }
  return None


def _surface_component_link_record(
  *,
  region_id: str,
  component_row: dict[str, Any],
  expected_component_names: set[str],
) -> dict[str, Any]:
  relations: list[str] = []
  blocked_binding = (
    component_row["blocked_region_binding"]["blocked"]
    and component_row["blocked_region_binding"]["blocked_region_id"] == region_id
  )
  if component_row["bound_region_id"] == region_id and blocked_binding:
    relations.append("blocked_invalid_region_binding")
  elif component_row["bound_region_id"] == region_id:
    relations.append("bound_to_this_outer_region")
  if component_row["component_name"] in expected_component_names:
    relations.append("expected_surface_effect_path")
  candidate_rank = _candidate_region_rank(component_row, region_id)
  if candidate_rank is not None:
    relations.append("ranked_region_candidate")
  if not relations:
    relations.append("nearby_review_candidate")
  return {
    "component_name": component_row["component_name"],
    "system": component_row["system"],
    "critical": component_row["critical"],
    "relations": relations,
    "bound_region_id": component_row["bound_region_id"],
    "component_review_status": component_row["review_status"],
    "component_review_semantics": component_row["review_semantics"],
    "component_review_severity": component_row["review_severity"],
    "component_overlap_fraction": component_row["component_overlap_fraction"],
    "center_distance_m": component_row["center_distance_m"],
    "candidate_region_rank": candidate_rank,
    "anomalies": component_row["anomalies"],
    "geometry_observations": component_row["geometry_observations"],
    "suppressed_anomalies": component_row["suppressed_anomalies"],
    "semantic_region_ids": component_row["semantic_region_ids"],
    "side_sign_relation": component_row["side_sign_relation"],
    "blocked_region_binding": component_row["blocked_region_binding"],
    "review_notes": component_row["review_notes"],
  }


def _surface_component_review_flags(
  *,
  geometry: dict[str, Any],
  links: list[dict[str, Any]],
  missing_existing_runtime_component_relations: list[str],
) -> list[str]:
  flags: list[str] = []
  if not geometry.get("status", "").startswith("mesh_silhouette_extracted"):
    flags.append("mesh_silhouette_needs_review")
  if not links:
    flags.append("no_internal_component_link")
  if missing_existing_runtime_component_relations:
    flags.append("missing_existing_runtime_component_relation")
    flags.append("missing_runtime_link/held")
  if any(link["component_review_status"] == "needs_review" for link in links):
    flags.append("linked_component_needs_review")
  if any(
    link["component_review_semantics"] in GEOMETRY_REVIEW_SEMANTICS
    for link in links
  ):
    flags.append("linked_component_geometry_needs_review")
  if any(
    link["component_review_semantics"] == "invalid_region_binding_blocked"
    for link in links
  ):
    flags.append("invalid_region_binding_blocked")
  if any(
    link["component_review_semantics"] == "cross_region_boundary_candidate_review_only"
    for link in links
  ):
    flags.append("cross_region_boundary_candidate_review_only")
  if any(
    link["component_review_semantics"] == "cross_region_structural_semantic_hold"
    for link in links
  ):
    flags.append("cross_region_semantic_hold")
  if any(
    link["component_review_semantics"] == "side_sign_mismatch_hard_blocker"
    for link in links
  ):
    flags.append("side_sign_review")
    flags.append("side_sign_mismatch_hard_blocker")
  if any(
    "expected_surface_effect_path" in link["relations"]
    and link["bound_region_id"] != link.get("source_region_id", "")
    for link in links
  ):
    flags.append("expected_component_bound_elsewhere")
  if not any("bound_to_this_outer_region" in link["relations"] for link in links):
    flags.append("no_direct_component_bound_to_surface_region")
  if not flags:
    flags.append("candidate_surface_component")
  return flags


def _surface_component_review_status(flags: list[str]) -> str:
  hard_flags = {
    "missing_runtime_link/held",
    "side_sign_mismatch_hard_blocker",
    "invalid_region_binding_blocked",
    "linked_component_geometry_needs_review",
    "mesh_silhouette_needs_review",
    "no_internal_component_link",
  }
  if any(flag in hard_flags for flag in flags):
    return "needs_human_review"
  if "cross_region_semantic_hold" in flags:
    return "review_only_cross_region_semantic_hold"
  if "cross_region_boundary_candidate_review_only" in flags:
    return "review_only_cross_region_boundary_candidate"
  if flags == ["candidate_surface_component"]:
    return "candidate_surface_component"
  return "needs_human_review"


def _surface_component_review_semantics(flags: list[str]) -> str:
  if "missing_runtime_link/held" in flags:
    return "missing_runtime_link/held"
  if "side_sign_mismatch_hard_blocker" in flags:
    return "side_sign_mismatch_hard_blocker"
  if "invalid_region_binding_blocked" in flags:
    return "invalid_region_binding_blocked"
  if "linked_component_geometry_needs_review" in flags:
    return "linked_component_geometry_needs_review"
  if "cross_region_semantic_hold" in flags:
    return "cross_region_semantic_hold"
  if "cross_region_boundary_candidate_review_only" in flags:
    return "cross_region_boundary_candidate_review_only"
  return "candidate_surface_component"


def build_surface_component_candidate_report(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
) -> dict[str, Any]:
  regions_by_id = {region["id"]: region for region in mapping["outer_regions"]}
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = {
    row["component_name"]: row for row in component_report["rows"]
  }
  rows: list[dict[str, Any]] = []
  for region_id in regions_by_id:
    region = regions_by_id[region_id]
    proxy = proxies_by_region[region_id]
    rule = _surface_rule_for_region(region)
    expected_names = set(rule["expected_internal_components"])
    direct_names = {
      row["component_name"]
      for row in component_report["rows"]
      if row["bound_region_id"] == region_id
    }
    linked_names = sorted(direct_names | expected_names)
    missing_expected_component_names = [
      name for name in sorted(expected_names) if name not in rows_by_component
    ]
    links = [
      _surface_component_link_record(
        region_id=region_id,
        component_row=rows_by_component[name],
        expected_component_names=expected_names,
      )
      for name in linked_names
      if name in rows_by_component
    ]
    for link in links:
      link["source_region_id"] = region_id
    missing_relations = list(rule["missing_existing_runtime_component_relations"])
    flags = _surface_component_review_flags(
      geometry=proxy["mesh_derived_review_geometry"],
      links=links,
      missing_existing_runtime_component_relations=missing_relations,
    )
    review_status = _surface_component_review_status(flags)
    review_semantics = _surface_component_review_semantics(flags)
    clean_link_count = sum(
      1
      for link in links
      if link["component_review_status"] == "candidate_binding"
      and "bound_to_this_outer_region" in link["relations"]
    )
    clean_direct_component_names = [
      link["component_name"]
      for link in links
      if link["component_review_status"] == "candidate_binding"
      and "bound_to_this_outer_region" in link["relations"]
    ]
    cross_region_component_names = [
      link["component_name"]
      for link in links
      if link["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
    ]
    blocked_component_names = [
      link["component_name"]
      for link in links
      if link["component_review_semantics"] in HARD_BLOCKER_REVIEW_SEMANTICS
    ]
    bad_geometry_component_names = [
      link["component_name"]
      for link in links
      if link["component_review_semantics"] in GEOMETRY_REVIEW_SEMANTICS
    ]
    runtime_relation_status = (
      "missing_runtime_link/held"
      if missing_relations
      else "runtime_relation_review_only_candidate"
    )
    rows.append(
      {
        "surface_component_id": rule["surface_component_id"],
        "source_region_id": region_id,
        "source_region_role": region["role"],
        "surface_role": rule["surface_role"],
        "source_region_bounds": region["bounds"],
        "support_bounds": proxy["support_bounds"],
        "proxy_kind": proxy["proxy_kind"],
        "mesh_source_nodes": proxy["mesh_derived_review_geometry"][
          "source_node_names"
        ],
        "mesh_region_vertex_count": proxy["mesh_derived_review_geometry"][
          "region_vertex_count"
        ],
        "expected_damage_modes": rule["expected_damage_modes"],
        "linked_internal_components": links,
        "linked_internal_component_count": len(links),
        "clean_direct_link_count": clean_link_count,
        "clean_direct_component_names": clean_direct_component_names,
        "cross_region_semantic_component_names": cross_region_component_names,
        "blocked_component_names": blocked_component_names,
        "bad_geometry_component_names": bad_geometry_component_names,
        "missing_expected_component_names": missing_expected_component_names,
        "missing_existing_runtime_component_relations": missing_relations,
        "runtime_relation_status": runtime_relation_status,
        "review_flags": flags,
        "review_status": review_status,
        "review_semantics": review_semantics,
        "authority_boundary": (
          "review_only_surface_component_candidate_not_runtime_damage_model"
        ),
      }
    )

  needs_review = [row for row in rows if row["review_status"] == "needs_human_review"]
  return {
    "schema_version": SURFACE_COMPONENT_SCHEMA_VERSION,
    "status": "surface_component_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_mapping_schema_version": mapping["schema_version"],
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "summary": {
      "surface_component_count": len(rows),
      "needs_review_count": len(needs_review),
      "missing_existing_runtime_component_relation_count": sum(
        1
        for row in rows
        if row["missing_existing_runtime_component_relations"]
      ),
      "no_direct_component_bound_count": sum(
        1
        for row in rows
        if "no_direct_component_bound_to_surface_region" in row["review_flags"]
      ),
      "linked_component_needs_review_count": sum(
        1
        for row in rows
        if "linked_component_needs_review" in row["review_flags"]
      ),
      "missing_runtime_link_held_count": sum(
        1
        for row in rows
        if row["runtime_relation_status"] == "missing_runtime_link/held"
      ),
      "side_sign_hard_blocker_count": sum(
        1
        for row in rows
        if "side_sign_mismatch_hard_blocker" in row["review_flags"]
      ),
      "invalid_region_binding_blocked_count": sum(
        1
        for row in rows
        if "invalid_region_binding_blocked" in row["review_flags"]
      ),
      "cross_region_semantic_hold_count": sum(
        1
        for row in rows
        if row["review_semantics"]
        in {
          "cross_region_semantic_hold",
          "cross_region_boundary_candidate_review_only",
        }
      ),
      "candidate_surface_component_count": sum(
        1
        for row in rows
        if row["review_status"] == "candidate_surface_component"
      ),
      "review_status": "manual_review_required",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review every surface component with old internal components that are drifted or sign-mismatched before runtime use.",
      },
      {
        "priority": "high",
        "question": "Add explicit canopy, intake, and horizontal-tail runtime component links if their surface damage should affect flight or sensors.",
      },
      {
        "priority": "medium",
        "question": "Use this report as the handoff table from outer-shape hits to component-damage propagation.",
      },
    ],
    "authority_boundary": {
      **mapping["authority_boundary"],
      "runtime_damage_model": False,
      "true_surface_component_boundaries": False,
    },
  }


def _semantic_damage_volume_rule(region_id: str, surface_role: str) -> dict[str, Any]:
  rule = SEMANTIC_DAMAGE_VOLUME_RULES.get(region_id)
  if rule is not None:
    return rule
  return {
    "semantic_component_id": f"semantic_{region_id}_volume",
    "volume_role": f"{surface_role}_volume",
    "runtime_system": "airframe_skin",
    "armor_mm": 3.0,
    "threshold_scale": 1.0,
  }


def _runtime_geometry_payload(proxy: dict[str, Any]) -> dict[str, Any]:
  payload: dict[str, Any] = {
    "primitive": proxy["proxy_kind"],
    "source": "a2_mesh_proxy_support_volume",
    "source_region_id": proxy["source_region_id"],
    "source_proxy_kind": proxy["proxy_kind"],
    "support_bounds": proxy["support_bounds"],
    "source_region_bounds": proxy["source_region_bounds"],
    "vertices_m": proxy["vertices_m"],
  }
  if "obb" in proxy:
    payload["obb"] = proxy["obb"]
  if "thin_prism" in proxy:
    payload["thin_prism"] = proxy["thin_prism"]
  if "convex_hull" in proxy:
    payload["convex_hull"] = proxy["convex_hull"]
  return payload


def _runtime_component_candidate(
  *,
  rule: dict[str, Any],
  row: dict[str, Any],
  proxy: dict[str, Any],
) -> dict[str, Any]:
  geometry = _runtime_geometry_payload(proxy)
  return {
    "name": rule["semantic_component_id"],
    "system": rule["runtime_system"],
    "offset": proxy["support_bounds"]["center"],
    "size": proxy["support_bounds"]["span"],
    "armor": rule["armor_mm"],
    "threshold_scale": rule["threshold_scale"],
    "geometry_primitive": proxy["proxy_kind"],
    "geometry": {
      **geometry,
      "surface_component_id": row["surface_component_id"],
      "volume_role": rule["volume_role"],
      "direct_receiver_components": row["clean_direct_component_names"],
      "cross_region_receiver_components": row[
        "cross_region_semantic_component_names"
      ],
      "runtime_projection_status": (
        "runtime_schema_parse_ready_candidate_not_activated"
      ),
    },
    "failure_modes": row["expected_damage_modes"],
    "dependencies": [
      {
        "system": rule["runtime_system"],
        "target_system": receiver,
        "edge_type": "semantic_surface_handoff_candidate",
        "scale": 0.35,
        "provenance": (
          "A2 target-geometry semantic volume handoff candidate; "
          "mesh-proxy review geometry, non-authoritative"
        ),
      }
      for receiver in row["clean_direct_component_names"]
    ],
    "redundancy_group_id": rule["semantic_component_id"],
    "redundancy_group": 0.0,
    "redundancy_weight": 0.35,
    "critical": False,
  }


def _semantic_receiver_handoff_status(row: dict[str, Any]) -> str:
  if row["blocked_component_names"] or row["bad_geometry_component_names"]:
    return "blocked_receiver_review_required"
  if row["cross_region_semantic_component_names"]:
    return "direct_receivers_parse_ready_cross_region_receivers_held"
  if row["clean_direct_component_names"]:
    return "direct_receivers_parse_ready"
  return "no_direct_receiver_review_required"


def build_semantic_damage_geometry_candidate(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  surface_report: dict[str, Any],
) -> dict[str, Any]:
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows: list[dict[str, Any]] = []
  for row in surface_report["rows"]:
    region_id = row["source_region_id"]
    proxy = proxies_by_region[region_id]
    rule = _semantic_damage_volume_rule(region_id, row["surface_role"])
    geometry = _runtime_geometry_payload(proxy)
    handoff_status = _semantic_receiver_handoff_status(row)
    rows.append(
      {
        "semantic_component_id": rule["semantic_component_id"],
        "surface_component_id": row["surface_component_id"],
        "source_region_id": region_id,
        "source_region_role": row["source_region_role"],
        "surface_role": row["surface_role"],
        "volume_component_role": rule["volume_role"],
        "runtime_system": rule["runtime_system"],
        "geometry_primitive": proxy["proxy_kind"],
        "source_proxy_kind": proxy["proxy_kind"],
        "support_bounds": proxy["support_bounds"],
        "source_region_bounds": proxy["source_region_bounds"],
        "mesh_source_nodes": row["mesh_source_nodes"],
        "mesh_region_vertex_count": row["mesh_region_vertex_count"],
        "mesh_silhouette_hulls": proxy["mesh_derived_review_geometry"]["hulls"],
        "runtime_geometry": geometry,
        "direct_receiver_components": row["clean_direct_component_names"],
        "direct_receiver_count": len(row["clean_direct_component_names"]),
        "cross_region_receiver_components": row[
          "cross_region_semantic_component_names"
        ],
        "cross_region_receiver_count": len(
          row["cross_region_semantic_component_names"]
        ),
        "blocked_receiver_components": row["blocked_component_names"],
        "bad_geometry_receiver_components": row["bad_geometry_component_names"],
        "expected_damage_modes": row["expected_damage_modes"],
        "surface_review_status": row["review_status"],
        "surface_review_semantics": row["review_semantics"],
        "surface_review_flags": row["review_flags"],
        "receiver_handoff_status": handoff_status,
        "runtime_projection_status": (
          "runtime_schema_parse_ready_candidate_not_activated"
        ),
        "runtime_component_json_candidate": _runtime_component_candidate(
          rule=rule,
          row=row,
          proxy=proxy,
        ),
        "authority_boundary": (
          "semantic_mesh_proxy_volume_candidate_not_active_runtime_damage_model"
        ),
      }
    )

  return {
    "schema_version": SEMANTIC_DAMAGE_GEOMETRY_SCHEMA_VERSION,
    "status": "semantic_damage_geometry_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_mapping_schema_version": mapping["schema_version"],
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "source_surface_component_schema_version": surface_report["schema_version"],
    "summary": {
      "semantic_volume_component_count": len(rows),
      "runtime_parse_ready_component_count": len(rows),
      "runtime_active_component_count": 0,
      "direct_receiver_component_reference_count": sum(
        row["direct_receiver_count"] for row in rows
      ),
      "cross_region_receiver_reference_count": sum(
        row["cross_region_receiver_count"] for row in rows
      ),
      "cross_region_handoff_held_count": sum(
        1
        for row in rows
        if row["receiver_handoff_status"]
        == "direct_receivers_parse_ready_cross_region_receivers_held"
      ),
      "blocked_receiver_count": sum(
        len(row["blocked_receiver_components"]) for row in rows
      ),
      "bad_geometry_receiver_count": sum(
        len(row["bad_geometry_receiver_components"]) for row in rows
      ),
      "geometry_primitive_counts": {
        primitive: sum(1 for row in rows if row["geometry_primitive"] == primitive)
        for primitive in sorted({row["geometry_primitive"] for row in rows})
      },
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review each semantic volume page before copying runtime_component_json_candidate into an active unit damage model.",
      },
      {
        "priority": "high",
        "question": "Keep engine_core and wing_spar_center cross-region receiver ownership held until split or explicitly accepted.",
      },
      {
        "priority": "medium",
        "question": "Use runtime_geometry.support_bounds plus primitive/source fields as the first parse-ready handoff from shell geometry to component damage.",
      },
    ],
    "authority_boundary": {
      **mapping["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_schema_parse_ready_candidate": True,
      "runtime_active_component": False,
      "true_surface_component_boundaries": False,
      "true_internal_component_geometry": False,
    },
  }
