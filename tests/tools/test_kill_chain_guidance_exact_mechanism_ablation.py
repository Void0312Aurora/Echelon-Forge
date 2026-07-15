from __future__ import annotations

import json

import pytest

from tools.diagnostics import kill_chain_decoupling_probe as probe
from tools.diagnostics import kill_chain_guidance_exact_mechanism_ablation as exact


def test_mechanism_profile_normalization_is_discrete() -> None:
  assert probe._normalize_guidance_mechanism_profile({}) == {
    "capture_mode": 1,
    "pn_mode": 0,
    "lead_mode": 2,
    "kinematics_source": 0,
    "apn_mode": 1,
    "capture_base_range_mode": 0,
    "capture_terminal_weight_mode": 0,
    "capture_lead_blend_mode": 0,
  }
  assert probe._normalize_guidance_mechanism_profile(None) is None
  with pytest.raises(ValueError, match="unsupported guidance mechanism profile fields"):
    probe._normalize_guidance_mechanism_profile({"nav_gain": 4})
  with pytest.raises(ValueError, match="pn_mode must be in"):
    probe._normalize_guidance_mechanism_profile({"pn_mode": 4})
  with pytest.raises(ValueError, match="must be an integer"):
    probe._normalize_guidance_mechanism_profile({"lead_mode": 1.5})


def test_exact_matrix_has_mirrors_controls_and_no_epsilon_gates() -> None:
  cases = exact.default_cases()
  assert len(cases) == 20
  assert {row["case_group"] for row in cases} == {
    "N30",
    "M45",
    "stress60",
    "O_near",
    "O_far",
  }
  assert {
    row["bearing_deg"]
    for row in cases
    if row["range_km"] == 4.0 and row["offset_deg"] == 45.0
  } == {-45.0, 45.0}
  variants = exact.selected_variants()
  assert len(variants) == 16
  assert all("profile" in row for row in variants)
  assert exact.FROZEN_TUNING == {
    "nav_gain": 4.0,
    "max_lateral_g": 35.0,
    "apn_target_accel_gain": 0.5,
  }


def _fake_runner(**kwargs):
  profile = kwargs.get("guidance_mechanism_profile")
  if profile is None:
    distance = 20.0
  else:
    distance = 100.0
    if profile["capture_mode"]:
      distance -= 30.0
    if profile["pn_mode"] != exact.PN_OFF:
      distance -= {
        exact.PN_LEGACY: 20.0,
        exact.PN_WORLD_LOS_HISTORY: 25.0,
        exact.PN_WORLD_TRACK_ANALYTIC: 35.0,
      }[profile["pn_mode"]]
    if profile["capture_mode"] and profile["lead_mode"] != exact.LEAD_OFF:
      distance -= 15.0
      if profile["lead_mode"] == exact.LEAD_QUADRATIC and not (
        profile["kinematics_source"] == exact.KINEMATICS_TRUTH_CV
      ):
        distance -= 5.0
    if profile["apn_mode"] and not (
      profile["kinematics_source"] == exact.KINEMATICS_TRUTH_CV
    ):
      distance -= 2.0
  trace = [
    {
      "guidance_capture_accel_mps2": 10.0,
      "guidance_pn_accel_mps2": 20.0,
      "guidance_apn_lateral_accel_mps2": 1.0,
      "guidance_preclamp_accel_mps2": 31.0,
      "guidance_postclamp_accel_mps2": 31.0,
      "guidance_component_sum_error_mps2": 0.0,
      "guidance_los_rate_rad_s": 0.1,
      "heading_velocity_error_deg": 40.0,
      "guidance_pn_source_used": 1,
      "guidance_target_kinematics_source_used": 1,
    }
  ]
  return {
    "nearest_miss_distance_m": distance,
    "truth_min_distance_m": distance,
    "guidance_runtime_trace": trace,
    "stage_abstractions": [
      {
        "abstraction_stage": "approach",
        "observed": {
          "nearest_approach_time_s": 2.0,
          "local_forward_m": -distance,
          "local_right_m": distance / 2.0,
          "local_up_m": 0.0,
          "aspect_bucket": "tail",
        },
      }
    ],
  }


