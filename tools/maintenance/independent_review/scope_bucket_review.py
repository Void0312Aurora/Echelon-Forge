#!/usr/bin/env python3
"""Gate Stage B scope/bucket independent review for RES-007 and RES-008.

This tool is intentionally narrower than release readiness. It reruns the
existing scope boundary probe, consumes retained Stage B result-pack and
independent-review evidence, and records whether the near_miss_0_35m and
beam/high scope boundaries are review-complete for the Stage B scope-only slice.

It must fail closed when review evidence is missing or incomplete, and it never
promotes stock runtime, Pk, deterministic-fuze, effect-scale, or component
probability authority.
"""

from __future__ import annotations

import argparse
import hashlib
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

from tools.maintenance.retained_artifacts.manifest_integrity import _sha256_file
from tools.maintenance.candidate_artifacts import scope_boundary_probe as boundary_probe

PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
GATE_SCHEMA_VERSION = "a2.scope_bucket_independent_review_gate.v1"
MANIFEST_SCHEMA_VERSION = "a2.scope_bucket_independent_review_retained_artifacts.v1"
GENERATED_ON = "2026-05-31"
EXPECTED_STANDOFFS_M = [0.25, 0.35, 0.45]
EXPECTED_CLOSURES_MPS = [700.0, 900.0, 1100.0]
EXPECTED_REJECTED_LABELS = [
  "head_on",
  "tail_chase",
  "high_off_boresight",
  "direct_hit",
  "closure_bucket != high",
  "weapon_family != blast_fragmentation",
]
UPSTREAM_RELEASE_BLOCKERS = [
  "RES-001",
  "RES-002",
  "RES-003",
  "RES-004",
  "RES-005",
  "RES-006",
  "RES-013/014-boundary",
]
PACKAGE_DIR = (
  REPO_ROOT
  / "docs"
  / "task"
  / "air_combat"
  / "archive"
  / "a2_high_fidelity_damage_model"
  / "calibration"
  / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)
DEFAULT_RETAINED_DIR = (
  PACKAGE_DIR
  / "retained_artifacts"
  / "scope_bucket_independent_review_20260531"
)

def _display_path(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving relative_to; differs from manifest_integrity._display_path (resolve).
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)

def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)

def _payload_sha256(payload: dict[str, Any]) -> str:
  return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()

def _load_json(path: Path) -> dict[str, Any] | None:
  if not path.is_file():
    return None
  return json.loads(path.read_text(encoding="utf-8"))

def _read_text(path: Path) -> str:
  if not path.is_file():
    return ""
  return path.read_text(encoding="utf-8")

def _check(check_id: str, summary: str, passed: bool) -> dict[str, Any]:
  return {
    "check_id": check_id,
    "summary": summary,
    "pass": bool(passed),
  }

def _missing_evidence(
  *,
  evidence_id: str,
  path: Path,
  required_for: str,
  blocker: str,
  repo_root: Path,
) -> dict[str, str]:
  return {
    "evidence_id": evidence_id,
    "path": _display_path(path, repo_root),
    "required_for": required_for,
    "blocker": blocker,
  }

def _failed_check_blockers(
  *,
  residual_id: str,
  checks: list[dict[str, Any]],
) -> list[dict[str, str]]:
  return [
    {
      "residual_id": residual_id,
      "check_id": str(check["check_id"]),
      "blocker": str(check["summary"]),
    }
    for check in checks
    if not check["pass"]
  ]

def _scope_manifest_review(scope_manifest_text: str) -> dict[str, Any]:
  checks = [
    _check(
      "SCOPE-MANIFEST-001",
      "scope manifest freezes the expected package id",
      PACKAGE_ID in scope_manifest_text,
    ),
    _check(
      "SCOPE-MANIFEST-002",
      "scope manifest records near_miss_0_35m as the candidate scope label",
      "near_miss_0_35m" in scope_manifest_text,
    ),
    _check(
      "SCOPE-MANIFEST-003",
      "scope manifest records beam/high axes",
      "`beam`" in scope_manifest_text and "`high`" in scope_manifest_text,
    ),
    _check(
      "SCOPE-MANIFEST-004",
      "scope manifest records runtime coarse near_miss guard",
      "runtime coarse bucket near_miss" in scope_manifest_text
      and "IND-GUARD-004" in scope_manifest_text,
    ),
    _check(
      "SCOPE-MANIFEST-005",
      "scope manifest lists all required out-of-scope rejection labels",
      all(label in scope_manifest_text for label in EXPECTED_REJECTED_LABELS),
    ),
  ]
  return {
    "status": "scope_manifest_complete" if all(row["pass"] for row in checks) else "scope_manifest_incomplete",
    "checks": checks,
  }

