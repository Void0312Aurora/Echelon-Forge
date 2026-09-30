from __future__ import annotations

from tools.geometry import continuous_rod_component_load_admission as admission
from tools.geometry import warhead_spatial_structural_admission as common


def _clamp_case() -> dict[str, object]:
  return next(
    case
    for case in common._case_definitions()
    if case["warhead_family"] == "continuous_rod"
    and case["direction"] == "front"
    and case["standoff_m"] == 10.0
    and case["detonation_attitude_deg"][0] == 90.0
  )


def test_component_load_admission_closes_load_response_and_primary_trace() -> None:
  cases = [_clamp_case()]
  baseline = admission._run_rows(
    cases, seed=20260914, minimum_effect_scale=admission.BASELINE_MIN_EFFECT_SCALE
  )
  variant = admission._run_rows(
    cases, seed=20260914, minimum_effect_scale=admission.DECOUPLED_MIN_EFFECT_SCALE
  )
  baseline_validation = admission._variant_validation(baseline)
  variant_validation = admission._variant_validation(variant)
  paired = admission._pair_validation(baseline, variant)

  assert baseline_validation["metrics"]["load_response_identity_residual_count"] == 0
  assert variant_validation["metrics"]["primary_trace_residual_count"] == 0
  assert paired["metrics"]["changed_load_effect_count"] > 0
  assert paired["metrics"]["changed_dependency_availability_count"] > 0
  assert not paired["residuals"]["load_topology"]
  assert not paired["residuals"]["response_topology"]
  assert not paired["residuals"]["dependency_topology"]
  assert not paired["residuals"]["projection_propagation"]


def test_component_load_admission_rejects_a_response_source_index_drift() -> None:
  row = admission._run_rows(
    [_clamp_case()], seed=20260914, minimum_effect_scale=admission.BASELINE_MIN_EFFECT_SCALE
  )[0]
  response = row["event"]["component_response_rows"][0]
  response["source_row_index"] += 1
  validation = admission._variant_validation([row])
  assert validation["metrics"]["load_response_identity_residual_count"] > 0
