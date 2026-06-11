from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.geometry import airframe_geometry_review


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_f16_geometry_manifest_records_dual_model_axis_and_scale() -> None:
  manifest = airframe_geometry_review.build_airframe_geometry_manifest()
  aircraft = airframe_geometry_review._load_json( # noqa: SLF001
    airframe_geometry_review.DEFAULT_AIRCRAFT
  )

  assert manifest["schema_version"] == "a2.target_geometry_manifest.v1"
  assert manifest["status"] == "target_geometry_manifest_generated_review_only"
  assert manifest["asset_source_status"] == "verified_redistributable_visual_reference"
  assert manifest["source"]["uid"] == "4bc2ff75dc584af2afd0aa6bd8b79015"
  assert manifest["source"]["author"] == "Carlos.Maciel"
  assert manifest["source"]["license"]["url"] == "http://creativecommons.org/licenses/by/4.0/"
  assert "Canopy01_1" in manifest["source_geometry_hints"][
    "metadata_notable_node_names"
  ]
  assert "EngineL01_17" in manifest["source_geometry_hints"][
    "metadata_notable_node_names"
  ]

  paths = manifest["paths"]
  assert paths["runtime_visual_glb"].endswith(
    "assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb"
  )
  assert paths["audit_scene_gltf"].endswith(
    "assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf"
  )

  axis = manifest["axis_alignment"]
  assert axis["asset_x"] == "sim_right"
  assert axis["asset_y"] == "sim_up"
  assert axis["asset_z_negative"] == "sim_forward"
  assert axis["nose_direction"] == "negative_asset_z"
  assert axis["runtime_registry_scale"] == 1.65

  gltf = manifest["gltf_summary"]
  assert gltf["triangle_count"] == 4504
  assert gltf["position_accessor_vertex_count"] == 13415
  assert gltf["node_count"] >= 40
  assert gltf["mesh_node_bounds"][0]["node_name"].startswith("Object_")

  dimension_check = manifest["public_dimension_check"]
  assert dimension_check["public_dimensions"]["length_m"] == 15.06
  assert dimension_check["public_dimensions"]["wingspan_m"] == 9.96
  assert dimension_check["public_dimensions"]["height_m"] == 4.88
  assert abs(dimension_check["scaled_dimension_error_percent"]["length_m"]) < 1.0
  assert abs(dimension_check["scaled_dimension_error_percent"]["wingspan_m"]) < 5.0
  assert abs(dimension_check["scaled_dimension_error_percent"]["height_m"]) < 6.0

  damage_geometry = manifest["current_damage_geometry"]
  assert damage_geometry["summary"]["hitbox_count"] >= 4
  assert damage_geometry["summary"]["component_count"] > 10
  assert damage_geometry["public_dimension_error_percent"]["height_m"] < -70.0
  assert manifest["authority_boundary"]["runtime_collision_mesh"] is False
  assert manifest["authority_boundary"]["real_weapon_pk_authority"] is False

  mapping = airframe_geometry_review.build_geometry_mapping_candidate(manifest)
  report = airframe_geometry_review.build_component_binding_report(aircraft, mapping)
  diagnostics = airframe_geometry_review.build_review_point_diagnostics(mapping, report)
  fine_proxy = airframe_geometry_review.build_fine_geometry_proxy_candidate(
    mapping, diagnostics, manifest=manifest
  )
  assert report["schema_version"] == "a2.target_geometry_component_binding_report.v1"
  assert report["status"] == "component_binding_report_generated_review_only"
  assert report["summary"]["component_count"] == 22
  assert report["summary"]["bound_component_count"] == 22
  assert report["summary"]["side_sign_review_count"] >= 4
  rows = {row["component_name"]: row for row in report["rows"]}
  assert rows["apg68_radar_array"]["bound_region_id"] == "nose_radome"
  assert rows["cockpit_crew_station"]["bound_region_id"] in {
    "nose_radome",
    "forward_fuselage",
  }
  assert rows["engine_core"]["bound_region_id"] == "aft_fuselage_engine"
  assert rows["afterburner_nozzle"]["bound_region_id"] == "engine_nozzle"
  assert "sign_review" in ";".join(rows["left_wing_fuel_cell"]["anomalies"])
  assert "sign_review" in ";".join(rows["right_wing_fuel_cell"]["anomalies"])

  assert diagnostics["schema_version"] == (
    "a2.target_geometry_review_point_diagnostics.v1"
  )
  assert diagnostics["summary"]["review_point_count"] >= 10
  points = {row["point_id"]: row for row in diagnostics["rows"]}
  assert points["nose_axis_4m"]["nearest_outer_region_id"] == "forward_fuselage"
  assert points["nose_axis_4m"]["nearest_outer_distance_m"] == 0.0
  assert points["nose_axis_4m"]["candidate_component_count"] > 0
  assert points["nose_axis_6m"]["nearest_outer_region_id"] == "nose_radome"
  assert points["tail_axis_6m"]["nearest_component_name"] in {
    "afterburner_nozzle",
    "engine_core",
    "rudder_actuator",
  }

  assert fine_proxy["schema_version"] == "a2.target_geometry_fine_proxy_candidate.v1"
  assert fine_proxy["status"] == "fine_geometry_proxy_candidate_generated_review_only"
  assert fine_proxy["summary"]["source_outer_region_count"] == 14
  assert fine_proxy["summary"]["proxy_count"] == 14
  assert fine_proxy["summary"]["held_region_count"] == 0
  assert fine_proxy["summary"]["mesh_source_vertex_count"] == 13415
  assert fine_proxy["summary"]["mesh_derived_silhouette_count"] >= 10
  assert fine_proxy["summary"]["proxy_kind_counts"]["thin_prism"] >= 5
  assert fine_proxy["summary"]["proxy_kind_counts"]["convex_hull"] >= 4
  assert fine_proxy["summary"]["total_proxy_support_volume_ratio"] < 0.75
  proxies = {proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]}
  assert proxies["left_wing"]["proxy_kind"] == "thin_prism"
  assert proxies["vertical_tail"]["thin_prism"]["thin_axis"] == "y"
  assert proxies["nose_radome"]["proxy_kind"] == "convex_hull"
  assert "runtime_collision_mesh" in proxies["nose_radome"]["runtime_prohibited_use"]
  assert proxies["nose_radome"]["mesh_derived_review_geometry"]["region_vertex_count"] > 0
  assert (
    proxies["nose_radome"]["mesh_derived_review_geometry"]["hulls"]["top"][
      "point_count"
    ]
    >= 3
  )
  fine_rows = {row["point_id"]: row for row in fine_proxy["review_point_distance_deltas"]}
  assert fine_rows["nose_axis_4m"]["nearest_fine_proxy_region_id"]
  assert "fine_minus_source_distance_delta_m" in fine_rows["above_4m"]


