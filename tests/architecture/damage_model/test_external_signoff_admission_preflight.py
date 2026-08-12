from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path
from tests.architecture.damage_model.helpers import (
  HEX64,
  assert_authority_guards_false,
  assert_retained_manifest_clean,
  run_maintenance_cli_in_process,
  walk_payload,
)

ensure_repo_root_on_sys_path()

pytestmark = pytest.mark.governance_audit


def _valid_external_packet(request_sha256: str) -> dict[str, Any]:
  from tools.maintenance.external_signoff_evidence import intake_contract as contract

  required_ids = contract.generate_signoff_intake_contract()["intake_contract_shape"][
    "required_signoff_ids"
  ]
  return {
    "schema_version": contract.EXPECTED_EXTERNAL_SCHEMA_VERSION,
    "package_id": contract.PACKAGE_ID,
    "signoff_packet_id": "unit-test-preflight-shape-only",
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


def test_signoff_admission_preflight_default_fails_closed_no_external_packet() -> None:
  from tools.maintenance.external_signoff_evidence import admission_preflight as preflight

  artifact = preflight.generate_signoff_admission_preflight()

  assert artifact["schema_version"] == "a2.blastfrag_signoff_admission_preflight.v1"
  assert artifact["preflight_id"] == (
    "TC-A2-BF-003-SIGNOFF-INTAKE-NEXT-C-ADMISSION-PREFLIGHT-20260601"
  )
  assert artifact["status"] == (
    "retained_fail_closed_signoff_admission_preflight_no_external_packet"
  )
  assert artifact["packet_type"] == (
    "signoff_admission_preflight_packet_not_admission_gate"
  )
  assert artifact["ready_for_admission_gate"] is False
  assert artifact["ready_for_res005_admission_gate"] is False
  assert artifact["ready_for_res006_admission_gate"] is False
  assert artifact["approval_granted"] is False
  assert artifact["release_grade_satisfied"] is False
  assert artifact["admission_granted"] is False
  assert artifact["signoff_decisions_consumed"] is False
  assert artifact["residuals_closed_by_this_preflight"] == []
  assert artifact["fail_closed"] is True
  assert artifact["not_admission_gate"] is True
  assert artifact["authority_guards_all_false"] is True
  assert not any(artifact["authority_guards"].values())

  refs = {row["artifact_key"]: row for row in artifact["input_refs"]}
  assert refs["signoff_intake_contract"]["present"] is True
  assert refs["signoff_intake_contract"]["schema_version"] == (
    "a2.blastfrag_signoff_intake_contract.v1"
  )
  assert HEX64.fullmatch(refs["signoff_intake_contract"]["sha256"])

  shape = artifact["shape_check_result"]
  assert shape["candidate_packet_supplied"] is False
  assert shape["intake_shape_valid"] is False
  assert shape["signoff_decisions_consumed"] is False
  assert artifact["preflight_blocker_count"] == 1
  assert artifact["preflight_blockers"][0]["blocker_id"] == (
    "external_signoff_packet_not_supplied"
  )

  for path in artifact["admission_paths"]:
    assert path["ready_for_admission_gate"] is False
    assert path["approval_granted_by_this_preflight"] is False
    assert path["admission_granted_by_this_preflight"] is False
    assert path["residual_closed_by_this_preflight"] is False


def test_signoff_admission_preflight_valid_external_shape_is_ready_only(
  tmp_path: Path,
) -> None:
  from tools.maintenance.external_signoff_evidence import (
    admission_preflight as preflight,
    intake_contract as contract,
  )

  request_sha = contract._sha256_file(
    contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
  )
  candidate_path = tmp_path / "candidate_signoff_packet.json"
  candidate_path.write_text(
    json.dumps(_valid_external_packet(request_sha), indent=2) + "\n",
    encoding="utf-8",
  )

  artifact = preflight.generate_signoff_admission_preflight(
    candidate_signoff_packet_path=candidate_path
  )

  assert artifact["status"] == (
    "preflight_ready_for_res005_res006_admission_gate_shape_only_not_approval"
  )
  assert artifact["ready_for_admission_gate"] is True
  assert artifact["ready_for_res005_admission_gate"] is True
  assert artifact["ready_for_res006_admission_gate"] is True
  assert artifact["approval_granted"] is False
  assert artifact["release_grade_satisfied"] is False
  assert artifact["admission_granted"] is False
  assert artifact["signoff_decisions_consumed"] is False
  assert artifact["residuals_closed_by_this_preflight"] == []
  assert artifact["benchmark_consumed_for_release"] is False
  assert artifact["authority_guards_all_false"] is True
  assert not any(artifact["authority_guards"].values())

  shape = artifact["shape_check_result"]
  assert shape["candidate_packet_supplied"] is True
  assert shape["intake_shape_valid"] is True
  assert shape["ready_for_separate_reviewer_admission_gate"] is True
  assert shape["signoff_decisions_consumed"] is False
  assert shape["finding_count"] == 0
  assert artifact["preflight_blockers"] == []
  assert HEX64.fullmatch(artifact["candidate_signoff_packet_ref"]["sha256"])


def test_signoff_admission_preflight_rejects_invalid_shape_without_copying_raw(
  tmp_path: Path,
) -> None:
  from tools.maintenance.external_signoff_evidence import (
    admission_preflight as preflight,
    intake_contract as contract,
  )

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

  artifact = preflight.generate_signoff_admission_preflight(
    candidate_signoff_packet_path=candidate_path
  )

  assert artifact["status"] == (
    "blocked_fail_closed_signoff_admission_preflight_shape_invalid"
  )
  assert artifact["ready_for_admission_gate"] is False
  assert artifact["approval_granted"] is False
  assert artifact["admission_granted"] is False
  assert artifact["signoff_decisions_consumed"] is False
  assert artifact["authority_guards_all_false"] is True

  shape = artifact["shape_check_result"]
  assert shape["intake_shape_valid"] is False
  assert "source_prose" in shape["forbidden_key_hits"][0]
  finding_ids = {row["source_finding_id"] for row in artifact["preflight_blockers"]}
  assert "forbidden_raw_or_unretained_field" in finding_ids
  assert "authority_guard_not_false" in finding_ids
  assert "missing_required_signoff_id" in finding_ids

  forbidden_raw_keys = {
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
    "workbook_copy",
  }
  for value in walk_payload(artifact):
    if isinstance(value, dict):
      assert not (forbidden_raw_keys & set(value))

  serialized = json.dumps(artifact, ensure_ascii=False)
  assert "forbidden raw source text" not in serialized


def test_signoff_admission_preflight_cli_writes_manifest_integrity_clean(
  tmp_path: Path,
) -> None:
  from tools.maintenance.retained_artifacts import manifest_integrity as integrity

  retained_dir = tmp_path / "retained"
  output_path = tmp_path / "preflight_cli.json"

  result = run_maintenance_cli_in_process(
    "damage_model.py external-evidence",
    "admission-preflight",
    "--retained-dir",
    retained_dir,
    "--output",
    output_path,
  )

  assert result.stdout == ""
  output_packet = json.loads(output_path.read_text(encoding="utf-8"))
  assert HEX64.fullmatch(output_packet["retained_artifact_sha256"])
  assert HEX64.fullmatch(output_packet["retained_manifest_sha256"])

  preflight_path = retained_dir / "signoff_admission_preflight_packet.json"
  manifest_path = retained_dir / "manifest.json"
  assert preflight_path.is_file()
  assert manifest_path.is_file()

  retained_preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert retained_preflight["schema_version"] == (
    "a2.blastfrag_signoff_admission_preflight.v1"
  )
  assert manifest["schema_version"] == (
    "a2.blastfrag_signoff_admission_preflight_retained_manifest.v1"
  )
  assert manifest["status"] == (
    "retained_fail_closed_signoff_admission_preflight_no_external_packet"
  )
  assert manifest["approval_granted"] is False
  assert manifest["release_grade_satisfied"] is False
  assert manifest["admission_granted"] is False
  assert manifest["ready_for_admission_gate"] is False
  assert manifest["signoff_decisions_consumed"] is False
  assert manifest["residuals_closed_by_this_preflight"] == []
  assert manifest["fail_closed"] is True
  assert manifest["not_admission_gate"] is True
  assert manifest["candidate_packet_supplied"] is False
  assert manifest["intake_shape_valid"] is False
  assert manifest["preflight_blocker_count"] == 1
  assert_authority_guards_false(manifest)
  assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])

  assert_retained_manifest_clean(integrity, manifest_path)
