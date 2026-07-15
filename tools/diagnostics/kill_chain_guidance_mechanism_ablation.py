#!/usr/bin/env python3
"""Run nested guidance-mechanism ablations over KCES constant-velocity cases."""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.diagnostics import kill_chain_decoupling_probe as probe  # noqa: E402


SCHEMA_VERSION = "a2.kill_chain_guidance_mechanism_ablation.v1"
EPSILON_GAIN = 1.0e-9
R_FUZE_M = 15.0
DEFAULT_SEED = 20260621

VARIANTS: tuple[dict[str, Any], ...] = (
  {
    "variant_id": "capture_only",
    "mechanisms": ["capture"],
    "overrides": {"nav_gain": EPSILON_GAIN, "apn_target_accel_gain": 0.0},
  },
  {
    "variant_id": "capture_pn",
    "mechanisms": ["capture", "pn"],
    "overrides": {"nav_gain": 4.0, "apn_target_accel_gain": 0.0},
  },
  {
    "variant_id": "capture_lead",
    "mechanisms": ["capture", "lead"],
    "overrides": {
      "nav_gain": EPSILON_GAIN,
      "apn_target_accel_gain": EPSILON_GAIN,
    },
  },
  {
    "variant_id": "capture_pn_lead",
    "mechanisms": ["capture", "pn", "lead"],
    "overrides": {"nav_gain": 4.0, "apn_target_accel_gain": EPSILON_GAIN},
  },
  {
    "variant_id": "capture_lead_apn",
    "mechanisms": ["capture", "lead", "apn"],
    "overrides": {"nav_gain": EPSILON_GAIN, "apn_target_accel_gain": 0.5},
  },
  {
    "variant_id": "full",
    "mechanisms": ["capture", "pn", "lead", "apn"],
    "overrides": {"nav_gain": 4.0, "apn_target_accel_gain": 0.5},
  },
  {
    "variant_id": "full_no_track_filter",
    "mechanisms": ["capture", "pn", "lead", "apn", "unfiltered_track"],
    "overrides": {
      "nav_gain": 4.0,
      "apn_target_accel_gain": 0.5,
      "bearing_filter_tau_s": 0.0,
      "elevation_filter_tau_s": 0.0,
      "range_filter_tau_s": 0.0,
    },
  },
  {
    "variant_id": "full_fast_scalar_autopilot",
    "mechanisms": ["capture", "pn", "lead", "apn", "near_instant_scalar_autopilot"],
    "overrides": {
      "nav_gain": 4.0,
      "apn_target_accel_gain": 0.5,
      "autopilot_tau_s": 0.001,
      "max_accel_response_g_per_s": 1.0e6,
    },
  },
  {
    "variant_id": "full_autopilot_order2",
    "mechanisms": ["capture", "pn", "lead", "apn", "second_order_autopilot"],
    "overrides": {
      "nav_gain": 4.0,
      "apn_target_accel_gain": 0.5,
      "autopilot_order": 2,
      "autopilot_damping": 1.0,
    },
  },
  {
    "variant_id": "full_autopilot_order3",
    "mechanisms": ["capture", "pn", "lead", "apn", "third_order_autopilot"],
    "overrides": {
      "nav_gain": 4.0,
      "apn_target_accel_gain": 0.5,
      "autopilot_order": 3,
      "autopilot_damping": 1.0,
    },
  },
)

CONDITIONAL_EFFECTS: tuple[tuple[str, str, str], ...] = (
  ("pn_without_lead_apn", "capture_only", "capture_pn"),
  ("lead_without_pn", "capture_only", "capture_lead"),
  ("lead_with_pn", "capture_pn", "capture_pn_lead"),
  ("pn_with_lead", "capture_lead", "capture_pn_lead"),
  ("apn_without_pn", "capture_lead", "capture_lead_apn"),
  ("apn_with_pn", "capture_pn_lead", "full"),
  ("pn_with_lead_apn", "capture_lead_apn", "full"),
  ("remove_track_filter", "full", "full_no_track_filter"),
  ("near_instant_scalar_autopilot", "full", "full_fast_scalar_autopilot"),
  ("second_order_autopilot", "full", "full_autopilot_order2"),
  ("third_order_autopilot", "full", "full_autopilot_order3"),
)


