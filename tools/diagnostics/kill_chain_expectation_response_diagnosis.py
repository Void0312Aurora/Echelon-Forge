#!/usr/bin/env python3
"""Diagnose KCES component-response review cells from before-report rows."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

SCHEMA_VERSION = "a2.kill_chain_expectation_response_diagnosis.v2"
DEFAULT_VARIANT = "REV-RUNTIME-PROJECTION"
DEFAULT_TARGET_MOTION_LAYER = "nonmaneuvering_constant_velocity"
LOW_RESPONSE_PROBABILITY_THRESHOLD = 0.05
WEAK_COMPONENT_LOAD_THRESHOLD = 0.25


def _nested_get(row: dict[str, Any], *path: str) -> Any:
  value: Any = row
  for part in path:
    if not isinstance(value, dict):
      return None
    value = value.get(part)
  return value


def _finite_float(value: Any) -> float | None:
  try:
    out = float(value)
  except Exception:
    return None
  return out if math.isfinite(out) else None


def _safe_ratio(numerator: Any, denominator: Any) -> float | None:
  top = _finite_float(numerator)
  bottom = _finite_float(denominator)
  if top is None or bottom is None or abs(bottom) <= 1.0e-12:
    return None
  return top / bottom


def _int_or_zero(value: Any) -> int:
  try:
    return int(value)
  except Exception:
    return 0


def _bool_or_none(value: Any) -> bool | None:
  if value is None:
    return None
  if isinstance(value, bool):
    return value
  if isinstance(value, str):
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes"}:
      return True
    if lowered in {"false", "0", "no"}:
      return False
  return bool(value)


def _component_detail_rows(row: dict[str, Any]) -> list[dict[str, Any]]:
  detail = dict(row.get("component_detail", {}) or {})
  return [
    dict(item)
    for item in list(detail.get("component_rows", []) or [])
    if isinstance(item, dict)
  ]


def _weak_load_low_response_count(
  *,
  component_rows: list[dict[str, Any]],
) -> int:
  if not component_rows:
    return 0
  return sum(
    1
    for component_row in component_rows
    if (_finite_float(component_row.get("effect_scale")) or 0.0)
    < WEAK_COMPONENT_LOAD_THRESHOLD
    and (_finite_float(component_row.get("failure_probability")) or 0.0)
    < LOW_RESPONSE_PROBABILITY_THRESHOLD
  )


def _read_report(path: Path) -> dict[str, Any]:
  with path.open("r", encoding="utf-8") as handle:
    data = json.load(handle)
  if not isinstance(data, dict):
    raise TypeError(f"expected object JSON at {path}")
  return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2, sort_keys=True, ensure_ascii=True)
    handle.write("\n")


def _selected_rows(
  report: dict[str, Any],
  *,
  variant: str,
  target_motion_layer: str,
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for raw in list(report.get("heatmap_rows", []) or []):
    if not isinstance(raw, dict):
      continue
    if str(_nested_get(raw, "launch_window", "target_motion_layer") or "") != target_motion_layer:
      continue
    if str(_nested_get(raw, "warhead_load_field", "R_effect_variant") or "") != variant:
      continue
    rows.append(raw)
  return rows


def _row_view(row: dict[str, Any]) -> dict[str, Any]:
  detail = dict(row.get("component_detail", {}) or {})
  detail_summary = dict(detail.get("summary", {}) or {})
  detail_rows = _component_detail_rows(row)
  strongest_load_component = dict(
    detail_summary.get("strongest_load_component", {}) or {}
  )
  max_probability_component = dict(
    detail_summary.get("max_probability_component", {}) or {}
  )
  return {
    "case_id": str(_nested_get(row, "identity", "case_id") or ""),
    "range_km": _finite_float(_nested_get(row, "launch_window", "range_km")),
    "signed_bearing_deg": _finite_float(
      _nested_get(row, "launch_window", "signed_bearing_deg")
    ),
    "abs_bearing_deg": abs(
      _finite_float(_nested_get(row, "launch_window", "signed_bearing_deg")) or 0.0
    ),
    "launch_class": str(_nested_get(row, "launch_window", "launch_class") or ""),
    "guidance_expectation_status": str(
      _nested_get(row, "guidance_approach", "guidance_expectation_status") or ""
    ),
    "entered_R_fuze": _bool_or_none(
      _nested_get(row, "guidance_approach", "entered_R_fuze")
    ),
    "rho_fuze": _finite_float(_nested_get(row, "guidance_approach", "rho_fuze")),
    "detonated": _bool_or_none(_nested_get(row, "fuze_decision", "detonated")),
    "effect_band": str(_nested_get(row, "warhead_load_field", "effect_band") or ""),
    "rho_effect_case": _finite_float(
      _nested_get(row, "warhead_load_field", "rho_effect_case")
    ),
    "component_load_row_count": _int_or_zero(
      _nested_get(row, "warhead_load_field", "component_load_row_count")
    ),
    "strongest_component_effect_scale": _finite_float(
      _nested_get(row, "warhead_load_field", "strongest_component_effect_scale")
    ),
    "weakest_component_effect_scale": _finite_float(
      _nested_get(row, "warhead_load_field", "weakest_component_effect_scale")
    ),
    "component_response_row_count": _int_or_zero(
      _nested_get(row, "component_response", "component_response_row_count")
    ),
    "max_failure_probability": _finite_float(
      _nested_get(row, "component_response", "max_failure_probability")
    ),
    "sampled_failure_count": _int_or_zero(
      _nested_get(row, "component_response", "sampled_failure_count")
    ),
    "min_integrity_delta": _finite_float(
      _nested_get(row, "component_response", "min_integrity_delta")
    ),
    "primary_failure_mode": str(
      _nested_get(row, "component_response", "primary_failure_mode") or ""
    ),
    "component_response_band": str(
      _nested_get(row, "component_response", "component_response_band") or ""
    ),
    "component_hit_count": _int_or_zero(
      _nested_get(row, "consequence_projection", "component_hit_count")
    ),
    "component_failure_count": _int_or_zero(
      _nested_get(row, "consequence_projection", "component_failure_count")
    ),
    "primary_component_system": str(
      _nested_get(row, "consequence_projection", "primary_component_system") or ""
    ),
    "component_detail_row_count": _int_or_zero(
      detail_summary.get("component_detail_row_count") or len(detail_rows)
    ),
    "detail_sampled_failure_count": _int_or_zero(
      detail_summary.get("sampled_failure_detail_count")
    ),
    "detail_weak_load_low_response_count": _weak_load_low_response_count(
      component_rows=detail_rows,
    ),
    "detail_strongest_load_component_name": str(
      strongest_load_component.get("component_name", "") or ""
    ),
    "detail_strongest_load_component_system": str(
      strongest_load_component.get("component_system", "") or ""
    ),
    "detail_strongest_load_effect_scale": _finite_float(
      strongest_load_component.get("effect_scale")
    ),
    "detail_strongest_load_rho_effect_component": _finite_float(
      strongest_load_component.get("rho_effect_component")
    ),
    "detail_max_probability_component_name": str(
      max_probability_component.get("component_name", "") or ""
    ),
    "detail_max_probability_component_system": str(
      max_probability_component.get("component_system", "") or ""
    ),
    "detail_max_probability": _finite_float(
      max_probability_component.get("failure_probability")
    ),
    "detail_max_probability_effect_scale": _finite_float(
      max_probability_component.get("effect_scale")
    ),
    "detail_max_probability_sampled_failure": _bool_or_none(
      max_probability_component.get("sampled_failure")
    ),
  }


def _is_component_response_candidate(row: dict[str, Any]) -> bool:
  view = _row_view(row)
  if view["launch_class"] != "N":
    return False
  if view["guidance_expectation_status"] != "satisfied":
    return False
  if view["entered_R_fuze"] is not True or view["detonated"] is not True:
    return False
  if str(view["effect_band"]) not in {"core", "effective", "outer_effective", "edge"}:
    return False
  if int(view["sampled_failure_count"]) > 0:
    return False
  return str(view["component_response_band"]) in {
    "observed_probability_only",
    "no_response_rows",
    "unclassified_component_response",
  }


def _is_baseline_response(row: dict[str, Any]) -> bool:
  view = _row_view(row)
  return (
    view["launch_class"] == "N"
    and view["guidance_expectation_status"] == "satisfied"
    and view["entered_R_fuze"] is True
    and view["detonated"] is True
    and int(view["sampled_failure_count"]) > 0
  )


def _nearest_baseline(candidate: dict[str, Any], baselines: list[dict[str, Any]]) -> dict[str, Any] | None:
  c_view = _row_view(candidate)
  c_range = c_view["range_km"]
  c_abs_bearing = c_view["abs_bearing_deg"]
  c_bearing = c_view["signed_bearing_deg"] or 0.0
  if c_range is None:
    return None
  same_range = [
    row
    for row in baselines
    if _row_view(row)["range_km"] == c_range
    and (_row_view(row)["abs_bearing_deg"] or 0.0) <= (c_abs_bearing or 0.0)
  ]
  if not same_range:
    same_range = [row for row in baselines if _row_view(row)["range_km"] == c_range]
  if not same_range:
    same_range = baselines
  if not same_range:
    return None

  def _sign_mismatch(row: dict[str, Any]) -> int:
    b_bearing = _row_view(row)["signed_bearing_deg"] or 0.0
    if abs(c_bearing) <= 1.0e-9 or abs(b_bearing) <= 1.0e-9:
      return 1 if abs(c_bearing) > 1.0e-9 else 0
    return 0 if (c_bearing > 0.0) == (b_bearing > 0.0) else 1

  return min(
    same_range,
    key=lambda row: (
      abs((_row_view(row)["range_km"] or 0.0) - (c_range or 0.0)),
      abs((_row_view(row)["abs_bearing_deg"] or 0.0) - (c_abs_bearing or 0.0)),
      _sign_mismatch(row),
      abs(_row_view(row)["signed_bearing_deg"] or 0.0),
    ),
  )


def _diagnosis_bucket(candidate: dict[str, Any]) -> tuple[str, str]:
  effect_band = str(candidate["effect_band"])
  max_probability = candidate["max_failure_probability"] or 0.0
  strongest = candidate["strongest_component_effect_scale"] or 0.0
  sampled = int(candidate["sampled_failure_count"] or 0)

  if sampled > 0:
    return (
      "sampled_response_observed",
      "sampled component failure is already present; no response residual",
    )
  if max_probability >= LOW_RESPONSE_PROBABILITY_THRESHOLD:
    return (
      "sampling_only_review",
      "response probability is not low; inspect seed/sample behavior before load retuning",
    )
  if strongest < WEAK_COMPONENT_LOAD_THRESHOLD and effect_band == "outer_effective":
    return (
      "outer_effect_low_component_load_probability_cliff",
      "case-level outer-effective band maps to weak component load and very low response probability",
    )
  if strongest < WEAK_COMPONENT_LOAD_THRESHOLD:
    return (
      "weak_component_load_probability_cliff",
      "component load scale is weak and response probability is very low",
    )
  return (
    "response_curve_probability_cliff",
    "component load scale is present but response probability remains very low",
  )


def _component_detail_projection_signal(candidate: dict[str, Any]) -> tuple[str, str]:
  detail_count = int(candidate.get("component_detail_row_count") or 0)
  if detail_count <= 0:
    return (
      "component_detail_missing",
      "before report does not preserve per-component load/response details",
    )
  weak_count = int(candidate.get("detail_weak_load_low_response_count") or 0)
  top_effect = candidate.get("detail_max_probability_effect_scale")
  top_probability = candidate.get("detail_max_probability")
  strongest_effect = candidate.get("detail_strongest_load_effect_scale")
  if weak_count == detail_count:
    return (
      "all_component_rows_weak_load_low_response",
      "all preserved component rows combine weak load scale with low response probability",
    )
  if (
    top_effect is not None
    and top_probability is not None
    and float(top_effect) < WEAK_COMPONENT_LOAD_THRESHOLD
    and float(top_probability) < LOW_RESPONSE_PROBABILITY_THRESHOLD
  ):
    return (
      "top_probability_component_weak_load_low_response",
      "highest-probability component is still weak-load / low-response",
    )
  if strongest_effect is not None and float(strongest_effect) < WEAK_COMPONENT_LOAD_THRESHOLD:
    return (
      "strongest_load_component_below_review_threshold",
      "strongest preserved component load is below the weak-load review threshold",
    )
  return (
    "response_curve_review_after_load",
    "component load detail is not weak enough to explain the low response alone",
  )


def _diagnose_candidate(
  row: dict[str, Any],
  *,
  baseline: dict[str, Any] | None,
) -> dict[str, Any]:
  candidate = _row_view(row)
  baseline_view = _row_view(baseline) if baseline is not None else {}
  bucket, reason = _diagnosis_bucket(candidate)
  detail_projection_signal, detail_projection_reason = (
    _component_detail_projection_signal(candidate)
  )
  probability_ratio = _safe_ratio(
    candidate.get("max_failure_probability"),
    baseline_view.get("max_failure_probability"),
  )
  strongest_load_ratio = _safe_ratio(
    candidate.get("strongest_component_effect_scale"),
    baseline_view.get("strongest_component_effect_scale"),
  )
  integrity_ratio = _safe_ratio(
    abs(candidate.get("min_integrity_delta") or 0.0),
    abs(baseline_view.get("min_integrity_delta") or 0.0),
  )
  return {
    **candidate,
    "diagnosis_bucket": bucket,
    "diagnosis_reason": reason,
    "detail_projection_signal": detail_projection_signal,
    "detail_projection_reason": detail_projection_reason,
    "baseline_case_id": baseline_view.get("case_id", ""),
    "baseline_abs_bearing_deg": baseline_view.get("abs_bearing_deg"),
    "baseline_effect_band": baseline_view.get("effect_band", ""),
    "baseline_strongest_component_effect_scale": baseline_view.get(
      "strongest_component_effect_scale"
    ),
    "baseline_max_failure_probability": baseline_view.get("max_failure_probability"),
    "baseline_sampled_failure_count": baseline_view.get("sampled_failure_count"),
    "baseline_min_integrity_delta": baseline_view.get("min_integrity_delta"),
    "strongest_load_ratio_to_baseline": strongest_load_ratio,
    "max_probability_ratio_to_baseline": probability_ratio,
    "abs_integrity_delta_ratio_to_baseline": integrity_ratio,
  }


def _write_detail_csv(path: Path, *, rows: list[dict[str, Any]]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  fields = [
    "case_id",
    "range_km",
    "signed_bearing_deg",
    "diagnosis_bucket",
    "diagnosis_reason",
    "detail_projection_signal",
    "detail_projection_reason",
    "effect_band",
    "rho_effect_case",
    "component_load_row_count",
    "strongest_component_effect_scale",
    "weakest_component_effect_scale",
    "component_response_row_count",
    "max_failure_probability",
    "sampled_failure_count",
    "min_integrity_delta",
    "primary_failure_mode",
    "primary_component_system",
    "component_detail_row_count",
    "detail_weak_load_low_response_count",
    "detail_strongest_load_component_name",
    "detail_strongest_load_component_system",
    "detail_strongest_load_effect_scale",
    "detail_strongest_load_rho_effect_component",
    "detail_max_probability_component_name",
    "detail_max_probability_component_system",
    "detail_max_probability",
    "detail_max_probability_effect_scale",
    "detail_max_probability_sampled_failure",
    "baseline_case_id",
    "baseline_abs_bearing_deg",
    "baseline_effect_band",
    "baseline_strongest_component_effect_scale",
    "baseline_max_failure_probability",
    "baseline_sampled_failure_count",
    "baseline_min_integrity_delta",
    "strongest_load_ratio_to_baseline",
    "max_probability_ratio_to_baseline",
    "abs_integrity_delta_ratio_to_baseline",
  ]
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(
      handle,
      fieldnames=fields,
      extrasaction="ignore",
      lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)


def _write_matrix_csv(path: Path, *, rows: list[dict[str, Any]]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  ranges = sorted({float(row["range_km"]) for row in rows if row.get("range_km") is not None})
  bearings = sorted(
    {
      float(row["signed_bearing_deg"])
      for row in rows
      if row.get("signed_bearing_deg") is not None
    }
  )
  by_cell = {
    (row["range_km"], row["signed_bearing_deg"]): row
    for row in rows
  }
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["range_km"] + [f"{bearing:g}" for bearing in bearings])
    for range_km in ranges:
      values = []
      for bearing in bearings:
        row = by_cell.get((range_km, bearing))
        values.append("" if row is None else row["diagnosis_bucket"])
      writer.writerow([f"{range_km:g}", *values])


def _plot_probability_scatter(
  path_base: Path,
  *,
  rows: list[dict[str, Any]],
  variant: str,
  target_motion_layer: str,
) -> dict[str, str]:
  fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=160)
  colors = {
    "outer_effect_low_component_load_probability_cliff": "#2f9e71",
    "weak_component_load_probability_cliff": "#7bc8a4",
    "response_curve_probability_cliff": "#4d9de0",
    "sampling_only_review": "#f4d35e",
  }
  for row in rows:
    x = row.get("rho_effect_case")
    y = row.get("max_failure_probability")
    if x is None or y is None:
      continue
    bearing = float(row.get("signed_bearing_deg") or 0.0)
    # Signed mirror cells can have almost identical x/y values; a tiny visual
    # jitter keeps the labels readable without changing the reported CSV data.
    x_plot = float(x) + (0.0014 if bearing > 0.0 else -0.0014 if bearing < 0.0 else 0.0)
    y_plot = float(y) + (0.00045 if bearing > 0.0 else -0.00045 if bearing < 0.0 else 0.0)
    bucket = str(row["diagnosis_bucket"])
    ax.scatter(
      x_plot,
      y_plot,
      s=80,
      color=colors.get(bucket, "#8d8d8d"),
      edgecolors="#111111",
      linewidths=0.6,
      label=bucket,
    )
    ax.text(
      x_plot + 0.001,
      y_plot + (0.00032 if bearing >= 0.0 else -0.00032),
      f"{float(row['range_km']):g}km/{bearing:+g}",
      fontsize=7,
      va="bottom" if bearing >= 0.0 else "top",
    )
  handles, labels = ax.get_legend_handles_labels()
  dedup: dict[str, Any] = {}
  for handle, label in zip(handles, labels, strict=True):
    dedup.setdefault(label, handle)
  if dedup:
    ax.legend(dedup.values(), dedup.keys(), fontsize=7, loc="best")
  ax.axhline(
    LOW_RESPONSE_PROBABILITY_THRESHOLD,
    color="#c43c39",
    linestyle="--",
    linewidth=1.0,
    label="low response threshold",
  )
  ax.set_title(f"Component Response Diagnosis ({variant})", fontsize=12)
  ax.set_xlabel("rho_effect_case")
  ax.set_ylabel("max_failure_probability")
  ax.grid(True, alpha=0.25)
  ax.text(
    0.0,
    -0.18,
    f"target_motion_layer={target_motion_layer}; engineering-proxy diagnostics only",
    transform=ax.transAxes,
    fontsize=8,
    color="#555555",
  )
  fig.tight_layout()
  png_path = path_base.with_suffix(".png")
  svg_path = path_base.with_suffix(".svg")
  fig.savefig(png_path)
  fig.savefig(svg_path)
  plt.close(fig)
  return {"png": str(png_path), "svg": str(svg_path)}


def _summary_markdown(
  *,
  input_path: Path,
  manifest: dict[str, Any],
  rows: list[dict[str, Any]],
) -> str:
  bucket_counts = dict(sorted(Counter(row["diagnosis_bucket"] for row in rows).items()))
  projection_signal_counts = dict(
    sorted(Counter(row["detail_projection_signal"] for row in rows).items())
  )
  lines = [
    "# KCES Component-Response Local Diagnosis",
    "",
    "This report consumes existing before-report rows and inspects the cells",
    "already attributed to `component_response`. It is a report-level local",
    "diagnostic; it does not rerun simulation, edit parameters, or claim real",
    "weapon / target / Pk authority.",
    "",
    "Boundary: engineering-proxy diagnostics only.",
    "",
    "## Source",
    "",
    f"- Input: `{input_path}`",
    f"- Variant: `{manifest['variant']}`",
    f"- Target motion layer: `{manifest['target_motion_layer']}`",
    f"- Candidate rows: `{manifest['candidate_row_count']}`",
    f"- Baseline rows: `{manifest['baseline_row_count']}`",
    f"- Diagnosis buckets: `{bucket_counts}`",
    f"- Detail projection signals: `{projection_signal_counts}`",
    "",
    "## Artifacts",
    "",
    f"- Manifest JSON: `{Path(manifest['manifest_path']).name}`",
    f"- Detail CSV: `{Path(manifest['detail_csv']).name}`",
    f"- Matrix CSV: `{Path(manifest['matrix_csv']).name}`",
    f"- Probability scatter PNG: `{Path(manifest['scatter_png']).name}`",
    f"- Probability scatter SVG: `{Path(manifest['scatter_svg']).name}`",
    "",
    "## Candidate Rows",
    "",
  ]
  for row in rows:
    lines.append(
      f"- `{row['case_id']}`: range_km=`{row['range_km']}`, "
      f"signed_bearing_deg=`{row['signed_bearing_deg']}`, "
      f"rho_effect_case=`{row['rho_effect_case']}`, "
      f"strongest_component_effect_scale=`{row['strongest_component_effect_scale']}`, "
      f"max_failure_probability=`{row['max_failure_probability']}`, "
      f"detail_projection_signal=`{row['detail_projection_signal']}`, "
      f"detail_top_component=`{row['detail_max_probability_component_name']}`, "
      f"baseline=`{row['baseline_case_id']}`, "
      f"probability_ratio=`{row['max_probability_ratio_to_baseline']}`"
    )
  lines.extend(
    [
      "",
      "## Interpretation",
      "",
      "- All selected rows have guidance / fuze / case-level load facts, but no",
      "  sampled component failure.",
      "- The current six cells fall into a report-level probability cliff: the",
      "  case-level `outer_effective` band maps to weak component load scale and",
      "  very low max failure probability.",
      "- When per-component details are present, `detail_projection_signal`",
      "  separates a weak component-load projection from a response-curve-only",
      "  explanation.",
    ]
  )
  return "\n".join(lines) + "\n"


def generate_response_diagnosis(
  *,
  input_path: Path,
  output_dir: Path,
  prefix: str = "kces_anchor_cv",
  variant: str = DEFAULT_VARIANT,
  target_motion_layer: str = DEFAULT_TARGET_MOTION_LAYER,
  date_stamp: str | None = None,
) -> dict[str, Any]:
  report = _read_report(input_path)
  selected = _selected_rows(
    report,
    variant=variant,
    target_motion_layer=target_motion_layer,
  )
  candidates = [row for row in selected if _is_component_response_candidate(row)]
  baselines = [row for row in selected if _is_baseline_response(row)]
  rows = [
    _diagnose_candidate(row, baseline=_nearest_baseline(row, baselines))
    for row in candidates
  ]
  output_dir.mkdir(parents=True, exist_ok=True)
  stamp = date_stamp or datetime.now().strftime("%Y%m%d")
  manifest_path = output_dir / f"{prefix}_response_diagnosis_manifest_{stamp}.json"
  summary_path = output_dir / f"{prefix}_response_diagnosis_summary_{stamp}.md"
  detail_csv = output_dir / f"{prefix}_response_diagnosis_detail_{stamp}.csv"
  matrix_csv = output_dir / f"{prefix}_response_diagnosis_matrix_{stamp}.csv"
  scatter_base = output_dir / f"{prefix}_response_diagnosis_probability_scatter_{stamp}"

  _write_detail_csv(detail_csv, rows=rows)
  _write_matrix_csv(matrix_csv, rows=rows)
  scatter = _plot_probability_scatter(
    scatter_base,
    rows=rows,
    variant=variant,
    target_motion_layer=target_motion_layer,
  )
  bucket_counts = dict(sorted(Counter(row["diagnosis_bucket"] for row in rows).items()))
  projection_signal_counts = dict(
    sorted(Counter(row["detail_projection_signal"] for row in rows).items())
  )
  manifest: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "status": "generated",
    "input_path": str(input_path),
    "manifest_path": str(manifest_path),
    "summary_markdown": str(summary_path),
    "output_dir": str(output_dir),
    "prefix": str(prefix),
    "variant": str(variant),
    "target_motion_layer": str(target_motion_layer),
    "date_stamp": str(stamp),
    "selected_row_count": len(selected),
    "candidate_row_count": len(rows),
    "baseline_row_count": len(baselines),
    "diagnosis_bucket_counts": bucket_counts,
    "detail_projection_signal_counts": projection_signal_counts,
    "detail_csv": str(detail_csv),
    "matrix_csv": str(matrix_csv),
    "scatter_png": scatter["png"],
    "scatter_svg": scatter["svg"],
    "thresholds": {
      "low_response_probability": LOW_RESPONSE_PROBABILITY_THRESHOLD,
      "weak_component_load": WEAK_COMPONENT_LOAD_THRESHOLD,
    },
    "rows": rows,
    "boundary": {
      "authority_level": "engineering_proxy_diagnostics_only",
      "runtime_parameter_retuning": False,
      "real_weapon_or_target_authority": False,
      "calibration_verdict": False,
    },
  }
  _write_json(manifest_path, manifest)
  summary_path.write_text(
    _summary_markdown(input_path=input_path, manifest=manifest, rows=rows),
    encoding="utf-8",
  )
  return manifest


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Diagnose KCES component-response review cells from a before report."
  )
  parser.add_argument("--input", required=True, type=Path, help="Before-report JSON path.")
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=None,
    help="Output directory. Defaults to the input file directory.",
  )
  parser.add_argument("--prefix", default="kces_anchor_cv")
  parser.add_argument("--variant", default=DEFAULT_VARIANT)
  parser.add_argument("--target-motion-layer", default=DEFAULT_TARGET_MOTION_LAYER)
  parser.add_argument(
    "--date-stamp",
    default=None,
    help="Filename date stamp, for example 20260628. Defaults to today.",
  )
  args = parser.parse_args(argv)

  manifest = generate_response_diagnosis(
    input_path=args.input,
    output_dir=args.output_dir or args.input.parent,
    prefix=args.prefix,
    variant=args.variant,
    target_motion_layer=args.target_motion_layer,
    date_stamp=args.date_stamp,
  )
  json.dump(manifest, sys.stdout, indent=2, sort_keys=True, ensure_ascii=True)
  sys.stdout.write("\n")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
