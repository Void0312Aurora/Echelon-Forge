from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.architecture.damage_model.helpers import (
  assert_authority_guards_false,
  assert_hex64,
  assert_no_keys_anywhere,
  assert_retained_manifest_clean,
  run_maintenance_cli,
)
from tests.architecture.helpers import ensure_repo_root_on_sys_path, read_json

ensure_repo_root_on_sys_path()

from tools.maintenance.benchmark_evidence import ( # noqa: E402
  spreadsheet_lineage_tolerance_packet as lineage_packet,
  spreadsheet_recalculation_admission as recalculation_gate,
  spreadsheet_replacement_tolerance as replacement_gate,
)
from tools.maintenance.retained_artifacts import manifest_integrity # noqa: E402


def _assert_recalculation_hash_only(payload: dict[str, Any]) -> None:
  forbidden_raw_keys = {
    "cached_formula_value",
    "formula",
    "raw_value",
    "raw_output_value",
    "source_table_payload",
    "source_table_rows",
  }
  assert_no_keys_anywhere(payload, forbidden_raw_keys)


def _assert_no_raw_or_row_level_outputs(payload: dict[str, Any]) -> None:
  forbidden_keys = {
    "cached_anchor_sha256",
    "cached_formula_value",
    "cached_hashes",
    "cell",
    "command_result",
    "comparison_output_sha256",
    "formula",
    "formula_sha256",
    "hash_only_comparison_rows",
    "raw_output_table",
    "raw_output_tables",
    "raw_output_value",
    "raw_value",
    "recalculated_output_sha256",
    "selected_hash_comparisons",
    "selected_recalculated_hashes",
    "source_table_payload",
    "source_table_rows",
    "stderr",
    "stdout",
    "temporary_workbook_copy",
  }
  assert_no_keys_anywhere(payload, forbidden_keys)


def _assert_hash_ref_label_only(payload: dict[str, Any]) -> None:
  forbidden_raw_keys = {
    "cached_formula_value",
    "command_result",
    "formula",
    "raw_output_table",
    "raw_output_tables",
    "raw_output_value",
    "raw_value",
    "source_table_payload",
    "source_table_rows",
    "stderr",
    "stdout",
    "temporary_workbook_copy",
  }
  assert_no_keys_anywhere(payload, forbidden_raw_keys)


@pytest.fixture(scope="module")
def recalculation_gate_artifact(
  tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, Any]:
  return recalculation_gate.generate_res006_beco_recalculation_admission_gate(
    retained_dir=tmp_path_factory.mktemp("recalculation_gate")
  )


@pytest.fixture(scope="module")
def lineage_tolerance_packet_artifact(
  tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, Any]:
  return lineage_packet.generate_res006_beco_lineage_tolerance_review_packet(
    retained_dir=tmp_path_factory.mktemp("lineage_tolerance") / "retained"
  )


@pytest.fixture(scope="module")
def replacement_tolerance_gate_artifact(
  tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, Any]:
  return replacement_gate.generate_res006_beco_replacement_tolerance_admission_gate(
    retained_dir=tmp_path_factory.mktemp("replacement_tolerance")
  )


def test_benchmark_recalculation_gate_records_fail_closed_identity(
  recalculation_gate_artifact: dict[str, Any],
) -> None:
  artifact = recalculation_gate_artifact

  assert artifact["schema_version"] == (
    "a2.res006_beco_recalculation_admission_gate.v1"
  )
  assert artifact["status"] == (
    "partial_fail_closed_res006_beco_recalculation_admission"
  )
  assert artifact["mechanism_comparison_hashes_input_status"] == (
    "partial_fail_closed_mechanism_comparison_hash_manifest"
  )
  assert_authority_guards_false(artifact)
  assert artifact["authority_guards"]["pk_authority_granted"] is False
  assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False

  source_rights = artifact["source_rights_output_policy_summary"]
  assert source_rights["present"] is True
  assert source_rights["allowed_output_policy_status"] == (
    "release_candidate_fail_closed_policy_frozen"
  )
  assert source_rights["selected_comparison_hashes_admitted_by_policy"] is False


