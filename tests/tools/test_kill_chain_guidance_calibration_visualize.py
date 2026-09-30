from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

from tools.diagnostics import kill_chain_guidance_calibration_visualize as visualize


RANGES = (4.0, 5.0, 6.0)
OFFSETS = (0.0, 5.0, 10.0)
GAINS = (3.5, 3.75, 4.0, 4.25, 4.5)


def _stage4_cell(range_km: float, offset_deg: float) -> dict[str, object]:
  if offset_deg == 0.0:
    launch_class = "N"
    robust_state = "robust_hit"
  elif offset_deg == 10.0:
    launch_class = "O"
    robust_state = "robust_miss"
  else:
    launch_class = "M"
    robust_state = "robust_miss" if range_km == 5.0 else "robust_hit"
  hit = robust_state == "robust_hit"
  return {
    "grid_tier": "main",
    "range_km": range_km,
    "offset_deg": offset_deg,
    "reclassified_launch_class": launch_class,
    "robust_state": robust_state,
    "rho_min": 0.05 if hit else 2.0,
    "rho_max": 0.1 if hit else 3.0,
  }


def _baseline_state(range_km: float, offset_deg: float) -> str:
  if offset_deg == 0.0:
    return "robust_hit"
  if offset_deg == 10.0:
    return "robust_miss"
  return "robust_miss" if range_km == 5.0 else "robust_hit"


def _candidate_state(nav_gain: float, range_km: float, offset_deg: float) -> str:
  baseline = _baseline_state(range_km, offset_deg)
  if nav_gain == 3.5 and (range_km, offset_deg) == (4.0, 5.0):
    return "robust_miss"
  if nav_gain == 4.25 and (range_km, offset_deg) == (5.0, 5.0):
    return "robust_hit"
  if nav_gain == 4.5 and (range_km, offset_deg) in {
    (5.0, 5.0),
    (6.0, 5.0),
  }:
    return "robust_miss" if baseline == "robust_hit" else "robust_hit"
  return baseline


def _stage4_launch_class(offset_deg: float) -> str:
  if offset_deg == 0.0:
    return "N"
  if offset_deg == 10.0:
    return "O"
  return "M"


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
  stage4_path = tmp_path / "stage4.json"
  stage4_path.write_text(
    json.dumps(
      {
        "schema_version": visualize.STAGE4_SCHEMA_VERSION,
        "status": "continuous_launch_envelope_rebuilt",
        "generated_at_utc": "2026-07-15T00:00:00+00:00",
        "main_cells": [
          _stage4_cell(range_km, offset_deg)
          for offset_deg in OFFSETS
          for range_km in RANGES
        ],
        "theta_fuze_by_range": [
          {"range_km": 4.0, "theta_fuze_robust_hit_max_deg": 5.0},
          {"range_km": 4.5, "theta_fuze_robust_hit_max_deg": 7.5},
          {"range_km": 5.0, "theta_fuze_robust_hit_max_deg": 0.0},
          {"range_km": 5.5, "theta_fuze_robust_hit_max_deg": 7.5},
          {"range_km": 6.0, "theta_fuze_robust_hit_max_deg": 5.0},
        ],
      }
    ),
    encoding="utf-8",
  )

  cells_path = tmp_path / "stage5_cells.csv"
  with cells_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(
      handle,
      fieldnames=(
        "candidate_id",
        "nav_gain",
        "grid_tier",
        "range_km",
        "offset_deg",
        "robust_state",
        "stage4_launch_class",
      ),
      lineterminator="\n",
    )
    writer.writeheader()
    for nav_gain in GAINS:
      for offset_deg in OFFSETS:
        for range_km in RANGES:
          writer.writerow(
            {
              "candidate_id": f"nav_gain_{nav_gain:g}",
              "nav_gain": nav_gain,
              "grid_tier": "main",
              "range_km": range_km,
              "offset_deg": offset_deg,
              "robust_state": _candidate_state(nav_gain, range_km, offset_deg),
              "stage4_launch_class": _stage4_launch_class(offset_deg),
            }
          )

  comparisons = []
  for nav_gain in GAINS:
    baseline = nav_gain == 4.0
    comparisons.append(
      {
        "candidate_id": f"nav_gain_{nav_gain:g}",
        "nav_gain": nav_gain,
        "is_baseline": baseline,
        "deltas_vs_baseline": (
          {}
          if baseline
          else {
            "holdout_robust_hit_count": int((nav_gain - 4.0) * 4),
            "theta_fuze_max_displacement_deg": 2.5,
            "guidance_saturation_fraction_p95": (nav_gain - 4.0) / 10.0,
          }
        ),
      }
    )
  stage5_path = tmp_path / "stage5.json"
  stage5_path.write_text(
    json.dumps(
      {
        "schema_version": visualize.STAGE5_SCHEMA_VERSION,
        "status": "scalar_calibration_completed_retained_baseline",
        "generated_at_utc": "2026-07-15T00:00:00+00:00",
        "raw_evidence": {"cells_csv": str(cells_path)},
        "evaluated_scalar": {
          "name": "nav_gain",
          "baseline": 4.0,
          "candidates": list(GAINS),
        },
        "comparisons_vs_baseline": comparisons,
        "selection": {
          "selected_nav_gain": 4.0,
          "decision": "retain_nav_gain_4_no_clear_net_benefit",
          "default_promotion_ready": False,
          "default_promotion_status": "held",
        },
      }
    ),
    encoding="utf-8",
  )
  return stage4_path, stage5_path, cells_path


