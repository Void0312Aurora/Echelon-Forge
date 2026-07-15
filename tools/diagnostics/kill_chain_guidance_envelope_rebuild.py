#!/usr/bin/env python3
"""Rebuild the CV launch envelope for the selected production guidance mechanisms.

The tool deliberately runs the production tuning surface without attaching a
diagnostics mechanism profile.  It first measures a 1 km x 5 degree grid, then
adds a 0.5 km x 2.5 degree boundary refinement selected from the measured data.
No smoothing or class post-processing is applied to hide non-monotonic results.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.diagnostics import kill_chain_decoupling_probe as probe  # noqa: E402
from tools.diagnostics import kill_chain_expectation_harness as old_harness  # noqa: E402


SCHEMA_VERSION = "a2.kill_chain_guidance_envelope_rebuild.v1"
MANIFEST_SCHEMA_VERSION = "a2.kill_chain_guidance_envelope_manifest.v1"
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/"
  "kill_chain_guidance_envelope_rebuild_20260715"
)
DEFAULT_STEM = "kill_chain_guidance_envelope_rebuild_20260715"
DEFAULT_SEEDS = (20260621, 20260622, 20260623)
MAIN_RANGES_KM = tuple(float(value) for value in range(4, 17))
MAIN_ANGLES_DEG = tuple(float(value) for value in range(0, 91, 5))
MAIN_RANGE_STEP_KM = 1.0
MAIN_ANGLE_STEP_DEG = 5.0
REFINEMENT_RANGE_STEP_KM = 0.5
REFINEMENT_ANGLE_STEP_DEG = 2.5
R_FUZE_M = 15.0
BOUNDARY_RHO_BAND = 0.25

# Stage 1/2 production candidates plus the stage-3 selected pure-PN structure.
# These are passed through MissileTuning; no diagnostics profile is attached.
PRODUCTION_CANDIDATE_TUNING: dict[str, float | int] = {
  "pn_los_rate_source": 1,
  "target_kinematics_estimator": 1,
  "target_tracker_alpha": 0.20,
  "target_tracker_beta": 0.02,
  "capture_guidance_mode": 0,
  "nav_gain": 4.0,
  "max_lateral_g": 35.0,
  "apn_target_accel_gain": 0.5,
}

ROBUST_HIT = "robust_hit"
ROBUST_MISS = "robust_miss"
MIXED = "mixed"


def _finite(value: Any) -> float | None:
  try:
    parsed = float(value)
  except Exception:
    return None
  return parsed if math.isfinite(parsed) else None


def _token(value: float) -> str:
  return f"{float(value):g}".replace("-", "m").replace(".", "p")


def _signed_bearings(angle_deg: float) -> tuple[float, ...]:
  angle = float(angle_deg)
  return (0.0,) if abs(angle) <= 1.0e-12 else (-angle, angle)


def _case_id(
  *, tier: str, range_km: float, angle_deg: float, bearing_deg: float, seed: int
) -> str:
  sign = "p" if bearing_deg >= 0.0 else "m"
  return (
    f"guidance_envelope_{tier}_{_token(range_km)}km_"
    f"{sign}{_token(abs(bearing_deg))}deg_s{int(seed)}"
  )


def _miss_distance(result: dict[str, Any]) -> float:
  for key in ("nearest_miss_distance_m", "truth_min_distance_m"):
    value = _finite(result.get(key))
    if value is not None:
      return value
  raise RuntimeError(
    f"guidance case {result.get('case_id', '<unknown>')} has no finite miss distance"
  )


def _approach_observation(result: dict[str, Any]) -> dict[str, Any]:
  for row in list(result.get("stage_abstractions", []) or []):
    if str(row.get("abstraction_stage", "") or "") == "approach":
      return dict(row.get("observed", {}) or {})
  return {}


def _resolved_runtime_mismatches(result: dict[str, Any]) -> list[str]:
  runtime = dict(result.get("resolved_guidance_runtime", {}) or {})
  expected = {
    "nav_gain": PRODUCTION_CANDIDATE_TUNING["nav_gain"],
    "pn_los_rate_source": PRODUCTION_CANDIDATE_TUNING["pn_los_rate_source"],
    "target_kinematics_estimator": PRODUCTION_CANDIDATE_TUNING[
      "target_kinematics_estimator"
    ],
    "capture_guidance_mode": PRODUCTION_CANDIDATE_TUNING[
      "capture_guidance_mode"
    ],
    "target_tracker_alpha": PRODUCTION_CANDIDATE_TUNING["target_tracker_alpha"],
    "target_tracker_beta": PRODUCTION_CANDIDATE_TUNING["target_tracker_beta"],
    "apn_target_accel_gain": PRODUCTION_CANDIDATE_TUNING[
      "apn_target_accel_gain"
    ],
    "guidance_max_lateral_g": PRODUCTION_CANDIDATE_TUNING["max_lateral_g"],
  }
  mismatches: list[str] = []
  integer_fields = {
    "pn_los_rate_source",
    "target_kinematics_estimator",
    "capture_guidance_mode",
  }
  for key, expected_value in expected.items():
    observed = runtime.get(key)
    if key in integer_fields:
      try:
        matches = int(observed) == int(expected_value)
      except Exception:
        matches = False
    else:
      observed_float = _finite(observed)
      matches = observed_float is not None and math.isclose(
        observed_float, float(expected_value), rel_tol=0.0, abs_tol=1.0e-12
      )
    if not matches:
      mismatches.append(f"{key}:expected={expected_value}:observed={observed}")
  return mismatches


def _run_one(
  *,
  database_path: Path,
  tier: str,
  range_km: float,
  angle_deg: float,
  bearing_deg: float,
  seed: int,
  refinement_reasons: tuple[str, ...] = (),
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> dict[str, Any]:
  case_id = _case_id(
    tier=tier,
    range_km=range_km,
    angle_deg=angle_deg,
    bearing_deg=bearing_deg,
    seed=seed,
  )
  print(f"[guidance-envelope:{tier}] {case_id}", file=sys.stderr)
  result = runner(
    database_path=database_path,
    case_id=case_id,
    range_m=float(range_km) * 1000.0,
    bearing_deg=float(bearing_deg),
    seed=int(seed),
    guidance_tuning_overrides=dict(PRODUCTION_CANDIDATE_TUNING),
  )
  distance_m = _miss_distance(result)
  mechanism_profile = result.get("guidance_mechanism_profile")
  approach = _approach_observation(result)
  runtime_mismatches = _resolved_runtime_mismatches(result)
  return {
    "grid_tier": tier,
    "case_id": case_id,
    "range_km": float(range_km),
    "range_m": float(range_km) * 1000.0,
    "offset_deg": float(angle_deg),
    "signed_bearing_deg": float(bearing_deg),
    "seed": int(seed),
    "nearest_distance_m": distance_m,
    "rho_fuze": distance_m / R_FUZE_M,
    "entered_R_fuze": distance_m <= R_FUZE_M,
    "fuze_triggered": bool(result.get("fuze_triggered")),
    "max_achieved_lateral_g": float(result.get("max_achieved_lateral_g", 0.0) or 0.0),
    "max_capture_component_g": float(result.get("max_capture_component_g", 0.0) or 0.0),
    "max_preclamp_command_g": float(result.get("max_preclamp_command_g", 0.0) or 0.0),
    "max_postclamp_command_g": float(result.get("max_postclamp_command_g", 0.0) or 0.0),
    "guidance_runtime_observation_count": int(
      result.get("guidance_runtime_observation_count", 0) or 0
    ),
    "guidance_runtime_missing_acceleration_diagnostics_count": int(
      result.get("guidance_runtime_missing_acceleration_diagnostics_count", 0) or 0
    ),
    "guidance_saturated_sample_count": int(
      result.get("guidance_saturated_sample_count", 0) or 0
    ),
    "guidance_saturation_fraction": float(
      result.get("guidance_saturation_fraction", 0.0) or 0.0
    ),
    "nearest_approach_time_s": _finite(approach.get("nearest_approach_time_s")),
    "nearest_approach_closure_mps": _finite(approach.get("closure_mps")),
    "resolved_guidance_runtime": dict(result.get("resolved_guidance_runtime", {}) or {}),
    "resolved_runtime_contract_matches": not runtime_mismatches,
    "resolved_runtime_contract_mismatches": runtime_mismatches,
    "diagnostics_profile_attached": mechanism_profile is not None,
    "refinement_reasons": list(refinement_reasons),
  }


def run_grid(
  *,
  database_path: Path,
  tier: str,
  coordinates: Iterable[tuple[float, float]],
  seeds: tuple[int, ...],
  refinement_reason_map: dict[tuple[float, float], set[str]] | None = None,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  reason_map = refinement_reason_map or {}
  for range_km, angle_deg in sorted(set(coordinates)):
    reasons = tuple(sorted(reason_map.get((range_km, angle_deg), set())))
    for seed in seeds:
      for bearing_deg in _signed_bearings(angle_deg):
        rows.append(
          _run_one(
            database_path=database_path,
            tier=tier,
            range_km=range_km,
            angle_deg=angle_deg,
            bearing_deg=bearing_deg,
            seed=seed,
            refinement_reasons=reasons,
            runner=runner,
          )
        )
  return rows


def _robust_state(rhos: list[float]) -> str:
  if rhos and max(rhos) <= 1.0:
    return ROBUST_HIT
  if rhos and min(rhos) > 1.0:
    return ROBUST_MISS
  return MIXED


def aggregate_cells(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[tuple[str, float, float], list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    grouped[
      (str(row["grid_tier"]), float(row["range_km"]), float(row["offset_deg"]))
    ].append(row)

  output: list[dict[str, Any]] = []
  for (tier, range_km, angle_deg), group in sorted(grouped.items()):
    rhos = [float(row["rho_fuze"]) for row in group]
    distances = [float(row["nearest_distance_m"]) for row in group]
    bearings = sorted({float(row["signed_bearing_deg"]) for row in group})
    seeds = sorted({int(row["seed"]) for row in group})
    mirror_distance_deltas: list[float] = []
    mirror_rho_deltas: list[float] = []
    mirror_entry_consistency: list[bool] = []
    for seed in seeds:
      seed_rows = [row for row in group if int(row["seed"]) == seed]
      if angle_deg == 0.0:
        mirror_distance_deltas.append(0.0)
        mirror_rho_deltas.append(0.0)
        mirror_entry_consistency.append(True)
      elif len(seed_rows) == 2:
        mirror_distance_deltas.append(
          abs(
            float(seed_rows[0]["nearest_distance_m"])
            - float(seed_rows[1]["nearest_distance_m"])
          )
        )
        mirror_rho_deltas.append(
          abs(float(seed_rows[0]["rho_fuze"]) - float(seed_rows[1]["rho_fuze"]))
        )
        mirror_entry_consistency.append(
          bool(seed_rows[0]["entered_R_fuze"])
          == bool(seed_rows[1]["entered_R_fuze"])
        )
      else:
        mirror_entry_consistency.append(False)
    seed_distance_spreads: list[float] = []
    seed_rho_spreads: list[float] = []
    for bearing in bearings:
      signed_rows = [
        row for row in group if float(row["signed_bearing_deg"]) == bearing
      ]
      signed_distances = [float(row["nearest_distance_m"]) for row in signed_rows]
      signed_rhos = [float(row["rho_fuze"]) for row in signed_rows]
      seed_distance_spreads.append(max(signed_distances) - min(signed_distances))
      seed_rho_spreads.append(max(signed_rhos) - min(signed_rhos))
    reasons = sorted(
      {
        str(reason)
        for row in group
        for reason in list(row.get("refinement_reasons", []) or [])
      }
    )
    output.append(
      {
        "grid_tier": tier,
        "range_km": range_km,
        "offset_deg": angle_deg,
        "run_count": len(group),
        "seed_count": len(seeds),
        "signed_bearing_count": len(bearings),
        "rho_min": min(rhos),
        "rho_max": max(rhos),
        "rho_mean": statistics.fmean(rhos),
        "rho_median": statistics.median(rhos),
        "nearest_distance_min_m": min(distances),
        "nearest_distance_max_m": max(distances),
        "nearest_distance_mean_m": statistics.fmean(distances),
        "hit_run_count": sum(bool(row["entered_R_fuze"]) for row in group),
        "robust_state": _robust_state(rhos),
        "minimum_abs_rho_minus_one": min(abs(value - 1.0) for value in rhos),
        "within_boundary_rho_band": min(abs(value - 1.0) for value in rhos)
        <= BOUNDARY_RHO_BAND,
        "max_mirror_abs_difference_m": max(mirror_distance_deltas, default=0.0),
        "max_mirror_abs_difference_rho": max(mirror_rho_deltas, default=0.0),
        "mirror_entry_classification_consistent": all(mirror_entry_consistency),
        "max_seed_spread_m": max(seed_distance_spreads, default=0.0),
        "max_seed_spread_rho": max(seed_rho_spreads, default=0.0),
        "max_achieved_lateral_g": max(
          float(row["max_achieved_lateral_g"]) for row in group
        ),
        "max_capture_component_g": max(
          float(row["max_capture_component_g"]) for row in group
        ),
        "max_preclamp_command_g": max(
          float(row["max_preclamp_command_g"]) for row in group
        ),
        "max_postclamp_command_g": max(
          float(row["max_postclamp_command_g"]) for row in group
        ),
        "max_guidance_saturation_fraction": max(
          float(row["guidance_saturation_fraction"]) for row in group
        ),
        "resolved_runtime_contract_matches": all(
          bool(row["resolved_runtime_contract_matches"]) for row in group
        ),
        "diagnostics_profile_attached": any(
          bool(row["diagnostics_profile_attached"]) for row in group
        ),
        "refinement_reasons": reasons,
      }
    )
  return output


def _main_neighbors(
  coordinate: tuple[float, float],
  coordinates: set[tuple[float, float]],
  *,
  include_diagonal: bool,
) -> list[tuple[float, float]]:
  range_km, angle_deg = coordinate
  output: list[tuple[float, float]] = []
  for range_delta in (-MAIN_RANGE_STEP_KM, 0.0, MAIN_RANGE_STEP_KM):
    for angle_delta in (-MAIN_ANGLE_STEP_DEG, 0.0, MAIN_ANGLE_STEP_DEG):
      if range_delta == 0.0 and angle_delta == 0.0:
        continue
      if not include_diagonal and range_delta != 0.0 and angle_delta != 0.0:
        continue
      candidate = (range_km + range_delta, angle_deg + angle_delta)
      if candidate in coordinates:
        output.append(candidate)
  return output


def classify_main_cells(main_cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
  indexed = {
    (float(row["range_km"]), float(row["offset_deg"])): dict(row)
    for row in main_cells
  }
  coordinates = set(indexed)
  output: list[dict[str, Any]] = []
  for coordinate, row in sorted(indexed.items()):
    neighbors = _main_neighbors(coordinate, coordinates, include_diagonal=True)
    neighbor_states = [str(indexed[item]["robust_state"]) for item in neighbors]
    state = str(row["robust_state"])
    if state == ROBUST_HIT and all(value == ROBUST_HIT for value in neighbor_states):
      launch_class = "N"
      reason = "cell_and_all_existing_8_neighbors_robust_hit"
    elif state == ROBUST_MISS and all(value == ROBUST_MISS for value in neighbor_states):
      launch_class = "O"
      reason = "cell_and_all_existing_8_neighbors_robust_miss"
    else:
      launch_class = "M"
      reason = "mixed_or_adjacent_to_a_different_robust_state"
    classified = dict(row)
    classified.update(
      {
        "reclassified_launch_class": launch_class,
        "classification_reason": reason,
        "existing_8_neighbor_count": len(neighbors),
        "neighbor_robust_hit_count": neighbor_states.count(ROBUST_HIT),
        "neighbor_mixed_count": neighbor_states.count(MIXED),
        "neighbor_robust_miss_count": neighbor_states.count(ROBUST_MISS),
      }
    )
    output.append(classified)
  return output


def refinement_coordinates(
  main_cells: list[dict[str, Any]],
) -> tuple[dict[tuple[float, float], set[str]], list[dict[str, Any]]]:
  indexed = {
    (float(row["range_km"]), float(row["offset_deg"])): row
    for row in main_cells
  }
  coordinates = set(indexed)
  flagged: dict[tuple[float, float], set[str]] = defaultdict(set)
  edges: list[dict[str, Any]] = []
  for coordinate, row in sorted(indexed.items()):
    if bool(row["within_boundary_rho_band"]):
      flagged[coordinate].add(
        f"rho_band:{_token(coordinate[0])}km:{_token(coordinate[1])}deg"
      )
    range_km, angle_deg = coordinate
    for neighbor in (
      (range_km + MAIN_RANGE_STEP_KM, angle_deg),
      (range_km, angle_deg + MAIN_ANGLE_STEP_DEG),
    ):
      if neighbor not in coordinates:
        continue
      before = str(row["robust_state"])
      after = str(indexed[neighbor]["robust_state"])
      if before == after:
        continue
      edge_id = (
        f"state_edge:{_token(range_km)}km:{_token(angle_deg)}deg->"
        f"{_token(neighbor[0])}km:{_token(neighbor[1])}deg"
      )
      flagged[coordinate].add(edge_id)
      flagged[neighbor].add(edge_id)
      edges.append(
        {
          "from_range_km": range_km,
          "from_offset_deg": angle_deg,
          "from_state": before,
          "to_range_km": neighbor[0],
          "to_offset_deg": neighbor[1],
          "to_state": after,
          "edge_id": edge_id,
        }
      )

  refinement: dict[tuple[float, float], set[str]] = defaultdict(set)
  minimum_range = min(item[0] for item in coordinates)
  maximum_range = max(item[0] for item in coordinates)
  minimum_angle = min(item[1] for item in coordinates)
  maximum_angle = max(item[1] for item in coordinates)
  for (range_km, angle_deg), reasons in flagged.items():
    for range_delta in (
      -REFINEMENT_RANGE_STEP_KM,
      0.0,
      REFINEMENT_RANGE_STEP_KM,
    ):
      for angle_delta in (
        -REFINEMENT_ANGLE_STEP_DEG,
        0.0,
        REFINEMENT_ANGLE_STEP_DEG,
      ):
        candidate = (
          round(range_km + range_delta, 6),
          round(angle_deg + angle_delta, 6),
        )
        if not (
          minimum_range <= candidate[0] <= maximum_range
          and minimum_angle <= candidate[1] <= maximum_angle
        ):
          continue
        if candidate in coordinates:
          continue
        refinement[candidate].update(reasons)
  return dict(refinement), edges


def _component_rows(
  coordinates: set[tuple[float, float]],
  selected: set[tuple[float, float]],
) -> list[list[tuple[float, float]]]:
  remaining = set(selected)
  components: list[list[tuple[float, float]]] = []
  while remaining:
    start = min(remaining)
    queue: deque[tuple[float, float]] = deque([start])
    remaining.remove(start)
    component: list[tuple[float, float]] = []
    while queue:
      current = queue.popleft()
      component.append(current)
      for neighbor in _main_neighbors(current, coordinates, include_diagonal=False):
        if neighbor in remaining:
          remaining.remove(neighbor)
          queue.append(neighbor)
    components.append(sorted(component))
  return sorted(components, key=lambda value: (-len(value), value))


def _holes(
  coordinates: set[tuple[float, float]],
  occupied: set[tuple[float, float]],
) -> list[list[tuple[float, float]]]:
  complement = coordinates - occupied
  components = _component_rows(coordinates, complement)
  ranges = [item[0] for item in coordinates]
  angles = [item[1] for item in coordinates]
  minimum_range, maximum_range = min(ranges), max(ranges)
  minimum_angle, maximum_angle = min(angles), max(angles)
  output: list[list[tuple[float, float]]] = []
  for component in components:
    touches_boundary = any(
      range_km in {minimum_range, maximum_range}
      or angle_deg in {minimum_angle, maximum_angle}
      for range_km, angle_deg in component
    )
    if not touches_boundary:
      output.append(component)
  return output


def topology_audit(main_cells: list[dict[str, Any]]) -> dict[str, Any]:
  indexed = {
    (float(row["range_km"]), float(row["offset_deg"])): row
    for row in main_cells
  }
  coordinates = set(indexed)
  hit_coordinates = {
    coordinate
    for coordinate, row in indexed.items()
    if row["robust_state"] == ROBUST_HIT
  }
  miss_coordinates = {
    coordinate
    for coordinate, row in indexed.items()
    if row["robust_state"] == ROBUST_MISS
  }
  n_coordinates = {
    coordinate
    for coordinate, row in indexed.items()
    if row.get("reclassified_launch_class") == "N"
  }
  o_coordinates = {
    coordinate
    for coordinate, row in indexed.items()
    if row.get("reclassified_launch_class") == "O"
  }

  angular_reversals: list[dict[str, Any]] = []
  for range_km in sorted({item[0] for item in coordinates}):
    rows = [
      indexed[(range_km, angle_deg)]
      for angle_deg in sorted(item[1] for item in coordinates if item[0] == range_km)
    ]
    prior_misses: list[float] = []
    for row in rows:
      state = str(row["robust_state"])
      angle_deg = float(row["offset_deg"])
      if state == ROBUST_MISS:
        prior_misses.append(angle_deg)
      elif state == ROBUST_HIT and prior_misses:
        angular_reversals.append(
          {
            "range_km": range_km,
            "earlier_robust_miss_angle_deg": prior_misses[-1],
            "later_robust_hit_angle_deg": angle_deg,
          }
        )

  range_intervals: list[dict[str, Any]] = []
  range_multi_interval_violations: list[dict[str, Any]] = []
  for angle_deg in sorted({item[1] for item in coordinates}):
    rows = [
      indexed[(range_km, angle_deg)]
      for range_km in sorted(item[0] for item in coordinates if item[1] == angle_deg)
    ]
    intervals: list[list[float]] = []
    active: list[float] = []
    for row in rows:
      if row["robust_state"] == ROBUST_HIT:
        active.append(float(row["range_km"]))
      elif active:
        intervals.append(active)
        active = []
    if active:
      intervals.append(active)
    range_row = {
      "offset_deg": angle_deg,
      "robust_hit_interval_count": len(intervals),
      "robust_hit_intervals_km": [
        {"minimum_range_km": min(values), "maximum_range_km": max(values)}
        for values in intervals
      ],
    }
    range_intervals.append(range_row)
    if len(intervals) > 1:
      range_multi_interval_violations.append(range_row)

  hit_components = _component_rows(coordinates, hit_coordinates)
  miss_components = _component_rows(coordinates, miss_coordinates)
  n_components = _component_rows(coordinates, n_coordinates)
  o_components = _component_rows(coordinates, o_coordinates)
  hit_holes = _holes(coordinates, hit_coordinates)
  miss_holes = _holes(coordinates, miss_coordinates)
  expected_shape_passed = (
    not angular_reversals
    and not range_multi_interval_violations
    and not hit_holes
    and len(hit_components) <= 1
  )
  return {
    "policy": {
      "angle_axis": (
        "at fixed range, robust_miss followed by a larger-angle robust_hit "
        "is a reversal"
      ),
      "range_axis": (
        "at fixed angle, the robust-hit ranges may form at most one interval; "
        "near-O -> hit -> far-O is allowed"
      ),
      "connectivity": "4-neighbor on the complete main grid",
      "mixed_cells": "not treated as robust hit or robust miss",
    },
    "all_main_cells_robust_hit": len(hit_coordinates) == len(coordinates),
    "all_main_cells_robust_miss": len(miss_coordinates) == len(coordinates),
    "robust_hit_component_count": len(hit_components),
    "robust_hit_component_sizes": [len(value) for value in hit_components],
    "robust_miss_component_count": len(miss_components),
    "robust_miss_component_sizes": [len(value) for value in miss_components],
    "N_component_count": len(n_components),
    "N_component_sizes": [len(value) for value in n_components],
    "O_component_count": len(o_components),
    "O_component_sizes": [len(value) for value in o_components],
    "robust_hit_internal_hole_count": len(hit_holes),
    "robust_hit_internal_holes": hit_holes,
    "robust_miss_internal_hole_count": len(miss_holes),
    "robust_miss_internal_holes": miss_holes,
    "angular_miss_to_hit_reversal_count": len(angular_reversals),
    "angular_miss_to_hit_reversals": angular_reversals,
    "range_hit_interval_rows": range_intervals,
    "range_multi_interval_violation_count": len(range_multi_interval_violations),
    "range_multi_interval_violations": range_multi_interval_violations,
    "expected_shape_passed": expected_shape_passed,
  }


def theta_fuze_rows(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
  for row in cells:
    grouped[float(row["range_km"])].append(row)
  output: list[dict[str, Any]] = []
  for range_km, group in sorted(grouped.items()):
    ordered = sorted(group, key=lambda row: float(row["offset_deg"]))
    hits = [row for row in ordered if row["robust_state"] == ROBUST_HIT]
    misses = [row for row in ordered if row["robust_state"] == ROBUST_MISS]
    mixed = [row for row in ordered if row["robust_state"] == MIXED]
    reversals = []
    seen_miss: float | None = None
    for row in ordered:
      if row["robust_state"] == ROBUST_MISS:
        seen_miss = float(row["offset_deg"])
      elif row["robust_state"] == ROBUST_HIT and seen_miss is not None:
        reversals.append(
          {
            "earlier_miss_angle_deg": seen_miss,
            "later_hit_angle_deg": float(row["offset_deg"]),
          }
        )
    max_hit = max((float(row["offset_deg"]) for row in hits), default=None)
    later_misses = [
      float(row["offset_deg"])
      for row in misses
      if max_hit is None or float(row["offset_deg"]) > max_hit
    ]
    output.append(
      {
        "range_km": range_km,
        "sampled_angle_count": len(ordered),
        "theta_fuze_robust_hit_max_deg": max_hit,
        "first_robust_miss_angle_deg": min(
          (float(row["offset_deg"]) for row in misses), default=None
        ),
        "first_robust_miss_above_theta_deg": min(later_misses, default=None),
        "mixed_angles_deg": [float(row["offset_deg"]) for row in mixed],
        "angular_miss_to_hit_reversal_count": len(reversals),
        "angular_miss_to_hit_reversals": reversals,
        "right_censored_at_90deg": bool(
          max_hit == 90.0
          and all(row["robust_state"] == ROBUST_HIT for row in ordered)
        ),
        "boundary_status": (
          "nonmonotonic"
          if reversals
          else "all_sampled_hit"
          if ordered and all(row["robust_state"] == ROBUST_HIT for row in ordered)
          else "all_sampled_miss"
          if ordered and all(row["robust_state"] == ROBUST_MISS for row in ordered)
          else "bracketed_or_mixed"
        ),
      }
    )
  return output


def range_boundary_rows(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
  for row in cells:
    grouped[float(row["offset_deg"])].append(row)
  output: list[dict[str, Any]] = []
  for angle_deg, group in sorted(grouped.items()):
    ordered = sorted(group, key=lambda row: float(row["range_km"]))
    hit_ranges = [
      float(row["range_km"]) for row in ordered if row["robust_state"] == ROBUST_HIT
    ]
    mixed_ranges = [
      float(row["range_km"]) for row in ordered if row["robust_state"] == MIXED
    ]
    blocks: list[list[float]] = []
    active: list[float] = []
    for row in ordered:
      if row["robust_state"] == ROBUST_HIT:
        active.append(float(row["range_km"]))
      elif active:
        blocks.append(active)
        active = []
    if active:
      blocks.append(active)
    output.append(
      {
        "offset_deg": angle_deg,
        "sampled_range_count": len(ordered),
        "minimum_robust_hit_range_km": min(hit_ranges, default=None),
        "maximum_robust_hit_range_km": max(hit_ranges, default=None),
        "mixed_ranges_km": mixed_ranges,
        "robust_hit_interval_count": len(blocks),
        "robust_hit_intervals_km": [
          {"minimum_range_km": min(block), "maximum_range_km": max(block)}
          for block in blocks
        ],
        "boundary_status": (
          "multiple_hit_intervals"
          if len(blocks) > 1
          else "single_hit_interval"
          if len(blocks) == 1
          else "no_robust_hit"
        ),
      }
    )
  return output


def old_label_differences(main_cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
  indexed = {
    (float(row["range_km"]), float(row["offset_deg"])): row
    for row in main_cells
  }
  output: list[dict[str, Any]] = []
  for range_km, angle_table in sorted(old_harness.CV_ANCHOR_CLASSES.items()):
    for angle_deg, old_class in sorted(angle_table.items()):
      row = indexed.get((float(range_km), float(angle_deg)))
      if row is None:
        continue
      new_class = str(row["reclassified_launch_class"])
      output.append(
        {
          "range_km": float(range_km),
          "offset_deg": float(angle_deg),
          "old_launch_class": str(old_class),
          "new_launch_class": new_class,
          "changed": str(old_class) != new_class,
          "transition": f"{old_class}->{new_class}",
          "robust_state": str(row["robust_state"]),
          "rho_min": float(row["rho_min"]),
          "rho_max": float(row["rho_max"]),
        }
      )
  return output


def _expected_run_count(
  coordinates: Iterable[tuple[float, float]], seeds: tuple[int, ...]
) -> int:
  return sum(len(_signed_bearings(angle_deg)) * len(seeds) for _, angle_deg in coordinates)


def _artifact_relpath(path: Path) -> str:
  try:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))
  except ValueError:
    return str(path.resolve())


def _csv_value(value: Any) -> Any:
  if isinstance(value, (dict, list, tuple)):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)
  return value


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
  fieldnames = sorted({key for row in rows for key in row})
  with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    if fieldnames:
      writer.writeheader()
      for row in rows:
        writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _git_value(*args: str) -> str:
  completed = subprocess.run(
    ["git", *args],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  return completed.stdout.strip() if completed.returncode == 0 else ""


def build_report(
  *,
  database_path: Path = probe.DEFAULT_DATABASE_PATH,
  ranges_km: tuple[float, ...] = MAIN_RANGES_KM,
  angles_deg: tuple[float, ...] = MAIN_ANGLES_DEG,
  seeds: tuple[int, ...] = DEFAULT_SEEDS,
  enable_refinement: bool = True,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> dict[str, Any]:
  main_coordinates = tuple(
    (float(range_km), float(angle_deg))
    for range_km in sorted(set(ranges_km))
    for angle_deg in sorted(set(angles_deg))
  )
  main_runs = run_grid(
    database_path=database_path,
    tier="main",
    coordinates=main_coordinates,
    seeds=seeds,
    runner=runner,
  )
  main_cells = classify_main_cells(aggregate_cells(main_runs))
  reason_map, state_change_edges = refinement_coordinates(main_cells)
  if not enable_refinement:
    reason_map = {}
  refinement_runs = run_grid(
    database_path=database_path,
    tier="refinement",
    coordinates=tuple(reason_map),
    seeds=seeds,
    refinement_reason_map=reason_map,
    runner=runner,
  )
  refinement_cells = aggregate_cells(refinement_runs)
  for row in refinement_cells:
    row["reclassified_launch_class"] = None
    row["classification_reason"] = "refinement_observation_not_morphologically_classified"
  all_runs = [*main_runs, *refinement_runs]
  all_cells = [*main_cells, *refinement_cells]
  topology = topology_audit(main_cells)
  theta_rows = theta_fuze_rows(all_cells)
  range_rows = range_boundary_rows(all_cells)
  sampled_angular_reversals = [
    {
      "range_km": float(row["range_km"]),
      **dict(reversal),
    }
    for row in theta_rows
    for reversal in list(row["angular_miss_to_hit_reversals"])
  ]
  sampled_range_multi_intervals = [
    row for row in range_rows if int(row["robust_hit_interval_count"]) > 1
  ]
  topology["refinement_aware_sampled_audit"] = {
    "scope": "all measured main and selected refinement cells",
    "angular_miss_to_hit_reversal_count": len(sampled_angular_reversals),
    "angular_miss_to_hit_reversals": sampled_angular_reversals,
    "range_multi_interval_violation_count": len(sampled_range_multi_intervals),
    "range_multi_interval_violations": sampled_range_multi_intervals,
  }
  old_rows = old_label_differences(main_cells)

  expected_main_runs = _expected_run_count(main_coordinates, seeds)
  expected_refinement_runs = _expected_run_count(tuple(reason_map), seeds)
  formal_full_grid = (
    set(ranges_km) == set(MAIN_RANGES_KM)
    and set(angles_deg) == set(MAIN_ANGLES_DEG)
  )
  max_g = max(
    (float(row["max_achieved_lateral_g"]) for row in all_runs), default=0.0
  )
  max_capture_g = max(
    (float(row["max_capture_component_g"]) for row in all_runs), default=0.0
  )
  max_preclamp_g = max(
    (float(row["max_preclamp_command_g"]) for row in all_runs), default=0.0
  )
  max_postclamp_g = max(
    (float(row["max_postclamp_command_g"]) for row in all_runs), default=0.0
  )
  max_saturation_fraction = max(
    (float(row["guidance_saturation_fraction"]) for row in all_runs), default=0.0
  )
  max_mirror_m = max(
    (float(row["max_mirror_abs_difference_m"]) for row in all_cells), default=0.0
  )
  mirror_classification_consistent = all(
    bool(row["mirror_entry_classification_consistent"]) for row in all_cells
  )
  max_seed_spread_m = max(
    (float(row["max_seed_spread_m"]) for row in all_cells), default=0.0
  )
  diagnostics_profile_count = sum(
    bool(row["diagnostics_profile_attached"]) for row in all_runs
  )
  runtime_observation_missing_run_count = sum(
    int(row["guidance_runtime_observation_count"]) <= 0 for row in all_runs
  )
  runtime_diagnostic_missing_run_count = sum(
    int(row["guidance_runtime_missing_acceleration_diagnostics_count"]) > 0
    for row in all_runs
  )
  resolved_runtime_mismatch_run_count = sum(
    not bool(row["resolved_runtime_contract_matches"]) for row in all_runs
  )
  expected_old_count = sum(len(value) for value in old_harness.CV_ANCHOR_CLASSES.values())
  data_gates = {
    "main_grid_run_count_complete": len(main_runs) == expected_main_runs,
    "refinement_run_count_complete": len(refinement_runs) == expected_refinement_runs,
    "formal_grid_uses_exact_three_required_unique_seeds": (
      set(seeds) == set(DEFAULT_SEEDS) and len(seeds) == len(set(seeds)) == 3
      if formal_full_grid
      else bool(seeds) and len(seeds) == len(set(seeds))
    ),
    "no_diagnostics_profile_attached": diagnostics_profile_count == 0,
    "guidance_runtime_observed_for_every_run": runtime_observation_missing_run_count == 0,
    "production_acceleration_diagnostics_observed_for_every_run": (
      runtime_diagnostic_missing_run_count == 0
    ),
    "resolved_runtime_matches_candidate_contract": (
      resolved_runtime_mismatch_run_count == 0
    ),
    "capture_component_zero_within_1e_12_g": max_capture_g <= 1.0e-12,
    "postclamp_command_not_above_35g": max_postclamp_g <= 35.0 + 1.0e-9,
    "achieved_lateral_acceleration_not_above_35g": max_g <= 35.0 + 1.0e-9,
    "mirror_entry_classification_consistent": mirror_classification_consistent,
    "mirror_nearest_distance_within_1e_3_m": max_mirror_m <= 1.0e-3,
    "seed_nearest_distance_spread_within_1e_3_m": max_seed_spread_m <= 1.0e-3,
    "all_old_anchor_cells_compared_when_full_grid": (
      len(old_rows) == expected_old_count
      if formal_full_grid
      else True
    ),
  }
  stage4_gates = {
    **data_gates,
    "angle_axis_has_no_robust_miss_to_hit_reversal":
      len(sampled_angular_reversals) == 0,
    "each_angle_has_at_most_one_robust_hit_range_interval":
      len(sampled_range_multi_intervals) == 0,
    "robust_hit_region_has_no_internal_hole":
      int(topology["robust_hit_internal_hole_count"]) == 0,
    "robust_hit_region_has_at_most_one_connected_component":
      int(topology["robust_hit_component_count"]) <= 1,
  }
  stage4_gate_values_passed = all(stage4_gates.values())
  formal_stage4_passed = formal_full_grid and stage4_gate_values_passed
  return {
    "schema_version": SCHEMA_VERSION,
    "status": (
      "continuous_launch_envelope_rebuilt"
      if formal_stage4_passed
      else "continuous_launch_envelope_rebuild_failed"
      if formal_full_grid
      else "custom_guidance_envelope_smoke_completed"
    ),
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "R_fuze_m": R_FUZE_M,
    "production_candidate_tuning": dict(PRODUCTION_CANDIDATE_TUNING),
    "diagnostics_mechanism_profile": None,
    "target_motion": "truth constant velocity at 250 m/s",
    "runtime": {
      "ef_py_artifact": str(Path(probe.ef_py.__file__).resolve()),
      "database_path": str(Path(database_path).resolve()),
    },
    "sampling": {
      "run_scope": "formal_full_grid" if formal_full_grid else "custom_smoke_grid",
      "main_ranges_km": list(ranges_km),
      "main_angles_deg": list(angles_deg),
      "main_range_step_km": MAIN_RANGE_STEP_KM,
      "main_angle_step_deg": MAIN_ANGLE_STEP_DEG,
      "seeds": list(seeds),
      "angle_zero_signed_run_policy": "run once",
      "nonzero_angle_signed_run_policy": "run both plus and minus bearings",
      "refinement_enabled": bool(enable_refinement),
      "refinement_range_step_km": REFINEMENT_RANGE_STEP_KM,
      "refinement_angle_step_deg": REFINEMENT_ANGLE_STEP_DEG,
      "refinement_selection": (
        "main-grid 4-neighbor robust-state change edge, or any run with "
        "abs(rho_fuze - 1) <= 0.25"
      ),
      "postprocessing_smoothing": False,
    },
    "classification_policy": {
      "robust_hit": "max rho_fuze across seeds and signed bearings <= 1",
      "robust_miss": "min rho_fuze across seeds and signed bearings > 1",
      "mixed": "neither robust_hit nor robust_miss",
      "N": "robust_hit cell whose existing 8-neighbors are all robust_hit",
      "O": "robust_miss cell whose existing 8-neighbors are all robust_miss",
      "M": "all other main-grid cells",
      "refinement_cells_reclassified": False,
    },
    "counts": {
      "main_cell_count": len(main_cells),
      "main_run_count": len(main_runs),
      "expected_main_run_count": expected_main_runs,
      "state_change_edge_count": len(state_change_edges),
      "refinement_cell_count": len(refinement_cells),
      "refinement_run_count": len(refinement_runs),
      "expected_refinement_run_count": expected_refinement_runs,
      "main_robust_state_counts": dict(
        sorted(Counter(str(row["robust_state"]) for row in main_cells).items())
      ),
      "main_reclassified_launch_class_counts": dict(
        sorted(
          Counter(
            str(row["reclassified_launch_class"]) for row in main_cells
          ).items()
        )
      ),
      "old_label_transition_counts": dict(
        sorted(Counter(str(row["transition"]) for row in old_rows).items())
      ),
    },
    "audit": {
      "max_mirror_abs_difference_m": max_mirror_m,
      "max_seed_spread_m": max_seed_spread_m,
      "mirror_entry_classification_consistent": mirror_classification_consistent,
      "max_capture_component_g": max_capture_g,
      "max_preclamp_command_g": max_preclamp_g,
      "max_postclamp_command_g": max_postclamp_g,
      "max_guidance_saturation_fraction": max_saturation_fraction,
      "max_achieved_lateral_g": max_g,
      "diagnostics_profile_attached_run_count": diagnostics_profile_count,
      "runtime_observation_missing_run_count": runtime_observation_missing_run_count,
      "runtime_diagnostic_missing_run_count": runtime_diagnostic_missing_run_count,
      "resolved_runtime_mismatch_run_count": resolved_runtime_mismatch_run_count,
      "data_integrity_gates": data_gates,
      "data_integrity_passed": all(data_gates.values()),
      "stage4_gates": stage4_gates,
      "stage4_gate_values_passed": stage4_gate_values_passed,
      "formal_full_grid": formal_full_grid,
      "stage4_passed": formal_stage4_passed,
    },
    "topology_audit": topology,
    "state_change_edges": state_change_edges,
    "main_cells": main_cells,
    "refinement_cells": refinement_cells,
    "theta_fuze_by_range": theta_rows,
    "robust_hit_range_boundaries_by_angle": range_rows,
    "old_label_differences": old_rows,
    "runs": all_runs,
    "limitations": [
      "This is a deterministic engineering CV envelope, not real AIM-120 engagement authority.",
      (
        "The N/M/O labels are rebuilt from the selected simulation mechanisms "
        "and are not real-world Pk classes."
      ),
      "Refinement is data-selected after the coarse grid; unsampled fine cells remain unknown.",
      "APN gain remains frozen at 0.5 although the target has zero truth acceleration.",
    ],
  }


def render_chinese_conclusion(report: dict[str, Any]) -> str:
  counts = dict(report["counts"])
  audit = dict(report["audit"])
  topology = dict(report["topology_audit"])
  sampled_topology = dict(topology["refinement_aware_sampled_audit"])
  transitions = dict(counts["old_label_transition_counts"])
  theta_rows = [
    row
    for row in report["theta_fuze_by_range"]
    if float(row["range_km"]).is_integer()
  ]
  range_rows = [
    row
    for row in report["robust_hit_range_boundaries_by_angle"]
    if math.isclose(float(row["offset_deg"]) % 5.0, 0.0, abs_tol=1.0e-9)
  ]
  lines = [
    "# 第四阶段：连续发射窗口重建结论",
    "",
    "本阶段使用生产候选 tuning，未附加 diagnostics mechanism profile。",
    "候选为世界系 LOS-history PN、世界系 CV tracker、capture guidance 关闭；",
    "`N=4`、`35 g`、`APN=0.5` 保持冻结。",
    "",
    "## 采样与分类",
    "",
    f"- 主网格：`{counts['main_cell_count']}` 个 unsigned cell，"
    f"`{counts['main_run_count']}` 次 signed/seed run。",
    f"- refinement：`{counts['refinement_cell_count']}` 个 cell，"
    f"`{counts['refinement_run_count']}` 次 run；状态变化边 "
    f"`{counts['state_change_edge_count']}` 条。",
    f"- robust 状态：`{counts['main_robust_state_counts']}`。",
    f"- 新 N/M/O：`{counts['main_reclassified_launch_class_counts']}`。",
    "- N/O 采用 8 邻域内缩定义，边界、mixed 和异状态邻接统一归入 M。",
    "",
    "## theta_fuze(range)",
    "",
    "| range km | 最大 robust-hit angle | 首个 robust-miss angle | 状态 |",
    "|---:|---:|---:|---|",
  ]
  for row in theta_rows:
    max_hit = row["theta_fuze_robust_hit_max_deg"]
    first_miss = row["first_robust_miss_angle_deg"]
    lines.append(
      f"| {float(row['range_km']):g} | "
      f"{('n/a' if max_hit is None else f'{float(max_hit):g}')} | "
      f"{('n/a' if first_miss is None else f'{float(first_miss):g}')} | "
      f"{row['boundary_status']} |"
    )
  lines.extend(
    [
      "",
      "## 固定 angle 的 minimum/maximum range 边界",
      "",
      "| angle deg | min robust-hit km | max robust-hit km | hit interval count |",
      "|---:|---:|---:|---:|",
    ]
  )
  for row in range_rows:
    minimum = row["minimum_robust_hit_range_km"]
    maximum = row["maximum_robust_hit_range_km"]
    lines.append(
      f"| {float(row['offset_deg']):g} | "
      f"{('n/a' if minimum is None else f'{float(minimum):g}')} | "
      f"{('n/a' if maximum is None else f'{float(maximum):g}')} | "
      f"{int(row['robust_hit_interval_count'])} |"
    )
  lines.extend(
    [
      "",
      "range 方向允许 minimum-range miss -> hit -> maximum-range miss；",
      "只有 robust-hit 分裂成两个以上区间才登记为多岛。",
      "",
      "## 拓扑与不变量审计",
      "",
      f"- 主网格固定 range 的 angle miss->hit 反转："
      f"`{topology['angular_miss_to_hit_reversal_count']}`。",
      f"- 主网格固定 angle 的多 robust-hit 区间："
      f"`{topology['range_multi_interval_violation_count']}`。",
      f"- 加入 refinement 后的 sampled angle 反转 / range 多区间："
      f"`{sampled_topology['angular_miss_to_hit_reversal_count']}` / "
      f"`{sampled_topology['range_multi_interval_violation_count']}`。",
      f"- robust-hit 连通分量 / 内部 holes："
      f"`{topology['robust_hit_component_count']}` / "
      f"`{topology['robust_hit_internal_hole_count']}`。",
      f"- robust-miss 连通分量 / 内部 holes："
      f"`{topology['robust_miss_component_count']}` / "
      f"`{topology['robust_miss_internal_hole_count']}`。",
      f"- 全域 robust hit：`{topology['all_main_cells_robust_hit']}`；"
      f"全域 robust miss：`{topology['all_main_cells_robust_miss']}`。",
      "",
      "工具不会对非单调、多岛、hole 或全域命中做平滑或后处理掩盖。",
      "",
      "## 旧标签差异与运行约束",
      "",
      f"- 旧->新标签计数：`{transitions}`。",
      f"- 最大左右镜像最近距差：`{audit['max_mirror_abs_difference_m']:.9g} m`。",
      f"- 左右镜像 hit/miss 分类一致："
      f"`{audit['mirror_entry_classification_consistent']}`。",
      f"- 最大 seed spread：`{audit['max_seed_spread_m']:.9g} m`。",
      f"- 最大 capture component：`{audit['max_capture_component_g']:.9g} g`。",
      f"- 最大 preclamp command：`{audit['max_preclamp_command_g']:.9g} g`。",
      f"- 最大 postclamp command：`{audit['max_postclamp_command_g']:.9g} g`。",
      f"- 单案最大饱和采样比例："
      f"`{audit['max_guidance_saturation_fraction']:.9g}`。",
      f"- 最大 achieved lateral acceleration："
      f"`{audit['max_achieved_lateral_g']:.9g} g`。",
      f"- diagnostics profile attached run："
      f"`{audit['diagnostics_profile_attached_run_count']}`。",
      f"- runtime observation / acceleration diagnostics missing run："
      f"`{audit['runtime_observation_missing_run_count']}` / "
      f"`{audit['runtime_diagnostic_missing_run_count']}`。",
      f"- resolved runtime contract mismatch run："
      f"`{audit['resolved_runtime_mismatch_run_count']}`。",
      f"- data integrity：`{'PASS' if audit['data_integrity_passed'] else 'FAIL'}`。",
      f"- stage-4 shape gate：`{'PASS' if audit['stage4_passed'] else 'FAIL'}`。",
      "",
      "该结果只说明当前仿真机制下的工程窗口；不构成真实武器射程、Pk "
      "或交战规则权威。",
      "",
    ]
  )
  return "\n".join(lines)


def write_bundle(
  report: dict[str, Any], *, output_dir: Path, stem: str
) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "report_json": output_dir / f"{stem}.json",
    "runs_csv": output_dir / f"{stem}_runs.csv",
    "cells_csv": output_dir / f"{stem}_cells.csv",
    "theta_fuze_csv": output_dir / f"{stem}_theta_fuze.csv",
    "range_boundaries_csv": output_dir / f"{stem}_range_boundaries.csv",
    "old_label_differences_csv": output_dir / f"{stem}_old_label_differences.csv",
    "conclusions_zh_md": output_dir / f"{stem}_conclusions.zh.md",
    "manifest_json": output_dir / f"{stem}_manifest.json",
  }
  report["artifacts"] = {
    key: _artifact_relpath(path) for key, path in paths.items()
  }
  _write_csv(paths["runs_csv"], list(report["runs"]))
  _write_csv(
    paths["cells_csv"],
    [*list(report["main_cells"]), *list(report["refinement_cells"])],
  )
  _write_csv(paths["theta_fuze_csv"], list(report["theta_fuze_by_range"]))
  _write_csv(
    paths["range_boundaries_csv"],
    list(report["robust_hit_range_boundaries_by_angle"]),
  )
  _write_csv(
    paths["old_label_differences_csv"], list(report["old_label_differences"])
  )
  paths["conclusions_zh_md"].write_text(
    render_chinese_conclusion(report), encoding="utf-8"
  )
  paths["report_json"].write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
  )

  ef_py_path = Path(probe.ef_py.__file__).resolve()
  source_path = Path(__file__).resolve()
  database_path = Path(str(report["runtime"]["database_path"])).resolve()
  aim120_path = database_path / "weapons/air_to_air/aim_120c.json"
  hashed_artifacts = {
    key: {
      "path": _artifact_relpath(path),
      "sha256": _sha256(path),
      "bytes": path.stat().st_size,
    }
    for key, path in paths.items()
    if key != "manifest_json" and path.exists()
  }
  manifest = {
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "generated_at_utc": report["generated_at_utc"],
    "report_schema_version": report["schema_version"],
    "tool": {
      "path": _artifact_relpath(source_path),
      "sha256": _sha256(source_path),
    },
    "git": {
      "head": _git_value("rev-parse", "HEAD"),
      "branch": _git_value("branch", "--show-current"),
      "worktree_porcelain": _git_value("status", "--short"),
    },
    "runtime": {
      "ef_py_path": str(ef_py_path),
      "ef_py_sha256": _sha256(ef_py_path),
      "database_path": str(database_path),
      "aim120_definition_path": _artifact_relpath(aim120_path),
      "aim120_definition_sha256": _sha256(aim120_path),
    },
    "run_contract": {
      "production_candidate_tuning": dict(PRODUCTION_CANDIDATE_TUNING),
      "diagnostics_mechanism_profile": None,
      "target_motion": report["target_motion"],
      "sampling": dict(report["sampling"]),
      "R_fuze_m": report["R_fuze_m"],
      "postprocessing_smoothing": False,
    },
    "counts": dict(report["counts"]),
    "audit": dict(report["audit"]),
    "artifacts": hashed_artifacts,
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "real_weapon_or_target_authority": False,
      "real_world_pk": False,
      "interpretation": "engineering CV launch-envelope evidence only",
    },
  }
  paths["manifest_json"].write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
  )
  for path in paths.values():
    path.chmod(0o644)
  return {key: str(path) for key, path in paths.items()}


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


def _parse_axis(values: list[float], default: tuple[float, ...]) -> tuple[float, ...]:
  return tuple(sorted(set(float(value) for value in values))) if values else default


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--database", type=Path, default=probe.DEFAULT_DATABASE_PATH)
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--stem", default=DEFAULT_STEM)
  parser.add_argument("--seed", type=int, action="append", default=[])
  parser.add_argument("--range-km", type=float, action="append", default=[])
  parser.add_argument("--angle-deg", type=float, action="append", default=[])
  parser.add_argument("--skip-refinement", action="store_true")
  parser.add_argument(
    "--strict",
    action="store_true",
    help="Return non-zero when the measured stage-4 topology gate fails.",
  )
  return parser


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  ranges_km = _parse_axis(list(args.range_km), MAIN_RANGES_KM)
  angles_deg = _parse_axis(list(args.angle_deg), MAIN_ANGLES_DEG)
  seeds = tuple(int(value) for value in args.seed) if args.seed else DEFAULT_SEEDS
  if not ranges_km or not all(
    MAIN_RANGES_KM[0] <= value <= MAIN_RANGES_KM[-1] for value in ranges_km
  ):
    raise ValueError("range-km values must be within [4, 16]")
  if not angles_deg or not all(0.0 <= value <= 90.0 for value in angles_deg):
    raise ValueError("angle-deg values must be within [0, 90]")
  probe.ef_py.set_log_level("warn")
  with _native_stdout_to_stderr():
    report = build_report(
      database_path=Path(args.database),
      ranges_km=ranges_km,
      angles_deg=angles_deg,
      seeds=seeds,
      enable_refinement=not bool(args.skip_refinement),
    )
  artifacts = write_bundle(
    report, output_dir=Path(args.output_dir), stem=str(args.stem)
  )
  print(
    json.dumps(
      {
        "status": report["status"],
        "data_integrity_passed": report["audit"]["data_integrity_passed"],
        "stage4_passed": report["audit"]["stage4_passed"],
        "counts": report["counts"],
        "topology_audit": report["topology_audit"],
        "artifacts": artifacts,
      },
      ensure_ascii=False,
    )
  )
  return 1 if bool(args.strict) and not report["audit"]["stage4_passed"] else 0


if __name__ == "__main__":
  raise SystemExit(main())
