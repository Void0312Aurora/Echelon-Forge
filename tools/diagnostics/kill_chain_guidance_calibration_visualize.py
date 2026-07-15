#!/usr/bin/env python3
"""Render stage-4/5 guidance-calibration evidence without rerunning simulation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = (
  "a2.kill_chain_guidance_calibration_visualization.v1"
)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap, TwoSlopeNorm  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

SCHEMA_VERSION = "a2.kill_chain_guidance_calibration_visualization_manifest.v1"
STAGE4_SCHEMA_VERSION = "a2.kill_chain_guidance_envelope_rebuild.v1"
STAGE5_SCHEMA_VERSION = "a2.kill_chain_guidance_scalar_calibration.v1"
DEFAULT_PREFIX = "kill_chain_guidance_calibration"
DEFAULT_STAGE4_REPORT = REPO_ROOT / (
  "docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/"
  "kill_chain_guidance_envelope_rebuild_20260715/"
  "kill_chain_guidance_envelope_rebuild_20260715.json"
)
DEFAULT_STAGE5_REPORT = REPO_ROOT / (
  "docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/"
  "kill_chain_guidance_scalar_calibration_20260715/"
  "kill_chain_guidance_scalar_calibration_20260715.json"
)

LAUNCH_CLASS_CODES = {"O": 0, "M": 1, "N": 2}
LAUNCH_CLASS_COLORS = {"O": "#d7d7d7", "M": "#f4b860", "N": "#61b87a"}
TRANSITION_CODES = {"lost": -1, "unchanged": 0, "gained": 1}
TRANSITION_COLORS = {
  "lost": "#3f7fbf",
  "unchanged": "#d7d7d7",
  "gained": "#e07a3f",
}
ROBUST_HIT = "robust_hit"
ROBUST_MISS = "robust_miss"
RHO_LOG10_MIN = -4.1
RHO_LOG10_MAX = 3.1


def _nested_get(value: Any, *path: str) -> Any:
  current = value
  for part in path:
    if not isinstance(current, dict):
      return None
    current = current.get(part)
  return current


def _finite_float(value: Any) -> float | None:
  try:
    result = float(value)
  except (TypeError, ValueError):
    return None
  return result if math.isfinite(result) else None


def _required_float(value: Any, *, field: str) -> float:
  result = _finite_float(value)
  if result is None:
    raise ValueError(f"expected finite {field}, got {value!r}")
  return result


def _read_json(path: Path) -> dict[str, Any]:
  with path.open("r", encoding="utf-8") as handle:
    result = json.load(handle)
  if not isinstance(result, dict):
    raise TypeError(f"expected object JSON at {path}")
  return result


def _read_csv(path: Path) -> list[dict[str, str]]:
  with path.open(newline="", encoding="utf-8") as handle:
    return list(csv.DictReader(handle))


def _write_json(path: Path, value: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", encoding="utf-8") as handle:
    json.dump(value, handle, ensure_ascii=True, indent=2, sort_keys=True)
    handle.write("\n")


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
  resolved = path.resolve()
  return {
    "path": _display_path(resolved),
    "sha256": _sha256(resolved),
    "bytes": resolved.stat().st_size,
  }


def _display_path(path: Path) -> str:
  resolved = path.resolve()
  try:
    return str(resolved.relative_to(REPO_ROOT))
  except ValueError:
    return str(resolved)


def _validate_schema(report: dict[str, Any], expected: str, *, label: str) -> None:
  actual = str(report.get("schema_version") or "")
  if actual != expected:
    raise ValueError(f"{label} schema mismatch: expected {expected!r}, got {actual!r}")


def _resolve_artifact(report_path: Path, raw_path: Any) -> Path:
  if not raw_path:
    raise ValueError(f"missing artifact path in {report_path}")
  path = Path(str(raw_path))
  candidates = [path] if path.is_absolute() else [
    REPO_ROOT / path,
    report_path.parent / path,
    report_path.parent / path.name,
  ]
  for candidate in candidates:
    if candidate.exists():
      return candidate.resolve()
  raise FileNotFoundError(
    f"could not resolve artifact {raw_path!r} referenced by {report_path}"
  )


def _default_date_stamp(report: dict[str, Any]) -> str:
  raw = str(report.get("generated_at_utc") or "")
  compact = raw[:10].replace("-", "")
  return compact if len(compact) == 8 and compact.isdigit() else "undated"


def _axis_values(rows: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
  ranges = sorted(
    {_required_float(row.get("range_km"), field="range_km") for row in rows}
  )
  offsets = sorted(
    {_required_float(row.get("offset_deg"), field="offset_deg") for row in rows}
  )
  if not ranges or not offsets:
    raise ValueError("matrix axes must not be empty")
  return ranges, offsets


def _axis_edges(values: list[float]) -> np.ndarray:
  array = np.asarray(values, dtype=float)
  if len(array) == 1:
    return np.array([array[0] - 0.5, array[0] + 0.5], dtype=float)
  midpoint = (array[:-1] + array[1:]) / 2.0
  return np.concatenate(
    ([array[0] - (midpoint[0] - array[0])], midpoint, [array[-1] + (array[-1] - midpoint[-1])])
  )


def _index_cells(
  rows: list[dict[str, Any]],
) -> dict[tuple[float, float], dict[str, Any]]:
  indexed: dict[tuple[float, float], dict[str, Any]] = {}
  for row in rows:
    key = (
      _required_float(row.get("range_km"), field="range_km"),
      _required_float(row.get("offset_deg"), field="offset_deg"),
    )
    if key in indexed:
      raise ValueError(f"duplicate matrix cell at range/offset={key}")
    indexed[key] = row
  return indexed


def _require_rectangular(
  indexed: dict[tuple[float, float], dict[str, Any]],
  *,
  ranges: list[float],
  offsets: list[float],
  label: str,
) -> None:
  missing = [
    (range_km, offset_deg)
    for offset_deg in offsets
    for range_km in ranges
    if (range_km, offset_deg) not in indexed
  ]
  if missing:
    raise ValueError(f"{label} is not rectangular; missing cells: {missing[:5]}")


def _matrix(
  indexed: dict[tuple[float, float], dict[str, Any]],
  *,
  ranges: list[float],
  offsets: list[float],
  getter: Callable[[dict[str, Any]], Any],
) -> list[list[Any]]:
  return [
    [getter(indexed[(range_km, offset_deg)]) for range_km in ranges]
    for offset_deg in offsets
  ]


def _write_matrix_csv(
  path: Path,
  *,
  ranges: list[float],
  offsets: list[float],
  values: list[list[Any]],
) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["absolute_offset_deg", *[f"{value:g}" for value in ranges]])
    for offset_deg, row in zip(offsets, values, strict=True):
      writer.writerow([f"{offset_deg:g}", *row])


def _save_figure(figure: Any, base_path: Path) -> dict[str, dict[str, Any]]:
  png_path = base_path.with_suffix(".png")
  svg_path = base_path.with_suffix(".svg")
  figure.savefig(
    png_path,
    dpi=180,
    bbox_inches="tight",
    metadata={"Date": None},
  )
  figure.savefig(
    svg_path,
    bbox_inches="tight",
    metadata={"Date": None},
  )
  svg_text = svg_path.read_text(encoding="utf-8")
  svg_path.write_text(
    "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
    encoding="utf-8",
  )
  plt.close(figure)
  return {"png": _file_record(png_path), "svg": _file_record(svg_path)}


def _configure_axis(
  axis: Any,
  *,
  ranges: list[float],
  offsets: list[float],
  label_size: float = 8.0,
) -> None:
  axis.set_xlabel("Initial range (km)")
  axis.set_ylabel("Absolute offset angle (deg)")
  axis.set_xticks(ranges)
  axis.set_yticks(offsets)
  axis.tick_params(axis="x", labelsize=label_size)
  axis.tick_params(axis="y", labelsize=label_size)
  axis.set_xlim(_axis_edges(ranges)[[0, -1]])
  axis.set_ylim(_axis_edges(offsets)[[0, -1]])


def _stage4_main_cells(report: dict[str, Any]) -> list[dict[str, Any]]:
  result = [
    dict(row)
    for row in list(report.get("main_cells") or [])
    if isinstance(row, dict) and str(row.get("grid_tier") or "main") == "main"
  ]
  if not result:
    raise ValueError("stage-4 report has no main-grid cells")
  return result


def _raw_refinement_boundaries(
  report: dict[str, Any],
) -> tuple[list[float], list[float], list[float], list[float]]:
  hit_points: dict[float, float] = {}
  miss_points: dict[float, float] = {}
  for row in list(report.get("theta_fuze_by_range") or []):
    if not isinstance(row, dict):
      continue
    range_km = _finite_float(row.get("range_km"))
    theta_deg = _finite_float(row.get("theta_fuze_robust_hit_max_deg"))
    if range_km is not None and theta_deg is not None:
      hit_points[range_km] = theta_deg
    miss_deg = _finite_float(row.get("first_robust_miss_angle_deg"))
    if range_km is not None and miss_deg is not None:
      miss_points[range_km] = miss_deg
  hit_ranges = sorted(hit_points)
  miss_ranges = sorted(miss_points)
  return (
    hit_ranges,
    [hit_points[range_km] for range_km in hit_ranges],
    miss_ranges,
    [miss_points[range_km] for range_km in miss_ranges],
  )


def _stage4_summary_context(
  report: dict[str, Any],
  *,
  indexed: dict[tuple[float, float], dict[str, Any]],
  ranges: list[float],
  offsets: list[float],
) -> dict[str, Any]:
  counts = Counter(
    str(row.get("reclassified_launch_class") or "") for row in indexed.values()
  )
  if 60.0 in offsets:
    hit_ranges = [
      range_km
      for range_km in ranges
      if _state(indexed[(range_km, 60.0)]) == ROBUST_HIT
    ]
  else:
    hit_ranges = []
  components = _nested_get(report, "topology_audit", "robust_hit_component_count")
  holes = _nested_get(report, "topology_audit", "robust_hit_internal_hole_count")
  hit_rho_edges = [
    _rho_edge(row)
    for row in indexed.values()
    if _state(row) == ROBUST_HIT
  ]
  miss_rho_edges = [
    _rho_edge(row)
    for row in indexed.values()
    if _state(row) == ROBUST_MISS
  ]
  rho_edges = hit_rho_edges + miss_rho_edges
  return {
    "launch_class_counts": {
      "N": counts["N"],
      "M": counts["M"],
      "O": counts["O"],
    },
    "sixty_deg_robust_hit_min_range_km": min(hit_ranges) if hit_ranges else None,
    "sixty_deg_robust_hit_max_range_km": max(hit_ranges) if hit_ranges else None,
    "robust_hit_component_count": components,
    "robust_hit_internal_hole_count": holes,
    "rho_edge_min": min(rho_edges),
    "rho_edge_max": max(rho_edges),
    "robust_hit_rho_edge_min": min(hit_rho_edges) if hit_rho_edges else None,
    "robust_hit_rho_edge_median": (
      float(np.median(hit_rho_edges)) if hit_rho_edges else None
    ),
    "robust_hit_rho_edge_max": max(hit_rho_edges) if hit_rho_edges else None,
    "robust_miss_rho_edge_min": min(miss_rho_edges) if miss_rho_edges else None,
    "robust_miss_rho_edge_max": max(miss_rho_edges) if miss_rho_edges else None,
  }


def _stage4_evidence_text(
  report: dict[str, Any],
  *,
  indexed: dict[tuple[float, float], dict[str, Any]],
  ranges: list[float],
  offsets: list[float],
) -> str:
  context = _stage4_summary_context(
    report,
    indexed=indexed,
    ranges=ranges,
    offsets=offsets,
  )
  counts = context["launch_class_counts"]
  minimum_range = context["sixty_deg_robust_hit_min_range_km"]
  maximum_range = context["sixty_deg_robust_hit_max_range_km"]
  hit_text = (
    f"{minimum_range:g}-{maximum_range:g} km"
    if minimum_range is not None and maximum_range is not None
    else "not sampled"
  )
  component_count = context["robust_hit_component_count"]
  hole_count = context["robust_hit_internal_hole_count"]
  return "\n".join(
    (
      f"N/M/O = {counts['N']}/{counts['M']}/{counts['O']}",
      f"60 deg robust-hit range = {hit_text}",
      f"robust-hit components = {component_count if component_count is not None else 'n/a'}",
      f"internal holes = {hole_count if hole_count is not None else 'n/a'}",
    )
  )


def _rho_edge(row: dict[str, Any]) -> float:
  state = str(row.get("robust_state") or "")
  if state == ROBUST_HIT:
    return _required_float(row.get("rho_max"), field="rho_max")
  if state == ROBUST_MISS:
    return _required_float(row.get("rho_min"), field="rho_min")
  raise ValueError(f"rho_edge requires robust_hit or robust_miss, got {state!r}")


def _plot_stage4_classification(
  base_path: Path,
  *,
  report: dict[str, Any],
  indexed: dict[tuple[float, float], dict[str, Any]],
  ranges: list[float],
  offsets: list[float],
  raw_classes: list[list[str]],
) -> dict[str, dict[str, Any]]:
  numeric = np.array(
    [[LAUNCH_CLASS_CODES[value] for value in row] for row in raw_classes],
    dtype=float,
  )
  ordered = ["O", "M", "N"]
  values = [LAUNCH_CLASS_CODES[label] for label in ordered]
  cmap = ListedColormap([LAUNCH_CLASS_COLORS[label] for label in ordered])
  cmap.set_bad("#eeeeee")
  norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap.N)
  figure, axis = plt.subplots(figsize=(12.8, 9.2), constrained_layout=True)
  image = axis.pcolormesh(
    _axis_edges(ranges),
    _axis_edges(offsets),
    numeric,
    cmap=cmap,
    norm=norm,
    shading="flat",
    edgecolors="white",
    linewidth=0.55,
  )
  colorbar = figure.colorbar(image, ax=axis, shrink=0.79, ticks=values)
  colorbar.ax.set_yticklabels(ordered)
  colorbar.ax.set_ylabel("Stage-4 launch class", rotation=270, labelpad=17)
  for row_index, offset_deg in enumerate(offsets):
    for column_index, range_km in enumerate(ranges):
      launch_class = raw_classes[row_index][column_index]
      axis.text(
        range_km,
        offset_deg,
        launch_class,
        ha="center",
        va="center",
        fontsize=6.3,
        color="#17212b",
      )
      if launch_class != "M":
        continue
      robust_state = str(indexed[(range_km, offset_deg)].get("robust_state") or "")
      if robust_state == ROBUST_HIT:
        axis.scatter(
          [range_km],
          [offset_deg - 1.35],
          s=20,
          marker="o",
          facecolors="none",
          edgecolors="#111111",
          linewidths=0.8,
          zorder=4,
        )
      elif robust_state == ROBUST_MISS:
        axis.scatter(
          [range_km],
          [offset_deg - 1.35],
          s=19,
          marker="x",
          color="#111111",
          linewidths=0.8,
          zorder=4,
        )
      else:
        raise ValueError(f"M cell has unsupported robust_state={robust_state!r}")

  hit_ranges, hit_theta, miss_ranges, miss_theta = _raw_refinement_boundaries(report)
  if hit_ranges:
    axis.plot(
      hit_ranges,
      hit_theta,
      color="#111111",
      linewidth=1.4,
      marker=".",
      markersize=4.5,
      drawstyle="steps-mid",
      label="raw sampled theta_fuze boundary (no smoothing)",
      zorder=5,
    )
  if miss_ranges:
    axis.plot(
      miss_ranges,
      miss_theta,
      color="#7f1d1d",
      linewidth=1.1,
      linestyle="--",
      marker="x",
      markersize=3.8,
      drawstyle="steps-mid",
      label="first robust miss (no smoothing)",
      zorder=5,
    )
  axis.scatter(
    [],
    [],
    s=22,
    marker="o",
    facecolors="none",
    edgecolors="#111111",
    label="M robust hit",
  )
  axis.scatter([], [], s=20, marker="x", color="#111111", label="M robust miss")
  axis.legend(loc="upper right", fontsize=8, framealpha=0.92)
  axis.text(
    0.02,
    0.98,
    _stage4_evidence_text(
      report,
      indexed=indexed,
      ranges=ranges,
      offsets=offsets,
    ),
    transform=axis.transAxes,
    ha="left",
    va="top",
    fontsize=8.2,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.9},
    zorder=6,
  )
  axis.set_title(
    "Stage 4 launch envelope: N/M/O with observed M state and raw refinement boundary"
  )
  _configure_axis(axis, ranges=ranges, offsets=offsets)
  axis.text(
    0.0,
    -0.105,
    "No interpolation or smoothing is applied to cells; the boundary is a step connection of sampled theta_fuze points.",
    transform=axis.transAxes,
    fontsize=8,
    color="#555555",
  )
  return _save_figure(figure, base_path)


def _plot_stage4_rho_edge(
  base_path: Path,
  *,
  ranges: list[float],
  offsets: list[float],
  log10_values: list[list[float]],
) -> dict[str, dict[str, Any]]:
  numeric = np.asarray(log10_values, dtype=float)
  figure, axis = plt.subplots(figsize=(12.8, 9.2), constrained_layout=True)
  image = axis.pcolormesh(
    _axis_edges(ranges),
    _axis_edges(offsets),
    numeric,
    cmap="coolwarm",
    norm=TwoSlopeNorm(
      vmin=RHO_LOG10_MIN,
      vcenter=0.0,
      vmax=RHO_LOG10_MAX,
    ),
    shading="flat",
    edgecolors="white",
    linewidth=0.55,
  )
  colorbar = figure.colorbar(image, ax=axis, shrink=0.79, extend="both")
  colorbar.set_ticks([-4.0, -2.0, 0.0, 1.0, 2.0, 3.0])
  colorbar.set_ticklabels(
    [r"$10^{-4}$", r"$10^{-2}$", "1", "10", r"$10^{2}$", r"$10^{3}$"]
  )
  colorbar.ax.set_ylabel(
    "Conservative rho_edge (log-scaled colors)",
    rotation=270,
    labelpad=18,
  )
  for row_index, offset_deg in enumerate(offsets):
    for column_index, range_km in enumerate(ranges):
      value = log10_values[row_index][column_index]
      if abs(value) > 3.0 or abs(value) < 0.35:
        axis.text(
          range_km,
          offset_deg,
          f"{value:.1f}",
          ha="center",
          va="center",
          fontsize=5.8,
          color="white" if abs(value) > 2.4 else "#17212b",
        )
  axis.set_title("Stage 4 conservative edge distance: hit uses rho_max, miss uses rho_min")
  _configure_axis(axis, ranges=ranges, offsets=offsets)
  axis.text(
    0.0,
    -0.105,
    "Fixed color scale [-4.1, 3.1]. Blue is inside the fuze boundary; red is outside; zero means rho_edge=1.",
    transform=axis.transAxes,
    fontsize=8,
    color="#555555",
  )
  return _save_figure(figure, base_path)


def _stage5_main_groups(rows: list[dict[str, str]]) -> dict[float, list[dict[str, Any]]]:
  grouped: dict[float, list[dict[str, Any]]] = {}
  for raw in rows:
    if str(raw.get("grid_tier") or "") != "main":
      continue
    nav_gain = _required_float(raw.get("nav_gain"), field="nav_gain")
    grouped.setdefault(nav_gain, []).append(dict(raw))
  if not grouped:
    raise ValueError("stage-5 cells CSV contains no main-grid rows")
  return grouped


def _state(row: dict[str, Any]) -> str:
  value = str(row.get("robust_state") or "")
  if value not in {ROBUST_HIT, ROBUST_MISS}:
    raise ValueError(f"expected robust_hit or robust_miss, got {value!r}")
  return value


def _transition(baseline_state: str, candidate_state: str) -> str:
  if baseline_state == candidate_state:
    return "unchanged"
  return "lost" if baseline_state == ROBUST_HIT else "gained"


def _transition_matrices(
  grouped: dict[float, list[dict[str, Any]]],
  *,
  baseline_gain: float,
  candidate_gains: list[float],
) -> tuple[list[float], list[float], dict[float, list[list[str]]], dict[tuple[float, float], dict[str, Any]]]:
  if baseline_gain not in grouped:
    raise ValueError(f"stage-5 cells do not contain baseline nav_gain={baseline_gain:g}")
  ranges, offsets = _axis_values(grouped[baseline_gain])
  baseline = _index_cells(grouped[baseline_gain])
  _require_rectangular(
    baseline,
    ranges=ranges,
    offsets=offsets,
    label="stage-5 baseline main grid",
  )
  matrices: dict[float, list[list[str]]] = {}
  for nav_gain in candidate_gains:
    if nav_gain not in grouped:
      raise ValueError(f"stage-5 cells do not contain nav_gain={nav_gain:g}")
    indexed = _index_cells(grouped[nav_gain])
    _require_rectangular(
      indexed,
      ranges=ranges,
      offsets=offsets,
      label=f"stage-5 nav_gain={nav_gain:g} main grid",
    )
    if set(indexed) != set(baseline):
      raise ValueError(f"stage-5 nav_gain={nav_gain:g} grid differs from baseline")
    candidate_matrix: list[list[str]] = []
    for offset_deg in offsets:
      matrix_row: list[str] = []
      for range_km in ranges:
        key = (range_km, offset_deg)
        transition = _transition(
          _state(baseline[key]),
          _state(indexed[key]),
        )
        baseline_class = str(baseline[key].get("stage4_launch_class") or "")
        if transition != "unchanged" and baseline_class != "M":
          raise ValueError(
            "stage-5 state change escaped the stage-4 M band at "
            f"nav_gain={nav_gain:g}, range_km={range_km:g}, "
            f"offset_deg={offset_deg:g}, stage4_launch_class={baseline_class!r}"
          )
        matrix_row.append(transition)
      candidate_matrix.append(matrix_row)
    matrices[nav_gain] = candidate_matrix
  return ranges, offsets, matrices, baseline


def _validate_stage4_stage5_baseline_consistency(
  stage4: dict[tuple[float, float], dict[str, Any]],
  stage5_baseline: dict[tuple[float, float], dict[str, Any]],
  *,
  ranges: list[float],
  offsets: list[float],
) -> None:
  mismatches: list[str] = []
  for offset_deg in offsets:
    for range_km in ranges:
      key = (range_km, offset_deg)
      stage4_state = _state(stage4[key])
      stage5_state = _state(stage5_baseline[key])
      stage4_class = str(stage4[key].get("reclassified_launch_class") or "")
      stage5_class = str(stage5_baseline[key].get("stage4_launch_class") or "")
      if stage4_state == stage5_state and stage4_class == stage5_class:
        continue
      mismatches.append(
        f"range_km={range_km:g}, offset_deg={offset_deg:g}, "
        f"stage4=({stage4_state},{stage4_class}), "
        f"stage5_baseline=({stage5_state},{stage5_class})"
      )
  if mismatches:
    raise ValueError(
      "stage-4 report and stage-5 baseline cells disagree: "
      + "; ".join(mismatches[:5])
    )


def _baseline_boundary_segments(
  baseline: dict[tuple[float, float], dict[str, Any]],
  *,
  ranges: list[float],
  offsets: list[float],
) -> list[list[tuple[float, float]]]:
  range_edges = _axis_edges(ranges)
  offset_edges = _axis_edges(offsets)
  segments: list[list[tuple[float, float]]] = []
  for offset_index, offset_deg in enumerate(offsets):
    for range_index, range_km in enumerate(ranges):
      state = _state(baseline[(range_km, offset_deg)])
      if range_index + 1 < len(ranges):
        right_range = ranges[range_index + 1]
        if state != _state(baseline[(right_range, offset_deg)]):
          x_value = range_edges[range_index + 1]
          segments.append(
            [
              (x_value, offset_edges[offset_index]),
              (x_value, offset_edges[offset_index + 1]),
            ]
          )
      if offset_index + 1 < len(offsets):
        upper_offset = offsets[offset_index + 1]
        if state != _state(baseline[(range_km, upper_offset)]):
          y_value = offset_edges[offset_index + 1]
          segments.append(
            [
              (range_edges[range_index], y_value),
              (range_edges[range_index + 1], y_value),
            ]
          )
  return segments


def _comparison_map(report: dict[str, Any]) -> dict[float, dict[str, Any]]:
  result: dict[float, dict[str, Any]] = {}
  for raw in list(report.get("comparisons_vs_baseline") or []):
    if not isinstance(raw, dict):
      continue
    result[_required_float(raw.get("nav_gain"), field="nav_gain")] = raw
  return result


def _delta(comparison: dict[str, Any], key: str) -> float | None:
  return _finite_float(_nested_get(comparison, "deltas_vs_baseline", key))


def _metric_text(value: float | None, *, unit: str = "", signed: bool = True) -> str:
  if value is None:
    return "n/a"
  prefix = "+" if signed and value > 0.0 else ""
  if math.isclose(value, round(value), abs_tol=1e-12):
    number = f"{prefix}{int(round(value))}"
  elif abs(value) < 0.001 and value != 0.0:
    number = f"{value:+.2e}" if signed else f"{value:.2e}"
  elif abs(value) < 10.0:
    number = f"{prefix}{value:.3f}"
  else:
    number = f"{prefix}{value:.1f}"
  return f"{number}{unit}"


def _write_transition_csv(
  path: Path,
  *,
  ranges: list[float],
  offsets: list[float],
  matrices: dict[float, list[list[str]]],
) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(
      ["nav_gain", "absolute_offset_deg", *[f"{value:g}" for value in ranges]]
    )
    for nav_gain, matrix in sorted(matrices.items()):
      for offset_deg, row in zip(offsets, matrix, strict=True):
        writer.writerow([f"{nav_gain:g}", f"{offset_deg:g}", *row])


def _plot_stage5_transitions(
  base_path: Path,
  *,
  report: dict[str, Any],
  ranges: list[float],
  offsets: list[float],
  matrices: dict[float, list[list[str]]],
  baseline: dict[tuple[float, float], dict[str, Any]],
  baseline_gain: float,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
  if len(matrices) != 4:
    raise ValueError(f"expected four non-baseline nav_gain candidates, got {len(matrices)}")
  comparison_by_gain = _comparison_map(report)
  figure, axes = plt.subplots(
    2,
    2,
    figsize=(15.5, 12.0),
    constrained_layout=True,
    sharex=True,
    sharey=True,
  )
  cmap = ListedColormap(
    [TRANSITION_COLORS[label] for label in ("lost", "unchanged", "gained")]
  )
  cmap.set_bad("#eeeeee")
  norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5], cmap.N)
  boundary_segments = _baseline_boundary_segments(
    baseline,
    ranges=ranges,
    offsets=offsets,
  )
  panel_metrics: dict[str, dict[str, Any]] = {}
  last_image = None
  for axis, nav_gain in zip(axes.ravel(), sorted(matrices), strict=True):
    raw = matrices[nav_gain]
    numeric = np.asarray(
      [[TRANSITION_CODES[value] for value in row] for row in raw],
      dtype=float,
    )
    last_image = axis.pcolormesh(
      _axis_edges(ranges),
      _axis_edges(offsets),
      numeric,
      cmap=cmap,
      norm=norm,
      shading="flat",
      edgecolors="white",
      linewidth=0.45,
    )
    if boundary_segments:
      axis.add_collection(
        LineCollection(
          boundary_segments,
          colors="#111111",
          linewidths=1.25,
          linestyles="solid",
          zorder=4,
        )
      )
    counts = Counter(value for row in raw for value in row)
    main_net = counts["gained"] - counts["lost"]
    comparison = comparison_by_gain.get(nav_gain)
    if comparison is None:
      raise ValueError(f"missing comparison row for nav_gain={nav_gain:g}")
    holdout_delta = _delta(comparison, "holdout_robust_hit_count")
    theta_shift = _delta(comparison, "theta_fuze_max_displacement_deg")
    saturation_delta = _delta(comparison, "guidance_saturation_fraction_p95")
    panel_metrics[f"{nav_gain:g}"] = {
      "lost_main_cells": counts["lost"],
      "gained_main_cells": counts["gained"],
      "main_net_robust_hit_change": main_net,
      "holdout_robust_hit_change": holdout_delta,
      "theta_fuze_max_displacement_deg": theta_shift,
      "guidance_saturation_fraction_p95_change": saturation_delta,
    }
    axis.text(
      0.02,
      0.98,
      "\n".join(
        (
          f"main net hit: {main_net:+d} (lost {counts['lost']}, gained {counts['gained']})",
          f"holdout hit: {_metric_text(holdout_delta)}",
          f"theta shift: {_metric_text(theta_shift, unit=' deg', signed=False)}",
          f"sat P95: {_metric_text(saturation_delta)}",
        )
      ),
      transform=axis.transAxes,
      ha="left",
      va="top",
      fontsize=8,
      bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "alpha": 0.88},
      zorder=6,
    )
    axis.set_title(f"nav_gain={nav_gain:g} vs {baseline_gain:g}")
    _configure_axis(axis, ranges=ranges, offsets=offsets, label_size=7.0)
    axis.set_xlabel("")
    axis.set_ylabel("")
    for row_index, offset_deg in enumerate(offsets):
      for column_index, range_km in enumerate(ranges):
        value = raw[row_index][column_index]
        if value == "unchanged":
          continue
        axis.text(
          range_km,
          offset_deg,
          "-" if value == "lost" else "+",
          ha="center",
          va="center",
          fontsize=7,
          fontweight="bold",
          color="white",
          zorder=5,
        )
  assert last_image is not None
  colorbar = figure.colorbar(
    last_image,
    ax=axes.ravel().tolist(),
    shrink=0.73,
    ticks=[-1, 0, 1],
    pad=0.012,
  )
  colorbar.ax.set_yticklabels(["lost", "unchanged", "gained"])
  colorbar.ax.set_ylabel("Robust-state transition", rotation=270, labelpad=18)
  figure.suptitle(
    (
      f"Stage 5 nav_gain candidates: robust-state change relative to N={baseline_gain:g}\n"
      "Black cell-edge segments are the unsmoothed baseline robust hit/miss boundary"
    ),
    fontsize=15,
  )
  figure.supxlabel("Initial range (km)")
  figure.supylabel("Absolute offset angle (deg)")
  return _save_figure(figure, base_path), panel_metrics


def _artifact_record(
  csv_path: Path,
  images: dict[str, dict[str, Any]],
  *,
  description: str,
) -> dict[str, Any]:
  return {
    "description": description,
    "csv": _file_record(csv_path),
    **images,
  }


def _write_summary(
  path: Path,
  *,
  stage4_path: Path,
  stage5_path: Path,
  stage4_context: dict[str, Any],
  artifacts: dict[str, dict[str, Any]],
  decision_context: dict[str, Any],
  panel_metrics: dict[str, dict[str, Any]],
) -> None:
  class_counts = stage4_context["launch_class_counts"]
  minimum_range = stage4_context["sixty_deg_robust_hit_min_range_km"]
  maximum_range = stage4_context["sixty_deg_robust_hit_max_range_km"]
  theta_limit = decision_context["theta_fuze_max_displacement_limit_deg"]
  theta_shifts = sorted(
    {
      float(values["theta_fuze_max_displacement_deg"])
      for values in panel_metrics.values()
      if values["theta_fuze_max_displacement_deg"] is not None
    }
  )
  sixty_deg_range_text = (
    f"{minimum_range:g}-{maximum_range:g} km"
    if minimum_range is not None and maximum_range is not None
    else "not sampled"
  )
  theta_limit_text = (
    f"{theta_limit:g} deg" if theta_limit is not None else "not declared"
  )
  theta_shift_text = "/".join(f"{value:g}" for value in theta_shifts) or "n/a"
  lines = [
    "# 杀伤链制导校准热图",
    "",
    "这些图只渲染已经封存的第四、第五阶段证据；未重跑仿真、",
    "未修改 tuning，也未增加默认发布权威。所有热图均按离散采样单元绘制，",
    "不对未采样区域做插值或平滑。",
    "",
    f"- 第四阶段来源：`{_display_path(stage4_path)}`",
    f"- 第五阶段来源：`{_display_path(stage5_path)}`",
    f"- 选择的 nav gain：`{decision_context['selected_nav_gain']}`",
    f"- 默认发布状态：`{decision_context['default_promotion_status']}`",
    "",
    "| 图 | Matrix CSV | PNG | SVG |",
    "| --- | --- | --- | --- |",
  ]
  for artifact_id, artifact in artifacts.items():
    csv_name = Path(artifact["csv"]["path"]).name
    png_name = Path(artifact["png"]["path"]).name
    svg_name = Path(artifact["svg"]["path"]).name
    lines.append(
      f"| `{artifact_id}` | [{csv_name}]({csv_name}) | "
      f"[{png_name}]({png_name}) | [{svg_name}]({svg_name}) |"
    )
  lines.extend(
    [
      "",
      "## 图示结论",
      "",
      (
        "- 第四阶段主网格为 "
        f"`N/M/O = {class_counts['N']}/{class_counts['M']}/{class_counts['O']}`；"
        "N 与 O 分别形成连续内部和连续外部，M 是经过八邻域内缩后保留的"
        "过渡带。"
      ),
      (
        f"- `60 deg` 主网格 robust-hit 区间为 `{sixty_deg_range_text}`；"
        "近端 miss -> hit -> 远端 miss 是单一命中区间，不应解释成射程方向单调。"
      ),
      (
        "- 保守 `rho_edge` 的 robust-hit 中位数为 "
        f"`{stage4_context['robust_hit_rho_edge_median']:.3g}`，robust-miss "
        f"范围为 `{stage4_context['robust_miss_rho_edge_min']:.3g}` 到 "
        f"`{stage4_context['robust_miss_rho_edge_max']:.3g}`；说明分类面主要是"
        "终端几何边界，而不是围绕 `rho=1` 的宽缓过渡。"
      ),
      "- 第五阶段的状态变化全部显示在基线命中边界附近；stage-4 N/O "
      "硬门未被破坏。",
      (
        "- 非基线候选的最大角边界位移取值为 "
        f"`{theta_shift_text} deg`，预注册上限为 `{theta_limit_text}`；"
        "低增益以丢失命中单元换取较低饱和，高增益扩张边界但提高饱和。"
      ),
      "- holdout hit 只作为观察量，不计为材料性收益。因此热图支持保留 "
      "`nav_gain=4`，但不解除机动目标/APN 权威缺口。",
      "",
      "## 第五阶段面板指标",
      "",
      "| nav_gain | Main net hit | Holdout hit | Theta shift deg | Saturation P95 delta |",
      "| ---: | ---: | ---: | ---: | ---: |",
    ]
  )
  for nav_gain, values in sorted(panel_metrics.items(), key=lambda item: float(item[0])):
    lines.append(
      f"| {nav_gain} | {values['main_net_robust_hit_change']:+d} | "
      f"{_metric_text(values['holdout_robust_hit_change'])} | "
      f"{_metric_text(values['theta_fuze_max_displacement_deg'], signed=False)} | "
      f"{_metric_text(values['guidance_saturation_fraction_p95_change'])} |"
    )
  lines.extend(
    [
      "",
      "解释边界：这里只是工程校准诊断，不是真实武器性能、目标易损性或 "
      "Pk 权威。",
    ]
  )
  path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_visualizations(
  *,
  stage4_report_path: Path,
  stage5_report_path: Path,
  output_dir: Path,
  prefix: str = DEFAULT_PREFIX,
  date_stamp: str | None = None,
) -> dict[str, Any]:
  stage4_report_path = stage4_report_path.resolve()
  stage5_report_path = stage5_report_path.resolve()
  stage4 = _read_json(stage4_report_path)
  stage5 = _read_json(stage5_report_path)
  _validate_schema(stage4, STAGE4_SCHEMA_VERSION, label="stage-4 report")
  _validate_schema(stage5, STAGE5_SCHEMA_VERSION, label="stage-5 report")

  stage4_rows = _stage4_main_cells(stage4)
  ranges, offsets = _axis_values(stage4_rows)
  stage4_index = _index_cells(stage4_rows)
  _require_rectangular(
    stage4_index,
    ranges=ranges,
    offsets=offsets,
    label="stage-4 main grid",
  )
  class_matrix = _matrix(
    stage4_index,
    ranges=ranges,
    offsets=offsets,
    getter=lambda row: str(row.get("reclassified_launch_class") or ""),
  )
  unknown_classes = sorted(
    {value for row in class_matrix for value in row} - set(LAUNCH_CLASS_CODES)
  )
  if unknown_classes:
    raise ValueError(f"unknown stage-4 launch classes: {unknown_classes}")
  rho_log_matrix = _matrix(
    stage4_index,
    ranges=ranges,
    offsets=offsets,
    getter=lambda row: math.log10(max(_rho_edge(row), 1e-300)),
  )

  cells_path = _resolve_artifact(
    stage5_report_path,
    _nested_get(stage5, "raw_evidence", "cells_csv")
    or _nested_get(stage5, "artifacts", "cells_csv"),
  )
  grouped = _stage5_main_groups(_read_csv(cells_path))
  baseline_gain = _required_float(
    _nested_get(stage5, "evaluated_scalar", "baseline"),
    field="evaluated_scalar.baseline",
  )
  declared_candidates = [
    _required_float(value, field="evaluated_scalar.candidates")
    for value in list(_nested_get(stage5, "evaluated_scalar", "candidates") or [])
  ]
  candidate_gains = [
    value for value in declared_candidates if not math.isclose(value, baseline_gain)
  ]
  transition_ranges, transition_offsets, transition_values, baseline = (
    _transition_matrices(
      grouped,
      baseline_gain=baseline_gain,
      candidate_gains=candidate_gains,
    )
  )
  if transition_ranges != ranges or transition_offsets != offsets:
    raise ValueError("stage-4 and stage-5 main-grid axes differ")
  _validate_stage4_stage5_baseline_consistency(
    stage4_index,
    baseline,
    ranges=ranges,
    offsets=offsets,
  )

  output_dir.mkdir(parents=True, exist_ok=True)
  stamp = date_stamp or _default_date_stamp(stage5)
  artifacts: dict[str, dict[str, Any]] = {}

  class_base = output_dir / f"{prefix}_stage4_launch_class_heatmap_{stamp}"
  class_csv = class_base.with_suffix(".csv")
  _write_matrix_csv(
    class_csv,
    ranges=ranges,
    offsets=offsets,
    values=class_matrix,
  )
  artifacts["stage4_launch_class"] = _artifact_record(
    class_csv,
    _plot_stage4_classification(
      class_base,
      report=stage4,
      indexed=stage4_index,
      ranges=ranges,
      offsets=offsets,
      raw_classes=class_matrix,
    ),
    description=(
      "Main-grid N/M/O classes, M-cell observed robust state, and raw sampled "
      "refinement boundary without smoothing."
    ),
  )

  rho_base = output_dir / f"{prefix}_stage4_log10_rho_edge_heatmap_{stamp}"
  rho_csv = rho_base.with_suffix(".csv")
  _write_matrix_csv(
    rho_csv,
    ranges=ranges,
    offsets=offsets,
    values=[[f"{value:.12g}" for value in row] for row in rho_log_matrix],
  )
  artifacts["stage4_log10_rho_edge"] = _artifact_record(
    rho_csv,
    _plot_stage4_rho_edge(
      rho_base,
      ranges=ranges,
      offsets=offsets,
      log10_values=rho_log_matrix,
    ),
    description=(
      "Conservative rho_edge heatmap: robust hits use rho_max and robust misses "
      "use rho_min, shown as log10 on the fixed [-4.1, 3.1] scale."
    ),
  )

  transition_base = output_dir / f"{prefix}_stage5_state_changes_vs_N4_heatmap_{stamp}"
  transition_csv = transition_base.with_suffix(".csv")
  _write_transition_csv(
    transition_csv,
    ranges=ranges,
    offsets=offsets,
    matrices=transition_values,
  )
  transition_images, panel_metrics = _plot_stage5_transitions(
    transition_base,
    report=stage5,
    ranges=ranges,
    offsets=offsets,
    matrices=transition_values,
    baseline=baseline,
    baseline_gain=baseline_gain,
  )
  artifacts["stage5_state_changes_vs_N4"] = _artifact_record(
    transition_csv,
    transition_images,
    description=(
      "Four non-baseline nav_gain candidates as robust-state changes relative "
      "to N=4, with the unsmoothed baseline cell boundary and decision metrics."
    ),
  )

  decision_context = {
    "baseline_nav_gain": baseline_gain,
    "selected_nav_gain": _nested_get(stage5, "selection", "selected_nav_gain"),
    "selection_decision": _nested_get(stage5, "selection", "decision"),
    "default_promotion_ready": _nested_get(
      stage5, "selection", "default_promotion_ready"
    ),
    "default_promotion_status": _nested_get(
      stage5, "selection", "default_promotion_status"
    ),
    "theta_fuze_max_displacement_limit_deg": _finite_float(
      _nested_get(
        stage5,
        "selection_policy",
        "regression_allowances",
        "theta_fuze_max_displacement_deg",
      )
    ),
  }
  stage4_context = _stage4_summary_context(
    stage4,
    indexed=stage4_index,
    ranges=ranges,
    offsets=offsets,
  )
  summary_path = output_dir / f"{prefix}_visualization_summary_{stamp}.md"
  _write_summary(
    summary_path,
    stage4_path=stage4_report_path,
    stage5_path=stage5_report_path,
    stage4_context=stage4_context,
    artifacts=artifacts,
    decision_context=decision_context,
    panel_metrics=panel_metrics,
  )
  manifest_path = output_dir / f"{prefix}_visualization_manifest_{stamp}.json"
  manifest: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "status": "guidance_calibration_heatmaps_rendered",
    "source_only_rendering": True,
    "simulation_rerun": False,
    "date_stamp": stamp,
    "prefix": prefix,
    "output_dir": _display_path(output_dir),
    "manifest_path": _display_path(manifest_path),
    "summary": _file_record(summary_path),
    "sources": {
      "stage4_report": {
        **_file_record(stage4_report_path),
        "schema_version": stage4.get("schema_version"),
        "status": stage4.get("status"),
      },
      "stage5_report": {
        **_file_record(stage5_report_path),
        "schema_version": stage5.get("schema_version"),
        "status": stage5.get("status"),
      },
      "stage5_cells_csv": _file_record(cells_path),
    },
    "matrix_scope": {
      "grid_tier": "main",
      "range_km_axis": ranges,
      "absolute_offset_deg_axis": offsets,
      "stage4_cell_count": len(stage4_rows),
      "stage5_baseline_nav_gain": baseline_gain,
      "stage5_candidate_nav_gains": sorted(transition_values),
      "stage5_candidate_cell_count": (
        len(ranges) * len(offsets) * len(transition_values)
      ),
    },
    "decision_context": decision_context,
    "stage4_visual_context": stage4_context,
    "stage5_panel_metrics": panel_metrics,
    "artifacts": artifacts,
    "reproducibility": {
      "matplotlib_backend": "Agg",
      "svg_hashsalt": matplotlib.rcParams["svg.hashsalt"],
      "svg_date_metadata": None,
      "postprocessing_smoothing": False,
      "input_rows_recomputed": False,
      "stage4_stage5_baseline_consistency_checked": True,
    },
    "interpretation_boundary": (
      "engineering calibration diagnostics only; not real weapon performance, "
      "target vulnerability, or Pk authority"
    ),
  }
  _write_json(manifest_path, manifest)
  return manifest


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Render stage-4/5 kill-chain guidance calibration heatmaps from existing "
      "JSON/CSV evidence without rerunning simulation."
    )
  )
  parser.add_argument(
    "--stage4-report",
    type=Path,
    default=DEFAULT_STAGE4_REPORT,
    help="Stage-4 guidance-envelope report JSON.",
  )
  parser.add_argument(
    "--stage5-report",
    type=Path,
    default=DEFAULT_STAGE5_REPORT,
    help="Stage-5 scalar-calibration report JSON.",
  )
  parser.add_argument(
    "--output-dir",
    type=Path,
    required=True,
    help="Directory for matrix CSV, PNG, SVG, summary, and manifest outputs.",
  )
  parser.add_argument("--prefix", default=DEFAULT_PREFIX)
  parser.add_argument(
    "--date-stamp",
    default=None,
    help="Deterministic filename stamp; defaults to the stage-5 report date.",
  )
  args = parser.parse_args(argv)
  manifest = generate_visualizations(
    stage4_report_path=args.stage4_report,
    stage5_report_path=args.stage5_report,
    output_dir=args.output_dir,
    prefix=args.prefix,
    date_stamp=args.date_stamp,
  )
  json.dump(manifest, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
  sys.stdout.write("\n")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
