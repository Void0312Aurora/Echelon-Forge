from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.scope_provenance import ( # noqa: E402
  geometry_warhead_row_provenance as row_provenance_gate,
  target_geometry_closeout as target_geometry_gate,
  warhead_scope_closeout as warhead_scope_gate,
)

pytestmark = pytest.mark.governance_audit


@pytest.fixture(scope="module")
def target_geometry_closeout_artifact() -> dict[str, Any]:
  return target_geometry_gate.generate_res003_target_geometry_closeout_gate(
    repo_root=REPO_ROOT
  )


@pytest.fixture(scope="module")
def warhead_family_closeout_artifact() -> dict[str, Any]:
  return warhead_scope_gate.generate_res004_warhead_scope_closeout_gate(
    repo_root=REPO_ROOT
  )


@pytest.fixture(scope="module")
def row_provenance_artifact() -> dict[str, Any]:
  return row_provenance_gate.generate_geometry_warhead_row_provenance_gate(
    repo_root=REPO_ROOT
  )


def test_target_geometry_scope_closeout_records_stage_b_identity(
  target_geometry_closeout_artifact: dict[str, Any],
) -> None:
  artifact = target_geometry_closeout_artifact

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.res003_target_geometry_closeout_gate.v1"
  assert artifact["status"] == (
    "res003_stage_b_effect_scale_witness_geometry_closeout_pass_release_blocked"
  )
  assert artifact["release_target"] == (
    "stage_b_effect_scale_witness_geometry_bookkeeping_only"
  )
  assert artifact["missing_evidence"] == []


def test_target_geometry_scope_closeout_consumes_required_evidence(
  target_geometry_closeout_artifact: dict[str, Any],
) -> None:
  artifact = target_geometry_closeout_artifact
  evidence = {row["evidence_id"]: row for row in artifact["consumed_evidence"]}

  assert set(evidence) == {
    "residual_register",
    "target_geometry_assumptions",
    "geometry_warhead_row_provenance_gate",
    "stage_b_independent_review_gate",
    "scope_bucket_independent_review_gate",
  }
  for row in evidence.values():
    assert row["present"] is True
    assert len(row["content_sha256"]) == 64
    assert row["content_hash"] == f"sha256:{row['content_sha256']}"
    assert row["size_bytes"] > 0


def test_target_geometry_scope_closeout_bounds_stage_b_assumptions(
  target_geometry_closeout_artifact: dict[str, Any],
) -> None:
  artifact = target_geometry_closeout_artifact
  assumption = artifact["stage_b_assumption_review"]

  assert assumption["status"] == "stage_b_assumption_surface_bounded"
  assert assumption["used_by_stage_b_geometry_items"] == [
    "outer_bbox",
    "beam_witness_panel",
  ]
  assert set(assumption["stage_b_source_ids"]) >= {
    "F16-TG-SRC-001",
    "F16-TG-SRC-002",
    "F16-TG-SRC-012",
  }
  assert assumption["row_findings"]["outer_bbox"]["support_level"] == (
    "candidate_dimension_anchor"
  )
  assert assumption["row_findings"]["beam_witness_panel"]["support_level"] == (
    "repo_authored_witness_geometry"
  )
  assert assumption["row_findings"]["right_aileron_actuator_projection"][
    "used_by_stage_b"
  ] == "no_for_stage_b_effect_scale_only"
  assert assumption["row_findings"]["internal_material_or_armor"][
    "support_level"
  ] == "unsupported"
  assert assumption["row_findings"]["occlusion_and_exposed_area_truth"][
    "support_level"
  ] == "unsupported"
  assert all(row["pass"] for row in assumption["checks"])


