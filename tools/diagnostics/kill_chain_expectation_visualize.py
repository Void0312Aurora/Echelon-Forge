#!/usr/bin/env python3
"""Visualize KCES before-report rows as heatmap matrices."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

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

from tools.diagnostics.common import add_kces_before_report_args, finite_float_or_none, write_json_output
SCHEMA_VERSION = "a2.kill_chain_expectation_visualization_manifest.v1"
DEFAULT_VARIANT = "REV-RUNTIME-PROJECTION"
DEFAULT_TARGET_MOTION_LAYER = "nonmaneuvering_constant_velocity"

@dataclass(frozen=True)
class MetricSpec:
  metric_id: str
  title: str
  description: str
  value_getter: Callable[[dict[str, Any]], Any]
  numeric: bool
  filename_stem: str
  annotation_formatter: Callable[[Any], str]
  category_values: dict[str, int] | None = None
  category_colors: dict[str, str] | None = None

def _nested_get(row: dict[str, Any], *path: str) -> Any:
  value: Any = row
  for part in path:
    if not isinstance(value, dict):
      return None
    value = value.get(part)
  return value

def _compact_float(value: Any) -> str:
  out = finite_float_or_none(value)
  if out is None:
    return ""
  if abs(out) >= 100.0:
    return f"{out:.0f}"
  if abs(out) >= 10.0:
    return f"{out:.1f}"
  if abs(out) >= 1.0:
    return f"{out:.2f}"
  return f"{out:.3f}"

def _short_status(value: Any) -> str:
  text = str(value or "")
  return {
    "satisfied": "sat",
    "guidance_or_model_residual": "res",
    "observed_marginal": "marg",
    "negative_control_satisfied": "neg-ok",
    "negative_control_alert": "neg-alert",
    "missing_guidance_fact": "missing",
    "not_run": "not-run",
  }.get(text, text[:9])

def _short_effect_band(value: Any) -> str:
  text = str(value or "")
  return {
    "core": "core",
    "effective": "eff",
    "outer_effective": "outer",
    "edge": "edge",
    "outside_effect": "out",
    "unclassified_missing_R_effect": "missing",
    "not_evaluated": "n/a",
  }.get(text, text[:9])

METRICS: tuple[MetricSpec, ...] = (
  MetricSpec(
    metric_id="launch_class",
    title="Launch Class",
    description="P2 engineering-proxy launch-window class.",
    value_getter=lambda row: _nested_get(row, "launch_window", "launch_class"),
    numeric=False,
    filename_stem="launch_class",
    category_values={"O": 0, "M": 1, "N": 2},
    category_colors={"O": "#d7d7d7", "M": "#f4b860", "N": "#61b87a"},
    annotation_formatter=lambda value: str(value or ""),
  ),
  MetricSpec(
    metric_id="guidance_status",
    title="Guidance Expectation Status",
    description="Derived stage expectation status for the selected runtime rows.",
    value_getter=lambda row: _nested_get(
      row,
      "guidance_approach",
      "guidance_expectation_status",
    ),
    numeric=False,
    filename_stem="guidance_status",
    category_values={
      "not_run": -4,
      "missing_guidance_fact": -3,
      "negative_control_alert": -2,
      "guidance_or_model_residual": -1,
      "negative_control_satisfied": 0,
      "observed_marginal": 1,
      "satisfied": 2,
    },
    category_colors={
      "not_run": "#8d8d8d",
      "missing_guidance_fact": "#6d6d6d",
      "negative_control_alert": "#c43c39",
      "guidance_or_model_residual": "#e07a3f",
      "negative_control_satisfied": "#d7d7d7",
      "observed_marginal": "#f4d35e",
      "satisfied": "#61b87a",
    },
    annotation_formatter=_short_status,
  ),
  MetricSpec(
    metric_id="rho_fuze",
    title="rho_fuze",
    description="Nearest distance divided by the declared fuze radius.",
    value_getter=lambda row: _nested_get(row, "guidance_approach", "rho_fuze"),
    numeric=True,
    filename_stem="rho_fuze",
    annotation_formatter=_compact_float,
  ),
  MetricSpec(
    metric_id="max_failure_probability",
    title="Max Failure Probability",
    description="Maximum per-component failure probability observed in the response stage.",
    value_getter=lambda row: _nested_get(
      row,
      "component_response",
      "max_failure_probability",
    ),
    numeric=True,
    filename_stem="max_failure_probability",
    annotation_formatter=_compact_float,
  ),
  MetricSpec(
    metric_id="effect_band",
    title="Effect Band",
    description="Case-level band from nearest distance over the selected R_effect variant.",
    value_getter=lambda row: _nested_get(row, "warhead_load_field", "effect_band"),
    numeric=False,
    filename_stem="effect_band",
    category_values={
      "unclassified_missing_R_effect": -1,
      "outside_effect": 0,
      "edge": 1,
      "outer_effective": 2,
      "effective": 3,
      "core": 4,
    },
    category_colors={
      "unclassified_missing_R_effect": "#8d8d8d",
      "outside_effect": "#d7d7d7",
      "edge": "#f4d35e",
      "outer_effective": "#7bc8a4",
      "effective": "#2f9e71",
      "core": "#176f4c",
    },
    annotation_formatter=_short_effect_band,
  ),
)

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

def _matrix_axes(rows: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
  ranges = sorted(
    {
      float(value)
      for value in (
        finite_float_or_none(_nested_get(row, "launch_window", "range_km"))
        for row in rows
      )
      if value is not None
    }
  )
  bearings = sorted(
    {
      float(value)
      for value in (
        finite_float_or_none(_nested_get(row, "launch_window", "signed_bearing_deg"))
        for row in rows
      )
      if value is not None
    }
  )
  if not ranges or not bearings:
    raise ValueError("selected rows do not contain range/bearing axes")
  return ranges, bearings

def _make_metric_matrix(
  rows: list[dict[str, Any]],
  *,
  spec: MetricSpec,
  ranges: list[float],
  bearings: list[float],
) -> tuple[np.ndarray, list[list[str]], list[list[str]]]:
  by_cell: dict[tuple[float, float], dict[str, Any]] = {}
  for row in rows:
    range_km = finite_float_or_none(_nested_get(row, "launch_window", "range_km"))
    bearing_deg = finite_float_or_none(
      _nested_get(row, "launch_window", "signed_bearing_deg")
    )
    if range_km is None or bearing_deg is None:
      continue
    by_cell[(float(range_km), float(bearing_deg))] = row

  matrix = np.full((len(ranges), len(bearings)), np.nan, dtype=float)
  annotations: list[list[str]] = [["" for _ in bearings] for _ in ranges]
  raw_text: list[list[str]] = [["" for _ in bearings] for _ in ranges]

  for r_index, range_km in enumerate(ranges):
    for b_index, bearing_deg in enumerate(bearings):
      row = by_cell.get((range_km, bearing_deg))
      if row is None:
        continue
      value = spec.value_getter(row)
      raw_text[r_index][b_index] = "" if value is None else str(value)
      annotations[r_index][b_index] = spec.annotation_formatter(value)
      if spec.numeric:
        numeric = finite_float_or_none(value)
        if numeric is not None:
          matrix[r_index, b_index] = numeric
      else:
        assert spec.category_values is not None
        if str(value) in spec.category_values:
          matrix[r_index, b_index] = float(spec.category_values[str(value)])
  return matrix, annotations, raw_text

def _write_matrix_csv(
  path: Path,
  *,
  ranges: list[float],
  bearings: list[float],
  raw_text: list[list[str]],
) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["range_km"] + [f"{bearing:g}" for bearing in bearings])
    for range_km, values in zip(ranges, raw_text, strict=True):
      writer.writerow([f"{range_km:g}", *values])

def _plot_matrix(
  base_path: Path,
  *,
  spec: MetricSpec,
  ranges: list[float],
  bearings: list[float],
  matrix: np.ndarray,
  annotations: list[list[str]],
  variant: str,
  target_motion_layer: str,
) -> dict[str, str]:
  figure_width = max(8.0, 0.72 * len(bearings) + 2.5)
  figure_height = max(4.8, 0.62 * len(ranges) + 2.0)
  fig, ax = plt.subplots(figsize=(figure_width, figure_height), dpi=160)
  masked = np.ma.masked_invalid(matrix)

  if spec.numeric:
    finite_values = matrix[np.isfinite(matrix)]
    vmax = float(np.max(finite_values)) if finite_values.size else 1.0
    if spec.metric_id == "rho_fuze":
      vmax = max(1.5, vmax)
      cmap = plt.get_cmap("viridis_r").copy()
    else:
      vmax = max(0.01, vmax)
      cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad(color="#eeeeee")
    image = ax.imshow(masked, cmap=cmap, vmin=0.0, vmax=vmax, aspect="auto")
    fig.colorbar(image, ax=ax, shrink=0.8)
  else:
    assert spec.category_values is not None
    assert spec.category_colors is not None
    ordered_items = sorted(spec.category_values.items(), key=lambda item: item[1])
    values = [item[1] for item in ordered_items]
    labels = [item[0] for item in ordered_items]
    colors = [spec.category_colors[label] for label in labels]
    cmap = ListedColormap(colors)
    cmap.set_bad(color="#eeeeee")
    boundaries = [values[0] - 0.5, *[value + 0.5 for value in values]]
    norm = BoundaryNorm(boundaries, cmap.N)
    image = ax.imshow(masked, cmap=cmap, norm=norm, aspect="auto")
    colorbar = fig.colorbar(image, ax=ax, shrink=0.8, ticks=values)
    colorbar.ax.set_yticklabels([spec.annotation_formatter(label) for label in labels])

  ax.set_title(f"{spec.title} ({variant})", fontsize=12)
  ax.set_xlabel("Signed bearing offset (deg)")
  ax.set_ylabel("Initial range (km)")
  ax.set_xticks(np.arange(len(bearings)), labels=[f"{b:g}" for b in bearings])
  ax.set_yticks(np.arange(len(ranges)), labels=[f"{r:g}" for r in ranges])
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

  for r_index, values in enumerate(annotations):
    for b_index, annotation in enumerate(values):
      if not annotation:
        continue
      ax.text(
        b_index,
        r_index,
        annotation,
        ha="center",
        va="center",
        fontsize=7,
        color="#111111",
      )

  fig.tight_layout()
  png_path = base_path.with_suffix(".png")
  svg_path = base_path.with_suffix(".svg")
  fig.savefig(png_path)
  fig.savefig(svg_path)
  plt.close(fig)
  return {"png": str(png_path), "svg": str(svg_path)}

def _summary_lines(
  *,
  input_path: Path,
  rows: list[dict[str, Any]],
  variant: str,
  target_motion_layer: str,
  artifacts: dict[str, dict[str, str]],
) -> list[str]:
  launch_counts = Counter(
    str(_nested_get(row, "launch_window", "launch_class") or "") for row in rows
  )
  status_counts = Counter(
    str(
      _nested_get(row, "guidance_approach", "guidance_expectation_status") or ""
    )
    for row in rows
  )
  residual_rows = [
    row
    for row in rows
    if str(
      _nested_get(row, "guidance_approach", "guidance_expectation_status") or ""
    )
    == "guidance_or_model_residual"
  ]
  anchor_rows = [
    row
    for row in rows
    if finite_float_or_none(_nested_get(row, "launch_window", "range_km")) == 8.0
    and abs(
      (finite_float_or_none(_nested_get(row, "launch_window", "signed_bearing_deg")) or 0.0)
    )
    == 30.0
  ]

  lines = [
    "# KCES Anchor CV Visualization Summary",
    "",
    "This artifact renders the existing before-report JSON as reviewable heatmap",
    "matrices. It does not rerun simulation, retune runtime parameters, or claim",
    "real weapon / target / Pk authority.",
    "",
    "Boundary: engineering-proxy diagnostics only.",
    "",
    "## Source",
    "",
    f"- Input: `{input_path}`",
    f"- Variant: `{variant}`",
    f"- Target motion layer: `{target_motion_layer}`",
    f"- Selected rows: `{len(rows)}`",
    f"- Launch classes: `{dict(sorted(launch_counts.items()))}`",
    f"- Guidance statuses: `{dict(sorted(status_counts.items()))}`",
    "",
    "## Artifacts",
    "",
    "| Metric | CSV | PNG | SVG |",
    "| --- | --- | --- | --- |",
  ]
  for metric_id in sorted(artifacts):
    row = artifacts[metric_id]
    lines.append(
      f"| `{metric_id}` | `{Path(row['csv']).name}` | "
      f"`{Path(row['png']).name}` | `{Path(row['svg']).name}` |"
    )
  lines.extend(["", "## Review Notes", ""])
  if residual_rows:
    lines.append("- Current nominal residual cells:")
    for row in residual_rows:
      case_id = str(_nested_get(row, "identity", "case_id") or "")
      range_km = _nested_get(row, "launch_window", "range_km")
      bearing = _nested_get(row, "launch_window", "signed_bearing_deg")
      rho_fuze = _nested_get(row, "guidance_approach", "rho_fuze")
      lines.append(
        f"  - `{case_id}`: range_km=`{range_km}`, "
        f"signed_bearing_deg=`{bearing}`, rho_fuze=`{rho_fuze}`"
      )
  else:
    lines.append("- No nominal guidance residual cells were selected.")
  if anchor_rows:
    lines.append("- `8 km / +/-30 deg` selected rows:")
    for row in sorted(
      anchor_rows,
      key=lambda item: float(
        finite_float_or_none(_nested_get(item, "launch_window", "signed_bearing_deg"))
        or 0.0
      ),
    ):
      case_id = str(_nested_get(row, "identity", "case_id") or "")
      nearest = _nested_get(row, "guidance_approach", "nearest_distance_m")
      rho_fuze = _nested_get(row, "guidance_approach", "rho_fuze")
      effect_band = _nested_get(row, "warhead_load_field", "effect_band")
      max_p = _nested_get(row, "component_response", "max_failure_probability")
      lines.append(
        f"  - `{case_id}`: nearest_distance_m=`{nearest}`, "
        f"rho_fuze=`{rho_fuze}`, effect_band=`{effect_band}`, "
        f"max_failure_probability=`{max_p}`"
      )
  return lines

def generate_visualizations(
  *,
  input_path: Path,
  output_dir: Path,
  prefix: str = "kces_anchor_cv",
  variant: str = DEFAULT_VARIANT,
  target_motion_layer: str = DEFAULT_TARGET_MOTION_LAYER,
  date_stamp: str | None = None,
) -> dict[str, Any]:
  report = _read_report(input_path)
  rows = _selected_rows(
    report,
    variant=variant,
    target_motion_layer=target_motion_layer,
  )
  if not rows:
    raise ValueError(
      "no heatmap rows matched "
      f"variant={variant!r}, target_motion_layer={target_motion_layer!r}"
    )
  ranges, bearings = _matrix_axes(rows)
  output_dir.mkdir(parents=True, exist_ok=True)
  stamp = date_stamp or datetime.now().strftime("%Y%m%d")
  artifacts: dict[str, dict[str, str]] = {}

  for spec in METRICS:
    matrix, annotations, raw_text = _make_metric_matrix(
      rows,
      spec=spec,
      ranges=ranges,
      bearings=bearings,
    )
    base = output_dir / f"{prefix}_{spec.filename_stem}_heatmap_{stamp}"
    csv_path = base.with_suffix(".csv")
    _write_matrix_csv(csv_path, ranges=ranges, bearings=bearings, raw_text=raw_text)
    image_paths = _plot_matrix(
      base,
      spec=spec,
      ranges=ranges,
      bearings=bearings,
      matrix=matrix,
      annotations=annotations,
      variant=variant,
      target_motion_layer=target_motion_layer,
    )
    artifacts[spec.metric_id] = {
      "description": spec.description,
      "csv": str(csv_path),
      **image_paths,
    }

  summary_path = output_dir / f"{prefix}_visualization_summary_{stamp}.md"
  summary_path.write_text(
    "\n".join(
      _summary_lines(
        input_path=input_path,
        rows=rows,
        variant=variant,
        target_motion_layer=target_motion_layer,
        artifacts=artifacts,
      )
    )
    + "\n",
    encoding="utf-8",
  )
  manifest_path = output_dir / f"{prefix}_visualization_manifest_{stamp}.json"
  manifest: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "status": "generated",
    "input_path": str(input_path),
    "manifest_path": str(manifest_path),
    "output_dir": str(output_dir),
    "prefix": str(prefix),
    "variant": str(variant),
    "target_motion_layer": str(target_motion_layer),
    "date_stamp": str(stamp),
    "selected_row_count": len(rows),
    "range_km_axis": ranges,
    "signed_bearing_deg_axis": bearings,
    "artifacts": artifacts,
    "summary_markdown": str(summary_path),
  }
  _write_json(manifest_path, manifest)
  return manifest

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Render KCES before-report heatmap rows to CSV, PNG, and SVG matrices."
  )
  add_kces_before_report_args(
    parser,
    variant_default=DEFAULT_VARIANT,
    target_motion_layer_default=DEFAULT_TARGET_MOTION_LAYER,
    date_stamp_example="20260623",
  )
  args = parser.parse_args(argv)

  output_dir = args.output_dir or args.input.parent
  manifest = generate_visualizations(
    input_path=args.input,
    output_dir=output_dir,
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
