from __future__ import annotations

from pathlib import Path

from tools.diagnostics import kill_chain_p11_expectation_rebaseline as rebaseline


def _cell(case_id: str, old: str, state: str, *, blocked: bool = False) -> dict:
  return {
    "case_id": case_id,
    "expectation_baseline_id": "P11-REBASELINE-20260915-ACCEPTED-WITH-RESIDUALS",
    "target_motion_layer": "nonmaneuvering_constant_velocity",
    "target_acceleration_x_mps2": 0.0,
    "range_km": 8.0,
    "bearing_deg": 30.0,
    "launch_class": old,
    "chain_states": [state],
    "seed_count": 3,
    "structural_consistent": True,
    "nearest_distance_min_m": 1.0 if state == "complete_effect_chain" else 20.0,
    "nearest_distance_max_m": 1.0 if state == "complete_effect_chain" else 20.0,
    "legacy_negative_control_alert": old == "O" and state != "outside_no_load",
    "in_radius_fuze_blocked": blocked,
    "terminal_track_residual_causes": (
      ["seeker_fov_exit_then_memory_timeout"] if blocked else []
    ),
  }


def _report(cells: list[dict]) -> dict:
  runs = [
    {"case_id": cell["case_id"], "seed": seed}
    for cell in cells
    for seed in rebaseline.EXPECTED_SEEDS
  ]
  return {
    "status": "integrated_structure_passed_residuals_open",
    "expectation_baseline": {
      "id": "P11-REBASELINE-20260915-ACCEPTED-WITH-RESIDUALS"
    },
    "matrix": {
      "case_count_per_seed": len(cells),
      "expected_run_count": len(runs),
      "seeds": list(rebaseline.EXPECTED_SEEDS),
    },
    "evaluation": {"p11_structural_admission_passed": True},
    "cells": cells,
    "runs": runs,
  }


def _input_path(tmp_path: Path) -> Path:
  path = tmp_path / "integrated.json"
  path.write_text("{}\n", encoding="utf-8")
  return path


def test_candidate_class_maps_observed_chain_state_without_mutating_old_label() -> None:
  rows = rebaseline._cell_rows(
    _report([_cell("old_o_hit", "O", "complete_effect_chain")])
  )
  assert rows[0]["old_launch_class"] == "O"
  assert rows[0]["candidate_launch_class"] == "N"
  assert rows[0]["transition"] == "promote_to_N"


def test_terminal_track_block_is_retained_as_candidate_m() -> None:
  rows = rebaseline._cell_rows(
    _report(
      [_cell("old_o_blocked", "O", "in_radius_fuze_blocked", blocked=True)]
    )
  )
  assert rows[0]["candidate_launch_class"] == "M"
  assert rows[0]["transition"] == "hold_M_terminal_track_residual"


def test_angle_topology_detects_miss_to_hit_reversal() -> None:
  rows = rebaseline._cell_rows(
    _report(
      [
        {**_cell("low", "O", "outside_no_load"), "bearing_deg": 30.0},
        {**_cell("high", "N", "complete_effect_chain"), "bearing_deg": 60.0},
      ]
    )
  )
  topology = rebaseline._angle_topology(rows)
  assert topology["monotonic_angle_topology"] is False
  assert topology["violation_count"] == 1


def test_range_topology_requires_explicit_near_range_entry_exception() -> None:
  rows = rebaseline._cell_rows(
    _report(
      [
        {**_cell("near_miss", "O", "outside_no_load"), "range_km": 4.0},
        {**_cell("far_hit", "N", "complete_effect_chain"), "range_km": 6.0},
      ]
    )
  )
  topology = rebaseline._range_topology(rows)
  assert topology["continuous_range_topology"] is False
  assert topology["range_violation_count"] == 1

  rows[1]["range_topology_exception"] = "near_range_entry"
  excepted = rebaseline._range_topology(rows)
  assert excepted["continuous_range_topology"] is False
  assert excepted["range_exception_count"] == 0