def _token(value: float) -> str:
  return f"{float(value):g}".replace("-", "m").replace(".", "p")


def default_cases() -> list[dict[str, Any]]:
  cells = (
    (4.0, 30.0, "N"),
    (6.0, 30.0, "N"),
    (8.0, 30.0, "N"),
    (4.0, 45.0, "M"),
    (6.0, 45.0, "M"),
    (8.0, 45.0, "M"),
    (8.0, 60.0, "M"),
    (10.0, 60.0, "O"),
    (12.0, 45.0, "O"),
    (16.0, 30.0, "O"),
  )
  rows: list[dict[str, Any]] = []
  for range_km, offset_deg, launch_class in cells:
    for bearing_deg in (-offset_deg, offset_deg):
      sign = "p" if bearing_deg >= 0.0 else "m"
      rows.append(
        {
          "case_id": (
            f"guidance_ablation_cv_{_token(range_km)}km_"
            f"{sign}{_token(abs(bearing_deg))}deg"
          ),
          "range_km": range_km,
          "range_m": range_km * 1000.0,
          "bearing_deg": bearing_deg,
          "offset_deg": offset_deg,
          "launch_class": launch_class,
        }
      )
  return rows


def selected_variants(variant_ids: tuple[str, ...] = ()) -> list[dict[str, Any]]:
  requested = set(variant_ids)
  rows = [dict(row) for row in VARIANTS if not requested or row["variant_id"] in requested]
  missing = requested - {str(row["variant_id"]) for row in rows}
  if missing:
    raise ValueError(f"unknown ablation variants: {sorted(missing)}")
  return rows


def _finite(value: Any) -> float | None:
  try:
    result = float(value)
  except Exception:
    return None
  return result if math.isfinite(result) else None


def _approach_observed(result: dict[str, Any]) -> dict[str, Any]:
  for row in list(result.get("stage_abstractions", []) or []):
    if str(row.get("abstraction_stage", "") or "") == "approach":
      observed = row.get("observed", {})
      return dict(observed) if isinstance(observed, dict) else {}
  return {}


def _values(rows: list[dict[str, Any]], field: str) -> list[float]:
  values = [_finite(row.get(field)) for row in rows]
  return [value for value in values if value is not None]


def _mean(values: list[float]) -> float | None:
  return statistics.fmean(values) if values else None


def _max_abs(values: list[float]) -> float | None:
  return max((abs(value) for value in values), default=None)


def summarize_runtime_trace(
  trace: list[dict[str, Any]],
  *,
  nearest_time_s: float | None,
) -> dict[str, Any]:
  terminal_rows = trace
  if nearest_time_s is not None:
    terminal_rows = [
      row
      for row in trace
      if (_finite(row.get("time_s")) or 0.0) >= nearest_time_s - 0.75
    ]
  closest = min(
    trace,
    key=lambda row: _finite(row.get("truth_distance_m")) or math.inf,
    default={},
  )
  commanded = _values(trace, "commanded_lateral_accel_mps2")
  achieved = _values(trace, "achieved_lateral_accel_mps2")
  terminal_commanded = _values(terminal_rows, "commanded_lateral_accel_mps2")
  terminal_achieved = _values(terminal_rows, "achieved_lateral_accel_mps2")
  saturated_count = sum(bool(row.get("command_saturated")) for row in trace)
  return {
    "sample_count": len(trace),
    "terminal_sample_count": len(terminal_rows),
    "max_commanded_g": max(commanded, default=0.0) / 9.80665,
    "max_achieved_g": max(achieved, default=0.0) / 9.80665,
    "command_saturation_fraction": saturated_count / len(trace) if trace else 0.0,
    "terminal_mean_commanded_g": (_mean(terminal_commanded) or 0.0) / 9.80665,
    "terminal_mean_achieved_g": (_mean(terminal_achieved) or 0.0) / 9.80665,
    "max_abs_bearing_rate_deg_s": _max_abs(_values(trace, "bearing_rate_deg_s")),
    "terminal_max_abs_bearing_rate_deg_s": _max_abs(
      _values(terminal_rows, "bearing_rate_deg_s")
    ),
    "max_lead_time_s": max(_values(trace, "guidance_lead_time_s"), default=0.0),
    "max_lead_blend": max(_values(trace, "guidance_lead_blend"), default=0.0),
    "max_apn_g": max(
      _values(trace, "guidance_apn_lateral_accel_mps2"),
      default=0.0,
    ) / 9.80665,
    "max_track_accel_g": max(
      _values(trace, "target_track_accel_mps2"),
      default=0.0,
    ) / 9.80665,
    "terminal_mean_track_accel_g": (
      _mean(_values(terminal_rows, "target_track_accel_mps2")) or 0.0
    ) / 9.80665,
    "max_abs_heading_velocity_error_deg": _max_abs(
      _values(trace, "heading_velocity_error_deg")
    ),
    "closest_sample_speed_mps": _finite(closest.get("current_speed_mps")),
    "closest_sample_filtered_range_m": _finite(closest.get("filtered_range_m")),
    "closest_sample_heading_velocity_error_deg": _finite(
      closest.get("heading_velocity_error_deg")
    ),
  }


