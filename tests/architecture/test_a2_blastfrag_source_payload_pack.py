from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_source_payload_pack as pack  # noqa: E402


EXPECTED_BECO_SHA256 = (
    "82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc"
)
EXPECTED_TP20_SHA256 = (
    "293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20baad56e39fb8423f165f"
)
EXPECTED_TP21_SHA256 = (
    "84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8"
)


def test_a2_blastfrag_source_payload_pack_current_repo_is_partial(
    tmp_path: Path,
) -> None:
    artifact = pack.write_source_payload_pack(output_dir=tmp_path)

    assert artifact["schema_version"] == "a2.source_payload_pack.v1"
    assert artifact["status"] == "partial_payloads_retained_release_review_blocked"
    assert artifact["residual_gate_results"] == {
        "RES-001": "blocked",
        "RES-002": "blocked",
    }
    assert artifact["res_001_gate_result"]["gate_result"] == "blocked"
    assert artifact["source_payload_pack_decision"][
        "source_payload_pack_closed"
    ] is False
    assert artifact["source_payload_pack_decision"][
        "source_payload_pack_partial"
    ] is True
    assert artifact["source_payload_pack_decision"]["required_payload_count"] == 3
    assert artifact["source_payload_pack_decision"]["retained_payload_count"] == 3
    assert artifact["source_payload_pack_decision"]["missing_payload_count"] == 0
    assert artifact["source_payload_pack_decision"]["all_required_payloads_retained"] is True
    assert artifact["source_payload_pack_decision"]["all_retained_payload_hashes_match"] is True
    assert artifact["source_payload_pack_decision"]["release_grade_rights_reviewed"] is False

    retained = artifact["retained_payload_inventory"]
    retained_by_label = {row["source_artifact_label"]: row for row in retained}
    assert list(retained_by_label) == ["TP-20 PDF", "BEC-O-V1.xlsx", "TP-21 PDF"]
    assert retained_by_label["TP-20 PDF"]["actual_sha256"] == EXPECTED_TP20_SHA256
    assert retained_by_label["BEC-O-V1.xlsx"]["actual_sha256"] == EXPECTED_BECO_SHA256
    assert retained_by_label["TP-21 PDF"]["actual_sha256"] == EXPECTED_TP21_SHA256
    assert all(row["hash_matches_expected"] is True for row in retained)
    assert all(
        row["rights_status"]
        == "official_public_candidate_only_rights_not_release_reviewed"
        for row in retained
    )
    assert all(row["benchmark_consumed_for_release"] is False for row in retained)
    assert artifact["missing_payloads"] == []

    policy = artifact["rights_allowed_output_policy_status"]
    assert policy["rights_review_status"] == (
        "public_distribution_statement_supported_candidate_not_signed_off"
    )
    assert policy["rights_release_grade_satisfied"] is False
    assert policy["allowed_output_policy_status"] == (
        "release_candidate_fail_closed_policy_frozen"
    )
    assert policy["allowed_output_policy_frozen"] is True
    assert policy["candidate_public_distribution_supported"] is True
    assert policy["allowed_output_release_grade_satisfied"] is False

    benchmark = artifact["benchmark_consumption_trace"]
    assert benchmark["explicit_non_consumed_artifact_ids"] == [
        "PIN-BFM-001",
        "PIN-BFM-002",
    ]
    assert benchmark["release_consumed_artifact_ids"] == []
    assert benchmark["benchmark_consumption_release_grade_satisfied"] is False

    comparison = artifact["comparison_output_hash_status"]
    assert comparison["comparison_output_hash_status"] == (
        "partial_hash_manifest_present_release_review_blocked"
    )
    assert comparison["selected_beco_cached_output_hash_count"] == 9
    assert len(comparison["selected_comparison_output_hashes"]) == 9
    assert all(
        row["comparison_hash_is_calibration"] is False
        for row in comparison["selected_comparison_output_hashes"]
    )
    assert comparison["benchmark_consumed_for_release"] is False
    assert comparison["comparison_output_release_grade_satisfied"] is False

    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["non_authoritative_guards"].values())

    retained_beco = tmp_path / "payloads" / "BEC-O-V1.xlsx"
    assert retained_beco.exists()
    assert pack._sha256_file(retained_beco) == EXPECTED_BECO_SHA256
    retained_tp20 = tmp_path / "payloads" / "TP-20.pdf"
    retained_tp21 = tmp_path / "payloads" / "TP-21.pdf"
    assert retained_tp20.exists()
    assert retained_tp21.exists()
    assert pack._sha256_file(retained_tp20) == EXPECTED_TP20_SHA256
    assert pack._sha256_file(retained_tp21) == EXPECTED_TP21_SHA256

    source_manifest = json.loads(
        (tmp_path / pack.SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert source_manifest["schema_version"] == (
        "a2.provenance_identity_retained_source_artifact_pack.v1"
    )
    assert source_manifest["status"] == "partial_payloads_retained_release_review_blocked"
    assert source_manifest["all_payloads_exist"] is True
    assert source_manifest["all_payload_hashes_match"] is True
    assert source_manifest["rights_review_status"] == (
        "public_distribution_statement_supported_candidate_not_signed_off"
    )
    assert source_manifest["allowed_output_policy_status"] == (
        "release_candidate_fail_closed_policy_frozen"
    )
    assert source_manifest["comparison_output_hash_status"] == (
        "partial_hash_manifest_present_release_review_blocked"
    )
    assert not any(source_manifest["non_authoritative_guards"].values())


def test_a2_blastfrag_source_payload_pack_fails_closed_when_payloads_absent(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(pack, "_discover_payload_candidates", lambda **_: [])

    artifact = pack.generate_source_payload_pack(
        output_dir=tmp_path,
        copy_available_payloads=True,
    )

    assert artifact["status"] == "blocked_missing_required_source_payloads"
    assert artifact["source_payload_pack_decision"]["source_payload_pack_blocked"] is True
    assert artifact["source_payload_pack_decision"]["retained_payload_count"] == 0
    assert artifact["source_payload_pack_decision"]["missing_payload_count"] == 3
    assert artifact["rights_allowed_output_policy_status"]["rights_review_status"] == (
        "missing_payload_rights_review"
    )
    assert "required_source_payloads_missing_or_mismatched" in artifact[
        "res_001_gate_result"
    ]["blocking_conditions"]
    assert artifact["res_001_gate_result"]["gate_result"] == "blocked"
    assert not any(artifact["non_authoritative_guards"].values())


def test_a2_blastfrag_source_payload_pack_rejects_hash_mismatch(
    tmp_path: Path,
) -> None:
    wrong_beco = tmp_path / "payloads" / "BEC-O-V1.xlsx"
    wrong_beco.parent.mkdir(parents=True)
    wrong_beco.write_bytes(b"not the retained spreadsheet payload")

    artifact = pack.generate_source_payload_pack(
        output_dir=tmp_path,
        copy_available_payloads=False,
    )

    beco_rows = [
        row
        for row in artifact["all_payload_inventory"]
        if row["source_artifact_label"] == "BEC-O-V1.xlsx"
    ]
    assert len(beco_rows) == 1
    assert beco_rows[0]["payload_exists"] is True
    assert beco_rows[0]["hash_matches_expected"] is False
    assert beco_rows[0]["retained_for_pack"] is False

    missing_beco = [
        row
        for row in artifact["missing_payloads"]
        if row["source_artifact_label"] == "BEC-O-V1.xlsx"
    ]
    assert len(missing_beco) == 1
    assert missing_beco[0]["missing_reason"] == "payload_sha256_mismatch"
    assert artifact["status"] in {
        "blocked_missing_required_source_payloads",
        "partial_non_authoritative_source_payload_pack",
    }
    assert artifact["res_001_gate_result"]["gate_result"] == "blocked"


def test_a2_blastfrag_source_payload_pack_cli_writes_retained_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "cli_source_payload_pack.json"
    retained_dir = tmp_path / "retained"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_source_payload_pack.py",
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
    assert artifact["status"] == "partial_payloads_retained_release_review_blocked"
    assert [
        row["source_artifact_label"]
        for row in artifact["retained_payload_inventory"]
    ] == ["TP-20 PDF", "BEC-O-V1.xlsx", "TP-21 PDF"]
    assert artifact["missing_payloads"] == []
    assert artifact["source_artifact_pack_manifest_sha256"]
    assert artifact["retained_manifest_sha256"]
    assert (retained_dir / "source_payload_pack.json").exists()
    assert (retained_dir / "source_artifact_pack_manifest.json").exists()
    assert (retained_dir / "manifest.json").exists()
    assert not any(artifact["non_authoritative_guards"].values())
