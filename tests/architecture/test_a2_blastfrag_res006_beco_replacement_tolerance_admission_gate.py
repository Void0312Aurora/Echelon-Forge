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
    a2_blastfrag_res006_beco_replacement_tolerance_admission_gate as gate,
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


def _assert_hash_ref_label_only(payload: dict[str, Any]) -> None:
    forbidden_raw_keys = {
        "cached_formula_value",
        "command_result",
        "formula",
        "raw_output_table",
        "raw_output_tables",
        "raw_output_value",
        "raw_value",
        "source_table_payload",
        "source_table_rows",
        "stderr",
        "stdout",
        "temporary_workbook_copy",
    }
    for value in _walk(payload):
        if isinstance(value, dict):
            assert not (forbidden_raw_keys & set(value))


def test_res006_replacement_tolerance_packet_fails_closed_with_missing_signoffs(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_res006_beco_replacement_tolerance_admission_gate(
        retained_dir=tmp_path
    )

    assert artifact["schema_version"] == (
        "a2.res006_beco_replacement_tolerance_admission_gate.v1"
    )
    assert artifact["residual_id"] == "RES-006"
    assert artifact["status"] == (
        "blocked_fail_closed_res006_beco_replacement_tolerance_admission_review"
    )
    assert artifact["benchmark_consumed_for_release"] is False
    assert artifact["raw_selected_values_retained"] is False
    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["authority_guards"].values())
    assert artifact["authority_guards"]["blast_mechanism_authority_granted"] is False
    assert artifact["authority_guards"][
        "component_failure_probability_authority_granted"
    ] is False
    assert artifact["authority_guards"]["effect_scale_authority_granted"] is False
    assert artifact["authority_guards"]["stock_descriptor_created"] is False
    assert artifact["authority_guards"]["runtime_authority_granted"] is False
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["fuze_authority_granted"] is False
    assert artifact["authority_guards"]["replacement_anchor_authority_granted"] is False

    refs = artifact["input_refs"]
    assert [ref["artifact_key"] for ref in refs] == [
        "res006_beco_recalculation_admission_gate",
        "beco_recalculated_hash_anchor_set",
        "mechanism_comparison_hashes",
        "source_rights_output_policy_gate",
    ]
    assert all(ref["present"] is True for ref in refs)
    assert all(HEX64.fullmatch(ref["sha256"]) for ref in refs)

    source_rights = artifact["source_rights_output_policy_summary"]
    assert source_rights["allowed_output_policy_status"] == (
        "release_candidate_fail_closed_policy_frozen"
    )
    assert source_rights["allowed_output_signoff_present"] is False
    assert source_rights["selected_comparison_output_hashes_admitted"] is False
    assert source_rights["recording_level"] == "path_sha_status_only"

    mismatch = artifact["cached_vs_recalculated_mismatch_summary"]
    assert mismatch["status"] == "cached_vs_recalculated_hash_mismatch_fail_closed"
    assert mismatch["cached_anchor_count"] == 9
    assert mismatch["recalculated_anchor_count"] == 9
    assert mismatch["comparison_row_count"] == 9
    assert mismatch["matching_count"] == 0
    assert mismatch["mismatch_count"] == 9
    assert mismatch["exact_hash_check_passed"] is False
    assert mismatch["raw_selected_values_retained"] is False
    assert mismatch["stdout_retained"] is False
    assert len(mismatch["mismatch_comparison_ids"]) == 9
    for row in mismatch["hash_only_comparison_rows"]:
        assert HEX64.fullmatch(row["cached_anchor_sha256"])
        assert HEX64.fullmatch(row["recalculated_output_sha256"])
        assert HEX64.fullmatch(row["formula_sha256"])
        assert row["raw_value_disclosed"] is False
        assert row["formula_text_disclosed"] is False

    replacement = artifact["replacement_candidate_summary"]
    assert replacement["candidate_replacement_anchor_set_retained"] is True
    assert replacement["replacement_anchor_set_admitted"] is False
    assert replacement["replacement_anchor_signoff_present"] is False
    assert replacement["replacement_anchor_authority_granted"] is False
    assert replacement["benchmark_consumed_for_release"] is False

    signoffs = artifact["required_signoff_items"]
    assert [item["signoff_id"] for item in signoffs] == [
        "independent_lineage_review_signoff",
        "allowed_output_policy_signoff",
        "numeric_tolerance_policy_signoff",
        "replacement_anchor_signoff",
    ]
    assert all(item["required"] is True for item in signoffs)
    assert all(item["signed_off"] is False for item in signoffs)
    assert all(item["admitted"] is False for item in signoffs)
    assert artifact["current_missing_items"] == [
        "independent_lineage_review_signoff",
        "allowed_output_policy_signoff",
        "numeric_tolerance_policy_signoff",
        "replacement_anchor_signoff",
    ]

    decision = artifact["admission_decision"]
    assert decision["decision"] == "res006_remains_blocked_fail_closed"
    assert decision["status"] == "blocked_fail_closed"
    assert decision["residual_closed"] is False
    assert decision["closed_residual_ids_by_this_gate"] == []
    assert decision["independent_lineage_review_present"] is False
    assert decision["allowed_output_signoff_present"] is False
    assert decision["tolerance_policy_admitted"] is False
    assert decision["replacement_anchor_set_admitted"] is False
    assert decision["benchmark_consumed_for_release"] is False
    assert decision["raw_selected_values_retained"] is False

    _assert_hash_ref_label_only(artifact)


