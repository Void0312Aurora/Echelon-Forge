"""Runtime activation and ownership-split report builders for airframe review."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import component_model, filesystem
from tools.geometry.airframe_review.constants import (
  CROSS_REGION_OWNERSHIP_SPLIT_SCHEMA_VERSION,
  DEFAULT_RUNTIME_DATABASE,
  PROMOTED_SHAPE_STATUSES,
  REPO_ROOT,
  TARGET_GEOMETRY_PROXY_TRAINING_CONFIG,
  TARGET_GEOMETRY_RUNTIME_ACTIVATION_SCHEMA_VERSION,
  TARGET_GEOMETRY_RUNTIME_BEHAVIOR_SCHEMA_VERSION,
  TARGET_GEOMETRY_TRAINING_PROXY_SCHEMA_VERSION,
)


def _ownership_split_policy(parent_component_name: str) -> dict[str, str]:
  if parent_component_name == "engine_core":
    return {
      "recommended_ownership_decision": (
        "split_into_engine_section_receivers_and_keep_intake_duct_receiver_separate"
      ),
      "parent_receiver_runtime_policy": (
        "retire_parent_engine_core_damage_receiver_when_split_receivers_are_accepted"
      ),
      "decision_rationale": (
        "The public-size engine proxy spans multiple semantic regions; the R15/R21 "
        "segments isolate afterburner/nozzle overlap, hot section, and forward "
        "compressor envelopes while leaving the intake airflow path on the existing "
        "dedicated intake receiver."
      ),
    }
  if parent_component_name == "wing_spar_center":
    return {
      "recommended_ownership_decision": (
        "split_into_center_carrythrough_root_and_inner_wing_spar_receivers"
      ),
      "parent_receiver_runtime_policy": (
        "retire_parent_wing_spar_center_damage_receiver_when_split_receivers_are_accepted"
      ),
      "decision_rationale": (
        "The carry-through spar proxy crosses center fuselage, wing roots, and inner "
        "wing skins; the R15/R21 segments provide owner-region receiver candidates "
        "without accepting a monolithic cross-region runtime receiver."
      ),
    }
  return {
    "recommended_ownership_decision": (
      "keep_cross_region_receiver_held_until_specific_split_policy_exists"
    ),
    "parent_receiver_runtime_policy": (
      "keep_parent_receiver_non_runtime_until_ownership_is_explicit"
    ),
    "decision_rationale": (
      "No component-specific ownership policy exists for this held receiver."
    ),
  }


def _segment_aabb_runtime_candidate(
  *,
  segment_row: dict[str, Any],
  parent_prior: dict[str, Any],
) -> dict[str, Any]:
  segment_bounds = segment_row["geometry"]["bounds"]
  return {
    "name": segment_row["segment_id"],
    "system": parent_prior["system"],
    "offset": segment_bounds["center"],
    "size": segment_bounds["span"],
    "geometry_primitive": "aabb",
    "geometry": {
      "primitive": "aabb",
      "source": "a2_cross_region_ownership_split_candidate",
      "source_parent_component_name": segment_row["parent_component_name"],
      "source_segment_id": segment_row["segment_id"],
      "owner_region_ids": segment_row["owner_region_ids"],
      "prior_shape": segment_row["segment_shape"],
      "prior_axis": segment_row["segment_axis"],
      "shape_promotion_status": segment_row["shape_promotion_status"],
      "segment_role": segment_row["segment_role"],
      "runtime_projection_status": "parse_ready_candidate_not_runtime_active",
    },
    "critical": parent_prior["critical"],
  }


def build_cross_region_ownership_split_candidate_report(
  mapping: dict[str, Any],
  internal_prior_report: dict[str, Any],
  held_segment_report: dict[str, Any],
  airframe_constraint_report: dict[str, Any],
) -> dict[str, Any]:
  prior_rows_by_name = {
    row["component_name"]: row for row in internal_prior_report["rows"]
  }
  constraint_rows_by_id = {
    row["item_id"]: row for row in airframe_constraint_report["rows"]
  }
  parent_names = sorted(
    {row["parent_component_name"] for row in held_segment_report["rows"]}
  )
  rows: list[dict[str, Any]] = []
  for parent_name in parent_names:
    parent_prior = prior_rows_by_name[parent_name]
    segments = [
      row
      for row in held_segment_report["rows"]
      if row["parent_component_name"] == parent_name
    ]
    segments.sort(key=lambda row: row["segment_index"])
    segment_entries: list[dict[str, Any]] = []
    for segment in segments:
      constraint_row = constraint_rows_by_id.get(segment["segment_id"], {})
      current_silhouette = constraint_row.get(
        "current_silhouette",
        {"outside_sample_count": None, "outside_views": []},
      )
      segment_entries.append(
        {
          "segment_id": segment["segment_id"],
          "segment_role": segment["segment_role"],
          "owner_region_ids": segment["owner_region_ids"],
          "segment_shape": segment["segment_shape"],
          "segment_axis": segment["segment_axis"],
          "nominal_dimensions_m": segment["nominal_dimensions_m"],
          "inside_whole_airframe_bounds": segment["inside_whole_airframe_bounds"],
          "whole_airframe_outside_fraction": segment[
            "whole_airframe_outside_fraction"
          ],
          "shape_promotion_status": segment["shape_promotion_status"],
          "silhouette_outside_sample_count": current_silhouette[
            "outside_sample_count"
          ],
          "silhouette_outside_views": current_silhouette["outside_views"],
          "airframe_triage_status": constraint_row.get("triage_status", ""),
          "runtime_component_json_candidate": _segment_aabb_runtime_candidate(
            segment_row=segment,
            parent_prior=parent_prior,
          ),
        }
      )

    policy = _ownership_split_policy(parent_name)
    owner_region_ids = sorted(
      {
        owner_region_id
        for segment in segments
        for owner_region_id in segment["owner_region_ids"]
      }
    )
    candidate_names = [
      entry["runtime_component_json_candidate"]["name"] for entry in segment_entries
    ]
    rows.append(
      {
        "parent_component_name": parent_name,
        "parent_system": parent_prior["system"],
        "parent_component_role": parent_prior["component_role"],
        "parent_review_semantics": parent_prior["component_review_semantics"],
        "parent_constraint_status": parent_prior["constraint_status"],
        "parent_receiver_runtime_policy": policy["parent_receiver_runtime_policy"],
        "recommended_ownership_decision": policy[
          "recommended_ownership_decision"
        ],
        "decision_rationale": policy["decision_rationale"],
        "decision_status": (
          "candidate_split_ready_for_runtime_tests_not_accepted"
        ),
        "runtime_activation_status": (
          "not_active_pending_ownership_review_and_runtime_tests"
        ),
        "parent_receiver_retirement_required_before_activation": True,
        "candidate_runtime_component_names": candidate_names,
        "owner_region_ids": owner_region_ids,
        "segment_count": len(segment_entries),
        "segment_entries": segment_entries,
        "parse_ready_runtime_candidate_count": len(segment_entries),
        "runtime_active_split_component_count": 0,
        "silhouette_exposure_segment_count": sum(
          1
          for entry in segment_entries
          if (entry["silhouette_outside_sample_count"] or 0) > 0
        ),
        "outside_whole_airframe_segment_count": sum(
          1
          for segment in segments
          if not segment["inside_whole_airframe_bounds"]
        ),
        "shape_promotion_segment_count": sum(
          1
          for segment in segments
          if segment["shape_promotion_status"] in PROMOTED_SHAPE_STATUSES
        ),
        "acceptance_checks_required": [
          "human_accepts_or_rejects_parent_receiver_retirement",
          "runtime_component_schema_parse_test_for_split_candidates",
          "component_damage_regression_for_parent_vs_split_receiver_behavior",
          "no_runtime_activation_without_explicit_tg_p7_decision",
        ],
        "authority_boundary": (
          "ownership_split_candidate_not_runtime_damage_ownership_acceptance"
        ),
      }
    )

  split_receiver_count = sum(row["segment_count"] for row in rows)
  return {
    "schema_version": CROSS_REGION_OWNERSHIP_SPLIT_SCHEMA_VERSION,
    "status": "cross_region_ownership_split_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_internal_component_prior_schema_version": internal_prior_report[
      "schema_version"
    ],
    "source_cross_region_held_segment_schema_version": held_segment_report[
      "schema_version"
    ],
    "source_airframe_constraint_schema_version": airframe_constraint_report[
      "schema_version"
    ],
    "summary": {
      "parent_decision_count": len(rows),
      "split_candidate_parent_count": sum(
        1
        for row in rows
        if row["recommended_ownership_decision"].startswith("split_into")
      ),
      "split_receiver_candidate_count": split_receiver_count,
      "engine_core_split_receiver_candidate_count": sum(
        row["segment_count"]
        for row in rows
        if row["parent_component_name"] == "engine_core"
      ),
      "wing_spar_center_split_receiver_candidate_count": sum(
        row["segment_count"]
        for row in rows
        if row["parent_component_name"] == "wing_spar_center"
      ),
      "zero_silhouette_exposure_split_candidate_count": sum(
        1
        for row in rows
        for entry in row["segment_entries"]
        if entry["silhouette_outside_sample_count"] == 0
      ),
      "outside_whole_airframe_split_candidate_count": sum(
        row["outside_whole_airframe_segment_count"] for row in rows
      ),
      "parent_receiver_retirement_required_count": sum(
        1
        for row in rows
        if row["parent_receiver_retirement_required_before_activation"]
      ),
      "runtime_parse_ready_split_candidate_count": split_receiver_count,
      "runtime_active_split_component_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Accept, reject, or keep held the proposed parent receiver retirement for engine_core and wing_spar_center.",
      },
      {
        "priority": "high",
        "question": "Run TG-P7 parse and behavior tests before activating any split receiver candidate.",
      },
      {
        "priority": "medium",
        "question": "Keep split receiver payloads as AABB fallback candidates until exact capsule or ellipsoid runtime intersection is separately implemented.",
      },
    ],
    "authority_boundary": {
      **internal_prior_report["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "runtime_split_receiver_activation": False,
      "runtime_schema_parse_ready_candidate": True,
      "parent_receiver_retirement_accepted": False,
      "cross_region_receiver_ownership_accepted": False,
      "true_internal_component_geometry": False,
    },
  }


def _runtime_loader_contract_status(candidate: dict[str, Any]) -> str:
  required_fields = {
    "name",
    "system",
    "offset",
    "size",
    "geometry_primitive",
    "geometry",
    "critical",
  }
  if not required_fields.issubset(candidate):
    return "missing_required_runtime_loader_fields"
  if candidate["geometry_primitive"] != "aabb":
    return "unsupported_runtime_loader_fallback_primitive"
  if candidate["geometry"].get("primitive") != "aabb":
    return "unsupported_nested_geometry_primitive"
  if len(candidate["offset"]) != 3 or len(candidate["size"]) != 3:
    return "invalid_offset_or_size_vector"
  if any(value <= 0 for value in candidate["size"]):
    return "invalid_non_positive_size"
  return "parse_ready_existing_loader_fields"


def _damage_component_locations_by_name(
  aircraft: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
  if not aircraft:
    return {}
  locations: dict[str, dict[str, Any]] = {}
  for hitbox_index, hitbox in enumerate(
    aircraft.get("damage_model", {}).get("hitboxes", [])
  ):
    for component_index, component in enumerate(hitbox.get("components", [])):
      component_name = component.get("name")
      if not component_name:
        continue
      locations[component_name] = {
        "hitbox_index": hitbox_index,
        "component_index": component_index,
        "target_path": f"damage_model.hitboxes[{hitbox_index}].components",
      }
  return locations


def _runtime_patch_location_for_parent(
  parent_component_name: str,
  component_locations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
  return component_locations.get(
    parent_component_name,
    {
      "hitbox_index": None,
      "component_index": None,
      "target_path": "damage_model.hitboxes[].components",
    },
  )


def build_target_geometry_runtime_activation_candidate_report(
  mapping: dict[str, Any],
  ownership_split_report: dict[str, Any],
  aircraft: dict[str, Any] | None = None,
) -> dict[str, Any]:
  component_locations = _damage_component_locations_by_name(aircraft)
  rows: list[dict[str, Any]] = []
  patch_additions: list[dict[str, Any]] = []
  patch_component_additions: list[dict[str, Any]] = []
  patch_component_removals: list[dict[str, Any]] = []
  parent_retirement_plan: list[dict[str, Any]] = []

  for parent_row in ownership_split_report["rows"]:
    parent_location = _runtime_patch_location_for_parent(
      parent_row["parent_component_name"],
      component_locations,
    )
    parent_retirement_plan.append(
      {
        "parent_component_name": parent_row["parent_component_name"],
        "target_hitbox_index": parent_location["hitbox_index"],
        "target_component_index": parent_location["component_index"],
        "target_path": parent_location["target_path"],
        "recommended_ownership_decision": parent_row[
          "recommended_ownership_decision"
        ],
        "parent_receiver_runtime_policy": parent_row[
          "parent_receiver_runtime_policy"
        ],
        "candidate_runtime_component_names": parent_row[
          "candidate_runtime_component_names"
        ],
        "retirement_application_status": (
          "not_applied_pending_explicit_tg_p7_acceptance"
        ),
      }
    )
    patch_component_removals.append(
      {
        "operation": "remove_component_by_name",
        "component_name": parent_row["parent_component_name"],
        "target_hitbox_index": parent_location["hitbox_index"],
        "target_component_index": parent_location["component_index"],
        "target_path": parent_location["target_path"],
        "application_status": "not_applied_to_repository_unit_database",
      }
    )
    for segment_entry in parent_row["segment_entries"]:
      candidate = copy.deepcopy(
        segment_entry["runtime_component_json_candidate"]
      )
      candidate["geometry"]["runtime_activation_candidate_status"] = (
        "tg_p7_parse_ready_not_applied"
      )
      candidate["geometry"]["activation_parent_component_name"] = parent_row[
        "parent_component_name"
      ]
      candidate["geometry"]["activation_parent_runtime_policy"] = parent_row[
        "parent_receiver_runtime_policy"
      ]
      candidate["geometry"]["activation_feature_flag"] = (
        "A2_TARGET_GEOMETRY_PROXY_F16C_R22"
      )
      loader_status = _runtime_loader_contract_status(candidate)
      patch_additions.append(candidate)
      patch_component_additions.append(
        {
          "operation": "append_component",
          "component_name": candidate["name"],
          "parent_component_name": parent_row["parent_component_name"],
          "target_hitbox_index": parent_location["hitbox_index"],
          "target_path": parent_location["target_path"],
          "application_status": "not_applied_to_repository_unit_database",
          "value": candidate,
        }
      )
      rows.append(
        {
          "candidate_component_name": candidate["name"],
          "parent_component_name": parent_row["parent_component_name"],
          "target_hitbox_index": parent_location["hitbox_index"],
          "unit_database_patch_path": parent_location["target_path"],
          "parent_system": parent_row["parent_system"],
          "recommended_ownership_decision": parent_row[
            "recommended_ownership_decision"
          ],
          "parent_receiver_runtime_policy": parent_row[
            "parent_receiver_runtime_policy"
          ],
          "segment_role": segment_entry["segment_role"],
          "owner_region_ids": segment_entry["owner_region_ids"],
          "geometry_primitive": candidate["geometry_primitive"],
          "offset_m": candidate["offset"],
          "size_m": candidate["size"],
          "runtime_loader_contract_status": loader_status,
          "runtime_activation_status": "not_applied_to_unit_database",
          "behavior_test_status": "required_before_activation",
          "feature_flag": "A2_TARGET_GEOMETRY_PROXY_F16C_R22",
          "runtime_component_json_candidate": candidate,
        }
      )

  loader_ready_count = sum(
    1
    for row in rows
    if row["runtime_loader_contract_status"]
    == "parse_ready_existing_loader_fields"
  )
  behavior_required_count = sum(
    1
    for row in rows
    if row["behavior_test_status"] == "required_before_activation"
  )
  return {
    "schema_version": TARGET_GEOMETRY_RUNTIME_ACTIVATION_SCHEMA_VERSION,
    "status": "target_geometry_runtime_activation_candidate_generated_tg_p7_r1",
    "generated_on": "2026-06-13",
    "source_geometry_generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_cross_region_ownership_split_schema_version": (
      ownership_split_report["schema_version"]
    ),
    "activation_policy": {
      "activation_scope": "f16c_block50_initial_training_geometry_proxy",
      "activation_mode": "unit_database_patch_candidate_not_applied",
      "target_unit": "F-16C_Block50",
      "target_path": "damage_model.hitboxes[].components",
      "requires_feature_flag": True,
      "feature_flag": "A2_TARGET_GEOMETRY_PROXY_F16C_R22",
      "parent_receiver_retirement_required_before_activation": True,
      "runtime_behavior_regression_required_before_activation": True,
    },
    "runtime_loader_contract": {
      "required_top_level_fields": [
        "name",
        "system",
        "offset",
        "size",
        "geometry_primitive",
        "geometry",
        "critical",
      ],
      "accepted_fallback_geometry_primitive": "aabb",
      "loader_status_required_for_activation": (
        "parse_ready_existing_loader_fields"
      ),
    },
    "summary": {
      "candidate_component_count": len(rows),
      "runtime_schema_parse_ready_component_count": loader_ready_count,
      "runtime_active_component_count": 0,
      "parent_receiver_retirement_candidate_count": len(
        parent_retirement_plan
      ),
      "parent_receiver_retirement_applied_count": 0,
      "aabb_fallback_component_count": sum(
        1 for row in rows if row["geometry_primitive"] == "aabb"
      ),
      "unit_database_patch_component_count": len(patch_additions),
      "behavior_test_required_count": behavior_required_count,
      "activation_blocker_count": len(rows) - loader_ready_count,
      "review_status": "tg_p7_parse_ready_activation_candidate_not_applied",
    },
    "rows": rows,
    "parent_receiver_retirement_plan": parent_retirement_plan,
    "unit_database_patch_candidate": {
      "target_unit": "F-16C_Block50",
      "target_path": "damage_model.hitboxes[].components",
      "operation": "remove_parent_components_and_append_split_receivers",
      "remove": patch_component_removals,
      "add": patch_additions,
      "add_components": patch_component_additions,
      "parent_receiver_retirement_plan": parent_retirement_plan,
      "patch_application_status": "not_applied_to_repository_unit_database",
    },
    "acceptance_gate": [
      "candidate_component_count_equals_8",
      "runtime_schema_parse_ready_component_count_equals_8",
      "parent_receiver_retirement_plan_exists_for_2_parents",
      "unit_database_patch_candidate_contains_8_component_records",
      "runtime_active_component_count_equals_0_until_explicit_activation",
      "behavior_tests_required_before_activation",
    ],
    "authority_boundary": {
      **ownership_split_report["authority_boundary"],
      "unit_database_modified": False,
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "runtime_activation_candidate": True,
      "training_proxy_feature_flag_required": True,
      "parent_receiver_retirement_accepted": False,
      "true_internal_component_geometry": False,
    },
  }


def _apply_runtime_activation_patch_candidate(
  aircraft: dict[str, Any],
  runtime_activation_report: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
  patched_aircraft = copy.deepcopy(aircraft)
  operations: list[dict[str, Any]] = []
  hitboxes = patched_aircraft.get("damage_model", {}).get("hitboxes", [])

  for removal in runtime_activation_report["unit_database_patch_candidate"][
    "remove"
  ]:
    hitbox_index = removal["target_hitbox_index"]
    if hitbox_index is None or hitbox_index >= len(hitboxes):
      operations.append({**removal, "result": "target_hitbox_missing"})
      continue
    components = hitboxes[hitbox_index].get("components", [])
    before_count = len(components)
    kept_components = [
      component
      for component in components
      if component.get("name") != removal["component_name"]
    ]
    hitboxes[hitbox_index]["components"] = kept_components
    operations.append(
      {
        **removal,
        "result": (
          "removed"
          if len(kept_components) < before_count
          else "component_not_found"
        ),
        "component_count_before": before_count,
        "component_count_after": len(kept_components),
      }
    )

  for addition in runtime_activation_report["unit_database_patch_candidate"][
    "add_components"
  ]:
    hitbox_index = addition["target_hitbox_index"]
    if hitbox_index is None or hitbox_index >= len(hitboxes):
      operations.append({**addition, "value": None, "result": "target_hitbox_missing"})
      continue
    components = hitboxes[hitbox_index].setdefault("components", [])
    before_count = len(components)
    components.append(copy.deepcopy(addition["value"]))
    operations.append(
      {
        **{key: value for key, value in addition.items() if key != "value"},
        "result": "appended",
        "component_count_before": before_count,
        "component_count_after": len(components),
      }
    )

  return patched_aircraft, operations


def build_target_geometry_runtime_behavior_regression_report(
  aircraft: dict[str, Any],
  runtime_activation_report: dict[str, Any],
) -> dict[str, Any]:
  base_component_names = component_model.damage_component_names(aircraft)
  patched_aircraft, operations = _apply_runtime_activation_patch_candidate(
    aircraft,
    runtime_activation_report,
  )
  patched_component_names = component_model.damage_component_names(patched_aircraft)
  parent_names = [
    row["parent_component_name"]
    for row in runtime_activation_report["parent_receiver_retirement_plan"]
  ]
  split_names = [
    row["candidate_component_name"] for row in runtime_activation_report["rows"]
  ]
  duplicate_names = component_model.duplicate_names(patched_component_names)
  rows: list[dict[str, Any]] = []
  for parent_row in runtime_activation_report["parent_receiver_retirement_plan"]:
    parent_name = parent_row["parent_component_name"]
    target_hitbox_index = parent_row["target_hitbox_index"]
    base_hitboxes = aircraft.get("damage_model", {}).get("hitboxes", [])
    patched_hitboxes = patched_aircraft.get("damage_model", {}).get("hitboxes", [])
    base_hitbox_component_count = (
      len(base_hitboxes[target_hitbox_index].get("components", []))
      if target_hitbox_index is not None and target_hitbox_index < len(base_hitboxes)
      else 0
    )
    patched_hitbox_component_count = (
      len(patched_hitboxes[target_hitbox_index].get("components", []))
      if target_hitbox_index is not None and target_hitbox_index < len(patched_hitboxes)
      else 0
    )
    split_component_names = [
      row["candidate_component_name"]
      for row in runtime_activation_report["rows"]
      if row["parent_component_name"] == parent_name
    ]
    rows.append(
      {
        "parent_component_name": parent_name,
        "target_hitbox_index": target_hitbox_index,
        "target_path": parent_row["target_path"],
        "base_hitbox_component_count": base_hitbox_component_count,
        "patched_hitbox_component_count": patched_hitbox_component_count,
        "parent_present_before_patch": parent_name in base_component_names,
        "parent_absent_after_patch": parent_name not in patched_component_names,
        "split_component_names": split_component_names,
        "split_component_present_count": sum(
          1 for name in split_component_names if name in patched_component_names
        ),
        "duplicate_component_name_count": sum(
          1 for name in split_component_names if name in duplicate_names
        ),
        "behavior_status": (
          "pass"
          if parent_name in base_component_names
          and parent_name not in patched_component_names
          and all(name in patched_component_names for name in split_component_names)
          else "fail"
        ),
      }
    )

  expected_projected_count = (
    len(base_component_names) - len(parent_names) + len(split_names)
  )
  behavior_pass = (
    len(patched_component_names) == expected_projected_count
    and all(parent_name not in patched_component_names for parent_name in parent_names)
    and all(split_name in patched_component_names for split_name in split_names)
    and not duplicate_names
    and all(row["behavior_status"] == "pass" for row in rows)
  )
  return {
    "schema_version": TARGET_GEOMETRY_RUNTIME_BEHAVIOR_SCHEMA_VERSION,
    "status": "target_geometry_runtime_behavior_regression_generated_tg_p7_r2",
    "generated_on": "2026-06-13",
    "source_runtime_activation_schema_version": runtime_activation_report[
      "schema_version"
    ],
    "target_unit": runtime_activation_report["activation_policy"]["target_unit"],
    "feature_flag": runtime_activation_report["activation_policy"][
      "feature_flag"
    ],
    "summary": {
      "base_component_count": len(base_component_names),
      "expected_projected_component_count": expected_projected_count,
      "projected_component_count": len(patched_component_names),
      "retired_parent_component_count": sum(
        1 for parent_name in parent_names if parent_name not in patched_component_names
      ),
      "split_component_added_count": sum(
        1 for split_name in split_names if split_name in patched_component_names
      ),
      "duplicate_component_name_count": len(duplicate_names),
      "parent_retirement_behavior_pass_count": sum(
        1 for row in rows if row["behavior_status"] == "pass"
      ),
      "behavior_regression_pass": behavior_pass,
      "runtime_active_component_count": 0,
      "unit_database_modified": False,
    },
    "rows": rows,
    "patch_operations": operations,
    "projected_component_names": patched_component_names,
    "duplicate_component_names": duplicate_names,
    "acceptance_gate": [
      "base_component_count_equals_26",
      "retired_parent_component_count_equals_2",
      "split_component_added_count_equals_8",
      "projected_component_count_equals_32",
      "duplicate_component_name_count_equals_0",
      "runtime_active_component_count_equals_0_until_training_path_activation",
    ],
    "authority_boundary": {
      **runtime_activation_report["authority_boundary"],
      "runtime_behavior_regression_candidate": True,
      "unit_database_modified": False,
      "runtime_active_component": False,
      "training_path_wired": False,
    },
  }


def build_target_geometry_training_proxy_unit_candidate(
  aircraft: dict[str, Any],
  runtime_activation_report: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
  return _apply_runtime_activation_patch_candidate(
    aircraft,
    runtime_activation_report,
  )


def build_target_geometry_training_proxy_database_report(
  aircraft: dict[str, Any],
  runtime_activation_report: dict[str, Any],
  runtime_behavior_report: dict[str, Any],
  *,
  database_source_path: Path = DEFAULT_RUNTIME_DATABASE,
  proxy_database_dir: Path | None = None,
) -> dict[str, Any]:
  patched_aircraft, operations = build_target_geometry_training_proxy_unit_candidate(
    aircraft,
    runtime_activation_report,
  )
  base_component_names = component_model.damage_component_names(aircraft)
  proxy_component_names = component_model.damage_component_names(patched_aircraft)
  parent_names = [
    row["parent_component_name"]
    for row in runtime_activation_report["parent_receiver_retirement_plan"]
  ]
  split_names = [
    row["candidate_component_name"] for row in runtime_activation_report["rows"]
  ]
  duplicate_names = component_model.duplicate_names(proxy_component_names)
  source_database_path = Path(database_source_path)
  source_unit_path = source_database_path / "aircraft" / "units" / "f16c_block50.json"
  rows = [
    {
      "parent_component_name": row["parent_component_name"],
      "target_hitbox_index": row["target_hitbox_index"],
      "target_path": row["target_path"],
      "base_hitbox_component_count": row["base_hitbox_component_count"],
      "proxy_hitbox_component_count": row["patched_hitbox_component_count"],
      "parent_absent_after_proxy_patch": row["parent_absent_after_patch"],
      "split_component_names": row["split_component_names"],
      "split_component_present_count": row["split_component_present_count"],
      "duplicate_component_name_count": row["duplicate_component_name_count"],
      "behavior_status": row["behavior_status"],
      "proxy_database_status": "ready_for_opt_in_training_database_path",
    }
    for row in runtime_behavior_report["rows"]
  ]
  return {
    "schema_version": TARGET_GEOMETRY_TRAINING_PROXY_SCHEMA_VERSION,
    "status": "target_geometry_training_proxy_database_generated_tg_p7_r3",
    "generated_on": "2026-06-13",
    "source_runtime_activation_schema_version": runtime_activation_report[
      "schema_version"
    ],
    "source_runtime_behavior_schema_version": runtime_behavior_report[
      "schema_version"
    ],
    "target_unit": runtime_activation_report["activation_policy"]["target_unit"],
    "feature_flag": runtime_activation_report["activation_policy"][
      "feature_flag"
    ],
    "runtime_database": {
      "source_database_path": filesystem.display_path(source_database_path, REPO_ROOT),
      "source_f16c_unit_path": filesystem.display_path(source_unit_path, REPO_ROOT),
      "proxy_database_path": (
        filesystem.display_path(proxy_database_dir, REPO_ROOT)
        if proxy_database_dir is not None
        else ""
      ),
      "proxy_f16c_unit_path": (
        filesystem.display_path(
          proxy_database_dir / "aircraft" / "units" / "f16c_block50.json",
          REPO_ROOT,
        )
        if proxy_database_dir is not None
        else ""
      ),
      "source_f16c_unit_sha256": (
        filesystem.sha256_file(source_unit_path) if source_unit_path.is_file() else ""
      ),
      "proxy_f16c_unit_sha256": "",
    },
    "training_runtime_contract": {
      "runtime_config_key": "runtime.database_path",
      "feature_flag": runtime_activation_report["activation_policy"][
        "feature_flag"
      ],
      "target_path": runtime_activation_report["activation_policy"][
        "target_path"
      ],
      "maintained_execution_entrypoint": (
        "python.rl.runtime.world_batch_vec_env.WorldBatchVecEnv"
      ),
      "maintained_cooperative_entrypoint": (
        "python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv"
      ),
      "default_database_path_remains": filesystem.display_path(
        DEFAULT_RUNTIME_DATABASE,
        REPO_ROOT,
      ),
      "opt_in_training_config_required": True,
      "opt_in_training_config_path": filesystem.display_path(
        TARGET_GEOMETRY_PROXY_TRAINING_CONFIG,
        REPO_ROOT,
      ),
      "training_path_wired": True,
    },
    "summary": {
      "default_database_component_count": len(base_component_names),
      "proxy_database_component_count": len(proxy_component_names),
      "component_count_delta": (
        len(proxy_component_names) - len(base_component_names)
      ),
      "retired_parent_component_count": sum(
        1 for parent_name in parent_names if parent_name not in proxy_component_names
      ),
      "split_receiver_component_count": sum(
        1 for split_name in split_names if split_name in proxy_component_names
      ),
      "duplicate_component_name_count": len(duplicate_names),
      "behavior_regression_pass": bool(
        runtime_behavior_report["summary"]["behavior_regression_pass"]
      ),
      "proxy_database_materialized": proxy_database_dir is not None,
      "repository_unit_database_modified": False,
      "default_runtime_split_receiver_active_count": 0,
      "proxy_runtime_split_receiver_active_count": sum(
        1 for split_name in split_names if split_name in proxy_component_names
      ),
      "training_database_path_ready": proxy_database_dir is not None,
    },
    "rows": rows,
    "patch_operations": operations,
    "proxy_component_names": proxy_component_names,
    "duplicate_component_names": duplicate_names,
    "acceptance_gate": [
      "default_database_component_count_equals_26",
      "proxy_database_component_count_equals_32",
      "retired_parent_component_count_equals_2",
      "split_receiver_component_count_equals_8",
      "duplicate_component_name_count_equals_0",
      "behavior_regression_pass_is_true",
      "repository_unit_database_modified_is_false",
      "runtime_database_path_override_required_for_training_proxy",
    ],
    "authority_boundary": {
      **runtime_behavior_report["authority_boundary"],
      "unit_database_modified": False,
      "default_runtime_active_component": False,
      "training_proxy_database_generated": proxy_database_dir is not None,
      "training_proxy_runtime_active_component": proxy_database_dir is not None,
      "training_proxy_feature_flag_required": True,
      "training_path_wired": True,
      "true_internal_component_geometry": False,
    },
  }
