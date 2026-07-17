from __future__ import annotations

import json

from tools.diagnostics.kces import envelope_audit


def _row(
  *,
  case_id: str,
  range_km: float = 4.0,
  signed_bearing_deg: float = 0.0,
  launch_class: str = "N",
  entered_r_fuze: bool = True,
  r_fuze_m: float | None = 18.0,
  r_effect_m: float | None = 12.0,
  variant: str = "REV-RUNTIME-PROJECTION",
  effect_band: str = "outer_effective",
  component_response_row_count: int = 4,
  max_failure_probability: float | None = 0.006,
  min_integrity_delta: float | None = -0.004,
  sampled_failure_count: int = 0,
) -> dict[str, object]:
  return {
    "identity": {
      "profile_id": "aim120_anchor",
      "case_id": case_id,
      "grid_tier": "anchor",
    },
    "launch_window": {
      "target_motion_layer": "nonmaneuvering_constant_velocity",
      "range_km": range_km,
      "signed_bearing_deg": signed_bearing_deg,
      "launch_class": launch_class,
    },
    "guidance_approach": {
      "guidance_expectation_status": "satisfied",
      "entered_R_fuze": entered_r_fuze,
      "R_fuze_m": r_fuze_m,
      "rho_fuze": 0.8 if entered_r_fuze else 1.2,
    },
    "fuze_decision": {"detonated": entered_r_fuze},
    "warhead_load_field": {
      "R_effect_variant": variant,
      "R_effect_m": r_effect_m,
      "R_effect_source": "missile_runtime_projection.resolved_projection_radius_m",
      "effect_band": effect_band,
      "rho_effect_case": 0.7,
    },
    "component_response": {
      "component_response_row_count": component_response_row_count,
      "max_failure_probability": max_failure_probability,
      "min_integrity_delta": min_integrity_delta,
      "sampled_failure_count": sampled_failure_count,
    },
  }


def test_outer_effective_trace_response_is_below_outer_floor() -> None:
  row = envelope_audit.audit_row(
    _row(case_id="outer_trace", effect_band="outer_effective")
  )

  assert row["component_response_quantized_band"] == "trace_response"
  assert row["component_response_expectation_status"] == "below_outer_effective_floor"
  assert row["envelope_cell_status"] == "below_outer_effective_floor"
  assert row["envelope_owner_stage"] == "warhead_load_field -> component_response"


def test_outside_effect_nontrivial_response_creates_negative_control_pressure() -> None:
  row = envelope_audit.audit_row(
    _row(
      case_id="outside_nontrivial",
      launch_class="O",
      effect_band="outside_effect",
      max_failure_probability=0.12,
      min_integrity_delta=-0.02,
    )
  )

  assert row["component_response_quantized_band"] == "nontrivial_response"
  assert row["component_response_expectation_status"] == "negative_control_pressure"
  assert row["envelope_cell_status"] == "negative_control_pressure"
  assert row["envelope_owner_stage"] == "launch_window -> warhead_load_field"


def test_nominal_launch_that_misses_r_fuze_is_guidance_or_model_residual() -> None:
  row = envelope_audit.audit_row(
    _row(
      case_id="missed_fuze",
      launch_class="N",
      entered_r_fuze=False,
      effect_band="effective",
      max_failure_probability=0.18,
      min_integrity_delta=-0.08,
    )
  )

  assert row["envelope_cell_status"] == "guidance_or_model_residual"
  assert row["envelope_owner_stage"] == "launch_window -> guidance_approach"


def test_nominal_guidance_residual_is_not_masked_by_missing_effect_metadata() -> None:
  row = envelope_audit.audit_row(
    _row(
      case_id="missed_fuze_missing_effect",
      launch_class="N",
      entered_r_fuze=False,
      r_effect_m=None,
      effect_band="unclassified_missing_R_effect",
    )
  )

  assert row["envelope_cell_status"] == "guidance_or_model_residual"
  assert row["envelope_owner_stage"] == "launch_window -> guidance_approach"


