"""Outer-region geometry mapping builder for airframe review."""

from __future__ import annotations

from typing import Any

from tools.geometry.airframe_review import asset_projection, bounds_ops
from tools.geometry.airframe_review.constants import (
  CURATED_MESH_SILHOUETTE_SOURCE_NODES,
  MAPPING_SCHEMA_VERSION,
)
from tools.geometry.airframe_review.primitives import _round


def _mesh_node_sim_bounds_by_name(manifest: dict[str, Any]) -> dict[str, dict[str, list[float]]]:
  asset_center = manifest["gltf_summary"]["transformed_bounds"]["center"]
  scale = float(manifest["public_dimension_check"]["registry_scale"])
  return {
    mesh_node["node_name"]: asset_projection.sim_bounds_from_asset_bounds(
      mesh_node["bounds"], asset_center=asset_center, scale=scale
    )
    for mesh_node in manifest["gltf_summary"]["mesh_node_bounds"]
  }


def _curated_mesh_bounds(
  manifest: dict[str, Any],
  *,
  node_names: list[str],
  margins_m: list[float],
) -> dict[str, list[float]]:
  bounds_by_name = _mesh_node_sim_bounds_by_name(manifest)
  missing = [node_name for node_name in node_names if node_name not in bounds_by_name]
  if missing:
    raise ValueError(
      "Curated mesh geometry source nodes are missing from the audit scene: "
      + ", ".join(missing)
    )
  return bounds_ops.pad_bounds(
    bounds_ops.merge_bounds(bounds_by_name[node_name] for node_name in node_names),
    margins_m,
  )


def _mesh_node_candidates(
  manifest: dict[str, Any],
  region_bounds: dict[str, list[float]],
  *,
  limit: int = 6,
) -> list[dict[str, Any]]:
  asset_center = manifest["gltf_summary"]["transformed_bounds"]["center"]
  scale = float(manifest["public_dimension_check"]["registry_scale"])
  scored: list[dict[str, Any]] = []
  region_volume = max(bounds_ops.volume(region_bounds), 1e-9)
  for mesh_node in manifest["gltf_summary"]["mesh_node_bounds"]:
    sim_bounds = asset_projection.sim_bounds_from_asset_bounds(
      mesh_node["bounds"], asset_center=asset_center, scale=scale
    )
    intersection = bounds_ops.intersection_bounds(region_bounds, sim_bounds)
    if intersection is None:
      continue
    intersection_volume = bounds_ops.volume(intersection)
    node_volume = max(bounds_ops.volume(sim_bounds), 1e-9)
    scored.append(
      {
        "node_name": mesh_node["node_name"],
        "mesh_name": mesh_node["mesh_name"],
        "triangle_count": mesh_node["triangle_count"],
        "coverage_fraction_of_region_box": _round(intersection_volume / region_volume, 5),
        "coverage_fraction_of_node_box": _round(intersection_volume / node_volume, 5),
        "sim_bounds": sim_bounds,
      }
    )
  scored.sort(
    key=lambda row: (
      row["coverage_fraction_of_node_box"],
      row["coverage_fraction_of_region_box"],
      row["triangle_count"],
    ),
    reverse=True,
  )
  return scored[:limit]


def _region_record(
  *,
  region_id: str,
  label: str,
  role: str,
  minimum: list[float],
  maximum: list[float],
  rationale: str,
  manifest: dict[str, Any],
  mesh_silhouette_source_nodes: list[str] | None = None,
  source_basis: str = "scaled_outer_envelope_fraction_plus_manual_review_seed",
) -> dict[str, Any]:
  bounds = bounds_ops.bounds_from_min_max(minimum, maximum)
  record: dict[str, Any] = {
    "id": region_id,
    "label": label,
    "role": role,
    "bounds_kind": "review_aabb_sim_m",
    "bounds": bounds,
    "source_basis": source_basis,
    "source_mesh_node_candidates": _mesh_node_candidates(manifest, bounds),
    "confidence": "low_initial_review_candidate",
    "manual_review_required": True,
    "rationale": rationale,
  }
  if mesh_silhouette_source_nodes:
    record["mesh_silhouette_source_nodes"] = mesh_silhouette_source_nodes
  return record


