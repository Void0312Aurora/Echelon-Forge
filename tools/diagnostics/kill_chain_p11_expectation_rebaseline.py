#!/usr/bin/env python3
"""Audit a candidate P11 N/M/O expectation rebaseline without mutating the harness."""

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


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))


SCHEMA_VERSION = "a2.kill_chain_p11_expectation_rebaseline.v1"
GENERATED_ON = "2026-09-15"
DEFAULT_INPUT = (
  REPO_ROOT
  / "docs/systems/weapons/reviews/kill_chain_integrated_admission_20260915"
  / "review_packets/kill_chain_integrated_admission_20260915.json"
)
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs/systems/weapons/reviews/kill_chain_p11_expectation_rebaseline_20260915"
  / "review_packets"
)
DEFAULT_STEM = "kill_chain_p11_expectation_rebaseline_20260915"
EXPECTED_SEED_COUNT = 3
EXPECTED_SEEDS = (20260621, 20260622, 20260623)
CLASS_ORDER = {"O": 0, "M": 1, "N": 2}


def _finite(value: Any, default: float = 0.0) -> float:
  try:
    parsed = float(value)
  except (TypeError, ValueError):
    return float(default)
  return parsed if math.isfinite(parsed) else float(default)


def _candidate_class(cell: dict[str, Any]) -> str:
  states = list(cell.get("chain_states", []) or [])
  if len(states) != 1:
    return "M"
  state = str(states[0])
  if state == "complete_effect_chain":
    return "N"
  if state == "outside_no_load":
    return "O"
  if state == "in_radius_fuze_blocked":
    return "M"
  return "M"


def _transition(old_class: str, candidate_class: str, cell: dict[str, Any]) -> str:
  if old_class == candidate_class:
    return f"retain_{candidate_class}"
  if candidate_class == "N":
    return "promote_to_N"
  if candidate_class == "O":
    return "demote_to_O"
  if bool(cell.get("in_radius_fuze_blocked")):
    return "hold_M_terminal_track_residual"
  return "reclassify_to_M"


def _cell_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
  run_seeds: dict[str, set[int]] = defaultdict(set)
  for run in list(report.get("runs", []) or []):
    run_seeds[str(run.get("case_id", "") or "")].add(
      int(run.get("seed", 0) or 0)
    )
  rows: list[dict[str, Any]] = []
  for source in list(report.get("cells", []) or []):
    cell = dict(source)
    old_class = str(cell.get("launch_class", "") or "")
    candidate = _candidate_class(cell)
    seeds = sorted(run_seeds.get(str(cell.get("case_id", "") or ""), set()))
    stable = (
      len(list(cell.get("chain_states", []) or [])) == 1
      and int(cell.get("seed_count", 0) or 0) == EXPECTED_SEED_COUNT
      and tuple(seeds) == EXPECTED_SEEDS
      and bool(cell.get("structural_consistent", False))
    )
    rows.append(
      {
        "case_id": str(cell.get("case_id", "") or ""),
        "target_motion_layer": str(cell.get("target_motion_layer", "") or ""),
        "target_acceleration_x_mps2": _finite(
          cell.get("target_acceleration_x_mps2")
        ),
        "range_km": _finite(cell.get("range_km")),
        "bearing_deg": _finite(cell.get("bearing_deg")),
        "old_launch_class": old_class,
        "observed_chain_state": (
          str(cell["chain_states"][0])
          if len(list(cell.get("chain_states", []) or [])) == 1
          else "mixed"
        ),
        "candidate_launch_class": candidate,
        "transition": _transition(old_class, candidate, cell),
        "stable_across_seeds": stable,
        "seed_count": int(cell.get("seed_count", 0) or 0),
        "seeds": seeds,
        "nearest_distance_min_m": _finite(cell.get("nearest_distance_min_m"), math.inf),
        "nearest_distance_max_m": _finite(cell.get("nearest_distance_max_m"), math.inf),
        "legacy_negative_control_alert": bool(
          cell.get("legacy_negative_control_alert", False)
        ),
        "in_radius_fuze_blocked": bool(cell.get("in_radius_fuze_blocked", False)),
        "terminal_track_residual_causes": ",".join(
          str(value)
          for value in list(cell.get("terminal_track_residual_causes", []) or [])
        ),
      }
    )
  return rows


