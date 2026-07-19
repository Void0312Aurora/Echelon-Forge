#!/usr/bin/env python3
"""Generate the damage-model source-rights signoff request packet.

This packet is a retained, machine-readable checklist for rights-safe,
allowed-output review. It is deliberately not an approval: it reads only
retained JSON evidence, records refs and hashes, identifies hash-only outputs
that may be reviewed, and keeps every release/authority guard fail-closed.
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

from tools.maintenance.retained_artifacts.manifest_integrity import (
  _sha256_file,
  _sha256_text,
  write_and_hash_json,
)
PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
SCHEMA_VERSION = "a2.source_rights_signoff_request_packet.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
  "a2.source_rights_signoff_request_retained_manifest.v1"
)

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
RETAINED_ROOT = PACKAGE_DIR / "retained_artifacts"

SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH = (
  RETAINED_ROOT
  / "source_rights_output_policy_20260531"
  / "source_rights_output_policy_gate.json"
)
SOURCE_PAYLOAD_PACK_MANIFEST_PATH = (
  RETAINED_ROOT
  / "source_payload_pack_20260531"
  / "source_artifact_pack_manifest.json"
)
RES005_SELECTED_CASE_GATE_PATH = (
  RETAINED_ROOT
  / "res005_tp21_selected_case_admission_20260601"
  / "res005_tp21_selected_case_admission_review_gate.json"
)
RES006_REPLACEMENT_TOLERANCE_GATE_PATH = (
  RETAINED_ROOT
  / "res006_beco_replacement_tolerance_admission_20260601"
  / "res006_beco_replacement_tolerance_admission_gate.json"
)
DEFAULT_RETAINED_DIR = (
  RETAINED_ROOT / "source_rights_signoff_request_20260601"
)

PACKET_FILENAME = "source_rights_signoff_request_packet.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

def _rel(path: Path, repo_root: Path) -> str:
  # Kept local: resolve ok but fallback path.as_posix() != str(path).
  try:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
  except ValueError:
    return path.as_posix()

def _load_json_optional(path: Path) -> dict[str, Any] | None:
  if not path.is_file():
    return None
  try:
    return json.loads(path.read_text(encoding="utf-8"))
  except json.JSONDecodeError:
    return None

def _write_json(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )

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
    "required_for_request_packet": required,
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

  ref["schema_version"] = payload.get("schema_version", "")
  ref["status"] = payload.get("status", "")
  return ref

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

def _source_payload_ref(
  source_manifest: dict[str, Any] | None,
  *,
  label: str,
) -> dict[str, Any]:
  for row in (source_manifest or {}).get("artifacts", []):
    if row.get("source_artifact_label") == label:
      return {
        "source_artifact_label": row.get("source_artifact_label", label),
        "source_id": row.get("source_id", ""),
        "requirement_id": row.get("requirement_id", ""),
        "relative_path": row.get("relative_path", ""),
        "payload_sha256": row.get("sha256") or row.get("actual_sha256", ""),
        "hash_matches_expected": bool(row.get("hash_matches_expected")),
        "benchmark_consumed_for_release": bool(
          row.get("benchmark_consumed_for_release")
        ),
        "rights_status": row.get("rights_status", ""),
      }
  return {
    "source_artifact_label": label,
    "source_id": "",
    "requirement_id": "",
    "relative_path": "",
    "payload_sha256": "",
    "hash_matches_expected": False,
    "benchmark_consumed_for_release": False,
    "rights_status": "missing_fail_closed",
  }

def _policy_summary(
  source_rights_policy: dict[str, Any] | None,
  source_policy_ref: dict[str, Any],
) -> dict[str, Any]:
  policy = (source_rights_policy or {}).get("allowed_output_policy", {})
  result = (source_rights_policy or {}).get("res_001_gate_result", {})
  return {
    "relative_path": source_policy_ref["relative_path"],
    "present": bool(source_rights_policy),
    "sha256": source_policy_ref.get("sha256", ""),
    "schema_version": source_policy_ref.get("schema_version", ""),
    "status": source_policy_ref.get("status", "missing_fail_closed"),
    "policy_status": policy.get("policy_status", "missing_fail_closed"),
    "policy_frozen_by_existing_gate": bool(policy.get("policy_frozen_by_this_gate")),
    "fail_closed": True,
    "approval_granted": False,
    "release_grade_satisfied": False,
    "source_gate_release_grade_satisfied": bool(
      result.get("release_grade_satisfied")
    ),
    "allowed_output_policy_release_grade_satisfied": bool(
      result.get("allowed_output_policy_release_grade_satisfied")
    ),
    "comparison_outputs_admitted": bool(result.get("comparison_outputs_admitted")),
    "benchmark_consumption_release_grade_satisfied": bool(
      result.get("benchmark_consumption_release_grade_satisfied")
    ),
    "current_selected_comparison_output_hash_count": len(
      policy.get("current_selected_comparison_output_hashes", [])
    ),
    "allowed_hash_outputs": policy.get("allowed_hash_outputs", []),
    "forbidden_copy_outputs": policy.get("forbidden_copy_outputs", []),
    "forbidden_consume_outputs": policy.get("forbidden_consume_outputs", []),
    "blocking_conditions": result.get("blocking_conditions", []),
  }

def _retained_payload_hash_review_items(
  source_manifest: dict[str, Any] | None,
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for label, residual_id in (
    ("TP-21 PDF", "RES-005"),
    ("BEC-O-V1.xlsx", "RES-006"),
  ):
    payload_ref = _source_payload_ref(source_manifest, label=label)
    rows.append(
      {
        "item_id": f"{residual_id}-RETAINED-PAYLOAD-SHA256",
        "residual_id": residual_id,
        "source_artifact_label": label,
        "request_review_allowed": bool(payload_ref["payload_sha256"]),
        "request_review_status": (
          "requestable_payload_hash_rights_evidence_only"
          if payload_ref["payload_sha256"]
          else "missing_payload_hash_fail_closed"
        ),
        "hash_only_outputs": {
          "payload_sha256": payload_ref["payload_sha256"],
        },
        "raw_source_content_retained": False,
        "benchmark_consumed_for_release": False,
        "approval_granted": False,
      }
    )
  return rows

def _tp21_hash_output_request(
  res005_gate: dict[str, Any] | None,
  source_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
  payload_ref = _source_payload_ref(source_manifest, label="TP-21 PDF")
  if res005_gate is None:
    return {
      "item_id": "RES-005-TP21-SELECTED-CASE-HASH-ONLY-OUTPUTS",
      "residual_id": "RES-005",
      "source_artifact_label": "TP-21 PDF",
      "request_review_allowed": False,
      "request_review_status": "res005_selected_case_packet_missing_fail_closed",
      "hash_only_outputs": {
        "payload_sha256": payload_ref["payload_sha256"],
        "selected_output_preimage_sha256_present": False,
        "selected_debris_output_hash_count": 0,
        "selected_debris_output_set_sha256": "",
      },
      "required_before_review_request": [
        "reviewer_selected_case_locator_label",
        "selected_output_preimage_sha256",
        "selected_debris_output_hash_anchor_set",
      ],
      "raw_selected_outputs_retained": False,
      "raw_source_content_retained": False,
      "approval_granted": False,
    }

  evidence = res005_gate.get("selected_case_evidence_state", {})
  prior = res005_gate.get("prior_debris_gate_summary", {})
  selected_hash_count = int(prior.get("selected_debris_output_hash_count", 0))
  requestable = bool(
    evidence.get("reviewer_selected_case_locator_present")
    and evidence.get("selected_output_preimage_sha256_present")
    and selected_hash_count > 0
  )
  return {
    "item_id": "RES-005-TP21-SELECTED-CASE-HASH-ONLY-OUTPUTS",
    "residual_id": "RES-005",
    "source_artifact_label": "TP-21 PDF",
    "request_review_allowed": requestable,
    "request_review_status": (
      "requestable_for_allowed_output_review_not_admitted"
      if requestable
      else "blocked_missing_selected_case_hash_inputs_fail_closed"
    ),
    "hash_only_outputs": {
      "payload_sha256": payload_ref["payload_sha256"],
      "controlled_criteria_vocabulary_sha256": prior.get(
        "controlled_criteria_vocabulary_sha256", ""
      ),
      "selected_output_preimage_sha256_present": bool(
        evidence.get("selected_output_preimage_sha256_present")
      ),
      "selected_debris_output_hash_count": selected_hash_count,
      "selected_debris_output_set_sha256": prior.get(
        "selected_debris_output_set_sha256", ""
      ),
    },
    "required_before_review_request": [
      item["item_id"]
      for item in res005_gate.get("required_reviewer_signoff_items", [])
      if not item.get("present")
      and item.get("item_id")
      in {
        "TP21-SELECTED-CASE-LOCATOR",
        "TP21-SELECTED-OUTPUT-PREIMAGE-SHA256",
        "TP21-SELECTED-DEBRIS-OUTPUT-ANCHOR-SET",
      }
    ],
    "raw_selected_outputs_retained": False,
    "raw_source_content_retained": False,
    "source_tables_retained": False,
    "source_figures_retained": False,
    "source_numeric_values_retained": False,
    "approval_granted": False,
  }

def _beco_hash_output_request(
  res006_gate: dict[str, Any] | None,
  source_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
  payload_ref = _source_payload_ref(source_manifest, label="BEC-O-V1.xlsx")
  if res006_gate is None:
    return {
      "item_id": "RES-006-BECO-HASH-ONLY-OUTPUTS",
      "residual_id": "RES-006",
      "source_artifact_label": "BEC-O-V1.xlsx",
      "request_review_allowed": False,
      "request_review_status": "res006_replacement_tolerance_packet_missing_fail_closed",
      "hash_only_outputs": {
        "payload_sha256": payload_ref["payload_sha256"],
        "comparison_row_count": 0,
        "cached_anchor_count": 0,
        "recalculated_anchor_count": 0,
        "rows": [],
      },
      "raw_selected_values_retained": False,
      "formula_text_retained": False,
      "approval_granted": False,
    }

  mismatch = res006_gate.get("cached_vs_recalculated_mismatch_summary", {})
  replacement = res006_gate.get("replacement_candidate_summary", {})
  rows = []
  for row in mismatch.get("hash_only_comparison_rows", []):
    rows.append(
      {
        "comparison_id": row.get("comparison_id", ""),
        "source_artifact_label": row.get(
          "source_artifact_label", "BEC-O-V1.xlsx"
        ),
        "output_role": row.get("output_role", ""),
        "unit_family": row.get("unit_family", ""),
        "cached_anchor_sha256": row.get("cached_anchor_sha256", ""),
        "recalculated_output_sha256": row.get(
          "recalculated_output_sha256", ""
        ),
        "formula_sha256": row.get("formula_sha256", ""),
        "hashes_match": bool(row.get("hashes_match")),
        "raw_value_disclosed": False,
        "formula_text_disclosed": False,
      }
    )
  requestable = bool(rows)
  return {
    "item_id": "RES-006-BECO-HASH-ONLY-OUTPUTS",
    "residual_id": "RES-006",
    "source_artifact_label": "BEC-O-V1.xlsx",
    "request_review_allowed": requestable,
    "request_review_status": (
      "requestable_for_allowed_output_and_replacement_review_not_admitted"
      if requestable
      else "blocked_missing_beco_hash_outputs_fail_closed"
    ),
    "hash_only_outputs": {
      "payload_sha256": payload_ref["payload_sha256"],
      "comparison_row_count": int(mismatch.get("comparison_row_count", 0)),
      "cached_anchor_count": int(mismatch.get("cached_anchor_count", 0)),
      "recalculated_anchor_count": int(
        mismatch.get("recalculated_anchor_count", 0)
      ),
      "mismatch_count": int(mismatch.get("mismatch_count", 0)),
      "exact_hash_check_passed": bool(mismatch.get("exact_hash_check_passed")),
      "cached_selected_output_set_sha256": mismatch.get(
        "cached_selected_output_set_sha256", ""
      ),
      "recalculated_selected_output_set_sha256": replacement.get(
        "selected_recalculated_output_set_sha256", ""
      ),
      "rows": rows,
    },
    "raw_selected_values_retained": False,
    "formula_text_retained": False,
    "temporary_workbook_copy_retained": False,
    "stdout_retained": False,
    "stderr_retained": False,
    "approval_granted": False,
  }

def _requested_signoff_items(
  *,
  tp21_request: dict[str, Any],
  beco_request: dict[str, Any],
) -> list[dict[str, Any]]:
  return [
    {
      "signoff_id": "source_rights_independent_review",
      "requested_from": "independent_rights_reviewer_or_release_owner",
      "request_scope": "retained TP-21 and BEC-O source payload hashes and public-distribution support",
      "required_decision": "rights_reviewed_release_grade_or_explicitly_rejected",
      "current_status": "missing_fail_closed",
      "approval_granted": False,
    },
    {
      "signoff_id": "allowed_output_policy_release_grade_review",
      "requested_from": "allowed_output_policy_reviewer",
      "request_scope": "hash-only output policy, forbidden-copy policy, and consume/do-not-consume boundaries",
      "required_decision": "reviewer_frozen_release_grade_allowed_output_policy_or_rejected",
      "current_status": "missing_fail_closed",
      "approval_granted": False,
    },
    {
      "signoff_id": "tp21_selected_case_hash_only_allowed_output_review",
      "requested_from": "source_rights_reviewer",
      "request_scope": tp21_request["item_id"],
      "request_review_allowed": tp21_request["request_review_allowed"],
      "required_decision": "admit_or_reject_selected TP-21 comparison-output hashes only",
      "current_status": "missing_fail_closed",
      "approval_granted": False,
    },
    {
      "signoff_id": "beco_hash_only_allowed_output_review",
      "requested_from": "source_rights_reviewer",
      "request_scope": beco_request["item_id"],
      "request_review_allowed": beco_request["request_review_allowed"],
      "required_decision": "admit_or_reject_selected BEC-O comparison-output hashes only",
      "current_status": "missing_fail_closed",
      "approval_granted": False,
    },
    {
      "signoff_id": "beco_lineage_tolerance_and_replacement_review",
      "requested_from": "independent_lineage_reviewer_numeric_tolerance_owner_and_replacement_anchor_owner",
      "request_scope": "BEC-O cached-vs-recalculated hash mismatch, tolerance policy, and candidate replacement anchor set",
      "required_decision": "admit_or_reject_replacement_anchor_without_mutating_cached_anchors_in_place",
      "current_status": "missing_fail_closed",
      "approval_granted": False,
    },
    {
      "signoff_id": "benchmark_consumption_release_decision",
      "requested_from": "release_owner",
      "request_scope": "explicit consume-or-do-not-consume release decision for TP-21 and BEC-O hash-only outputs",
      "required_decision": "benchmark_consumption_allowed_or_explicitly_denied",
      "current_status": "missing_fail_closed",
      "approval_granted": False,
    },
    {
      "signoff_id": "authority_boundary_confirmation",
      "requested_from": "integration_owner",
      "request_scope": "confirm all stock/runtime/effect/component/Pk/fuze/source-truth guards remain false before and after review",
      "required_decision": "all_authority_guards_false_or_packet_rejected",
      "current_status": "missing_fail_closed",
      "approval_granted": False,
    },
  ]

def _explicit_forbidden_outputs(
  source_rights_policy: dict[str, Any] | None,
) -> list[dict[str, Any]]:
  policy = (source_rights_policy or {}).get("allowed_output_policy", {})
  source_forbidden = [
    *policy.get("forbidden_copy_outputs", []),
    *policy.get("forbidden_consume_outputs", []),
  ]
  specific = [
    "tp21_source_prose_tables_figures_or_numeric_values",
    "tp21_raw_selected_output_payloads",
    "tp21_selected_output_preimage_body",
    "beco_spreadsheet_formulas_or_cell_ranges",
    "beco_raw_cell_values_or_tool_output_tables",
    "beco_temporary_workbook_copy_stdout_or_stderr",
    "comparison_output_values_without_review_admission",
    "stock_descriptor_fields_or_runtime_authority_fields",
  ]
  outputs: list[dict[str, Any]] = []
  for output_id in dict.fromkeys([*source_forbidden, *specific]):
    outputs.append(
      {
        "output_id": output_id,
        "current_status": "forbidden_fail_closed",
        "requestable": False,
        "approval_granted": False,
      }
    )
  return outputs

def _hash_only_allowed_request_shape() -> dict[str, Any]:
  return {
    "shape_id": "hash_only_allowed_output_signoff_request_shape_v1",
    "allowed_retained_fields": [
      "residual_id",
      "source_artifact_label",
      "source_id",
      "requirement_id",
      "input_artifact_relative_path",
      "input_artifact_sha256",
      "payload_sha256",
      "comparison_id",
      "output_role_label",
      "unit_family_label",
      "comparison_output_sha256",
      "recalculated_output_sha256",
      "formula_sha256",
      "hash_set_sha256",
      "hash_count",
      "signoff_id",
      "review_decision_ref",
    ],
    "required_absences": [
      "source prose",
      "source tables",
      "source figures",
      "source numeric values",
      "spreadsheet formulas",
      "spreadsheet cell ranges",
      "raw selected output values",
      "selected output preimage bodies",
      "temporary workbook copies",
      "stdout",
      "stderr",
    ],
    "request_may_reference_prior_retained_json_only": True,
    "approval_granted": False,
    "release_grade_satisfied": False,
  }

def _current_missing_items(signoffs: list[dict[str, Any]]) -> list[dict[str, str]]:
  return [
    {
      "signoff_id": row["signoff_id"],
      "requested_from": row["requested_from"],
      "missing_reason": "signoff_or_review_decision_not_present",
    }
    for row in signoffs
    if not row["approval_granted"]
  ]

def generate_source_rights_signoff_request_packet(
  *,
  repo_root: Path = REPO_ROOT,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  source_rights_output_policy_gate_path: Path = (
    SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH
  ),
  source_payload_pack_manifest_path: Path = SOURCE_PAYLOAD_PACK_MANIFEST_PATH,
  res005_selected_case_gate_path: Path = RES005_SELECTED_CASE_GATE_PATH,
  res006_replacement_tolerance_gate_path: Path = (
    RES006_REPLACEMENT_TOLERANCE_GATE_PATH
  ),
) -> dict[str, Any]:
  input_refs = [
    _input_ref(
      artifact_key="source_rights_output_policy_gate",
      path=source_rights_output_policy_gate_path,
      repo_root=repo_root,
      role="current_fail_closed_allowed_output_policy_input",
      required=True,
    ),
    _input_ref(
      artifact_key="source_payload_pack_manifest",
      path=source_payload_pack_manifest_path,
      repo_root=repo_root,
      role="retained_source_payload_manifest_input",
      required=True,
    ),
    _input_ref(
      artifact_key="res005_tp21_selected_case_admission_review_gate",
      path=res005_selected_case_gate_path,
      repo_root=repo_root,
      role="optional_current_res005_tp21_hash_only_packet_input",
      required=False,
    ),
    _input_ref(
      artifact_key="res006_beco_replacement_tolerance_admission_gate",
      path=res006_replacement_tolerance_gate_path,
      repo_root=repo_root,
      role="optional_current_res006_beco_hash_only_packet_input",
      required=False,
    ),
  ]
  refs_by_key = {row["artifact_key"]: row for row in input_refs}

  source_rights_policy = _load_json_optional(source_rights_output_policy_gate_path)
  source_manifest = _load_json_optional(source_payload_pack_manifest_path)
  res005_gate = _load_json_optional(res005_selected_case_gate_path)
  res006_gate = _load_json_optional(res006_replacement_tolerance_gate_path)

  tp21_request = _tp21_hash_output_request(res005_gate, source_manifest)
  beco_request = _beco_hash_output_request(res006_gate, source_manifest)
  retained_payload_requests = _retained_payload_hash_review_items(source_manifest)
  signoff_items = _requested_signoff_items(
    tp21_request=tp21_request,
    beco_request=beco_request,
  )
  guards = _authority_guards()
  missing_required_inputs = [
    row["artifact_key"]
    for row in input_refs
    if row["required_for_request_packet"] and not row["present"]
  ]
  status = (
    "blocked_fail_closed_source_rights_signoff_request_inputs_missing"
    if missing_required_inputs
    else "retained_fail_closed_source_rights_signoff_request_packet"
  )

  return {
    "schema_version": SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": status,
    "packet_type": "source_rights_allowed_output_signoff_request_checklist",
    "artifact_dir": _rel(retained_dir, repo_root),
    "request_id": "TC-A2-BF-003-RIGHTS-SIGNOFF-REQUEST-20260601",
    "approval_granted": False,
    "release_grade_satisfied": False,
    "admission_granted": False,
    "fail_closed": True,
    "input_refs": input_refs,
    "current_policy_status": _policy_summary(
      source_rights_policy,
      refs_by_key["source_rights_output_policy_gate"],
    ),
    "source_payload_hash_refs": {
      "tp21": _source_payload_ref(source_manifest, label="TP-21 PDF"),
      "beco": _source_payload_ref(source_manifest, label="BEC-O-V1.xlsx"),
    },
    "hash_only_allowed_request_shape": _hash_only_allowed_request_shape(),
    "requested_hash_only_review_items": [
      *retained_payload_requests,
      tp21_request,
      beco_request,
    ],
    "requested_signoff_items": signoff_items,
    "current_missing_items": _current_missing_items(signoff_items),
    "explicit_forbidden_outputs": _explicit_forbidden_outputs(
      source_rights_policy
    ),
    "forbidden_output_policy": {
      "raw_source_text_tables_values_formulas_retained": False,
      "raw_outputs_retained": False,
      "selected_output_preimages_retained": False,
      "benchmark_consumed_for_release": False,
      "copy_or_consume_forbidden_outputs": [
        row["output_id"]
        for row in _explicit_forbidden_outputs(source_rights_policy)
      ],
    },
    "authority_guards": guards,
    "authority_guards_all_false": not any(guards.values()),
    "authority_must_remain_false_before_signoff": sorted(guards),
    "signoff_preconditions": [
      "source rights reviewer must admit only hash outputs, not raw TP-21 or BEC-O content",
      "TP-21 selected case hashes cannot be reviewed until locator, preimage sha256, and selected output hashes exist",
      "BEC-O cached/recalculated hash pairs can be reviewed as hash-only evidence but remain unadmitted",
      "release-grade benchmark consumption requires explicit consume-or-do-not-consume decision",
      "all authority guards must remain false until and unless a later retained approval packet says otherwise",
    ],
    "behavior_risks": [
      "this packet can be mistaken for approval because it lists requestable BEC-O hash rows",
      "TP-21 empty selected-output anchor can be mistaken for selected-case evidence",
      "formula sha256 values can be mistaken for permission to disclose formula text",
      "source-rights policy remains release-candidate fail-closed until a separate reviewer signoff is retained",
    ],
    "integration_notes": [
      "This request packet does not modify source-rights policy gates, source ledgers, source payloads, residual registers, or status docs.",
      "RES-005 and RES-006 remain fail-closed; this packet only names the signoffs needed for later review.",
      "No TP-21/BEC-O raw source text, tables, values, formulas, raw outputs, workbook copies, stdout, or stderr are retained here.",
    ],
    "packet_sha256": _sha256_text(
      json.dumps(
        {
          "input_refs": input_refs,
          "requested_hash_only_review_items": [
            *retained_payload_requests,
            tp21_request,
            beco_request,
          ],
          "requested_signoff_items": signoff_items,
          "authority_guards": guards,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
      )
    ),
  }

def write_retained_artifacts(
  *,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  source_rights_output_policy_gate_path: Path = (
    SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH
  ),
  source_payload_pack_manifest_path: Path = SOURCE_PAYLOAD_PACK_MANIFEST_PATH,
  res005_selected_case_gate_path: Path = RES005_SELECTED_CASE_GATE_PATH,
  res006_replacement_tolerance_gate_path: Path = (
    RES006_REPLACEMENT_TOLERANCE_GATE_PATH
  ),
) -> dict[str, Any]:
  artifact = generate_source_rights_signoff_request_packet(
    repo_root=repo_root,
    retained_dir=retained_dir,
    source_rights_output_policy_gate_path=source_rights_output_policy_gate_path,
    source_payload_pack_manifest_path=source_payload_pack_manifest_path,
    res005_selected_case_gate_path=res005_selected_case_gate_path,
    res006_replacement_tolerance_gate_path=res006_replacement_tolerance_gate_path,
  )
  packet_path = retained_dir / PACKET_FILENAME
  packet_sha256 = write_and_hash_json(packet_path, artifact, ensure_ascii=False)
  packet_artifact = {
    "artifact_key": "source_rights_signoff_request_packet",
    "filename": PACKET_FILENAME,
    "relative_path": _rel(packet_path, repo_root),
    "schema_version": artifact["schema_version"],
    "sha256": packet_sha256,
  }

  manifest = {
    "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": artifact["status"],
    "artifact_dir": _rel(retained_dir, repo_root),
    "artifacts": [packet_artifact],
    "input_refs": artifact["input_refs"],
    "approval_granted": False,
    "release_grade_satisfied": False,
    "fail_closed": True,
    "requested_signoff_item_count": len(artifact["requested_signoff_items"]),
    "requested_hash_only_review_item_count": len(
      artifact["requested_hash_only_review_items"]
    ),
    "current_missing_items": artifact["current_missing_items"],
    "raw_source_text_tables_values_formulas_retained": False,
    "raw_outputs_retained": False,
    "benchmark_consumed_for_release": False,
    "authority_guards": artifact["authority_guards"],
    "authority_guards_all_false": artifact["authority_guards_all_false"],
  }
  manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
  manifest_sha256 = write_and_hash_json(manifest_path, manifest, ensure_ascii=False)

  artifact["retained_artifact_ref"] = _rel(packet_path, repo_root)
  artifact["retained_artifact_sha256"] = packet_sha256
  artifact["retained_manifest_ref"] = _rel(manifest_path, repo_root)
  artifact["retained_manifest_sha256"] = manifest_sha256
  return artifact

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the fail-closed damage-model source-rights allowed-output signoff "
      "request packet."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional path for a copy of the generated request packet JSON.",
  )
  parser.add_argument(
    "--retained-dir",
    type=Path,
    default=DEFAULT_RETAINED_DIR,
    help="Directory for retained source-rights signoff request artifacts.",
  )
  parser.add_argument(
    "--source-rights-output-policy-gate",
    type=Path,
    default=SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH,
    help="Existing source-rights output policy gate JSON.",
  )
  parser.add_argument(
    "--source-payload-pack-manifest",
    type=Path,
    default=SOURCE_PAYLOAD_PACK_MANIFEST_PATH,
    help="Existing source payload pack manifest JSON.",
  )
  parser.add_argument(
    "--res005-selected-case-gate",
    type=Path,
    default=RES005_SELECTED_CASE_GATE_PATH,
    help="Optional current RES-005 TP-21 selected-case packet JSON.",
  )
  parser.add_argument(
    "--res006-replacement-tolerance-gate",
    type=Path,
    default=RES006_REPLACEMENT_TOLERANCE_GATE_PATH,
    help="Optional current RES-006 BEC-O replacement/tolerance packet JSON.",
  )
  args = parser.parse_args(argv)

  artifact = write_retained_artifacts(
    retained_dir=args.retained_dir,
    source_rights_output_policy_gate_path=args.source_rights_output_policy_gate,
    source_payload_pack_manifest_path=args.source_payload_pack_manifest,
    res005_selected_case_gate_path=args.res005_selected_case_gate,
    res006_replacement_tolerance_gate_path=args.res006_replacement_tolerance_gate,
  )
  if args.output:
    _write_json(args.output, artifact)
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
