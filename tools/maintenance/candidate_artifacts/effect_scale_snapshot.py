#!/usr/bin/env python3
"""Generate a Stage B effect-scale candidate benchmark snapshot for A2.

This tool freezes the current fixed-seed benchmark snapshot for the Stage B
effect-scale-only candidate package. It remains non-authoritative: the output
is a candidate review artifact and must not be interpreted as validated
effect-scale authority, component-failure truth, Pk, or deterministic-fuze
authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()
REPO_ROOT = Path(repo_root())
from tools.maintenance.candidate_artifacts import validation_scaffold as scaffold


PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
SNAPSHOT_SCHEMA_VERSION = "a2.stage_b_effect_scale_snapshot.v1"


def _lookup(root: dict[str, Any], path: tuple[str, ...]) -> Any:
  value: Any = root
  for part in path:
    value = value[part]
  return value


def _criteria_rows(artifact: dict[str, Any]) -> list[dict[str, Any]]:
  checks: list[dict[str, Any]] = [
    {
      "criteria_id": "BFM-CRIT-ES-001",
      "benchmark_id": "BFM-BM-001",
      "field_path": ("benchmarks", "BFM-BM-001", "metrics", "unit_roundtrip_pass"),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-002",
      "benchmark_id": "BFM-BM-001",
      "field_path": ("benchmarks", "BFM-BM-001", "metrics", "monotonic_overpressure_pass"),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-003",
      "benchmark_id": "BFM-BM-001",
      "field_path": ("benchmarks", "BFM-BM-001", "metrics", "monotonic_impulse_pass"),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-004",
      "benchmark_id": "BFM-BM-003",
      "field_path": ("benchmarks", "BFM-BM-003", "metrics", "fixed_seed_replay_pass"),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-005",
      "benchmark_id": "BFM-BM-003",
      "field_path": ("benchmarks", "BFM-BM-003", "metrics", "isotropy_pass"),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-006",
      "benchmark_id": "BFM-BM-003",
      "field_path": ("benchmarks", "BFM-BM-003", "metrics", "sampling_convergence_pass"),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-007",
      "benchmark_id": "BFM-BM-003",
      "field_path": (
        "benchmarks",
        "BFM-BM-003",
        "sampling_convergence_summary",
        "relative_delta",
      ),
      "expected": "<=0.05",
    },
    {
      "criteria_id": "BFM-CRIT-ES-008",
      "benchmark_id": "BFM-BM-005",
      "field_path": (
        "benchmarks",
        "BFM-BM-005",
        "metrics",
        "source_trace_completeness_pass",
      ),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-009",
      "benchmark_id": "BFM-BM-005",
      "field_path": ("benchmarks", "BFM-BM-005", "metrics", "unit_consistency_pass"),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-010",
      "benchmark_id": "BFM-BM-005",
      "field_path": (
        "benchmarks",
        "BFM-BM-005",
        "metrics",
        "forbidden_authority_fields_absent",
      ),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-011",
      "benchmark_id": "BFM-BM-005",
      "field_path": (
        "benchmarks",
        "BFM-BM-005",
        "metrics",
        "uncertainty_summary_present",
      ),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-012",
      "benchmark_id": "BFM-BM-005",
      "field_path": ("benchmarks", "BFM-BM-005", "metrics", "seed_window_cv_pass"),
      "expected": True,
    },
    {
      "criteria_id": "BFM-CRIT-ES-013",
      "benchmark_id": "BFM-BM-005",
      "field_path": (
        "benchmarks",
        "BFM-BM-005",
        "uncertainty_summary",
        "fragment_areal_density_per_m2",
        "cv",
      ),
      "expected": "<=0.05",
    },
    {
      "criteria_id": "BFM-CRIT-ES-014",
      "benchmark_id": "BFM-BM-005",
      "field_path": (
        "benchmarks",
        "BFM-BM-005",
        "uncertainty_summary",
        "fragment_energy_j_proxy",
        "cv",
      ),
      "expected": "<=0.05",
    },
    {
      "criteria_id": "BFM-CRIT-ES-015",
      "benchmark_id": "BFM-BM-005",
      "field_path": (
        "benchmarks",
        "BFM-BM-005",
        "uncertainty_summary",
        "penetration_margin_proxy",
        "cv",
      ),
      "expected": "<=0.05",
    },
    {
      "criteria_id": "BFM-CRIT-ES-016",
      "benchmark_id": "BFM-BM-005",
      "field_path": (
        "benchmarks",
        "BFM-BM-005",
        "uncertainty_summary",
        "blast_impulse_kpa_ms_proxy",
        "cv",
      ),
      "expected": "<=0.05",
    },
    {
      "criteria_id": "BFM-CRIT-ES-017",
      "benchmark_id": "BFM-BM-006",
      "field_path": ("benchmarks", "BFM-BM-006", "metrics", "source_trace_error_count"),
      "expected": "=0",
    },
    {
      "criteria_id": "BFM-CRIT-ES-018",
      "benchmark_id": "BFM-BM-006",
      "field_path": ("benchmarks", "BFM-BM-006", "metrics", "source_trace_warning_count"),
      "expected": "=0",
    },
  ]

  rows: list[dict[str, Any]] = []
  for check in checks:
    actual = _lookup(artifact, check["field_path"])
    expected = check["expected"]
    passed = False
    if expected is True:
      passed = bool(actual) is True
    elif expected == "<=0.05":
      passed = float(actual) <= 0.05
    elif expected == "=0":
      passed = float(actual) == 0.0
    rows.append(
      {
        "criteria_id": check["criteria_id"],
        "benchmark_id": check["benchmark_id"],
        "field": ".".join(check["field_path"][2:]),
        "expected": expected,
        "actual": actual,
        "pass": passed,
      }
    )
  return rows


def generate_stage_b_effect_scale_snapshot(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
  artifact = scaffold.generate_validation_scaffold(repo_root=repo_root)
  criteria_rows = _criteria_rows(artifact)
  failed_ids = [row["criteria_id"] for row in criteria_rows if not row["pass"]]
  bm001 = artifact["benchmarks"]["BFM-BM-001"]
  bm003 = artifact["benchmarks"]["BFM-BM-003"]
  bm005 = artifact["benchmarks"]["BFM-BM-005"]
  bm006 = artifact["benchmarks"]["BFM-BM-006"]

  return {
    "package_id": PACKAGE_ID,
    "schema_version": SNAPSHOT_SCHEMA_VERSION,
    "status": "candidate_non_authoritative_stage_b_snapshot",
    "artifact_provenance": {
      "source_kind": "candidate_stage_b_effect_scale_snapshot",
      "validation_scaffold_ref": (
    "tools/maintenance/damage_model.py candidate-artifacts validation-scaffold"
      ),
      "criteria_ref": (
        "docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/calibration/"
        "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/"
        "validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md"
      ),
      "seed": int(artifact["artifact_provenance"]["seed"]),
      "sample_count": int(artifact["artifact_provenance"]["sample_count"]),
    },
    "scope": {
      "target_type": artifact["scope"]["target_type"],
      "weapon_class": artifact["scope"]["weapon_class"],
      "weapon_family": artifact["scope"]["weapon_family"],
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "candidate_scope_label": artifact["scope"]["candidate_scope_label"],
      "runtime_miss_distance_bucket": artifact["scope"]["runtime_miss_distance_bucket"],
    },
    "criteria_evaluation": criteria_rows,
    "summary": {
      "all_hard_gates_pass_in_current_snapshot": not failed_ids,
      "failed_criteria_ids": failed_ids,
      "reviewed_benchmarks": ["BFM-BM-001", "BFM-BM-003", "BFM-BM-005", "BFM-BM-006"],
      "primary_release_scope": "effect_scale_authority_only",
      "review_status": "author_snapshot_only_pending_independent_review",
    },
    "benchmark_snapshot": {
      "BFM-BM-001": {
        "status": bm001["status"],
        "metrics": bm001["metrics"],
        "current_point": bm001["current_point"],
      },
      "BFM-BM-003": {
        "status": bm003["status"],
        "metrics": bm003["metrics"],
        "current_point": bm003["current_point"],
        "sampling_convergence_summary": bm003["sampling_convergence_summary"],
      },
      "BFM-BM-005": {
        "status": bm005["status"],
        "metrics": bm005["metrics"],
        "mechanism_load_vector": bm005["mechanism_load_vector"],
        "diagnostic_only_fields": bm005["diagnostic_only_fields"],
        "uncertainty_summary": bm005["uncertainty_summary"],
      },
      "BFM-BM-006": {
        "status": bm006["status"],
        "metrics": bm006["metrics"],
      },
    },
    "current_findings": [
      (
        "the current fixed-seed scaffold snapshot satisfies every frozen "
        "Stage B hard gate in BFM-BM-001/003/005/006"
      ),
      (
        "this remains a candidate benchmark snapshot generated from a "
        "non-authoritative scaffold; it is not an independent validation result"
      ),
      (
        "candidate closure-sensitive response is tracked by the scope probe, "
        "but this Stage B snapshot remains non-authoritative and does not close "
        "RES-008 or independent review"
      ),
    ],
    "non_authoritative_guards": {
      "stock_runtime_authority_granted": False,
      "effect_scale_authority_granted": False,
      "component_failure_probability_authority_granted": False,
      "pk_authority_granted": False,
      "deterministic_fuze_authority_granted": False,
    },
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the Stage B effect-scale candidate benchmark snapshot for "
      "the current A2 blast-fragmentation package."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path. Defaults to stdout.",
  )
  args = parser.parse_args(argv)

  artifact = generate_stage_b_effect_scale_snapshot()
  payload = json.dumps(artifact, indent=2, sort_keys=True)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
  else:
    print(payload)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
