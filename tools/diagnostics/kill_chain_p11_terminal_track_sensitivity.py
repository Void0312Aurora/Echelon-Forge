#!/usr/bin/env python3
"""Measure P11 terminal-track residual sensitivity to the memory timeout."""

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


SCHEMA_VERSION = "a2.kill_chain_p11_terminal_track_sensitivity.v1"
GENERATED_ON = "2026-09-15"
DEFAULT_SEEDS = (20260621, 20260622, 20260623)
DEFAULT_MEMORY_TIMEOUTS_S = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0)
DEFAULT_CASES = (
  {
    "case_id": "kces_anchor_grid_mild_6km_m60deg",
    "range_m": 6000.0,
    "bearing_deg": -60.0,
    "target_acceleration_mps2": (-8.0, 0.0, 0.0),
  },
  {
    "case_id": "kces_anchor_grid_mild_6km_p60deg",
    "range_m": 6000.0,
    "bearing_deg": 60.0,
    "target_acceleration_mps2": (8.0, 0.0, 0.0),
  },
)
DEFAULT_DATABASE_PATH = REPO_ROOT / "examples/config/database"
DEFAULT_SOURCE_REPORT = (
  REPO_ROOT
  / "artifacts/kill_chain/20260915/raw_review_packets/kill_chain_integrated_admission_20260915"
  / "kill_chain_integrated_admission_20260915.json"
)
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "artifacts/kill_chain/20260915/raw_review_packets/kill_chain_p11_terminal_track_sensitivity_20260915"
)
DEFAULT_STEM = "kill_chain_p11_terminal_track_sensitivity_20260915"
STATE_ORDER = {"outside_no_load": 0, "in_radius_fuze_blocked": 1, "complete_effect_chain": 2}


def _finite(value: Any, default: float = 0.0) -> float:
  try:
    parsed = float(value)
  except (TypeError, ValueError):
    return float(default)
  return parsed if math.isfinite(parsed) else float(default)


def _finite_or_none(value: Any) -> float | None:
  try:
    parsed = float(value)
  except (TypeError, ValueError):
    return None
  return parsed if math.isfinite(parsed) else None


def _state_for_run(result: dict[str, Any], *, fuze_radius_m: float = 15.0) -> str:
  if bool(result.get("fuze_triggered", False)):
    return "complete_effect_chain"
  nearest = _finite_or_none(result.get("nearest_miss_distance_m"))
  if nearest is not None and nearest <= float(fuze_radius_m) + 1.0e-9:
    return "in_radius_fuze_blocked"
  return "outside_no_load"


def _memory_to_ballistic(summary: dict[str, Any]) -> float | None:
  memory = _finite_or_none(summary.get("first_memory_time_s"))
  ballistic = _finite_or_none(summary.get("first_ballistic_time_s"))
  if memory is None or ballistic is None:
    return None
  return ballistic - memory


def _run_case(
  *,
  database_path: Path,
  case: dict[str, Any],
  seed: int,
  memory_timeout_s: float,
) -> dict[str, Any]:
  result = probe.run_guidance_case(
    database_path=database_path,
    case_id=str(case["case_id"]),
    range_m=float(case["range_m"]),
    bearing_deg=float(case["bearing_deg"]),
    seed=int(seed),
    guidance_tuning_overrides={"track_break_time_s": float(memory_timeout_s)},
    target_acceleration_mps2=tuple(
      float(value) for value in case["target_acceleration_mps2"]
    ),
  )
  runtime_summary = dict(result.get("guidance_runtime_summary", {}) or {})
  return {
    "case_id": str(case["case_id"]),
    "range_m": float(case["range_m"]),
    "bearing_deg": float(case["bearing_deg"]),
    "target_acceleration_x_mps2": float(case["target_acceleration_mps2"][0]),
    "seed": int(seed),
    "requested_memory_timeout_s": float(memory_timeout_s),
    "resolved_memory_timeout_s": _finite_or_none(
      runtime_summary.get("track_memory_timeout_s")
    ),
    "state": _state_for_run(result),
    "nearest_miss_distance_m": _finite_or_none(result.get("nearest_miss_distance_m")),
    "fuze_triggered": bool(result.get("fuze_triggered", False)),
    "fuze_reason": str(result.get("fuze_reason", "") or ""),
    "first_detection_outside_fov_time_s": _finite_or_none(
      runtime_summary.get("first_detection_outside_fov_time_s")
    ),
    "first_memory_time_s": _finite_or_none(runtime_summary.get("first_memory_time_s")),
    "first_ballistic_time_s": _finite_or_none(
      runtime_summary.get("first_ballistic_time_s")
    ),
    "memory_to_ballistic_s": _memory_to_ballistic(runtime_summary),
    "max_detection_fov_excess_deg": _finite(
      runtime_summary.get("max_detection_fov_excess_deg")
    ),
    "max_seeker_fov_excess_deg": _finite(
      runtime_summary.get("max_seeker_fov_excess_deg")
    ),
    "last_runtime_seeker_mode_name": str(
      dict(runtime_summary.get("last_runtime_observation", {}) or {}).get(
        "seeker_mode_name", ""
      )
      or ""
    ),
  }


