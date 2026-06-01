from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_res006_beco_lineage_tolerance_review_packet as packet,
)
from tools.maintenance import a2_retained_manifest_integrity as manifest_integrity  # noqa: E402


HEX64 = re.compile(r"^[a-f0-9]{64}$")


def _walk(payload: Any) -> list[Any]:
    values = [payload]
    if isinstance(payload, dict):
        for value in payload.values():
            values.extend(_walk(value))
    elif isinstance(payload, list):
        for value in payload:
            values.extend(_walk(value))
    return values


def _assert_no_raw_or_row_level_outputs(payload: dict[str, Any]) -> None:
    forbidden_keys = {
        "cached_anchor_sha256",
        "cached_formula_value",
        "cached_hashes",
        "cell",
        "command_result",
        "comparison_output_sha256",
        "formula",
        "formula_sha256",
        "hash_only_comparison_rows",
        "raw_output_table",
        "raw_output_tables",
        "raw_output_value",
        "raw_value",
        "recalculated_output_sha256",
        "selected_hash_comparisons",
        "selected_recalculated_hashes",
        "source_table_payload",
        "source_table_rows",
        "stderr",
        "stdout",
        "temporary_workbook_copy",
    }
    for value in _walk(payload):
        if isinstance(value, dict):
            assert not (forbidden_keys & set(value))


