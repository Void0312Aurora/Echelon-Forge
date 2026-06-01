#!/usr/bin/env python3
"""Generate the RES-005 TP-21 selected-case admission review packet.

This packet is deliberately fail-closed. It records only refs, hashes, labels,
review/signoff requirements, and missing owner inputs. It does not retain TP-21
source prose, tables, figures, raw numeric values, or raw selected outputs, and
it grants no fragment/component/effect/stock/runtime/Pk/fuze authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_mechanism_comparison_hashes as comparison_hashes,
)


PACKAGE_ID = comparison_hashes.PACKAGE_ID
SCHEMA_VERSION = "a2.res005_tp21_selected_case_admission_review_gate.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
    "a2.res005_tp21_selected_case_admission_review_retained_manifest.v1"
)

PACKAGE_DIR = comparison_hashes.PACKAGE_DIR
A2_TASK_DIR = PACKAGE_DIR.parent.parent
DEBRIS_ADMISSION_DIR = (
    PACKAGE_DIR / "retained_artifacts" / "res005_tp21_debris_admission_20260531"
)
SOURCE_RIGHTS_POLICY_DIR = (
    PACKAGE_DIR / "retained_artifacts" / "source_rights_output_policy_20260531"
)
DEFAULT_RETAINED_DIR = (
    PACKAGE_DIR
    / "retained_artifacts"
    / "res005_tp21_selected_case_admission_20260601"
)

DEBRIS_GATE_PATH = DEBRIS_ADMISSION_DIR / "res005_tp21_debris_admission_gate.json"
DEBRIS_ANCHOR_SET_PATH = DEBRIS_ADMISSION_DIR / "selected_debris_output_anchor_set.json"
SOURCE_RIGHTS_POLICY_PATH = (
    SOURCE_RIGHTS_POLICY_DIR / "source_rights_output_policy_gate.json"
)
RESIDUAL_REGISTER_PATH = PACKAGE_DIR / "residual_register.zh.md"
MECHANISM_BACKLOG_PATH = A2_TASK_DIR / "mechanism_admission_failclosed_backlog_20260601.zh.md"
CANDIDATE_ACCEPTANCE_STATUS_PATH = A2_TASK_DIR / "candidate_acceptance_status.zh.md"
TASK_CLUSTER_STATUS_PATH = A2_TASK_DIR / "task_cluster_execution_status_20260601.zh.md"
VALIDATION_NOTE_PATH = (
    PACKAGE_DIR / "validation_res005_tp21_debris_admission_gate_20260531.zh.md"
)

GATE_FILENAME = "res005_tp21_selected_case_admission_review_gate.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


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
    row: dict[str, Any] = {
        "artifact_id": artifact_id,
        "role": role,
        "relative_path": _rel(path, repo_root),
        "sha256": _sha256_file(path),
    }
    if payload is not None:
        row["schema_version"] = payload.get("schema_version", "")
        row["status"] = payload.get("status", "")
    return row


def _authority_guards() -> dict[str, bool]:
    return {
        "fragment_mechanism_authority_granted": False,
        "blast_mechanism_authority_granted": False,
        "component_failure_probability_authority_granted": False,
        "effect_scale_authority_granted": False,
        "stock_descriptor_created": False,
        "stock_database_authority_granted": False,
        "runtime_authority_granted": False,
        "pk_authority_granted": False,
        "deterministic_fuze_authority_granted": False,
        "benchmark_consumption_authority_granted": False,
    }


def _tp21_rights_row(source_rights_policy: dict[str, Any]) -> dict[str, Any]:
    for row in source_rights_policy.get("payload_rights_inventory", []):
        if row.get("residual_id") == "RES-005":
            return row
    for row in source_rights_policy.get("payload_rights_inventory", []):
        if row.get("source_id") == "VPS-BFM-015":
            return row
    for row in source_rights_policy.get("payload_rights_inventory", []):
        if row.get("source_artifact_label") == "TP-21 PDF":
            return row
    return {}


def _source_rights_summary(source_rights_policy: dict[str, Any]) -> dict[str, Any]:
    policy = source_rights_policy.get("allowed_output_policy", {})
    tp21_row = _tp21_rights_row(source_rights_policy)
    row_policy = tp21_row.get("output_policy", {})
    current_selected_hashes = policy.get("current_selected_comparison_output_hashes", [])
    current_outputs_admitted = bool(
        row_policy.get("current_comparison_outputs_admitted")
    ) and bool(policy.get("release_grade_satisfied"))
    return {
        "schema_version": source_rights_policy.get("schema_version", ""),
        "status": source_rights_policy.get("status", ""),
        "policy_status": policy.get("policy_status", ""),
        "release_grade_satisfied": bool(policy.get("release_grade_satisfied")),
        "current_selected_comparison_output_hash_count": len(current_selected_hashes),
        "current_comparison_outputs_admitted": current_outputs_admitted,
        "tp21_payload_ref": {
            "source_id": tp21_row.get("source_id", "VPS-BFM-015"),
            "source_artifact_label": tp21_row.get("source_artifact_label", "TP-21 PDF"),
            "relative_path": tp21_row.get("relative_path", ""),
            "payload_sha256": tp21_row.get("actual_sha256", ""),
            "rights_status": tp21_row.get("rights_status", ""),
            "benchmark_consumed_for_release": bool(
                tp21_row.get("benchmark_consumed_for_release")
            ),
            "release_consumption_allowed": bool(
                tp21_row.get("release_consumption_allowed")
            ),
        },
        "allowed_hash_outputs": policy.get("allowed_hash_outputs", []),
        "forbidden_copy_outputs": policy.get("forbidden_copy_outputs", []),
        "forbidden_consume_outputs": policy.get("forbidden_consume_outputs", []),
    }


def _prior_gate_summary(
    debris_gate: dict[str, Any],
    anchor_set: dict[str, Any],
) -> dict[str, Any]:
    decision = debris_gate.get("admission_decision", {})
    reviewer_case = debris_gate.get("reviewer_selected_case_artifact", {})
    return {
        "debris_gate_schema_version": debris_gate.get("schema_version", ""),
        "debris_gate_status": debris_gate.get("status", ""),
        "debris_gate_decision": decision.get("decision", ""),
        "narrowly_closes_res005": bool(decision.get("narrowly_closes_res005")),
        "closed_residual_ids_by_prior_gate": decision.get(
            "closed_residual_ids_by_this_gate", []
        ),
        "anchor_set_schema_version": anchor_set.get("schema_version", ""),
        "anchor_set_status": anchor_set.get("anchor_set_status", ""),
        "controlled_criteria_keys": anchor_set.get("controlled_criteria_keys", []),
        "controlled_criteria_vocabulary_sha256": anchor_set.get(
            "controlled_criteria_vocabulary_sha256", ""
        ),
        "selected_debris_output_hash_count": int(
            anchor_set.get("selected_debris_output_hash_count", 0)
        ),
        "selected_debris_output_set_sha256": anchor_set.get(
            "selected_debris_output_set_sha256", ""
        ),
        "current_comparison_outputs_admitted": bool(
            anchor_set.get("current_comparison_outputs_admitted")
        ),
        "reviewer_case_status": reviewer_case.get("artifact_status", ""),
        "reviewer_case_locator_present": bool(
            reviewer_case.get("page_section_provenance_labels_present")
        ),
        "selected_output_preimage_hash_present": bool(
            reviewer_case.get("selected_output_preimage_hash_present")
        ),
        "selected_output_hashes_present": bool(
            reviewer_case.get("selected_output_hashes_present")
        ),
        "independent_reviewer_signoff_present": bool(
            reviewer_case.get("reviewer_signoff_present")
        ),
        "allowed_output_signoff_present": bool(
            reviewer_case.get("allowed_output_signoff_present")
        ),
    }


def _required_item(
    *,
    item_id: str,
    owner: str,
    required_evidence: str,
    present: bool,
    missing_reason: str,
    retained_form: str = "hash_ref_or_label_only",
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "owner": owner,
        "required_evidence": required_evidence,
        "retained_form": retained_form,
        "present": present,
        "current_status": "present" if present else "missing_fail_closed",
        "missing_reason": "" if present else missing_reason,
    }


def _required_reviewer_items(
    *,
    prior_summary: dict[str, Any],
    rights_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    selected_hash_count = prior_summary["selected_debris_output_hash_count"]
    return [
        _required_item(
            item_id="TP21-SELECTED-CASE-LOCATOR",
            owner="mechanism_admission_owner",
            required_evidence=(
                "stable reviewer-selected TP-21 case locator label without "
                "retaining source prose, tables, figures, or raw values"
            ),
            present=bool(prior_summary["reviewer_case_locator_present"]),
            missing_reason="reviewer-selected case locator label is absent",
            retained_form="label_only",
        ),
        _required_item(
            item_id="TP21-SELECTED-OUTPUT-PREIMAGE-SHA256",
            owner="mechanism_admission_owner",
            required_evidence=(
                "sha256 of a redacted selected-case output preimage; the "
                "preimage itself must not be retained in this packet"
            ),
            present=bool(prior_summary["selected_output_preimage_hash_present"]),
            missing_reason="selected output preimage sha256 is absent",
        ),
        _required_item(
            item_id="TP21-SELECTED-DEBRIS-OUTPUT-ANCHOR-SET",
            owner="mechanism_admission_owner",
            required_evidence="hash-only selected debris output anchor set for the selected case",
            present=selected_hash_count > 0 and bool(
                prior_summary["selected_output_hashes_present"]
            ),
            missing_reason="selected debris output hash anchor set is empty",
        ),
        _required_item(
            item_id="TP21-INDEPENDENT-REVIEWER-SIGNOFF",
            owner="independent_mechanism_reviewer",
            required_evidence=(
                "independent reviewer signoff id for the selected case, "
                "locator label, and preimage hash"
            ),
            present=bool(prior_summary["independent_reviewer_signoff_present"]),
            missing_reason="independent reviewer signoff is absent",
            retained_form="signoff_ref_only",
        ),
        _required_item(
            item_id="TP21-ALLOWED-OUTPUT-SIGNOFF",
            owner="source_rights_reviewer",
            required_evidence=(
                "allowed-output signoff that admits only hash outputs for the "
                "reviewer-selected case"
            ),
            present=bool(rights_summary["current_comparison_outputs_admitted"])
            and bool(prior_summary["allowed_output_signoff_present"]),
            missing_reason=(
                "source-rights policy remains fail-closed for current selected "
                "comparison outputs"
            ),
            retained_form="signoff_ref_only",
        ),
        _required_item(
            item_id="TP21-AUTHORITY-BOUNDARY-SIGNOFF",
            owner="integration_owner",
            required_evidence=(
                "reviewer confirmation that fragment/component/effect/stock/"
                "runtime/Pk/fuze authority remains false"
            ),
            present=False,
            missing_reason="authority-boundary signoff is absent",
            retained_form="signoff_ref_only",
        ),
    ]


def _current_missing_items(
    required_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "item_id": row["item_id"],
            "owner": row["owner"],
            "missing_reason": row["missing_reason"],
            "next_owner_input": row["required_evidence"],
        }
        for row in required_items
        if not row["present"]
    ]


def _input_refs(
    *,
    repo_root: Path,
    debris_gate_path: Path,
    debris_gate: dict[str, Any],
    debris_anchor_set_path: Path,
    debris_anchor_set: dict[str, Any],
    source_rights_policy_path: Path,
    source_rights_policy: dict[str, Any],
    residual_register_path: Path,
    mechanism_backlog_path: Path,
    candidate_acceptance_status_path: Path,
    task_cluster_status_path: Path,
    validation_note_path: Path,
) -> list[dict[str, Any]]:
    return [
        _artifact_ref(
            artifact_id="res005_prior_debris_admission_gate",
            path=debris_gate_path,
            repo_root=repo_root,
            role="prior_fail_closed_res005_gate_input",
            payload=debris_gate,
        ),
        _artifact_ref(
            artifact_id="res005_selected_debris_output_anchor_set",
            path=debris_anchor_set_path,
            repo_root=repo_root,
            role="prior_hash_only_empty_anchor_set_input",
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
            artifact_id="residual_register",
            path=residual_register_path,
            repo_root=repo_root,
            role="res005_residual_status_ref",
        ),
        _artifact_ref(
            artifact_id="mechanism_admission_failclosed_backlog",
            path=mechanism_backlog_path,
            repo_root=repo_root,
            role="tc_a2_bf_003_res005_backlog_ref",
        ),
        _artifact_ref(
            artifact_id="candidate_acceptance_status",
            path=candidate_acceptance_status_path,
            repo_root=repo_root,
            role="g2_candidate_acceptance_boundary_ref",
        ),
        _artifact_ref(
            artifact_id="task_cluster_execution_status",
            path=task_cluster_status_path,
            repo_root=repo_root,
            role="task_cluster_boundary_ref",
        ),
        _artifact_ref(
            artifact_id="validation_res005_tp21_debris_admission_note",
            path=validation_note_path,
            repo_root=repo_root,
            role="prior_validation_note_ref",
        ),
    ]


def generate_selected_case_admission_gate(
    *,
    repo_root: Path = REPO_ROOT,
    debris_gate_path: Path = DEBRIS_GATE_PATH,
    debris_anchor_set_path: Path = DEBRIS_ANCHOR_SET_PATH,
    source_rights_policy_path: Path = SOURCE_RIGHTS_POLICY_PATH,
    residual_register_path: Path = RESIDUAL_REGISTER_PATH,
    mechanism_backlog_path: Path = MECHANISM_BACKLOG_PATH,
    candidate_acceptance_status_path: Path = CANDIDATE_ACCEPTANCE_STATUS_PATH,
    task_cluster_status_path: Path = TASK_CLUSTER_STATUS_PATH,
    validation_note_path: Path = VALIDATION_NOTE_PATH,
) -> dict[str, Any]:
    debris_gate = _load_json(debris_gate_path)
    debris_anchor_set = _load_json(debris_anchor_set_path)
    source_rights_policy = _load_json(source_rights_policy_path)

    refs = _input_refs(
        repo_root=repo_root,
        debris_gate_path=debris_gate_path,
        debris_gate=debris_gate,
        debris_anchor_set_path=debris_anchor_set_path,
        debris_anchor_set=debris_anchor_set,
        source_rights_policy_path=source_rights_policy_path,
        source_rights_policy=source_rights_policy,
        residual_register_path=residual_register_path,
        mechanism_backlog_path=mechanism_backlog_path,
        candidate_acceptance_status_path=candidate_acceptance_status_path,
        task_cluster_status_path=task_cluster_status_path,
        validation_note_path=validation_note_path,
    )
    prior_summary = _prior_gate_summary(debris_gate, debris_anchor_set)
    rights_summary = _source_rights_summary(source_rights_policy)
    required_items = _required_reviewer_items(
        prior_summary=prior_summary,
        rights_summary=rights_summary,
    )
    missing_items = _current_missing_items(required_items)
    selected_case_admitted = not missing_items
    guards = _authority_guards()
    status = (
        "admitted_non_authoritative_selected_case_review_packet"
        if selected_case_admitted
        else "blocked_fail_closed_tp21_selected_case_admission_review_packet"
    )
    decision = {
        "status": "admitted" if selected_case_admitted else "blocked",
        "decision": (
            "selected_case_admitted_non_authoritative"
            if selected_case_admitted
            else "not_admitted_fail_closed"
        ),
        "fail_closed": not selected_case_admitted,
        "selected_tp21_case_admitted": selected_case_admitted,
        "narrowly_closes_res005": False,
        "closed_residual_ids_by_this_gate": [],
        "closed_residual_subscopes_by_this_gate": [],
        "residual_status_after_gate": (
            "open_fail_closed_tp21_selected_debris_outputs_missing"
        ),
        "benchmark_consumed_for_release": False,
        "release_grade_validated": False,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "schema": {
            "name": "res005_tp21_selected_case_admission_review_gate",
            "version": "v1",
        },
        "package_id": PACKAGE_ID,
        "package": {
            "package_id": PACKAGE_ID,
            "task_cluster": "TC-A2-BF-003-RES005-TP21",
            "acceptance_layer": "G2 candidate acceptance",
            "residual_layer": "G3 residual read-only",
            "authority_state": "candidate_non_authoritative_fail_closed",
        },
        "residual_id": "RES-005",
        "residual": {
            "residual_id": "RES-005",
            "review_target": "tp21_reviewer_selected_case_admission",
            "status_before_gate": "open_fail_closed_tp21_selected_debris_outputs_missing",
            "status_after_gate": decision["residual_status_after_gate"],
            "closed_by_this_gate": False,
            "residual_closed": False,
        },
        "status": status,
        "input_refs": refs,
        "prior_debris_gate_summary": prior_summary,
        "source_rights_policy_summary": rights_summary,
        "required_reviewer_signoff_items": required_items,
        "current_missing_items": missing_items,
        "selected_case_evidence_state": {
            "reviewer_selected_case_locator_present": prior_summary[
                "reviewer_case_locator_present"
            ],
            "selected_output_preimage_sha256_present": prior_summary[
                "selected_output_preimage_hash_present"
            ],
            "selected_debris_output_hash_count": prior_summary[
                "selected_debris_output_hash_count"
            ],
            "selected_debris_output_hashes_retained": False,
            "raw_selected_outputs_retained": False,
            "raw_tp21_source_content_retained": False,
            "source_tables_retained": False,
            "source_figures_retained": False,
            "source_numeric_values_retained": False,
            "independent_reviewer_signoff_present": prior_summary[
                "independent_reviewer_signoff_present"
            ],
            "allowed_output_signoff_present": required_items[4]["present"],
        },
        "decision": decision,
        "admission_decision": decision,
        "benchmark_consumed_for_release": False,
        "raw_tp21_source_content_retained": False,
        "raw_selected_outputs_retained": False,
        "hash_only_ref_only_label_only": True,
        "source_payload_body_retained": False,
        "source_tables_retained": False,
        "source_figures_retained": False,
        "source_numeric_values_retained": False,
        "authority_guards": guards,
        "non_authoritative_guards": guards,
        "authority_guards_all_false": not any(guards.values()),
        "owner_inputs_required_next": [
            "mechanism admission owner supplies reviewer-selected case locator label and selected-output preimage sha256",
            "independent mechanism reviewer signs off selected case, locator label, and preimage hash",
            "source-rights reviewer signs off hash-only allowed-output admission for the selected case",
            "integration owner reruns this gate and updates residual register only if a later gate explicitly closes RES-005",
        ],
        "behavior_risks": [
            "controlled criteria keys can be mistaken for a concrete reviewer-selected TP-21 case",
            "empty selected-output anchors can be mistaken for admitted evidence",
            "source-rights candidate policy can be mistaken for release-grade allowed-output signoff",
            "this review packet does not grant fragment, component, effect, stock, runtime, Pk, or fuze authority",
        ],
        "integration_notes": [
            "RES-005 remains open and fail-closed because reviewer locator, preimage hash, independent signoff, and allowed-output signoff are missing.",
            "This packet retains only refs, sha256 hashes, labels, missing-item rows, and authority guards.",
            "No TP-21 source content, raw selected outputs, or release benchmark consumption is retained by this gate.",
        ],
        "packet_sha256": _sha256_text(
            _canonical_json(
                {
                    "input_refs": refs,
                    "required_reviewer_signoff_items": required_items,
                    "current_missing_items": missing_items,
                    "decision": decision,
                    "authority_guards": guards,
                }
            )
        ),
    }


def write_retained_artifacts(
    *,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    repo_root: Path = REPO_ROOT,
    debris_gate_path: Path = DEBRIS_GATE_PATH,
    debris_anchor_set_path: Path = DEBRIS_ANCHOR_SET_PATH,
    source_rights_policy_path: Path = SOURCE_RIGHTS_POLICY_PATH,
    residual_register_path: Path = RESIDUAL_REGISTER_PATH,
    mechanism_backlog_path: Path = MECHANISM_BACKLOG_PATH,
    candidate_acceptance_status_path: Path = CANDIDATE_ACCEPTANCE_STATUS_PATH,
    task_cluster_status_path: Path = TASK_CLUSTER_STATUS_PATH,
    validation_note_path: Path = VALIDATION_NOTE_PATH,
) -> dict[str, Any]:
    artifact = generate_selected_case_admission_gate(
        repo_root=repo_root,
        debris_gate_path=debris_gate_path,
        debris_anchor_set_path=debris_anchor_set_path,
        source_rights_policy_path=source_rights_policy_path,
        residual_register_path=residual_register_path,
        mechanism_backlog_path=mechanism_backlog_path,
        candidate_acceptance_status_path=candidate_acceptance_status_path,
        task_cluster_status_path=task_cluster_status_path,
        validation_note_path=validation_note_path,
    )
    retained_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = retained_dir / GATE_FILENAME
    _write_json(artifact_path, artifact)
    artifact_sha256 = _sha256_file(artifact_path)

    manifest = {
        "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
        "package_id": PACKAGE_ID,
        "status": artifact["status"],
        "artifact_dir": _rel(retained_dir, repo_root),
        "res005_tp21_selected_case_admission_review_gate_artifact": {
            "filename": GATE_FILENAME,
            "relative_path": _rel(artifact_path, repo_root),
            "schema_version": artifact["schema_version"],
            "sha256": artifact_sha256,
        },
        "input_refs": artifact["input_refs"],
        "decision": artifact["decision"],
        "current_missing_items": artifact["current_missing_items"],
        "benchmark_consumed_for_release": False,
        "raw_tp21_source_content_retained": False,
        "raw_selected_outputs_retained": False,
        "hash_only_ref_only_label_only": True,
        "authority_guards_all_false": artifact["authority_guards_all_false"],
        "authority_guards": artifact["authority_guards"],
    }
    manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
    _write_json(manifest_path, manifest)

    artifact["retained_artifact_ref"] = _rel(artifact_path, repo_root)
    artifact["retained_artifact_sha256"] = artifact_sha256
    artifact["retained_manifest_ref"] = _rel(manifest_path, repo_root)
    artifact["retained_manifest_sha256"] = _sha256_file(manifest_path)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the fail-closed A2 RES-005 TP-21 selected-case admission "
            "review packet."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated gate JSON.",
    )
    parser.add_argument(
        "--retained-dir",
        type=Path,
        default=DEFAULT_RETAINED_DIR,
        help="Directory for retained RES-005 TP-21 selected-case admission artifacts.",
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
    args = parser.parse_args()

    artifact = write_retained_artifacts(
        retained_dir=args.retained_dir,
        debris_gate_path=args.debris_gate,
        debris_anchor_set_path=args.debris_anchor_set,
        source_rights_policy_path=args.source_rights_policy,
    )
    if args.output:
        _write_json(args.output, artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