def _probe_review(probe: dict[str, Any]) -> dict[str, Any]:
  miss_distance = probe["miss_distance_probe"]
  closure = probe["closure_probe"]
  aspect = probe["aspect_guard_probe"]
  miss_rows = list(miss_distance["rows"])
  closure_rows = list(closure["rows"])
  rejected_labels = list(aspect["rejected_scope_labels"])
  missing_rejections = [
    label for label in EXPECTED_REJECTED_LABELS if label not in rejected_labels
  ]

  miss_checks = [
    _check(
      "PROBE-RES007-001",
      "miss-distance probe uses 0.25/0.35/0.45 m rows",
      [row["standoff_m"] for row in miss_rows] == EXPECTED_STANDOFFS_M,
    ),
    _check(
      "PROBE-RES007-002",
      "0.35 m anchor is present",
      bool(miss_distance["metrics"]["anchor_present"]),
    ),
    _check(
      "PROBE-RES007-003",
      "blast scaled distance is monotonic increasing",
      bool(
        miss_distance["metrics"][
          "blast_scaled_distance_monotonic_increasing_pass"
        ]
      ),
    ),
    _check(
      "PROBE-RES007-004",
      "fragment areal density is monotonic decreasing",
      bool(
        miss_distance["metrics"][
          "fragment_areal_density_monotonic_decreasing_pass"
        ]
      ),
    ),
    _check(
      "PROBE-RES007-005",
      "all miss-distance rows stay in runtime coarse near_miss bucket",
      bool(miss_distance["metrics"]["runtime_bucket_consistent_pass"])
      and all(row["runtime_miss_distance_bucket"] == "near_miss" for row in miss_rows),
    ),
  ]
  beam_high_checks = [
    _check(
      "PROBE-RES008-001",
      "closure probe uses 700/900/1100 mps rows",
      [row["closure_mps"] for row in closure_rows] == EXPECTED_CLOSURES_MPS,
    ),
    _check(
      "PROBE-RES008-002",
      "closure response is active and not constant across retained rows",
      bool(closure["metrics"]["mechanism_response_active"])
      and bool(closure["metrics"]["candidate_closure_sensitive_response_observed"])
      and not bool(closure["metrics"]["mechanism_response_constant_across_closure"]),
    ),
    _check(
      "PROBE-RES008-003",
      "closure rows stay in runtime coarse near_miss bucket",
      bool(closure["metrics"]["runtime_bucket_consistent_pass"])
      and all(row["runtime_miss_distance_bucket"] == "near_miss" for row in closure_rows),
    ),
    _check(
      "PROBE-RES008-004",
      "closure probe does not self-close RES-008",
      not bool(closure["metrics"]["res008_closed_by_probe"]),
    ),
    _check(
      "PROBE-RES008-005",
      "scope guard accepts only beam",
      aspect["accepted_scope_labels"] == ["beam"],
    ),
    _check(
      "PROBE-RES008-006",
      "scope guard rejects every required out-of-scope label",
      not missing_rejections,
    ),
  ]

  return {
    "status": (
      "probe_coverage_complete"
      if all(row["pass"] for row in miss_checks + beam_high_checks)
      else "probe_coverage_incomplete"
    ),
    "probe_coverage_summary": {
      "miss_distance_probe_id": miss_distance["probe_id"],
      "standoff_rows_m": [row["standoff_m"] for row in miss_rows],
      "miss_distance_row_count": len(miss_rows),
      "miss_distance_anchor_present": bool(
        miss_distance["metrics"]["anchor_present"]
      ),
      "runtime_bucket_consistent": bool(
        miss_distance["metrics"]["runtime_bucket_consistent_pass"]
      )
      and bool(closure["metrics"]["runtime_bucket_consistent_pass"]),
      "closure_probe_id": closure["probe_id"],
      "closure_rows_mps": [row["closure_mps"] for row in closure_rows],
      "closure_row_count": len(closure_rows),
      "closure_response_active": bool(
        closure["metrics"]["mechanism_response_active"]
      ),
      "closure_response_review_status": (
        "review_required_from_independent_review_artifact"
      ),
      "aspect_guard_probe_id": aspect["probe_id"],
    },
    "boundary_rejection_coverage": {
      "accepted_scope_labels": list(aspect["accepted_scope_labels"]),
      "required_rejected_scope_labels": list(EXPECTED_REJECTED_LABELS),
      "observed_rejected_scope_labels": rejected_labels,
      "missing_rejected_scope_labels": missing_rejections,
      "all_required_rejections_observed": not missing_rejections,
    },
    "res007_checks": miss_checks,
    "res008_checks": beam_high_checks,
  }

