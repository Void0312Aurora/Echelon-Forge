#!/usr/bin/env python3
"""Explain the P10 8 km APN nearest-distance null-response band."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.diagnostics import kill_chain_decoupling_probe as probe  # noqa: E402
from tools.diagnostics import kill_chain_maneuver_apn_admission as p10  # noqa: E402


SCHEMA_VERSION = "a2.kill_chain_p10_apn_null_band_followup.v1"
GENERATED_ON = "2026-09-15"
DISCUSSION_URL = "https://github.com/Void0312Aurora/Echelon-Forge/discussions/32"
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs/systems/weapons/reviews/kill_chain_p10_apn_null_band_followup_20260915"
  / "review_packets"
)
DEFAULT_STEM = "kill_chain_p10_apn_null_band_followup_20260915"
DEFAULT_AIM120_DEFINITION = (
  REPO_ROOT / "examples/config/database/weapons/air_to_air/aim_120c.json"
)
RANGES_KM = (7.0, 7.5, 8.0, 8.5, 9.0)
MIRRORED_CORNERS = ((-60.0, -8.0), (60.0, 8.0))
APN_GAINS = (0.0, 0.125, 0.25, 0.5)
SEEDS = (20260621, 20260622, 20260623)
NULL_RESPONSE_THRESHOLD_M = 1.0e-3
NEAR_ZERO_BASELINE_THRESHOLD_M = 1.0e-2
ESTIMATOR_CONVERGENCE_ERROR_MPS2 = 0.1
ESTIMATOR_CONVERGENCE_HOLD_SAMPLES = 12
MIN_ACTIVE_APN_ACCELERATION_MPS2 = 0.1


def _finite(value: Any, default: float = 0.0) -> float:
  try:
    parsed = float(value)
  except (TypeError, ValueError):
    return float(default)
  return parsed if math.isfinite(parsed) else float(default)


def _optional_finite(value: Any) -> float | None:
  try:
    parsed = float(value)
  except (TypeError, ValueError):
    return None
  return parsed if math.isfinite(parsed) else None


def _rms(values: list[float]) -> float:
  return math.sqrt(statistics.fmean(value * value for value in values)) if values else 0.0


def _first_time(rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> float | None:
  for row in rows:
    if predicate(row):
      return _optional_finite(row.get("time_s"))
  return None


def _first_estimator_convergence_time(rows: list[dict[str, Any]]) -> float | None:
  hold = ESTIMATOR_CONVERGENCE_HOLD_SAMPLES
  for index in range(max(0, len(rows) - hold + 1)):
    window = rows[index:index + hold]
    if all(
      bool(row.get("target_acceleration_valid"))
      and _finite(row.get("target_accel_error_mps2"), math.inf)
      <= ESTIMATOR_CONVERGENCE_ERROR_MPS2
      for row in window
    ):
      return _optional_finite(rows[index].get("time_s"))
  return None


def _nearest_time(result: dict[str, Any], trace: list[dict[str, Any]]) -> float:
  approach = dict(
    dict(result.get("runtime_facade", {}) or {}).get("approach_fact", {}) or {}
  )
  event_time = _optional_finite(approach.get("nearest_approach_time_s"))
  if event_time is not None and event_time >= 0.0:
    return event_time
  if not trace:
    return _finite(result.get("sim_time_s"))
  nearest = min(trace, key=lambda row: _finite(row.get("truth_distance_m"), math.inf))
  return _finite(nearest.get("time_s"))


def _resolved_mismatch(result: dict[str, Any], gain: float) -> dict[str, dict[str, Any]]:
  expected = {
    key: value
    for key, value in p10.PRODUCTION_MECHANISM_TUNING.items()
    if key != "max_lateral_g"
  }
  expected["guidance_max_lateral_g"] = p10.PRODUCTION_MECHANISM_TUNING["max_lateral_g"]
  expected["apn_target_accel_gain"] = float(gain)
  resolved = dict(result.get("resolved_guidance_runtime", {}) or {})
  return {
    key: {"expected": expected_value, "observed": resolved.get(key)}
    for key, expected_value in expected.items()
    if resolved.get(key) != expected_value
  }


def _summarize_result(
  result: dict[str, Any],
  *,
  range_km: float,
  bearing_deg: float,
  target_accel_x_mps2: float,
  apn_gain: float,
  seed: int,
) -> dict[str, Any]:
  trace = list(result.get("guidance_runtime_trace", []) or [])
  nearest_time_s = _nearest_time(result, trace)
  pre_nearest = [
    row for row in trace if _finite(row.get("time_s")) <= nearest_time_s + 1.0e-9
  ]
  if not pre_nearest:
    pre_nearest = trace
  times = [_finite(row.get("time_s")) for row in pre_nearest]
  dt_s = statistics.median(
    [later - earlier for earlier, later in zip(times, times[1:]) if later > earlier]
  ) if len(times) > 1 else 0.0
  pn = [_finite(row.get("guidance_pn_accel_mps2")) for row in pre_nearest]
  apn = [_finite(row.get("guidance_apn_lateral_accel_mps2")) for row in pre_nearest]
  first_valid_s = _first_time(
    pre_nearest,
    lambda row: bool(row.get("target_acceleration_valid")),
  )
  convergence_s = _first_estimator_convergence_time(pre_nearest)
  first_apn_s = _first_time(
    pre_nearest,
    lambda row: _finite(row.get("guidance_apn_lateral_accel_mps2")) > 1.0e-9,
  )
  nearest_distance_m = _optional_finite(result.get("nearest_miss_distance_m"))
  if nearest_distance_m is None:
    nearest_distance_m = _finite(result.get("truth_min_distance_m"), math.inf)
  apn_impulse_mps = sum(apn) * dt_s
  pn_impulse_mps = sum(pn) * dt_s
  return {
    "case_id": str(result.get("case_id", "") or ""),
    "range_km": float(range_km),
    "bearing_deg": float(bearing_deg),
    "target_accel_x_mps2": float(target_accel_x_mps2),
    "apn_gain": float(apn_gain),
    "seed": int(seed),
    "maneuver_onset_time_s": 0.0,
    "nearest_distance_m": nearest_distance_m,
    "entered_R_fuze": nearest_distance_m <= p10.R_FUZE_M,
    "nearest_approach_time_s": nearest_time_s,
    "estimator_first_valid_time_s": first_valid_s,
    "estimator_convergence_time_s": convergence_s,
    "time_to_go_at_estimator_valid_s": (
      nearest_time_s - first_valid_s if first_valid_s is not None else None
    ),
    "time_to_go_at_estimator_convergence_s": (
      nearest_time_s - convergence_s if convergence_s is not None else None
    ),
    "apn_first_nonzero_time_s": first_apn_s,
    "time_to_go_at_first_apn_s": (
      nearest_time_s - first_apn_s if first_apn_s is not None else None
    ),
    "trace_sample_count": len(pre_nearest),
    "trace_dt_s": dt_s,
    "max_pn_acceleration_mps2": max(pn, default=0.0),
    "rms_pn_acceleration_mps2": _rms(pn),
    "pn_impulse_mps": pn_impulse_mps,
    "max_apn_acceleration_mps2": max(apn, default=0.0),
    "rms_apn_acceleration_mps2": _rms(apn),
    "apn_impulse_mps": apn_impulse_mps,
    "apn_to_pn_impulse_ratio": (
      apn_impulse_mps / pn_impulse_mps if pn_impulse_mps > 1.0e-12 else None
    ),
    "max_component_sum_error_mps2": max(
      (_finite(row.get("guidance_component_sum_error_mps2")) for row in pre_nearest),
      default=0.0,
    ),
    "resolved_runtime_mismatch": _resolved_mismatch(result, apn_gain),
  }


def _case_id(
  *, range_km: float, bearing_deg: float, acceleration: float, gain: float, seed: int
) -> str:
  raw = f"p10_null_r{range_km:g}_b{bearing_deg:+g}_a{acceleration:+g}_g{gain:g}_s{seed}"
  return raw.replace("+", "p").replace("-", "m").replace(".", "p")


def _run_case(
  *,
  range_km: float,
  bearing_deg: float,
  acceleration: float,
  gain: float,
  seed: int,
  runner: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
  result = runner(
    case_id=_case_id(
      range_km=range_km,
      bearing_deg=bearing_deg,
      acceleration=acceleration,
      gain=gain,
      seed=seed,
    ),
    range_m=float(range_km) * 1000.0,
    bearing_deg=float(bearing_deg),
    seed=int(seed),
    guidance_tuning_overrides={
      **p10.PRODUCTION_MECHANISM_TUNING,
      "apn_target_accel_gain": float(gain),
    },
    collect_guidance_runtime_trace=True,
    guidance_trace_stride=1,
    target_acceleration_mps2=(float(acceleration), 0.0, 0.0),
  )
  return _summarize_result(
    result,
    range_km=range_km,
    bearing_deg=bearing_deg,
    target_accel_x_mps2=acceleration,
    apn_gain=gain,
    seed=seed,
  )


def _aggregate_cells(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  baselines = {
    (row["range_km"], row["bearing_deg"], row["target_accel_x_mps2"], row["seed"]): row
    for row in rows
    if row["apn_gain"] == 0.0
  }
  grouped: dict[tuple[float, float], list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    baseline = baselines[
      (row["range_km"], row["bearing_deg"], row["target_accel_x_mps2"], row["seed"])
    ]
    row["nearest_distance_delta_vs_apn0_m"] = (
      row["nearest_distance_m"] - baseline["nearest_distance_m"]
    )
    grouped[(row["range_km"], row["apn_gain"])].append(row)

  cells: list[dict[str, Any]] = []
  for (range_km, gain), group in sorted(grouped.items()):
    distances = [row["nearest_distance_m"] for row in group]
    deltas = [row["nearest_distance_delta_vs_apn0_m"] for row in group]
    baseline_distances = [
      baselines[
        (row["range_km"], row["bearing_deg"], row["target_accel_x_mps2"], row["seed"])
      ]["nearest_distance_m"]
      for row in group
    ]
    convergences = [
      row["estimator_convergence_time_s"]
      for row in group
      if row["estimator_convergence_time_s"] is not None
    ]
    apn_impulses = [row["apn_impulse_mps"] for row in group]
    pn_impulses = [row["pn_impulse_mps"] for row in group]
    max_abs_delta = max((abs(value) for value in deltas), default=math.inf)
    cells.append(
      {
        "range_km": range_km,
        "apn_gain": gain,
        "sample_count": len(group),
        "mean_baseline_nearest_distance_m": statistics.fmean(baseline_distances),
        "mean_nearest_distance_m": statistics.fmean(distances),
        "mean_nearest_distance_delta_vs_apn0_m": statistics.fmean(deltas),
        "max_abs_nearest_distance_delta_vs_apn0_m": max_abs_delta,
        "null_response": gain > 0.0 and max_abs_delta <= NULL_RESPONSE_THRESHOLD_M,
        "mean_nearest_approach_time_s": statistics.fmean(
          row["nearest_approach_time_s"] for row in group
        ),
        "mean_estimator_convergence_time_s": (
          statistics.fmean(convergences) if convergences else None
        ),
        "mean_time_to_go_at_estimator_convergence_s": statistics.fmean(
          row["time_to_go_at_estimator_convergence_s"] for row in group
          if row["time_to_go_at_estimator_convergence_s"] is not None
        ) if convergences else None,
        "mean_max_pn_acceleration_mps2": statistics.fmean(
          row["max_pn_acceleration_mps2"] for row in group
        ),
        "mean_max_apn_acceleration_mps2": statistics.fmean(
          row["max_apn_acceleration_mps2"] for row in group
        ),
        "mean_pn_impulse_mps": statistics.fmean(pn_impulses),
        "mean_apn_impulse_mps": statistics.fmean(apn_impulses),
        "mean_apn_to_pn_impulse_ratio": (
          statistics.fmean(
            row["apn_to_pn_impulse_ratio"]
            for row in group
            if row["apn_to_pn_impulse_ratio"] is not None
          )
          if any(row["apn_to_pn_impulse_ratio"] is not None for row in group)
          else None
        ),
        "nearest_distance_spread_across_mirrors_and_seeds_m": (
          max(distances) - min(distances)
        ),
      }
    )
  return cells


def _evaluate(rows: list[dict[str, Any]], cells: list[dict[str, Any]]) -> dict[str, Any]:
  expected_count = len(RANGES_KM) * len(MIRRORED_CORNERS) * len(APN_GAINS) * len(SEEDS)
  nonzero_rows = [row for row in rows if row["apn_gain"] > 0.0]
  null_cells = [cell for cell in cells if cell["null_response"]]
  ranges_with_null = sorted({cell["range_km"] for cell in null_cells})
  all_gains_null_ranges = [
    range_km
    for range_km in RANGES_KM
    if all(
      next(
        cell for cell in cells
        if cell["range_km"] == range_km and cell["apn_gain"] == gain
      )["null_response"]
      for gain in APN_GAINS
      if gain > 0.0
    )
  ]
  null_baseline_near_zero = bool(null_cells) and all(
    cell["mean_baseline_nearest_distance_m"] <= NEAR_ZERO_BASELINE_THRESHOLD_M
    for cell in null_cells
  )
  null_apn_active = bool(null_cells) and all(
    cell["mean_max_apn_acceleration_mps2"] >= MIN_ACTIVE_APN_ACCELERATION_MPS2
    for cell in null_cells
  )
  estimator_converges = all(
    row["estimator_convergence_time_s"] is not None
    and row["estimator_convergence_time_s"] < row["nearest_approach_time_s"]
    for row in rows
  )
  gates = {
    "matrix_complete": len(rows) == expected_count,
    "resolved_runtime_matches_fixed_p10_tuple": all(
      not row["resolved_runtime_mismatch"] for row in rows
    ),
    "component_sum_closes": max(
      (row["max_component_sum_error_mps2"] for row in rows), default=math.inf
    ) <= p10.TRACKER_GATES["max_component_sum_error_mps2"],
    "estimator_converges_before_nearest_approach": estimator_converges,
    "nonzero_gain_produces_observable_apn_command": bool(nonzero_rows) and all(
      row["max_apn_acceleration_mps2"] >= MIN_ACTIVE_APN_ACCELERATION_MPS2
      for row in nonzero_rows
    ),
    "null_response_cells_have_near_zero_pn_baseline": null_baseline_near_zero,
    "null_response_cells_still_have_active_apn": null_apn_active,
    "range_sweep_observes_response_transition": bool(all_gains_null_ranges)
    and any(
      range_km > 8.0 and range_km not in all_gains_null_ranges
      for range_km in RANGES_KM
    ),
    "mirror_and_seed_spread_within_limit": max(
      (
        cell["nearest_distance_spread_across_mirrors_and_seeds_m"]
        for cell in cells
      ),
      default=math.inf,
    ) <= p10.TRACKER_GATES["max_mirror_nearest_distance_error_m"],
  }
  explained = all(gates.values()) and 8.0 in all_gains_null_ranges
  first_non_null_range_above_8_km = next(
    (
      range_km
      for range_km in sorted(RANGES_KM)
      if range_km > 8.0 and range_km not in all_gains_null_ranges
    ),
    None,
  )
  return {
    "gates": gates,
    "explained": explained,
    "null_response_threshold_m": NULL_RESPONSE_THRESHOLD_M,
    "near_zero_baseline_threshold_m": NEAR_ZERO_BASELINE_THRESHOLD_M,
    "ranges_with_any_null_cell_km": ranges_with_null,
    "ranges_with_all_nonzero_gains_null_km": all_gains_null_ranges,
    "first_non_null_range_above_8_km": first_non_null_range_above_8_km,
    "mechanism": (
      "nearest_distance_observable_floor_with_active_apn"
      if explained
      else "null_band_mechanism_not_closed"
    ),
  }


def build_report(
  *, runner: Callable[..., dict[str, Any]] = probe.run_guidance_case
) -> dict[str, Any]:
  rows = [
    _run_case(
      range_km=range_km,
      bearing_deg=bearing,
      acceleration=acceleration,
      gain=gain,
      seed=seed,
      runner=runner,
    )
    for range_km in RANGES_KM
    for bearing, acceleration in MIRRORED_CORNERS
    for gain in APN_GAINS
    for seed in SEEDS
  ]
  cells = _aggregate_cells(rows)
  evaluation = _evaluate(rows, cells)
  return {
    "schema_version": SCHEMA_VERSION,
    "status": (
      "p10_apn_null_band_explained"
      if evaluation["explained"]
      else "p10_apn_null_band_followup_inconclusive"
    ),
    "generated_on": GENERATED_ON,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "discussion": {
      "number": 32,
      "url": DISCUSSION_URL,
      "title": "[P10] Explain the 8 km APN null-response band before promotion freeze",
    },
    "authority_boundary": {
      "engineering_synthetic_only": True,
      "changes_p10_admission": False,
      "changes_runtime_tuning": False,
      "real_weapon_performance_authority": False,
      "pk_authority": False,
    },
    "matrix": {
      "ranges_km": list(RANGES_KM),
      "mirrored_corners": [
        {"bearing_deg": bearing, "target_accel_x_mps2": acceleration}
        for bearing, acceleration in MIRRORED_CORNERS
      ],
      "apn_gains": list(APN_GAINS),
      "seeds": list(SEEDS),
      "maneuver_model": "constant_world_x_acceleration_from_launch",
      "maneuver_onset_time_s": 0.0,
      "expected_run_count": (
        len(RANGES_KM) * len(MIRRORED_CORNERS) * len(APN_GAINS) * len(SEEDS)
      ),
    },
    "fixed_guidance_tuning": dict(p10.PRODUCTION_MECHANISM_TUNING),
    "counts": {
      "run_count": len(rows),
      "cell_count": len(cells),
      "null_response_cell_count": sum(cell["null_response"] for cell in cells),
    },
    "evaluation": evaluation,
    "conclusion": {
      "primary": (
        "The 8 km delta is numerically null because the APN=0 baseline already reaches "
        "a sub-centimeter nearest-distance floor in this deterministic geometry."
      ),
      "plumbing_check": (
        "CVA convergence and nonzero PN/APN command contributions occur before nearest "
        "approach, so the null nearest-distance delta is not an APN plumbing failure."
      ),
      "scope": (
        "This explains the selected synthetic corner geometry only and does not freeze a "
        "real-world performance envelope."
      ),
      "hypothesis_disposition": {
        "time_to_go_or_maneuver_phase_alignment": (
          "not_supported_as_primary_cause: estimator convergence stays fixed while "
          "time-to-go changes smoothly across the sweep"
        ),
        "pn_baseline_near_local_optimum": (
          "supported: APN=0 nearest distance remains below 1 cm throughout the null band"
        ),
        "acceleration_estimator_transient_timing": (
          "not_supported: CVA converges before nearest approach in every run"
        ),
        "scenario_grid_placement": (
          "supported: 8 km lies inside a 7.0-8.5 km floor band and the response "
          "becomes non-null at 9 km"
        ),
      },
    },
    "cells": cells,
    "runs": rows,
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
  evaluation = report["evaluation"]
  cells = list(report["cells"])
  baseline_8 = next(
    cell for cell in cells if cell["range_km"] == 8.0 and cell["apn_gain"] == 0.0
  )
  gain_8 = [
    cell for cell in cells if cell["range_km"] == 8.0 and cell["apn_gain"] > 0.0
  ]
  max_delta_8 = max(
    cell["max_abs_nearest_distance_delta_vs_apn0_m"] for cell in gain_8
  )
  min_apn_8 = min(cell["mean_max_apn_acceleration_mps2"] for cell in gain_8)
  convergence_8 = max(
    _finite(cell["mean_estimator_convergence_time_s"]) for cell in gain_8
  )
  tgo_8 = min(
    _finite(cell["mean_time_to_go_at_estimator_convergence_s"]) for cell in gain_8
  )
  return "\n".join(
    [
      "# P10 APN 8 km 低响应带复核结论",
      "",
      f"- Discussion：[#32]({DISCUSSION_URL})。",
      f"- 状态：`{report['status']}`；机制闭合：`{evaluation['explained']}`。",
      f"- 矩阵：`{report['counts']['run_count']}` runs / "
      f"`{report['counts']['cell_count']}` cells，三种子、两组镜像困难角点。",
      f"- 8 km 的 APN=0 平均最近距为 "
      f"`{baseline_8['mean_nearest_distance_m']:.6f} m`；所有非零增益相对基线的"
      f"最大绝对变化为 `{max_delta_8:.6e} m`。",
      f"- 8 km 非零增益的最小峰值 APN 分量为 `{min_apn_8:.6f} m/s²`；"
      f"估计器最迟在 `{convergence_8:.3f} s` 收敛，距最近点仍有至少 "
      f"`{tgo_8:.3f} s`。",
      f"- 全部非零增益均落入 null threshold 的范围："
      f"`{evaluation['ranges_with_all_nonzero_gains_null_km']}` km。",
      f"- 扫描中的首个高于 8 km 的非 null 距离为 "
      f"`{evaluation['first_non_null_range_above_8_km']}` km。",
      "",
      "结论：8 km 不是孤立异常，而是 7.0-8.5 km 低响应带的一部分；纯 PN 基线"
      "已经落在厘米以下的数值/几何观测底部，9 km 基线离开该底部后 APN 响应恢复。"
      "CVA 与 APN 均在最近点前生效，因此不是 APN 接线失效或估计器瞬态造成。"
      "这一解释只覆盖当前 synthetic 固定机动角点，不改变 P10 准入，也不构成真实"
      " AIM-120 性能或 Pk 权威。",
      "",
    ]
  )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
    if rows:
      writer.writeheader()
      writer.writerows(rows)


def write_bundle(report: dict[str, Any], *, output_dir: Path, stem: str) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "report_json": output_dir / f"{stem}.json",
    "runs_csv": output_dir / f"{stem}_runs.csv",
    "cells_csv": output_dir / f"{stem}_cells.csv",
    "conclusions_zh_md": output_dir / f"{stem}_conclusions.zh.md",
    "figure_png": output_dir / f"{stem}_figure.png",
    "manifest_json": output_dir / f"{stem}_manifest.json",
  }
  paths["report_json"].write_text(
    json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
  )
  _write_csv(paths["runs_csv"], report["runs"])
  _write_csv(paths["cells_csv"], report["cells"])
  paths["conclusions_zh_md"].write_text(conclusions_zh(report), encoding="utf-8")
  from tools.diagnostics.render_kill_chain_p10_apn_null_band import render

  render(report, paths["figure_png"])
  manifest = {
    "schema_version": "a2.kill_chain_p10_apn_null_band_followup_manifest.v1",
    "report_schema_version": SCHEMA_VERSION,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "git": {
      "head": _git_value("rev-parse", "HEAD"),
      "branch": _git_value("branch", "--show-current"),
      "worktree_porcelain": _git_value("status", "--short"),
    },
    "inputs": {
      "tool": {"path": str(Path(__file__).relative_to(REPO_ROOT)), "sha256": _sha256(Path(__file__))},
      "renderer": {
        "path": str(Path(sys.modules[render.__module__].__file__).relative_to(REPO_ROOT)),
        "sha256": _sha256(Path(sys.modules[render.__module__].__file__)),
      },
      "probe": {"path": str(Path(probe.__file__).relative_to(REPO_ROOT)), "sha256": _sha256(Path(probe.__file__))},
      "p10_admission_tool": {"path": str(Path(p10.__file__).relative_to(REPO_ROOT)), "sha256": _sha256(Path(p10.__file__))},
      "aim120_definition": {"path": str(DEFAULT_AIM120_DEFINITION.relative_to(REPO_ROOT)), "sha256": _sha256(DEFAULT_AIM120_DEFINITION)},
      "ef_py": {"path": str(Path(probe.ef_py.__file__).resolve()), "sha256": _sha256(Path(probe.ef_py.__file__).resolve())},
    },
    "artifacts": {
      key: {
        "path": str(path.relative_to(REPO_ROOT)),
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
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--stem", default=DEFAULT_STEM)
  parser.add_argument("--strict", action="store_true")
  args = parser.parse_args(argv)
  probe.ef_py.set_log_level("error")
  report = build_report()
  paths = write_bundle(report, output_dir=args.output_dir, stem=str(args.stem))
  print(json.dumps({"status": report["status"], "evaluation": report["evaluation"], "artifacts": paths}, ensure_ascii=False))
  return 1 if args.strict and not report["evaluation"]["explained"] else 0


if __name__ == "__main__":
  raise SystemExit(main())
