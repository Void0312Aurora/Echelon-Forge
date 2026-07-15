#!/usr/bin/env python3
"""Ablate capture range and lead schedules after the PN/tracker corrections."""

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
from tools.diagnostics import kill_chain_guidance_exact_mechanism_ablation as exact  # noqa: E402


SCHEMA_VERSION = "a2.kill_chain_capture_structure_ablation.v1"
DEFAULT_SEED = 20260621
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/"
  "kill_chain_capture_structure_ablation_20260715"
)
R_FUZE_M = 15.0
CAPTURE_REFERENCE_RANGE_M = 6000.0
LEAD_REFERENCE_RANGE_M = 8000.0
LEAD_BLEND_MAX = 0.55
CURRENT_TERMINAL_WEIGHT_MIN = 0.25
CURRENT_TERMINAL_WEIGHT_MAX = 2.5

# Stage 1/2 candidates are selected explicitly.  The weapon database remains untouched.
CANDIDATE_TUNING: dict[str, float | int] = {
  "nav_gain": 4.0,
  "max_lateral_g": 35.0,
  "apn_target_accel_gain": 0.5,
  "pn_los_rate_source": 1,
  "target_kinematics_estimator": 1,
  "target_tracker_alpha": 0.20,
  "target_tracker_beta": 0.02,
}

CAPTURE_OFF = 0
CAPTURE_ON = 1
BASE_INVERSE_RANGE = 0
BASE_REFERENCE_RANGE = 1
TERMINAL_CURRENT_CLAMPED = 0
TERMINAL_UNITY = 1
TERMINAL_RECIPROCAL_UNCLAMPED = 2
LEAD_CURRENT_SCHEDULE = 0
LEAD_CONSTANT_MAX = 1
LEAD_OFF = 2


def _profile(
  profile_id: str,
  description_zh: str,
  *,
  capture_mode: int = CAPTURE_ON,
  base_range_mode: int = BASE_INVERSE_RANGE,
  terminal_weight_mode: int = TERMINAL_CURRENT_CLAMPED,
  lead_blend_mode: int = LEAD_CURRENT_SCHEDULE,
) -> dict[str, Any]:
  return {
    "profile_id": profile_id,
    "description_zh": description_zh,
    "profile": {
      "capture_mode": capture_mode,
      # Freeze the already selected world-frame LOS-history PN and world-CV track.
      "pn_mode": 2,
      "lead_mode": 2,
      "kinematics_source": 0,
      "apn_mode": 1,
      "capture_base_range_mode": base_range_mode,
      "capture_terminal_weight_mode": terminal_weight_mode,
      "capture_lead_blend_mode": lead_blend_mode,
    },
  }


# Keep this numbering stable: it is referenced by the staged calibration plan.
PROFILES: tuple[dict[str, Any], ...] = (
  _profile("P0", "capture 关闭负控", capture_mode=CAPTURE_OFF),
  _profile("P1", "当前 capture 结构"),
  _profile("P2", "当前 range 结构，lead blend 关闭", lead_blend_mode=LEAD_OFF),
  _profile(
    "P3", "当前 range 结构，lead blend 固定为最大值", lead_blend_mode=LEAD_CONSTANT_MAX
  ),
  _profile("P4", "terminal weight 固定为 1", terminal_weight_mode=TERMINAL_UNITY),
  _profile("P5", "base denominator 固定为参考距离", base_range_mode=BASE_REFERENCE_RANGE),
  _profile(
    "P6",
    "base denominator 固定且 terminal weight 固定为 1",
    base_range_mode=BASE_REFERENCE_RANGE,
    terminal_weight_mode=TERMINAL_UNITY,
  ),
  _profile(
    "P7",
    "terminal reciprocal 保留但移除上下 clamp",
    terminal_weight_mode=TERMINAL_RECIPROCAL_UNCLAMPED,
  ),
  _profile(
    "P8",
    "inverse-range base、unity terminal、constant lead",
    terminal_weight_mode=TERMINAL_UNITY,
    lead_blend_mode=LEAD_CONSTANT_MAX,
  ),
)

MATCHED_EFFECTS: tuple[tuple[str, str, str], ...] = (
  ("capture_total", "P0", "P1"),
  ("lead_content", "P2", "P1"),
  ("lead_range_schedule", "P3", "P1"),
  ("terminal_weighting", "P4", "P1"),
  ("base_inverse_range", "P5", "P1"),
  ("terminal_given_base_flat", "P6", "P5"),
  ("base_inverse_given_terminal_flat", "P6", "P4"),
  ("terminal_clamp", "P7", "P1"),
  ("lead_range_schedule_terminal_flat", "P8", "P4"),
)

CLAMP_AUDIT_PROFILE_IDS = ("P1", "P4", "P7")
CLAMP_AUDIT_RANGES_KM = (2.0, 2.4, 3.0, 20.0, 24.0, 28.0)
CLAMP_AUDIT_SIGNED_BEARINGS_DEG = (-30.0, -15.0, 15.0, 30.0)


def selected_profiles(profile_ids: tuple[str, ...] = ()) -> list[dict[str, Any]]:
  requested = set(profile_ids)
  rows = [dict(row) for row in PROFILES if not requested or row["profile_id"] in requested]
  missing = requested - {str(row["profile_id"]) for row in rows}
  if missing:
    raise ValueError(f"unknown capture structure profiles: {sorted(missing)}")
  return rows


def anchor_cases() -> list[dict[str, Any]]:
  """Return the same 20 signed anchors used by the exact mechanism ablation."""
  return [dict(row) for row in exact.default_cases()]