def test_benchmark_recalculation_gate_blocks_res006_admission(
  recalculation_gate_artifact: dict[str, Any],
) -> None:
  artifact = recalculation_gate_artifact
  decision = artifact["admission_decision"]

  assert decision["residual_id"] == "RES-006"
  assert decision["decision"] == "res006_remains_blocked_fail_closed"
  assert decision["res006_narrowly_closed"] is False
  assert decision["beco_recalculation_hashes_admitted"] is False
  assert decision["allowed_output_signoff_present"] is False
  assert decision["tolerance_policy_admitted"] is False
  assert decision["replacement_anchor_set_admitted"] is False
  assert decision["closed_residual_ids_by_this_gate"] == []


def test_benchmark_recalculation_gate_retains_cached_hash_anchors(
  recalculation_gate_artifact: dict[str, Any],
) -> None:
  artifact = recalculation_gate_artifact
  cached = artifact["cached_anchor_summary"]

  assert cached["cached_hash_anchor_count"] == 9
  assert cached["all_selected_cached_hashes_present"] is True
  assert cached["spreadsheet_calculation_executed"] is False
  assert_hex64(cached["selected_comparison_output_set_sha256"])
  for row in cached["cached_hashes"]:
    assert_hex64(row["cached_anchor_sha256"])
    assert_hex64(row["formula_sha256"])
    assert row["raw_value_disclosed"] is False
    assert row["formula_text_disclosed"] is False


def test_benchmark_recalculation_gate_records_spreadsheet_execution_path(
  recalculation_gate_artifact: dict[str, Any],
) -> None:
  artifact = recalculation_gate_artifact
  tooling = artifact["tooling_detection"]
  beco = artifact["beco_recalculation_gate"]
  replacement = artifact["replacement_path"]
  anchor_set = artifact["candidate_replacement_anchor_set"]

  if tooling["tool_detection_status"] == "spreadsheet_execution_tool_available":
    assert beco["spreadsheet_execution_attempted"] is True
    assert beco["execution_attempt"]["attempted"] is True
    assert beco["execution_attempt"]["raw_values_retained"] is False
    assert beco["execution_attempt"]["temporary_workbook_copy_retained"] is False
    assert anchor_set["status"] == (
      "candidate_replacement_anchor_set_retained_not_admitted"
    )
    assert anchor_set["recalculated_hash_count"] == 9
    assert anchor_set["all_selected_recalculated_hashes_present"] is True
    assert_hex64(anchor_set["selected_recalculated_output_set_sha256"])
    assert anchor_set["raw_selected_values_retained"] is False
    assert anchor_set["formula_text_retained"] is False
    assert anchor_set["replacement_anchor_set_admitted"] is False
    for row in anchor_set["selected_recalculated_hashes"]:
      assert_hex64(row["recalculated_output_sha256"])
      assert_hex64(row["formula_sha256"])
      assert row["raw_value_disclosed"] is False
      assert row["formula_text_disclosed"] is False

    mismatch = artifact["mismatch_lineage"]
    assert mismatch["status"] == (
      "cached_to_recalculated_hash_lineage_mismatch_fail_closed"
    )
    assert mismatch["cached_anchor_count"] == 9
    assert mismatch["recalculated_anchor_count"] == 9
    assert mismatch["matching_count"] == 0
    assert mismatch["mismatch_count"] == 9
    assert mismatch["missing_recalculated_count"] == 0
    assert len(mismatch["mismatch_comparison_ids"]) == 9
    assert mismatch["raw_values_retained"] is False
    assert mismatch["formula_text_retained"] is False
    assert replacement["status"] == (
      "candidate_recalculated_anchor_set_retained_review_required"
    )
    assert replacement["candidate_replacement_anchor_set_retained"] is True
    assert replacement["replacement_anchor_set_admitted"] is False
  else:
    assert beco["spreadsheet_execution_attempted"] is False
    assert anchor_set["status"] == (
      "candidate_replacement_anchor_set_unavailable_fail_closed"
    )
    assert replacement["status"] == "replacement_anchor_set_not_available_fail_closed"


