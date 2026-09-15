#!/usr/bin/env python3
"""Render the P10 APN null-band follow-up figure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from matplotlib.colors import SymLogNorm


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = (
  REPO_ROOT
  / "docs/systems/weapons/reviews/kill_chain_p10_apn_null_band_followup_20260915"
  / "review_packets/kill_chain_p10_apn_null_band_followup_20260915.json"
)
DEFAULT_OUTPUT = DEFAULT_REPORT.with_name(
  "kill_chain_p10_apn_null_band_followup_20260915_figure.png"
)


def _cell_lookup(report: dict[str, Any]) -> dict[tuple[float, float], dict[str, Any]]:
  return {
    (float(row["range_km"]), float(row["apn_gain"])): dict(row)
    for row in report["cells"]
  }


def _delta_label(value: float) -> str:
  return f"{value:+.1e}" if abs(value) < 0.01 else f"{value:+.2f}"


def render(report: dict[str, Any], output: Path) -> None:
  ranges = [float(value) for value in report["matrix"]["ranges_km"]]
  gains = [float(value) for value in report["matrix"]["apn_gains"]]
  nonzero_gains = [gain for gain in gains if gain > 0.0]
  lookup = _cell_lookup(report)
  delta = np.array(
    [
      [lookup[(range_km, gain)]["mean_nearest_distance_delta_vs_apn0_m"] for range_km in ranges]
      for gain in nonzero_gains
    ],
    dtype=float,
  )
  max_abs = max(float(np.max(np.abs(delta))), 1.0e-6)

  fig, axes = plt.subplots(2, 2, figsize=(16, 10))
  fig.subplots_adjust(left=0.07, right=0.97, top=0.88, bottom=0.09, wspace=0.24, hspace=0.34)

  heat = axes[0, 0]
  image = heat.imshow(
    delta,
    cmap="coolwarm",
    norm=SymLogNorm(linthresh=1.0e-3, vmin=-max_abs, vmax=max_abs, base=10),
    aspect="auto",
  )
  heat.set_title("Nearest-distance response")
  heat.set_xticks(range(len(ranges)), [f"{value:g}" for value in ranges])
  heat.set_yticks(range(len(nonzero_gains)), [f"{value:g}" for value in nonzero_gains])
  heat.set_xlabel("Initial range (km)")
  heat.set_ylabel("APN gain")
  for y_idx in range(delta.shape[0]):
    for x_idx in range(delta.shape[1]):
      value = float(delta[y_idx, x_idx])
      heat.text(x_idx, y_idx, _delta_label(value), ha="center", va="center", fontsize=9)
  fig.colorbar(image, ax=heat, label="Mean Δ nearest distance vs APN=0 (m)")

  baseline = axes[0, 1]
  baseline_values = [lookup[(range_km, 0.0)]["mean_nearest_distance_m"] for range_km in ranges]
  baseline.plot(ranges, baseline_values, marker="o", color="tab:blue", label="APN=0 baseline")
  baseline.axhline(0.01, color="tab:gray", linestyle="--", linewidth=1.0, label="1 cm floor gate")
  baseline.axhline(15.0, color="tab:red", linestyle=":", linewidth=1.0, label="R_fuze = 15 m")
  baseline.set_yscale("log")
  baseline.set_title("Pure-PN closest-approach floor")
  baseline.set_xlabel("Initial range (km)")
  baseline.set_ylabel("Mean nearest distance (m, log scale)")
  baseline.grid(alpha=0.25)
  baseline.legend(fontsize=9)

  phase = axes[1, 0]
  selected_gain = 0.125
  nearest_times = [lookup[(range_km, selected_gain)]["mean_nearest_approach_time_s"] for range_km in ranges]
  convergence_times = [lookup[(range_km, selected_gain)]["mean_estimator_convergence_time_s"] for range_km in ranges]
  phase.plot(ranges, nearest_times, marker="o", label="Nearest approach")
  phase.plot(ranges, convergence_times, marker="s", label="CVA converged")
  phase.axhline(0.0, color="tab:gray", linewidth=1.0, label="Maneuver onset")
  phase.set_title("Phase timing at APN gain 0.125")
  phase.set_xlabel("Initial range (km)")
  phase.set_ylabel("Time since launch (s)")
  phase.grid(alpha=0.25)
  phase.legend(fontsize=9)

  command = axes[1, 1]
  pn_impulse = [lookup[(range_km, selected_gain)]["mean_pn_impulse_mps"] for range_km in ranges]
  apn_impulse = [lookup[(range_km, selected_gain)]["mean_apn_impulse_mps"] for range_km in ranges]
  apn_line = command.plot(
    ranges, apn_impulse, marker="s", color="tab:orange", label="APN |a| integral"
  )
  command.set_title("Command contributions remain active · dual scales")
  command.set_xlabel("Initial range (km)")
  command.set_ylabel("APN integrated |a| (m/s)", color="tab:orange")
  command.tick_params(axis="y", labelcolor="tab:orange")
  command.grid(alpha=0.25)
  pn_axis = command.twinx()
  pn_line = pn_axis.plot(
    ranges, pn_impulse, marker="o", color="tab:blue", label="PN |a| integral"
  )
  pn_axis.set_ylabel("PN integrated |a| (m/s)", color="tab:blue")
  pn_axis.tick_params(axis="y", labelcolor="tab:blue")
  lines = apn_line + pn_line
  command.legend(lines, [line.get_label() for line in lines], fontsize=9, loc="center right")

  explained = bool(report["evaluation"]["explained"])
  fig.suptitle(
    "P10 APN Null-Band Follow-up · Discussion #32\n"
    f"8 km mechanism {'explained' if explained else 'remains open'}: active APN over a near-zero PN miss-distance floor",
    fontsize=16,
  )
  output.parent.mkdir(parents=True, exist_ok=True)
  fig.savefig(output, dpi=180, bbox_inches="tight")
  plt.close(fig)


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
  args = parser.parse_args(argv)
  report = json.loads(args.report.read_text(encoding="utf-8"))
  render(report, args.output)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