def test_target_geometry_scope_closeout_preserves_review_interlocks(
  target_geometry_closeout_artifact: dict[str, Any],
) -> None:
  artifact = target_geometry_closeout_artifact
  provenance = artifact["provenance_interlock"]

  assert provenance["status"] == "row_provenance_interlock_preserved"
  assert provenance["upstream_res003_status"]["author_side_subslice_ready"] is True
  assert provenance["upstream_res003_status"]["release_grade"] is False
  assert provenance["upstream_res003_status"]["closed_by_this_gate"] is False
  assert all(row["pass"] for row in provenance["checks"])

  stage_b = artifact["stage_b_review_interlock"]
  assert stage_b["status"] == "stage_b_review_interlock_bounded"
  assert stage_b["bfm_bm_003_independence_row"]["allowed_claim"] == (
    "sampling replay and convergence inside witness-geometry bookkeeping"
  )
  assert stage_b["bfm_bm_003_independence_row"]["forbidden_claim"] == (
    "true F-16 exposure geometry or direction-pattern truth"
  )
  assert all(row["pass"] for row in stage_b["checks"])


def test_target_geometry_scope_closeout_blocks_global_release_authority(
  target_geometry_closeout_artifact: dict[str, Any],
) -> None:
  artifact = target_geometry_closeout_artifact
  res003 = artifact["residual_closeout_decisions"]["RES-003"]

  assert res003["stage_b_effect_scale_witness_geometry"] == (
    "closed_narrow_non_authoritative"
  )
  assert res003["closed_residual_subscope"] == (
    "stage_b_effect_scale_witness_geometry_bookkeeping"
  )
  assert res003["global_target_geometry_authority"] == "not_granted"
  assert res003["real_f16_component_geometry_material_occlusion"] == "blocked"
  assert res003["phase5_component_probability_geometry_dependency"] == "blocked"
  assert res003["residual_register_edit_required_by_this_gate"] is False

  decision = artifact["closeout_decision"]
  assert decision["stage_b_effect_scale_witness_geometry_closeout_complete"] is True
  assert decision["stage_b_effect_scale_closeout_is_release_authority"] is False
  assert decision["global_res003_target_geometry_closeout_complete"] is False
  assert decision["real_f16_vulnerability_geometry_closeout_complete"] is False
  assert decision["closed_residual_ids_by_this_gate"] == []
  assert decision["closed_residual_subscopes_by_this_gate"] == [
    "RES-003:stage_b_effect_scale_witness_geometry_bookkeeping"
  ]
  assert decision["release_ready"] is False
  assert decision["release_blocked"] is True


def test_target_geometry_scope_closeout_keeps_authority_guards_false() -> None:
  artifact = target_geometry_gate.generate_res003_target_geometry_closeout_gate(
    repo_root=REPO_ROOT
  )

  guards = artifact["authority_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["target_geometry_authority_granted"] is False
  assert guards["target_component_geometry_authority_granted"] is False
  assert guards["target_material_authority_granted"] is False
  assert guards["target_occlusion_authority_granted"] is False
  assert guards["witness_geometry_bookkeeping_promoted_to_truth"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False
  assert not any(value is True for value in guards.values())

  boundaries = "\n".join(artifact["explicit_boundaries"])
  assert "Stage B effect-scale witness-geometry bookkeeping" in boundaries
  assert "not true 3D exposure geometry" in boundaries
  assert "No real F-16 component coordinates" in boundaries
  assert "Phase 5 component_failure_probability authority remains blocked" in boundaries


def test_target_geometry_scope_closeout_fails_closed_without_evidence(
  tmp_path: Path,
) -> None:
  artifact = target_geometry_gate.generate_res003_target_geometry_closeout_gate(
    repo_root=REPO_ROOT,
    package_dir=tmp_path,
  )

  assert artifact["status"] == "res003_target_geometry_closeout_fail_closed"
  assert artifact["closeout_decision"][
    "stage_b_effect_scale_witness_geometry_closeout_complete"
  ] is False
  assert artifact["residual_closeout_decisions"]["RES-003"][
    "stage_b_effect_scale_witness_geometry"
  ] == "fail_closed"
  assert artifact["closeout_decision"]["closed_residual_subscopes_by_this_gate"] == []
  assert [row["evidence_id"] for row in artifact["missing_evidence"]] == [
    "residual_register",
    "target_geometry_assumptions",
    "geometry_warhead_row_provenance_gate",
    "stage_b_independent_review_gate",
    "scope_bucket_independent_review_gate",
  ]
  assert artifact["minimum_gap_list"][0]["gap_id"] == "missing:residual_register"
  assert artifact["authority_guards"]["pk_authority_granted"] is False
  assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_target_geometry_scope_closeout_cli_writes_retained_json_and_doc(
  tmp_path: Path,
) -> None:
  output_dir = tmp_path / "res003_target_geometry_closeout_20260531"
  doc_output = tmp_path / "validation_res003_target_geometry_closeout_gate.md"
  result = subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "scope-provenance",
      "target-geometry-closeout",
      "--output-dir",
      str(output_dir),
      "--doc-output",
      str(doc_output),
    ],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )

  command_summary = json.loads(result.stdout)
  assert command_summary["status"] == (
    "res003_stage_b_effect_scale_witness_geometry_closeout_pass_release_blocked"
  )
  gate_path = output_dir / "res003_target_geometry_closeout_gate.json"
  manifest_path = output_dir / "manifest.json"
  assert gate_path.is_file()
  assert manifest_path.is_file()
  assert doc_output.is_file()

  artifact = json.loads(gate_path.read_text(encoding="utf-8"))
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert artifact["closeout_decision"][
    "stage_b_effect_scale_witness_geometry_closeout_complete"
  ] is True
  assert artifact["closeout_decision"]["release_ready"] is False
  assert manifest["schema_version"] == (
    "a2.res003_target_geometry_closeout_manifest.v1"
  )
  assert manifest["status"] == "res003_target_geometry_closeout_retained_release_blocked"
  assert manifest["artifacts"][0]["artifact_key"] == (
    "res003_target_geometry_closeout_gate"
  )
  assert manifest["artifacts"][0]["content_sha256"] == command_summary[
    "gate_sha256"
  ]
  assert manifest["authority_guards"]["target_geometry_authority_granted"] is False
  assert "RES-003 is narrowly closed only for Stage B effect-scale witness-geometry bookkeeping" in doc_output.read_text(
    encoding="utf-8"
  )


