#!/usr/bin/env python3
"""Render human-readable P11 terminal-track memory sensitivity evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = (
  REPO_ROOT
  / "artifacts/kill_chain/20260915/raw_review_packets/kill_chain_p11_terminal_track_sensitivity_20260915"
  / "kill_chain_p11_terminal_track_sensitivity_20260915.json"
)
DEFAULT_OUTPUT = DEFAULT_REPORT.with_name(
  "kill_chain_p11_terminal_track_sensitivity_20260915_heatmap.png"
)
DEFAULT_MANIFEST = DEFAULT_REPORT.with_name(
  "kill_chain_p11_terminal_track_sensitivity_20260915_manifest.json"
)
STATE_VALUE = {"outside_no_load": 0, "in_radius_fuze_blocked": 1, "complete_effect_chain": 2}
STATE_LABEL = {0: "O", 1: "F", 2: "C"}


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def render(report: dict[str, Any], output: Path) -> None:
  cells = list(report.get("cells", []) or [])
  timeouts = sorted({float(cell["requested_memory_timeout_s"]) for cell in cells})
  case_ids = sorted(
    {str(cell["case_id"]) for cell in cells},
    key=lambda value: (0 if value.endswith("m60deg") else 1, value),
  )
  index = {
    (str(cell["case_id"]), float(cell["requested_memory_timeout_s"])): cell
    for cell in cells
  }
  state_matrix = np.zeros((len(case_ids), len(timeouts)), dtype=float)
  distance_matrix = np.full((len(case_ids), len(timeouts)), np.nan, dtype=float)
  for row_idx, case_id in enumerate(case_ids):
    for col_idx, timeout in enumerate(timeouts):
      cell = index[(case_id, timeout)]
      state_matrix[row_idx, col_idx] = STATE_VALUE.get(str(cell["state"]), 0)
      distance = cell.get("nearest_miss_distance_min_m")
      if distance is not None:
        distance_matrix[row_idx, col_idx] = float(distance)

  cmap = ListedColormap(["#d9d9d9", "#f2c14e", "#2a9d8f"])
  fig, axes = plt.subplots(
    nrows=1,
    ncols=2,
    figsize=(15, 6.8),
    gridspec_kw={"width_ratios": [1.15, 1.7]},
  )
  fig.subplots_adjust(left=0.08, right=0.98, top=0.80, bottom=0.24, wspace=0.28)

  heatmap = axes[0].imshow(
    state_matrix,
    cmap=cmap,
    vmin=0,
    vmax=2,
    aspect="auto",
    interpolation="nearest",
  )
  del heatmap
  axes[0].set_xticks(range(len(timeouts)), [f"{value:g}" for value in timeouts])
  axes[0].set_yticks(
    range(len(case_ids)),
    ["−60° mild maneuver", "+60° mild maneuver"],
  )
  axes[0].set_xlabel("track_break_time_s (s)")
  axes[0].set_ylabel("case")
  axes[0].set_title("Chain state")
  for row_idx, case_id in enumerate(case_ids):
    for col_idx, timeout in enumerate(timeouts):
      cell = index[(case_id, timeout)]
      value = int(state_matrix[row_idx, col_idx])
      distance = cell.get("nearest_miss_distance_min_m")
      label = STATE_LABEL[value]
      if distance is not None:
        label += f"\n{float(distance):.2f} m"
      axes[0].text(
        col_idx,
        row_idx,
        label,
        ha="center",
        va="center",
        color="white" if value == 2 else "black",
        fontsize=8,
        fontweight="bold" if value == 1 else "normal",
      )

  line_colors = ("#264653", "#e76f51")
  distance_axis = axes[1]
  for row_idx, case_id in enumerate(case_ids):
    distance_axis.plot(
      timeouts,
      distance_matrix[row_idx],
      marker="o",
      linewidth=2.0,
      color=line_colors[row_idx % len(line_colors)],
      label="−60°" if row_idx == 0 else "+60°",
    )
  distance_axis.axhline(
    15.0,
    color="#6c757d",
    linestyle="--",
    linewidth=1.2,
    label="R_fuze = 15 m",
  )
  distance_axis.set_xticks(timeouts, [f"{value:g}" for value in timeouts])
  distance_axis.set_xlabel("track_break_time_s (s)")
  distance_axis.set_ylabel("nearest distance (m)")
  distance_axis.set_title("Nearest-distance response")
  distance_axis.grid(axis="y", alpha=0.25)
  distance_axis.legend(frameon=False, loc="upper right")

  counts = report["counts"]
  evaluation = report["evaluation"]
  fig.suptitle(
    "P11 Terminal-Track Memory Sensitivity\n"
    f"Residual explained {'PASS' if evaluation['residual_explanation_ready'] else 'HELD'} · "
    f"{counts['run_count']} runs / {counts['stable_cell_count']} stable cells · "
    "default remains 0.75 s",
    fontsize=15,
  )
  fig.legend(
    handles=[
      Patch(facecolor="#2a9d8f", label="C: complete effect chain"),
      Patch(facecolor="#f2c14e", label="F: in R_fuze, fuze blocked"),
      Patch(facecolor="#d9d9d9", label="O: outside, no load"),
      Line2D([0], [0], color="#6c757d", linestyle="--", label="R_fuze = 15 m"),
    ],
    loc="lower center",
    bbox_to_anchor=(0.5, 0.025),
    ncol=4,
    frameon=False,
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
    manifest.setdefault("artifacts", {})["heatmap_png"] = {
      "path": str(args.output.resolve().relative_to(REPO_ROOT)),
      "sha256": _sha256(args.output),
      "bytes": args.output.stat().st_size,
    }
    args.manifest.write_text(
      json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
      encoding="utf-8",
    )
  print(json.dumps({"output": str(args.output.resolve()), "bytes": args.output.stat().st_size}))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