def test_benchmark_recalculation_gate_omits_raw_recalculation_payloads(
  recalculation_gate_artifact: dict[str, Any],
) -> None:
  artifact = recalculation_gate_artifact
  _assert_recalculation_hash_only(artifact)


def test_benchmark_recalculation_missing_spreadsheet_executor_fails_closed(
  monkeypatch: Any,
  tmp_path: Path,
) -> None:
  monkeypatch.setattr(
    recalculation_gate.res005006_gate.shutil,
    "which",
    lambda _name: None,
  )

  artifact = recalculation_gate.generate_res006_beco_recalculation_admission_gate(
    retained_dir=tmp_path
  )

  tooling = artifact["tooling_detection"]
  beco = artifact["beco_recalculation_gate"]
  anchor_set = artifact["candidate_replacement_anchor_set"]
  mismatch = artifact["mismatch_lineage"]
  decision = artifact["admission_decision"]

  assert tooling["tool_detection_status"] == "spreadsheet_execution_tool_missing"
  assert tooling["selected_spreadsheet_executor"] is None
  assert tooling["dependency_install_attempted"] is False
  assert tooling["network_fetch_attempted"] is False
  assert beco["gate_status"] == "blocked_fail_closed_beco_execution_tool_missing"
  assert beco["spreadsheet_execution_attempted"] is False
  assert beco["spreadsheet_recalculation_admitted"] is False
  assert anchor_set["recalculated_hash_count"] == 0
  assert anchor_set["replacement_anchor_set_admitted"] is False
  assert mismatch["recalculated_anchor_count"] == 0
  assert mismatch["missing_recalculated_count"] == 0
  assert decision["res006_narrowly_closed"] is False
  assert "neither libreoffice nor soffice" in decision["remaining_blockers"][0]

  _assert_recalculation_hash_only(artifact)


def test_benchmark_recalculation_skip_execution_records_explicit_fail_closed_path(
  tmp_path: Path,
) -> None:
  artifact = recalculation_gate.generate_res006_beco_recalculation_admission_gate(
    retained_dir=tmp_path,
    attempt_spreadsheet_execution=False,
  )

  assert artifact["tooling_detection"]["tool_detection_status"] == (
    "spreadsheet_execution_probe_skipped"
  )
  assert artifact["beco_recalculation_gate"]["gate_status"] == (
    "blocked_fail_closed_beco_execution_tool_missing"
  )
  assert artifact["candidate_replacement_anchor_set"]["status"] == (
    "candidate_replacement_anchor_set_unavailable_fail_closed"
  )
  assert artifact["replacement_path"]["candidate_replacement_anchor_set_retained"] is False
  assert artifact["admission_decision"]["res006_narrowly_closed"] is False
  assert artifact["authority_guards_all_false"] is True