def test_marginal_cell_is_not_masked_by_missing_effect_metadata() -> None:
  row = envelope_audit.audit_row(
    _row(
      case_id="marginal_missing_effect",
      launch_class="M",
      r_effect_m=None,
      effect_band="unclassified_missing_R_effect",
    )
  )

  assert row["envelope_cell_status"] == "boundary_observation"
  assert row["envelope_owner_stage"] == "launch_window"


def test_quiet_outside_cell_is_not_masked_by_missing_effect_metadata() -> None:
  row = envelope_audit.audit_row(
    _row(
      case_id="outside_missing_effect",
      launch_class="O",
      entered_r_fuze=False,
      r_effect_m=None,
      effect_band="unclassified_missing_R_effect",
      component_response_row_count=0,
      max_failure_probability=None,
      min_integrity_delta=None,
    )
  )

  assert row["envelope_cell_status"] == "satisfied"
  assert row["envelope_owner_stage"] == "negative_control_satisfied"


def test_strong_outside_cell_is_not_masked_by_missing_effect_metadata() -> None:
  row = envelope_audit.audit_row(
    _row(
      case_id="outside_pressure_missing_effect",
      launch_class="O",
      r_effect_m=None,
      effect_band="unclassified_missing_R_effect",
      max_failure_probability=0.12,
      min_integrity_delta=-0.02,
    )
  )

  assert row["envelope_cell_status"] == "negative_control_pressure"
  assert row["envelope_owner_stage"] == "launch_window -> warhead_load_field"


def test_missing_effect_metadata_is_not_judged() -> None:
  row = envelope_audit.audit_row(
    _row(
      case_id="missing_effect",
      r_effect_m=None,
      effect_band="unclassified_missing_R_effect",
    )
  )

  assert row["envelope_cell_status"] == "not_judged_missing_metadata"
  assert row["envelope_owner_stage"] == "harness_metadata"


def test_generate_envelope_audit_writes_review_artifacts(tmp_path) -> None:
  report = {
    "schema_version": "a2.kill_chain_expectation_before_report.v1",
    "heatmap_rows": [
      _row(
        case_id="outer_trace",
        range_km=4.0,
        signed_bearing_deg=0.0,
        effect_band="outer_effective",
      ),
      _row(
        case_id="core_material",
        range_km=4.0,
        signed_bearing_deg=30.0,
        effect_band="core",
        max_failure_probability=0.42,
        min_integrity_delta=-0.18,
        sampled_failure_count=1,
      ),
      _row(
        case_id="outside_nontrivial",
        range_km=6.0,
        signed_bearing_deg=0.0,
        launch_class="O",
        effect_band="outside_effect",
        max_failure_probability=0.12,
        min_integrity_delta=-0.02,
      ),
    ],
  }
  input_path = tmp_path / "before.json"
  input_path.write_text(json.dumps(report), encoding="utf-8")

  manifest = envelope_audit.generate_envelope_audit(
    input_path=input_path,
    output_dir=tmp_path / "out",
    prefix="sample",
    date_stamp="20260706",
  )

  assert manifest["schema_version"] == envelope_audit.SCHEMA_VERSION
  assert manifest["envelope_schema_version"] == envelope_audit.ENVELOPE_SCHEMA_VERSION
  assert manifest["selected_row_count"] == 3
  assert manifest["rows"][0]["R_effect_source"] == (
    "missile_runtime_projection.resolved_projection_radius_m"
  )
  assert manifest["envelope_cell_status_counts"] == {
    "below_outer_effective_floor": 1,
    "negative_control_pressure": 1,
    "satisfied": 1,
  }
  assert (tmp_path / "out" / "sample_expectation_envelope_manifest_20260706.json").exists()
  assert (tmp_path / "out" / "sample_expectation_envelope_detail_20260706.csv").exists()
  assert (tmp_path / "out" / "sample_expectation_envelope_matrix_20260706.csv").exists()
  summary = (
    tmp_path / "out" / "sample_expectation_envelope_summary_20260706.md"
  ).read_text(encoding="utf-8")
  assert "standards-layer air-to-air kill-chain expectation" in summary
  assert "engineering-proxy diagnostics only" in summary
