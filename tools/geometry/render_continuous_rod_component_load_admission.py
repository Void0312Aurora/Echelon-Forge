#!/usr/bin/env python3
"""Render the P8 component-load admission packet as readable heatmaps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


DIRECTIONS = ("front", "back", "right", "left", "up", "down")
STANDOFFS = (0.5, 2.0, 6.0, 10.0)
HEADINGS = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)


def _load_value(event: dict[str, Any], name: str) -> float:
  loads = list(event.get("component_mechanism_load_rows", []))
  if not loads:
    return 0.0
  if name == "effect_scale":
    return max(float(row["effect_scale"]) for row in loads)
  if name == "rod_cut_margin":
    return max(float(row["mechanism_rod_cut_margin"]) for row in loads)
  raise KeyError(name)


def _response_probability_delta(baseline: dict[str, Any], variant: dict[str, Any]) -> float:
  left = {
    tuple(
      str(row[field])
      for field in ("component_name", "component_system", "component_redundancy_group_id")
    ): row
    for row in baseline.get("component_response_rows", [])
  }
  right = {
    tuple(
      str(row[field])
      for field in ("component_name", "component_system", "component_redundancy_group_id")
    ): row
    for row in variant.get("component_response_rows", [])
  }
  return max(
    (abs(float(left[key]["failure_probability"]) - float(right[key]["failure_probability"]))
     for key in set(left) & set(right)),
    default=0.0,
  )


def render(report_path: Path, output_path: Path) -> None:
  report = json.loads(report_path.read_text(encoding="utf-8"))
  pairs = {str(pair["case_id"]): pair for pair in report["pairs"]}
  metrics = report["evaluation"]["metrics"]["paired"]
  decision = report["admission_decision"]
  fields = (
    ("Component-load effect scale", "effect_scale", "viridis"),
    ("Maximum rod-cut margin", "rod_cut_margin", "plasma"),
    ("Max response probability delta", "response_probability_delta", "magma"),
  )
  figure, axes = plt.subplots(3, 6, figsize=(22, 11.8), constrained_layout=False)
  figure.subplots_adjust(left=0.08, right=0.93, top=0.86, bottom=0.08, wspace=0.30, hspace=0.52)
  figure.patch.set_facecolor("#f7f8fa")
  figure.suptitle(
    "P8 Continuous-Rod Component Load Admission",
    x=0.04,
    y=0.985,
    ha="left",
    fontsize=20,
    fontweight="bold",
    color="#17202d",
  )
  figure.text(
    0.04,
    0.952,
    f"192 paired cases  ·  {metrics['load_pair_count']} load/response rows  ·  "
    f"{report['evaluation']['metrics']['baseline']['unique_redundancy_group_count']} redundancy groups  ·  "
    f"{metrics['changed_load_effect_count']} load effect shifts  ·  "
    f"{metrics['changed_response_probability_count']} response probability shifts",
    ha="left",
    fontsize=10.5,
    color="#56616f",
  )
  figure.text(
    0.96,
    0.956,
    str(decision["component_load_admission"]).upper(),
    ha="right",
    va="center",
    fontsize=12,
    fontweight="bold",
    color="#17804c" if decision["component_load_admission"] == "passed" else "#b54708",
    bbox={"boxstyle": "round,pad=0.35", "facecolor": "#eef8f1", "edgecolor": "#69b889"},
  )
  matrices: dict[tuple[int, str], np.ndarray] = {}
  for row_index, (_, field, _) in enumerate(fields):
    for direction in DIRECTIONS:
      matrix = np.zeros((len(STANDOFFS), len(HEADINGS)), dtype=float)
      for y_index, standoff in enumerate(STANDOFFS):
        for x_index, heading in enumerate(HEADINGS):
          case_id = (
            f"continuous_rod:{direction}:standoff_{str(standoff).replace('.', 'p')}m:"
            f"heading_{int(heading)}"
          )
          pair = pairs.get(case_id)
          if pair is None:
            continue
          if field == "response_probability_delta":
            matrix[y_index, x_index] = _response_probability_delta(
              pair["baseline_event"], pair["decoupled_event"]
            )
          else:
            matrix[y_index, x_index] = _load_value(pair["baseline_event"], field)
      matrices[(row_index, direction)] = matrix

  for row_index, (label, field, cmap) in enumerate(fields):
    row_maximum = max(
      float(matrices[(row_index, direction)].max()) for direction in DIRECTIONS
    )
    for column_index, direction in enumerate(DIRECTIONS):
      matrix = matrices[(row_index, direction)]
      axis = axes[row_index, column_index]
      image = axis.imshow(
        matrix,
        cmap=cmap,
        aspect="auto",
        interpolation="nearest",
        vmin=0.0,
        vmax=row_maximum or 1.0,
      )
      axis.set_title(direction.upper(), fontsize=11, fontweight="bold", color="#17202d")
      axis.set_xticks(range(len(HEADINGS)), [str(int(value)) for value in HEADINGS], fontsize=7)
      axis.set_yticks(range(len(STANDOFFS)), [str(value) for value in STANDOFFS], fontsize=7)
      axis.set_xlabel("heading (deg)", fontsize=8)
      axis.set_ylabel("standoff (m)", fontsize=8)
      for y_index in range(matrix.shape[0]):
        for x_index in range(matrix.shape[1]):
          value = matrix[y_index, x_index]
          if value <= 0.0:
            continue
          color = "white" if value > 0.36 * float(row_maximum or 1.0) else "#17202d"
          format_value = ".2f" if field != "response_probability_delta" else ".3g"
          axis.text(
            x_index,
            y_index,
            format(value, format_value),
            ha="center",
            va="center",
            fontsize=7,
            color=color,
          )
      if column_index == 0:
        axis.text(
          -0.30,
          0.5,
          label,
          transform=axis.transAxes,
          rotation=90,
          va="center",
          ha="center",
          fontsize=10,
          fontweight="bold",
          color="#17202d",
        )
    colorbar = figure.colorbar(image, ax=axes[row_index, :], fraction=0.018, pad=0.02)
    colorbar.ax.tick_params(labelsize=7)
  figure.text(
    0.04,
    0.018,
    "Baseline: curve floor 0.05 / final bound 0.05. Variant: curve floor 0.05 / final bound 0.00. "
    "Topology remains fixed; only final-bound-driven load and response state changes are shown.",
    fontsize=8.5,
    color="#56616f",
  )
  output_path.parent.mkdir(parents=True, exist_ok=True)
  figure.savefig(output_path, dpi=180, facecolor=figure.get_facecolor())
  plt.close(figure)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--report", type=Path, required=True)
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()
  render(args.report, args.output)
  print(args.output)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
