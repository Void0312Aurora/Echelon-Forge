"""JSON and CSV artifact writers for airframe review reports."""

from __future__ import annotations

import copy
import csv
import json
import shutil
from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import filesystem
from tools.geometry.airframe_review.constants import DEFAULT_RUNTIME_DATABASE, REPO_ROOT
from tools.geometry.airframe_review.primitives import _strip_internal_keys


def write_manifest(manifest: dict[str, Any], output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "manifest.json"
  output_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  return output_path


def write_mapping_candidate(mapping: dict[str, Any], output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "f16c_geometry_mapping_candidate_20260611.json"
  output_path.write_text(
    json.dumps(mapping, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  return output_path


def write_component_binding_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "component_binding_report_20260611.json"
  csv_path = output_dir / "component_binding_report_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "component_name",
    "system",
    "critical",
    "hitbox_index",
    "bound_region_id",
    "bound_region_role",
    "component_overlap_fraction",
    "region_overlap_fraction",
    "center_inside_bound_region",
    "center_distance_m",
    "outer_envelope_containment_fraction",
    "review_status",
    "review_semantics",
    "review_severity",
    "anomalies",
    "geometry_observations",
    "suppressed_anomalies",
    "semantic_region_ids",
    "side_sign_mismatch",
    "blocked_region_binding",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          key: (
            ";".join(row[key])
            if key
            in {
              "anomalies",
              "geometry_observations",
              "suppressed_anomalies",
              "semantic_region_ids",
            }
            else row["side_sign_relation"]["side_sign_mismatch"]
            if key == "side_sign_mismatch"
            else json.dumps(row[key], sort_keys=True)
            if key == "blocked_region_binding"
            else row[key]
          )
          for key in fieldnames
        }
      )
  return json_path, csv_path


def write_review_point_diagnostics(
  diagnostics: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "review_point_diagnostics_20260611.json"
  csv_path = output_dir / "review_point_diagnostics_20260611.csv"
  json_path.write_text(
    json.dumps(diagnostics, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "point_index",
    "point_id",
    "aspect",
    "point_m",
    "nearest_outer_region_id",
    "nearest_outer_distance_m",
    "inside_outer_region_count",
    "nearest_component_name",
    "nearest_component_distance_m",
    "inside_component_count",
    "candidate_component_count",
    "interpretation",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in diagnostics["rows"]:
      writer.writerow(
        {
          key: (
            ";".join(str(value) for value in row[key])
            if key == "point_m"
            else row[key]
          )
          for key in fieldnames
        }
      )
  return json_path, csv_path


def write_fine_geometry_proxy_candidate(
  fine_proxy: dict[str, Any],
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "fine_geometry_proxy_candidate_20260611.json"
  serializable = _strip_internal_keys(fine_proxy)
  output_path.write_text(
    json.dumps(serializable, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  return output_path


def write_surface_component_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "surface_component_candidate_20260611.json"
  csv_path = output_dir / "surface_component_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "surface_component_id",
    "source_region_id",
    "source_region_role",
    "surface_role",
    "proxy_kind",
    "linked_internal_component_count",
    "clean_direct_link_count",
    "clean_direct_component_names",
    "cross_region_semantic_component_names",
    "blocked_component_names",
    "bad_geometry_component_names",
    "missing_existing_runtime_component_relations",
    "runtime_relation_status",
    "review_status",
    "review_semantics",
    "review_flags",
    "expected_damage_modes",
    "linked_internal_components",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "surface_component_id": row["surface_component_id"],
          "source_region_id": row["source_region_id"],
          "source_region_role": row["source_region_role"],
          "surface_role": row["surface_role"],
          "proxy_kind": row["proxy_kind"],
          "linked_internal_component_count": row[
            "linked_internal_component_count"
          ],
          "clean_direct_link_count": row["clean_direct_link_count"],
          "clean_direct_component_names": ";".join(
            row["clean_direct_component_names"]
          ),
          "cross_region_semantic_component_names": ";".join(
            row["cross_region_semantic_component_names"]
          ),
          "blocked_component_names": ";".join(row["blocked_component_names"]),
          "bad_geometry_component_names": ";".join(
            row["bad_geometry_component_names"]
          ),
          "missing_existing_runtime_component_relations": ";".join(
            row["missing_existing_runtime_component_relations"]
          ),
          "runtime_relation_status": row["runtime_relation_status"],
          "review_status": row["review_status"],
          "review_semantics": row["review_semantics"],
          "review_flags": ";".join(row["review_flags"]),
          "expected_damage_modes": ";".join(row["expected_damage_modes"]),
          "linked_internal_components": ";".join(
            link["component_name"] for link in row["linked_internal_components"]
          ),
        }
      )
  return json_path, csv_path


def write_semantic_damage_geometry_candidate(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "semantic_damage_geometry_candidate_20260611.json"
  csv_path = output_dir / "semantic_damage_geometry_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "semantic_component_id",
    "surface_component_id",
    "source_region_id",
    "volume_component_role",
    "runtime_system",
    "geometry_primitive",
    "direct_receiver_components",
    "cross_region_receiver_components",
    "receiver_handoff_status",
    "runtime_projection_status",
    "support_center_m",
    "support_span_m",
    "mesh_region_vertex_count",
    "surface_review_semantics",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "semantic_component_id": row["semantic_component_id"],
          "surface_component_id": row["surface_component_id"],
          "source_region_id": row["source_region_id"],
          "volume_component_role": row["volume_component_role"],
          "runtime_system": row["runtime_system"],
          "geometry_primitive": row["geometry_primitive"],
          "direct_receiver_components": ";".join(
            row["direct_receiver_components"]
          ),
          "cross_region_receiver_components": ";".join(
            row["cross_region_receiver_components"]
          ),
          "receiver_handoff_status": row["receiver_handoff_status"],
          "runtime_projection_status": row["runtime_projection_status"],
          "support_center_m": ";".join(
            str(value) for value in row["support_bounds"]["center"]
          ),
          "support_span_m": ";".join(
            str(value) for value in row["support_bounds"]["span"]
          ),
          "mesh_region_vertex_count": row["mesh_region_vertex_count"],
          "surface_review_semantics": row["surface_review_semantics"],
        }
      )
  return json_path, csv_path


def write_internal_component_prior_candidate(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "internal_component_prior_candidate_20260611.json"
  csv_path = output_dir / "internal_component_prior_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "component_name",
    "system",
    "component_role",
    "prior_shape",
    "prior_axis",
    "shape_promotion_status",
    "size_basis",
    "size_evidence_level",
    "nominal_dimensions_m",
    "size_source_urls",
    "bound_region_id",
    "constraint_region_ids",
    "constraint_mode",
    "constraint_bounds_source",
    "placement_bounds_source",
    "constraint_status",
    "original_aabb_containment_fraction",
    "shrink_scale",
    "required_fit_scale",
    "size_preserved",
    "center_shift_m",
    "airframe_projection_center_shift_m",
    "placement_outside_fraction",
    "pre_constraint_outside_fraction",
    "post_constraint_outside_fraction",
    "constrained_center_m",
    "constrained_span_m",
    "component_review_semantics",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "component_name": row["component_name"],
          "system": row["system"],
          "component_role": row["component_role"],
          "prior_shape": row["prior_shape"],
          "prior_axis": row["prior_axis"],
          "shape_promotion_status": row["shape_promotion_status"],
          "size_basis": row["size_basis"],
          "size_evidence_level": row["size_evidence_level"],
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "size_source_urls": ";".join(row["size_source_urls"]),
          "bound_region_id": row["bound_region_id"],
          "constraint_region_ids": ";".join(row["constraint_region_ids"]),
          "constraint_mode": row["constraint_mode"],
          "constraint_bounds_source": row["constraint_bounds_source"],
          "placement_bounds_source": row["placement_bounds_source"],
          "constraint_status": row["constraint_status"],
          "original_aabb_containment_fraction": row[
            "original_aabb_containment_fraction"
          ],
          "shrink_scale": row["constraint_adjustment"]["shrink_scale"],
          "required_fit_scale": row["constraint_adjustment"]["required_fit_scale"],
          "size_preserved": row["constraint_adjustment"]["size_preserved"],
          "center_shift_m": row["constraint_adjustment"]["center_shift_m"],
          "airframe_projection_center_shift_m": row["constraint_adjustment"][
            "airframe_projection_center_shift_m"
          ],
          "placement_outside_fraction": row["constraint_adjustment"][
            "placement_outside_fraction"
          ],
          "pre_constraint_outside_fraction": row["constraint_adjustment"][
            "pre_constraint_outside_fraction"
          ],
          "post_constraint_outside_fraction": row["constraint_adjustment"][
            "post_constraint_outside_fraction"
          ],
          "constrained_center_m": ";".join(
            str(value) for value in row["constrained_geometry"]["center_m"]
          ),
          "constrained_span_m": ";".join(
            str(value) for value in row["constrained_geometry"]["bounds"]["span"]
          ),
          "component_review_semantics": row["component_review_semantics"],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def write_cross_region_held_component_segments_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "cross_region_held_component_segments_20260611.json"
  csv_path = output_dir / "cross_region_held_component_segments_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "parent_component_name",
    "segment_id",
    "segment_index",
    "segment_role",
    "owner_region_ids",
    "segment_shape",
    "segment_axis",
    "source_parent_segment_shape",
    "shape_promotion_status",
    "center_offset_m",
    "nominal_dimensions_m",
    "center_m",
    "span_m",
    "inside_parent_prior_bounds",
    "inside_whole_airframe_bounds",
    "parent_prior_outside_fraction",
    "whole_airframe_outside_fraction",
    "source_basis",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "parent_component_name": row["parent_component_name"],
          "segment_id": row["segment_id"],
          "segment_index": row["segment_index"],
          "segment_role": row["segment_role"],
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "segment_shape": row["segment_shape"],
          "segment_axis": row["segment_axis"],
          "source_parent_segment_shape": row["source_parent_segment_shape"],
          "shape_promotion_status": row["shape_promotion_status"],
          "center_offset_m": ";".join(
            str(value) for value in row["center_offset_m"]
          ),
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "center_m": ";".join(str(value) for value in row["geometry"]["center_m"]),
          "span_m": ";".join(
            str(value) for value in row["geometry"]["bounds"]["span"]
          ),
          "inside_parent_prior_bounds": row["inside_parent_prior_bounds"],
          "inside_whole_airframe_bounds": row["inside_whole_airframe_bounds"],
          "parent_prior_outside_fraction": row["parent_prior_outside_fraction"],
          "whole_airframe_outside_fraction": row[
            "whole_airframe_outside_fraction"
          ],
          "source_basis": row["source_basis"],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def write_cross_region_ownership_split_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "cross_region_ownership_split_candidate_20260611.json"
  csv_path = output_dir / "cross_region_ownership_split_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "parent_component_name",
    "parent_system",
    "parent_review_semantics",
    "recommended_ownership_decision",
    "decision_status",
    "parent_receiver_runtime_policy",
    "segment_count",
    "candidate_runtime_component_names",
    "owner_region_ids",
    "parse_ready_runtime_candidate_count",
    "silhouette_exposure_segment_count",
    "outside_whole_airframe_segment_count",
    "shape_promotion_segment_count",
    "runtime_active_split_component_count",
    "runtime_activation_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "parent_component_name": row["parent_component_name"],
          "parent_system": row["parent_system"],
          "parent_review_semantics": row["parent_review_semantics"],
          "recommended_ownership_decision": row[
            "recommended_ownership_decision"
          ],
          "decision_status": row["decision_status"],
          "parent_receiver_runtime_policy": row["parent_receiver_runtime_policy"],
          "segment_count": row["segment_count"],
          "candidate_runtime_component_names": ";".join(
            row["candidate_runtime_component_names"]
          ),
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "parse_ready_runtime_candidate_count": row[
            "parse_ready_runtime_candidate_count"
          ],
          "silhouette_exposure_segment_count": row[
            "silhouette_exposure_segment_count"
          ],
          "outside_whole_airframe_segment_count": row[
            "outside_whole_airframe_segment_count"
          ],
          "shape_promotion_segment_count": row["shape_promotion_segment_count"],
          "runtime_active_split_component_count": row[
            "runtime_active_split_component_count"
          ],
          "runtime_activation_status": row["runtime_activation_status"],
        }
      )
  return json_path, csv_path


def write_target_geometry_runtime_activation_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "target_geometry_runtime_activation_candidate_20260613.json"
  csv_path = output_dir / "target_geometry_runtime_activation_candidate_20260613.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "candidate_component_name",
    "parent_component_name",
    "parent_system",
    "recommended_ownership_decision",
    "parent_receiver_runtime_policy",
    "segment_role",
    "owner_region_ids",
    "geometry_primitive",
    "offset_m",
    "size_m",
    "runtime_loader_contract_status",
    "runtime_activation_status",
    "behavior_test_status",
    "feature_flag",
    "unit_database_patch_path",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "candidate_component_name": row["candidate_component_name"],
          "parent_component_name": row["parent_component_name"],
          "parent_system": row["parent_system"],
          "recommended_ownership_decision": row[
            "recommended_ownership_decision"
          ],
          "parent_receiver_runtime_policy": row[
            "parent_receiver_runtime_policy"
          ],
          "segment_role": row["segment_role"],
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "geometry_primitive": row["geometry_primitive"],
          "offset_m": ";".join(str(value) for value in row["offset_m"]),
          "size_m": ";".join(str(value) for value in row["size_m"]),
          "runtime_loader_contract_status": row[
            "runtime_loader_contract_status"
          ],
          "runtime_activation_status": row["runtime_activation_status"],
          "behavior_test_status": row["behavior_test_status"],
          "feature_flag": row["feature_flag"],
          "unit_database_patch_path": row["unit_database_patch_path"],
        }
      )
  return json_path, csv_path


def write_target_geometry_runtime_behavior_regression_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "target_geometry_runtime_behavior_regression_20260613.json"
  csv_path = output_dir / "target_geometry_runtime_behavior_regression_20260613.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "parent_component_name",
    "target_hitbox_index",
    "target_path",
    "base_hitbox_component_count",
    "patched_hitbox_component_count",
    "parent_present_before_patch",
    "parent_absent_after_patch",
    "split_component_names",
    "split_component_present_count",
    "duplicate_component_name_count",
    "behavior_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "parent_component_name": row["parent_component_name"],
          "target_hitbox_index": row["target_hitbox_index"],
          "target_path": row["target_path"],
          "base_hitbox_component_count": row[
            "base_hitbox_component_count"
          ],
          "patched_hitbox_component_count": row[
            "patched_hitbox_component_count"
          ],
          "parent_present_before_patch": row["parent_present_before_patch"],
          "parent_absent_after_patch": row["parent_absent_after_patch"],
          "split_component_names": ";".join(row["split_component_names"]),
          "split_component_present_count": row["split_component_present_count"],
          "duplicate_component_name_count": row[
            "duplicate_component_name_count"
          ],
          "behavior_status": row["behavior_status"],
        }
      )
  return json_path, csv_path


