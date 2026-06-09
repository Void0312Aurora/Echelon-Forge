from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tests.architecture.damage_model.helpers import (
    assert_authority_guards_false,
    run_maintenance_cli,
)
from tests.architecture.helpers import read_json


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_scope_boundary_probe as boundary_probe,
    a2_blastfrag_stage_b_effect_scale_snapshot as snapshot,
    a2_blastfrag_stage_b_validation_result_pack as result_pack,
    a2_blastfrag_validation_scaffold as scaffold,
)


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
            "tools/maintenance/a2_blastfrag_validation_scaffold.py",
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
            "tools/maintenance/a2_blastfrag_scope_boundary_probe.py",
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
        "a2_blastfrag_stage_b_effect_scale_snapshot.py",
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
            "tools/maintenance/a2_blastfrag_stage_b_validation_result_pack.py",
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
