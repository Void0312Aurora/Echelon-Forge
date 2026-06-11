from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path
from tests.architecture.damage_model.helpers import (
    HEX64,
    assert_authority_guards_false,
    assert_retained_manifest_clean,
    run_maintenance_cli,
    walk_payload,
)

ensure_repo_root_on_sys_path()

from tools.maintenance.external_signoff_evidence import (  # noqa: E402
    intake_contract as contract,
    packet_template as template_gen,
)
from tools.maintenance.retained_artifacts import manifest_integrity as integrity  # noqa: E402


FIXTURE_DIR = (
    REPO_ROOT
    / "tests"
    / "architecture"
    / "damage_model"
    / "fixtures"
    / "external_signoff_intake"
)
PLACEHOLDER_SHA256 = "0" * 64
VALID_FIXTURE = "valid_external_signoff_packet_shape.json"
INVALID_FIXTURE = "invalid_external_signoff_packet_raw_field.json"


def _required_signoff_ids() -> list[str]:
    return contract.generate_signoff_intake_contract()["intake_contract_shape"][
        "required_signoff_ids"
    ]


def _valid_external_packet(request_sha256: str) -> dict[str, Any]:
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
            for signoff_id in _required_signoff_ids()
        ],
        "raw_content_absence": {field: False for field in contract.RAW_ABSENCE_FIELDS},
        "authority_guard_confirmation": {
            guard_id: False for guard_id in contract._authority_guards()
        },
        "benchmark_consumption_decision": "not_consumed_for_release_by_this_packet",
    }


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _write_candidate_with_current_source_sha(
    *,
    fixture_name: str,
    tmp_path: Path,
) -> tuple[Path, dict[str, Any], str]:
    payload = _load_fixture(fixture_name)
    request_sha256 = contract._sha256_file(
        contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
    )

    assert payload["source_rights_signoff_request_packet_sha256"] == PLACEHOLDER_SHA256
    payload["source_rights_signoff_request_packet_sha256"] = request_sha256
    for row in payload["reviewer_decisions"]:
        assert row["reviewed_input_ref_sha256"] == PLACEHOLDER_SHA256
        row["reviewed_input_ref_sha256"] = request_sha256

    candidate_path = tmp_path / fixture_name
    candidate_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return candidate_path, payload, request_sha256


def _assert_no_res005_res006_closure(artifact: dict[str, Any]) -> None:
    assert artifact["residuals_closed_by_this_contract"] == []
    residual_text = json.dumps(
        artifact["residuals_closed_by_this_contract"],
        sort_keys=True,
    )
    assert "RES005" not in residual_text
    assert "RES006" not in residual_text
    assert "RES-005" not in residual_text
    assert "RES-006" not in residual_text


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
    for value in walk_payload(artifact):
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

    result = run_maintenance_cli(
        "damage_model_external_evidence.py",
        "intake-contract",
        "--retained-dir",
        retained_dir,
        "--output",
        output_path,
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
    assert_authority_guards_false(manifest)
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])

    assert_retained_manifest_clean(integrity, manifest_path)


def test_valid_external_fixture_shape_passes_without_granting_approval(
    tmp_path: Path,
) -> None:
    candidate_path, payload, request_sha256 = _write_candidate_with_current_source_sha(
        fixture_name=VALID_FIXTURE,
        tmp_path=tmp_path,
    )

    required_ids = _required_signoff_ids()
    assert len(required_ids) == 7
    assert [row["signoff_id"] for row in payload["reviewer_decisions"]] == required_ids
    assert set(payload["raw_content_absence"]) == set(contract.RAW_ABSENCE_FIELDS)
    assert all(value is False for value in payload["raw_content_absence"].values())
    assert set(payload["authority_guard_confirmation"]) == set(
        contract._authority_guards()
    )
    assert all(
        value is False for value in payload["authority_guard_confirmation"].values()
    )
    assert payload["benchmark_consumption_decision"] == (
        "not_consumed_for_release_by_this_packet"
    )
    assert {
        row["reviewed_input_ref_sha256"] for row in payload["reviewer_decisions"]
    } == {request_sha256}

    artifact = contract.generate_signoff_intake_contract(
        candidate_signoff_packet_path=candidate_path
    )

    assert artifact["status"] == "candidate_signoff_intake_shape_valid_not_approval"
    assert artifact["approval_granted"] is False
    assert artifact["admission_granted"] is False
    assert artifact["release_grade_satisfied"] is False
    assert artifact["benchmark_consumed_for_release"] is False
    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["authority_guards"].values())
    _assert_no_res005_res006_closure(artifact)

    check = artifact["current_check_result"]
    assert check["candidate_packet_supplied"] is True
    assert check["intake_shape_valid"] is True
    assert check["ready_for_separate_reviewer_admission_gate"] is True
    assert check["signoff_decisions_consumed"] is False
    assert check["missing_signoff_ids"] == []
    assert check["unexpected_signoff_ids"] == []
    assert check["duplicate_signoff_ids"] == []
    assert check["forbidden_key_hits"] == []
    assert check["finding_count"] == 0


