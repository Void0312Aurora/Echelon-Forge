#!/usr/bin/env python3
"""Apply the air-to-air kill-chain expectation envelope to KCES report rows."""

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


SCHEMA_VERSION = "a2.kill_chain_expectation_envelope_audit.v1"
ENVELOPE_SCHEMA_VERSION = "a2.kill_chain_expectation_envelope.v0"
DEFAULT_VARIANT = "REV-RUNTIME-PROJECTION"
DEFAULT_TARGET_MOTION_LAYER = "nonmaneuvering_constant_velocity"
RESPONSE_ORDER = {
  "no_component_response": 0,
  "trace_response": 1,
  "weak_response": 2,
  "nontrivial_response": 3,
  "material_response": 4,
  "severe_response": 5,
}
EXPECTED_RESPONSE_FLOORS = {
  "core": "material_response",
  "effective": "nontrivial_response",
  "outer_effective": "weak_response",
  "edge": "trace_response",
  "outside_effect": "no_component_response",
}


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


def _band_rank(value: str) -> int:
  return RESPONSE_ORDER.get(str(value), -1)


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
    motion_layer = str(
      _nested_get(raw, "launch_window", "target_motion_layer") or ""
    )
    effect_variant = str(
      _nested_get(raw, "warhead_load_field", "R_effect_variant") or ""
    )
    if motion_layer == target_motion_layer and effect_variant == variant:
      rows.append(raw)
  return rows


def quantize_component_response(row: dict[str, Any]) -> dict[str, Any]:
  n_rows = _int_or_zero(
    _nested_get(row, "component_response", "component_response_row_count")
  )
  p_max = _finite_float(
    _nested_get(row, "component_response", "max_failure_probability")
  )
  min_delta = _finite_float(
    _nested_get(row, "component_response", "min_integrity_delta")
  )
  delta_abs = max(0.0, -(min_delta or 0.0))
  n_sampled = _int_or_zero(
    _nested_get(row, "component_response", "sampled_failure_count")
  )

  if n_rows <= 0:
    band = "no_component_response"
  elif p_max is None or min_delta is None:
    band = "unknown_component_response"
  elif p_max >= 0.70 or delta_abs >= 0.35:
    band = "severe_response"
  elif p_max >= 0.30 or delta_abs >= 0.15:
    band = "material_response"
  elif p_max >= 0.10 or delta_abs >= 0.05:
    band = "nontrivial_response"
  elif p_max >= 0.02 or delta_abs >= 0.02:
    band = "weak_response"
  else:
    band = "trace_response"

  return {
    "component_response_quantized_band": band,
    "component_response_sampled_failure_observed": n_sampled > 0,
    "component_response_quantization_schema": (
      "a2.kill_chain_component_response_quantization.v0"
    ),
    "p_max": p_max,
    "delta_abs": delta_abs,
    "n_sampled": n_sampled,
    "n_rows": n_rows,
  }


def _component_response_expectation_status(
  *,
  effect_band: str,
  response_band: str,
) -> str:
  if effect_band in {"", "unclassified_missing_R_effect", "not_evaluated"}:
    return "not_applicable_no_effect_band"
  if response_band == "unknown_component_response":
    return "not_judged_missing_metadata"
  if effect_band == "outside_effect":
    return (
      "negative_control_pressure"
      if _band_rank(response_band) >= _band_rank("nontrivial_response")
      else "satisfied"
    )
  if effect_band == "edge":
    if _band_rank(response_band) >= _band_rank("material_response"):
      return "negative_control_pressure"
    return "satisfied" if _band_rank(response_band) >= _band_rank("trace_response") else "below_expected_floor"
  floor = EXPECTED_RESPONSE_FLOORS.get(effect_band)
  if floor is None:
    return "not_applicable_no_effect_band"
  if _band_rank(response_band) >= _band_rank(floor):
    return "satisfied"
  if effect_band == "outer_effective" and response_band == "trace_response":
    return "below_outer_effective_floor"
  return "below_expected_floor"