def _result_row(
  *,
  case: dict[str, Any],
  variant: dict[str, Any],
  result: dict[str, Any],
) -> dict[str, Any]:
  approach = _approach_observed(result)
  nearest_distance_m = _finite(result.get("nearest_miss_distance_m"))
  if nearest_distance_m is None:
    nearest_distance_m = _finite(result.get("truth_min_distance_m"))
  nearest_time_s = _finite(approach.get("nearest_approach_time_s"))
  trace_summary = summarize_runtime_trace(
    list(result.get("guidance_runtime_trace", []) or []),
    nearest_time_s=nearest_time_s,
  )
  return {
    "case_id": str(case["case_id"]),
    "range_km": float(case["range_km"]),
    "bearing_deg": float(case["bearing_deg"]),
    "offset_deg": float(case["offset_deg"]),
    "launch_class": str(case["launch_class"]),
    "variant_id": str(variant["variant_id"]),
    "mechanisms": list(variant["mechanisms"]),
    "tuning_overrides": dict(variant["overrides"]),
    "nearest_distance_m": nearest_distance_m,
    "rho_fuze": nearest_distance_m / R_FUZE_M if nearest_distance_m is not None else None,
    "entered_R_fuze": bool(nearest_distance_m is not None and nearest_distance_m <= R_FUZE_M),
    "nearest_approach_time_s": nearest_time_s,
    "local_forward_m": _finite(approach.get("local_forward_m")),
    "local_right_m": _finite(approach.get("local_right_m")),
    "local_up_m": _finite(approach.get("local_up_m")),
    "closure_mps": _finite(approach.get("closure_mps")),
    "aspect_bucket": str(approach.get("aspect_bucket", "") or ""),
    **trace_summary,
  }


