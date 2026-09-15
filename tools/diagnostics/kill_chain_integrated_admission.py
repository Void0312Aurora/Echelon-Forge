#!/usr/bin/env python3
"""Run the P11 integrated kill-chain structural admission matrix."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import ensure_repo_imports, repo_root  # noqa: E402

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.diagnostics import kill_chain_decoupling_probe as probe  # noqa: E402
from tools.diagnostics import kill_chain_expectation_harness as harness  # noqa: E402
from tools.diagnostics.common import native_stdout_to_stderr  # noqa: E402

SCHEMA_VERSION = "a2.kill_chain_integrated_admission.v1"
GENERATED_ON = "2026-09-15"
DEFAULT_SEEDS = (20260621, 20260622, 20260623)
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs/systems/weapons/reviews/kill_chain_integrated_admission_20260915"
  / "review_packets"
)
DEFAULT_STEM = "kill_chain_integrated_admission_20260915"
DEFAULT_AIM120_DEFINITION = (
  REPO_ROOT / "examples/config/database/weapons/air_to_air/aim_120c.json"
)
EXPECTATION_REBASELINE_REVIEW = (
  REPO_ROOT
  / "docs/systems/weapons/reviews/kill_chain_p11_expectation_rebaseline_20260915"
  / "review_packets/kill_chain_p11_independent_review_acceptance_20260915.zh.md"
)
MOTION_LAYERS = ("nonmaneuvering_constant_velocity", "mild_maneuver")
EXPECTED_CASES_PER_SEED = 93
EXPECTED_GUIDANCE_RUNTIME: dict[str, float | int] = {
  "nav_gain": 4.0,
  "pn_los_rate_source": 1,
  "target_kinematics_estimator": 2,
  "capture_guidance_mode": 0,
  "target_tracker_alpha": 0.2,
  "target_tracker_beta": 0.02,
  "target_tracker_gamma": 0.5,
  "apn_target_accel_gain": 0.125,
  "guidance_max_lateral_g": 35.0,
}
EXPECTED_STAGE_OWNERS = {
  "approach": "guidance_kinematics",
  "fuze_decision": "fuze_decision",
  "warhead_load_field": "warhead_load_field",
  "component_response": "component_response",
  "consequence_projection": "consequence_projection",
}
CONSEQUENCE_DELTA_FIELDS = (
  "system_health_delta",
  "mission_capability_delta",
  "mobility_capability_delta",
  "sensor_capability_delta",
  "survivability_margin_delta",
)
CONSEQUENCE_FLAG_FIELDS = (
  "mission_kill",
  "mobility_kill",
  "sensor_kill",
  "destroyed",
  "lifecycle_terminal",
)


def _finite(value: Any, default: float = 0.0) -> float:
  try:
    out = float(value)
  except (TypeError, ValueError):
    return float(default)
  return out if math.isfinite(out) else float(default)


def _stage_map(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
  return {
    str(row.get("abstraction_stage", "") or ""): dict(row)
    for row in list(case.get("stage_abstractions", []) or [])
    if str(row.get("abstraction_stage", "") or "")
  }


def _resolved_runtime_mismatch(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
  runtime = dict(case.get("resolved_guidance_runtime", {}) or {})
  mismatch: dict[str, dict[str, Any]] = {}
  integer_fields = {
    "pn_los_rate_source",
    "target_kinematics_estimator",
    "capture_guidance_mode",
  }
  for key, expected in EXPECTED_GUIDANCE_RUNTIME.items():
    observed = runtime.get(key)
    if key in integer_fields:
      equal = int(observed) == int(expected) if observed is not None else False
    else:
      equal = observed is not None and abs(_finite(observed) - float(expected)) <= 1.0e-12
    if not equal:
      mismatch[key] = {"expected": expected, "observed": observed}
  return mismatch


def _consequence_is_zero(
  stages: dict[str, dict[str, Any]],
  runtime_facade: dict[str, Any],
) -> bool:
  stage = stages.get("consequence_projection", {})
  if not bool(stage.get("present")):
    return True
  observed = dict(stage.get("observed", {}) or {})
  consequence = dict(runtime_facade.get("consequence_projection", {}) or {})
  if int(consequence.get("component_hit_count", 0) or 0) != 0:
    return False
  if int(consequence.get("component_failure_count", 0) or 0) != 0:
    return False
  if any(abs(_finite(observed.get(field))) > 1.0e-12 for field in CONSEQUENCE_DELTA_FIELDS):
    return False
  return not any(bool(observed.get(field)) for field in CONSEQUENCE_FLAG_FIELDS)


def _terminal_track_residual_cause(
  *,
  entered_r_fuze: bool,
  fuze_triggered: bool,
  fuze: dict[str, Any],
  guidance_runtime_summary: dict[str, Any],
) -> str:
  if not entered_r_fuze or fuze_triggered:
    return ""
  last = dict(guidance_runtime_summary.get("last_runtime_observation", {}) or {})
  final_mode = int(last.get("seeker_mode", -1) or 0)
  fov_excess = _finite(guidance_runtime_summary.get("max_detection_fov_excess_deg"))
  if (
    not bool(fuze.get("terminal_track_valid"))
    and final_mode == 2
    and fov_excess > 0.0
    and guidance_runtime_summary.get("first_detection_outside_fov_time_s") is not None
    and guidance_runtime_summary.get("first_memory_time_s") is not None
    and guidance_runtime_summary.get("first_ballistic_time_s") is not None
  ):
    return "seeker_fov_exit_then_memory_timeout"
  if not bool(fuze.get("terminal_track_valid")) and final_mode == 2:
    return "ballistic_without_terminal_track"
  if not bool(fuze.get("target_detected")):
    return "fuze_target_detection_rejected"
  return "unclassified_in_radius_fuze_block"


def _case_evidence(
  *,
  seed: int,
  grid_case: dict[str, Any],
  heatmap_row: dict[str, Any],
  probe_case: dict[str, Any],
) -> dict[str, Any]:
  stages = _stage_map(probe_case)
  runtime_facade = dict(probe_case.get("runtime_facade", {}) or {})
  runtime_fuze = dict(runtime_facade.get("fuze_decision", {}) or {})
  guidance = dict(heatmap_row.get("guidance_approach", {}) or {})
  fuze = dict(heatmap_row.get("fuze_decision", {}) or {})
  load = dict(heatmap_row.get("warhead_load_field", {}) or {})
  response = dict(heatmap_row.get("component_response", {}) or {})
  consequence = dict(heatmap_row.get("consequence_projection", {}) or {})
  guidance_runtime_summary = dict(
    probe_case.get("guidance_runtime_summary", {}) or {}
  )
  last_runtime_observation = dict(
    guidance_runtime_summary.get("last_runtime_observation", {}) or {}
  )
  entered = bool(guidance.get("entered_R_fuze"))
  triggered = bool(fuze.get("fuze_triggered"))
  detonated = bool(fuze.get("detonated"))
  load_count = int(load.get("component_load_row_count", 0) or 0)
  response_count = int(response.get("component_response_row_count", 0) or 0)
  stage_ids_exact = set(stages) == set(EXPECTED_STAGE_OWNERS)
  stage_owners_clean = stage_ids_exact and all(
    str(stages[name].get("owner", "") or "") == owner
    for name, owner in EXPECTED_STAGE_OWNERS.items()
  )
  approach_and_fuze_observed = bool(stages.get("approach", {}).get("present")) and bool(
    stages.get("fuze_decision", {}).get("present")
  )
  downstream_present = all(
    bool(stages.get(name, {}).get("present"))
    for name in ("warhead_load_field", "component_response", "consequence_projection")
  )
  response_owner_clean = int(
    dict(probe_case.get("component_load_factor_summary", {}) or {}).get(
      "rows_with_response_fields_on_load_row", 0
    )
    or 0
  ) == 0
  runtime_mismatch = _resolved_runtime_mismatch(probe_case)
  no_guidance_override = not dict(probe_case.get("guidance_tuning_overrides", {}) or {})
  authority_guarded = (
    str(dict(heatmap_row.get("guards", {}) or {}).get("authority_boundary_status", ""))
    == "engineering_proxy_guarded"
  )
  violations: list[str] = []
  if not stage_ids_exact:
    violations.append("required_stage_rows_missing_or_extra")
  if not stage_owners_clean:
    violations.append("stage_owner_mismatch")
  if not approach_and_fuze_observed:
    violations.append("approach_or_fuze_not_observed")
  if runtime_mismatch or not no_guidance_override:
    violations.append("not_config_backed_p10_guidance")
  if not response_owner_clean:
    violations.append("component_response_owner_leaked_into_load_row")
  if not authority_guarded:
    violations.append("authority_boundary_violation")
  if triggered:
    if not entered:
      violations.append("fuze_triggered_outside_declared_radius")
    if not detonated:
      violations.append("triggered_without_detonation")
    if not bool(probe_case.get("effect")):
      violations.append("triggered_without_effect_event")
    if not bool(runtime_facade.get("runtime_dto_available")):
      violations.append("triggered_without_runtime_facade")
    if not downstream_present:
      violations.append("triggered_without_complete_downstream_stages")
    if load_count <= 0 or response_count <= 0:
      violations.append("triggered_without_component_load_response_rows")
    if load_count != response_count:
      violations.append("component_load_response_cardinality_mismatch")
  else:
    if load_count != 0 or response_count != 0:
      violations.append("untriggered_case_has_load_or_response_rows")
    if bool(stages.get("warhead_load_field", {}).get("present")):
      violations.append("untriggered_case_has_warhead_stage")
    if bool(stages.get("component_response", {}).get("present")):
      violations.append("untriggered_case_has_component_response_stage")
    if not _consequence_is_zero(stages, runtime_facade):
      violations.append("untriggered_case_has_nonzero_consequence")

  if triggered:
    chain_state = "complete_effect_chain"
  elif entered:
    chain_state = "in_radius_fuze_blocked"
  else:
    chain_state = "outside_no_load"
  launch_class = str(grid_case.get("launch_class", "") or "")
  terminal_track_residual_cause = _terminal_track_residual_cause(
    entered_r_fuze=entered,
    fuze_triggered=triggered,
    fuze=fuze,
    guidance_runtime_summary=guidance_runtime_summary,
  )
  outcome_state = str(consequence.get("outcome_state", "") or "") or chain_state
  return {
    "case_id": str(grid_case["case_id"]),
    "seed": int(seed),
    "target_motion_layer": str(grid_case["target_motion_layer"]),
    "target_motion_profile_id": str(grid_case["target_motion_profile_id"]),
    "maneuver_severity": str(grid_case["maneuver_severity"]),
    "target_acceleration_x_mps2": _finite(grid_case["target_acceleration_mps2"][0]),
    "range_km": _finite(grid_case["range_km"]),
    "bearing_deg": _finite(grid_case["signed_bearing_deg"]),
    "launch_class": launch_class,
    "nearest_distance_m": _finite(guidance.get("nearest_distance_m"), math.inf),
    "entered_R_fuze": entered,
    "fuze_triggered": triggered,
    "detonated": detonated,
    "fuze_reason": str(fuze.get("fuze_reason", "") or ""),
    "fuze_terminal_track_valid": bool(fuze.get("terminal_track_valid")),
    "fuze_target_detected": bool(fuze.get("target_detected")),
    "fuze_sensor_opportunity_score": _finite(
      runtime_fuze.get("sensor_opportunity_score")
    ),
    "fuze_quality": _finite(fuze.get("fuze_quality")),
    "seeker_fov_half_angle_deg": _finite(
      guidance_runtime_summary.get("seeker_fov_half_angle_deg")
    ),
    "max_abs_filtered_bearing_deg": _finite(
      guidance_runtime_summary.get("max_abs_filtered_bearing_deg")
    ),
    "max_seeker_fov_excess_deg": _finite(
      guidance_runtime_summary.get("max_seeker_fov_excess_deg")
    ),
    "max_abs_detection_bearing_deg": _finite(
      guidance_runtime_summary.get("max_abs_detection_bearing_deg")
    ),
    "max_detection_fov_excess_deg": _finite(
      guidance_runtime_summary.get("max_detection_fov_excess_deg")
    ),
    "first_detection_outside_fov_time_s": guidance_runtime_summary.get(
      "first_detection_outside_fov_time_s"
    ),
    "first_memory_time_s": guidance_runtime_summary.get("first_memory_time_s"),
    "first_ballistic_time_s": guidance_runtime_summary.get("first_ballistic_time_s"),
    "track_memory_timeout_s": guidance_runtime_summary.get("track_memory_timeout_s"),
    "observed_memory_to_ballistic_s": (
      _finite(guidance_runtime_summary.get("first_ballistic_time_s"))
      - _finite(guidance_runtime_summary.get("first_memory_time_s"))
      if guidance_runtime_summary.get("first_memory_time_s") is not None
      and guidance_runtime_summary.get("first_ballistic_time_s") is not None
      else None
    ),
    "last_runtime_seeker_mode": int(
      last_runtime_observation.get("seeker_mode", -1) or 0
    ),
    "last_runtime_seeker_mode_name": str(
      last_runtime_observation.get("seeker_mode_name", "") or ""
    ),
    "terminal_track_residual_cause": terminal_track_residual_cause,
    "effect_family": str(
      dict(runtime_facade.get("warhead_load_field", {}) or {}).get("effect_family", "")
      or dict(probe_case.get("effect", {}) or {}).get("effect_family", "")
      or ""
    ),
    "component_load_row_count": load_count,
    "component_response_row_count": response_count,
    "consequence_present": bool(stages.get("consequence_projection", {}).get("present")),
    "consequence_zero_when_untriggered": (
      True if triggered else _consequence_is_zero(stages, runtime_facade)
    ),
    "outcome_state": outcome_state,
    "chain_state": chain_state,
    "stage_ids_exact": stage_ids_exact,
    "stage_owners_clean": stage_owners_clean,
    "approach_and_fuze_observed": approach_and_fuze_observed,
    "response_owner_clean": response_owner_clean,
    "no_guidance_override": no_guidance_override,
    "resolved_runtime_mismatch": runtime_mismatch,
    "authority_guarded": authority_guarded,
    "structural_consistent": not violations,
    "structural_violations": violations,
    "nominal_guidance_residual": launch_class == "N" and not entered,
    "legacy_negative_control_alert": launch_class == "O" and (
      entered or load_count > 0 or response_count > 0
    ),
    "in_radius_fuze_blocked": entered and not triggered,
  }


def _aggregate_cells(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    grouped[str(row["case_id"])].append(row)
  cells: list[dict[str, Any]] = []
  for case_id, group in sorted(grouped.items()):
    first = group[0]
    distances = [float(row["nearest_distance_m"]) for row in group]
    states = sorted({str(row["chain_state"]) for row in group})
    outcomes = sorted({str(row["outcome_state"]) for row in group})
    cells.append(
      {
        "case_id": case_id,
        "target_motion_layer": first["target_motion_layer"],
        "target_acceleration_x_mps2": first["target_acceleration_x_mps2"],
        "range_km": first["range_km"],
        "bearing_deg": first["bearing_deg"],
        "launch_class": first["launch_class"],
        "seed_count": len(group),
        "seeds": sorted({int(row["seed"]) for row in group}),
        "complete_effect_chain_count": sum(
          row["chain_state"] == "complete_effect_chain" for row in group
        ),
        "in_radius_fuze_blocked_count": sum(
          row["chain_state"] == "in_radius_fuze_blocked" for row in group
        ),
        "outside_no_load_count": sum(
          row["chain_state"] == "outside_no_load" for row in group
        ),
        "chain_states": states,
        "outcome_states": outcomes,
        "nearest_distance_min_m": min(distances),
        "nearest_distance_max_m": max(distances),
        "nearest_distance_spread_m": max(distances) - min(distances),
        "terminal_track_residual_causes": sorted(
          {
            str(row.get("terminal_track_residual_cause", "") or "")
            for row in group
            if str(row.get("terminal_track_residual_cause", "") or "")
          }
        ),
        "max_seeker_fov_excess_deg": max(
          (_finite(row.get("max_seeker_fov_excess_deg")) for row in group),
          default=0.0,
        ),
        "max_detection_fov_excess_deg": max(
          (_finite(row.get("max_detection_fov_excess_deg")) for row in group),
          default=0.0,
        ),
        "structural_consistent": all(row["structural_consistent"] for row in group),
        "nominal_guidance_residual": any(
          row["nominal_guidance_residual"] for row in group
        ),
        "legacy_negative_control_alert": any(
          row["legacy_negative_control_alert"] for row in group
        ),
        "in_radius_fuze_blocked": any(row["in_radius_fuze_blocked"] for row in group),
      }
    )
  return cells


def _evaluate(
  rows: list[dict[str, Any]],
  cells: list[dict[str, Any]],
  seeds: tuple[int, ...],
  *,
  expected_cases_per_seed: int = EXPECTED_CASES_PER_SEED,
) -> dict[str, Any]:
  expected_runs = int(expected_cases_per_seed) * len(seeds)
  case_ids = {str(cell["case_id"]) for cell in cells}
  actual_run_keys = [
    (str(row["case_id"]), int(row["seed"])) for row in rows
  ]
  expected_run_keys = {
    (case_id, int(seed)) for case_id in case_ids for seed in seeds
  }
  matrix_complete = (
    len(case_ids) == int(expected_cases_per_seed)
    and len(actual_run_keys) == expected_runs
    and len(actual_run_keys) == len(set(actual_run_keys))
    and set(actual_run_keys) == expected_run_keys
    and all(
      int(cell["seed_count"]) == len(seeds)
      and set(int(seed) for seed in cell["seeds"]) == set(seeds)
      for cell in cells
    )
  )
  structural_gates = {
    "anchor_matrix_complete": matrix_complete,
    "unique_case_seed_pairs": len(actual_run_keys) == len(set(actual_run_keys)),
    "each_cell_has_exact_required_seed_set": bool(cells) and all(
      int(cell["seed_count"]) == len(seeds)
      and set(int(seed) for seed in cell["seeds"]) == set(seeds)
      for cell in cells
    ),
    "all_cases_structurally_consistent": bool(rows) and all(
      row["structural_consistent"] for row in rows
    ),
    "all_cases_config_backed_without_guidance_override": bool(rows) and all(
      row["no_guidance_override"] and not row["resolved_runtime_mismatch"]
      for row in rows
    ),
    "all_cases_have_required_stage_rows_and_owners": bool(rows) and all(
      row["stage_ids_exact"] and row["stage_owners_clean"] for row in rows
    ),
    "all_cases_observe_approach_and_fuze": bool(rows) and all(
      row["approach_and_fuze_observed"] for row in rows
    ),
    "component_response_owner_boundary_clean": bool(rows) and all(
      row["response_owner_clean"] for row in rows
    ),
    "authority_boundary_guarded": bool(rows) and all(
      row["authority_guarded"] for row in rows
    ),
    "multi_seed_anchor_evidence": len(set(seeds)) >= 3,
    "per_cell_chain_topology_stable_across_seeds": bool(cells) and all(
      len(cell["chain_states"]) == 1 for cell in cells
    ),
    "nearest_distance_deterministic_across_seeds": bool(cells) and max(
      (cell["nearest_distance_spread_m"] for cell in cells), default=math.inf
    ) <= 1.0e-9,
    "terminal_track_residual_causes_explicit": all(
      not cell["in_radius_fuze_blocked"]
      or bool(cell["terminal_track_residual_causes"])
      for cell in cells
    ),
  }
  expectation_gates = {
    "all_nominal_cells_enter_R_fuze": not any(
      cell["nominal_guidance_residual"] for cell in cells
    ),
    "legacy_outside_cells_have_no_fuze_entry_or_downstream_effect": not any(
      cell["legacy_negative_control_alert"] for cell in cells
    ),
    "all_in_radius_cases_resolve_to_fuze_trigger": not any(
      cell["in_radius_fuze_blocked"] for cell in cells
    ),
  }
  structural_passed = all(structural_gates.values())
  accepted_n_o_passed = all(
    expectation_gates[name]
    for name in (
      "all_nominal_cells_enter_R_fuze",
      "legacy_outside_cells_have_no_fuze_entry_or_downstream_effect",
    )
  )
  expectation_passed = all(expectation_gates.values())
  return {
    "structural_gates": structural_gates,
    "expectation_gates": expectation_gates,
    "p11_structural_admission_passed": structural_passed,
    "accepted_n_o_expectation_envelope_passed": accepted_n_o_passed,
    "terminal_track_contract_passed": expectation_gates[
      "all_in_radius_cases_resolve_to_fuze_trigger"
    ],
    "legacy_expectation_envelope_passed": expectation_passed,
    "p11_complete": structural_passed and expectation_passed,
  }


def build_report(*, seeds: tuple[int, ...] = DEFAULT_SEEDS) -> dict[str, Any]:
  run_rows: list[dict[str, Any]] = []
  for seed in seeds:
    batch = harness.generate_before_report(
      grid_tier="anchor-grid",
      target_motion_layers=MOTION_LAYERS,
      effect_variants=("REV-RUNTIME-PROJECTION",),
      seed=int(seed),
      include_raw_probe=True,
    )
    grid = {str(row["case_id"]): row for row in batch["case_grid"]}
    heatmap = {
      str(row["identity"]["case_id"]): row for row in batch["heatmap_rows"]
    }
    raw = {
      str(row["case_id"]): row
      for row in batch["raw_probe_report"]["guidance_cases"]
    }
    for case_id in sorted(grid):
      run_rows.append(
        _case_evidence(
          seed=int(seed),
          grid_case=grid[case_id],
          heatmap_row=heatmap[case_id],
          probe_case=raw[case_id],
        )
      )
  cells = _aggregate_cells(run_rows)
  evaluation = _evaluate(run_rows, cells, tuple(seeds))
  chain_state_counts = dict(sorted(Counter(row["chain_state"] for row in run_rows).items()))
  outcome_counts = dict(sorted(Counter(row["outcome_state"] for row in run_rows).items()))
  alert_cells = [cell for cell in cells if cell["legacy_negative_control_alert"]]
  fuze_blocked_cells = [cell for cell in cells if cell["in_radius_fuze_blocked"]]
  fuze_blocked_cause_counts = dict(
    sorted(
      Counter(
        cause
        for cell in fuze_blocked_cells
        for cause in cell.get("terminal_track_residual_causes", [])
      ).items()
    )
  )
  nominal_residual_cells = [cell for cell in cells if cell["nominal_guidance_residual"]]
  structural_passed = bool(evaluation["p11_structural_admission_passed"])
  complete = bool(evaluation["p11_complete"])
  return {
    "schema_version": SCHEMA_VERSION,
    "status": (
      "integrated_kill_chain_admission_passed"
      if complete
      else "integrated_structure_passed_residuals_open"
      if structural_passed
      else "integrated_kill_chain_structural_admission_failed"
    ),
    "generated_on": GENERATED_ON,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "authority_boundary": {
      "engineering_synthetic_only": True,
      "config_backed_runtime": True,
      "integrated_structural_admission": structural_passed,
      "integrated_kill_chain_admission": complete,
      "real_weapon_performance_authority": False,
      "deterministic_fuze_authority": False,
      "pk_authority": False,
    },
    "expectation_baseline": {
      "id": harness.EXPECTATION_BASELINE_ID,
      "review_verdict": "accept-with-residuals",
      "independent_review_equivalent_to_manual_review": True,
      "review_record": str(EXPECTATION_REBASELINE_REVIEW.relative_to(REPO_ROOT)),
      "terminal_track_residual_retained": True,
    },
    "matrix": {
      "grid_tier": "anchor-grid",
      "motion_layers": list(MOTION_LAYERS),
      "seeds": list(seeds),
      "case_count_per_seed": EXPECTED_CASES_PER_SEED,
      "expected_run_count": EXPECTED_CASES_PER_SEED * len(seeds),
      "effect_variant": "REV-RUNTIME-PROJECTION",
      "mild_maneuver_acceleration_mps2": harness.MILD_MANEUVER_ACCELERATION_MPS2,
    },
    "expected_guidance_runtime": dict(EXPECTED_GUIDANCE_RUNTIME),
    "counts": {
      "run_count": len(run_rows),
      "cell_count": len(cells),
      "triggered_run_count": sum(row["fuze_triggered"] for row in run_rows),
      "untriggered_run_count": sum(not row["fuze_triggered"] for row in run_rows),
      "structural_violation_run_count": sum(
        not row["structural_consistent"] for row in run_rows
      ),
      "legacy_negative_control_alert_cell_count": len(alert_cells),
      "in_radius_fuze_blocked_cell_count": len(fuze_blocked_cells),
      "nominal_guidance_residual_cell_count": len(nominal_residual_cells),
    },
    "chain_state_counts": chain_state_counts,
    "outcome_state_counts": outcome_counts,
    "evaluation": evaluation,
    "residuals": {
      "legacy_negative_control_alert_cells": alert_cells,
      "in_radius_fuze_blocked_cells": fuze_blocked_cells,
      "in_radius_fuze_blocked_cause_counts": fuze_blocked_cause_counts,
      "nominal_guidance_residual_cells": nominal_residual_cells,
      "next_gate": (
        "adjudicate terminal-track runtime contract without changing the accepted "
        "N/M/O expectation baseline before declaring P11 complete"
      ),
    },
    "cells": cells,
    "runs": run_rows,
  }


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _git_value(*args: str) -> str:
  result = subprocess.run(
    ["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False
  )
  return result.stdout.strip() if result.returncode == 0 else ""


def conclusions_zh(report: dict[str, Any]) -> str:
  counts = report["counts"]
  evaluation = report["evaluation"]
  cause_counts = dict(
    report.get("residuals", {}).get("in_radius_fuze_blocked_cause_counts", {}) or {}
  )
  cause_summary = ", ".join(
    f"`{cause}`={count}" for cause, count in sorted(cause_counts.items())
  ) or "none"
  return "\n".join(
    [
      "# P11 集成杀伤链准入结论",
      "",
      f"- 总状态：`{report['status']}`。",
      f"- P11 结构准入：`{evaluation['p11_structural_admission_passed']}`；"
      f"P11 complete：`{evaluation['p11_complete']}`。",
      f"- 独立审核接受的 N/M/O 包络："
      f"`{evaluation['accepted_n_o_expectation_envelope_passed']}`；"
      f"terminal-track contract：`{evaluation['terminal_track_contract_passed']}`。",
      f"- 三种子 anchor：`{counts['run_count']}` runs / `{counts['cell_count']}` cells；"
      f"结构违规 `{counts['structural_violation_run_count']}`。",
      f"- 完整触发链：`{counts['triggered_run_count']}` runs；未触发且无 load/response："
      f"`{counts['untriggered_run_count']}` runs。",
      f"- O 类负控告警：`{counts['legacy_negative_control_alert_cell_count']}` cells；"
      f"N 类制导残差：`{counts['nominal_guidance_residual_cell_count']}` cells。",
      f"- 已进入 R_fuze 但 terminal-track 未闭合："
      f"`{counts['in_radius_fuze_blocked_cell_count']}` cells。",
      f"- terminal-track 残差原因：{cause_summary}。目标越过诊断场景的"
      " ±90 deg seeker FOV 后进入 Memory，超时后转为 Ballistic；未修改视场或"
      "放宽引信终端跟踪门。",
      "",
      "本批证明 config-backed guidance→fuze→warhead load→component response→"
      "platform consequence 的运行时结构闭合，独立审核已接受重基线后的 N/M/O 包络。"
      "近距 terminal-track runtime contract 仍未裁定，因此不声明完整 P11 通过。",
      "",
      "所有数据仍是 synthetic engineering evidence，不构成真实 AIM-120、F-16C、"
      "确定性引信或 Pk 权威。",
      "",
    ]
  )


def write_bundle(report: dict[str, Any], *, output_dir: Path, stem: str) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "report_json": output_dir / f"{stem}.json",
    "runs_csv": output_dir / f"{stem}_runs.csv",
    "cells_csv": output_dir / f"{stem}_cells.csv",
    "conclusions_zh_md": output_dir / f"{stem}_conclusions.zh.md",
    "heatmaps_png": output_dir / f"{stem}_heatmaps.png",
    "manifest_json": output_dir / f"{stem}_manifest.json",
  }
  paths["report_json"].write_text(
    json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
  )
  for key, field in (("runs_csv", "runs"), ("cells_csv", "cells")):
    rows = list(report[field])
    with paths[key].open("w", newline="", encoding="utf-8") as handle:
      writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
      if rows:
        writer.writeheader()
        writer.writerows(rows)
  paths["conclusions_zh_md"].write_text(conclusions_zh(report), encoding="utf-8")
  from tools.diagnostics.render_kill_chain_integrated_admission import render

  render(report, paths["heatmaps_png"])
  manifest = {
    "schema_version": "a2.kill_chain_integrated_admission_manifest.v1",
    "report_schema_version": SCHEMA_VERSION,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "git": {
      "head": _git_value("rev-parse", "HEAD"),
      "branch": _git_value("branch", "--show-current"),
      "worktree_porcelain": _git_value("status", "--short"),
    },
    "inputs": {
      "tool": {
        "path": str(Path(__file__).resolve().relative_to(REPO_ROOT)),
        "sha256": _sha256(Path(__file__).resolve()),
      },
      "expectation_harness": {
        "path": str(Path(harness.__file__).resolve().relative_to(REPO_ROOT)),
        "sha256": _sha256(Path(harness.__file__).resolve()),
      },
      "decoupling_probe": {
        "path": str(Path(probe.__file__).resolve().relative_to(REPO_ROOT)),
        "sha256": _sha256(Path(probe.__file__).resolve()),
      },
      "aim120_definition": {
        "path": str(DEFAULT_AIM120_DEFINITION.resolve().relative_to(REPO_ROOT)),
        "sha256": _sha256(DEFAULT_AIM120_DEFINITION),
      },
      "expectation_rebaseline_review": {
        "path": str(EXPECTATION_REBASELINE_REVIEW.resolve().relative_to(REPO_ROOT)),
        "sha256": _sha256(EXPECTATION_REBASELINE_REVIEW),
      },
      "ef_py": {
        "path": str(Path(probe.ef_py.__file__).resolve()),
        "sha256": _sha256(Path(probe.ef_py.__file__).resolve()),
      },
    },
    "artifacts": {
      key: {
        "path": str(path.resolve().relative_to(REPO_ROOT)),
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
      }
      for key, path in paths.items()
      if key != "manifest_json"
    },
  }
  paths["manifest_json"].write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
  )
  return {key: str(path.resolve()) for key, path in paths.items()}


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--seed", type=int, action="append", default=[])
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--stem", default=DEFAULT_STEM)
  parser.add_argument("--strict-structural", action="store_true")
  args = parser.parse_args(argv)
  seeds = tuple(args.seed) if args.seed else DEFAULT_SEEDS
  with native_stdout_to_stderr():
    report = build_report(seeds=seeds)
  paths = write_bundle(report, output_dir=args.output_dir, stem=str(args.stem))
  print(json.dumps({"status": report["status"], "artifacts": paths}, indent=2))
  if args.strict_structural and not report["evaluation"]["p11_structural_admission_passed"]:
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
