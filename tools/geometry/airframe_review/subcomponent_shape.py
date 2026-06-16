"""Subcomponent shape and centerline placement candidates."""

from __future__ import annotations

import math
from typing import Any

from tools.geometry.airframe_review import shape_geometry
from tools.geometry.airframe_review.constants import (
  SUBCOMPONENT_CENTERLINE_PLACEMENT_RULES,
  SUBCOMPONENT_LATEST_PLACEMENT_RULES,
  SUBCOMPONENT_SHAPE_PLACEMENT_DESIGN_RULES,
  SUBCOMPONENT_SHAPE_PLACEMENT_SCHEMA_VERSION,
)
from tools.geometry.airframe_review.primitives import _round, _round_vec


def _subcomponent_shape_design_rule(row: dict[str, Any]) -> dict[str, Any]:
  rule = SUBCOMPONENT_SHAPE_PLACEMENT_DESIGN_RULES.get(row["item_id"])
  if rule is not None:
    return rule
  item_id = row["item_id"]
  if "fuel_cell" in item_id:
    return {
      "candidate_shape_family": "conformal_fuel_bladder_ellipsoid",
      "evaluation_shape": "ellipsoid",
      "evaluation_axis": "",
      "placement_policy": (
        "preserve_capacity_informed_dimensions_and_retest_as_rounded_fuel_volume"
      ),
      "rationale": (
        "fuel cells should be conformal bladder-like receivers; a rounded volume "
        "is a better first candidate than a rectangular block."
      ),
    }
  if row["prior_shape"] == "obb":
    return {
      "candidate_shape_family": "rounded_lru_ellipsoid",
      "evaluation_shape": "ellipsoid",
      "evaluation_axis": "",
      "placement_policy": (
        "preserve_public_or_standard_LRU_dimensions_and_replace_box_corners_with_rounded_receiver_proxy"
      ),
      "rationale": (
        "small avionics/control receivers are represented as damage volumes; an "
        "ellipsoid proxy tests whether the exposure is only a box-corner artifact."
      ),
    }
  if row["prior_shape"] == "capsule":
    return {
      "candidate_shape_family": "rounded_capsule_recheck",
      "evaluation_shape": "capsule",
      "evaluation_axis": row["prior_axis"] or "x",
      "placement_policy": (
        "preserve_current_capsule_dimensions_and_recheck_with_airframe_silhouette"
      ),
      "rationale": (
        "current capsule is already rounded; remaining exposure likely needs a "
        "better centerline or multi-region placement model."
      ),
    }
  return {
    "candidate_shape_family": "current_shape_recheck",
    "evaluation_shape": row["prior_shape"],
    "evaluation_axis": row["prior_axis"],
    "placement_policy": "preserve_current_dimensions_and_shape_for_recheck",
    "rationale": (
      "no component-specific replacement rule exists yet; keep the current shape "
      "and record the residual exposure for follow-up."
    ),
  }


def _geometry_from_existing_half_extents(
  *,
  source_geometry: dict[str, Any],
  shape: str,
  axis: str,
  center: list[float] | None = None,
) -> dict[str, Any]:
  resolved_center = center or source_geometry["center_m"]
  half_extents = source_geometry["half_extents_m"]
  rule = {
    "shape": shape,
    "axis": axis,
  }
  payload = shape_geometry._shape_payload_from_half_extents(
    rule=rule,
    half_extents=half_extents,
    center=resolved_center,
  )
  bounds = shape_geometry._bounds_from_center_half_extents(resolved_center, half_extents)
  return {
    **payload,
    "center_m": _round_vec(resolved_center),
    "half_extents_m": _round_vec(half_extents),
    "bounds": bounds,
    "volume_m3": _round(shape_geometry._shape_volume_m3(rule, half_extents)),
  }


def _geometry_with_center_offset(
  *,
  source_geometry: dict[str, Any],
  center_offset_m: list[float],
) -> dict[str, Any]:
  center = [
    float(source_geometry["center_m"][index]) + float(center_offset_m[index])
    for index in range(3)
  ]
  half_extents = source_geometry["half_extents_m"]
  bounds = shape_geometry._bounds_from_center_half_extents(center, half_extents)
  return {
    **source_geometry,
    "center_m": _round_vec(center),
    "bounds": bounds,
  }


