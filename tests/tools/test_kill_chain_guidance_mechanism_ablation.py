from __future__ import annotations

import json

import pytest

from tools.diagnostics import kill_chain_decoupling_probe as probe
from tools.diagnostics import kill_chain_guidance_mechanism_ablation as ablation


class _Tuning:
  nav_gain = 0.0
  apn_target_accel_gain = 0.0
  autopilot_order = 1


def test_guidance_tuning_overrides_are_explicit_and_finite() -> None:
  tuning = _Tuning()
  applied = probe._apply_guidance_tuning_overrides(
    tuning,
    {"nav_gain": 4.0, "apn_target_accel_gain": 0.5, "autopilot_order": 2},
  )
  assert applied == {
    "apn_target_accel_gain": 0.5,
    "autopilot_order": 2,
    "nav_gain": 4.0,
  }
  assert tuning.nav_gain == 4.0
  assert tuning.apn_target_accel_gain == 0.5
  assert tuning.autopilot_order == 2

  with pytest.raises(ValueError, match="unsupported guidance tuning override"):
    probe._apply_guidance_tuning_overrides(tuning, {"capture_gain": 0.0})
  with pytest.raises(ValueError, match="must be finite"):
    probe._apply_guidance_tuning_overrides(tuning, {"nav_gain": float("nan")})


def test_default_matrix_contains_mirrors_and_negative_controls() -> None:
  cases = ablation.default_cases()
  assert len(cases) == 20
  assert {row["launch_class"] for row in cases} == {"N", "M", "O"}
  assert any(row["range_km"] == 10.0 and row["offset_deg"] == 60.0 for row in cases)
  assert any(row["range_km"] == 16.0 and row["offset_deg"] == 30.0 for row in cases)
  assert {
    row["bearing_deg"]
    for row in cases
    if row["range_km"] == 4.0 and row["offset_deg"] == 45.0
  } == {-45.0, 45.0}
  assert [row["variant_id"] for row in ablation.selected_variants()] == [
    "capture_only",
    "capture_pn",
    "capture_lead",
    "capture_pn_lead",
    "capture_lead_apn",
    "full",
    "full_no_track_filter",
    "full_fast_scalar_autopilot",
    "full_autopilot_order2",
    "full_autopilot_order3",
  ]


def _fake_runner(**kwargs):
  overrides = dict(kwargs["guidance_tuning_overrides"])
  nav_gain = float(overrides["nav_gain"])
  apn_gain = float(overrides["apn_target_accel_gain"])
  key = (
    "pn" if nav_gain > 1.0 else "no_pn",
    "apn" if apn_gain > 0.1 else "lead" if apn_gain > 0.0 else "no_lead",
  )
  distances = {
    ("no_pn", "no_lead"): 100.0,
    ("pn", "no_lead"): 70.0,
    ("no_pn", "lead"): 40.0,
    ("pn", "lead"): 20.0,
    ("no_pn", "apn"): 41.0,
    ("pn", "apn"): 21.0,
  }
  distance = distances[key]
  trace = [
    {
      "time_s": 1.0,
      "truth_distance_m": distance + 10.0,
      "commanded_lateral_accel_mps2": 9.80665,
      "achieved_lateral_accel_mps2": 8.0,
      "command_saturated": False,
      "bearing_rate_deg_s": 2.0,
      "guidance_lead_time_s": 2.5 if apn_gain > 0.0 else 0.0,
      "guidance_lead_blend": 0.55 if apn_gain > 0.0 else 0.0,
      "guidance_apn_lateral_accel_mps2": 1.0 if apn_gain > 0.1 else 0.0,
      "target_track_accel_mps2": 20.0,
      "heading_velocity_error_deg": 30.0,
      "current_speed_mps": 800.0,
      "filtered_range_m": distance + 10.0,
    },
    {
      "time_s": 2.0,
      "truth_distance_m": distance,
      "commanded_lateral_accel_mps2": 19.6133,
      "achieved_lateral_accel_mps2": 18.0,
      "command_saturated": True,
      "bearing_rate_deg_s": 3.0,
      "guidance_lead_time_s": 1.0 if apn_gain > 0.0 else 0.0,
      "guidance_lead_blend": 0.55 if apn_gain > 0.0 else 0.0,
      "guidance_apn_lateral_accel_mps2": 2.0 if apn_gain > 0.1 else 0.0,
      "target_track_accel_mps2": 10.0,
      "heading_velocity_error_deg": 60.0,
      "current_speed_mps": 700.0,
      "filtered_range_m": distance,
    },
  ]
  return {
    "nearest_miss_distance_m": distance,
    "truth_min_distance_m": distance,
    "guidance_runtime_trace": trace,
    "stage_abstractions": [
      {
        "abstraction_stage": "approach",
        "observed": {
          "miss_distance_m": distance,
          "nearest_approach_time_s": 2.0,
          "local_forward_m": -distance,
          "local_right_m": distance / 2.0,
          "local_up_m": 0.0,
          "closure_mps": 1000.0,
          "aspect_bucket": "tail",
        },
      }
    ],
  }


def test_report_computes_conditional_mechanism_effects(tmp_path) -> None:
  case = ablation.default_cases()[0]
  report = ablation.generate_report(cases=[case], runner=_fake_runner)
  assert report["run_count"] == 10
  effects = {
    row["effect_id"]: row["miss_distance_delta_m"]
    for row in report["conditional_effects"]
  }
  assert effects["pn_without_lead_apn"] == -30.0
  assert effects["lead_without_pn"] == -60.0
  assert effects["lead_with_pn"] == -50.0
  assert effects["apn_with_pn"] == 1.0
  assert report["summary"]["conditional_effects"]["lead_with_pn"][
    "interpretation_counts"
  ] == {"improved": 1}

  paths = ablation.write_bundle(report, output_dir=tmp_path, stem="ablation")
  assert set(paths) == {"json", "rows_csv", "effects_csv", "summary_md"}
  payload = json.loads((tmp_path / "ablation.json").read_text(encoding="utf-8"))
  assert payload["schema_version"] == ablation.SCHEMA_VERSION
  assert b"\r\n" not in (tmp_path / "ablation_rows.csv").read_bytes()
  assert b"\r\n" not in (tmp_path / "ablation_effects.csv").read_bytes()
  assert "lead_with_pn" in (tmp_path / "ablation_summary.md").read_text(
    encoding="utf-8"
  )


def test_empty_override_preserves_baseline_and_trace_stride() -> None:
  baseline = probe.run_guidance_case(
    case_id="guidance_ablation_baseline_equivalence",
    range_m=4000.0,
    bearing_deg=45.0,
  )
  traced = probe.run_guidance_case(
    case_id="guidance_ablation_empty_override_equivalence",
    range_m=4000.0,
    bearing_deg=45.0,
    guidance_tuning_overrides={},
    collect_guidance_runtime_trace=True,
    guidance_trace_stride=10,
  )
  assert traced["guidance_tuning_overrides"] == {}
  assert traced["nearest_miss_distance_m"] == pytest.approx(
    baseline["nearest_miss_distance_m"],
    abs=1.0e-9,
  )
  trace = traced["guidance_runtime_trace"]
  assert trace
  assert {
    "command_saturated",
    "guidance_apn_lateral_accel_mps2",
    "guidance_lead_blend",
    "heading_velocity_error_deg",
    "target_track_accel_mps2",
  }.issubset(trace[0])
  assert len(trace) < int(traced["step"]) / 5
