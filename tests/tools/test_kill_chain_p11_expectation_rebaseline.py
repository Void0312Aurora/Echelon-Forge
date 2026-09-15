from __future__ import annotations

from tools.diagnostics import kill_chain_p11_expectation_rebaseline as rebaseline


def _cell(case_id: str, old: str, state: str, *, blocked: bool = False) -> dict:
  return {
    "case_id": case_id,
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
  return {
    "status": "integrated_structure_passed_residuals_open",
    "matrix": {"case_count_per_seed": len(cells)},
    "evaluation": {"p11_structural_admission_passed": True},
    "cells": cells,
  }


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


def test_build_report_is_candidate_only_and_keeps_p11_incomplete() -> None:
  cells = [
    {**_cell("retain_n", "N", "complete_effect_chain"), "bearing_deg": 30.0},
    {**_cell("promote_n", "O", "complete_effect_chain"), "bearing_deg": 45.0},
    {
      **_cell("hold_m", "O", "in_radius_fuze_blocked", blocked=True),
      "bearing_deg": 55.0,
    },
    {**_cell("retain_o", "O", "outside_no_load"), "bearing_deg": 60.0},
  ]
  report = rebaseline.build_report(_report(cells), input_path=rebaseline.DEFAULT_INPUT)
  assert report["evaluation"]["candidate_ready_for_manual_review"] is True
  assert report["evaluation"]["legacy_expectation_harness_unchanged"] is True
  assert report["evaluation"]["p11_complete"] is False
  assert report["old_to_candidate_transition_counts"]["O->N"] == 1
