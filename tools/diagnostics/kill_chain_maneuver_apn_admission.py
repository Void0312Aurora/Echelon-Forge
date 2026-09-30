#!/usr/bin/env python3
"""Build the P10 maneuver-tracker and APN admission evidence bundle.

This is an engineering/synthetic admission only.  It proves whether non-zero
target acceleration is observable and whether APN propagation is structurally
identifiable.  It does not claim real AIM-120 performance or Pk authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlparse
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.diagnostics import kill_chain_decoupling_probe as probe  # noqa: E402


SCHEMA_VERSION = "a2.kill_chain_maneuver_apn_admission.v1"
MANIFEST_SCHEMA_VERSION = "a2.kill_chain_maneuver_apn_admission_manifest.v2"
ARTIFACT_INDEX_SCHEMA_VERSION = "a2.kill_chain_artifact_index.v1"
RUNTIME_ATTESTATION_SCHEMA_VERSION = "a2.kill_chain_runtime_build_attestation.v1"
DEFAULT_RETENTION_OWNER = "Echelon-Forge maintainers"
GENERATED_ON = "2026-09-15"
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "artifacts/kill_chain/20260915/raw_review_packets/"
  "kill_chain_maneuver_apn_admission_20260915"
)
DEFAULT_STEM = "kill_chain_maneuver_apn_admission_20260915"
DEFAULT_AIM120_DEFINITION = (
  REPO_ROOT / "examples/config/database/weapons/air_to_air/aim_120c.json"
)
R_FUZE_M = 15.0
RANGES_KM = (6.0, 8.0, 10.0)
BEARINGS_DEG = (-60.0, -30.0, 0.0, 30.0, 60.0)
TARGET_ACCELERATIONS_X_MPS2 = (-8.0, 0.0, 8.0)
APN_GAINS = (0.0, 0.125, 0.25, 0.5)
NOISY_SEEDS = (20260621, 20260622, 20260623)
NOISY_RANGE_KM = 8.0
NOISY_BEARINGS_DEG = (-30.0, 30.0)
NOISY_ACCELERATIONS_X_MPS2 = (-8.0, 8.0)
ACCELERATION_STABLE_START_TIME_S = 3.5
PUBLISHED_ARTIFACT_KEYS = (
  "report_json",
  "clean_runs_csv",
  "noisy_runs_csv",
  "config_backed_runs_csv",
  "candidate_summary_csv",
)

PRODUCTION_MECHANISM_TUNING: dict[str, float | int] = {
  "pn_los_rate_source": 1,
  "target_kinematics_estimator": 2,
  "target_tracker_alpha": 0.20,
  "target_tracker_beta": 0.02,
  "target_tracker_gamma": 0.5,
  "capture_guidance_mode": 0,
  "nav_gain": 4.0,
  "max_lateral_g": 35.0,
}

TRACKER_GATES = {
  "clean_max_acceleration_rmse_mps2": 1.25,
  "clean_max_terminal_acceleration_error_mps2": 0.10,
  "constant_velocity_max_false_acceleration_mps2": 1.0e-6,
  "zero_truth_max_apn_acceleration_mps2": 1.0e-6,
  "maneuver_min_identifiable_apn_acceleration_mps2": 0.10,
  "max_component_sum_error_mps2": 1.0e-9,
  "max_mirror_nearest_distance_error_m": 1.0e-3,
  "max_achieved_lateral_g": 35.0 + 1.0e-6,
}

NOISY_PROMOTION_GATES = {
  "max_acceleration_rmse_mps2": 12.0,
  "max_estimated_acceleration_mps2": 32.0,
}


def _finite(value: Any, default: float = 0.0) -> float:
  try:
    parsed = float(value)
  except (TypeError, ValueError):
    return float(default)
  return parsed if math.isfinite(parsed) else float(default)


def _nearest_distance(result: dict[str, Any]) -> float:
  for field in ("nearest_miss_distance_m", "truth_min_distance_m"):
    value = result.get(field)
    if value is not None and math.isfinite(float(value)):
      return float(value)
  raise RuntimeError(f"missing finite nearest distance for {result.get('case_id')}")


def _stable_trace(result: dict[str, Any]) -> list[dict[str, Any]]:
  return [
    row
    for row in list(result.get("guidance_runtime_trace", []) or [])
    if _finite(row.get("time_s")) >= ACCELERATION_STABLE_START_TIME_S
    and _finite(row.get("truth_distance_m")) > 1000.0
    and bool(row.get("target_acceleration_valid"))
  ]


def _max(rows: Iterable[dict[str, Any]], field: str, default: float = 0.0) -> float:
  values = [_finite(row.get(field), default) for row in rows]
  return max(values, default=default)


def _summarize_run(
  result: dict[str, Any],
  *,
  tier: str,
  range_km: float,
  bearing_deg: float,
  target_accel_x_mps2: float,
  apn_gain: float,
  seed: int,
) -> dict[str, Any]:
  stable = _stable_trace(result)
  errors = [_finite(row.get("target_accel_error_mps2")) for row in stable]
  terminal_error = errors[-1] if errors else math.inf
  resolved = dict(result.get("resolved_guidance_runtime", {}) or {})
  expected = {
    key: value
    for key, value in PRODUCTION_MECHANISM_TUNING.items()
    if key != "max_lateral_g"
  }
  expected["guidance_max_lateral_g"] = PRODUCTION_MECHANISM_TUNING["max_lateral_g"]
  expected["apn_target_accel_gain"] = apn_gain
  resolved_mismatch = {
    key: {"expected": value, "actual": resolved.get(key)}
    for key, value in expected.items()
    if resolved.get(key) != value
  }
  return {
    "tier": tier,
    "case_id": str(result.get("case_id", "")),
    "range_km": float(range_km),
    "bearing_deg": float(bearing_deg),
    "target_accel_x_mps2": float(target_accel_x_mps2),
    "apn_gain": float(apn_gain),
    "seed": int(seed),
    "nearest_distance_m": _nearest_distance(result),
    "rho_fuze": _nearest_distance(result) / R_FUZE_M,
    "entered_R_fuze": _nearest_distance(result) <= R_FUZE_M,
    "max_achieved_lateral_g": _finite(result.get("max_achieved_lateral_g")),
    "stable_trace_count": len(stable),
    "acceleration_valid_observed": bool(stable),
    "acceleration_rmse_mps2": (
      math.sqrt(statistics.fmean(value * value for value in errors))
      if errors
      else math.inf
    ),
    "terminal_acceleration_error_mps2": terminal_error,
    "max_estimated_acceleration_mps2": _max(stable, "target_track_accel_mps2"),
    "max_apn_acceleration_mps2": _max(stable, "guidance_apn_lateral_accel_mps2"),
    "max_component_sum_error_mps2": _max(stable, "guidance_component_sum_error_mps2"),
    "resolved_runtime_mismatch": resolved_mismatch,
  }


def _run(
  *,
  tier: str,
  range_km: float,
  bearing_deg: float,
  target_accel_x_mps2: float,
  apn_gain: float,
  seed: int,
  noisy: bool,
  runner: Callable[..., dict[str, Any]],
  apply_guidance_overrides: bool = True,
) -> dict[str, Any]:
  case_id = (
    f"p10_{tier}_r{range_km:g}_b{bearing_deg:+g}_a{target_accel_x_mps2:+g}_"
    f"g{apn_gain:g}_s{seed}"
  ).replace("+", "p").replace("-", "m").replace(".", "p")
  result = runner(
    case_id=case_id,
    range_m=float(range_km) * 1000.0,
    bearing_deg=float(bearing_deg),
    seed=int(seed),
    guidance_tuning_overrides=(
      {
        **PRODUCTION_MECHANISM_TUNING,
        "apn_target_accel_gain": float(apn_gain),
      }
      if apply_guidance_overrides
      else None
    ),
    collect_guidance_runtime_trace=True,
    guidance_trace_stride=3,
    guidance_measurement_period_s=0.05 if noisy else 0.0,
    guidance_bearing_noise_std_deg=0.2 if noisy else 0.0,
    guidance_range_noise_std_m=10.0 if noisy else 0.0,
    target_acceleration_mps2=(float(target_accel_x_mps2), 0.0, 0.0),
  )
  return _summarize_run(
    result,
    tier=tier,
    range_km=range_km,
    bearing_deg=bearing_deg,
    target_accel_x_mps2=target_accel_x_mps2,
    apn_gain=apn_gain,
    seed=seed,
  )


def _mirror_error(rows: list[dict[str, Any]]) -> float:
  lookup = {
    (
      row["tier"], row["range_km"], row["bearing_deg"],
      row["target_accel_x_mps2"], row["apn_gain"], row["seed"],
    ): row
    for row in rows
  }
  errors: list[float] = []
  for row in rows:
    mirrored = lookup.get(
      (
        row["tier"], row["range_km"], -row["bearing_deg"],
        -row["target_accel_x_mps2"], row["apn_gain"], row["seed"],
      )
    )
    if mirrored is not None:
      errors.append(abs(row["nearest_distance_m"] - mirrored["nearest_distance_m"]))
  return max(errors, default=math.inf)


def _candidate_summary(rows: list[dict[str, Any]], gain: float) -> dict[str, Any]:
  selected = [row for row in rows if row["apn_gain"] == gain]
  distances = [row["nearest_distance_m"] for row in selected]
  maneuver = [row for row in selected if row["target_accel_x_mps2"] != 0.0]
  constant_velocity = [row for row in selected if row["target_accel_x_mps2"] == 0.0]
  return {
    "apn_gain": float(gain),
    "run_count": len(selected),
    "hit_count": sum(value <= R_FUZE_M for value in distances),
    "miss_count": sum(value > R_FUZE_M for value in distances),
    "worst_nearest_distance_m": max(distances, default=math.inf),
    "mean_nearest_distance_m": statistics.fmean(distances) if distances else math.inf,
    "total_excess_over_R_fuze_m": sum(max(0.0, value - R_FUZE_M) for value in distances),
    "max_acceleration_rmse_mps2": max(
      (row["acceleration_rmse_mps2"] for row in maneuver), default=math.inf
    ),
    "max_terminal_acceleration_error_mps2": max(
      (row["terminal_acceleration_error_mps2"] for row in maneuver), default=math.inf
    ),
    "max_estimated_acceleration_mps2": max(
      (row["max_estimated_acceleration_mps2"] for row in maneuver), default=math.inf
    ),
    "min_maneuver_apn_acceleration_mps2": min(
      (row["max_apn_acceleration_mps2"] for row in maneuver), default=0.0
    ),
    "max_constant_velocity_apn_acceleration_mps2": max(
      (row["max_apn_acceleration_mps2"] for row in constant_velocity), default=0.0
    ),
    "max_constant_velocity_false_acceleration_mps2": max(
      (row["max_estimated_acceleration_mps2"] for row in constant_velocity), default=0.0
    ),
    "max_achieved_lateral_g": max(
      (row["max_achieved_lateral_g"] for row in selected), default=math.inf
    ),
    "max_component_sum_error_mps2": max(
      (row["max_component_sum_error_mps2"] for row in selected), default=math.inf
    ),
  }


def _clear_net_benefit(candidate: dict[str, Any], baseline: dict[str, Any]) -> bool:
  return bool(
    candidate["apn_gain"] > 0.0
    and candidate["hit_count"] >= baseline["hit_count"]
    and candidate["worst_nearest_distance_m"] <= baseline["worst_nearest_distance_m"]
    and candidate["total_excess_over_R_fuze_m"]
    < baseline["total_excess_over_R_fuze_m"] - 0.1
  )


def _run_identity(row: dict[str, Any]) -> tuple[Any, ...]:
  return (
    "noisy" if "noisy" in str(row["tier"]) else "clean",
    row["range_km"],
    row["bearing_deg"],
    row["target_accel_x_mps2"],
    row["seed"],
  )


def _config_backed_parity(
  config_rows: list[dict[str, Any]], selected_rows: list[dict[str, Any]]
) -> dict[str, float]:
  selected = {_run_identity(row): row for row in selected_rows}
  nearest_deltas: list[float] = []
  acceleration_rmse_deltas: list[float] = []
  for row in config_rows:
    reference = selected.get(_run_identity(row))
    if reference is None:
      return {
        "max_nearest_distance_delta_m": math.inf,
        "max_acceleration_rmse_delta_mps2": math.inf,
      }
    nearest_deltas.append(
      abs(row["nearest_distance_m"] - reference["nearest_distance_m"])
    )
    acceleration_rmse_deltas.append(
      abs(row["acceleration_rmse_mps2"] - reference["acceleration_rmse_mps2"])
    )
  return {
    "max_nearest_distance_delta_m": max(nearest_deltas, default=math.inf),
    "max_acceleration_rmse_delta_mps2": max(
      acceleration_rmse_deltas, default=math.inf
    ),
  }


def build_report(
  *,
  ranges_km: tuple[float, ...] = RANGES_KM,
  bearings_deg: tuple[float, ...] = BEARINGS_DEG,
  accelerations_x_mps2: tuple[float, ...] = TARGET_ACCELERATIONS_X_MPS2,
  apn_gains: tuple[float, ...] = APN_GAINS,
  noisy_seeds: tuple[int, ...] = NOISY_SEEDS,
  include_noisy: bool = True,
  include_config_backed_confirmation: bool = False,
  runner: Callable[..., dict[str, Any]] = probe.run_guidance_case,
) -> dict[str, Any]:
  clean_rows = [
    _run(
      tier="clean_stage4",
      range_km=range_km,
      bearing_deg=bearing_deg,
      target_accel_x_mps2=acceleration,
      apn_gain=gain,
      seed=NOISY_SEEDS[0],
      noisy=False,
      runner=runner,
    )
    for gain in apn_gains
    for range_km in ranges_km
    for bearing_deg in bearings_deg
    for acceleration in accelerations_x_mps2
  ]
  noisy_rows: list[dict[str, Any]] = []
  if include_noisy:
    noisy_rows = [
      _run(
        tier="noisy_stage5_holdout",
        range_km=NOISY_RANGE_KM,
        bearing_deg=bearing_deg,
        target_accel_x_mps2=acceleration,
        apn_gain=gain,
        seed=seed,
        noisy=True,
        runner=runner,
      )
      for gain in apn_gains
      for seed in noisy_seeds
      for bearing_deg in NOISY_BEARINGS_DEG
      for acceleration in NOISY_ACCELERATIONS_X_MPS2
    ]

  clean_candidates = [_candidate_summary(clean_rows, gain) for gain in apn_gains]
  noisy_candidates = [_candidate_summary(noisy_rows, gain) for gain in apn_gains]
  baseline = next(row for row in clean_candidates if row["apn_gain"] == 0.0)
  beneficial_gains = [
    row["apn_gain"] for row in clean_candidates if _clear_net_benefit(row, baseline)
  ]
  selected_gain = min(beneficial_gains) if beneficial_gains else 0.0
  maneuver_clean = [row for row in clean_rows if row["target_accel_x_mps2"] != 0.0]
  constant_velocity_clean = [
    row for row in clean_rows if row["target_accel_x_mps2"] == 0.0
  ]
  nonzero_gain_maneuver = [
    row for row in maneuver_clean if row["apn_gain"] > 0.0
  ]
  resolved_mismatch_count = sum(
    bool(row["resolved_runtime_mismatch"]) for row in clean_rows + noisy_rows
  )
  clean_expected = (
    len(ranges_km) * len(bearings_deg) * len(accelerations_x_mps2) * len(apn_gains)
  )
  noisy_expected = (
    len(noisy_seeds)
    * len(NOISY_BEARINGS_DEG)
    * len(NOISY_ACCELERATIONS_X_MPS2)
    * len(apn_gains)
    if include_noisy
    else 0
  )
  stage4_gates = {
    "clean_matrix_complete": len(clean_rows) == clean_expected,
    "resolved_runtime_matches_requested_tuning": resolved_mismatch_count == 0,
    "all_maneuver_runs_observe_valid_acceleration": all(
      row["acceleration_valid_observed"] for row in maneuver_clean
    ),
    "clean_acceleration_rmse_within_limit": max(
      row["acceleration_rmse_mps2"] for row in maneuver_clean
    ) <= TRACKER_GATES["clean_max_acceleration_rmse_mps2"],
    "clean_terminal_acceleration_error_within_limit": max(
      row["terminal_acceleration_error_mps2"] for row in maneuver_clean
    ) <= TRACKER_GATES["clean_max_terminal_acceleration_error_mps2"],
    "constant_velocity_false_acceleration_within_limit": max(
      row["max_estimated_acceleration_mps2"] for row in constant_velocity_clean
    ) <= TRACKER_GATES["constant_velocity_max_false_acceleration_mps2"],
    "constant_velocity_apn_is_zero": max(
      row["max_apn_acceleration_mps2"] for row in constant_velocity_clean
    ) <= TRACKER_GATES["zero_truth_max_apn_acceleration_mps2"],
    "maneuver_apn_is_identifiable": min(
      row["max_apn_acceleration_mps2"] for row in nonzero_gain_maneuver
    ) >= TRACKER_GATES["maneuver_min_identifiable_apn_acceleration_mps2"],
    "component_sum_closes": max(
      row["max_component_sum_error_mps2"] for row in clean_rows
    ) <= TRACKER_GATES["max_component_sum_error_mps2"],
    "mirror_nearest_distance_within_limit": _mirror_error(clean_rows)
    <= TRACKER_GATES["max_mirror_nearest_distance_error_m"],
    "lateral_acceleration_limit_respected": max(
      row["max_achieved_lateral_g"] for row in clean_rows
    ) <= TRACKER_GATES["max_achieved_lateral_g"],
  }
  noisy_tracker_rmse_max = max(
    (row["acceleration_rmse_mps2"] for row in noisy_rows), default=math.inf
  )
  noisy_tracker_peak_max = max(
    (row["max_estimated_acceleration_mps2"] for row in noisy_rows), default=math.inf
  )
  stage5_gates = {
    "noisy_holdout_complete": include_noisy and len(noisy_rows) == noisy_expected,
    "all_noisy_runs_observe_valid_acceleration": bool(noisy_rows) and all(
      row["acceleration_valid_observed"] for row in noisy_rows
    ),
    "noisy_acceleration_rmse_within_limit": noisy_tracker_rmse_max
    <= NOISY_PROMOTION_GATES["max_acceleration_rmse_mps2"],
    "noisy_acceleration_peak_within_limit": noisy_tracker_peak_max
    <= NOISY_PROMOTION_GATES["max_estimated_acceleration_mps2"],
    "nonzero_apn_gain_has_clear_net_benefit": bool(beneficial_gains),
  }
  stage4_passed = all(stage4_gates.values())
  stage5_passed = all(stage5_gates.values())
  config_backed_rows: list[dict[str, Any]] = []
  config_backed_confirmation = {
    "attempted": False,
    "passed": False,
    "selected_apn_gain": selected_gain,
    "gates": {
      "config_backed_matrix_complete": False,
      "resolved_runtime_matches_selected_tuple": False,
      "config_backed_matches_override_evidence": False,
    },
    "limits": {
      "max_nearest_distance_delta_m": 1.0e-9,
      "max_acceleration_rmse_delta_mps2": 1.0e-9,
    },
    "observed": {
      "max_nearest_distance_delta_m": math.inf,
      "max_acceleration_rmse_delta_mps2": math.inf,
    },
  }
  if include_config_backed_confirmation and stage4_passed and stage5_passed:
    config_backed_clean = [
      _run(
        tier="config_backed_clean",
        range_km=range_km,
        bearing_deg=bearing_deg,
        target_accel_x_mps2=acceleration,
        apn_gain=selected_gain,
        seed=NOISY_SEEDS[0],
        noisy=False,
        runner=runner,
        apply_guidance_overrides=False,
      )
      for range_km in ranges_km
      for bearing_deg in bearings_deg
      for acceleration in accelerations_x_mps2
    ]
    config_backed_noisy = [
      _run(
        tier="config_backed_noisy",
        range_km=NOISY_RANGE_KM,
        bearing_deg=bearing_deg,
        target_accel_x_mps2=acceleration,
        apn_gain=selected_gain,
        seed=seed,
        noisy=True,
        runner=runner,
        apply_guidance_overrides=False,
      )
      for seed in noisy_seeds
      for bearing_deg in NOISY_BEARINGS_DEG
      for acceleration in NOISY_ACCELERATIONS_X_MPS2
    ]
    config_backed_rows = config_backed_clean + config_backed_noisy
    selected_rows = [
      row for row in clean_rows + noisy_rows if row["apn_gain"] == selected_gain
    ]
    parity = _config_backed_parity(config_backed_rows, selected_rows)
    config_expected = (
      len(ranges_km) * len(bearings_deg) * len(accelerations_x_mps2)
      + len(noisy_seeds) * len(NOISY_BEARINGS_DEG) * len(NOISY_ACCELERATIONS_X_MPS2)
    )
    config_gates = {
      "config_backed_matrix_complete": len(config_backed_rows) == config_expected,
      "resolved_runtime_matches_selected_tuple": all(
        not row["resolved_runtime_mismatch"] for row in config_backed_rows
      ),
      "config_backed_matches_override_evidence": (
        parity["max_nearest_distance_delta_m"] <= 1.0e-9
        and parity["max_acceleration_rmse_delta_mps2"] <= 1.0e-9
      ),
    }
    config_backed_confirmation = {
      "attempted": True,
      "passed": all(config_gates.values()),
      "selected_apn_gain": selected_gain,
      "gates": config_gates,
      "limits": {
        "max_nearest_distance_delta_m": 1.0e-9,
        "max_acceleration_rmse_delta_mps2": 1.0e-9,
      },
      "observed": parity,
    }
  config_backed_passed = bool(config_backed_confirmation["passed"])
  p10_complete = stage4_passed and stage5_passed and config_backed_passed
  return {
    "schema_version": SCHEMA_VERSION,
    "status": (
      "maneuver_apn_config_backed_admission_passed"
      if p10_complete
      else "maneuver_apn_candidate_selected_default_promotion_ready"
      if stage4_passed and stage5_passed
      else "maneuver_tracker_structural_pass_apn_promotion_held"
      if stage4_passed
      else "maneuver_apn_structural_admission_failed"
    ),
    "generated_on": GENERATED_ON,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "authority_boundary": {
      "engineering_synthetic_only": True,
      "real_weapon_performance_authority": False,
      "pk_authority": False,
      "default_promotion_authority": config_backed_passed,
    },
    "production_mechanism_tuning": dict(PRODUCTION_MECHANISM_TUNING),
    "matrix": {
      "clean": {
        "ranges_km": list(ranges_km),
        "bearings_deg": list(bearings_deg),
        "target_accelerations_x_mps2": list(accelerations_x_mps2),
        "apn_gains": list(apn_gains),
        "expected_run_count": clean_expected,
        "acceleration_stable_start_time_s": ACCELERATION_STABLE_START_TIME_S,
      },
      "noisy_holdout": {
        "measurement_period_s": 0.05,
        "bearing_noise_std_deg": 0.2,
        "range_noise_std_m": 10.0,
        "range_km": NOISY_RANGE_KM,
        "bearings_deg": list(NOISY_BEARINGS_DEG),
        "target_accelerations_x_mps2": list(NOISY_ACCELERATIONS_X_MPS2),
        "seeds": list(noisy_seeds),
        "expected_run_count": noisy_expected,
        "acceleration_stable_start_time_s": ACCELERATION_STABLE_START_TIME_S,
      },
    },
    "counts": {
      "clean_run_count": len(clean_rows),
      "noisy_run_count": len(noisy_rows),
      "config_backed_run_count": len(config_backed_rows),
      "total_run_count": len(clean_rows) + len(noisy_rows) + len(config_backed_rows),
      "resolved_runtime_mismatch_count": resolved_mismatch_count,
    },
    "stage4_structural_admission": {
      "passed": stage4_passed,
      "gates": stage4_gates,
      "limits": dict(TRACKER_GATES),
      "observed": {
        "max_clean_acceleration_rmse_mps2": max(
          row["acceleration_rmse_mps2"] for row in maneuver_clean
        ),
        "max_clean_terminal_acceleration_error_mps2": max(
          row["terminal_acceleration_error_mps2"] for row in maneuver_clean
        ),
        "max_constant_velocity_false_acceleration_mps2": max(
          row["max_estimated_acceleration_mps2"] for row in constant_velocity_clean
        ),
        "max_constant_velocity_apn_acceleration_mps2": max(
          row["max_apn_acceleration_mps2"] for row in constant_velocity_clean
        ),
        "min_maneuver_apn_acceleration_mps2": min(
          row["max_apn_acceleration_mps2"] for row in nonzero_gain_maneuver
        ),
        "max_component_sum_error_mps2": max(
          row["max_component_sum_error_mps2"] for row in clean_rows
        ),
        "max_mirror_nearest_distance_error_m": _mirror_error(clean_rows),
        "max_achieved_lateral_g": max(
          row["max_achieved_lateral_g"] for row in clean_rows
        ),
      },
    },
    "stage5_apn_selection": {
      "passed": stage5_passed,
      "gates": stage5_gates,
      "limits": dict(NOISY_PROMOTION_GATES),
      "observed": {
        "max_noisy_acceleration_rmse_mps2": noisy_tracker_rmse_max,
        "max_noisy_estimated_acceleration_mps2": noisy_tracker_peak_max,
      },
      "selected_apn_gain": selected_gain,
      "decision": (
        "select_lowest_clear_net_benefit_candidate"
        if beneficial_gains
        else "retain_apn_gain_zero_no_clear_net_benefit"
      ),
      "clear_net_benefit_gains": beneficial_gains,
      "default_promotion_ready": stage5_passed,
    },
    "config_backed_confirmation": config_backed_confirmation,
    "admission": {
      "maneuver_tracker_structural_admission": "passed" if stage4_passed else "failed",
      "apn_mechanism_identifiability": (
        "passed" if stage4_gates["maneuver_apn_is_identifiable"] else "failed"
      ),
      "noisy_acceleration_authority": (
        "passed"
        if stage5_gates["noisy_acceleration_rmse_within_limit"]
        and stage5_gates["noisy_acceleration_peak_within_limit"]
        else "held"
      ),
      "apn_default_promotion": (
        "passed" if config_backed_passed else "ready" if stage5_passed else "held"
      ),
      "p10_complete": p10_complete,
    },
    "clean_candidate_summary": clean_candidates,
    "noisy_candidate_summary": noisy_candidates,
    "clean_runs": clean_rows,
    "noisy_runs": noisy_rows,
    "config_backed_runs": config_backed_rows,
  }


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _git_blob_sha256(path: Path, revision: str = "HEAD") -> str:
  relative = path.resolve().relative_to(REPO_ROOT).as_posix()
  result = subprocess.run(
    ["git", "show", f"{revision}:{relative}"],
    cwd=REPO_ROOT,
    capture_output=True,
    check=False,
  )
  return hashlib.sha256(result.stdout).hexdigest() if result.returncode == 0 else ""


def _git_value(*args: str) -> str:
  result = subprocess.run(
    ["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False
  )
  return result.stdout.strip() if result.returncode == 0 else ""


def _valid_publication_uri(uri: str | None) -> bool:
  value = str(uri or "").strip()
  if not value or any(char.isspace() for char in value):
    return False
  parsed = urlparse(value)
  return bool(
    (parsed.scheme == "https" and parsed.netloc)
    or (parsed.scheme == "file" and parsed.path)
  )


def _read_uri_bytes(uri: str) -> bytes:
  if not _valid_publication_uri(uri):
    raise ValueError(f"unsupported publication URI: {uri!r}")
  with urlopen(uri, timeout=10.0) as response:  # noqa: S310 - schemes checked above
    return response.read()


def _published_artifact_blocker(
  artifact_index_uri: str,
  expected_artifacts: dict[str, dict[str, Any]],
) -> str | None:
  try:
    index = json.loads(_read_uri_bytes(artifact_index_uri).decode("utf-8"))
  except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
    return "artifact_index_unretrievable"
  if index.get("schema_version") != ARTIFACT_INDEX_SCHEMA_VERSION:
    return "artifact_index_schema_mismatch"
  indexed_artifacts = index.get("artifacts")
  if not isinstance(indexed_artifacts, dict):
    return "artifact_index_invalid"
  for key in PUBLISHED_ARTIFACT_KEYS:
    expected = expected_artifacts.get(key)
    indexed = indexed_artifacts.get(key)
    if not isinstance(expected, dict) or not isinstance(indexed, dict):
      return "artifact_index_incomplete"
    if (
      indexed.get("sha256") != expected.get("sha256")
      or indexed.get("bytes") != expected.get("bytes")
    ):
      return "artifact_index_digest_mismatch"
    artifact_uri = str(indexed.get("uri", "") or "")
    try:
      payload = _read_uri_bytes(artifact_uri)
    except (OSError, ValueError):
      return "published_artifact_unretrievable"
    if (
      len(payload) != expected["bytes"]
      or hashlib.sha256(payload).hexdigest() != expected["sha256"]
    ):
      return "published_artifact_digest_mismatch"
  return None


def _runtime_attestation_blocker(
  runtime_attestation_uri: str,
  *,
  git_head: str,
  ef_py_sha256: str,
) -> str | None:
  try:
    attestation = json.loads(
      _read_uri_bytes(runtime_attestation_uri).decode("utf-8")
    )
  except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
    return "runtime_build_attestation_unretrievable"
  if attestation.get("schema_version") != RUNTIME_ATTESTATION_SCHEMA_VERSION:
    return "runtime_build_attestation_schema_mismatch"
  if (
    attestation.get("git_head") != git_head
    or attestation.get("ef_py_sha256") != ef_py_sha256
  ):
    return "runtime_build_attestation_mismatch"
  return None


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
  columns = [
    "tier", "case_id", "range_km", "bearing_deg", "target_accel_x_mps2",
    "apn_gain", "seed", "nearest_distance_m", "rho_fuze", "entered_R_fuze",
    "max_achieved_lateral_g", "stable_trace_count", "acceleration_valid_observed",
    "acceleration_rmse_mps2", "terminal_acceleration_error_mps2",
    "max_estimated_acceleration_mps2", "max_apn_acceleration_mps2",
    "max_component_sum_error_mps2",
  ]
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)


def _write_candidate_csv(path: Path, report: dict[str, Any]) -> None:
  rows = []
  for tier, field in (
    ("clean_stage4", "clean_candidate_summary"),
    ("noisy_stage5_holdout", "noisy_candidate_summary"),
  ):
    for row in report[field]:
      rows.append({"tier": tier, **row})
  columns = ["tier", *list(rows[0].keys())[1:]] if rows else ["tier"]
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)


def _bundle_admission(
  report: dict[str, Any],
  *,
  worktree_porcelain: str,
  artifact_uri: str | None,
  artifact_index_uri: str | None,
  runtime_attestation_uri: str | None,
  retention_owner: str,
  expected_artifacts: dict[str, dict[str, Any]],
  git_head: str,
  ef_py_sha256: str,
) -> dict[str, Any]:
  blockers = []
  if not bool(report["admission"]["p10_complete"]):
    blockers.append("simulation_gates_failed")
  if worktree_porcelain:
    blockers.append("generator_worktree_not_clean")
  if not artifact_uri:
    blockers.append("raw_packets_not_published")
  elif not _valid_publication_uri(artifact_uri):
    blockers.append("artifact_uri_invalid")
  if not artifact_index_uri:
    blockers.append("artifact_index_missing")
  else:
    artifact_blocker = _published_artifact_blocker(
      artifact_index_uri,
      expected_artifacts,
    )
    if artifact_blocker:
      blockers.append(artifact_blocker)
  if not runtime_attestation_uri:
    blockers.append("runtime_build_attestation_missing")
  else:
    runtime_blocker = _runtime_attestation_blocker(
      runtime_attestation_uri,
      git_head=git_head,
      ef_py_sha256=ef_py_sha256,
    )
    if runtime_blocker:
      blockers.append(runtime_blocker)
  if not retention_owner.strip():
    blockers.append("retention_owner_missing")
  return {
    "promotion_status": "passed" if not blockers else "held",
    "blockers": blockers,
  }


def conclusions_zh(
  report: dict[str, Any], *, bundle_admission: dict[str, Any] | None = None
) -> str:
  stage4 = report["stage4_structural_admission"]
  stage5 = report["stage5_apn_selection"]
  admission = report["admission"]
  observed4 = stage4["observed"]
  observed5 = stage5["observed"]
  config_backed = report["config_backed_confirmation"]
  noisy_acceleration_passed = bool(
    stage5["gates"]["noisy_holdout_complete"]
    and stage5["gates"]["all_noisy_runs_observe_valid_acceleration"]
    and stage5["gates"]["noisy_acceleration_rmse_within_limit"]
    and stage5["gates"]["noisy_acceleration_peak_within_limit"]
  )
  bundle_admission = bundle_admission or {
    "promotion_status": "held",
    "blockers": ["provenance_not_evaluated"],
  }
  promotion_passed = bundle_admission["promotion_status"] == "passed"
  return "\n".join(
    [
      "# P10 机动目标 / APN 准入结论",
      "",
      f"- 计算门状态：`{report['status']}`。",
      f"- 证据准入状态：`{bundle_admission['promotion_status']}`；"
      f"blockers：`{bundle_admission['blockers']}`。",
      f"- clean stage-4 structural admission：`{stage4['passed']}`；"
      f"CVA 最大稳定加速度 RMSE 为 "
      f"`{observed4['max_clean_acceleration_rmse_mps2']:.3f} m/s²`，末值最大误差 "
      f"`{observed4['max_clean_terminal_acceleration_error_mps2']:.3f} m/s²`。",
      f"- 匀速目标最大伪加速度为 "
      f"`{observed4['max_constant_velocity_false_acceleration_mps2']:.3e} m/s²`；"
      f"匀速目标最大 APN 分量为 "
      f"`{observed4['max_constant_velocity_apn_acceleration_mps2']:.3e} m/s²`。",
      f"- 非零机动的最小可辨识 APN 分量为 "
      f"`{observed4['min_maneuver_apn_acceleration_mps2']:.3f} m/s²`；"
      f"镜像最近距离最大误差为 "
      f"`{observed4['max_mirror_nearest_distance_error_m']:.6f} m`。",
      f"- noisy acceleration authority：`{'passed' if noisy_acceleration_passed else 'held'}`；"
      f"最大加速度 RMSE "
      f"`{observed5['max_noisy_acceleration_rmse_mps2']:.3f} m/s²`，"
      f"最大估计加速度 `{observed5['max_noisy_estimated_acceleration_mps2']:.3f} m/s²`。",
      f"- stage-5 APN selection：`{stage5['passed']}`；非零增益明确净收益："
      f"`{stage5['gates']['nonzero_apn_gain_has_clear_net_benefit']}`。",
      f"- APN gain 选择：`{stage5['selected_apn_gain']:g}`；"
      f"`{stage5['decision']}`。",
      f"- config-backed 无 override 复验：`{config_backed['passed']}`；"
      f"共 `{report['counts']['config_backed_run_count']}` runs，最近距最大差 "
      f"`{config_backed['observed']['max_nearest_distance_delta_m']:.3e} m`。",
      f"- P10 computational gates complete：`{admission['p10_complete']}`；"
      f"APN default promotion：`{'passed' if promotion_passed else 'held'}`。",
      "",
      "该结果只形成 synthetic engineering evidence。它不构成真实 AIM-120 性能、Pk、"
      "默认武器参数或交战规则权威。",
      "",
    ]
  )


def write_bundle(
  report: dict[str, Any],
  *,
  output_dir: Path,
  stem: str,
  artifact_uri: str | None = None,
  artifact_index_uri: str | None = None,
  runtime_attestation_uri: str | None = None,
  retention_owner: str = DEFAULT_RETENTION_OWNER,
) -> dict[str, str]:
  source_worktree_porcelain = _git_value("status", "--short")
  git_head = _git_value("rev-parse", "HEAD")
  ef_py_path = Path(probe.ef_py.__file__).resolve()
  ef_py_sha256 = _sha256(ef_py_path)
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "report_json": output_dir / f"{stem}.json",
    "clean_runs_csv": output_dir / f"{stem}_clean_runs.csv",
    "noisy_runs_csv": output_dir / f"{stem}_noisy_runs.csv",
    "config_backed_runs_csv": output_dir / f"{stem}_config_backed_runs.csv",
    "candidate_summary_csv": output_dir / f"{stem}_candidate_summary.csv",
    "conclusions_zh_md": output_dir / f"{stem}_conclusions.zh.md",
    "manifest_json": output_dir / f"{stem}_manifest.json",
  }
  paths["report_json"].write_text(
    json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
  )
  _write_csv(paths["clean_runs_csv"], report["clean_runs"])
  _write_csv(paths["noisy_runs_csv"], report["noisy_runs"])
  _write_csv(paths["config_backed_runs_csv"], report["config_backed_runs"])
  _write_candidate_csv(paths["candidate_summary_csv"], report)
  expected_artifacts = {
    key: {
      "path": str(paths[key].resolve().relative_to(REPO_ROOT)),
      "sha256": _sha256(paths[key]),
      "bytes": paths[key].stat().st_size,
    }
    for key in PUBLISHED_ARTIFACT_KEYS
  }
  bundle_admission = _bundle_admission(
    report,
    worktree_porcelain=source_worktree_porcelain,
    artifact_uri=artifact_uri,
    artifact_index_uri=artifact_index_uri,
    runtime_attestation_uri=runtime_attestation_uri,
    retention_owner=retention_owner,
    expected_artifacts=expected_artifacts,
    git_head=git_head,
    ef_py_sha256=ef_py_sha256,
  )
  paths["conclusions_zh_md"].write_text(
    conclusions_zh(report, bundle_admission=bundle_admission), encoding="utf-8"
  )
  manifest = {
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "report_schema_version": SCHEMA_VERSION,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "tool": {
      "path": str(Path(__file__).resolve().relative_to(REPO_ROOT)),
      "sha256": _sha256(Path(__file__)),
    },
    "git": {
      "head": git_head,
      "branch": _git_value("branch", "--show-current"),
      "worktree_porcelain": source_worktree_porcelain,
    },
    "admission": bundle_admission,
    "retention": {
      "owner": retention_owner,
      "raw_packet_root": str(output_dir.resolve().relative_to(REPO_ROOT)),
      "retrieval_status": (
        "verified"
        if not any(
          blocker.startswith(("artifact_", "published_artifact_", "raw_packets_"))
          for blocker in bundle_admission["blockers"]
        )
        else "unverified"
      ),
      "artifact_uri": artifact_uri,
      "artifact_index_uri": artifact_index_uri,
      "runtime_attestation_uri": runtime_attestation_uri,
    },
    "runtime": {
      "ef_py_path": str(ef_py_path),
      "ef_py_sha256": ef_py_sha256,
      "aim120_definition_path": str(DEFAULT_AIM120_DEFINITION.resolve()),
      "aim120_definition_sha256": _sha256(DEFAULT_AIM120_DEFINITION),
      "aim120_source_blob_sha256": _git_blob_sha256(DEFAULT_AIM120_DEFINITION),
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


def _tuple_or_default(values: list[Any], default: tuple[Any, ...]) -> tuple[Any, ...]:
  return tuple(values) if values else default


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--stem", default=DEFAULT_STEM)
  parser.add_argument("--range-km", type=float, action="append", default=[])
  parser.add_argument("--bearing-deg", type=float, action="append", default=[])
  parser.add_argument("--target-accel-x-mps2", type=float, action="append", default=[])
  parser.add_argument("--apn-gain", type=float, action="append", default=[])
  parser.add_argument("--seed", type=int, action="append", default=[])
  parser.add_argument("--skip-noisy", action="store_true")
  parser.add_argument("--skip-config-backed-confirmation", action="store_true")
  parser.add_argument("--artifact-uri")
  parser.add_argument("--artifact-index-uri")
  parser.add_argument("--runtime-attestation-uri")
  parser.add_argument("--retention-owner", default=DEFAULT_RETENTION_OWNER)
  parser.add_argument("--strict", action="store_true")
  return parser


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  probe.ef_py.set_log_level("error")
  report = build_report(
    ranges_km=_tuple_or_default(args.range_km, RANGES_KM),
    bearings_deg=_tuple_or_default(args.bearing_deg, BEARINGS_DEG),
    accelerations_x_mps2=_tuple_or_default(
      args.target_accel_x_mps2, TARGET_ACCELERATIONS_X_MPS2
    ),
    apn_gains=_tuple_or_default(args.apn_gain, APN_GAINS),
    noisy_seeds=_tuple_or_default(args.seed, NOISY_SEEDS),
    include_noisy=not bool(args.skip_noisy),
    include_config_backed_confirmation=(
      not bool(args.skip_noisy) and not bool(args.skip_config_backed_confirmation)
    ),
  )
  artifacts = write_bundle(
    report,
    output_dir=args.output_dir,
    stem=str(args.stem),
    artifact_uri=args.artifact_uri,
    artifact_index_uri=args.artifact_index_uri,
    runtime_attestation_uri=args.runtime_attestation_uri,
    retention_owner=str(args.retention_owner),
  )
  manifest = json.loads(Path(artifacts["manifest_json"]).read_text(encoding="utf-8"))
  print(
    json.dumps(
      {
        "status": report["status"],
        "admission": report["admission"],
        "counts": report["counts"],
        "stage4": report["stage4_structural_admission"],
        "stage5": report["stage5_apn_selection"],
        "artifacts": artifacts,
      },
      ensure_ascii=False,
      allow_nan=False,
    )
  )
  promotion_passed = manifest["admission"]["promotion_status"] == "passed"
  return 1 if bool(args.strict) and not promotion_passed else 0


if __name__ == "__main__":
  raise SystemExit(main())
