#!/usr/bin/env python3
"""Generate the damage-model external signoff intake contract.

This is deliberately a contract/checker layer, not a signoff. It defines the
hash-only shape that a future reviewer packet must satisfy before a separate
admission gate may consider it. It never copies TP-21/BEC-O raw content, never
consumes benchmark outputs for release, and never grants authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.external_signoff_evidence import signoff_request # noqa: E402


PACKAGE_ID = signoff_request.PACKAGE_ID
SCHEMA_VERSION = "a2.blastfrag_signoff_intake_contract.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
  "a2.blastfrag_signoff_intake_contract_retained_manifest.v1"
)
EXPECTED_EXTERNAL_SCHEMA_VERSION = "a2.external_signoff_intake_packet.v1"

RETAINED_ROOT = signoff_request.RETAINED_ROOT
DEFAULT_RETAINED_DIR = RETAINED_ROOT / "signoff_intake_contract_20260601"
SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH = (
  signoff_request.DEFAULT_RETAINED_DIR / signoff_request.PACKET_FILENAME
)

CONTRACT_FILENAME = "signoff_intake_contract.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

ALLOWED_REVIEW_DECISIONS = [
  "approved_for_hash_only_review",
  "rejected",
  "blocked_more_info_required",
]
BENCHMARK_DECISION_VALUES = [
  "not_consumed_for_release_by_this_packet",
  "explicit_release_decision_deferred",
]
RAW_ABSENCE_FIELDS = [
  "tp21_source_prose_tables_figures_or_numeric_values_retained",
  "tp21_raw_selected_outputs_retained",
  "tp21_selected_output_preimage_body_retained",
  "beco_raw_cell_values_or_tool_output_tables_retained",
  "beco_spreadsheet_formula_text_or_cell_ranges_retained",
  "beco_temporary_workbook_copy_retained",
  "stdout_retained",
  "stderr_retained",
]
FORBIDDEN_PACKET_KEYS = {
  "cell_range",
  "cell_value",
  "formula_text",
  "raw_output_table",
  "raw_output_value",
  "raw_selected_output_value",
  "raw_value",
  "selected_output_preimage",
  "selected_output_preimage_body",
  "source_figures",
  "source_numeric_values",
  "source_prose",
  "source_table_rows",
  "source_tables",
  "spreadsheet_formula_text",
  "stderr",
  "stdout",
  "temporary_workbook_copy",
  "workbook_copy",
}


def _rel(path: Path, repo_root: Path) -> str:
  try:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
  except ValueError:
    return path.as_posix()


def _sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    while True:
      chunk = handle.read(1024 * 1024)
      if not chunk:
        break
      digest.update(chunk)
  return digest.hexdigest()


def _sha256_text(text: str) -> str:
  return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
  return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )


def _load_json_optional(path: Path) -> dict[str, Any] | None:
  if not path.is_file():
    return None
  try:
    payload = json.loads(path.read_text(encoding="utf-8"))
  except json.JSONDecodeError:
    return None
  if not isinstance(payload, dict):
    return None
  return payload


def _hex64(value: Any) -> bool:
  return (
    isinstance(value, str)
    and len(value) == 64
    and all(ch in "0123456789abcdef" for ch in value)
  )


def _authority_guards() -> dict[str, bool]:
  return {
    "allowed_output_release_authority_granted": False,
    "benchmark_consumption_authority_granted": False,
    "blast_mechanism_authority_granted": False,
    "component_authority_granted": False,
    "component_failure_probability_authority_granted": False,
    "deterministic_fuze_authority_granted": False,
    "effect_scale_authority_granted": False,
    "fragment_mechanism_authority_granted": False,
    "fuze_authority_granted": False,
    "pk_authority_granted": False,
    "replacement_anchor_authority_granted": False,
    "runtime_authority_granted": False,
    "source_truth_authority_granted": False,
    "stock_database_authority_granted": False,
    "stock_descriptor_created": False,
  }


def _iter_key_paths(value: Any, row_path: str = "$"):
  if isinstance(value, dict):
    for key, child in value.items():
      child_path = f"{row_path}.{key}"
      yield str(key), child_path
      yield from _iter_key_paths(child, child_path)
  elif isinstance(value, list):
    for index, child in enumerate(value):
      yield from _iter_key_paths(child, f"{row_path}[{index}]")


def _input_ref(
  *,
  artifact_key: str,
  path: Path,
  repo_root: Path,
  role: str,
  required: bool,
) -> dict[str, Any]:
  ref: dict[str, Any] = {
    "artifact_key": artifact_key,
    "relative_path": _rel(path, repo_root),
    "role": role,
    "required_for_contract": required,
    "present": path.is_file(),
  }
  if not path.is_file():
    ref["status"] = (
      "missing_required_fail_closed" if required else "missing_optional_fail_closed"
    )
    return ref

  ref["sha256"] = _sha256_file(path)
  try:
    payload = json.loads(path.read_text(encoding="utf-8"))
  except json.JSONDecodeError:
    ref["status"] = "json_parse_failed_fail_closed"
    return ref
  if isinstance(payload, dict):
    ref["schema_version"] = payload.get("schema_version", "")
    ref["status"] = payload.get("status", "")
  return ref


def _required_signoff_ids(request_packet: dict[str, Any] | None) -> list[str]:
  rows = (request_packet or {}).get("requested_signoff_items", [])
  return [
    row.get("signoff_id", "")
    for row in rows
    if isinstance(row, dict) and row.get("signoff_id")
  ]


def _candidate_packet_ref(
  *,
  candidate_packet_path: Path | None,
  repo_root: Path,
) -> dict[str, Any]:
  if candidate_packet_path is None:
    return {
      "present": False,
      "status": "external_signoff_packet_not_supplied_fail_closed",
    }
  ref: dict[str, Any] = {
    "relative_path": _rel(candidate_packet_path, repo_root),
    "present": candidate_packet_path.is_file(),
  }
  if not candidate_packet_path.is_file():
    ref["status"] = "external_signoff_packet_missing_fail_closed"
    return ref

  ref["sha256"] = _sha256_file(candidate_packet_path)
  payload = _load_json_optional(candidate_packet_path)
  if payload is None:
    ref["status"] = "external_signoff_packet_json_invalid_fail_closed"
    return ref
  ref["schema_version"] = payload.get("schema_version", "")
  ref["package_id"] = payload.get("package_id", "")
  ref["status"] = "external_signoff_packet_loaded_for_shape_check_only"
  return ref


def _finding(finding_id: str, detail: str) -> dict[str, str]:
  return {
    "finding_id": finding_id,
    "detail": detail,
    "effect": "intake_shape_rejected_fail_closed",
  }


def _evaluate_external_signoff_packet(
  *,
  candidate_packet: dict[str, Any] | None,
  required_signoff_ids: list[str],
  source_request_sha256: str,
) -> dict[str, Any]:
  findings: list[dict[str, str]] = []
  decision_summaries: list[dict[str, Any]] = []

  if candidate_packet is None:
    findings.append(
      _finding(
        "external_signoff_packet_not_supplied",
        "no candidate signoff packet was supplied to the intake checker",
      )
    )
    return {
      "candidate_packet_supplied": False,
      "intake_shape_valid": False,
      "ready_for_separate_reviewer_admission_gate": False,
      "signoff_decisions_consumed": False,
      "reviewer_decision_summaries": [],
      "missing_signoff_ids": required_signoff_ids,
      "unexpected_signoff_ids": [],
      "forbidden_key_hits": [],
      "finding_count": len(findings),
      "findings": findings,
    }

  if candidate_packet.get("schema_version") != EXPECTED_EXTERNAL_SCHEMA_VERSION:
    findings.append(
      _finding(
        "schema_version_mismatch",
        f"expected {EXPECTED_EXTERNAL_SCHEMA_VERSION}",
      )
    )
  if candidate_packet.get("package_id") != PACKAGE_ID:
    findings.append(_finding("package_id_mismatch", "package_id does not match"))
  if candidate_packet.get("source_rights_signoff_request_packet_sha256") != source_request_sha256:
    findings.append(
      _finding(
        "source_request_sha256_mismatch",
        "candidate packet is not pinned to the current signoff request packet",
      )
    )

  forbidden_hits = sorted(
    {
      key_path
      for key, key_path in _iter_key_paths(candidate_packet)
      if key in FORBIDDEN_PACKET_KEYS
    }
  )
  for key_path in forbidden_hits:
    findings.append(
      _finding(
        "forbidden_raw_or_unretained_field",
        f"candidate packet contains forbidden key {key_path}",
      )
    )

  decisions = candidate_packet.get("reviewer_decisions")
  if not isinstance(decisions, list):
    decisions = []
    findings.append(
      _finding(
        "reviewer_decisions_missing",
        "reviewer_decisions must be a list of hash-only decision refs",
      )
    )

  seen_ids: list[str] = []
  for index, row in enumerate(decisions):
    if not isinstance(row, dict):
      findings.append(
        _finding(
          "reviewer_decision_not_object",
          f"reviewer_decisions[{index}] is not an object",
        )
      )
      continue
    signoff_id = row.get("signoff_id", "")
    decision = row.get("decision", "")
    seen_ids.append(signoff_id)
    if signoff_id not in required_signoff_ids:
      findings.append(
        _finding(
          "unexpected_signoff_id",
          f"reviewer_decisions[{index}] has unexpected signoff_id {signoff_id}",
        )
      )
    if decision not in ALLOWED_REVIEW_DECISIONS:
      findings.append(
        _finding(
          "unsupported_review_decision",
          f"reviewer_decisions[{index}] decision is not allowed",
        )
      )
    for field in (
      "reviewer_ref_sha256",
      "decision_ref_sha256",
      "reviewed_input_ref_sha256",
    ):
      if not _hex64(row.get(field)):
        findings.append(
          _finding(
            "decision_hash_ref_missing",
            f"reviewer_decisions[{index}].{field} must be sha256 hex",
          )
        )
    decision_summaries.append(
      {
        "signoff_id": signoff_id,
        "decision": decision,
        "hash_refs_present": all(
          _hex64(row.get(field))
          for field in (
            "reviewer_ref_sha256",
            "decision_ref_sha256",
            "reviewed_input_ref_sha256",
          )
        ),
      }
    )

  missing_ids = sorted(set(required_signoff_ids) - set(seen_ids))
  unexpected_ids = sorted(set(seen_ids) - set(required_signoff_ids))
  duplicate_ids = sorted({signoff_id for signoff_id in seen_ids if seen_ids.count(signoff_id) > 1})
  for signoff_id in missing_ids:
    findings.append(_finding("missing_required_signoff_id", signoff_id))
  for signoff_id in duplicate_ids:
    findings.append(_finding("duplicate_signoff_id", signoff_id))

  raw_absence = candidate_packet.get("raw_content_absence", {})
  if not isinstance(raw_absence, dict):
    raw_absence = {}
    findings.append(
      _finding(
        "raw_content_absence_missing",
        "raw_content_absence must be an object with all retained flags false",
      )
    )
  for field in RAW_ABSENCE_FIELDS:
    if raw_absence.get(field) is not False:
      findings.append(
        _finding(
          "raw_absence_flag_not_false",
          f"raw_content_absence.{field} must be false",
        )
      )

  guard_confirmation = candidate_packet.get("authority_guard_confirmation", {})
  required_guards = _authority_guards()
  if not isinstance(guard_confirmation, dict):
    guard_confirmation = {}
    findings.append(
      _finding(
        "authority_guard_confirmation_missing",
        "authority_guard_confirmation must be an object with all guards false",
      )
    )
  for guard_id in required_guards:
    if guard_confirmation.get(guard_id) is not False:
      findings.append(
        _finding(
          "authority_guard_not_false",
          f"authority_guard_confirmation.{guard_id} must be false",
        )
      )

  if candidate_packet.get("benchmark_consumption_decision") not in BENCHMARK_DECISION_VALUES:
    findings.append(
      _finding(
        "benchmark_consumption_decision_not_allowed",
        "candidate packet may not consume benchmark outputs for release",
      )
    )

  shape_valid = not findings
  return {
    "candidate_packet_supplied": True,
    "intake_shape_valid": shape_valid,
    "ready_for_separate_reviewer_admission_gate": shape_valid,
    "signoff_decisions_consumed": False,
    "reviewer_decision_summaries": decision_summaries,
    "missing_signoff_ids": missing_ids,
    "unexpected_signoff_ids": unexpected_ids,
    "duplicate_signoff_ids": duplicate_ids,
    "forbidden_key_hits": forbidden_hits,
    "finding_count": len(findings),
    "findings": findings,
  }


def _intake_contract_shape(required_signoff_ids: list[str]) -> dict[str, Any]:
  return {
    "expected_external_schema_version": EXPECTED_EXTERNAL_SCHEMA_VERSION,
    "required_top_level_fields": [
      "schema_version",
      "package_id",
      "signoff_packet_id",
      "source_rights_signoff_request_packet_sha256",
      "reviewer_decisions",
      "raw_content_absence",
      "authority_guard_confirmation",
      "benchmark_consumption_decision",
    ],
    "required_signoff_ids": required_signoff_ids,
    "allowed_review_decisions": ALLOWED_REVIEW_DECISIONS,
    "required_decision_hash_ref_fields": [
      "reviewer_ref_sha256",
      "decision_ref_sha256",
      "reviewed_input_ref_sha256",
    ],
    "raw_content_absence_fields_must_be_false": RAW_ABSENCE_FIELDS,
    "authority_guard_confirmation_fields_must_be_false": sorted(_authority_guards()),
    "allowed_benchmark_consumption_decisions": BENCHMARK_DECISION_VALUES,
    "forbidden_packet_keys": sorted(FORBIDDEN_PACKET_KEYS),
    "contract_effect": "shape_check_only_not_approval_not_admission",
  }


def generate_signoff_intake_contract(
  *,
  repo_root: Path = REPO_ROOT,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  source_rights_signoff_request_packet_path: Path = (
    SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
  ),
  candidate_signoff_packet_path: Path | None = None,
) -> dict[str, Any]:
  input_refs = [
    _input_ref(
      artifact_key="source_rights_signoff_request_packet",
      path=source_rights_signoff_request_packet_path,
      repo_root=repo_root,
      role="current_fail_closed_signoff_request_input",
      required=True,
    )
  ]
  request_packet = _load_json_optional(source_rights_signoff_request_packet_path)
  request_sha256 = (
    _sha256_file(source_rights_signoff_request_packet_path)
    if source_rights_signoff_request_packet_path.is_file()
    else ""
  )
  required_ids = _required_signoff_ids(request_packet)
  candidate_ref = _candidate_packet_ref(
    candidate_packet_path=candidate_signoff_packet_path,
    repo_root=repo_root,
  )
  candidate_packet = (
    _load_json_optional(candidate_signoff_packet_path)
    if candidate_signoff_packet_path is not None
    else None
  )
  check_result = _evaluate_external_signoff_packet(
    candidate_packet=candidate_packet,
    required_signoff_ids=required_ids,
    source_request_sha256=request_sha256,
  )
  missing_required_inputs = [
    row["artifact_key"]
    for row in input_refs
    if row["required_for_contract"] and not row["present"]
  ]
  if missing_required_inputs:
    status = "blocked_fail_closed_signoff_intake_contract_inputs_missing"
  elif check_result["intake_shape_valid"]:
    status = "candidate_signoff_intake_shape_valid_not_approval"
  elif check_result["candidate_packet_supplied"]:
    status = "blocked_fail_closed_signoff_intake_shape_invalid"
  else:
    status = "retained_fail_closed_signoff_intake_contract_no_external_packet"

  guards = _authority_guards()
  return {
    "schema_version": SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": status,
    "packet_type": "signoff_intake_schema_and_shape_checker_contract",
    "artifact_dir": _rel(retained_dir, repo_root),
    "contract_id": "TC-A2-BF-003-SIGNOFF-INTAKE-CONTRACT-20260601",
    "approval_granted": False,
    "release_grade_satisfied": False,
    "admission_granted": False,
    "residuals_closed_by_this_contract": [],
    "benchmark_consumed_for_release": False,
    "fail_closed": True,
    "input_refs": input_refs,
    "candidate_signoff_packet_ref": candidate_ref,
    "intake_contract_shape": _intake_contract_shape(required_ids),
    "current_check_result": check_result,
    "authority_guards": guards,
    "authority_guards_all_false": not any(guards.values()),
    "forbidden_output_policy": {
      "raw_source_text_tables_values_formulas_retained": False,
      "raw_outputs_retained": False,
      "selected_output_preimages_retained": False,
      "temporary_workbook_copy_stdout_or_stderr_retained": False,
      "source_payloads_consumed_as_release_benchmarks": False,
    },
    "integration_notes": [
      "This contract standardizes future external signoff packet intake only.",
      "A shape-valid external packet is not approval and does not close RES-005 or RES-006.",
      "A later admission gate must consume retained hash refs and reviewer decisions explicitly.",
      "No TP-21/BEC-O raw source text, tables, values, formulas, raw outputs, workbook copies, stdout, or stderr are retained here.",
    ],
    "contract_sha256": _sha256_text(
      _canonical_json(
        {
          "input_refs": input_refs,
          "candidate_signoff_packet_ref": candidate_ref,
          "intake_contract_shape": _intake_contract_shape(required_ids),
          "current_check_result": check_result,
          "authority_guards": guards,
        }
      )
    ),
  }


def write_retained_artifacts(
  *,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  source_rights_signoff_request_packet_path: Path = (
    SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
  ),
  candidate_signoff_packet_path: Path | None = None,
) -> dict[str, Any]:
  artifact = generate_signoff_intake_contract(
    repo_root=repo_root,
    retained_dir=retained_dir,
    source_rights_signoff_request_packet_path=source_rights_signoff_request_packet_path,
    candidate_signoff_packet_path=candidate_signoff_packet_path,
  )
  retained_dir.mkdir(parents=True, exist_ok=True)

  contract_path = retained_dir / CONTRACT_FILENAME
  _write_json(contract_path, artifact)
  contract_sha256 = _sha256_file(contract_path)
  contract_artifact = {
    "artifact_key": "signoff_intake_contract",
    "filename": CONTRACT_FILENAME,
    "relative_path": _rel(contract_path, repo_root),
    "schema_version": artifact["schema_version"],
    "sha256": contract_sha256,
  }

  manifest = {
    "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": artifact["status"],
    "artifact_dir": _rel(retained_dir, repo_root),
    "artifacts": [contract_artifact],
    "input_refs": artifact["input_refs"],
    "approval_granted": False,
    "release_grade_satisfied": False,
    "admission_granted": False,
    "fail_closed": True,
    "candidate_packet_supplied": artifact["current_check_result"][
      "candidate_packet_supplied"
    ],
    "intake_shape_valid": artifact["current_check_result"]["intake_shape_valid"],
    "signoff_decisions_consumed": False,
    "required_signoff_ids": artifact["intake_contract_shape"][
      "required_signoff_ids"
    ],
    "finding_count": artifact["current_check_result"]["finding_count"],
    "raw_source_text_tables_values_formulas_retained": False,
    "raw_outputs_retained": False,
    "benchmark_consumed_for_release": False,
    "authority_guards": artifact["authority_guards"],
    "authority_guards_all_false": artifact["authority_guards_all_false"],
  }
  manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
  _write_json(manifest_path, manifest)

  artifact["retained_artifact_ref"] = _rel(contract_path, repo_root)
  artifact["retained_artifact_sha256"] = contract_sha256
  artifact["retained_manifest_ref"] = _rel(manifest_path, repo_root)
  artifact["retained_manifest_sha256"] = _sha256_file(manifest_path)
  return artifact


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the fail-closed damage-model external signoff intake "
      "contract and optional packet shape check."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional path for a copy of the generated contract JSON.",
  )
  parser.add_argument(
    "--retained-dir",
    type=Path,
    default=DEFAULT_RETAINED_DIR,
    help="Directory for retained signoff intake contract artifacts.",
  )
  parser.add_argument(
    "--source-rights-signoff-request-packet",
    type=Path,
    default=SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH,
    help="Current source-rights signoff request packet JSON.",
  )
  parser.add_argument(
    "--candidate-signoff-packet",
    type=Path,
    help="Optional external signoff packet to shape-check without consuming it.",
  )
  args = parser.parse_args(argv)

  artifact = write_retained_artifacts(
    retained_dir=args.retained_dir,
    source_rights_signoff_request_packet_path=args.source_rights_signoff_request_packet,
    candidate_signoff_packet_path=args.candidate_signoff_packet,
  )
  if args.output:
    _write_json(args.output, artifact)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
