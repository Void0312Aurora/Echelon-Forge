#!/usr/bin/env python3
"""Generate the RES-006 BEC-O lineage/tolerance review candidate packet.

This packet is deliberately narrower than admission: it reads retained JSON
evidence only, summarizes cached-vs-recalculated topology without copying row
hash tables, and fails closed until independent lineage, allowed-output,
numeric tolerance, and replacement-anchor signoffs exist.
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
SCHEMA_VERSION = "a2.res006_beco_lineage_tolerance_review_candidate_packet.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
    "a2.res006_beco_lineage_tolerance_review_retained_manifest.v1"
)

PACKAGE_DIR = comparison_hashes.PACKAGE_DIR
RETAINED_ROOT = PACKAGE_DIR / "retained_artifacts"
RES006_RECALCULATION_DIR = (
    RETAINED_ROOT / "res006_beco_recalculation_admission_20260531"
)
MECHANISM_COMPARISON_HASHES_DIR = comparison_hashes.DEFAULT_RETAINED_DIR
SOURCE_RIGHTS_OUTPUT_POLICY_DIR = (
    RETAINED_ROOT / "source_rights_output_policy_20260531"
)
RES006_REPLACEMENT_TOLERANCE_DIR = (
    RETAINED_ROOT / "res006_beco_replacement_tolerance_admission_20260601"
)
DEFAULT_RETAINED_DIR = (
    RETAINED_ROOT / "res006_beco_lineage_tolerance_review_20260601"
)

RES006_RECALCULATION_GATE_FILENAME = "res006_beco_recalculation_admission_gate.json"
BECO_RECALCULATED_ANCHOR_SET_FILENAME = "beco_recalculated_hash_anchor_set.json"
MECHANISM_COMPARISON_HASHES_FILENAME = (
    comparison_hashes.MECHANISM_COMPARISON_HASHES_FILENAME
)
SOURCE_RIGHTS_OUTPUT_POLICY_GATE_FILENAME = "source_rights_output_policy_gate.json"
RES006_REPLACEMENT_TOLERANCE_GATE_FILENAME = (
    "res006_beco_replacement_tolerance_admission_gate.json"
)
PACKET_FILENAME = "res006_beco_lineage_tolerance_review_candidate_packet.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

DEFAULT_RES006_RECALCULATION_GATE = (
    RES006_RECALCULATION_DIR / RES006_RECALCULATION_GATE_FILENAME
)
DEFAULT_BECO_RECALCULATED_ANCHOR_SET = (
    RES006_RECALCULATION_DIR / BECO_RECALCULATED_ANCHOR_SET_FILENAME
)
DEFAULT_MECHANISM_COMPARISON_HASHES = (
    MECHANISM_COMPARISON_HASHES_DIR / MECHANISM_COMPARISON_HASHES_FILENAME
)
DEFAULT_SOURCE_RIGHTS_OUTPUT_POLICY_GATE = (
    SOURCE_RIGHTS_OUTPUT_POLICY_DIR / SOURCE_RIGHTS_OUTPUT_POLICY_GATE_FILENAME
)
DEFAULT_RES006_REPLACEMENT_TOLERANCE_GATE = (
    RES006_REPLACEMENT_TOLERANCE_DIR / RES006_REPLACEMENT_TOLERANCE_GATE_FILENAME
)

SIGNOFF_IDS = [
    "independent_lineage_review_signoff",
    "allowed_output_policy_signoff",
    "numeric_tolerance_policy_signoff",
    "replacement_anchor_signoff",
]


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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _input_ref(
    *,
    artifact_key: str,
    path: Path,
    repo_root: Path,
    role: str,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "artifact_key": artifact_key,
        "role": role,
        "relative_path": _rel(path, repo_root),
        "present": path.is_file(),
    }
    if not path.is_file():
        ref["status"] = "missing_fail_closed"
        return ref

    ref["sha256"] = _sha256_file(path)
    payload = _load_json(path)
    if payload is None:
        ref["status"] = "json_parse_failed_fail_closed"
        return ref

    ref["schema_version"] = payload.get("schema_version", "")
    ref["status"] = payload.get("status", "")
    return ref


def _authority_guards() -> dict[str, bool]:
    return {
        "stock_descriptor_created": False,
        "stock_database_authority_granted": False,
        "runtime_authority_granted": False,
        "blast_mechanism_authority_granted": False,
        "fragment_mechanism_authority_granted": False,
        "effect_scale_authority_granted": False,
        "component_authority_granted": False,
        "component_failure_probability_authority_granted": False,
        "pk_authority_granted": False,
        "fuze_authority_granted": False,
        "deterministic_fuze_authority_granted": False,
        "replacement_anchor_authority_granted": False,
        "cached_anchor_replacement_authority_granted": False,
        "benchmark_consumption_authority_granted": False,
    }


def _rows_by_id(
    rows: list[dict[str, Any]],
    *,
    hash_field: str,
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        comparison_id = row.get("comparison_id")
        if not comparison_id:
            continue
        if row.get(hash_field):
            indexed[str(comparison_id)] = row
    return indexed


def _cached_rows(
    mechanism_comparison_hashes: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if mechanism_comparison_hashes is None:
        return {}
    beco = mechanism_comparison_hashes.get("beco_workbook", {})
    rows = beco.get("selected_comparison_hashes", [])
    if not isinstance(rows, list):
        return {}
    return _rows_by_id(
        [row for row in rows if isinstance(row, dict)],
        hash_field="comparison_output_sha256",
    )


def _recalculated_rows(
    beco_recalculated_anchor_set: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if beco_recalculated_anchor_set is None:
        return {}
    rows = beco_recalculated_anchor_set.get("selected_recalculated_hashes", [])
    if not isinstance(rows, list):
        return {}
    return _rows_by_id(
        [row for row in rows if isinstance(row, dict)],
        hash_field="recalculated_output_sha256",
    )


def _add_ordered(target: list[str], values: list[Any]) -> None:
    for value in values:
        if not isinstance(value, str) or not value:
            continue
        if value not in target:
            target.append(value)


def _comparison_ids_from_prior_summaries(
    *,
    res006_recalculation_gate: dict[str, Any] | None,
    replacement_tolerance_gate: dict[str, Any] | None,
) -> list[str]:
    ids: list[str] = []
    summaries: list[dict[str, Any]] = []
    if res006_recalculation_gate is not None:
        lineage = res006_recalculation_gate.get("mismatch_lineage", {})
        if isinstance(lineage, dict):
            summaries.append(lineage)
    if replacement_tolerance_gate is not None:
        mismatch = replacement_tolerance_gate.get(
            "cached_vs_recalculated_mismatch_summary", {}
        )
        if isinstance(mismatch, dict):
            summaries.append(mismatch)

    for summary in summaries:
        for key in (
            "matching_comparison_ids",
            "mismatch_comparison_ids",
            "missing_cached_comparison_ids",
            "missing_recalculated_comparison_ids",
        ):
            values = summary.get(key, [])
            if isinstance(values, list):
                _add_ordered(ids, values)

    return ids


def _ordered_comparison_ids(
    *,
    cached_by_id: dict[str, dict[str, Any]],
    recalculated_by_id: dict[str, dict[str, Any]],
    res006_recalculation_gate: dict[str, Any] | None,
    replacement_tolerance_gate: dict[str, Any] | None,
) -> list[str]:
    ids = _comparison_ids_from_prior_summaries(
        res006_recalculation_gate=res006_recalculation_gate,
        replacement_tolerance_gate=replacement_tolerance_gate,
    )

    if cached_by_id or recalculated_by_id or ids:
        _add_ordered(
            ids,
            [
                str(row["comparison_id"])
                for row in comparison_hashes.BECO_SELECTED_OUTPUTS
                if row.get("comparison_id")
            ],
        )
    _add_ordered(ids, list(cached_by_id))
    _add_ordered(ids, list(recalculated_by_id))
    return ids


def _anchor_source_summary(
    *,
    mechanism_comparison_hashes: dict[str, Any] | None,
    beco_recalculated_anchor_set: dict[str, Any] | None,
    refs_by_key: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cached_by_id = _cached_rows(mechanism_comparison_hashes)
    recalculated_by_id = _recalculated_rows(beco_recalculated_anchor_set)
    beco = (
        mechanism_comparison_hashes.get("beco_workbook", {})
        if mechanism_comparison_hashes is not None
        else {}
    )

    return {
        "cached_anchor_source": {
            "source_ref_key": "mechanism_comparison_hashes",
            "present": mechanism_comparison_hashes is not None,
            "input_artifact_sha256": refs_by_key["mechanism_comparison_hashes"].get(
                "sha256", ""
            ),
            "source_status": refs_by_key["mechanism_comparison_hashes"].get(
                "status", "missing_fail_closed"
            ),
            "anchor_role": "cached_workbook_selected_output_hash_anchors",
            "selected_output_hash_count": len(cached_by_id),
            "selected_output_set_sha256": beco.get(
                "selected_comparison_output_set_sha256", ""
            ),
            "comparison_ids": list(cached_by_id),
            "individual_anchor_hashes_retained_in_this_packet": False,
            "anchor_rows_retained_in_this_packet": False,
            "raw_selected_values_retained": False,
            "formula_text_retained": False,
        },
        "recalculated_anchor_source": {
            "source_ref_key": "beco_recalculated_hash_anchor_set",
            "present": beco_recalculated_anchor_set is not None,
            "input_artifact_sha256": refs_by_key[
                "beco_recalculated_hash_anchor_set"
            ].get("sha256", ""),
            "source_status": refs_by_key[
                "beco_recalculated_hash_anchor_set"
            ].get("status", "missing_fail_closed"),
            "anchor_role": "headless_recalculated_selected_output_hash_anchors",
            "selected_output_hash_count": len(recalculated_by_id),
            "expected_selected_hash_count": int(
                beco_recalculated_anchor_set.get("expected_selected_hash_count", 0)
                if beco_recalculated_anchor_set is not None
                else 0
            ),
            "selected_output_set_sha256": (
                beco_recalculated_anchor_set.get(
                    "selected_recalculated_output_set_sha256", ""
                )
                if beco_recalculated_anchor_set is not None
                else ""
            ),
            "comparison_ids": list(recalculated_by_id),
            "individual_anchor_hashes_retained_in_this_packet": False,
            "anchor_rows_retained_in_this_packet": False,
            "raw_selected_values_retained": False,
            "formula_text_retained": False,
            "stdout_retained": False,
            "stderr_retained": False,
            "temporary_workbook_copy_retained": False,
        },
    }


def _cached_vs_recalculated_summary(
    *,
    res006_recalculation_gate: dict[str, Any] | None,
    mechanism_comparison_hashes: dict[str, Any] | None,
    beco_recalculated_anchor_set: dict[str, Any] | None,
    replacement_tolerance_gate: dict[str, Any] | None,
) -> dict[str, Any]:
    cached_by_id = _cached_rows(mechanism_comparison_hashes)
    recalculated_by_id = _recalculated_rows(beco_recalculated_anchor_set)
    comparison_ids = _ordered_comparison_ids(
        cached_by_id=cached_by_id,
        recalculated_by_id=recalculated_by_id,
        res006_recalculation_gate=res006_recalculation_gate,
        replacement_tolerance_gate=replacement_tolerance_gate,
    )

    matching_ids: list[str] = []
    mismatch_ids: list[str] = []
    missing_cached_ids: list[str] = []
    missing_recalculated_ids: list[str] = []

    for comparison_id in comparison_ids:
        cached_hash = cached_by_id.get(comparison_id, {}).get(
            "comparison_output_sha256", ""
        )
        recalculated_hash = recalculated_by_id.get(comparison_id, {}).get(
            "recalculated_output_sha256", ""
        )
        if not cached_hash:
            missing_cached_ids.append(comparison_id)
        if not recalculated_hash:
            missing_recalculated_ids.append(comparison_id)
        if cached_hash and recalculated_hash and cached_hash == recalculated_hash:
            matching_ids.append(comparison_id)
        elif cached_hash and recalculated_hash:
            mismatch_ids.append(comparison_id)

    exact_hash_check_passed = bool(
        comparison_ids
        and not mismatch_ids
        and not missing_cached_ids
        and not missing_recalculated_ids
    )
    status = (
        "cached_and_recalculated_hash_ids_match_review_still_required"
        if exact_hash_check_passed
        else "cached_vs_recalculated_hash_mismatch_fail_closed"
    )
    if not comparison_ids:
        status = "cached_vs_recalculated_comparison_inputs_missing_fail_closed"

    if mismatch_ids and not matching_ids and not missing_cached_ids and not missing_recalculated_ids:
        topology = "zero_match_all_selected_comparison_ids_mismatched"
    elif exact_hash_check_passed:
        topology = "all_selected_comparison_ids_exact_hash_matched"
    else:
        topology = "mixed_or_incomplete_selected_comparison_id_topology"

    return {
        "status": status,
        "topology": topology,
        "counts_and_comparison_ids_only": True,
        "comparison_id_count": len(comparison_ids),
        "cached_anchor_count": len(cached_by_id),
        "recalculated_anchor_count": len(recalculated_by_id),
        "matching_count": len(matching_ids),
        "mismatch_count": len(mismatch_ids),
        "missing_cached_count": len(missing_cached_ids),
        "missing_recalculated_count": len(missing_recalculated_ids),
        "matching_comparison_ids": matching_ids,
        "mismatch_comparison_ids": mismatch_ids,
        "missing_cached_comparison_ids": missing_cached_ids,
        "missing_recalculated_comparison_ids": missing_recalculated_ids,
        "exact_hash_check_passed": exact_hash_check_passed,
        "individual_row_hashes_retained_in_this_packet": False,
        "raw_selected_values_retained": False,
        "formula_text_retained": False,
        "raw_output_tables_retained": False,
        "temporary_workbook_copy_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
    }


def _source_rights_summary(
    *,
    source_rights_output_policy_gate: dict[str, Any] | None,
    replacement_tolerance_gate: dict[str, Any] | None,
) -> dict[str, Any]:
    policy = (
        source_rights_output_policy_gate.get("allowed_output_policy", {})
        if source_rights_output_policy_gate is not None
        else {}
    )
    prior_summary = (
        replacement_tolerance_gate.get("source_rights_output_policy_summary", {})
        if replacement_tolerance_gate is not None
        else {}
    )

    return {
        "present": source_rights_output_policy_gate is not None,
        "policy_status": policy.get("policy_status", "missing_fail_closed"),
        "policy_frozen_fail_closed": bool(policy.get("policy_frozen_by_this_gate")),
        "release_grade_satisfied": bool(policy.get("release_grade_satisfied")),
        "selected_comparison_output_hashes_admitted": bool(
            prior_summary.get("selected_comparison_output_hashes_admitted", False)
        ),
        "selected_comparison_output_hash_count": int(
            prior_summary.get("selected_comparison_output_hash_count", 0)
        ),
        "allowed_output_signoff_present": bool(
            prior_summary.get("allowed_output_signoff_present", False)
        ),
        "recording_level": "input_ref_sha_and_policy_status_only",
    }


def _prior_signoff_items(
    replacement_tolerance_gate: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if replacement_tolerance_gate is None:
        return {}
    rows = replacement_tolerance_gate.get("required_signoff_items", [])
    if not isinstance(rows, list):
        return {}
    return {
        row["signoff_id"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("signoff_id"), str)
    }


def _required_signoffs(
    *,
    source_rights_summary: dict[str, Any],
    beco_recalculated_anchor_set: dict[str, Any] | None,
    replacement_tolerance_gate: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    prior_items = _prior_signoff_items(replacement_tolerance_gate)

    definitions = {
        "independent_lineage_review_signoff": {
            "category": "lineage",
            "review_input_refs": [
                "res006_beco_recalculation_admission_gate",
                "beco_recalculated_hash_anchor_set",
            ],
            "owner_input_needed": (
                "named independent reviewer acceptance of BEC-O recalculation "
                "runtime/version lineage and retained hash-only evidence"
            ),
            "fail_closed_reason": (
                "existing recalculation evidence is local retained evidence, "
                "not an independent lineage review"
            ),
        },
        "allowed_output_policy_signoff": {
            "category": "allowed_output",
            "review_input_refs": [
                "source_rights_output_policy_gate",
                "res006_beco_replacement_tolerance_admission_gate",
            ],
            "owner_input_needed": (
                "release owner or rights reviewer must explicitly admit selected "
                "BEC-O comparison output hashes under the allowed-output policy"
            ),
            "fail_closed_reason": (
                "source rights policy remains fail-closed for selected comparison "
                "outputs"
            ),
        },
        "numeric_tolerance_policy_signoff": {
            "category": "numeric_tolerance",
            "review_input_refs": [
                "res006_beco_recalculation_admission_gate",
                "res006_beco_replacement_tolerance_admission_gate",
            ],
            "owner_input_needed": (
                "release-grade numeric tolerance policy or exact-hash replacement "
                "policy for cached-vs-recalculated BEC-O output differences"
            ),
            "fail_closed_reason": (
                "this packet retains hashes and topology only and admits no raw "
                "numeric tolerance"
            ),
        },
        "replacement_anchor_signoff": {
            "category": "replacement_anchor",
            "review_input_refs": [
                "beco_recalculated_hash_anchor_set",
                "res006_beco_replacement_tolerance_admission_gate",
            ],
            "owner_input_needed": (
                "explicit retained decision promoting or rejecting the recalculated "
                "hash anchor set without mutating cached anchors in place"
            ),
            "fail_closed_reason": (
                "candidate recalculated anchor set is retained but not admitted"
                if beco_recalculated_anchor_set is not None
                else "candidate recalculated anchor set is unavailable"
            ),
        },
    }

    signoffs: list[dict[str, Any]] = []
    for signoff_id in SIGNOFF_IDS:
        prior = prior_items.get(signoff_id, {})
        signed_off = bool(prior.get("signed_off", False))
        admitted = bool(prior.get("admitted", False))
        if signoff_id == "allowed_output_policy_signoff":
            signed_off = signed_off or bool(
                source_rights_summary["allowed_output_signoff_present"]
            )
        current_status = "present" if signed_off and admitted else "missing"
        signoffs.append(
            {
                "signoff_id": signoff_id,
                "category": definitions[signoff_id]["category"],
                "required": True,
                "current_status": current_status,
                "signed_off": signed_off,
                "admitted": admitted,
                "review_input_refs": definitions[signoff_id]["review_input_refs"],
                "owner_input_needed": definitions[signoff_id]["owner_input_needed"],
                "fail_closed_reason": definitions[signoff_id]["fail_closed_reason"],
            }
        )
    return signoffs


def _lineage_tolerance_decision_inputs(
    *,
    res006_recalculation_gate: dict[str, Any] | None,
    beco_recalculated_anchor_set: dict[str, Any] | None,
    replacement_tolerance_gate: dict[str, Any] | None,
    source_rights_summary: dict[str, Any],
    cached_vs_recalculated_summary: dict[str, Any],
) -> dict[str, Any]:
    recalc_gate = (
        res006_recalculation_gate.get("beco_recalculation_gate", {})
        if res006_recalculation_gate is not None
        else {}
    )
    prior_decision = (
        replacement_tolerance_gate.get("admission_decision", {})
        if replacement_tolerance_gate is not None
        else {}
    )
    prior_replacement = (
        replacement_tolerance_gate.get("replacement_candidate_summary", {})
        if replacement_tolerance_gate is not None
        else {}
    )

    return {
        "lineage": {
            "local_recalculation_gate_present": res006_recalculation_gate is not None,
            "local_recalculation_gate_status": (
                res006_recalculation_gate.get("status", "")
                if res006_recalculation_gate is not None
                else "missing_fail_closed"
            ),
            "spreadsheet_execution_attempted": bool(
                recalc_gate.get("spreadsheet_execution_attempted", False)
            ),
            "recalculation_execution_status": (
                beco_recalculated_anchor_set.get(
                    "recalculation_execution_status", ""
                )
                if beco_recalculated_anchor_set is not None
                else ""
            ),
            "executor_tool_recorded": bool(
                beco_recalculated_anchor_set.get("executor_tool")
                if beco_recalculated_anchor_set is not None
                else False
            ),
            "executor_version_recorded": bool(
                beco_recalculated_anchor_set.get("executor_version_string")
                if beco_recalculated_anchor_set is not None
                else False
            ),
            "independent_lineage_review_present": bool(
                prior_decision.get("independent_lineage_review_present", False)
            ),
            "independent_lineage_review_required": True,
            "raw_selected_values_retained": False,
            "formula_text_retained": False,
            "stdout_retained": False,
            "stderr_retained": False,
            "temporary_workbook_copy_retained": False,
        },
        "allowed_output": {
            "source_policy_present": source_rights_summary["present"],
            "source_policy_status": source_rights_summary["policy_status"],
            "release_grade_satisfied": source_rights_summary[
                "release_grade_satisfied"
            ],
            "selected_comparison_output_hashes_admitted": source_rights_summary[
                "selected_comparison_output_hashes_admitted"
            ],
            "allowed_output_signoff_present": source_rights_summary[
                "allowed_output_signoff_present"
            ],
        },
        "numeric_tolerance": {
            "exact_hash_check_passed": cached_vs_recalculated_summary[
                "exact_hash_check_passed"
            ],
            "numeric_tolerance_policy_present": bool(
                prior_decision.get("tolerance_policy_admitted", False)
            ),
            "numeric_tolerance_policy_admitted": bool(
                prior_decision.get("tolerance_policy_admitted", False)
            ),
            "raw_numeric_values_retained_in_this_packet": False,
            "review_requires_external_signoff": True,
        },
        "replacement_anchor": {
            "candidate_replacement_anchor_set_retained": bool(
                prior_replacement.get(
                    "candidate_replacement_anchor_set_retained",
                    beco_recalculated_anchor_set is not None,
                )
            ),
            "replacement_anchor_set_admitted": False,
            "replacement_anchor_signoff_present": bool(
                prior_replacement.get("replacement_anchor_signoff_present", False)
            ),
            "replacement_anchor_authority_granted": False,
            "in_place_cached_anchor_replacement_allowed": False,
        },
    }


def _admission_decision(
    *,
    cached_vs_recalculated_summary: dict[str, Any],
    required_signoffs: list[dict[str, Any]],
) -> dict[str, Any]:
    missing_items = [
        item["signoff_id"]
        for item in required_signoffs
        if not item["signed_off"] or not item["admitted"]
    ]
    blockers = [
        item["fail_closed_reason"]
        for item in required_signoffs
        if not item["signed_off"] or not item["admitted"]
    ]
    if not cached_vs_recalculated_summary["exact_hash_check_passed"]:
        blockers.insert(
            0,
            "cached-vs-recalculated selected hashes do not satisfy exact-hash admission",
        )

    return {
        "residual_id": "RES-006",
        "decision": "res006_remains_blocked_fail_closed",
        "status": "blocked_fail_closed",
        "residual_closed": False,
        "res006_narrowly_closed": False,
        "closed_residual_ids_by_this_packet": [],
        "exact_hash_check_passed": cached_vs_recalculated_summary[
            "exact_hash_check_passed"
        ],
        "independent_lineage_review_present": False,
        "allowed_output_signoff_present": False,
        "numeric_tolerance_policy_admitted": False,
        "replacement_anchor_set_admitted": False,
        "release_grade_validated": False,
        "benchmark_consumed_for_release": False,
        "raw_selected_values_retained": False,
        "current_missing_items": missing_items,
        "remaining_blockers": blockers,
    }


def _load_existing_inputs(
    *,
    res006_recalculation_gate_path: Path,
    beco_recalculated_anchor_set_path: Path,
    mechanism_comparison_hashes_path: Path,
    source_rights_output_policy_gate_path: Path,
    replacement_tolerance_gate_path: Path,
) -> dict[str, dict[str, Any] | None]:
    return {
        "res006_recalculation_gate": _load_json(res006_recalculation_gate_path),
        "beco_recalculated_anchor_set": _load_json(
            beco_recalculated_anchor_set_path
        ),
        "mechanism_comparison_hashes": _load_json(mechanism_comparison_hashes_path),
        "source_rights_output_policy_gate": _load_json(
            source_rights_output_policy_gate_path
        ),
        "replacement_tolerance_gate": _load_json(replacement_tolerance_gate_path),
    }


def generate_res006_beco_lineage_tolerance_review_packet(
    *,
    repo_root: Path = REPO_ROOT,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    res006_recalculation_gate_path: Path = DEFAULT_RES006_RECALCULATION_GATE,
    beco_recalculated_anchor_set_path: Path = DEFAULT_BECO_RECALCULATED_ANCHOR_SET,
    mechanism_comparison_hashes_path: Path = DEFAULT_MECHANISM_COMPARISON_HASHES,
    source_rights_output_policy_gate_path: Path = (
        DEFAULT_SOURCE_RIGHTS_OUTPUT_POLICY_GATE
    ),
    replacement_tolerance_gate_path: Path = DEFAULT_RES006_REPLACEMENT_TOLERANCE_GATE,
) -> dict[str, Any]:
    input_refs = [
        _input_ref(
            artifact_key="res006_beco_recalculation_admission_gate",
            path=res006_recalculation_gate_path,
            repo_root=repo_root,
            role="local_recalculation_gate_and_cached_vs_recalculated_lineage",
        ),
        _input_ref(
            artifact_key="beco_recalculated_hash_anchor_set",
            path=beco_recalculated_anchor_set_path,
            repo_root=repo_root,
            role="candidate_recalculated_hash_anchor_set_not_admitted",
        ),
        _input_ref(
            artifact_key="mechanism_comparison_hashes",
            path=mechanism_comparison_hashes_path,
            repo_root=repo_root,
            role="cached_hash_anchor_source",
        ),
        _input_ref(
            artifact_key="source_rights_output_policy_gate",
            path=source_rights_output_policy_gate_path,
            repo_root=repo_root,
            role="allowed_output_policy_source",
        ),
        _input_ref(
            artifact_key="res006_beco_replacement_tolerance_admission_gate",
            path=replacement_tolerance_gate_path,
            repo_root=repo_root,
            role="prior_fail_closed_tolerance_replacement_gate",
        ),
    ]
    refs_by_key = {ref["artifact_key"]: ref for ref in input_refs}
    loaded = _load_existing_inputs(
        res006_recalculation_gate_path=res006_recalculation_gate_path,
        beco_recalculated_anchor_set_path=beco_recalculated_anchor_set_path,
        mechanism_comparison_hashes_path=mechanism_comparison_hashes_path,
        source_rights_output_policy_gate_path=source_rights_output_policy_gate_path,
        replacement_tolerance_gate_path=replacement_tolerance_gate_path,
    )

    anchor_sources = _anchor_source_summary(
        mechanism_comparison_hashes=loaded["mechanism_comparison_hashes"],
        beco_recalculated_anchor_set=loaded["beco_recalculated_anchor_set"],
        refs_by_key=refs_by_key,
    )
    mismatch_summary = _cached_vs_recalculated_summary(
        res006_recalculation_gate=loaded["res006_recalculation_gate"],
        mechanism_comparison_hashes=loaded["mechanism_comparison_hashes"],
        beco_recalculated_anchor_set=loaded["beco_recalculated_anchor_set"],
        replacement_tolerance_gate=loaded["replacement_tolerance_gate"],
    )
    source_rights = _source_rights_summary(
        source_rights_output_policy_gate=loaded["source_rights_output_policy_gate"],
        replacement_tolerance_gate=loaded["replacement_tolerance_gate"],
    )
    required_signoffs = _required_signoffs(
        source_rights_summary=source_rights,
        beco_recalculated_anchor_set=loaded["beco_recalculated_anchor_set"],
        replacement_tolerance_gate=loaded["replacement_tolerance_gate"],
    )
    decision_inputs = _lineage_tolerance_decision_inputs(
        res006_recalculation_gate=loaded["res006_recalculation_gate"],
        beco_recalculated_anchor_set=loaded["beco_recalculated_anchor_set"],
        replacement_tolerance_gate=loaded["replacement_tolerance_gate"],
        source_rights_summary=source_rights,
        cached_vs_recalculated_summary=mismatch_summary,
    )
    decision = _admission_decision(
        cached_vs_recalculated_summary=mismatch_summary,
        required_signoffs=required_signoffs,
    )
    guards = _authority_guards()

    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": PACKAGE_ID,
        "residual_id": "RES-006",
        "status": "blocked_fail_closed_res006_beco_lineage_tolerance_review_candidate",
        "review_target": "RES-006_BEC-O_lineage_tolerance_review_candidate",
        "artifact_dir": _rel(retained_dir, repo_root),
        "packet_role": "machine_readable_review_candidate_not_admission",
        "input_refs": input_refs,
        "anchor_source_summary": anchor_sources,
        "cached_vs_recalculated_summary": mismatch_summary,
        "lineage_tolerance_decision_inputs": decision_inputs,
        "lineage_tolerance_required_signoffs": required_signoffs,
        "current_missing_items": decision["current_missing_items"],
        "admission_decision": decision,
        "current_gate_results": {
            "RES-006": "blocked_fail_closed_lineage_tolerance_review_candidate"
        },
        "benchmark_consumed_for_release": False,
        "raw_selected_values_retained": False,
        "formula_text_retained": False,
        "temporary_workbook_copy_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_output_tables_retained": False,
        "individual_row_hashes_retained_in_this_packet": False,
        "authority_guards": guards,
        "authority_guards_all_false": not any(guards.values()),
        "behavior_risks": [
            "candidate recalculated hashes could be mistaken for an admitted replacement anchor",
            "0/9 hash match topology could be mistaken for numeric tolerance evidence",
            "local recalculation lineage could be mistaken for independent review",
            "source rights policy could be mistaken for selected-output admission despite remaining fail-closed",
        ],
        "integration_notes": [
            "This packet does not replace cached BEC-O anchors or close RES-006.",
            "Only retained JSON inputs are read; workbook contents, raw selected values, formulas, stdout, stderr, temporary workbook copies, and raw output tables are not retained.",
            "Cached-vs-recalculated topology is retained as counts and comparison ids only.",
            "Release use still requires independent lineage, allowed-output, numeric tolerance, and replacement-anchor signoff.",
            "Blast/component/effect/stock/runtime/Pk/fuze/replacement authority guards remain false.",
        ],
    }


def write_retained_artifacts(
    *,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    repo_root: Path = REPO_ROOT,
    res006_recalculation_gate_path: Path = DEFAULT_RES006_RECALCULATION_GATE,
    beco_recalculated_anchor_set_path: Path = DEFAULT_BECO_RECALCULATED_ANCHOR_SET,
    mechanism_comparison_hashes_path: Path = DEFAULT_MECHANISM_COMPARISON_HASHES,
    source_rights_output_policy_gate_path: Path = (
        DEFAULT_SOURCE_RIGHTS_OUTPUT_POLICY_GATE
    ),
    replacement_tolerance_gate_path: Path = DEFAULT_RES006_REPLACEMENT_TOLERANCE_GATE,
) -> dict[str, Any]:
    packet = generate_res006_beco_lineage_tolerance_review_packet(
        repo_root=repo_root,
        retained_dir=retained_dir,
        res006_recalculation_gate_path=res006_recalculation_gate_path,
        beco_recalculated_anchor_set_path=beco_recalculated_anchor_set_path,
        mechanism_comparison_hashes_path=mechanism_comparison_hashes_path,
        source_rights_output_policy_gate_path=source_rights_output_policy_gate_path,
        replacement_tolerance_gate_path=replacement_tolerance_gate_path,
    )
    retained_dir.mkdir(parents=True, exist_ok=True)

    packet_path = retained_dir / PACKET_FILENAME
    _write_json(packet_path, packet)
    packet_sha256 = _sha256_file(packet_path)
    packet_artifact = {
        "artifact_key": "res006_beco_lineage_tolerance_review_candidate_packet",
        "filename": PACKET_FILENAME,
        "relative_path": _rel(packet_path, repo_root),
        "schema_version": packet["schema_version"],
        "sha256": packet_sha256,
    }

    manifest = {
        "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
        "package_id": PACKAGE_ID,
        "residual_id": "RES-006",
        "status": packet["status"],
        "artifact_dir": _rel(retained_dir, repo_root),
        "artifacts": [packet_artifact],
        "input_refs": packet["input_refs"],
        "cached_vs_recalculated_summary": packet[
            "cached_vs_recalculated_summary"
        ],
        "lineage_tolerance_required_signoffs": packet[
            "lineage_tolerance_required_signoffs"
        ],
        "current_missing_items": packet["current_missing_items"],
        "admission_decision": packet["admission_decision"],
        "benchmark_consumed_for_release": False,
        "raw_selected_values_retained": False,
        "formula_text_retained": False,
        "temporary_workbook_copy_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_output_tables_retained": False,
        "authority_guards": packet["authority_guards"],
        "authority_guards_all_false": packet["authority_guards_all_false"],
    }
    manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
    _write_json(manifest_path, manifest)

    packet["retained_artifact_sha256"] = packet_sha256
    packet["retained_manifest_sha256"] = _sha256_file(manifest_path)
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the fail-closed RES-006 BEC-O lineage/tolerance review "
            "candidate packet."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated packet JSON.",
    )
    parser.add_argument(
        "--retained-dir",
        type=Path,
        default=DEFAULT_RETAINED_DIR,
        help="Directory for retained RES-006 lineage/tolerance review artifacts.",
    )
    parser.add_argument(
        "--res006-recalculation-gate",
        type=Path,
        default=DEFAULT_RES006_RECALCULATION_GATE,
        help="Existing retained RES-006 recalculation admission gate JSON.",
    )
    parser.add_argument(
        "--beco-recalculated-anchor-set",
        type=Path,
        default=DEFAULT_BECO_RECALCULATED_ANCHOR_SET,
        help="Existing retained BEC-O recalculated hash anchor set JSON.",
    )
    parser.add_argument(
        "--mechanism-comparison-hashes",
        type=Path,
        default=DEFAULT_MECHANISM_COMPARISON_HASHES,
        help="Existing retained mechanism comparison hashes JSON.",
    )
    parser.add_argument(
        "--source-rights-output-policy-gate",
        type=Path,
        default=DEFAULT_SOURCE_RIGHTS_OUTPUT_POLICY_GATE,
        help="Existing retained source rights output policy gate JSON.",
    )
    parser.add_argument(
        "--replacement-tolerance-gate",
        type=Path,
        default=DEFAULT_RES006_REPLACEMENT_TOLERANCE_GATE,
        help="Existing retained RES-006 replacement/tolerance admission gate JSON.",
    )
    args = parser.parse_args(argv)

    packet = write_retained_artifacts(
        retained_dir=args.retained_dir,
        res006_recalculation_gate_path=args.res006_recalculation_gate,
        beco_recalculated_anchor_set_path=args.beco_recalculated_anchor_set,
        mechanism_comparison_hashes_path=args.mechanism_comparison_hashes,
        source_rights_output_policy_gate_path=args.source_rights_output_policy_gate,
        replacement_tolerance_gate_path=args.replacement_tolerance_gate,
    )
    if args.output:
        _write_json(args.output, packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
