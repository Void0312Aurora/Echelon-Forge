from __future__ import annotations

import json
import math

from tools.diagnostics import kill_chain_guidance_scalar_calibration as calibration


def _stage4_report() -> dict[str, object]:
  cells = []
  for range_km in (4.0, 5.0, 6.0):
    for angle_deg, launch_class in ((0.0, "N"), (5.0, "M"), (10.0, "O")):
      cells.append(
        {
          "range_km": range_km,
          "offset_deg": angle_deg,
          "reclassified_launch_class": launch_class,
        }
      )
  return {
    "schema_version": "a2.kill_chain_guidance_envelope_rebuild.v1",
    "status": "continuous_launch_envelope_rebuilt",
    "audit": {"stage4_passed": True},
    "main_cells": cells,
  }


def _runtime(overrides: dict[str, float | int]) -> dict[str, float | int]:
  return {
    "nav_gain": overrides["nav_gain"],
    "pn_los_rate_source": overrides["pn_los_rate_source"],
    "target_kinematics_estimator": overrides["target_kinematics_estimator"],
    "capture_guidance_mode": overrides["capture_guidance_mode"],
    "target_tracker_alpha": overrides["target_tracker_alpha"],
    "target_tracker_beta": overrides["target_tracker_beta"],
    "apn_target_accel_gain": overrides["apn_target_accel_gain"],
    "guidance_max_lateral_g": overrides["max_lateral_g"],
  }


def _result(kwargs, distance_m: float, *, saturation: float = 0.2):
  overrides = dict(kwargs["guidance_tuning_overrides"])
  return {
    "nearest_miss_distance_m": distance_m,
    "truth_min_distance_m": distance_m,
    "fuze_triggered": distance_m <= calibration.R_FUZE_M,
    "max_achieved_lateral_g": 30.0,
    "max_capture_component_g": 0.0,
    "max_preclamp_command_g": 50.0,
    "max_postclamp_command_g": 35.0,
    "guidance_runtime_observation_count": 10,
    "guidance_runtime_missing_acceleration_diagnostics_count": 0,
    "guidance_saturation_fraction": saturation,
    "guidance_mechanism_profile": None,
    "resolved_guidance_runtime": _runtime(overrides),
  }


def _benefit_runner(**kwargs):
  angle_deg = abs(float(kwargs["bearing_deg"]))
  nav_gain = float(kwargs["guidance_tuning_overrides"]["nav_gain"])
  if math.isclose(nav_gain, 3.5):
    distance_m = 20.0 if angle_deg <= 2.5 else 25.0
  elif angle_deg <= 2.5:
    distance_m = 5.0 if math.isclose(nav_gain, 4.0) else 4.0
  elif angle_deg <= 5.0:
    distance_m = 10.0
  elif angle_deg < 10.0:
    distance_m = 5.0 if math.isclose(nav_gain, 4.5) else 25.0
  else:
    distance_m = 25.0
  return _result(kwargs, distance_m)


def _neutral_runner(**kwargs):
  angle_deg = abs(float(kwargs["bearing_deg"]))
  distance_m = 5.0 if angle_deg <= 5.0 else 25.0
  return _result(kwargs, distance_m)


def _saturation_benefit_runner(**kwargs):
  angle_deg = abs(float(kwargs["bearing_deg"]))
  nav_gain = float(kwargs["guidance_tuning_overrides"]["nav_gain"])
  distance_m = 5.0 if angle_deg <= 5.0 else 25.0
  saturation = 0.1 if math.isclose(nav_gain, 4.5) else 0.2
  return _result(kwargs, distance_m, saturation=saturation)


def test_only_nav_gain_is_evaluated_and_other_scalars_are_frozen() -> None:
  rows = {row["parameter"]: row for row in calibration.identifiability_table()}
  assert rows["nav_gain"]["stage5_status"] == "evaluated_OFAT"
  assert rows["capture_guidance_scalars"]["stage5_status"] == "excluded"
  assert rows["apn_target_accel_gain"]["stage5_status"] == "excluded_frozen_at_0.5"
  assert rows["target_tracker_alpha_beta"]["stage5_status"] == "excluded_frozen_at_0.20_0.02"
  assert rows["max_lateral_g"]["stage5_status"] == "constraint_frozen_at_35"


def test_N_and_O_are_hard_constraints_but_M_is_observation_only() -> None:
  report = calibration.build_report(
    stage4_report=_stage4_report(),
    nav_gains=(3.5, 4.0),
    seeds=(1, 2, 3),
    runner=_benefit_runner,
  )
  candidates = {float(row["nav_gain"]): row for row in report["candidate_summaries"]}
  assert candidates[3.5]["gates"]["stage4_N_cells_remain_robust_hit"] is False
  assert candidates[3.5]["audit"]["N_violation_count"] == 3
  assert candidates[3.5]["hard_gate_passed"] is False
  assert candidates[4.0]["metrics"]["M_observed_transition_counts"] == {
    "M->robust_hit": 3
  }
  assert "M" not in " ".join(candidates[4.0]["gates"])


