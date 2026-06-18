"""Airframe silhouette constraint correction candidates."""

from __future__ import annotations

from typing import Any

from tools.geometry.airframe_review import shape_geometry
from tools.geometry.airframe_review.constants import (
  AIRFRAME_CONSTRAINT_CORRECTION_SCHEMA_VERSION,
  CROSS_REGION_REVIEW_SEMANTICS,
)


def _airframe_constraint_triage_status(
  *,
  current: dict[str, Any],
  candidate: dict[str, Any],
  item_review_semantics: str,
  size_evidence_level: str,
) -> str:
  if current["outside_sample_count"] == 0:
    if "low_confidence" in size_evidence_level:
      return "inside_airframe_low_confidence_size_review"
    if item_review_semantics in CROSS_REGION_REVIEW_SEMANTICS:
      return "inside_airframe_cross_region_ownership_held"
    return "inside_airframe_candidate"
  if candidate["outside_sample_count"] == 0:
    return "center_shift_candidate_resolves_silhouette_exposure"
  if candidate["outside_sample_count"] < current["outside_sample_count"]:
    return "center_shift_candidate_reduces_silhouette_exposure"
  return "silhouette_exposure_requires_size_or_shape_review"


def _airframe_constraint_recommended_action(status: str) -> str:
  if status == "inside_airframe_candidate":
    return "no_geometry_correction_required_before_human_size_review"
  if status == "inside_airframe_low_confidence_size_review":
    return "replace_low_confidence_engineering_proxy_with_better_size_source"
  if status == "inside_airframe_cross_region_ownership_held":
    return "keep_cross_region_receiver_held_until_ownership_is_split_or_accepted"
  if status == "center_shift_candidate_resolves_silhouette_exposure":
    return "review_candidate_center_shift_before_applying_to_prior_rule"
  if status == "center_shift_candidate_reduces_silhouette_exposure":
    return "review_center_shift_plus_component_specific_size_or_shape_change"
  return "research_size_shape_or_multi_region_placement_before_acceptance"


def _airframe_constraint_row(
  *,
  item_id: str,
  record_type: str,
  component_name: str,
  parent_component_name: str,
  system: str,
  component_role: str,
  geometry: dict[str, Any],
  prior_shape: str,
  prior_axis: str,
  nominal_dimensions_m: list[float],
  size_basis: str,
  size_evidence_level: str,
  bound_region_id: str,
  owner_region_ids: list[str],
  component_review_semantics: str,
  constraint_status: str,
  airframe_projection_hulls: dict[str, list[list[float]]],
) -> dict[str, Any]:
  fit = shape_geometry._silhouette_fit_candidate(
    geometry=geometry,
    airframe_projection_hulls=airframe_projection_hulls,
  )
  status = _airframe_constraint_triage_status(
    current=fit["current_silhouette"],
    candidate=fit["candidate_silhouette"],
    item_review_semantics=component_review_semantics,
    size_evidence_level=size_evidence_level,
  )
  return {
    "item_id": item_id,
    "record_type": record_type,
    "component_name": component_name,
    "parent_component_name": parent_component_name,
    "system": system,
    "component_role": component_role,
    "prior_shape": prior_shape,
    "prior_axis": prior_axis,
    "nominal_dimensions_m": nominal_dimensions_m,
    "size_basis": size_basis,
    "size_evidence_level": size_evidence_level,
    "bound_region_id": bound_region_id,
    "owner_region_ids": owner_region_ids,
    "component_review_semantics": component_review_semantics,
    "constraint_status": constraint_status,
    "current_geometry": geometry,
    "current_silhouette": fit["current_silhouette"],
    "candidate_center_shift_m": fit["center_shift_candidate_m"],
    "candidate_center_m": fit["candidate_center_m"],
    "candidate_bounds": fit["candidate_bounds"],
    "candidate_silhouette": fit["candidate_silhouette"],
    "outside_sample_reduction": fit["outside_sample_reduction"],
    "triage_status": status,
    "recommended_action": _airframe_constraint_recommended_action(status),
    "runtime_projection_status": (
      "review_only_airframe_constraint_correction_candidate_not_runtime_active"
    ),
    "authority_boundary": (
      "silhouette_constraint_diagnostic_and_center_shift_candidate_only"
    ),
  }


