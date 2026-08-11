#!/usr/bin/env python3
"""Generate the Stage B effect-scale independent-review gate for A2.

This gate is intentionally narrower than release readiness. It reviews the
author-side Stage B closeout evidence for the focused residual slice, records
which review checks pass, and preserves all upstream provenance, identity,
mechanism-source and stock-runtime blockers. A review pass here is not a stock
descriptor release and is not a validation-manifest promotion.
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

from tools.maintenance.a2_packet_paths import (  # noqa: E402
  CANDIDATE_PACKAGE_DIR as A2_CANDIDATE_PACKAGE_DIR,
)
from tools.maintenance.release_governance import effect_scale_release_closeout as closeout
from tools.maintenance.release_governance import effect_scale_release_readiness as readiness


PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
REVIEW_GATE_SCHEMA_VERSION = "a2.stage_b_independent_review_gate.v1"
FOCUSED_RESIDUAL_IDS = ("RES-007", "RES-008", "RES-010", "RES-011", "RES-012")
UPSTREAM_RELEASE_BLOCKER_IDS = (
  "RES-001",
  "RES-002",
  "RES-003",
  "RES-004",
  "RES-005",
  "RES-006",
)
PACKAGE_DIR = (
  A2_CANDIDATE_PACKAGE_DIR
)


def _display_path(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving relative_to; differs from manifest_integrity._display_path (resolve).
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)


def _check(check_id: str, summary: str, passed: bool) -> dict[str, Any]:
  return {
    "check_id": check_id,
    "summary": summary,
    "pass": bool(passed),
  }


def _review_gate_result(checks: list[dict[str, Any]]) -> str:
  if all(row["pass"] for row in checks):
    return "review_passed"
  return "blocked"


def _all_runtime_bucket(rows: list[dict[str, Any]], expected: str) -> bool:
  return all(row.get("runtime_miss_distance_bucket") == expected for row in rows)


def _near_miss_bucket_review(closeout_artifact: dict[str, Any]) -> dict[str, Any]:
  closeout_row = closeout_artifact["near_miss_bucket_closeout"]
  rows = list(closeout_row["rows"])
  standoffs = [row["standoff_m"] for row in rows]
  metrics = closeout_row["metrics"]
  checks = [
    _check(
      "IR-RES007-001",
      "author-side near-miss bucket closeout is complete",
      closeout_row["author_side_closeout_complete"],
    ),
    _check(
      "IR-RES007-002",
      "bucket sensitivity uses the retained 0.25/0.35/0.45 m probe set",
      standoffs == [0.25, 0.35, 0.45],
    ),
    _check(
      "IR-RES007-003",
      "0.35 m anchor is present and retained in the probe rows",
      0.35 in standoffs and metrics["anchor_present"],
    ),
    _check(
      "IR-RES007-004",
      "blast scaled distance is monotonic increasing across the probe set",
      metrics["blast_scaled_distance_monotonic_increasing_pass"],
    ),
    _check(
      "IR-RES007-005",
      "fragment areal density is monotonic decreasing across the probe set",
      metrics["fragment_areal_density_monotonic_decreasing_pass"],
    ),
    _check(
      "IR-RES007-006",
      "all retained probe rows stay in the runtime coarse near_miss bucket",
      metrics["runtime_bucket_consistent_pass"]
      and _all_runtime_bucket(rows, "near_miss"),
    ),
    _check(
      "IR-RES007-007",
      "author-side closeout still keeps release blocked rather than self-promoting",
      closeout_row["release_blocked"],
    ),
  ]
  return {
    "residual_id": "RES-007",
    "review_area": "bucket_sensitivity",
    "review_gate_result": _review_gate_result(checks),
    "release_gate_result": "blocked_by_upstream_release_dependencies",
    "register_status_after_review": "remains_open_release_blocked",
    "probe_id": closeout_row["probe_id"],
    "standoff_probe_m": standoffs,
    "runtime_bucket": "near_miss",
    "checks": checks,
    "review_finding": (
      "the retained three-point near-miss bucket sensitivity probe is "
      "internally consistent for independent-review purposes"
    ),
    "release_dependency": (
      "release interpretation remains blocked by upstream provenance, "
      "identity, target/warhead and mechanism-source residuals"
    ),
  }


def _beam_high_scope_review(closeout_artifact: dict[str, Any]) -> dict[str, Any]:
  closeout_row = closeout_artifact["beam_high_scope_closeout"]
  closure_probe = closeout_row["closure_probe"]
  aspect_guard = closeout_row["aspect_guard"]
  closure_rows = list(closure_probe["rows"])
  closures = [row["closure_mps"] for row in closure_rows]
  metrics = closure_probe["metrics"]
  rejected_labels = set(aspect_guard["rejected_scope_labels"])
  required_rejections = {
    "head_on",
    "tail_chase",
    "high_off_boresight",
    "direct_hit",
    "closure_bucket != high",
    "weapon_family != blast_fragmentation",
  }
  checks = [
    _check(
      "IR-RES008-001",
      "author-side beam/high scope closeout is complete",
      closeout_row["author_side_closeout_complete"],
    ),
    _check(
      "IR-RES008-002",
      "closure sensitivity uses the retained 700/900/1100 mps probe set",
      closures == [700.0, 900.0, 1100.0],
    ),
    _check(
      "IR-RES008-003",
      "closure response is active and not constant across retained rows",
      metrics["mechanism_response_active"]
      and metrics["candidate_closure_sensitive_response_observed"]
      and not metrics["mechanism_response_constant_across_closure"],
    ),
    _check(
      "IR-RES008-004",
      "closure probe remains inside the runtime near_miss bucket",
      metrics["runtime_bucket_consistent_pass"]
      and _all_runtime_bucket(closure_rows, "near_miss"),
    ),
    _check(
      "IR-RES008-005",
      "aspect guard accepts only beam",
      aspect_guard["accepted_scope_labels"] == ["beam"],
    ),
    _check(
      "IR-RES008-006",
      "aspect guard rejects all retained out-of-scope labels",
      required_rejections.issubset(rejected_labels),
    ),
    _check(
      "IR-RES008-007",
      "author-side probe did not self-close RES-008 or claim independent review",
      not metrics["res008_closed_by_probe"]
      and not metrics["independent_review_complete"],
    ),
  ]
  return {
    "residual_id": "RES-008",
    "review_area": "beam_high_scope_leakage",
    "review_gate_result": _review_gate_result(checks),
    "release_gate_result": "blocked_by_mechanism_source_residuals",
    "register_status_after_review": "remains_open_release_blocked",
    "closure_probe_id": closure_probe["probe_id"],
    "closure_probe_mps": closures,
    "accepted_scope_labels": list(aspect_guard["accepted_scope_labels"]),
    "rejected_scope_labels": list(aspect_guard["rejected_scope_labels"]),
    "checks": checks,
    "review_finding": (
      "beam/high scope leakage checks pass: only the beam label is "
      "accepted and the retained closure probe stays inside the candidate scope"
    ),
    "release_dependency": (
      "closure physics authority remains blocked by open target, warhead, "
      "fragment and blast mechanism-source residuals"
    ),
  }


def _validation_result_review(closeout_artifact: dict[str, Any]) -> dict[str, Any]:
  validation = closeout_artifact["validation_result_closeout"]
  execution = closeout_artifact["benchmark_result_execution_record"]
  counts = validation["criteria_counts"]
  checks = [
    _check(
      "IR-RES010-001",
      "all frozen Stage B hard-gate criteria pass in the retained execution record",
      counts["all_hard_gates_pass"]
      and counts["criteria_count"] == 18
      and counts["failed_criteria_count"] == 0,
    ),
    _check(
      "IR-RES010-002",
      "result execution record keeps hard_gate_pass_is_release=false",
      execution["hard_gate_pass_is_release"] is False
      and validation["hard_gate_pass_is_release"] is False,
    ),
    _check(
      "IR-RES010-003",
      "three author-side evidence artifact hashes are retained",
      len(validation["artifact_hashes"]) == 3,
    ),
    _check(
      "IR-RES010-004",
      "reviewed benchmark set remains the frozen Stage B effect-scale set",
      validation["reviewed_benchmarks"]
      == ["BFM-BM-001", "BFM-BM-003", "BFM-BM-005", "BFM-BM-006"],
    ),
    _check(
      "IR-RES010-005",
      "formal validation manifest is not promoted by this independent review",
      validation["validation_manifest_status"] == "not_promoted_to_validated",
    ),
    _check(
      "IR-RES010-006",
      "author-side closeout remains release-blocked",
      validation["release_blocked"],
    ),
  ]
  return {
    "residual_id": "RES-010",
    "review_area": "validation_result_promotion",
    "review_gate_result": _review_gate_result(checks),
    "release_gate_result": "blocked_formal_validation_promotion",
    "register_status_after_review": "remains_open_release_blocked",
    "criteria_counts": dict(counts),
    "artifact_hash_count": len(validation["artifact_hashes"]),
    "reviewed_benchmarks": list(validation["reviewed_benchmarks"]),
    "validation_manifest_status": validation["validation_manifest_status"],
    "formal_validation_promotion_result": "blocked",
    "formal_validation_promotion_blocked_by": list(UPSTREAM_RELEASE_BLOCKER_IDS),
    "checks": checks,
    "review_finding": (
      "the retained Stage B execution record is complete and review-passing, "
      "but this gate does not promote the validation manifest"
    ),
    "release_dependency": (
      "formal validation result promotion waits on release-grade provenance, "
      "identity, target/warhead assumptions and mechanism-source residual closure"
    ),
  }


def _uncertainty_review(closeout_artifact: dict[str, Any]) -> dict[str, Any]:
  uncertainty = closeout_artifact["uncertainty_closeout"]
  cv_rows = list(uncertainty["cv_rows"])
  checks = [
    _check(
      "IR-RES011-001",
      "author-side uncertainty closeout is complete",
      uncertainty["author_side_closeout_complete"],
    ),
    _check(
      "IR-RES011-002",
      "seed-window CV gate passes",
      uncertainty["seed_window_cv_pass"],
    ),
    _check(
      "IR-RES011-003",
      "all retained CV rows pass the <=0.05 threshold",
      all(row["pass"] for row in cv_rows),
    ),
    _check(
      "IR-RES011-004",
      "uncertainty review keeps the result at snapshot scope only",
      uncertainty["release_blocked"],
    ),
  ]
  return {
    "residual_id": "RES-011",
    "review_area": "uncertainty_snapshot",
    "review_gate_result": _review_gate_result(checks),
    "release_gate_result": "blocked_uncertainty_coverage_release",
    "register_status_after_review": "remains_open_release_blocked",
    "seed_window_cv_pass": bool(uncertainty["seed_window_cv_pass"]),
    "cv_rows": cv_rows,
    "coverage_release_result": "blocked",
    "coverage_release_blocked_by": list(UPSTREAM_RELEASE_BLOCKER_IDS),
    "checks": checks,
    "review_finding": (
      "the retained seed-window CV snapshot is review-passing for the "
      "candidate evidence surface"
    ),
    "release_dependency": (
      "release-grade uncertainty coverage still depends on provenance, "
      "identity and mechanism-source residual closure"
    ),
  }


def _independence_review(closeout_artifact: dict[str, Any]) -> dict[str, Any]:
  independence = closeout_artifact["independence_review_dependency_trace"]
  rows = list(independence["benchmark_independence_rows"])
  row_by_benchmark = {row["benchmark_id"]: row for row in rows}
  checks = [
    _check(
      "IR-RES012-001",
      "author-side benchmark/input dependency trace is complete",
      independence["author_side_closeout_complete"],
    ),
    _check(
      "IR-RES012-002",
      "all six Stage B benchmark independence rows are retained",
      list(row_by_benchmark) == [
        "BFM-BM-001",
        "BFM-BM-002",
        "BFM-BM-003",
        "BFM-BM-004",
        "BFM-BM-005",
        "BFM-BM-006",
      ],
    ),
    _check(
      "IR-RES012-003",
      "integrated BFM-BM-005 remains explicitly not independent real validation",
      row_by_benchmark["BFM-BM-005"]["independence_class"]
      == "not_independent_real_validation"
      and row_by_benchmark["BFM-BM-005"]["audit_outcome"]
      == "candidate_hygiene_only_not_independent_validation",
    ),
    _check(
      "IR-RES012-004",
      "administrative BFM-BM-006 is not used as physics validation",
      row_by_benchmark["BFM-BM-006"]["independence_class"]
      == "administratively_independent"
      and "physics validation" in row_by_benchmark["BFM-BM-006"]["forbidden_claim"],
    ),
    _check(
      "IR-RES012-005",
      "independence closeout remains release-blocked rather than self-promoting",
      independence["release_blocked"],
    ),
  ]
  return {
    "residual_id": "RES-012",
    "review_area": "benchmark_input_independence",
    "review_gate_result": _review_gate_result(checks),
    "release_gate_result": "blocked_by_provenance_identity_and_source_residuals",
    "register_status_after_review": "remains_open_release_blocked",
    "benchmark_independence_rows": rows,
    "checks": checks,
    "review_finding": (
      "the retained benchmark/input separation audit is review-passing "
      "because it preserves limited roles and forbidden claims explicitly"
    ),
    "release_dependency": (
      "release-grade independence cannot be promoted until source provenance, "
      "surrogate identity and mechanism-source residuals close"
    ),
  }


def _release_blocking_conditions() -> list[dict[str, str]]:
  return [
    {
      "blocker_id": "BLOCK-IR-001",
      "residual_id": "RES-001",
      "summary": "release-grade source provenance remains open",
    },
    {
      "blocker_id": "BLOCK-IR-002",
      "residual_id": "RES-002",
      "summary": "release-grade surrogate identity remains open",
    },
    {
      "blocker_id": "BLOCK-IR-003",
      "residual_id": "RES-003",
      "summary": "target geometry source and assumptions remain unaudited for release authority",
    },
    {
      "blocker_id": "BLOCK-IR-004",
      "residual_id": "RES-004",
      "summary": "warhead class scope and sensitivity remain source-blocked",
    },
    {
      "blocker_id": "BLOCK-IR-005",
      "residual_id": "RES-005",
      "summary": "fragment mechanism source residual remains open",
    },
    {
      "blocker_id": "BLOCK-IR-006",
      "residual_id": "RES-006",
      "summary": "blast mechanism source residual remains open",
    },
    {
      "blocker_id": "BLOCK-IR-007",
      "residual_id": "RES-013/014-boundary",
      "summary": "stock runtime, Pk and deterministic-fuze authority remain outside this gate",
    },
  ]


def _residual_result_summary(
  review_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  return [
    {
      "residual_id": row["residual_id"],
      "review_area": row["review_area"],
      "review_gate_result": row["review_gate_result"],
      "release_gate_result": row["release_gate_result"],
      "register_status_after_review": row["register_status_after_review"],
      "all_review_checks_pass": all(check["pass"] for check in row["checks"]),
      "release_dependency": row["release_dependency"],
    }
    for row in review_rows
  ]


def generate_stage_b_independent_review_gate(
  *,
  repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
  closeout_artifact = closeout.generate_stage_b_release_closeout(repo_root=repo_root)
  readiness_artifact = readiness.generate_stage_b_release_readiness_gate(
    repo_root=repo_root
  )
  review_rows = [
    _near_miss_bucket_review(closeout_artifact),
    _beam_high_scope_review(closeout_artifact),
    _validation_result_review(closeout_artifact),
    _uncertainty_review(closeout_artifact),
    _independence_review(closeout_artifact),
  ]
  review_passed = all(row["review_gate_result"] == "review_passed" for row in review_rows)
  release_blockers = _release_blocking_conditions()
  return {
    "package_id": PACKAGE_ID,
    "schema_version": REVIEW_GATE_SCHEMA_VERSION,
    "status": "independent_review_passed_release_blocked"
    if review_passed
    else "independent_review_blocked_release_blocked",
    "generated_on": "2026-05-31",
    "reviewer_role": "A2-RC-STAGE-B-INDEPENDENT-REVIEW",
    "model_reasoning_record": "inherited_from_parent_no_override_requested",
    "review_target": "stage_b_effect_scale_independent_review_only",
    "release_target": "effect_scale_authority_only",
    "scope": dict(closeout_artifact["scope"]),
    "focused_residual_ids": list(FOCUSED_RESIDUAL_IDS),
    "review_decision": {
      "independent_review_complete": review_passed,
      "focused_review_passed": review_passed,
      "review_passed_residual_ids": [
        row["residual_id"]
        for row in review_rows
        if row["review_gate_result"] == "review_passed"
      ],
      "review_blocked_residual_ids": [
        row["residual_id"]
        for row in review_rows
        if row["review_gate_result"] != "review_passed"
      ],
      "hard_gate_pass_is_release": False,
      "formal_validation_manifest_promoted": False,
      "stock_runtime_authority_granted": False,
    },
    "release_decision": {
      "release_ready": False,
      "release_blocked": True,
      "current_hard_gate_snapshot_pass": closeout_artifact["release_decision"][
        "current_hard_gate_snapshot_pass"
      ],
      "hard_gate_pass_is_release": False,
      "blocked_even_when_hard_gates_pass": True,
      "release_blocked_by_residual_ids": [
        row["residual_id"] for row in release_blockers
      ],
      "stage_c_component_probability_release_included": False,
      "stock_runtime_authority_granted": False,
    },
    "retained_evidence_refs": {
      "author_side_closeout": _display_path(
        PACKAGE_DIR
        / "retained_artifacts"
        / "stage_b_effect_scale_20260531"
        / "stage_b_release_closeout.json",
        repo_root,
      ),
      "author_side_retained_pack": _display_path(
        PACKAGE_DIR
        / "retained_artifacts"
        / "stage_b_effect_scale_20260530"
        / "manifest.json",
        repo_root,
      ),
      "review_doc": _display_path(
        PACKAGE_DIR
        / "validation_independent_review_stage_b_effect_scale_20260531.zh.md",
        repo_root,
      ),
    },
    "readiness_gate_snapshot": {
      "status": readiness_artifact["status"],
      "readiness_level": readiness_artifact["readiness_level"],
      "hard_gate_pass_is_release": readiness_artifact["release_decision"][
        "hard_gate_pass_is_release"
      ],
      "blocking_residual_ids": list(readiness_artifact["blocking_residual_ids"]),
      "note": (
        "this independent review gate is a review record; release integration "
        "must still keep upstream blockers before any readiness promotion"
      ),
    },
    "near_miss_bucket_review": review_rows[0],
    "beam_high_scope_leakage_review": review_rows[1],
    "validation_result_promotion_review": review_rows[2],
    "uncertainty_review": review_rows[3],
    "benchmark_input_independence_review": review_rows[4],
    "residual_review_gate_results": _residual_result_summary(review_rows),
    "release_blocking_conditions": release_blockers,
    "current_findings": [
      (
        "RES-007/008/010/011/012 have review-passing independent-review "
        "checks against the retained author-side Stage B closeout surface"
      ),
      (
        "the review pass does not promote validation_manifest_status and "
        "does not convert the hard-gate pass into release authority"
      ),
      (
        "release remains blocked by RES-001/002 plus target, warhead, "
        "fragment and blast mechanism-source residuals"
      ),
    ],
    "explicit_boundaries": [
      "do not treat review_passed as release_ready",
      "do not promote validation_manifest_status to validated from this gate",
      "do not release stock runtime authority or create a stock descriptor",
      "do not release Stage C component probability, Pk or deterministic fuze authority",
    ],
    "non_authoritative_guards": {
      "stock_descriptor_created": False,
      "stock_database_authority_granted": False,
      "stock_runtime_authority_granted": False,
      "effect_scale_authority_granted": False,
      "effect_scale_authority_in_stock": False,
      "component_failure_probability_authority_granted": False,
      "component_failure_probability_authority_in_stock": False,
      "pk_authority_granted": False,
      "deterministic_fuze_authority_granted": False,
      "candidate_bundle_role": "independent_review_record_only",
    },
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the Stage B effect-scale independent-review gate for the "
      "current A2 blast-fragmentation candidate package."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path. Defaults to stdout.",
  )
  args = parser.parse_args(argv)

  artifact = generate_stage_b_independent_review_gate()
  payload = json.dumps(artifact, indent=2, sort_keys=True)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
  else:
    print(payload)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
