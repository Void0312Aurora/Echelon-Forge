#!/usr/bin/env python3
"""Produce the bounded RES-001 internal release signoff closeout gate.

The gate consumes only retained source/provenance evidence and writes a
fail-closed decision artifact. It is project-internal release/signoff evidence,
not legal advice, and it never releases stock, effect, component, Pk, fuze, or
runtime authority.
"""

from __future__ import annotations

import sys
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.maintenance.retained_artifacts.manifest_integrity import _sha256_file, _sha256_text
PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
SCHEMA_VERSION = "a2.res001_release_signoff_gate.v1"
MANIFEST_SCHEMA_VERSION = "a2.res001_release_signoff_manifest.v1"

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
SOURCE_PAYLOAD_DIR = PACKAGE_DIR / "retained_artifacts" / "source_payload_pack_20260531"
SOURCE_RIGHTS_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "source_rights_output_policy_20260531"
)
MECHANISM_HASH_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "mechanism_comparison_hashes_20260531"
)
PROVENANCE_REVIEW_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "provenance_identity_review_20260531"
)
DEFAULT_OUTPUT_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "res001_release_signoff_20260531"
)
DEFAULT_REPORT_PATH = PACKAGE_DIR / "validation_res001_release_signoff_gate_20260531.zh.md"

SOURCE_ARTIFACT_PACK_MANIFEST = SOURCE_PAYLOAD_DIR / "source_artifact_pack_manifest.json"
SOURCE_PAYLOAD_PACK = SOURCE_PAYLOAD_DIR / "source_payload_pack.json"
SOURCE_RIGHTS_GATE = SOURCE_RIGHTS_DIR / "source_rights_output_policy_gate.json"
MECHANISM_HASHES = MECHANISM_HASH_DIR / "mechanism_comparison_hashes.json"
PROVENANCE_REVIEW_GATE = PROVENANCE_REVIEW_DIR / "provenance_identity_review_gate.json"

GATE_FILENAME = "res001_release_signoff_gate.json"
MANIFEST_FILENAME = "manifest.json"
POLICY_STATUS = "release_candidate_fail_closed_policy_frozen"
LEGAL_RIGHTS_CANDIDATE_STATUS = (
  "public_distribution_statement_supported_candidate_not_signed_off"
)
EXPLICIT_NON_CONSUMPTION_STATUS = "explicit_non_consumption_only_release_chain_missing"

REQUIRED_CHECKS = [
  "source_payload_pack_present",
  "payload_retention_complete",
  "payload_hashes_match",
  "public_distribution_support_present",
  "release_grade_legal_rights_not_asserted",
  "allowed_output_policy_frozen_fail_closed",
  "raw_payload_bodies_non_copyable",
  "benchmark_explicitly_not_consumed_or_hash_only_admitted",
  "beco_tp21_outputs_not_release_consumed_unless_hash_only_admitted",
  "comparison_values_not_copied",
  "provenance_identity_review_res001_author_side_present",
  "authority_guards_all_false",
]

def _read_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))

def _read_json_if_exists(path: Path) -> dict[str, Any]:
  return _read_json(path) if path.exists() else {}

def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)

def _display_path(path: Path, repo_root: Path = REPO_ROOT) -> str:
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)

def _resolve_repo_path(path_value: str, repo_root: Path) -> Path:
  path = Path(path_value)
  return path if path.is_absolute() else repo_root / path

def _all_false(mapping: dict[str, Any]) -> bool:
  return bool(mapping) and not any(bool(value) for value in mapping.values())

def _merged_authority_guards(*artifacts: dict[str, Any]) -> dict[str, bool]:
  guards = {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "runtime_authority_granted": False,
    "fragment_mechanism_authority_granted": False,
    "blast_mechanism_authority_granted": False,
    "effect_scale_authority_released": False,
    "effect_scale_authority_in_stock": False,
    "effect_scale_authority_granted": False,
    "component_failure_probability_authority_released": False,
    "component_failure_probability_authority_in_stock": False,
    "component_failure_probability_authority_granted": False,
    "pk_authority_released": False,
    "pk_authority_granted": False,
    "pk_authority": False,
    "deterministic_fuze_authority_released": False,
    "deterministic_fuze_authority_granted": False,
    "deterministic_fuze_authority": False,
  }
  for artifact in artifacts:
    for key, value in artifact.get("non_authoritative_guards", {}).items():
      guards[key] = bool(guards.get(key, False) or value)
  return guards