def test_visualization_writes_three_source_only_evidence_figures(tmp_path) -> None:
  stage4_path, stage5_path, _cells_path = _write_inputs(tmp_path)
  manifest = visualize.generate_visualizations(
    stage4_report_path=stage4_path,
    stage5_report_path=stage5_path,
    output_dir=tmp_path / "viz",
    prefix="sample",
    date_stamp="20260715",
  )

  assert manifest["schema_version"] == visualize.SCHEMA_VERSION
  assert manifest["source_only_rendering"] is True
  assert manifest["simulation_rerun"] is False
  assert manifest["matrix_scope"]["range_km_axis"] == list(RANGES)
  assert manifest["matrix_scope"]["absolute_offset_deg_axis"] == list(OFFSETS)
  assert set(manifest["artifacts"]) == {
    "stage4_launch_class",
    "stage4_log10_rho_edge",
    "stage5_state_changes_vs_N4",
  }

  for artifact in manifest["artifacts"].values():
    for kind in ("csv", "png", "svg"):
      record = artifact[kind]
      path = Path(record["path"])
      assert path.exists()
      assert record["bytes"] == path.stat().st_size
      assert len(record["sha256"]) == 64
    assert Path(artifact["png"]["path"]).read_bytes().startswith(b"\x89PNG")
    svg_text = Path(artifact["svg"]["path"]).read_text(encoding="utf-8")
    assert "<svg" in svg_text
    assert all(line == line.rstrip() for line in svg_text.splitlines())

  class_csv = Path(manifest["artifacts"]["stage4_launch_class"]["csv"]["path"])
  class_text = class_csv.read_text(encoding="utf-8")
  assert class_text.startswith("absolute_offset_deg,4,5,6\n")
  assert "5,M,M,M" in class_text

  rho_csv = Path(manifest["artifacts"]["stage4_log10_rho_edge"]["csv"]["path"])
  rho_rows = list(csv.reader(rho_csv.open(encoding="utf-8")))
  assert math.isclose(float(rho_rows[1][1]), -1.0)
  assert math.isclose(float(rho_rows[3][1]), math.log10(2.0))

  transition_csv = Path(
    manifest["artifacts"]["stage5_state_changes_vs_N4"]["csv"]["path"]
  )
  transition_text = transition_csv.read_text(encoding="utf-8")
  assert transition_text.startswith("nav_gain,absolute_offset_deg,4,5,6\n")
  assert "lost" in transition_text
  assert "gained" in transition_text
  assert manifest["stage5_panel_metrics"]["3.5"]["main_net_robust_hit_change"] == -1
  assert manifest["stage5_panel_metrics"]["4.25"]["main_net_robust_hit_change"] == 1

  summary = Path(manifest["summary"]["path"]).read_text(encoding="utf-8")
  assert "不对未采样区域做插值或平滑" in summary
  assert "未重跑仿真" in summary
  assert "默认发布状态：`held`" in summary
  assert manifest["stage4_visual_context"]["launch_class_counts"] == {
    "N": 3,
    "M": 3,
    "O": 3,
  }


