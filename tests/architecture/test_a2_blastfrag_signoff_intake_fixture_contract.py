from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_signoff_intake_contract as contract,
)


FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "a2_signoff_intake"
PLACEHOLDER_SHA256 = "0" * 64
VALID_FIXTURE = "valid_external_signoff_packet_shape.json"
INVALID_FIXTURE = "invalid_external_signoff_packet_raw_field.json"


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


def _required_signoff_ids() -> list[str]:
    return contract.generate_signoff_intake_contract()["intake_contract_shape"][
        "required_signoff_ids"
    ]


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
