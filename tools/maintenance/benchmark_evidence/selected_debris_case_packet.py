#!/usr/bin/env python3
"""Generate a fail-closed TP-21 selected-case candidate packet for RES-005.

The packet is candidate evidence only. It retains refs, hashes, controlled
labels, selection criteria, missing reviewer inputs, and authority guards. It
does not extract or retain TP-21 prose, tables, figures, raw numeric values, or
raw selected outputs, and it does not close RES-005.
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
from tools.maintenance.benchmark_evidence import comparison_hashes # noqa: E402

PACKAGE_ID = comparison_hashes.PACKAGE_ID
SCHEMA_VERSION = "a2.res005_tp21_selected_case_candidate_packet.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
  "a2.res005_tp21_selected_case_candidate_retained_manifest.v1"
)

PACKAGE_DIR = comparison_hashes.PACKAGE_DIR
RETAINED_ARTIFACTS_DIR = PACKAGE_DIR / "retained_artifacts"
SOURCE_PAYLOAD_PACK_DIR = RETAINED_ARTIFACTS_DIR / "source_payload_pack_20260531"
DEBRIS_ADMISSION_DIR = RETAINED_ARTIFACTS_DIR / "res005_tp21_debris_admission_20260531"
SOURCE_RIGHTS_POLICY_DIR = (
  RETAINED_ARTIFACTS_DIR / "source_rights_output_policy_20260531"
)
SELECTED_CASE_ADMISSION_DIR = (
  RETAINED_ARTIFACTS_DIR / "res005_tp21_selected_case_admission_20260601"
)
DEFAULT_RETAINED_DIR = (
  RETAINED_ARTIFACTS_DIR / "res005_tp21_selected_case_candidate_20260601"
)

SOURCE_ARTIFACT_PACK_MANIFEST_PATH = (
  SOURCE_PAYLOAD_PACK_DIR / "source_artifact_pack_manifest.json"
)
DEBRIS_GATE_PATH = DEBRIS_ADMISSION_DIR / "res005_tp21_debris_admission_gate.json"
DEBRIS_ANCHOR_SET_PATH = DEBRIS_ADMISSION_DIR / "selected_debris_output_anchor_set.json"
SOURCE_RIGHTS_POLICY_PATH = SOURCE_RIGHTS_POLICY_DIR / "source_rights_output_policy_gate.json"
SELECTED_CASE_ADMISSION_REVIEW_GATE_PATH = (
  SELECTED_CASE_ADMISSION_DIR / "res005_tp21_selected_case_admission_review_gate.json"
)

PACKET_FILENAME = "res005_tp21_selected_case_candidate_packet.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

def _rel(path: Path, repo_root: Path) -> str:
  # Kept local: resolve ok but fallback path.as_posix() != str(path).
  try:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
  except ValueError:
    return path.as_posix()

def _canonical_json(payload: Any) -> str:
  return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )

def _artifact_ref(
  *,
  artifact_id: str,
  path: Path,
  repo_root: Path,
  role: str,
  payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
  ref: dict[str, Any] = {
    "artifact_id": artifact_id,
    "role": role,
    "relative_path": _rel(path, repo_root),
    "sha256": _sha256_file(path),
  }
  if payload is not None:
    ref["schema_version"] = payload.get("schema_version", "")
    ref["status"] = payload.get("status", "")
  return ref

def _authority_guards() -> dict[str, bool]:
  return {
    "benchmark_consumption_authority_granted": False,
    "blast_mechanism_authority_granted": False,
    "component_failure_probability_authority_granted": False,
    "deterministic_fuze_authority_granted": False,
    "effect_scale_authority_granted": False,
    "fragment_mechanism_authority_granted": False,
    "pk_authority_granted": False,
    "runtime_authority_granted": False,
    "stock_database_authority_granted": False,
    "stock_descriptor_created": False,
  }

def _tp21_source_artifact(source_manifest: dict[str, Any]) -> dict[str, Any]:
  for row in source_manifest.get("artifacts", []):
    if row.get("source_id") == "VPS-BFM-015":
      return row
    if row.get("source_artifact_label") == "TP-21 PDF":
      return row
  return {}

def _tp21_rights_row(source_rights_policy: dict[str, Any]) -> dict[str, Any]:
  for row in source_rights_policy.get("payload_rights_inventory", []):
    if row.get("source_id") == "VPS-BFM-015":
      return row
    if row.get("source_artifact_label") == "TP-21 PDF":
      return row
  return {}

def _source_payload_summary(source_manifest: dict[str, Any]) -> dict[str, Any]:
  tp21 = _tp21_source_artifact(source_manifest)
  return {
    "source_id": tp21.get("source_id", "VPS-BFM-015"),
    "source_artifact_label": tp21.get("source_artifact_label", "TP-21 PDF"),
    "relative_path": tp21.get("relative_path", ""),
    "sha256": tp21.get("sha256", tp21.get("actual_sha256", "")),
    "payload_exists": bool(tp21.get("payload_exists")),
    "hash_matches_expected": bool(tp21.get("hash_matches_expected")),
    "retention_status": tp21.get(
      "retention_status", tp21.get("payload_retention_status", "")
    ),
    "rights_status": tp21.get("rights_status", ""),
    "allowed_use": tp21.get("allowed_use", ""),
    "benchmark_consumed_for_release": bool(
      tp21.get("benchmark_consumed_for_release")
    ),
    "benchmark_consumption_status": tp21.get("benchmark_consumption_status", ""),
  }

def _rights_summary(source_rights_policy: dict[str, Any]) -> dict[str, Any]:
  allowed_policy = source_rights_policy.get("allowed_output_policy", {})
  tp21 = _tp21_rights_row(source_rights_policy)
  tp21_policy = tp21.get("output_policy", {})
  current_hashes = allowed_policy.get("current_selected_comparison_output_hashes", [])
  return {
    "schema_version": source_rights_policy.get("schema_version", ""),
    "status": source_rights_policy.get("status", ""),
    "policy_status": allowed_policy.get("policy_status", ""),
    "release_grade_satisfied": bool(allowed_policy.get("release_grade_satisfied")),
    "current_selected_comparison_output_hash_count": len(current_hashes),
    "tp21_current_comparison_outputs_admitted": bool(
      tp21_policy.get("current_comparison_outputs_admitted")
    ),
    "tp21_release_consumption_allowed": bool(
      tp21.get("release_consumption_allowed")
    ),
    "tp21_benchmark_consumed_for_release": bool(
      tp21.get("benchmark_consumed_for_release")
    ),
    "hash_allowed_outputs": tp21_policy.get(
      "hash_allowed_outputs", allowed_policy.get("allowed_hash_outputs", [])
    ),
    "copy_forbidden_outputs": tp21_policy.get(
      "copy_forbidden_outputs", allowed_policy.get("forbidden_copy_outputs", [])
    ),
    "consume_forbidden_outputs": tp21_policy.get(
      "consume_forbidden_outputs",
      allowed_policy.get("forbidden_consume_outputs", []),
    ),
  }

def _admission_evidence_state(
  admission_review_gate: dict[str, Any],
) -> dict[str, Any]:
  evidence = admission_review_gate.get("selected_case_evidence_state", {})
  decision = admission_review_gate.get("decision", {})
  return {
    "reviewer_selected_case_locator_present": bool(
      evidence.get("reviewer_selected_case_locator_present")
    ),
    "selected_output_preimage_sha256_present": bool(
      evidence.get("selected_output_preimage_sha256_present")
    ),
    "selected_debris_output_hash_count": int(
      evidence.get("selected_debris_output_hash_count", 0)
    ),
    "independent_reviewer_signoff_present": bool(
      evidence.get("independent_reviewer_signoff_present")
    ),
    "allowed_output_signoff_present": bool(
      evidence.get("allowed_output_signoff_present")
    ),
    "admission_review_status": admission_review_gate.get("status", ""),
    "admission_review_decision": decision.get("decision", ""),
    "selected_tp21_case_admitted": bool(decision.get("selected_tp21_case_admitted")),
    "release_grade_validated": bool(decision.get("release_grade_validated")),
  }

def _present_missing_item(
  *,
  item_id: str,
  description: str,
  present: bool,
  retained_form: str,
  missing_reason: str,
) -> dict[str, Any]:
  return {
    "item_id": item_id,
    "description": description,
    "present": present,
    "retained_form": retained_form,
    "current_status": "present" if present else "missing_fail_closed",
    "missing_reason": "" if present else missing_reason,
  }

def _present_vs_missing(
  *,
  source_payload: dict[str, Any],
  anchor_set: dict[str, Any],
  evidence_state: dict[str, Any],
  rights_summary: dict[str, Any],
) -> list[dict[str, Any]]:
  return [
    _present_missing_item(
      item_id="TP21-PAYLOAD-RETAINED-HASH-MATCHED",
      description="retained TP-21 payload file exists and sha256 matches manifest",
      present=bool(source_payload["payload_exists"])
      and bool(source_payload["hash_matches_expected"]),
      retained_form="ref_and_sha256_only",
      missing_reason="retained TP-21 payload hash evidence is absent or mismatched",
    ),
    _present_missing_item(
      item_id="TP21-CONTROLLED-CRITERIA-VOCABULARY",
      description="controlled debris selection criteria labels",
      present=bool(anchor_set.get("controlled_criteria_keys"))
      and bool(anchor_set.get("controlled_criteria_vocabulary_sha256")),
      retained_form="label_and_sha256_only",
      missing_reason="controlled criteria labels or vocabulary hash are absent",
    ),
    _present_missing_item(
      item_id="TP21-REVIEWER-SELECTED-CASE-LOCATOR",
      description="reviewer-selected TP-21 case locator label",
      present=bool(evidence_state["reviewer_selected_case_locator_present"]),
      retained_form="label_only",
      missing_reason="reviewer-selected case locator label is absent",
    ),
    _present_missing_item(
      item_id="TP21-SELECTED-OUTPUT-PREIMAGE-SHA256",
      description="sha256 of redacted selected-output preimage",
      present=bool(evidence_state["selected_output_preimage_sha256_present"]),
      retained_form="hash_only",
      missing_reason="selected-output preimage sha256 is absent",
    ),
    _present_missing_item(
      item_id="TP21-SELECTED-OUTPUT-HASH-ANCHORS",
      description="hash-only selected-output anchor evidence",
      present=int(evidence_state["selected_debris_output_hash_count"]) > 0,
      retained_form="hash_only",
      missing_reason="selected-output hash anchor set is empty",
    ),
    _present_missing_item(
      item_id="TP21-INDEPENDENT-REVIEWER-SIGNOFF",
      description="independent reviewer signoff for selected case evidence",
      present=bool(evidence_state["independent_reviewer_signoff_present"]),
      retained_form="signoff_ref_only",
      missing_reason="independent reviewer signoff is absent",
    ),
    _present_missing_item(
      item_id="TP21-ALLOWED-OUTPUT-SIGNOFF",
      description="allowed-output signoff for hash-only selected outputs",
      present=bool(evidence_state["allowed_output_signoff_present"])
      and bool(rights_summary["tp21_current_comparison_outputs_admitted"])
      and bool(rights_summary["release_grade_satisfied"]),
      retained_form="signoff_ref_only",
      missing_reason="allowed-output signoff remains fail-closed or not release-grade",
    ),
  ]

def _selection_criteria(anchor_set: dict[str, Any]) -> dict[str, Any]:
  criteria_keys = anchor_set.get("controlled_criteria_keys", [])
  return {
    "criteria_source": "res005_tp21_debris_admission_anchor_set",
    "controlled_criteria_keys": criteria_keys,
    "controlled_criteria_key_count": len(criteria_keys),
    "controlled_criteria_vocabulary_sha256": anchor_set.get(
      "controlled_criteria_vocabulary_sha256", ""
    ),
    "criteria_are_labels_only": True,
    "criteria_are_not_raw_tp21_values": True,
    "criteria_are_not_calibration_authority": True,
  }

def _candidate_locator_policy(evidence_state: dict[str, Any]) -> dict[str, Any]:
  return {
    "locator_status": (
      "present_label_only"
      if evidence_state["reviewer_selected_case_locator_present"]
      else "missing_fail_closed"
    ),
    "candidate_locator_labels_retained": [],
    "allowed_locator_label_keys": [
      "tp21_page_locator_label",
      "tp21_section_or_figure_locator_label",
      "reviewer_case_selection_id",
    ],
    "locator_labels_are_not_source_quotes": True,
    "source_prose_tables_figures_or_raw_values_retained": False,
    "missing_reason": (
      ""
      if evidence_state["reviewer_selected_case_locator_present"]
      else "safe reviewer-selected TP-21 case locator label is absent"
    ),
  }

def _hash_only_preimage_policy(
  *,
  anchor_set: dict[str, Any],
  evidence_state: dict[str, Any],
  rights_summary: dict[str, Any],
) -> dict[str, Any]:
  return {
    "preimage_policy_status": (
      "hash_present_preimage_not_retained"
      if evidence_state["selected_output_preimage_sha256_present"]
      else "missing_hash_fail_closed"
    ),
    "selected_output_preimage_sha256_present": bool(
      evidence_state["selected_output_preimage_sha256_present"]
    ),
    "selected_output_preimage_retained": False,
    "selected_output_raw_values_retained": False,
    "selected_debris_output_hash_count": int(
      evidence_state["selected_debris_output_hash_count"]
    ),
    "selected_debris_output_set_sha256": anchor_set.get(
      "selected_debris_output_set_sha256", ""
    ),
    "hash_allowed_outputs": rights_summary["hash_allowed_outputs"],
    "copy_forbidden_outputs": rights_summary["copy_forbidden_outputs"],
    "consume_forbidden_outputs": rights_summary["consume_forbidden_outputs"],
    "raw_tp21_source_content_retained": False,
    "source_tables_retained": False,
    "source_figures_retained": False,
    "source_numeric_values_retained": False,
    "benchmark_consumed_for_release": False,
  }

def _input_refs(
  *,
  repo_root: Path,
  source_artifact_pack_manifest_path: Path,
  source_manifest: dict[str, Any],
  debris_gate_path: Path,
  debris_gate: dict[str, Any],
  debris_anchor_set_path: Path,
  debris_anchor_set: dict[str, Any],
  source_rights_policy_path: Path,
  source_rights_policy: dict[str, Any],
  selected_case_admission_review_gate_path: Path,
  admission_review_gate: dict[str, Any],
) -> list[dict[str, Any]]:
  return [
    _artifact_ref(
      artifact_id="source_artifact_pack_manifest",
      path=source_artifact_pack_manifest_path,
      repo_root=repo_root,
      role="retained_tp21_payload_manifest_input",
      payload=source_manifest,
    ),
    _artifact_ref(
      artifact_id="res005_tp21_debris_admission_gate",
      path=debris_gate_path,
      repo_root=repo_root,
      role="prior_res005_debris_fail_closed_gate_input",
      payload=debris_gate,
    ),
    _artifact_ref(
      artifact_id="selected_debris_output_anchor_set",
      path=debris_anchor_set_path,
      repo_root=repo_root,
      role="hash_only_selected_output_anchor_input",
      payload=debris_anchor_set,
    ),
    _artifact_ref(
      artifact_id="source_rights_output_policy_gate",
      path=source_rights_policy_path,
      repo_root=repo_root,
      role="source_rights_allowed_output_policy_input",
      payload=source_rights_policy,
    ),
    _artifact_ref(
      artifact_id="res005_tp21_selected_case_admission_review_gate",
      path=selected_case_admission_review_gate_path,
      repo_root=repo_root,
      role="selected_case_review_gate_input",
      payload=admission_review_gate,
    ),
  ]

def generate_selected_case_candidate_packet(
  *,
  repo_root: Path = REPO_ROOT,
  source_artifact_pack_manifest_path: Path = SOURCE_ARTIFACT_PACK_MANIFEST_PATH,
  debris_gate_path: Path = DEBRIS_GATE_PATH,
  debris_anchor_set_path: Path = DEBRIS_ANCHOR_SET_PATH,
  source_rights_policy_path: Path = SOURCE_RIGHTS_POLICY_PATH,
  selected_case_admission_review_gate_path: Path = SELECTED_CASE_ADMISSION_REVIEW_GATE_PATH,
) -> dict[str, Any]:
  source_manifest = _load_json(source_artifact_pack_manifest_path)
  debris_gate = _load_json(debris_gate_path)
  debris_anchor_set = _load_json(debris_anchor_set_path)
  source_rights_policy = _load_json(source_rights_policy_path)
  admission_review_gate = _load_json(selected_case_admission_review_gate_path)

  refs = _input_refs(
    repo_root=repo_root,
    source_artifact_pack_manifest_path=source_artifact_pack_manifest_path,
    source_manifest=source_manifest,
    debris_gate_path=debris_gate_path,
    debris_gate=debris_gate,
    debris_anchor_set_path=debris_anchor_set_path,
    debris_anchor_set=debris_anchor_set,
    source_rights_policy_path=source_rights_policy_path,
    source_rights_policy=source_rights_policy,
    selected_case_admission_review_gate_path=selected_case_admission_review_gate_path,
    admission_review_gate=admission_review_gate,
  )
  source_payload = _source_payload_summary(source_manifest)
  rights = _rights_summary(source_rights_policy)
  evidence_state = _admission_evidence_state(admission_review_gate)
  present_missing = _present_vs_missing(
    source_payload=source_payload,
    anchor_set=debris_anchor_set,
    evidence_state=evidence_state,
    rights_summary=rights,
  )
  missing_items = [row for row in present_missing if not row["present"]]
  safe_candidate_ready = not missing_items
  guards = _authority_guards()

  status = (
    "candidate_ready_non_authoritative_hash_only_selected_case_packet"
    if safe_candidate_ready
    else "blocked_fail_closed_tp21_selected_case_candidate_packet"
  )
  candidate_selection_status = {
    "status": "candidate_ready" if safe_candidate_ready else "blocked",
    "decision": (
      "candidate_packet_ready_non_authoritative"
      if safe_candidate_ready
      else "not_ready_fail_closed"
    ),
    "fail_closed": not safe_candidate_ready,
    "selected_case_candidate_packet_ready": safe_candidate_ready,
    "selected_case_admitted_for_release": False,
    "narrowly_closes_res005": False,
    "residual_status_after_packet": "open_fail_closed_res005",
    "benchmark_consumed_for_release": False,
    "release_grade_validated": False,
    "missing_item_count": len(missing_items),
  }

  packet_core = {
    "input_refs": refs,
    "candidate_selection_status": candidate_selection_status,
    "present_vs_missing": present_missing,
    "selection_criteria": _selection_criteria(debris_anchor_set),
    "candidate_locator_policy": _candidate_locator_policy(evidence_state),
    "hash_only_preimage_policy": _hash_only_preimage_policy(
      anchor_set=debris_anchor_set,
      evidence_state=evidence_state,
      rights_summary=rights,
    ),
    "authority_guards": guards,
  }

  return {
    "schema_version": SCHEMA_VERSION,
    "schema": {
      "name": "res005_tp21_selected_case_candidate_packet",
      "version": "v1",
    },
    "package_id": PACKAGE_ID,
    "package": {
      "package_id": PACKAGE_ID,
      "task_cluster": "TC-A2-BF-003-RES005-TP21",
      "worker_id": "TC-A2-BF-003-RES005-TP21-CANDIDATE-SELECTION",
      "authority_state": "candidate_non_authoritative_fail_closed",
    },
    "residual_id": "RES-005",
    "status": status,
    "input_refs": refs,
    "source_payload_summary": source_payload,
    "source_rights_policy_summary": rights,
    "admission_review_evidence_state": evidence_state,
    "candidate_selection_status": candidate_selection_status,
    "present_vs_missing": present_missing,
    "current_missing_items": [
      {
        "item_id": row["item_id"],
        "missing_reason": row["missing_reason"],
        "retained_form_required": row["retained_form"],
      }
      for row in missing_items
    ],
    "selection_criteria": packet_core["selection_criteria"],
    "candidate_locator_policy": packet_core["candidate_locator_policy"],
    "hash_only_preimage_policy": packet_core["hash_only_preimage_policy"],
    "candidate_evidence_guarantees": {
      "hash_only_ref_only_label_only": True,
      "raw_tp21_source_content_retained": False,
      "raw_tp21_source_content_copied": False,
      "source_payload_body_retained": False,
      "source_tables_retained": False,
      "source_figures_retained": False,
      "source_numeric_values_retained": False,
      "selected_output_preimages_retained": False,
      "selected_output_raw_values_retained": False,
      "benchmark_consumed_for_release": False,
      "release_evidence": False,
    },
    "benchmark_consumed_for_release": False,
    "raw_tp21_source_content_retained": False,
    "selected_output_raw_values_retained": False,
    "selected_output_preimages_retained": False,
    "hash_only_ref_only_label_only": True,
    "authority_guards": guards,
    "non_authoritative_guards": guards,
    "authority_guards_all_false": not any(guards.values()),
    "res005_closure_granted": False,
    "authority_granted_by_this_packet": False,
    "behavior_risks": [
      "candidate locator labels can be mistaken for reviewer-selected source content",
      "controlled criteria labels can be mistaken for raw TP-21 selected output values",
      "hash-only candidate evidence can be mistaken for release evidence",
      "this packet does not grant fragment, component, effect, stock, runtime, Pk, or fuze authority",
    ],
    "integration_notes": [
      "RES-005 remains open and fail-closed until safe locator labels, selected-output preimage sha256, hash anchors, independent review, and allowed-output signoff are present.",
      "This packet is machine-readable candidate evidence only; it is not release evidence.",
      "No TP-21 source prose, tables, figures, raw numeric values, raw selected outputs, stock fields, runtime fields, Pk fields, or fuze authority are retained.",
    ],
    "packet_sha256": _sha256_text(_canonical_json(packet_core)),
  }

def write_retained_artifacts(
  *,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  source_artifact_pack_manifest_path: Path = SOURCE_ARTIFACT_PACK_MANIFEST_PATH,
  debris_gate_path: Path = DEBRIS_GATE_PATH,
  debris_anchor_set_path: Path = DEBRIS_ANCHOR_SET_PATH,
  source_rights_policy_path: Path = SOURCE_RIGHTS_POLICY_PATH,
  selected_case_admission_review_gate_path: Path = SELECTED_CASE_ADMISSION_REVIEW_GATE_PATH,
) -> dict[str, Any]:
  packet = generate_selected_case_candidate_packet(
    repo_root=repo_root,
    source_artifact_pack_manifest_path=source_artifact_pack_manifest_path,
    debris_gate_path=debris_gate_path,
    debris_anchor_set_path=debris_anchor_set_path,
    source_rights_policy_path=source_rights_policy_path,
    selected_case_admission_review_gate_path=selected_case_admission_review_gate_path,
  )
  packet_path = retained_dir / PACKET_FILENAME
  packet_sha256 = write_and_hash_json(packet_path, packet, ensure_ascii=False)

  manifest = {
    "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": packet["status"],
    "artifact_dir": _rel(retained_dir, repo_root),
    "res005_tp21_selected_case_candidate_packet_artifact": {
      "filename": PACKET_FILENAME,
      "relative_path": _rel(packet_path, repo_root),
      "schema_version": packet["schema_version"],
      "sha256": packet_sha256,
    },
    "input_refs": packet["input_refs"],
    "candidate_selection_status": packet["candidate_selection_status"],
    "current_missing_items": packet["current_missing_items"],
    "candidate_evidence_guarantees": packet["candidate_evidence_guarantees"],
    "benchmark_consumed_for_release": False,
    "raw_tp21_source_content_retained": False,
    "selected_output_raw_values_retained": False,
    "hash_only_ref_only_label_only": True,
    "authority_guards_all_false": packet["authority_guards_all_false"],
    "authority_guards": packet["authority_guards"],
  }
  manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
  manifest_sha256 = write_and_hash_json(manifest_path, manifest, ensure_ascii=False)

  packet["retained_artifact_ref"] = _rel(packet_path, repo_root)
  packet["retained_artifact_sha256"] = packet_sha256
  packet["retained_manifest_ref"] = _rel(manifest_path, repo_root)
  packet["retained_manifest_sha256"] = manifest_sha256
  return packet

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the fail-closed A2 RES-005 TP-21 selected-case "
      "candidate packet."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional path for a copy of the generated candidate packet JSON.",
  )
  parser.add_argument(
    "--retained-dir",
    type=Path,
    default=DEFAULT_RETAINED_DIR,
    help="Directory for retained RES-005 TP-21 selected-case candidate artifacts.",
  )
  parser.add_argument(
    "--source-artifact-pack-manifest",
    type=Path,
    default=SOURCE_ARTIFACT_PACK_MANIFEST_PATH,
    help="Existing retained source artifact pack manifest JSON.",
  )
  parser.add_argument(
    "--debris-gate",
    type=Path,
    default=DEBRIS_GATE_PATH,
    help="Existing retained RES-005 TP-21 debris admission gate JSON.",
  )
  parser.add_argument(
    "--debris-anchor-set",
    type=Path,
    default=DEBRIS_ANCHOR_SET_PATH,
    help="Existing retained selected debris output anchor set JSON.",
  )
  parser.add_argument(
    "--source-rights-policy",
    type=Path,
    default=SOURCE_RIGHTS_POLICY_PATH,
    help="Existing source-rights allowed-output policy gate JSON.",
  )
  parser.add_argument(
    "--selected-case-admission-review-gate",
    type=Path,
    default=SELECTED_CASE_ADMISSION_REVIEW_GATE_PATH,
    help="Existing RES-005 TP-21 selected-case admission review gate JSON.",
  )
  args = parser.parse_args(argv)

  packet = write_retained_artifacts(
    retained_dir=args.retained_dir,
    source_artifact_pack_manifest_path=args.source_artifact_pack_manifest,
    debris_gate_path=args.debris_gate,
    debris_anchor_set_path=args.debris_anchor_set,
    source_rights_policy_path=args.source_rights_policy,
    selected_case_admission_review_gate_path=args.selected_case_admission_review_gate,
  )
  if args.output:
    _write_json(args.output, packet)
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