def test_range_topology_accepts_only_four_approved_near_range_transitions() -> None:
  cells = []
  for bearing in (-60.0, 60.0):
    cells.extend(
      [
        {
          **_cell(f"cv_near_{bearing:g}", "O", "outside_no_load"),
          "range_km": 4.0,
          "bearing_deg": bearing,
        },
        {
          **_cell(f"cv_entry_{bearing:g}", "N", "complete_effect_chain"),
          "range_km": 6.0,
          "bearing_deg": bearing,
          "range_topology_exception": "near_range_entry",
        },
        {
          **_cell(f"mild_near_{bearing:g}", "M", "in_radius_fuze_blocked", blocked=True),
          "target_motion_layer": "mild_maneuver",
          "range_km": 6.0,
          "bearing_deg": bearing,
        },
        {
          **_cell(f"mild_entry_{bearing:g}", "N", "complete_effect_chain"),
          "target_motion_layer": "mild_maneuver",
          "range_km": 8.0,
          "bearing_deg": bearing,
          "range_topology_exception": "near_range_entry",
        },
      ]
    )

  topology = rebaseline._range_topology(rebaseline._cell_rows(_report(cells)))
  assert topology["continuous_range_topology"] is True
  assert topology["range_exception_count"] == 4


def test_range_topology_rejects_exception_token_on_12_to_16km_reversal() -> None:
  rows = rebaseline._cell_rows(
    _report(
      [
        {
          **_cell("unapproved_12km", "O", "outside_no_load"),
          "range_km": 12.0,
          "bearing_deg": 60.0,
        },
        {
          **_cell("unapproved_16km", "N", "complete_effect_chain"),
          "range_km": 16.0,
          "bearing_deg": 60.0,
          "range_topology_exception": "near_range_entry",
        },
      ]
    )
  )

  topology = rebaseline._range_topology(rows)
  assert topology["continuous_range_topology"] is False
  assert topology["range_violation_count"] == 1


def test_build_report_is_candidate_only_and_keeps_p11_incomplete(tmp_path) -> None:
  cells = [
    {**_cell("retain_n", "N", "complete_effect_chain"), "bearing_deg": 30.0},
    {**_cell("promote_n", "O", "complete_effect_chain"), "bearing_deg": 45.0},
    {
      **_cell("hold_m", "O", "in_radius_fuze_blocked", blocked=True),
      "bearing_deg": 55.0,
    },
    {**_cell("retain_o", "O", "outside_no_load"), "bearing_deg": 60.0},
  ]
  report = rebaseline.build_report(_report(cells), input_path=_input_path(tmp_path))
  assert report["evaluation"]["candidate_ready_for_manual_review"] is True
  assert report["evaluation"]["legacy_expectation_harness_unchanged"] is True
  assert report["evaluation"]["p11_complete"] is False
  assert report["old_to_candidate_transition_counts"]["O->N"] == 1


def test_source_matrix_gate_rejects_duplicate_case_seed_pair(tmp_path) -> None:
  source = _report([_cell("a", "N", "complete_effect_chain")])
  source["runs"][-1] = dict(source["runs"][0])
  report = rebaseline.build_report(source, input_path=_input_path(tmp_path))
  assert report["source_matrix_audit"]["checks"]["unique_case_seed_pairs"] is False
  assert report["evaluation"]["candidate_ready_for_manual_review"] is False
  assert "不能形成候选重基线" in rebaseline.conclusions_zh(report)


def test_source_matrix_gate_rejects_unknown_cell_baseline(tmp_path) -> None:
  source = _report([_cell("a", "N", "complete_effect_chain")])
  source["cells"][0]["expectation_baseline_id"] = "UNKNOWN-BASELINE"

  report = rebaseline.build_report(source, input_path=_input_path(tmp_path))

  assert report["source_matrix_audit"]["checks"][
    "accepted_expectation_baseline"
  ] is False
  assert report["evaluation"]["candidate_ready_for_manual_review"] is False


def test_terminal_residual_gate_requires_nonempty_cause(tmp_path) -> None:
  cell = _cell("blocked", "O", "in_radius_fuze_blocked", blocked=True)
  cell["terminal_track_residual_causes"] = []
  report = rebaseline.build_report(
    _report([cell]), input_path=_input_path(tmp_path)
  )
  assert report["evaluation"]["gates"][
    "terminal_track_residuals_remain_explicit"
  ] is False
