from __future__ import annotations

from copy import deepcopy

from tools.geometry import continuous_rod_ring_band_admission as admission


def _row(case_id: str, *, hit: bool, coverage: float, effect: float) -> dict[str, object]:
  return {
    "case_id": case_id,
    "event": {
      "continuous_rod_ring_band_intersection": hit,
      "continuous_rod_angular_coverage_fraction": coverage,
      "spatial_projection_effect_scale": effect,
    },
  }


def test_sampling_comparison_accepts_bounded_numeric_drift() -> None:
  baseline = [_row("case-a", hit=True, coverage=0.125, effect=0.4)]
  variant = [_row("case-a", hit=True, coverage=0.128, effect=0.405)]
  result = admission._compare_sampling_variant(
    baseline,
    variant,
    label="bounded",
    configuration={"azimuthal_samples": 288},
  )
  assert result["status"] == "passed"
  assert result["classification_difference_count"] == 0


def test_sampling_comparison_rejects_topology_change() -> None:
  baseline = [_row("case-a", hit=True, coverage=0.01, effect=0.05)]
  variant = deepcopy(baseline)
  variant[0]["event"]["continuous_rod_ring_band_intersection"] = False  # type: ignore[index]
  result = admission._compare_sampling_variant(
    baseline,
    variant,
    label="topology-change",
    configuration={"phase_deg": 0.25},
  )
  assert result["status"] == "failed"
  assert result["classification_difference_count"] == 1


def test_limited_runtime_probe_exports_explicit_model_without_overclaiming_admission() -> None:
  report = admission.generate_report(limit=1)
  assert report["admission_decision"][
    "continuous_rod_expanding_ring_band_admission"
  ] == "held"
  assert report["admission_decision"]["default_profile_promotion"] == "not_evaluated"
  event = report["rows"][0]["event"]
  assert event["continuous_rod_ring_band_active"] is True
  assert event["continuous_rod_spatial_model"] == "expanding_ring_band"
  assert event["continuous_rod_azimuthal_sample_count"] == 720


def test_projection_floor_ablation_requires_the_complete_matrix() -> None:
  from tools.geometry import continuous_rod_projection_floor_ablation as floor_ablation

  report = floor_ablation.generate_report(limit=1)
  assert report["admission_decision"]["complete_matrix"] == "not_evaluated"
  assert report["admission_decision"]["p7_projection_floor_clamp_admission"] == "held"