def test_airframe_geometry_review_cli_writes_manifest(tmp_path: Path) -> None:
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
  assert summary["component_count"] == 22
  assert summary["review_point_count"] >= 10
  assert summary["inside_outer_region_point_count"] > 0

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
    svg_path = tmp_path / svg_name
    assert svg_path.is_file()
    text = svg_path.read_text(encoding="utf-8")
    assert "component overlays, and review points" in text
    assert "legacy_hitbox_0" in text
    assert "forward_fuselage" in text

  component_json_path = tmp_path / "component_binding_report_20260611.json"
  component_csv_path = tmp_path / "component_binding_report_20260611.csv"
  assert component_json_path.is_file()
  assert component_csv_path.is_file()
  report = json.loads(component_json_path.read_text(encoding="utf-8"))
  assert report["summary"]["component_count"] == 22
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
  assert fine_proxy["summary"]["mesh_derived_silhouette_count"] >= 10
  assert result.stdout.find("fine_proxy_count") >= 0
  assert result.stdout.find("mesh_derived_silhouette_count") >= 0
  assert result.stdout.find("fine_proxy_support_volume_ratio") >= 0
  assert result.stdout.find("fine_proxy_review_dashboard") >= 0

  for svg_name in ("fine_proxy_top.svg", "fine_proxy_side.svg", "fine_proxy_front.svg"):
    svg_path = tmp_path / svg_name
    assert svg_path.is_file()
    text = svg_path.read_text(encoding="utf-8")
    assert "mesh-derived fine geometry proxy candidate" in text
    assert "mesh-derived silhouette" in text
    assert "source AABB" in text
    assert "runtime collision mesh" in text

  dashboard_path = tmp_path / "fine_proxy_review_dashboard.html"
  assert dashboard_path.is_file()
  dashboard = dashboard_path.read_text(encoding="utf-8")
  assert "F-16 Fine Proxy Human Review Dashboard" in dashboard
  assert "hold_for_human_review" in dashboard
  assert "needs_human_review" in dashboard
  assert "candidate_accept_after_visual_check" in dashboard
  assert "inflated_selection_bounds" in dashboard
  assert "mesh_silhouette" in dashboard

  scene_path = tmp_path / "scene.html"
  assert scene_path.is_file()
  scene = scene_path.read_text(encoding="utf-8")
  assert "F-16 Target Geometry Review Packet" in scene
  assert "nose_axis_4m" in scene
  assert "Fine Geometry Proxy Overlay" in scene
  assert "mesh-derived silhouettes" in scene
  assert "fine_proxy_review_dashboard.html" in scene
