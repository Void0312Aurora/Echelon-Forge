from __future__ import annotations

from tools.diagnostics import kill_chain_decoupling_probe as probe
from tools.diagnostics import kill_chain_p11_terminal_track_sensitivity as sensitivity


def _run(
  case_id: str,
  timeout: float,
  state: str,
  seed: int,
  *,
  fuze_triggered: bool = False,
) -> dict:
  return {
    "case_id": case_id,
    "range_m": 6000.0,
    "bearing_deg": -60.0 if case_id.endswith("m60deg") else 60.0,
    "target_acceleration_x_mps2": -8.0 if case_id.endswith("m60deg") else 8.0,
    "seed": seed,
    "requested_memory_timeout_s": timeout,
    "resolved_memory_timeout_s": timeout,
    "state": state,
    "nearest_miss_distance_m": 13.3 if state != "outside_no_load" else 20.0,
    "fuze_triggered": fuze_triggered,
    "fuze_reason": "fuze_armed" if fuze_triggered else "fuze_no_terminal_track",
    "first_detection_outside_fov_time_s": 9.1,
    "first_memory_time_s": 9.1167,
    "first_ballistic_time_s": 9.85 if state != "complete_effect_chain" else None,
    "memory_to_ballistic_s": 0.7333 if state != "complete_effect_chain" else None,
    "max_detection_fov_excess_deg": 85.0,
    "max_seeker_fov_excess_deg": 0.3,
    "last_runtime_seeker_mode_name": "ballistic" if state != "complete_effect_chain" else "track",
  }


def test_state_classification_prioritizes_fuze_then_radius() -> None:
  assert sensitivity._state_for_run({"fuze_triggered": True, "nearest_miss_distance_m": 1.0}) == (
    "complete_effect_chain"
  )
  assert sensitivity._state_for_run({"fuze_triggered": False, "nearest_miss_distance_m": 14.9}) == (
    "in_radius_fuze_blocked"
  )
  assert sensitivity._state_for_run({"fuze_triggered": False, "nearest_miss_distance_m": 15.1}) == (
    "outside_no_load"
  )


def test_timeout_monotonicity_rejects_block_to_miss_reversal() -> None:
  cells = [
    {"case_id": "case", "requested_memory_timeout_s": 0.75, "state": "in_radius_fuze_blocked"},
    {"case_id": "case", "requested_memory_timeout_s": 1.5, "state": "complete_effect_chain"},
    {"case_id": "case", "requested_memory_timeout_s": 3.0, "state": "outside_no_load"},
  ]
  assert sensitivity._monotonic_timeout_cells(cells) is False


def _synthetic_report() -> dict:
  case_ids = [case["case_id"] for case in sensitivity.DEFAULT_CASES]
  runs = []
  for seed in (1, 2):
    for case_id in case_ids:
      runs.append(_run(case_id, 0.75, "in_radius_fuze_blocked", seed))
      runs.append(_run(case_id, 1.5, "complete_effect_chain", seed, fuze_triggered=True))
  return sensitivity.build_report(
    runs,
    seeds=(1, 2),
    memory_timeouts_s=(0.75, 1.5),
    source_report=sensitivity.DEFAULT_SOURCE_REPORT,
  )


def test_build_report_keeps_default_residual_and_reports_transition() -> None:
  report = _synthetic_report()
  assert report["status"] == "p11_terminal_track_memory_sensitivity_explained"
  assert report["evaluation"]["residual_explanation_ready"] is True
  assert report["evaluation"]["default_timeout_change_authorized"] is False
  assert report["counts"]["in_radius_fuze_blocked_run_count"] == 4
  assert report["counts"]["complete_effect_chain_run_count"] == 4


def test_renderer_writes_human_readable_png(tmp_path) -> None:
  from tools.diagnostics.render_kill_chain_p11_terminal_track_sensitivity import render

  output = tmp_path / "sensitivity.png"
  render(_synthetic_report(), output)
  assert output.stat().st_size > 1000


def test_track_break_timeout_is_an_explicit_probe_override() -> None:
  class Tuning:
    track_break_time_s = 0.75

  tuning = Tuning()
  applied = probe._apply_guidance_tuning_overrides(
    tuning,
    {"track_break_time_s": 1.5},
  )
  assert applied == {"track_break_time_s": 1.5}
  assert tuning.track_break_time_s == 1.5
