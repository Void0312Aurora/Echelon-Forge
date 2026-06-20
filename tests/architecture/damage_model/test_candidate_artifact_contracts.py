from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.architecture.damage_model.helpers import (
  assert_authority_guards_false,
  run_maintenance_cli,
)
from tests.architecture.helpers import read_json


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import ( # noqa: E402
  effect_scale_result_pack as result_pack,
  effect_scale_retained_pack as retained_pack,
  effect_scale_snapshot as snapshot,
  package_bundle as bundle,
  runtime_authority_exercise as authority_pack,
  scope_boundary_probe as boundary_probe,
  validation_scaffold as scaffold,
)

CandidateBundle = dict[str, Any]


@pytest.fixture(scope="module")
def candidate_bundle_artifact() -> CandidateBundle:
  return bundle.generate_candidate_bundle(repo_root=REPO_ROOT)


def test_validation_scaffold_current_repo_is_non_authoritative() -> None:
  artifact = scaffold.generate_validation_scaffold(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.vulnerability_surrogate_validation.v1"
  assert artifact["validation_status"] == "not_run"
  assert artifact["scope"]["target_type"] == "F-16C_Block50"
  assert artifact["scope"]["weapon_class"] == "AIM-120C-class"
  assert artifact["scope"]["weapon_family"] == "blast_fragmentation"
  assert artifact["scope"]["candidate_scope_label"] == "near_miss_0_35m"
  assert artifact["scope"]["runtime_miss_distance_bucket"] == "near_miss"

  boundary = artifact["current_authority_boundary"]
  assert boundary["calibration_status"] == "unvalidated"
  assert not boundary["effect_scale_authority"]
  assert not boundary["component_failure_probability_authority"]
  assert not boundary["pk_authority"]
  assert not boundary["deterministic_fuze_authority"]
  assert boundary["runtime_descriptor_status"] == "not_created"

  bm002 = artifact["benchmarks"]["BFM-BM-002"]
  assert bm002["metrics"]["fixed_seed_replay_pass"]
  assert bm002["metrics"]["positive_mass_velocity_pass"]
  assert bm002["metrics"]["energy_unit_sanity_pass"]
  assert bm002["metrics"]["no_truth_labels_pass"]
  assert bm002["current_point"]["mean_fragment_mass_kg"] > 0.0
  assert bm002["current_point"]["mean_fragment_velocity_mps"] > 0.0
  assert bm002["current_point"]["mean_fragment_energy_j"] > 0.0

  bm004 = artifact["benchmarks"]["BFM-BM-004"]
  assert bm004["metrics"]["unit_roundtrip_pass"]
  assert bm004["metrics"]["domain_rejection_pass"]
  assert bm004["metrics"]["monotonic_penetration_margin_pass"]
  assert bm004["metrics"]["incidence_domain_rejection_pass"]
  assert bm004["current_point"]["penetration_margin_proxy"] < (
    bm004["samples"][0]["penetration_margin_proxy"]
  )

  bm006 = artifact["benchmarks"]["BFM-BM-006"]
  assert bm006["metrics"]["source_trace_error_count"] == 0
  assert bm006["metrics"]["source_trace_warning_count"] == 0

  bm003 = artifact["benchmarks"]["BFM-BM-003"]
  assert bm003["metrics"]["sampling_convergence_pass"]
  assert bm003["sampling_convergence_summary"]["reference_sample_count"] == 4096
  assert bm003["sampling_convergence_summary"]["comparison_sample_count"] == 8192
  assert bm003["sampling_convergence_summary"]["relative_delta"] <= 0.05

  mechanism = artifact["mechanism_load_vector"]
  assert set(mechanism.keys()) == {
    "blast_scaled_distance_m_kg13",
    "fragment_areal_density_per_m2",
    "surface_incidence_cos",
  }
  assert mechanism["blast_scaled_distance_m_kg13"] > 0.0
  assert mechanism["fragment_areal_density_per_m2"] > 0.0
  assert 0.0 <= mechanism["surface_incidence_cos"] <= 1.0

  guards = artifact["non_authoritative_guards"]
  assert guards["forbidden_outputs_omitted"] == [
    "effect_scale",
    "component_failure_probability",
    "pk",
    "deterministic_fuze",
  ]
  assert not guards["descriptor_row_created"]
  assert not guards["runtime_authority_granted"]

  draft = artifact["vulnerability_evidence_draft"]
  assert draft["status"] == "schema_aligned_non_authoritative_draft"
  descriptor = draft["descriptor"]
  assert descriptor["schema_version"] == "a2.vulnerability_evidence.v1"
  assert descriptor["source_kind"] == "engineering_surrogate"
  assert descriptor["calibration_status"] == "unvalidated"
  assert descriptor["miss_distance_bucket"] == "near_miss"
  assert not descriptor["effect_scale_authority"]
  assert not descriptor["component_failure_probability_authority"]
  assert not descriptor["pk_authority"]
  assert not descriptor["deterministic_fuze_authority"]

  rows = descriptor["rows"]
  assert len(rows) == 1
  row = rows[0]
  assert row["weapon_family"] == "blast_fragmentation"
  assert row["aspect_bucket"] == "beam"
  assert row["closure_bucket"] == "high"
  assert row["miss_distance_bucket"] == "near_miss"
  assert "effect_scale" not in row
  assert "component_failure_probability" not in row
  assert row["min_fragment_energy_j"] <= artifact["diagnostic_only_fields"]["fragment_energy_j_proxy"]
  assert row["max_fragment_energy_j"] >= artifact["diagnostic_only_fields"]["fragment_energy_j_proxy"]
  assert row["min_blast_scaled_distance_m_kg13"] <= mechanism["blast_scaled_distance_m_kg13"]
  assert row["max_blast_scaled_distance_m_kg13"] >= mechanism["blast_scaled_distance_m_kg13"]
  assert row["min_fragment_areal_density_per_m2"] <= mechanism["fragment_areal_density_per_m2"]
  assert row["max_fragment_areal_density_per_m2"] >= mechanism["fragment_areal_density_per_m2"]
  assert row["min_penetration_margin"] <= artifact["diagnostic_only_fields"]["penetration_margin_proxy"]
  assert row["max_penetration_margin"] >= artifact["diagnostic_only_fields"]["penetration_margin_proxy"]
  assert row["min_surface_incidence_cos"] <= mechanism["surface_incidence_cos"]
  assert row["max_surface_incidence_cos"] >= mechanism["surface_incidence_cos"]

  bm005 = artifact["benchmarks"]["BFM-BM-005"]
  assert bm005["metrics"]["uncertainty_summary_present"]
  assert bm005["metrics"]["seed_window_cv_pass"]
  uncertainty = bm005["uncertainty_summary"]
  assert uncertainty["evaluated_seeds"] == [20260529, 20260630, 20260731, 20260832]
  assert uncertainty["fragment_areal_density_per_m2"]["cv"] <= 0.05
  assert uncertainty["fragment_energy_j_proxy"]["cv"] <= 0.05
  assert uncertainty["penetration_margin_proxy"]["cv"] <= 0.05


def test_validation_scaffold_is_fixed_seed_reproducible() -> None:
  lhs = scaffold.generate_validation_scaffold(repo_root=REPO_ROOT, seed=12345)
  rhs = scaffold.generate_validation_scaffold(repo_root=REPO_ROOT, seed=12345)

  assert (
    lhs["benchmarks"]["BFM-BM-002"]["current_point"]["mean_fragment_energy_j"]
    == rhs["benchmarks"]["BFM-BM-002"]["current_point"]["mean_fragment_energy_j"]
  )
  assert (
    lhs["benchmarks"]["BFM-BM-003"]["current_point"]["beam_witness_areal_density_per_m2"]
    == rhs["benchmarks"]["BFM-BM-003"]["current_point"]["beam_witness_areal_density_per_m2"]
  )
  assert (
    lhs["benchmarks"]["BFM-BM-003"]["current_point"]["hit_count"]
    == rhs["benchmarks"]["BFM-BM-003"]["current_point"]["hit_count"]
  )
  assert (
    lhs["benchmarks"]["BFM-BM-004"]["current_point"]["penetration_margin_proxy"]
    == rhs["benchmarks"]["BFM-BM-004"]["current_point"]["penetration_margin_proxy"]
  )
  assert lhs["mechanism_load_vector"] == rhs["mechanism_load_vector"]
  assert lhs["diagnostic_only_fields"] == rhs["diagnostic_only_fields"]
  assert lhs["vulnerability_evidence_draft"] == rhs["vulnerability_evidence_draft"]


def test_validation_scaffold_tracks_candidate_closure_sensitive_mechanism_fields() -> None:
  low = scaffold.generate_validation_scaffold(repo_root=REPO_ROOT, closure_mps=700.0)
  anchor = scaffold.generate_validation_scaffold(repo_root=REPO_ROOT, closure_mps=900.0)
  high = scaffold.generate_validation_scaffold(repo_root=REPO_ROOT, closure_mps=1100.0)

  assert (
    low["mechanism_load_vector"]["blast_scaled_distance_m_kg13"] ==
    anchor["mechanism_load_vector"]["blast_scaled_distance_m_kg13"] ==
    high["mechanism_load_vector"]["blast_scaled_distance_m_kg13"]
  )
  assert (
    low["mechanism_load_vector"]["fragment_areal_density_per_m2"] <
    anchor["mechanism_load_vector"]["fragment_areal_density_per_m2"] <
    high["mechanism_load_vector"]["fragment_areal_density_per_m2"]
  )
  assert (
    low["diagnostic_only_fields"]["blast_impulse_kpa_ms_proxy"] <
    anchor["diagnostic_only_fields"]["blast_impulse_kpa_ms_proxy"] <
    high["diagnostic_only_fields"]["blast_impulse_kpa_ms_proxy"]
  )
  assert (
    low["diagnostic_only_fields"]["fragment_energy_j_proxy"] <
    anchor["diagnostic_only_fields"]["fragment_energy_j_proxy"] <
    high["diagnostic_only_fields"]["fragment_energy_j_proxy"]
  )


def test_validation_scaffold_cli_writes_json(tmp_path: Path) -> None:
  output_path = tmp_path / "blastfrag_scaffold.json"
  subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "candidate-artifacts",
      "validation-scaffold",
      "--output",
      str(output_path),
      "--seed",
      "24680",
      "--sample-count",
      "1024",
    ],
    cwd=REPO_ROOT,
    check=True,
  )

  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["artifact_provenance"]["seed"] == 24680
  assert artifact["artifact_provenance"]["sample_count"] == 1024
  assert artifact["validation_status"] == "not_run"
  assert artifact["current_authority_boundary"]["runtime_descriptor_status"] == "not_created"
  assert artifact["vulnerability_evidence_draft"]["descriptor"]["source_kind"] == "engineering_surrogate"


