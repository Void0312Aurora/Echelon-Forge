from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path
from tests.architecture.damage_model.helpers import (
  HEX64,
  run_maintenance_cli,
  walk_payload,
)

ensure_repo_root_on_sys_path()

from tools.maintenance.benchmark_evidence import ( # noqa: E402
  comparison_hashes as hashes,
  mechanism_evidence as evidence,
)
from tools.maintenance.scope_provenance import mechanism_source_closeout as gate # noqa: E402


def _by_residual(artifact: dict[str, object]) -> dict[str, dict[str, object]]:
  rows = artifact["residual_benchmark_evidence"]
  assert isinstance(rows, list)
  return {str(row["residual_id"]): row for row in rows}


def _matrix_by_lineage(artifact: dict[str, object]) -> dict[str, dict[str, object]]:
  rows = artifact["source_consumption_validation_matrix"]
  assert isinstance(rows, list)
  return {str(row["lineage_id"]): row for row in rows}


def test_mechanism_benchmark_evidence_current_repo_fails_closed() -> None:
  artifact = evidence.generate_mechanism_benchmark_evidence(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.mechanism_benchmark_evidence.v1"
  assert (
    artifact["status"]
    == "blocked_fail_closed_mechanism_benchmark_evidence_manifest"
  )
  for ref in artifact["doc_refs"].values():
    assert (REPO_ROOT / str(ref)).exists()

  assert artifact["current_gate_results"] == {
    "RES-003": "blocked_fail_closed_release_grade_geometry_benchmark_missing",
    "RES-004": (
      "blocked_fail_closed_release_grade_warhead_sensitivity_benchmark_missing"
    ),
    "RES-005": "blocked_fail_closed_fragment_benchmark_payload_missing",
    "RES-006": "blocked_fail_closed_blast_benchmark_payload_missing",
  }

  decision = artifact["benchmark_evidence_decision"]
  assert decision["mechanism_benchmark_evidence_ready"] is False
  assert decision["mechanism_benchmark_evidence_blocked"] is True
  assert decision["fail_closed"] is True
  assert decision["closed_residual_ids_by_this_gate"] == []
  assert decision["candidate_or_toy_probe_is_calibration"] is False
  assert decision["pk_authority_included"] is False
  assert decision["deterministic_fuze_authority_included"] is False

  rows = _by_residual(artifact)
  for residual_id in ("RES-003", "RES-004", "RES-005", "RES-006"):
    row = rows[residual_id]
    assert row["source_present"] is True
    assert row["candidate_or_scaffold_consumed"] is True
    assert row["benchmark_consumed"] is False
    assert row["release_grade_validated"] is False
    assert row["shortest_completion_path"]

  res003 = rows["RES-003"]
  assert res003["evidence_status"] == (
    "review_inputs_present_external_geometry_benchmark_missing"
  )
  res003_observed = res003["observed_evidence"]
  assert res003_observed["target_geometry_assumption_summary"][
    "unsupported_row_count"
  ] == 2
  assert "PIN-F16-003" in res003_observed["pin_evidence"][
    "sanity_only_pin_ids"
  ]

  res004 = rows["RES-004"]
  assert res004["evidence_status"] == (
    "scope_and_sensitivity_boundary_present_external_warhead_benchmark_missing"
  )
  res004_observed = res004["observed_evidence"]
  assert res004_observed["warhead_scope_summary"][
    "consumed_by_surrogate_yes_count"
  ] == 3
  assert "PIN-AIM120-TPC-REJ" in res004_observed["pin_evidence"][
    "rejected_pin_ids"
  ]


def test_mechanism_benchmark_evidence_separates_source_consumption_and_validation() -> None:
  artifact = evidence.generate_mechanism_benchmark_evidence(repo_root=REPO_ROOT)

  matrix = _matrix_by_lineage(artifact)
  assert set(matrix) == {
    "FRAG-GURNEY-BRL405",
    "FRAG-TP21-DEBRIS",
    "FRAG-TOY-SCAFFOLD",
    "BLAST-KINGERY-BULMASH",
    "BLAST-BEC-O-TP20",
    "BLAST-TOY-SCAFFOLD",
  }
  for row in matrix.values():
    assert set(row) == {
      "lineage_id",
      "residual_id",
      "source_present",
      "benchmark_consumed",
      "release_grade_validated",
      "evidence_status",
    }
    assert row["source_present"] is True
    assert row["benchmark_consumed"] is False
    assert row["release_grade_validated"] is False

  lineages = artifact["fragment_blast_lineage_summary"]
  frag = {row["lineage_id"]: row for row in lineages["fragment"]}
  blast = {row["lineage_id"]: row for row in lineages["blast"]}

  assert "VPS-BFM-007" in frag["FRAG-GURNEY-BRL405"][
    "pending_acquisition_source_ids"
  ]
  assert "PIN-BFM-002" in frag["FRAG-TP21-DEBRIS"]["pin_evidence"][
    "externally_verified_candidate_pin_ids"
  ]
  assert frag["FRAG-TP21-DEBRIS"]["pin_evidence"][
    "consumption_status_by_pin"
  ]["PIN-BFM-002"] == "not_consumed_for_stage_b_release"
  assert frag["FRAG-TOY-SCAFFOLD"]["candidate_or_scaffold_consumed"] is True
  assert frag["FRAG-TOY-SCAFFOLD"]["evidence_status"] == (
    "toy_probe_consumed_for_hygiene_not_calibration"
  )

  assert "VPS-BFM-003" in blast["BLAST-KINGERY-BULMASH"][
    "pending_acquisition_source_ids"
  ]
  assert "PIN-BFM-001" in blast["BLAST-BEC-O-TP20"]["pin_evidence"][
    "externally_verified_candidate_pin_ids"
  ]
  assert blast["BLAST-BEC-O-TP20"]["pin_evidence"][
    "consumption_status_by_pin"
  ]["PIN-BFM-001"] == "not_consumed_for_stage_b_release"
  assert blast["BLAST-TOY-SCAFFOLD"]["candidate_or_scaffold_consumed"] is True
  assert blast["BLAST-TOY-SCAFFOLD"]["evidence_status"] == (
    "toy_probe_consumed_for_hygiene_not_calibration"
  )


def test_mechanism_benchmark_evidence_cli_keeps_authority_guards_false(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "mechanism_benchmark_evidence.json"

  result = run_maintenance_cli(
    "damage_model.py benchmark-evidence",
    "mechanism-evidence",
    "--output",
    output_path,
  )

  assert result.stdout == ""
  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["schema_version"] == "a2.mechanism_benchmark_evidence.v1"

  guards = artifact["non_authoritative_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["target_geometry_authority_granted"] is False
  assert guards["aim120c_warhead_authority_granted"] is False
  assert guards["fragment_mechanism_authority_granted"] is False
  assert guards["blast_mechanism_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False
  assert any("source_present" in note for note in artifact["integration_notes"])


def test_mechanism_comparison_hashes_current_repo_is_fail_closed() -> None:
  artifact = hashes.generate_mechanism_comparison_hashes(repo_root=REPO_ROOT)

  assert artifact["schema_version"] == "a2.mechanism_comparison_hashes.v1"
  assert artifact["status"] == "partial_fail_closed_mechanism_comparison_hash_manifest"
  assert artifact["current_gate_results"] == {
    "RES-005": (
      "partial_fail_closed_tp21_criteria_vocabulary_hash_present_"
      "selected_debris_output_requirements_open"
    ),
    "RES-006": (
      "partial_fail_closed_beco_cached_comparison_hashes_present_"
      "spreadsheet_execution_required"
    ),
  }

  decision = artifact["comparison_hash_decision"]
  assert decision["closed_residual_ids_by_this_gate"] == []
  assert decision["fail_closed"] is True
  assert decision["source_presence_is_calibration"] is False
  assert decision["beco_cached_hashes_are_calibration"] is False
  assert decision["tp21_vocabulary_is_calibration"] is False
  assert decision["benchmark_consumed_for_release"] is False
  assert decision["release_grade_validated"] is False
  assert decision["selected_beco_cached_output_hashes_present"] is True
  assert decision["tp21_selected_debris_output_hashes_present"] is False

  matrix = {
    row["lineage_id"]: row for row in artifact["source_consumption_validation_matrix"]
  }
  assert matrix["FRAG-TP21-DEBRIS"]["source_present"] is True
  assert matrix["FRAG-TP21-DEBRIS"]["comparison_output_hash_present"] is False
  assert matrix["FRAG-TP21-DEBRIS"]["benchmark_consumed"] is False
  assert matrix["BLAST-BEC-O-TP20"]["source_present"] is True
  assert matrix["BLAST-BEC-O-TP20"]["comparison_output_hash_present"] is True
  assert matrix["BLAST-BEC-O-TP20"]["benchmark_consumed"] is False

  assert artifact["authority_guards_all_false"] is True
  assert not any(artifact["non_authoritative_guards"].values())


def test_mechanism_comparison_hashes_beco_metadata_and_hash_only_outputs() -> None:
  artifact = hashes.generate_mechanism_comparison_hashes(repo_root=REPO_ROOT)
  beco = artifact["beco_workbook"]

  assert beco["workbook_sha256"] == (
    "82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc"
  )
  assert beco["parse_status"] == "metadata_and_cached_formula_hashes_retained"
  assert beco["spreadsheet_calculation_executed"] is False
  assert beco["spreadsheet_execution_status"] == (
    "not_executed_fail_closed_cached_values_only"
  )
  assert beco["benchmark_consumed_for_release"] is False
  assert beco["cached_workbook_values_are_calibration"] is False

  sheets = {row["sheet_name"]: row for row in beco["sheet_inventory"]}
  assert set(sheets) == {
    "START",
    "ENGLISH UNITS ",
    "ENGLISH-TO-METRIC CONVERSION",
    "METRIC UNITS",
    "METRIC-TO-ENGLISH CONVERSION",
    "Munition Data",
    "Explosive Data",
  }
  assert sheets["METRIC UNITS"]["dimension"] == "A1:CL273"
  assert sheets["METRIC UNITS"]["numeric_cached_formula_value_count"] > 0

  selected = beco["selected_comparison_hashes"]
  assert len(selected) == len(hashes.BECO_SELECTED_OUTPUTS)
  assert beco["selected_comparison_output_count"] == len(hashes.BECO_SELECTED_OUTPUTS)
  assert HEX64.fullmatch(beco["selected_comparison_output_set_sha256"])
  for row in selected:
    assert row["value_kind"] == "cached_formula_numeric"
    assert row["formula_present"] is True
    assert row["cached_formula_value_present"] is True
    assert row["numeric_cached_formula_value_present"] is True
    assert HEX64.fullmatch(row["formula_sha256"])
    assert HEX64.fullmatch(row["comparison_output_sha256"])
    assert row["benchmark_consumed_for_release"] is False
    assert row["comparison_hash_is_calibration"] is False

  forbidden_raw_keys = {"cached_formula_value", "formula"}
  for value in walk_payload(beco):
    if isinstance(value, dict):
      assert not (forbidden_raw_keys & set(value))

  requirements = artifact["fail_closed_selected_output_requirements"]["RES-006"]
  assert len(requirements) == len(hashes.BECO_SELECTED_OUTPUTS)
  assert all(
    row["current_status"] == "cached_hash_available_recalculation_required"
    for row in requirements
  )
  assert all(row["raw_source_value_must_not_be_copied_to_dataset"] for row in requirements)


def test_mechanism_comparison_hashes_tp21_vocabulary_not_dataset() -> None:
  artifact = hashes.generate_mechanism_comparison_hashes(repo_root=REPO_ROOT)
  tp21 = artifact["tp21_criteria_vocabulary"]

  assert tp21["artifact_sha256"] == (
    "84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8"
  )
  assert tp21["criteria_vocabulary_status"] == (
    "controlled_vocabulary_hash_retained_no_source_text_dataset"
  )
  assert HEX64.fullmatch(tp21["criteria_vocabulary_sha256"])
  assert tp21["source_text_copied_to_dataset"] is False
  assert tp21["selected_debris_output_hashes"] == []
  assert tp21["benchmark_consumed_for_release"] is False
  assert tp21["criteria_vocabulary_is_calibration"] is False

  vocab_keys = [row["criteria_key"] for row in tp21["allowed_criteria_vocabulary"]]
  assert vocab_keys == [
    "debris_item_class",
    "debris_mass_bin",
    "debris_velocity_or_throw_bin",
    "standoff_or_separation_bin",
    "target_exposure_or_area_bin",
    "unit_system",
    "applicability_limit",
    "exclusion_reason",
  ]
  requirements = artifact["fail_closed_selected_output_requirements"]["RES-005"]
  assert len(requirements) == len(vocab_keys)
  assert all(
    row["current_status"] == "selected_debris_output_hash_missing"
    for row in requirements
  )
  assert all(row["source_text_must_not_be_copied_to_dataset"] for row in requirements)

  assert "extracted_text" not in json.dumps(tp21, ensure_ascii=False)
  assert "source_table" not in json.dumps(tp21, ensure_ascii=False)


def test_mechanism_comparison_hashes_cli_writes_retained_manifest(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "mechanism_comparison_hashes_cli.json"
  retained_dir = tmp_path / "retained"

  result = run_maintenance_cli(
    "damage_model.py benchmark-evidence",
    "comparison-hashes",
    "--write-retained-artifacts",
    "--retained-dir",
    retained_dir,
    "--output",
    output_path,
  )

  assert result.stdout == ""
  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["schema_version"] == "a2.mechanism_comparison_hashes.v1"
  assert artifact["retained_artifact_sha256"]
  assert artifact["retained_manifest_sha256"]
  assert (retained_dir / "mechanism_comparison_hashes.json").exists()
  assert (retained_dir / "manifest.json").exists()

  manifest = json.loads((retained_dir / "manifest.json").read_text(encoding="utf-8"))
  assert manifest["schema_version"] == (
    "a2.mechanism_comparison_hashes_retained_manifest.v1"
  )
  assert manifest["status"] == "partial_fail_closed_mechanism_comparison_hash_manifest"
  assert HEX64.fullmatch(manifest["mechanism_comparison_hashes_artifact"]["sha256"])
  assert HEX64.fullmatch(manifest["beco_selected_comparison_output_set_sha256"])
  assert HEX64.fullmatch(manifest["tp21_criteria_vocabulary_sha256"])
  assert manifest["authority_guards_all_false"] is True
  assert not any(manifest["non_authoritative_guards"].values())


def test_mechanism_source_closeout_gate_current_repo_is_blocked_review_ready() -> None:
  artifact = gate.generate_mechanism_source_closeout_gate(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.mechanism_source_closeout_gate.v1"
  assert (
    artifact["status"]
    == "blocked_non_authoritative_mechanism_source_closeout_candidate"
  )
  assert artifact["review_target"] == (
    "res_003_004_005_006_mechanism_source_closeout_lane"
  )
  assert artifact["readiness_level"] == (
    "author_side_evidence_present_but_calibrated_authority_blocked"
  )

  assert artifact["documentation_status"]["ready_for_review"] is True
  assert artifact["documentation_status"]["placeholder_hits"] == []
  for ref in artifact["doc_refs"].values():
    assert (REPO_ROOT / ref).exists()

  assert artifact["current_gate_results"] == {
    "RES-003": "blocked_author_side_review_ready",
    "RES-004": "blocked_author_side_review_ready",
    "RES-005": "blocked_author_side_review_ready",
    "RES-006": "blocked_author_side_review_ready",
  }
  decision = artifact["closeout_decision"]
  assert decision["mechanism_source_closeout_ready"] is False
  assert decision["mechanism_source_closeout_blocked"] is True
  assert decision["author_side_subitems_recorded"] is True
  assert decision["closed_residual_ids_by_this_gate"] == []
  assert decision["authority_release_included"] is False

  assert [row["check_id"] for row in artifact["closeout_checks"]] == [
    "CLOSEOUT-RES003-001",
    "CLOSEOUT-RES003-002",
    "CLOSEOUT-RES004-001",
    "CLOSEOUT-RES004-002",
    "CLOSEOUT-RES005-001",
    "CLOSEOUT-RES005-002",
    "CLOSEOUT-RES006-001",
    "CLOSEOUT-RES006-002",
  ]
  assert all(row["author_side_satisfied"] for row in artifact["closeout_checks"])
  assert not any(row["release_grade_satisfied"] for row in artifact["closeout_checks"])
  assert {row["status"] for row in artifact["closeout_checks"]} == {
    "blocked_release_grade_evidence_missing"
  }

  res003 = artifact["closeout_checks"][0]
  assert "F16-TG-SRC-012" in res003["observed_author_side_evidence"][
    "source_evidence"
  ]["present_source_ids"]
  assert "PIN-F16-003" in res003["observed_author_side_evidence"][
    "pin_evidence"
  ]["sanity_only_pin_ids"]
  assert "engineering hitboxes are not calibrated vulnerability geometry" in res003[
    "blocking_summary"
  ]

  res004 = artifact["closeout_checks"][2]
  assert res004["observed_author_side_evidence"]["warhead_scope_summary"][
    "weapon_class"
  ] == "AIM-120C-class"
  assert "PIN-AIM120-TPC-REJ" in res004["observed_author_side_evidence"][
    "pin_evidence"
  ]["rejected_pin_ids"]
  assert "variant-specific warhead mass" in res004["blocking_summary"]

  res005 = artifact["closeout_checks"][5]
  assert res005["observed_author_side_evidence"]["bm005_audit_outcome"] == (
    "candidate_hygiene_only_not_independent_validation"
  )
  assert res005["observed_author_side_evidence"][
    "stage_c_gate_band_fragment_energy_pass"
  ] is True
  assert "toy/integration hygiene" in res005["blocking_summary"]

  res006 = artifact["closeout_checks"][6]
  assert "PIN-BFM-001" in res006["observed_author_side_evidence"][
    "pin_evidence"
  ]["retention_pending_pin_ids"]
  assert "VPS-BFM-003" in res006["observed_author_side_evidence"][
    "source_evidence"
  ]["rejected_or_pending_source_ids"]
  assert "retained comparison outputs" in res006["blocking_summary"]

  assert artifact["residual_condition_trace"] == [
    {
      "residual_id": "RES-003",
      "author_side_satisfied_check_ids": [
        "CLOSEOUT-RES003-001",
        "CLOSEOUT-RES003-002",
      ],
      "release_grade_blocking_check_ids": [
        "CLOSEOUT-RES003-001",
        "CLOSEOUT-RES003-002",
      ],
      "gate_result": "blocked_author_side_review_ready",
    },
    {
      "residual_id": "RES-004",
      "author_side_satisfied_check_ids": [
        "CLOSEOUT-RES004-001",
        "CLOSEOUT-RES004-002",
      ],
      "release_grade_blocking_check_ids": [
        "CLOSEOUT-RES004-001",
        "CLOSEOUT-RES004-002",
      ],
      "gate_result": "blocked_author_side_review_ready",
    },
    {
      "residual_id": "RES-005",
      "author_side_satisfied_check_ids": [
        "CLOSEOUT-RES005-001",
        "CLOSEOUT-RES005-002",
      ],
      "release_grade_blocking_check_ids": [
        "CLOSEOUT-RES005-001",
        "CLOSEOUT-RES005-002",
      ],
      "gate_result": "blocked_author_side_review_ready",
    },
    {
      "residual_id": "RES-006",
      "author_side_satisfied_check_ids": [
        "CLOSEOUT-RES006-001",
        "CLOSEOUT-RES006-002",
      ],
      "release_grade_blocking_check_ids": [
        "CLOSEOUT-RES006-001",
        "CLOSEOUT-RES006-002",
      ],
      "gate_result": "blocked_author_side_review_ready",
    },
  ]


def test_mechanism_source_closeout_gate_keeps_authority_guards_false() -> None:
  artifact = gate.generate_mechanism_source_closeout_gate(repo_root=REPO_ROOT)

  guards = artifact["non_authoritative_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["target_geometry_authority_granted"] is False
  assert guards["aim120c_warhead_authority_granted"] is False
  assert guards["fragment_mechanism_authority_granted"] is False
  assert guards["blast_mechanism_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False

  evidence_summary = artifact["mechanism_load_evidence_summary"]
  assert evidence_summary["validation_scaffold_status"] == "not_run"
  assert evidence_summary["stage_b_all_hard_gates_pass"] is True
  assert evidence_summary["stage_b_review_status"] == (
    "author_snapshot_only_pending_independent_review"
  )
  assert evidence_summary["stage_c_baseline_component_probability_source"] == (
    "synthetic_sigmoid"
  )
  assert any("engineering hitboxes" in risk for risk in artifact["behavior_risks"])
  assert any("toy probes" in risk for risk in artifact["behavior_risks"])
  assert any("RES-013 Pk" in note for note in artifact["integration_notes"])
  assert any(
    "RES-014 deterministic fuze" in note for note in artifact["integration_notes"]
  )


def test_mechanism_source_closeout_gate_cli_writes_json(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "mechanism_source_closeout_gate.json"

  result = run_maintenance_cli(
    "damage_model.py scope-provenance",
    "mechanism-source-closeout",
    "--output",
    output_path,
  )

  assert result.stdout == ""
  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["schema_version"] == "a2.mechanism_source_closeout_gate.v1"
  assert artifact["current_gate_results"]["RES-003"] == (
    "blocked_author_side_review_ready"
  )
  assert artifact["current_gate_results"]["RES-006"] == (
    "blocked_author_side_review_ready"
  )
  assert artifact["non_authoritative_guards"]["pk_authority_granted"] is False
  assert (
    artifact["non_authoritative_guards"]["deterministic_fuze_authority_granted"]
    is False
  )