def _source_matrix_audit(
  report: dict[str, Any], rows: list[dict[str, Any]]
) -> dict[str, Any]:
  case_ids = [str(row["case_id"]) for row in rows]
  actual_run_keys = [
    (str(run.get("case_id", "") or ""), int(run.get("seed", 0) or 0))
    for run in list(report.get("runs", []) or [])
  ]
  expected_run_keys = {
    (case_id, seed) for case_id in set(case_ids) for seed in EXPECTED_SEEDS
  }
  matrix = dict(report.get("matrix", {}) or {})
  checks = {
    "unique_cell_ids": len(case_ids) == len(set(case_ids)),
    "expected_cell_count": len(rows)
    == int(matrix.get("case_count_per_seed", 0) or 0),
    "declared_seed_set_exact": tuple(sorted(int(seed) for seed in matrix.get("seeds", [])))
    == EXPECTED_SEEDS,
    "unique_case_seed_pairs": len(actual_run_keys) == len(set(actual_run_keys)),
    "complete_case_seed_cartesian_product": set(actual_run_keys) == expected_run_keys,
    "declared_run_count_exact": len(actual_run_keys)
    == int(matrix.get("expected_run_count", 0) or 0),
  }
  return {
    "checks": checks,
    "passed": all(checks.values()),
    "actual_cell_count": len(rows),
    "actual_run_count": len(actual_run_keys),
    "expected_seed_set": list(EXPECTED_SEEDS),
  }


def _angle_topology(rows: list[dict[str, Any]]) -> dict[str, Any]:
  grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    grouped[(row["target_motion_layer"], row["range_km"])].append(row)
  violations: list[dict[str, Any]] = []
  for (layer, range_km), group in sorted(grouped.items()):
    by_abs_angle: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for row in group:
      by_abs_angle[abs(row["bearing_deg"])].append(row)
    previous_order: int | None = None
    previous_angle: float | None = None
    for angle in sorted(by_abs_angle):
      classes = {row["candidate_launch_class"] for row in by_abs_angle[angle]}
      if len(classes) != 1:
        violations.append(
          {
            "type": "mirror_class_mismatch",
            "target_motion_layer": layer,
            "range_km": range_km,
            "angle_deg": angle,
            "classes": sorted(classes),
          }
        )
        continue
      current_class = next(iter(classes))
      current_order = CLASS_ORDER.get(current_class, -1)
      if previous_order is not None and current_order > previous_order:
        violations.append(
          {
            "type": "angle_miss_to_hit_reversal",
            "target_motion_layer": layer,
            "range_km": range_km,
            "previous_angle_deg": previous_angle,
            "previous_class": next(
              row["candidate_launch_class"]
              for row in by_abs_angle[previous_angle]
            ),
            "angle_deg": angle,
            "class": current_class,
          }
        )
      previous_order = current_order
      previous_angle = angle
  return {
    "group_count": len(grouped),
    "violation_count": len(violations),
    "violations": violations,
    "monotonic_angle_topology": not violations,
  }


