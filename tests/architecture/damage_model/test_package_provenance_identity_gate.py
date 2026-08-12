from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path, read_json
from tests.architecture.damage_model.helpers import run_maintenance_cli

ensure_repo_root_on_sys_path()

from tools.maintenance.release_governance import package_provenance_identity as package_gate  # noqa: E402

pytestmark = pytest.mark.governance_audit


def test_package_provenance_identity_gate_is_blocked() -> None:
  artifact = package_gate.generate_package_provenance_identity_gate(
    repo_root=REPO_ROOT
  )

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.package_provenance_identity_gate.v1"
  assert (
    artifact["status"]
    == "blocked_non_authoritative_package_provenance_identity_candidate"
  )
  assert (
    artifact["review_target"]
    == "shared_provenance_and_surrogate_identity_surface"
  )
  assert (
    artifact["readiness_level"]
    == "author_side_pin_and_identity_surface_present_but_not_release_grade"
  )

  scope = artifact["scope"]
  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["aspect_bucket"] == "beam"
  assert scope["closure_bucket"] == "high"
  assert scope["miss_distance_bucket"] == "near_miss_0_35m"

  pin_summary = artifact["artifact_pin_manifest_summary"]
  assert pin_summary["manifest_status"] == "author_frozen_pending_independent_review"
  assert (
    pin_summary["package_provenance_status"]
    == "official_public_artifacts_partially_verified_release_grade_closeout_pending"
  )
  assert pin_summary["status_counts"]["verified_candidate_artifact"] == 2
  assert pin_summary["status_counts"]["pending_acquisition"] == 0
  assert pin_summary["status_counts"]["sanity_only"] >= 1

  identity = artifact["surrogate_identity_summary"]
  assert identity["model_ref"].startswith("candidate://a2/runtime-aligned-vps/")
  assert identity["model_version"] == "v0_candidate_runtime_aligned"
  assert len(identity["repo_commit"]) == 40
  assert (
    identity["worktree_state"]
    == "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present"
  )
  assert identity["retained_artifact_pack_status"] == "present_author_side_non_authoritative"
  assert identity["retained_artifact_count"] == 4
  assert identity["current_validation_status"] == "not_validated"
  assert identity["output_anchor_count"] >= 3

  retained = artifact["retained_artifact_pack_summary"]
  assert retained["stage_b"]["status"] == "author_retained_candidate_artifacts_only"
  assert retained["stage_b"]["manifest_exists"] is True
  assert retained["stage_b"]["retained_artifact_count"] == 4
  assert retained["stage_b"]["all_artifacts_exist"] is True
  assert (
    retained["stage_c"]["status"]
    == "author_retained_stage_c_component_probability_candidate_artifacts_only"
  )
  assert retained["stage_c"]["manifest_exists"] is True
  assert retained["stage_c"]["retained_artifact_count"] == 4
  assert retained["stage_c"]["all_artifacts_exist"] is True

  satisfied = artifact["satisfied_conditions"]
  assert [row["condition_id"] for row in satisfied] == [
    "READY-PI-001",
    "READY-PI-002",
    "READY-PI-003",
    "READY-PI-004",
    "READY-PI-005",
  ]
  assert satisfied[0]["residual_ids"] == ["RES-001", "RES-002"]

  blockers = artifact["blocking_conditions"]
  assert [row["blocker_id"] for row in blockers] == [
    "BLOCK-PI-001",
    "BLOCK-PI-002",
    "BLOCK-PI-003",
    "BLOCK-PI-004",
  ]
  assert artifact["blocking_residual_ids"] == [
    "RES-001",
    "RES-002",
    "RES-002",
    "RES-013/014-boundary",
  ]
  assert any("externally verified and checksummed" in row["summary"] for row in blockers)
  assert any("not in a clean release-grade identity state" in row["summary"] for row in blockers)
  assert any(
    "do not close release-grade surrogate identity" in row["summary"]
    for row in blockers
  )
  assert any("pk authority or deterministic fuze authority" in row["summary"] for row in blockers)

  trace = artifact["residual_condition_trace"]
  assert trace == [
    {
      "residual_id": "RES-001",
      "satisfied_condition_ids": ["READY-PI-001", "READY-PI-002"],
      "blocking_condition_ids": ["BLOCK-PI-001"],
      "gate_result": "blocked",
    },
    {
      "residual_id": "RES-002",
      "satisfied_condition_ids": [
        "READY-PI-001",
        "READY-PI-003",
        "READY-PI-004",
        "READY-PI-005",
      ],
      "blocking_condition_ids": ["BLOCK-PI-002", "BLOCK-PI-003"],
      "gate_result": "blocked",
    },
  ]

  boundaries = artifact["explicit_boundaries"]
  assert "do not treat author-side retained packs as release-grade identity closure" in boundaries
  assert "do not treat candidate or sanity-only pins as acquired authority inputs" in boundaries

  guards = artifact["non_authoritative_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["effect_scale_authority_in_stock"] is False
  assert guards["component_failure_probability_authority_in_stock"] is False
  assert guards["pk_authority"] is False
  assert guards["deterministic_fuze_authority"] is False


def test_package_provenance_identity_gate_fails_closed_for_optimistic_release_fields(
  monkeypatch,
) -> None:
  original_read_text = package_gate._read_text

  def optimistic_read_text(path: Path) -> str:
    text = original_read_text(path)
    if path == package_gate.DOC_REFS["artifact_pin_manifest"]:
      return text.replace(
        "official_public_artifacts_partially_verified_release_grade_closeout_pending",
        "release_grade_closed",
      )
    if path == package_gate.DOC_REFS["surrogate_identity_manifest"]:
      return text.replace(
        "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present",
        "clean_release_candidate",
      )
    return text

  monkeypatch.setattr(package_gate, "_read_text", optimistic_read_text)

  artifact = package_gate.generate_package_provenance_identity_gate(
    repo_root=REPO_ROOT
  )

  blockers = artifact["blocking_conditions"]
  assert (
    artifact["status"]
    == "blocked_non_authoritative_package_provenance_identity_candidate"
  )
  assert [row["blocker_id"] for row in blockers] == [
    "BLOCK-PI-001",
    "BLOCK-PI-003",
    "BLOCK-PI-004",
  ]
  assert any("candidate-only, sanity-only or pending" in row["summary"] for row in blockers)
  assert any(
    "do not close release-grade surrogate identity" in row["summary"]
    for row in blockers
  )
  assert artifact["residual_condition_trace"][0]["blocking_condition_ids"] == [
    "BLOCK-PI-001"
  ]
  assert artifact["residual_condition_trace"][1]["blocking_condition_ids"] == [
    "BLOCK-PI-003"
  ]
  assert artifact["non_authoritative_guards"]["stock_database_authority_granted"] is False
  assert artifact["non_authoritative_guards"]["effect_scale_authority_in_stock"] is False
  assert (
    artifact["non_authoritative_guards"][
      "component_failure_probability_authority_in_stock"
    ]
    is False
  )


def test_package_provenance_identity_gate_fails_closed_on_placeholder_hits(
  monkeypatch,
) -> None:
  original_read_text = package_gate._read_text

  def placeholder_read_text(path: Path) -> str:
    text = original_read_text(path)
    if path == package_gate.DOC_REFS["validation_provenance_identity_gate"]:
      return f"{text}\n<待填>\n"
    return text

  monkeypatch.setattr(package_gate, "_read_text", placeholder_read_text)

  artifact = package_gate.generate_package_provenance_identity_gate(
    repo_root=REPO_ROOT
  )

  assert "READY-PI-001" not in [
    row["condition_id"] for row in artifact["satisfied_conditions"]
  ]
  assert artifact["blocking_conditions"][0] == {
    "blocker_id": "BLOCK-PI-000",
    "residual_id": "RES-001/002",
    "summary": (
      "placeholder text remains in package provenance or "
      "surrogate-identity documentation"
    ),
  }
  assert artifact["residual_condition_trace"][0]["blocking_condition_ids"][0] == (
    "BLOCK-PI-000"
  )
  assert artifact["residual_condition_trace"][1]["blocking_condition_ids"][0] == (
    "BLOCK-PI-000"
  )


def test_package_provenance_identity_gate_cli_writes_json(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "a2_package_provenance_identity_gate.json"

  run_maintenance_cli(
    "damage_model.py release-governance",
    "package-provenance-identity",
    "--output",
    output_path,
    capture_output=False,
  )

  artifact = read_json(output_path)
  assert (
    artifact["status"]
    == "blocked_non_authoritative_package_provenance_identity_candidate"
  )
  assert artifact["blocking_conditions"][0]["blocker_id"] == "BLOCK-PI-001"