def clamp_audit_cases() -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for range_km in CLAMP_AUDIT_RANGES_KM:
    for bearing_deg in CLAMP_AUDIT_SIGNED_BEARINGS_DEG:
      sign = "p" if bearing_deg >= 0.0 else "m"
      rows.append(
        {
          "case_id": (
            f"capture_clamp_{str(range_km).replace('.', 'p')}km_"
            f"{sign}{abs(int(bearing_deg))}deg"
          ),
          "range_km": range_km,
          "range_m": range_km * 1000.0,
          "bearing_deg": bearing_deg,
          "offset_deg": abs(bearing_deg),
          "launch_class": "audit",
          "case_group": "clamp_audit",
        }
      )
  return rows


def _finite(value: Any) -> float | None:
  try:
    result = float(value)
  except Exception:
    return None
  return result if math.isfinite(result) else None


def _mean(values: list[float]) -> float | None:
  return statistics.fmean(values) if values else None


def _quantile(values: list[float], fraction: float) -> float | None:
  if not values:
    return None
  ordered = sorted(values)
  index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
  return ordered[index]


def _miss_distance(result: dict[str, Any]) -> float | None:
  value = _finite(result.get("nearest_miss_distance_m"))
  if value is None:
    value = _finite(result.get("truth_min_distance_m"))
  return value


def _approach_observed(result: dict[str, Any]) -> dict[str, Any]:
  for row in list(result.get("stage_abstractions", []) or []):
    if str(row.get("abstraction_stage", "") or "") == "approach":
      observed = row.get("observed", {})
      return dict(observed) if isinstance(observed, dict) else {}
  return {}


def _range_factors(range_m: float, profile: dict[str, int]) -> dict[str, Any]:
  safe_range_m = max(1.0, float(range_m))
  base_mode = int(profile["capture_base_range_mode"])
  terminal_mode = int(profile["capture_terminal_weight_mode"])
  lead_mode = int(profile["capture_lead_blend_mode"])

  base_denominator_m = (
    safe_range_m if base_mode == BASE_INVERSE_RANGE else CAPTURE_REFERENCE_RANGE_M
  )
  reciprocal = CAPTURE_REFERENCE_RANGE_M / safe_range_m
  if terminal_mode == TERMINAL_CURRENT_CLAMPED:
    terminal_weight = min(
      CURRENT_TERMINAL_WEIGHT_MAX,
      max(CURRENT_TERMINAL_WEIGHT_MIN, reciprocal),
    )
    if reciprocal > CURRENT_TERMINAL_WEIGHT_MAX:
      terminal_regime = "upper_clamped"
    elif reciprocal < CURRENT_TERMINAL_WEIGHT_MIN:
      terminal_regime = "lower_clamped"
    elif math.isclose(reciprocal, CURRENT_TERMINAL_WEIGHT_MAX, abs_tol=1.0e-12):
      terminal_regime = "upper_boundary"
    elif math.isclose(reciprocal, CURRENT_TERMINAL_WEIGHT_MIN, abs_tol=1.0e-12):
      terminal_regime = "lower_boundary"
    else:
      terminal_regime = "reciprocal_interior"
  elif terminal_mode == TERMINAL_UNITY:
    terminal_weight = 1.0
    terminal_regime = "unity"
  else:
    terminal_weight = reciprocal
    terminal_regime = "reciprocal_unclamped"

  lead_fraction = min(1.0, max(0.20, LEAD_REFERENCE_RANGE_M / safe_range_m))
  if lead_mode == LEAD_CURRENT_SCHEDULE:
    lead_blend = LEAD_BLEND_MAX * lead_fraction
  elif lead_mode == LEAD_CONSTANT_MAX:
    lead_blend = LEAD_BLEND_MAX
  else:
    lead_blend = 0.0
  return {
    "base_denominator_m": base_denominator_m,
    "terminal_reciprocal_raw": reciprocal,
    "terminal_weight": terminal_weight,
    "terminal_regime": terminal_regime,
    "lead_blend": lead_blend,
    # Capture gain and speed/lateral error are common factors.  This is the
    # structure-only multiplier that permits exact matched comparisons.
    "range_structure_multiplier_per_m": terminal_weight / base_denominator_m,
  }


def _trace_summary(trace: list[dict[str, Any]], profile: dict[str, int]) -> dict[str, Any]:
  capture_g = [
    value / 9.80665
    for value in (_finite(row.get("guidance_capture_accel_mps2")) for row in trace)
    if value is not None
  ]
  preclamp_g = [
    value / 9.80665
    for value in (_finite(row.get("guidance_preclamp_accel_mps2")) for row in trace)
    if value is not None
  ]
  postclamp_g = [
    value / 9.80665
    for value in (_finite(row.get("guidance_postclamp_accel_mps2")) for row in trace)
    if value is not None
  ]
  trace_ranges = [
    value
    for value in (_finite(row.get("truth_distance_m")) for row in trace)
    if value is not None and value > 0.0
  ]
  regimes = Counter(
    str(_range_factors(value, profile)["terminal_regime"]) for value in trace_ranges
  )
  sample_count = min(len(preclamp_g), len(postclamp_g))
  return {
    "trace_sample_count": len(trace),
    "max_capture_g": max(capture_g, default=0.0),
    "capture_g_p95": _quantile(capture_g, 0.95),
    "max_preclamp_g": max(preclamp_g, default=0.0),
    "max_postclamp_g": max(postclamp_g, default=0.0),
    "clamp_fraction": (
      sum(before > after + 1.0e-9 for before, after in zip(preclamp_g, postclamp_g))
      / sample_count
      if sample_count
      else 0.0
    ),
    "terminal_regime_sample_counts": dict(sorted(regimes.items())),
  }


