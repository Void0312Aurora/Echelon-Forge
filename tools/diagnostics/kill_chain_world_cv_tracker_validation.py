#!/usr/bin/env python3
"""Calibrate and validate the world-frame CV target tracker candidate."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.diagnostics import kill_chain_decoupling_probe as probe  # noqa: E402


SCHEMA_VERSION = "a2.kill_chain_world_cv_tracker_validation.v1"
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/"
  "kill_chain_world_cv_tracker_validation_20260715"
)
SEEDS = (20260621, 20260622, 20260623)
R_FUZE_M = 15.0
BASE_TUNING = {
  "nav_gain": 4.0,
  "max_lateral_g": 35.0,
  "apn_target_accel_gain": 0.5,
}
WORLD_CV_TUNING = {
  **BASE_TUNING,
  "pn_los_rate_source": 1,
  "target_kinematics_estimator": 1,
  "target_tracker_alpha": 0.20,
  "target_tracker_beta": 0.02,
}
TRACK_PROFILE = {
  "capture_mode": 1,
  "pn_mode": 3,
  "lead_mode": 1,
  "kinematics_source": 0,
  "apn_mode": 0,
}
TRUTH_PROFILE = {**TRACK_PROFILE, "kinematics_source": 1}


def _run(*, case_id: str, range_m: float, bearing_deg: float, seed: int,
         tuning: dict[str, float | int], profile: dict[str, int] | None = None,
         noisy: bool = False, trace: bool = False) -> dict[str, Any]:
  with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    return probe.run_guidance_case(
      case_id=case_id,
      range_m=range_m,
      bearing_deg=bearing_deg,
      seed=seed,
      guidance_tuning_overrides=tuning,
      guidance_mechanism_profile=profile,
      collect_guidance_runtime_trace=trace,
      guidance_measurement_period_s=0.05 if noisy else 0.0,
      guidance_bearing_noise_std_deg=0.2 if noisy else 0.0,
      guidance_range_noise_std_m=10.0 if noisy else 0.0,
    )


def _miss(result: dict[str, Any]) -> float:
  for key in ("nearest_miss_distance_m", "truth_min_distance_m"):
    value = result.get(key)
    if value is not None and math.isfinite(float(value)):
      return float(value)
  raise RuntimeError(f"missing finite miss distance for {result.get('case_id')}")


def _stable_trace(result: dict[str, Any]) -> list[dict[str, Any]]:
  return [
    row for row in list(result.get("guidance_runtime_trace", []) or [])
    if float(row.get("time_s", 0.0) or 0.0) >= 1.0
    and float(row.get("truth_distance_m", 0.0) or 0.0) > 1000.0
  ]


def _finite_values(rows: Iterable[dict[str, Any]], field: str) -> list[float]:
  values: list[float] = []
  for row in rows:
    value = row.get(field)
    if value is None:
      continue
    parsed = float(value)
    if math.isfinite(parsed):
      values.append(parsed)
  return values


def _rmse(values: list[float]) -> float:
  return math.sqrt(statistics.fmean(value * value for value in values)) if values else math.inf


def _percentile(values: list[float], fraction: float) -> float:
  if not values:
    return math.inf
  ordered = sorted(values)
  index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
  return ordered[index]


def build_report() -> dict[str, Any]:
  clean_rows: list[dict[str, Any]] = []
  oracle_gaps: list[float] = []
  for range_m in (4000.0, 6000.0, 8000.0):
    for bearing_deg in (-45.0, 45.0):
      track = _run(
        case_id=f"clean_track_{range_m:g}_{bearing_deg:g}", range_m=range_m,
        bearing_deg=bearing_deg, seed=SEEDS[0], tuning=WORLD_CV_TUNING,
        profile=TRACK_PROFILE, trace=True,
      )
      truth = _run(
        case_id=f"clean_truth_{range_m:g}_{bearing_deg:g}", range_m=range_m,
        bearing_deg=bearing_deg, seed=SEEDS[0], tuning=WORLD_CV_TUNING,
        profile=TRUTH_PROFILE,
      )
      gap = abs(_miss(track) - _miss(truth))
      oracle_gaps.append(gap)
      clean_rows.append(
        {
          "range_m": range_m,
          "bearing_deg": bearing_deg,
          "track_miss_distance_m": _miss(track),
          "truth_oracle_miss_distance_m": _miss(truth),
          "track_truth_abs_gap_m": gap,
          "trace": _stable_trace(track),
        }
      )

  nominal_rows: list[dict[str, Any]] = []
  for range_m in (4000.0, 6000.0, 8000.0):
    for bearing_deg in (-30.0, 30.0):
      result = _run(
        case_id=f"nominal_{range_m:g}_{bearing_deg:g}", range_m=range_m,
        bearing_deg=bearing_deg, seed=SEEDS[0], tuning=WORLD_CV_TUNING,
      )
      nominal_rows.append(
        {"range_m": range_m, "bearing_deg": bearing_deg,
         "miss_distance_m": _miss(result)}
      )

  noisy_rows: list[dict[str, Any]] = []
  noisy_trace: list[dict[str, Any]] = []
  for seed in SEEDS:
    for range_m in (4000.0, 6000.0, 8000.0):
      for bearing_deg in (-45.0, 45.0):
        result = _run(
          case_id=f"noisy_{seed}_{range_m:g}_{bearing_deg:g}", range_m=range_m,
          bearing_deg=bearing_deg, seed=seed, tuning=WORLD_CV_TUNING,
          profile=TRACK_PROFILE, noisy=True, trace=True,
        )
        stable = _stable_trace(result)
        noisy_trace.extend(stable)
        accepted_timestamps = [
          float(row["target_measurement_timestamp_s"])
          for row in list(result.get("guidance_runtime_trace", []) or [])
          if row.get("target_measurement_fresh")
          and row.get("target_measurement_timestamp_s") is not None
        ]
        final_trace = list(result.get("guidance_runtime_trace", []) or [])[-1]
        noisy_rows.append(
          {
            "seed": seed,
            "range_m": range_m,
            "bearing_deg": bearing_deg,
            "miss_distance_m": _miss(result),
            "accepted_measurement_count": int(
              final_trace.get("target_estimator_sample_count", 0) or 0
            ),
            "fresh_trace_count": len(accepted_timestamps),
            "unique_fresh_timestamp_count": len(set(accepted_timestamps)),
            "rejected_duplicate_measurement_count": int(
              final_trace.get("target_duplicate_measurement_count", 0) or 0
            ),
          }
        )

  clean_trace = [row for case in clean_rows for row in case["trace"]]
  clean_position_rmse_m = _rmse(_finite_values(clean_trace, "target_position_error_m"))
  clean_velocity_rmse_mps = _rmse(_finite_values(clean_trace, "target_velocity_error_mps"))
  clean_false_accel_p95_mps2 = _percentile(
    _finite_values(clean_trace, "target_track_accel_mps2"), 0.95
  )
  noisy_position_rmse_m = _rmse(_finite_values(noisy_trace, "target_position_error_m"))
  noisy_velocity_rmse_mps = _rmse(_finite_values(noisy_trace, "target_velocity_error_mps"))
  noisy_los_rate_rmse_rad_s = _rmse(
    _finite_values(noisy_trace, "target_los_rate_error_rad_s")
  )
  noisy_false_accel_p95_mps2 = _percentile(
    _finite_values(noisy_trace, "target_track_accel_mps2"), 0.95
  )

  mirror_deltas = []
  for range_m in (4000.0, 6000.0, 8000.0):
    pair = [row for row in nominal_rows if row["range_m"] == range_m]
    mirror_deltas.append(abs(pair[0]["miss_distance_m"] - pair[1]["miss_distance_m"]))
  correction_integrity = all(
    row["accepted_measurement_count"] == row["fresh_trace_count"]
    == row["unique_fresh_timestamp_count"]
    and row["rejected_duplicate_measurement_count"] > 0
    for row in noisy_rows
  )

  gates = {
    "clean_position_rmse_below_10m": clean_position_rmse_m < 10.0,
    "clean_velocity_rmse_below_2mps": clean_velocity_rmse_mps < 2.0,
    "clean_false_accel_p95_below_0p5mps2": clean_false_accel_p95_mps2 < 0.5,
    "noisy_position_rmse_below_40m": noisy_position_rmse_m < 40.0,
    "noisy_velocity_rmse_below_20mps": noisy_velocity_rmse_mps < 20.0,
    "noisy_los_rate_rmse_below_5mradps": noisy_los_rate_rmse_rad_s < 0.005,
    "noisy_false_accel_p95_below_3g": noisy_false_accel_p95_mps2 < 3.0 * 9.80665,
    "duplicate_measurements_never_corrected": correction_integrity,
    "clean_track_truth_oracle_gap_below_1p5m": max(oracle_gaps) < 1.5,
    "nominal_cells_inside_fuze": all(
      row["miss_distance_m"] <= R_FUZE_M for row in nominal_rows
    ),
    "nominal_mirror_delta_below_1mm": max(mirror_deltas) <= 1.0e-3,
  }
  for row in clean_rows:
    row.pop("trace", None)
  return {
    "schema_version": SCHEMA_VERSION,
    "selected_estimator": "world_cv",
    "selected_parameters": {"alpha": 0.20, "beta": 0.02,
                            "minimum_velocity_baseline_s": 0.5},
    "measurement_layers": {
      "clean": {"period_s": 0.0, "bearing_noise_std_deg": 0.0,
                "range_noise_std_m": 0.0},
      "default_noisy": {"period_s": 0.05, "bearing_noise_std_deg": 0.2,
                        "range_noise_std_m": 10.0, "seeds": list(SEEDS)},
    },
    "summary": {
      "clean_position_rmse_m": clean_position_rmse_m,
      "clean_velocity_rmse_mps": clean_velocity_rmse_mps,
      "clean_false_accel_p95_mps2": clean_false_accel_p95_mps2,
      "noisy_position_rmse_m": noisy_position_rmse_m,
      "noisy_velocity_rmse_mps": noisy_velocity_rmse_mps,
      "noisy_los_rate_rmse_mrad_s": noisy_los_rate_rmse_rad_s * 1000.0,
      "noisy_false_accel_p95_mps2": noisy_false_accel_p95_mps2,
      "clean_track_truth_oracle_max_gap_m": max(oracle_gaps),
      "clean_track_truth_oracle_mean_gap_m": statistics.fmean(oracle_gaps),
      "nominal_max_miss_distance_m": max(row["miss_distance_m"] for row in nominal_rows),
      "nominal_max_mirror_delta_m": max(mirror_deltas),
    },
    "clean_track_truth_rows": clean_rows,
    "nominal_rows": nominal_rows,
    "noisy_rows": noisy_rows,
    "gates": gates,
    "passed": all(gates.values()),
  }


def write_report(report: dict[str, Any], output_dir: Path) -> None:
  output_dir.mkdir(parents=True, exist_ok=True)
  (output_dir / "world_cv_tracker_validation.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
  )
  summary = report["summary"]
  lines = [
    "# 第二阶段：世界系 CV 目标运动估计验收",
    "",
    "结论：问题属于坐标与测量时间语义，不是只调球坐标滤波 tau。",
    "候选采用新鲜时间戳校正、世界系 CV 外推、速度成熟门控和零加速度 CV 层。",
    "",
    f"- 选定参数：`alpha=0.20`, `beta=0.02`, 速度基线 `0.5 s`。",
    f"- clean position/velocity RMSE：`{summary['clean_position_rmse_m']:.3f} m` / "
    f"`{summary['clean_velocity_rmse_mps']:.3f} m/s`。",
    f"- 20 Hz 默认噪声 position/velocity RMSE："
    f"`{summary['noisy_position_rmse_m']:.3f} m` / "
    f"`{summary['noisy_velocity_rmse_mps']:.3f} m/s`。",
    f"- 默认噪声 LOS-rate RMSE：`{summary['noisy_los_rate_rmse_mrad_s']:.3f} mrad/s`。",
    f"- CV 假加速度 P95：`{summary['noisy_false_accel_p95_mps2']:.6f} m/s²`。",
    f"- clean M45 track-vs-truth oracle 最大最近距差："
    f"`{summary['clean_track_truth_oracle_max_gap_m']:.3f} m`。",
    f"- N30 最大最近距：`{summary['nominal_max_miss_distance_m']:.3f} m`。",
    "",
    "验收门：",
    "",
    *[
      f"- `{name}`: {'PASS' if passed else 'FAIL'}"
      for name, passed in report["gates"].items()
    ],
    "",
    "候选仍保持可选择状态；最终是否写入 AIM-120 默认配置留到第五阶段。",
    "",
  ]
  (output_dir / "world_cv_tracker_validation.zh.md").write_text(
    "\n".join(lines), encoding="utf-8"
  )


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  args = parser.parse_args()
  probe.ef_py.set_log_level("warn")
  report = build_report()
  write_report(report, args.output_dir)
  print(json.dumps({"passed": report["passed"], "summary": report["summary"],
                    "output_dir": str(args.output_dir)}, ensure_ascii=False))
  return 0 if report["passed"] else 1


if __name__ == "__main__":
  raise SystemExit(main())