def _aggregate_cells(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
  for row in runs:
    grouped[(str(row["case_id"]), float(row["requested_memory_timeout_s"]))].append(row)
  cells: list[dict[str, Any]] = []
  for (case_id, timeout), group in sorted(grouped.items()):
    states = sorted({str(row["state"]) for row in group})
    distances = [
      float(row["nearest_miss_distance_m"])
      for row in group
      if row["nearest_miss_distance_m"] is not None
    ]
    memory_to_ballistic = [
      float(row["memory_to_ballistic_s"])
      for row in group
      if row["memory_to_ballistic_s"] is not None
    ]
    cells.append(
      {
        "case_id": case_id,
        "requested_memory_timeout_s": timeout,
        "seed_count": len(group),
        "seeds": sorted({int(row["seed"]) for row in group}),
        "states": states,
        "stable_across_seeds": len(states) == 1,
        "state": states[0] if len(states) == 1 else "mixed",
        "fuze_triggered_count": sum(bool(row["fuze_triggered"]) for row in group),
        "nearest_miss_distance_min_m": min(distances) if distances else None,
        "nearest_miss_distance_max_m": max(distances) if distances else None,
        "nearest_miss_distance_spread_m": (
          max(distances) - min(distances) if distances else None
        ),
        "memory_to_ballistic_min_s": (
          min(memory_to_ballistic) if memory_to_ballistic else None
        ),
        "memory_to_ballistic_max_s": (
          max(memory_to_ballistic) if memory_to_ballistic else None
        ),
        "fuze_reasons": sorted({str(row["fuze_reason"]) for row in group}),
        "last_seeker_modes": sorted(
          {str(row["last_runtime_seeker_mode_name"]) for row in group}
        ),
      }
    )
  return cells


def _monotonic_timeout_cells(cells: list[dict[str, Any]]) -> bool:
  grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
  for cell in cells:
    grouped[str(cell["case_id"])].append(cell)
  for group in grouped.values():
    ordered = sorted(group, key=lambda row: float(row["requested_memory_timeout_s"]))
    ranks = [STATE_ORDER.get(str(row["state"]), -1) for row in ordered]
    if any(rank < 0 for rank in ranks) or ranks != sorted(ranks):
      return False
  return bool(grouped)


def build_report(
  runs: list[dict[str, Any]],
  *,
  seeds: tuple[int, ...],
  memory_timeouts_s: tuple[float, ...],
  source_report: Path,
) -> dict[str, Any]:
  cells = _aggregate_cells(runs)
  expected_run_count = len(DEFAULT_CASES) * len(seeds) * len(memory_timeouts_s)
  expected_case_ids = {str(case["case_id"]) for case in DEFAULT_CASES}
  expected_run_keys = {
    (case_id, float(timeout), int(seed))
    for case_id in expected_case_ids
    for timeout in memory_timeouts_s
    for seed in seeds
  }
  actual_run_keys = [
    (
      str(row["case_id"]),
      float(row["requested_memory_timeout_s"]),
      int(row["seed"]),
    )
    for row in runs
  ]
  matrix_complete = (
    len(actual_run_keys) == len(expected_run_keys)
    and len(actual_run_keys) == len(set(actual_run_keys))
    and set(actual_run_keys) == expected_run_keys
  )
  stable = bool(cells) and all(
    bool(cell["stable_across_seeds"])
    and int(cell["seed_count"]) == len(seeds)
    and set(int(seed) for seed in cell["seeds"]) == set(seeds)
    for cell in cells
  )
  resolved_timeout = all(
    row["resolved_memory_timeout_s"] is not None
    and abs(float(row["resolved_memory_timeout_s"]) - float(row["requested_memory_timeout_s"]))
    <= 1.0e-12
    for row in runs
  )
  baseline_cells = [
    cell for cell in cells if abs(float(cell["requested_memory_timeout_s"]) - 0.75) <= 1.0e-12
  ]
  baseline_residual = bool(baseline_cells) and all(
    cell["state"] == "in_radius_fuze_blocked" for cell in baseline_cells
  )
  transition_cases = {
    str(cell["case_id"])
    for cell in cells
    if cell["state"] == "complete_effect_chain"
  }
  all_cases_transition = transition_cases == expected_case_ids
  gates = {
    "expected_run_matrix_complete": matrix_complete
    and len(runs) == expected_run_count,
    "runtime_resolves_requested_memory_timeout": resolved_timeout,
    "all_cells_stable_across_seeds": stable,
    "timeout_response_is_monotonic": _monotonic_timeout_cells(cells),
    "baseline_075s_reproduces_terminal_track_residual": baseline_residual,
    "all_cases_have_a_timeout_that_restores_fuze_trigger": all_cases_transition,
  }
  candidate_ready = all(gates.values())
  state_counts = dict(sorted(Counter(str(row["state"]) for row in runs).items()))
  return {
    "schema_version": SCHEMA_VERSION,
    "status": (
      "p11_terminal_track_memory_sensitivity_explained"
      if candidate_ready
      else "p11_terminal_track_memory_sensitivity_inconclusive"
    ),
    "generated_on": GENERATED_ON,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_report": {
      "path": _repo_relative(source_report),
      "sha256": _sha256(source_report),
    },
    "authority_boundary": {
      "diagnostic_only": True,
      "runtime_default_modified": False,
      "database_modified": False,
      "expectation_harness_modified": False,
      "p11_complete": False,
      "real_weapon_performance_authority": False,
      "pk_authority": False,
    },
    "matrix": {
      "cases": [dict(case) for case in DEFAULT_CASES],
      "seeds": list(seeds),
      "memory_timeouts_s": list(memory_timeouts_s),
      "expected_run_count": expected_run_count,
      "fuze_radius_m": 15.0,
    },
    "counts": {
      "run_count": len(runs),
      "cell_count": len(cells),
      "stable_cell_count": sum(bool(cell["stable_across_seeds"]) for cell in cells),
      "complete_effect_chain_run_count": sum(
        row["state"] == "complete_effect_chain" for row in runs
      ),
      "in_radius_fuze_blocked_run_count": sum(
        row["state"] == "in_radius_fuze_blocked" for row in runs
      ),
      "outside_no_load_run_count": sum(row["state"] == "outside_no_load" for row in runs),
    },
    "run_state_counts": state_counts,
    "evaluation": {
      "gates": gates,
      "residual_explanation_ready": candidate_ready,
      "default_timeout_change_authorized": False,
      "p11_complete": False,
      "next_action": (
        "retain the 0.75 s default unless a separate runtime contract accepts a wider "
        "terminal memory policy; use this sensitivity only as residual evidence"
      ),
    },
    "cells": cells,
    "runs": runs,
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


def _repo_relative(path: Path) -> str:
  resolved = path.resolve()
  try:
    rendered = str(resolved.relative_to(REPO_ROOT))
  except ValueError:
    rendered = str(resolved)
  return rendered.replace("/", "\\")


def conclusions_zh(report: dict[str, Any]) -> str:
  counts = report["counts"]
  evaluation = report["evaluation"]
  conclusion = (
    "结论：该批把 `seeker_fov_exit_then_memory_timeout` 量化为一个可复现的记忆窗口"
    "边界问题。它没有证明 0.75 s 是错误值，也没有授权放宽 seeker FOV、terminal fuze"
    "门或生产默认配置；P11 仍保持 incomplete，后续应由独立 runtime contract 决定是否调整。"
    if evaluation["residual_explanation_ready"]
    else "结论：至少一个矩阵、稳定性、单调性或转换门失败；当前扫描不能把残差归因"
    "到记忆窗口，也不得支持默认值调整。"
  )
  return "\n".join(
    [
      "# P11 terminal-track 记忆窗口敏感性结论",
      "",
      f"- 状态：`{report['status']}`；残差解释可用："
      f"`{evaluation['residual_explanation_ready']}`。",
      f"- 矩阵：`{counts['run_count']}` runs / `{counts['stable_cell_count']}` 个跨三种子稳定 cells。",
      f"- run 状态：`{report['run_state_counts']}`。",
      "- 基准 `track_break_time_s=0.75 s` 重现两个 `in_radius_fuze_blocked`；扩大记忆窗口后，"
      "若进入 `complete_effect_chain`，只能说明该残差对记忆窗口敏感，不等于默认值应被修改。",
      f"- 所有 cells 的 timeout 响应单调：`{report['evaluation']['gates']['timeout_response_is_monotonic']}`。",
      "",
      conclusion,
      "",
    ]
  )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
  columns = list(rows[0]) if rows else []
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns)
    if rows:
      writer.writeheader()
      writer.writerows(rows)


