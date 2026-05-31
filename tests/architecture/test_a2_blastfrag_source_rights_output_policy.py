from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_source_rights_output_policy as gate,
)


EXPECTED_BECO_SHA256 = (
    "82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc"
)
EXPECTED_TP20_SHA256 = (
    "293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20baad56e39fb8423f165f"
)
EXPECTED_TP21_SHA256 = (
    "84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8"
)


def test_a2_blastfrag_source_rights_output_policy_current_repo_is_blocked_release_candidate(
    tmp_path: Path,
) -> None:
    artifact = gate.write_retained_source_rights_output_policy_gate(output_dir=tmp_path)

    assert artifact["schema_version"] == "a2.source_rights_output_policy_gate.v1"
    assert artifact["status"] == (
        "blocked_release_candidate_rights_supported_policy_fail_closed"
    )
    assert artifact["review_target"] == (
        "res_001_source_rights_review_allowed_output_policy"
    )

    result = artifact["res_001_gate_result"]
    assert result["gate_result"] == "blocked"
    assert result["release_grade_satisfied"] is False
    assert result["payload_retention_complete"] is True
    assert result["payload_hashes_match"] is True
    assert result["rights_supported_by_public_distribution_statement"] is True
    assert result["release_grade_rights_reviewed"] is False
    assert result["allowed_output_policy_frozen"] is True
    assert result["allowed_output_policy_release_grade_satisfied"] is False
    assert result["comparison_outputs_admitted"] is False
    assert result["benchmark_consumption_release_grade_satisfied"] is False
    assert result["blocking_conditions"] == [
        "independent_rights_reviewer_signoff_missing",
        "allowed_output_policy_release_grade_signoff_missing",
        "selected_comparison_output_hash_manifest_missing",
        "benchmark_consumption_release_signoff_missing",
        "authority_boundary_signoff_missing",
    ]

    policy = artifact["allowed_output_policy"]
    assert policy["policy_status"] == "release_candidate_fail_closed_policy_frozen"
    assert policy["policy_frozen_by_this_gate"] is True
    assert policy["release_grade_satisfied"] is False
    assert policy["current_selected_comparison_output_hashes"] == []
    assert "retained_payload_file_sha256" in policy["allowed_hash_outputs"]
    assert "future_selected_comparison_output_sha256_only_after_reviewer_admission" in (
        policy["allowed_hash_outputs"]
    )
    assert "spreadsheet_tool_output_tables" in policy["forbidden_copy_outputs"]
    assert "comparison_outputs_without_selected_sha256_and_signoff" in policy[
        "forbidden_consume_outputs"
    ]

    by_label = {
        row["source_artifact_label"]: row
        for row in artifact["payload_rights_inventory"]
    }
    assert list(by_label) == ["TP-20 PDF", "BEC-O-V1.xlsx", "TP-21 PDF"]
    assert by_label["TP-20 PDF"]["actual_sha256"] == EXPECTED_TP20_SHA256
    assert by_label["BEC-O-V1.xlsx"]["actual_sha256"] == EXPECTED_BECO_SHA256
    assert by_label["TP-21 PDF"]["actual_sha256"] == EXPECTED_TP21_SHA256

    assert all(row["payload_exists"] for row in by_label.values())
    assert all(row["hash_matches_expected"] for row in by_label.values())
    assert all(
        row["payload_retention_status"] == "retained_hash_matched"
        for row in by_label.values()
    )
    assert all(
        row["rights_status"]
        == "public_distribution_statement_supported_rights_review_candidate"
        for row in by_label.values()
    )
    assert all(
        row["rights_supported_by_public_distribution_statement"]
        for row in by_label.values()
    )
    assert all(row["rights_release_grade_satisfied"] is False for row in by_label.values())
    assert all(row["release_consumption_allowed"] is False for row in by_label.values())
    assert all(
        row["benchmark_consumed_for_release"] is False for row in by_label.values()
    )

    assert by_label["TP-20 PDF"]["rights_statement_evidence"]["statement_id"] == (
        "distribution_statement_a_public_release_unlimited"
    )
    assert by_label["BEC-O-V1.xlsx"]["rights_statement_evidence"]["statement_id"] == (
        "distribution_statement_a_public_release_unlimited"
    )
    assert by_label["TP-21 PDF"]["rights_statement_evidence"]["statement_id"] == (
        "public_release_distribution_unlimited"
    )
    assert by_label["BEC-O-V1.xlsx"]["output_policy"][
        "benchmark_consumption_allowed"
    ] is False
    assert "spreadsheet_formulas" in by_label["BEC-O-V1.xlsx"]["output_policy"][
        "copy_forbidden_outputs"
    ]

    signoff_fields = [
        row["field"] for row in artifact["required_release_signoff_fields"]
    ]
    assert signoff_fields == [
        "rights_reviewer_identity",
        "rights_review_decision",
        "allowed_output_policy_reviewer_identity",
        "allowed_output_policy_release_grade_status",
        "selected_comparison_output_hash_manifest_sha256",
        "benchmark_consumption_signoff",
        "authority_boundary_signoff",
    ]
    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["non_authoritative_guards"].values())

    manifest = json.loads((tmp_path / gate.RETAINED_MANIFEST_FILENAME).read_text())
    assert manifest["schema_version"] == (
        "a2.source_rights_output_policy_retained_manifest.v1"
    )
    assert manifest["res_001_gate_result"]["gate_result"] == "blocked"
    assert len(manifest["source_rights_output_policy_gate"]["sha256"]) == 64
    assert not any(manifest["non_authoritative_guards"].values())


