from __future__ import annotations

import math

from tools.geometry import target_geometry_lethality_matrix_probe as probe
from tools.geometry import target_geometry_proxy_standoff_grid_probe as standoff_probe


def _assert_velocity_points_to_origin(case: dict[str, object]) -> None:
  local_point = tuple(float(value) for value in case["local_point_m"])  # type: ignore[index]
  velocity = tuple(
    float(value) for value in case["missile_velocity_body_mps"]  # type: ignore[index]
  )
  expected = probe.missile_velocity_toward_origin(local_point)
  for actual_value, expected_value in zip(velocity, expected, strict=True):
    assert abs(actual_value - expected_value) <= 1.0e-9
  if math.sqrt(sum(value * value for value in local_point)) > 1.0e-9:
    assert abs(math.sqrt(sum(value * value for value in velocity)) - 900.0) <= 1.0e-9
    assert sum(point * vel for point, vel in zip(local_point, velocity, strict=True)) < 0.0


def test_target_geometry_lethality_matrix_probe_observes_proxy_deltas() -> None:
  report = probe.generate_report()

  assert report["schema_version"] == "a2.target_geometry_lethality_matrix_probe.v1"
  assert report["status"] == "target_geometry_lethality_matrix_probe_generated_20260614"
  assert report["authority_boundary"]["default_database_modified"] is False
  assert report["authority_boundary"]["proxy_database_opt_in_only"] is True
  assert report["authority_boundary"]["real_weapon_pk_authority"] is False
  assert report["authority_boundary"]["deterministic_fuze_authority"] is False

  metrics = report["metrics"]
  assert metrics["case_count"] == len(probe.CASE_DEFINITIONS)
  assert metrics["warhead_family_count"] == len(probe.WARHEAD_FAMILIES)
  assert metrics["comparison_count"] == (
    len(probe.CASE_DEFINITIONS) * len(probe.WARHEAD_FAMILIES)
  )
  assert metrics["event_run_count"] == metrics["comparison_count"] * 2
  assert metrics["changed_comparison_count"] > 0
  assert metrics["changed_primary_component_count"] > 0
  assert metrics["changed_component_event_row_count"] > 0
  assert metrics["family_changed_comparison_counts"]["blast_fragmentation"] > 0
  assert metrics["family_changed_comparison_counts"]["continuous_rod"] > 0
  assert metrics["proxy_split_receiver_comparison_count"] > 0
  assert metrics["proxy_retired_parent_comparison_count"] == 0
  assert metrics["nose_cockpit_center_unchanged_for_both_families"] is True
  assert metrics["right_beam_near_far_monotonic_checks"]["all_pass"] is True

  comparisons = report["comparisons"]
  assert all(
    comparison["default_event"]["effect_family"] == comparison["warhead_family"]
    for comparison in comparisons
  )
  assert all(
    comparison["proxy_event"]["effect_family"] == comparison["warhead_family"]
    for comparison in comparisons
  )
  assert any(
    comparison["proxy_split_receiver_names_observed"]
    for comparison in comparisons
    if comparison["warhead_family"] == "continuous_rod"
  )
  assert all(
    comparison["proxy_event"]["component_failure_probability_event_aggregation"]
    == "max_probability_across_component_mechanism_load_rows"
    for comparison in comparisons
  )
  assert all(
    "component_primary_row_failure_probability" in comparison["proxy_event"]
    for comparison in comparisons
  )
  assert all(
    "component_max_failure_probability_component_name" in comparison["proxy_event"]
    for comparison in comparisons
  )
  assert any(
    abs(
      float(comparison["proxy_event"]["component_failure_probability"])
      - float(comparison["proxy_event"]["component_primary_row_failure_probability"])
    )
    > 1.0e-9
    for comparison in comparisons
  )

  outcome = report["outcome_summary"]
  assert outcome["status"] == "structure_damage_and_component_failure_reported"
  assert outcome["event_run_count"] == metrics["event_run_count"]
  assert outcome["structure_damage_event_count"] > 0
  assert outcome["component_failure_event_count"] > 0
  assert outcome["structural_breakup_event_count"] > 0
  assert set(outcome["structural_breakup_event_count_by_database"]) == {
    "default",
    "proxy",
  }
  assert all(
    ":continuous_rod:" in comparison_id
    for comparison_id in outcome["structural_breakup_comparison_ids"]
  )
  assert any(
    ":right_beam_near_7m" in comparison_id
    for comparison_id in outcome["structural_breakup_comparison_ids"]
  )
  assert all(
    ":right_beam_far_14m" not in comparison_id
    for comparison_id in outcome["structural_breakup_comparison_ids"]
  )
  assert set(outcome["structure_damage_event_count_by_database"]) == {
    "default",
    "proxy",
  }
  assert set(outcome["component_failure_event_count_by_database"]) == {
    "default",
    "proxy",
  }
  assert outcome["max_structure_damage_delta"]["structure_damage_delta"] < 0.0
  assert (
    outcome["max_component_failure_probability"]["component_failure_probability"]
    > 0.0
  )
  assert outcome["component_failure_component_names"]
  assert len(outcome["event_rows"]) == metrics["event_run_count"]
  assert all("structure_damage_delta" in row for row in outcome["event_rows"])
  assert all("component_failure_observed" in row for row in outcome["event_rows"])
  assert all(
    "aircraft_damage_state_delta_by_system" in comparison["proxy_event"]
    for comparison in comparisons
  )
  assert all(
    "damage_reports" in comparison["proxy_event"] for comparison in comparisons
  )
  assert all(
    "platform_consequence_events" in comparison["proxy_event"]
    for comparison in comparisons
  )
  assert all(
    "structural_breakup_events" in comparison["proxy_event"]
    for comparison in comparisons
  )