def test_res006_lineage_tolerance_packet_is_fail_closed_and_machine_readable(
    tmp_path: Path,
) -> None:
    artifact = packet.generate_res006_beco_lineage_tolerance_review_packet(
        retained_dir=tmp_path / "retained"
    )

    assert artifact["schema_version"] == (
        "a2.res006_beco_lineage_tolerance_review_candidate_packet.v1"
    )
    assert artifact["residual_id"] == "RES-006"
    assert artifact["status"] == (
        "blocked_fail_closed_res006_beco_lineage_tolerance_review_candidate"
    )
    assert artifact["packet_role"] == "machine_readable_review_candidate_not_admission"
    assert artifact["benchmark_consumed_for_release"] is False
    assert artifact["raw_selected_values_retained"] is False
    assert artifact["raw_output_tables_retained"] is False
    assert artifact["stdout_retained"] is False
    assert artifact["stderr_retained"] is False
    assert artifact["temporary_workbook_copy_retained"] is False

    refs = artifact["input_refs"]
    assert [ref["artifact_key"] for ref in refs] == [
        "res006_beco_recalculation_admission_gate",
        "beco_recalculated_hash_anchor_set",
        "mechanism_comparison_hashes",
        "source_rights_output_policy_gate",
        "res006_beco_replacement_tolerance_admission_gate",
    ]
    assert all(ref["present"] is True for ref in refs)
    assert all(HEX64.fullmatch(ref["sha256"]) for ref in refs)

    guards = artifact["authority_guards"]
    assert artifact["authority_guards_all_false"] is True
    assert not any(guards.values())
    assert guards["blast_mechanism_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["stock_descriptor_created"] is False
    assert guards["runtime_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["fuze_authority_granted"] is False
    assert guards["replacement_anchor_authority_granted"] is False
    assert guards["cached_anchor_replacement_authority_granted"] is False

    summary = artifact["cached_vs_recalculated_summary"]
    assert summary["counts_and_comparison_ids_only"] is True
    assert summary["status"] == "cached_vs_recalculated_hash_mismatch_fail_closed"
    assert summary["topology"] == "zero_match_all_selected_comparison_ids_mismatched"
    assert summary["comparison_id_count"] == 9
    assert summary["cached_anchor_count"] == 9
    assert summary["recalculated_anchor_count"] == 9
    assert summary["matching_count"] == 0
    assert summary["mismatch_count"] == 9
    assert summary["missing_cached_count"] == 0
    assert summary["missing_recalculated_count"] == 0
    assert summary["exact_hash_check_passed"] is False
    assert summary["matching_comparison_ids"] == []
    assert summary["mismatch_comparison_ids"] == [
        "BEC-O-METRIC-DEFAULT-001",
        "BEC-O-METRIC-DEFAULT-002",
        "BEC-O-METRIC-DEFAULT-003",
        "BEC-O-METRIC-DEFAULT-004",
        "BEC-O-METRIC-DEFAULT-005",
        "BEC-O-METRIC-DEFAULT-006",
        "BEC-O-METRIC-DEFAULT-007",
        "BEC-O-METRIC-DEFAULT-008",
        "BEC-O-METRIC-DEFAULT-009",
    ]
    assert summary["individual_row_hashes_retained_in_this_packet"] is False
    assert "hash_only_comparison_rows" not in summary

    sources = artifact["anchor_source_summary"]
    cached = sources["cached_anchor_source"]
    recalculated = sources["recalculated_anchor_source"]
    assert cached["selected_output_hash_count"] == 9
    assert recalculated["selected_output_hash_count"] == 9
    assert HEX64.fullmatch(cached["selected_output_set_sha256"])
    assert HEX64.fullmatch(recalculated["selected_output_set_sha256"])
    assert cached["individual_anchor_hashes_retained_in_this_packet"] is False
    assert recalculated["individual_anchor_hashes_retained_in_this_packet"] is False
    assert cached["anchor_rows_retained_in_this_packet"] is False
    assert recalculated["anchor_rows_retained_in_this_packet"] is False

    signoffs = artifact["lineage_tolerance_required_signoffs"]
    assert [item["signoff_id"] for item in signoffs] == [
        "independent_lineage_review_signoff",
        "allowed_output_policy_signoff",
        "numeric_tolerance_policy_signoff",
        "replacement_anchor_signoff",
    ]
    assert all(item["required"] is True for item in signoffs)
    assert all(item["current_status"] == "missing" for item in signoffs)
    assert all(item["signed_off"] is False for item in signoffs)
    assert all(item["admitted"] is False for item in signoffs)
    assert artifact["current_missing_items"] == [
        "independent_lineage_review_signoff",
        "allowed_output_policy_signoff",
        "numeric_tolerance_policy_signoff",
        "replacement_anchor_signoff",
    ]

    decision_inputs = artifact["lineage_tolerance_decision_inputs"]
    assert decision_inputs["lineage"]["local_recalculation_gate_present"] is True
    assert decision_inputs["lineage"]["spreadsheet_execution_attempted"] is True
    assert decision_inputs["lineage"]["independent_lineage_review_present"] is False
    assert decision_inputs["allowed_output"]["allowed_output_signoff_present"] is False
    assert (
        decision_inputs["numeric_tolerance"]["numeric_tolerance_policy_admitted"]
        is False
    )
    assert (
        decision_inputs["replacement_anchor"][
            "in_place_cached_anchor_replacement_allowed"
        ]
        is False
    )

    decision = artifact["admission_decision"]
    assert decision["decision"] == "res006_remains_blocked_fail_closed"
    assert decision["status"] == "blocked_fail_closed"
    assert decision["residual_closed"] is False
    assert decision["closed_residual_ids_by_this_packet"] == []
    assert decision["benchmark_consumed_for_release"] is False
    assert decision["raw_selected_values_retained"] is False

    _assert_no_raw_or_row_level_outputs(artifact)


def test_res006_lineage_tolerance_packet_missing_inputs_remain_fail_closed(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.json"
    artifact = packet.generate_res006_beco_lineage_tolerance_review_packet(
        retained_dir=tmp_path / "retained",
        res006_recalculation_gate_path=missing,
        beco_recalculated_anchor_set_path=missing,
        mechanism_comparison_hashes_path=missing,
        source_rights_output_policy_gate_path=missing,
        replacement_tolerance_gate_path=missing,
    )

    assert artifact["status"] == (
        "blocked_fail_closed_res006_beco_lineage_tolerance_review_candidate"
    )
    assert all(ref["present"] is False for ref in artifact["input_refs"])
    assert all(ref["status"] == "missing_fail_closed" for ref in artifact["input_refs"])
    assert artifact["cached_vs_recalculated_summary"]["comparison_id_count"] == 0
    assert artifact["cached_vs_recalculated_summary"]["cached_anchor_count"] == 0
    assert artifact["cached_vs_recalculated_summary"]["recalculated_anchor_count"] == 0
    assert artifact["cached_vs_recalculated_summary"][
        "status"
    ] == "cached_vs_recalculated_comparison_inputs_missing_fail_closed"
    assert artifact["lineage_tolerance_decision_inputs"]["lineage"][
        "local_recalculation_gate_present"
    ] is False
    assert artifact["lineage_tolerance_decision_inputs"]["replacement_anchor"][
        "candidate_replacement_anchor_set_retained"
    ] is False
    assert artifact["current_missing_items"] == [
        "independent_lineage_review_signoff",
        "allowed_output_policy_signoff",
        "numeric_tolerance_policy_signoff",
        "replacement_anchor_signoff",
    ]
    assert artifact["authority_guards_all_false"] is True
    assert artifact["benchmark_consumed_for_release"] is False
    assert artifact["raw_selected_values_retained"] is False

    _assert_no_raw_or_row_level_outputs(artifact)


def test_res006_lineage_tolerance_cli_writes_packet_and_manifest(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "packet_copy.json"
    retained_dir = tmp_path / "retained"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res006_beco_lineage_tolerance_review_packet.py",
            "--retained-dir",
            str(retained_dir),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert result.stdout == ""
    assert output_path.is_file()
    output_copy = json.loads(output_path.read_text(encoding="utf-8"))
    assert HEX64.fullmatch(output_copy["retained_artifact_sha256"])
    assert HEX64.fullmatch(output_copy["retained_manifest_sha256"])

    packet_path = retained_dir / "res006_beco_lineage_tolerance_review_candidate_packet.json"
    manifest_path = retained_dir / "manifest.json"
    assert packet_path.is_file()
    assert manifest_path.is_file()

    retained_packet = json.loads(packet_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert retained_packet["schema_version"] == (
        "a2.res006_beco_lineage_tolerance_review_candidate_packet.v1"
    )
    assert manifest["schema_version"] == (
        "a2.res006_beco_lineage_tolerance_review_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "blocked_fail_closed_res006_beco_lineage_tolerance_review_candidate"
    )
    assert manifest["artifacts"][0]["artifact_key"] == (
        "res006_beco_lineage_tolerance_review_candidate_packet"
    )
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])
    assert len(manifest["input_refs"]) == 5
    assert all(HEX64.fullmatch(ref["sha256"]) for ref in manifest["input_refs"])
    assert manifest["cached_vs_recalculated_summary"][
        "counts_and_comparison_ids_only"
    ] is True
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["authority_guards"].values())

    summary = manifest_integrity.check_retained_manifest_integrity(
        manifest_paths=[manifest_path]
    )
    assert summary["missing_total"] == 0
    assert summary["sha_mismatch_total"] == 0
    assert summary["guard_true_total"] == 0

    _assert_no_raw_or_row_level_outputs(retained_packet)
    _assert_no_raw_or_row_level_outputs(manifest)
