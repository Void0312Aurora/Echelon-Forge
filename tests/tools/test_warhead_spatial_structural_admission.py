from __future__ import annotations

import pytest

from tools.geometry import warhead_spatial_structural_admission as admission


def _row(
  *,
  family: str = "blast_fragmentation",
  direction: str = "front",
  standoff: float = 0.5,
  heading: float = 0.0,
  effect: float = 0.6,
  orientation: float = 0.9,
) -> dict[str, object]:
  event = {
    "spatial_projection_trace_valid": True,
    "spatial_projection_effect_scale": effect,
    "spatial_projection_base_scale": 0.7,
    "spatial_projection_near_field_floor": 0.75,
    "spatial_projection_floor_selected_scale": 0.75,
    "spatial_projection_preclamp_scale": effect,
    "spatial_projection_min_bound": 0.05,
    "spatial_projection_max_bound": 0.8,
    "spatial_projection_axis_weight": 1.0,
    "spatial_projection_orientation_weight": orientation,
    "spatial_projection_armor_scale": 1.0,
    "spatial_projection_exposure_scale": 1.0,
    "spatial_projection_sampling_scale": effect / (0.75 * orientation),
    "spatial_projection_near_field_floor_applied": True,
    "spatial_projection_effect_scale_clamped": False,
    "spatial_effect_scale": effect,
  }
  return {
    "case_id": f"{family}:{direction}:{standoff}:{heading}",
    "warhead_family": family,
    "direction": direction,
    "standoff_m": standoff,
    "detonation_attitude_deg": [heading, 0.0, 0.0],
    "event": event,
  }


def test_case_matrix_has_six_directions_and_eight_headings() -> None:
  cases = list(admission._case_definitions())
  assert len(cases) == 2 * 6 * 4 * 8
  assert {str(case["direction"]) for case in cases} == set(admission.DIRECTION_ANCHORS)
  assert sorted({float(case["detonation_attitude_deg"][0]) for case in cases}) == sorted(
    admission.ATTITUDES_DEG
  )


@pytest.mark.parametrize("target_heading_deg", [0.0, 90.0, 180.0, 270.0])
def test_runtime_closure_is_rotation_invariant_for_all_body_directions(
  target_heading_deg: float,
) -> None:
  cases = [
    case
    for case in admission._case_definitions()
    if case["warhead_family"] == "continuous_rod"
    and case["standoff_m"] == 0.5
    and case["detonation_attitude_deg"][0] == 0.0
  ]
  assert {case["direction"] for case in cases} == set(admission.DIRECTION_ANCHORS)
  for index, case in enumerate(cases):
    event = admission._event_row(
      case,
      20260930 + index,
      target_heading_deg=target_heading_deg,
    )["event"]
    assert event["vulnerability_closure_mps"] == pytest.approx(
      admission.MISSILE_SPEED_MPS, abs=1.0e-6
    )


def test_evaluate_rows_accepts_a_closed_projection_trace() -> None:
  evaluation = admission.evaluate_rows([_row()])
  assert evaluation["diagnostic_trace_gate_pass"] is True
  assert evaluation["metrics"]["post_closure_failure_count"] == 0
  assert evaluation["metrics"]["preclamp_decomposition_failure_count"] == 0
  assert evaluation["metrics"]["candidate_aggregate_mismatch_count"] == 0
  assert evaluation["metrics"]["flag_closure_failure_count"] == 0


def test_evaluate_rows_reports_distance_and_orientation_residuals() -> None:
  rows = [
    _row(standoff=0.5, effect=0.4, heading=0.0),
    _row(standoff=2.0, effect=0.6, heading=0.0),
    _row(standoff=0.5, effect=0.4, heading=180.0),
  ]
  evaluation = admission.evaluate_rows(rows)
  assert evaluation["diagnostic_trace_gate_pass"] is True
  assert evaluation["metrics"]["distance_monotonic_violation_count"] == 1
  assert evaluation["metrics"]["orientation_sign_collapse_count"] == 1
  assert evaluation["metrics"]["axial_orientation_sign_collapse_count"] == 1