def test_target_geometry_matrix_cases_use_origin_pointing_velocity() -> None:
  for case in probe.CASE_DEFINITIONS:
    _assert_velocity_points_to_origin(case)


def test_target_geometry_proxy_standoff_near_miss_probability_is_load_sensitive() -> None:
  top_contour = standoff_probe._top_contour_points()
  cases = {
    str(case["case_id"]): case
    for case in standoff_probe._external_grid_cases(top_contour)
  }

  def event_probability(family: str, case_id: str) -> float:
    case = cases[case_id]
    event = probe._event_summary(
      database_path=probe.PROXY_DATABASE_PATH,
      family=family,
      local_point_m=tuple(float(value) for value in case["local_point_m"]),
      missile_velocity_body_mps=tuple(
        float(value) for value in case["missile_velocity_body_mps"]
      ),
      seed=20260615,
    )
    return float(event["component_primary_row_failure_probability"])

  blast_nose_0p5m = event_probability("blast_fragmentation", "nose_standoff_0p5m")
  blast_nose_4m = event_probability("blast_fragmentation", "nose_standoff_4p0m")
  rod_left_beam_0p5m = event_probability(
    "continuous_rod", "left_beam_standoff_0p5m"
  )
  rod_left_beam_4m = event_probability("continuous_rod", "left_beam_standoff_4p0m")

  assert blast_nose_0p5m >= 0.55
  assert blast_nose_4m <= 0.05
  assert blast_nose_0p5m - blast_nose_4m >= 0.45
  assert rod_left_beam_0p5m >= 0.55
  assert rod_left_beam_4m <= 0.35
  assert rod_left_beam_0p5m - rod_left_beam_4m >= 0.30


def test_target_geometry_proxy_standoff_support_points_are_mirror_symmetric() -> None:
  top_contour = standoff_probe._top_contour_points()
  cases = {
    (
      str(case["aspect"]),
      float(case["standoff_distance_m"]),
      float(case["local_up_m"]),
    ): case
    for case in standoff_probe._external_grid_cases(top_contour)
  }

  mirror_pairs = (
    ("nose_right", "nose_left"),
    ("right_beam", "left_beam"),
    ("tail_right", "tail_left"),
  )
  for right_aspect, left_aspect in mirror_pairs:
    for local_up_m in standoff_probe.LOCAL_UP_LEVELS_M:
      for standoff in standoff_probe.STANDOFF_DISTANCES_M:
        right_case = cases[(right_aspect, float(standoff), float(local_up_m))]
        left_case = cases[(left_aspect, float(standoff), float(local_up_m))]
        right_point = [float(value) for value in right_case["local_point_m"]]
        left_point = [float(value) for value in left_case["local_point_m"]]

        assert abs(right_point[0] - left_point[0]) <= 1.0e-6
        assert abs(right_point[1] + left_point[1]) <= 2.0e-6
        assert abs(right_point[2] - left_point[2]) <= 1.0e-6


def test_target_geometry_proxy_standoff_grid_includes_vertical_layers() -> None:
  top_contour = standoff_probe._top_contour_points()
  cases = standoff_probe._external_grid_cases(top_contour)

  assert len(cases) == (
    len(standoff_probe.ASPECT_DIRECTIONS)
    * len(standoff_probe.STANDOFF_DISTANCES_M)
    * len(standoff_probe.LOCAL_UP_LEVELS_M)
  )
  assert sorted({float(case["local_up_m"]) for case in cases}) == sorted(
    float(value) for value in standoff_probe.LOCAL_UP_LEVELS_M
  )
  assert any(str(case["case_id"]).startswith("right_beam_zp1p0m") for case in cases)
  assert any(str(case["case_id"]).startswith("left_beam_zm1p0m") for case in cases)


