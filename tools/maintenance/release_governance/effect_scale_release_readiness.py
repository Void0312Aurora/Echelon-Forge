#!/usr/bin/env python3
"""Evaluate the current Stage B effect-scale candidate release-readiness gate.

This tool inspects the current Stage B candidate package summaries and emits a
machine-readable readiness decision. It remains non-authoritative: the output
explains why the package is still blocked from stock runtime authority, rather
than granting any authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import effect_scale_result_pack as result_pack
from tools.maintenance.candidate_artifacts import effect_scale_retained_pack as retained_pack
from tools.maintenance.release_governance import package_provenance_identity as provenance_identity_gate


PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
READINESS_GATE_SCHEMA_VERSION = "a2.stage_b_release_readiness_gate.v1"
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

DOC_REFS = {
  "source_ledger": PACKAGE_DIR / "source_ledger.zh.md",
  "surrogate_model_card": PACKAGE_DIR / "surrogate_model_card.zh.md",
  "validation_report_draft": PACKAGE_DIR / "validation_report_draft.zh.md",
  "validation_metrics": (
    PACKAGE_DIR / "validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md"
  ),
  "validation_scope_manifest": (
    PACKAGE_DIR / "validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md"
  ),
  "artifact_pin_manifest": (
    PACKAGE_DIR / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md"
  ),
  "surrogate_identity_manifest": (
    PACKAGE_DIR / "surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md"
  ),
  "validation_retained_artifact_pack": (
    PACKAGE_DIR / "validation_retained_artifact_pack_stage_b_effect_scale_20260530.zh.md"
  ),
  "target_geometry_assumptions": (
    PACKAGE_DIR / "target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md"
  ),
  "warhead_scope": (
    PACKAGE_DIR / "warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md"
  ),
  "validation_release_readiness_gate": (
    PACKAGE_DIR / "validation_release_readiness_gate_stage_b_effect_scale_20260530.zh.md"
  ),
  "residual_register": PACKAGE_DIR / "residual_register.zh.md",
}


def _read_text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _extract_field(text: str, field: str) -> str:
  match = re.search(
    rf"\|\s*`?{re.escape(field)}`?\s*\|\s*`?([^|`]+?)`?\s*\|",
    text,
  )
  return match.group(1).strip() if match else ""


def _scan_placeholder_hits(paths: list[Path]) -> list[dict[str, Any]]:
  hits: list[dict[str, Any]] = []
  patterns = (
    re.compile(r"<待填>"),
    re.compile(r"<待定义>"),
    re.compile(r"模板"),
  )
  for path in paths:
    for line_no, line in enumerate(_read_text(path).splitlines(), start=1):
      if any(pattern.search(line) for pattern in patterns):
        hits.append({"path": str(path), "line": line_no, "content": line.strip()})
  return hits


def _open_residual_ids(path: Path) -> set[str]:
  residuals: set[str] = set()
  for line in _read_text(path).splitlines():
    if not line.startswith("| `RES-"):
      continue
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 7:
      continue
    status = cells[-1].strip("`")
    if status == "open" or status.startswith("open_"):
      residuals.add(cells[0].strip("`"))
  return residuals


def _authority_blocked_residual_ids(path: Path) -> set[str]:
  residuals: set[str] = set()
  for line in _read_text(path).splitlines():
    if not line.startswith("| `RES-"):
      continue
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 7:
      continue
    status = cells[-1].strip("`")
    if (
      status == "open"
      or status.startswith("open_")
      or "authority_blocked" in status
      or "authority_fail_closed" in status
      or "authority_boundary_deferred" in status
    ):
      residuals.add(cells[0].strip("`"))
  return residuals


def _artifact_pin_status_counts(text: str) -> dict[str, int]:
  return {
    "acquired_for_candidate": len(
      re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`acquired_for_candidate`\s*\|", text)
    ),
    "verified_candidate_artifact": len(
      re.findall(
        r"\|\s*`[^`]+`\s*\|.*\|\s*`[^`]*verified_candidate_artifact[^`]*`\s*\|",
        text,
      )
    ),
    "sanity_only": len(
      re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`sanity_only`\s*\|", text)
    ),
    "pending_acquisition": len(
      re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`pending_acquisition`\s*\|", text)
    ),
    "rejected": len(
      re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`rejected`\s*\|", text)
    ),
  }


def _res001_provenance_summary(
  *,
  package_provenance_status: str,
  pin_counts: dict[str, int],
) -> str:
  if pin_counts["pending_acquisition"] > 0:
    return "pending acquisition artifacts still exist in the Stage B pin surface"
  if (
    package_provenance_status
    == "official_public_artifacts_partially_verified_release_grade_closeout_pending"
  ):
    return (
      "official public artifacts are externally verified and checksummed, "
      "but Stage B provenance is still not release-grade closed because "
      "canonical retention, allowed-output policy and "
      "benchmark-consumption closeout remain open"
    )
  return "Stage B provenance is not yet release-grade closed"


def _satisfied_conditions(
  *,
  placeholder_hits: list[dict[str, Any]],
  criteria_status: str,
  scope_manifest_status: str,
  result_pack_artifact: dict[str, Any],
  retained_artifact_pack: dict[str, Any],
) -> list[dict[str, str]]:
  conditions: list[dict[str, str]] = []
  if not placeholder_hits:
    conditions.append(
      {
        "condition_id": "READY-001",
        "summary": "candidate package documentation has no placeholder hits",
      }
    )
  if criteria_status == "frozen_pre_run_stage_b_effect_scale_only":
    conditions.append(
      {
        "condition_id": "READY-002",
        "summary": "Stage B effect-scale acceptance criteria are frozen pre-run",
      }
    )
  if scope_manifest_status == "frozen_pre_run_stage_b_effect_scale_only":
    conditions.append(
      {
        "condition_id": "READY-003",
        "summary": "scope and independence manifest are frozen for Stage B effect-scale-only review",
      }
    )
  result_table = result_pack_artifact["result_table_summary"]
  if result_table["all_hard_gates_pass_in_current_snapshot"]:
    conditions.append(
      {
        "condition_id": "READY-004",
        "summary": "current fixed-seed Stage B hard-gate snapshot passes all frozen hard gates",
      }
    )
  if len(result_pack_artifact["artifact_hashes"]) == 3:
    conditions.append(
      {
        "condition_id": "READY-005",
        "summary": "current candidate result pack consolidates three hashed author-side artifacts",
      }
    )
  if (
    retained_artifact_pack["manifest_exists"]
    and retained_artifact_pack["all_artifacts_exist"]
    and retained_artifact_pack["retained_artifact_count"] == 4
  ):
    conditions.append(
      {
        "condition_id": "READY-006",
        "summary": "canonical retained Stage B author-side artifacts are present for the current candidate surface",
      }
    )
  return conditions


def _blocking_conditions(
  *,
  authority_blocked_residual_ids: set[str],
  independent_review_status: str,
  worktree_state: str,
  retained_artifact_pack: dict[str, Any],
  package_provenance_status: str,
  pin_counts: dict[str, int],
  result_pack_artifact: dict[str, Any],
  validation_manifest_status: str,
) -> list[dict[str, str]]:
  blockers: list[dict[str, str]] = []
  if independent_review_status != "completed":
    blockers.append(
      {
        "blocker_id": "BLOCK-001",
        "residual_id": "RES-010",
        "summary": "independent review record is still missing",
      }
    )
  if worktree_state != "clean_release_candidate":
    retained_phrase = (
      "a canonical retained artifact pack is present, but "
      if (
        retained_artifact_pack["manifest_exists"]
        and retained_artifact_pack["all_artifacts_exist"]
        and retained_artifact_pack["retained_artifact_count"] == 4
      )
      else "no canonical retained artifact pack is pinned, and "
    )
    blockers.append(
      {
        "blocker_id": "BLOCK-002",
        "residual_id": "RES-002",
        "summary": (
          "surrogate identity remains author-side because "
          f"{retained_phrase}the repo is not in a clean release-grade identity state"
        ),
      }
    )
  if package_provenance_status != "release_grade_closed":
    blockers.append(
      {
        "blocker_id": "BLOCK-003",
        "residual_id": "RES-001",
        "summary": _res001_provenance_summary(
          package_provenance_status=package_provenance_status,
          pin_counts=pin_counts,
        ),
      }
    )
  result_table = result_pack_artifact["result_table_summary"]
  if not result_table["all_hard_gates_pass_in_current_snapshot"]:
    blockers.append(
      {
        "blocker_id": "BLOCK-004",
        "residual_id": "RES-010",
        "summary": "Stage B hard gates are not all passing in the current snapshot",
      }
    )
  miss_distance_probe = result_pack_artifact["scope_audit_summary"]
  if not miss_distance_probe["miss_distance_monotonic_pass"]:
    blockers.append(
      {
        "blocker_id": "BLOCK-005",
        "residual_id": "RES-007",
        "summary": "near-miss bucket probe does not satisfy the current candidate monotonicity surface",
      }
    )
  blockers.append(
    {
      "blocker_id": "BLOCK-006",
      "residual_id": "RES-008",
      "summary": (
        "candidate closure-sensitive response is present, but RES-008 remains "
        "non-authoritative and retained as a future authority boundary"
      ),
    }
  )
  if validation_manifest_status != "validated":
    blockers.append(
      {
        "blocker_id": "BLOCK-007",
        "residual_id": "RES-010",
        "summary": "validation manifest still stays at not_run rather than validated/passed",
      }
    )
  if "RES-012" in authority_blocked_residual_ids:
    blockers.append(
      {
        "blocker_id": "BLOCK-009",
        "residual_id": "RES-012",
        "summary": (
          "result pack has author-side independence semantics, but "
          "independent benchmark/input separation review remains authority-blocked"
        ),
      }
    )
  if "RES-007" in authority_blocked_residual_ids:
    blockers.append(
      {
        "blocker_id": "BLOCK-010",
        "residual_id": "RES-007",
        "summary": (
          "near-miss bucket has a passing three-point candidate probe, "
          "but bucket sensitivity and independent review remain authority-blocked"
        ),
      }
    )
  if "RES-011" in authority_blocked_residual_ids:
    blockers.append(
      {
        "blocker_id": "BLOCK-011",
        "residual_id": "RES-011",
        "summary": (
          "seed-window uncertainty CV passes in the candidate snapshot, "
          "but uncertainty coverage and independent closeout remain authority-blocked"
        ),
      }
    )
  blockers.append(
    {
      "blocker_id": "BLOCK-012",
      "residual_id": "RES-013/014-boundary",
      "summary": "stock runtime authority remains explicitly closed by package boundary",
    }
  )
  return blockers


def generate_stage_b_release_readiness_gate(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
  result_pack_artifact = result_pack.generate_stage_b_validation_result_pack(
    repo_root=repo_root
  )
  retained_artifact_pack = retained_pack.load_retained_artifact_pack_manifest(
    repo_root=repo_root
  )
  provenance_identity_artifact = (
    provenance_identity_gate.generate_package_provenance_identity_gate(
      repo_root=repo_root
    )
  )
  criteria_text = _read_text(DOC_REFS["validation_metrics"])
  scope_text = _read_text(DOC_REFS["validation_scope_manifest"])
  pin_text = _read_text(DOC_REFS["artifact_pin_manifest"])
  identity_text = _read_text(DOC_REFS["surrogate_identity_manifest"])
  report_text = _read_text(DOC_REFS["validation_report_draft"])
  placeholder_hits = _scan_placeholder_hits(
    [
      DOC_REFS["source_ledger"],
      DOC_REFS["surrogate_model_card"],
      DOC_REFS["validation_report_draft"],
      DOC_REFS["validation_metrics"],
      DOC_REFS["validation_scope_manifest"],
      DOC_REFS["artifact_pin_manifest"],
      DOC_REFS["surrogate_identity_manifest"],
      DOC_REFS["validation_retained_artifact_pack"],
      DOC_REFS["target_geometry_assumptions"],
      DOC_REFS["warhead_scope"],
      DOC_REFS["validation_release_readiness_gate"],
    ]
  )
  criteria_status = _extract_field(criteria_text, "criteria_status")
  scope_manifest_status = _extract_field(scope_text, "scope_manifest_status")
  independent_review_status = "not_started"
  worktree_state = _extract_field(identity_text, "worktree_state")
  validation_manifest_status = _extract_field(report_text, "validation_status")
  pin_counts = _artifact_pin_status_counts(pin_text)
  package_provenance_status = _extract_field(pin_text, "package_provenance_status")
  open_residual_ids = _open_residual_ids(DOC_REFS["residual_register"])
  authority_blocked_residual_ids = _authority_blocked_residual_ids(
    DOC_REFS["residual_register"]
  )
  stage_b_residual_scope = ["RES-007", "RES-008", "RES-010", "RES-011", "RES-012"]
  blockers = _blocking_conditions(
    authority_blocked_residual_ids=authority_blocked_residual_ids,
    independent_review_status=independent_review_status,
    worktree_state=worktree_state,
    retained_artifact_pack=retained_artifact_pack,
    package_provenance_status=package_provenance_status,
    pin_counts=pin_counts,
    result_pack_artifact=result_pack_artifact,
    validation_manifest_status=validation_manifest_status,
  )
  satisfied = _satisfied_conditions(
    placeholder_hits=placeholder_hits,
    criteria_status=criteria_status,
    scope_manifest_status=scope_manifest_status,
    result_pack_artifact=result_pack_artifact,
    retained_artifact_pack=retained_artifact_pack,
  )
  return {
    "package_id": PACKAGE_ID,
    "schema_version": READINESS_GATE_SCHEMA_VERSION,
    "status": "blocked_non_authoritative_stage_b_release_candidate",
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss_0_35m",
    },
    "release_target": "effect_scale_authority_only",
    "readiness_level": "author_side_candidate_review_ready_but_not_release_ready",
    "release_decision": {
      "release_ready": False,
      "release_blocked": True,
      "current_hard_gate_snapshot_pass": bool(
        result_pack_artifact["result_table_summary"][
          "all_hard_gates_pass_in_current_snapshot"
        ]
      ),
      "hard_gate_pass_is_release": False,
      "blocked_even_when_hard_gates_pass": bool(
        result_pack_artifact["result_table_summary"][
          "all_hard_gates_pass_in_current_snapshot"
        ]
      ),
      "release_target": "effect_scale_authority_only",
      "stage_c_component_probability_release_included": False,
      "stock_runtime_authority_granted": False,
    },
    "stage_b_effect_scale_residual_scope": stage_b_residual_scope,
    "open_stage_b_effect_scale_residual_ids": [
      residual_id
      for residual_id in stage_b_residual_scope
      if residual_id in open_residual_ids
    ],
    "authority_blocked_stage_b_effect_scale_residual_ids": [
      residual_id
      for residual_id in stage_b_residual_scope
      if residual_id in authority_blocked_residual_ids
    ],
    "retained_artifact_pack_summary": {
      "status": retained_artifact_pack["status"],
      "manifest_exists": retained_artifact_pack["manifest_exists"],
      "manifest_relative_path": retained_artifact_pack["manifest_relative_path"],
      "retained_artifact_count": retained_artifact_pack["retained_artifact_count"],
      "all_artifacts_exist": retained_artifact_pack["all_artifacts_exist"],
    },
    "shared_provenance_identity_gate_summary": {
      "status": provenance_identity_artifact["status"],
      "readiness_level": provenance_identity_artifact["readiness_level"],
      "satisfied_condition_count": len(
        provenance_identity_artifact["satisfied_conditions"]
      ),
      "blocking_condition_count": len(
        provenance_identity_artifact["blocking_conditions"]
      ),
      "blocking_residual_ids": list(
        provenance_identity_artifact["blocking_residual_ids"]
      ),
    },
    "satisfied_conditions": satisfied,
    "blocking_conditions": blockers,
    "blocking_residual_ids": [row["residual_id"] for row in blockers],
    "explicit_boundaries": [
      "do not treat this gate as independent review",
      "do not treat this gate as stock runtime authority",
      "do not treat candidate closure-sensitive response as reviewed release-grade closure validation",
      "do not release component_failure_probability, pk or deterministic fuze from this Stage B gate",
    ],
    "current_findings": [
      (
        "the package is reviewable on the author side, but release readiness "
        "is still blocked by independent review, release-grade surrogate "
        "identity closure and provenance/closure residuals"
      ),
      (
        "the current gate deliberately reports blocked status even though "
        "author-side hard gates pass, because passing the snapshot is not "
        "the same thing as release readiness"
      ),
    ],
    "non_authoritative_guards": {
      "stock_descriptor_created": False,
      "stock_database_authority_granted": False,
      "effect_scale_authority_in_stock": False,
      "component_failure_probability_authority_in_stock": False,
      "pk_authority": False,
      "deterministic_fuze_authority": False,
      "candidate_bundle_role": "review_and_packaging_only",
    },
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Evaluate the current Stage B effect-scale candidate release-readiness "
      "gate for the A2 blast-fragmentation package."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path. Defaults to stdout.",
  )
  args = parser.parse_args(argv)

  artifact = generate_stage_b_release_readiness_gate()
  payload = json.dumps(artifact, indent=2, sort_keys=True)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
  else:
    print(payload)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
