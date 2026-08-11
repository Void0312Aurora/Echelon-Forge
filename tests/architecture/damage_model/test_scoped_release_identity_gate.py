from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path

ensure_repo_root_on_sys_path()

from tools.maintenance.release_governance import scoped_release_identity as scoped_identity_gate  # noqa: E402


def test_scoped_release_identity_gate_passes_scoped_surface() -> None:
  artifact = scoped_identity_gate.generate_res002_scoped_release_identity_gate(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.res002_scoped_release_identity_gate.v1"
  assert artifact["status"] == "scoped_res002_identity_pass_non_authoritative"
  assert artifact["decision"]["res002_scoped_package_identity"] == (
    "narrow_scoped_identity_pass"
  )
  assert artifact["decision"]["res002_residual_register_status_change"] == (
    "not_applied"
  )
  assert artifact["decision"]["release_validation_status_promoted"] is False
  assert artifact["decision"]["authority_release_included"] is False
  assert artifact["decision"]["global_release_identity_claimed"] is False

  model_identity = artifact["model_identity"]
  assert model_identity["model_ref"] == (
    "candidate://a2/runtime-aligned-vps/"
    "f16c-aim120c-blastfrag-beam-high-nearmiss-0_35m-v0"
  )
  assert model_identity["model_version"] == "v0_candidate_runtime_aligned"
  assert len(model_identity["head_commit"]) == 40
  assert model_identity["identity_manifest_validation_status"] == "not_validated"

  checks = artifact["identity_surface_checks"]
  assert checks["all_relevant_files_exist"] is True
  assert checks["required_retained_artifacts_under_repo_paths"] is True
  assert checks["source_payload_pack_retained_and_hash_verified"] is True
  assert checks["provenance_identity_review_consumed"] is True
  assert checks["authority_guards_all_false"] is True
  assert checks["missing_forbidden_outputs"] == []
  assert checks["legacy_identity_manifest_temp_anchor_count"] >= 3

  assert artifact["temporary_anchor_scan"]["scoped_surface_anchor_count"] == 0
  assert artifact["temporary_anchor_scan"]["scoped_surface_contains_temp_anchors"] is False
  assert scoped_identity_gate.TEMP_ANCHOR not in json.dumps(artifact, sort_keys=True)

  assert len(artifact["retained_artifact_directory_summary"]) == 8
  assert all(
    row["exists"] and row["file_count"] > 0
    for row in artifact["retained_artifact_directory_summary"]
  )
  assert len(artifact["retained_artifact_hash_inventory"]) >= 20
  assert len(artifact["relevant_file_hash_inventory"]) == len(scoped_identity_gate.DOC_REFS)
  assert all(row["sha256"] for row in artifact["relevant_file_hash_inventory"])
  relevant_files = {
    row["role"]: row for row in artifact["relevant_file_hash_inventory"]
  }
  assert relevant_files["subagent_usage_policy"]["relative_path"] == (
    "docs/engineering/automation/standards/subagent_usage_policy.md"
  )
  assert artifact["dirty_worktree_note"]["global_worktree_dirty"] is True
  assert artifact["dirty_worktree_note"]["unrelated_dirty_path_count"] > 0
  assert artifact["policy_evaluation"]["standards_global_clean_policy"][
    "global_clean_worktree_required"
  ] is False

  guards = artifact["authority_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["runtime_authority_granted"] is False
  assert guards["effect_scale_authority_released"] is False
  assert guards["component_failure_probability_authority_released"] is False
  assert guards["pk_authority_released"] is False
  assert guards["deterministic_fuze_authority_released"] is False
  assert guards["validation_status_promoted"] is False
  assert guards["residual_register_edited"] is False


def test_scoped_release_identity_gate_fails_closed_when_global_clean_required() -> None:
  artifact = scoped_identity_gate.generate_res002_scoped_release_identity_gate(
    repo_root=REPO_ROOT,
    force_global_clean_required=True,
  )

  assert artifact["status"] == "failed_closed_global_clean_worktree_required"
  assert artifact["decision"]["res002_scoped_package_identity"] == "fail_closed"
  assert artifact["decision"]["global_clean_worktree_required"] is True
  assert artifact["policy_evaluation"][
    "global_dirty_policy_required_and_unsatisfied"
  ] is True
  assert "globally clean worktree" in artifact["decision"]["fail_closed_reason"]
  assert artifact["dirty_worktree_note"]["global_worktree_dirty"] is True
  assert artifact["decision"]["release_validation_status_promoted"] is False
  assert not any(artifact["authority_guards"].values())


def test_scoped_release_identity_gate_writes_retained_bundle(
  tmp_path: Path,
) -> None:
  manifest = scoped_identity_gate.write_retained_scoped_identity_artifact(
    repo_root=REPO_ROOT,
    retained_output_dir=tmp_path,
  )

  artifact_path = tmp_path / scoped_identity_gate.GATE_FILENAME
  manifest_path = tmp_path / scoped_identity_gate.MANIFEST_FILENAME
  artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

  assert manifest_path.exists()
  assert artifact_path.exists()
  assert manifest["schema_version"] == "a2.res002_scoped_release_identity_manifest.v1"
  assert manifest["scoped_gate_status"] == artifact["status"]
  assert manifest["scoped_identity_decision"] == "narrow_scoped_identity_pass"
  assert manifest["retained_input_directory_count"] == 8
  assert manifest["retained_input_artifact_count"] == len(
    artifact["retained_artifact_hash_inventory"]
  )
  assert manifest["relevant_file_hash_count"] == len(scoped_identity_gate.DOC_REFS)
  assert manifest["temporary_anchor_scan"]["scoped_surface_anchor_count"] == 0
  assert manifest["artifacts"][0]["sha256"] == scoped_identity_gate._sha256_file(artifact_path)
  assert not any(manifest["authority_guards"].values())


def test_scoped_release_identity_gate_cli_default_writes_manifest(
  tmp_path: Path,
) -> None:
  result = subprocess.run(
    [
      sys.executable,
   str(REPO_ROOT / "tools/maintenance/damage_model.py"),
      "release-governance",
      "scoped-release-identity",
      "--retained-output-dir",
      str(tmp_path),
    ],
    cwd=REPO_ROOT,
    check=True,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
  )

  payload = json.loads(result.stdout)
  assert payload["schema_version"] == "a2.res002_scoped_release_identity_manifest.v1"
  assert payload["scoped_gate_status"] == (
    "scoped_res002_identity_pass_non_authoritative"
  )
  assert (tmp_path / scoped_identity_gate.GATE_FILENAME).exists()
  assert (tmp_path / scoped_identity_gate.MANIFEST_FILENAME).exists()
