from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_res001_release_signoff_gate as gate,
)


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_a2_blastfrag_res001_release_signoff_gate_current_repo_is_narrowly_closeable(
    tmp_path: Path,
) -> None:
    artifact = gate.write_retained_artifacts(
        output_dir=tmp_path / "retained",
        report_path=tmp_path / "validation_res001_release_signoff_gate_20260531.zh.md",
    )

    assert artifact["schema_version"] == "a2.res001_release_signoff_gate.v1"
    assert artifact["status"] == (
        "narrowly_closeable_internal_release_signoff_fail_closed_boundaries"
    )
    decision = artifact["residual_decision"]
    assert decision["gate_result"] == (
        "narrowly_closeable_by_internal_release_signoff_gate"
    )
    assert decision["residual_closeable_by_this_gate"] is True
    assert decision["closed_residual_ids_by_this_gate"] == ["RES-001"]
    assert decision["missing_required_fields"] == []
    assert decision["release_grade_legal_rights_asserted"] is False
    assert decision["legal_advice_provided"] is False
    assert "RES-002" in decision["residual_ids_not_closed_by_this_gate"]
    assert "RES-005" in decision["residual_ids_not_closed_by_this_gate"]

    checks = {row["check_id"]: row["satisfied"] for row in artifact["required_checks"]}
    assert set(checks) == set(gate.REQUIRED_CHECKS)
    assert all(checks.values())

    payload = artifact["source_payload_retention"]
    assert payload["complete"] is True
    assert payload["payload_hashes_match"] is True
    assert payload["required_payload_count"] == 3
    assert payload["retained_payload_count"] == 3
    assert all(row["payload_exists"] for row in payload["payloads"])
    assert all(row["hash_matches_expected"] for row in payload["payloads"])
    assert all(
        row["benchmark_consumed_for_release"] is False for row in payload["payloads"]
    )

    rights = artifact["rights_and_output_policy"]
    assert rights["public_distribution_support_present"] is True
    assert rights["release_grade_legal_rights_asserted"] is False
    assert rights["release_grade_legal_rights_not_asserted"] is True
    assert rights["allowed_output_policy_status"] == (
        "release_candidate_fail_closed_policy_frozen"
    )
    assert rights["allowed_output_policy_frozen_fail_closed"] is True
    assert rights["raw_payload_bodies_non_copyable"] is True
    assert rights["copy_policy_summary"] == {
        "payload_bodies": "non_copyable",
        "spreadsheet_cells_formulas_outputs": "non_copyable",
        "comparison_values": "non_copyable",
        "hashes_and_policy_metadata": "copyable_as_evidence_only",
    }

    benchmark = artifact["benchmark_and_comparison_output_policy"]
    assert benchmark["benchmark_consumption_decision"]["decision"] == (
        "explicit_release_non_consumption"
    )
    assert benchmark["benchmark_consumption_decision"]["satisfied"] is True
    assert benchmark["benchmark_consumption_decision"][
        "source_release_consumed_requirement_ids"
    ] == []
    assert benchmark["benchmark_consumption_decision"][
        "mechanism_outputs_benchmark_consumed_for_release"
    ] is False
    assert benchmark["beco_outputs_release_consumed"] is False
    assert benchmark["tp21_outputs_release_consumed"] is False
    assert benchmark[
        "beco_tp21_outputs_not_release_consumed_unless_hash_only_admitted"
    ] is True
    assert benchmark["comparison_values_not_copied"] is True
    assert benchmark["hash_only_comparison_anchor_count"] == 9
    assert benchmark["tp21_selected_debris_output_hashes_present"] is False

    provenance = artifact["provenance_identity_review_consumption"]
    assert provenance["res001_author_side_checks_present"] is True
    assert provenance["provenance_gate_result_for_res001"] == "blocked"
    assert provenance["res002_not_closed_by_this_gate"] is True

    authority = artifact["authority_boundary_signoff"]
    assert authority["signed_off_by_this_gate"] is True
    assert authority["authority_guards_all_false"] is True
    assert authority["stock_effect_component_pk_fuze_authority_all_false"] is True
    assert not any(authority["non_authoritative_guards"].values())

    gate_json = tmp_path / "retained" / gate.GATE_FILENAME
    manifest_json = tmp_path / "retained" / gate.MANIFEST_FILENAME
    report = tmp_path / "validation_res001_release_signoff_gate_20260531.zh.md"
    assert gate_json.exists()
    assert manifest_json.exists()
    assert report.exists()
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "a2.res001_release_signoff_manifest.v1"
    assert manifest["residual_decision"]["closed_residual_ids_by_this_gate"] == [
        "RES-001"
    ]
    assert manifest["res001_release_signoff_gate"]["sha256"]
    assert manifest["validation_report"]["sha256"]
    assert not any(manifest["non_authoritative_guards"].values())