def test_scope_boundary_probe_current_repo_is_non_authoritative() -> None:
  artifact = boundary_probe.generate_scope_boundary_probe(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.scope_boundary_probe.v1"
  assert artifact["status"] == "candidate_non_authoritative_scope_probe_results"

  scope = artifact["scope"]
  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["aspect_bucket"] == "beam"
  assert scope["closure_bucket"] == "high"
  assert scope["candidate_scope_label"] == "near_miss_0_35m"
  assert scope["runtime_miss_distance_bucket"] == "near_miss"

  miss_distance_probe = artifact["miss_distance_probe"]
  assert miss_distance_probe["probe_id"] == "SCP-PROBE-001"
  assert miss_distance_probe["metrics"]["blast_scaled_distance_monotonic_increasing_pass"]
  assert miss_distance_probe["metrics"]["fragment_areal_density_monotonic_decreasing_pass"]
  assert miss_distance_probe["metrics"]["runtime_bucket_consistent_pass"]
  assert miss_distance_probe["metrics"]["anchor_present"]
  assert [row["standoff_m"] for row in miss_distance_probe["rows"]] == [
    0.25,
    0.35,
    0.45,
  ]
  assert all(
    row["runtime_miss_distance_bucket"] == "near_miss"
    for row in miss_distance_probe["rows"]
  )

  closure_probe = artifact["closure_probe"]
  assert closure_probe["probe_id"] == "SCP-PROBE-002"
  assert closure_probe["metrics"]["closure_label_probe_executed"]
  assert closure_probe["metrics"]["mechanism_response_active"]
  assert not closure_probe["metrics"]["mechanism_response_constant_across_closure"]
  assert closure_probe["metrics"]["candidate_closure_sensitive_response_observed"]
  assert not closure_probe["metrics"]["res008_closed_by_probe"]
  assert not closure_probe["metrics"]["independent_review_complete"]
  assert closure_probe["metrics"]["runtime_bucket_consistent_pass"]
  assert closure_probe["metrics"]["anchor_present"]
  assert [row["closure_mps"] for row in closure_probe["rows"]] == [
    700.0,
    900.0,
    1100.0,
  ]
  assert (
    closure_probe["rows"][0]["fragment_areal_density_per_m2"]
    < closure_probe["rows"][1]["fragment_areal_density_per_m2"]
    < closure_probe["rows"][2]["fragment_areal_density_per_m2"]
  )
  assert (
    closure_probe["rows"][0]["blast_impulse_kpa_ms_proxy"]
    < closure_probe["rows"][1]["blast_impulse_kpa_ms_proxy"]
    < closure_probe["rows"][2]["blast_impulse_kpa_ms_proxy"]
  )
  assert (
    closure_probe["rows"][0]["fragment_energy_j_proxy"]
    < closure_probe["rows"][1]["fragment_energy_j_proxy"]
    < closure_probe["rows"][2]["fragment_energy_j_proxy"]
  )
  assert "candidate closure-sensitive response is present" in closure_probe[
    "limitation_note"
  ]
  assert "RES-008 remains non-authoritative" in closure_probe["limitation_note"]

  aspect_probe = artifact["aspect_guard_probe"]
  assert aspect_probe["probe_id"] == "SCP-PROBE-003"
  assert aspect_probe["metrics"]["beam_only_guard_documented"]
  assert aspect_probe["metrics"]["rejected_label_count"] == 6
  assert aspect_probe["accepted_scope_labels"] == ["beam"]
  assert aspect_probe["rejected_scope_labels"] == [
    "head_on",
    "tail_chase",
    "high_off_boresight",
    "direct_hit",
    "closure_bucket != high",
    "weapon_family != blast_fragmentation",
  ]

  guards = artifact["non_authoritative_guards"]
  assert not guards["stock_runtime_authority_granted"]
  assert not guards["effect_scale_authority_granted"]
  assert not guards["component_failure_probability_authority_granted"]
  assert not guards["pk_authority_granted"]
  assert not guards["deterministic_fuze_authority_granted"]


def test_scope_boundary_probe_cli_writes_json(tmp_path: Path) -> None:
  output_path = tmp_path / "a2_scope_boundary_probe.json"
  subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "candidate-artifacts",
      "scope-boundary-probe",
      "--output",
      str(output_path),
    ],
    cwd=REPO_ROOT,
    check=True,
  )

  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["status"] == "candidate_non_authoritative_scope_probe_results"
  assert artifact["scope"]["candidate_scope_label"] == "near_miss_0_35m"
  assert artifact["miss_distance_probe"]["metrics"]["anchor_present"] is True


