#!/usr/bin/env python3
"""Run the P7 continuous-rod projection-floor paired ablation.

The two variants use identical geometry, orientation, seeds, and explicit
ring-band settings.  Only ``projection_min_effect_scale`` changes.  The
report intentionally separates floor localization from downstream response
propagation because the current parameter also supplies the projection curve
intercept.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root, resolve_repo_path  # noqa: E402

ensure_repo_imports()
from tools.geometry import warhead_spatial_structural_admission as common  # noqa: E402


REPO_ROOT = Path(repo_root())
SCHEMA_VERSION = "a2.continuous_rod_projection_floor_ablation.v1"
STATUS = "continuous_rod_projection_floor_ablation_generated"
GENERATED_ON = "2026-09-14"
BASELINE_MIN_EFFECT_SCALE = 0.05
ABLATION_MIN_EFFECT_SCALE = 0.0
TOLERANCE = 1.0e-9
DEFAULT_OUTPUT_PATH = Path(
  resolve_repo_path(
    "docs",
    "systems",
    "effects",
    "reviews",
    "continuous_rod_projection_floor_ablation_20260914",
    "review_packets",
    "continuous_rod_projection_floor_ablation_20260914.json",
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
  cases: list[dict[str, Any]], *, seed: int, minimum_effect_scale: float
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
    )
    for index, case in enumerate(cases)
  ]


def _row_key(row: dict[str, Any]) -> str:
  return str(row["case_id"])


def _float(event: dict[str, Any], field: str) -> float:
  return float(event[field])


def _close(left: float, right: float) -> bool:
  return math.isclose(left, right, rel_tol=1.0e-8, abs_tol=TOLERANCE)


def _load_key(row: dict[str, Any]) -> tuple[str, str, str]:
  return (
    str(row["component_name"]),
    str(row["component_system"]),
    str(row["component_redundancy_group_id"]),
  )


def _response_key(row: dict[str, Any]) -> tuple[str, str, str]:
  return _load_key(row)


def _pair_component_rows(
  baseline: dict[str, Any], ablated: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
  baseline_loads = {
    _load_key(row): row for row in baseline["component_mechanism_load_rows"]
  }
  ablated_loads = {
    _load_key(row): row for row in ablated["component_mechanism_load_rows"]
  }
  load_pairs: list[dict[str, Any]] = []
  load_residuals: list[dict[str, Any]] = []
  for key in sorted(set(baseline_loads) | set(ablated_loads)):
    left = baseline_loads.get(key)
    right = ablated_loads.get(key)
    if left is None or right is None:
      load_residuals.append({"key": list(key), "reason": "load_row_presence_changed"})
      continue
    load_pairs.append(
      {
        "key": list(key),
        "baseline_effect_scale": float(left["effect_scale"]),
        "ablated_effect_scale": float(right["effect_scale"]),
        "effect_scale_delta": float(left["effect_scale"])
        - float(right["effect_scale"]),
        "baseline_failure_probability": float(left["component_failure_probability"]),
        "ablated_failure_probability": float(right["component_failure_probability"]),
        "failure_probability_delta": float(left["component_failure_probability"])
        - float(right["component_failure_probability"]),
        "baseline_rod_cut_margin": float(left["mechanism_rod_cut_margin"]),
        "ablated_rod_cut_margin": float(right["mechanism_rod_cut_margin"]),
        "rod_cut_margin_delta": float(left["mechanism_rod_cut_margin"])
        - float(right["mechanism_rod_cut_margin"]),
      }
    )
  baseline_responses = {
    _response_key(row): row for row in baseline["component_response_rows"]
  }
  ablated_responses = {
    _response_key(row): row for row in ablated["component_response_rows"]
  }
  response_pairs: list[dict[str, Any]] = []
  for key in sorted(set(baseline_responses) | set(ablated_responses)):
    left = baseline_responses.get(key)
    right = ablated_responses.get(key)
    if left is None or right is None:
      load_residuals.append(
        {"key": list(key), "reason": "response_row_presence_changed"}
      )
      continue
    response_pairs.append(
      {
        "key": list(key),
        "baseline_failure_probability": float(left["failure_probability"]),
        "ablated_failure_probability": float(right["failure_probability"]),
        "failure_probability_delta": float(left["failure_probability"])
        - float(right["failure_probability"]),
        "baseline_integrity_after": float(left["integrity_after"]),
        "ablated_integrity_after": float(right["integrity_after"]),
        "integrity_after_delta": float(left["integrity_after"])
        - float(right["integrity_after"]),
        "baseline_failure_mode": str(left["failure_mode"]),
        "ablated_failure_mode": str(right["failure_mode"]),
      }
    )
  return load_pairs + [{"_response_pair": pair} for pair in response_pairs], load_residuals


def _pair_row(baseline_row: dict[str, Any], ablated_row: dict[str, Any]) -> dict[str, Any]:
  baseline = baseline_row["event"]
  ablated = ablated_row["event"]
  component_pairs, component_residuals = _pair_component_rows(baseline, ablated)
  load_pairs = [pair for pair in component_pairs if "_response_pair" not in pair]
  response_pairs = [pair["_response_pair"] for pair in component_pairs if "_response_pair" in pair]
  return {
    "case_id": _row_key(baseline_row),
    "direction": baseline_row["direction"],
    "standoff_m": float(baseline_row["standoff_m"]),
    "heading_deg": float(baseline_row["detonation_attitude_deg"][0]),
    "geometry": {
      "baseline_intersection": bool(baseline["continuous_rod_ring_band_intersection"]),
      "ablated_intersection": bool(ablated["continuous_rod_ring_band_intersection"]),
      "baseline_coverage_fraction": _float(
        baseline, "continuous_rod_angular_coverage_fraction"
      ),
      "ablated_coverage_fraction": _float(
        ablated, "continuous_rod_angular_coverage_fraction"
      ),
      "coverage_fraction_delta": _float(
        baseline, "continuous_rod_angular_coverage_fraction"
      )
      - _float(ablated, "continuous_rod_angular_coverage_fraction"),
      "baseline_nearest_intersection_distance_m": _float(
        baseline, "continuous_rod_nearest_intersection_distance_m"
      ),
      "ablated_nearest_intersection_distance_m": _float(
        ablated, "continuous_rod_nearest_intersection_distance_m"
      ),
    },
    "projection": {
      "baseline_min_bound": _float(baseline, "spatial_projection_min_bound"),
      "ablated_min_bound": _float(ablated, "spatial_projection_min_bound"),
      "baseline_base_scale": _float(baseline, "spatial_projection_base_scale"),
      "ablated_base_scale": _float(ablated, "spatial_projection_base_scale"),
      "base_scale_delta": _float(baseline, "spatial_projection_base_scale")
      - _float(ablated, "spatial_projection_base_scale"),
      "baseline_preclamp_scale": _float(baseline, "spatial_projection_preclamp_scale"),
      "ablated_preclamp_scale": _float(ablated, "spatial_projection_preclamp_scale"),
      "preclamp_scale_delta": _float(baseline, "spatial_projection_preclamp_scale")
      - _float(ablated, "spatial_projection_preclamp_scale"),
      "baseline_effect_scale": _float(baseline, "spatial_projection_effect_scale"),
      "ablated_effect_scale": _float(ablated, "spatial_projection_effect_scale"),
      "effect_scale_delta": _float(baseline, "spatial_projection_effect_scale")
      - _float(ablated, "spatial_projection_effect_scale"),
      "baseline_clamped": bool(baseline["spatial_projection_effect_scale_clamped"]),
      "ablated_clamped": bool(ablated["spatial_projection_effect_scale_clamped"]),
    },
    "trace": {
      "baseline_primary_name": str(baseline["component_primary_name"]),
      "ablated_primary_name": str(ablated["component_primary_name"]),
      "baseline_primary_system": str(baseline["component_primary_system"]),
      "ablated_primary_system": str(ablated["component_primary_system"]),
      "baseline_primary_redundancy_group_id": str(
        baseline["component_primary_redundancy_group_id"]
      ),
      "ablated_primary_redundancy_group_id": str(
        ablated["component_primary_redundancy_group_id"]
      ),
      "baseline_trace_valid": bool(baseline["spatial_projection_trace_valid"]),
      "ablated_trace_valid": bool(ablated["spatial_projection_trace_valid"]),
    },
    "mechanism": {
      "baseline_rod_cut_margin": _float(baseline, "mechanism_rod_cut_margin"),
      "ablated_rod_cut_margin": _float(ablated, "mechanism_rod_cut_margin"),
      "rod_cut_margin_delta": _float(baseline, "mechanism_rod_cut_margin")
      - _float(ablated, "mechanism_rod_cut_margin"),
    },
    "component_load_pairs": load_pairs,
    "component_response_pairs": response_pairs,
    "component_pair_residuals": component_residuals,
  }


def _evaluate_pairs(pairs: list[dict[str, Any]]) -> dict[str, Any]:
  hit_pairs = [
    pair for pair in pairs if bool(pair["geometry"]["baseline_intersection"])
  ]
  baseline_clamped = [
    pair for pair in hit_pairs if bool(pair["projection"]["baseline_clamped"])
  ]
  non_clamped = [pair for pair in hit_pairs if pair not in baseline_clamped]
  all_load_pairs = [
    load
    for pair in pairs
    for load in pair["component_load_pairs"]
  ]
  all_response_pairs = [
    response
    for pair in pairs
    for response in pair["component_response_pairs"]
  ]
  geometry_topology_residuals = [
    {
      "case_id": pair["case_id"],
      "reason": "intersection_or_component_row_set_changed",
    }
    for pair in pairs
    if pair["geometry"]["baseline_intersection"]
    != pair["geometry"]["ablated_intersection"]
    or bool(pair["component_pair_residuals"])
  ]
  representative_trace_residuals = [
    {
      "case_id": pair["case_id"],
      "baseline_coverage_fraction": pair["geometry"]["baseline_coverage_fraction"],
      "ablated_coverage_fraction": pair["geometry"]["ablated_coverage_fraction"],
      "baseline_nearest_intersection_distance_m": pair["geometry"][
        "baseline_nearest_intersection_distance_m"
      ],
      "ablated_nearest_intersection_distance_m": pair["geometry"][
        "ablated_nearest_intersection_distance_m"
      ],
    }
    for pair in pairs
    if pair["geometry"]["baseline_intersection"]
    == pair["geometry"]["ablated_intersection"]
    and (
      not _close(
        pair["geometry"]["baseline_coverage_fraction"],
        pair["geometry"]["ablated_coverage_fraction"],
      )
      or not _close(
        pair["geometry"]["baseline_nearest_intersection_distance_m"],
        pair["geometry"]["ablated_nearest_intersection_distance_m"],
      )
      or pair["trace"]["baseline_primary_name"]
      != pair["trace"]["ablated_primary_name"]
      or pair["trace"]["baseline_primary_system"]
      != pair["trace"]["ablated_primary_system"]
      or pair["trace"]["baseline_primary_redundancy_group_id"]
      != pair["trace"]["ablated_primary_redundancy_group_id"]
      or pair["trace"]["baseline_trace_valid"]
      != pair["trace"]["ablated_trace_valid"]
    )
  ]
  non_clamped_residuals = [
    {
      "case_id": pair["case_id"],
      "effect_scale_delta": pair["projection"]["effect_scale_delta"],
      "base_scale_delta": pair["projection"]["base_scale_delta"],
      "preclamp_scale_delta": pair["projection"]["preclamp_scale_delta"],
    }
    for pair in non_clamped
    if abs(float(pair["projection"]["effect_scale_delta"])) > TOLERANCE
  ]
  floor_rows = [
    pair
    for pair in baseline_clamped
    if not _close(
      pair["projection"]["baseline_effect_scale"],
      pair["projection"]["baseline_min_bound"],
    )
    or not _close(
      pair["projection"]["ablated_effect_scale"],
      pair["projection"]["ablated_preclamp_scale"],
    )
  ]
  mechanism_residuals = [
    {
      "case_id": pair["case_id"],
      "rod_cut_margin_delta": pair["mechanism"]["rod_cut_margin_delta"],
    }
    for pair in pairs
    if abs(float(pair["mechanism"]["rod_cut_margin_delta"])) > TOLERANCE
  ]
  load_effect_residuals = [
    load
    for load in all_load_pairs
    if float(load["effect_scale_delta"]) < -TOLERANCE
  ]
  response_mode_changes = [
    response
    for response in all_response_pairs
    if response["baseline_failure_mode"] != response["ablated_failure_mode"]
  ]
  effect_deltas = [float(pair["projection"]["effect_scale_delta"]) for pair in hit_pairs]
  clamped_deltas = [
    float(pair["projection"]["effect_scale_delta"]) for pair in baseline_clamped
  ]
  non_clamped_deltas = [
    float(pair["projection"]["effect_scale_delta"]) for pair in non_clamped
  ]
  load_deltas = [float(load["effect_scale_delta"]) for load in all_load_pairs]
  response_probability_deltas = [
    float(response["failure_probability_delta"]) for response in all_response_pairs
  ]
  integrity_deltas = [float(response["integrity_after_delta"]) for response in all_response_pairs]
  metrics = {
    "pair_count": len(pairs),
    "expected_pair_count": common.EXPECTED_FAMILY_ROW_COUNT,
    "baseline_intersection_count": len(hit_pairs),
    "baseline_non_intersection_count": len(pairs) - len(hit_pairs),
    "baseline_clamped_count": len(baseline_clamped),
    "ablated_clamped_count": sum(
      1
      for pair in pairs
      if bool(pair["projection"]["ablated_clamped"])
    ),
    "geometry_topology_residual_count": len(geometry_topology_residuals),
    "representative_trace_stability_residual_count": len(
      representative_trace_residuals
    ),
    "floor_application_residual_count": len(floor_rows),
    "non_clamped_effect_shift_count": len(non_clamped_residuals),
    "mechanism_invariance_residual_count": len(mechanism_residuals),
    "component_load_pair_count": len(all_load_pairs),
    "component_load_effect_shift_count": sum(
      1 for delta in load_deltas if abs(delta) > TOLERANCE
    ),
    "component_load_failure_probability_shift_count": sum(
      1
      for load in all_load_pairs
      if abs(float(load["failure_probability_delta"])) > TOLERANCE
    ),
    "component_response_pair_count": len(all_response_pairs),
    "component_response_probability_shift_count": sum(
      1
      for delta in response_probability_deltas
      if abs(delta) > TOLERANCE
    ),
    "component_response_integrity_shift_count": sum(
      1 for delta in integrity_deltas if abs(delta) > TOLERANCE
    ),
    "component_response_failure_mode_change_count": len(response_mode_changes),
    "effect_delta_mean_all_hit": sum(effect_deltas) / len(effect_deltas)
    if effect_deltas
    else 0.0,
    "effect_delta_max_all_hit": max(effect_deltas, default=0.0),
    "effect_delta_mean_clamped": sum(clamped_deltas) / len(clamped_deltas)
    if clamped_deltas
    else 0.0,
    "effect_delta_max_clamped": max(clamped_deltas, default=0.0),
    "effect_delta_mean_non_clamped": sum(non_clamped_deltas) / len(non_clamped_deltas)
    if non_clamped_deltas
    else 0.0,
    "effect_delta_max_non_clamped": max(non_clamped_deltas, default=0.0),
    "component_load_effect_delta_mean": sum(load_deltas) / len(load_deltas)
    if load_deltas
    else 0.0,
    "component_load_effect_delta_max": max(load_deltas, default=0.0),
    "component_response_probability_delta_mean": sum(response_probability_deltas)
    / len(response_probability_deltas)
    if response_probability_deltas
    else 0.0,
    "component_response_probability_delta_max": max(response_probability_deltas, default=0.0),
    "component_response_integrity_delta_mean": sum(integrity_deltas) / len(integrity_deltas)
    if integrity_deltas
    else 0.0,
    "component_response_integrity_delta_max_absolute": max(
      (abs(delta) for delta in integrity_deltas), default=0.0
    ),
  }
  geometry_gate = metrics["geometry_topology_residual_count"] == 0
  trace_stability_gate = metrics["representative_trace_stability_residual_count"] == 0
  floor_localization_gate = (
    metrics["baseline_clamped_count"] > 0
    and metrics["ablated_clamped_count"] == 0
    and metrics["floor_application_residual_count"] == 0
    and metrics["non_clamped_effect_shift_count"] == 0
  )
  mechanism_gate = metrics["mechanism_invariance_residual_count"] == 0
  propagation_gate = bool(
    all_load_pairs
    and metrics["component_load_effect_shift_count"] > 0
    and metrics["component_response_pair_count"] > 0
    and metrics["component_response_failure_mode_change_count"] == 0
  )
  return {
    "metrics": metrics,
    "gates": {
      "complete_matrix": (
        "passed"
        if metrics["pair_count"] == metrics["expected_pair_count"]
        else "not_evaluated"
      ),
      "geometry_topology_invariance": "passed" if geometry_gate else "failed",
      "representative_trace_stability": (
        "passed" if trace_stability_gate else "failed"
      ),
      "floor_localization": "passed" if floor_localization_gate else "failed",
      "mechanism_load_invariance": "passed" if mechanism_gate else "failed",
      "component_response_propagation": "passed" if propagation_gate else "failed",
      "p7_projection_floor_clamp_admission": (
        "passed"
        if metrics["pair_count"] == metrics["expected_pair_count"]
        and geometry_gate
        and trace_stability_gate
        and floor_localization_gate
        and mechanism_gate
        else "held"
      ),
    },
    "residuals": {
      "geometry_topology": geometry_topology_residuals,
      "representative_trace_stability": representative_trace_residuals,
      "floor_application": floor_rows,
      "non_clamped_effect_shift": non_clamped_residuals,
      "mechanism": mechanism_residuals,
      "component_load": load_effect_residuals,
      "component_response_failure_mode_changes": response_mode_changes,
    },
  }


def generate_report(*, seed: int = 20260914, limit: int | None = None) -> dict[str, Any]:
  common._configure_runtime_log_level()
  cases = _rod_cases()
  if limit is not None:
    cases = cases[: max(0, int(limit))]
  baseline_rows = _run_rows(
    cases, seed=seed, minimum_effect_scale=BASELINE_MIN_EFFECT_SCALE
  )
  ablated_rows = _run_rows(
    cases, seed=seed, minimum_effect_scale=ABLATION_MIN_EFFECT_SCALE
  )
  pairs = [
    _pair_row(baseline, ablated)
    for baseline, ablated in zip(baseline_rows, ablated_rows)
  ]
  evaluation = _evaluate_pairs(pairs)
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
      "baseline": {
        "projection_min_effect_scale": BASELINE_MIN_EFFECT_SCALE,
        "meaning": "current curve intercept and final lower bound",
      },
      "ablated": {
        "projection_min_effect_scale": ABLATION_MIN_EFFECT_SCALE,
        "meaning": "zero curve intercept and zero final lower bound",
      },
      "controlled_variables": [
        "same case matrix",
        "same per-case seed",
        "same explicit expanding-ring-band profile",
        "same 720 x 5 geometry samples",
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
      "next_gate": "P7.1 separate projection curve intercept from final minimum bound",
      "blockers": [
        "projection_min_effect_scale changes the full spatial curve, not only the lower clamp",
        "24 surviving 10 m intersections are clamped in the baseline variant",
        "component-load response topology and vulnerability/consequence remain separate gates",
      ],
    },
    "evaluation": evaluation,
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
  return 0 if report["evaluation"]["gates"]["p7_projection_floor_clamp_admission"] == "passed" else 2


if __name__ == "__main__":
  raise SystemExit(main())