def _result_pack_review(result_pack: dict[str, Any] | None) -> dict[str, Any]:
  if result_pack is None:
    return {
      "status": "missing_result_pack",
      "checks": [
        _check(
          "RESULT-PACK-001",
          "retained Stage B result pack exists",
          False,
        )
      ],
    }

  scope = result_pack.get("scope", {})
  result_summary = result_pack.get("result_table_summary", {})
  release = result_pack.get("release_readiness_interpretation", {})
  scope_audit = result_pack.get("scope_audit_summary", {})
  rows = result_pack.get("independence_audit", [])
  row_by_benchmark = {row.get("benchmark_id"): row for row in rows}
  checks = [
    _check(
      "RESULT-PACK-001",
      "retained Stage B result pack exists",
      True,
    ),
    _check(
      "RESULT-PACK-002",
      "result pack schema is Stage B validation result pack v1",
      result_pack.get("schema_version") == "a2.stage_b_validation_result_pack.v1",
    ),
    _check(
      "RESULT-PACK-003",
      "result pack scope matches near_miss_0_35m beam/high blast-fragmentation",
      scope.get("candidate_scope_label") == "near_miss_0_35m"
      and scope.get("runtime_miss_distance_bucket") == "near_miss"
      and scope.get("aspect_bucket") == "beam"
      and scope.get("closure_bucket") == "high"
      and scope.get("weapon_family") == "blast_fragmentation",
    ),
    _check(
      "RESULT-PACK-004",
      "result pack keeps hard-gate pass below release authority",
      result_summary.get("hard_gate_pass_is_release") is False
      and release.get("release_ready") is False
      and release.get("stock_runtime_authority_granted") is False,
    ),
    _check(
      "RESULT-PACK-005",
      "result pack records complete miss-distance and active closure scope audit",
      scope_audit.get("miss_distance_row_count") == 3
      and scope_audit.get("miss_distance_monotonic_pass") is True
      and scope_audit.get("closure_mechanism_response_active") is True,
    ),
    _check(
      "RESULT-PACK-006",
      "result pack keeps BFM-BM-005 out of independent validation authority",
      row_by_benchmark.get("BFM-BM-005", {}).get("independence_class")
      == "not_independent_real_validation"
      and "authority release"
      in row_by_benchmark.get("BFM-BM-005", {}).get("forbidden_claim", ""),
    ),
  ]
  return {
    "status": (
      "result_pack_complete" if all(row["pass"] for row in checks) else "result_pack_incomplete"
    ),
    "checks": checks,
    "artifact_hashes": result_pack.get("artifact_hashes", []),
    "scope_audit_summary": scope_audit,
    "release_readiness_interpretation": release,
  }

