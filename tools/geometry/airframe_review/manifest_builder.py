"""Manifest builder for airframe geometry review assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import filesystem, gltf_io
from tools.geometry.airframe_review.constants import (
  DEFAULT_AIRCRAFT,
  DEFAULT_AUDIT_SCENE,
  DEFAULT_GENERATED_ON,
  DEFAULT_INTAKE_METADATA,
  DEFAULT_REGISTRY,
  DEFAULT_VISUAL_GLB,
  REPO_ROOT,
  SCHEMA_VERSION,
)
from tools.geometry.airframe_review.primitives import Bounds, _round


def _find_registry_entry(registry: dict[str, Any], visual_glb: Path, repo_root: Path) -> dict[str, Any]:
  expected_suffix = "/" + filesystem.display_path(visual_glb, repo_root).split("examples/viz/web_viz/", 1)[-1]
  expected_suffix = expected_suffix.replace("/static/", "/static/")
  for entry in registry.get("entries", []):
    asset_path = entry.get("visual", {}).get("asset_path", "")
    if asset_path and asset_path.endswith(visual_glb.name):
      return entry
    if asset_path == expected_suffix:
      return entry
  return {}


def _hitbox_envelope(hitboxes: list[dict[str, Any]]) -> dict[str, Any]:
  bounds = Bounds.empty()
  component_count = 0
  systems: set[str] = set()
  for hitbox in hitboxes:
    offset = [float(value) for value in hitbox["offset"]]
    size = [float(value) for value in hitbox["size"]]
    for axis in range(3):
      bounds.minimum[axis] = min(bounds.minimum[axis], offset[axis] - size[axis] / 2.0)
      bounds.maximum[axis] = max(bounds.maximum[axis], offset[axis] + size[axis] / 2.0)
    systems.update(str(system) for system in hitbox.get("systems", []))
    components = hitbox.get("components", [])
    component_count += len(components)
    for component in components:
      if "system" in component:
        systems.add(str(component["system"]))
  return {
    "hitbox_count": len(hitboxes),
    "component_count": component_count,
    "systems": sorted(systems),
    "combined_envelope": bounds.to_record(),
  }


def _percent_error(actual: float, expected: float) -> float:
  if expected == 0.0:
    return 0.0
  return ((actual - expected) / expected) * 100.0


def _source_metadata(intake_metadata: dict[str, Any]) -> dict[str, Any]:
  user = intake_metadata.get("user", {})
  license_record = intake_metadata.get("license", {})
  return {
    "title": intake_metadata.get("name", ""),
    "uid": intake_metadata.get("uid", ""),
    "viewer_url": intake_metadata.get("viewerUrl", ""),
    "author": user.get("displayName", ""),
    "author_profile": user.get("profileUrl", ""),
    "license": {
      "label": license_record.get("label", ""),
      "full_name": license_record.get("fullName", ""),
      "url": license_record.get("url", ""),
      "requirements": license_record.get("requirements", ""),
    },
    "created_at": intake_metadata.get("createdAt", ""),
    "published_at": intake_metadata.get("publishedAt", ""),
    "downloaded_at": intake_metadata.get("downloadedAt", ""),
  }


def build_airframe_geometry_manifest(
  *,
  aircraft_path: Path = DEFAULT_AIRCRAFT,
  audit_scene_path: Path = DEFAULT_AUDIT_SCENE,
  visual_glb_path: Path = DEFAULT_VISUAL_GLB,
  intake_metadata_path: Path = DEFAULT_INTAKE_METADATA,
  registry_path: Path = DEFAULT_REGISTRY,
  repo_root: Path = REPO_ROOT,
  generated_on: str = DEFAULT_GENERATED_ON,
) -> dict[str, Any]:
  aircraft = gltf_io.load_json(aircraft_path)
  intake_metadata = gltf_io.load_json(intake_metadata_path)
  registry = gltf_io.load_json(registry_path)
  gltf_summary = gltf_io.summarize_gltf_scene(audit_scene_path)
  registry_entry = _find_registry_entry(registry, visual_glb_path, repo_root)

  public_dimensions = {
    "length_m": float(aircraft["airframe"]["length_m"]),
    "wingspan_m": float(aircraft["airframe"]["wingspan_m"]),
    "height_m": float(aircraft["airframe"]["height_m"]),
    "reference_area_m2": float(aircraft["airframe"]["reference_area"]),
  }
  transformed_span = gltf_summary["transformed_bounds"]["span"]
  registry_scale = float(registry_entry.get("visual", {}).get("scale", 1.0))
  length_fit_scale = public_dimensions["length_m"] / transformed_span[2]
  scaled_review_dimensions = {
    "length_m": transformed_span[2] * registry_scale,
    "wingspan_m": transformed_span[0] * registry_scale,
    "height_m": transformed_span[1] * registry_scale,
  }
  dimension_errors = {
    key: _round(_percent_error(scaled_review_dimensions[key], public_dimensions[key]))
    for key in ("length_m", "wingspan_m", "height_m")
  }

  hitbox_summary = _hitbox_envelope(aircraft.get("damage_model", {}).get("hitboxes", []))
  hitbox_span = hitbox_summary["combined_envelope"]["span"]

  manifest = {
    "schema_version": SCHEMA_VERSION,
    "status": "target_geometry_manifest_generated_review_only",
    "generated_on": generated_on,
    "asset_source_status": "verified_redistributable_visual_reference",
    "review_scope": "f16c_outer_shape_scale_axis_manifest_only",
    "source": _source_metadata(intake_metadata),
    "source_geometry_hints": {
      "face_count": intake_metadata.get("faceCount"),
      "vertex_count": intake_metadata.get("vertexCount"),
      "metadata_notable_node_names": intake_metadata.get("localGeometrySummary", {}).get(
        "notableNodeNames", []
      ),
      "metadata_scene": intake_metadata.get("localGeometrySummary", {}).get("scene", ""),
      "note": (
        "The retained glTF scene may use generic Object_* node names; source "
        "metadata hints are review aids and must not be treated as true "
        "component boundaries."
      ),
    },
    "paths": {
      "aircraft_database": filesystem.display_path(aircraft_path, repo_root),
      "runtime_visual_glb": filesystem.display_path(visual_glb_path, repo_root),
      "audit_scene_gltf": filesystem.display_path(audit_scene_path, repo_root),
      "intake_metadata": filesystem.display_path(intake_metadata_path, repo_root),
      "registry": filesystem.display_path(registry_path, repo_root),
    },
    "file_hashes": {
      "runtime_visual_glb_sha256": filesystem.sha256_file(visual_glb_path),
      "audit_scene_gltf_sha256": filesystem.sha256_file(audit_scene_path),
      "intake_metadata_sha256": filesystem.sha256_file(intake_metadata_path),
      "aircraft_database_sha256": filesystem.sha256_file(aircraft_path),
    },
    "registry_entry": {
      "id": registry_entry.get("id", ""),
      "label": registry_entry.get("label", ""),
      "asset_path": registry_entry.get("visual", {}).get("asset_path", ""),
      "scale": registry_scale,
      "yaw_correction_deg": registry_entry.get("visual", {}).get("yaw_correction_deg", 0.0),
      "realism_note": registry_entry.get("realism_note", ""),
    },
    "gltf_summary": gltf_summary,
    "axis_alignment": {
      "convention": "project_review_axis_map_v1",
      "asset_x": "sim_right",
      "asset_y": "sim_up",
      "asset_z_negative": "sim_forward",
      "nose_direction": "negative_asset_z",
      "tail_engine_direction": "positive_asset_z",
      "yaw_correction_deg": registry_entry.get("visual", {}).get("yaw_correction_deg", 0.0),
      "runtime_registry_scale": registry_scale,
    },
    "public_dimension_check": {
      "public_dimensions": public_dimensions,
      "asset_transformed_span": {
        "asset_x_right_span": _round(transformed_span[0]),
        "asset_y_up_span": _round(transformed_span[1]),
        "asset_z_forward_length_span": _round(transformed_span[2]),
      },
      "length_fit_scale": _round(length_fit_scale),
      "registry_scale": registry_scale,
      "scale_delta_percent": _round(_percent_error(registry_scale, length_fit_scale)),
      "scaled_review_dimensions": {
        key: _round(value) for key, value in scaled_review_dimensions.items()
      },
      "scaled_dimension_error_percent": dimension_errors,
      "scale_basis": "registry_scale_matches_public_length_order_and_preserves_frontend_visual_size",
    },
    "current_damage_geometry": {
      "source": "damage_model.hitboxes",
      "summary": hitbox_summary,
      "public_dimension_error_percent": {
        "length_m": _round(_percent_error(hitbox_span[0], public_dimensions["length_m"])),
        "wingspan_m": _round(_percent_error(hitbox_span[1], public_dimensions["wingspan_m"])),
        "height_m": _round(_percent_error(hitbox_span[2], public_dimensions["height_m"])),
      },
      "known_gap": "current_axis_aligned_hitboxes_cover_core_damage_scaffold_but_understate_full_aircraft_height",
    },
    "authority_boundary": {
      "runtime_collision_mesh": False,
      "true_f16_engineering_geometry": False,
      "true_internal_component_boundaries": False,
      "real_weapon_pk_authority": False,
      "structural_breakup_or_debris_claim": False,
      "allowed_use": [
        "outer_shape_review",
        "scale_and_axis_audit",
        "component_binding_review_input",
        "test_point_distance_diagnostic_input",
      ],
    },
  }
  return manifest
