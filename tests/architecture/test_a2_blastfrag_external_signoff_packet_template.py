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
    a2_blastfrag_external_signoff_packet_template as template_gen,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_signoff_intake_contract as contract,
)
from tools.maintenance import a2_retained_manifest_integrity as integrity  # noqa: E402


HEX64 = re.compile(r"^[a-f0-9]{64}$")


def _walk(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for child in value.values():
            values.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk(child))
    return values


def _required_signoff_ids() -> list[str]:
    return contract.generate_signoff_intake_contract()["intake_contract_shape"][
        "required_signoff_ids"
    ]


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
    assert all(row["decision"] not in contract.ALLOWED_REVIEW_DECISIONS for row in decisions)
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

    for value in _walk(template):
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

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_external_signoff_packet_template.py",
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
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["authority_guards"].values())
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])
    assert HEX64.fullmatch(manifest["input_refs"][0]["sha256"])

    summary = integrity.check_retained_manifest_integrity(
        manifest_paths=[manifest_path]
    )
    assert summary["manifest_count"] == 1
    assert summary["missing_total"] == 0
    assert summary["sha_mismatch_total"] == 0
    assert summary["guard_true_total"] == 0