def _independent_review_review(review_gate: dict[str, Any] | None) -> dict[str, Any]:
  if review_gate is None:
    return {
      "status": "missing_independent_review_gate",
      "checks": [
        _check(
          "INDEPENDENT-REVIEW-001",
          "retained Stage B independent-review gate exists",
          False,
        )
      ],
      "residual_rows": {},
    }

  residual_rows = {
    row.get("residual_id"): row
    for row in review_gate.get("residual_review_gate_results", [])
  }
  decision = review_gate.get("review_decision", {})
  release = review_gate.get("release_decision", {})
  guards = review_gate.get("non_authoritative_guards", {})
  checks = [
    _check(
      "INDEPENDENT-REVIEW-001",
      "retained Stage B independent-review gate exists",
      True,
    ),
    _check(
      "INDEPENDENT-REVIEW-002",
      "independent review is complete and focused review passed",
      decision.get("independent_review_complete") is True
      and decision.get("focused_review_passed") is True,
    ),
    _check(
      "INDEPENDENT-REVIEW-003",
      "RES-007 is review-passed in retained independent review",
      residual_rows.get("RES-007", {}).get("review_gate_result")
      == "review_passed",
    ),
    _check(
      "INDEPENDENT-REVIEW-004",
      "RES-008 is review-passed in retained independent review",
      residual_rows.get("RES-008", {}).get("review_gate_result")
      == "review_passed",
    ),
    _check(
      "INDEPENDENT-REVIEW-005",
      "independent review keeps release blocked",
      release.get("release_ready") is False
      and release.get("release_blocked") is True
      and release.get("hard_gate_pass_is_release") is False,
    ),
    _check(
      "INDEPENDENT-REVIEW-006",
      "independent review grants no runtime, component, Pk, or fuze authority",
      guards.get("stock_runtime_authority_granted") is False
      and guards.get("component_failure_probability_authority_granted") is False
      and guards.get("pk_authority_granted") is False
      and guards.get("deterministic_fuze_authority_granted") is False,
    ),
  ]
  return {
    "status": (
      "independent_review_complete"
      if all(row["pass"] for row in checks)
      else "independent_review_incomplete"
    ),
    "checks": checks,
    "residual_rows": residual_rows,
    "review_decision": decision,
    "release_decision": release,
  }

def _residual_decision(
  *,
  residual_id: str,
  review_area: str,
  checks: list[dict[str, Any]],
  release_gate_result: str,
) -> dict[str, Any]:
  blockers = _failed_check_blockers(residual_id=residual_id, checks=checks)
  narrow_pass = not blockers
  return {
    "residual_id": residual_id,
    "review_area": review_area,
    "scope_bucket_review_status": (
      "narrow_stage_b_scope_review_complete" if narrow_pass else "fail_closed"
    ),
    "decision": (
      "narrow_pass_stage_b_scope_only" if narrow_pass else "fail_closed"
    ),
    "residual_register_status_after_gate": "remains_open_release_blocked",
    "release_gate_result": release_gate_result,
    "release_blocked_by_residual_ids": list(UPSTREAM_RELEASE_BLOCKERS),
    "blockers": blockers,
    "checks": checks,
  }

def _authority_guards() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "stock_runtime_authority_granted": False,
    "effect_scale_authority_granted": False,
    "effect_scale_authority_in_stock": False,
    "component_failure_probability_authority_granted": False,
    "component_failure_probability_authority_in_stock": False,
    "pk_authority_granted": False,
    "deterministic_fuze_authority_granted": False,
    "formal_validation_manifest_promoted": False,
    "hard_gate_pass_is_release": False,
  }

