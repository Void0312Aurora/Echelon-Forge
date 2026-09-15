from __future__ import annotations

import pytest

from tools.diagnostics import kill_chain_maneuver_apn_admission as admission


def test_summarize_run_preserves_tracker_and_apn_evidence() -> None:
  gain = 0.5
  result = {
    "case_id": "synthetic",
    "nearest_miss_distance_m": 7.5,
    "max_achieved_lateral_g": 12.0,
    "resolved_guidance_runtime": {
      **{
        key: value
        for key, value in admission.PRODUCTION_MECHANISM_TUNING.items()
        if key != "max_lateral_g"
      },
      "guidance_max_lateral_g": 35.0,
      "apn_target_accel_gain": gain,
    },
    "guidance_runtime_trace": [
      {
        "time_s": 1.5,
        "truth_distance_m": 4000.0,
        "target_acceleration_valid": True,
        "target_accel_error_mps2": 1.0,
        "target_track_accel_mps2": 7.0,
        "guidance_apn_lateral_accel_mps2": 2.0,
        "guidance_component_sum_error_mps2": 1.0e-12,
      },
      {
        "time_s": 2.0,
        "truth_distance_m": 3000.0,
        "target_acceleration_valid": True,
        "target_accel_error_mps2": 0.5,
        "target_track_accel_mps2": 7.5,
        "guidance_apn_lateral_accel_mps2": 3.0,
        "guidance_component_sum_error_mps2": 2.0e-12,
      },
    ],
  }

  row = admission._summarize_run(
    result,
    tier="clean_stage4",
    range_km=8.0,
    bearing_deg=30.0,
    target_accel_x_mps2=8.0,
    apn_gain=gain,
    seed=20260621,
  )

  assert row["entered_R_fuze"] is True
  assert row["rho_fuze"] == 0.5
  assert row["acceleration_valid_observed"] is True
  assert row["terminal_acceleration_error_mps2"] == 0.5
  assert row["max_estimated_acceleration_mps2"] == 7.5
  assert row["max_apn_acceleration_mps2"] == 3.0
  assert row["resolved_runtime_mismatch"] == {}


def test_clear_net_benefit_requires_no_envelope_regression() -> None:
  baseline = {
    "apn_gain": 0.0,
    "hit_count": 28,
    "worst_nearest_distance_m": 90.0,
    "total_excess_over_R_fuze_m": 150.0,
  }
  beneficial = {
    "apn_gain": 0.125,
    "hit_count": 28,
    "worst_nearest_distance_m": 85.0,
    "total_excess_over_R_fuze_m": 140.0,
  }
  regression = {
    **beneficial,
    "worst_nearest_distance_m": 95.0,
  }

  assert admission._clear_net_benefit(beneficial, baseline) is True
  assert admission._clear_net_benefit(regression, baseline) is False


def test_mirror_error_pairs_bearing_and_acceleration_signs() -> None:
  common = {
    "tier": "clean_stage4",
    "range_km": 8.0,
    "apn_gain": 0.5,
    "seed": 20260621,
  }
  rows = [
    {
      **common,
      "bearing_deg": -30.0,
      "target_accel_x_mps2": -8.0,
      "nearest_distance_m": 2.0000,
    },
    {
      **common,
      "bearing_deg": 30.0,
      "target_accel_x_mps2": 8.0,
      "nearest_distance_m": 2.0004,
    },
  ]

  assert admission._mirror_error(rows) == pytest.approx(0.0004)