def _missing_guidance_metadata(row: dict[str, Any]) -> bool:
  return _nested_get(row, "guidance_approach", "R_fuze_m") is None


def _missing_effect_metadata(row: dict[str, Any]) -> bool:
  variant = str(_nested_get(row, "warhead_load_field", "R_effect_variant") or "")
  effect_band = str(_nested_get(row, "warhead_load_field", "effect_band") or "")
  if not variant or variant == "not_evaluated":
    return True
  if effect_band == "unclassified_missing_R_effect":
    return True
  if _nested_get(row, "warhead_load_field", "R_effect_m") is None:
    return True
  return False


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
  launch_class = str(_nested_get(row, "launch_window", "launch_class") or "")
  effect_band = str(_nested_get(row, "warhead_load_field", "effect_band") or "")
  entered_r_fuze = _bool_or_none(
    _nested_get(row, "guidance_approach", "entered_R_fuze")
  )
  quantized = quantize_component_response(row)
  response_band = str(quantized["component_response_quantized_band"])
  response_status = _component_response_expectation_status(
    effect_band=effect_band,
    response_band=response_band,
  )
  guidance_status = str(
    _nested_get(row, "guidance_approach", "guidance_expectation_status") or ""
  )
  if _missing_guidance_metadata(row):
    cell_status = "not_judged_missing_metadata"
    owner_stage = "harness_metadata"
  elif launch_class == "N" and entered_r_fuze is not True:
    cell_status = "guidance_or_model_residual"
    owner_stage = "launch_window -> guidance_approach"
  elif launch_class == "O":
    negative_control_pressure = (
      guidance_status == "negative_control_alert"
      or _band_rank(response_band) >= _band_rank("nontrivial_response")
    )
    cell_status = (
      "negative_control_pressure" if negative_control_pressure else "satisfied"
    )
    owner_stage = (
      "launch_window -> warhead_load_field"
      if negative_control_pressure
      else "negative_control_satisfied"
    )
  elif launch_class == "M":
    cell_status = "boundary_observation"
    owner_stage = "launch_window"
  elif _missing_effect_metadata(row):
    cell_status = "not_judged_missing_metadata"
    owner_stage = "harness_metadata"
  elif response_status == "negative_control_pressure":
    cell_status = "negative_control_pressure"
    owner_stage = "warhead_load_field"
  elif response_status in {"below_expected_floor", "below_outer_effective_floor"}:
    cell_status = response_status
    owner_stage = "warhead_load_field -> component_response"
  elif response_status == "not_judged_missing_metadata":
    cell_status = "not_judged_missing_metadata"
    owner_stage = "component_response"
  else:
    cell_status = "satisfied"
    owner_stage = "no_review_pressure"

  return {
    "schema_version": ENVELOPE_SCHEMA_VERSION,
    "profile_id": str(_nested_get(row, "identity", "profile_id") or ""),
    "case_id": str(_nested_get(row, "identity", "case_id") or ""),
    "grid_tier": str(_nested_get(row, "identity", "grid_tier") or ""),
    "target_motion_layer": str(
      _nested_get(row, "launch_window", "target_motion_layer") or ""
    ),
    "range_km": _finite_float(_nested_get(row, "launch_window", "range_km")),
    "signed_bearing_deg": _finite_float(
      _nested_get(row, "launch_window", "signed_bearing_deg")
    ),
    "launch_class": launch_class,
    "R_effect_variant": str(
      _nested_get(row, "warhead_load_field", "R_effect_variant") or ""
    ),
    "R_effect_source": str(
      _nested_get(row, "warhead_load_field", "R_effect_source") or ""
    ),
    "guidance_expectation_status": str(
      _nested_get(row, "guidance_approach", "guidance_expectation_status") or ""
    ),
    "entered_R_fuze": entered_r_fuze,
    "rho_fuze": _finite_float(_nested_get(row, "guidance_approach", "rho_fuze")),
    "detonated": _bool_or_none(_nested_get(row, "fuze_decision", "detonated")),
    "R_effect_m": _finite_float(
      _nested_get(row, "warhead_load_field", "R_effect_m")
    ),
    "effect_band": effect_band,
    "rho_effect_case": _finite_float(
      _nested_get(row, "warhead_load_field", "rho_effect_case")
    ),
    "component_response_quantized_band": response_band,
    "component_response_sampled_failure_observed": bool(
      quantized["component_response_sampled_failure_observed"]
    ),
    "component_response_expectation_status": response_status,
    "envelope_cell_status": cell_status,
    "envelope_owner_stage": owner_stage,
    "p_max": quantized["p_max"],
    "delta_abs": quantized["delta_abs"],
    "n_sampled": quantized["n_sampled"],
    "n_rows": quantized["n_rows"],
  }


