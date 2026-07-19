#!/usr/bin/env python3
"""Render proxy-only heatmaps using independent variables as axes."""

from __future__ import annotations

import argparse
import json
import math
import sys
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from python.runtime_bootstrap import resolve_repo_path


SCHEMA_VERSION = "a2.target_geometry_proxy_independent_variable_heatmap.v1"
STATUS = "target_geometry_proxy_independent_variable_heatmap_rendered_20260615"
GENERATED_ON = "2026-06-15"
MATRIX_PROBE_PATH = Path(
  resolve_repo_path(
    "docs",
    "task",
    "air_combat",
    "a2_high_fidelity_damage_model",
    "missile_lethality_target_geometry",
    "review_packets",
    "f16c_20260611",
    "target_geometry_lethality_matrix_probe_20260614.json",
  )
)
DEFAULT_OUTPUT_DIR = Path(
  resolve_repo_path(
    "docs",
    "task",
    "air_combat",
    "a2_high_fidelity_damage_model",
    "missile_lethality_target_geometry",
    "review_packets",
    "f16c_20260611",
  )
)
WARHEAD_FAMILIES = ("blast_fragmentation", "continuous_rod")
ASPECT_ORDER = (
  "nose",
  "centerline",
  "left_beam",
  "right_beam",
  "aft_fuselage_engine",
  "tail_engine",
  "tail_aft_engine",
  "tail_right",
)
RANGE_BUCKET_ORDER = (
  "direct_component_center",
  "direct_structural_center",
  "direct_receiver_center",
  "direct_receiver_edge",
  "near_miss_7m",
  "near_miss_14m",
  "near_tail",
)


def _relative_path(path: Path) -> str:
  return str(path.resolve().relative_to(REPO_ROOT))