def build_report(input_report: dict[str, Any], *, input_path: Path) -> dict[str, Any]:
  rows = _cell_rows(input_report)
  transition_counts = dict(
    sorted(Counter(row["transition"] for row in rows).items())
  )
  old_candidate_counts = dict(
    sorted(
      Counter(
        f"{row['old_launch_class']}->{row['candidate_launch_class']}"
        for row in rows
      ).items()
    )
  )
  observed_state_counts = dict(
    sorted(Counter(row["observed_chain_state"] for row in rows).items())
  )
  topology = _angle_topology(rows)
  stable = bool(rows) and all(row["stable_across_seeds"] for row in rows)
  candidate_counts = dict(
    sorted(Counter(row["candidate_launch_class"] for row in rows).items())
  )
  unresolved_rows = [
    row for row in rows if row["candidate_launch_class"] != row["old_launch_class"]
  ]
  terminal_rows = [row for row in rows if row["in_radius_fuze_blocked"]]
  source_matrix_audit = _source_matrix_audit(input_report, rows)
  gates = {
    "source_report_structural_admission_passed": bool(
      input_report.get("evaluation", {})
      .get("p11_structural_admission_passed", False)
    ),
    "source_anchor_matrix_complete": source_matrix_audit["passed"],
    "all_cells_stable_across_required_seeds": stable,
    "candidate_classes_are_defined": bool(rows) and all(
      row["candidate_launch_class"] in CLASS_ORDER for row in rows
    ),
    "candidate_angle_topology_monotonic": topology["monotonic_angle_topology"],
    "terminal_track_residuals_remain_explicit": bool(terminal_rows) and all(
      bool(str(row["terminal_track_residual_causes"]).strip())
      for row in terminal_rows
    ),
  }
  candidate_ready = all(gates.values())
  return {
    "schema_version": SCHEMA_VERSION,
    "status": (
      "p11_expectation_rebaseline_candidate_ready_for_review"
      if candidate_ready
      else "p11_expectation_rebaseline_candidate_inconclusive"
    ),
    "generated_on": GENERATED_ON,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_report": {
      "path": str(input_path.resolve().relative_to(REPO_ROOT)),
      "sha256": _sha256(input_path),
      "status": input_report.get("status", ""),
    },
    "authority_boundary": {
      "candidate_only": True,
      "mutates_expectation_harness": False,
      "changes_p11_admission": False,
      "real_weapon_performance_authority": False,
      "pk_authority": False,
    },
    "policy": {
      "complete_effect_chain": "candidate N",
      "in_radius_fuze_blocked": "candidate M; retain explicit terminal-track residual",
      "outside_no_load": "candidate O",
      "mixed_or_unknown": "candidate M and hold for review",
      "required_seed_count": EXPECTED_SEED_COUNT,
    },
    "counts": {
      "cell_count": len(rows),
      "stable_cell_count": sum(row["stable_across_seeds"] for row in rows),
      "changed_label_cell_count": len(unresolved_rows),
      "terminal_track_residual_cell_count": len(terminal_rows),
    },
    "observed_chain_state_counts": observed_state_counts,
    "candidate_class_counts": candidate_counts,
    "old_to_candidate_transition_counts": old_candidate_counts,
    "transition_disposition_counts": transition_counts,
    "evaluation": {
      "gates": gates,
      "candidate_ready_for_manual_review": candidate_ready,
      "legacy_expectation_harness_unchanged": True,
      "p11_complete": False,
      "next_action": (
        "manually review candidate labels and terminal-track residual, then make an "
        "explicit expectation-harness change only if accepted"
      ),
    },
    "topology": topology,
    "source_matrix_audit": source_matrix_audit,
    "cells": rows,
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
  transitions = report["old_to_candidate_transition_counts"]
  return "\n".join(
    [
      "# P11 期望包络候选重基线审计",
      "",
      f"- 状态：`{report['status']}`；候选可供人工审查："
      f"`{evaluation['candidate_ready_for_manual_review']}`。",
      f"- 来源：`{report['source_report']['status']}`，`{counts['cell_count']}` cells；"
      f"跨三种子稳定 `{counts['stable_cell_count']}`。",
      f"- 观测状态计数：`{report['observed_chain_state_counts']}`。",
      f"- 候选 N/M/O：`{report['candidate_class_counts']}`；旧标签发生变化的 cells："
      f"`{counts['changed_label_cell_count']}`。",
      f"- 旧→候选转移：`{transitions}`。",
      f"- 候选角度拓扑单调：`{report['topology']['monotonic_angle_topology']}`；"
      f"违规 `{report['topology']['violation_count']}`。",
      f"- terminal-track residual cells：`{counts['terminal_track_residual_cell_count']}`；"
      "这些残差仍被保留，不被重基线吞并。",
      "",
      "结论：P10 默认制导改变了原始 P11 N/M/O 标签，现有报告足以形成一个稳定的"
      "候选重基线，但不能自动视为已接受的期望包络。需人工审查旧标签语义与"
      "terminal-track 残差后，才能显式修改 harness；本审计不改变 P11 complete 状态。",
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
  report: dict[str, Any], *, output_dir: Path, stem: str, input_path: Path
) -> dict[str, str]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths = {
    "report_json": output_dir / f"{stem}.json",
    "cells_csv": output_dir / f"{stem}_cells.csv",
    "conclusions_zh_md": output_dir / f"{stem}_conclusions.zh.md",
    "manifest_json": output_dir / f"{stem}_manifest.json",
  }
  paths["report_json"].write_text(
    json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
  )
  _write_csv(paths["cells_csv"], report["cells"])
  paths["conclusions_zh_md"].write_text(conclusions_zh(report), encoding="utf-8")
  manifest = {
    "schema_version": "a2.kill_chain_p11_expectation_rebaseline_manifest.v1",
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
      "source_report": {
        "path": str(input_path.resolve().relative_to(REPO_ROOT)),
        "sha256": _sha256(input_path),
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
  parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--stem", default=DEFAULT_STEM)
  args = parser.parse_args(argv)
  input_path = args.input.resolve()
  report = build_report(
    json.loads(input_path.read_text(encoding="utf-8")),
    input_path=input_path,
  )
  paths = write_bundle(
    report,
    output_dir=args.output_dir,
    stem=str(args.stem),
    input_path=input_path,
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
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