def _payload_files_verified(
  *,
  source_manifest: dict[str, Any],
  repo_root: Path,
) -> tuple[bool, bool, list[dict[str, Any]]]:
  rows: list[dict[str, Any]] = []
  for row in source_manifest.get("artifacts", []):
    path = _resolve_repo_path(str(row.get("relative_path", "")), repo_root)
    expected = str(row.get("sha256", ""))
    exists = path.exists() and path.is_file()
    actual = _sha256_file(path) if exists else ""
    rows.append(
      {
        "requirement_id": row.get("requirement_id", ""),
        "source_artifact_label": row.get("source_artifact_label", ""),
        "relative_path": row.get("relative_path", ""),
        "expected_sha256": expected,
        "actual_sha256": actual,
        "payload_exists": exists,
        "hash_matches_expected": bool(expected and actual == expected),
        "benchmark_consumed_for_release": bool(
          row.get("benchmark_consumed_for_release", False)
        ),
        "benchmark_consumption_status": row.get(
          "benchmark_consumption_status", ""
        ),
        "rights_status": row.get("rights_status", ""),
        "retention_status": row.get("retention_status", ""),
      }
    )
  payloads_exist = bool(rows) and all(row["payload_exists"] for row in rows)
  hashes_match = bool(rows) and all(row["hash_matches_expected"] for row in rows)
  return payloads_exist, hashes_match, rows

def _public_distribution_supported(rights_gate: dict[str, Any]) -> bool:
  rows = rights_gate.get("payload_rights_inventory", [])
  if not rows:
    return False
  return all(
    bool(row.get("rights_supported_by_public_distribution_statement"))
    for row in rows
  )

def _release_grade_legal_rights_not_asserted(
  *,
  source_manifest: dict[str, Any],
  rights_gate: dict[str, Any],
) -> bool:
  if source_manifest.get("rights_review_status") != LEGAL_RIGHTS_CANDIDATE_STATUS:
    return False
  result = rights_gate.get("res_001_gate_result", {})
  if bool(result.get("release_grade_rights_reviewed")):
    return False
  if bool(result.get("release_grade_satisfied")):
    return False
  return not any(
    bool(row.get("rights_release_grade_satisfied"))
    for row in rights_gate.get("payload_rights_inventory", [])
  )

def _allowed_output_policy_frozen_fail_closed(rights_gate: dict[str, Any]) -> bool:
  policy = rights_gate.get("allowed_output_policy", {})
  forbidden_copy = set(policy.get("forbidden_copy_outputs", []))
  forbidden_consume = set(policy.get("forbidden_consume_outputs", []))
  return (
    policy.get("policy_status") == POLICY_STATUS
    and bool(policy.get("policy_frozen_by_this_gate"))
    and bool(rights_gate.get("res_001_gate_result", {}).get("allowed_output_policy_frozen"))
    and "source_payload_body_or_bulk_content" in forbidden_copy
    and "spreadsheet_tool_output_tables" in forbidden_copy
    and "comparison_output_values_without_review_admission" in forbidden_copy
    and "comparison_outputs_without_selected_sha256_and_signoff" in forbidden_consume
  )

def _raw_payload_bodies_non_copyable(rights_gate: dict[str, Any]) -> bool:
  rows = rights_gate.get("payload_rights_inventory", [])
  if not rows:
    return False
  for row in rows:
    policy = row.get("output_policy", {})
    forbidden = set(policy.get("copy_forbidden_outputs", []))
    if "payload_body_or_bulk_content" not in forbidden:
      return False
    if row.get("source_artifact_label") == "BEC-O-V1.xlsx" and not {
      "spreadsheet_formulas",
      "spreadsheet_cell_ranges",
      "spreadsheet_or_tool_output_tables",
    }.issubset(forbidden):
      return False
  return True

def _contains_disallowed_raw_comparison_values(value: Any) -> bool:
  forbidden_keys = {
    "cached_formula_value",
    "raw_source_value",
    "raw_value",
    "comparison_output_value",
    "source_table",
    "extracted_text",
  }
  if isinstance(value, dict):
    if forbidden_keys & set(value):
      return True
    return any(_contains_disallowed_raw_comparison_values(item) for item in value.values())
  if isinstance(value, list):
    return any(_contains_disallowed_raw_comparison_values(item) for item in value)
  return False