def _outer_region_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
  dims = manifest["public_dimension_check"]["scaled_review_dimensions"]
  half_length = float(dims["length_m"]) / 2.0
  half_width = float(dims["wingspan_m"]) / 2.0
  half_height = float(dims["height_m"]) / 2.0
  fuselage_half_width = min(0.85, half_width * 0.18)
  nose_half_width = min(0.48, half_width * 0.10)
  source_nodes = CURATED_MESH_SILHOUETTE_SOURCE_NODES
  mesh_aligned_source = "curated_audit_mesh_node_bounds_plus_manual_review_margin"
  nose_bounds = bounds_ops.bounds_from_min_max(
    [0.67 * half_length, -nose_half_width, -0.42 * half_height],
    [half_length, nose_half_width, -0.15 * half_height],
  )
  canopy_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["canopy"],
    margins_m=[0.05, 0.06, 0.05],
  )
  intake_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["intake"],
    margins_m=[0.08, 0.07, 0.08],
  )
  aft_engine_bounds = bounds_ops.bounds_from_min_max(
    [-0.78 * half_length, -0.90, -0.54 * half_height],
    [-0.20 * half_length, 0.90, 0.15 * half_height],
  )
  engine_nozzle_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["engine_nozzle"],
    margins_m=[0.10, 0.06, 0.10],
  )
  left_wing_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["left_wing"],
    margins_m=[0.07, 0.17, 0.04],
  )
  right_wing_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["right_wing"],
    margins_m=[0.07, 0.17, 0.04],
  )
  left_wing_root_bounds = bounds_ops.bounds_from_min_max(
    [-0.38 * half_length, -1.45, -0.48 * half_height],
    [0.09 * half_length, -0.25, -0.13 * half_height],
  )
  right_wing_root_bounds = bounds_ops.bounds_from_min_max(
    [-0.38 * half_length, 0.25, -0.48 * half_height],
    [0.09 * half_length, 1.45, -0.13 * half_height],
  )
  left_horizontal_tail_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["left_horizontal_tail"],
    margins_m=[0.07, 0.07, 0.05],
  )
  right_horizontal_tail_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["right_horizontal_tail"],
    margins_m=[0.07, 0.07, 0.05],
  )
  vertical_tail_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["vertical_tail"],
    margins_m=[0.03, 0.33, 0.08],
  )

  return [
    _region_record(
      region_id="nose_radome",
      label="nose_radome",
      role="outer_skin",
      minimum=nose_bounds["min"],
      maximum=nose_bounds["max"],
      rationale="Forward-most narrow body area; height corrected from audit mesh nose slice instead of expanded selection.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["nose_radome"],
      source_basis="audit_mesh_aligned_nose_slice_plus_public_length_scale",
    ),
    _region_record(
      region_id="forward_fuselage",
      label="forward_fuselage",
      role="outer_skin",
      minimum=[0.30 * half_length, -fuselage_half_width, -0.34 * half_height],
      maximum=[0.72 * half_length, fuselage_half_width, 0.36 * half_height],
      rationale="Forward fuselage and avionics/cockpit support area; covers the old 4 m/6 m nose test zone.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["forward_fuselage"],
    ),
    _region_record(
      region_id="canopy",
      label="canopy",
      role="raised_outer_skin",
      minimum=canopy_bounds["min"],
      maximum=canopy_bounds["max"],
      rationale="Canopy candidate aligned to the audit mesh canopy nodes; kept separate because old hitboxes understate shape.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["canopy"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="center_fuselage",
      label="center_fuselage",
      role="outer_skin",
      minimum=[-0.25 * half_length, -fuselage_half_width, -0.34 * half_height],
      maximum=[0.32 * half_length, fuselage_half_width, 0.34 * half_height],
      rationale="Main body core around fuel, avionics, and flight-control components.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["center_fuselage"],
    ),
    _region_record(
      region_id="intake",
      label="intake",
      role="outer_skin",
      minimum=intake_bounds["min"],
      maximum=intake_bounds["max"],
      rationale="Lower intake candidate aligned to the audit mesh intake nodes for underside proximity review.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["intake"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="aft_fuselage_engine",
      label="aft_fuselage_engine",
      role="outer_skin",
      minimum=aft_engine_bounds["min"],
      maximum=aft_engine_bounds["max"],
      rationale="Aft fuselage and engine bay candidate for tail-aspect blast/fragment review.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["aft_fuselage_engine"],
      source_basis="audit_mesh_aligned_aft_body_slice_plus_public_length_scale",
    ),
    _region_record(
      region_id="engine_nozzle",
      label="engine_nozzle",
      role="outer_skin",
      minimum=engine_nozzle_bounds["min"],
      maximum=engine_nozzle_bounds["max"],
      rationale="Rear nozzle candidate aligned to the audit mesh nozzle node for tail-on shot diagnostics.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["engine_nozzle"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="left_wing",
      label="left_wing",
      role="lifting_surface",
      minimum=left_wing_bounds["min"],
      maximum=left_wing_bounds["max"],
      rationale="Left wing lifting surface aligned to the audit mesh wing nodes; sign naming remains review-only.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["left_wing"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="right_wing",
      label="right_wing",
      role="lifting_surface",
      minimum=right_wing_bounds["min"],
      maximum=right_wing_bounds["max"],
      rationale="Right wing lifting surface aligned to the audit mesh wing nodes; sign naming remains review-only.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["right_wing"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="left_wing_root",
      label="left_wing_root",
      role="structural_transition",
      minimum=left_wing_root_bounds["min"],
      maximum=left_wing_root_bounds["max"],
      rationale="Left wing root transition corrected toward the audit mesh wing plane; useful for grazing-warhead review.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["left_wing_root"],
      source_basis="audit_mesh_aligned_wing_root_slice_plus_public_length_scale",
    ),
    _region_record(
      region_id="right_wing_root",
      label="right_wing_root",
      role="structural_transition",
      minimum=right_wing_root_bounds["min"],
      maximum=right_wing_root_bounds["max"],
      rationale="Right wing root transition corrected toward the audit mesh wing plane; mirrored from left wing root candidate.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["right_wing_root"],
      source_basis="audit_mesh_aligned_wing_root_slice_plus_public_length_scale",
    ),
    _region_record(
      region_id="left_horizontal_tail",
      label="left_horizontal_tail",
      role="tail_surface",
      minimum=left_horizontal_tail_bounds["min"],
      maximum=left_horizontal_tail_bounds["max"],
      rationale="Left horizontal tail candidate aligned to audit mesh tail-plane nodes for aft control-surface exposure.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["left_horizontal_tail"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="right_horizontal_tail",
      label="right_horizontal_tail",
      role="tail_surface",
      minimum=right_horizontal_tail_bounds["min"],
      maximum=right_horizontal_tail_bounds["max"],
      rationale="Right horizontal tail candidate aligned to audit mesh tail-plane nodes for aft control-surface exposure.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["right_horizontal_tail"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="vertical_tail",
      label="vertical_tail",
      role="tail_surface",
      minimum=vertical_tail_bounds["min"],
      maximum=vertical_tail_bounds["max"],
      rationale="Vertical tail candidate; separated because old damage boxes omit most aircraft height.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["vertical_tail"],
      source_basis=mesh_aligned_source,
    ),
  ]


