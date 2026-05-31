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
    a2_blastfrag_res005006_benchmark_execution_admission_gate as gate,
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


def test_res005006_benchmark_execution_admission_current_repo_fail_closed(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_benchmark_execution_admission_gate(retained_dir=tmp_path)

    assert artifact["schema_version"] == (
        "a2.res005006_benchmark_execution_admission_gate.v1"
    )
    assert artifact["status"] == "partial_fail_closed_benchmark_execution_admission_gate"
    assert artifact["mechanism_comparison_hashes_input_status"] == (
        "partial_fail_closed_mechanism_comparison_hash_manifest"
    )

    summary = artifact["admission_summary"]
    assert summary["fail_closed"] is True
    assert summary["tp21_selected_debris_outputs_admitted"] is False
    assert summary["tolerance_policy_admitted"] is False
    assert summary["benchmark_consumption_admitted"] is False
    assert artifact["benchmark_consumption_decision"]["decision"] == (
        "not_consumed_fail_closed"
    )
    assert artifact["benchmark_consumption_decision"][
        "benchmark_consumed_for_release"
    ] is False
    assert artifact["benchmark_consumption_decision"]["closed_residual_ids_by_this_gate"] == []

    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["non_authoritative_guards"].values())
    assert artifact["non_authoritative_guards"]["pk_authority_granted"] is False
    assert artifact["non_authoritative_guards"][
        "deterministic_fuze_authority_granted"
    ] is False


def test_res005006_beco_execution_evidence_is_hash_only(tmp_path: Path) -> None:
    artifact = gate.generate_benchmark_execution_admission_gate(retained_dir=tmp_path)
    beco_gate = artifact["beco_spreadsheet_execution_gate"]

    assert beco_gate["residual_id"] == "RES-006"
    assert beco_gate["cached_hash_anchor_count"] == 9
    assert beco_gate["spreadsheet_recalculation_admitted"] is False

    detection = artifact["tooling_detection"]
    if detection["tool_detection_status"] == "spreadsheet_execution_tool_available":
        assert beco_gate["spreadsheet_execution_attempted"] is True
        assert beco_gate["execution_attempt"]["attempted"] is True
        assert beco_gate["execution_attempt"]["raw_values_retained"] is False
        assert beco_gate["execution_attempt"]["temporary_workbook_copy_retained"] is False
        assert beco_gate["selected_recalculated_hash_count"] == 9
        assert len(beco_gate["selected_hash_comparisons"]) == 9
        for row in beco_gate["selected_hash_comparisons"]:
            assert HEX64.fullmatch(row["cached_anchor_sha256"])
            assert HEX64.fullmatch(row["recalculated_output_sha256"])
            assert row["raw_value_disclosed"] is False
    else:
        assert beco_gate["spreadsheet_execution_attempted"] is False
        assert beco_gate["gate_status"] == "blocked_fail_closed_beco_execution_tool_missing"
        assert "missing executable/tooling blocker" in beco_gate["exact_blocker"]

    forbidden_raw_keys = {"cached_formula_value", "formula", "raw_value"}
    for value in _walk(beco_gate):
        if isinstance(value, dict):
            assert not (forbidden_raw_keys & set(value))


def test_res005006_tp21_selected_debris_requirements_fail_closed(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_benchmark_execution_admission_gate(
        retained_dir=tmp_path,
        attempt_spreadsheet_execution=False,
    )
    tp21 = artifact["tp21_debris_admission_gate"]

    assert tp21["residual_id"] == "RES-005"
    assert tp21["gate_status"] == (
        "blocked_fail_closed_tp21_selected_debris_outputs_missing"
    )
    assert tp21["selected_debris_output_hash_count"] == 0
    assert tp21["selected_debris_output_hashes_present"] is False
    assert HEX64.fullmatch(tp21["criteria_vocabulary_sha256"])
    assert tp21["source_text_copied_to_dataset"] is False
    assert tp21["source_tables_copied_to_dataset"] is False
    assert "reviewer-selected TP-21 debris comparison case artifacts" in tp21[
        "exact_blocker"
    ]

    requirements = tp21["selected_output_requirements"]
    assert len(requirements) == 8
    assert all(
        row["current_status"] == "selected_debris_output_hash_missing"
        for row in requirements
    )
    assert all(row["source_text_must_not_be_copied_to_dataset"] for row in requirements)

    serialized = json.dumps(tp21, ensure_ascii=False)
    assert "extracted_text" not in serialized
    assert "source_table_payload" not in serialized
    assert "source_table_rows" not in serialized


def test_res005006_missing_spreadsheet_executor_reports_exact_blocker(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(gate.shutil, "which", lambda _name: None)

    artifact = gate.generate_benchmark_execution_admission_gate(retained_dir=tmp_path)
    tooling = artifact["tooling_detection"]
    beco = artifact["beco_spreadsheet_execution_gate"]

    assert tooling["tool_detection_status"] == "spreadsheet_execution_tool_missing"
    assert tooling["selected_spreadsheet_executor"] is None
    assert tooling["dependency_install_attempted"] is False
    assert tooling["network_fetch_attempted"] is False
    assert tooling["missing_execution_tooling_blockers"] == [
        "missing executable/tooling blocker: neither libreoffice nor soffice "
        "was found as a working headless spreadsheet execution tool"
    ]

    assert beco["gate_status"] == "blocked_fail_closed_beco_execution_tool_missing"
    assert beco["spreadsheet_execution_attempted"] is False
    assert beco["spreadsheet_recalculation_admitted"] is False
    assert beco["exact_blocker"] == tooling["missing_execution_tooling_blockers"][0]


def test_res005006_cli_writes_retained_gate_and_manifest(tmp_path: Path) -> None:
    output_path = tmp_path / "gate_cli.json"
    retained_dir = tmp_path / "retained"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res005006_benchmark_execution_admission_gate.py",
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
        "a2.res005006_benchmark_execution_admission_gate.v1"
    )
    assert artifact["retained_artifact_sha256"]
    assert artifact["retained_manifest_sha256"]
    assert (retained_dir / "benchmark_execution_admission_gate.json").exists()
    assert (retained_dir / "manifest.json").exists()

    manifest = json.loads((retained_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == (
        "a2.res005006_benchmark_execution_admission_retained_manifest.v1"
    )
    assert manifest["status"] == "partial_fail_closed_benchmark_execution_admission_gate"
    assert HEX64.fullmatch(
        manifest["benchmark_execution_admission_gate_artifact"]["sha256"]
    )
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["non_authoritative_guards"].values())