def test_warhead_family_scope_closeout_records_stage_b_identity(
  warhead_family_closeout_artifact: dict[str, Any],
) -> None:
  artifact = warhead_family_closeout_artifact

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.res004_warhead_scope_closeout_gate.v1"
  assert artifact["status"] == (
    "res004_stage_b_effect_scale_warhead_family_scope_closeout_pass_release_blocked"
  )
  assert artifact["release_target"] == (
    "stage_b_effect_scale_aim120c_class_blast_fragmentation_family_scope_only"
  )
  assert artifact["missing_evidence"] == []


def test_warhead_family_scope_closeout_consumes_required_evidence(
  warhead_family_closeout_artifact: dict[str, Any],
) -> None:
  artifact = warhead_family_closeout_artifact
  evidence = {row["evidence_id"]: row for row in artifact["consumed_evidence"]}

  assert set(evidence) == {
    "residual_register",
    "warhead_scope_and_sensitivity",
    "artifact_pin_manifest",
    "warhead_source_ledger",
    "geometry_warhead_row_provenance_gate",
    "mechanism_source_closeout_gate",
  }
  for row in evidence.values():
    assert row["present"] is True
    assert len(row["content_sha256"]) == 64
    assert row["content_hash"] == f"sha256:{row['content_sha256']}"
    assert row["size_bytes"] > 0


def test_warhead_family_scope_closeout_bounds_stage_b_scope(
  warhead_family_closeout_artifact: dict[str, Any],
) -> None:
  artifact = warhead_family_closeout_artifact
  scope = artifact["stage_b_scope_review"]

  assert scope["status"] == "stage_b_warhead_family_scope_surface_bounded"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["consumed_by_surrogate_assumptions"] == [
    "WAR-001",
    "WAR-002",
    "WAR-005",
  ]
  assert scope["non_release_assumptions"] == [
    "WAR-003",
    "WAR-004",
    "WAR-006",
    "WAR-007",
  ]
  assert all(row["pass"] for row in scope["checks"])

  rows = scope["row_findings"]
  assert rows["WAR-001"]["sensitivity_axis"] == "family gate / vocabulary"
  assert rows["WAR-002"]["consumed_by_surrogate"] == "yes"
  assert rows["WAR-002"]["sensitivity_axis"] == (
    "blast scaled-distance proxy, toy fragment-count / energy proxy"
  )
  assert rows["WAR-003"]["consumed_by_surrogate"] == "loaded_but_not_release_gating"
  assert rows["WAR-004"]["consumed_by_surrogate"] == "no_numeric_consumption"
  assert rows["WAR-006"]["consumed_by_surrogate"] == "no_for_stage_b_release"
  assert rows["WAR-007"]["consumed_by_surrogate"] == "no"
  assert rows["WAR-007"]["third_party_candidates"].startswith("rejected:")