def test_res006_replacement_tolerance_missing_inputs_remain_machine_readable(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.json"
    artifact = gate.generate_res006_beco_replacement_tolerance_admission_gate(
        retained_dir=tmp_path / "retained",
        res006_recalculation_gate_path=missing,
        beco_recalculated_anchor_set_path=missing,
        mechanism_comparison_hashes_path=missing,
        source_rights_output_policy_gate_path=missing,
    )

    assert artifact["status"] == (
        "blocked_fail_closed_res006_beco_replacement_tolerance_admission_review"
    )
    assert all(ref["present"] is False for ref in artifact["input_refs"])
    assert all(ref["status"] == "missing_fail_closed" for ref in artifact["input_refs"])
    assert artifact["cached_vs_recalculated_mismatch_summary"][
        "comparison_row_count"
    ] == 0
    assert artifact["replacement_candidate_summary"]["status"] == (
        "candidate_replacement_anchor_set_missing_fail_closed"
    )
    assert artifact["admission_decision"]["decision"] == (
        "res006_remains_blocked_fail_closed"
    )
    assert artifact["authority_guards_all_false"] is True
    assert artifact["benchmark_consumed_for_release"] is False
    assert artifact["raw_selected_values_retained"] is False

    _assert_hash_ref_label_only(artifact)


def test_res006_replacement_tolerance_cli_writes_gate_and_manifest(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "gate_cli.json"
    retained_dir = tmp_path / "retained"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res006_beco_replacement_tolerance_admission_gate.py",
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
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["retained_artifact_sha256"]
    assert artifact["retained_manifest_sha256"]

    gate_path = retained_dir / "res006_beco_replacement_tolerance_admission_gate.json"
    manifest_path = retained_dir / "manifest.json"
    assert gate_path.is_file()
    assert manifest_path.is_file()

    retained_gate = json.loads(gate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert retained_gate["schema_version"] == (
        "a2.res006_beco_replacement_tolerance_admission_gate.v1"
    )
    assert manifest["schema_version"] == (
        "a2.res006_beco_replacement_tolerance_admission_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "blocked_fail_closed_res006_beco_replacement_tolerance_admission_review"
    )
    assert manifest["artifacts"][0]["artifact_key"] == (
        "res006_beco_replacement_tolerance_admission_gate"
    )
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])
    assert len(manifest["input_refs"]) == 4
    assert all(HEX64.fullmatch(ref["sha256"]) for ref in manifest["input_refs"])
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["authority_guards"].values())

    summary = manifest_integrity.check_retained_manifest_integrity(
        manifest_paths=[manifest_path]
    )
    assert summary["missing_total"] == 0
    assert summary["sha_mismatch_total"] == 0
    assert summary["guard_true_total"] == 0