def write_target_geometry_training_proxy_database_report(
  report: dict[str, Any],
  proxy_aircraft: dict[str, Any],
  output_dir: Path,
  *,
  source_database_path: Path = DEFAULT_RUNTIME_DATABASE,
) -> tuple[dict[str, Any], Path, Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  proxy_database_dir = output_dir / "target_geometry_training_proxy_database_20260613"
  if proxy_database_dir.exists():
    shutil.rmtree(proxy_database_dir)
  shutil.copytree(source_database_path, proxy_database_dir)

  proxy_unit_path = proxy_database_dir / "aircraft" / "units" / "f16c_block50.json"
  proxy_unit_path.write_text(
    json.dumps(proxy_aircraft, indent=2, sort_keys=True, ensure_ascii=False)
    + "\n",
    encoding="utf-8",
  )

  materialized_report = copy.deepcopy(report)
  materialized_report["runtime_database"].update(
    {
      "proxy_database_path": filesystem.display_path(proxy_database_dir, REPO_ROOT),
      "proxy_f16c_unit_path": filesystem.display_path(proxy_unit_path, REPO_ROOT),
      "proxy_f16c_unit_sha256": filesystem.sha256_file(proxy_unit_path),
    }
  )
  materialized_report["summary"]["proxy_database_materialized"] = True
  materialized_report["summary"]["training_database_path_ready"] = True
  materialized_report["authority_boundary"][
    "training_proxy_database_generated"
  ] = True
  materialized_report["authority_boundary"][
    "training_proxy_runtime_active_component"
  ] = True

  json_path = output_dir / "target_geometry_training_proxy_database_20260613.json"
  json_path.write_text(
    json.dumps(materialized_report, indent=2, sort_keys=True, ensure_ascii=False)
    + "\n",
    encoding="utf-8",
  )
  return materialized_report, json_path, proxy_database_dir, proxy_unit_path


def write_airframe_constraint_correction_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "airframe_constraint_correction_candidate_20260611.json"
  csv_path = output_dir / "airframe_constraint_correction_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "item_id",
    "record_type",
    "parent_component_name",
    "system",
    "component_role",
    "prior_shape",
    "prior_axis",
    "nominal_dimensions_m",
    "size_evidence_level",
    "bound_region_id",
    "owner_region_ids",
    "current_outside_views",
    "current_outside_sample_count",
    "candidate_outside_views",
    "candidate_outside_sample_count",
    "outside_sample_reduction",
    "candidate_center_shift_m",
    "candidate_center_m",
    "triage_status",
    "recommended_action",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "item_id": row["item_id"],
          "record_type": row["record_type"],
          "parent_component_name": row["parent_component_name"],
          "system": row["system"],
          "component_role": row["component_role"],
          "prior_shape": row["prior_shape"],
          "prior_axis": row["prior_axis"],
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "size_evidence_level": row["size_evidence_level"],
          "bound_region_id": row["bound_region_id"],
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "current_outside_views": ";".join(
            row["current_silhouette"]["outside_views"]
          ),
          "current_outside_sample_count": row["current_silhouette"][
            "outside_sample_count"
          ],
          "candidate_outside_views": ";".join(
            row["candidate_silhouette"]["outside_views"]
          ),
          "candidate_outside_sample_count": row["candidate_silhouette"][
            "outside_sample_count"
          ],
          "outside_sample_reduction": row["outside_sample_reduction"],
          "candidate_center_shift_m": row["candidate_center_shift_m"],
          "candidate_center_m": ";".join(
            str(value) for value in row["candidate_center_m"]
          ),
          "triage_status": row["triage_status"],
          "recommended_action": row["recommended_action"],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def write_whole_airframe_contour_containment_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "whole_airframe_contour_containment_20260614.json"
  csv_path = output_dir / "whole_airframe_contour_containment_20260614.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  fieldnames = [
    "item_id",
    "record_type",
    "component_name",
    "parent_component_name",
    "system",
    "prior_shape",
    "prior_axis",
    "nominal_dimensions_m",
    "owner_region_ids",
    "outside_views",
    "outside_sample_count",
    "max_outside_distance_m",
    "exceeds_tolerance",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "item_id": row["item_id"],
          "record_type": row["record_type"],
          "component_name": row["component_name"],
          "parent_component_name": row["parent_component_name"],
          "system": row["system"],
          "prior_shape": row["prior_shape"],
          "prior_axis": row["prior_axis"],
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "outside_views": ";".join(row["outside_views"]),
          "outside_sample_count": row["outside_sample_count"],
          "max_outside_distance_m": row["max_outside_distance_m"],
          "exceeds_tolerance": row["exceeds_tolerance"],
        }
      )
  return json_path, csv_path