def test_warhead_family_scope_closeout_records_source_pin_boundary(
  warhead_family_closeout_artifact: dict[str, Any],
) -> None:
  artifact = warhead_family_closeout_artifact
  source_pin = artifact["source_pin_review"]

  assert source_pin["status"] == "source_pin_boundary_bounded"
  assert source_pin["res004_pin_ids"] == [
    "PIN-AIM120-001",
    "PIN-AIM120-002",
    "PIN-AIM120-TPC-001",
    "PIN-AIM120-TPC-REJ",
  ]
  assert source_pin["release_consumed_pin_ids"] == []
  assert source_pin["pin_consumption_status"]["PIN-AIM120-TPC-001"] == "sanity_only"
  assert source_pin["pin_consumption_status"]["PIN-AIM120-TPC-REJ"] == "rejected"
  assert all(source_pin["source_presence"].values())
  assert all(row["pass"] for row in source_pin["checks"])


def test_warhead_family_scope_closeout_preserves_provenance_and_mechanism_interlocks(
  warhead_family_closeout_artifact: dict[str, Any],
) -> None:
  artifact = warhead_family_closeout_artifact
  provenance = artifact["provenance_interlock"]

  assert provenance["status"] == "row_provenance_interlock_preserved"
  assert provenance["upstream_res004_status"]["author_side_subslice_ready"] is True
  assert provenance["upstream_res004_status"]["release_grade"] is False
  assert provenance["upstream_res004_status"]["closed_by_this_gate"] is False
  assert all(row["pass"] for row in provenance["checks"])

  mechanism = artifact["mechanism_source_interlock"]
  assert mechanism["status"] == "mechanism_source_interlock_bounded"
  assert mechanism["upstream_res004_result"] == "blocked_author_side_review_ready"
  assert any(
    "family label is separated" in item
    for item in mechanism["closed_author_side_subitems"]
  )
  assert all(row["pass"] for row in mechanism["checks"])


def test_warhead_family_scope_closeout_blocks_release_authority(
  warhead_family_closeout_artifact: dict[str, Any],
) -> None:
  artifact = warhead_family_closeout_artifact
  res004 = artifact["residual_closeout_decisions"]["RES-004"]

  assert res004["stage_b_effect_scale_warhead_family_scope"] == (
    "closed_narrow_non_authoritative"
  )
  assert res004["closed_residual_subscope"] == (
    "stage_b_effect_scale_aim120c_class_blast_fragmentation_family_scope"
  )
  assert res004["missile_specific_aim120c_warhead_truth"] == "forbidden"
  assert res004["variant_specific_mass_tnt_fragment_pattern"] == "blocked"
  assert res004["toy_numeric_proxy_authority"] == "not_granted"
  assert res004["deterministic_fuze_dependency"] == "forbidden"
  assert res004["pk_dependency"] == "forbidden"
  assert res004["component_probability_dependency"] == "blocked"
  assert res004["residual_register_edit_required_by_this_gate"] is False

  decision = artifact["closeout_decision"]
  assert (
    decision["stage_b_effect_scale_warhead_family_scope_closeout_complete"]
    is True
  )
  assert decision["stage_b_effect_scale_closeout_is_release_authority"] is False
  assert decision["aim120c_specific_warhead_truth_closeout_complete"] is False
  assert decision["deterministic_fuze_closeout_complete"] is False
  assert decision["component_probability_release_ready"] is False
  assert decision["closed_residual_ids_by_this_gate"] == []
  assert decision["closed_residual_subscopes_by_this_gate"] == [
    "RES-004:stage_b_effect_scale_aim120c_class_blast_fragmentation_family_scope"
  ]
  assert decision["release_ready"] is False
  assert decision["release_blocked"] is True


