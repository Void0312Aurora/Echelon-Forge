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
    a2_blastfrag_res006_beco_recalculation_admission_gate as gate,
)


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


def _assert_hash_only(payload: dict[str, Any]) -> None:
    forbidden_raw_keys = {
        "cached_formula_value",
        "formula",
        "raw_value",
        "raw_output_value",
        "source_table_payload",
        "source_table_rows",
    }
    for value in _walk(payload):
        if isinstance(value, dict):
            assert not (forbidden_raw_keys & set(value))


def test_res006_beco_recalculation_gate_retains_hash_only_candidate_path(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_res006_beco_recalculation_admission_gate(
        retained_dir=tmp_path
    )

    assert artifact["schema_version"] == (
        "a2.res006_beco_recalculation_admission_gate.v1"
    )
    assert artifact["status"] == (
        "partial_fail_closed_res006_beco_recalculation_admission"
    )
    assert artifact["mechanism_comparison_hashes_input_status"] == (
        "partial_fail_closed_mechanism_comparison_hash_manifest"
    )
    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["authority_guards"].values())
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False

    source_rights = artifact["source_rights_output_policy_summary"]
    assert source_rights["present"] is True
    assert source_rights["allowed_output_policy_status"] == (
        "release_candidate_fail_closed_policy_frozen"
    )
    assert source_rights["selected_comparison_hashes_admitted_by_policy"] is False

    decision = artifact["admission_decision"]
    assert decision["residual_id"] == "RES-006"
    assert decision["decision"] == "res006_remains_blocked_fail_closed"
    assert decision["res006_narrowly_closed"] is False
    assert decision["beco_recalculation_hashes_admitted"] is False
    assert decision["allowed_output_signoff_present"] is False
    assert decision["tolerance_policy_admitted"] is False
    assert decision["replacement_anchor_set_admitted"] is False
    assert decision["closed_residual_ids_by_this_gate"] == []

    cached = artifact["cached_anchor_summary"]
    assert cached["cached_hash_anchor_count"] == 9
    assert cached["all_selected_cached_hashes_present"] is True
    assert cached["spreadsheet_calculation_executed"] is False
    assert HEX64.fullmatch(cached["selected_comparison_output_set_sha256"])
    for row in cached["cached_hashes"]:
        assert HEX64.fullmatch(row["cached_anchor_sha256"])
        assert HEX64.fullmatch(row["formula_sha256"])
        assert row["raw_value_disclosed"] is False
        assert row["formula_text_disclosed"] is False

    tooling = artifact["tooling_detection"]
    beco = artifact["beco_recalculation_gate"]
    replacement = artifact["replacement_path"]
    anchor_set = artifact["candidate_replacement_anchor_set"]

    if tooling["tool_detection_status"] == "spreadsheet_execution_tool_available":
        assert beco["spreadsheet_execution_attempted"] is True
        assert beco["execution_attempt"]["attempted"] is True
        assert beco["execution_attempt"]["raw_values_retained"] is False
        assert beco["execution_attempt"]["temporary_workbook_copy_retained"] is False
        assert anchor_set["status"] == (
            "candidate_replacement_anchor_set_retained_not_admitted"
        )
        assert anchor_set["recalculated_hash_count"] == 9
        assert anchor_set["all_selected_recalculated_hashes_present"] is True
        assert HEX64.fullmatch(anchor_set["selected_recalculated_output_set_sha256"])
        assert anchor_set["raw_selected_values_retained"] is False
        assert anchor_set["formula_text_retained"] is False
        assert anchor_set["replacement_anchor_set_admitted"] is False
        for row in anchor_set["selected_recalculated_hashes"]:
            assert HEX64.fullmatch(row["recalculated_output_sha256"])
            assert HEX64.fullmatch(row["formula_sha256"])
            assert row["raw_value_disclosed"] is False
            assert row["formula_text_disclosed"] is False

        mismatch = artifact["mismatch_lineage"]
        assert mismatch["status"] == (
            "cached_to_recalculated_hash_lineage_mismatch_fail_closed"
        )
        assert mismatch["cached_anchor_count"] == 9
        assert mismatch["recalculated_anchor_count"] == 9
        assert mismatch["matching_count"] == 0
        assert mismatch["mismatch_count"] == 9
        assert mismatch["missing_recalculated_count"] == 0
        assert len(mismatch["mismatch_comparison_ids"]) == 9
        assert mismatch["raw_values_retained"] is False
        assert mismatch["formula_text_retained"] is False
        assert replacement["status"] == (
            "candidate_recalculated_anchor_set_retained_review_required"
        )
        assert replacement["candidate_replacement_anchor_set_retained"] is True
        assert replacement["replacement_anchor_set_admitted"] is False
    else:
        assert beco["spreadsheet_execution_attempted"] is False
        assert anchor_set["status"] == (
            "candidate_replacement_anchor_set_unavailable_fail_closed"
        )
        assert replacement["status"] == "replacement_anchor_set_not_available_fail_closed"

    _assert_hash_only(artifact)