def generate_scope_bucket_independent_review_gate(
  *,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = PACKAGE_DIR,
) -> tuple[dict[str, Any], dict[str, Any]]:
  probe = boundary_probe.generate_scope_boundary_probe(repo_root=repo_root)
  retained_stage_b_dir = package_dir / "retained_artifacts" / "stage_b_effect_scale_20260530"
  retained_review_dir = package_dir / "retained_artifacts" / "stage_b_independent_review_20260531"
  scope_manifest_path = (
    package_dir
    / "validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md"
  )
  result_pack_path = retained_stage_b_dir / "stage_b_validation_result_pack.json"
  review_gate_path = retained_review_dir / "stage_b_independent_review_gate.json"
  review_manifest_path = retained_review_dir / "manifest.json"
  review_doc_path = (
    package_dir / "validation_independent_review_stage_b_effect_scale_20260531.zh.md"
  )

  result_pack = _load_json(result_pack_path)
  review_gate = _load_json(review_gate_path)
  review_manifest = _load_json(review_manifest_path)
  scope_manifest_text = _read_text(scope_manifest_path)
  review_doc_text = _read_text(review_doc_path)

  missing_review_evidence: list[dict[str, str]] = []
  if not scope_manifest_text:
    missing_review_evidence.append(
      _missing_evidence(
        evidence_id="EVID-SCOPE-MANIFEST-001",
        path=scope_manifest_path,
        required_for="RES-007/RES-008 scope axis freeze",
        blocker="scope and independence manifest is missing",
        repo_root=repo_root,
      )
    )
  if result_pack is None:
    missing_review_evidence.append(
      _missing_evidence(
        evidence_id="EVID-RESULT-PACK-001",
        path=result_pack_path,
        required_for="Stage B result-pack consumption",
        blocker="retained Stage B result pack JSON is missing",
        repo_root=repo_root,
      )
    )
  if review_gate is None:
    missing_review_evidence.append(
      _missing_evidence(
        evidence_id="EVID-INDEPENDENT-REVIEW-001",
        path=review_gate_path,
        required_for="RES-007/RES-008 independent review",
        blocker="retained Stage B independent-review gate JSON is missing",
        repo_root=repo_root,
      )
    )
  if review_manifest is None:
    missing_review_evidence.append(
      _missing_evidence(
        evidence_id="EVID-INDEPENDENT-REVIEW-MANIFEST-001",
        path=review_manifest_path,
        required_for="retained independent-review artifact chain",
        blocker="retained Stage B independent-review manifest is missing",
        repo_root=repo_root,
      )
    )
  if not review_doc_text:
    missing_review_evidence.append(
      _missing_evidence(
        evidence_id="EVID-INDEPENDENT-REVIEW-DOC-001",
        path=review_doc_path,
        required_for="human-readable independent review record",
        blocker="Stage B independent-review documentation is missing",
        repo_root=repo_root,
      )
    )

  scope_manifest_review = _scope_manifest_review(scope_manifest_text)
  probe_review = _probe_review(probe)
  result_pack_review = _result_pack_review(result_pack)
  independent_review = _independent_review_review(review_gate)
  doc_manifest_checks = [
    _check(
      "REVIEW-DOC-001",
      "independent-review document records review passed and release blocked",
      "independent_review_passed" in review_doc_text
      and "release_blocked" in review_doc_text,
    ),
    _check(
      "REVIEW-MANIFEST-001",
      "independent-review manifest retains the review gate artifact",
      bool(review_manifest)
      and any(
        row.get("artifact_key") == "stage_b_independent_review_gate"
        for row in review_manifest.get("artifacts", [])
      ),
    ),
  ]

  res007_checks = (
    scope_manifest_review["checks"]
    + probe_review["res007_checks"]
    + result_pack_review["checks"]
    + independent_review["checks"]
    + doc_manifest_checks
  )
  res008_checks = (
    scope_manifest_review["checks"]
    + probe_review["res008_checks"]
    + result_pack_review["checks"]
    + independent_review["checks"]
    + doc_manifest_checks
  )
  res007 = _residual_decision(
    residual_id="RES-007",
    review_area="near_miss_0_35m_bucket_boundary",
    checks=res007_checks,
    release_gate_result="release_blocked_by_upstream_and_runtime_boundary_residuals",
  )
  res008 = _residual_decision(
    residual_id="RES-008",
    review_area="beam_high_scope_boundary",
    checks=res008_checks,
    release_gate_result="release_blocked_by_mechanism_source_and_runtime_boundary_residuals",
  )

  both_narrow_pass = (
    res007["decision"] == "narrow_pass_stage_b_scope_only"
    and res008["decision"] == "narrow_pass_stage_b_scope_only"
  )
  gate = {
    "package_id": PACKAGE_ID,
    "schema_version": GATE_SCHEMA_VERSION,
    "status": (
      "scope_bucket_independent_review_passed_release_blocked"
      if both_narrow_pass
      else "scope_bucket_independent_review_fail_closed"
    ),
    "generated_on": GENERATED_ON,
    "reviewer_role": "A2-EV-SCOPE-BUCKET-INDEPENDENT-REVIEW",
    "review_target": "RES-007_RES-008_scope_bucket_independent_review_only",
    "release_target": "none_review_gate_record_only",
    "scope": dict(probe["scope"]),
    "consumed_evidence": {
      "scope_boundary_probe_rerun": {
        "schema_version": probe["schema_version"],
        "status": probe["status"],
        "sha256": _payload_sha256(probe),
      },
      "scope_and_independence_manifest": {
        "path": _display_path(scope_manifest_path, repo_root),
        "present": bool(scope_manifest_text),
        "status": scope_manifest_review["status"],
      },
      "stage_b_result_pack": {
        "path": _display_path(result_pack_path, repo_root),
        "present": result_pack is not None,
        "status": result_pack_review["status"],
      },
      "stage_b_independent_review_gate": {
        "path": _display_path(review_gate_path, repo_root),
        "present": review_gate is not None,
        "status": independent_review["status"],
      },
      "stage_b_independent_review_manifest": {
        "path": _display_path(review_manifest_path, repo_root),
        "present": review_manifest is not None,
      },
      "stage_b_independent_review_doc": {
        "path": _display_path(review_doc_path, repo_root),
        "present": bool(review_doc_text),
      },
    },
    "probe_coverage_summary": probe_review["probe_coverage_summary"],
    "boundary_rejection_coverage": probe_review["boundary_rejection_coverage"],
    "closure_response_review_status": {
      "probe_response_active": probe_review["probe_coverage_summary"][
        "closure_response_active"
      ],
      "probe_self_review_complete": False,
      "independent_review_complete": independent_review["status"]
      == "independent_review_complete",
      "decision": (
        "review_complete_for_stage_b_scope_only"
        if res008["decision"] == "narrow_pass_stage_b_scope_only"
        else "fail_closed"
      ),
    },
    "residual_statuses": [res007, res008],
    "review_decision": {
      "res007_scope_bucket_review_complete": res007["decision"]
      == "narrow_pass_stage_b_scope_only",
      "res008_scope_bucket_review_complete": res008["decision"]
      == "narrow_pass_stage_b_scope_only",
      "narrow_stage_b_scope_only_acceptance": both_narrow_pass,
      "release_ready": False,
      "release_blocked": True,
      "release_blocked_by_residual_ids": list(UPSTREAM_RELEASE_BLOCKERS),
      "missing_review_evidence_count": len(missing_review_evidence),
    },
    "missing_review_evidence": missing_review_evidence,
    "fail_closed_blockers": res007["blockers"] + res008["blockers"],
    "authority_guards": _authority_guards(),
    "allowed_claim": (
      "RES-007 and RES-008 are independently review-complete only for the "
      "bounded Stage B scope/bucket evidence slice"
      if both_narrow_pass
      else "scope/bucket review is fail-closed until the listed blockers clear"
    ),
    "forbidden_claims": [
      "stock runtime authority",
      "effect-scale release authority",
      "component-failure probability authority",
      "Pk authority",
      "deterministic fuze authority",
      "validated near_miss sub-bucket authority",
      "closure physics authority",
    ],
    "current_findings": [
      (
        "near_miss_0_35m has a retained three-point boundary probe and "
        "review-passing independent evidence for Stage B scope-only acceptance"
        if res007["decision"] == "narrow_pass_stage_b_scope_only"
        else "near_miss_0_35m remains fail-closed for the exact blockers listed"
      ),
      (
        "beam/high has retained closure-response and out-of-scope rejection "
        "coverage with review-passing independent evidence for Stage B scope-only acceptance"
        if res008["decision"] == "narrow_pass_stage_b_scope_only"
        else "beam/high remains fail-closed for the exact blockers listed"
      ),
      (
        "all runtime, Pk, deterministic-fuze and component-probability authority "
        "guards remain false"
      ),
    ],
  }
  return gate, probe