def test_warhead_family_scope_closeout_keeps_authority_guards_false() -> None:
  artifact = warhead_scope_gate.generate_res004_warhead_scope_closeout_gate(
    repo_root=REPO_ROOT
  )

  guards = artifact["authority_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["runtime_descriptor_created"] is False
  assert guards["aim120c_warhead_authority_granted"] is False
  assert guards["missile_specific_warhead_truth_granted"] is False
  assert guards["variant_specific_warhead_mass_authority_granted"] is False
  assert guards["tnt_equivalent_authority_granted"] is False
  assert guards["fragment_pattern_authority_granted"] is False
  assert guards["toy_warhead_numeric_proxy_promoted_to_authority"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False
  assert guards["fuze_authority_granted"] is False
  assert not any(value is True for value in guards.values())

  boundaries = "\n".join(artifact["explicit_boundaries"])
  assert "Stage B effect-scale AIM-120C-class blast-fragmentation family scope" in boundaries
  assert "not AIM-120C-7/C-8 warhead truth" in boundaries
  assert "repo warhead.mass_kg" in boundaries
  assert "third-party 40 lb / 18 kg claims remain sanity-only" in boundaries
  assert "deterministic fuze" in boundaries


def test_warhead_family_scope_closeout_fails_closed_without_evidence(
  tmp_path: Path,
) -> None:
  artifact = warhead_scope_gate.generate_res004_warhead_scope_closeout_gate(
    repo_root=tmp_path,
    package_dir=tmp_path,
  )

  assert artifact["status"] == "res004_warhead_scope_closeout_fail_closed"
  assert artifact["closeout_decision"][
    "stage_b_effect_scale_warhead_family_scope_closeout_complete"
  ] is False
  assert artifact["residual_closeout_decisions"]["RES-004"][
    "stage_b_effect_scale_warhead_family_scope"
  ] == "fail_closed"
  assert artifact["closeout_decision"]["closed_residual_subscopes_by_this_gate"] == []
  assert [row["evidence_id"] for row in artifact["missing_evidence"]] == [
    "residual_register",
    "warhead_scope_and_sensitivity",
    "artifact_pin_manifest",
    "warhead_source_ledger",
    "geometry_warhead_row_provenance_gate",
    "mechanism_source_closeout_gate",
  ]
  assert artifact["minimum_gap_list"][0]["gap_id"] == "missing:residual_register"
  assert artifact["authority_guards"]["pk_authority_granted"] is False
  assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_warhead_family_scope_closeout_cli_writes_retained_json_and_doc(
  tmp_path: Path,
) -> None:
  output_dir = tmp_path / "res004_warhead_scope_closeout_20260531"
  doc_output = tmp_path / "validation_res004_warhead_scope_closeout_gate.md"
  result = subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "scope-provenance",
      "warhead-scope-closeout",
      "--output-dir",
      str(output_dir),
      "--doc-output",
      str(doc_output),
    ],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )

  command_summary = json.loads(result.stdout)
  assert command_summary["status"] == (
    "res004_stage_b_effect_scale_warhead_family_scope_closeout_pass_release_blocked"
  )
  gate_path = output_dir / "res004_warhead_scope_closeout_gate.json"
  manifest_path = output_dir / "manifest.json"
  assert gate_path.is_file()
  assert manifest_path.is_file()
  assert doc_output.is_file()

  artifact = json.loads(gate_path.read_text(encoding="utf-8"))
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert artifact["closeout_decision"][
    "stage_b_effect_scale_warhead_family_scope_closeout_complete"
  ] is True
  assert artifact["closeout_decision"]["release_ready"] is False
  assert manifest["schema_version"] == "a2.res004_warhead_scope_closeout_manifest.v1"
  assert manifest["status"] == "res004_warhead_scope_closeout_retained_release_blocked"
  assert manifest["artifacts"][0]["artifact_key"] == (
    "res004_warhead_scope_closeout_gate"
  )
  assert manifest["artifacts"][0]["content_sha256"] == command_summary[
    "gate_sha256"
  ]
  assert manifest["authority_guards"]["aim120c_warhead_authority_granted"] is False
  assert "RES-004 is narrowly closed only for Stage B effect-scale AIM-120C-class blast-fragmentation family scope" in doc_output.read_text(
    encoding="utf-8"
  )