def test_a2_blastfrag_res001_release_signoff_gate_fails_closed_for_incomplete_payload(
    tmp_path: Path,
) -> None:
    source_manifest = json.loads(gate.SOURCE_ARTIFACT_PACK_MANIFEST.read_text())
    source_manifest["all_payloads_exist"] = False
    source_manifest["all_payload_hashes_match"] = False
    source_manifest["source_payloads_retained"] = False
    source_manifest["retained_payload_count"] = 2
    source_manifest["artifacts"][0]["relative_path"] = str(tmp_path / "missing.pdf")
    bad_source_manifest = _write_json(tmp_path / "source_manifest.json", source_manifest)

    artifact = gate.generate_res001_release_signoff_gate(
        source_manifest_path=bad_source_manifest,
        output_dir=tmp_path / "out",
    )

    assert artifact["status"] == "failed_closed_res001_release_signoff_evidence_incomplete"
    assert artifact["residual_decision"]["residual_closeable_by_this_gate"] is False
    assert artifact["residual_decision"]["closed_residual_ids_by_this_gate"] == []
    assert artifact["residual_decision"]["missing_required_fields"] == [
        "payload_retention_complete",
        "payload_hashes_match",
    ]
    assert artifact["authority_boundary_signoff"]["signed_off_by_this_gate"] is False


def test_a2_blastfrag_res001_release_signoff_gate_fails_closed_for_raw_comparison_value(
    tmp_path: Path,
) -> None:
    mechanism = json.loads(gate.MECHANISM_HASHES.read_text())
    mechanism["beco_workbook"]["selected_comparison_hashes"][0][
        "cached_formula_value"
    ] = "must-not-copy"
    bad_mechanism = _write_json(tmp_path / "mechanism_comparison_hashes.json", mechanism)

    artifact = gate.generate_res001_release_signoff_gate(
        mechanism_hashes_path=bad_mechanism,
        output_dir=tmp_path / "out",
    )

    assert artifact["status"] == "failed_closed_res001_release_signoff_evidence_incomplete"
    assert artifact["residual_decision"]["missing_required_fields"] == [
        "comparison_values_not_copied",
    ]
    assert artifact["benchmark_and_comparison_output_policy"][
        "benchmark_consumption_decision"
    ]["raw_comparison_values_detected"] is True


def test_a2_blastfrag_res001_release_signoff_gate_fails_closed_for_authority_guard(
    tmp_path: Path,
) -> None:
    rights = json.loads(gate.SOURCE_RIGHTS_GATE.read_text())
    rights["non_authoritative_guards"]["pk_authority"] = True
    bad_rights = _write_json(tmp_path / "source_rights_output_policy_gate.json", rights)

    artifact = gate.generate_res001_release_signoff_gate(
        source_rights_gate_path=bad_rights,
        output_dir=tmp_path / "out",
    )

    assert artifact["status"] == "failed_closed_res001_release_signoff_evidence_incomplete"
    assert artifact["residual_decision"]["missing_required_fields"] == [
        "authority_guards_all_false"
    ]
    authority = artifact["authority_boundary_signoff"]
    assert authority["authority_guards_all_false"] is False
    assert authority["stock_effect_component_pk_fuze_authority_all_false"] is False
    assert authority["non_authoritative_guards"]["pk_authority"] is True


def test_a2_blastfrag_res001_release_signoff_gate_cli_writes_default_artifacts() -> None:
    result = subprocess.run(
        [sys.executable, "tools/maintenance/a2_blastfrag_res001_release_signoff_gate.py"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert result.stdout == ""
    gate_path = gate.DEFAULT_OUTPUT_DIR / gate.GATE_FILENAME
    manifest_path = gate.DEFAULT_OUTPUT_DIR / gate.MANIFEST_FILENAME
    assert gate_path.exists()
    assert manifest_path.exists()
    artifact = json.loads(gate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert artifact["residual_decision"]["gate_result"] == (
        "narrowly_closeable_by_internal_release_signoff_gate"
    )
    assert manifest["residual_decision"]["closed_residual_ids_by_this_gate"] == [
        "RES-001"
    ]