def test_rendered_png_and_svg_are_deterministic_for_same_inputs(tmp_path) -> None:
  stage4_path, stage5_path, _cells_path = _write_inputs(tmp_path)
  first = visualize.generate_visualizations(
    stage4_report_path=stage4_path,
    stage5_report_path=stage5_path,
    output_dir=tmp_path / "first",
    prefix="sample",
    date_stamp="20260715",
  )
  second = visualize.generate_visualizations(
    stage4_report_path=stage4_path,
    stage5_report_path=stage5_path,
    output_dir=tmp_path / "second",
    prefix="sample",
    date_stamp="20260715",
  )
  for artifact_id in first["artifacts"]:
    for kind in ("png", "svg"):
      assert (
        first["artifacts"][artifact_id][kind]["sha256"]
        == second["artifacts"][artifact_id][kind]["sha256"]
      )


def test_rho_edge_uses_hit_max_and_miss_min() -> None:
  assert visualize._rho_edge(
    {"robust_state": "robust_hit", "rho_min": 0.1, "rho_max": 0.8}
  ) == 0.8
  assert visualize._rho_edge(
    {"robust_state": "robust_miss", "rho_min": 1.2, "rho_max": 3.0}
  ) == 1.2


def test_duplicate_stage5_baseline_cell_is_rejected(tmp_path) -> None:
  stage4_path, stage5_path, cells_path = _write_inputs(tmp_path)
  rows = list(csv.DictReader(cells_path.open(encoding="utf-8")))
  with cells_path.open("a", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=rows[0], lineterminator="\n")
    writer.writerow(next(row for row in rows if row["nav_gain"] == "4.0"))

  with pytest.raises(ValueError, match="duplicate matrix cell"):
    visualize.generate_visualizations(
      stage4_report_path=stage4_path,
      stage5_report_path=stage5_path,
      output_dir=tmp_path / "viz",
      prefix="sample",
      date_stamp="20260715",
    )


def test_stage5_state_change_outside_M_band_is_rejected(tmp_path) -> None:
  stage4_path, stage5_path, cells_path = _write_inputs(tmp_path)
  rows = list(csv.DictReader(cells_path.open(encoding="utf-8")))
  changed = False
  for row in rows:
    if (
      row["nav_gain"] == "3.5"
      and row["range_km"] == "4.0"
      and row["offset_deg"] == "0.0"
    ):
      row["robust_state"] = "robust_miss"
      changed = True
  assert changed
  with cells_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=rows[0], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

  with pytest.raises(ValueError, match="escaped the stage-4 M band"):
    visualize.generate_visualizations(
      stage4_report_path=stage4_path,
      stage5_report_path=stage5_path,
      output_dir=tmp_path / "viz",
      prefix="sample",
      date_stamp="20260715",
    )


def test_stage4_stage5_baseline_mismatch_is_rejected(tmp_path) -> None:
  stage4_path, stage5_path, cells_path = _write_inputs(tmp_path)
  rows = list(csv.DictReader(cells_path.open(encoding="utf-8")))
  changed = False
  for row in rows:
    if (
      row["nav_gain"] == "4.0"
      and row["range_km"] == "5.0"
      and row["offset_deg"] == "0.0"
    ):
      row["stage4_launch_class"] = "M"
      changed = True
  assert changed
  with cells_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=rows[0], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

  with pytest.raises(ValueError, match="stage-4 report and stage-5 baseline"):
    visualize.generate_visualizations(
      stage4_report_path=stage4_path,
      stage5_report_path=stage5_path,
      output_dir=tmp_path / "viz",
      prefix="sample",
      date_stamp="20260715",
    )