# Row provenance keeps scope closeout bounded and non-authoritative.
def test_geometry_warhead_row_provenance_records_blocked_candidate_identity(
  row_provenance_artifact: dict[str, Any],
) -> None:
  artifact = row_provenance_artifact

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == (
    "a2.geometry_warhead_row_provenance_gate.v1"
  )
  assert artifact["status"] == (
    "blocked_non_authoritative_geometry_warhead_row_provenance_candidate"
  )
  assert artifact["decision"]["release_grade_for_current_narrow_scope"] is False
  assert artifact["decision"]["closed_residual_ids_by_this_gate"] == []
  assert artifact["decision"]["blocking_residual_ids"] == ["RES-003", "RES-004"]


def test_geometry_warhead_row_provenance_consumes_required_inputs(
  row_provenance_artifact: dict[str, Any],
) -> None:
  artifact = row_provenance_artifact
  assert artifact["missing_inputs"] == []
  required_inputs = {
    row["input_id"]: row for row in artifact["consumed_inputs"] if row["required"]
  }

  assert set(required_inputs) == {
    "subagent_usage_policy",
    "residual_register",
    "target_geometry_assumptions",
    "warhead_scope_and_sensitivity",
    "artifact_pin_manifest",
    "target_geometry_source_ledger",
    "warhead_source_ledger",
  }
  assert required_inputs["subagent_usage_policy"]["path"] == (
    "docs/engineering/automation/standards/subagent_usage_policy.md"
  )
  for row in required_inputs.values():
    assert row["exists"] is True
    assert len(row["sha256"]) == 64
    assert row["content_hash"] == f"sha256:{row['sha256']}"
    assert row["size_bytes"] > 0


def test_geometry_warhead_row_provenance_blocks_residual_statuses(
  row_provenance_artifact: dict[str, Any],
) -> None:
  artifact = row_provenance_artifact
  residual_status = artifact["residual_status"]

  assert residual_status["RES-003"]["status"] == "blocked_row_level_bounds_missing"
  assert residual_status["RES-003"]["register"]["register_status"] == (
    "research_closed_stage_b_witness_geometry_bookkeeping_authority_blocked_global_geometry"
  )
  assert residual_status["RES-003"]["closed_by_this_gate"] is False
  assert residual_status["RES-004"]["status"] == "blocked_warhead_class_bounds_missing"
  assert residual_status["RES-004"]["register"]["register_status"] == (
    "research_closed_stage_b_family_scope_authority_blocked_specific_warhead_truth"
  )
  assert residual_status["RES-004"]["closed_by_this_gate"] is False


def test_geometry_warhead_row_provenance_records_gate_checks(
  row_provenance_artifact: dict[str, Any],
) -> None:
  artifact = row_provenance_artifact

  assert [check["check_id"] for check in artifact["gate_checks"]] == [
    "ROWWAR-RES003-001",
    "ROWWAR-RES003-002",
    "ROWWAR-RES004-001",
    "ROWWAR-RES004-002",
  ]
  assert not any(check["release_grade_satisfied"] for check in artifact["gate_checks"])


def test_geometry_warhead_row_provenance_records_res003_row_blockers(
  row_provenance_artifact: dict[str, Any],
) -> None:
  artifact = row_provenance_artifact
  res003_rows = artifact["gate_checks"][0]["evidence"]["row_findings"]

  assert {row["geometry_item"] for row in res003_rows} >= {
    "outer_bbox",
    "beam_witness_panel",
    "internal_material_or_armor",
    "occlusion_and_exposed_area_truth",
  }
  assert {
    row["blocker"] for row in res003_rows if row["geometry_item"] == "outer_bbox"
  } == {"dimension_anchor_has_no_reviewed_row_level_error_bound"}
  assert {
    tuple(row["source_ids"])
    for row in res003_rows
    if row["geometry_item"] == "outer_bbox"
  } == {("F16-TG-SRC-001", "F16-TG-SRC-002", "F16-TG-SRC-012")}
  assert {
    row["blocker"]
    for row in res003_rows
    if row["geometry_item"] == "beam_witness_panel"
  } == {"repo_authored_witness_geometry_lacks_true_3d_exposure_bounds"}


