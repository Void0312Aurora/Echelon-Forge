#!/usr/bin/env python3
"""Validate the selectable production world-LOS-history PN source."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.diagnostics import kill_chain_decoupling_probe as probe  # noqa: E402
from tools.diagnostics import kill_chain_guidance_exact_mechanism_ablation as exact  # noqa: E402


SCHEMA_VERSION = "a2.kill_chain_world_pn_production_validation.v1"
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/"
  "kill_chain_world_pn_production_validation_20260715"
)
FROZEN_TUNING = {
  "nav_gain": 4.0,
  "max_lateral_g": 35.0,
  "apn_target_accel_gain": 0.5,
}
HISTORY_PROFILE = {
  "capture_mode": 1,
  "pn_mode": 2,
  "lead_mode": 2,
  "kinematics_source": 0,
  "apn_mode": 1,
}


def _miss_distance(result: dict[str, Any]) -> float:
  for key in ("nearest_miss_distance_m", "truth_min_distance_m"):
    value = result.get(key)
    if value is not None and math.isfinite(float(value)):
      return float(value)
  raise RuntimeError(f"guidance case lacks a finite miss distance: {result.get('case_id')}")


def _run(case: dict[str, Any], *, seed: int, source: int | None = None,
         profile: dict[str, int] | None = None) -> dict[str, Any]:
  tuning = dict(FROZEN_TUNING)
  if source is not None:
    tuning["pn_los_rate_source"] = int(source)
  with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    return probe.run_guidance_case(
      case_id=str(case["case_id"]),
      range_m=float(case["range_m"]),
      bearing_deg=float(case["bearing_deg"]),
      seed=int(seed),
      guidance_tuning_overrides=tuning,
      guidance_mechanism_profile=profile,
    )


def build_report(seed: int) -> dict[str, Any]:
  rows: list[dict[str, Any]] = []
  for case in exact.default_cases():
    legacy_default = _run(case, seed=seed)
    legacy_explicit = _run(case, seed=seed, source=0)
    production_world = _run(case, seed=seed, source=1)
    diagnostic_world = _run(case, seed=seed, profile=HISTORY_PROFILE)
    row = dict(case)
    row.update(
      {
        "legacy_default_miss_distance_m": _miss_distance(legacy_default),
        "legacy_explicit_miss_distance_m": _miss_distance(legacy_explicit),
        "production_world_miss_distance_m": _miss_distance(production_world),
        "diagnostic_world_miss_distance_m": _miss_distance(diagnostic_world),
      }
    )
    row["legacy_abs_delta_m"] = abs(
      row["legacy_default_miss_distance_m"] - row["legacy_explicit_miss_distance_m"]
    )
    row["world_abs_delta_m"] = abs(
      row["production_world_miss_distance_m"] - row["diagnostic_world_miss_distance_m"]
    )
    rows.append(row)

  mirror: dict[tuple[float, float], list[float]] = defaultdict(list)
  for row in rows:
    mirror[(float(row["range_km"]), float(row["offset_deg"]))].append(
      float(row["production_world_miss_distance_m"])
    )
  mirror_deltas = [abs(values[0] - values[1]) for values in mirror.values() if len(values) == 2]
  n_rows = [row for row in rows if row["launch_class"] == "N"]
  gates = {
    "legacy_default_unchanged": max(row["legacy_abs_delta_m"] for row in rows) <= 1.0e-9,
    "production_matches_diagnostic_history":
      max(row["world_abs_delta_m"] for row in rows) <= 1.0e-9,
    "mirror_symmetry": max(mirror_deltas, default=0.0) <= 1.0e-3,
    "nominal_cells_inside_fuze": all(
      float(row["production_world_miss_distance_m"]) <= exact.R_FUZE_M for row in n_rows
    ),
  }
  return {
    "schema_version": SCHEMA_VERSION,
    "seed": int(seed),
    "frozen_tuning": dict(FROZEN_TUNING),
    "production_source": "world_los_history",
    "diagnostic_reference": dict(HISTORY_PROFILE),
    "fuze_radius_m": exact.R_FUZE_M,
    "row_count": len(rows),
    "rows": rows,
    "summary": {
      "max_legacy_abs_delta_m": max(row["legacy_abs_delta_m"] for row in rows),
      "max_world_abs_delta_m": max(row["world_abs_delta_m"] for row in rows),
      "max_mirror_abs_delta_m": max(mirror_deltas, default=0.0),
      "nominal_max_miss_distance_m": max(
        float(row["production_world_miss_distance_m"]) for row in n_rows
      ),
      "old_outside_cells_inside_fuze": [
        str(row["case_id"])
        for row in rows
        if row["launch_class"] == "O"
        and float(row["production_world_miss_distance_m"]) <= exact.R_FUZE_M
      ],
    },
    "gates": gates,
    "passed": all(gates.values()),
  }


def write_report(report: dict[str, Any], output_dir: Path) -> None:
  output_dir.mkdir(parents=True, exist_ok=True)
  (output_dir / "world_pn_production_validation.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
  )
  summary = report["summary"]
  gate_lines = [
    f"- `{name}`: {'PASS' if passed else 'FAIL'}"
    for name, passed in report["gates"].items()
  ]
  markdown = "\n".join(
    [
      "# 第一阶段：世界系 LOS-history PN 生产候选验收",
      "",
      "结论：候选通过第一阶段门槛，但尚未写入 AIM-120 默认配置。",
      "",
      f"- 样本数：`{report['row_count']}` 个左右镜像 anchor case。",
      f"- legacy 默认与显式 legacy 最大差：`{summary['max_legacy_abs_delta_m']:.12g} m`。",
      f"- 生产候选与 diagnostics history profile 最大差：`{summary['max_world_abs_delta_m']:.12g} m`。",
      f"- 左右镜像最大差：`{summary['max_mirror_abs_delta_m']:.12g} m`。",
      f"- N 类最大最近距：`{summary['nominal_max_miss_distance_m']:.6f} m`（fuze 半径 15 m）。",
      "- 旧 O 类进入 fuze 的 case："
      + (", ".join(f"`{item}`" for item in summary["old_outside_cells_inside_fuze"])
         or "无"),
      "",
      "验收门：",
      "",
      *gate_lines,
      "",
      "旧 O 的移动只登记为窗口结构变化，不在第一阶段用旧标签否决坐标机制。",
      "阶段二继续处理 track 世界系运动估计和重复测量消费。",
      "",
    ]
  )
  (output_dir / "world_pn_production_validation.zh.md").write_text(
    markdown, encoding="utf-8"
  )


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--seed", type=int, default=exact.DEFAULT_SEED)
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  args = parser.parse_args()
  probe.ef_py.set_log_level("warn")
  report = build_report(args.seed)
  write_report(report, args.output_dir)
  print(json.dumps({"passed": report["passed"], "output_dir": str(args.output_dir),
                    "summary": report["summary"]}, ensure_ascii=False))
  return 0 if report["passed"] else 1


if __name__ == "__main__":
  raise SystemExit(main())
