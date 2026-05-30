from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_validation_scaffold as scaffold


def test_a2_blastfrag_validation_scaffold_current_repo_is_non_authoritative() -> None:
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

    bm006 = artifact["benchmarks"]["BFM-BM-006"]
    assert bm006["metrics"]["source_trace_error_count"] == 0
    assert bm006["metrics"]["source_trace_warning_count"] == 0

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
    assert row["min_blast_scaled_distance_m_kg13"] <= mechanism["blast_scaled_distance_m_kg13"]
    assert row["max_blast_scaled_distance_m_kg13"] >= mechanism["blast_scaled_distance_m_kg13"]
    assert row["min_fragment_areal_density_per_m2"] <= mechanism["fragment_areal_density_per_m2"]
    assert row["max_fragment_areal_density_per_m2"] >= mechanism["fragment_areal_density_per_m2"]
    assert row["min_surface_incidence_cos"] <= mechanism["surface_incidence_cos"]
    assert row["max_surface_incidence_cos"] >= mechanism["surface_incidence_cos"]


def test_a2_blastfrag_validation_scaffold_is_fixed_seed_reproducible() -> None:
    lhs = scaffold.generate_validation_scaffold(repo_root=REPO_ROOT, seed=12345)
    rhs = scaffold.generate_validation_scaffold(repo_root=REPO_ROOT, seed=12345)

    assert (
        lhs["benchmarks"]["BFM-BM-003"]["current_point"]["beam_witness_areal_density_per_m2"]
        == rhs["benchmarks"]["BFM-BM-003"]["current_point"]["beam_witness_areal_density_per_m2"]
    )
    assert (
        lhs["benchmarks"]["BFM-BM-003"]["current_point"]["hit_count"]
        == rhs["benchmarks"]["BFM-BM-003"]["current_point"]["hit_count"]
    )
    assert lhs["mechanism_load_vector"] == rhs["mechanism_load_vector"]
    assert lhs["diagnostic_only_fields"] == rhs["diagnostic_only_fields"]
    assert lhs["vulnerability_evidence_draft"] == rhs["vulnerability_evidence_draft"]


def test_a2_blastfrag_validation_scaffold_cli_writes_json(tmp_path: Path) -> None:
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