def test_stage_b_effect_scale_snapshot_current_repo_is_non_authoritative() -> None:
  artifact = snapshot.generate_stage_b_effect_scale_snapshot(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.stage_b_effect_scale_snapshot.v1"
  assert artifact["status"] == "candidate_non_authoritative_stage_b_snapshot"

  scope = artifact["scope"]
  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["aspect_bucket"] == "beam"
  assert scope["closure_bucket"] == "high"
  assert scope["candidate_scope_label"] == "near_miss_0_35m"
  assert scope["runtime_miss_distance_bucket"] == "near_miss"

  summary = artifact["summary"]
  assert summary["all_hard_gates_pass_in_current_snapshot"]
  assert summary["failed_criteria_ids"] == []
  assert summary["reviewed_benchmarks"] == [
    "BFM-BM-001",
    "BFM-BM-003",
    "BFM-BM-005",
    "BFM-BM-006",
  ]
  assert summary["primary_release_scope"] == "effect_scale_authority_only"
  assert summary["review_status"] == "author_snapshot_only_pending_independent_review"

  criteria_rows = artifact["criteria_evaluation"]
  assert len(criteria_rows) == 18
  assert all(row["pass"] for row in criteria_rows)
  assert criteria_rows[0]["criteria_id"] == "BFM-CRIT-ES-001"
  assert criteria_rows[-1]["criteria_id"] == "BFM-CRIT-ES-018"

  bm005 = artifact["benchmark_snapshot"]["BFM-BM-005"]
  assert bm005["metrics"]["source_trace_completeness_pass"]
  assert bm005["metrics"]["unit_consistency_pass"]
  assert bm005["metrics"]["forbidden_authority_fields_absent"]
  assert bm005["metrics"]["uncertainty_summary_present"]
  assert bm005["metrics"]["seed_window_cv_pass"]
  assert bm005["uncertainty_summary"]["fragment_areal_density_per_m2"]["cv"] <= 0.05
  assert bm005["uncertainty_summary"]["blast_impulse_kpa_ms_proxy"]["cv"] <= 0.05
  assert bm005["uncertainty_summary"]["fragment_energy_j_proxy"]["cv"] <= 0.05
  assert bm005["uncertainty_summary"]["penetration_margin_proxy"]["cv"] <= 0.05

  findings = artifact["current_findings"]
  assert "every frozen Stage B hard gate" in findings[0]
  assert "not an independent validation result" in findings[1]
  assert "candidate closure-sensitive response is tracked" in findings[2]
  assert "does not close RES-008" in findings[2]

  assert_authority_guards_false(artifact, guards_key="non_authoritative_guards")


def test_stage_b_effect_scale_snapshot_cli_writes_json(tmp_path: Path) -> None:
  output_path = tmp_path / "a2_stage_b_effect_scale_snapshot.json"
  run_maintenance_cli(
    "damage_model.py candidate-artifacts",
    "effect-scale-snapshot",
    "--output",
    output_path,
  )

  artifact = read_json(output_path)
  assert artifact["status"] == "candidate_non_authoritative_stage_b_snapshot"
  assert artifact["summary"]["all_hard_gates_pass_in_current_snapshot"] is True
  assert_authority_guards_false(artifact, guards_key="non_authoritative_guards")


def test_stage_b_validation_result_pack_current_repo_is_non_authoritative() -> None:
  artifact = result_pack.generate_stage_b_validation_result_pack(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.stage_b_validation_result_pack.v1"
  assert artifact["status"] == "candidate_non_authoritative_stage_b_result_pack"

  scope = artifact["scope"]
  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["aspect_bucket"] == "beam"
  assert scope["closure_bucket"] == "high"
  assert scope["candidate_scope_label"] == "near_miss_0_35m"
  assert scope["runtime_miss_distance_bucket"] == "near_miss"

  artifact_hashes = artifact["artifact_hashes"]
  assert len(artifact_hashes) == 3
  assert [row["artifact_id"] for row in artifact_hashes] == [
    "ART-SCAFFOLD-001",
    "ART-SCOPE-PROBE-001",
    "ART-STAGE-B-SNAPSHOT-001",
  ]
  assert all(len(row["sha256"]) == 64 for row in artifact_hashes)

  result_summary = artifact["result_table_summary"]
  assert result_summary["all_hard_gates_pass_in_current_snapshot"] is True
  assert result_summary["hard_gate_pass_is_release"] is False
  assert result_summary["failed_criteria_ids"] == []
  assert result_summary["reviewed_benchmarks"] == [
    "BFM-BM-001",
    "BFM-BM-003",
    "BFM-BM-005",
    "BFM-BM-006",
  ]
  assert result_summary["primary_release_scope"] == "effect_scale_authority_only"
  assert (
    result_summary["review_status"]
    == "author_result_pack_only_pending_independent_review"
  )
  assert len(result_summary["evidence_artifact_hashes"]["validation_scaffold"]) == 64
  assert len(result_summary["evidence_artifact_hashes"]["scope_boundary_probe"]) == 64
  assert len(result_summary["evidence_artifact_hashes"]["stage_b_snapshot"]) == 64

  release = artifact["release_readiness_interpretation"]
  assert release["current_hard_gate_snapshot_pass"] is True
  assert release["hard_gate_pass_is_release"] is False
  assert release["release_ready"] is False
  assert release["release_target"] == "effect_scale_authority_only"
  assert release["stage_c_component_probability_release_included"] is False
  assert release["stock_runtime_authority_granted"] is False

  uncertainty = artifact["uncertainty_result_summary"]
  assert uncertainty["fragment_areal_density_cv"] <= 0.05
  assert uncertainty["blast_impulse_cv"] <= 0.05
  assert uncertainty["fragment_energy_cv"] <= 0.05
  assert uncertainty["penetration_margin_cv"] <= 0.05
  assert uncertainty["seed_window_cv_pass"] is True
  assert "candidate uncertainty snapshot only" in uncertainty["result_interpretation"]

  scope_audit = artifact["scope_audit_summary"]
  assert scope_audit["miss_distance_row_count"] == 3
  assert scope_audit["miss_distance_monotonic_pass"] is True
  assert scope_audit["closure_mechanism_response_active"] is True
  assert "candidate closure-sensitive response is present" in scope_audit[
    "closure_limitation_note"
  ]
  assert "RES-008 remains non-authoritative" in scope_audit[
    "scope_guard_interpretation"
  ]

  independence = artifact["independence_audit"]
  assert [row["benchmark_id"] for row in independence] == [
    "BFM-BM-001",
    "BFM-BM-002",
    "BFM-BM-003",
    "BFM-BM-004",
    "BFM-BM-005",
    "BFM-BM-006",
  ]
  bm005 = next(row for row in independence if row["benchmark_id"] == "BFM-BM-005")
  assert bm005["independence_class"] == "not_independent_real_validation"
  assert bm005["current_release_role"] == "integrated_mechanism_load_hygiene_only"
  assert bm005["audit_outcome"] == "candidate_hygiene_only_not_independent_validation"
  bm006 = next(row for row in independence if row["benchmark_id"] == "BFM-BM-006")
  assert bm006["audit_outcome"] == "administrative_gate_only"

  findings = artifact["current_findings"]
  assert "stable content hashes" in findings[0]
  assert "all current Stage B hard gates pass" in findings[1]
  assert "must not be narrated as independent surrogate validation" in findings[2]

  guards = artifact["non_authoritative_guards"]
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False


def test_stage_b_validation_result_pack_cli_writes_json(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "a2_stage_b_validation_result_pack.json"
  subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "candidate-artifacts",
      "effect-scale-result-pack",
      "--output",
      str(output_path),
    ],
    cwd=REPO_ROOT,
    check=True,
  )

  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["status"] == "candidate_non_authoritative_stage_b_result_pack"
  assert (
    artifact["result_table_summary"]["all_hard_gates_pass_in_current_snapshot"]
    is True
  )
  assert artifact["scope_audit_summary"]["closure_mechanism_response_active"] is True



# Retained candidate artifacts are package evidence, not release authority.
def test_candidate_retained_artifact_pack_writes_retained_files(tmp_path: Path) -> None:
  artifact = retained_pack.generate_retained_artifact_pack(
    repo_root=REPO_ROOT,
    output_dir=tmp_path / "retained_pack",
  )

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.stage_b_retained_artifact_pack.v1"
  assert artifact["status"] == "author_retained_candidate_artifacts_only"
  assert artifact["retention_scope"] == "stage_b_effect_scale_author_side_candidate_only"
  assert artifact["retained_artifact_count"] == 4
  assert len(artifact["manifest_sha256"]) == 64

  origin = artifact["retained_origin_summary"]
  assert origin["runtime_origin"] == "no_stock_runtime_descriptor_author_side_artifacts_only"
  assert origin["review_surface"] == "author_side_stage_b_effect_scale_candidate_only"
  assert origin["independent_release_artifact_present"] is False
  assert origin["stock_runtime_authority_present"] is False
  assert origin["stage_c_component_probability_artifacts_present"] is False

  rows = artifact["artifacts"]
  assert [row["artifact_key"] for row in rows] == [
    "validation_scaffold_snapshot",
    "scope_boundary_probe_snapshot",
    "stage_b_effect_scale_snapshot",
    "stage_b_validation_result_pack",
  ]
  assert [row["origin_class"] for row in rows] == [
    "author_side_validation_scaffold_snapshot_only",
    "author_side_scope_boundary_probe_only",
    "author_side_stage_b_hard_gate_snapshot_only",
    "author_side_stage_b_result_pack_only",
  ]
  for row in rows:
    path = REPO_ROOT / row["relative_path"]
    assert path.exists()
    assert len(row["sha256"]) == 64
    assert len(row["content_sha256"]) == 64
    assert "stock runtime authority" in row["forbidden_claim"]
    assert "component-probability release" in row["forbidden_claim"]
    assert "Pk authority" in row["forbidden_claim"]
    assert "deterministic-fuze authority" in row["forbidden_claim"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("status", payload.get("validation_status")) == row["status"]
    assert payload["schema_version"] == row["schema_version"]

  guards = artifact["non_authoritative_guards"]
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False

  loaded = retained_pack.load_retained_artifact_pack_manifest(
    repo_root=REPO_ROOT,
    output_dir=tmp_path / "retained_pack",
  )
  assert loaded["manifest_exists"] is True
  assert loaded["retained_artifact_count"] == 4
  assert loaded["all_artifacts_exist"] is True
  assert loaded["manifest_relative_path"].endswith("retained_pack/manifest.json")


def test_candidate_retained_artifact_pack_cli_writes_manifest(
  tmp_path: Path,
) -> None:
  output_dir = tmp_path / "retained_pack_cli"
  completed = subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "candidate-artifacts",
      "effect-scale-retained-pack",
      "--output-dir",
      str(output_dir),
    ],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )
  artifact = json.loads(completed.stdout)
  assert artifact["status"] == "author_retained_candidate_artifacts_only"
  assert artifact["retained_artifact_count"] == 4
  assert artifact["retained_origin_summary"]["stock_runtime_authority_present"] is False
  assert (output_dir / "manifest.json").exists()