def write_subcomponent_shape_placement_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "subcomponent_shape_placement_candidate_20260611.json"
  csv_path = output_dir / "subcomponent_shape_placement_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "item_id",
    "record_type",
    "parent_component_name",
    "system",
    "component_role",
    "current_shape",
    "current_axis",
    "candidate_shape_family",
    "candidate_evaluation_shape",
    "candidate_evaluation_axis",
    "nominal_dimensions_m",
    "size_evidence_level",
    "bound_region_id",
    "owner_region_ids",
    "current_outside_views",
    "current_outside_sample_count",
    "candidate_outside_views",
    "candidate_outside_sample_count",
    "outside_sample_reduction",
    "candidate_center_shift_m",
    "candidate_center_m",
    "centerline_candidate_outside_views",
    "centerline_candidate_outside_sample_count",
    "centerline_candidate_center_offset_m",
    "centerline_candidate_center_m",
    "centerline_candidate_shift_m",
    "centerline_incremental_outside_sample_reduction",
    "centerline_outside_sample_reduction",
    "latest_candidate_stage",
    "latest_candidate_outside_views",
    "latest_candidate_outside_sample_count",
    "latest_candidate_center_m",
    "latest_candidate_total_center_offset_m",
    "latest_candidate_incremental_shift_m",
    "latest_incremental_outside_sample_reduction",
    "latest_outside_sample_reduction",
    "shape_design_status",
    "centerline_candidate_status",
    "latest_candidate_status",
    "recommended_action",
    "centerline_candidate_recommended_action",
    "latest_candidate_recommended_action",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "item_id": row["item_id"],
          "record_type": row["record_type"],
          "parent_component_name": row["parent_component_name"],
          "system": row["system"],
          "component_role": row["component_role"],
          "current_shape": row["current_shape"],
          "current_axis": row["current_axis"],
          "candidate_shape_family": row["candidate_shape_family"],
          "candidate_evaluation_shape": row["candidate_evaluation_shape"],
          "candidate_evaluation_axis": row["candidate_evaluation_axis"],
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "size_evidence_level": row["size_evidence_level"],
          "bound_region_id": row["bound_region_id"],
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "current_outside_views": ";".join(
            row["current_silhouette"]["outside_views"]
          ),
          "current_outside_sample_count": row["current_silhouette"][
            "outside_sample_count"
          ],
          "candidate_outside_views": ";".join(
            row["candidate_silhouette"]["outside_views"]
          ),
          "candidate_outside_sample_count": row["candidate_silhouette"][
            "outside_sample_count"
          ],
          "outside_sample_reduction": row["outside_sample_reduction"],
          "candidate_center_shift_m": row["candidate_center_shift_m"],
          "candidate_center_m": ";".join(
            str(value) for value in row["candidate_geometry"]["center_m"]
          ),
          "centerline_candidate_outside_views": ";".join(
            row["centerline_candidate_silhouette"]["outside_views"]
          ),
          "centerline_candidate_outside_sample_count": row[
            "centerline_candidate_silhouette"
          ]["outside_sample_count"],
          "centerline_candidate_center_offset_m": ";".join(
            str(value)
            for value in row["centerline_candidate_center_offset_m"]
          ),
          "centerline_candidate_center_m": ";".join(
            str(value)
            for value in row["centerline_candidate_geometry"]["center_m"]
          ),
          "centerline_candidate_shift_m": row[
            "centerline_candidate_shift_m"
          ],
          "centerline_incremental_outside_sample_reduction": row[
            "centerline_incremental_outside_sample_reduction"
          ],
          "centerline_outside_sample_reduction": row[
            "centerline_outside_sample_reduction"
          ],
          "latest_candidate_stage": row["latest_candidate_stage"],
          "latest_candidate_outside_views": ";".join(
            row["latest_candidate_silhouette"]["outside_views"]
          ),
          "latest_candidate_outside_sample_count": row[
            "latest_candidate_silhouette"
          ]["outside_sample_count"],
          "latest_candidate_center_m": ";".join(
            str(value) for value in row["latest_candidate_geometry"]["center_m"]
          ),
          "latest_candidate_total_center_offset_m": ";".join(
            str(value) for value in row["latest_candidate_total_center_offset_m"]
          ),
          "latest_candidate_incremental_shift_m": row[
            "latest_candidate_incremental_shift_m"
          ],
          "latest_incremental_outside_sample_reduction": row[
            "latest_incremental_outside_sample_reduction"
          ],
          "latest_outside_sample_reduction": row[
            "latest_outside_sample_reduction"
          ],
          "shape_design_status": row["shape_design_status"],
          "centerline_candidate_status": row[
            "centerline_candidate_status"
          ],
          "latest_candidate_status": row["latest_candidate_status"],
          "recommended_action": row["recommended_action"],
          "centerline_candidate_recommended_action": row[
            "centerline_candidate_recommended_action"
          ],
          "latest_candidate_recommended_action": row[
            "latest_candidate_recommended_action"
          ],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def write_semantic_parent_child_layout_candidate(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "semantic_parent_child_layout_candidate_20260611.json"
  csv_path = output_dir / "semantic_parent_child_layout_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "parent_semantic_component_id",
    "parent_surface_component_id",
    "source_region_id",
    "volume_component_role",
    "geometry_primitive",
    "bound_receiver_count",
    "extra_receiver_slot_count",
    "primary_receiver_component_name",
    "extra_receiver_component_names",
    "cross_region_held_receiver_names",
    "cross_region_held_segment_overlay_count",
    "cross_region_held_segment_overlay_ids",
    "child_receiver_prior_shapes",
    "held_segment_count",
    "parent_receiver_handoff_status",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "parent_semantic_component_id": row["parent_semantic_component_id"],
          "parent_surface_component_id": row["parent_surface_component_id"],
          "source_region_id": row["source_region_id"],
          "volume_component_role": row["volume_component_role"],
          "geometry_primitive": row["geometry_primitive"],
          "bound_receiver_count": row["bound_receiver_count"],
          "extra_receiver_slot_count": row["extra_receiver_slot_count"],
          "primary_receiver_component_name": row[
            "primary_receiver_component_name"
          ],
          "extra_receiver_component_names": ";".join(
            row["extra_receiver_component_names"]
          ),
          "cross_region_held_receiver_names": ";".join(
            row["cross_region_held_receiver_names"]
          ),
          "cross_region_held_segment_overlay_count": row[
            "cross_region_held_segment_overlay_count"
          ],
          "cross_region_held_segment_overlay_ids": ";".join(
            segment["segment_id"]
            for segment in row["cross_region_held_segment_overlays"]
          ),
          "child_receiver_prior_shapes": ";".join(
            (
              f'{child["component_name"]}:{child["prior_shape"]}'
              f':segments={child["held_segment_count"]}'
            )
            for child in row["child_receiver_priors"]
          ),
          "held_segment_count": sum(
            child["held_segment_count"] for child in row["child_receiver_priors"]
          ),
          "parent_receiver_handoff_status": row[
            "parent_receiver_handoff_status"
          ],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path
