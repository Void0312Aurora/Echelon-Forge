#!/usr/bin/env python3
"""Render human-readable P10 maneuver/APN admission heatmaps."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import SymLogNorm


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = (
  REPO_ROOT
  / "docs/systems/weapons/reviews/kill_chain_maneuver_apn_admission_20260915/"
  "review_packets/kill_chain_maneuver_apn_admission_20260915.json"
)
DEFAULT_OUTPUT = DEFAULT_REPORT.with_name(
  "kill_chain_maneuver_apn_admission_20260915_heatmaps.png"
)
DEFAULT_MANIFEST = DEFAULT_REPORT.with_name(
  "kill_chain_maneuver_apn_admission_20260915_manifest.json"
)


def _token(value: float) -> str:
  return f"{float(value):g}"


def _delta_label(value: float) -> str:
  magnitude = abs(value)
  if magnitude < 0.001:
    return f"{value:+.1e}"
  if magnitude < 0.1:
    return f"{value:+.3f}"
  return f"{value:+.1f}"


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def render(report: dict[str, Any], output: Path) -> None:
  clean_rows = list(report["clean_runs"])
  noisy_rows = list(report["noisy_runs"])
  ranges = [float(value) for value in report["matrix"]["clean"]["ranges_km"]]
  bearings = [float(value) for value in report["matrix"]["clean"]["bearings_deg"]]
  accelerations = [
    float(value)
    for value in report["matrix"]["clean"]["target_accelerations_x_mps2"]
  ]
  gains = [
    float(value) for value in report["matrix"]["clean"]["apn_gains"]
    if float(value) > 0.0
  ]
  lookup = {
    (
      float(row["range_km"]), float(row["bearing_deg"]),
      float(row["target_accel_x_mps2"]), float(row["apn_gain"]),
    ): float(row["nearest_distance_m"])
    for row in clean_rows
  }
  delta_values = [
    lookup[(range_km, bearing, acceleration, gain)]
    - lookup[(range_km, bearing, acceleration, 0.0)]
    for range_km in ranges
    for gain in gains
    for acceleration in accelerations
    for bearing in bearings
  ]
  max_abs_delta = max(abs(value) for value in delta_values)
  norm = SymLogNorm(
    linthresh=0.01,
    linscale=1.0,
    vmin=-max_abs_delta,
    vmax=max_abs_delta,
    base=10,
  )

  fig = plt.figure(figsize=(18, 15), constrained_layout=True)
  grid = fig.add_gridspec(
    nrows=len(ranges) + 1,
    ncols=len(gains),
    height_ratios=[1.0] * len(ranges) + [1.15],
  )
  image = None
  for row_idx, range_km in enumerate(ranges):
    for col_idx, gain in enumerate(gains):
      ax = fig.add_subplot(grid[row_idx, col_idx])
      matrix = np.array(
        [
          [
            lookup[(range_km, bearing, acceleration, gain)]
            - lookup[(range_km, bearing, acceleration, 0.0)]
            for bearing in bearings
          ]
          for acceleration in accelerations
        ],
        dtype=float,
      )
      image = ax.imshow(matrix, cmap="coolwarm", norm=norm, aspect="auto")
      ax.set_title(f"Range {range_km:g} km · APN gain {gain:g}")
      ax.set_xticks(range(len(bearings)), [_token(value) for value in bearings])
      ax.set_yticks(
        range(len(accelerations)), [_token(value) for value in accelerations]
      )
      ax.set_xlabel("Initial bearing (deg)")
      ax.set_ylabel("Target lateral acceleration x (m/s²)")
      for y_idx in range(matrix.shape[0]):
        for x_idx in range(matrix.shape[1]):
          value = float(matrix[y_idx, x_idx])
          color = "white" if abs(value) > max_abs_delta * 0.20 else "black"
          ax.text(
            x_idx, y_idx, _delta_label(value), ha="center", va="center",
            fontsize=8, color=color,
          )

  if image is not None:
    fig.colorbar(
      image,
      ax=[axis for axis in fig.axes],
      shrink=0.52,
      pad=0.012,
      label="Δ nearest distance vs APN gain 0 (m); negative improves",
    )

  noisy_ax = fig.add_subplot(grid[-1, :2])
  noisy_baseline = [row for row in noisy_rows if float(row["apn_gain"]) == 0.0]
  seeds = sorted({int(row["seed"]) for row in noisy_baseline})
  geometries = sorted(
    {
      (float(row["bearing_deg"]), float(row["target_accel_x_mps2"]))
      for row in noisy_baseline
    }
  )
  noisy_lookup = {
    (
      int(row["seed"]), float(row["bearing_deg"]),
      float(row["target_accel_x_mps2"]),
    ): float(row["acceleration_rmse_mps2"])
    for row in noisy_baseline
  }
  noisy_matrix = np.array(
    [
      [noisy_lookup[(seed, bearing, acceleration)] for seed in seeds]
      for bearing, acceleration in geometries
    ]
  )
  noisy_image = noisy_ax.imshow(noisy_matrix, cmap="magma", aspect="auto")
  noisy_ax.set_title("Noisy holdout acceleration RMSE · APN gain 0")
  noisy_ax.set_xticks(range(len(seeds)), [str(seed) for seed in seeds])
  noisy_ax.set_yticks(
    range(len(geometries)),
    [f"b={bearing:+g}°, ax={acceleration:+g}" for bearing, acceleration in geometries],
  )
  noisy_ax.set_xlabel("Seed")
  noisy_ax.set_ylabel("Mirrored maneuver geometry")
  for y_idx in range(noisy_matrix.shape[0]):
    for x_idx in range(noisy_matrix.shape[1]):
      noisy_ax.text(
        x_idx, y_idx, f"{noisy_matrix[y_idx, x_idx]:.1f}",
        ha="center", va="center", color="white", fontsize=9,
      )
  fig.colorbar(noisy_image, ax=noisy_ax, shrink=0.75, label="Acceleration RMSE (m/s²)")

  candidate_ax = fig.add_subplot(grid[-1, 2])
  candidates = list(report["clean_candidate_summary"])
  candidate_gains = [float(row["apn_gain"]) for row in candidates]
  worst = [float(row["worst_nearest_distance_m"]) for row in candidates]
  hit_count = [int(row["hit_count"]) for row in candidates]
  candidate_ax.plot(candidate_gains, worst, marker="o", label="Worst nearest distance")
  candidate_ax.axhline(15.0, color="gray", linewidth=1.0, linestyle="--", label="R_fuze = 15 m")
  candidate_ax.set_title("Stage-5 APN candidate trade-off")
  candidate_ax.set_xlabel("APN target-acceleration gain")
  candidate_ax.set_ylabel("Worst nearest distance (m)")
  candidate_ax.grid(alpha=0.25)
  hit_ax = candidate_ax.twinx()
  hit_ax.plot(candidate_gains, hit_count, marker="s", color="tab:green", label="Hit cells")
  hit_ax.set_ylabel("Clean cells within R_fuze")
  lines = candidate_ax.get_lines() + hit_ax.get_lines()
  labels = [line.get_label() for line in lines]
  candidate_ax.legend(lines, labels, loc="upper left", fontsize=8)
  for gain, value in zip(candidate_gains, worst):
    candidate_ax.annotate(
      f"{value:.1f} m", (gain, value), textcoords="offset points", xytext=(0, 6),
      ha="center", fontsize=8,
    )

  fig.suptitle(
    "P10 Maneuver / APN Admission Evidence\n"
    "Clean structural identifiability passes; noisy acceleration and APN promotion remain held",
    fontsize=16,
  )
  output.parent.mkdir(parents=True, exist_ok=True)
  fig.savefig(output, dpi=180, bbox_inches="tight")
  plt.close(fig)


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
  parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
  args = parser.parse_args(argv)
  report = json.loads(args.report.read_text(encoding="utf-8"))
  render(report, args.output)
  if args.manifest.exists():
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    manifest.setdefault("artifacts", {})["heatmaps_png"] = {
      "path": str(args.output.resolve().relative_to(REPO_ROOT)),
      "sha256": _sha256(args.output),
      "bytes": args.output.stat().st_size,
    }
    args.manifest.write_text(
      json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
      encoding="utf-8",
    )
  print(
    json.dumps(
      {
        "report": str(args.report.resolve()),
        "output": str(args.output.resolve()),
        "bytes": args.output.stat().st_size,
      }
    )
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