# Runtime-aligned authority exercise remains test-local candidate evidence.
def test_runtime_aligned_authority_exercise_is_test_local_only() -> None:
  artifact = authority_pack.generate_runtime_aligned_authority_pack(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_runtime_aligned_authority_exercise_v0"
  )
  assert artifact["schema_version"] == "a2.vulnerability_authority_exercise.v1"
  assert artifact["status"] == "test_local_authority_exercise_only"

  scope = artifact["scope"]
  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["candidate_scope_label"] == "near_miss_0_35m"
  assert scope["runtime_miss_distance_bucket"] == "near_miss"

  boundary = artifact["authority_boundary"]
  assert not boundary["stock_database_authority_granted"]
  assert boundary["effect_scale_authority_candidate"]
  assert boundary["component_failure_probability_authority_candidate"]
  assert not boundary["pk_authority"]
  assert not boundary["deterministic_fuze_authority"]
  assert boundary["runtime_database_integration"] == "forbidden_by_default"

  baseline = artifact["baseline_event_summary"]
  assert not baseline["direct_hitbox_intersection"]
  assert baseline["projected_hitbox_count"] > 0
  assert baseline["component_hit_count"] > 0
  assert baseline["component_primary_name"] == "right_aileron_actuator"
  assert baseline["mechanism_fragment_energy_j"] > 0.0
  assert baseline["mechanism_penetration_margin"] > 0.0
  assert baseline["mechanism_blast_impulse_kpa_ms"] > 0.0
  assert baseline["component_primary_mechanism_fragment_energy_j"] > 0.0
  assert baseline["component_primary_mechanism_penetration_margin"] > 0.0
  assert baseline["component_primary_mechanism_blast_impulse_kpa_ms"] > 0.0

  component_rows = artifact["baseline_component_rows"]
  assert len(component_rows) >= 1
  primary_rows = [
    row for row in component_rows if row["component_name"] == "right_aileron_actuator"
  ]
  assert len(primary_rows) == 1
  primary_row = primary_rows[0]
  assert primary_row["mechanism_fragment_energy_j"] > 0.0
  assert primary_row["mechanism_penetration_margin"] > 0.0
  assert primary_row["mechanism_blast_impulse_kpa_ms"] > 0.0

  effect_descriptor = artifact["effect_scale_descriptor_candidate"]
  assert effect_descriptor["source_kind"] == "validated_physics_surrogate"
  assert effect_descriptor["calibration_status"] == "calibrated"
  assert effect_descriptor["effect_scale_authority"]
  assert not effect_descriptor["component_failure_probability_authority"]
  assert not effect_descriptor["pk_authority"]
  assert not effect_descriptor["deterministic_fuze_authority"]
  effect_row = effect_descriptor["rows"][0]
  assert effect_row["miss_distance_bucket"] == "near_miss"
  assert effect_row["effect_scale"] == 1.11
  assert effect_row["min_fragment_energy_j"] <= baseline["mechanism_fragment_energy_j"]
  assert effect_row["max_fragment_energy_j"] >= baseline["mechanism_fragment_energy_j"]
  assert (
    effect_row["min_penetration_margin"]
    <= baseline["mechanism_penetration_margin"]
    <= effect_row["max_penetration_margin"]
  )
  assert (
    effect_row["min_blast_impulse_kpa_ms"]
    <= baseline["mechanism_blast_impulse_kpa_ms"]
    <= effect_row["max_blast_impulse_kpa_ms"]
  )

  component_descriptor = artifact["component_failure_probability_descriptor_candidate"]
  assert component_descriptor["source_kind"] == "validated_physics_surrogate"
  assert component_descriptor["calibration_status"] == "calibrated"
  assert not component_descriptor["effect_scale_authority"]
  assert component_descriptor["component_failure_probability_authority"]
  assert not component_descriptor["pk_authority"]
  assert not component_descriptor["deterministic_fuze_authority"]
  component_row = component_descriptor["rows"][0]
  assert component_row["component_name"] == "right_aileron_actuator"
  assert component_row["component_system"] == "flight_control"
  assert component_row["component_redundancy_group_id"] == "lateral_flight_control_actuators"
  assert component_row["component_failure_probability"] == 0.67
  assert (
    component_row["min_fragment_energy_j"]
    <= primary_row["mechanism_fragment_energy_j"]
    <= component_row["max_fragment_energy_j"]
  )
  assert (
    component_row["min_penetration_margin"]
    <= primary_row["mechanism_penetration_margin"]
    <= component_row["max_penetration_margin"]
  )
  assert (
    component_row["min_blast_impulse_kpa_ms"]
    <= primary_row["mechanism_blast_impulse_kpa_ms"]
    <= component_row["max_blast_impulse_kpa_ms"]
  )


