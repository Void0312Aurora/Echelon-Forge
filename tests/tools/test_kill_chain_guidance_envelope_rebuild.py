from __future__ import annotations

import json
import math

from tools.diagnostics import kill_chain_guidance_envelope_rebuild as envelope


def _fake_runner(**kwargs):
  range_km = float(kwargs["range_m"]) / 1000.0
  bearing_deg = float(kwargs["bearing_deg"])
  angle_deg = abs(bearing_deg)
  distance_m = 5.0 if angle_deg <= 45.0 else 25.0 + 0.1 * (range_km - 4.0)
  overrides = dict(kwargs["guidance_tuning_overrides"])
  return {
    "nearest_miss_distance_m": distance_m,
    "truth_min_distance_m": distance_m,
    "fuze_triggered": distance_m <= envelope.R_FUZE_M,
    "max_achieved_lateral_g": 20.0,
    "max_capture_component_g": 0.0,
    "max_preclamp_command_g": 22.0,
    "max_postclamp_command_g": 22.0,
    "guidance_runtime_observation_count": 10,
    "guidance_runtime_missing_acceleration_diagnostics_count": 0,
    "guidance_saturated_sample_count": 0,
    "guidance_saturation_fraction": 0.0,
    "guidance_mechanism_profile": None,
    "resolved_guidance_runtime": {
      "nav_gain": overrides["nav_gain"],
      "pn_los_rate_source": overrides["pn_los_rate_source"],
      "target_kinematics_estimator": overrides["target_kinematics_estimator"],
      "capture_guidance_mode": overrides["capture_guidance_mode"],
      "target_tracker_alpha": overrides["target_tracker_alpha"],
      "target_tracker_beta": overrides["target_tracker_beta"],
      "apn_target_accel_gain": overrides["apn_target_accel_gain"],
      "guidance_max_lateral_g": overrides["max_lateral_g"],
    },
    "stage_abstractions": [
      {
        "abstraction_stage": "approach",
        "observed": {
          "nearest_approach_time_s": 5.0,
          "closure_mps": 600.0,
        },
      }
    ],
  }


def _cell(range_km: float, angle_deg: float, state: str) -> dict[str, object]:
  return {
    "range_km": range_km,
    "offset_deg": angle_deg,
    "robust_state": state,
    "reclassified_launch_class": (
      "N" if state == envelope.ROBUST_HIT else "O" if state == envelope.ROBUST_MISS else "M"
    ),
  }


def test_formal_grid_expands_481_signed_cases_per_seed_and_passes() -> None:
  report = envelope.build_report(runner=_fake_runner)
  assert report["counts"]["main_cell_count"] == 13 * 19
  assert report["counts"]["main_run_count"] == 481 * 3
  assert report["counts"]["refinement_cell_count"] > 0
  assert report["audit"]["formal_full_grid"] is True
  assert report["audit"]["stage4_passed"] is True
  assert report["status"] == "continuous_launch_envelope_rebuilt"


def test_custom_grid_is_smoke_not_formal_stage4_pass() -> None:
  report = envelope.build_report(
    ranges_km=(4.0,),
    angles_deg=(30.0,),
    seeds=(20260621,),
    enable_refinement=False,
    runner=_fake_runner,
  )
  assert report["audit"]["data_integrity_passed"] is True
  assert report["audit"]["stage4_gate_values_passed"] is True
  assert report["audit"]["stage4_passed"] is False
  assert report["status"] == "custom_guidance_envelope_smoke_completed"


def test_runtime_diagnostics_and_mirror_distance_are_hard_gates() -> None:
  def broken_runner(**kwargs):
    result = _fake_runner(**kwargs)
    if float(kwargs["bearing_deg"]) > 0.0:
      result["nearest_miss_distance_m"] += 0.01
    result["guidance_runtime_missing_acceleration_diagnostics_count"] = 1
    return result

  report = envelope.build_report(
    ranges_km=(4.0,),
    angles_deg=(30.0,),
    seeds=(20260621,),
    enable_refinement=False,
    runner=broken_runner,
  )
  gates = report["audit"]["data_integrity_gates"]
  assert gates["production_acceleration_diagnostics_observed_for_every_run"] is False
  assert gates["mirror_nearest_distance_within_1e_3_m"] is False
  assert report["audit"]["stage4_gate_values_passed"] is False


def test_two_sided_range_window_is_allowed_but_two_hit_islands_fail() -> None:
  single_band = [
    _cell(4.0, 60.0, envelope.ROBUST_MISS),
    _cell(5.0, 60.0, envelope.ROBUST_HIT),
    _cell(6.0, 60.0, envelope.ROBUST_HIT),
    _cell(7.0, 60.0, envelope.ROBUST_MISS),
  ]
  assert envelope.topology_audit(single_band)["range_multi_interval_violation_count"] == 0

  two_islands = [
    _cell(4.0, 60.0, envelope.ROBUST_HIT),
    _cell(5.0, 60.0, envelope.ROBUST_MISS),
    _cell(6.0, 60.0, envelope.ROBUST_HIT),
  ]
  audit = envelope.topology_audit(two_islands)
  assert audit["range_multi_interval_violation_count"] == 1
  assert audit["expected_shape_passed"] is False


def test_bundle_hashes_the_selected_database_definition(tmp_path) -> None:
  database = tmp_path / "database"
  aim120 = database / "weapons/air_to_air/aim_120c.json"
  aim120.parent.mkdir(parents=True)
  aim120.write_text('{"name":"custom"}\n', encoding="utf-8")
  report = envelope.build_report(
    database_path=database,
    ranges_km=(4.0,),
    angles_deg=(30.0,),
    seeds=(20260621,),
    enable_refinement=False,
    runner=_fake_runner,
  )
  envelope.write_bundle(report, output_dir=tmp_path / "bundle", stem="envelope")
  manifest = json.loads(
    (tmp_path / "bundle/envelope_manifest.json").read_text(encoding="utf-8")
  )
  assert manifest["runtime"]["aim120_definition_path"] == str(aim120.resolve())
  assert manifest["runtime"]["aim120_definition_sha256"] == envelope._sha256(aim120)
  assert math.isclose(manifest["run_contract"]["R_fuze_m"], 15.0)