def _result_row(
  *,
  case: dict[str, Any],
  profile_row: dict[str, Any],
  result: dict[str, Any],
  matrix: str,
) -> dict[str, Any]:
  profile = dict(profile_row["profile"])
  approach = _approach_observed(result)
  distance_m = _miss_distance(result)
  launch_factors = _range_factors(float(case["range_m"]), profile)
  return {
    "matrix": matrix,
    "case_id": str(case["case_id"]),
    "range_km": float(case["range_km"]),
    "bearing_deg": float(case["bearing_deg"]),
    "offset_deg": float(case["offset_deg"]),
    "launch_class": str(case["launch_class"]),
    "case_group": str(case["case_group"]),
    "profile_id": str(profile_row["profile_id"]),
    "profile": profile,
    "nearest_distance_m": distance_m,
    "rho_fuze": distance_m / R_FUZE_M if distance_m is not None else None,
    "entered_R_fuze": bool(distance_m is not None and distance_m <= R_FUZE_M),
    "nearest_approach_time_s": _finite(approach.get("nearest_approach_time_s")),
    "local_forward_m": _finite(approach.get("local_forward_m")),
    "local_right_m": _finite(approach.get("local_right_m")),
    "local_up_m": _finite(approach.get("local_up_m")),
    "aspect_bucket": str(approach.get("aspect_bucket", "") or ""),
    "launch_range_factors": launch_factors,
    **_trace_summary(list(result.get("guidance_runtime_trace", []) or []), profile),
  }