def test_geometry_warhead_row_provenance_records_res004_row_blockers(
  row_provenance_artifact: dict[str, Any],
) -> None:
  artifact = row_provenance_artifact
  res004_rows = artifact["gate_checks"][2]["evidence"]["row_findings"]

  assert {row["assumption_id"] for row in res004_rows} >= {
    "WAR-001",
    "WAR-002",
    "WAR-006",
    "WAR-007",
  }
  assert {
    row["blocker"] for row in res004_rows if row["assumption_id"] == "WAR-002"
  } == {"repo_toy_numeric_input_not_calibrated_aim120c_truth"}
  assert {
    tuple(row["source_ids"])
    for row in res004_rows
    if row["assumption_id"] == "WAR-005"
  } == {
    (
      "PHYS-BF-001",
      "PHYS-BF-002",
      "PHYS-BF-006",
      "PHYS-BF-013",
      "PHYS-BF-014",
      "PHYS-BF-015",
    )
  }
  assert "repo warhead.mass_kg and lethal_radius fields are toy inputs/bookkeeping, not calibrated AIM-120C truth" in artifact[
    "release_blockers"
  ]["RES-004"]


def test_geometry_warhead_row_provenance_keeps_authority_guards_false() -> None:
  artifact = row_provenance_gate.generate_geometry_warhead_row_provenance_gate(repo_root=REPO_ROOT)

  guards = artifact["authority_guard"]
  assert guards == {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "target_geometry_authority_granted": False,
    "row_level_geometry_authority_granted": False,
    "aim120c_warhead_authority_granted": False,
    "warhead_class_authority_granted": False,
    "effect_scale_authority_granted": False,
    "component_failure_probability_authority_granted": False,
    "pk_authority_granted": False,
    "deterministic_fuze_authority_granted": False,
    "fuze_authority_granted": False,
  }
  assert artifact["decision"]["authority_release_included"] is False
  assert any("RES-013 Pk" in note for note in artifact["integration_notes"])
  assert any(
    "RES-014 deterministic fuze" in note for note in artifact["integration_notes"]
  )


def test_geometry_warhead_row_provenance_cli_writes_retained_artifacts(
  tmp_path: Path,
) -> None:
  retained_dir = tmp_path / "retained"
  doc_output = tmp_path / "validation_geometry_warhead_row_provenance_gate.md"

  result = subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "scope-provenance",
      "row-provenance",
      "--retained-dir",
      str(retained_dir),
      "--doc-output",
      str(doc_output),
    ],
    cwd=REPO_ROOT,
    check=True,
    text=True,
    capture_output=True,
  )

  summary = json.loads(result.stdout)
  gate_path = REPO_ROOT / summary["gate_path"]
  manifest_path = REPO_ROOT / summary["manifest_path"]
  assert gate_path == retained_dir / "geometry_warhead_row_provenance_gate.json"
  assert manifest_path == retained_dir / "manifest.json"
  assert doc_output.exists()

  written_gate = json.loads(gate_path.read_text(encoding="utf-8"))
  written_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert written_gate["residual_status"]["RES-003"]["status"] == (
    "blocked_row_level_bounds_missing"
  )
  assert written_gate["residual_status"]["RES-004"]["status"] == (
    "blocked_warhead_class_bounds_missing"
  )
  assert written_manifest["artifacts"][0]["sha256"] == summary["gate_sha256"]
  assert written_manifest["release_grade_for_current_narrow_scope"] is False
  assert "RES-003/004 have machine-readable author-side row provenance evidence" in doc_output.read_text(
    encoding="utf-8"
  )