def test_more_unlabelled_holdout_hits_and_shifted_contour_cannot_select_candidate() -> None:
  report = calibration.build_report(
    stage4_report=_stage4_report(),
    nav_gains=(4.0, 4.5),
    seeds=(1, 2, 3),
    runner=_benefit_runner,
  )
  assert report["selection"]["selected_nav_gain"] == 4.0
  assert report["selection"]["decision"] == "retain_nav_gain_4_no_clear_net_benefit"
  comparison = next(
    row for row in report["comparisons_vs_baseline"] if row["nav_gain"] == 4.5
  )
  assert comparison["clear_net_benefit"] is False
  assert comparison["deltas_vs_baseline"]["holdout_robust_hit_count"] == 2
  assert comparison["deltas_vs_baseline"]["theta_fuze_max_displacement_deg"] == 5.0
  assert (
    comparison["regression_guards"]["theta_fuze_max_displacement_within_2_5deg"]
    is False
  )
  assert not any("holdout" in key for key in comparison["material_improvements"])


def test_material_saturation_P95_gain_with_stable_contour_can_select_candidate() -> None:
  report = calibration.build_report(
    stage4_report=_stage4_report(),
    nav_gains=(4.0, 4.5),
    seeds=(1, 2, 3),
    runner=_saturation_benefit_runner,
  )
  assert report["selection"]["selected_nav_gain"] == 4.5
  comparison = next(
    row for row in report["comparisons_vs_baseline"] if row["nav_gain"] == 4.5
  )
  assert comparison["clear_net_benefit"] is True
  assert comparison["deltas_vs_baseline"]["theta_fuze_max_displacement_deg"] == 0.0
  assert math.isclose(
    comparison["deltas_vs_baseline"]["guidance_saturation_fraction_p95"],
    -0.1,
  )


def test_no_material_gain_retains_N4() -> None:
  report = calibration.build_report(
    stage4_report=_stage4_report(),
    nav_gains=(3.75, 4.0, 4.25),
    seeds=(1, 2, 3),
    runner=_neutral_runner,
  )
  assert report["selection"]["selected_nav_gain"] == 4.0
  assert report["selection"]["decision"] == "retain_nav_gain_4_no_clear_net_benefit"
  assert report["selection"]["clear_net_benefit_candidate_ids"] == []


def test_scalar_selection_never_auto_promotes_default_without_maneuver_authority() -> None:
  report = calibration.build_report(
    stage4_report=_stage4_report(),
    nav_gains=(4.0, 4.5),
    seeds=(1, 2, 3),
    runner=_benefit_runner,
  )
  assert report["selection"]["default_promotion_ready"] is False
  assert report["selection"]["default_promotion_status"] == "held"
  assert report["release_gate"]["default_promotion_ready"] is False
  assert "maneuver" in report["release_gate"]["status"]


def test_mirror_seed_runtime_capture_and_35g_are_hard_gates() -> None:
  def broken_runner(**kwargs):
    result = _neutral_runner(**kwargs)
    if float(kwargs["bearing_deg"]) > 0.0:
      result["nearest_miss_distance_m"] += 0.01
    if int(kwargs["seed"]) == 3:
      result["nearest_miss_distance_m"] += 0.02
    result["max_capture_component_g"] = 0.1
    result["max_postclamp_command_g"] = 35.1
    result["guidance_runtime_missing_acceleration_diagnostics_count"] = 1
    return result

  report = calibration.build_report(
    stage4_report=_stage4_report(),
    nav_gains=(4.0,),
    seeds=(1, 2, 3),
    runner=broken_runner,
  )
  candidate = report["candidate_summaries"][0]
  gates = candidate["gates"]
  assert gates["mirror_nearest_distance_within_1e_3_m"] is False
  assert gates["seed_nearest_distance_spread_within_1e_3_m"] is False
  assert gates["capture_component_zero_within_1e_12_g"] is False
  assert gates["postclamp_command_not_above_35g"] is False
  assert gates["production_acceleration_diagnostics_observed_for_every_run"] is False
  assert candidate["hard_gate_passed"] is False


def test_bundle_hashes_stage4_input_and_keeps_release_held(tmp_path) -> None:
  stage4_path = tmp_path / "stage4.json"
  stage4_path.write_text(
    json.dumps(_stage4_report(), ensure_ascii=False) + "\n", encoding="utf-8"
  )
  database = tmp_path / "database"
  aim120 = database / "weapons/air_to_air/aim_120c.json"
  aim120.parent.mkdir(parents=True)
  aim120.write_text('{"name":"custom"}\n', encoding="utf-8")
  report = calibration.build_report(
    stage4_report=_stage4_report(),
    stage4_report_path=stage4_path,
    database_path=database,
    nav_gains=(4.0,),
    seeds=(1, 2, 3),
    runner=_neutral_runner,
  )
  calibration.write_bundle(
    report,
    output_dir=tmp_path / "bundle",
    stem="scalar",
    stage4_report_path=stage4_path,
  )
  manifest = json.loads(
    (tmp_path / "bundle/scalar_manifest.json").read_text(encoding="utf-8")
  )
  assert manifest["inputs"]["stage4_report_sha256"] == calibration._sha256(stage4_path)
  assert manifest["inputs"]["aim120_definition_sha256"] == calibration._sha256(aim120)
  assert manifest["selection"]["default_promotion_ready"] is False
