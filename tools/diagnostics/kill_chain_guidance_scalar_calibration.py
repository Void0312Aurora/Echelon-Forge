#!/usr/bin/env python3
"""Conservatively calibrate the remaining identifiable guidance scalar.

Stages 1--4 selected the guidance mechanisms and rebuilt the CV launch
envelope.  Under that contract only ``nav_gain`` remains identifiable in the
constant-velocity experiment.  This tool therefore performs a one-factor-at-a-
time sweep of nav gain while keeping capture disabled, APN frozen, and the
stage-2 tracker gains frozen.

Stage-4 N and O cells are hard constraints.  M cells and the independent
half-step holdout are observations only.  No candidate is selected because it
expands an unlabeled sampled boundary: theta and range-contour displacement are
explicit regression gates.  A non-baseline value must pass every invariant and
materially improve either N-cell rho or the saturation-fraction P95.  Otherwise
the result is to retain N=4.
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
from tools.diagnostics import kill_chain_guidance_envelope_rebuild as envelope  # noqa: E402


SCHEMA_VERSION = "a2.kill_chain_guidance_scalar_calibration.v1"
MANIFEST_SCHEMA_VERSION = "a2.kill_chain_guidance_scalar_calibration_manifest.v1"
DEFAULT_STAGE4_REPORT = (
  REPO_ROOT
  / "docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/"
  "kill_chain_guidance_envelope_rebuild_20260715/"
  "kill_chain_guidance_envelope_rebuild_20260715.json"
)
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/"
  "kill_chain_guidance_scalar_calibration_20260715"
)
DEFAULT_STEM = "kill_chain_guidance_scalar_calibration_20260715"
DEFAULT_NAV_GAINS = (3.5, 3.75, 4.0, 4.25, 4.5)
BASELINE_NAV_GAIN = 4.0
DEFAULT_SEEDS = envelope.DEFAULT_SEEDS
R_FUZE_M = envelope.R_FUZE_M

MIRROR_TOLERANCE_M = 1.0e-3
SEED_SPREAD_TOLERANCE_M = 1.0e-3
CAPTURE_TOLERANCE_G = 1.0e-12
MAX_LATERAL_G = 35.0
G_TOLERANCE = 1.0e-9

# A non-baseline candidate must be materially better and must remain within all
# of these regression allowances.  M cells never participate in these gates.
N_RHO_MAX_REGRESSION_ALLOWANCE = 0.05
N_RHO_MEAN_REGRESSION_ALLOWANCE = 0.01
SATURATION_REGRESSION_ALLOWANCE = 0.02
MATERIAL_N_RHO_MEAN_IMPROVEMENT = 0.05
MATERIAL_SATURATION_IMPROVEMENT = 0.05
THETA_CONTOUR_DISPLACEMENT_LIMIT_DEG = 2.5
RANGE_CONTOUR_DISPLACEMENT_LIMIT_KM = 0.5


def _finite(value: Any) -> float | None:
  try:
    parsed = float(value)
  except Exception:
    return None
  return parsed if math.isfinite(parsed) else None


def _token(value: float) -> str:
  return f"{float(value):g}".replace("-", "m").replace(".", "p")


def _signed_bearings(angle_deg: float) -> tuple[float, ...]:
  return (0.0,) if math.isclose(angle_deg, 0.0, abs_tol=1.0e-12) else (-angle_deg, angle_deg)


def _case_id(
  *, nav_gain: float, grid_tier: str, range_km: float, bearing_deg: float, seed: int
) -> str:
  sign = "p" if bearing_deg >= 0.0 else "m"
  return (
    f"guidance_scalar_n{_token(nav_gain)}_{grid_tier}_"
    f"{_token(range_km)}km_{sign}{_token(abs(bearing_deg))}deg_s{int(seed)}"
  )


def _miss_distance(result: dict[str, Any]) -> float:
  for key in ("nearest_miss_distance_m", "truth_min_distance_m"):
    value = _finite(result.get(key))
    if value is not None:
      return value
  raise RuntimeError(
    f"guidance case {result.get('case_id', '<unknown>')} has no finite miss distance"
  )


def _candidate_tuning(nav_gain: float) -> dict[str, float | int]:
  tuning = dict(envelope.PRODUCTION_CANDIDATE_TUNING)
  tuning["nav_gain"] = float(nav_gain)
  return tuning


def _resolved_runtime_mismatches(
  result: dict[str, Any], expected_tuning: dict[str, float | int]
) -> list[str]:
  runtime = dict(result.get("resolved_guidance_runtime", {}) or {})
  expected = {
    "nav_gain": expected_tuning["nav_gain"],
    "pn_los_rate_source": expected_tuning["pn_los_rate_source"],
    "target_kinematics_estimator": expected_tuning["target_kinematics_estimator"],
    "capture_guidance_mode": expected_tuning["capture_guidance_mode"],
    "target_tracker_alpha": expected_tuning["target_tracker_alpha"],
    "target_tracker_beta": expected_tuning["target_tracker_beta"],
    "apn_target_accel_gain": expected_tuning["apn_target_accel_gain"],
    "guidance_max_lateral_g": expected_tuning["max_lateral_g"],
  }
  integer_fields = {
    "pn_los_rate_source",
    "target_kinematics_estimator",
    "capture_guidance_mode",
  }
  mismatches: list[str] = []
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
  nav_gain: float,
  grid_tier: str,
  range_km: float,
  angle_deg: float,
  bearing_deg: float,
  seed: int,
  stage4_class: str | None,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> dict[str, Any]:
  case_id = _case_id(
    nav_gain=nav_gain,
    grid_tier=grid_tier,
    range_km=range_km,
    bearing_deg=bearing_deg,
    seed=seed,
  )
  print(f"[guidance-scalar:{_token(nav_gain)}:{grid_tier}] {case_id}", file=sys.stderr)
  tuning = _candidate_tuning(nav_gain)
  result = runner(
    database_path=database_path,
    case_id=case_id,
    range_m=float(range_km) * 1000.0,
    bearing_deg=float(bearing_deg),
    seed=int(seed),
    guidance_tuning_overrides=tuning,
  )
  distance_m = _miss_distance(result)
  runtime_mismatches = _resolved_runtime_mismatches(result, tuning)
  return {
    "candidate_id": f"nav_gain_{_token(nav_gain)}",
    "nav_gain": float(nav_gain),
    "grid_tier": grid_tier,
    "case_id": case_id,
    "range_km": float(range_km),
    "range_m": float(range_km) * 1000.0,
    "offset_deg": float(angle_deg),
    "signed_bearing_deg": float(bearing_deg),
    "seed": int(seed),
    "stage4_launch_class": stage4_class,
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
    "guidance_saturation_fraction": float(
      result.get("guidance_saturation_fraction", 0.0) or 0.0
    ),
    "resolved_guidance_runtime": dict(result.get("resolved_guidance_runtime", {}) or {}),
    "resolved_runtime_contract_matches": not runtime_mismatches,
    "resolved_runtime_contract_mismatches": runtime_mismatches,
    "diagnostics_profile_attached": result.get("guidance_mechanism_profile") is not None,
  }


def run_grid(
  *,
  database_path: Path,
  nav_gain: float,
  grid_tier: str,
  coordinates: Iterable[tuple[float, float]],
  seeds: tuple[int, ...],
  stage4_classes: dict[tuple[float, float], str],
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for range_km, angle_deg in sorted(set(coordinates)):
    stage4_class = stage4_classes.get((float(range_km), float(angle_deg)))
    for seed in seeds:
      for bearing_deg in _signed_bearings(float(angle_deg)):
        rows.append(
          _run_one(
            database_path=database_path,
            nav_gain=nav_gain,
            grid_tier=grid_tier,
            range_km=float(range_km),
            angle_deg=float(angle_deg),
            bearing_deg=float(bearing_deg),
            seed=int(seed),
            stage4_class=stage4_class,
            runner=runner,
          )
        )
  return rows


def _aggregate_candidate_cells(
  rows: list[dict[str, Any]], stage4_classes: dict[tuple[float, float], str]
) -> list[dict[str, Any]]:
  cells = envelope.aggregate_cells(rows)
  for cell in cells:
    coordinate = (float(cell["range_km"]), float(cell["offset_deg"]))
    cell["nav_gain"] = float(rows[0]["nav_gain"]) if rows else None
    cell["candidate_id"] = str(rows[0]["candidate_id"]) if rows else None
    cell["stage4_launch_class"] = stage4_classes.get(coordinate)
  return cells


def _adjacent_coordinates(
  coordinate: tuple[float, float],
  coordinates: set[tuple[float, float]],
  range_values: tuple[float, ...],
  angle_values: tuple[float, ...],
) -> list[tuple[float, float]]:
  range_km, angle_deg = coordinate
  range_index = range_values.index(range_km)
  angle_index = angle_values.index(angle_deg)
  output: list[tuple[float, float]] = []
  for next_range_index, next_angle_index in (
    (range_index - 1, angle_index),
    (range_index + 1, angle_index),
    (range_index, angle_index - 1),
    (range_index, angle_index + 1),
  ):
    if not (0 <= next_range_index < len(range_values)):
      continue
    if not (0 <= next_angle_index < len(angle_values)):
      continue
    candidate = (range_values[next_range_index], angle_values[next_angle_index])
    if candidate in coordinates:
      output.append(candidate)
  return output


def _components(
  coordinates: set[tuple[float, float]],
  selected: set[tuple[float, float]],
  range_values: tuple[float, ...],
  angle_values: tuple[float, ...],
) -> list[list[tuple[float, float]]]:
  remaining = set(selected)
  output: list[list[tuple[float, float]]] = []
  while remaining:
    start = min(remaining)
    queue: deque[tuple[float, float]] = deque([start])
    remaining.remove(start)
    component: list[tuple[float, float]] = []
    while queue:
      current = queue.popleft()
      component.append(current)
      for neighbor in _adjacent_coordinates(
        current, coordinates, range_values, angle_values
      ):
        if neighbor in remaining:
          remaining.remove(neighbor)
          queue.append(neighbor)
    output.append(sorted(component))
  return sorted(output, key=lambda value: (-len(value), value))


def topology_audit(cells: list[dict[str, Any]]) -> dict[str, Any]:
  indexed = {
    (float(row["range_km"]), float(row["offset_deg"])): row for row in cells
  }
  coordinates = set(indexed)
  range_values = tuple(sorted({item[0] for item in coordinates}))
  angle_values = tuple(sorted({item[1] for item in coordinates}))
  expected_coordinates = {
    (range_km, angle_deg)
    for range_km in range_values
    for angle_deg in angle_values
  }
  rectangular_grid_complete = coordinates == expected_coordinates
  angular_reversals: list[dict[str, Any]] = []
  for range_km in range_values:
    prior_miss: float | None = None
    for angle_deg in angle_values:
      state = str(indexed[(range_km, angle_deg)]["robust_state"])
      if state == envelope.ROBUST_MISS:
        prior_miss = angle_deg
      elif state == envelope.ROBUST_HIT and prior_miss is not None:
        angular_reversals.append(
          {
            "range_km": range_km,
            "earlier_robust_miss_angle_deg": prior_miss,
            "later_robust_hit_angle_deg": angle_deg,
          }
        )

  range_intervals: list[dict[str, Any]] = []
  range_multi_interval_violations: list[dict[str, Any]] = []
  for angle_deg in angle_values:
    blocks: list[list[float]] = []
    active: list[float] = []
    for range_km in range_values:
      state = str(indexed[(range_km, angle_deg)]["robust_state"])
      if state == envelope.ROBUST_HIT:
        active.append(range_km)
      elif active:
        blocks.append(active)
        active = []
    if active:
      blocks.append(active)
    row = {
      "offset_deg": angle_deg,
      "robust_hit_interval_count": len(blocks),
      "robust_hit_intervals_km": [
        {"minimum_range_km": min(block), "maximum_range_km": max(block)}
        for block in blocks
      ],
    }
    range_intervals.append(row)
    if len(blocks) > 1:
      range_multi_interval_violations.append(row)

  hit_coordinates = {
    coordinate
    for coordinate, row in indexed.items()
    if row["robust_state"] == envelope.ROBUST_HIT
  }
  hit_components = _components(
    coordinates, hit_coordinates, range_values, angle_values
  )
  complement_components = _components(
    coordinates, coordinates - hit_coordinates, range_values, angle_values
  )
  holes: list[list[tuple[float, float]]] = []
  for component in complement_components:
    touches_boundary = any(
      range_km in {range_values[0], range_values[-1]}
      or angle_deg in {angle_values[0], angle_values[-1]}
      for range_km, angle_deg in component
    )
    if not touches_boundary:
      holes.append(component)
  passed = (
    rectangular_grid_complete
    and not angular_reversals
    and not range_multi_interval_violations
    and len(hit_components) <= 1
    and not holes
  )
  return {
    "rectangular_grid_complete": rectangular_grid_complete,
    "angular_miss_to_hit_reversal_count": len(angular_reversals),
    "angular_miss_to_hit_reversals": angular_reversals,
    "range_hit_interval_rows": range_intervals,
    "range_multi_interval_violation_count": len(range_multi_interval_violations),
    "range_multi_interval_violations": range_multi_interval_violations,
    "robust_hit_component_count": len(hit_components),
    "robust_hit_component_sizes": [len(value) for value in hit_components],
    "robust_hit_internal_hole_count": len(holes),
    "robust_hit_internal_holes": holes,
    "single_hit_band_passed": passed,
  }


def _percentile(values: Iterable[float], quantile: float) -> float:
  ordered = sorted(float(value) for value in values)
  if not ordered:
    return 0.0
  if len(ordered) == 1:
    return ordered[0]
  position = min(max(float(quantile), 0.0), 1.0) * (len(ordered) - 1)
  lower = math.floor(position)
  upper = math.ceil(position)
  if lower == upper:
    return ordered[lower]
  fraction = position - lower
  return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def contour_summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
  theta_rows = envelope.theta_fuze_rows(cells)
  range_rows = envelope.range_boundary_rows(cells)
  return {
    "theta_fuze_robust_hit_max_deg_by_range": {
      str(float(row["range_km"])): row["theta_fuze_robust_hit_max_deg"]
      for row in theta_rows
    },
    "minimum_robust_hit_range_km_by_angle": {
      str(float(row["offset_deg"])): row["minimum_robust_hit_range_km"]
      for row in range_rows
    },
    "maximum_robust_hit_range_km_by_angle": {
      str(float(row["offset_deg"])): row["maximum_robust_hit_range_km"]
      for row in range_rows
    },
  }


def _boundary_displacement(
  candidate: dict[str, Any], baseline: dict[str, Any], key: str
) -> float | None:
  candidate_values = dict(candidate.get(key, {}) or {})
  baseline_values = dict(baseline.get(key, {}) or {})
  displacements: list[float] = []
  for coordinate in sorted(set(candidate_values) | set(baseline_values)):
    candidate_value = candidate_values.get(coordinate)
    baseline_value = baseline_values.get(coordinate)
    if candidate_value is None and baseline_value is None:
      displacements.append(0.0)
    elif candidate_value is None or baseline_value is None:
      return None
    else:
      displacements.append(abs(float(candidate_value) - float(baseline_value)))
  return max(displacements, default=0.0)


def _max_boundary_displacement(*values: float | None) -> float | None:
  if any(value is None for value in values):
    return None
  return max((float(value) for value in values if value is not None), default=0.0)


def _expected_run_count(
  coordinates: Iterable[tuple[float, float]], seeds: tuple[int, ...]
) -> int:
  return sum(len(_signed_bearings(angle_deg)) * len(seeds) for _, angle_deg in coordinates)


def _candidate_report(
  *,
  nav_gain: float,
  main_runs: list[dict[str, Any]],
  holdout_runs: list[dict[str, Any]],
  main_coordinates: tuple[tuple[float, float], ...],
  holdout_coordinates: tuple[tuple[float, float], ...],
  seeds: tuple[int, ...],
  stage4_classes: dict[tuple[float, float], str],
) -> dict[str, Any]:
  main_cells = _aggregate_candidate_cells(main_runs, stage4_classes)
  holdout_cells = _aggregate_candidate_cells(holdout_runs, {}) if holdout_runs else []
  main_topology = topology_audit(main_cells)
  holdout_topology = topology_audit(holdout_cells) if holdout_cells else {
    "single_hit_band_passed": True,
    "not_run": True,
  }
  all_runs = [*main_runs, *holdout_runs]
  all_cells = [*main_cells, *holdout_cells]
  n_cells = [row for row in main_cells if row.get("stage4_launch_class") == "N"]
  o_cells = [row for row in main_cells if row.get("stage4_launch_class") == "O"]
  m_cells = [row for row in main_cells if row.get("stage4_launch_class") == "M"]
  n_violations = [row for row in n_cells if row["robust_state"] != envelope.ROBUST_HIT]
  o_violations = [row for row in o_cells if row["robust_state"] != envelope.ROBUST_MISS]
  max_mirror = max(
    (float(row["max_mirror_abs_difference_m"]) for row in all_cells), default=0.0
  )
  max_seed_spread = max(
    (float(row["max_seed_spread_m"]) for row in all_cells), default=0.0
  )
  max_capture = max(
    (float(row["max_capture_component_g"]) for row in all_runs), default=0.0
  )
  max_postclamp = max(
    (float(row["max_postclamp_command_g"]) for row in all_runs), default=0.0
  )
  max_achieved = max(
    (float(row["max_achieved_lateral_g"]) for row in all_runs), default=0.0
  )
  max_saturation = max(
    (float(row["guidance_saturation_fraction"]) for row in all_runs), default=0.0
  )
  saturation_p95 = _percentile(
    (float(row["guidance_saturation_fraction"]) for row in all_runs), 0.95
  )
  expected_main_runs = _expected_run_count(main_coordinates, seeds)
  expected_holdout_runs = _expected_run_count(holdout_coordinates, seeds)
  gates = {
    "main_run_count_complete": len(main_runs) == expected_main_runs,
    "holdout_run_count_complete": len(holdout_runs) == expected_holdout_runs,
    "stage4_N_cells_remain_robust_hit": not n_violations,
    "stage4_O_cells_remain_robust_miss": not o_violations,
    "no_diagnostics_profile_attached": not any(
      bool(row["diagnostics_profile_attached"]) for row in all_runs
    ),
    "guidance_runtime_observed_for_every_run": all(
      int(row["guidance_runtime_observation_count"]) > 0 for row in all_runs
    ),
    "production_acceleration_diagnostics_observed_for_every_run": all(
      int(row["guidance_runtime_missing_acceleration_diagnostics_count"]) == 0
      for row in all_runs
    ),
    "resolved_runtime_matches_candidate_contract": all(
      bool(row["resolved_runtime_contract_matches"]) for row in all_runs
    ),
    "capture_component_zero_within_1e_12_g": max_capture <= CAPTURE_TOLERANCE_G,
    "postclamp_command_not_above_35g": max_postclamp <= MAX_LATERAL_G + G_TOLERANCE,
    "achieved_lateral_acceleration_not_above_35g": max_achieved <= MAX_LATERAL_G + G_TOLERANCE,
    "mirror_nearest_distance_within_1e_3_m": max_mirror <= MIRROR_TOLERANCE_M,
    "seed_nearest_distance_spread_within_1e_3_m": max_seed_spread <= SEED_SPREAD_TOLERANCE_M,
    "main_grid_single_hit_band": bool(main_topology["single_hit_band_passed"]),
    "holdout_grid_single_hit_band": bool(holdout_topology["single_hit_band_passed"]),
  }
  m_transitions = Counter(
    f"M->{row['robust_state']}" for row in m_cells
  )
  holdout_states = Counter(str(row["robust_state"]) for row in holdout_cells)
  return {
    "candidate_id": f"nav_gain_{_token(nav_gain)}",
    "nav_gain": float(nav_gain),
    "evaluated_scalar": "nav_gain",
    "hard_gate_passed": all(gates.values()),
    "gates": gates,
    "audit": {
      "max_mirror_abs_difference_m": max_mirror,
      "max_seed_spread_m": max_seed_spread,
      "max_capture_component_g": max_capture,
      "max_postclamp_command_g": max_postclamp,
      "max_achieved_lateral_g": max_achieved,
      "max_guidance_saturation_fraction": max_saturation,
      "N_violation_count": len(n_violations),
      "O_violation_count": len(o_violations),
      "N_violations": [
        {"range_km": row["range_km"], "offset_deg": row["offset_deg"], "rho_max": row["rho_max"]}
        for row in n_violations
      ],
      "O_violations": [
        {"range_km": row["range_km"], "offset_deg": row["offset_deg"], "rho_min": row["rho_min"]}
        for row in o_violations
      ],
    },
    "metrics": {
      "N_cell_count": len(n_cells),
      "O_cell_count": len(o_cells),
      "M_cell_count": len(m_cells),
      "N_rho_mean": statistics.fmean(float(row["rho_mean"]) for row in n_cells) if n_cells else None,
      "N_rho_max": max((float(row["rho_max"]) for row in n_cells), default=None),
      "O_rho_mean": statistics.fmean(float(row["rho_mean"]) for row in o_cells) if o_cells else None,
      "O_rho_min": min((float(row["rho_min"]) for row in o_cells), default=None),
      "M_observed_transition_counts": dict(sorted(m_transitions.items())),
      "main_robust_state_counts": dict(
        sorted(Counter(str(row["robust_state"]) for row in main_cells).items())
      ),
      "holdout_robust_state_counts": dict(sorted(holdout_states.items())),
      "holdout_robust_hit_count": int(holdout_states[envelope.ROBUST_HIT]),
      "holdout_cell_count": len(holdout_cells),
      "max_guidance_saturation_fraction": max_saturation,
      "guidance_saturation_fraction_p95": saturation_p95,
    },
    "main_topology_audit": main_topology,
    "holdout_topology_audit": holdout_topology,
    "main_contour": contour_summary(main_cells),
    "holdout_contour": contour_summary(holdout_cells) if holdout_cells else {},
    "main_cells": main_cells,
    "holdout_cells": holdout_cells,
    "runs": all_runs,
  }


def _metric(candidate: dict[str, Any], key: str) -> float:
  value = candidate["metrics"].get(key)
  if value is None:
    return 0.0
  return float(value)


def compare_with_baseline(
  candidate: dict[str, Any], baseline: dict[str, Any]
) -> dict[str, Any]:
  nav_gain = float(candidate["nav_gain"])
  if math.isclose(nav_gain, BASELINE_NAV_GAIN, abs_tol=1.0e-12):
    return {
      "candidate_id": candidate["candidate_id"],
      "nav_gain": nav_gain,
      "is_baseline": True,
      "clear_net_benefit": False,
      "regression_guards": {},
      "material_improvements": {},
      "deltas_vs_baseline": {},
      "decision": "reference_baseline",
    }
  n_mean_delta = _metric(candidate, "N_rho_mean") - _metric(baseline, "N_rho_mean")
  n_max_delta = _metric(candidate, "N_rho_max") - _metric(baseline, "N_rho_max")
  o_min_delta = _metric(candidate, "O_rho_min") - _metric(baseline, "O_rho_min")
  holdout_hit_delta = int(
    _metric(candidate, "holdout_robust_hit_count")
    - _metric(baseline, "holdout_robust_hit_count")
  )
  saturation_p95_delta = (
    _metric(candidate, "guidance_saturation_fraction_p95")
    - _metric(baseline, "guidance_saturation_fraction_p95")
  )
  theta_displacement = _max_boundary_displacement(
    _boundary_displacement(
      candidate["main_contour"],
      baseline["main_contour"],
      "theta_fuze_robust_hit_max_deg_by_range",
    ),
    _boundary_displacement(
      candidate["holdout_contour"],
      baseline["holdout_contour"],
      "theta_fuze_robust_hit_max_deg_by_range",
    ),
  )
  minimum_range_displacement = _max_boundary_displacement(
    _boundary_displacement(
      candidate["main_contour"],
      baseline["main_contour"],
      "minimum_robust_hit_range_km_by_angle",
    ),
    _boundary_displacement(
      candidate["holdout_contour"],
      baseline["holdout_contour"],
      "minimum_robust_hit_range_km_by_angle",
    ),
  )
  maximum_range_displacement = _max_boundary_displacement(
    _boundary_displacement(
      candidate["main_contour"],
      baseline["main_contour"],
      "maximum_robust_hit_range_km_by_angle",
    ),
    _boundary_displacement(
      candidate["holdout_contour"],
      baseline["holdout_contour"],
      "maximum_robust_hit_range_km_by_angle",
    ),
  )
  regression_guards = {
    "candidate_passes_all_hard_gates": bool(candidate["hard_gate_passed"]),
    "N_rho_max_not_degraded_more_than_0_05": n_max_delta <= N_RHO_MAX_REGRESSION_ALLOWANCE,
    "N_rho_mean_not_degraded_more_than_0_01": n_mean_delta <= N_RHO_MEAN_REGRESSION_ALLOWANCE,
    "theta_fuze_max_displacement_within_2_5deg": (
      theta_displacement is not None
      and theta_displacement <= THETA_CONTOUR_DISPLACEMENT_LIMIT_DEG
    ),
    "minimum_range_boundary_displacement_within_0_5km": (
      minimum_range_displacement is not None
      and minimum_range_displacement <= RANGE_CONTOUR_DISPLACEMENT_LIMIT_KM
    ),
    "maximum_range_boundary_displacement_within_0_5km": (
      maximum_range_displacement is not None
      and maximum_range_displacement <= RANGE_CONTOUR_DISPLACEMENT_LIMIT_KM
    ),
    "saturation_fraction_p95_not_increased_more_than_0_02": (
      saturation_p95_delta <= SATURATION_REGRESSION_ALLOWANCE
    ),
  }
  material_improvements = {
    "N_rho_mean_improves_by_at_least_0_05": n_mean_delta <= -MATERIAL_N_RHO_MEAN_IMPROVEMENT,
    "saturation_fraction_p95_improves_by_at_least_0_05": (
      saturation_p95_delta <= -MATERIAL_SATURATION_IMPROVEMENT
    ),
  }
  clear_net_benefit = all(regression_guards.values()) and any(material_improvements.values())
  return {
    "candidate_id": candidate["candidate_id"],
    "nav_gain": nav_gain,
    "is_baseline": False,
    "clear_net_benefit": clear_net_benefit,
    "regression_guards": regression_guards,
    "material_improvements": material_improvements,
    "deltas_vs_baseline": {
      "N_rho_mean": n_mean_delta,
      "N_rho_max": n_max_delta,
      "O_rho_min": o_min_delta,
      "holdout_robust_hit_count": holdout_hit_delta,
      "guidance_saturation_fraction_p95": saturation_p95_delta,
      "theta_fuze_max_displacement_deg": theta_displacement,
      "minimum_range_boundary_max_displacement_km": minimum_range_displacement,
      "maximum_range_boundary_max_displacement_km": maximum_range_displacement,
    },
    "decision": "clear_net_benefit" if clear_net_benefit else "reject_or_no_material_gain",
  }


def _selection_key(comparison: dict[str, Any]) -> tuple[float, ...]:
  deltas = comparison["deltas_vs_baseline"]
  return (
    -float(deltas["N_rho_mean"]),
    -float(deltas["guidance_saturation_fraction_p95"]),
    -abs(float(comparison["nav_gain"]) - BASELINE_NAV_GAIN),
  )


def _load_stage4_report(path: Path) -> dict[str, Any]:
  report = json.loads(path.read_text(encoding="utf-8"))
  if report.get("schema_version") != envelope.SCHEMA_VERSION:
    raise ValueError(f"unexpected stage-4 schema: {report.get('schema_version')}")
  if not bool(dict(report.get("audit", {})).get("stage4_passed")):
    raise ValueError("stage-4 report has not passed its formal gate")
  return report


def _stage4_cells(report: dict[str, Any]) -> list[dict[str, Any]]:
  rows = [dict(row) for row in list(report.get("main_cells", []) or [])]
  if not rows:
    raise ValueError("stage-4 report has no main cells")
  for row in rows:
    if row.get("reclassified_launch_class") not in {"N", "M", "O"}:
      raise ValueError("stage-4 cell is missing an N/M/O class")
  return rows


def _half_step_values(values: Iterable[float]) -> tuple[float, ...]:
  ordered = sorted(set(float(value) for value in values))
  return tuple((left + right) / 2.0 for left, right in zip(ordered, ordered[1:]))


def identifiability_table() -> list[dict[str, Any]]:
  return [
    {
      "parameter": "nav_gain",
      "stage5_status": "evaluated_OFAT",
      "reason": "remaining scalar with observable CV trajectory effect",
    },
    {
      "parameter": "capture_guidance_scalars",
      "stage5_status": "excluded",
      "reason": "stage 3 selected capture_guidance_mode=disabled",
    },
    {
      "parameter": "apn_target_accel_gain",
      "stage5_status": "excluded_frozen_at_0.5",
      "reason": "truth target acceleration is zero in the CV experiment",
    },
    {
      "parameter": "target_tracker_alpha_beta",
      "stage5_status": "excluded_frozen_at_0.20_0.02",
      "reason": "estimated and frozen in stage 2; joint retuning would confound mechanisms",
    },
    {
      "parameter": "max_lateral_g",
      "stage5_status": "constraint_frozen_at_35",
      "reason": "safety and runtime constraint, not an objective scalar",
    },
  ]


def build_report(
  *,
  stage4_report: dict[str, Any] | None = None,
  stage4_report_path: Path = DEFAULT_STAGE4_REPORT,
  database_path: Path = probe.DEFAULT_DATABASE_PATH,
  nav_gains: tuple[float, ...] = DEFAULT_NAV_GAINS,
  seeds: tuple[int, ...] = DEFAULT_SEEDS,
  ranges_km: tuple[float, ...] | None = None,
  angles_deg: tuple[float, ...] | None = None,
  enable_holdout: bool = True,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> dict[str, Any]:
  if stage4_report is None:
    stage4_report = _load_stage4_report(Path(stage4_report_path))
  cells = _stage4_cells(stage4_report)
  available_ranges = tuple(sorted({float(row["range_km"]) for row in cells}))
  available_angles = tuple(sorted({float(row["offset_deg"]) for row in cells}))
  selected_ranges = tuple(sorted(set(ranges_km or available_ranges)))
  selected_angles = tuple(sorted(set(angles_deg or available_angles)))
  if not set(selected_ranges).issubset(available_ranges):
    raise ValueError("requested range is absent from the stage-4 main grid")
  if not set(selected_angles).issubset(available_angles):
    raise ValueError("requested angle is absent from the stage-4 main grid")
  selected_cells = [
    row
    for row in cells
    if float(row["range_km"]) in selected_ranges
    and float(row["offset_deg"]) in selected_angles
  ]
  stage4_classes = {
    (float(row["range_km"]), float(row["offset_deg"])): str(
      row["reclassified_launch_class"]
    )
    for row in selected_cells
  }
  main_coordinates = tuple(sorted(stage4_classes))
  holdout_coordinates = (
    tuple(
      (range_km, angle_deg)
      for range_km in _half_step_values(selected_ranges)
      for angle_deg in _half_step_values(selected_angles)
    )
    if enable_holdout
    else ()
  )
  candidate_reports: list[dict[str, Any]] = []
  for nav_gain in sorted(set(float(value) for value in nav_gains)):
    main_runs = run_grid(
      database_path=database_path,
      nav_gain=nav_gain,
      grid_tier="main",
      coordinates=main_coordinates,
      seeds=seeds,
      stage4_classes=stage4_classes,
      runner=runner,
    )
    holdout_runs = run_grid(
      database_path=database_path,
      nav_gain=nav_gain,
      grid_tier="holdout",
      coordinates=holdout_coordinates,
      seeds=seeds,
      stage4_classes={},
      runner=runner,
    )
    candidate_reports.append(
      _candidate_report(
        nav_gain=nav_gain,
        main_runs=main_runs,
        holdout_runs=holdout_runs,
        main_coordinates=main_coordinates,
        holdout_coordinates=holdout_coordinates,
        seeds=seeds,
        stage4_classes=stage4_classes,
      )
    )

  baseline = next(
    (
      row
      for row in candidate_reports
      if math.isclose(float(row["nav_gain"]), BASELINE_NAV_GAIN, abs_tol=1.0e-12)
    ),
    None,
  )
  if baseline is None:
    raise ValueError("nav-gain sweep must include the N=4 baseline")
  comparisons = [compare_with_baseline(row, baseline) for row in candidate_reports]
  beneficial = [row for row in comparisons if bool(row["clear_net_benefit"])]
  selected_comparison = max(beneficial, key=_selection_key) if beneficial else None
  selected_nav_gain = (
    float(selected_comparison["nav_gain"])
    if selected_comparison is not None
    else BASELINE_NAV_GAIN
  )
  selected_candidate = next(
    row
    for row in candidate_reports
    if math.isclose(float(row["nav_gain"]), selected_nav_gain, abs_tol=1.0e-12)
  )
  formal_scope = (
    set(selected_ranges) == set(envelope.MAIN_RANGES_KM)
    and set(selected_angles) == set(envelope.MAIN_ANGLES_DEG)
    and set(float(value) for value in nav_gains) == set(DEFAULT_NAV_GAINS)
    and set(seeds) == set(DEFAULT_SEEDS)
    and len(seeds) == len(set(seeds)) == len(DEFAULT_SEEDS)
    and enable_holdout
    and bool(dict(stage4_report.get("audit", {})).get("stage4_passed"))
  )
  selected_passed = bool(selected_candidate["hard_gate_passed"])
  status = (
    "scalar_calibration_completed_changed_nav_gain"
    if formal_scope and selected_passed and not math.isclose(selected_nav_gain, BASELINE_NAV_GAIN)
    else "scalar_calibration_completed_retained_baseline"
    if formal_scope and selected_passed
    else "scalar_calibration_failed"
    if formal_scope
    else "custom_scalar_calibration_smoke_completed"
  )
  all_runs = [run for row in candidate_reports for run in row["runs"]]
  all_cells = [
    cell
    for row in candidate_reports
    for cell in [*row["main_cells"], *row["holdout_cells"]]
  ]
  return {
    "schema_version": SCHEMA_VERSION,
    "status": status,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "stage4_source": {
      "path": str(Path(stage4_report_path).resolve()),
      "schema_version": stage4_report.get("schema_version"),
      "status": stage4_report.get("status"),
      "stage4_passed": bool(dict(stage4_report.get("audit", {})).get("stage4_passed")),
    },
    "identifiability": identifiability_table(),
    "frozen_production_mechanism_tuning": {
      key: value
      for key, value in envelope.PRODUCTION_CANDIDATE_TUNING.items()
      if key != "nav_gain"
    },
    "evaluated_scalar": {
      "name": "nav_gain",
      "method": "one_factor_at_a_time",
      "baseline": BASELINE_NAV_GAIN,
      "candidates": sorted(set(float(value) for value in nav_gains)),
    },
    "sampling": {
      "ranges_km": list(selected_ranges),
      "angles_deg": list(selected_angles),
      "main_cell_count": len(main_coordinates),
      "holdout_policy": "midpoint between adjacent stage-4 range and angle samples",
      "holdout_enabled": enable_holdout,
      "holdout_ranges_km": list(_half_step_values(selected_ranges)) if enable_holdout else [],
      "holdout_angles_deg": list(_half_step_values(selected_angles)) if enable_holdout else [],
      "holdout_cell_count": len(holdout_coordinates),
      "seeds": list(seeds),
      "signed_bearing_policy": "zero once; nonzero plus and minus",
      "M_policy": "observed and reported, never a binary optimization pressure",
      "holdout_policy_role": "observed and reported, never counted as material benefit",
    },
    "selection_policy": {
      "hard_constraints": "stage-4 N stays robust hit; O stays robust miss",
      "topology": "one connected robust-hit band, no angular reversal, range multi-island, or internal hole",
      "mirror_tolerance_m": MIRROR_TOLERANCE_M,
      "seed_spread_tolerance_m": SEED_SPREAD_TOLERANCE_M,
      "max_lateral_g": MAX_LATERAL_G,
      "regression_allowances": {
        "N_rho_max": N_RHO_MAX_REGRESSION_ALLOWANCE,
        "N_rho_mean": N_RHO_MEAN_REGRESSION_ALLOWANCE,
        "guidance_saturation_fraction_p95": SATURATION_REGRESSION_ALLOWANCE,
        "theta_fuze_max_displacement_deg": THETA_CONTOUR_DISPLACEMENT_LIMIT_DEG,
        "minimum_range_boundary_max_displacement_km": RANGE_CONTOUR_DISPLACEMENT_LIMIT_KM,
        "maximum_range_boundary_max_displacement_km": RANGE_CONTOUR_DISPLACEMENT_LIMIT_KM,
      },
      "material_improvement_thresholds": {
        "N_rho_mean": MATERIAL_N_RHO_MEAN_IMPROVEMENT,
        "guidance_saturation_fraction_p95": MATERIAL_SATURATION_IMPROVEMENT,
      },
      "non_objectives": [
        "holdout robust-hit count",
        "M hit/miss transition",
        "larger O-cell miss distance",
      ],
      "fallback": "retain nav_gain=4 when no non-baseline candidate has clear net benefit",
    },
    "formal_scope": formal_scope,
    "candidate_summaries": [
      {
        key: value
        for key, value in row.items()
        if key not in {"main_cells", "holdout_cells", "runs"}
      }
      for row in candidate_reports
    ],
    "comparisons_vs_baseline": comparisons,
    "selection": {
      "selected_nav_gain": selected_nav_gain,
      "decision": (
        "change_nav_gain_due_to_clear_net_benefit"
        if selected_comparison is not None
        else "retain_nav_gain_4_no_clear_net_benefit"
      ),
      "clear_net_benefit_candidate_ids": [
        str(row["candidate_id"]) for row in beneficial
      ],
      "selected_candidate_hard_gate_passed": selected_passed,
      "scalar_selection_passed": formal_scope and selected_passed,
      "formal_stage5_passed": formal_scope and selected_passed,
      "default_promotion_ready": False,
      "default_promotion_status": "held",
      "default_promotion_hold_reasons": [
        "stage-2 world_cv tracker reports acceleration_world_mps2 fixed at zero",
        "stage-4 and stage-5 calibration authority covers only constant-velocity targets",
        "maneuver-target and APN authority evidence is absent",
      ],
    },
    "release_gate": {
      "scalar_selection_and_default_promotion_are_separate_decisions": True,
      "scalar_selection_passed": formal_scope and selected_passed,
      "selected_nav_gain": selected_nav_gain,
      "default_promotion_ready": False,
      "status": "held_for_maneuver_and_APN_authority",
      "required_next_evidence": [
        "maneuver-target envelope with nonzero truth acceleration",
        "tracker acceleration authority beyond fixed zero",
        "APN gain identifiability and holdout validation",
      ],
    },
    "runtime": {
      "ef_py_artifact": str(Path(probe.ef_py.__file__).resolve()),
      "database_path": str(Path(database_path).resolve()),
    },
    "runs": all_runs,
    "cells": all_cells,
    "limitations": [
      "The calibration target is the deterministic engineering CV envelope, not real missile performance.",
      "M cells and half-step holdout cells have no real-world truth label.",
      "APN remains unidentifiable because truth target acceleration is zero.",
      "A retained N=4 result means no tested value showed clear constrained net benefit, not that N=4 is universally optimal.",
    ],
  }


def _candidate_csv_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
  comparisons = {
    str(row["candidate_id"]): row for row in report["comparisons_vs_baseline"]
  }
  rows: list[dict[str, Any]] = []
  for candidate in report["candidate_summaries"]:
    comparison = comparisons[str(candidate["candidate_id"])]
    rows.append(
      {
        "candidate_id": candidate["candidate_id"],
        "nav_gain": candidate["nav_gain"],
        "hard_gate_passed": candidate["hard_gate_passed"],
        "clear_net_benefit": comparison["clear_net_benefit"],
        "decision": comparison["decision"],
        **{f"gate_{key}": value for key, value in candidate["gates"].items()},
        **{f"audit_{key}": value for key, value in candidate["audit"].items() if not isinstance(value, list)},
        **{f"metric_{key}": value for key, value in candidate["metrics"].items()},
        **{
          f"delta_{key}": value
          for key, value in comparison["deltas_vs_baseline"].items()
        },
      }
    )
  return rows


def _format_number(value: Any) -> str:
  parsed = _finite(value)
  return "n/a" if parsed is None else f"{parsed:.9g}"


def render_chinese_conclusion(report: dict[str, Any]) -> str:
  selection = dict(report["selection"])
  lines = [
    "# 第五阶段：制导标量约束校准结论",
    "",
    "## 可识别性边界",
    "",
    "本阶段只对 `nav_gain` 做 OFAT。capture 已关闭，APN 在 CV 目标下不可识别，",
    "tracker alpha/beta 已在第二阶段冻结，35g 是约束而不是优化变量。",
    "",
    "## 约束与判据",
    "",
    "- 阶段4的 N 必须保持 robust hit，O 必须保持 robust miss。",
    "- M 只观察，不施加二值优化压力。",
    "- 半步长网格独立于阶段4主网格，仅用于观察边界外推；更多 hit 不计为收益。",
    "- 镜像差、seed spread、capture=0、35g、runtime contract 与单命中带均为硬门。",
    "- 相对 N=4，theta 最大位移不得超过 2.5deg，minimum/maximum range "
    "边界最大位移不得超过 0.5km。",
    "- 非基线候选还必须在无实质回归的前提下达到预注册的材料性改善阈值。",
    "- release gate 独立于标量选择：world_cv tracker 的 "
    "`acceleration_world_mps2` 当前固定为 0，阶段4/5只有 CV authority。",
    "",
    "## 候选结果",
    "",
    "| nav gain | hard gate | clear net benefit | N violations | O violations | holdout hits(obs) | saturation P95 | theta shift | range shift min/max |",
    "|---:|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  comparisons = {
    str(row["candidate_id"]): row for row in report["comparisons_vs_baseline"]
  }
  for candidate in report["candidate_summaries"]:
    comparison = comparisons[str(candidate["candidate_id"])]
    deltas = dict(comparison.get("deltas_vs_baseline", {}) or {})
    lines.append(
      f"| {float(candidate['nav_gain']):g} | {candidate['hard_gate_passed']} | "
      f"{comparison['clear_net_benefit']} | "
      f"{candidate['audit']['N_violation_count']} | "
      f"{candidate['audit']['O_violation_count']} | "
      f"{candidate['metrics']['holdout_robust_hit_count']} | "
      f"{float(candidate['metrics']['guidance_saturation_fraction_p95']):.9g} | "
      f"{_format_number(deltas.get('theta_fuze_max_displacement_deg', 0.0))} | "
      f"{_format_number(deltas.get('minimum_range_boundary_max_displacement_km', 0.0))}/"
      f"{_format_number(deltas.get('maximum_range_boundary_max_displacement_km', 0.0))} |"
    )
  lines.extend(
    [
      "",
      "## 选择",
      "",
      f"- selected nav gain：`{float(selection['selected_nav_gain']):g}`。",
      f"- decision：`{selection['decision']}`。",
      f"- selected hard gate：`{selection['selected_candidate_hard_gate_passed']}`。",
      f"- scalar selection passed：`{selection['scalar_selection_passed']}`。",
      f"- default promotion ready：`{selection['default_promotion_ready']}`；"
      "当前 held，原因是 maneuver/APN authority 尚未建立。",
      "",
      "该选择仅对当前确定性 CV 工程校准域有效，不构成真实武器性能或交战权威。",
      "",
    ]
  )
  return "\n".join(lines)


def _csv_value(value: Any) -> Any:
  if isinstance(value, (dict, list, tuple)):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
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


def _artifact_relpath(path: Path) -> str:
  try:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))
  except ValueError:
    return str(path.resolve())


def _git_value(*args: str) -> str:
  completed = subprocess.run(
    ["git", *args], cwd=REPO_ROOT, check=False, capture_output=True, text=True
  )
  return completed.stdout.strip() if completed.returncode == 0 else ""


def write_bundle(
  report: dict[str, Any],
  *,
  output_dir: Path,
  stem: str,
  stage4_report_path: Path = DEFAULT_STAGE4_REPORT,
) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "report_json": output_dir / f"{stem}.json",
    "candidate_summary_csv": output_dir / f"{stem}_candidate_summary.csv",
    "runs_csv": output_dir / f"{stem}_runs.csv",
    "cells_csv": output_dir / f"{stem}_cells.csv",
    "conclusions_zh_md": output_dir / f"{stem}_conclusions.zh.md",
    "manifest_json": output_dir / f"{stem}_manifest.json",
  }
  report["artifacts"] = {key: _artifact_relpath(path) for key, path in paths.items()}
  _write_csv(paths["candidate_summary_csv"], _candidate_csv_rows(report))
  _write_csv(paths["runs_csv"], list(report["runs"]))
  _write_csv(paths["cells_csv"], list(report["cells"]))
  paths["conclusions_zh_md"].write_text(
    render_chinese_conclusion(report), encoding="utf-8"
  )
  report_payload = {
    key: value for key, value in report.items() if key not in {"runs", "cells"}
  }
  report_payload["raw_evidence"] = {
    "runs_csv": report["artifacts"]["runs_csv"],
    "cells_csv": report["artifacts"]["cells_csv"],
    "storage_policy": "raw rows are retained in CSV and omitted from summary JSON",
    "run_count": len(report["runs"]),
    "cell_count": len(report["cells"]),
  }
  paths["report_json"].write_text(
    json.dumps(report_payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
  )

  ef_py_path = Path(probe.ef_py.__file__).resolve()
  database_path = Path(str(report.get("runtime", {}).get("database_path", probe.DEFAULT_DATABASE_PATH))).resolve()
  aim120_path = database_path / "weapons/air_to_air/aim_120c.json"
  stage4_path = Path(stage4_report_path).resolve()
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
    "tool": {"path": _artifact_relpath(Path(__file__)), "sha256": _sha256(Path(__file__))},
    "git": {
      "head": _git_value("rev-parse", "HEAD"),
      "branch": _git_value("branch", "--show-current"),
      "worktree_porcelain": _git_value("status", "--short"),
    },
    "inputs": {
      "stage4_report_path": _artifact_relpath(stage4_path),
      "stage4_report_sha256": _sha256(stage4_path),
      "aim120_definition_path": _artifact_relpath(aim120_path),
      "aim120_definition_sha256": _sha256(aim120_path),
    },
    "runtime": {
      "ef_py_path": str(ef_py_path),
      "ef_py_sha256": _sha256(ef_py_path),
      "database_path": str(database_path),
    },
    "run_contract": {
      "identifiability": report["identifiability"],
      "evaluated_scalar": report["evaluated_scalar"],
      "frozen_production_mechanism_tuning": report["frozen_production_mechanism_tuning"],
      "sampling": report["sampling"],
      "selection_policy": report["selection_policy"],
    },
    "selection": report["selection"],
    "release_gate": report["release_gate"],
    "artifacts": hashed_artifacts,
    "authority_boundary": {
      "real_weapon_or_target_authority": False,
      "real_world_pk": False,
      "interpretation": "deterministic engineering CV scalar calibration only",
    },
  }
  paths["manifest_json"].write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
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


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--stage4-report", type=Path, default=DEFAULT_STAGE4_REPORT)
  parser.add_argument("--database", type=Path, default=probe.DEFAULT_DATABASE_PATH)
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--stem", default=DEFAULT_STEM)
  parser.add_argument("--nav-gain", type=float, action="append", default=[])
  parser.add_argument("--seed", type=int, action="append", default=[])
  parser.add_argument("--range-km", type=float, action="append", default=[])
  parser.add_argument("--angle-deg", type=float, action="append", default=[])
  parser.add_argument("--skip-holdout", action="store_true")
  parser.add_argument(
    "--strict",
    action="store_true",
    help="Return non-zero unless a formal run selects a candidate that passes all gates.",
  )
  return parser


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  stage4_report = _load_stage4_report(Path(args.stage4_report))
  nav_gains = (
    tuple(sorted(set(float(value) for value in args.nav_gain)))
    if args.nav_gain
    else DEFAULT_NAV_GAINS
  )
  seeds = tuple(int(value) for value in args.seed) if args.seed else DEFAULT_SEEDS
  ranges = tuple(sorted(set(float(value) for value in args.range_km))) or None
  angles = tuple(sorted(set(float(value) for value in args.angle_deg))) or None
  probe.ef_py.set_log_level("warn")
  with _native_stdout_to_stderr():
    report = build_report(
      stage4_report=stage4_report,
      stage4_report_path=Path(args.stage4_report),
      database_path=Path(args.database),
      nav_gains=nav_gains,
      seeds=seeds,
      ranges_km=ranges,
      angles_deg=angles,
      enable_holdout=not bool(args.skip_holdout),
    )
  report["runtime"] = {
    "ef_py_artifact": str(Path(probe.ef_py.__file__).resolve()),
    "database_path": str(Path(args.database).resolve()),
  }
  artifacts = write_bundle(
    report,
    output_dir=Path(args.output_dir),
    stem=str(args.stem),
    stage4_report_path=Path(args.stage4_report),
  )
  print(
    json.dumps(
      {
        "status": report["status"],
        "formal_scope": report["formal_scope"],
        "selection": report["selection"],
        "artifacts": artifacts,
      },
      ensure_ascii=False,
      allow_nan=False,
    )
  )
  return (
    1
    if bool(args.strict) and not bool(report["selection"]["formal_stage5_passed"])
    else 0
  )


if __name__ == "__main__":
  raise SystemExit(main())