def _subcomponent_centerline_rule(row: dict[str, Any]) -> dict[str, Any]:
  return SUBCOMPONENT_CENTERLINE_PLACEMENT_RULES.get(
    row["item_id"],
    {
      "center_offset_m": [0.0, 0.0, 0.0],
      "source_basis": "no_R19_centerline_candidate_rule",
      "placement_policy": (
        "no_centerline_candidate_available_keep_shape_candidate_for_review"
      ),
      "rationale": (
        "no local centerline search rule exists for this item; keep the shape "
        "candidate as the review artifact."
      ),
    },
  )


def _subcomponent_latest_rule(row: dict[str, Any]) -> dict[str, Any]:
  return SUBCOMPONENT_LATEST_PLACEMENT_RULES.get(
    row["item_id"],
    {
      "stage": "R19_centerline_candidate",
      "center_offset_from_centerline_m": [0.0, 0.0, 0.0],
      "source_basis": "R19_local_centerline_candidate",
      "placement_policy": row.get(
        "centerline_candidate_placement_policy",
        "preserve_dimensions_and_use_latest_centerline_candidate",
      ),
      "rationale": row.get(
        "centerline_candidate_rationale",
        "R19 centerline candidate already clears sampled silhouette exposure.",
      ),
    },
  )


def _subcomponent_shape_design_status(
  *,
  current_outside_count: int,
  candidate_outside_count: int,
  center_shift_m: float,
) -> str:
  if candidate_outside_count == 0 and center_shift_m > 0.0:
    return "shape_and_center_shift_candidate_resolves_silhouette_exposure"
  if candidate_outside_count == 0:
    return "shape_candidate_resolves_silhouette_exposure"
  if candidate_outside_count < current_outside_count:
    return "shape_candidate_reduces_exposure_requires_followup_geometry"
  return "shape_candidate_does_not_reduce_exposure_requires_new_placement_model"


def _subcomponent_centerline_design_status(
  *,
  candidate_outside_count: int,
  centerline_outside_count: int,
) -> str:
  if centerline_outside_count == 0:
    return "centerline_candidate_resolves_silhouette_exposure_review_required"
  if centerline_outside_count < candidate_outside_count:
    return "centerline_candidate_reduces_exposure_requires_followup_geometry"
  return "centerline_candidate_does_not_reduce_exposure_requires_new_geometry"


def _subcomponent_latest_status(outside_count: int) -> str:
  if outside_count == 0:
    return "latest_candidate_resolves_silhouette_exposure_review_required"
  return "latest_candidate_still_exposes_silhouette_requires_geometry_model"


def _subcomponent_centerline_recommended_action(status: str) -> str:
  if status == "centerline_candidate_resolves_silhouette_exposure_review_required":
    return "review_centerline_semantics_before_promoting_to_prior_or_segment_rule"
  if status == "centerline_candidate_reduces_exposure_requires_followup_geometry":
    return "keep_centerline_candidate_as_intermediate_and_research_cross_section_or_true_centerline"
  return "design_new_size_cross_section_or_multi_region_centerline_model"


def _subcomponent_latest_recommended_action(status: str) -> str:
  if status == "latest_candidate_resolves_silhouette_exposure_review_required":
    return "review_latest_candidate_semantics_before_promoting_to_prior_or_segment_rule"
  return "keep_runtime_inactive_and_design_new_section_or_envelope_model"


def _subcomponent_shape_design_recommended_action(status: str) -> str:
  if status == "shape_candidate_resolves_silhouette_exposure":
    return "review_shape_semantics_then_promote_to_next_internal_prior_rule"
  if status == "shape_and_center_shift_candidate_resolves_silhouette_exposure":
    return "review_shape_semantics_and_center_shift_before_applying_to_prior_rule"
  if status == "shape_candidate_reduces_exposure_requires_followup_geometry":
    return "keep_candidate_as_intermediate_and_research_size_cross_section_or_multi_region_centerline"
  return "design_new_size_or_centerline_model_before_runtime_activation"


