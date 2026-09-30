#!/usr/bin/env python3
"""Render the retained continuous-rod ring-band admission as a static PNG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
  REPO_ROOT
  / "docs"
  / "systems"
  / "effects"
  / "reviews"
  / "continuous_rod_ring_band_admission_20260914"
  / "review_packets"
  / "continuous_rod_ring_band_admission_20260914.json"
)
DEFAULT_OUTPUT_PATH = REPORT_PATH.parents[1] / "continuous-rod-ring-band-evidence.png"
DIRECTIONS = ("front", "back", "right", "left", "up", "down")
STANDOFFS_M = (0.5, 2.0, 6.0, 10.0)
HEADINGS_DEG = (0, 45, 90, 135, 180, 225, 270, 315)


def _matrix(rows: list[dict[str, Any]], direction: str, field: str) -> np.ndarray:
  indexed = {
    (
      str(row["direction"]),
      float(row["standoff_m"]),
      int(float(row["detonation_attitude_deg"][0])),
    ): row
    for row in rows
  }
  return np.asarray(
    [
      [float(indexed[(direction, standoff, heading)]["event"][field]) for heading in HEADINGS_DEG]
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


def _annotate(
  ax: plt.Axes,
  matrix: np.ndarray,
  formatter: Any,
  *,
  threshold: float,
  dark_on_high: bool = False,
) -> None:
  for row_index in range(matrix.shape[0]):
    for column_index in range(matrix.shape[1]):
      value = float(matrix[row_index, column_index])
      use_dark_text = value >= threshold if dark_on_high else value < threshold
      ax.text(
        column_index,
        row_index,
        formatter(value),
        ha="center",
        va="center",
        fontsize=6.8,
        color="#18212b" if use_dark_text else "white",
        fontweight="semibold",
      )


def render(report_path: Path, output_path: Path) -> None:
  report = json.loads(report_path.read_text(encoding="utf-8"))
  rows = list(report["rows"])
  decision = report["admission_decision"]
  metrics = report["geometry_evaluation"]["metrics"]
  convergence = report["sampling_convergence"]
  coverage_max = max(
    float(row["event"]["continuous_rod_angular_coverage_fraction"])
    for row in rows
  )
  effect_max = max(float(row["event"]["spatial_projection_effect_scale"]) for row in rows)

  figure, axes = plt.subplots(3, 6, figsize=(22, 11.8), constrained_layout=False)
  figure.patch.set_facecolor("#f7f8fa")
  figure.suptitle(
    "Continuous-Rod Expanding Ring-Band — Structural Admission Evidence",
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
      f"{metrics['intersection_count']} intersections / {metrics['row_count']} cases  ·  "
      f"720 azimuth × 5 polar rays  ·  ±6° band  ·  "
      f"convergence {str(convergence['status']).upper()}"
    ),
    fontsize=10.5,
    color="#425466",
  )
  figure.text(
    0.96,
    0.956,
    str(decision["continuous_rod_expanding_ring_band_admission"]).upper(),
    ha="right",
    va="center",
    fontsize=12,
    fontweight="bold",
    color="#0b6e4f",
    bbox={"boxstyle": "round,pad=0.38", "facecolor": "#dff4e8", "edgecolor": "#8fd0ad"},
  )

  for column, direction in enumerate(DIRECTIONS):
    intersection = _matrix(rows, direction, "continuous_rod_ring_band_intersection")
    coverage = _matrix(rows, direction, "continuous_rod_angular_coverage_fraction")
    effect = _matrix(rows, direction, "spatial_projection_effect_scale")

    axes[0, column].imshow(
      intersection,
      cmap=ListedColormap(["#eef1f4", "#087f5b"]),
      vmin=0.0,
      vmax=1.0,
      aspect="auto",
    )
    axes[0, column].set_title(direction.upper(), fontsize=10.5, fontweight="bold", pad=7)
    _annotate(
      axes[0, column],
      intersection,
      lambda value: "HIT" if value > 0.5 else "—",
      threshold=0.5,
    )
    _style_axis(axes[0, column], show_y_label=column == 0, show_x_label=False)

    axes[1, column].imshow(
      coverage,
      cmap="YlOrBr",
      vmin=0.0,
      vmax=coverage_max,
      aspect="auto",
    )
    _annotate(
      axes[1, column],
      coverage,
      lambda value: f"{100.0 * value:.1f}%" if value > 0.0 else "—",
      threshold=0.52 * coverage_max,
    )
    _style_axis(axes[1, column], show_y_label=column == 0, show_x_label=False)

    axes[2, column].imshow(
      effect,
      cmap="magma",
      vmin=0.0,
      vmax=effect_max,
      aspect="auto",
    )
    _annotate(
      axes[2, column],
      effect,
      lambda value: f"{value:.2f}" if value > 0.0 else "—",
      threshold=0.42 * effect_max,
      dark_on_high=True,
    )
    _style_axis(axes[2, column], show_y_label=column == 0, show_x_label=True)

  figure.text(0.012, 0.775, "GEOMETRY\nINTERSECTION", rotation=90, va="center", fontsize=9, fontweight="bold")
  figure.text(0.012, 0.505, "AZIMUTHAL\nCOVERAGE", rotation=90, va="center", fontsize=9, fontweight="bold")
  figure.text(0.012, 0.235, "EFFECT\nSCALE", rotation=90, va="center", fontsize=9, fontweight="bold")
  figure.text(
    0.04,
    0.018,
    (
      "Rows use face-referenced standoff, not target-center distance. "
      "Zero cells are geometric rejection, not a clamp. Synthetic structural evidence only; "
      "default-profile promotion, component-load admission, and integrated Pk remain unevaluated."
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