def test_evaluate_rows_rejects_a_broken_model_owned_decomposition() -> None:
  broken = _row()
  broken["event"]["spatial_projection_preclamp_scale"] = 0.61  # type: ignore[index]
  evaluation = admission.evaluate_rows([broken])
  assert evaluation["diagnostic_trace_gate_pass"] is False
  assert evaluation["metrics"]["preclamp_decomposition_failure_count"] == 1


def test_runtime_smoke_exports_model_owned_trace_and_component_rows() -> None:
  report = admission.generate_report(limit=1)
  assert report["diagnostic_trace_gate_pass"] is True
  assert report["admission_decision"]["warhead_spatial_field_admission"] == "held"
  event = report["rows"][0]["event"]
  assert event["spatial_projection_trace_valid"] is True
  assert event["spatial_projection_base_scale"] > 0.0
  assert event["spatial_projection_floor_selected_scale"] >= event[
    "spatial_projection_base_scale"
  ]
  assert event["component_mechanism_load_rows"]
  assert event["component_response_rows"]


def test_directional_fragmentation_profile_retains_signed_orientation_signal() -> None:
  cases = list(admission._case_definitions())
  forward = admission._event_row(cases[0], 20260914)["event"]
  reverse = admission._event_row(cases[4], 20260915)["event"]
  assert forward["fragment_angular_distribution"] == "polar_azimuthal"
  assert forward["fragment_angular_distribution_active"] is True
  assert forward["fragment_angular_density"] > 1.0
  assert forward["fragment_angular_signed_polar_cosine"] > 0.0
  assert reverse["fragment_angular_signed_polar_cosine"] < 0.0
  assert forward["spatial_projection_effect_scale"] != reverse[
    "spatial_projection_effect_scale"
  ]


def test_near_field_floor_switch_is_visible_in_the_runtime_trace() -> None:
  cases = list(admission._case_definitions())
  enabled = admission._event_row(cases[0], 20260918, near_field_floor_enabled=True)["event"]
  disabled = admission._event_row(cases[0], 20260919, near_field_floor_enabled=False)["event"]
  assert enabled["spatial_projection_near_field_floor_applied"] is True
  assert disabled["spatial_projection_near_field_floor_applied"] is False
  assert enabled["spatial_projection_floor_selected_scale"] > disabled[
    "spatial_projection_floor_selected_scale"
  ]


def test_legacy_fragmentation_profile_remains_scalar_and_sign_folded() -> None:
  cases = [case for case in admission._case_definitions() if case["warhead_family"] == "blast_fragmentation"]
  forward = admission._event_row(cases[0], 20260916, directional_fragmentation=False)["event"]
  reverse = admission._event_row(cases[4], 20260917, directional_fragmentation=False)["event"]
  assert forward["fragment_angular_distribution"] == "legacy_scalar"
  assert forward["fragment_angular_distribution_active"] is False
  assert forward["spatial_projection_effect_scale"] == reverse["spatial_projection_effect_scale"]