def test_benchmark_recalculation_cli_writes_gate_anchor_set_and_manifest(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "gate_cli.json"
  retained_dir = tmp_path / "retained"

  result = run_maintenance_cli(
    "damage_model.py benchmark-evidence",
    "spreadsheet-recalculation-admission",
    "--skip-spreadsheet-execution",
    "--retained-dir",
    retained_dir,
    "--output",
    output_path,
  )

  assert result.stdout == ""
  artifact = read_json(output_path)
  assert artifact["schema_version"] == (
    "a2.res006_beco_recalculation_admission_gate.v1"
  )
  assert artifact["retained_artifact_sha256"]
  assert artifact["retained_anchor_set_sha256"]
  assert artifact["retained_manifest_sha256"]

  gate_path = retained_dir / "res006_beco_recalculation_admission_gate.json"
  anchor_path = retained_dir / "beco_recalculated_hash_anchor_set.json"
  manifest_path = retained_dir / "manifest.json"
  assert gate_path.is_file()
  assert anchor_path.is_file()
  assert manifest_path.is_file()

  retained_gate = read_json(gate_path)
  anchor_set = read_json(anchor_path)
  manifest = read_json(manifest_path)
  assert retained_gate["candidate_replacement_anchor_set_artifact"][
    "filename"
  ] == "beco_recalculated_hash_anchor_set.json"
  assert anchor_set["schema_version"] == (
    "a2.res006_beco_recalculated_hash_anchor_set.v1"
  )
  assert manifest["schema_version"] == (
    "a2.res006_beco_recalculation_admission_retained_manifest.v1"
  )
  assert manifest["status"] == (
    "res006_beco_recalculation_admission_retained_release_blocked"
  )
  assert manifest["artifacts"][0]["artifact_key"] == (
    "res006_beco_recalculation_admission_gate"
  )
  assert_hex64(manifest["artifacts"][0]["sha256"])
  assert_hex64(manifest["artifacts"][1]["sha256"])
  assert manifest["authority_guards_all_false"] is True
  assert manifest["authority_guards"]["pk_authority_granted"] is False
  assert manifest["authority_guards"]["deterministic_fuze_authority_granted"] is False

  _assert_recalculation_hash_only(retained_gate)
  _assert_recalculation_hash_only(anchor_set)


def test_benchmark_lineage_tolerance_packet_records_fail_closed_identity(
  lineage_tolerance_packet_artifact: dict[str, Any],
) -> None:
  artifact = lineage_tolerance_packet_artifact

  assert artifact["schema_version"] == (
    "a2.res006_beco_lineage_tolerance_review_candidate_packet.v1"
  )
  assert artifact["residual_id"] == "RES-006"
  assert artifact["status"] == (
    "blocked_fail_closed_res006_beco_lineage_tolerance_review_candidate"
  )
  assert artifact["packet_role"] == "machine_readable_review_candidate_not_admission"
  assert artifact["benchmark_consumed_for_release"] is False
  assert artifact["raw_selected_values_retained"] is False
  assert artifact["raw_output_tables_retained"] is False
  assert artifact["stdout_retained"] is False
  assert artifact["stderr_retained"] is False
  assert artifact["temporary_workbook_copy_retained"] is False

  refs = artifact["input_refs"]
  assert [ref["artifact_key"] for ref in refs] == [
    "res006_beco_recalculation_admission_gate",
    "beco_recalculated_hash_anchor_set",
    "mechanism_comparison_hashes",
    "source_rights_output_policy_gate",
    "res006_beco_replacement_tolerance_admission_gate",
  ]
  assert all(ref["present"] is True for ref in refs)
  for ref in refs:
    assert_hex64(ref["sha256"])

  guards = artifact["authority_guards"]
  assert artifact["authority_guards_all_false"] is True
  assert not any(guards.values())
  assert guards["blast_mechanism_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["stock_descriptor_created"] is False
  assert guards["runtime_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["fuze_authority_granted"] is False
  assert guards["replacement_anchor_authority_granted"] is False
  assert guards["cached_anchor_replacement_authority_granted"] is False


def test_benchmark_lineage_tolerance_packet_summarizes_hash_mismatch(
  lineage_tolerance_packet_artifact: dict[str, Any],
) -> None:
  artifact = lineage_tolerance_packet_artifact
  summary = artifact["cached_vs_recalculated_summary"]

  assert summary["counts_and_comparison_ids_only"] is True
  assert summary["status"] == "cached_vs_recalculated_hash_mismatch_fail_closed"
  assert summary["topology"] == "zero_match_all_selected_comparison_ids_mismatched"
  assert summary["comparison_id_count"] == 9
  assert summary["cached_anchor_count"] == 9
  assert summary["recalculated_anchor_count"] == 9
  assert summary["matching_count"] == 0
  assert summary["mismatch_count"] == 9
  assert summary["missing_cached_count"] == 0
  assert summary["missing_recalculated_count"] == 0
  assert summary["exact_hash_check_passed"] is False
  assert summary["matching_comparison_ids"] == []
  assert summary["mismatch_comparison_ids"] == [
    "BEC-O-METRIC-DEFAULT-001",
    "BEC-O-METRIC-DEFAULT-002",
    "BEC-O-METRIC-DEFAULT-003",
    "BEC-O-METRIC-DEFAULT-004",
    "BEC-O-METRIC-DEFAULT-005",
    "BEC-O-METRIC-DEFAULT-006",
    "BEC-O-METRIC-DEFAULT-007",
    "BEC-O-METRIC-DEFAULT-008",
    "BEC-O-METRIC-DEFAULT-009",
  ]
  assert summary["individual_row_hashes_retained_in_this_packet"] is False
  assert "hash_only_comparison_rows" not in summary


def test_benchmark_lineage_tolerance_packet_keeps_anchor_sources_hash_only(
  lineage_tolerance_packet_artifact: dict[str, Any],
) -> None:
  artifact = lineage_tolerance_packet_artifact
  sources = artifact["anchor_source_summary"]
  cached = sources["cached_anchor_source"]
  recalculated = sources["recalculated_anchor_source"]

  assert cached["selected_output_hash_count"] == 9
  assert recalculated["selected_output_hash_count"] == 9
  assert_hex64(cached["selected_output_set_sha256"])
  assert_hex64(recalculated["selected_output_set_sha256"])
  assert cached["individual_anchor_hashes_retained_in_this_packet"] is False
  assert recalculated["individual_anchor_hashes_retained_in_this_packet"] is False
  assert cached["anchor_rows_retained_in_this_packet"] is False
  assert recalculated["anchor_rows_retained_in_this_packet"] is False


def test_benchmark_lineage_tolerance_packet_requires_missing_signoffs(
  lineage_tolerance_packet_artifact: dict[str, Any],
) -> None:
  artifact = lineage_tolerance_packet_artifact
  signoffs = artifact["lineage_tolerance_required_signoffs"]

  assert [item["signoff_id"] for item in signoffs] == [
    "independent_lineage_review_signoff",
    "allowed_output_policy_signoff",
    "numeric_tolerance_policy_signoff",
    "replacement_anchor_signoff",
  ]
  assert all(item["required"] is True for item in signoffs)
  assert all(item["current_status"] == "missing" for item in signoffs)
  assert all(item["signed_off"] is False for item in signoffs)
  assert all(item["admitted"] is False for item in signoffs)
  assert artifact["current_missing_items"] == [
    "independent_lineage_review_signoff",
    "allowed_output_policy_signoff",
    "numeric_tolerance_policy_signoff",
    "replacement_anchor_signoff",
  ]


def test_benchmark_lineage_tolerance_packet_blocks_admission(
  lineage_tolerance_packet_artifact: dict[str, Any],
) -> None:
  artifact = lineage_tolerance_packet_artifact
  decision_inputs = artifact["lineage_tolerance_decision_inputs"]

  assert decision_inputs["lineage"]["local_recalculation_gate_present"] is True
  assert decision_inputs["lineage"]["spreadsheet_execution_attempted"] is True
  assert decision_inputs["lineage"]["independent_lineage_review_present"] is False
  assert decision_inputs["allowed_output"]["allowed_output_signoff_present"] is False
  assert (
    decision_inputs["numeric_tolerance"]["numeric_tolerance_policy_admitted"]
    is False
  )
  assert (
    decision_inputs["replacement_anchor"][
      "in_place_cached_anchor_replacement_allowed"
    ]
    is False
  )

  decision = artifact["admission_decision"]
  assert decision["decision"] == "res006_remains_blocked_fail_closed"
  assert decision["status"] == "blocked_fail_closed"
  assert decision["residual_closed"] is False
  assert decision["closed_residual_ids_by_this_packet"] == []
  assert decision["benchmark_consumed_for_release"] is False
  assert decision["raw_selected_values_retained"] is False


def test_benchmark_lineage_tolerance_packet_omits_raw_outputs(
  lineage_tolerance_packet_artifact: dict[str, Any],
) -> None:
  artifact = lineage_tolerance_packet_artifact
  _assert_no_raw_or_row_level_outputs(artifact)


def test_benchmark_lineage_tolerance_packet_missing_inputs_remain_fail_closed(
  tmp_path: Path,
) -> None:
  missing = tmp_path / "missing.json"
  artifact = lineage_packet.generate_res006_beco_lineage_tolerance_review_packet(
    retained_dir=tmp_path / "retained",
    res006_recalculation_gate_path=missing,
    beco_recalculated_anchor_set_path=missing,
    mechanism_comparison_hashes_path=missing,
    source_rights_output_policy_gate_path=missing,
    replacement_tolerance_gate_path=missing,
  )

  assert artifact["status"] == (
    "blocked_fail_closed_res006_beco_lineage_tolerance_review_candidate"
  )
  assert all(ref["present"] is False for ref in artifact["input_refs"])
  assert all(ref["status"] == "missing_fail_closed" for ref in artifact["input_refs"])
  assert artifact["cached_vs_recalculated_summary"]["comparison_id_count"] == 0
  assert artifact["cached_vs_recalculated_summary"]["cached_anchor_count"] == 0
  assert artifact["cached_vs_recalculated_summary"]["recalculated_anchor_count"] == 0
  assert artifact["cached_vs_recalculated_summary"][
    "status"
  ] == "cached_vs_recalculated_comparison_inputs_missing_fail_closed"
  assert artifact["lineage_tolerance_decision_inputs"]["lineage"][
    "local_recalculation_gate_present"
  ] is False
  assert artifact["lineage_tolerance_decision_inputs"]["replacement_anchor"][
    "candidate_replacement_anchor_set_retained"
  ] is False
  assert artifact["current_missing_items"] == [
    "independent_lineage_review_signoff",
    "allowed_output_policy_signoff",
    "numeric_tolerance_policy_signoff",
    "replacement_anchor_signoff",
  ]
  assert artifact["authority_guards_all_false"] is True
  assert artifact["benchmark_consumed_for_release"] is False
  assert artifact["raw_selected_values_retained"] is False

  _assert_no_raw_or_row_level_outputs(artifact)


def test_benchmark_lineage_tolerance_cli_writes_packet_and_manifest(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "packet_copy.json"
  retained_dir = tmp_path / "retained"

  result = run_maintenance_cli(
    "damage_model.py benchmark-evidence",
    "spreadsheet-lineage-tolerance-packet",
    "--retained-dir",
    retained_dir,
    "--output",
    output_path,
  )

  assert result.stdout == ""
  assert output_path.is_file()
  output_copy = read_json(output_path)
  assert_hex64(output_copy["retained_artifact_sha256"])
  assert_hex64(output_copy["retained_manifest_sha256"])

  packet_path = retained_dir / "res006_beco_lineage_tolerance_review_candidate_packet.json"
  manifest_path = retained_dir / "manifest.json"
  assert packet_path.is_file()
  assert manifest_path.is_file()

  retained_packet = read_json(packet_path)
  manifest = read_json(manifest_path)
  assert retained_packet["schema_version"] == (
    "a2.res006_beco_lineage_tolerance_review_candidate_packet.v1"
  )
  assert manifest["schema_version"] == (
    "a2.res006_beco_lineage_tolerance_review_retained_manifest.v1"
  )
  assert manifest["status"] == (
    "blocked_fail_closed_res006_beco_lineage_tolerance_review_candidate"
  )
  assert manifest["artifacts"][0]["artifact_key"] == (
    "res006_beco_lineage_tolerance_review_candidate_packet"
  )
  assert_hex64(manifest["artifacts"][0]["sha256"])
  assert len(manifest["input_refs"]) == 5
  for ref in manifest["input_refs"]:
    assert_hex64(ref["sha256"])
  assert manifest["cached_vs_recalculated_summary"][
    "counts_and_comparison_ids_only"
  ] is True
  assert manifest["authority_guards_all_false"] is True
  assert not any(manifest["authority_guards"].values())

  summary = manifest_integrity.check_retained_manifest_integrity(
    manifest_paths=[manifest_path]
  )
  assert summary["missing_total"] == 0
  assert summary["sha_mismatch_total"] == 0
  assert summary["guard_true_total"] == 0

  _assert_no_raw_or_row_level_outputs(retained_packet)
  _assert_no_raw_or_row_level_outputs(manifest)


def test_benchmark_replacement_tolerance_gate_records_fail_closed_identity(
  replacement_tolerance_gate_artifact: dict[str, Any],
) -> None:
  artifact = replacement_tolerance_gate_artifact

  assert artifact["schema_version"] == (
    "a2.res006_beco_replacement_tolerance_admission_gate.v1"
  )
  assert artifact["residual_id"] == "RES-006"
  assert artifact["status"] == (
    "blocked_fail_closed_res006_beco_replacement_tolerance_admission_review"
  )
  assert artifact["benchmark_consumed_for_release"] is False
  assert artifact["raw_selected_values_retained"] is False
  assert_authority_guards_false(artifact)
  assert artifact["authority_guards"]["blast_mechanism_authority_granted"] is False
  assert artifact["authority_guards"][
    "component_failure_probability_authority_granted"
  ] is False
  assert artifact["authority_guards"]["effect_scale_authority_granted"] is False
  assert artifact["authority_guards"]["stock_descriptor_created"] is False
  assert artifact["authority_guards"]["runtime_authority_granted"] is False
  assert artifact["authority_guards"]["pk_authority_granted"] is False
  assert artifact["authority_guards"]["fuze_authority_granted"] is False
  assert artifact["authority_guards"]["replacement_anchor_authority_granted"] is False

  refs = artifact["input_refs"]
  assert [ref["artifact_key"] for ref in refs] == [
    "res006_beco_recalculation_admission_gate",
    "beco_recalculated_hash_anchor_set",
    "mechanism_comparison_hashes",
    "source_rights_output_policy_gate",
  ]
  assert all(ref["present"] is True for ref in refs)
  for ref in refs:
    assert_hex64(ref["sha256"])


def test_benchmark_replacement_tolerance_gate_records_source_policy_and_mismatch(
  replacement_tolerance_gate_artifact: dict[str, Any],
) -> None:
  artifact = replacement_tolerance_gate_artifact
  source_rights = artifact["source_rights_output_policy_summary"]

  assert source_rights["allowed_output_policy_status"] == (
    "release_candidate_fail_closed_policy_frozen"
  )
  assert source_rights["allowed_output_signoff_present"] is False
  assert source_rights["selected_comparison_output_hashes_admitted"] is False
  assert source_rights["recording_level"] == "path_sha_status_only"

  mismatch = artifact["cached_vs_recalculated_mismatch_summary"]
  assert mismatch["status"] == "cached_vs_recalculated_hash_mismatch_fail_closed"
  assert mismatch["cached_anchor_count"] == 9
  assert mismatch["recalculated_anchor_count"] == 9
  assert mismatch["comparison_row_count"] == 9
  assert mismatch["matching_count"] == 0
  assert mismatch["mismatch_count"] == 9
  assert mismatch["exact_hash_check_passed"] is False
  assert mismatch["raw_selected_values_retained"] is False
  assert mismatch["stdout_retained"] is False
  assert len(mismatch["mismatch_comparison_ids"]) == 9
  for row in mismatch["hash_only_comparison_rows"]:
    assert_hex64(row["cached_anchor_sha256"])
    assert_hex64(row["recalculated_output_sha256"])
    assert_hex64(row["formula_sha256"])
    assert row["raw_value_disclosed"] is False
    assert row["formula_text_disclosed"] is False


def test_benchmark_replacement_tolerance_gate_requires_missing_signoffs(
  replacement_tolerance_gate_artifact: dict[str, Any],
) -> None:
  artifact = replacement_tolerance_gate_artifact
  replacement = artifact["replacement_candidate_summary"]

  assert replacement["candidate_replacement_anchor_set_retained"] is True
  assert replacement["replacement_anchor_set_admitted"] is False
  assert replacement["replacement_anchor_signoff_present"] is False
  assert replacement["replacement_anchor_authority_granted"] is False
  assert replacement["benchmark_consumed_for_release"] is False

  signoffs = artifact["required_signoff_items"]
  assert [item["signoff_id"] for item in signoffs] == [
    "independent_lineage_review_signoff",
    "allowed_output_policy_signoff",
    "numeric_tolerance_policy_signoff",
    "replacement_anchor_signoff",
  ]
  assert all(item["required"] is True for item in signoffs)
  assert all(item["signed_off"] is False for item in signoffs)
  assert all(item["admitted"] is False for item in signoffs)
  assert artifact["current_missing_items"] == [
    "independent_lineage_review_signoff",
    "allowed_output_policy_signoff",
    "numeric_tolerance_policy_signoff",
    "replacement_anchor_signoff",
  ]


def test_benchmark_replacement_tolerance_gate_blocks_admission(
  replacement_tolerance_gate_artifact: dict[str, Any],
) -> None:
  artifact = replacement_tolerance_gate_artifact
  decision = artifact["admission_decision"]

  assert decision["decision"] == "res006_remains_blocked_fail_closed"
  assert decision["status"] == "blocked_fail_closed"
  assert decision["residual_closed"] is False
  assert decision["closed_residual_ids_by_this_gate"] == []
  assert decision["independent_lineage_review_present"] is False
  assert decision["allowed_output_signoff_present"] is False
  assert decision["tolerance_policy_admitted"] is False
  assert decision["replacement_anchor_set_admitted"] is False
  assert decision["benchmark_consumed_for_release"] is False
  assert decision["raw_selected_values_retained"] is False


def test_benchmark_replacement_tolerance_gate_uses_hash_ref_label_only_payload(
  replacement_tolerance_gate_artifact: dict[str, Any],
) -> None:
  artifact = replacement_tolerance_gate_artifact
  _assert_hash_ref_label_only(artifact)


def test_benchmark_replacement_tolerance_missing_inputs_remain_machine_readable(
  tmp_path: Path,
) -> None:
  missing = tmp_path / "missing.json"
  artifact = replacement_gate.generate_res006_beco_replacement_tolerance_admission_gate(
    retained_dir=tmp_path / "retained",
    res006_recalculation_gate_path=missing,
    beco_recalculated_anchor_set_path=missing,
    mechanism_comparison_hashes_path=missing,
    source_rights_output_policy_gate_path=missing,
  )

  assert artifact["status"] == (
    "blocked_fail_closed_res006_beco_replacement_tolerance_admission_review"
  )
  assert all(ref["present"] is False for ref in artifact["input_refs"])
  assert all(ref["status"] == "missing_fail_closed" for ref in artifact["input_refs"])
  assert artifact["cached_vs_recalculated_mismatch_summary"][
    "comparison_row_count"
  ] == 0
  assert artifact["replacement_candidate_summary"]["status"] == (
    "candidate_replacement_anchor_set_missing_fail_closed"
  )
  assert artifact["admission_decision"]["decision"] == (
    "res006_remains_blocked_fail_closed"
  )
  assert artifact["authority_guards_all_false"] is True
  assert artifact["benchmark_consumed_for_release"] is False
  assert artifact["raw_selected_values_retained"] is False

  _assert_hash_ref_label_only(artifact)


def test_benchmark_replacement_tolerance_cli_writes_gate_and_manifest(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "gate_cli.json"
  retained_dir = tmp_path / "retained"

  result = run_maintenance_cli(
    "damage_model.py benchmark-evidence",
    "spreadsheet-replacement-tolerance",
    "--retained-dir",
    retained_dir,
    "--output",
    output_path,
  )

  assert result.stdout == ""
  artifact = read_json(output_path)
  assert artifact["retained_artifact_sha256"]
  assert artifact["retained_manifest_sha256"]

  gate_path = retained_dir / "res006_beco_replacement_tolerance_admission_gate.json"
  manifest_path = retained_dir / "manifest.json"
  assert gate_path.is_file()
  assert manifest_path.is_file()

  retained_gate = read_json(gate_path)
  manifest = read_json(manifest_path)
  assert retained_gate["schema_version"] == (
    "a2.res006_beco_replacement_tolerance_admission_gate.v1"
  )
  assert manifest["schema_version"] == (
    "a2.res006_beco_replacement_tolerance_admission_retained_manifest.v1"
  )
  assert manifest["status"] == (
    "blocked_fail_closed_res006_beco_replacement_tolerance_admission_review"
  )
  assert manifest["artifacts"][0]["artifact_key"] == (
    "res006_beco_replacement_tolerance_admission_gate"
  )
  assert_hex64(manifest["artifacts"][0]["sha256"])
  assert len(manifest["input_refs"]) == 4
  for ref in manifest["input_refs"]:
    assert_hex64(ref["sha256"])
  assert_authority_guards_false(manifest)
  assert_retained_manifest_clean(manifest_integrity, manifest_path)
