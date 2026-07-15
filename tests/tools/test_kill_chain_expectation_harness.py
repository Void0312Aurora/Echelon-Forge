from __future__ import annotations

from tools.diagnostics import kill_chain_expectation_harness as harness


def test_anchor_grid_counts_and_classification() -> None:
  cases = harness.generate_case_grid(
    grid_tier="anchor-grid",
    target_motion_layers=(
      "nonmaneuvering_constant_velocity",
      "mild_maneuver",
    ),
  )

  assert len(cases) == 93
  assert sum(1 for case in cases if case["runtime_supported"]) == 78
  assert sum(1 for case in cases if not case["runtime_supported"]) == 15

  case_by_id = {str(case["case_id"]): case for case in cases}
  anchor = case_by_id["kces_anchor_grid_cv_8km_p30deg"]
  assert anchor["launch_class"] == "N"
  assert anchor["range_m"] == 8000.0
  assert anchor["signed_bearing_deg"] == 30.0
  assert case_by_id["kces_anchor_grid_cv_16km_p30deg"]["launch_class"] == "O"


def test_before_report_smoke_projects_heatmap_rows() -> None:
  report = harness.generate_before_report(
    grid_tier="anchor-grid",
    target_motion_layers=("nonmaneuvering_constant_velocity",),
    case_ids=("kces_anchor_grid_cv_8km_p30deg",),
    effect_variants=("REV-RUNTIME-PROJECTION", "REV-SMALLER-LOAD"),
    seed=20260621,
  )

  assert report["schema_version"] == "a2.kill_chain_expectation_before_report.v1"
  assert report["summary"]["case_count"] == 1
  assert report["summary"]["runnable_case_count"] == 1
  assert report["summary"]["heatmap_row_count"] == 2
  rows = report["heatmap_rows"]
  runtime_row = rows[0]
  assert runtime_row["identity"]["case_id"] == "kces_anchor_grid_cv_8km_p30deg"
  assert runtime_row["launch_window"]["launch_class"] == "N"
  assert runtime_row["guidance_approach"]["entered_R_fuze"] is True
  assert runtime_row["guidance_approach"]["guidance_expectation_status"] == "satisfied"
  assert runtime_row["guards"]["authority_boundary_status"] == "engineering_proxy_guarded"
  assert runtime_row["warhead_load_field"]["R_effect_variant"] == "REV-RUNTIME-PROJECTION"
  assert runtime_row["warhead_load_field"]["R_effect_m"] == 9.0
  assert runtime_row["warhead_load_field"]["R_effect_source"] == (
    "missile_runtime_projection.resolved_projection_radius_m"
  )
  assert runtime_row["warhead_load_field"]["effect_band"] == "outside_effect"
  detail = runtime_row["component_detail"]
  assert detail["schema_version"] == "a2.kill_chain_expectation_component_detail.v1"
  assert detail["R_effect_variant"] == "REV-RUNTIME-PROJECTION"
  assert detail["summary"]["component_detail_row_count"] > 0
  assert detail["summary"]["matched_component_response_row_count"] > 0
  assert detail["summary"]["max_probability_component"]["failure_probability"] == (
    runtime_row["component_response"]["max_failure_probability"]
  )
  component_row = detail["component_rows"][0]
  assert "component_name" in component_row
  assert "effect_scale" in component_row
  assert "rho_effect_component" in component_row
  assert "failure_probability" in component_row
  assert "sampled_failure" in component_row

  smaller_row = rows[1]
  assert smaller_row["warhead_load_field"]["R_effect_variant"] == "REV-SMALLER-LOAD"
  assert smaller_row["warhead_load_field"]["effect_band"] == "unclassified_missing_R_effect"
  assert smaller_row["component_detail"]["R_effect_m"] is None
  assert smaller_row["component_detail"]["component_rows"][0]["rho_effect_component"] is None