def test_explicit_continuous_rod_ring_band_rejects_axial_and_hits_equatorial_geometry() -> None:
  cases = [
    case
    for case in admission._case_definitions()
    if case["warhead_family"] == "continuous_rod"
    and case["direction"] == "front"
    and case["standoff_m"] == 0.5
  ]
  axial_case = next(case for case in cases if case["detonation_attitude_deg"][0] == 0.0)
  equatorial_case = next(
    case for case in cases if case["detonation_attitude_deg"][0] == 90.0
  )
  opposite_case = next(
    case for case in cases if case["detonation_attitude_deg"][0] == 270.0
  )
  axial = admission._event_row(
    axial_case, 20260920, explicit_continuous_rod=True
  )["event"]
  equatorial = admission._event_row(
    equatorial_case, 20260921, explicit_continuous_rod=True
  )["event"]
  opposite = admission._event_row(
    opposite_case, 20260922, explicit_continuous_rod=True
  )["event"]

  assert axial["continuous_rod_ring_band_active"] is True
  assert axial["continuous_rod_spatial_model"] == "expanding_ring_band"
  assert axial["continuous_rod_ring_band_intersection"] is False
  assert axial["spatial_projection_trace_valid"] is False
  assert axial["spatial_projection_effect_scale"] == 0.0

  assert equatorial["continuous_rod_ring_band_intersection"] is True
  assert equatorial["spatial_projection_trace_valid"] is True
  assert equatorial["continuous_rod_azimuthal_sample_count"] == 720
  assert equatorial["continuous_rod_intersecting_azimuthal_sample_count"] > 0
  assert equatorial["continuous_rod_angular_coverage_fraction"] > 0.0
  assert equatorial["spatial_projection_axis_weight"] == 1.0
  assert equatorial["spatial_projection_orientation_weight"] == 1.0
  assert equatorial["spatial_projection_effect_scale"] > 0.0
  assert equatorial["continuous_rod_angular_coverage_fraction"] == opposite[
    "continuous_rod_angular_coverage_fraction"
  ]
  assert equatorial["spatial_projection_effect_scale"] == opposite[
    "spatial_projection_effect_scale"
  ]


def test_legacy_continuous_rod_profile_does_not_activate_ring_band() -> None:
  case = next(
    case
    for case in admission._case_definitions()
    if case["warhead_family"] == "continuous_rod"
  )
  event = admission._event_row(case, 20260923, explicit_continuous_rod=False)["event"]
  assert event["continuous_rod_ring_band_active"] is False
  assert event["continuous_rod_spatial_model"] == "legacy_side_sweep"


def test_projection_curve_floor_can_be_fixed_while_final_bound_is_ablated() -> None:
  case = next(
    case
    for case in admission._case_definitions()
    if case["warhead_family"] == "continuous_rod"
    and case["direction"] == "front"
    and case["standoff_m"] == 0.5
    and case["detonation_attitude_deg"][0] == 90.0
  )
  coupled = admission._event_row(
    case,
    20260924,
    explicit_continuous_rod=True,
    projection_min_effect_scale=0.0,
  )["event"]
  decoupled = admission._event_row(
    case,
    20260924,
    explicit_continuous_rod=True,
    projection_min_effect_scale=0.0,
    projection_curve_floor_effect_scale=0.05,
  )["event"]
  assert coupled["spatial_projection_curve_floor_scale"] == 0.0
  assert decoupled["spatial_projection_curve_floor_scale"] == 0.05
  assert decoupled["spatial_projection_base_scale"] > coupled[
    "spatial_projection_base_scale"
  ]
  assert decoupled["spatial_projection_effect_scale"] > coupled[
    "spatial_projection_effect_scale"
  ]


def test_projection_trace_tie_break_is_stable_when_final_bound_changes() -> None:
  case = next(
    case
    for case in admission._case_definitions()
    if case["warhead_family"] == "continuous_rod"
    and case["direction"] == "up"
    and case["standoff_m"] == 10.0
    and case["detonation_attitude_deg"][0] == 0.0
  )
  baseline = admission._event_row(
    case,
    20260925,
    explicit_continuous_rod=True,
    projection_min_effect_scale=0.05,
    projection_curve_floor_effect_scale=0.05,
  )["event"]
  ablated = admission._event_row(
    case,
    20260925,
    explicit_continuous_rod=True,
    projection_min_effect_scale=0.0,
    projection_curve_floor_effect_scale=0.05,
  )["event"]
  assert baseline["component_primary_name"] == ablated["component_primary_name"]
  assert baseline["continuous_rod_angular_coverage_fraction"] == ablated[
    "continuous_rod_angular_coverage_fraction"
  ]