def _subcomponent_shape_candidate_row(
  row: dict[str, Any],
  *,
  airframe_projection_hulls: dict[str, list[list[list[float]]]],
) -> dict[str, Any]:
  rule = _subcomponent_shape_design_rule(row)
  current_geometry = row["current_geometry"]
  candidate_seed = _geometry_from_existing_half_extents(
    source_geometry=current_geometry,
    shape=rule["evaluation_shape"],
    axis=rule["evaluation_axis"],
  )
  fit = shape_geometry._silhouette_fit_candidate(
    geometry=candidate_seed,
    airframe_projection_hulls=airframe_projection_hulls,
  )
  candidate_geometry = _geometry_from_existing_half_extents(
    source_geometry=current_geometry,
    shape=rule["evaluation_shape"],
    axis=rule["evaluation_axis"],
    center=fit["candidate_center_m"],
  )
  centerline_rule = _subcomponent_centerline_rule(row)
  centerline_geometry = _geometry_with_center_offset(
    source_geometry=candidate_geometry,
    center_offset_m=centerline_rule["center_offset_m"],
  )
  centerline_silhouette = shape_geometry._airframe_silhouette_diagnostics(
    centerline_geometry,
    airframe_projection_hulls,
  )
  latest_rule = _subcomponent_latest_rule(
    {
      **row,
      "centerline_candidate_placement_policy": centerline_rule[
        "placement_policy"
      ],
      "centerline_candidate_rationale": centerline_rule["rationale"],
    }
  )
  latest_geometry = _geometry_with_center_offset(
    source_geometry=centerline_geometry,
    center_offset_m=latest_rule["center_offset_from_centerline_m"],
  )
  latest_silhouette = shape_geometry._airframe_silhouette_diagnostics(
    latest_geometry,
    airframe_projection_hulls,
  )
  current_outside_count = row["current_silhouette"]["outside_sample_count"]
  candidate_outside_count = fit["candidate_silhouette"]["outside_sample_count"]
  centerline_outside_count = centerline_silhouette["outside_sample_count"]
  latest_outside_count = latest_silhouette["outside_sample_count"]
  status = _subcomponent_shape_design_status(
    current_outside_count=current_outside_count,
    candidate_outside_count=candidate_outside_count,
    center_shift_m=fit["center_shift_candidate_m"],
  )
  centerline_status = _subcomponent_centerline_design_status(
    candidate_outside_count=candidate_outside_count,
    centerline_outside_count=centerline_outside_count,
  )
  centerline_shift_m = math.sqrt(
    sum(float(value) ** 2 for value in centerline_rule["center_offset_m"])
  )
  latest_incremental_shift_m = math.sqrt(
    sum(
      float(value) ** 2
      for value in latest_rule["center_offset_from_centerline_m"]
    )
  )
  latest_total_center_offset = [
    float(centerline_rule["center_offset_m"][index])
    + float(latest_rule["center_offset_from_centerline_m"][index])
    for index in range(3)
  ]
  latest_status = _subcomponent_latest_status(latest_outside_count)
  return {
    "item_id": row["item_id"],
    "record_type": row["record_type"],
    "parent_component_name": row["parent_component_name"],
    "system": row["system"],
    "component_role": row["component_role"],
    "bound_region_id": row["bound_region_id"],
    "owner_region_ids": row["owner_region_ids"],
    "current_shape": row["prior_shape"],
    "current_axis": row["prior_axis"],
    "candidate_shape_family": rule["candidate_shape_family"],
    "candidate_evaluation_shape": rule["evaluation_shape"],
    "candidate_evaluation_axis": rule["evaluation_axis"],
    "nominal_dimensions_m": row["nominal_dimensions_m"],
    "dimension_policy": (
      "preserve_nominal_public_or_declared_prior_dimensions_no_shrink"
    ),
    "size_basis": row["size_basis"],
    "size_evidence_level": row["size_evidence_level"],
    "placement_policy": rule["placement_policy"],
    "design_rationale": rule["rationale"],
    "current_geometry": current_geometry,
    "candidate_geometry": candidate_geometry,
    "centerline_candidate_geometry": centerline_geometry,
    "latest_candidate_geometry": latest_geometry,
    "current_silhouette": row["current_silhouette"],
    "candidate_silhouette": fit["candidate_silhouette"],
    "centerline_candidate_silhouette": centerline_silhouette,
    "latest_candidate_silhouette": latest_silhouette,
    "candidate_center_shift_m": fit["center_shift_candidate_m"],
    "centerline_candidate_center_offset_m": _round_vec(
      centerline_rule["center_offset_m"]
    ),
    "centerline_candidate_shift_m": _round(centerline_shift_m),
    "centerline_candidate_source_basis": centerline_rule["source_basis"],
    "centerline_candidate_placement_policy": (
      centerline_rule["placement_policy"]
    ),
    "centerline_candidate_rationale": centerline_rule["rationale"],
    "latest_candidate_stage": latest_rule["stage"],
    "latest_candidate_center_offset_from_centerline_m": _round_vec(
      latest_rule["center_offset_from_centerline_m"]
    ),
    "latest_candidate_total_center_offset_m": _round_vec(
      latest_total_center_offset
    ),
    "latest_candidate_incremental_shift_m": _round(
      latest_incremental_shift_m
    ),
    "latest_candidate_source_basis": latest_rule["source_basis"],
    "latest_candidate_placement_policy": latest_rule["placement_policy"],
    "latest_candidate_rationale": latest_rule["rationale"],
    "outside_sample_reduction": (
      current_outside_count - candidate_outside_count
    ),
    "centerline_outside_sample_reduction": (
      current_outside_count - centerline_outside_count
    ),
    "centerline_incremental_outside_sample_reduction": (
      candidate_outside_count - centerline_outside_count
    ),
    "latest_outside_sample_reduction": (
      current_outside_count - latest_outside_count
    ),
    "latest_incremental_outside_sample_reduction": (
      centerline_outside_count - latest_outside_count
    ),
    "shape_design_status": status,
    "centerline_candidate_status": centerline_status,
    "latest_candidate_status": latest_status,
    "recommended_action": _subcomponent_shape_design_recommended_action(status),
    "centerline_candidate_recommended_action": (
      _subcomponent_centerline_recommended_action(centerline_status)
    ),
    "latest_candidate_recommended_action": (
      _subcomponent_latest_recommended_action(latest_status)
    ),
    "runtime_projection_status": (
      "review_only_subcomponent_shape_candidate_not_runtime_active"
    ),
    "authority_boundary": (
      "shape_design_candidate_preserves_nominal_dimensions_but_is_not_true_internal_engineering_geometry"
    ),
  }