def _load_probe(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _mean(values: list[float]) -> float:
  return sum(values) / len(values) if values else math.nan


def _sorted_unique(values: set[str], preferred_order: tuple[str, ...]) -> list[str]:
  preferred = [value for value in preferred_order if value in values]
  rest = sorted(values - set(preferred))
  return preferred + rest


def _proxy_record(comparison: dict[str, Any]) -> dict[str, Any]:
  event = comparison["proxy_event"]
  local = [float(value) for value in comparison["local_point_m"]]
  velocity = [float(value) for value in comparison["missile_velocity_body_mps"]]
  return {
    "case_id": str(comparison["case_id"]),
    "warhead_family": str(comparison["warhead_family"]),
    "aspect": str(comparison["aspect"]),
    "range_bucket": str(comparison["range_bucket"]),
    "local_forward_m": local[0],
    "local_right_m": local[1],
    "local_up_m": local[2],
    "miss_distance_m": float(event["miss_distance_m"]),
    "missile_velocity_forward_mps": velocity[0],
    "missile_velocity_right_mps": velocity[1],
    "missile_velocity_up_mps": velocity[2],
    "closure_mps": float(event["closure_mps"]),
    "proxy_component_primary_name": str(event["component_primary_name"]) or "(none)",
    "proxy_component_primary_system": str(event["component_primary_system"]),
    "proxy_component_failure_probability": float(
      event["component_primary_row_failure_probability"]
    ),
    "proxy_component_primary_failure_probability": float(
      event["component_primary_row_failure_probability"]
    ),
    "proxy_component_primary_distance_m": float(
      event["component_primary_row_distance_m"]
    ),
    "proxy_component_primary_effect_scale": float(
      event["component_primary_row_effect_scale"]
    ),
    "proxy_event_max_component_failure_probability": float(
      event["component_failure_probability"]
    ),
    "proxy_event_max_component_failure_probability_component_name": str(
      event["component_max_failure_probability_component_name"]
    )
    or "(none)",
    "proxy_event_max_component_failure_probability_component_system": str(
      event["component_max_failure_probability_component_system"]
    ),
    "proxy_component_failure_probability_source": str(
      event["component_failure_probability_source"]
    ),
    "proxy_component_primary_integrity": float(
      event["component_primary_integrity"]
    ),
    "proxy_component_primary_rod_cut_margin": float(
      event["component_primary_mechanism_rod_cut_margin"]
    ),
    "proxy_component_primary_fragment_energy_j": float(
      event["component_primary_mechanism_fragment_energy_j"]
    ),
    "proxy_component_hit_count": int(event["component_hit_count"]),
    "proxy_component_failure_count": int(event["component_failure_count"]),
  }


def _records(probe: dict[str, Any]) -> list[dict[str, Any]]:
  return [_proxy_record(comparison) for comparison in probe["comparisons"]]


def _aspect_range_aggregate(
  records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
  aspects = _sorted_unique(
    {str(record["aspect"]) for record in records},
    ASPECT_ORDER,
  )
  ranges = _sorted_unique(
    {str(record["range_bucket"]) for record in records},
    RANGE_BUCKET_ORDER,
  )
  by_family: dict[str, dict[str, Any]] = {}
  for family in WARHEAD_FAMILIES:
    family_records = [
      record for record in records if str(record["warhead_family"]) == family
    ]
    cell_map: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in family_records:
      cell_map[(str(record["aspect"]), str(record["range_bucket"]))].append(record)
    cells: list[dict[str, Any]] = []
    matrix: list[list[float | None]] = []
    count_matrix: list[list[int]] = []
    for aspect in aspects:
      matrix_row: list[float | None] = []
      count_row: list[int] = []
      for range_bucket in ranges:
        rows = cell_map[(aspect, range_bucket)]
        probabilities = [
          float(row["proxy_component_failure_probability"]) for row in rows
        ]
        value = _mean(probabilities) if probabilities else None
        matrix_row.append(value)
        count_row.append(len(rows))
        cells.append(
          {
            "aspect": aspect,
            "range_bucket": range_bucket,
            "sample_count": len(rows),
            "mean_proxy_component_failure_probability": value,
            "case_ids": [str(row["case_id"]) for row in rows],
            "primary_components": sorted(
              {str(row["proxy_component_primary_name"]) for row in rows}
            ),
          }
        )
      matrix.append(matrix_row)
      count_matrix.append(count_row)
    by_family[family] = {
      "aspects": aspects,
      "range_buckets": ranges,
      "matrix": matrix,
      "count_matrix": count_matrix,
      "cells": cells,
    }
  return by_family


def build_report(probe: dict[str, Any]) -> dict[str, Any]:
  records = _records(probe)
  aspect_range = _aspect_range_aggregate(records)
  metrics = {
    "proxy_record_count": len(records),
    "warhead_family_count": len(WARHEAD_FAMILIES),
    "aspect_count": len({str(record["aspect"]) for record in records}),
    "range_bucket_count": len(
      {str(record["range_bucket"]) for record in records}
    ),
    "local_forward_unique_count": len(
      {float(record["local_forward_m"]) for record in records}
    ),
    "local_right_unique_count": len(
      {float(record["local_right_m"]) for record in records}
    ),
    "probability_source_values": sorted(
      {
        str(record["proxy_component_failure_probability_source"])
        for record in records
      }
    ),
  }
  return {
    "schema_version": SCHEMA_VERSION,
    "status": STATUS,
    "generated_on": GENERATED_ON,
    "source_probe_path": _relative_path(MATRIX_PROBE_PATH),
    "authority_boundary": {
      "database_scope": "proxy_only",
      "probability_field": "proxy_event.component_primary_row_failure_probability",
      "event_max_probability_field": (
        "proxy_event.component_failure_probability "
        "(max across component mechanism load rows)"
      ),
      "probability_source": "runtime component response row failure_probability_source",
      "synthetic_component_failure_probability": True,
      "real_weapon_pk_authority": False,
      "deterministic_fuze_authority": False,
    },
    "independent_variables": [
      "warhead_family",
      "aspect",
      "range_bucket",
      "local_forward_m",
      "local_right_m",
      "local_up_m",
      "miss_distance_m",
      "missile_velocity_forward_mps",
      "missile_velocity_right_mps",
      "missile_velocity_up_mps",
    ],
    "dependent_variables": [
      "proxy_component_failure_probability",
      "proxy_component_primary_failure_probability",
      "proxy_component_primary_distance_m",
      "proxy_component_primary_effect_scale",
      "proxy_event_max_component_failure_probability",
      "proxy_component_primary_rod_cut_margin",
      "proxy_component_primary_fragment_energy_j",
      "proxy_component_primary_integrity",
    ],
    "metrics": metrics,
    "records": records,
    "aspect_range_probability_matrices": aspect_range,
  }


def _ensure_matplotlib() -> Any:
  import matplotlib

  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np

  return plt, np


def _short_label(text: str, width: int = 26) -> str:
  return textwrap.shorten(text, width=width, placeholder="...")


def _bucket_axis_label(text: str) -> str:
  return "\n".join(str(text).split("_"))


def _case_marker_label(case_id: str) -> str:
  labels = {
    "center_spar_carrythrough": "C spar",
    "engine_afterburner_segment": "afterburn",
    "engine_forward_compressor_center": "compressor",
    "engine_hot_section_center": "hot sec",
    "left_aileron_direct_center": "L aileron",
    "left_beam_near_7m": "L beam 7",
    "nose_cockpit_center": "nose",
    "right_aileron_direct_center": "R aileron",
    "right_beam_far_14m": "R beam 14",
    "right_beam_near_7m": "R beam 7",
    "right_wing_fuel_center": "R fuel",
    "tail_right_near": "tail R",
  }
  return labels.get(case_id, _short_label(case_id, width=14))


def render_aspect_range_heatmap(
  report: dict[str, Any],
  *,
  output_dir: Path,
) -> dict[str, str]:
  plt, np = _ensure_matplotlib()
  fig, axes = plt.subplots(
    1,
    len(WARHEAD_FAMILIES),
    figsize=(16.0, 8.5),
    constrained_layout=True,
  )
  for axis_index, family in enumerate(WARHEAD_FAMILIES):
    axis = axes[axis_index]
    matrix_info = report["aspect_range_probability_matrices"][family]
    matrix = np.array(
      [
        [
          float(value) if value is not None else np.nan
          for value in matrix_row
        ]
        for matrix_row in matrix_info["matrix"]
      ],
      dtype=float,
    )
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad(color="#eef2f7")
    image = axis.imshow(matrix, vmin=0.0, vmax=1.0, cmap=cmap, aspect="auto")
    axis.set_title(family, fontsize=12, pad=10)
    axis.set_xticks(range(len(matrix_info["range_buckets"])))
    axis.set_xticklabels(
      [_bucket_axis_label(value) for value in matrix_info["range_buckets"]],
      rotation=0,
      ha="center",
      fontsize=8,
    )
    axis.set_yticks(range(len(matrix_info["aspects"])))
    axis.set_yticklabels(matrix_info["aspects"], fontsize=9)
    axis.set_xlabel("range_bucket")
    if axis_index == 0:
      axis.set_ylabel("aspect")
    axis.tick_params(axis="both", length=0)
    axis.set_xticks(
      [idx + 0.5 for idx in range(len(matrix_info["range_buckets"]) - 1)],
      minor=True,
    )
    axis.set_yticks(
      [idx + 0.5 for idx in range(len(matrix_info["aspects"]) - 1)],
      minor=True,
    )
    axis.grid(which="minor", color="white", linewidth=0.8)
    count_matrix = matrix_info["count_matrix"]
    for y_idx, row in enumerate(matrix_info["matrix"]):
      for x_idx, value in enumerate(row):
        count = int(count_matrix[y_idx][x_idx])
        if value is None:
          continue
        label = f"{float(value):.3f}\nn={count}"
        color = "white" if float(value) > 0.52 else "#1f2933"
        axis.text(
          x_idx,
          y_idx,
          label,
          ha="center",
          va="center",
          fontsize=8,
          color=color,
        )
    cbar = fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Proxy P(fail)", rotation=270, labelpad=14, fontsize=9)
  fig.suptitle(
    "Proxy-only component failure probability by independent variables\n"
    "aspect x range_bucket; synthetic debug-hit probe",
    fontsize=14,
  )
  output_dir.mkdir(parents=True, exist_ok=True)
  png_path = output_dir / "target_geometry_proxy_heatmap_aspect_range_20260615.png"
  svg_path = output_dir / "target_geometry_proxy_heatmap_aspect_range_20260615.svg"
  fig.savefig(png_path, dpi=180, bbox_inches="tight")
  fig.savefig(svg_path, bbox_inches="tight")
  plt.close(fig)
  return {
    "png_path": _relative_path(png_path),
    "svg_path": _relative_path(svg_path),
  }


def render_local_position_heatmap(
  report: dict[str, Any],
  *,
  output_dir: Path,
) -> dict[str, str]:
  plt, np = _ensure_matplotlib()
  fig, axes = plt.subplots(
    1,
    len(WARHEAD_FAMILIES),
    figsize=(16.0, 7.5),
    constrained_layout=True,
    sharex=True,
    sharey=True,
  )
  all_records = list(report["records"])
  x_values = [float(record["local_forward_m"]) for record in all_records]
  y_values = [float(record["local_right_m"]) for record in all_records]
  for axis_index, family in enumerate(WARHEAD_FAMILIES):
    axis = axes[axis_index]
    records = [
      record
      for record in all_records
      if str(record["warhead_family"]) == family
    ]
    values = [
      float(record["proxy_component_failure_probability"]) for record in records
    ]
    scatter = axis.scatter(
      [float(record["local_forward_m"]) for record in records],
      [float(record["local_right_m"]) for record in records],
      c=values,
      cmap="viridis",
      vmin=0.0,
      vmax=1.0,
      s=520,
      marker="s",
      edgecolors="#1f2933",
      linewidths=0.75,
    )
    for record in records:
      label = (
        f"{float(record['proxy_component_failure_probability']):.3f}\n"
        f"{_case_marker_label(str(record['case_id']))}"
      )
      axis.text(
        float(record["local_forward_m"]),
        float(record["local_right_m"]),
        label,
        ha="center",
        va="center",
        fontsize=7,
        color="white"
        if float(record["proxy_component_failure_probability"]) > 0.52
        else "#111827",
      )
    axis.set_title(family, fontsize=12, pad=10)
    axis.set_xlabel("local_forward_m")
    if axis_index == 0:
      axis.set_ylabel("local_right_m")
    axis.grid(True, color="#d0d7de", linewidth=0.7, alpha=0.8)
    axis.set_xlim(min(x_values) - 0.8, max(x_values) + 0.8)
    axis.set_ylim(min(y_values) - 1.0, max(y_values) + 1.0)
    axis.axhline(0.0, color="#4b5563", linewidth=0.9)
    axis.axvline(0.0, color="#4b5563", linewidth=0.9)
    cbar = fig.colorbar(scatter, ax=axis, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Proxy P(fail)", rotation=270, labelpad=14, fontsize=9)
  fig.suptitle(
    "Proxy-only component failure probability by local-position variables\n"
    "x=local_forward_m, y=local_right_m; local_up_m retained in JSON",
    fontsize=14,
  )
  output_dir.mkdir(parents=True, exist_ok=True)
  png_path = output_dir / "target_geometry_proxy_heatmap_local_position_20260615.png"
  svg_path = output_dir / "target_geometry_proxy_heatmap_local_position_20260615.svg"
  fig.savefig(png_path, dpi=180, bbox_inches="tight")
  fig.savefig(svg_path, bbox_inches="tight")
  plt.close(fig)
  return {
    "png_path": _relative_path(png_path),
    "svg_path": _relative_path(svg_path),
  }


def write_report(report: dict[str, Any], *, output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = (
    output_dir / "target_geometry_proxy_independent_variable_heatmap_20260615.json"
  )
  output_path.write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return output_path


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--input", type=Path, default=MATRIX_PROBE_PATH)
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--no-render", action="store_true")
  args = parser.parse_args()

  probe = _load_probe(args.input)
  report = build_report(probe)
  if not args.no_render:
    report["rendered_figures"] = {
      "aspect_range": render_aspect_range_heatmap(
        report,
        output_dir=args.output_dir,
      ),
      "local_position": render_local_position_heatmap(
        report,
        output_dir=args.output_dir,
      ),
    }
  output_path = write_report(report, output_dir=args.output_dir)
  print(json.dumps(report, indent=2, sort_keys=True))
  print(f"\nwrote {_relative_path(output_path)}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