def _axis(rows: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
  ranges = sorted(
    {
      value
      for value in (_finite_float(item.get("range_km")) for item in rows)
      if value is not None
    }
  )
  bearings = sorted(
    {
      value
      for value in (_finite_float(item.get("signed_bearing_deg")) for item in rows)
      if value is not None
    }
  )
  return ranges, bearings


def _write_detail_csv(path: Path, *, rows: list[dict[str, Any]]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  fields = [
    "case_id",
    "range_km",
    "signed_bearing_deg",
    "launch_class",
    "R_effect_variant",
    "R_effect_source",
    "guidance_expectation_status",
    "entered_R_fuze",
    "rho_fuze",
    "detonated",
    "R_effect_m",
    "effect_band",
    "rho_effect_case",
    "component_response_quantized_band",
    "component_response_sampled_failure_observed",
    "component_response_expectation_status",
    "envelope_cell_status",
    "envelope_owner_stage",
    "p_max",
    "delta_abs",
    "n_sampled",
    "n_rows",
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


def _write_matrix_csv(
  path: Path,
  *,
  rows: list[dict[str, Any]],
  ranges: list[float],
  bearings: list[float],
) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  by_cell = {
    (row.get("range_km"), row.get("signed_bearing_deg")): row
    for row in rows
  }
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["range_km"] + [f"{bearing:g}" for bearing in bearings])
    for range_km in ranges:
      values = []
      for bearing in bearings:
        row = by_cell.get((range_km, bearing))
        values.append("" if row is None else str(row["envelope_cell_status"]))
      writer.writerow([f"{range_km:g}", *values])


def _group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
  by_launch = Counter(row["launch_class"] for row in rows)
  by_effect = Counter(row["effect_band"] for row in rows)
  by_response = Counter(row["component_response_quantized_band"] for row in rows)
  by_status = Counter(row["envelope_cell_status"] for row in rows)
  by_owner = Counter(row["envelope_owner_stage"] for row in rows)
  return {
    "launch_class_counts": dict(sorted(by_launch.items())),
    "effect_band_counts": dict(sorted(by_effect.items())),
    "component_response_quantized_band_counts": dict(sorted(by_response.items())),
    "envelope_cell_status_counts": dict(sorted(by_status.items())),
    "envelope_owner_stage_counts": dict(sorted(by_owner.items())),
  }


def _summary_markdown(
  *,
  input_path: Path,
  manifest: dict[str, Any],
  rows: list[dict[str, Any]],
) -> str:
  group_summary = _group_summary(rows)
  review_rows = [
    row
    for row in rows
    if row["envelope_cell_status"]
    not in {"satisfied", "boundary_observation"}
  ]
  lines = [
    "# KCES Expectation Envelope Audit",
    "",
    "This report applies the standards-layer air-to-air kill-chain expectation",
    "envelope to existing KCES before-report rows. It is a read-only review",
    "artifact; it does not rerun simulation, edit parameters, or grant",
    "calibration authority.",
    "",
    "Boundary: standards planning supplement / engineering-proxy diagnostics only.",
    "",
    "## Source",
    "",
    f"- Input: `{input_path}`",
    f"- Variant: `{manifest['variant']}`",
    f"- Target motion layer: `{manifest['target_motion_layer']}`",
    f"- Selected rows: `{manifest['selected_row_count']}`",
    f"- Envelope status counts: `{group_summary['envelope_cell_status_counts']}`",
    f"- Owner-stage counts: `{group_summary['envelope_owner_stage_counts']}`",
    "",
    "## Artifacts",
    "",
    f"- Manifest JSON: `{Path(manifest['manifest_path']).name}`",
    f"- Detail CSV: `{Path(manifest['detail_csv']).name}`",
    f"- Status matrix CSV: `{Path(manifest['matrix_csv']).name}`",
    "",
    "## Review Rows",
    "",
  ]
  if not review_rows:
    lines.append("- No non-satisfied envelope rows were selected.")
  for row in review_rows:
    lines.append(
      f"- `{row['case_id']}`: status=`{row['envelope_cell_status']}`, "
      f"owner=`{row['envelope_owner_stage']}`, "
      f"launch=`{row['launch_class']}`, effect=`{row['effect_band']}`, "
      f"response=`{row['component_response_quantized_band']}`, "
      f"p_max=`{row['p_max']}`, delta_abs=`{row['delta_abs']}`"
    )
  lines.extend(
    [
      "",
      "## Interpretation",
      "",
      "- `guidance_or_model_residual` belongs to launch-window / guidance review.",
      "- `below_outer_effective_floor` means the cell entered the effect envelope",
      "  but only produced `trace_response`; it belongs to load / response factor",
      "  decomposition rather than direct guidance or fuze retuning.",
      "- `negative_control_pressure` means an outside or edge cell responded too",
      "  strongly for the envelope.",
    ]
  )
  return "\n".join(lines) + "\n"


def generate_envelope_audit(
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
  if not selected:
    raise ValueError(
      "no heatmap rows matched "
      f"variant={variant!r}, target_motion_layer={target_motion_layer!r}"
    )
  rows = [audit_row(row) for row in selected]
  ranges, bearings = _axis(rows)
  output_dir.mkdir(parents=True, exist_ok=True)
  stamp = date_stamp or datetime.now().strftime("%Y%m%d")

  manifest_path = output_dir / f"{prefix}_expectation_envelope_manifest_{stamp}.json"
  summary_path = output_dir / f"{prefix}_expectation_envelope_summary_{stamp}.md"
  detail_csv = output_dir / f"{prefix}_expectation_envelope_detail_{stamp}.csv"
  matrix_csv = output_dir / f"{prefix}_expectation_envelope_matrix_{stamp}.csv"

  _write_detail_csv(detail_csv, rows=rows)
  _write_matrix_csv(matrix_csv, rows=rows, ranges=ranges, bearings=bearings)
  group_summary = _group_summary(rows)
  manifest: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "status": "generated",
    "envelope_schema_version": ENVELOPE_SCHEMA_VERSION,
    "input_path": str(input_path),
    "manifest_path": str(manifest_path),
    "summary_markdown": str(summary_path),
    "output_dir": str(output_dir),
    "prefix": str(prefix),
    "variant": str(variant),
    "target_motion_layer": str(target_motion_layer),
    "date_stamp": str(stamp),
    "selected_row_count": len(rows),
    "range_km_axis": ranges,
    "signed_bearing_deg_axis": bearings,
    **group_summary,
    "detail_csv": str(detail_csv),
    "matrix_csv": str(matrix_csv),
    "rows": rows,
    "boundary": {
      "authority_level": "standards_planning_supplement",
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
    description="Apply the KCES expectation envelope to a before report."
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
    help="Filename date stamp, for example 20260706. Defaults to today.",
  )
  args = parser.parse_args(argv)

  manifest = generate_envelope_audit(
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
