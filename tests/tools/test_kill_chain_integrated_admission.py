from __future__ import annotations

from tools.diagnostics import kill_chain_integrated_admission as admission
from tools.diagnostics.render_kill_chain_integrated_admission import _state_value


def _stage(name: str, *, present: bool = True, observed: dict | None = None) -> dict:
  return {
    "abstraction_stage": name,
    "owner": admission.EXPECTED_STAGE_OWNERS[name],
    "present": int(present),
    "observed": dict(observed or {}),
  }


def _fixture(*, triggered: bool) -> tuple[dict, dict, dict]:
  grid = {
    "case_id": "fixture",
    "target_motion_layer": "mild_maneuver",
    "target_motion_profile_id": "constant_lateral_acceleration_8mps2_v0",
    "maneuver_severity": "mild_engineering_proxy",
    "target_acceleration_mps2": [8.0, 0.0, 0.0],
    "range_km": 8.0,
    "signed_bearing_deg": 30.0,
    "launch_class": "M",
  }
  heatmap = {
    "guidance_approach": {"nearest_distance_m": 1.0 if triggered else 20.0,
                          "entered_R_fuze": triggered},
    "fuze_decision": {"fuze_triggered": triggered, "detonated": triggered,
                      "fuze_reason": "fuze_armed" if triggered else "miss"},
    "warhead_load_field": {"component_load_row_count": 2 if triggered else 0},
    "component_response": {"component_response_row_count": 2 if triggered else 0},
    "consequence_projection": {"outcome_state": "damage_applied" if triggered else ""},
    "guards": {"authority_boundary_status": "engineering_proxy_guarded"},
  }
  downstream = triggered
  stages = [
    _stage("approach"),
    _stage("fuze_decision"),
    _stage("warhead_load_field", present=downstream),
    _stage("component_response", present=downstream),
    _stage("consequence_projection", present=downstream),
  ]
  probe_case = {
    "stage_abstractions": stages,
    "resolved_guidance_runtime": dict(admission.EXPECTED_GUIDANCE_RUNTIME),
    "guidance_tuning_overrides": {},
    "effect": {"effect_family": "blast_fragmentation"} if triggered else {},
    "runtime_facade": {"runtime_dto_available": triggered},
    "component_load_factor_summary": {"rows_with_response_fields_on_load_row": 0},
  }
  return grid, heatmap, probe_case


def test_case_evidence_accepts_complete_triggered_chain() -> None:
  grid, heatmap, probe_case = _fixture(triggered=True)
  row = admission._case_evidence(
    seed=20260621,
    grid_case=grid,
    heatmap_row=heatmap,
    probe_case=probe_case,
  )

  assert row["chain_state"] == "complete_effect_chain"
  assert row["structural_consistent"] is True
  assert row["structural_violations"] == []


def test_case_evidence_rejects_untriggered_downstream_load() -> None:
  grid, heatmap, probe_case = _fixture(triggered=False)
  heatmap["warhead_load_field"]["component_load_row_count"] = 1
  row = admission._case_evidence(
    seed=20260621,
    grid_case=grid,
    heatmap_row=heatmap,
    probe_case=probe_case,
  )

  assert row["structural_consistent"] is False
  assert "untriggered_case_has_load_or_response_rows" in row["structural_violations"]


def test_case_evidence_diagnoses_fov_exit_before_terminal_track_loss() -> None:
  grid, heatmap, probe_case = _fixture(triggered=False)
  heatmap["guidance_approach"] = {
    "nearest_distance_m": 13.3,
    "entered_R_fuze": True,
  }
  heatmap["fuze_decision"].update(
    {
      "fuze_reason": "fuze_no_terminal_track",
      "terminal_track_valid": False,
      "target_detected": False,
    }
  )
  probe_case["guidance_runtime_summary"] = {
    "first_detection_outside_fov_time_s": 9.10,
    "first_memory_time_s": 9.12,
    "first_ballistic_time_s": 9.88,
    "track_memory_timeout_s": 0.75,
    "max_detection_fov_excess_deg": 0.30,
    "last_runtime_observation": {
      "seeker_mode": 2,
      "seeker_mode_name": "ballistic",
    },
  }

  row = admission._case_evidence(
    seed=20260621,
    grid_case=grid,
    heatmap_row=heatmap,
    probe_case=probe_case,
  )

  assert row["chain_state"] == "in_radius_fuze_blocked"
  assert row["terminal_track_residual_cause"] == (
    "seeker_fov_exit_then_memory_timeout"
  )
  assert row["last_runtime_seeker_mode_name"] == "ballistic"
  assert abs(row["observed_memory_to_ballistic_s"] - 0.76) < 1.0e-12
  assert row["track_memory_timeout_s"] == 0.75