def write_bundle(
  report: dict[str, Any], *, output_dir: Path, stem: str, source_report: Path
) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "report_json": output_dir / f"{stem}.json",
    "runs_csv": output_dir / f"{stem}_runs.csv",
    "cells_csv": output_dir / f"{stem}_cells.csv",
    "conclusions_zh_md": output_dir / f"{stem}_conclusions.zh.md",
    "manifest_json": output_dir / f"{stem}_manifest.json",
  }
  paths["report_json"].write_text(
    json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
  )
  _write_csv(paths["runs_csv"], report["runs"])
  _write_csv(paths["cells_csv"], report["cells"])
  paths["conclusions_zh_md"].write_text(conclusions_zh(report), encoding="utf-8")
  manifest = {
    "schema_version": "a2.kill_chain_p11_terminal_track_sensitivity_manifest.v1",
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
        "sha256": _sha256(Path(__file__)),
      },
      "probe": {
        "path": _repo_relative(Path(probe.__file__)),
        "sha256": _sha256(Path(probe.__file__)),
      },
      "source_report": {
        "path": _repo_relative(source_report),
        "sha256": _sha256(source_report),
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
  parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE_PATH)
  parser.add_argument("--source-report", type=Path, default=DEFAULT_SOURCE_REPORT)
  parser.add_argument(
    "--memory-timeouts-s",
    default=",".join(str(value) for value in DEFAULT_MEMORY_TIMEOUTS_S),
  )
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--stem", default=DEFAULT_STEM)
  args = parser.parse_args(argv)
  memory_timeouts_s = tuple(
    float(item.strip()) for item in str(args.memory_timeouts_s).split(",") if item.strip()
  )
  if not memory_timeouts_s or any(value <= 0.0 or not math.isfinite(value) for value in memory_timeouts_s):
    raise SystemExit("--memory-timeouts-s must contain positive finite values")
  runs = [
    _run_case(
      database_path=args.database,
      case=case,
      seed=seed,
      memory_timeout_s=timeout,
    )
    for timeout in memory_timeouts_s
    for seed in DEFAULT_SEEDS
    for case in DEFAULT_CASES
  ]
  report = build_report(
    runs,
    seeds=DEFAULT_SEEDS,
    memory_timeouts_s=memory_timeouts_s,
    source_report=args.source_report.resolve(),
  )
  paths = write_bundle(
    report,
    output_dir=args.output_dir,
    stem=str(args.stem),
    source_report=args.source_report.resolve(),
  )
  print(
    json.dumps(
      {
        "status": report["status"],
        "counts": report["counts"],
        "evaluation": report["evaluation"],
        "artifacts": paths,
      },
      ensure_ascii=False,
    )
  )
  return 0 if report["evaluation"]["residual_explanation_ready"] else 1


if __name__ == "__main__":
  raise SystemExit(main())