def write_retained_artifacts(
  *,
  output_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = PACKAGE_DIR,
) -> dict[str, Any]:
  gate, probe = generate_scope_bucket_independent_review_gate(
    repo_root=repo_root,
    package_dir=package_dir,
  )
  output_dir.mkdir(parents=True, exist_ok=True)
  artifact_paths = {
    "scope_bucket_independent_review_gate": output_dir
    / "scope_bucket_independent_review_gate.json",
    "scope_boundary_probe_rerun": output_dir / "scope_boundary_probe_rerun.json",
  }
  artifact_paths["scope_bucket_independent_review_gate"].write_text(
    _canonical_json(gate) + "\n",
    encoding="utf-8",
  )
  artifact_paths["scope_boundary_probe_rerun"].write_text(
    _canonical_json(probe) + "\n",
    encoding="utf-8",
  )

  manifest = {
    "package_id": PACKAGE_ID,
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "status": (
      "scope_bucket_independent_review_retained_release_blocked"
      if gate["review_decision"]["narrow_stage_b_scope_only_acceptance"]
      else "scope_bucket_independent_review_retained_fail_closed"
    ),
    "generated_on": GENERATED_ON,
    "artifact_dir": _display_path(output_dir, repo_root),
    "retention_scope": "RES-007_RES-008_scope_bucket_independent_review_only",
    "artifacts": [
      {
        "artifact_key": artifact_key,
        "filename": path.name,
        "relative_path": _display_path(path, repo_root),
        "schema_version": (
          GATE_SCHEMA_VERSION
          if artifact_key == "scope_bucket_independent_review_gate"
          else boundary_probe.PROBE_SCHEMA_VERSION
        ),
        "status": (
          gate["status"]
          if artifact_key == "scope_bucket_independent_review_gate"
          else probe["status"]
        ),
        "content_sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
        "origin_class": (
          "scope_bucket_independent_review_gate_record_only"
          if artifact_key == "scope_bucket_independent_review_gate"
          else "rerun_scope_boundary_probe_input_to_review_gate"
        ),
        "allowed_claim": (
          "bounded RES-007/RES-008 scope-bucket review gate decision is retained"
          if artifact_key == "scope_bucket_independent_review_gate"
          else "current scope boundary probe rerun consumed by the gate is retained"
        ),
        "forbidden_claim": (
          "release readiness, stock runtime authority, component-probability release, "
          "Pk authority, deterministic-fuze authority, or validated closure physics"
        ),
      }
      for artifact_key, path in artifact_paths.items()
    ],
    "review_decision": dict(gate["review_decision"]),
    "authority_guards": _authority_guards(),
  }
  manifest_path = output_dir / "manifest.json"
  manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
  return {
    "gate": gate,
    "probe": probe,
    "manifest": manifest,
    "paths": {
      "gate": artifact_paths["scope_bucket_independent_review_gate"],
      "probe": artifact_paths["scope_boundary_probe_rerun"],
      "manifest": manifest_path,
    },
  }

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate retained RES-007/RES-008 scope-bucket independent-review "
      "gate artifacts for the A2 blast-fragmentation candidate package."
    )
  )
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=DEFAULT_RETAINED_DIR,
    help="Directory for retained JSON artifacts. Defaults to the candidate retained-artifacts gate directory.",
  )
  parser.add_argument(
    "--stdout",
    action="store_true",
    help="Also print the gate JSON to stdout after writing retained artifacts.",
  )
  args = parser.parse_args(argv)

  result = write_retained_artifacts(output_dir=args.output_dir)
  gate = result["gate"]
  if args.stdout:
    print(_canonical_json(gate))
  else:
    print(
      json.dumps(
        {
          "status": gate["status"],
          "gate": _display_path(result["paths"]["gate"], REPO_ROOT),
          "manifest": _display_path(result["paths"]["manifest"], REPO_ROOT),
        },
        indent=2,
        sort_keys=True,
      )
    )
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