def _benchmark_consumption_decision(
  *,
  source_manifest: dict[str, Any],
  source_payload_pack: dict[str, Any],
  rights_gate: dict[str, Any],
  mechanism_hashes: dict[str, Any],
) -> dict[str, Any]:
  artifacts = source_manifest.get("artifacts", [])
  source_release_consumed = [
    row.get("requirement_id", "")
    for row in artifacts
    if bool(row.get("benchmark_consumed_for_release"))
  ]
  payload_chain_status = source_manifest.get("benchmark_consumption_chain_status")
  source_pack_trace = source_payload_pack.get("benchmark_consumption_trace", {})
  explicit_non_consumed = sorted(
    set(source_pack_trace.get("explicit_non_consumed_artifact_ids", []))
    or {
      str(row.get("artifact_id", ""))
      for row in artifacts
      if row.get("benchmark_consumption_status")
      == "not_consumed_for_stage_b_release"
    }
  )
  mechanism_decision = mechanism_hashes.get("comparison_hash_decision", {})
  beco_hashes_present = bool(
    mechanism_decision.get("selected_beco_cached_output_hashes_present")
  )
  tp21_hashes_present = bool(
    mechanism_decision.get("tp21_selected_debris_output_hashes_present")
  )
  selected_outputs_admitted = bool(
    rights_gate.get("res_001_gate_result", {}).get("comparison_outputs_admitted")
  )
  mechanism_benchmark_consumed = bool(
    mechanism_decision.get("benchmark_consumed_for_release")
  )
  hash_only_admitted = (
    selected_outputs_admitted
    and not mechanism_benchmark_consumed
    and not _contains_disallowed_raw_comparison_values(mechanism_hashes)
  )
  explicit_non_consumption = (
    not source_release_consumed
    and payload_chain_status == EXPLICIT_NON_CONSUMPTION_STATUS
    and not mechanism_benchmark_consumed
    and bool(explicit_non_consumed)
  )
  return {
    "decision": (
      "explicit_release_non_consumption"
      if explicit_non_consumption
      else (
        "hash_only_admitted_without_raw_value_consumption"
        if hash_only_admitted
        else "missing_release_non_consumption_or_hash_only_admission"
      )
    ),
    "satisfied": explicit_non_consumption or hash_only_admitted,
    "source_release_consumed_requirement_ids": source_release_consumed,
    "explicit_non_consumed_artifact_ids": explicit_non_consumed,
    "source_payload_pack_chain_status": payload_chain_status,
    "selected_outputs_admitted_by_rights_policy": selected_outputs_admitted,
    "beco_hash_only_anchors_present": beco_hashes_present,
    "tp21_hash_only_selected_outputs_present": tp21_hashes_present,
    "mechanism_outputs_benchmark_consumed_for_release": mechanism_benchmark_consumed,
    "raw_comparison_values_detected": _contains_disallowed_raw_comparison_values(
      mechanism_hashes
    ),
  }

def _provenance_res001_author_side_present(provenance_gate: dict[str, Any]) -> bool:
  if provenance_gate.get("residual_gate_results", {}).get("RES-001") != "blocked":
    return False
  for row in provenance_gate.get("residual_condition_trace", []):
    if row.get("residual_id") == "RES-001":
      return row.get("author_side_closed_check_ids") == [
        "REVIEW-RES001-001",
        "REVIEW-RES001-002",
        "REVIEW-RES001-003",
        "REVIEW-RES001-004",
      ]
  return False

def _input_ref(path: Path, artifact: dict[str, Any], repo_root: Path) -> dict[str, Any]:
  return {
    "relative_path": _display_path(path, repo_root),
    "exists": path.exists(),
    "sha256": _sha256_file(path) if path.exists() else "",
    "schema_version": artifact.get("schema_version", ""),
    "status": artifact.get("status", ""),
  }

