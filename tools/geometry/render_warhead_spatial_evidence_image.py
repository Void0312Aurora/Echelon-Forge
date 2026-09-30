#!/usr/bin/env python3
"""Render the retained warhead spatial packet as a deterministic PNG figure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET = (
  REPO_ROOT
  / "docs"
  / "systems"
  / "effects"
  / "reviews"
  / "warhead_spatial_angular_field_admission_20260914"
  / "review_packets"
  / "warhead_spatial_angular_field_admission_20260914.json"
)
DEFAULT_OUTPUT = DEFAULT_PACKET.parent.parent / "warhead-spatial-evidence.png"
DIRECTIONS = ("front", "back", "right", "left", "up", "down")
HEADINGS = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
STANDOFFS = (0.5, 2.0, 6.0, 10.0)
FAMILIES = ("blast_fragmentation", "continuous_rod")


def _matrix(rows: list[dict], family: str, standoff: float, field: str) -> np.ndarray:
  lookup = {
    (str(row["direction"]), float(row["detonation_attitude_deg"][0])): float(row["event"][field])
    for row in rows
    if str(row["warhead_family"]) == family and abs(float(row["standoff_m"]) - standoff) <= 1.0e-9
  }
  return np.asarray(
    [[lookup[(direction, heading)] for heading in HEADINGS] for direction in DIRECTIONS],
    dtype=float,
  )


def _annotate_heatmap(ax: plt.Axes, matrix: np.ndarray, *, cmap, vmin: float, vmax: float) -> None:
  image = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
  ax.set_xticks(range(len(HEADINGS)), [f"{int(value)}°" for value in HEADINGS], fontsize=7)
  ax.set_yticks(range(len(DIRECTIONS)), DIRECTIONS, fontsize=8)
  ax.set_xlabel("heading", fontsize=8, labelpad=2)
  ax.set_ylabel("direction", fontsize=8, labelpad=2)
  ax.tick_params(length=0, pad=2)
  for row_index in range(matrix.shape[0]):
    for column_index in range(matrix.shape[1]):
      value = matrix[row_index, column_index]
      normalized = (value - vmin) / (vmax - vmin or 1.0)
      color = "white" if normalized > 0.55 else "#15202b"
      ax.text(column_index, row_index, f"{value:.2f}", ha="center", va="center", fontsize=6.5, color=color)
  for spine in ax.spines.values():
    spine.set_linewidth(0.6)
    spine.set_color("#7f8b96")
  return image


def render(packet_path: Path, output_path: Path) -> None:
  packet = json.loads(packet_path.read_text(encoding="utf-8"))
  rows = list(packet["rows"])
  effect_matrices = [
    (family, standoff, _matrix(rows, family, standoff, "spatial_projection_effect_scale"))
    for family in FAMILIES
    for standoff in STANDOFFS
  ]
  angular_matrices = [
    (standoff, _matrix(rows, "blast_fragmentation", standoff, "fragment_angular_density"))
    for standoff in STANDOFFS
  ]
  effect_values = np.concatenate([matrix.ravel() for _, _, matrix in effect_matrices])
  angular_values = np.concatenate([matrix.ravel() for _, matrix in angular_matrices])
  metrics = packet["metrics"]
  decision = packet["admission_decision"]

  plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
  })
  figure = plt.figure(figsize=(16, 17.5), dpi=180, constrained_layout=False)
  grid = figure.add_gridspec(
    nrows=6,
    ncols=4,
    height_ratios=(0.55, 2.25, 2.25, 1.35, 1.0, 0.35),
    hspace=0.85,
    wspace=0.52,
  )
  figure.text(
    0.04,
    0.975,
    "Warhead spatial evidence",
    fontsize=22,
    fontweight="bold",
    va="top",
    color="#15202b",
  )
  figure.text(
    0.04,
    0.948,
    "384 rows  ·  six directions  ·  four standoffs  ·  eight headings",
    fontsize=10,
    color="#56616d",
  )
  figure.text(
    0.96,
    0.965,
    f"fragmentation angular admission: {decision['fragmentation_angular_field_admission'].upper()}\n"
    f"overall spatial-field admission: {decision['warhead_spatial_field_admission'].upper()}",
    fontsize=10,
    ha="right",
    va="top",
    color="#16834b" if decision["fragmentation_angular_field_admission"] == "passed" else "#b54708",
  )

  effect_min = float(effect_values.min())
  effect_max = float(effect_values.max())
  effect_axes = []
  for index, (family, standoff, matrix) in enumerate(effect_matrices):
    row_index = 1 + index // 4
    column_index = index % 4
    ax = figure.add_subplot(grid[row_index, column_index])
    effect_axes.append(ax)
    image = _annotate_heatmap(ax, matrix, cmap="Blues" if family == "blast_fragmentation" else "Oranges", vmin=effect_min, vmax=effect_max)
    ax.set_title(f"{family.replace('_', ' ')} · {standoff:g} m", fontsize=9, pad=5)
  effect_cbar = figure.colorbar(image, ax=effect_axes, fraction=0.018, pad=0.025, aspect=28)
  effect_cbar.set_label("projected effect scale", fontsize=9)
  effect_cbar.ax.tick_params(labelsize=8)

  angular_min = float(angular_values.min())
  angular_max = float(angular_values.max())
  angular_axes = []
  for index, (standoff, matrix) in enumerate(angular_matrices):
    ax = figure.add_subplot(grid[3, index])
    angular_axes.append(ax)
    angular_image = _annotate_heatmap(ax, matrix, cmap="YlGn", vmin=angular_min, vmax=angular_max)
    ax.set_title(f"blast fragmentation · {standoff:g} m", fontsize=9, pad=5)
  angular_cbar = figure.colorbar(angular_image, ax=angular_axes, fraction=0.018, pad=0.025, aspect=28)
  angular_cbar.set_label("fragment angular density", fontsize=9)
  angular_cbar.ax.tick_params(labelsize=8)

  diagnostic_ax = figure.add_subplot(grid[4, :])
  diagnostic_ax.set_title("Admission and residuals", loc="left", fontsize=11, fontweight="bold", pad=3, color="#15202b")
  diagnostics = [
    ("trace valid", int(metrics["trace_valid_count"]), "#42a967"),
    ("closure failures", int(metrics["post_closure_failure_count"] + metrics["preclamp_decomposition_failure_count"] + metrics["candidate_aggregate_mismatch_count"] + metrics["flag_closure_failure_count"]), "#42a967"),
    ("rod baseline Δ", int(packet["continuous_rod_baseline_regression"]["mismatch_count"]), "#42a967"),
    ("sign residuals", int(metrics["orientation_sign_collapse_count"]), "#d95f02"),
    ("axial residuals", int(metrics["axial_orientation_sign_collapse_count"]), "#d95f02"),
  ]
  diagnostic_ax.set_xlim(-0.15, len(diagnostics) - 0.35)
  diagnostic_ax.set_ylim(0, max(1, int(metrics["row_count"]) * 1.15))
  diagnostic_ax.set_xticks(range(len(diagnostics)), [label for label, _, _ in diagnostics], fontsize=8)
  diagnostic_ax.set_ylabel("count", fontsize=8)
  diagnostic_ax.grid(axis="y", color="#d8dee5", linewidth=0.6)
  diagnostic_ax.bar(range(len(diagnostics)), [value for _, value, _ in diagnostics], color=[color for _, _, color in diagnostics], width=0.58)
  for index, (_, value, _) in enumerate(diagnostics):
    diagnostic_ax.text(index, max(3, value + 5), str(value), ha="center", va="bottom", fontsize=9, color="#15202b")
  diagnostic_ax.spines[["top", "right"]].set_visible(False)
  diagnostic_ax.spines[["left", "bottom"]].set_color("#7f8b96")

  figure.text(
    0.04,
    0.018,
    "Front/back axial sign collapse is 0 for fragmentation; the retained non-axial residuals are equatorial geometry. "
    "Overall admission remains held by the continuous-rod ring-band geometry boundary.",
    fontsize=8.5,
    color="#56616d",
  )
  output_path.parent.mkdir(parents=True, exist_ok=True)
  figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
  plt.close(figure)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
  args = parser.parse_args()
  render(args.packet, args.output)
  print(args.output)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
