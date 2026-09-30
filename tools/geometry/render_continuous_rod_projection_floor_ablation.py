#!/usr/bin/env python3
"""Render the P7 projection-floor ablation as a static PNG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
  REPO_ROOT
  / "docs"
  / "systems"
  / "effects"
  / "reviews"
  / "continuous_rod_projection_floor_ablation_20260914"
  / "review_packets"
  / "continuous_rod_projection_floor_ablation_20260914.json"
)
DEFAULT_OUTPUT_PATH = REPORT_PATH.parents[1] / "continuous-rod-projection-floor-ablation.png"
DIRECTIONS = ("front", "back", "right", "left", "up", "down")
STANDOFFS_M = (0.5, 2.0, 6.0, 10.0)
HEADINGS_DEG = (0, 45, 90, 135, 180, 225, 270, 315)


def _matrix(pairs: list[dict[str, Any]], direction: str, field: str) -> np.ndarray:
  indexed = {
    (str(pair["direction"]), float(pair["standoff_m"]), int(pair["heading_deg"])): pair
    for pair in pairs
  }
  return np.asarray(
    [
      [
        float(indexed[(direction, standoff, heading)]["projection"][field])
        for heading in HEADINGS_DEG
      ]
      for standoff in STANDOFFS_M
    ],
    dtype=float,
  )


def _style_axis(ax: plt.Axes, *, show_y_label: bool, show_x_label: bool) -> None:
  ax.set_xticks(range(len(HEADINGS_DEG)))
  ax.set_xticklabels([str(value) for value in HEADINGS_DEG], fontsize=7)
  ax.set_yticks(range(len(STANDOFFS_M)))
  ax.set_yticklabels([f"{value:g}" for value in STANDOFFS_M], fontsize=8)
  ax.set_xticks(np.arange(-0.5, len(HEADINGS_DEG), 1), minor=True)
  ax.set_yticks(np.arange(-0.5, len(STANDOFFS_M), 1), minor=True)
  ax.grid(which="minor", color="white", linewidth=0.8, alpha=0.72)
  ax.tick_params(which="minor", bottom=False, left=False)
  if show_y_label:
    ax.set_ylabel("standoff from\nenvelope face (m)", fontsize=8)
  if show_x_label:
    ax.set_xlabel("warhead heading (deg)", fontsize=8)


def _annotate(ax: plt.Axes, matrix: np.ndarray, *, formatter: Any, threshold: float) -> None:
  for row_index in range(matrix.shape[0]):
    for column_index in range(matrix.shape[1]):
      value = float(matrix[row_index, column_index])
      ax.text(
        column_index,
        row_index,
        formatter(value),
        ha="center",
        va="center",
        fontsize=6.7,
        color="#17212b" if value < threshold else "white",
        fontweight="semibold",
      )


def render(report_path: Path, output_path: Path) -> None:
  report = json.loads(report_path.read_text(encoding="utf-8"))
  pairs = list(report["pairs"])
  metrics = report["evaluation"]["metrics"]
  decision = report["admission_decision"]
  is_decoupled = "p7_1_curve_minimum_separation" in decision
  decision_label = decision.get(
    "p7_1_curve_minimum_separation",
    decision.get("p7_projection_floor_clamp_admission", "held"),
  )
  field_map = {
    "baseline_effect_scale": ("Current min bound = 0.05", "viridis"),
    "ablated_effect_scale": ("Ablated min bound = 0.00", "viridis"),
    "effect_scale_delta": ("Baseline − ablated effect", "magma"),
  }
  figure, axes = plt.subplots(3, 6, figsize=(22, 11.8), constrained_layout=False)
  figure.patch.set_facecolor("#f7f8fa")
  figure.suptitle(
    (
      "P7.1 Continuous-Rod Curve-Floor / Minimum-Bound Decoupling"
      if is_decoupled
      else "P7 Continuous-Rod Projection Minimum-Bound Ablation"
    ),
    x=0.04,
    y=0.975,
    ha="left",
    fontsize=19,
    fontweight="bold",
    color="#15202b",
  )
  figure.text(
    0.04,
    0.937,
    (
      f"{metrics['pair_count']} paired cases  ·  {metrics['baseline_clamped_count']} baseline clamp rows  ·  "
      f"{metrics['non_clamped_effect_shift_count']} non-clamped rows shifted  ·  "
      f"component response probability shifts {metrics['component_response_probability_shift_count']}"
    ),
    fontsize=10.5,
    color="#425466",
  )
  figure.text(
    0.96,
    0.956,
    str(decision_label).upper(),
    ha="right",
    va="center",
    fontsize=12,
    fontweight="bold",
    color="#9a3412",
    bbox={"boxstyle": "round,pad=0.38", "facecolor": "#fff0e6", "edgecolor": "#e7a979"},
  )
  for column, direction in enumerate(DIRECTIONS):
    for row_index, field in enumerate(field_map):
      matrix = _matrix(pairs, direction, field)
      vmax = 0.85 if row_index < 2 else max(float(matrix.max()), 1.0e-9)
      axes[row_index, column].imshow(
        matrix,
        cmap=field_map[field][1],
        vmin=0.0,
        vmax=vmax,
        aspect="auto",
      )
      if row_index == 0:
        axes[row_index, column].set_title(direction.upper(), fontsize=10.5, fontweight="bold", pad=7)
      _annotate(
        axes[row_index, column],
        matrix,
        formatter=(lambda value: f"{value:.2f}" if value > 0.0 else "—"),
        threshold=0.42 * vmax,
      )
      _style_axis(
        axes[row_index, column],
        show_y_label=column == 0,
        show_x_label=row_index == 2,
      )
  figure.text(0.012, 0.775, "BASELINE\nEFFECT", rotation=90, va="center", fontsize=9, fontweight="bold")
  figure.text(0.012, 0.505, "ABLATION\nEFFECT", rotation=90, va="center", fontsize=9, fontweight="bold")
  figure.text(0.012, 0.235, "EFFECT\nDELTA", rotation=90, va="center", fontsize=9, fontweight="bold")
  figure.text(
    0.04,
    0.018,
    (
      (
        "Same geometry, orientation, seed, and ring-band sampling in both variants. "
        "The curve floor is fixed at 0.05 while only the final lower bound is ablated; "
        "non-clamped cells therefore remain stable."
        if is_decoupled
        else "Same geometry, orientation, seed, and ring-band sampling in both variants. "
        "The ablation changes the current curve intercept as well as the final lower bound; "
        "24 10 m rows are clamped at 0.05, so P7 remains HELD until these roles are separated."
      )
    ),
    fontsize=8.5,
    color="#56616f",
  )
  figure.subplots_adjust(left=0.055, right=0.985, top=0.90, bottom=0.085, wspace=0.23, hspace=0.35)
  output_path.parent.mkdir(parents=True, exist_ok=True)
  figure.savefig(output_path, dpi=180, facecolor=figure.get_facecolor())
  plt.close(figure)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--report", type=Path, default=REPORT_PATH)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
  args = parser.parse_args()
  render(args.report, args.output)
  print(args.output)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