def generate_res001_release_signoff_gate(
  *,
  repo_root: Path = REPO_ROOT,
  source_manifest_path: Path = SOURCE_ARTIFACT_PACK_MANIFEST,
  source_payload_pack_path: Path = SOURCE_PAYLOAD_PACK,
  source_rights_gate_path: Path = SOURCE_RIGHTS_GATE,
  mechanism_hashes_path: Path = MECHANISM_HASHES,
  provenance_review_gate_path: Path = PROVENANCE_REVIEW_GATE,
  output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
  source_manifest = _read_json_if_exists(source_manifest_path)
  source_payload_pack = _read_json_if_exists(source_payload_pack_path)
  rights_gate = _read_json_if_exists(source_rights_gate_path)
  mechanism_hashes = _read_json_if_exists(mechanism_hashes_path)
  provenance_gate = _read_json_if_exists(provenance_review_gate_path)

  payloads_exist, hashes_match, payload_rows = _payload_files_verified(
    source_manifest=source_manifest,
    repo_root=repo_root,
  )
  benchmark_decision = _benchmark_consumption_decision(
    source_manifest=source_manifest,
    source_payload_pack=source_payload_pack,
    rights_gate=rights_gate,
    mechanism_hashes=mechanism_hashes,
  )
  guards = _merged_authority_guards(
    source_manifest,
    source_payload_pack,
    rights_gate,
    mechanism_hashes,
    provenance_gate,
  )
  checks = {
    "source_payload_pack_present": bool(source_manifest_path.exists() and source_manifest),
    "payload_retention_complete": bool(
      payloads_exist
      and source_manifest.get("source_payloads_retained", False)
      and source_manifest.get("retained_payload_count")
      == source_manifest.get("required_payload_count")
    ),
    "payload_hashes_match": hashes_match
    and bool(source_manifest.get("all_payload_hashes_match", False)),
    "public_distribution_support_present": _public_distribution_supported(
      rights_gate
    ),
    "release_grade_legal_rights_not_asserted": (
      _release_grade_legal_rights_not_asserted(
        source_manifest=source_manifest,
        rights_gate=rights_gate,
      )
    ),
    "allowed_output_policy_frozen_fail_closed": (
      _allowed_output_policy_frozen_fail_closed(rights_gate)
    ),
    "raw_payload_bodies_non_copyable": _raw_payload_bodies_non_copyable(
      rights_gate
    ),
    "benchmark_explicitly_not_consumed_or_hash_only_admitted": benchmark_decision[
      "satisfied"
    ],
    "beco_tp21_outputs_not_release_consumed_unless_hash_only_admitted": (
      not benchmark_decision["mechanism_outputs_benchmark_consumed_for_release"]
      and (
        not benchmark_decision["selected_outputs_admitted_by_rights_policy"]
        or not benchmark_decision["raw_comparison_values_detected"]
      )
    ),
    "comparison_values_not_copied": not benchmark_decision[
      "raw_comparison_values_detected"
    ],
    "provenance_identity_review_res001_author_side_present": (
      _provenance_res001_author_side_present(provenance_gate)
    ),
    "authority_guards_all_false": _all_false(guards),
  }
  missing = [check_id for check_id in REQUIRED_CHECKS if not checks.get(check_id)]
  narrowly_closeable = not missing
  status = (
    "narrowly_closeable_internal_release_signoff_fail_closed_boundaries"
    if narrowly_closeable
    else "failed_closed_res001_release_signoff_evidence_incomplete"
  )

  return {
    "package_id": PACKAGE_ID,
    "schema_version": SCHEMA_VERSION,
    "status": status,
    "review_target": "res_001_release_signoff_closeout",
    "artifact_dir": _display_path(output_dir, repo_root),
    "decision_scope": (
      "project_internal_release_signoff_evidence_only_not_legal_advice"
    ),
    "residual_decision": {
      "residual_id": "RES-001",
      "gate_result": (
        "narrowly_closeable_by_internal_release_signoff_gate"
        if narrowly_closeable
        else "failed_closed_missing_required_evidence"
      ),
      "residual_closeable_by_this_gate": narrowly_closeable,
      "release_grade_legal_rights_asserted": False,
      "legal_advice_provided": False,
      "closed_residual_ids_by_this_gate": ["RES-001"]
      if narrowly_closeable
      else [],
      "residual_ids_not_closed_by_this_gate": [
        "RES-002",
        "RES-003",
        "RES-004",
        "RES-005",
        "RES-006",
        "RES-013",
        "RES-014",
      ],
      "missing_required_fields": missing,
    },
    "input_artifacts": {
      "source_artifact_pack_manifest": _input_ref(
        source_manifest_path, source_manifest, repo_root
      ),
      "source_payload_pack": _input_ref(
        source_payload_pack_path, source_payload_pack, repo_root
      ),
      "source_rights_output_policy_gate": _input_ref(
        source_rights_gate_path, rights_gate, repo_root
      ),
      "mechanism_comparison_hashes": _input_ref(
        mechanism_hashes_path, mechanism_hashes, repo_root
      ),
      "provenance_identity_review_gate": _input_ref(
        provenance_review_gate_path, provenance_gate, repo_root
      ),
    },
    "required_checks": [
      {
        "check_id": check_id,
        "satisfied": bool(checks.get(check_id)),
      }
      for check_id in REQUIRED_CHECKS
    ],
    "source_payload_retention": {
      "complete": checks["payload_retention_complete"],
      "payload_hashes_match": checks["payload_hashes_match"],
      "required_payload_count": source_manifest.get("required_payload_count", 0),
      "retained_payload_count": source_manifest.get("retained_payload_count", 0),
      "payloads": payload_rows,
    },
    "rights_and_output_policy": {
      "public_distribution_support_present": checks[
        "public_distribution_support_present"
      ],
      "release_grade_legal_rights_asserted": False,
      "release_grade_legal_rights_not_asserted": checks[
        "release_grade_legal_rights_not_asserted"
      ],
      "allowed_output_policy_status": rights_gate.get(
        "allowed_output_policy", {}
      ).get("policy_status", ""),
      "allowed_output_policy_frozen_fail_closed": checks[
        "allowed_output_policy_frozen_fail_closed"
      ],
      "raw_payload_bodies_non_copyable": checks[
        "raw_payload_bodies_non_copyable"
      ],
      "copy_policy_summary": {
        "payload_bodies": "non_copyable",
        "spreadsheet_cells_formulas_outputs": "non_copyable",
        "comparison_values": "non_copyable",
        "hashes_and_policy_metadata": "copyable_as_evidence_only",
      },
    },
    "benchmark_and_comparison_output_policy": {
      "benchmark_consumption_decision": benchmark_decision,
      "beco_outputs_release_consumed": False,
      "tp21_outputs_release_consumed": False,
      "beco_tp21_outputs_not_release_consumed_unless_hash_only_admitted": checks[
        "beco_tp21_outputs_not_release_consumed_unless_hash_only_admitted"
      ],
      "comparison_values_not_copied": checks["comparison_values_not_copied"],
      "hash_only_comparison_anchor_count": mechanism_hashes.get(
        "beco_workbook", {}
      ).get("selected_comparison_output_count", 0),
      "tp21_selected_debris_output_hashes_present": bool(
        mechanism_hashes.get("comparison_hash_decision", {}).get(
          "tp21_selected_debris_output_hashes_present", False
        )
      ),
    },
    "provenance_identity_review_consumption": {
      "res001_author_side_checks_present": checks[
        "provenance_identity_review_res001_author_side_present"
      ],
      "provenance_gate_result_for_res001": provenance_gate.get(
        "residual_gate_results", {}
      ).get("RES-001", ""),
      "independent_release_identity_not_closed": True,
      "res002_not_closed_by_this_gate": True,
    },
    "authority_boundary_signoff": {
      "signed_off_by_this_gate": narrowly_closeable,
      "authority_guards_all_false": checks["authority_guards_all_false"],
      "non_authoritative_guards": guards,
      "stock_effect_component_pk_fuze_authority_all_false": (
        not guards["stock_descriptor_created"]
        and not guards["stock_database_authority_granted"]
        and not guards["effect_scale_authority_released"]
        and not guards["effect_scale_authority_in_stock"]
        and not guards["effect_scale_authority_granted"]
        and not guards["component_failure_probability_authority_released"]
        and not guards["component_failure_probability_authority_in_stock"]
        and not guards["component_failure_probability_authority_granted"]
        and not guards["pk_authority_released"]
        and not guards["pk_authority_granted"]
        and not guards["pk_authority"]
        and not guards["deterministic_fuze_authority_released"]
        and not guards["deterministic_fuze_authority_granted"]
        and not guards["deterministic_fuze_authority"]
      ),
    },
    "explicit_boundaries": [
      "This is project-internal release/signoff evidence only and is not legal advice.",
      "Retained payload public-distribution support is recorded; release-grade legal rights are not asserted.",
      "Raw payload bodies, spreadsheet cells/formulas/output tables, and comparison values are non-copyable.",
      "BEC-O and TP-21 outputs are not release-consumed unless admitted by hash-only policy.",
      "Current benchmark consumption is an explicit non-consumption decision.",
      "No stock, effect-scale, component-probability, Pk, deterministic-fuze, mechanism, or runtime authority is released.",
    ],
  }

def _retained_manifest(
  *,
  artifact: dict[str, Any],
  artifact_path: Path,
  artifact_text: str,
  report_path: Path,
  repo_root: Path,
) -> dict[str, Any]:
  return {
    "package_id": PACKAGE_ID,
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "status": artifact["status"],
    "artifact_dir": artifact["artifact_dir"],
    "res001_release_signoff_gate": {
      "filename": GATE_FILENAME,
      "relative_path": _display_path(artifact_path, repo_root),
      "sha256": _sha256_file(artifact_path),
      "content_sha256": _sha256_text(artifact_text.rstrip("\n")),
      "schema_version": SCHEMA_VERSION,
    },
    "validation_report": {
      "relative_path": _display_path(report_path, repo_root),
      "exists": report_path.exists(),
      "sha256": _sha256_file(report_path) if report_path.exists() else "",
    },
    "residual_decision": artifact["residual_decision"],
    "input_artifacts": artifact["input_artifacts"],
    "required_checks": artifact["required_checks"],
    "authority_boundary_signoff": artifact["authority_boundary_signoff"],
    "non_authoritative_guards": artifact["authority_boundary_signoff"][
      "non_authoritative_guards"
    ],
  }

def _report_text(artifact: dict[str, Any], manifest: dict[str, Any]) -> str:
  decision = artifact["residual_decision"]
  missing = decision["missing_required_fields"]
  missing_text = ", ".join(f"`{item}`" for item in missing) if missing else "`none`"
  result = decision["gate_result"]
  closeable = "`true`" if decision["residual_closeable_by_this_gate"] else "`false`"
  gate_sha = manifest["res001_release_signoff_gate"]["sha256"]
  manifest_ref = manifest.get("manifest_relative_path", "manifest.json")
  payload_complete = str(artifact["source_payload_retention"]["complete"]).lower()
  public_support = str(
    artifact["rights_and_output_policy"]["public_distribution_support_present"]
  ).lower()
  guards_false = str(
    artifact["authority_boundary_signoff"]["authority_guards_all_false"]
  ).lower()
  core_guards_false = str(
    artifact["authority_boundary_signoff"][
      "stock_effect_component_pk_fuze_authority_all_false"
    ]
  ).lower()
  authority_signed = str(
    artifact["authority_boundary_signoff"]["signed_off_by_this_gate"]
  ).lower()
  return f"""# RES-001 Release Signoff Closeout Gate - 2026-05-31

状态：`{artifact['status']}` / `project_internal_release_signoff_evidence_only_not_legal_advice` / `non-authoritative`。

本文记录 RES-001 的有界 release signoff closeout gate。该 gate 只消费已 retained 的 source payload pack、source rights / allowed-output policy gate、mechanism comparison hash manifest 和 provenance identity review gate；不提供法律意见，不复制 source body、spreadsheet raw value 或 comparison value，也不释放 stock / effect / component / Pk / fuze authority。

## 1. Decision

| field | value |
|---|---|
| `package_id` | `{artifact['package_id']}` |
| `schema_version` | `{artifact['schema_version']}` |
| `RES-001 gate result` | `{result}` |
| `residual_closeable_by_this_gate` | {closeable} |
| `missing_required_fields` | {missing_text} |
| `release_grade_legal_rights_asserted` | `false` |
| `legal_advice_provided` | `false` |
| `gate_sha256` | `{gate_sha}` |
| `retained_manifest` | `{manifest_ref}` |

## 2. Evidence Boundaries

| boundary | decision |
|---|---|
| payload retention | `{payload_complete}`; retained payload count `{artifact['source_payload_retention']['retained_payload_count']}` / required `{artifact['source_payload_retention']['required_payload_count']}` |
| public distribution support | `{public_support}` |
| release-grade legal rights | not asserted by this gate |
| allowed-output policy | `{artifact['rights_and_output_policy']['allowed_output_policy_status']}` |
| raw payload bodies | non-copyable |
| BEC-O / TP-21 outputs | not release-consumed unless hash-only admitted |
| benchmark consumption | `{artifact['benchmark_and_comparison_output_policy']['benchmark_consumption_decision']['decision']}` |
| comparison values | non-copyable; hash-only anchors may be retained |
| RES-002 / mechanism residuals | not closed |

## 3. Authority Guards

所有 authority guards 必须保持 `false`。本次结果：

| guard group | value |
|---|---|
| `authority_guards_all_false` | `{guards_false}` |
| `stock_effect_component_pk_fuze_authority_all_false` | `{core_guards_false}` |
| `authority_boundary_signed_off_by_this_gate` | `{authority_signed}` |

## 4. Verification

```bash
python3 tools/maintenance/damage_model.py release-governance source-release-signoff
pytest -q tests/architecture/damage_model/test_release_signoff_gate.py
```
"""

def write_retained_artifacts(
  *,
  repo_root: Path = REPO_ROOT,
  output_dir: Path = DEFAULT_OUTPUT_DIR,
  report_path: Path = DEFAULT_REPORT_PATH,
  source_manifest_path: Path = SOURCE_ARTIFACT_PACK_MANIFEST,
  source_payload_pack_path: Path = SOURCE_PAYLOAD_PACK,
  source_rights_gate_path: Path = SOURCE_RIGHTS_GATE,
  mechanism_hashes_path: Path = MECHANISM_HASHES,
  provenance_review_gate_path: Path = PROVENANCE_REVIEW_GATE,
) -> dict[str, Any]:
  output_dir.mkdir(parents=True, exist_ok=True)
  artifact = generate_res001_release_signoff_gate(
    repo_root=repo_root,
    source_manifest_path=source_manifest_path,
    source_payload_pack_path=source_payload_pack_path,
    source_rights_gate_path=source_rights_gate_path,
    mechanism_hashes_path=mechanism_hashes_path,
    provenance_review_gate_path=provenance_review_gate_path,
    output_dir=output_dir,
  )

  artifact_path = output_dir / GATE_FILENAME
  artifact_text = _canonical_json(artifact) + "\n"
  artifact_path.write_text(artifact_text, encoding="utf-8")

  report_path.parent.mkdir(parents=True, exist_ok=True)
  preliminary_manifest = _retained_manifest(
    artifact=artifact,
    artifact_path=artifact_path,
    artifact_text=artifact_text,
    report_path=report_path,
    repo_root=repo_root,
  )
  report_path.write_text(_report_text(artifact, preliminary_manifest), encoding="utf-8")

  manifest = _retained_manifest(
    artifact=artifact,
    artifact_path=artifact_path,
    artifact_text=artifact_text,
    report_path=report_path,
    repo_root=repo_root,
  )
  manifest_path = output_dir / MANIFEST_FILENAME
  manifest_text = _canonical_json(manifest) + "\n"
  manifest_path.write_text(manifest_text, encoding="utf-8")
  manifest["manifest_relative_path"] = _display_path(manifest_path, repo_root)
  manifest["manifest_sha256"] = _sha256_file(manifest_path)

  report_path.write_text(_report_text(artifact, manifest), encoding="utf-8")
  manifest = _retained_manifest(
    artifact=artifact,
    artifact_path=artifact_path,
    artifact_text=artifact_text,
    report_path=report_path,
    repo_root=repo_root,
  )
  manifest["manifest_relative_path"] = _display_path(manifest_path, repo_root)
  manifest_text = _canonical_json(manifest) + "\n"
  manifest_path.write_text(manifest_text, encoding="utf-8")
  manifest["manifest_sha256"] = _sha256_file(manifest_path)

  artifact["res001_release_signoff_gate_sha256"] = _sha256_file(artifact_path)
  artifact["retained_manifest_ref"] = _display_path(manifest_path, repo_root)
  artifact["retained_manifest_sha256"] = manifest["manifest_sha256"]
  artifact["validation_report_ref"] = _display_path(report_path, repo_root)
  artifact["validation_report_sha256"] = _sha256_file(report_path)
  return artifact

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Write the bounded A2 RES-001 release signoff closeout gate."
  )
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=DEFAULT_OUTPUT_DIR,
    help="Directory for retained RES-001 release signoff artifacts.",
  )
  parser.add_argument(
    "--report",
    type=Path,
    default=DEFAULT_REPORT_PATH,
    help="Markdown validation report path.",
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional path for a copy of the generated gate JSON.",
  )
  args = parser.parse_args(argv)

  artifact = write_retained_artifacts(output_dir=args.output_dir, report_path=args.report)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_canonical_json(artifact) + "\n", encoding="utf-8")
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