def build_airframe_constraint_correction_candidate_report(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  internal_prior_report: dict[str, Any],
  held_segment_report: dict[str, Any],
) -> dict[str, Any]:
  airframe_projection_hulls = shape_geometry._whole_airframe_containment_hulls(fine_proxy)
  rows: list[dict[str, Any]] = []
  for prior_row in internal_prior_report["rows"]:
    rows.append(
      _airframe_constraint_row(
        item_id=prior_row["component_name"],
        record_type="receiver_prior",
        component_name=prior_row["component_name"],
        parent_component_name=prior_row["component_name"],
        system=prior_row["system"],
        component_role=prior_row["component_role"],
        geometry=prior_row["constrained_geometry"],
        prior_shape=prior_row["prior_shape"],
        prior_axis=prior_row["prior_axis"],
        nominal_dimensions_m=prior_row["nominal_dimensions_m"],
        size_basis=prior_row["size_basis"],
        size_evidence_level=prior_row["size_evidence_level"],
        bound_region_id=prior_row["bound_region_id"],
        owner_region_ids=prior_row["constraint_region_ids"],
        component_review_semantics=prior_row["component_review_semantics"],
        constraint_status=prior_row["constraint_status"],
        airframe_projection_hulls=airframe_projection_hulls,
      )
    )
  prior_rows_by_name = {
    row["component_name"]: row for row in internal_prior_report["rows"]
  }
  for segment_row in held_segment_report["rows"]:
    parent_prior = prior_rows_by_name[segment_row["parent_component_name"]]
    rows.append(
      _airframe_constraint_row(
        item_id=segment_row["segment_id"],
        record_type="held_split_segment",
        component_name=segment_row["segment_id"],
        parent_component_name=segment_row["parent_component_name"],
        system=parent_prior["system"],
        component_role=segment_row["segment_role"],
        geometry=segment_row["geometry"],
        prior_shape=segment_row["segment_shape"],
        prior_axis=segment_row["segment_axis"],
        nominal_dimensions_m=segment_row["nominal_dimensions_m"],
        size_basis=segment_row["source_basis"],
        size_evidence_level="held_segment_split_proxy",
        bound_region_id=parent_prior["bound_region_id"],
        owner_region_ids=segment_row["owner_region_ids"],
        component_review_semantics=segment_row["parent_component_review_semantics"],
        constraint_status=segment_row["parent_component_constraint_status"],
        airframe_projection_hulls=airframe_projection_hulls,
      )
    )

  status_values = sorted({row["triage_status"] for row in rows})
  return {
    "schema_version": AIRFRAME_CONSTRAINT_CORRECTION_SCHEMA_VERSION,
    "status": "airframe_constraint_correction_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_internal_component_prior_schema_version": internal_prior_report[
      "schema_version"
    ],
    "source_cross_region_held_segment_schema_version": held_segment_report[
      "schema_version"
    ],
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "summary": {
      "item_count": len(rows),
      "receiver_prior_count": sum(
        1 for row in rows if row["record_type"] == "receiver_prior"
      ),
      "held_split_segment_count": sum(
        1 for row in rows if row["record_type"] == "held_split_segment"
      ),
      "silhouette_exposure_item_count": sum(
        1
        for row in rows
        if row["current_silhouette"]["outside_sample_count"] > 0
      ),
      "center_shift_resolves_item_count": sum(
        1
        for row in rows
        if row["triage_status"]
        == "center_shift_candidate_resolves_silhouette_exposure"
      ),
      "center_shift_reduces_item_count": sum(
        1
        for row in rows
        if row["triage_status"]
        == "center_shift_candidate_reduces_silhouette_exposure"
      ),
      "size_or_shape_review_item_count": sum(
        1
        for row in rows
        if row["triage_status"]
        == "silhouette_exposure_requires_size_or_shape_review"
      ),
      "low_confidence_inside_item_count": sum(
        1
        for row in rows
        if row["triage_status"] == "inside_airframe_low_confidence_size_review"
      ),
      "triage_status_counts": {
        status: sum(1 for row in rows if row["triage_status"] == status)
        for status in status_values
      },
      "runtime_active_component_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review items with silhouette exposure before accepting their size or placement priors.",
      },
      {
        "priority": "high",
        "question": "Apply center-shift candidates only after confirming the movement matches component semantics.",
      },
      {
        "priority": "medium",
        "question": "Replace low-confidence engineering proxies with better dimensions before runtime activation.",
      },
    ],
    "authority_boundary": {
      **internal_prior_report["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "airframe_silhouette_constraint_diagnostic": True,
      "center_shift_candidate_not_applied": True,
    },
  }