def build_subcomponent_shape_placement_candidate_report(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  airframe_constraint_report: dict[str, Any],
) -> dict[str, Any]:
  airframe_projection_hulls = shape_geometry._whole_airframe_containment_hulls(fine_proxy)
  rows = [
    _subcomponent_shape_candidate_row(
      row,
      airframe_projection_hulls=airframe_projection_hulls,
    )
    for row in airframe_constraint_report["rows"]
    if row["current_silhouette"]["outside_sample_count"] > 0
  ]
  status_values = sorted({row["shape_design_status"] for row in rows})
  centerline_status_values = sorted(
    {row["centerline_candidate_status"] for row in rows}
  )
  latest_status_values = sorted({row["latest_candidate_status"] for row in rows})
  shape_families = sorted({row["candidate_shape_family"] for row in rows})
  if rows:
    manual_review_queue = [
      {
        "priority": "high",
        "question": "Review any remaining shape-placement candidates before applying them to the internal prior or held-segment rules.",
      },
      {
        "priority": "high",
        "question": "For unresolved candidates, research better true dimensions, tapered cross-sections, or cross-region centerlines rather than shrinking nominal dimensions.",
      },
      {
        "priority": "high",
        "question": "Review R19 centerline candidates separately; they preserve dimensions but change semantic placement and are not accepted runtime geometry.",
      },
      {
        "priority": "high",
        "question": "R20 latest candidates promoted in R21 are retained here only when new exposure remains after the review-only rule update.",
      },
      {
        "priority": "medium",
        "question": "Keep runtime damage behavior unchanged until these shape candidates are explicitly accepted.",
      },
    ]
  else:
    manual_review_queue = [
      {
        "priority": "high",
        "question": "No remaining shape-placement candidates after R21 review-only rule promotion; continue to hold runtime activation for explicit ownership decisions.",
      },
      {
        "priority": "medium",
        "question": "Keep runtime damage behavior unchanged until the promoted review-only rules are explicitly accepted, split, or deliberately held with tests.",
      },
    ]
  return {
    "schema_version": SUBCOMPONENT_SHAPE_PLACEMENT_SCHEMA_VERSION,
    "status": "subcomponent_shape_placement_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_airframe_constraint_correction_schema_version": (
      airframe_constraint_report["schema_version"]
    ),
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "summary": {
      "source_constraint_item_count": airframe_constraint_report["summary"][
        "item_count"
      ],
      "source_silhouette_exposure_item_count": airframe_constraint_report[
        "summary"
      ]["silhouette_exposure_item_count"],
      "shape_placement_candidate_count": len(rows),
      "nominal_dimension_preserved_count": len(rows),
      "candidate_reduces_exposure_count": sum(
        1 for row in rows if row["outside_sample_reduction"] > 0
      ),
      "candidate_resolves_exposure_count": sum(
        1
        for row in rows
        if row["candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "candidate_unresolved_exposure_count": sum(
        1
        for row in rows
        if row["candidate_silhouette"]["outside_sample_count"] > 0
      ),
      "candidate_no_improvement_count": sum(
        1 for row in rows if row["outside_sample_reduction"] <= 0
      ),
      "current_total_outside_sample_count": sum(
        row["current_silhouette"]["outside_sample_count"] for row in rows
      ),
      "candidate_total_outside_sample_count": sum(
        row["candidate_silhouette"]["outside_sample_count"] for row in rows
      ),
      "candidate_total_outside_sample_reduction": sum(
        row["outside_sample_reduction"] for row in rows
      ),
      "centerline_candidate_count": len(rows),
      "centerline_candidate_reduces_exposure_count": sum(
        1
        for row in rows
        if row["centerline_incremental_outside_sample_reduction"] > 0
      ),
      "centerline_candidate_resolves_exposure_count": sum(
        1
        for row in rows
        if row["centerline_candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "centerline_candidate_unresolved_exposure_count": sum(
        1
        for row in rows
        if row["centerline_candidate_silhouette"]["outside_sample_count"] > 0
      ),
      "centerline_candidate_total_outside_sample_count": sum(
        row["centerline_candidate_silhouette"]["outside_sample_count"]
        for row in rows
      ),
      "centerline_candidate_total_outside_sample_reduction": sum(
        row["centerline_outside_sample_reduction"] for row in rows
      ),
      "centerline_candidate_incremental_outside_sample_reduction": sum(
        row["centerline_incremental_outside_sample_reduction"]
        for row in rows
      ),
      "latest_candidate_count": len(rows),
      "latest_candidate_resolves_exposure_count": sum(
        1
        for row in rows
        if row["latest_candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "latest_candidate_unresolved_exposure_count": sum(
        1
        for row in rows
        if row["latest_candidate_silhouette"]["outside_sample_count"] > 0
      ),
      "latest_candidate_total_outside_sample_count": sum(
        row["latest_candidate_silhouette"]["outside_sample_count"]
        for row in rows
      ),
      "latest_candidate_total_outside_sample_reduction": sum(
        row["latest_outside_sample_reduction"] for row in rows
      ),
      "latest_candidate_incremental_outside_sample_reduction": sum(
        row["latest_incremental_outside_sample_reduction"] for row in rows
      ),
      "candidate_shape_family_counts": {
        family: sum(1 for row in rows if row["candidate_shape_family"] == family)
        for family in shape_families
      },
      "shape_design_status_counts": {
        status: sum(1 for row in rows if row["shape_design_status"] == status)
        for status in status_values
      },
      "centerline_candidate_status_counts": {
        status: sum(
          1 for row in rows if row["centerline_candidate_status"] == status
        )
        for status in centerline_status_values
      },
      "latest_candidate_status_counts": {
        status: sum(
          1 for row in rows if row["latest_candidate_status"] == status
        )
        for status in latest_status_values
      },
      "runtime_active_component_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": manual_review_queue,
    "authority_boundary": {
      **airframe_constraint_report["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "nominal_dimensions_preserved": True,
      "shape_candidate_not_applied_to_internal_prior_rules": False,
      "centerline_candidate_not_applied_to_internal_prior_rules": False,
      "latest_candidate_not_applied_to_internal_prior_rules": False,
      "latest_candidate_promoted_to_internal_prior_or_segment_rules": True,
    },
  }
