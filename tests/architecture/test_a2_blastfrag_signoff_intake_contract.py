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
    a2_blastfrag_signoff_intake_contract as contract,
)
from tools.maintenance import a2_retained_manifest_integrity as integrity  # noqa: E402


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


def _valid_external_packet(request_sha256: str) -> dict[str, Any]:
    required_ids = contract.generate_signoff_intake_contract()["intake_contract_shape"][
        "required_signoff_ids"
    ]
    return {
        "schema_version": contract.EXPECTED_EXTERNAL_SCHEMA_VERSION,
        "package_id": contract.PACKAGE_ID,
        "signoff_packet_id": "unit-test-shape-only",
        "source_rights_signoff_request_packet_sha256": request_sha256,
        "reviewer_decisions": [
            {
                "signoff_id": signoff_id,
                "decision": "approved_for_hash_only_review",
                "reviewer_ref_sha256": "a" * 64,
                "decision_ref_sha256": "b" * 64,
                "reviewed_input_ref_sha256": request_sha256,
            }
            for signoff_id in required_ids
        ],
        "raw_content_absence": {
            field: False for field in contract.RAW_ABSENCE_FIELDS
        },
        "authority_guard_confirmation": {
            guard_id: False for guard_id in contract._authority_guards()
        },
        "benchmark_consumption_decision": "not_consumed_for_release_by_this_packet",
    }


def test_signoff_intake_contract_default_is_fail_closed_no_external_packet() -> None:
    artifact = contract.generate_signoff_intake_contract()

    assert artifact["schema_version"] == "a2.blastfrag_signoff_intake_contract.v1"
    assert artifact["contract_id"] == "TC-A2-BF-003-SIGNOFF-INTAKE-CONTRACT-20260601"
    assert artifact["status"] == (
        "retained_fail_closed_signoff_intake_contract_no_external_packet"
    )
    assert artifact["approval_granted"] is False
    assert artifact["release_grade_satisfied"] is False
    assert artifact["admission_granted"] is False
    assert artifact["benchmark_consumed_for_release"] is False
    assert artifact["fail_closed"] is True
    assert artifact["residuals_closed_by_this_contract"] == []
    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["authority_guards"].values())

    check = artifact["current_check_result"]
    assert check["candidate_packet_supplied"] is False
    assert check["intake_shape_valid"] is False
    assert check["ready_for_separate_reviewer_admission_gate"] is False
    assert check["signoff_decisions_consumed"] is False
    assert check["finding_count"] == 1
    assert check["findings"][0]["finding_id"] == "external_signoff_packet_not_supplied"

    shape = artifact["intake_contract_shape"]
    assert shape["expected_external_schema_version"] == (
        "a2.external_signoff_intake_packet.v1"
    )
    assert shape["contract_effect"] == "shape_check_only_not_approval_not_admission"
    assert shape["required_signoff_ids"] == [
        "source_rights_independent_review",
        "allowed_output_policy_release_grade_review",
        "tp21_selected_case_hash_only_allowed_output_review",
        "beco_hash_only_allowed_output_review",
        "beco_lineage_tolerance_and_replacement_review",
        "benchmark_consumption_release_decision",
        "authority_boundary_confirmation",
    ]
    assert "raw_value" in shape["forbidden_packet_keys"]
    assert "stdout" in shape["forbidden_packet_keys"]
    assert "pk_authority_granted" in shape[
        "authority_guard_confirmation_fields_must_be_false"
    ]


def test_signoff_intake_contract_valid_external_shape_is_not_approval(
    tmp_path: Path,
) -> None:
    request_sha = contract._sha256_file(
        contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
    )
    candidate_path = tmp_path / "candidate_signoff_packet.json"
    candidate_path.write_text(
        json.dumps(_valid_external_packet(request_sha), indent=2) + "\n",
        encoding="utf-8",
    )

    artifact = contract.generate_signoff_intake_contract(
        candidate_signoff_packet_path=candidate_path
    )

    assert artifact["status"] == "candidate_signoff_intake_shape_valid_not_approval"
    assert artifact["approval_granted"] is False
    assert artifact["release_grade_satisfied"] is False
    assert artifact["admission_granted"] is False
    assert artifact["fail_closed"] is True

    check = artifact["current_check_result"]
    assert check["candidate_packet_supplied"] is True
    assert check["intake_shape_valid"] is True
    assert check["ready_for_separate_reviewer_admission_gate"] is True
    assert check["signoff_decisions_consumed"] is False
    assert check["missing_signoff_ids"] == []
    assert check["unexpected_signoff_ids"] == []
    assert check["finding_count"] == 0
    assert len(check["reviewer_decision_summaries"]) == 7
    assert all(row["hash_refs_present"] for row in check["reviewer_decision_summaries"])
    assert HEX64.fullmatch(artifact["candidate_signoff_packet_ref"]["sha256"])