def test_invalid_external_fixture_raw_field_and_authority_true_fail_closed(
    tmp_path: Path,
) -> None:
    candidate_path, payload, _request_sha256 = _write_candidate_with_current_source_sha(
        fixture_name=INVALID_FIXTURE,
        tmp_path=tmp_path,
    )

    assert payload["raw_value"] is None
    assert payload["authority_guard_confirmation"]["pk_authority_granted"] is True
    assert [row["signoff_id"] for row in payload["reviewer_decisions"]] == (
        _required_signoff_ids()
    )

    artifact = contract.generate_signoff_intake_contract(
        candidate_signoff_packet_path=candidate_path
    )

    assert artifact["status"] == "blocked_fail_closed_signoff_intake_shape_invalid"
    assert artifact["approval_granted"] is False
    assert artifact["admission_granted"] is False
    assert artifact["release_grade_satisfied"] is False
    assert artifact["benchmark_consumed_for_release"] is False
    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["authority_guards"].values())
    _assert_no_res005_res006_closure(artifact)

    check = artifact["current_check_result"]
    assert check["candidate_packet_supplied"] is True
    assert check["intake_shape_valid"] is False
    assert check["ready_for_separate_reviewer_admission_gate"] is False
    assert check["signoff_decisions_consumed"] is False
    assert check["missing_signoff_ids"] == []
    assert check["unexpected_signoff_ids"] == []
    assert check["duplicate_signoff_ids"] == []
    assert "$.raw_value" in check["forbidden_key_hits"]

    finding_ids = {row["finding_id"] for row in check["findings"]}
    assert "forbidden_raw_or_unretained_field" in finding_ids
    assert "authority_guard_not_false" in finding_ids
    assert any("pk_authority_granted" in row["detail"] for row in check["findings"])


def test_external_signoff_template_reuses_intake_contract_shape() -> None:
    template = template_gen.generate_external_signoff_packet_template()
    source_sha256 = contract._sha256_file(
        contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
    )
    required_signoff_ids = _required_signoff_ids()

    assert template["schema_version"] == contract.EXPECTED_EXTERNAL_SCHEMA_VERSION
    assert template["template_schema_version"] == (
        "a2.external_signoff_packet_template.v1"
    )
    assert template["package_id"] == contract.PACKAGE_ID
    assert template["source_rights_signoff_request_packet_sha256"] == source_sha256
    assert template["approval_granted"] is False
    assert template["release_grade_satisfied"] is False
    assert template["template_only"] is True
    assert template["admission_granted"] is False
    assert template["signoff_decisions_consumed"] is False
    assert template["benchmark_consumed_for_release"] is False
    assert template["benchmark_consumption_decision"] == (
        "not_consumed_for_release_by_this_packet"
    )

    assert template["raw_content_absence"] == {
        field: False for field in contract.RAW_ABSENCE_FIELDS
    }
    assert template["authority_guard_confirmation"] == contract._authority_guards()
    assert not any(template["authority_guard_confirmation"].values())

    decisions = template["reviewer_decisions"]
    assert [row["signoff_id"] for row in decisions] == required_signoff_ids
    assert all(row["template_only"] is True for row in decisions)
    assert all(row["placeholder_ref_only"] is True for row in decisions)
    assert all(row["approval_granted"] is False for row in decisions)
    assert all(row["admission_granted"] is False for row in decisions)
    assert all(row["signoff_decisions_consumed"] is False for row in decisions)
    assert all(
        row["decision"] not in contract.ALLOWED_REVIEW_DECISIONS for row in decisions
    )
    assert all(row["reviewed_input_ref_sha256"] == source_sha256 for row in decisions)
    assert all(not HEX64.fullmatch(row["reviewer_ref_sha256"]) for row in decisions)
    assert all(not HEX64.fullmatch(row["decision_ref_sha256"]) for row in decisions)

    schema = template["json_schema"]
    assert schema["properties"]["schema_version"]["const"] == (
        contract.EXPECTED_EXTERNAL_SCHEMA_VERSION
    )
    assert schema["properties"]["package_id"]["const"] == contract.PACKAGE_ID
    assert schema["properties"]["source_rights_signoff_request_packet_sha256"][
        "const"
    ] == source_sha256
    assert set(schema["required"]) == {
        "schema_version",
        "package_id",
        "signoff_packet_id",
        "source_rights_signoff_request_packet_sha256",
        "reviewer_decisions",
        "raw_content_absence",
        "authority_guard_confirmation",
        "benchmark_consumption_decision",
    }