def run_ablation_matrix(
  *,
  database_path: Path = probe.DEFAULT_DATABASE_PATH,
  cases: list[dict[str, Any]] | None = None,
  variants: list[dict[str, Any]] | None = None,
  seed: int = DEFAULT_SEED,
  trace_stride: int = 1,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> list[dict[str, Any]]:
  case_rows = list(cases if cases is not None else default_cases())
  variant_rows = list(variants if variants is not None else selected_variants())
  rows: list[dict[str, Any]] = []
  for case in case_rows:
    for variant in variant_rows:
      print(
        f"[guidance-ablation] {case['case_id']} {variant['variant_id']}",
        file=sys.stderr,
      )
      result = runner(
        database_path=database_path,
        case_id=f"{case['case_id']}__{variant['variant_id']}",
        range_m=float(case["range_m"]),
        bearing_deg=float(case["bearing_deg"]),
        seed=int(seed),
        guidance_tuning_overrides=dict(variant["overrides"]),
        collect_guidance_runtime_trace=True,
        guidance_trace_stride=max(1, int(trace_stride)),
      )
      rows.append(_result_row(case=case, variant=variant, result=result))
  return rows


def conditional_effect_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
  for row in rows:
    by_case[str(row["case_id"])][str(row["variant_id"])] = row
  effects: list[dict[str, Any]] = []
  for case_id, variants in sorted(by_case.items()):
    for effect_id, before_id, after_id in CONDITIONAL_EFFECTS:
      before = variants.get(before_id)
      after = variants.get(after_id)
      if before is None or after is None:
        continue
      before_distance = _finite(before.get("nearest_distance_m"))
      after_distance = _finite(after.get("nearest_distance_m"))
      delta = (
        after_distance - before_distance
        if before_distance is not None and after_distance is not None
        else None
      )
      effects.append(
        {
          "case_id": case_id,
          "range_km": before["range_km"],
          "bearing_deg": before["bearing_deg"],
          "offset_deg": before["offset_deg"],
          "launch_class": before["launch_class"],
          "effect_id": effect_id,
          "before_variant": before_id,
          "after_variant": after_id,
          "before_nearest_distance_m": before_distance,
          "after_nearest_distance_m": after_distance,
          "miss_distance_delta_m": delta,
          "interpretation": (
            "improved"
            if delta is not None and delta < -0.5
            else "worsened"
            if delta is not None and delta > 0.5
            else "neutral"
          ),
          "entered_R_fuze_before": bool(before.get("entered_R_fuze")),
          "entered_R_fuze_after": bool(after.get("entered_R_fuze")),
        }
      )
  return effects


def _effect_summary(effects: list[dict[str, Any]]) -> dict[str, Any]:
  grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
  for row in effects:
    grouped[str(row["effect_id"])].append(row)
  summary: dict[str, Any] = {}
  for effect_id, group in sorted(grouped.items()):
    deltas = [
      value
      for value in (_finite(row.get("miss_distance_delta_m")) for row in group)
      if value is not None
    ]
    interpretations = Counter(str(row["interpretation"]) for row in group)
    by_offset: dict[str, list[float]] = defaultdict(list)
    for row in group:
      delta = _finite(row.get("miss_distance_delta_m"))
      if delta is not None:
        by_offset[f"{float(row['offset_deg']):g}"].append(delta)
    summary[effect_id] = {
      "case_count": len(group),
      "mean_miss_distance_delta_m": _mean(deltas),
      "median_miss_distance_delta_m": statistics.median(deltas) if deltas else None,
      "min_miss_distance_delta_m": min(deltas, default=None),
      "max_miss_distance_delta_m": max(deltas, default=None),
      "interpretation_counts": dict(sorted(interpretations.items())),
      "mean_delta_by_offset_deg": {
        offset: _mean(values) for offset, values in sorted(by_offset.items())
      },
    }
  return summary


def _symmetry_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
  paired: dict[tuple[str, float, float], dict[int, float]] = defaultdict(dict)
  for row in rows:
    distance = _finite(row.get("nearest_distance_m"))
    if distance is None:
      continue
    sign = 1 if float(row["bearing_deg"]) >= 0.0 else -1
    paired[(str(row["variant_id"]), float(row["range_km"]), float(row["offset_deg"]))][
      sign
    ] = distance
  diffs = [
    abs(values[1] - values[-1])
    for values in paired.values()
    if 1 in values and -1 in values
  ]
  return {
    "pair_count": len(diffs),
    "max_abs_nearest_distance_difference_m": max(diffs, default=None),
    "mean_abs_nearest_distance_difference_m": _mean(diffs),
  }


def generate_report(
  *,
  database_path: Path = probe.DEFAULT_DATABASE_PATH,
  cases: list[dict[str, Any]] | None = None,
  variants: list[dict[str, Any]] | None = None,
  seed: int = DEFAULT_SEED,
  trace_stride: int = 1,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> dict[str, Any]:
  case_rows = list(cases if cases is not None else default_cases())
  variant_rows = list(variants if variants is not None else selected_variants())
  rows = run_ablation_matrix(
    database_path=database_path,
    cases=case_rows,
    variants=variant_rows,
    seed=seed,
    trace_stride=trace_stride,
    runner=runner,
  )
  effects = conditional_effect_rows(rows)
  full_rows = [row for row in rows if row["variant_id"] == "full"]
  return {
    "schema_version": SCHEMA_VERSION,
    "status": "mechanism_ablation_generated",
    "seed": int(seed),
    "R_fuze_m": R_FUZE_M,
    "switch_policy": {
      "method": "nested_runtime_gates_plus_structural_controls",
      "epsilon_gain": EPSILON_GAIN,
      "parameter_optimization": False,
      "capture_present_in_all_variants": True,
      "structural_controls": [
        "remove_track_filter",
        "near_instant_scalar_autopilot",
        "second_order_autopilot",
        "third_order_autopilot",
      ],
      "nonlinear_interaction_warning": True,
    },
    "runtime_context": {
      "ef_py_artifact": str(Path(probe.ef_py.__file__).resolve()),
      "guidance_update_period_s": 0.0,
      "target_motion": "nonmaneuvering_constant_velocity",
    },
    "case_count": len(case_rows),
    "variant_count": len(variant_rows),
    "run_count": len(rows),
    "cases": case_rows,
    "variants": variant_rows,
    "rows": rows,
    "conditional_effects": effects,
    "summary": {
      "full_entered_R_fuze_count": sum(bool(row["entered_R_fuze"]) for row in full_rows),
      "full_outside_R_fuze_count": sum(not bool(row["entered_R_fuze"]) for row in full_rows),
      "full_launch_class_counts": dict(
        sorted(Counter(str(row["launch_class"]) for row in full_rows).items())
      ),
      "conditional_effects": _effect_summary(effects),
      "symmetry": _symmetry_summary(rows),
    },
    "limitations": [
      "epsilon gains are mechanism gates, not exact zero-valued C++ switches",
      "capture remains present in every variant and is not independently identified",
      "conditional deltas include nonlinear trajectory feedback, projection, saturation, and energy coupling",
      "constant-velocity cases diagnose the current engineering runtime and do not establish real-weapon authority",
    ],
  }


def _csv_value(value: Any) -> Any:
  if isinstance(value, (list, dict)):
    return json.dumps(value, sort_keys=True, ensure_ascii=True)
  return value


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
  fieldnames = sorted({key for row in rows for key in row})
  with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
      writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def render_markdown(report: dict[str, Any]) -> str:
  summary = dict(report.get("summary", {}) or {})
  effect_summary = dict(summary.get("conditional_effects", {}) or {})
  lines = [
    "# Guidance mechanism ablation summary",
    "",
    f"- Runs: `{int(report.get('run_count', 0))}` across "
    f"`{int(report.get('case_count', 0))}` cases and "
    f"`{int(report.get('variant_count', 0))}` mechanism variants.",
    f"- Full chain entered `R_fuze=15 m` in "
    f"`{int(summary.get('full_entered_R_fuze_count', 0))}` cases and remained outside in "
    f"`{int(summary.get('full_outside_R_fuze_count', 0))}` cases.",
    "- Negative deltas below mean that adding the named mechanism reduced miss distance.",
    "",
    "| Conditional effect | Mean delta (m) | 30 deg | 45 deg | 60 deg | Improved | Neutral | Worsened |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for effect_id, row in sorted(effect_summary.items()):
    counts = dict(row.get("interpretation_counts", {}) or {})
    mean_delta = _finite(row.get("mean_miss_distance_delta_m"))
    by_offset = dict(row.get("mean_delta_by_offset_deg", {}) or {})
    offset_values = {
      offset: _finite(by_offset.get(offset)) for offset in ("30", "45", "60")
    }
    offset_text = {
      offset: f"{value:.3f}" if value is not None else "n/a"
      for offset, value in offset_values.items()
    }
    lines.append(
      f"| `{effect_id}` | {mean_delta:.3f} | {offset_text['30']} | "
      f"{offset_text['45']} | {offset_text['60']} | "
      f"{int(counts.get('improved', 0))} | {int(counts.get('neutral', 0))} | "
      f"{int(counts.get('worsened', 0))} |"
      if mean_delta is not None
      else f"| `{effect_id}` | n/a | n/a | n/a | n/a | 0 | 0 | 0 |"
    )
  rows = list(report.get("rows", []) or [])
  selected_cells = ((4.0, 45.0), (6.0, 45.0), (8.0, 45.0), (16.0, 30.0))
  selected_variant_ids = (
    "full",
    "full_no_track_filter",
    "full_fast_scalar_autopilot",
    "full_autopilot_order2",
    "full_autopilot_order3",
  )
  lines.extend(
    [
      "",
      "## Structural controls",
      "",
      "The 16 km / 30 deg row is an O-class negative control; values at or below 15 m breach it.",
      "",
      "| Variant | 4 km / 45 deg | 6 km / 45 deg | 8 km / 45 deg | 16 km / 30 deg |",
      "|---|---:|---:|---:|---:|",
    ]
  )
  for variant_id in selected_variant_ids:
    values: list[str] = []
    for range_km, offset_deg in selected_cells:
      distances = [
        float(row["nearest_distance_m"])
        for row in rows
        if str(row.get("variant_id")) == variant_id
        and float(row.get("range_km", 0.0)) == range_km
        and float(row.get("offset_deg", 0.0)) == offset_deg
        and _finite(row.get("nearest_distance_m")) is not None
      ]
      mean_distance = _mean(distances)
      values.append(f"{mean_distance:.3f}" if mean_distance is not None else "n/a")
    lines.append(f"| `{variant_id}` | " + " | ".join(values) + " |")
  lines.extend(
    [
      "",
      "## Interpretation limits",
      "",
      *[f"- {item}" for item in list(report.get("limitations", []) or [])],
      "",
    ]
  )
  return "\n".join(lines)


def write_bundle(report: dict[str, Any], *, output_dir: Path, stem: str) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / f"{stem}.json"
  rows_path = output_dir / f"{stem}_rows.csv"
  effects_path = output_dir / f"{stem}_effects.csv"
  summary_path = output_dir / f"{stem}_summary.md"
  paths = {
    "json": str(json_path),
    "rows_csv": str(rows_path),
    "effects_csv": str(effects_path),
    "summary_md": str(summary_path),
  }
  report["artifacts"] = paths
  json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
  _write_csv(rows_path, list(report.get("rows", []) or []))
  _write_csv(effects_path, list(report.get("conditional_effects", []) or []))
  summary_path.write_text(render_markdown(report), encoding="utf-8")
  for path in (json_path, rows_path, effects_path, summary_path):
    path.chmod(0o644)
  return paths


@contextlib.contextmanager
def _native_stdout_to_stderr():
  sys.stdout.flush()
  saved_stdout_fd = os.dup(1)
  try:
    os.dup2(2, 1)
    yield
  finally:
    sys.stdout.flush()
    os.dup2(saved_stdout_fd, 1)
    os.close(saved_stdout_fd)


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--database", default=str(probe.DEFAULT_DATABASE_PATH))
  parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
  parser.add_argument("--trace-stride", type=int, default=1)
  parser.add_argument("--case-limit", type=int, default=0)
  parser.add_argument("--variant", action="append", default=[])
  parser.add_argument("--output-dir", default="")
  parser.add_argument(
    "--stem",
    default="kill_chain_guidance_mechanism_ablation_20260715",
  )
  return parser


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  cases = default_cases()
  if int(args.case_limit) > 0:
    cases = cases[: int(args.case_limit)]
  variants = selected_variants(tuple(str(value) for value in list(args.variant or [])))
  with _native_stdout_to_stderr():
    report = generate_report(
      database_path=Path(args.database),
      cases=cases,
      variants=variants,
      seed=int(args.seed),
      trace_stride=max(1, int(args.trace_stride)),
    )
  if args.output_dir:
    report["artifacts"] = write_bundle(
      report,
      output_dir=Path(args.output_dir),
      stem=str(args.stem),
    )
  print(json.dumps(report, indent=2, ensure_ascii=True))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
