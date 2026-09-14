#!/usr/bin/env python3
"""Run P7.1 with an independent projection curve floor and final lower bound."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root, resolve_repo_path  # noqa: E402

ensure_repo_imports()
from tools.geometry import continuous_rod_projection_floor_ablation as floor  # noqa: E402
from tools.geometry import warhead_spatial_structural_admission as common  # noqa: E402


REPO_ROOT = Path(repo_root())
SCHEMA_VERSION = "a2.continuous_rod_projection_curve_floor_decoupling.v1"
STATUS = "continuous_rod_projection_curve_floor_decoupling_generated"
GENERATED_ON = "2026-09-14"
CURVE_FLOOR_EFFECT_SCALE = 0.05
BASELINE_MIN_EFFECT_SCALE = 0.05
DECOUPLED_MIN_EFFECT_SCALE = 0.0
TOLERANCE = 1.0e-9
DEFAULT_OUTPUT_PATH = Path(
  resolve_repo_path(
    "docs",
    "systems",
    "effects",
    "reviews",
    "continuous_rod_projection_curve_floor_decoupling_20260914",
    "review_packets",
    "continuous_rod_projection_curve_floor_decoupling_20260914.json",
  )
)


def _relative_path(path: Path) -> str:
  try:
    return str(path.resolve().relative_to(REPO_ROOT))
  except ValueError:
    return str(path.resolve())


def _rod_cases() -> list[dict[str, Any]]:
  return [
    case
    for case in common._case_definitions()
    if str(case["warhead_family"]) == "continuous_rod"
  ]


def _run_rows(
  cases: list[dict[str, Any]],
  *,
  seed: int,
  minimum_effect_scale: float | None,
  curve_floor_effect_scale: float | None,
) -> list[dict[str, Any]]:
  return [
    common._event_row(
      case,
      seed + index,
      explicit_continuous_rod=True,
      continuous_rod_band_half_angle_deg=6.0,
      continuous_rod_azimuthal_samples=720,
      continuous_rod_polar_samples=5,
      continuous_rod_azimuthal_phase_deg=0.0,
      projection_min_effect_scale=minimum_effect_scale,
      projection_curve_floor_effect_scale=curve_floor_effect_scale,
    )
    for index, case in enumerate(cases)
  ]


def _event_pair_summary(
  baseline: dict[str, Any], variant: dict[str, Any]
) -> dict[str, Any]:
  baseline_event = baseline["event"]
  variant_event = variant["event"]
  pair = floor._pair_row(baseline, variant)
  return {
    **pair,
    "projection": {
      **pair["projection"],
      "curve_floor_delta": float(
        baseline_event["spatial_projection_curve_floor_scale"]
      )
      - float(variant_event["spatial_projection_curve_floor_scale"]),
    },
  }


def _compare_default_curve_floor(
  default_rows: list[dict[str, Any]], explicit_rows: list[dict[str, Any]]
) -> dict[str, Any]:
  default_by_id = {str(row["case_id"]): row for row in default_rows}
  explicit_by_id = {str(row["case_id"]): row for row in explicit_rows}
  fields = (
    "spatial_projection_effect_scale",
    "spatial_projection_base_scale",
    "spatial_projection_curve_floor_scale",
    "spatial_projection_preclamp_scale",
    "mechanism_rod_cut_margin",
  )
  mismatches: list[dict[str, Any]] = []
  for case_id in sorted(set(default_by_id) & set(explicit_by_id)):
    left = default_by_id[case_id]["event"]
    right = explicit_by_id[case_id]["event"]
    for field in fields:
      if not math.isclose(float(left[field]), float(right[field]), rel_tol=1.0e-8, abs_tol=TOLERANCE):
        mismatches.append(
          {
            "case_id": case_id,
            "field": field,
            "default": float(left[field]),
            "explicit": float(right[field]),
          }
        )
  return {
    "status": "passed" if not mismatches and len(default_by_id) == len(explicit_by_id) else "failed",
    "compared_row_count": len(set(default_by_id) & set(explicit_by_id)),
    "missing_case_count": len(set(default_by_id) ^ set(explicit_by_id)),
    "mismatch_count": len(mismatches),
    "mismatches": mismatches[:20],
  }


def _decoupled_evaluation(
  pairs: list[dict[str, Any]],
) -> dict[str, Any]:
  hit_pairs = [
    pair for pair in pairs if bool(pair["geometry"]["baseline_intersection"])
  ]
  baseline_clamped = [
    pair for pair in hit_pairs if bool(pair["projection"]["baseline_clamped"])
  ]
  non_clamped = [pair for pair in hit_pairs if pair not in baseline_clamped]
  geometry_residuals = [
    pair["case_id"]
    for pair in pairs
    if pair["geometry"]["baseline_intersection"]
    != pair["geometry"]["ablated_intersection"]
    or not math.isclose(
      pair["geometry"]["baseline_coverage_fraction"],
      pair["geometry"]["ablated_coverage_fraction"],
      rel_tol=1.0e-8,
      abs_tol=TOLERANCE,
    )
    or not math.isclose(
      pair["geometry"]["baseline_nearest_intersection_distance_m"],
      pair["geometry"]["ablated_nearest_intersection_distance_m"],
      rel_tol=1.0e-8,
      abs_tol=TOLERANCE,
    )
    or bool(pair["component_pair_residuals"])
  ]
  non_clamped_effect_shift = [
    pair["case_id"]
    for pair in non_clamped
    if abs(float(pair["projection"]["effect_scale_delta"])) > TOLERANCE
  ]
  floor_application_residuals = [
    pair["case_id"]
    for pair in baseline_clamped
    if not math.isclose(
      pair["projection"]["baseline_effect_scale"],
      pair["projection"]["baseline_min_bound"],
      rel_tol=1.0e-8,
      abs_tol=TOLERANCE,
    )
    or not math.isclose(
      pair["projection"]["ablated_effect_scale"],
      pair["projection"]["ablated_preclamp_scale"],
      rel_tol=1.0e-8,
      abs_tol=TOLERANCE,
    )
  ]
  trace_residuals = [
    pair["case_id"]
    for pair in pairs
    if abs(float(pair["projection"]["curve_floor_delta"])) > TOLERANCE
    or pair["trace"]["baseline_primary_name"]
    != pair["trace"]["ablated_primary_name"]
    or pair["trace"]["baseline_primary_system"]
    != pair["trace"]["ablated_primary_system"]
    or pair["trace"]["baseline_primary_redundancy_group_id"]
    != pair["trace"]["ablated_primary_redundancy_group_id"]
    or pair["trace"]["baseline_trace_valid"]
    != pair["trace"]["ablated_trace_valid"]
  ]
  mechanism_residuals = [
    pair["case_id"]
    for pair in pairs
    if abs(float(pair["mechanism"]["rod_cut_margin_delta"])) > TOLERANCE
  ]
  response_mode_changes = [
    response
    for pair in pairs
    for response in pair["component_response_pairs"]
    if response["baseline_failure_mode"] != response["ablated_failure_mode"]
  ]
  load_pairs = [
    load
    for pair in pairs
    for load in pair["component_load_pairs"]
  ]
  response_pairs = [
    response
    for pair in pairs
    for response in pair["component_response_pairs"]
  ]
  effect_deltas = [float(pair["projection"]["effect_scale_delta"]) for pair in hit_pairs]
  clamped_deltas = [
    float(pair["projection"]["effect_scale_delta"]) for pair in baseline_clamped
  ]
  response_deltas = [
    float(response["failure_probability_delta"]) for response in response_pairs
  ]
  integrity_deltas = [
    float(response["integrity_after_delta"]) for response in response_pairs
  ]
  metrics = {
    "pair_count": len(pairs),
    "expected_pair_count": common.EXPECTED_FAMILY_ROW_COUNT,
    "intersection_count": len(hit_pairs),
    "baseline_clamped_count": len(baseline_clamped),
    "ablated_clamped_count": sum(
      1 for pair in pairs if bool(pair["projection"]["ablated_clamped"])
    ),
    "geometry_residual_count": len(geometry_residuals),
    "floor_application_residual_count": len(floor_application_residuals),
    "non_clamped_effect_shift_count": len(non_clamped_effect_shift),
    "representative_trace_residual_count": len(trace_residuals),
    "mechanism_residual_count": len(mechanism_residuals),
    "component_load_pair_count": len(load_pairs),
    "component_load_effect_shift_count": sum(
      1 for load in load_pairs if abs(float(load["effect_scale_delta"])) > TOLERANCE
    ),
    "component_response_pair_count": len(response_pairs),
    "component_response_probability_shift_count": sum(
      1 for delta in response_deltas if abs(delta) > TOLERANCE
    ),
    "component_response_integrity_shift_count": sum(
      1 for delta in integrity_deltas if abs(delta) > TOLERANCE
    ),
    "component_response_failure_mode_change_count": len(response_mode_changes),
    "effect_delta_mean_hit": sum(effect_deltas) / len(effect_deltas)
    if effect_deltas
    else 0.0,
    "effect_delta_max_hit": max(effect_deltas, default=0.0),
    "effect_delta_mean_clamped": sum(clamped_deltas) / len(clamped_deltas)
    if clamped_deltas
    else 0.0,
    "effect_delta_max_clamped": max(clamped_deltas, default=0.0),
    "component_response_probability_delta_mean": sum(response_deltas)
    / len(response_deltas)
    if response_deltas
    else 0.0,
    "component_response_integrity_delta_mean": sum(integrity_deltas)
    / len(integrity_deltas)
    if integrity_deltas
    else 0.0,
  }
  gates = {
    "complete_matrix": "passed"
    if len(pairs) == common.EXPECTED_FAMILY_ROW_COUNT
    else "failed",
    "geometry_invariance": "passed" if not geometry_residuals else "failed",
    "floor_only_localization": "passed"
    if not floor_application_residuals and not non_clamped_effect_shift
    else "failed",
    "representative_trace_stability": "passed" if not trace_residuals else "failed",
    "mechanism_load_invariance": "passed" if not mechanism_residuals else "failed",
    "downstream_effect_propagation": "passed"
    if metrics["component_load_effect_shift_count"] > 0
    and metrics["component_response_pair_count"] > 0
    and not response_mode_changes
    else "failed",
  }
  gates["p7_1_curve_minimum_separation"] = (
    "passed"
    if all(value == "passed" for value in gates.values())
    else "held"
  )
  return {
    "metrics": metrics,
    "gates": gates,
    "residuals": {
      "geometry": geometry_residuals,
      "floor_application": floor_application_residuals,
      "non_clamped_effect_shift": non_clamped_effect_shift,
      "representative_trace": trace_residuals,
      "mechanism": mechanism_residuals,
      "component_response_failure_mode_changes": response_mode_changes,
    },
  }


def generate_report(*, seed: int = 20260914, limit: int | None = None) -> dict[str, Any]:
  common._configure_runtime_log_level()
  cases = _rod_cases()
  if limit is not None:
    cases = cases[: max(0, int(limit))]
  default_rows = _run_rows(
    cases,
    seed=seed,
    minimum_effect_scale=None,
    curve_floor_effect_scale=None,
  )
  explicit_baseline_rows = _run_rows(
    cases,
    seed=seed,
    minimum_effect_scale=BASELINE_MIN_EFFECT_SCALE,
    curve_floor_effect_scale=CURVE_FLOOR_EFFECT_SCALE,
  )
  decoupled_rows = _run_rows(
    cases,
    seed=seed,
    minimum_effect_scale=DECOUPLED_MIN_EFFECT_SCALE,
    curve_floor_effect_scale=CURVE_FLOOR_EFFECT_SCALE,
  )
  pairs = [
    _event_pair_summary(baseline, decoupled)
    for baseline, decoupled in zip(explicit_baseline_rows, decoupled_rows)
  ]
  evaluation = _decoupled_evaluation(pairs)
  compatibility = _compare_default_curve_floor(default_rows, explicit_baseline_rows)
  evaluation["gates"]["default_curve_floor_compatibility"] = compatibility["status"]
  evaluation["gates"]["p7_1_curve_minimum_separation"] = (
    "passed"
    if all(value == "passed" for value in evaluation["gates"].values())
    else "held"
  )
  return {
    "schema_version": SCHEMA_VERSION,
    "status": STATUS,
    "generated_on": GENERATED_ON,
    "authority_boundary": {
      "guidance_bypassed": True,
      "fuze_decision_authority": False,
      "synthetic_warhead_profile": True,
      "default_database_modified": False,
      "real_weapon_pk_authority": False,
      "integrated_kill_chain_admission": False,
    },
    "ablation": {
      "explicit_baseline": {
        "projection_min_effect_scale": BASELINE_MIN_EFFECT_SCALE,
        "projection_curve_floor_effect_scale": CURVE_FLOOR_EFFECT_SCALE,
      },
      "decoupled_ablation": {
        "projection_min_effect_scale": DECOUPLED_MIN_EFFECT_SCALE,
        "projection_curve_floor_effect_scale": CURVE_FLOOR_EFFECT_SCALE,
      },
      "controlled_variables": [
        "same 192-case matrix",
        "same per-case seed",
        "same explicit expanding-ring-band settings",
        "same target database and component geometry",
      ],
    },
    "matrix": {
      "target_unit": "F-16C_Block50",
      "standoff_reference": "distance outward from the selected hitbox-envelope face",
      "directions": list(common.DIRECTION_ANCHORS),
      "standoff_distances_m": list(common.STANDOFF_DISTANCES_M),
      "detonation_headings_deg": list(common.ATTITUDES_DEG),
      "case_count": len(cases),
    },
    "admission_decision": {
      **evaluation["gates"],
      "next_gate": "P8 component-load admission",
      "blockers": [
        "the 0.05 curve floor and 0.00 final lower bound are structural test parameters, not calibrated weapon data",
        "component-load topology and vulnerability/consequence authority remain separate gates",
        "integrated guidance-fuze-warhead Pk authority is not evaluated",
      ],
    },
    "evaluation": evaluation,
    "default_curve_floor_compatibility": compatibility,
    "pairs": pairs,
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
  parser.add_argument("--seed", type=int, default=20260914)
  parser.add_argument("--limit", type=int, default=None, help="run only the first N rows")
  args = parser.parse_args()
  report = generate_report(seed=args.seed, limit=args.limit)
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(
    json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
  )
  print(
    json.dumps(
      {
        "output": _relative_path(args.output),
        "admission_decision": report["admission_decision"],
        "metrics": report["evaluation"]["metrics"],
      },
      indent=2,
    )
  )
  return 0 if report["admission_decision"]["p7_1_curve_minimum_separation"] == "passed" else 2


if __name__ == "__main__":
  raise SystemExit(main())
