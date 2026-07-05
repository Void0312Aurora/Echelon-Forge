from __future__ import annotations

import json

from tools.diagnostics import kill_chain_expectation_response_diagnosis as diagnosis


def _row(
  *,
  case_id: str,
  bearing: float,
  sampled_failure_count: int,
  strongest_load: float,
  max_failure_probability: float,
  component_response_band: str,
) -> dict[str, object]:
  return {
    "identity": {"case_id": case_id},
    "launch_window": {
      "target_motion_layer": "nonmaneuvering_constant_velocity",
      "range_km": 4.0,
      "signed_bearing_deg": bearing,
      "launch_class": "N",
    },
    "guidance_approach": {
      "guidance_expectation_status": "satisfied",
      "entered_R_fuze": True,
      "rho_fuze": 0.2 if sampled_failure_count else 0.7,
    },
    "fuze_decision": {"detonated": True},
    "warhead_load_field": {
      "R_effect_variant": "REV-RUNTIME-PROJECTION",
      "effect_band": "core" if sampled_failure_count else "outer_effective",
      "rho_effect_case": 0.2 if sampled_failure_count else 0.7,
      "component_load_row_count": 4,
      "strongest_component_effect_scale": strongest_load,
      "weakest_component_effect_scale": 0.06,
    },
    "component_response": {
      "component_response_row_count": 4,
      "max_failure_probability": max_failure_probability,
      "sampled_failure_count": sampled_failure_count,
      "min_integrity_delta": -0.3 if sampled_failure_count else -0.004,
      "primary_failure_mode": "hydraulic_pressure_loss",
      "component_response_band": component_response_band,
    },
    "consequence_projection": {
      "component_hit_count": 4,
      "component_failure_count": sampled_failure_count,
      "primary_component_system": "flight_control",
    },
    "component_detail": {
      "summary": {
        "component_detail_row_count": 1,
        "sampled_failure_detail_count": sampled_failure_count,
        "strongest_load_component": {
          "component_name": "aileron_actuator",
          "component_system": "flight_control",
          "effect_scale": strongest_load,
          "rho_effect_component": 0.2 if sampled_failure_count else 0.7,
        },
        "max_probability_component": {
          "component_name": "aileron_actuator",
          "component_system": "flight_control",
          "failure_probability": max_failure_probability,
          "effect_scale": strongest_load,
          "sampled_failure": bool(sampled_failure_count),
        },
      },
      "component_rows": [
        {
          "component_name": "aileron_actuator",
          "component_system": "flight_control",
          "effect_scale": strongest_load,
          "rho_effect_component": 0.2 if sampled_failure_count else 0.7,
          "failure_probability": max_failure_probability,
          "sampled_failure": bool(sampled_failure_count),
        }
      ],
    },
  }


def test_response_diagnosis_writes_probability_cliff_artifacts(tmp_path) -> None:
  report = {
    "schema_version": "a2.kill_chain_expectation_before_report.v1",
    "heatmap_rows": [
      _row(
        case_id="baseline",
        bearing=15.0,
        sampled_failure_count=2,
        strongest_load=0.9,
        max_failure_probability=0.88,
        component_response_band="sampled_failure_observed",
      ),
      _row(
        case_id="candidate",
        bearing=30.0,
        sampled_failure_count=0,
        strongest_load=0.12,
        max_failure_probability=0.006,
        component_response_band="observed_probability_only",
      ),
    ],
  }
  input_path = tmp_path / "before.json"
  input_path.write_text(json.dumps(report), encoding="utf-8")

  manifest = diagnosis.generate_response_diagnosis(
    input_path=input_path,
    output_dir=tmp_path / "out",
    prefix="sample",
    date_stamp="20260628",
  )

  assert manifest["schema_version"] == diagnosis.SCHEMA_VERSION
  assert manifest["candidate_row_count"] == 1
  assert manifest["baseline_row_count"] == 1
  row = manifest["rows"][0]
  assert row["case_id"] == "candidate"
  assert row["diagnosis_bucket"] == "outer_effect_low_component_load_probability_cliff"
  assert row["detail_projection_signal"] == "all_component_rows_weak_load_low_response"
  assert row["baseline_case_id"] == "baseline"
  assert row["max_probability_ratio_to_baseline"] < 0.01

  assert (tmp_path / "out" / "sample_response_diagnosis_manifest_20260628.json").exists()
  assert (tmp_path / "out" / "sample_response_diagnosis_detail_20260628.csv").exists()
  assert (tmp_path / "out" / "sample_response_diagnosis_matrix_20260628.csv").exists()
  assert open(manifest["scatter_png"], "rb").read(8).startswith(b"\x89PNG")
  assert "<svg" in open(manifest["scatter_svg"], encoding="utf-8").read()
  assert "engineering-proxy diagnostics only" in (
    tmp_path / "out" / "sample_response_diagnosis_summary_20260628.md"
  ).read_text(encoding="utf-8")