def test_evaluation_separates_structural_admission_from_legacy_envelope() -> None:
  rows = []
  for seed in admission.DEFAULT_SEEDS:
    rows.append(
        {
          "case_id": "legacy_o_alert",
          "seed": seed,
          "target_motion_layer": "nonmaneuvering_constant_velocity",
          "target_acceleration_x_mps2": 0.0,
          "range_km": 16.0,
          "bearing_deg": 30.0,
          "launch_class": "O",
          "chain_state": "complete_effect_chain",
          "outcome_state": "damage_applied",
        "structural_consistent": True,
        "no_guidance_override": True,
        "resolved_runtime_mismatch": {},
        "stage_ids_exact": True,
        "stage_owners_clean": True,
        "approach_and_fuze_observed": True,
        "response_owner_clean": True,
        "authority_guarded": True,
        "nearest_distance_m": 1.0,
        "nominal_guidance_residual": False,
        "legacy_negative_control_alert": True,
        "in_radius_fuze_blocked": False,
      }
    )
  cells = admission._aggregate_cells(rows)
  evaluation = admission._evaluate(
    rows,
    cells,
    admission.DEFAULT_SEEDS,
    expected_cases_per_seed=1,
  )

  assert evaluation["p11_structural_admission_passed"] is True
  assert evaluation["accepted_n_o_expectation_envelope_passed"] is False
  assert evaluation["legacy_expectation_envelope_passed"] is False
  assert evaluation["p11_complete"] is False


def test_evaluation_accepts_n_o_baseline_but_retains_terminal_contract_hold() -> None:
  rows = []
  for seed in admission.DEFAULT_SEEDS:
    rows.extend(
      [
        {
          "case_id": "accepted_n",
          "seed": seed,
          "launch_class": "N",
          "chain_state": "complete_effect_chain",
          "outcome_state": "damage_applied",
          "structural_consistent": True,
          "no_guidance_override": True,
          "resolved_runtime_mismatch": {},
          "stage_ids_exact": True,
          "stage_owners_clean": True,
          "approach_and_fuze_observed": True,
          "response_owner_clean": True,
          "authority_guarded": True,
          "nearest_distance_m": 1.0,
          "nominal_guidance_residual": False,
          "legacy_negative_control_alert": False,
          "in_radius_fuze_blocked": False,
          "terminal_track_residual_cause": "",
          "target_motion_layer": "nonmaneuvering_constant_velocity",
          "target_acceleration_x_mps2": 0.0,
          "range_km": 8.0,
          "bearing_deg": 0.0,
        },
        {
          "case_id": "accepted_m_residual",
          "seed": seed,
          "launch_class": "M",
          "chain_state": "in_radius_fuze_blocked",
          "outcome_state": "in_radius_fuze_blocked",
          "structural_consistent": True,
          "no_guidance_override": True,
          "resolved_runtime_mismatch": {},
          "stage_ids_exact": True,
          "stage_owners_clean": True,
          "approach_and_fuze_observed": True,
          "response_owner_clean": True,
          "authority_guarded": True,
          "nearest_distance_m": 13.3,
          "nominal_guidance_residual": False,
          "legacy_negative_control_alert": False,
          "in_radius_fuze_blocked": True,
          "terminal_track_residual_cause": "seeker_fov_exit_then_memory_timeout",
          "target_motion_layer": "mild_maneuver",
          "target_acceleration_x_mps2": 8.0,
          "range_km": 6.0,
          "bearing_deg": 60.0,
        },
      ]
    )
  cells = admission._aggregate_cells(rows)
  evaluation = admission._evaluate(
    rows,
    cells,
    admission.DEFAULT_SEEDS,
    expected_cases_per_seed=2,
  )
  assert evaluation["p11_structural_admission_passed"] is True
  assert evaluation["accepted_n_o_expectation_envelope_passed"] is True
  assert evaluation["terminal_track_contract_passed"] is False
  assert evaluation["p11_complete"] is False


def test_structural_matrix_gate_rejects_duplicate_case_seed_pair() -> None:
  rows = []
  for seed in admission.DEFAULT_SEEDS:
    rows.append(
      {
        "case_id": "case",
        "seed": seed,
        "launch_class": "O",
        "chain_state": "outside_no_load",
        "outcome_state": "outside_no_load",
        "structural_consistent": True,
        "no_guidance_override": True,
        "resolved_runtime_mismatch": {},
        "stage_ids_exact": True,
        "stage_owners_clean": True,
        "approach_and_fuze_observed": True,
        "response_owner_clean": True,
        "authority_guarded": True,
        "nearest_distance_m": 20.0,
        "nominal_guidance_residual": False,
        "legacy_negative_control_alert": False,
        "in_radius_fuze_blocked": False,
        "terminal_track_residual_cause": "",
        "target_motion_layer": "nonmaneuvering_constant_velocity",
        "target_acceleration_x_mps2": 0.0,
        "range_km": 8.0,
        "bearing_deg": 90.0,
      }
    )
  rows[-1] = dict(rows[0])
  cells = admission._aggregate_cells(rows)
  evaluation = admission._evaluate(
    rows,
    cells,
    admission.DEFAULT_SEEDS,
    expected_cases_per_seed=1,
  )
  assert evaluation["structural_gates"]["unique_case_seed_pairs"] is False
  assert evaluation["p11_structural_admission_passed"] is False


def test_heatmap_state_values_distinguish_complete_blocked_and_outside() -> None:
  assert _state_value({"chain_states": ["complete_effect_chain"]}) == 2
  assert _state_value({"chain_states": ["in_radius_fuze_blocked"]}) == 1
  assert _state_value({"chain_states": ["outside_no_load"]}) == 0
