"""Fine geometry proxy candidate builders for airframe review."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import asset_projection, bounds_ops, contours
from tools.geometry.airframe_review.constants import (
  FINE_PROXY_KIND_BY_REGION,
  FINE_PROXY_SCHEMA_VERSION,
  REPO_ROOT,
  SILHOUETTE_VIEW_AXES,
)
from tools.geometry.airframe_review.primitives import _round, _round_vec


def _resize_bounds_about_center(
  bounds: dict[str, list[float]],
  factors: list[float],
) -> dict[str, list[float]]:
  center = bounds["center"]
  span = bounds["span"]
  minimum = [
    center[index] - span[index] * factors[index] / 2.0 for index in range(3)
  ]
  maximum = [
    center[index] + span[index] * factors[index] / 2.0 for index in range(3)
  ]
  return bounds_ops.bounds_from_min_max(minimum, maximum)


def _bounds_corners(bounds: dict[str, list[float]]) -> list[list[float]]:
  return [
    _round_vec([x, y, z])
    for x in (bounds["min"][0], bounds["max"][0])
    for y in (bounds["min"][1], bounds["max"][1])
    for z in (bounds["min"][2], bounds["max"][2])
  ]


def _mesh_silhouette_for_region(
  region: dict[str, Any],
  sim_vertex_records: list[dict[str, Any]],
) -> dict[str, Any]:
  source_node_names = set(region.get("mesh_silhouette_source_nodes", []))
  candidate_records = [
    record
    for record in sim_vertex_records
    if not source_node_names or record["node_name"] in source_node_names
  ]
  selection_bounds = region["bounds"]
  selected_records = [
    record
    for record in candidate_records
    if bounds_ops.contains_point(selection_bounds, record["point_m"])
  ]
  selected = [record["point_m"] for record in selected_records]
  hulls: dict[str, Any] = {}
  for view, axes in SILHOUETTE_VIEW_AXES.items():
    projected = [(vertex[axes[0]], vertex[axes[1]]) for vertex in selected]
    hull = contours.convex_hull_2d(projected)
    hulls[view] = {
      "axes": ["xyz"[axes[0]], "xyz"[axes[1]]],
      "point_count": len(hull),
      "points_m": hull,
    }

  status = "mesh_silhouette_extracted_from_curated_mesh_nodes"
  if not source_node_names:
    status = "mesh_silhouette_extracted_from_region_bounds"
  if len(selected) < 3 or any(hull["point_count"] < 3 for hull in hulls.values()):
    status = "insufficient_region_vertices_for_closed_silhouette"
  node_counts: dict[str, int] = {}
  for record in selected_records:
    node_counts[record["node_name"]] = node_counts.get(record["node_name"], 0) + 1
  return {
    "status": status,
    "source": "audit_gltf_vertices_filtered_by_curated_mesh_nodes_and_region_bounds",
    "source_vertex_count": len(sim_vertex_records),
    "candidate_vertex_count": len(candidate_records),
    "region_vertex_count": len(selected),
    "selection_strategy": "curated_mesh_node_whitelist_and_source_region_bounds",
    "fallback_policy": "disabled_no_bounds_expansion",
    "source_node_names": sorted(source_node_names),
    "selected_node_vertex_counts": dict(sorted(node_counts.items())),
    "selection_bounds": selection_bounds,
    "hulls": hulls,
  }


def _fine_proxy_support_bounds(region: dict[str, Any], proxy_kind: str) -> dict[str, list[float]]:
  region_id = region["id"]
  bounds = region["bounds"]
  if proxy_kind == "thin_prism":
    if region_id == "vertical_tail":
      return _resize_bounds_about_center(bounds, [0.90, 0.24, 0.96])
    return _resize_bounds_about_center(bounds, [0.94, 0.88, 0.36])
  if proxy_kind == "convex_hull":
    factors_by_region = {
      "nose_radome": [0.92, 0.58, 0.72],
      "canopy": [0.82, 0.76, 0.82],
      "intake": [0.84, 0.70, 0.76],
      "left_wing_root": [0.84, 0.72, 0.72],
      "right_wing_root": [0.84, 0.72, 0.72],
    }
    return _resize_bounds_about_center(
      bounds,
      factors_by_region.get(region_id, [0.86, 0.70, 0.74]),
    )
  if region_id == "engine_nozzle":
    return _resize_bounds_about_center(bounds, [0.90, 0.78, 0.84])
  return _resize_bounds_about_center(bounds, [0.96, 0.88, 0.88])


def _convex_proxy_vertices(
  region_id: str,
  support_bounds: dict[str, list[float]],
) -> list[list[float]]:
  bounds = support_bounds
  min_x, min_y, min_z = bounds["min"]
  max_x, max_y, max_z = bounds["max"]
  center = bounds["center"]
  if region_id == "nose_radome":
    return [
      _round_vec([max_x, center[1], center[2]]),
      _round_vec([min_x, min_y, min_z]),
      _round_vec([min_x, min_y, max_z]),
      _round_vec([min_x, max_y, min_z]),
      _round_vec([min_x, max_y, max_z]),
      _round_vec([(min_x + max_x) / 2.0, center[1], min_z]),
      _round_vec([(min_x + max_x) / 2.0, center[1], max_z]),
    ]
  if region_id == "canopy":
    return [
      _round_vec([min_x, min_y, min_z]),
      _round_vec([min_x, max_y, min_z]),
      _round_vec([max_x, min_y, min_z]),
      _round_vec([max_x, max_y, min_z]),
      _round_vec([min_x + (max_x - min_x) * 0.35, center[1], max_z]),
      _round_vec([min_x + (max_x - min_x) * 0.75, center[1], max_z * 0.98]),
    ]
  return _bounds_corners(bounds)


def _fine_proxy_record(
  region: dict[str, Any],
  *,
  sim_vertex_records: list[dict[str, Any]],
) -> dict[str, Any]:
  region_id = region["id"]
  proxy_kind = FINE_PROXY_KIND_BY_REGION.get(region_id, "obb")
  source_bounds = region["bounds"]
  support_bounds = _fine_proxy_support_bounds(region, proxy_kind)
  support_span = support_bounds["span"]
  source_volume = bounds_ops.volume(source_bounds)
  support_volume = bounds_ops.volume(support_bounds)
  record: dict[str, Any] = {
    "source_region_id": region_id,
    "source_region_role": region["role"],
    "proxy_kind": proxy_kind,
    "source_basis": "review_mapping_plus_audit_mesh_silhouette_candidate",
    "source_region_bounds": source_bounds,
    "support_bounds": support_bounds,
    "mesh_derived_review_geometry": _mesh_silhouette_for_region(
      region, sim_vertex_records
    ),
    "vertices_m": (
      _convex_proxy_vertices(region_id, support_bounds)
      if proxy_kind == "convex_hull"
      else _bounds_corners(support_bounds)
    ),
    "fit_metrics": {
      "source_aabb_volume_m3": _round(source_volume),
      "proxy_support_volume_m3": _round(support_volume),
      "aabb_volume_ratio": _round(support_volume / max(source_volume, 1e-9), 5),
      "max_support_surface_inset_m": _round(
        max(
          (source_bounds["span"][axis] - support_span[axis]) / 2.0
          for axis in range(3)
        )
      ),
    },
    "runtime_allowed_use": [
      "distance_diagnostic_candidate",
      "review_visualization_input",
    ],
    "runtime_prohibited_use": [
      "runtime_collision_mesh",
      "real_f16_engineering_geometry",
      "true_internal_component_boundary",
      "real_weapon_pk",
      "structural_breakup_or_debris_claim",
    ],
    "review_status": "manual_review_required",
    "manual_review_notes": [
      "First-pass fine proxy for TG-P6 review only.",
      "Use support_bounds for distance sanity until a later audited hull or shell exists.",
    ],
  }
  if proxy_kind in {"obb", "thin_prism"}:
    record["obb"] = {
      "center_m": support_bounds["center"],
      "axes": [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
      ],
      "half_extents_m": _round_vec([value / 2.0 for value in support_span]),
    }
  if proxy_kind == "thin_prism":
    thin_axis = 1 if region_id == "vertical_tail" else 2
    record["thin_prism"] = {
      "thin_axis": ["x", "y", "z"][thin_axis],
      "nominal_thickness_m": _round(support_span[thin_axis]),
      "thickness_basis": "review_candidate_reduces_air_volume_from_outer_region_aabb",
    }
  if proxy_kind == "convex_hull":
    record["convex_hull"] = {
      "vertex_source": "simplified_review_support_points_not_raw_mesh_vertices",
      "vertex_count": len(record["vertices_m"]),
      "simplification_error_m": None,
    }
  if "wing" in region_id or "tail" in region_id:
    record["manual_review_notes"].append(
      "Left/right coordinate sign and thin-surface orientation remain explicit review items."
    )
  if region.get("mesh_silhouette_source_nodes"):
    record["manual_review_notes"].append(
      "Mesh-derived silhouette uses a curated audit-node whitelist; missing nodes fail review instead of using expanded bounds."
    )
  return record


def _rank_point_to_fine_proxies(
  point: list[float],
  fine_proxy: dict[str, Any],
) -> list[dict[str, Any]]:
  ranked: list[dict[str, Any]] = []
  for proxy in fine_proxy["proxies"]:
    distance = bounds_ops.point_box_distance(point, proxy["support_bounds"])
    ranked.append(
      {
        "source_region_id": proxy["source_region_id"],
        "proxy_kind": proxy["proxy_kind"],
        "distance_m": _round(distance),
        "contains_point": bounds_ops.contains_point(proxy["support_bounds"], point),
        "source_aabb_distance_m": _round(
          bounds_ops.point_box_distance(point, proxy["source_region_bounds"])
        ),
      }
    )
  ranked.sort(
    key=lambda row: (
      row["distance_m"],
      row["source_aabb_distance_m"],
      row["source_region_id"],
    )
  )
  return ranked


def build_fine_geometry_proxy_candidate(
  mapping: dict[str, Any],
  diagnostics: dict[str, Any],
  *,
  manifest: dict[str, Any] | None = None,
  audit_scene_path: Path | None = None,
) -> dict[str, Any]:
  sim_vertex_records: list[dict[str, Any]] = []
  sim_triangle_records: list[dict[str, Any]] = []
  if manifest is not None:
    if audit_scene_path is None:
      audit_scene_path = REPO_ROOT / manifest["paths"]["audit_scene_gltf"]
    sim_vertex_records = asset_projection.extract_gltf_sim_vertex_records(audit_scene_path, manifest)
    sim_triangle_records = asset_projection.extract_gltf_sim_triangle_records(audit_scene_path, manifest)
  proxies = [
    _fine_proxy_record(region, sim_vertex_records=sim_vertex_records)
    for region in mapping["outer_regions"]
  ]
  fine_proxy: dict[str, Any] = {
    "schema_version": FINE_PROXY_SCHEMA_VERSION,
    "status": "fine_geometry_proxy_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "outer_envelope": mapping["outer_envelope"],
    "source_mapping_schema_version": mapping["schema_version"],
    "proxies": proxies,
    "review_point_distance_deltas": [],
  }
  distance_rows: list[dict[str, Any]] = []
  for row in diagnostics["rows"]:
    point = [float(value) for value in row["point_m"]]
    rankings = _rank_point_to_fine_proxies(point, fine_proxy)
    nearest = rankings[0]
    distance_rows.append(
      {
        "point_id": row["point_id"],
        "aspect": row["aspect"],
        "point_m": row["point_m"],
        "nearest_source_aabb_region_id": row["nearest_outer_region_id"],
        "nearest_source_aabb_distance_m": row["nearest_outer_distance_m"],
        "nearest_fine_proxy_region_id": nearest["source_region_id"],
        "nearest_fine_proxy_kind": nearest["proxy_kind"],
        "nearest_fine_proxy_distance_m": nearest["distance_m"],
        "fine_minus_source_distance_delta_m": _round(
          nearest["distance_m"] - row["nearest_outer_distance_m"]
        ),
        "inside_fine_proxy_count": sum(1 for item in rankings if item["contains_point"]),
        "fine_proxy_rankings": rankings[:5],
        "authority_boundary": "review_only_distance_sanity_not_runtime_lethality_decision",
      }
    )
  kind_counts: dict[str, int] = {}
  for proxy in proxies:
    kind_counts[proxy["proxy_kind"]] = kind_counts.get(proxy["proxy_kind"], 0) + 1
  source_volume = sum(bounds_ops.volume(proxy["source_region_bounds"]) for proxy in proxies)
  support_volume = sum(bounds_ops.volume(proxy["support_bounds"]) for proxy in proxies)
  mesh_silhouette_count = sum(
    1
    for proxy in proxies
    if proxy["mesh_derived_review_geometry"]["status"].startswith(
      "mesh_silhouette_extracted"
    )
  )
  fine_proxy["summary"] = {
    "source_outer_region_count": len(mapping["outer_regions"]),
    "proxy_count": len(proxies),
    "held_region_count": len(proxies) - mesh_silhouette_count,
    "mesh_derived_silhouette_count": mesh_silhouette_count,
    "mesh_source_vertex_count": len(sim_vertex_records),
    "mesh_source_triangle_count": len(sim_triangle_records),
    "inflated_fallback_count": 0,
    "fallback_policy": "disabled_no_bounds_expansion",
    "proxy_kind_counts": kind_counts,
    "total_source_aabb_volume_m3": _round(source_volume),
    "total_proxy_support_volume_m3": _round(support_volume),
    "total_proxy_support_volume_ratio": _round(
      support_volume / max(source_volume, 1e-9),
      5,
    ),
    "review_point_count": len(distance_rows),
    "review_status": "manual_review_required",
  }
  fine_proxy["review_point_distance_deltas"] = distance_rows
  # Internal-only channel for the whole-airframe contour path. Not serialized;
  # downstream callers recompute the contour from these records so the glTF is
  # parsed once per packet generation.
  fine_proxy["_sim_vertex_records"] = sim_vertex_records
  fine_proxy["_sim_triangle_records"] = sim_triangle_records
  fine_proxy["manual_review_queue"] = [
    {
      "priority": "high",
      "question": "Confirm thin wing and tail proxies do not hide left/right coordinate sign issues.",
    },
    {
      "priority": "high",
      "question": "Review nose, canopy, and intake convex-hull candidates before any path intersection use.",
    },
    {
      "priority": "medium",
      "question": "Compare fine-minus-source distance deltas for nose, beam, above, and below points.",
    },
  ]
  fine_proxy["authority_boundary"] = mapping["authority_boundary"]
  return fine_proxy
