from __future__ import annotations

import json

from tools.diagnostics import kill_chain_expectation_stage_attribution as attribution


def _row(
  *,
  case_id: str,
  range_km: float,
  signed_bearing_deg: float,
  launch_class: str,
  guidance_status: str,
  entered_r_fuze: bool,
  detonated: bool,
  effect_band: str,
  max_failure_probability: float,
  sampled_failure_count: int,
  component_response_band: str,
) -> dict[str, object]:
  return {
    "identity": {"case_id": case_id},
    "launch_window": {
      "target_motion_layer": "nonmaneuvering_constant_velocity",
      "range_km": range_km,
      "signed_bearing_deg": signed_bearing_deg,
      "launch_class": launch_class,
    },
    "run_status": "generated",
    "guidance_approach": {
      "guidance_expectation_status": guidance_status,
      "entered_R_fuze": entered_r_fuze,
      "rho_fuze": 0.75 if entered_r_fuze else 1.25,
    },
    "fuze_decision": {"detonated": detonated},
    "warhead_load_field": {
      "R_effect_variant": "REV-RUNTIME-PROJECTION",
      "effect_band": effect_band,
      "rho_effect_case": 0.75,
      "strongest_component_effect_scale": 0.5,
    },
    "component_response": {
      "max_failure_probability": max_failure_probability,
      "sampled_failure_count": sampled_failure_count,
      "component_response_band": component_response_band,
    },
    "guards": {"authority_boundary_status": "engineering_proxy_guarded"},
  }


def test_stage_attribution_writes_review_artifacts(tmp_path) -> None:
  report = {
    "schema_version": "a2.kill_chain_expectation_before_report.v1",
    "heatmap_rows": [
      _row(
        case_id="n_guidance",
        range_km=4.0,
        signed_bearing_deg=-45.0,
        launch_class="N",
        guidance_status="guidance_or_model_residual",
        entered_r_fuze=False,
        detonated=False,
        effect_band="outside_effect",
        max_failure_probability=0.0,
        sampled_failure_count=0,
        component_response_band="no_response_rows",
      ),
      _row(
        case_id="n_response",
        range_km=4.0,
        signed_bearing_deg=30.0,
        launch_class="N",
        guidance_status="satisfied",
        entered_r_fuze=True,
        detonated=True,
        effect_band="outer_effective",
        max_failure_probability=0.006,
        sampled_failure_count=0,
        component_response_band="observed_probability_only",
      ),
      _row(
        case_id="n_ok",
        range_km=4.0,
        signed_bearing_deg=0.0,
        launch_class="N",
        guidance_status="satisfied",
        entered_r_fuze=True,
        detonated=True,
        effect_band="core",
        max_failure_probability=0.8,
        sampled_failure_count=2,
        component_response_band="sampled_failure_observed",
      ),
      _row(
        case_id="o_ok",
        range_km=6.0,
        signed_bearing_deg=90.0,
        launch_class="O",
        guidance_status="negative_control_satisfied",
        entered_r_fuze=False,
        detonated=False,
        effect_band="outside_effect",
        max_failure_probability=0.0,
        sampled_failure_count=0,
        component_response_band="no_response_rows",
      ),
    ],
  }
  input_path = tmp_path / "before.json"
  input_path.write_text(json.dumps(report), encoding="utf-8")

  manifest = attribution.generate_stage_attribution(
    input_path=input_path,
    output_dir=tmp_path / "out",
    prefix="sample",
    date_stamp="20260623",
  )

  assert manifest["schema_version"] == attribution.SCHEMA_VERSION
  assert manifest["stage_counts"] == {
    "component_response": 1,
    "guidance_approach": 1,
    "negative_control_satisfied": 1,
    "no_review_pressure": 1,
  }
  rows_by_id = {row["case_id"]: row for row in manifest["rows"]}
  assert rows_by_id["n_guidance"]["first_review_stage"] == "guidance_approach"
  assert rows_by_id["n_response"]["first_review_stage"] == "component_response"
  assert rows_by_id["n_ok"]["first_review_stage"] == "no_review_pressure"

  assert (tmp_path / "out" / "sample_first_review_stage_manifest_20260623.json").exists()
  assert (tmp_path / "out" / "sample_first_review_stage_matrix_20260623.csv").exists()
  assert (tmp_path / "out" / "sample_first_review_stage_detail_20260623.csv").exists()
  assert open(manifest["stage_heatmap_png"], "rb").read(8).startswith(b"\x89PNG")
  assert "<svg" in open(manifest["stage_heatmap_svg"], encoding="utf-8").read()
  assert "engineering-proxy diagnostics only" in (
    tmp_path / "out" / "sample_first_review_stage_summary_20260623.md"
  ).read_text(encoding="utf-8")
