#!/usr/bin/env python3
"""Generate the RES-006 BEC-O recalculation admission gate.

This tool is intentionally narrower than the combined RES-005/006 benchmark
gate. It reruns the BEC-O selected-output hash path, retains only hash-only
replacement-anchor candidates, explains the cached-vs-recalculated mismatch
lineage, and fails closed unless an allowed-output/tolerance signoff exists.
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

from tools.maintenance.retained_artifacts.manifest_integrity import _sha256_file, _sha256_text
from tools.maintenance.benchmark_evidence import ( # noqa: E402
  benchmark_execution_admission as res005006_gate,
  comparison_hashes,
)

PACKAGE_ID = comparison_hashes.PACKAGE_ID
SCHEMA_VERSION = "a2.res006_beco_recalculation_admission_gate.v1"
ANCHOR_SET_SCHEMA_VERSION = "a2.res006_beco_recalculated_hash_anchor_set.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
  "a2.res006_beco_recalculation_admission_retained_manifest.v1"
)

PACKAGE_DIR = comparison_hashes.PACKAGE_DIR
SOURCE_PAYLOAD_PACK_DIR = comparison_hashes.SOURCE_PAYLOAD_PACK_DIR
MECHANISM_COMPARISON_HASHES_DIR = comparison_hashes.DEFAULT_RETAINED_DIR
SOURCE_RIGHTS_OUTPUT_POLICY_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "source_rights_output_policy_20260531"
)
DEFAULT_RETAINED_DIR = (
  PACKAGE_DIR
  / "retained_artifacts"
  / "res006_beco_recalculation_admission_20260531"
)

GATE_FILENAME = "res006_beco_recalculation_admission_gate.json"
ANCHOR_SET_FILENAME = "beco_recalculated_hash_anchor_set.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"
SOURCE_RIGHTS_GATE_FILENAME = "source_rights_output_policy_gate.json"

def _rel(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving; differs from manifest_integrity._display_path.
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return path.as_posix()

def _canonical_json(payload: Any) -> str:
  return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _write_json(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def _load_json(path: Path) -> dict[str, Any] | None:
  if not path.is_file():
    return None
  return json.loads(path.read_text(encoding="utf-8"))

def _authority_guards() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "runtime_authority_granted": False,
    "fragment_mechanism_authority_granted": False,
    "blast_mechanism_authority_granted": False,
    "effect_scale_authority_granted": False,
    "component_failure_probability_authority_granted": False,
    "pk_authority_granted": False,
    "deterministic_fuze_authority_granted": False,
    "benchmark_consumption_authority_granted": False,
    "replacement_anchor_authority_granted": False,
  }

def _source_rights_summary(
  *,
  repo_root: Path,
  source_rights_output_policy_dir: Path,
) -> dict[str, Any]:
  path = source_rights_output_policy_dir / SOURCE_RIGHTS_GATE_FILENAME
  payload = _load_json(path)
  if payload is None:
    return {
      "path": _rel(path, repo_root),
      "present": False,
      "status": "missing_fail_closed",
      "allowed_output_policy_status": "missing_fail_closed",
      "release_grade_satisfied": False,
      "selected_comparison_hashes_admitted_by_policy": False,
    }

  policy = payload.get("allowed_output_policy", {})
  return {
    "path": _rel(path, repo_root),
    "present": True,
    "schema_version": payload.get("schema_version", ""),
    "status": payload.get("status", ""),
    "allowed_output_policy_status": policy.get("policy_status", ""),
    "release_grade_satisfied": bool(policy.get("release_grade_satisfied")),
    "policy_frozen_by_this_gate": bool(policy.get("policy_frozen_by_this_gate")),
    "selected_comparison_hashes_admitted_by_policy": False,
    "allowed_hash_outputs": policy.get("allowed_hash_outputs", []),
    "forbidden_copy_outputs": policy.get("forbidden_copy_outputs", []),
    "forbidden_consume_outputs": policy.get("forbidden_consume_outputs", []),
  }

def _cached_anchor_summary(mechanism_artifact: dict[str, Any]) -> dict[str, Any]:
  beco = mechanism_artifact["beco_workbook"]
  cached_hashes = [
    {
      "comparison_id": row["comparison_id"],
      "sheet": row["sheet"],
      "cell": row["cell"],
      "output_role": row["output_role"],
      "unit_family": row["unit_family"],
      "cached_anchor_sha256": row["comparison_output_sha256"],
      "formula_sha256": row["formula_sha256"],
      "raw_value_disclosed": False,
      "formula_text_disclosed": False,
      "comparison_hash_is_calibration": False,
    }
    for row in beco.get("selected_comparison_hashes", [])
    if row.get("comparison_output_sha256")
  ]
  return {
    "source_artifact_label": "BEC-O-V1.xlsx",
    "source_id": "VPS-BFM-014",
    "residual_id": "RES-006",
    "relative_path": beco.get("relative_path", ""),
    "workbook_sha256": beco.get("workbook_sha256", ""),
    "parse_status": beco.get("parse_status", ""),
    "spreadsheet_calculation_executed": bool(
      beco.get("spreadsheet_calculation_executed")
    ),
    "cached_hash_anchor_count": len(cached_hashes),
    "all_selected_cached_hashes_present": bool(
      beco.get("all_selected_cached_hashes_present")
    ),
    "selected_comparison_output_set_sha256": beco.get(
      "selected_comparison_output_set_sha256", ""
    ),
    "cached_hash_lineage": (
      "mechanism_comparison_hashes.v1 captured workbook cached formula "
      "values as hash-only anchors; spreadsheet_calculation_executed=false"
    ),
    "cached_hashes": cached_hashes,
  }

def _candidate_anchor_set(
  *,
  beco_gate: dict[str, Any],
  tooling: dict[str, Any],
  cached_summary: dict[str, Any],
) -> dict[str, Any]:
  attempt = beco_gate.get("execution_attempt", {})
  recalculated_rows = attempt.get("selected_recalculated_hashes", [])
  selected_executor = tooling.get("selected_spreadsheet_executor") or {}
  anchors = [
    {
      "comparison_id": row["comparison_id"],
      "source_id": row["source_id"],
      "source_artifact_label": row["source_artifact_label"],
      "sheet": row["sheet"],
      "cell": row["cell"],
      "output_role": row["output_role"],
      "unit_family": row["unit_family"],
      "recalculated_output_sha256": row["comparison_output_sha256"],
      "formula_sha256": row["formula_sha256"],
      "calculation_source": row.get("calculation_source", ""),
      "raw_value_disclosed": False,
      "formula_text_disclosed": False,
      "comparison_hash_is_calibration": False,
      "benchmark_consumed_for_release": False,
    }
    for row in recalculated_rows
    if row.get("comparison_output_sha256")
  ]
  all_anchors_present = len(anchors) == len(comparison_hashes.BECO_SELECTED_OUTPUTS)
  payload = {
    "schema_version": ANCHOR_SET_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": (
      "candidate_replacement_anchor_set_retained_not_admitted"
      if all_anchors_present
      else "candidate_replacement_anchor_set_unavailable_fail_closed"
    ),
    "residual_id": "RES-006",
    "source_artifact_label": "BEC-O-V1.xlsx",
    "source_artifact_sha256": cached_summary["workbook_sha256"],
    "recalculation_execution_status": attempt.get("execution_status", ""),
    "executor_tool": selected_executor.get("tool", ""),
    "executor_version_string": selected_executor.get("version_string", ""),
    "recalculated_hash_count": len(anchors),
    "expected_selected_hash_count": len(comparison_hashes.BECO_SELECTED_OUTPUTS),
    "all_selected_recalculated_hashes_present": all_anchors_present,
    "raw_selected_values_retained": False,
    "formula_text_retained": False,
    "temporary_workbook_copy_retained": False,
    "stdout_retained": False,
    "stderr_retained": False,
    "replacement_anchor_set_admitted": False,
    "replacement_anchor_set_is_calibration": False,
    "benchmark_consumed_for_release": False,
    "selected_recalculated_hashes": anchors,
  }
  comparable = [
    {
      "comparison_id": row["comparison_id"],
      "sheet": row["sheet"],
      "cell": row["cell"],
      "output_role": row["output_role"],
      "recalculated_output_sha256": row["recalculated_output_sha256"],
    }
    for row in anchors
  ]
  payload["selected_recalculated_output_set_sha256"] = _sha256_text(
    _canonical_json(comparable)
  )
  payload["payload_sha256"] = _sha256_text(_canonical_json(comparable))
  return payload

def _mismatch_lineage(
  *,
  beco_gate: dict[str, Any],
  cached_summary: dict[str, Any],
  anchor_set: dict[str, Any],
) -> dict[str, Any]:
  comparisons = beco_gate.get("selected_hash_comparisons", [])
  mismatch_ids = [
    row["comparison_id"]
    for row in comparisons
    if row.get("cached_anchor_sha256")
    and row.get("recalculated_output_sha256")
    and not row.get("hashes_match")
  ]
  missing_recalculated_ids = [
    row["comparison_id"]
    for row in comparisons
    if row.get("cached_anchor_sha256") and not row.get("recalculated_output_sha256")
  ]
  matching_ids = [
    row["comparison_id"] for row in comparisons if row.get("hashes_match")
  ]
  all_recalculated_present = anchor_set.get("all_selected_recalculated_hashes_present")
  all_hashes_match = bool(
    comparisons
    and len(comparisons) == len(comparison_hashes.BECO_SELECTED_OUTPUTS)
    and not mismatch_ids
    and not missing_recalculated_ids
  )
  return {
    "status": (
      "cached_and_recalculated_hashes_match"
      if all_hashes_match
      else "cached_to_recalculated_hash_lineage_mismatch_fail_closed"
    ),
    "cached_anchor_count": cached_summary["cached_hash_anchor_count"],
    "recalculated_anchor_count": anchor_set["recalculated_hash_count"],
    "matching_count": len(matching_ids),
    "mismatch_count": len(mismatch_ids),
    "missing_recalculated_count": len(missing_recalculated_ids),
    "matching_comparison_ids": matching_ids,
    "mismatch_comparison_ids": mismatch_ids,
    "missing_recalculated_comparison_ids": missing_recalculated_ids,
    "cached_anchor_lineage": cached_summary["cached_hash_lineage"],
    "recalculated_anchor_lineage": (
      "local LibreOffice headless reopen/recalculate copy retained "
      "hash-only selected output anchors; raw selected values, formula "
      "text, temporary workbook copy, stdout and stderr are not retained"
    ),
    "lineage_interpretation": (
      "all selected recalculated hashes are available but at least one "
      "hash differs from the cached anchors; without raw numeric "
      "tolerance review and allowed-output signoff, exact-hash admission "
      "must fail closed"
      if all_recalculated_present and mismatch_ids
      else (
        "selected recalculated hashes are incomplete, so RES-006 remains "
        "blocked before tolerance or replacement review"
      )
    ),
    "hash_only_comparison_rows": comparisons,
    "raw_values_retained": False,
    "formula_text_retained": False,
  }

def _replacement_path(
  *,
  anchor_set: dict[str, Any],
  mismatch_lineage: dict[str, Any],
  source_rights_summary: dict[str, Any],
) -> dict[str, Any]:
  replacement_candidate_present = bool(
    anchor_set.get("all_selected_recalculated_hashes_present")
  )
  return {
    "status": (
      "candidate_recalculated_anchor_set_retained_review_required"
      if replacement_candidate_present
      else "replacement_anchor_set_not_available_fail_closed"
    ),
    "candidate_replacement_anchor_set_retained": replacement_candidate_present,
    "candidate_replacement_anchor_set_sha256": anchor_set.get(
      "selected_recalculated_output_set_sha256", ""
    ),
    "cached_to_recalculated_lineage_status": mismatch_lineage["status"],
    "exact_hash_policy_candidate": (
      "future review may replace cached anchors with this recalculated "
      "hash-only set only through a separate retained signoff"
    ),
    "numeric_tolerance_policy_candidate": (
      "not admitted here; no raw numeric values or tolerances are retained"
    ),
    "allowed_output_policy_status": source_rights_summary[
      "allowed_output_policy_status"
    ],
    "allowed_output_signoff_present": False,
    "replacement_anchor_set_admitted": False,
    "release_grade_validated": False,
    "benchmark_consumed_for_release": False,
    "minimum_evidence_to_admit": [
      "independent reviewer accepts the selected recalculation runtime and version lineage",
      "allowed-output policy explicitly admits selected comparison output hashes",
      "release-grade exact-hash replacement or numeric tolerance policy is signed off",
      "replacement anchors are promoted in a separate retained artifact instead of mutating cached anchors in place",
    ],
  }

def _admission_decision(
  *,
  beco_gate: dict[str, Any],
  mismatch_lineage: dict[str, Any],
  replacement_path: dict[str, Any],
  source_rights_summary: dict[str, Any],
) -> dict[str, Any]:
  exact_hash_check_passed = mismatch_lineage["status"] == (
    "cached_and_recalculated_hashes_match"
  )
  allowed_output_signoff_present = bool(
    source_rights_summary.get("release_grade_satisfied")
  )
  tolerance_policy_admitted = False
  replacement_admitted = False
  res006_closed = (
    exact_hash_check_passed
    and allowed_output_signoff_present
    and tolerance_policy_admitted
    and replacement_admitted
  )

  blockers: list[str] = []
  if beco_gate.get("exact_blocker"):
    blockers.append(beco_gate["exact_blocker"])
  if not exact_hash_check_passed:
    blockers.append(
      "cached-vs-recalculated selected hashes do not satisfy exact-hash admission"
    )
  if not allowed_output_signoff_present:
    blockers.append(
      "source rights allowed-output policy remains fail-closed for selected comparison outputs"
    )
  if not tolerance_policy_admitted:
    blockers.append(
      "release-grade tolerance or replacement-anchor signoff is not present"
    )
  if not replacement_admitted:
    blockers.append(
      "candidate recalculated hash anchor set is retained but not admitted"
      if replacement_path["candidate_replacement_anchor_set_retained"]
      else "candidate recalculated hash anchor set is unavailable"
    )

  return {
    "residual_id": "RES-006",
    "decision": (
      "res006_narrowly_closed_beco_recalculation_admitted"
      if res006_closed
      else "res006_remains_blocked_fail_closed"
    ),
    "res006_narrowly_closed": res006_closed,
    "beco_recalculation_hashes_admitted": res006_closed,
    "exact_hash_check_passed": exact_hash_check_passed,
    "allowed_output_signoff_present": allowed_output_signoff_present,
    "tolerance_policy_admitted": tolerance_policy_admitted,
    "replacement_anchor_set_admitted": replacement_admitted,
    "release_grade_validated": False,
    "benchmark_consumed_for_release": False,
    "closed_residual_ids_by_this_gate": ["RES-006"] if res006_closed else [],
    "remaining_blockers": blockers,
  }

def generate_res006_beco_recalculation_admission_gate(
  *,
  repo_root: Path = REPO_ROOT,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  source_payload_pack_dir: Path = SOURCE_PAYLOAD_PACK_DIR,
  source_rights_output_policy_dir: Path = SOURCE_RIGHTS_OUTPUT_POLICY_DIR,
  attempt_spreadsheet_execution: bool = True,
) -> dict[str, Any]:
  mechanism_artifact = comparison_hashes.generate_mechanism_comparison_hashes(
    repo_root=repo_root,
    source_payload_pack_dir=source_payload_pack_dir,
  )
  tooling = res005006_gate.detect_execution_tooling()
  if not attempt_spreadsheet_execution:
    tooling = {
      **tooling,
      "tool_detection_status": "spreadsheet_execution_probe_skipped",
      "selected_spreadsheet_executor": None,
      "missing_execution_tooling_blockers": [
        "spreadsheet execution attempt disabled by caller"
      ],
    }

  retained_dir.mkdir(parents=True, exist_ok=True)
  beco_gate = res005006_gate._beco_execution_gate(
    mechanism_artifact=mechanism_artifact,
    tooling=tooling,
    retained_dir=retained_dir,
  )
  cached_summary = _cached_anchor_summary(mechanism_artifact)
  source_rights = _source_rights_summary(
    repo_root=repo_root,
    source_rights_output_policy_dir=source_rights_output_policy_dir,
  )
  anchor_set = _candidate_anchor_set(
    beco_gate=beco_gate,
    tooling=tooling,
    cached_summary=cached_summary,
  )
  mismatch_lineage = _mismatch_lineage(
    beco_gate=beco_gate,
    cached_summary=cached_summary,
    anchor_set=anchor_set,
  )
  replacement_path = _replacement_path(
    anchor_set=anchor_set,
    mismatch_lineage=mismatch_lineage,
    source_rights_summary=source_rights,
  )
  decision = _admission_decision(
    beco_gate=beco_gate,
    mismatch_lineage=mismatch_lineage,
    replacement_path=replacement_path,
    source_rights_summary=source_rights,
  )
  guards = _authority_guards()

  return {
    "schema_version": SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": (
      "res006_beco_recalculation_admission_passed"
      if decision["res006_narrowly_closed"]
      else "partial_fail_closed_res006_beco_recalculation_admission"
    ),
    "review_target": "RES-006_BEC-O_recalculation_hash_admission_gate",
    "source_payload_pack_ref": _rel(source_payload_pack_dir, repo_root),
    "source_rights_output_policy_ref": _rel(
      source_rights_output_policy_dir / SOURCE_RIGHTS_GATE_FILENAME,
      repo_root,
    ),
    "mechanism_comparison_hashes_ref": _rel(
      MECHANISM_COMPARISON_HASHES_DIR
      / comparison_hashes.MECHANISM_COMPARISON_HASHES_FILENAME,
      repo_root,
    ),
    "mechanism_comparison_hashes_input_status": mechanism_artifact["status"],
    "source_rights_output_policy_summary": source_rights,
    "tooling_detection": tooling,
    "cached_anchor_summary": cached_summary,
    "beco_recalculation_gate": beco_gate,
    "candidate_replacement_anchor_set": anchor_set,
    "mismatch_lineage": mismatch_lineage,
    "replacement_path": replacement_path,
    "admission_decision": decision,
    "current_gate_results": {
      "RES-006": decision["decision"],
    },
    "authority_guards": guards,
    "authority_guards_all_false": not any(guards.values()),
    "behavior_risks": [
      "candidate recalculated hash anchors may be mistaken for admitted release benchmarks",
      "hash mismatch may hide numeric equivalence because raw values and tolerances are intentionally not retained here",
      "LibreOffice headless execution may be mistaken for independent spreadsheet review",
      "replacement anchors may be mistaken for permission to mutate cached anchors in place",
    ],
    "integration_notes": [
      "This gate is scoped only to RES-006 BEC-O recalculation admission.",
      "BEC-O raw selected values, formulas, stdout, stderr and temporary workbook copies are not retained.",
      "A candidate recalculated hash anchor set is retained only under this RES-006 scope and is not promoted into mechanism_comparison_hashes.",
      "Stock/runtime/effect-scale/component/Pk/fuze authority guards remain false.",
    ],
  }

def write_retained_artifacts(
  *,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  source_payload_pack_dir: Path = SOURCE_PAYLOAD_PACK_DIR,
  source_rights_output_policy_dir: Path = SOURCE_RIGHTS_OUTPUT_POLICY_DIR,
  attempt_spreadsheet_execution: bool = True,
) -> dict[str, Any]:
  artifact = generate_res006_beco_recalculation_admission_gate(
    repo_root=repo_root,
    retained_dir=retained_dir,
    source_payload_pack_dir=source_payload_pack_dir,
    source_rights_output_policy_dir=source_rights_output_policy_dir,
    attempt_spreadsheet_execution=attempt_spreadsheet_execution,
  )
  retained_dir.mkdir(parents=True, exist_ok=True)

  anchor_path = retained_dir / ANCHOR_SET_FILENAME
  _write_json(anchor_path, artifact["candidate_replacement_anchor_set"])
  anchor_sha256 = _sha256_file(anchor_path)
  artifact["candidate_replacement_anchor_set_artifact"] = {
    "filename": ANCHOR_SET_FILENAME,
    "relative_path": _rel(anchor_path, repo_root),
    "schema_version": ANCHOR_SET_SCHEMA_VERSION,
    "sha256": anchor_sha256,
  }

  gate_path = retained_dir / GATE_FILENAME
  _write_json(gate_path, artifact)
  gate_sha256 = _sha256_file(gate_path)

  manifest = {
    "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": (
      "res006_beco_recalculation_admission_retained_release_blocked"
      if not artifact["admission_decision"]["res006_narrowly_closed"]
      else "res006_beco_recalculation_admission_retained_passed"
    ),
    "artifact_dir": _rel(retained_dir, repo_root),
    "artifacts": [
      {
        "artifact_key": "res006_beco_recalculation_admission_gate",
        "filename": GATE_FILENAME,
        "relative_path": _rel(gate_path, repo_root),
        "schema_version": artifact["schema_version"],
        "sha256": gate_sha256,
      },
      artifact["candidate_replacement_anchor_set_artifact"],
    ],
    "current_gate_results": artifact["current_gate_results"],
    "admission_decision": artifact["admission_decision"],
    "replacement_path": artifact["replacement_path"],
    "authority_guards": artifact["authority_guards"],
    "authority_guards_all_false": artifact["authority_guards_all_false"],
  }
  manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
  _write_json(manifest_path, manifest)

  artifact["retained_artifact_sha256"] = gate_sha256
  artifact["retained_anchor_set_sha256"] = anchor_sha256
  artifact["retained_manifest_sha256"] = _sha256_file(manifest_path)
  return artifact

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Generate the fail-closed RES-006 BEC-O recalculation admission gate."
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional path for a copy of the generated gate JSON.",
  )
  parser.add_argument(
    "--source-payload-pack-dir",
    type=Path,
    default=SOURCE_PAYLOAD_PACK_DIR,
    help="Retained source payload pack directory.",
  )
  parser.add_argument(
    "--source-rights-output-policy-dir",
    type=Path,
    default=SOURCE_RIGHTS_OUTPUT_POLICY_DIR,
    help="Retained source rights/output policy directory.",
  )
  parser.add_argument(
    "--retained-dir",
    type=Path,
    default=DEFAULT_RETAINED_DIR,
    help="Directory for retained RES-006 BEC-O recalculation artifacts.",
  )
  parser.add_argument(
    "--skip-spreadsheet-execution",
    action="store_true",
    help="Detect tooling but do not attempt BEC-O headless recalculation.",
  )
  args = parser.parse_args(argv)

  artifact = write_retained_artifacts(
    retained_dir=args.retained_dir,
    source_payload_pack_dir=args.source_payload_pack_dir,
    source_rights_output_policy_dir=args.source_rights_output_policy_dir,
    attempt_spreadsheet_execution=not args.skip_spreadsheet_execution,
  )
  if args.output:
    _write_json(args.output, artifact)
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
