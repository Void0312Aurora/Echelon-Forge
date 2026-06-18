from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.geometry import airframe_geometry_review
from tools.geometry.airframe_review import component_model, constants, gltf_io
from tests.tools.airframe_review_fixtures import require_airframe_geometry_extra


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_airframe_geometry_review_cli_writes_manifest(tmp_path: Path) -> None:
  require_airframe_geometry_extra()
  stale_isolated_page = (
    tmp_path
    / "component_review_views"
    / "surface_links"
    / "surface-vertical-tail-skin-afterburner-nozzle.html"
  )
  stale_isolated_page.parent.mkdir(parents=True)
  stale_isolated_page.write_text("stale view from prior generation", encoding="utf-8")
  for stale_dir in (
    "semantic_damage_geometry_views",
    "internal_component_prior_views",
    "semantic_parent_child_layout_views",
    "subcomponent_shape_placement_views",
  ):
    stale_path = tmp_path / stale_dir / "stale.html"
    stale_path.parent.mkdir(parents=True)
    stale_path.write_text("stale intermediate view", encoding="utf-8")
  for stale_file in (
    "top.svg",
    "side.svg",
    "front.svg",
    "fine_proxy_top.svg",
    "fine_proxy_side.svg",
    "fine_proxy_front.svg",
    "fine_proxy_review_dashboard.html",
    "human_review_triage.html",
  ):
    (tmp_path / stale_file).write_text("stale intermediate visual", encoding="utf-8")

  result = subprocess.run(
    [
      sys.executable,
      "tools/geometry/airframe_geometry_review.py",
      "--out",
      str(tmp_path),
    ],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )

  summary = json.loads(result.stdout)
  assert summary["status"] == "target_geometry_manifest_generated_review_only"
  assert summary["triangle_count"] == 4504
  assert summary["component_count"] == 26
  assert summary["review_point_count"] >= 10
  assert summary["inside_outer_region_point_count"] > 0
  assert summary["inflated_fallback_count"] == 0
  assert summary["cross_region_held_segment_count"] == 8
  assert summary["cross_region_held_segment_outside_airframe_count"] == 0
  assert summary["cross_region_held_segment_shape_promotion_count"] == 5
  assert summary["internal_component_prior_shape_promotion_count"] == 9
  assert (
    summary["semantic_parent_child_layout_cross_region_held_segment_count"] == 8
  )
  assert summary["airframe_constraint_item_count"] == 34
  # Projected audit-mesh triangle union + shape-aware sampling now leaves no
  # receiver prior outside the whole-airframe contour.
  assert summary["airframe_constraint_silhouette_exposure_item_count"] == 0
  assert summary["airframe_constraint_center_shift_resolves_item_count"] == 0
  assert summary["airframe_constraint_size_or_shape_review_item_count"] == 0
  # Whole-airframe projected mesh contour containment diagnostic.
  assert summary["whole_airframe_contour_method"] == (
    "projected_mesh_triangle_union"
  )
  assert summary["whole_airframe_contour_tolerance_m"] == 0.05
  assert summary["whole_airframe_contour_item_count"] == 26
  assert (
    summary["whole_airframe_contour_excluded_review_only_split_segment_count"]
    == 8
  )
  assert summary["whole_airframe_contour_exceeds_tolerance_item_count"] == 0
  assert summary["whole_airframe_contour_max_outside_distance_m"] == 0.0
  assert summary["whole_airframe_contour_exceeding_item_ids"] == []
  for view in ("top", "side", "front"):
    assert summary["whole_airframe_contour_contours"][view]["status"] == (
      "projected_mesh_triangle_union"
    )
    assert summary["whole_airframe_contour_contours"][view][
      "source_triangle_count"
    ] == 4504
    assert summary["whole_airframe_contour_contours"][view]["polygon_count"] == 1
    assert summary["whole_airframe_contour_contours"][view][
      "contour_point_count"
    ] >= 100
  assert summary["cross_region_ownership_parent_decision_count"] == 2
  assert summary["cross_region_ownership_split_receiver_candidate_count"] == 8
  assert (
    summary["cross_region_ownership_zero_silhouette_exposure_split_candidate_count"]
    == 8
  )
  assert summary["cross_region_ownership_runtime_active_split_component_count"] == 0
  assert summary["target_geometry_runtime_activation_candidate_count"] == 8
  assert summary["target_geometry_runtime_activation_parse_ready_count"] == 8
  assert summary["target_geometry_runtime_activation_patch_component_count"] == 8
  assert (
    summary[
      "target_geometry_runtime_activation_parent_retirement_candidate_count"
    ]
    == 2
  )
  assert summary["target_geometry_runtime_activation_runtime_active_count"] == 0
  assert summary["target_geometry_runtime_behavior_base_component_count"] == 26
  assert (
    summary["target_geometry_runtime_behavior_projected_component_count"] == 32
  )
  assert (
    summary["target_geometry_runtime_behavior_retired_parent_component_count"] == 2
  )
  assert (
    summary["target_geometry_runtime_behavior_split_component_added_count"] == 8
  )
  assert (
    summary["target_geometry_runtime_behavior_duplicate_component_name_count"] == 0
  )
  assert summary["target_geometry_runtime_behavior_regression_pass"] is True
  assert (
    summary["target_geometry_training_proxy_default_database_component_count"]
    == 26
  )
  assert summary["target_geometry_training_proxy_database_component_count"] == 32
  assert (
    summary["target_geometry_training_proxy_split_receiver_component_count"] == 8
  )
  assert summary["target_geometry_training_proxy_database_materialized"] is True
  assert summary["subcomponent_shape_placement_candidate_count"] == 0
  assert summary["subcomponent_shape_placement_resolves_count"] == 0
  assert summary["subcomponent_shape_placement_unresolved_count"] == 0
  assert summary["subcomponent_centerline_resolves_count"] == 0
  assert summary["subcomponent_centerline_unresolved_count"] == 0
  assert summary["subcomponent_latest_resolves_count"] == 0
  assert summary["subcomponent_latest_unresolved_count"] == 0

  manifest_path = tmp_path / "manifest.json"
  assert manifest_path.is_file()
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert manifest["paths"]["audit_scene_gltf"].endswith("gltf/scene.gltf")
  assert len(manifest["file_hashes"]["runtime_visual_glb_sha256"]) == 64

  mapping_path = tmp_path / "f16c_geometry_mapping_candidate_20260611.json"
  assert mapping_path.is_file()
  mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
  assert mapping["schema_version"] == "a2.target_geometry_mapping_candidate.v1"
  assert mapping["status"] == "outer_region_candidate_generated_review_only"
  assert mapping["mesh_node_name_quality"]["decision"] == (
    "do_not_auto_classify_regions_from_node_names_only"
  )
  region_ids = {region["id"] for region in mapping["outer_regions"]}
  assert {
    "nose_radome",
    "forward_fuselage",
    "canopy",
    "intake",
    "left_wing",
    "right_wing",
    "vertical_tail",
  }.issubset(region_ids)
  forward = next(
    region for region in mapping["outer_regions"] if region["id"] == "forward_fuselage"
  )
  assert forward["bounds"]["min"][0] < 4.0 < forward["bounds"]["max"][0]
  assert forward["manual_review_required"] is True
  assert forward["source_mesh_node_candidates"]

  for svg_name in ("top.svg", "side.svg", "front.svg"):
    assert not (tmp_path / svg_name).exists()

  # Whole-airframe projected mesh contour containment artifacts.
  contour_json_path = tmp_path / "whole_airframe_contour_containment_20260614.json"
  contour_csv_path = tmp_path / "whole_airframe_contour_containment_20260614.csv"
  assert contour_json_path.is_file()
  assert contour_csv_path.is_file()
  contour_report = json.loads(contour_json_path.read_text(encoding="utf-8"))
  assert contour_report["schema_version"] == (
    "a2.target_geometry_whole_airframe_contour_containment.v1"
  )
  assert contour_report["contour_method"] == "projected_mesh_triangle_union"
  assert contour_report["tolerance_m"] == 0.05
  assert contour_report["summary"]["item_count"] == 26
  assert contour_report["summary"]["excluded_review_only_split_segment_count"] == 8
  assert contour_report["summary"]["exceeds_tolerance_item_count"] == 0
  assert contour_report["authority_boundary"][
    "projected_mesh_contour_diagnostic_only"
  ] is True
  assert contour_report["authority_boundary"]["not_runtime_collision_mesh"] is True
  contour_csv = contour_csv_path.read_text(encoding="utf-8")
  assert "left_wing_fuel_cell" in contour_csv
  assert "max_outside_distance_m" in contour_csv
  for view in ("top", "side", "front"):
    contour_svg = tmp_path / f"whole_airframe_contour_{view}.svg"
    assert contour_svg.is_file()
    svg_text = contour_svg.read_text(encoding="utf-8")
    assert "projected audit-mesh contour" in svg_text
    assert "projected_mesh_triangle_union" in svg_text
    assert "review-only" in svg_text
  contour_dashboard = tmp_path / "whole_airframe_contour_dashboard.html"
  assert contour_dashboard.is_file()
  dashboard_text = contour_dashboard.read_text(encoding="utf-8")
  assert "Whole-Airframe Projected Mesh Contour Containment" in dashboard_text
  assert "wing_spar_center" in dashboard_text

  component_json_path = tmp_path / "component_binding_report_20260611.json"
  component_csv_path = tmp_path / "component_binding_report_20260611.csv"
  assert component_json_path.is_file()
  assert component_csv_path.is_file()
  report = json.loads(component_json_path.read_text(encoding="utf-8"))
  assert report["summary"]["component_count"] == 26
  assert "component_name,bound_region_id" not in component_csv_path.read_text(
    encoding="utf-8"
  )
  assert "apg68_radar_array" in component_csv_path.read_text(encoding="utf-8")

  diagnostics_json_path = tmp_path / "review_point_diagnostics_20260611.json"
  diagnostics_csv_path = tmp_path / "review_point_diagnostics_20260611.csv"
  assert diagnostics_json_path.is_file()
  assert diagnostics_csv_path.is_file()
  diagnostics = json.loads(diagnostics_json_path.read_text(encoding="utf-8"))
  point_rows = {row["point_id"]: row for row in diagnostics["rows"]}
  assert point_rows["nose_axis_4m"]["nearest_outer_distance_m"] == 0.0
  assert "nose_axis_4m" in diagnostics_csv_path.read_text(encoding="utf-8")

  fine_proxy_path = tmp_path / "fine_geometry_proxy_candidate_20260611.json"
  assert fine_proxy_path.is_file()
  fine_proxy = json.loads(fine_proxy_path.read_text(encoding="utf-8"))
  assert fine_proxy["schema_version"] == "a2.target_geometry_fine_proxy_candidate.v1"
  assert fine_proxy["summary"]["proxy_count"] == len(mapping["outer_regions"])
  assert fine_proxy["summary"]["total_proxy_support_volume_ratio"] < 0.75
  assert fine_proxy["summary"]["mesh_derived_silhouette_count"] == 14
  assert fine_proxy["summary"]["inflated_fallback_count"] == 0
  assert result.stdout.find("fine_proxy_count") >= 0
  assert result.stdout.find("mesh_derived_silhouette_count") >= 0
  assert result.stdout.find("inflated_fallback_count") >= 0
  assert result.stdout.find("fine_proxy_support_volume_ratio") >= 0
  assert result.stdout.find("current_visual_result") >= 0
  assert result.stdout.find("fine_proxy_review_dashboard") == -1
  assert result.stdout.find("human_review_triage") == -1
  assert result.stdout.find("isolated_component_review_index") == -1
  assert result.stdout.find("isolated_component_review_manifest") == -1
  assert result.stdout.find("surface_component_count") >= 0
  assert result.stdout.find("semantic_damage_volume_count") >= 0
  assert result.stdout.find("semantic_damage_geometry_review_index") == -1
  assert result.stdout.find("internal_component_prior_count") >= 0
  assert result.stdout.find("internal_component_prior_review_index") == -1
  assert result.stdout.find("semantic_parent_child_layout_parent_count") >= 0
  assert result.stdout.find("semantic_parent_child_layout_review_index") == -1
  assert result.stdout.find("cross_region_ownership_split_json") >= 0
  assert result.stdout.find("cross_region_ownership_split_receiver_candidate_count") >= 0
  assert result.stdout.find("target_geometry_training_proxy_database") >= 0
  assert (
    result.stdout.find("target_geometry_training_proxy_database_component_count")
    >= 0
  )

  assert not stale_isolated_page.exists()
  for retired_path in (
    "component_review_views",
    "semantic_damage_geometry_views",
    "internal_component_prior_views",
    "semantic_parent_child_layout_views",
    "subcomponent_shape_placement_views",
    "fine_proxy_top.svg",
    "fine_proxy_side.svg",
    "fine_proxy_front.svg",
    "fine_proxy_review_dashboard.html",
    "human_review_triage.html",
  ):
    assert not (tmp_path / retired_path).exists()

  surface_json_path = tmp_path / "surface_component_candidate_20260611.json"
  surface_csv_path = tmp_path / "surface_component_candidate_20260611.csv"
  assert surface_json_path.is_file()
  assert surface_csv_path.is_file()
  surface_report = json.loads(surface_json_path.read_text(encoding="utf-8"))
  assert surface_report["schema_version"] == (
    "a2.target_geometry_surface_component_candidate.v1"
  )
  assert surface_report["summary"]["surface_component_count"] == 14
  assert "surface_left_wing_skin" in surface_csv_path.read_text(encoding="utf-8")
  assert "dedicated_intake_lip_or_duct_component" in surface_csv_path.read_text(
    encoding="utf-8"
  )

  semantic_json_path = tmp_path / "semantic_damage_geometry_candidate_20260611.json"
  semantic_csv_path = tmp_path / "semantic_damage_geometry_candidate_20260611.csv"
  assert semantic_json_path.is_file()
  assert semantic_csv_path.is_file()
  semantic_report = json.loads(semantic_json_path.read_text(encoding="utf-8"))
  assert semantic_report["schema_version"] == (
    "a2.target_geometry_semantic_damage_geometry_candidate.v1"
  )
  assert semantic_report["summary"]["semantic_volume_component_count"] == 14
  assert semantic_report["summary"]["runtime_parse_ready_component_count"] == 14
  assert semantic_report["summary"]["runtime_active_component_count"] == 0
  assert "semantic_left_wing_skin_volume" in semantic_csv_path.read_text(
    encoding="utf-8"
  )
  assert "direct_receivers_parse_ready_cross_region_receivers_held" in (
    semantic_csv_path.read_text(encoding="utf-8")
  )

  internal_prior_json_path = (
    tmp_path / "internal_component_prior_candidate_20260611.json"
  )
  internal_prior_csv_path = (
    tmp_path / "internal_component_prior_candidate_20260611.csv"
  )
  assert internal_prior_json_path.is_file()
  assert internal_prior_csv_path.is_file()
  internal_prior_report = json.loads(
    internal_prior_json_path.read_text(encoding="utf-8")
  )
  assert internal_prior_report["schema_version"] == (
    "a2.target_geometry_internal_component_prior_candidate.v1"
  )
  assert internal_prior_report["summary"]["internal_component_prior_count"] == 26
  assert internal_prior_report["summary"]["post_constraint_outside_count"] == 0
  assert internal_prior_report["summary"]["cross_region_held_prior_count"] == 2
  assert internal_prior_report["summary"]["shape_promotion_count"] == 9
  assert "left_wing_fuel_cell" in internal_prior_csv_path.read_text(
    encoding="utf-8"
  )
  assert "r18_promoted_from_subcomponent_shape_candidate" in (
    internal_prior_csv_path.read_text(encoding="utf-8")
  )
  assert "placed_inside_airframe_exceeds_parent_shell_review" in internal_prior_csv_path.read_text(
    encoding="utf-8"
  )
  assert "whole_airframe_source_region_union_bounds" in (
    internal_prior_csv_path.read_text(encoding="utf-8")
  )

  held_segment_json_path = (
    tmp_path / "cross_region_held_component_segments_20260611.json"
  )
  held_segment_csv_path = (
    tmp_path / "cross_region_held_component_segments_20260611.csv"
  )
  assert held_segment_json_path.is_file()
  assert held_segment_csv_path.is_file()
  held_segment_report = json.loads(
    held_segment_json_path.read_text(encoding="utf-8")
  )
  assert held_segment_report["schema_version"] == (
    "a2.target_geometry_cross_region_held_component_segments.v1"
  )
  assert held_segment_report["summary"]["held_segment_count"] == 8
  assert held_segment_report["summary"][
    "outside_whole_airframe_segment_count"
  ] == 0
  assert held_segment_report["summary"]["shape_promotion_segment_count"] == 5
  assert "wing_spar_center_carrythrough_segment" in (
    held_segment_csv_path.read_text(encoding="utf-8")
  )
  assert "engine_core_afterburner_segment" in held_segment_csv_path.read_text(
    encoding="utf-8"
  )
  assert "R18_promoted_R17_segmented_engine_afterburner_capsule" in (
    held_segment_csv_path.read_text(encoding="utf-8")
  )

  airframe_constraint_json_path = (
    tmp_path / "airframe_constraint_correction_candidate_20260611.json"
  )
  airframe_constraint_csv_path = (
    tmp_path / "airframe_constraint_correction_candidate_20260611.csv"
  )
  assert airframe_constraint_json_path.is_file()
  assert airframe_constraint_csv_path.is_file()
  airframe_constraint_report = json.loads(
    airframe_constraint_json_path.read_text(encoding="utf-8")
  )
  assert airframe_constraint_report["schema_version"] == (
    "a2.target_geometry_airframe_constraint_correction_candidate.v1"
  )
  assert airframe_constraint_report["summary"]["item_count"] == 34
  assert airframe_constraint_report["summary"][
    "silhouette_exposure_item_count"
  ] == 0
  assert "apg68_radar_array" in airframe_constraint_csv_path.read_text(
    encoding="utf-8"
  )
  assert "inside_airframe_cross_region_ownership_held" in (
    airframe_constraint_csv_path.read_text(encoding="utf-8")
  )

  ownership_split_json_path = (
    tmp_path / "cross_region_ownership_split_candidate_20260611.json"
  )
  ownership_split_csv_path = (
    tmp_path / "cross_region_ownership_split_candidate_20260611.csv"
  )
  assert ownership_split_json_path.is_file()
  assert ownership_split_csv_path.is_file()
  ownership_split_report = json.loads(
    ownership_split_json_path.read_text(encoding="utf-8")
  )
  assert ownership_split_report["schema_version"] == (
    "a2.target_geometry_cross_region_ownership_split_candidate.v1"
  )
  assert ownership_split_report["summary"]["split_receiver_candidate_count"] == 8
  assert ownership_split_report["summary"][
    "runtime_active_split_component_count"
  ] == 0
  ownership_split_csv = ownership_split_csv_path.read_text(encoding="utf-8")
  assert (
    "split_into_engine_section_receivers_and_keep_intake_duct_receiver_separate"
    in ownership_split_csv
  )
  assert "wing_spar_center_carrythrough_segment" in ownership_split_csv

  runtime_activation_json_path = (
    tmp_path / "target_geometry_runtime_activation_candidate_20260613.json"
  )
  runtime_activation_csv_path = (
    tmp_path / "target_geometry_runtime_activation_candidate_20260613.csv"
  )
  assert runtime_activation_json_path.is_file()
  assert runtime_activation_csv_path.is_file()
  runtime_activation_report = json.loads(
    runtime_activation_json_path.read_text(encoding="utf-8")
  )
  assert runtime_activation_report["schema_version"] == (
    "a2.target_geometry_runtime_activation_candidate.v1"
  )
  assert runtime_activation_report["summary"]["candidate_component_count"] == 8
  assert runtime_activation_report["summary"][
    "runtime_schema_parse_ready_component_count"
  ] == 8
  assert runtime_activation_report["summary"][
    "runtime_active_component_count"
  ] == 0
  assert len(runtime_activation_report["unit_database_patch_candidate"]["add"]) == 8
  assert runtime_activation_report["activation_policy"]["target_path"] == (
    "damage_model.hitboxes[].components"
  )
  assert runtime_activation_report["rows"][0]["unit_database_patch_path"] == (
    "damage_model.hitboxes[2].components"
  )
  runtime_activation_csv = runtime_activation_csv_path.read_text(encoding="utf-8")
  assert "parse_ready_existing_loader_fields" in runtime_activation_csv
  assert "A2_TARGET_GEOMETRY_PROXY_F16C_R22" in runtime_activation_csv
  assert "damage_model.hitboxes[2].components" in runtime_activation_csv

  runtime_behavior_json_path = (
    tmp_path / "target_geometry_runtime_behavior_regression_20260613.json"
  )
  runtime_behavior_csv_path = (
    tmp_path / "target_geometry_runtime_behavior_regression_20260613.csv"
  )
  assert runtime_behavior_json_path.is_file()
  assert runtime_behavior_csv_path.is_file()
  runtime_behavior_report = json.loads(
    runtime_behavior_json_path.read_text(encoding="utf-8")
  )
  assert runtime_behavior_report["schema_version"] == (
    "a2.target_geometry_runtime_behavior_regression.v1"
  )
  assert runtime_behavior_report["summary"]["base_component_count"] == 26
  assert runtime_behavior_report["summary"]["projected_component_count"] == 32
  assert runtime_behavior_report["summary"][
    "retired_parent_component_count"
  ] == 2
  assert runtime_behavior_report["summary"]["split_component_added_count"] == 8
  assert runtime_behavior_report["summary"]["duplicate_component_name_count"] == 0
  assert runtime_behavior_report["summary"]["behavior_regression_pass"] is True
  runtime_behavior_csv = runtime_behavior_csv_path.read_text(encoding="utf-8")
  assert "engine_core,2,damage_model.hitboxes[2].components" in (
    runtime_behavior_csv
  )
  assert "wing_spar_center,3,damage_model.hitboxes[3].components" in (
    runtime_behavior_csv
  )

  training_proxy_json_path = (
    tmp_path / "target_geometry_training_proxy_database_20260613.json"
  )
  training_proxy_database_dir = (
    tmp_path / "target_geometry_training_proxy_database_20260613"
  )
  training_proxy_unit_path = (
    training_proxy_database_dir / "aircraft" / "units" / "f16c_block50.json"
  )
  assert training_proxy_json_path.is_file()
  assert training_proxy_database_dir.is_dir()
  assert training_proxy_unit_path.is_file()
  training_proxy_report = json.loads(
    training_proxy_json_path.read_text(encoding="utf-8")
  )
  assert training_proxy_report["schema_version"] == (
    "a2.target_geometry_training_proxy_database.v1"
  )
  assert (
    training_proxy_report["runtime_database"]["proxy_f16c_unit_sha256"]
    and len(training_proxy_report["runtime_database"]["proxy_f16c_unit_sha256"])
    == 64
  )
  assert (
    training_proxy_report["summary"]["default_database_component_count"] == 26
  )
  assert training_proxy_report["summary"]["proxy_database_component_count"] == 32
  assert training_proxy_report["summary"]["split_receiver_component_count"] == 8
  assert training_proxy_report["summary"]["retired_parent_component_count"] == 2
  assert training_proxy_report["summary"]["duplicate_component_name_count"] == 0
  assert training_proxy_report["summary"]["behavior_regression_pass"] is True
  assert training_proxy_report["training_runtime_contract"][
    "training_path_wired"
  ] is True
  assert training_proxy_report["authority_boundary"]["training_path_wired"] is True
  proxy_unit = json.loads(training_proxy_unit_path.read_text(encoding="utf-8"))
  proxy_component_names = component_model.damage_component_names(
    proxy_unit
  )
  default_component_names = component_model.damage_component_names(
    gltf_io.load_json(constants.DEFAULT_AIRCRAFT)
  )
  assert len(default_component_names) == 26
  assert len(proxy_component_names) == 32
  assert "engine_core" in default_component_names
  assert "wing_spar_center" in default_component_names
  assert "engine_core" not in proxy_component_names
  assert "wing_spar_center" not in proxy_component_names
  assert "engine_core_afterburner_segment" in proxy_component_names
  assert "wing_spar_center_carrythrough_segment" in proxy_component_names

  shape_placement_json_path = (
    tmp_path / "subcomponent_shape_placement_candidate_20260611.json"
  )
  shape_placement_csv_path = (
    tmp_path / "subcomponent_shape_placement_candidate_20260611.csv"
  )
  assert shape_placement_json_path.is_file()
  assert shape_placement_csv_path.is_file()
  shape_placement_report = json.loads(
    shape_placement_json_path.read_text(encoding="utf-8")
  )
  assert shape_placement_report["schema_version"] == (
    "a2.target_geometry_subcomponent_shape_placement_candidate.v1"
  )
  # The R22 thin-prism/frustum shape updates clear the source exposure queue,
  # so shape placement has no rows to process.
  assert shape_placement_report["summary"][
    "shape_placement_candidate_count"
  ] == 0
  assert shape_placement_report["summary"][
    "source_silhouette_exposure_item_count"
  ] == 0
  assert (
    shape_placement_report["summary"]["candidate_resolves_exposure_count"]
    + shape_placement_report["summary"]["candidate_unresolved_exposure_count"]
    == 0
  )
  assert shape_placement_report["summary"][
    "candidate_total_outside_sample_reduction"
  ] >= 0
  assert (
    shape_placement_report["summary"]["centerline_candidate_resolves_exposure_count"]
    + shape_placement_report["summary"][
      "centerline_candidate_unresolved_exposure_count"
    ]
    == 0
  )
  assert shape_placement_report["summary"][
    "centerline_candidate_total_outside_sample_count"
  ] >= 0
  assert (
    shape_placement_report["summary"]["latest_candidate_resolves_exposure_count"]
    + shape_placement_report["summary"]["latest_candidate_unresolved_exposure_count"]
    == 0
  )
  assert shape_placement_report["summary"][
    "latest_candidate_total_outside_sample_count"
  ] >= 0
  assert len(shape_placement_report["rows"]) == 0
  shape_placement_csv_text = shape_placement_csv_path.read_text(encoding="utf-8")
  # Previously exposed receivers are now cleared and absent from the
  # shape-placement rows.
  for item_id in (
    "left_wing_fuel_cell",
    "right_wing_fuel_cell",
    "wing_spar_center",
  ):
    assert item_id not in shape_placement_csv_text
  # Receivers that stay inside the contour are not shape-placement rows.
  assert "apg68_radar_array" not in shape_placement_csv_text
  assert "afterburner_nozzle" not in shape_placement_csv_text
  assert "engine_core" not in shape_placement_csv_text
  assert "cockpit_crew_station" not in shape_placement_csv_text
  assert "inertial_navigation_unit" not in shape_placement_csv_text

  parent_child_json_path = (
    tmp_path / "semantic_parent_child_layout_candidate_20260611.json"
  )
  parent_child_csv_path = (
    tmp_path / "semantic_parent_child_layout_candidate_20260611.csv"
  )
  assert parent_child_json_path.is_file()
  assert parent_child_csv_path.is_file()
  parent_child_report = json.loads(
    parent_child_json_path.read_text(encoding="utf-8")
  )
  assert parent_child_report["schema_version"] == (
    "a2.target_geometry_semantic_parent_child_layout_candidate.v1"
  )
  assert parent_child_report["summary"]["parent_semantic_component_count"] == 14
  assert parent_child_report["summary"]["bound_receiver_component_count"] == 26
  assert parent_child_report["summary"]["extra_receiver_slot_count"] == 13
  assert parent_child_report["summary"]["cross_region_held_segment_count"] == 8
  assert parent_child_report["summary"][
    "cross_region_held_segment_overlay_count"
  ] == 5
  assert "semantic_left_wing_skin_volume" in parent_child_csv_path.read_text(
    encoding="utf-8"
  )
  assert "segments=5" in parent_child_csv_path.read_text(encoding="utf-8")

  for retired_view_dir in (
    "semantic_damage_geometry_views",
    "internal_component_prior_views",
    "semantic_parent_child_layout_views",
    "subcomponent_shape_placement_views",
  ):
    assert not (tmp_path / retired_view_dir).exists()

  scene_path = tmp_path / "scene.html"
  assert scene_path.is_file()
  scene = scene_path.read_text(encoding="utf-8")
  assert "F-16 Final Geometry Contour Result" in scene
  assert "Current final visual result only" in scene
  assert "fine_proxy_review_dashboard.html" not in scene
  assert "human_review_triage.html" not in scene
  assert "component_review_views/index.html" not in scene
  assert "Fine Geometry Proxy Overlay" not in scene
  assert "Surface Component Candidates" not in scene
  assert "Semantic Damage Geometry Volumes" not in scene
  assert "semantic_damage_geometry_views/index.html" not in scene
  assert "Internal Component Prior Geometry" not in scene
  assert "internal_component_prior_views/index.html" not in scene
  assert "Cross-Region Held Split Segments" not in scene
  assert "Airframe Constraint Correction Candidates" not in scene
  assert "Cross-Region Ownership Split Candidates" not in scene
  assert "TG-P7 Runtime Activation Candidate" not in scene
  assert "TG-P7 Runtime Behavior Regression Candidate" not in scene
  assert "TG-P7 Training Proxy Database" not in scene
  assert "Subcomponent Shape Placement Candidates" not in scene
  assert "subcomponent_shape_placement_views/index.html" not in scene
  assert "Semantic Parent-Child Component Layout" not in scene
  assert "semantic_parent_child_layout_views/index.html" not in scene
  assert "Whole-Airframe Projected Mesh Contour Containment" in scene
  assert "whole_airframe_contour_dashboard.html" in scene
  assert "whole_airframe_contour_top.svg" in scene
  assert "projecting triangle faces" in scene
  assert "engineering review margin" in scene
