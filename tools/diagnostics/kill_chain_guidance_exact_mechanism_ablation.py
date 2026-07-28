#!/usr/bin/env python3
"""Run exact, diagnostics-only guidance mechanism ablations with frozen scalars."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.diagnostics.common import native_stdout_to_stderr
from tools.diagnostics import kill_chain_decoupling_probe as probe  # noqa: E402

SCHEMA_VERSION = "a2.kill_chain_guidance_exact_mechanism_ablation.v2"
DEFAULT_SEED = 20260621
R_FUZE_M = 15.0
FROZEN_TUNING = {
  "nav_gain": 4.0,
  "max_lateral_g": 35.0,
  "apn_target_accel_gain": 0.5,
}

PN_LEGACY = 0
PN_OFF = 1
PN_WORLD_LOS_HISTORY = 2
PN_WORLD_TRACK_ANALYTIC = 3
LEAD_OFF = 0
LEAD_VELOCITY = 1
LEAD_QUADRATIC = 2
KINEMATICS_TRACK = 0
KINEMATICS_TRUTH_CV = 1

def _profile(
  variant_id: str,
  *,
  capture: int = 1,
  pn: int = PN_LEGACY,
  lead: int = LEAD_QUADRATIC,
  kinematics: int = KINEMATICS_TRACK,
  apn: int = 1,
) -> dict[str, Any]:
  return {
    "variant_id": variant_id,
    "profile": {
      "capture_mode": capture,
      "pn_mode": pn,
      "lead_mode": lead,
      "kinematics_source": kinematics,
      "apn_mode": apn,
    },
  }

VARIANTS: tuple[dict[str, Any], ...] = (
  _profile("legacy_full_track_quadratic"),
  _profile("legacy_no_capture", capture=0),
  _profile("legacy_no_pn", pn=PN_OFF),
  _profile("legacy_no_apn", apn=0),
  _profile("legacy_no_lead", lead=LEAD_OFF),
  _profile("legacy_track_velocity_no_apn", lead=LEAD_VELOCITY, apn=0),
  _profile("legacy_no_capture_no_lead", capture=0, lead=LEAD_OFF),
  _profile("history_full_track_quadratic", pn=PN_WORLD_LOS_HISTORY),
  _profile("history_track_quadratic_no_apn", pn=PN_WORLD_LOS_HISTORY, apn=0),
  _profile(
    "history_track_velocity_no_apn",
    pn=PN_WORLD_LOS_HISTORY,
    lead=LEAD_VELOCITY,
    apn=0,
  ),
  _profile(
    "analytic_track_quadratic_no_apn",
    pn=PN_WORLD_TRACK_ANALYTIC,
    apn=0,
  ),
  _profile(
    "analytic_track_velocity_no_apn",
    pn=PN_WORLD_TRACK_ANALYTIC,
    lead=LEAD_VELOCITY,
    apn=0,
  ),
  _profile(
    "analytic_truth_velocity_no_apn",
    pn=PN_WORLD_TRACK_ANALYTIC,
    lead=LEAD_VELOCITY,
    kinematics=KINEMATICS_TRUTH_CV,
    apn=0,
  ),
  _profile(
    "analytic_truth_quadratic_no_apn",
    pn=PN_WORLD_TRACK_ANALYTIC,
    kinematics=KINEMATICS_TRUTH_CV,
    apn=0,
  ),
  _profile(
    "analytic_truth_velocity_apn",
    pn=PN_WORLD_TRACK_ANALYTIC,
    lead=LEAD_VELOCITY,
    kinematics=KINEMATICS_TRUTH_CV,
    apn=1,
  ),
  _profile(
    "legacy_truth_velocity_no_apn",
    pn=PN_LEGACY,
    lead=LEAD_VELOCITY,
    kinematics=KINEMATICS_TRUTH_CV,
    apn=0,
  ),
)

MATCHED_EFFECTS: tuple[tuple[str, str, str], ...] = (
  ("remove_capture_from_current", "legacy_full_track_quadratic", "legacy_no_capture"),
  ("remove_pn_from_current", "legacy_full_track_quadratic", "legacy_no_pn"),
  ("add_apn_to_current", "legacy_no_apn", "legacy_full_track_quadratic"),
  ("remove_lead_from_current", "legacy_full_track_quadratic", "legacy_no_lead"),
  (
    "add_acceleration_lead_legacy",
    "legacy_track_velocity_no_apn",
    "legacy_no_apn",
  ),
  (
    "replace_legacy_pn_with_world_history_full",
    "legacy_full_track_quadratic",
    "history_full_track_quadratic",
  ),
  (
    "replace_legacy_pn_with_world_history_no_apn",
    "legacy_no_apn",
    "history_track_quadratic_no_apn",
  ),
  (
    "replace_legacy_pn_with_world_history_velocity",
    "legacy_track_velocity_no_apn",
    "history_track_velocity_no_apn",
  ),
  (
    "replace_world_history_with_track_analytic_pn",
    "history_track_velocity_no_apn",
    "analytic_track_velocity_no_apn",
  ),
  (
    "add_acceleration_lead_world_history",
    "history_track_velocity_no_apn",
    "history_track_quadratic_no_apn",
  ),
  (
    "add_acceleration_lead_track_analytic",
    "analytic_track_velocity_no_apn",
    "analytic_track_quadratic_no_apn",
  ),
  (
    "replace_track_with_truth_cv_for_legacy_capture_lead",
    "legacy_track_velocity_no_apn",
    "legacy_truth_velocity_no_apn",
  ),
  (
    "replace_track_with_truth_cv_for_analytic_chain",
    "analytic_track_velocity_no_apn",
    "analytic_truth_velocity_no_apn",
  ),
  (
    "truth_cv_quadratic_invariant",
    "analytic_truth_velocity_no_apn",
    "analytic_truth_quadratic_no_apn",
  ),
  (
    "truth_cv_apn_invariant",
    "analytic_truth_velocity_no_apn",
    "analytic_truth_velocity_apn",
  ),
  (
    "lead_requires_capture_invariant",
    "legacy_no_capture_no_lead",
    "legacy_no_capture",
  ),
)

def _token(value: float) -> str:
  return f"{float(value):g}".replace("-", "m").replace(".", "p")

def _case_group(range_km: float, offset_deg: float) -> str:
  if offset_deg == 30.0 and range_km <= 8.0:
    return "N30"
  if offset_deg == 45.0 and range_km <= 8.0:
    return "M45"
  if offset_deg == 60.0 and range_km == 8.0:
    return "stress60"
  if (offset_deg == 60.0 and range_km == 10.0) or (
    offset_deg == 45.0 and range_km == 12.0
  ):
    return "O_near"
  return "O_far"

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
            f"guidance_exact_cv_{_token(range_km)}km_"
            f"{sign}{_token(abs(bearing_deg))}deg"
          ),
          "range_km": range_km,
          "range_m": range_km * 1000.0,
          "bearing_deg": bearing_deg,
          "offset_deg": offset_deg,
          "launch_class": launch_class,
          "case_group": _case_group(range_km, offset_deg),
        }
      )
  return rows

def selected_variants(variant_ids: tuple[str, ...] = ()) -> list[dict[str, Any]]:
  requested = set(variant_ids)
  rows = [dict(row) for row in VARIANTS if not requested or row["variant_id"] in requested]
  missing = requested - {str(row["variant_id"]) for row in rows}
  if missing:
    raise ValueError(f"unknown exact ablation variants: {sorted(missing)}")
  return rows

def _finite(value: Any) -> float | None:
  try:
    result = float(value)
  except Exception:
    return None
  return result if math.isfinite(result) else None

def _mean(values: list[float]) -> float | None:
  # Kept local: empty -> None via statistics.fmean (≠ mean_finite).
  return statistics.fmean(values) if values else None

def _approach_observed(result: dict[str, Any]) -> dict[str, Any]:
  for row in list(result.get("stage_abstractions", []) or []):
    if str(row.get("abstraction_stage", "") or "") == "approach":
      observed = row.get("observed", {})
      return dict(observed) if isinstance(observed, dict) else {}
  return {}

def _trace_values(trace: list[dict[str, Any]], field: str) -> list[float]:
  values = [_finite(row.get(field)) for row in trace]
  return [value for value in values if value is not None]

def _trace_summary(trace: list[dict[str, Any]]) -> dict[str, Any]:
  source_counts = Counter(int(row.get("guidance_pn_source_used", 0) or 0) for row in trace)
  kinematics_counts = Counter(
    int(row.get("guidance_target_kinematics_source_used", 0) or 0)
    for row in trace
  )
  preclamp = _trace_values(trace, "guidance_preclamp_accel_mps2")
  postclamp = _trace_values(trace, "guidance_postclamp_accel_mps2")
  return {
    "trace_sample_count": len(trace),
    "max_capture_g": max(
      _trace_values(trace, "guidance_capture_accel_mps2"), default=0.0
    ) / 9.80665,
    "max_pn_g": max(_trace_values(trace, "guidance_pn_accel_mps2"), default=0.0)
    / 9.80665,
    "max_apn_g": max(
      _trace_values(trace, "guidance_apn_lateral_accel_mps2"), default=0.0
    ) / 9.80665,
    "max_preclamp_g": max(preclamp, default=0.0) / 9.80665,
    "max_postclamp_g": max(postclamp, default=0.0) / 9.80665,
    "clamp_fraction": (
      sum(before > after + 1.0e-9 for before, after in zip(preclamp, postclamp))
      / len(preclamp)
      if preclamp
      else 0.0
    ),
    "max_component_sum_error_mps2": max(
      _trace_values(trace, "guidance_component_sum_error_mps2"), default=0.0
    ),
    "max_los_rate_rad_s": max(
      _trace_values(trace, "guidance_los_rate_rad_s"), default=0.0
    ),
    "max_abs_heading_velocity_error_deg": max(
      (abs(value) for value in _trace_values(trace, "heading_velocity_error_deg")),
      default=0.0,
    ),
    "pn_source_counts": dict(sorted(source_counts.items())),
    "target_kinematics_source_counts": dict(sorted(kinematics_counts.items())),
  }

def _result_row(
  *, case: dict[str, Any], variant: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
  approach = _approach_observed(result)
  nearest_distance_m = _finite(result.get("nearest_miss_distance_m"))
  if nearest_distance_m is None:
    nearest_distance_m = _finite(result.get("truth_min_distance_m"))
  return {
    "case_id": str(case["case_id"]),
    "range_km": float(case["range_km"]),
    "bearing_deg": float(case["bearing_deg"]),
    "offset_deg": float(case["offset_deg"]),
    "launch_class": str(case["launch_class"]),
    "case_group": str(case["case_group"]),
    "variant_id": str(variant["variant_id"]),
    "profile": dict(variant["profile"]),
    "nearest_distance_m": nearest_distance_m,
    "rho_fuze": nearest_distance_m / R_FUZE_M if nearest_distance_m is not None else None,
    "entered_R_fuze": bool(nearest_distance_m is not None and nearest_distance_m <= R_FUZE_M),
    "nearest_approach_time_s": _finite(approach.get("nearest_approach_time_s")),
    "local_forward_m": _finite(approach.get("local_forward_m")),
    "local_right_m": _finite(approach.get("local_right_m")),
    "local_up_m": _finite(approach.get("local_up_m")),
    "aspect_bucket": str(approach.get("aspect_bucket", "") or ""),
    **_trace_summary(list(result.get("guidance_runtime_trace", []) or [])),
  }

def run_ablation_matrix(
  *,
  database_path: Path = probe.DEFAULT_DATABASE_PATH,
  cases: list[dict[str, Any]] | None = None,
  variants: list[dict[str, Any]] | None = None,
  seed: int = DEFAULT_SEED,
  trace_stride: int = 5,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> list[dict[str, Any]]:
  case_rows = list(cases if cases is not None else default_cases())
  variant_rows = list(variants if variants is not None else selected_variants())
  rows: list[dict[str, Any]] = []
  for case in case_rows:
    for variant in variant_rows:
      print(f"[guidance-exact] {case['case_id']} {variant['variant_id']}", file=sys.stderr)
      result = runner(
        database_path=database_path,
        case_id=f"{case['case_id']}__{variant['variant_id']}",
        range_m=float(case["range_m"]),
        bearing_deg=float(case["bearing_deg"]),
        seed=int(seed),
        guidance_tuning_overrides=dict(FROZEN_TUNING),
        guidance_mechanism_profile=dict(variant["profile"]),
        collect_guidance_runtime_trace=True,
        guidance_trace_stride=max(1, int(trace_stride)),
      )
      rows.append(_result_row(case=case, variant=variant, result=result))
  return rows

def _pair_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[tuple[str, float, float, str], list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    grouped[
      (
        str(row["variant_id"]),
        float(row["range_km"]),
        float(row["offset_deg"]),
        str(row["case_group"]),
      )
    ].append(row)
  pairs: list[dict[str, Any]] = []
  for (variant_id, range_km, offset_deg, case_group), group in sorted(grouped.items()):
    distances = [
      value
      for value in (_finite(row.get("nearest_distance_m")) for row in group)
      if value is not None
    ]
    if not distances:
      continue
    pairs.append(
      {
        "variant_id": variant_id,
        "range_km": range_km,
        "offset_deg": offset_deg,
        "case_group": case_group,
        "pair_count": len(distances),
        "pair_mean_nearest_distance_m": statistics.fmean(distances),
        "mirror_abs_difference_m": (
          abs(distances[0] - distances[1]) if len(distances) == 2 else None
        ),
        "pair_entered_R_fuze": all(value <= R_FUZE_M for value in distances),
      }
    )
  return pairs

def matched_effect_rows(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  by_cell: dict[tuple[float, float], dict[str, dict[str, Any]]] = defaultdict(dict)
  for row in pair_rows:
    by_cell[(float(row["range_km"]), float(row["offset_deg"]))][
      str(row["variant_id"])
    ] = row
  effects: list[dict[str, Any]] = []
  for (range_km, offset_deg), variants in sorted(by_cell.items()):
    for effect_id, before_id, after_id in MATCHED_EFFECTS:
      before = variants.get(before_id)
      after = variants.get(after_id)
      if before is None or after is None:
        continue
      before_distance = float(before["pair_mean_nearest_distance_m"])
      after_distance = float(after["pair_mean_nearest_distance_m"])
      effects.append(
        {
          "effect_id": effect_id,
          "range_km": range_km,
          "offset_deg": offset_deg,
          "case_group": str(before["case_group"]),
          "before_variant": before_id,
          "after_variant": after_id,
          "before_nearest_distance_m": before_distance,
          "after_nearest_distance_m": after_distance,
          "miss_distance_delta_m": after_distance - before_distance,
        }
      )
  return effects

def _effect_summary(effects: list[dict[str, Any]]) -> dict[str, Any]:
  grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
  for row in effects:
    grouped[str(row["effect_id"])].append(row)
  summary: dict[str, Any] = {}
  for effect_id, group in sorted(grouped.items()):
    by_group: dict[str, list[float]] = defaultdict(list)
    for row in group:
      by_group[str(row["case_group"])].append(float(row["miss_distance_delta_m"]))
    all_values = [float(row["miss_distance_delta_m"]) for row in group]
    summary[effect_id] = {
      "cell_count": len(group),
      "median_delta_m": statistics.median(all_values),
      "min_delta_m": min(all_values),
      "max_delta_m": max(all_values),
      "mean_delta_by_case_group_m": {
        name: statistics.fmean(values) for name, values in sorted(by_group.items())
      },
    }
  return summary

def _baseline_equivalence(
  *,
  database_path: Path,
  rows: list[dict[str, Any]],
  seed: int,
  runner: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
  checks = [
    case
    for case in default_cases()
    if float(case["bearing_deg"]) > 0.0
    and (float(case["range_km"]), float(case["offset_deg"]))
    in {(4.0, 30.0), (4.0, 45.0), (16.0, 30.0)}
  ]
  indexed = {
    (float(row["range_km"]), float(row["bearing_deg"])): row
    for row in rows
    if row["variant_id"] == "legacy_full_track_quadratic"
  }
  output: list[dict[str, Any]] = []
  for case in checks:
    result = runner(
      database_path=database_path,
      case_id=f"{case['case_id']}__unprofiled_baseline",
      range_m=float(case["range_m"]),
      bearing_deg=float(case["bearing_deg"]),
      seed=int(seed),
      guidance_tuning_overrides=dict(FROZEN_TUNING),
    )
    baseline = _finite(result.get("nearest_miss_distance_m"))
    if baseline is None:
      baseline = _finite(result.get("truth_min_distance_m"))
    profiled = indexed[(float(case["range_km"]), float(case["bearing_deg"]))]
    profiled_distance = _finite(profiled.get("nearest_distance_m"))
    delta = (
      profiled_distance - baseline
      if baseline is not None and profiled_distance is not None
      else None
    )
    output.append(
      {
        "case_id": str(case["case_id"]),
        "unprofiled_nearest_distance_m": baseline,
        "profiled_nearest_distance_m": profiled_distance,
        "profile_minus_unprofiled_m": delta,
      }
    )
  return output

def _acceptance_summary(
  rows: list[dict[str, Any]],
  pair_rows: list[dict[str, Any]],
  effects: list[dict[str, Any]],
  baseline_equivalence: list[dict[str, Any]],
) -> dict[str, Any]:
  full_pairs = [
    row for row in pair_rows if row["variant_id"] == "legacy_full_track_quadratic"
  ]
  invariant_values = [
    abs(float(row["miss_distance_delta_m"]))
    for row in effects
    if row["effect_id"]
    in {"truth_cv_quadratic_invariant", "truth_cv_apn_invariant", "lead_requires_capture_invariant"}
  ]
  max_invariant_delta = max(invariant_values, default=0.0)
  max_baseline_delta = max(
    (
      abs(float(row["profile_minus_unprofiled_m"]))
      for row in baseline_equivalence
      if _finite(row.get("profile_minus_unprofiled_m")) is not None
    ),
    default=0.0,
  )
  max_symmetry_delta = max(
    (
      float(row["mirror_abs_difference_m"])
      for row in pair_rows
      if _finite(row.get("mirror_abs_difference_m")) is not None
    ),
    default=0.0,
  )
  variants = {str(row["variant_id"]): row for row in VARIANTS}
  disabled_capture_g = [
    float(row["max_capture_g"])
    for row in rows
    if variants[str(row["variant_id"])]["profile"]["capture_mode"] == 0
  ]
  disabled_pn_g = [
    float(row["max_pn_g"])
    for row in rows
    if variants[str(row["variant_id"])]["profile"]["pn_mode"] == PN_OFF
  ]
  disabled_apn_g = [
    float(row["max_apn_g"])
    for row in rows
    if variants[str(row["variant_id"])]["profile"]["apn_mode"] == 0
  ]
  max_disabled_component_g = max(
    [*disabled_capture_g, *disabled_pn_g, *disabled_apn_g], default=0.0
  )
  max_postclamp_g = max((float(row["max_postclamp_g"]) for row in rows), default=0.0)
  return {
    "baseline_profile_equivalent_within_1e_3_m": max_baseline_delta <= 1.0e-3,
    "max_baseline_profile_delta_m": max_baseline_delta,
    "mirror_symmetric_within_1e_3_m": max_symmetry_delta <= 1.0e-3,
    "max_mirror_abs_difference_m": max_symmetry_delta,
    "component_vectors_close_within_1e_6_mps2": max(
      (float(row["max_component_sum_error_mps2"]) for row in rows), default=0.0
    )
    <= 1.0e-6,
    "max_component_sum_error_mps2": max(
      (float(row["max_component_sum_error_mps2"]) for row in rows), default=0.0
    ),
    "disabled_components_zero_within_1e_12_g": max_disabled_component_g <= 1.0e-12,
    "max_disabled_component_g": max_disabled_component_g,
    "postclamp_never_exceeds_35g": max_postclamp_g <= 35.0 + 1.0e-9,
    "max_postclamp_g": max_postclamp_g,
    "truth_cv_and_capture_interaction_invariants_within_1e_6_m":
      max_invariant_delta <= 1.0e-6,
    "max_invariant_abs_delta_m": max_invariant_delta,
    "legacy_full_N30_all_enter_R_fuze": all(
      bool(row["pair_entered_R_fuze"])
      for row in full_pairs
      if row["case_group"] == "N30"
    ),
    "legacy_full_O_controls_all_outside_R_fuze": all(
      not bool(row["pair_entered_R_fuze"])
      for row in full_pairs
      if str(row["case_group"]).startswith("O_")
    ),
  }

def generate_report(
  *,
  database_path: Path = probe.DEFAULT_DATABASE_PATH,
  cases: list[dict[str, Any]] | None = None,
  variants: list[dict[str, Any]] | None = None,
  seed: int = DEFAULT_SEED,
  trace_stride: int = 5,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
  run_baseline_equivalence: bool = True,
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
  pairs = _pair_rows(rows)
  effects = matched_effect_rows(pairs)
  baseline_equivalence = (
    _baseline_equivalence(
      database_path=database_path,
      rows=rows,
      seed=seed,
      runner=runner,
    )
    if run_baseline_equivalence
    and any(row["variant_id"] == "legacy_full_track_quadratic" for row in rows)
    and len(case_rows) == len(default_cases())
    else []
  )
  return {
    "schema_version": SCHEMA_VERSION,
    "status": "exact_mechanism_ablation_generated",
    "seed": int(seed),
    "R_fuze_m": R_FUZE_M,
    "frozen_tuning": dict(FROZEN_TUNING),
    "switch_policy": {
      "method": "diagnostics_only_per_missile_exact_profile",
      "epsilon_gates": False,
      "production_defaults_modified": False,
      "lead_semantics": "capture aimpoint prediction, not an independent acceleration",
      "pn_modes": {
        "0": "legacy body rates through Transform",
        "1": "off",
        "2": "world LOS history with filtered closing speed",
        "3": "world analytic LOS rate from selected target kinematics",
      },
    },
    "runtime_context": {
      "ef_py_artifact": str(Path(probe.ef_py.__file__).resolve()),
      "target_motion": "truth constant velocity",
      "case_summary_unit": "left-right pair mean before group aggregation",
    },
    "case_count": len(case_rows),
    "variant_count": len(variant_rows),
    "run_count": len(rows),
    "cases": case_rows,
    "variants": variant_rows,
    "rows": rows,
    "pair_rows": pairs,
    "matched_effects": effects,
    "baseline_equivalence": baseline_equivalence,
    "summary": {
      "matched_effects": _effect_summary(effects),
      "acceptance": _acceptance_summary(rows, pairs, effects, baseline_equivalence),
    },
    "limitations": [
      "The truth-CV source is an oracle diagnostic and is not a production guidance input.",
      "Conditional deltas include nonlinear trajectory, saturation, and energy feedback.",
      "The constant-velocity matrix diagnoses implementation mechanisms, not real-weapon authority.",
      "M45 is a residual observation group; entering 15 m is not imposed as an acceptance gate.",
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
  effect_summary = dict(report.get("summary", {}).get("matched_effects", {}) or {})
  groups = ("N30", "M45", "stress60", "O_near", "O_far")
  lines = [
    "# Exact guidance mechanism ablation",
    "",
    f"- Runs: `{int(report.get('run_count', 0))}`.",
    "- Scalars are frozen at `N=4`, `35 g`, and `APN gain=0.5`.",
    "- Negative deltas mean the after-profile reduced miss distance.",
    "",
    "| Matched effect | N30 | M45 | 60 stress | O near | O far |",
    "|---|---:|---:|---:|---:|---:|",
  ]
  for effect_id, row in sorted(effect_summary.items()):
    by_group = dict(row.get("mean_delta_by_case_group_m", {}) or {})
    values = [
      f"{float(by_group[name]):.3f}" if name in by_group else "n/a" for name in groups
    ]
    lines.append(f"| `{effect_id}` | " + " | ".join(values) + " |")
  acceptance = dict(report.get("summary", {}).get("acceptance", {}) or {})
  lines.extend(["", "## Acceptance", ""])
  for key, value in sorted(acceptance.items()):
    lines.append(f"- `{key}`: `{value}`")
  lines.extend(["", "## Limits", ""])
  lines.extend(f"- {item}" for item in list(report.get("limitations", []) or []))
  lines.append("")
  return "\n".join(lines)

def write_bundle(report: dict[str, Any], *, output_dir: Path, stem: str) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "json": str(output_dir / f"{stem}.json"),
    "rows_csv": str(output_dir / f"{stem}_rows.csv"),
    "pairs_csv": str(output_dir / f"{stem}_pairs.csv"),
    "effects_csv": str(output_dir / f"{stem}_effects.csv"),
    "summary_md": str(output_dir / f"{stem}_summary.md"),
  }
  report["artifacts"] = paths
  Path(paths["json"]).write_text(
    json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
  )
  _write_csv(Path(paths["rows_csv"]), list(report.get("rows", []) or []))
  _write_csv(Path(paths["pairs_csv"]), list(report.get("pair_rows", []) or []))
  _write_csv(Path(paths["effects_csv"]), list(report.get("matched_effects", []) or []))
  Path(paths["summary_md"]).write_text(render_markdown(report), encoding="utf-8")
  for path in paths.values():
    Path(path).chmod(0o644)
  return paths

def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--database", default=str(probe.DEFAULT_DATABASE_PATH))
  parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
  parser.add_argument("--trace-stride", type=int, default=5)
  parser.add_argument("--case-limit", type=int, default=0)
  parser.add_argument("--variant", action="append", default=[])
  parser.add_argument("--output-dir", default="")
  parser.add_argument("--stem", default="kill_chain_guidance_exact_mechanism_ablation_20260715")
  return parser

def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  probe.ef_py.set_log_level("warn")
  cases = default_cases()
  if int(args.case_limit) > 0:
    cases = cases[: int(args.case_limit)]
  variants = selected_variants(tuple(str(value) for value in list(args.variant or [])))
  with native_stdout_to_stderr():
    report = generate_report(
      database_path=Path(args.database),
      cases=cases,
      variants=variants,
      seed=int(args.seed),
      trace_stride=max(1, int(args.trace_stride)),
      run_baseline_equivalence=int(args.case_limit) <= 0,
    )
  if args.output_dir:
    report["artifacts"] = write_bundle(
      report, output_dir=Path(args.output_dir), stem=str(args.stem)
    )
  print(json.dumps(report, indent=2, ensure_ascii=True))
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