def test_runtime_aligned_authority_exercise_is_reproducible() -> None:
  lhs = authority_pack.generate_runtime_aligned_authority_pack(repo_root=REPO_ROOT)
  rhs = authority_pack.generate_runtime_aligned_authority_pack(repo_root=REPO_ROOT)

  assert lhs["baseline_event_summary"] == rhs["baseline_event_summary"]
  assert lhs["baseline_component_rows"] == rhs["baseline_component_rows"]
  assert lhs["effect_scale_descriptor_candidate"] == rhs["effect_scale_descriptor_candidate"]
  assert (
    lhs["component_failure_probability_descriptor_candidate"]
    == rhs["component_failure_probability_descriptor_candidate"]
  )


def test_runtime_aligned_authority_exercise_cli_writes_json(tmp_path: Path) -> None:
  output_path = tmp_path / "blastfrag_runtime_aligned_authority_pack.json"
  subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "candidate-artifacts",
      "runtime-authority-exercise",
      "--output",
      str(output_path),
      "--effect-scale",
      "1.07",
      "--component-failure-probability",
      "0.61",
    ],
    cwd=REPO_ROOT,
    check=True,
  )

  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["effect_scale_descriptor_candidate"]["rows"][0]["effect_scale"] == 1.07
  assert (
    artifact["component_failure_probability_descriptor_candidate"]["rows"][0][
      "component_failure_probability"
    ]
    == 0.61
  )