def build_geometry_mapping_candidate(manifest: dict[str, Any]) -> dict[str, Any]:
  regions = _outer_region_records(manifest)
  return {
    "schema_version": MAPPING_SCHEMA_VERSION,
    "status": "outer_region_candidate_generated_review_only",
    "generated_on": manifest["generated_on"],
    "asset_ref": {
      "source_uid": manifest["source"]["uid"],
      "runtime_visual_glb": manifest["paths"]["runtime_visual_glb"],
      "audit_scene_gltf": manifest["paths"]["audit_scene_gltf"],
      "manifest_schema_version": manifest["schema_version"],
    },
    "coordinate_frame": {
      "frame": "sim_local_m_review",
      "x_positive": "nose_forward",
      "y_positive": "right_or_left_by_project_sign_review_only",
      "z_positive": "up",
      "source_axis_map": manifest["axis_alignment"],
      "origin": "center_of_audit_asset_transformed_bounds_after_registry_scale",
    },
    "outer_envelope": {
      "bounds_kind": "review_aabb_sim_m",
      "bounds": asset_projection.sim_bounds_from_asset_bounds(
        manifest["gltf_summary"]["transformed_bounds"],
        asset_center=manifest["gltf_summary"]["transformed_bounds"]["center"],
        scale=float(manifest["public_dimension_check"]["registry_scale"]),
      ),
      "scaled_review_dimensions": manifest["public_dimension_check"][
        "scaled_review_dimensions"
      ],
    },
    "mesh_node_name_quality": {
      "actual_scene_node_pattern": "generic_Object_nodes",
      "semantic_hints_from_intake_metadata": manifest["source_geometry_hints"][
        "metadata_notable_node_names"
      ],
      "decision": "do_not_auto_classify_regions_from_node_names_only",
    },
    "outer_regions": regions,
    "legacy_damage_geometry_overlay": manifest["current_damage_geometry"]["summary"],
    "manual_review_queue": [
      {
        "question": "Do the generated nose and forward-fuselage regions cover the 4 m and 6 m nose test points without creating a hard edge?",
        "priority": "high",
      },
      {
        "question": "Do canopy, intake, and vertical-tail regions correct the legacy hitbox height gap without overstating true internal component boundaries?",
        "priority": "high",
      },
      {
        "question": "Are left/right wing signs aligned with the runtime local-coordinate convention before component binding?",
        "priority": "medium",
      },
    ],
    "authority_boundary": manifest["authority_boundary"],
  }