def test_target_geometry_proxy_centerline_z_cases_use_origin_pointing_velocity() -> None:
  cases = standoff_probe._centerline_z_cases()
  by_z = {float(case["local_up_m"]): case for case in cases}

  assert sorted(by_z) == sorted(
    float(value) for value in standoff_probe.CENTERLINE_Z_LEVELS_M
  )
  assert by_z[0.0]["local_point_m"] == [0.0, 0.0, 0.0]
  assert by_z[2.0]["missile_velocity_body_mps"] == [0.0, 0.0, -900.0]
  assert by_z[-2.0]["missile_velocity_body_mps"] == [0.0, 0.0, 900.0]
  assert by_z[0.0]["missile_velocity_body_mps"] == [0.0, 0.0, 0.0]
  assert all(
    float(case["missile_velocity_body_mps"][0]) == 0.0
    and float(case["missile_velocity_body_mps"][1]) == 0.0
    for case in cases
  )
  for case in cases:
    _assert_velocity_points_to_origin(case)


def test_target_geometry_proxy_standoff_cases_use_origin_pointing_velocity() -> None:
  top_contour = standoff_probe._top_contour_points()
  cases = standoff_probe._external_grid_cases(top_contour)

  for case in cases:
    _assert_velocity_points_to_origin(case)


def test_target_geometry_proxy_standoff_outcome_summary_exposes_damage_layers() -> None:
  record = {
    "case_id": "nose_standoff_0p5m",
    "warhead_family": "blast_fragmentation",
    "aspect": "nose",
    "standoff_distance_m": 0.5,
    "local_up_m": 0.0,
    "local_point_m": [8.0, 0.0, 0.0],
    "detonation_position_class": "external_top_contour_standoff",
    "proxy_component_primary_name": "cockpit_crew_station",
    "proxy_component_primary_system": "cockpit",
    "proxy_component_primary_distance_m": 0.5,
    "proxy_component_failure_probability": 0.6,
    "proxy_event_max_component_failure_probability": 0.7,
    "proxy_component_max_failure_probability_component_name": "mission_computer",
    "proxy_component_failure_observed": True,
    "proxy_component_damage_event_names": ["cockpit_crew_station"],
    "proxy_system_health_delta": -0.2,
    "proxy_structure_damage_delta": -0.1,
    "proxy_structure_integrity_after": 0.9,
    "proxy_structure_damage_observed": True,
    "proxy_structural_breakup_event_count": 0,
    "proxy_structural_breakup_observed": False,
    "proxy_structural_breakup_modes": [],
    "proxy_structural_breakup_part_refs": [],
  }

  summary = standoff_probe._outcome_summary([record])
  family = summary["by_family"]["blast_fragmentation"]
  heatmap = standoff_probe._heatmap_matrix([record])

  assert summary["status"] == "standoff_aspect_distance_outcomes_reported"
  assert summary["component_failure_observed_record_count"] == 1
  assert summary["structure_damage_observed_record_count"] == 1
  assert summary["structural_breakup_observed_record_count"] == 0
  assert (
    family["max_structure_damage_record"]["proxy_structure_damage_delta"]
    == -0.1
  )
  assert family["default_z_by_standoff_distance_m"][0][
    "mean_proxy_component_failure_probability"
  ] == 0.6
  assert heatmap["component_failure_observed_matrix"][0][0] is True
  assert heatmap["structure_damage_delta_matrix"][0][0] == -0.1
  assert heatmap["structural_breakup_observed_matrix"][0][0] is False


def test_target_geometry_proxy_xy_grid_classifies_all_samples() -> None:
  top_contour = standoff_probe._top_contour_points()
  aabbs = standoff_probe._proxy_aabbs()
  cases = standoff_probe._xy_grid_cases(top_contour=top_contour, aabbs=aabbs)
  by_xy = {
    (float(case["local_forward_m"]), float(case["local_right_m"])): case
    for case in cases
  }

  assert len(cases) == len(standoff_probe.XY_GRID_LEVELS_M) ** 2
  assert sorted({float(case["local_forward_m"]) for case in cases}) == sorted(
    float(value) for value in standoff_probe.XY_GRID_LEVELS_M
  )
  assert sorted({float(case["local_right_m"]) for case in cases}) == sorted(
    float(value) for value in standoff_probe.XY_GRID_LEVELS_M
  )

  center = by_xy[(0.0, 0.0)]
  assert center["detonation_position_class"] == "inside_component_debug"
  assert "center_fuselage_fuel_cell" in center["inside_component_names"]

  corner = by_xy[(-12.0, -12.0)]
  assert corner["detonation_position_class"] == "external_top_contour_standoff"

  matrix = standoff_probe._xy_position_class_matrix(cases)
  assert matrix["local_forward_levels_m"] == list(standoff_probe.XY_GRID_LEVELS_M)
  assert matrix["local_right_levels_m"] == list(standoff_probe.XY_GRID_LEVELS_M)
  assert len(matrix["detonation_position_class_matrix"]) == len(
    standoff_probe.XY_GRID_LEVELS_M
  )
