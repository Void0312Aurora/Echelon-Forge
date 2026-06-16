"""Semantic parent-child layout candidates for airframe review."""

from __future__ import annotations

from typing import Any

from tools.geometry.airframe_review.constants import (
  CROSS_REGION_REVIEW_SEMANTICS,
  SEMANTIC_PARENT_CHILD_LAYOUT_SCHEMA_VERSION,
)


def _child_prior_projection_role(index: int, child_count: int) -> str:
  if child_count <= 1:
    return "single_receiver_overlay"
  if index == 0:
    return "primary_receiver_overlay"
  return "extra_receiver_overlay"


def build_semantic_parent_child_layout_candidate(
  mapping: dict[str, Any],
  semantic_report: dict[str, Any],
  internal_prior_report: dict[str, Any],
  held_segment_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
  priors_by_region: dict[str, list[dict[str, Any]]] = {}
  for prior_row in internal_prior_report["rows"]:
    priors_by_region.setdefault(prior_row["bound_region_id"], []).append(prior_row)
  held_segments_by_parent: dict[str, list[dict[str, Any]]] = {}
  held_segments_by_owner_region: dict[str, list[dict[str, Any]]] = {}
  if held_segment_report is not None:
    for segment_row in held_segment_report["rows"]:
      held_segments_by_parent.setdefault(
        segment_row["parent_component_name"],
        [],
      ).append(segment_row)
      for owner_region_id in segment_row["owner_region_ids"]:
        held_segments_by_owner_region.setdefault(owner_region_id, []).append(
          segment_row
        )

  rows: list[dict[str, Any]] = []
  for semantic_row in semantic_report["rows"]:
    region_id = semantic_row["source_region_id"]
    child_priors = priors_by_region.get(region_id, [])
    child_count = len(child_priors)
    child_receiver_priors = []
    for index, prior_row in enumerate(child_priors):
      held_segments = held_segments_by_parent.get(
        prior_row["component_name"],
        [],
      )
      child_receiver_priors.append(
        {
          "component_name": prior_row["component_name"],
          "system": prior_row["system"],
          "component_role": prior_row["component_role"],
          "prior_shape": prior_row["prior_shape"],
          "prior_axis": prior_row["prior_axis"],
          "size_basis": prior_row["size_basis"],
          "size_evidence_level": prior_row["size_evidence_level"],
          "size_source_urls": prior_row["size_source_urls"],
          "nominal_dimensions_m": prior_row["nominal_dimensions_m"],
          "constraint_status": prior_row["constraint_status"],
          "component_review_semantics": prior_row["component_review_semantics"],
          "layout_role": _child_prior_projection_role(index, child_count),
          "is_cross_region_held": (
            prior_row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
          ),
          "constraint_region_ids": prior_row["constraint_region_ids"],
          "placement_bounds": prior_row["placement_bounds"],
          "placement_bounds_source": prior_row["placement_bounds_source"],
          "whole_airframe_bounds": prior_row["whole_airframe_bounds"],
          "constrained_geometry": prior_row["constrained_geometry"],
          "held_segments": held_segments,
          "held_segment_count": len(held_segments),
          "constraint_adjustment": prior_row["constraint_adjustment"],
          "runtime_projection_status": prior_row["runtime_projection_status"],
        }
      )
    child_names = {prior_row["component_name"] for prior_row in child_priors}
    cross_region_held_segment_overlays = [
      segment_row
      for segment_row in held_segments_by_owner_region.get(region_id, [])
      if segment_row["parent_component_name"] not in child_names
    ]
    rows.append(
      {
        "parent_semantic_component_id": semantic_row["semantic_component_id"],
        "parent_surface_component_id": semantic_row["surface_component_id"],
        "source_region_id": region_id,
        "volume_component_role": semantic_row["volume_component_role"],
        "geometry_primitive": semantic_row["geometry_primitive"],
        "source_proxy_kind": semantic_row["source_proxy_kind"],
        "support_bounds": semantic_row["support_bounds"],
        "source_region_bounds": semantic_row["source_region_bounds"],
        "whole_airframe_bounds": internal_prior_report["whole_airframe_bounds"],
        "parent_runtime_projection_status": semantic_row[
          "runtime_projection_status"
        ],
        "parent_receiver_handoff_status": semantic_row["receiver_handoff_status"],
        "bound_receiver_count": child_count,
        "extra_receiver_slot_count": max(child_count - 1, 0),
        "primary_receiver_component_name": (
          child_priors[0]["component_name"] if child_priors else ""
        ),
        "extra_receiver_component_names": [
          prior_row["component_name"] for prior_row in child_priors[1:]
        ],
        "cross_region_held_receiver_names": [
          prior_row["component_name"]
          for prior_row in child_priors
          if prior_row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
        ],
        "cross_region_held_segment_overlays": cross_region_held_segment_overlays,
        "cross_region_held_segment_overlay_count": len(
          cross_region_held_segment_overlays
        ),
        "child_receiver_priors": child_receiver_priors,
        "layout_policy": (
          "one_parent_semantic_shell_view_with_receiver_priors_overlaid"
        ),
        "runtime_projection_status": (
          "review_only_visual_layout_not_runtime_activation"
        ),
        "authority_boundary": (
          "display_grouping_only_parent_child_damage_ownership_not_accepted"
        ),
      }
    )

  return {
    "schema_version": SEMANTIC_PARENT_CHILD_LAYOUT_SCHEMA_VERSION,
    "status": "semantic_parent_child_layout_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_semantic_damage_geometry_schema_version": semantic_report[
      "schema_version"
    ],
    "source_internal_component_prior_schema_version": internal_prior_report[
      "schema_version"
    ],
    "source_cross_region_held_segment_schema_version": (
      held_segment_report["schema_version"] if held_segment_report else ""
    ),
    "summary": {
      "parent_semantic_component_count": len(rows),
      "bound_receiver_component_count": sum(
        row["bound_receiver_count"] for row in rows
      ),
      "extra_receiver_slot_count": sum(
        row["extra_receiver_slot_count"] for row in rows
      ),
      "parent_without_receiver_count": sum(
        1 for row in rows if row["bound_receiver_count"] == 0
      ),
      "cross_region_held_receiver_count": sum(
        len(row["cross_region_held_receiver_names"]) for row in rows
      ),
      "cross_region_held_segment_count": (
        held_segment_report["summary"]["held_segment_count"]
        if held_segment_report
        else 0
      ),
      "cross_region_held_segment_overlay_count": sum(
        row["cross_region_held_segment_overlay_count"] for row in rows
      ),
      "runtime_active_component_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review the 14 parent shell pages as the primary geometry surface; do not review the 26 receiver priors as independent top-level parts.",
      },
      {
        "priority": "high",
        "question": "Treat extra receiver slots as overlays inside the parent shell, not as accepted parent-child damage ownership.",
      },
      {
        "priority": "high",
        "question": "Keep red cross-region held receivers unactivated until engine_core and wing_spar_center ownership is split or explicitly accepted.",
      },
    ],
    "authority_boundary": {
      **mapping["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "public_size_reference_seeded_geometry": True,
      "parent_child_damage_ownership": False,
    },
  }
