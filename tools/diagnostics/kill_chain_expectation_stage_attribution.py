#!/usr/bin/env python3
"""Attribute KCES before-report rows to the first review stage."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.diagnostics.common import finite_float_or_none, write_json_output
SCHEMA_VERSION = "a2.kill_chain_expectation_stage_attribution.v1"
DEFAULT_VARIANT = "REV-RUNTIME-PROJECTION"
DEFAULT_TARGET_MOTION_LAYER = "nonmaneuvering_constant_velocity"

STAGE_VALUES = {
  "guard": -3,
  "not_run": -2,
  "unknown": -1,
  "negative_control_satisfied": 0,
  "no_review_pressure": 1,
  "marginal_observation": 2,
  "component_response": 3,
  "warhead_load_field": 4,
  "fuze_decision": 5,
  "guidance_approach": 6,
  "negative_control_alert": 7,
}
STAGE_COLORS = {
  "guard": "#8d8d8d",
  "not_run": "#b0b0b0",
  "unknown": "#6d6d6d",
  "negative_control_satisfied": "#d7d7d7",
  "no_review_pressure": "#61b87a",
  "marginal_observation": "#f4d35e",
  "component_response": "#7bc8a4",
  "warhead_load_field": "#2f9e71",
  "fuze_decision": "#4d9de0",
  "guidance_approach": "#e07a3f",
  "negative_control_alert": "#c43c39",
}
STAGE_LABELS = {
  "guard": "guard",
  "not_run": "not-run",
  "unknown": "unknown",
  "negative_control_satisfied": "neg-ok",
  "no_review_pressure": "ok",
  "marginal_observation": "marg",
  "component_response": "resp",
  "warhead_load_field": "load",
  "fuze_decision": "fuze",
  "guidance_approach": "guidance",
  "negative_control_alert": "neg-alert",
}

def _nested_get(row: dict[str, Any], *path: str) -> Any:
  value: Any = row
  for part in path:
    if not isinstance(value, dict):
      return None
    value = value.get(part)
  return value

def _bool_or_none(value: Any) -> bool | None:
  if value is None:
    return None
  if isinstance(value, bool):
    return value
  if isinstance(value, str):
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes"}:
      return True
    if lowered in {"false", "0", "no"}:
      return False
  return bool(value)

def _int_or_zero(value: Any) -> int:
  try:
    return int(value)
  except Exception:
    return 0

def _read_report(path: Path) -> dict[str, Any]:
  with path.open("r", encoding="utf-8") as handle:
    data = json.load(handle)
  if not isinstance(data, dict):
    raise TypeError(f"expected object JSON at {path}")
  return data

def _write_json(path: Path, data: dict[str, Any]) -> None:
  write_json_output(path, data, sort_keys=True, skip_empty_path=False)

def _selected_rows(
  report: dict[str, Any],
  *,
  variant: str,
  target_motion_layer: str,
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for raw in list(report.get("heatmap_rows", []) or []):
    if not isinstance(raw, dict):
      continue
    motion_layer = str(
      _nested_get(raw, "launch_window", "target_motion_layer") or ""
    )
    effect_variant = str(
      _nested_get(raw, "warhead_load_field", "R_effect_variant") or ""
    )
    if motion_layer == target_motion_layer and effect_variant == variant:
      rows.append(raw)
  return rows

def _response_signal(row: dict[str, Any]) -> str:
  response_band = str(
    _nested_get(row, "component_response", "component_response_band") or ""
  )
  sampled_count = _int_or_zero(
    _nested_get(row, "component_response", "sampled_failure_count")
  )
  max_probability = finite_float_or_none(
    _nested_get(row, "component_response", "max_failure_probability")
  )
  if sampled_count > 0 or response_band == "sampled_failure_observed":
    return "sampled_failure_observed"
  if max_probability is None:
    return "missing_response_fact"
  if response_band == "observed_probability_only":
    return "probability_only_no_sampled_failure"
  if max_probability > 0.0:
    return "probability_only_no_sampled_failure"
  return "no_response_signal"

def _load_signal(row: dict[str, Any]) -> str:
  effect_band = str(_nested_get(row, "warhead_load_field", "effect_band") or "")
  strongest = finite_float_or_none(
    _nested_get(row, "warhead_load_field", "strongest_component_effect_scale")
  )
  if effect_band in {"core", "effective", "outer_effective", "edge"}:
    return "load_band_available"
  if effect_band == "unclassified_missing_R_effect":
    return "missing_effect_radius"
  if (strongest or 0.0) > 0.0:
    return "component_load_present_outside_case_band"
  return "no_load_signal"

def _stage_attribution(row: dict[str, Any]) -> dict[str, Any]:
  run_status = str(row.get("run_status", "") or "")
  launch_class = str(_nested_get(row, "launch_window", "launch_class") or "")
  guidance_status = str(
    _nested_get(row, "guidance_approach", "guidance_expectation_status") or ""
  )
  entered_r_fuze = _bool_or_none(
    _nested_get(row, "guidance_approach", "entered_R_fuze")
  )
  detonated = _bool_or_none(_nested_get(row, "fuze_decision", "detonated"))
  authority_status = str(
    _nested_get(row, "guards", "authority_boundary_status") or ""
  )
  effect_band = str(_nested_get(row, "warhead_load_field", "effect_band") or "")
  response_signal = _response_signal(row)
  load_signal = _load_signal(row)

  if run_status and run_status != "generated":
    return _attribution(
      row,
      stage="not_run",
      priority="held",
      reason="case did not produce runtime facts",
      response_signal=response_signal,
      load_signal=load_signal,
    )
  if authority_status != "engineering_proxy_guarded":
    return _attribution(
      row,
      stage="guard",
      priority="high",
      reason="authority boundary guard is not clean",
      response_signal=response_signal,
      load_signal=load_signal,
    )

  if launch_class == "O":
    if guidance_status == "negative_control_alert":
      return _attribution(
        row,
        stage="negative_control_alert",
        priority="high",
        reason="outside-envelope negative control produced approach/load/response pressure",
        response_signal=response_signal,
        load_signal=load_signal,
      )
    return _attribution(
      row,
      stage="negative_control_satisfied",
      priority="none",
      reason="outside-envelope negative control stayed quiet",
      response_signal=response_signal,
      load_signal=load_signal,
    )

  if launch_class == "M":
    return _attribution(
      row,
      stage="marginal_observation",
      priority="low",
      reason="marginal launch-window cell is observed, not treated as failed",
      response_signal=response_signal,
      load_signal=load_signal,
    )

  if launch_class == "N":
    if guidance_status != "satisfied" or entered_r_fuze is not True:
      return _attribution(
        row,
        stage="guidance_approach",
        priority="high",
        reason="nominal cell did not enter the declared fuze radius",
        response_signal=response_signal,
        load_signal=load_signal,
      )
    if detonated is not True:
      return _attribution(
        row,
        stage="fuze_decision",
        priority="high",
        reason="nominal cell entered fuze radius but did not detonate",
        response_signal=response_signal,
        load_signal=load_signal,
      )
    if effect_band == "outside_effect":
      if response_signal == "sampled_failure_observed":
        return _attribution(
          row,
          stage="warhead_load_field",
          priority="medium",
          reason="outside-effect nominal cell produced sampled component response",
          response_signal=response_signal,
          load_signal=load_signal,
        )
      return _attribution(
        row,
        stage="no_review_pressure",
        priority="none",
        reason=(
          "nominal cell satisfied guidance/fuze and remained outside the selected "
          "effective-load radius without sampled response"
        ),
        response_signal=response_signal,
        load_signal=load_signal,
      )
    if effect_band in {"unclassified_missing_R_effect", ""}:
      return _attribution(
        row,
        stage="warhead_load_field",
        priority="medium",
        reason="nominal cell detonated without declared effective-load metadata",
        response_signal=response_signal,
        load_signal=load_signal,
      )
    if response_signal in {
      "probability_only_no_sampled_failure",
      "missing_response_fact",
      "no_response_signal",
    }:
      return _attribution(
        row,
        stage="component_response",
        priority="medium",
        reason=(
          "nominal cell has guidance/fuze/load facts but no sampled component "
          "failure in the response stage"
        ),
        response_signal=response_signal,
        load_signal=load_signal,
      )
    return _attribution(
      row,
      stage="no_review_pressure",
      priority="none",
      reason="nominal cell satisfied guidance/fuze/load and observed sampled response",
      response_signal=response_signal,
      load_signal=load_signal,
    )

  return _attribution(
    row,
    stage="unknown",
    priority="medium",
    reason=f"unrecognized launch_class={launch_class!r}",
    response_signal=response_signal,
    load_signal=load_signal,
  )

def _attribution(
  row: dict[str, Any],
  *,
  stage: str,
  priority: str,
  reason: str,
  response_signal: str,
  load_signal: str,
) -> dict[str, Any]:
  return {
    "case_id": str(_nested_get(row, "identity", "case_id") or ""),
    "range_km": finite_float_or_none(_nested_get(row, "launch_window", "range_km")),
    "signed_bearing_deg": finite_float_or_none(
      _nested_get(row, "launch_window", "signed_bearing_deg")
    ),
    "launch_class": str(_nested_get(row, "launch_window", "launch_class") or ""),
    "first_review_stage": str(stage),
    "review_priority": str(priority),
    "review_reason": str(reason),
    "guidance_expectation_status": str(
      _nested_get(row, "guidance_approach", "guidance_expectation_status") or ""
    ),
    "entered_R_fuze": _bool_or_none(
      _nested_get(row, "guidance_approach", "entered_R_fuze")
    ),
    "rho_fuze": finite_float_or_none(_nested_get(row, "guidance_approach", "rho_fuze")),
    "detonated": _bool_or_none(_nested_get(row, "fuze_decision", "detonated")),
    "effect_band": str(_nested_get(row, "warhead_load_field", "effect_band") or ""),
    "rho_effect_case": finite_float_or_none(
      _nested_get(row, "warhead_load_field", "rho_effect_case")
    ),
    "load_signal": str(load_signal),
    "max_failure_probability": finite_float_or_none(
      _nested_get(row, "component_response", "max_failure_probability")
    ),
    "sampled_failure_count": _int_or_zero(
      _nested_get(row, "component_response", "sampled_failure_count")
    ),
    "component_response_band": str(
      _nested_get(row, "component_response", "component_response_band") or ""
    ),
    "response_signal": str(response_signal),
  }

def _axis(rows: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
  ranges = sorted(
    {
      value
      for value in (finite_float_or_none(item.get("range_km")) for item in rows)
      if value is not None
    }
  )
  bearings = sorted(
    {
      value
      for value in (finite_float_or_none(item.get("signed_bearing_deg")) for item in rows)
      if value is not None
    }
  )
  if not ranges or not bearings:
    raise ValueError("attribution rows do not contain range/bearing axes")
  return ranges, bearings

def _write_csv(
  path: Path,
  *,
  rows: list[dict[str, Any]],
  ranges: list[float],
  bearings: list[float],
) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  by_cell = {
    (row.get("range_km"), row.get("signed_bearing_deg")): row
    for row in rows
  }
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["range_km"] + [f"{bearing:g}" for bearing in bearings])
    for range_km in ranges:
      values = []
      for bearing in bearings:
        row = by_cell.get((range_km, bearing))
        values.append("" if row is None else str(row["first_review_stage"]))
      writer.writerow([f"{range_km:g}", *values])

def _write_detail_csv(path: Path, *, rows: list[dict[str, Any]]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  fields = [
    "case_id",
    "range_km",
    "signed_bearing_deg",
    "launch_class",
    "first_review_stage",
    "review_priority",
    "review_reason",
    "guidance_expectation_status",
    "entered_R_fuze",
    "rho_fuze",
    "detonated",
    "effect_band",
    "rho_effect_case",
    "load_signal",
    "max_failure_probability",
    "sampled_failure_count",
    "component_response_band",
    "response_signal",
  ]
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(
      handle,
      fieldnames=fields,
      extrasaction="ignore",
      lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)

def _plot_stage_heatmap(
  path_base: Path,
  *,
  rows: list[dict[str, Any]],
  ranges: list[float],
  bearings: list[float],
  variant: str,
  target_motion_layer: str,
) -> dict[str, str]:
  by_cell = {
    (row.get("range_km"), row.get("signed_bearing_deg")): row
    for row in rows
  }
  matrix = np.full((len(ranges), len(bearings)), np.nan, dtype=float)
  annotations = [["" for _ in bearings] for _ in ranges]
  for r_index, range_km in enumerate(ranges):
    for b_index, bearing in enumerate(bearings):
      row = by_cell.get((range_km, bearing))
      if row is None:
        continue
      stage = str(row["first_review_stage"])
      matrix[r_index, b_index] = float(STAGE_VALUES.get(stage, -1))
      annotations[r_index][b_index] = STAGE_LABELS.get(stage, stage[:8])

  ordered_items = sorted(STAGE_VALUES.items(), key=lambda item: item[1])
  values = [item[1] for item in ordered_items]
  labels = [item[0] for item in ordered_items]
  colors = [STAGE_COLORS[label] for label in labels]
  cmap = ListedColormap(colors)
  cmap.set_bad(color="#eeeeee")
  boundaries = [values[0] - 0.5, *[value + 0.5 for value in values]]
  norm = BoundaryNorm(boundaries, cmap.N)

  fig, ax = plt.subplots(
    figsize=(max(8.0, 0.72 * len(bearings) + 2.5), max(4.8, 0.62 * len(ranges) + 2.0)),
    dpi=160,
  )
  image = ax.imshow(np.ma.masked_invalid(matrix), cmap=cmap, norm=norm, aspect="auto")
  colorbar = fig.colorbar(image, ax=ax, shrink=0.8, ticks=values)
  colorbar.ax.set_yticklabels([STAGE_LABELS[label] for label in labels])

  ax.set_title(f"First Review Stage ({variant})", fontsize=12)
  ax.set_xlabel("Signed bearing offset (deg)")
  ax.set_ylabel("Initial range (km)")
  ax.set_xticks(np.arange(len(bearings)), labels=[f"{bearing:g}" for bearing in bearings])
  ax.set_yticks(np.arange(len(ranges)), labels=[f"{range_km:g}" for range_km in ranges])
  ax.tick_params(axis="x", rotation=45)
  ax.set_xticks(np.arange(-0.5, len(bearings), 1), minor=True)
  ax.set_yticks(np.arange(-0.5, len(ranges), 1), minor=True)
  ax.grid(which="minor", color="#ffffff", linewidth=0.8)
  ax.tick_params(which="minor", bottom=False, left=False)
  ax.text(
    0.0,
    -0.18,
    f"target_motion_layer={target_motion_layer}; engineering-proxy diagnostics only",
    transform=ax.transAxes,
    fontsize=8,
    color="#555555",
  )
  for r_index, values_row in enumerate(annotations):
    for b_index, label in enumerate(values_row):
      if label:
        ax.text(b_index, r_index, label, ha="center", va="center", fontsize=7)

  fig.tight_layout()
  png_path = path_base.with_suffix(".png")
  svg_path = path_base.with_suffix(".svg")
  fig.savefig(png_path)
  fig.savefig(svg_path)
  plt.close(fig)
  return {"png": str(png_path), "svg": str(svg_path)}

def _top_rows(rows: list[dict[str, Any]], *, stage: str) -> list[dict[str, Any]]:
  return sorted(
    [row for row in rows if row["first_review_stage"] == stage],
    key=lambda row: (
      float(row.get("range_km") or 0.0),
      float(row.get("signed_bearing_deg") or 0.0),
    ),
  )

def _summary_markdown(
  *,
  input_path: Path,
  output: dict[str, Any],
  rows: list[dict[str, Any]],
) -> str:
  stage_counts = dict(sorted(Counter(row["first_review_stage"] for row in rows).items()))
  priority_counts = dict(sorted(Counter(row["review_priority"] for row in rows).items()))
  lines = [
    "# KCES First-Review-Stage Attribution Summary",
    "",
    "This report consumes existing before-report rows and attributes each selected",
    "heatmap cell to the first stage that should be reviewed. It is a diagnostic",
    "triage artifact, not a calibration verdict or real-world authority claim.",
    "",
    "Boundary: engineering-proxy diagnostics only.",
    "",
    "## Source",
    "",
    f"- Input: `{input_path}`",
    f"- Variant: `{output['variant']}`",
    f"- Target motion layer: `{output['target_motion_layer']}`",
    f"- Selected rows: `{output['selected_row_count']}`",
    f"- Stage counts: `{stage_counts}`",
    f"- Priority counts: `{priority_counts}`",
    "",
    "## Artifacts",
    "",
    f"- Manifest JSON: `{Path(output['manifest_path']).name}`",
    f"- Stage matrix CSV: `{Path(output['stage_matrix_csv']).name}`",
    f"- Detail CSV: `{Path(output['detail_csv']).name}`",
    f"- Stage heatmap PNG: `{Path(output['stage_heatmap_png']).name}`",
    f"- Stage heatmap SVG: `{Path(output['stage_heatmap_svg']).name}`",
    "",
    "## Review Focus",
    "",
  ]
  guidance = _top_rows(rows, stage="guidance_approach")
  response = _top_rows(rows, stage="component_response")
  if guidance:
    lines.append("- Guidance / launch-window residual cells:")
    for row in guidance:
      lines.append(
        f"  - `{row['case_id']}`: range_km=`{row['range_km']}`, "
        f"signed_bearing_deg=`{row['signed_bearing_deg']}`, "
        f"rho_fuze=`{row['rho_fuze']}`"
      )
  else:
    lines.append("- No guidance / launch-window residual cells were selected.")
  if response:
    lines.append("- Component-response review cells after guidance/fuze/load facts:")
    for row in response:
      lines.append(
        f"  - `{row['case_id']}`: range_km=`{row['range_km']}`, "
        f"signed_bearing_deg=`{row['signed_bearing_deg']}`, "
        f"effect_band=`{row['effect_band']}`, "
        f"max_failure_probability=`{row['max_failure_probability']}`"
      )
  else:
    lines.append("- No component-response review cells were selected.")
  lines.extend(
    [
      "",
      "## Interpretation",
      "",
      "- `guidance_approach` means a nominal cell did not enter the declared",
      "  `R_fuze`; it should be reviewed before applying warhead or response",
      "  pressure.",
      "- `component_response` means guidance, fuze, and case-level load facts are",
      "  present, but the response stage did not observe sampled component failure.",
      "- `marginal_observation` and `negative_control_satisfied` are not failures;",
      "  they preserve the heatmap topology for later comparison.",
    ]
  )
  return "\n".join(lines) + "\n"

def generate_stage_attribution(
  *,
  input_path: Path,
  output_dir: Path,
  prefix: str = "kces_anchor_cv",
  variant: str = DEFAULT_VARIANT,
  target_motion_layer: str = DEFAULT_TARGET_MOTION_LAYER,
  date_stamp: str | None = None,
) -> dict[str, Any]:
  report = _read_report(input_path)
  selected = _selected_rows(
    report,
    variant=variant,
    target_motion_layer=target_motion_layer,
  )
  if not selected:
    raise ValueError(
      "no heatmap rows matched "
      f"variant={variant!r}, target_motion_layer={target_motion_layer!r}"
    )
  rows = [_stage_attribution(row) for row in selected]
  ranges, bearings = _axis(rows)
  output_dir.mkdir(parents=True, exist_ok=True)
  stamp = date_stamp or datetime.now().strftime("%Y%m%d")

  matrix_csv = output_dir / f"{prefix}_first_review_stage_matrix_{stamp}.csv"
  detail_csv = output_dir / f"{prefix}_first_review_stage_detail_{stamp}.csv"
  heatmap_base = output_dir / f"{prefix}_first_review_stage_heatmap_{stamp}"
  manifest_path = output_dir / f"{prefix}_first_review_stage_manifest_{stamp}.json"
  summary_path = output_dir / f"{prefix}_first_review_stage_summary_{stamp}.md"

  _write_csv(matrix_csv, rows=rows, ranges=ranges, bearings=bearings)
  _write_detail_csv(detail_csv, rows=rows)
  image_paths = _plot_stage_heatmap(
    heatmap_base,
    rows=rows,
    ranges=ranges,
    bearings=bearings,
    variant=variant,
    target_motion_layer=target_motion_layer,
  )

  stage_counts = dict(sorted(Counter(row["first_review_stage"] for row in rows).items()))
  priority_counts = dict(sorted(Counter(row["review_priority"] for row in rows).items()))
  manifest: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "status": "generated",
    "input_path": str(input_path),
    "manifest_path": str(manifest_path),
    "summary_markdown": str(summary_path),
    "output_dir": str(output_dir),
    "prefix": str(prefix),
    "variant": str(variant),
    "target_motion_layer": str(target_motion_layer),
    "date_stamp": str(stamp),
    "selected_row_count": len(rows),
    "range_km_axis": ranges,
    "signed_bearing_deg_axis": bearings,
    "stage_counts": stage_counts,
    "priority_counts": priority_counts,
    "stage_matrix_csv": str(matrix_csv),
    "detail_csv": str(detail_csv),
    "stage_heatmap_png": image_paths["png"],
    "stage_heatmap_svg": image_paths["svg"],
    "rows": rows,
    "boundary": {
      "authority_level": "engineering_proxy_diagnostics_only",
      "runtime_parameter_retuning": False,
      "real_weapon_or_target_authority": False,
      "calibration_verdict": False,
    },
  }
  _write_json(manifest_path, manifest)
  summary_path.write_text(
    _summary_markdown(input_path=input_path, output=manifest, rows=rows),
    encoding="utf-8",
  )
  return manifest

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Attribute KCES before-report rows to the first review stage."
  )
  parser.add_argument("--input", required=True, type=Path, help="Before-report JSON path.")
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=None,
    help="Output directory. Defaults to the input file directory.",
  )
  parser.add_argument("--prefix", default="kces_anchor_cv")
  parser.add_argument("--variant", default=DEFAULT_VARIANT)
  parser.add_argument("--target-motion-layer", default=DEFAULT_TARGET_MOTION_LAYER)
  parser.add_argument(
    "--date-stamp",
    default=None,
    help="Filename date stamp, for example 20260623. Defaults to today.",
  )
  args = parser.parse_args(argv)

  manifest = generate_stage_attribution(
    input_path=args.input,
    output_dir=args.output_dir or args.input.parent,
    prefix=args.prefix,
    variant=args.variant,
    target_motion_layer=args.target_motion_layer,
    date_stamp=args.date_stamp,
  )
  json.dump(manifest, sys.stdout, indent=2, sort_keys=True, ensure_ascii=True)
  sys.stdout.write("\n")
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
