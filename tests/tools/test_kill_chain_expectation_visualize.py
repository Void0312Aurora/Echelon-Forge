from __future__ import annotations

import json

from tools.diagnostics import kill_chain_expectation_visualize as visualize


def _row(
  *,
  case_id: str,
  range_km: float,
  signed_bearing_deg: float,
  launch_class: str,
  status: str,
  rho_fuze: float,
  max_failure_probability: float,
  effect_band: str,
) -> dict[str, object]:
  return {
    "identity": {"case_id": case_id},
    "launch_window": {
      "target_motion_layer": "nonmaneuvering_constant_velocity",
      "range_km": range_km,
      "signed_bearing_deg": signed_bearing_deg,
      "launch_class": launch_class,
    },
    "guidance_approach": {
      "rho_fuze": rho_fuze,
      "guidance_expectation_status": status,
    },
    "warhead_load_field": {
      "R_effect_variant": "REV-RUNTIME-PROJECTION",
      "effect_band": effect_band,
    },
    "component_response": {
      "max_failure_probability": max_failure_probability,
    },
  }


def test_visualization_writes_manifest_images_and_matrices(tmp_path) -> None:
  report = {
    "schema_version": "a2.kill_chain_expectation_before_report.v1",
    "heatmap_rows": [
      _row(
        case_id="case_4_m30",
        range_km=4.0,
        signed_bearing_deg=-30.0,
        launch_class="N",
        status="satisfied",
        rho_fuze=0.25,
        max_failure_probability=0.8,
        effect_band="core",
      ),
      _row(
        case_id="case_4_p30",
        range_km=4.0,
        signed_bearing_deg=30.0,
        launch_class="N",
        status="guidance_or_model_residual",
        rho_fuze=1.4,
        max_failure_probability=0.0,
        effect_band="outside_effect",
      ),
      _row(
        case_id="case_6_m30",
        range_km=6.0,
        signed_bearing_deg=-30.0,
        launch_class="M",
        status="observed_marginal",
        rho_fuze=0.75,
        max_failure_probability=0.2,
        effect_band="outer_effective",
      ),
      _row(
        case_id="case_6_p30",
        range_km=6.0,
        signed_bearing_deg=30.0,
        launch_class="O",
        status="negative_control_satisfied",
        rho_fuze=1.8,
        max_failure_probability=0.0,
        effect_band="outside_effect",
      ),
    ],
  }
  input_path = tmp_path / "before.json"
  input_path.write_text(json.dumps(report), encoding="utf-8")

  manifest = visualize.generate_visualizations(
    input_path=input_path,
    output_dir=tmp_path / "viz",
    prefix="sample",
    date_stamp="20260623",
  )

  assert manifest["schema_version"] == visualize.SCHEMA_VERSION
  assert manifest["selected_row_count"] == 4
  assert manifest["range_km_axis"] == [4.0, 6.0]
  assert manifest["signed_bearing_deg_axis"] == [-30.0, 30.0]

  manifest_path = tmp_path / "viz" / "sample_visualization_manifest_20260623.json"
  assert manifest_path.exists()
  assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "generated"

  launch_paths = manifest["artifacts"]["launch_class"]
  assert (tmp_path / "viz" / "sample_launch_class_heatmap_20260623.csv").exists()
  assert "range_km,-30,30" in (
    tmp_path / "viz" / "sample_launch_class_heatmap_20260623.csv"
  ).read_text(encoding="utf-8")
  assert "<svg" in open(launch_paths["svg"], encoding="utf-8").read()
  assert open(launch_paths["png"], "rb").read(8).startswith(b"\x89PNG")
  assert "engineering-proxy diagnostics only" in (
    tmp_path / "viz" / "sample_visualization_summary_20260623.md"
  ).read_text(encoding="utf-8")
