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
    a2_blastfrag_res005_tp21_debris_admission_gate as gate,
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


def test_res005_tp21_debris_admission_gate_fails_closed_without_selected_case() -> None:
    artifact = gate.generate_tp21_debris_admission_gate()

    assert artifact["schema_version"] == "a2.res005_tp21_debris_admission_gate.v1"
    assert artifact["status"] == "blocked_fail_closed_tp21_debris_admission_gate"
    assert artifact["residual_id"] == "RES-005"

    decision = artifact["admission_decision"]
    assert decision["decision"] == "not_admitted_fail_closed"
    assert decision["narrowly_closes_res005"] is False
    assert decision["closed_residual_ids_by_this_gate"] == []
    assert decision["closed_residual_subscopes_by_this_gate"] == []
    assert decision["benchmark_consumed_for_release"] is False
    assert decision["release_grade_validated"] is False
    assert len(decision["exact_blockers"]) == 4
    assert "page/section provenance labels" in decision["exact_blockers"][0]
    assert "selected output preimage hash" in decision["exact_blockers"][1]
    assert "reviewer signoff" in decision["exact_blockers"][2]
    assert "allowed-output policy" in decision["exact_blockers"][3]


def test_res005_tp21_debris_admission_is_hash_only_and_no_raw_source_payload() -> None:
    artifact = gate.generate_tp21_debris_admission_gate()
    anchor_set = artifact["selected_debris_output_anchor_set"]

    assert HEX64.fullmatch(anchor_set["source_artifact_sha256"])
    assert HEX64.fullmatch(anchor_set["controlled_criteria_vocabulary_sha256"])
    assert HEX64.fullmatch(anchor_set["source_rights_policy_sha256"])
    assert HEX64.fullmatch(anchor_set["selected_debris_output_set_sha256"])
    assert anchor_set["selected_debris_output_hashes"] == []
    assert anchor_set["selected_debris_output_hash_count"] == 0
    assert anchor_set["selected_output_preimages_retained"] is False
    assert anchor_set["raw_tp21_source_content_retained"] is False
    assert anchor_set["source_tables_retained"] is False
    assert anchor_set["source_figures_retained"] is False
    assert anchor_set["source_numeric_values_retained"] is False
    assert anchor_set["benchmark_consumed_for_release"] is False

    reviewer_case = artifact["reviewer_selected_case_artifact"]
    assert reviewer_case["artifact_status"] == "missing_fail_closed"
    assert reviewer_case["page_section_provenance_labels_present"] is False
    assert reviewer_case["selected_output_preimage_hash_present"] is False
    assert reviewer_case["source_content_copied_to_dataset"] is False
    assert reviewer_case["source_tables_copied_to_dataset"] is False
    assert reviewer_case["source_numeric_values_copied_to_dataset"] is False

    forbidden_keys = {
        "raw_source_text",
        "source_table_payload",
        "source_table_rows",
        "document_numeric_value",
        "tp21_raw_value",
        "selected_output_raw_value",
    }
    for value in _walk(artifact):
        if isinstance(value, dict):
            assert not (forbidden_keys & set(value))

    serialized = json.dumps(artifact, ensure_ascii=False)
    assert "extracted_text" not in serialized
    assert "source_table_payload" not in serialized
    assert "source_table_rows" not in serialized
    assert "selected_output_raw_value" not in serialized


def test_res005_tp21_debris_admission_preserves_authority_guards_false() -> None:
    artifact = gate.generate_tp21_debris_admission_gate()

    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["non_authoritative_guards"].values())
    assert artifact["non_authoritative_guards"]["stock_database_authority_granted"] is False
    assert artifact["non_authoritative_guards"]["runtime_authority_granted"] is False
    assert artifact["non_authoritative_guards"]["effect_scale_authority_granted"] is False
    assert artifact["non_authoritative_guards"][
        "component_failure_probability_authority_granted"
    ] is False
    assert artifact["non_authoritative_guards"]["pk_authority_granted"] is False
    assert artifact["non_authoritative_guards"][
        "deterministic_fuze_authority_granted"
    ] is False


def test_res005_tp21_debris_admission_requirements_are_concrete() -> None:
    artifact = gate.generate_tp21_debris_admission_gate()

    selected_requirements = artifact["selected_output_requirements"]
    provenance_requirements = artifact["page_section_provenance_requirements"]

    assert len(selected_requirements) == 8
    assert all(
        row["current_status"] == "selected_output_preimage_missing"
        for row in selected_requirements
    )
    assert all(
        row["source_content_must_not_be_copied_to_dataset"]
        for row in selected_requirements
    )

    assert [row["label_key"] for row in provenance_requirements] == [
        "tp21_page_locator_label",
        "tp21_section_or_figure_locator_label",
        "reviewer_case_selection_id",
        "selected_output_preimage_sha256",
        "allowed_output_signoff_id",
    ]
    assert provenance_requirements[-1]["current_status"] == (
        "missing_allowed_output_signoff"
    )
    assert all(row["raw_source_content_retained"] is False for row in provenance_requirements)


def test_res005_tp21_debris_admission_cli_writes_retained_artifacts(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "gate_cli.json"
    retained_dir = tmp_path / "retained"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res005_tp21_debris_admission_gate.py",
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
    assert artifact["schema_version"] == "a2.res005_tp21_debris_admission_gate.v1"
    assert artifact["retained_artifact_sha256"]
    assert artifact["retained_anchor_set_sha256"]
    assert artifact["retained_manifest_sha256"]

    gate_path = retained_dir / "res005_tp21_debris_admission_gate.json"
    anchor_path = retained_dir / "selected_debris_output_anchor_set.json"
    manifest_path = retained_dir / "manifest.json"
    assert gate_path.exists()
    assert anchor_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == (
        "a2.res005_tp21_debris_admission_retained_manifest.v1"
    )
    assert manifest["status"] == "blocked_fail_closed_tp21_debris_admission_gate"
    assert HEX64.fullmatch(
        manifest["res005_tp21_debris_admission_gate_artifact"]["sha256"]
    )
    assert HEX64.fullmatch(
        manifest["selected_debris_output_anchor_set_artifact"]["sha256"]
    )
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["non_authoritative_guards"].values())