def test_a2_blastfrag_source_rights_output_policy_fails_closed_without_public_statement(
    monkeypatch,
) -> None:
    def no_statement(path: Path, content_type: str) -> dict[str, object]:
        return {
            "extraction_status": "test_no_statement",
            "statement_locator": "test",
            "statement_detected": False,
            "statement_id": "",
            "has_distribution_statement_a_label": False,
            "has_public_release_phrase": False,
            "has_unlimited_distribution_phrase": False,
        }

    monkeypatch.setattr(gate, "_extract_rights_evidence", no_statement)

    artifact = gate.generate_source_rights_output_policy_gate()

    assert artifact["status"] == (
        "blocked_public_distribution_statement_support_incomplete_fail_closed"
    )
    result = artifact["res_001_gate_result"]
    assert result["payload_retention_complete"] is True
    assert result["rights_supported_by_public_distribution_statement"] is False
    assert "public_distribution_statement_evidence_missing" in result[
        "blocking_conditions"
    ]
    assert all(
        row["rights_status"]
        == "rights_review_public_distribution_statement_not_supported_fail_closed"
        for row in artifact["payload_rights_inventory"]
    )
    assert not any(artifact["non_authoritative_guards"].values())


def test_a2_blastfrag_source_rights_output_policy_fails_closed_for_hash_mismatch(
    tmp_path: Path,
) -> None:
    bad_payload = tmp_path / "bad.pdf"
    bad_payload.write_bytes(b"not the retained source payload")
    source_manifest = {
        "package_id": gate.PACKAGE_ID,
        "schema_version": gate.SOURCE_ARTIFACT_PACK_SCHEMA_VERSION,
        "status": "test_manifest",
        "artifacts": [
            {
                "requirement_id": "PIN-BFM-TEST:bad",
                "artifact_id": "PIN-BFM-TEST",
                "source_id": "VPS-BFM-TEST",
                "source_artifact_label": "TP-20 PDF",
                "relative_path": str(bad_payload),
                "sha256": EXPECTED_TP20_SHA256,
                "benchmark_consumption_status": "not_consumed_for_stage_b_release",
            }
        ],
    }
    source_manifest_path = tmp_path / "source_artifact_pack_manifest.json"
    source_manifest_path.write_text(json.dumps(source_manifest), encoding="utf-8")

    artifact = gate.generate_source_rights_output_policy_gate(
        source_manifest_path=source_manifest_path,
        output_dir=tmp_path / "out",
    )

    assert artifact["status"] == "blocked_payload_retention_incomplete_fail_closed"
    result = artifact["res_001_gate_result"]
    assert result["payload_retention_complete"] is False
    assert result["payload_hashes_match"] is False
    assert result["rights_supported_by_public_distribution_statement"] is False
    assert "payload_retention_missing_or_hash_mismatch" in result[
        "blocking_conditions"
    ]
    row = artifact["payload_rights_inventory"][0]
    assert row["payload_exists"] is True
    assert row["hash_matches_expected"] is False
    assert row["payload_retention_status"] == "missing_or_hash_mismatch"
    assert row["rights_statement_evidence"]["extraction_status"] == (
        "payload_missing_or_hash_mismatch_fail_closed"
    )
    assert not any(artifact["non_authoritative_guards"].values())


def test_a2_blastfrag_source_rights_output_policy_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "source_rights_output_policy_gate.json"
    retained_dir = tmp_path / "retained"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_source_rights_output_policy.py",
            "--write-retained-artifacts",
            "--output-dir",
            str(retained_dir),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["status"] == (
        "blocked_release_candidate_rights_supported_policy_fail_closed"
    )
    assert artifact["res_001_gate_result"]["gate_result"] == "blocked"
    assert artifact["source_rights_output_policy_gate_sha256"]
    assert artifact["retained_manifest_sha256"]
    assert (retained_dir / gate.RIGHTS_POLICY_ARTIFACT_FILENAME).exists()
    assert (retained_dir / gate.RETAINED_MANIFEST_FILENAME).exists()
    assert not any(artifact["non_authoritative_guards"].values())