def test_res006_missing_spreadsheet_executor_fails_closed(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(gate.res005006_gate.shutil, "which", lambda _name: None)

    artifact = gate.generate_res006_beco_recalculation_admission_gate(
        retained_dir=tmp_path
    )

    tooling = artifact["tooling_detection"]
    beco = artifact["beco_recalculation_gate"]
    anchor_set = artifact["candidate_replacement_anchor_set"]
    mismatch = artifact["mismatch_lineage"]
    decision = artifact["admission_decision"]

    assert tooling["tool_detection_status"] == "spreadsheet_execution_tool_missing"
    assert tooling["selected_spreadsheet_executor"] is None
    assert tooling["dependency_install_attempted"] is False
    assert tooling["network_fetch_attempted"] is False
    assert beco["gate_status"] == "blocked_fail_closed_beco_execution_tool_missing"
    assert beco["spreadsheet_execution_attempted"] is False
    assert beco["spreadsheet_recalculation_admitted"] is False
    assert anchor_set["recalculated_hash_count"] == 0
    assert anchor_set["replacement_anchor_set_admitted"] is False
    assert mismatch["recalculated_anchor_count"] == 0
    assert mismatch["missing_recalculated_count"] == 0
    assert decision["res006_narrowly_closed"] is False
    assert "neither libreoffice nor soffice" in decision["remaining_blockers"][0]

    _assert_hash_only(artifact)


def test_res006_skip_execution_records_explicit_fail_closed_path(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_res006_beco_recalculation_admission_gate(
        retained_dir=tmp_path,
        attempt_spreadsheet_execution=False,
    )

    assert artifact["tooling_detection"]["tool_detection_status"] == (
        "spreadsheet_execution_probe_skipped"
    )
    assert artifact["beco_recalculation_gate"]["gate_status"] == (
        "blocked_fail_closed_beco_execution_tool_missing"
    )
    assert artifact["candidate_replacement_anchor_set"]["status"] == (
        "candidate_replacement_anchor_set_unavailable_fail_closed"
    )
    assert artifact["replacement_path"]["candidate_replacement_anchor_set_retained"] is False
    assert artifact["admission_decision"]["res006_narrowly_closed"] is False
    assert artifact["authority_guards_all_false"] is True


def test_res006_cli_writes_gate_anchor_set_and_manifest(tmp_path: Path) -> None:
    output_path = tmp_path / "gate_cli.json"
    retained_dir = tmp_path / "retained"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res006_beco_recalculation_admission_gate.py",
            "--skip-spreadsheet-execution",
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
    assert artifact["schema_version"] == (
        "a2.res006_beco_recalculation_admission_gate.v1"
    )
    assert artifact["retained_artifact_sha256"]
    assert artifact["retained_anchor_set_sha256"]
    assert artifact["retained_manifest_sha256"]

    gate_path = retained_dir / "res006_beco_recalculation_admission_gate.json"
    anchor_path = retained_dir / "beco_recalculated_hash_anchor_set.json"
    manifest_path = retained_dir / "manifest.json"
    assert gate_path.is_file()
    assert anchor_path.is_file()
    assert manifest_path.is_file()

    retained_gate = json.loads(gate_path.read_text(encoding="utf-8"))
    anchor_set = json.loads(anchor_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert retained_gate["candidate_replacement_anchor_set_artifact"][
        "filename"
    ] == "beco_recalculated_hash_anchor_set.json"
    assert anchor_set["schema_version"] == (
        "a2.res006_beco_recalculated_hash_anchor_set.v1"
    )
    assert manifest["schema_version"] == (
        "a2.res006_beco_recalculation_admission_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "res006_beco_recalculation_admission_retained_release_blocked"
    )
    assert manifest["artifacts"][0]["artifact_key"] == (
        "res006_beco_recalculation_admission_gate"
    )
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])
    assert HEX64.fullmatch(manifest["artifacts"][1]["sha256"])
    assert manifest["authority_guards_all_false"] is True
    assert manifest["authority_guards"]["pk_authority_granted"] is False
    assert manifest["authority_guards"]["deterministic_fuze_authority_granted"] is False

    _assert_hash_only(retained_gate)
    _assert_hash_only(anchor_set)
