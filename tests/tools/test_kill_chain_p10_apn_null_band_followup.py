from __future__ import annotations

import pytest

from tools.diagnostics import kill_chain_p10_apn_null_band_followup as followup


def _runtime(overrides: dict) -> dict:
  return {
    "nav_gain": overrides["nav_gain"],
    "pn_los_rate_source": overrides["pn_los_rate_source"],
    "target_kinematics_estimator": overrides["target_kinematics_estimator"],
    "capture_guidance_mode": overrides["capture_guidance_mode"],
    "target_tracker_alpha": overrides["target_tracker_alpha"],
    "target_tracker_beta": overrides["target_tracker_beta"],
    "target_tracker_gamma": overrides["target_tracker_gamma"],
    "apn_target_accel_gain": overrides["apn_target_accel_gain"],
    "guidance_max_lateral_g": overrides["max_lateral_g"],
  }


def _fake_runner(**kwargs):
  range_km = float(kwargs["range_m"]) / 1000.0
  gain = float(kwargs["guidance_tuning_overrides"]["apn_target_accel_gain"])
  baseline = 0.0015 if range_km == 8.0 else 2.0 + abs(range_km - 8.0)
  nearest = baseline + (gain * 1.0e-4 if range_km == 8.0 else -gain)
  trace = []
  for index in range(40):
    time_s = index * 0.1
    valid = index >= 3
    error = 8.0 if index < 3 else 0.05
    trace.append(
      {
        "time_s": time_s,
        "truth_distance_m": max(nearest, 4000.0 - 1000.0 * time_s),
        "target_acceleration_valid": valid,
        "target_accel_error_mps2": error,
        "guidance_pn_accel_mps2": 10.0,
        "guidance_apn_lateral_accel_mps2": gain * 2.0 if valid else 0.0,
        "guidance_component_sum_error_mps2": 1.0e-12,
      }
    )
  return {
    "case_id": kwargs["case_id"],
    "nearest_miss_distance_m": nearest,
    "sim_time_s": 4.0,
    "runtime_facade": {"approach_fact": {"nearest_approach_time_s": 4.0}},
    "resolved_guidance_runtime": _runtime(kwargs["guidance_tuning_overrides"]),
    "guidance_runtime_trace": trace,
  }


def test_summarize_result_captures_phase_and_command_evidence() -> None:
  raw = _fake_runner(
    case_id="fixture",
    range_m=8000.0,
    bearing_deg=-60.0,
    seed=20260621,
    guidance_tuning_overrides={
      **followup.p10.PRODUCTION_MECHANISM_TUNING,
      "apn_target_accel_gain": 0.125,
    },
    target_acceleration_mps2=(-8.0, 0.0, 0.0),
  )
  row = followup._summarize_result(
    raw,
    range_km=8.0,
    bearing_deg=-60.0,
    target_accel_x_mps2=-8.0,
    apn_gain=0.125,
    seed=20260621,
  )

  assert row["estimator_first_valid_time_s"] == pytest.approx(0.3)
  assert row["estimator_convergence_time_s"] == pytest.approx(0.3)
  assert row["time_to_go_at_estimator_convergence_s"] == pytest.approx(3.7)
  assert row["max_pn_acceleration_mps2"] == 10.0
  assert row["max_apn_acceleration_mps2"] == 0.25
  assert row["apn_impulse_mps"] > 0.0
  assert row["resolved_runtime_mismatch"] == {}


def test_evaluation_attributes_null_band_to_near_zero_baseline() -> None:
  old_ranges = followup.RANGES_KM
  old_corners = followup.MIRRORED_CORNERS
  old_gains = followup.APN_GAINS
  old_seeds = followup.SEEDS
  try:
    followup.RANGES_KM = (7.0, 8.0, 9.0)
    followup.MIRRORED_CORNERS = ((-60.0, -8.0), (60.0, 8.0))
    followup.APN_GAINS = (0.0, 0.125)
    followup.SEEDS = (20260621,)
    report = followup.build_report(runner=_fake_runner)
  finally:
    followup.RANGES_KM = old_ranges
    followup.MIRRORED_CORNERS = old_corners
    followup.APN_GAINS = old_gains
    followup.SEEDS = old_seeds

  assert report["status"] == "p10_apn_null_band_explained"
  assert report["evaluation"]["explained"] is True
  assert report["evaluation"]["mechanism"] == (
    "nearest_distance_observable_floor_with_active_apn"
  )
  assert report["evaluation"]["ranges_with_all_nonzero_gains_null_km"] == [8.0]
  assert report["evaluation"]["first_non_null_range_above_8_km"] == 9.0
  assert report["evaluation"]["gates"]["range_sweep_observes_response_transition"] is True
  dispositions = report["conclusion"]["hypothesis_disposition"]
  assert dispositions["pn_baseline_near_local_optimum"].startswith("supported")
  assert dispositions["acceleration_estimator_transient_timing"].startswith(
    "not_supported"
  )
  report["evaluation"]["explained"] = False
  assert "不能确认 8 km 低响应带的成因" in followup.conclusions_zh(report)


def test_renderer_writes_nonempty_png(tmp_path) -> None:
  rows = []
  for range_km in followup.RANGES_KM:
    for gain in followup.APN_GAINS:
      rows.append(
        {
          "range_km": range_km,
          "apn_gain": gain,
          "mean_nearest_distance_m": 0.001 if range_km == 8.0 else 2.0,
          "mean_nearest_distance_delta_vs_apn0_m": 0.0 if gain == 0.0 else -gain,
          "mean_nearest_approach_time_s": 12.0 + range_km,
          "mean_estimator_convergence_time_s": 0.5,
          "mean_pn_impulse_mps": 80.0,
          "mean_apn_impulse_mps": gain * 8.0,
        }
      )
  report = {
    "matrix": {
      "ranges_km": list(followup.RANGES_KM),
      "apn_gains": list(followup.APN_GAINS),
    },
    "evaluation": {"explained": True},
    "cells": rows,
  }
  output = tmp_path / "figure.png"
  from tools.diagnostics.render_kill_chain_p10_apn_null_band import render

  render(report, output)
  assert output.stat().st_size > 1000
