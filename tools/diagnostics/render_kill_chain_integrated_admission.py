#!/usr/bin/env python3
"""Render human-readable P11 integrated kill-chain admission heatmaps."""

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


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = (
  REPO_ROOT
  / "artifacts/kill_chain/20260915/raw_review_packets/kill_chain_integrated_admission_20260915/"
  "kill_chain_integrated_admission_20260915.json"
)
DEFAULT_OUTPUT = DEFAULT_REPORT.with_name(
  "kill_chain_integrated_admission_20260915_heatmaps.png"
)
DEFAULT_MANIFEST = DEFAULT_REPORT.with_name(
  "kill_chain_integrated_admission_20260915_manifest.json"
)


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _state_value(cell: dict[str, Any]) -> int:
  states = set(cell.get("chain_states", []) or [])
  if states == {"complete_effect_chain"}:
    return 2
  if states == {"in_radius_fuze_blocked"}:
    return 1
  return 0


def _state_label(value: int) -> str:
  return {0: "O", 1: "F", 2: "C"}.get(int(value), "?")


def _matrix(
  cells: list[dict[str, Any]],
  *,
  layer: str,
) -> tuple[list[float], list[float], np.ndarray, dict[tuple[float, float], dict[str, Any]]]:
  selected = [cell for cell in cells if cell["target_motion_layer"] == layer]
  ranges = sorted({float(cell["range_km"]) for cell in selected})
  bearings = sorted({float(cell["bearing_deg"]) for cell in selected})
  index = {(float(cell["range_km"]), float(cell["bearing_deg"])): cell for cell in selected}
  matrix = np.zeros((len(ranges), len(bearings)), dtype=float)
  for row_idx, range_km in enumerate(ranges):
    for col_idx, bearing_deg in enumerate(bearings):
      matrix[row_idx, col_idx] = _state_value(index[(range_km, bearing_deg)])
  return ranges, bearings, matrix, index


def render(report: dict[str, Any], output: Path) -> None:
  cells = list(report.get("cells", []) or [])
  layers = [
    layer for layer in ("nonmaneuvering_constant_velocity", "mild_maneuver")
    if any(cell["target_motion_layer"] == layer for cell in cells)
  ]
  cmap = ListedColormap(["#d9d9d9", "#f2c14e", "#2a9d8f"])
  fig, axes = plt.subplots(
    nrows=1,
    ncols=max(2, len(layers)),
    figsize=(18, 7),
  )
  fig.subplots_adjust(left=0.06, right=0.98, top=0.80, bottom=0.27, wspace=0.18)
  axes = np.atleast_1d(axes)
  for axis_idx, layer in enumerate(layers):
    ax = axes[axis_idx]
    ranges, bearings, matrix, index = _matrix(cells, layer=layer)
    image = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=2, aspect="auto")
    ax.set_xticks(range(len(bearings)), [f"{value:+g}" for value in bearings])
    ax.set_yticks(range(len(ranges)), [f"{value:g}" for value in ranges])
    ax.set_xlabel("Signed bearing (deg)")
    ax.set_ylabel("Initial range (km)")
    title = "CV target" if layer.startswith("nonmaneuvering") else "Mild maneuver"
    ax.set_title(title)
    for row_idx, range_km in enumerate(ranges):
      for col_idx, bearing_deg in enumerate(bearings):
        cell = index[(range_km, bearing_deg)]
        value = int(matrix[row_idx, col_idx])
        residual = []
        if cell["legacy_negative_control_alert"]:
          residual.append("O!")
        if cell["in_radius_fuze_blocked"]:
          residual.append("T!")
        label = _state_label(value)
        if residual:
          label += "\n" + "/".join(residual)
        text_color = "white" if value == 2 else "black"
        ax.text(
          col_idx,
          row_idx,
          label,
          ha="center",
          va="center",
          color=text_color,
          fontsize=9,
          fontweight="bold" if residual else "normal",
        )
  for axis in axes[len(layers):]:
    axis.axis("off")
  from matplotlib.patches import Patch

  legend = [
    Patch(facecolor="#2a9d8f", label="C: complete effect chain"),
    Patch(facecolor="#f2c14e", label="F: in R_fuze, fuze blocked"),
    Patch(facecolor="#d9d9d9", label="O: outside, no load"),
    Patch(facecolor="none", edgecolor="black", label="O!: accepted O expectation alert"),
    Patch(facecolor="none", edgecolor="black", label="T!: terminal-track residual"),
  ]
  fig.legend(
    handles=legend,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.015),
    ncol=3,
    frameon=False,
  )
  counts = report["counts"]
  evaluation = report["evaluation"]
  fig.suptitle(
    "P11 Integrated Kill-Chain Admission\n"
    f"Structure {'PASS' if evaluation['p11_structural_admission_passed'] else 'HELD'} · "
    f"Accepted N/O envelope "
    f"{'PASS' if evaluation['accepted_n_o_expectation_envelope_passed'] else 'HELD'} · "
    f"Terminal track {'PASS' if evaluation['terminal_track_contract_passed'] else 'HELD'} · "
    f"{counts['run_count']} runs / {counts['cell_count']} cells",
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
  print(json.dumps({"output": str(args.output.resolve()), "bytes": args.output.stat().st_size}))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