def test_external_signoff_template_is_not_shape_valid_until_reviewer_fills_refs(
    tmp_path: Path,
) -> None:
    template = template_gen.generate_external_signoff_packet_template()
    candidate_path = tmp_path / "external_signoff_packet_template.json"
    candidate_path.write_text(
        json.dumps(template, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    artifact = contract.generate_signoff_intake_contract(
        candidate_signoff_packet_path=candidate_path,
    )

    assert artifact["status"] == "blocked_fail_closed_signoff_intake_shape_invalid"
    assert artifact["approval_granted"] is False
    assert artifact["admission_granted"] is False
    assert artifact["fail_closed"] is True
    check = artifact["current_check_result"]
    assert check["candidate_packet_supplied"] is True
    assert check["intake_shape_valid"] is False
    assert check["signoff_decisions_consumed"] is False
    assert check["missing_signoff_ids"] == []
    assert check["unexpected_signoff_ids"] == []
    finding_ids = {row["finding_id"] for row in check["findings"]}
    assert "unsupported_review_decision" in finding_ids
    assert "decision_hash_ref_missing" in finding_ids


def test_external_signoff_template_retains_no_forbidden_packet_keys() -> None:
    template = template_gen.generate_external_signoff_packet_template()
    forbidden_keys = contract.FORBIDDEN_PACKET_KEYS

    for value in walk_payload(template):
        if isinstance(value, dict):
            assert not (forbidden_keys & set(value))

    serialized = json.dumps(template, ensure_ascii=False, sort_keys=True)
    assert "TP-21" not in serialized
    assert "BEC-O" not in serialized
    assert '"stdout"' not in serialized
    assert '"stderr"' not in serialized


def test_external_signoff_template_cli_writes_clean_retained_manifest(
    tmp_path: Path,
) -> None:
    retained_dir = tmp_path / "external_signoff_packet_template"
    output_path = tmp_path / "template_copy.json"

    result = run_maintenance_cli(
        "damage_model_external_evidence.py",
        "packet-template",
        "--retained-dir",
        retained_dir,
        "--output",
        output_path,
    )

    assert result.stdout == ""
    assert output_path.is_file()

    template_path = retained_dir / "external_signoff_packet_template.json"
    manifest_path = retained_dir / "manifest.json"
    assert template_path.is_file()
    assert manifest_path.is_file()

    retained_template = json.loads(template_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert retained_template["template_only"] is True
    assert retained_template["approval_granted"] is False
    assert retained_template["admission_granted"] is False
    assert retained_template["signoff_decisions_consumed"] is False
    assert manifest["schema_version"] == (
        "a2.external_signoff_packet_template_retained_manifest.v1"
    )
    assert manifest["approval_granted"] is False
    assert manifest["release_grade_satisfied"] is False
    assert manifest["template_only"] is True
    assert manifest["admission_granted"] is False
    assert manifest["signoff_decisions_consumed"] is False
    assert manifest["benchmark_consumed_for_release"] is False
    assert_authority_guards_false(manifest)
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])
    assert HEX64.fullmatch(manifest["input_refs"][0]["sha256"])

    summary = assert_retained_manifest_clean(integrity, manifest_path)
    assert summary["manifest_count"] == 1
