#!/usr/bin/env python3
"""Render target-geometry lethality probability matrices from the matrix probe."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import resolve_repo_path


SCHEMA_VERSION = "a2.target_geometry_lethality_probability_matrix.v1"
STATUS = "target_geometry_lethality_probability_matrix_rendered_20260615"
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
MATRIX_COLUMNS = (
  "default_component_failure_probability",
  "proxy_component_failure_probability",
  "proxy_minus_default_probability",
)


def _relative_path(path: Path) -> str:
  return str(path.resolve().relative_to(REPO_ROOT))


def _load_probe(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _probability_row(comparison: dict[str, Any]) -> dict[str, Any]:
  default_event = comparison["default_event"]
  proxy_event = comparison["proxy_event"]
  default_probability = float(default_event["component_primary_row_failure_probability"])
  proxy_probability = float(proxy_event["component_primary_row_failure_probability"])
  default_primary = str(default_event["component_primary_name"]) or "(none)"
  proxy_primary = str(proxy_event["component_primary_name"]) or "(none)"
  return {
    "case_id": str(comparison["case_id"]),
    "warhead_family": str(comparison["warhead_family"]),
    "aspect": str(comparison["aspect"]),
    "range_bucket": str(comparison["range_bucket"]),
    "local_point_m": list(comparison["local_point_m"]),
    "missile_velocity_body_mps": list(comparison["missile_velocity_body_mps"]),
    "default_component_primary_name": default_primary,
    "proxy_component_primary_name": proxy_primary,
    "primary_component_changed": default_primary != proxy_primary,
    "default_component_failure_probability": default_probability,
    "proxy_component_failure_probability": proxy_probability,
    "proxy_minus_default_probability": proxy_probability - default_probability,
    "default_event_max_component_failure_probability": float(
      default_event["component_failure_probability"]
    ),
    "proxy_event_max_component_failure_probability": float(
      proxy_event["component_failure_probability"]
    ),
    "default_event_max_component_failure_probability_component_name": str(
      default_event["component_max_failure_probability_component_name"]
    )
    or "(none)",
    "proxy_event_max_component_failure_probability_component_name": str(
      proxy_event["component_max_failure_probability_component_name"]
    )
    or "(none)",
    "default_component_primary_distance_m": float(
      default_event["component_primary_row_distance_m"]
    ),
    "proxy_component_primary_distance_m": float(
      proxy_event["component_primary_row_distance_m"]
    ),
    "default_component_primary_effect_scale": float(
      default_event["component_primary_row_effect_scale"]
    ),
    "proxy_component_primary_effect_scale": float(
      proxy_event["component_primary_row_effect_scale"]
    ),
    "default_component_failure_probability_source": str(
      default_event["component_failure_probability_source"]
    ),
    "proxy_component_failure_probability_source": str(
      proxy_event["component_failure_probability_source"]
    ),
    "geometry_effect_observed": bool(comparison["geometry_effect_observed"]),
  }


def _family_matrix_rows(
  probe: dict[str, Any],
  *,
  family: str,
) -> list[dict[str, Any]]:
  rows = [
    _probability_row(comparison)
    for comparison in probe["comparisons"]
    if str(comparison["warhead_family"]) == family
  ]
  rows.sort(key=lambda row: str(row["case_id"]))
  return rows


def build_probability_matrix_report(probe: dict[str, Any]) -> dict[str, Any]:
  matrices = {
    family: {
      "columns": list(MATRIX_COLUMNS),
      "rows": _family_matrix_rows(probe, family=family),
    }
    for family in WARHEAD_FAMILIES
  }
  metrics = {
    "warhead_family_count": len(WARHEAD_FAMILIES),
    "matrix_count": len(matrices),
    "row_count_per_matrix": {
      family: len(matrix["rows"]) for family, matrix in matrices.items()
    },
    "primary_component_changed_rows": {
      family: sum(
        1 for row in matrix["rows"] if bool(row["primary_component_changed"])
      )
      for family, matrix in matrices.items()
    },
    "probability_delta_nonzero_rows": {
      family: sum(
        1
        for row in matrix["rows"]
        if abs(float(row["proxy_minus_default_probability"])) > 1.0e-9
      )
      for family, matrix in matrices.items()
    },
  }
  return {
    "schema_version": SCHEMA_VERSION,
    "status": STATUS,
    "generated_on": GENERATED_ON,
    "source_probe_path": _relative_path(MATRIX_PROBE_PATH),
    "authority_boundary": {
      "probability_field": "component_primary_row_failure_probability",
      "event_max_probability_field": (
        "component_failure_probability "
        "(max across component mechanism load rows)"
      ),
      "probability_source": "runtime component row component_failure_probability_source",
      "synthetic_component_failure_probability": True,
      "real_weapon_pk_authority": False,
      "deterministic_fuze_authority": False,
      "default_database_modified": False,
      "proxy_database_opt_in_only": True,
    },
    "metrics": metrics,
    "matrices": matrices,
  }


def _ensure_matplotlib() -> Any:
  import matplotlib

  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  from matplotlib.colors import TwoSlopeNorm

  return plt, TwoSlopeNorm


def _row_label(row: dict[str, Any]) -> str:
  primary = (
    f"D:{row['default_component_primary_name']} -> "
    f"P:{row['proxy_component_primary_name']}"
  )
  return "\n".join(
    (
      str(row["case_id"]),
      textwrap.shorten(primary, width=58, placeholder="..."),
    )
  )


def _column_values(rows: list[dict[str, Any]], column: str) -> list[float]:
  return [float(row[column]) for row in rows]


def _annotate_column(ax: object, values: list[float], *, signed: bool) -> None:
  for idx, value in enumerate(values):
    text = f"{value:+.3f}" if signed else f"{value:.3f}"
    color = "white" if abs(value) > 0.45 else "#1f2933"
    ax.text(0, idx, text, ha="center", va="center", color=color, fontsize=8)


def render_family_matrix(
  *,
  family: str,
  rows: list[dict[str, Any]],
  output_dir: Path,
) -> dict[str, str]:
  plt, TwoSlopeNorm = _ensure_matplotlib()
  labels = [_row_label(row) for row in rows]
  default_values = _column_values(rows, "default_component_failure_probability")
  proxy_values = _column_values(rows, "proxy_component_failure_probability")
  delta_values = _column_values(rows, "proxy_minus_default_probability")
  max_abs_delta = max([abs(value) for value in delta_values] + [0.01])

  figure, axes = plt.subplots(
    nrows=1,
    ncols=3,
    figsize=(14.5, max(7.0, 0.62 * len(rows) + 2.3)),
    gridspec_kw={"width_ratios": [1.0, 1.0, 1.0]},
    constrained_layout=True,
  )
  panels = (
    (
      "Default",
      default_values,
      "viridis",
      None,
      False,
      "Component failure probability",
    ),
    (
      "Proxy",
      proxy_values,
      "viridis",
      None,
      False,
      "Component failure probability",
    ),
    (
      "Proxy - Default",
      delta_values,
      "coolwarm",
      TwoSlopeNorm(vmin=-max_abs_delta, vcenter=0.0, vmax=max_abs_delta),
      True,
      "Probability delta",
    ),
  )

  for axis_index, (title, values, cmap, norm, signed, colorbar_label) in enumerate(
    panels
  ):
    axis = axes[axis_index]
    data = [[value] for value in values]
    image = axis.imshow(
      data,
      aspect="auto",
      cmap=cmap,
      norm=norm,
      vmin=None if norm is not None else 0.0,
      vmax=None if norm is not None else 1.0,
    )
    axis.set_title(title, fontsize=12, pad=10)
    axis.set_xticks([0])
    axis.set_xticklabels(["P(fail)" if not signed else "Delta"], fontsize=9)
    axis.set_yticks(range(len(rows)))
    if axis_index == 0:
      axis.set_yticklabels(labels, fontsize=7)
    else:
      axis.set_yticklabels([])
    axis.tick_params(axis="both", length=0)
    axis.set_xticks([-.5, .5], minor=True)
    axis.set_yticks([idx + 0.5 for idx in range(len(rows) - 1)], minor=True)
    axis.grid(which="minor", color="white", linewidth=0.8)
    _annotate_column(axis, values, signed=signed)
    colorbar = figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    colorbar.ax.set_ylabel(colorbar_label, rotation=270, labelpad=14, fontsize=8)

  figure.suptitle(
    (
      f"{family}: synthetic component failure probability matrix\n"
      "Debug local-hit probe; not real weapon Pk authority"
    ),
    fontsize=14,
  )

  output_dir.mkdir(parents=True, exist_ok=True)
  stem = f"target_geometry_lethality_probability_matrix_{family}_20260615"
  png_path = output_dir / f"{stem}.png"
  svg_path = output_dir / f"{stem}.svg"
  figure.savefig(png_path, dpi=180, bbox_inches="tight")
  figure.savefig(svg_path, bbox_inches="tight")
  plt.close(figure)
  return {
    "png_path": _relative_path(png_path),
    "svg_path": _relative_path(svg_path),
  }


def render_probability_matrix_figures(
  report: dict[str, Any],
  *,
  output_dir: Path,
) -> dict[str, dict[str, str]]:
  rendered: dict[str, dict[str, str]] = {}
  for family, matrix in report["matrices"].items():
    rendered[family] = render_family_matrix(
      family=family,
      rows=list(matrix["rows"]),
      output_dir=output_dir,
    )
  return rendered


def write_probability_matrix_report(
  report: dict[str, Any],
  *,
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = (
    output_dir / "target_geometry_lethality_probability_matrix_20260615.json"
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
  report = build_probability_matrix_report(probe)
  if not args.no_render:
    report["rendered_figures"] = render_probability_matrix_figures(
      report,
      output_dir=args.output_dir,
    )
  output_path = write_probability_matrix_report(report, output_dir=args.output_dir)
  print(json.dumps(report, indent=2, sort_keys=True))
  print(f"\nwrote {_relative_path(output_path)}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