# Candidate bundle aggregates evidence without promoting authority.
def test_candidate_bundle_identity_scope_and_review_inputs(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  assert artifact["bundle_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0_candidate_bundle_v0"
  )
  assert artifact["schema_version"] == "a2.vps_candidate_bundle.v1"
  assert artifact["status"] == "candidate_non_authoritative_bundle"

  scope = artifact["scope"]
  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["aspect_bucket"] == "beam"
  assert scope["closure_bucket"] == "high"
  assert scope["miss_distance_bucket"] == "near_miss_0_35m"

  boundary = artifact["authority_boundary"]
  assert not boundary["stock_descriptor_created"]
  assert not boundary["stock_database_authority_granted"]
  assert not boundary["effect_scale_authority_in_stock"]
  assert not boundary["component_failure_probability_authority_in_stock"]
  assert not boundary["pk_authority"]
  assert not boundary["deterministic_fuze_authority"]

  docs = artifact["documentation_status"]
  assert docs["ready_for_review"]
  assert docs["placeholder_hits"] == []

  doc_refs = artifact["doc_refs"]
  for ref in doc_refs.values():
    assert (REPO_ROOT / ref).exists()

  source_groups = artifact["source_groups"]
  assert len(source_groups) >= 4
  assert {entry["group_id"] for entry in source_groups} == {
    "target_geometry",
    "warhead_and_fuze",
    "mechanism_load_methods",
    "component_fragility_methods",
  }
  for entry in source_groups:
    assert (REPO_ROOT / entry["ledger_ref"]).exists()
    assert len(entry["selected_source_ids"]) >= 4


def test_candidate_bundle_residual_statuses_close_research_not_authority(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  residual_statuses = artifact["residual_statuses"]
  assert residual_statuses["RES-001"] == (
    "closed_narrow_internal_signoff_non_authoritative"
  )
  assert residual_statuses["RES-002"] == (
    "closed_scoped_identity_non_authoritative"
  )
  assert residual_statuses["RES-003"] == (
    "research_closed_stage_b_witness_geometry_bookkeeping_authority_blocked_global_geometry"
  )
  assert residual_statuses["RES-004"] == (
    "research_closed_stage_b_family_scope_authority_blocked_specific_warhead_truth"
  )
  assert residual_statuses["RES-007"] == (
    "closed_stage_b_scope_review_only_release_blocked"
  )
  assert residual_statuses["RES-008"] == (
    "closed_stage_b_scope_review_only_release_blocked"
  )
  assert residual_statuses["RES-005"] == (
    "research_closed_mechanism_load_envelope_authority_fail_closed_tp21_selected_debris_outputs_missing"
  )
  assert residual_statuses["RES-006"] == (
    "research_closed_mechanism_load_envelope_authority_fail_closed_beco_recalculation_not_admitted"
  )
  assert residual_statuses["RES-009"] == (
    "research_closed_stage_c_candidate_surface_authority_blocked_fragility_truth"
  )
  assert residual_statuses["RES-013"] == (
    "research_out_of_scope_authority_boundary_deferred_pk"
  )
  assert residual_statuses["RES-014"] == (
    "research_out_of_scope_authority_boundary_deferred_deterministic_fuze"
  )

  residuals = artifact["open_residual_ids"]
  assert residuals == []

  research_profile = artifact["research_profile_status"]
  assert research_profile["status"] == "research_closed_authority_retained"
  assert research_profile["research_profile_closed"] is True
  assert research_profile["authority_profile_closed"] is False
  assert research_profile["research_blocker_residual_ids"] == []
  assert research_profile["research_closed_residual_ids"] == [
    "RES-001",
    "RES-002",
    "RES-003",
    "RES-004",
    "RES-005",
    "RES-006",
    "RES-007",
    "RES-008",
    "RES-009",
    "RES-010",
    "RES-011",
    "RES-012",
    "RES-013",
    "RES-014",
  ]
  assert artifact["authority_blocker_residual_ids"] == [
    "RES-003",
    "RES-004",
    "RES-005",
    "RES-006",
    "RES-007",
    "RES-008",
    "RES-009",
    "RES-010",
    "RES-011",
    "RES-012",
    "RES-013",
    "RES-014",
  ]


def test_candidate_bundle_acceptance_gates_preserve_release_blocks(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  acceptance_gates = artifact["residual_acceptance_gate_summaries"]
  res003_gate = acceptance_gates["res003_target_geometry_closeout"]
  assert res003_gate["status"] == (
    "res003_stage_b_effect_scale_witness_geometry_closeout_pass_release_blocked"
  )
  assert res003_gate["release_ready"] is False
  assert res003_gate["release_blocked"] is True
  assert res003_gate["closed_residual_ids_by_this_gate"] == []
  assert res003_gate["closed_residual_subscopes_by_this_gate"] == [
    "RES-003:stage_b_effect_scale_witness_geometry_bookkeeping"
  ]
  assert res003_gate["authority_guards_all_false"] is True
  assert res003_gate["residual_decision"][
    "global_target_geometry_authority"
  ] == "not_granted"

  res004_gate = acceptance_gates["res004_warhead_scope_closeout"]
  assert res004_gate["status"] == (
    "res004_stage_b_effect_scale_warhead_family_scope_closeout_pass_release_blocked"
  )
  assert res004_gate["release_ready"] is False
  assert res004_gate["release_blocked"] is True
  assert res004_gate["closed_residual_ids_by_this_gate"] == []
  assert res004_gate["closed_residual_subscopes_by_this_gate"] == [
    "RES-004:stage_b_effect_scale_aim120c_class_blast_fragmentation_family_scope"
  ]
  assert res004_gate["authority_guards_all_false"] is True
  assert res004_gate["residual_decision"][
    "missile_specific_aim120c_warhead_truth"
  ] == "forbidden"

  res005_gate = acceptance_gates["res005_tp21_debris_admission"]
  assert res005_gate["decision"] == "not_admitted_fail_closed"
  assert res005_gate["narrowly_closes_res005"] is False
  assert res005_gate["closed_residual_ids_by_this_gate"] == []
  assert res005_gate["selected_debris_output_hash_count"] == 0
  assert res005_gate["raw_tp21_source_content_retained"] is False
  assert res005_gate["benchmark_consumed_for_release"] is False
  assert res005_gate["authority_guards_all_false"] is True
  assert len(res005_gate["exact_blockers"]) == 4

  res006_gate = acceptance_gates["res006_beco_recalculation_admission"]
  assert res006_gate["decision"] == "res006_remains_blocked_fail_closed"
  assert res006_gate["res006_narrowly_closed"] is False
  assert res006_gate["closed_residual_ids_by_this_gate"] == []
  assert res006_gate["cached_anchor_count"] == 9
  assert res006_gate["recalculated_anchor_count"] == 9
  assert res006_gate["matching_count"] == 0
  assert res006_gate["mismatch_count"] == 9
  assert res006_gate["candidate_replacement_anchor_set_retained"] is True
  assert res006_gate["replacement_anchor_set_admitted"] is False
  assert res006_gate["allowed_output_signoff_present"] is False
  assert res006_gate["tolerance_policy_admitted"] is False
  assert res006_gate["authority_guards_all_false"] is True


def test_candidate_bundle_validation_acceptance_summaries_stay_non_authoritative(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  validation_summary = artifact["validation_scaffold_summary"]
  assert validation_summary["validation_status"] == "not_run"
  assert (
    validation_summary["current_authority_boundary"]["runtime_descriptor_status"]
    == "not_created"
  )
  assert validation_summary["implemented_benchmarks"] == [
    "BFM-BM-001",
    "BFM-BM-002",
    "BFM-BM-003",
    "BFM-BM-004",
    "BFM-BM-005",
    "BFM-BM-006",
  ]
  assert validation_summary["draft_descriptor_status"] == "schema_aligned_non_authoritative_draft"

  acceptance_summary = artifact["validation_acceptance_criteria_summary"]
  assert acceptance_summary["criteria_status"] == "frozen_pre_run_stage_b_effect_scale_only"
  assert acceptance_summary["primary_release_scope"] == "effect_scale_authority_only"
  assert acceptance_summary["component_probability_release_status"] == "deferred_to_stage_c"
  assert acceptance_summary["review_status"] == "author_frozen_pending_independent_review"
  assert acceptance_summary["runtime_descriptor_action"] == (
    "forbidden_until_review_record_and_benchmark_results_exist"
  )
  assert acceptance_summary["hard_gate_benchmarks"] == [
    "BFM-BM-001",
    "BFM-BM-003",
    "BFM-BM-005",
    "BFM-BM-006",
  ]
  assert acceptance_summary["deferred_items"] == [
    "BFM-DEF-001",
    "BFM-DEF-002",
    "BFM-DEF-003",
    "BFM-DEF-004",
  ]

  stage_c_acceptance_summary = artifact["validation_stage_c_acceptance_criteria_summary"]
  assert (
    stage_c_acceptance_summary["criteria_status"]
    == "frozen_pre_run_stage_c_component_probability_candidate_only"
  )
  assert (
    stage_c_acceptance_summary["primary_release_scope"]
    == "component_failure_probability_authority_only"
  )
  assert (
    stage_c_acceptance_summary["effect_scale_dependency_status"]
    == "stage_b_review_track_retained_separately"
  )
  assert (
    stage_c_acceptance_summary["review_status"]
    == "author_frozen_pending_independent_review"
  )
  assert (
    stage_c_acceptance_summary["runtime_descriptor_action"]
    == "forbidden_until_fragility_review_record_and_result_closeout_exist"
  )
  assert stage_c_acceptance_summary["hard_gate_count"] == 23
  assert stage_c_acceptance_summary["deferred_items"] == [
    "BFM-DEF-CP-001",
    "BFM-DEF-CP-002",
    "BFM-DEF-CP-003",
    "BFM-DEF-CP-004",
  ]


def test_candidate_bundle_scope_probe_and_stage_b_snapshot_summaries(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  scope_summary = artifact["validation_scope_and_independence_summary"]
  assert scope_summary["scope_manifest_status"] == "frozen_pre_run_stage_b_effect_scale_only"
  assert scope_summary["primary_release_scope"] == "effect_scale_authority_only"
  assert scope_summary["independence_status"] == "documented_pre_run_pending_result_audit"
  assert scope_summary["review_status"] == "author_frozen_pending_independent_review"
  assert "runtime coarse bucket near_miss" in scope_summary["runtime_bucket_note"]
  assert scope_summary["boundary_probes"] == [
    "SCP-PROBE-001",
    "SCP-PROBE-002",
    "SCP-PROBE-003",
  ]
  assert scope_summary["out_of_scope_labels"] == [
    "closure_bucket != high",
    "direct_hit",
    "head_on",
    "high_off_boresight",
    "tail_chase",
    "weapon_family != blast_fragmentation",
  ]
  assert scope_summary["documented_benchmarks"] == [
    "BFM-BM-001",
    "BFM-BM-002",
    "BFM-BM-003",
    "BFM-BM-004",
    "BFM-BM-005",
    "BFM-BM-006",
  ]

  probe_summary = artifact["validation_scope_probe_summary"]
  assert probe_summary["status"] == "candidate_non_authoritative_scope_probe_results"
  assert probe_summary["scope"]["candidate_scope_label"] == "near_miss_0_35m"
  assert probe_summary["miss_distance_probe"]["probe_id"] == "SCP-PROBE-001"
  assert probe_summary["miss_distance_probe"]["row_count"] == 3
  assert probe_summary["miss_distance_probe"]["metrics"][
    "blast_scaled_distance_monotonic_increasing_pass"
  ]
  assert probe_summary["miss_distance_probe"]["metrics"][
    "fragment_areal_density_monotonic_decreasing_pass"
  ]
  assert probe_summary["miss_distance_probe"]["standoff_values_m"] == [0.25, 0.35, 0.45]
  assert probe_summary["closure_probe"]["probe_id"] == "SCP-PROBE-002"
  assert probe_summary["closure_probe"]["row_count"] == 3
  assert probe_summary["closure_probe"]["metrics"]["mechanism_response_active"]
  assert not probe_summary["closure_probe"]["metrics"][
    "mechanism_response_constant_across_closure"
  ]
  assert probe_summary["closure_probe"]["metrics"][
    "candidate_closure_sensitive_response_observed"
  ]
  assert not probe_summary["closure_probe"]["metrics"]["res008_closed_by_probe"]
  assert probe_summary["closure_probe"]["closure_values_mps"] == [700.0, 900.0, 1100.0]
  assert "candidate closure-sensitive response is present" in probe_summary["closure_probe"]["limitation_note"]
  assert "RES-008 remains non-authoritative" in probe_summary["closure_probe"]["limitation_note"]
  assert probe_summary["aspect_guard_probe"]["probe_id"] == "SCP-PROBE-003"
  assert probe_summary["aspect_guard_probe"]["accepted_scope_labels"] == ["beam"]
  assert probe_summary["aspect_guard_probe"]["rejected_scope_labels"] == [
    "head_on",
    "tail_chase",
    "high_off_boresight",
    "direct_hit",
    "closure_bucket != high",
    "weapon_family != blast_fragmentation",
  ]

  stage_b_snapshot_summary = artifact["validation_benchmark_snapshot_summary"]
  assert stage_b_snapshot_summary["status"] == "candidate_non_authoritative_stage_b_snapshot"
  assert stage_b_snapshot_summary["all_hard_gates_pass_in_current_snapshot"]
  assert stage_b_snapshot_summary["failed_criteria_ids"] == []
  assert stage_b_snapshot_summary["reviewed_benchmarks"] == [
    "BFM-BM-001",
    "BFM-BM-003",
    "BFM-BM-005",
    "BFM-BM-006",
  ]
  assert (
    stage_b_snapshot_summary["review_status"]
    == "author_snapshot_only_pending_independent_review"
  )
  assert stage_b_snapshot_summary["fragment_areal_density_cv"] <= 0.05
  assert stage_b_snapshot_summary["blast_impulse_cv"] <= 0.05
  assert stage_b_snapshot_summary["fragment_energy_cv"] <= 0.05
  assert stage_b_snapshot_summary["penetration_margin_cv"] <= 0.05


def test_candidate_bundle_stage_c_probability_artifact_summaries_stay_review_only(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  stage_c_snapshot_summary = artifact[
    "validation_stage_c_component_probability_snapshot_summary"
  ]
  assert (
    stage_c_snapshot_summary["status"]
    == "candidate_non_authoritative_stage_c_component_probability_snapshot"
  )
  assert stage_c_snapshot_summary["all_hard_gates_pass_in_current_snapshot"] is True
  assert (
    stage_c_snapshot_summary["review_status"]
    == "author_snapshot_only_pending_independent_review"
  )
  assert (
    stage_c_snapshot_summary["primary_release_scope"]
    == "component_failure_probability_authority_only"
  )
  assert stage_c_snapshot_summary["baseline_component_probability_source"] == (
    "synthetic_sigmoid"
  )
  assert stage_c_snapshot_summary["component_name"] == "right_aileron_actuator"
  assert stage_c_snapshot_summary["component_system"] == "flight_control"
  assert (
    stage_c_snapshot_summary["component_redundancy_group_id"]
    == "lateral_flight_control_actuators"
  )
  assert stage_c_snapshot_summary["component_failure_probability"] == 0.67
  assert stage_c_snapshot_summary["surface_probability_monotonic_pass"] is True
  assert stage_c_snapshot_summary["surface_anchor_probability_cv"] <= 0.05

  stage_c_result_pack_summary = artifact[
    "validation_stage_c_component_probability_result_pack_summary"
  ]
  assert (
    stage_c_result_pack_summary["status"]
    == "candidate_non_authoritative_stage_c_component_probability_result_pack"
  )
  assert stage_c_result_pack_summary["artifact_hash_count"] == 3
  assert stage_c_result_pack_summary["all_hard_gates_pass_in_current_snapshot"] is True
  assert (
    stage_c_result_pack_summary["review_status"]
    == "author_result_pack_only_pending_independent_review"
  )
  assert (
    stage_c_result_pack_summary["primary_release_scope"]
    == "component_failure_probability_authority_only"
  )
  assert stage_c_result_pack_summary["gate_band_contains_primary_fragment_energy"] is True
  assert (
    stage_c_result_pack_summary["gate_band_contains_primary_penetration_margin"] is True
  )
  assert stage_c_result_pack_summary["gate_band_contains_primary_blast_impulse"] is True
  assert (
    stage_c_result_pack_summary["baseline_component_probability_source"]
    == "synthetic_sigmoid"
  )
  assert (
    stage_c_result_pack_summary["candidate_component_name"]
    == "right_aileron_actuator"
  )
  assert stage_c_result_pack_summary["candidate_component_failure_probability"] == 0.67
  assert stage_c_result_pack_summary["gate_band_contains_primary_surface_incidence"] is True
  assert stage_c_result_pack_summary["surface_probability_monotonic_pass"] is True
  assert stage_c_result_pack_summary["surface_anchor_probability_cv"] <= 0.05


def test_candidate_bundle_stage_c_review_and_provenance_gates_stay_blocked(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  stage_c_review_gate_summary = artifact[
    "validation_stage_c_component_probability_review_gate_summary"
  ]
  assert (
    stage_c_review_gate_summary["status"]
    == "blocked_non_authoritative_stage_c_review_candidate"
  )
  assert (
    stage_c_review_gate_summary["review_target"]
    == "component_failure_probability_authority_only"
  )
  assert (
    stage_c_review_gate_summary["readiness_level"]
    == "author_side_component_candidate_ready_but_not_fragility_review_closed"
  )
  assert stage_c_review_gate_summary["satisfied_condition_count"] == 7
  assert stage_c_review_gate_summary["blocking_condition_count"] == 8
  assert stage_c_review_gate_summary["blocking_residual_ids"] == [
    "RES-012",
    "RES-010",
    "RES-009",
    "RES-011",
    "RES-003",
    "RES-005",
    "RES-006",
    "RES-013/014-boundary",
  ]
  assert (
    stage_c_review_gate_summary["upstream_stage_b_status"]
    == "blocked_non_authoritative_stage_b_release_candidate"
  )

  provenance_identity_summary = artifact["validation_provenance_identity_gate_summary"]
  assert (
    provenance_identity_summary["status"]
    == "blocked_non_authoritative_package_provenance_identity_candidate"
  )
  assert (
    provenance_identity_summary["review_target"]
    == "shared_provenance_and_surrogate_identity_surface"
  )
  assert (
    provenance_identity_summary["readiness_level"]
    == "author_side_pin_and_identity_surface_present_but_not_release_grade"
  )
  assert provenance_identity_summary["satisfied_condition_count"] == 5
  assert provenance_identity_summary["blocking_condition_count"] == 4
  assert provenance_identity_summary["blocking_residual_ids"] == [
    "RES-001",
    "RES-002",
    "RES-002",
    "RES-013/014-boundary",
  ]


def test_candidate_bundle_stage_c_retained_and_release_summaries(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  stage_c_retained_pack_summary = artifact[
    "validation_stage_c_component_probability_retained_artifact_pack_summary"
  ]
  assert (
    stage_c_retained_pack_summary["status"]
    == "author_retained_stage_c_component_probability_candidate_artifacts_only"
  )
  assert stage_c_retained_pack_summary["manifest_exists"] is True
  assert stage_c_retained_pack_summary["retained_artifact_count"] == 4
  assert stage_c_retained_pack_summary["all_artifacts_exist"] is True
  assert (
    stage_c_retained_pack_summary["retention_scope"]
    == "stage_c_component_probability_author_side_candidate_only"
  )
  assert stage_c_retained_pack_summary["artifact_keys"] == [
    "runtime_aligned_authority_pack",
    "stage_c_component_probability_snapshot",
    "stage_c_component_probability_surface_probe",
    "stage_c_component_probability_result_pack",
  ]
  assert (
    stage_c_retained_pack_summary["runtime_origin"]
    == "test_local_runtime_authority_exercise_only"
  )

  result_pack_summary = artifact["validation_result_pack_summary"]
  assert result_pack_summary["status"] == "candidate_non_authoritative_stage_b_result_pack"
  assert result_pack_summary["artifact_hash_count"] == 3
  assert result_pack_summary["all_hard_gates_pass_in_current_snapshot"] is True
  assert (
    result_pack_summary["review_status"]
    == "author_result_pack_only_pending_independent_review"
  )
  assert result_pack_summary["closure_mechanism_response_active"] is True
  assert (
    result_pack_summary["bm005_audit_outcome"]
    == "candidate_hygiene_only_not_independent_validation"
  )

  readiness_gate_summary = artifact["validation_release_readiness_gate_summary"]
  assert (
    readiness_gate_summary["status"]
    == "blocked_non_authoritative_stage_b_release_candidate"
  )
  assert readiness_gate_summary["release_target"] == "effect_scale_authority_only"
  assert (
    readiness_gate_summary["readiness_level"]
    == "author_side_candidate_review_ready_but_not_release_ready"
  )
  assert readiness_gate_summary["satisfied_condition_count"] == 6
  assert readiness_gate_summary["blocking_condition_count"] == 8
  assert readiness_gate_summary["blocking_residual_ids"] == [
    "RES-010",
    "RES-002",
    "RES-001",
    "RES-008",
    "RES-010",
    "RES-012",
    "RES-011",
    "RES-013/014-boundary",
  ]


def test_candidate_bundle_stage_b_retained_review_and_identity_summaries(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  retained_pack_summary = artifact["validation_retained_artifact_pack_summary"]
  assert retained_pack_summary["status"] == "author_retained_candidate_artifacts_only"
  assert retained_pack_summary["manifest_exists"] is True
  assert retained_pack_summary["retained_artifact_count"] == 4
  assert retained_pack_summary["all_artifacts_exist"] is True
  assert retained_pack_summary["retention_scope"] == (
    "stage_b_effect_scale_author_side_candidate_only"
  )
  assert retained_pack_summary["artifact_keys"] == [
    "validation_scaffold_snapshot",
    "scope_boundary_probe_snapshot",
    "stage_b_effect_scale_snapshot",
    "stage_b_validation_result_pack",
  ]

  review_readiness = artifact["validation_review_readiness_summary"]
  assert (
    review_readiness["review_readiness_status"]
    == "author_review_ready_pending_independent_review"
  )
  assert review_readiness["primary_release_scope"] == "effect_scale_authority_only"
  assert review_readiness["independent_review_status"] == "not_started"
  assert review_readiness["benchmark_snapshot_status"] == "candidate_snapshot_generated"
  assert (
    review_readiness["stock_runtime_action"]
    == "forbidden_until_independent_review_and_residual_closeout"
  )
  assert review_readiness["review_ids"] == [
    "RR-ES-001",
    "RR-ES-002",
    "RR-ES-003",
    "RR-ES-004",
    "RR-ES-005",
  ]

  artifact_pin_summary = artifact["artifact_pin_manifest_summary"]
  assert artifact_pin_summary["manifest_status"] == "author_frozen_pending_independent_review"
  assert (
    artifact_pin_summary["package_provenance_status"]
    == "official_public_artifacts_partially_verified_release_grade_closeout_pending"
  )
  assert artifact_pin_summary["primary_release_scope"] == "effect_scale_authority_only"
  assert artifact_pin_summary["status_counts"]["acquired_for_candidate"] >= 4
  assert artifact_pin_summary["status_counts"]["verified_candidate_artifact"] == 2
  assert artifact_pin_summary["status_counts"]["sanity_only"] >= 1
  assert artifact_pin_summary["status_counts"]["pending_acquisition"] == 0
  assert artifact_pin_summary["status_counts"]["rejected"] >= 2

  identity_summary = artifact["surrogate_identity_manifest_summary"]
  assert identity_summary["model_ref"] == (
    "candidate://a2/runtime-aligned-vps/"
    "f16c-aim120c-blastfrag-beam-high-nearmiss-0_35m-v0"
  )
  assert identity_summary["model_version"] == "v0_candidate_runtime_aligned"
  assert (
    identity_summary["worktree_state"]
    == "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present"
  )
  assert identity_summary["current_validation_status"] == "not_validated"
  assert identity_summary["primary_release_scope"] == "effect_scale_authority_only"
  assert identity_summary["output_anchor_count"] == 3
  assert (
    identity_summary["retained_artifact_pack_status"]
    == "present_author_side_non_authoritative"
  )
  assert identity_summary["retained_artifact_manifest_ref"].endswith("manifest.json")
  assert identity_summary["retained_artifact_count"] == 4


def test_candidate_bundle_geometry_warhead_and_runtime_exercise_summaries(
  candidate_bundle_artifact: CandidateBundle,
) -> None:
  artifact = candidate_bundle_artifact

  geometry_summary = artifact["target_geometry_assumption_summary"]
  assert geometry_summary["author_status"] == "frozen_for_stage_b_review_only"
  assert geometry_summary["target_type"] == "F-16C_Block50"
  assert geometry_summary["used_by_stage_b_yes_count"] >= 1
  assert geometry_summary["unsupported_row_count"] >= 2

  warhead_summary = artifact["warhead_scope_summary"]
  assert warhead_summary["weapon_class"] == "AIM-120C-class"
  assert warhead_summary["weapon_family"] == "blast_fragmentation"
  assert warhead_summary["consumed_by_surrogate_yes_count"] >= 2
  assert warhead_summary["rejected_rows"] >= 1

  exercise = artifact["runtime_aligned_authority_exercise_summary"]
  assert exercise["status"] == "test_local_authority_exercise_only"
  assert not exercise["authority_boundary"]["stock_database_authority_granted"]
  assert exercise["effect_scale_descriptor_candidate"]["effect_scale_authority"]
  assert not exercise["effect_scale_descriptor_candidate"][
    "component_failure_probability_authority"
  ]
  assert exercise["component_failure_probability_descriptor_candidate"][
    "component_failure_probability_authority"
  ]
  assert not exercise["component_failure_probability_descriptor_candidate"][
    "effect_scale_authority"
  ]


def test_candidate_bundle_cli_writes_json(tmp_path: Path) -> None:
  output_path = tmp_path / "a2_candidate_vps_bundle.json"
  subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "candidate-artifacts",
      "package-bundle",
      "--output",
      str(output_path),
    ],
    cwd=REPO_ROOT,
    check=True,
  )

  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["status"] == "candidate_non_authoritative_bundle"
  assert artifact["documentation_status"]["ready_for_review"] is True
  assert artifact["authority_boundary"]["stock_database_authority_granted"] is False
  assert (
    artifact["validation_acceptance_criteria_summary"]["primary_release_scope"]
    == "effect_scale_authority_only"
  )
  assert (
    artifact["validation_scope_and_independence_summary"]["scope_manifest_status"]
    == "frozen_pre_run_stage_b_effect_scale_only"
  )
  assert (
    artifact["validation_stage_c_acceptance_criteria_summary"]["hard_gate_count"] == 23
  )
  assert (
    artifact["validation_stage_c_component_probability_snapshot_summary"][
      "component_failure_probability"
    ]
    == 0.67
  )
  assert (
    artifact["validation_stage_c_component_probability_result_pack_summary"][
      "artifact_hash_count"
    ]
    == 3
  )
  assert (
    artifact["validation_scope_probe_summary"]["closure_probe"]["metrics"][
      "mechanism_response_constant_across_closure"
    ]
    is False
  )
  assert (
    artifact["validation_benchmark_snapshot_summary"][
      "all_hard_gates_pass_in_current_snapshot"
    ]
    is True
  )
  assert artifact["validation_result_pack_summary"]["artifact_hash_count"] == 3
  assert (
    artifact["validation_release_readiness_gate_summary"]["blocking_condition_count"]
    == 8
  )
  assert (
    artifact["validation_release_readiness_gate_summary"]["satisfied_condition_count"]
    == 6
  )
  assert artifact["validation_retained_artifact_pack_summary"]["retained_artifact_count"] == 4
  assert (
    artifact["residual_acceptance_gate_summaries"][
      "res003_target_geometry_closeout"
    ]["release_blocked"]
    is True
  )
  assert (
    artifact["residual_acceptance_gate_summaries"][
      "res006_beco_recalculation_admission"
    ]["mismatch_count"]
    == 9
  )