def test_exact_report_uses_pair_means_and_grouped_effects(tmp_path) -> None:
  cases = exact.default_cases()[:2]
  variants = exact.selected_variants(
    (
      "legacy_full_track_quadratic",
      "legacy_no_capture",
      "legacy_no_capture_no_lead",
    )
  )
  report = exact.generate_report(
    cases=cases,
    variants=variants,
    runner=_fake_runner,
    run_baseline_equivalence=False,
  )
  assert report["run_count"] == 6
  assert len(report["pair_rows"]) == 3
  effects = {
    row["effect_id"]: row["miss_distance_delta_m"]
    for row in report["matched_effects"]
  }
  assert effects["remove_capture_from_current"] == 50.0
  assert effects["lead_requires_capture_invariant"] == 0.0
  assert report["summary"]["matched_effects"]["remove_capture_from_current"][
    "mean_delta_by_case_group_m"
  ] == {"N30": 50.0}

  paths = exact.write_bundle(report, output_dir=tmp_path, stem="exact")
  assert set(paths) == {
    "json",
    "rows_csv",
    "pairs_csv",
    "effects_csv",
    "summary_md",
  }
  payload = json.loads((tmp_path / "exact.json").read_text(encoding="utf-8"))
  assert payload["schema_version"] == exact.SCHEMA_VERSION
  assert b"\r\n" not in (tmp_path / "exact_rows.csv").read_bytes()


def test_runtime_profile_preserves_legacy_baseline_and_exports_vectors() -> None:
  baseline = probe.run_guidance_case(
    case_id="exact_profile_unattached_baseline",
    range_m=4000.0,
    bearing_deg=45.0,
    guidance_tuning_overrides=dict(exact.FROZEN_TUNING),
  )
  profiled = probe.run_guidance_case(
    case_id="exact_profile_attached_legacy",
    range_m=4000.0,
    bearing_deg=45.0,
    guidance_tuning_overrides=dict(exact.FROZEN_TUNING),
    guidance_mechanism_profile={
      "capture_mode": 1,
      "pn_mode": exact.PN_LEGACY,
      "lead_mode": exact.LEAD_QUADRATIC,
      "kinematics_source": exact.KINEMATICS_TRACK,
      "apn_mode": 1,
    },
    collect_guidance_runtime_trace=True,
    guidance_trace_stride=10,
  )
  assert profiled["nearest_miss_distance_m"] == pytest.approx(
    baseline["nearest_miss_distance_m"], abs=1.0e-3
  )
  trace = profiled["guidance_runtime_trace"]
  assert trace
  assert trace[0]["guidance_mechanism_profile_active"] is True
  assert {
    "guidance_capture_accel_xyz_mps2",
    "guidance_pn_accel_xyz_mps2",
    "guidance_apn_accel_xyz_mps2",
    "guidance_preclamp_accel_xyz_mps2",
    "guidance_postclamp_accel_xyz_mps2",
    "guidance_los_rate_xyz_rad_s",
    "guidance_achieved_accel_xyz_mps2",
  }.issubset(trace[0])
  assert max(row["guidance_component_sum_error_mps2"] for row in trace) < 1.0e-6


def test_truth_cv_removes_acceleration_lead_and_apn_effects() -> None:
  common = {
    "case_id": "truth_cv_invariant",
    "range_m": 4000.0,
    "bearing_deg": 45.0,
    "guidance_tuning_overrides": dict(exact.FROZEN_TUNING),
  }
  velocity = probe.run_guidance_case(
    **common,
    guidance_mechanism_profile={
      "capture_mode": 1,
      "pn_mode": exact.PN_WORLD_TRACK_ANALYTIC,
      "lead_mode": exact.LEAD_VELOCITY,
      "kinematics_source": exact.KINEMATICS_TRUTH_CV,
      "apn_mode": 0,
    },
  )
  quadratic_apn = probe.run_guidance_case(
    **{**common, "case_id": "truth_cv_invariant_quadratic_apn"},
    guidance_mechanism_profile={
      "capture_mode": 1,
      "pn_mode": exact.PN_WORLD_TRACK_ANALYTIC,
      "lead_mode": exact.LEAD_QUADRATIC,
      "kinematics_source": exact.KINEMATICS_TRUTH_CV,
      "apn_mode": 1,
    },
  )
  assert quadratic_apn["nearest_miss_distance_m"] == pytest.approx(
    velocity["nearest_miss_distance_m"], abs=1.0e-9
  )