def _run_case(
  *,
  database_path: Path,
  case: dict[str, Any],
  profile_row: dict[str, Any],
  seed: int,
  trace_stride: int,
  matrix: str,
  runner: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
  print(
    f"[capture-structure:{matrix}] {case['case_id']} {profile_row['profile_id']}",
    file=sys.stderr,
  )
  result = runner(
    database_path=database_path,
    case_id=f"{case['case_id']}__{profile_row['profile_id']}",
    range_m=float(case["range_m"]),
    bearing_deg=float(case["bearing_deg"]),
    seed=int(seed),
    guidance_tuning_overrides=dict(CANDIDATE_TUNING),
    guidance_mechanism_profile=dict(profile_row["profile"]),
    collect_guidance_runtime_trace=True,
    guidance_trace_stride=max(1, int(trace_stride)),
  )
  return _result_row(case=case, profile_row=profile_row, result=result, matrix=matrix)


def run_matrix(
  *,
  database_path: Path = probe.DEFAULT_DATABASE_PATH,
  cases: list[dict[str, Any]],
  profiles: list[dict[str, Any]],
  seed: int = DEFAULT_SEED,
  trace_stride: int = 5,
  matrix: str,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for case in cases:
    for profile_row in profiles:
      rows.append(
        _run_case(
          database_path=database_path,
          case=case,
          profile_row=profile_row,
          seed=seed,
          trace_stride=trace_stride,
          matrix=matrix,
          runner=runner,
        )
      )
  return rows


def _pair_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[tuple[str, float, float, str], list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    grouped[
      (
        str(row["profile_id"]),
        float(row["range_km"]),
        float(row["offset_deg"]),
        str(row["case_group"]),
      )
    ].append(row)
  output: list[dict[str, Any]] = []
  for (profile_id, range_km, offset_deg, case_group), group in sorted(grouped.items()):
    distances = [
      value
      for value in (_finite(row.get("nearest_distance_m")) for row in group)
      if value is not None
    ]
    if not distances:
      continue
    output.append(
      {
        "profile_id": profile_id,
        "range_km": range_km,
        "offset_deg": offset_deg,
        "case_group": case_group,
        "pair_count": len(distances),
        "pair_mean_nearest_distance_m": statistics.fmean(distances),
        "pair_mean_rho_fuze": statistics.fmean(distances) / R_FUZE_M,
        "mirror_abs_difference_m": (
          abs(distances[0] - distances[1]) if len(distances) == 2 else None
        ),
        "pair_entered_R_fuze": all(value <= R_FUZE_M for value in distances),
        "pair_mean_clamp_fraction": statistics.fmean(
          float(row.get("clamp_fraction", 0.0) or 0.0) for row in group
        ),
        "pair_max_capture_g": max(float(row.get("max_capture_g", 0.0) or 0.0) for row in group),
      }
    )
  return output


def matched_effect_rows(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  by_cell: dict[tuple[float, float], dict[str, dict[str, Any]]] = defaultdict(dict)
  for row in pair_rows:
    by_cell[(float(row["range_km"]), float(row["offset_deg"]))][
      str(row["profile_id"])
    ] = row
  output: list[dict[str, Any]] = []
  for (range_km, offset_deg), profiles in sorted(by_cell.items()):
    for effect_id, before_id, after_id in MATCHED_EFFECTS:
      before = profiles.get(before_id)
      after = profiles.get(after_id)
      if before is None or after is None:
        continue
      before_distance = float(before["pair_mean_nearest_distance_m"])
      after_distance = float(after["pair_mean_nearest_distance_m"])
      output.append(
        {
          "effect_id": effect_id,
          "range_km": range_km,
          "offset_deg": offset_deg,
          "case_group": str(before["case_group"]),
          "before_profile": before_id,
          "after_profile": after_id,
          "before_nearest_distance_m": before_distance,
          "after_nearest_distance_m": after_distance,
          "miss_distance_delta_m": after_distance - before_distance,
          "absolute_effect_m": abs(after_distance - before_distance),
          "clamp_fraction_delta": (
            float(after["pair_mean_clamp_fraction"])
            - float(before["pair_mean_clamp_fraction"])
          ),
        }
      )
  return output


def interaction_effect_rows(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  by_cell: dict[tuple[float, float], dict[str, dict[str, Any]]] = defaultdict(dict)
  for row in pair_rows:
    by_cell[(float(row["range_km"]), float(row["offset_deg"]))][
      str(row["profile_id"])
    ] = row
  output: list[dict[str, Any]] = []
  for (range_km, offset_deg), profiles in sorted(by_cell.items()):
    if all(profile_id in profiles for profile_id in ("P1", "P4", "P5", "P6")):
      distance = {
        profile_id: float(profiles[profile_id]["pair_mean_nearest_distance_m"])
        for profile_id in ("P1", "P4", "P5", "P6")
      }
      contrast = distance["P1"] - distance["P4"] - distance["P5"] + distance["P6"]
      output.append(
        {
          "effect_id": "range_interaction",
          "formula": "P1 - P4 - P5 + P6",
          "range_km": range_km,
          "offset_deg": offset_deg,
          "case_group": str(profiles["P1"]["case_group"]),
          "contrast_m": contrast,
          "absolute_effect_m": abs(contrast),
          "contrast_rho_fuze": contrast / R_FUZE_M,
        }
      )
    if all(profile_id in profiles for profile_id in ("P1", "P3", "P4", "P8")):
      distance = {
        profile_id: float(profiles[profile_id]["pair_mean_nearest_distance_m"])
        for profile_id in ("P1", "P3", "P4", "P8")
      }
      contrast = (distance["P1"] - distance["P3"]) - (
        distance["P4"] - distance["P8"]
      )
      output.append(
        {
          "effect_id": "lead_x_terminal_interaction",
          "formula": "(P1 - P3) - (P4 - P8)",
          "range_km": range_km,
          "offset_deg": offset_deg,
          "case_group": str(profiles["P1"]["case_group"]),
          "contrast_m": contrast,
          "absolute_effect_m": abs(contrast),
          "contrast_rho_fuze": contrast / R_FUZE_M,
        }
      )
  return output


def _effect_summary(effects: list[dict[str, Any]]) -> dict[str, Any]:
  grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
  for row in effects:
    grouped[str(row["effect_id"])].append(row)
  output: dict[str, Any] = {}
  for effect_id, group in sorted(grouped.items()):
    signed = [float(row["miss_distance_delta_m"]) for row in group]
    absolute = [abs(value) for value in signed]
    material = [
      row
      for row in group
      if float(row["absolute_effect_m"]) / R_FUZE_M >= 0.05
    ]
    affected_groups = sorted({str(row["case_group"]) for row in material})
    affected_ranges = sorted({float(row["range_km"]) for row in material})
    output[effect_id] = {
      "cell_count": len(group),
      "median_signed_delta_m": statistics.median(signed),
      "mean_absolute_effect_m": statistics.fmean(absolute),
      "max_absolute_effect_m": max(absolute),
      "material_cell_count_ge_0p05_rho": len(material),
      "material_case_groups": affected_groups,
      "material_range_count": len(affected_ranges),
      "improved_cell_count": sum(value < -1.0e-9 for value in signed),
      "degraded_cell_count": sum(value > 1.0e-9 for value in signed),
      "effective_owner": len(material) >= 3,
      "mean_delta_by_case_group_m": {
        name: statistics.fmean(
          float(row["miss_distance_delta_m"])
          for row in group
          if str(row["case_group"]) == name
        )
        for name in sorted({str(row["case_group"]) for row in group})
      },
    }
  return output


def _interaction_summary(interactions: list[dict[str, Any]]) -> dict[str, Any]:
  grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
  for row in interactions:
    grouped[str(row["effect_id"])].append(row)
  output: dict[str, Any] = {}
  for effect_id, group in sorted(grouped.items()):
    signed = [float(row["contrast_m"]) for row in group]
    absolute = [abs(value) for value in signed]
    material = [value for value in absolute if value / R_FUZE_M >= 0.05]
    output[effect_id] = {
      "cell_count": len(group),
      "formula": str(group[0]["formula"]),
      "median_signed_contrast_m": statistics.median(signed),
      "mean_absolute_effect_m": statistics.fmean(absolute),
      "max_absolute_effect_m": max(absolute),
      "material_cell_count_ge_0p05_rho": len(material),
      "effective_owner": len(material) >= 3,
    }
  return output


def _baseline_equivalence(
  *,
  database_path: Path,
  cases: list[dict[str, Any]],
  profiled_rows: list[dict[str, Any]],
  seed: int,
  runner: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
  indexed = {
    (str(row["case_id"]), float(row["bearing_deg"])): row
    for row in profiled_rows
    if row["profile_id"] == "P1"
  }
  output: list[dict[str, Any]] = []
  for case in cases:
    print(f"[capture-structure:equivalence] {case['case_id']}", file=sys.stderr)
    result = runner(
      database_path=database_path,
      case_id=f"{case['case_id']}__candidate_unprofiled",
      range_m=float(case["range_m"]),
      bearing_deg=float(case["bearing_deg"]),
      seed=int(seed),
      guidance_tuning_overrides=dict(CANDIDATE_TUNING),
    )
    unprofiled = _miss_distance(result)
    profiled = indexed[(str(case["case_id"]), float(case["bearing_deg"]))]
    profiled_distance = _finite(profiled.get("nearest_distance_m"))
    delta = (
      profiled_distance - unprofiled
      if profiled_distance is not None and unprofiled is not None
      else None
    )
    output.append(
      {
        "case_id": str(case["case_id"]),
        "range_km": float(case["range_km"]),
        "bearing_deg": float(case["bearing_deg"]),
        "unprofiled_candidate_nearest_distance_m": unprofiled,
        "P1_profiled_nearest_distance_m": profiled_distance,
        "profile_minus_unprofiled_m": delta,
      }
    )
  return output


def _selected_production_equivalence(
  *,
  database_path: Path,
  cases: list[dict[str, Any]],
  profiled_rows: list[dict[str, Any]],
  selected_profile: str | None,
  seed: int,
  runner: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
  if selected_profile != "P0":
    return []
  indexed = {
    (str(row["case_id"]), float(row["bearing_deg"])): row
    for row in profiled_rows
    if row["profile_id"] == selected_profile
  }
  tuning = {**CANDIDATE_TUNING, "capture_guidance_mode": 0}
  output: list[dict[str, Any]] = []
  for case in cases:
    print(f"[capture-structure:selected-production] {case['case_id']}", file=sys.stderr)
    result = runner(
      database_path=database_path,
      case_id=f"{case['case_id']}__selected_production",
      range_m=float(case["range_m"]),
      bearing_deg=float(case["bearing_deg"]),
      seed=int(seed),
      guidance_tuning_overrides=tuning,
    )
    production_distance = _miss_distance(result)
    profiled_distance = _finite(
      indexed[(str(case["case_id"]), float(case["bearing_deg"]))].get("nearest_distance_m")
    )
    output.append(
      {
        "case_id": str(case["case_id"]),
        "range_km": float(case["range_km"]),
        "bearing_deg": float(case["bearing_deg"]),
        "selected_profile": selected_profile,
        "production_capture_guidance_mode": 0,
        "production_nearest_distance_m": production_distance,
        "profiled_nearest_distance_m": profiled_distance,
        "profile_minus_production_m": (
          profiled_distance - production_distance
          if profiled_distance is not None and production_distance is not None
          else None
        ),
      }
    )
  return output


def _profile_score(pair_rows: list[dict[str, Any]], profile_id: str) -> dict[str, Any]:
  rows = [row for row in pair_rows if row["profile_id"] == profile_id]
  n_rows = [row for row in rows if row["case_group"] == "N30"]
  m_rows = [row for row in rows if row["case_group"] == "M45"]
  stress_rows = [row for row in rows if row["case_group"] == "stress60"]
  distances = [float(row["pair_mean_nearest_distance_m"]) for row in rows]
  mirror = [
    float(row["mirror_abs_difference_m"])
    for row in rows
    if _finite(row.get("mirror_abs_difference_m")) is not None
  ]
  profile = next(
    dict(row["profile"]) for row in PROFILES if str(row["profile_id"]) == profile_id
  )
  range_schedule_count = (
    int(profile["capture_base_range_mode"] == BASE_INVERSE_RANGE)
    + int(profile["capture_terminal_weight_mode"] != TERMINAL_UNITY)
    + int(profile["capture_lead_blend_mode"] == LEAD_CURRENT_SCHEDULE)
  )
  boundary_rho = [
    float(row["pair_mean_rho_fuze"])
    for row in rows
    if row["case_group"] in {"M45", "stress60"}
  ]
  # This is a mechanism-selection score, not the final launch-window objective.
  # Old O labels deliberately carry no reward or penalty here.
  return {
    "profile_id": profile_id,
    "N30_all_enter_R_fuze": all(bool(row["pair_entered_R_fuze"]) for row in n_rows),
    "N30_mean_rho_fuze": _mean([float(row["pair_mean_rho_fuze"]) for row in n_rows]),
    "M45_mean_rho_fuze": _mean([float(row["pair_mean_rho_fuze"]) for row in m_rows]),
    "stress60_mean_rho_fuze": _mean(
      [float(row["pair_mean_rho_fuze"]) for row in stress_rows]
    ),
    "boundary_mean_rho_fuze": _mean(boundary_rho),
    "all_anchor_mean_rho_fuze": _mean([value / R_FUZE_M for value in distances]),
    "max_mirror_abs_difference_m": max(mirror, default=0.0),
    "mean_clamp_fraction": _mean(
      [float(row["pair_mean_clamp_fraction"]) for row in rows]
    ),
    "range_schedule_count": range_schedule_count,
    "uses_terminal_clamp": (
      int(profile["capture_terminal_weight_mode"]) == TERMINAL_CURRENT_CLAMPED
    ),
  }


def _selection_summary(
  pair_rows: list[dict[str, Any]],
  effect_summary: dict[str, Any],
  interaction_summary: dict[str, Any],
) -> dict[str, Any]:
  scores = [_profile_score(pair_rows, str(profile["profile_id"])) for profile in PROFILES]
  eligible = [
    row
    for row in scores
    if row["profile_id"] != "P2"
    and bool(row["N30_all_enter_R_fuze"])
    and float(row["max_mirror_abs_difference_m"]) <= 1.0e-3
  ]
  eligible_ids = {str(row["profile_id"]) for row in eligible}
  capture_effect_rows = [
    row for row in matched_effect_rows(pair_rows)
    if row["effect_id"] == "capture_total"
  ]
  capture_systematically_degrades = bool(capture_effect_rows) and all(
    float(row["miss_distance_delta_m"]) > 1.0e-9 for row in capture_effect_rows
  )
  if "P0" in eligible_ids and capture_systematically_degrades:
    selected = "P0"
    reason = (
      "The pursuit-style capture term worsened every matched anchor after world-frame PN was "
      "corrected; retain pure world-frame PN rather than tune compensating range schedules."
    )
  else:
    capture_enabled = [row for row in eligible if row["profile_id"] != "P0"]
    finite_boundary = [
      row
      for row in capture_enabled
      if _finite(row.get("boundary_mean_rho_fuze")) is not None
    ]
    best_boundary_rho = min(
      (float(row["boundary_mean_rho_fuze"]) for row in finite_boundary),
      default=math.inf,
    )
    performance_equivalent = [
      row
      for row in finite_boundary
      if float(row["boundary_mean_rho_fuze"]) <= best_boundary_rho + 0.05
    ]
    ranked = sorted(
      performance_equivalent,
      key=lambda row: (
        int(row["range_schedule_count"]),
        bool(row["uses_terminal_clamp"]),
        float(row["boundary_mean_rho_fuze"]),
        float(row.get("mean_clamp_fraction") or 0.0),
        str(row["profile_id"]),
      ),
    )
    selected = str(ranked[0]["profile_id"]) if ranked else None
    reason = (
      "Retain structures within 0.05 rho_fuze of the best M45/stress60 result, then "
      "remove algebraically duplicated range schedules."
    )
  effective_owners = sorted(
    effect_id
    for effect_id, row in {**effect_summary, **interaction_summary}.items()
    if bool(row.get("effective_owner"))
  )
  return {
    "profile_scores": scores,
    "eligible_profiles": sorted(eligible_ids),
    "selected_profile": selected,
    "selection_policy": {
      "hard_gates": [
        "all N30 signed pairs enter R_fuze",
        "maximum mirror delta <= 1 mm",
        "old O labels are not used as mechanism gates",
      ],
      "performance_equivalence_band_rho_fuze": 0.05,
      "lexicographic_order_within_band": [
        "fewer range schedules",
        "no terminal clamp",
        "lower M45/stress60 mean rho_fuze",
        "lower command clamp fraction",
      ],
      "old_O_labels_used_as_gate": False,
      "capture_systematically_degrades_all_anchor_cells": capture_systematically_degrades,
      "reason": reason,
    },
    "effective_owner_criterion": {
      "material_effect_threshold_rho_fuze": 0.05,
      "material_effect_threshold_m": 0.05 * R_FUZE_M,
      "minimum_material_cells": 3,
      "alternative_future_contour_shift": "2.5 deg or 0.5 km after stage 4",
      "interpretation": (
        "An owner must create a repeatable multi-cell matched effect. A single boundary "
        "outlier is insufficient; the contour-shift alternative becomes available only "
        "after the continuous envelope exists."
      ),
    },
    "effective_owner_effects": effective_owners,
  }


def _acceptance_summary(
  *,
  rows: list[dict[str, Any]],
  pair_rows: list[dict[str, Any]],
  baseline_equivalence: list[dict[str, Any]],
  selected_production_equivalence: list[dict[str, Any]],
  clamp_rows: list[dict[str, Any]],
  selection: dict[str, Any],
) -> dict[str, Any]:
  baseline_deltas = [
    abs(value)
    for value in (_finite(row.get("profile_minus_unprofiled_m")) for row in baseline_equivalence)
    if value is not None
  ]
  selected_production_deltas = [
    abs(value)
    for value in (
      _finite(row.get("profile_minus_production_m"))
      for row in selected_production_equivalence
    )
    if value is not None
  ]
  mirror_deltas = [
    value
    for value in (_finite(row.get("mirror_abs_difference_m")) for row in pair_rows)
    if value is not None
  ]
  postclamp = [float(row.get("max_postclamp_g", 0.0) or 0.0) for row in rows + clamp_rows]
  p0_capture = [
    float(row.get("max_capture_g", 0.0) or 0.0)
    for row in rows
    if row["profile_id"] == "P0"
  ]
  audit_cells = {
    (float(row["range_km"]), float(row["bearing_deg"]), str(row["profile_id"]))
    for row in clamp_rows
  }
  expected_audit_cells = len(CLAMP_AUDIT_RANGES_KM) * len(
    CLAMP_AUDIT_SIGNED_BEARINGS_DEG
  ) * len(CLAMP_AUDIT_PROFILE_IDS)
  return {
    "P1_profile_equivalent_to_unprofiled_candidate_within_1e_3_m": max(
      baseline_deltas, default=math.inf
    )
    <= 1.0e-3,
    "max_P1_profile_equivalence_delta_m": max(baseline_deltas, default=None),
    "selected_profile_matches_production_candidate_within_1e_3_m": (
      bool(selected_production_deltas)
      and max(selected_production_deltas) <= 1.0e-3
    ),
    "max_selected_profile_production_delta_m": max(
      selected_production_deltas, default=None
    ),
    "mirror_symmetric_within_1e_3_m": max(mirror_deltas, default=math.inf) <= 1.0e-3,
    "max_mirror_abs_difference_m": max(mirror_deltas, default=None),
    "P0_capture_component_zero_within_1e_12_g": max(p0_capture, default=math.inf)
    <= 1.0e-12,
    "max_P0_capture_g": max(p0_capture, default=None),
    "postclamp_never_exceeds_35g": max(postclamp, default=math.inf) <= 35.0 + 1.0e-9,
    "max_postclamp_g": max(postclamp, default=None),
    "clamp_audit_complete": len(audit_cells) == expected_audit_cells,
    "clamp_audit_cell_count": len(audit_cells),
    "expected_clamp_audit_cell_count": expected_audit_cells,
    "candidate_structure_selected": selection.get("selected_profile") is not None,
  }


def generate_report(
  *,
  database_path: Path = probe.DEFAULT_DATABASE_PATH,
  cases: list[dict[str, Any]] | None = None,
  profiles: list[dict[str, Any]] | None = None,
  seed: int = DEFAULT_SEED,
  trace_stride: int = 5,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
  run_clamp_audit: bool = True,
  run_baseline_equivalence: bool = True,
) -> dict[str, Any]:
  case_rows = list(cases if cases is not None else anchor_cases())
  profile_rows = list(profiles if profiles is not None else selected_profiles())
  rows = run_matrix(
    database_path=database_path,
    cases=case_rows,
    profiles=profile_rows,
    seed=seed,
    trace_stride=trace_stride,
    matrix="anchor",
    runner=runner,
  )
  pairs = _pair_rows(rows)
  effects = matched_effect_rows(pairs)
  effect_summary = _effect_summary(effects)
  interactions = interaction_effect_rows(pairs)
  interaction_summary = _interaction_summary(interactions)
  profile_ids = {str(row["profile_id"]) for row in profile_rows}
  baseline_equivalence = (
    _baseline_equivalence(
      database_path=database_path,
      cases=case_rows,
      profiled_rows=rows,
      seed=seed,
      runner=runner,
    )
    if run_baseline_equivalence and "P1" in profile_ids
    else []
  )
  clamp_profiles = [
    row for row in PROFILES if str(row["profile_id"]) in CLAMP_AUDIT_PROFILE_IDS
  ]
  clamp_rows = (
    run_matrix(
      database_path=database_path,
      cases=clamp_audit_cases(),
      profiles=clamp_profiles,
      seed=seed,
      trace_stride=trace_stride,
      matrix="clamp_audit",
      runner=runner,
    )
    if run_clamp_audit
    else []
  )
  selection = _selection_summary(pairs, effect_summary, interaction_summary)
  selected_production_equivalence = _selected_production_equivalence(
    database_path=database_path,
    cases=case_rows,
    profiled_rows=rows,
    selected_profile=selection.get("selected_profile"),
    seed=seed,
    runner=runner,
  )
  acceptance = _acceptance_summary(
    rows=rows,
    pair_rows=pairs,
    baseline_equivalence=baseline_equivalence,
    selected_production_equivalence=selected_production_equivalence,
    clamp_rows=clamp_rows,
    selection=selection,
  )
  return {
    "schema_version": SCHEMA_VERSION,
    "status": "capture_structure_ablation_generated",
    "seed": int(seed),
    "R_fuze_m": R_FUZE_M,
    "candidate_tuning": dict(CANDIDATE_TUNING),
    "frozen_mechanisms": {
      "pn": "world LOS history",
      "target_kinematics": "world CV alpha-beta tracker",
      "target_tracker_alpha": 0.20,
      "target_tracker_beta": 0.02,
      "target_motion": "truth constant velocity",
    },
    "capture_structure_contract": {
      "capture_reference_range_m": CAPTURE_REFERENCE_RANGE_M,
      "lead_reference_range_m": LEAD_REFERENCE_RANGE_M,
      "lead_blend_max": LEAD_BLEND_MAX,
      "current_terminal_clamp": [
        CURRENT_TERMINAL_WEIGHT_MIN,
        CURRENT_TERMINAL_WEIGHT_MAX,
      ],
      "base_range_modes": {"0": "inverse_range", "1": "reference_range"},
      "terminal_weight_modes": {
        "0": "current_clamped",
        "1": "unity",
        "2": "reciprocal_unclamped",
      },
      "lead_blend_modes": {
        "0": "current_schedule",
        "1": "constant_max",
        "2": "off",
      },
    },
    "runtime_context": {
      "ef_py_artifact": str(Path(probe.ef_py.__file__).resolve()),
      "case_summary_unit": "left-right pair mean before group aggregation",
      "production_database_modified": False,
    },
    "anchor_case_count": len(case_rows),
    "profile_count": len(profile_rows),
    "anchor_run_count": len(rows),
    "clamp_audit_run_count": len(clamp_rows),
    "baseline_equivalence_run_count": len(baseline_equivalence),
    "selected_production_equivalence_run_count": len(selected_production_equivalence),
    "total_run_count": (
      len(rows) + len(clamp_rows) + len(baseline_equivalence)
      + len(selected_production_equivalence)
    ),
    "cases": case_rows,
    "profiles": profile_rows,
    "rows": rows,
    "pair_rows": pairs,
    "matched_effects": effects,
    "interaction_effects": interactions,
    "baseline_equivalence": baseline_equivalence,
    "selected_production_equivalence": selected_production_equivalence,
    "clamp_audit": {
      "ranges_km": list(CLAMP_AUDIT_RANGES_KM),
      "signed_bearings_deg": list(CLAMP_AUDIT_SIGNED_BEARINGS_DEG),
      "profile_ids": list(CLAMP_AUDIT_PROFILE_IDS),
      "rows": clamp_rows,
    },
    "summary": {
      "matched_effects": effect_summary,
      "interaction_effects": interaction_summary,
      "selection": selection,
      "acceptance": acceptance,
      "passed": all(
        bool(value)
        for key, value in acceptance.items()
        if key
        in {
          "P1_profile_equivalent_to_unprofiled_candidate_within_1e_3_m",
          "selected_profile_matches_production_candidate_within_1e_3_m",
          "mirror_symmetric_within_1e_3_m",
          "P0_capture_component_zero_within_1e_12_g",
          "postclamp_never_exceeds_35g",
          "clamp_audit_complete",
          "candidate_structure_selected",
        }
      ),
    },
    "limitations": [
      "The old O labels are observations only and are not used to select the corrected mechanism.",
      (
        "Matched miss-distance effects include nonlinear trajectory, saturation, "
        "and energy feedback."
      ),
      "Constant-velocity anchors cannot establish maneuver-target APN authority.",
      "The selected structure remains a candidate until the continuous launch window is rebuilt.",
    ],
  }


def _csv_value(value: Any) -> Any:
  if isinstance(value, (dict, list)):
    return json.dumps(value, sort_keys=True, ensure_ascii=True)
  return value


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
  fields = sorted({key for row in rows for key in row})
  with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
      writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _fmt(value: Any, digits: int = 3) -> str:
  parsed = _finite(value)
  return f"{parsed:.{digits}f}" if parsed is not None else "n/a"


def render_chinese_conclusions(report: dict[str, Any]) -> str:
  summary = dict(report.get("summary", {}) or {})
  effects = dict(summary.get("matched_effects", {}) or {})
  interactions = dict(summary.get("interaction_effects", {}) or {})
  selection = dict(summary.get("selection", {}) or {})
  acceptance = dict(summary.get("acceptance", {}) or {})
  selected = selection.get("selected_profile")
  profile_by_id = {str(row["profile_id"]): row for row in report.get("profiles", [])}
  selected_description = (
    str(profile_by_id[selected]["description_zh"])
    if selected is not None and selected in profile_by_id
    else "无候选通过结构门"
  )
  lines = [
    "# 第三阶段：capture 结构消融结论 — 2026-07-15",
    "",
    "## 结论",
    "",
    (
      f"本轮冻结世界系 LOS-history PN、世界系 CV tracker、`N=4`、`35 g` 与 "
      f"`APN gain=0.5`，只改变 capture 的 range 与 lead 结构。共运行 "
      f"`{int(report.get('total_run_count', 0))}` 次确定性案例。"
    ),
    "",
    f"结构选择结果：`{selected or 'none'}`（{selected_description}）。",
    "该选择只准入第四阶段连续窗口重建；它不是最终 AIM-120 默认参数结论。",
    "",
    "## 匹配条件效应",
    "",
    "| Effect | 中位有符号效应 (m) | 平均绝对效应 (m) | 最大效应 (m) | 有效 owner |",
    "| --- | ---: | ---: | ---: | --- |",
  ]
  for effect_id, row in sorted(effects.items()):
    lines.append(
      f"| `{effect_id}` | {_fmt(row.get('median_signed_delta_m'))} | "
      f"{_fmt(row.get('mean_absolute_effect_m'))} | "
      f"{_fmt(row.get('max_absolute_effect_m'))} | "
      f"{'YES' if row.get('effective_owner') else 'NO'} |"
    )
  for effect_id, row in sorted(interactions.items()):
    lines.append(
      f"| `{effect_id}` | {_fmt(row.get('median_signed_contrast_m'))} | "
      f"{_fmt(row.get('mean_absolute_effect_m'))} | "
      f"{_fmt(row.get('max_absolute_effect_m'))} | "
      f"{'YES' if row.get('effective_owner') else 'NO'} |"
    )
  lines.extend(
    [
      "",
      "有效 owner 判据不是“单案改善最大”：matched toggle 必须在至少 3 个单元、"
      "至少 3 个 anchor 单元产生 `|Δrho_fuze|>=0.05` 的重复效应；单个边界异常"
      "不能成为 owner。旧 O 标签不参与选择门。",
      "`capture_total` 的正号表示加入 capture 后最近距恶化；若全部 anchor 同号，"
      "选择纯 world-frame PN，而不是继续给相互补偿的 capture/lead schedule 调参。",
      "",
      "## Clamp 边界审计",
      "",
      "审计覆盖 `2/2.4/3/20/24/28 km × ±15/±30 deg × P1/P4/P7`。"
      "`2.4 km` 与 `24 km` 分别是当前 terminal weight 的上、下 clamp 边界；"
      "P4 固定为 unity，P7 保留 reciprocal 但移除 clamp。",
      "",
      "## 验收",
      "",
    ]
  )
  for name, value in acceptance.items():
    if isinstance(value, bool):
      lines.append(f"- `{name}`: {'PASS' if value else 'FAIL'}")
    else:
      lines.append(f"- `{name}`: `{value}`")
  lines.extend(
    [
      "",
      "## 阶段边界",
      "",
      "- P1 与未附着 diagnostics profile 的候选 runtime 必须逐案等价，否则本轮结构差异无效。",
      "- P0 必须给出严格零 capture 分量，总指令不得超过 35 g。",
      "- 第四阶段必须在选定结构上重建连续 `4..16 km × 0..90 deg` 包线；"
      "不得用旧 `16 km / 30 deg -> O` 反向否决已修正机制。",
      "- 当前匀速矩阵不能授予真实武器、机动目标 APN 或 Pk 权威。",
      "",
    ]
  )
  return "\n".join(lines)


def write_bundle(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "json": str(output_dir / "kill_chain_capture_structure_ablation_20260715.json"),
    "conclusions_zh": str(
      output_dir / "kill_chain_capture_structure_ablation_conclusions_20260715.zh.md"
    ),
    "rows_csv": str(output_dir / "kill_chain_capture_structure_ablation_rows.csv"),
    "effects_csv": str(output_dir / "kill_chain_capture_structure_ablation_effects.csv"),
    "interactions_csv": str(
      output_dir / "kill_chain_capture_structure_ablation_interactions.csv"
    ),
    "clamp_audit_csv": str(
      output_dir / "kill_chain_capture_structure_ablation_clamp_audit.csv"
    ),
  }
  report["artifacts"] = paths
  Path(paths["json"]).write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
  )
  Path(paths["conclusions_zh"]).write_text(
    render_chinese_conclusions(report), encoding="utf-8"
  )
  _write_csv(Path(paths["rows_csv"]), list(report.get("rows", []) or []))
  _write_csv(Path(paths["effects_csv"]), list(report.get("matched_effects", []) or []))
  _write_csv(
    Path(paths["interactions_csv"]),
    list(report.get("interaction_effects", []) or []),
  )
  _write_csv(
    Path(paths["clamp_audit_csv"]),
    list(report.get("clamp_audit", {}).get("rows", []) or []),
  )
  for path in paths.values():
    Path(path).chmod(0o644)
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
  parser.add_argument("--database", type=Path, default=probe.DEFAULT_DATABASE_PATH)
  parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
  parser.add_argument("--trace-stride", type=int, default=5)
  parser.add_argument("--profile", action="append", default=[])
  parser.add_argument("--case-limit", type=int, default=0)
  parser.add_argument("--skip-clamp-audit", action="store_true")
  parser.add_argument("--skip-baseline-equivalence", action="store_true")
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  return parser


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  probe.ef_py.set_log_level("warn")
  cases = anchor_cases()
  if int(args.case_limit) > 0:
    cases = cases[: int(args.case_limit)]
  profiles = selected_profiles(tuple(str(value) for value in args.profile))
  with _native_stdout_to_stderr():
    report = generate_report(
      database_path=Path(args.database),
      cases=cases,
      profiles=profiles,
      seed=int(args.seed),
      trace_stride=max(1, int(args.trace_stride)),
      run_clamp_audit=not bool(args.skip_clamp_audit),
      run_baseline_equivalence=not bool(args.skip_baseline_equivalence),
    )
  report["artifacts"] = write_bundle(report, Path(args.output_dir))
  print(
    json.dumps(
      {
        "passed": bool(report["summary"]["passed"]),
        "selected_profile": report["summary"]["selection"]["selected_profile"],
        "total_run_count": report["total_run_count"],
        "output_dir": str(args.output_dir),
      },
      ensure_ascii=False,
    )
  )
  return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
  raise SystemExit(main())