def test_signoff_intake_contract_rejects_raw_fields_and_authority_true(
    tmp_path: Path,
) -> None:
    request_sha = contract._sha256_file(
        contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
    )
    candidate = _valid_external_packet(request_sha)
    candidate["source_prose"] = "forbidden raw source text"
    candidate["authority_guard_confirmation"]["pk_authority_granted"] = True
    candidate["reviewer_decisions"].pop()
    candidate_path = tmp_path / "bad_candidate_signoff_packet.json"
    candidate_path.write_text(
        json.dumps(candidate, indent=2) + "\n",
        encoding="utf-8",
    )

    artifact = contract.generate_signoff_intake_contract(
        candidate_signoff_packet_path=candidate_path
    )

    assert artifact["status"] == "blocked_fail_closed_signoff_intake_shape_invalid"
    assert artifact["approval_granted"] is False
    assert artifact["authority_guards_all_false"] is True
    check = artifact["current_check_result"]
    assert check["intake_shape_valid"] is False
    assert "source_prose" in check["forbidden_key_hits"][0]
    finding_ids = {row["finding_id"] for row in check["findings"]}
    assert "forbidden_raw_or_unretained_field" in finding_ids
    assert "authority_guard_not_false" in finding_ids
    assert "missing_required_signoff_id" in finding_ids


def test_signoff_intake_contract_retains_no_raw_payload_values() -> None:
    artifact = contract.generate_signoff_intake_contract()

    forbidden_raw_keys = {
        "cell",
        "cell_range",
        "cell_value",
        "formula_text",
        "raw_output_table",
        "raw_output_value",
        "raw_selected_output_value",
        "raw_value",
        "selected_output_preimage",
        "selected_output_preimage_body",
        "source_table_rows",
        "stdout",
        "stderr",
        "temporary_workbook_copy",
    }
    for value in _walk(artifact):
        if isinstance(value, dict):
            assert not (forbidden_raw_keys & set(value))

    serialized = json.dumps(artifact, ensure_ascii=False)
    assert "forbidden raw source text" not in serialized
    assert "selected_output_raw_value" not in serialized
    assert "spreadsheet_formula_text" in serialized


def test_signoff_intake_contract_cli_writes_manifest_integrity_clean(
    tmp_path: Path,
) -> None:
    retained_dir = tmp_path / "retained"
    output_path = tmp_path / "contract_cli.json"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_signoff_intake_contract.py",
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
    output_contract = json.loads(output_path.read_text(encoding="utf-8"))
    assert HEX64.fullmatch(output_contract["retained_artifact_sha256"])
    assert HEX64.fullmatch(output_contract["retained_manifest_sha256"])

    contract_path = retained_dir / "signoff_intake_contract.json"
    manifest_path = retained_dir / "manifest.json"
    assert contract_path.is_file()
    assert manifest_path.is_file()

    retained_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert retained_contract["schema_version"] == (
        "a2.blastfrag_signoff_intake_contract.v1"
    )
    assert manifest["schema_version"] == (
        "a2.blastfrag_signoff_intake_contract_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "retained_fail_closed_signoff_intake_contract_no_external_packet"
    )
    assert manifest["approval_granted"] is False
    assert manifest["release_grade_satisfied"] is False
    assert manifest["admission_granted"] is False
    assert manifest["fail_closed"] is True
    assert manifest["candidate_packet_supplied"] is False
    assert manifest["intake_shape_valid"] is False
    assert manifest["signoff_decisions_consumed"] is False
    assert manifest["finding_count"] == 1
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["authority_guards"].values())
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])

    summary = integrity.check_retained_manifest_integrity(
        manifest_paths=[manifest_path]
    )
    assert summary["missing_total"] == 0
    assert summary["sha_mismatch_total"] == 0
    assert summary["guard_true_total"] == 0
