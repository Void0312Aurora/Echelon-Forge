from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_component_probability_result_pack as result_pack,
)


def test_a2_blastfrag_stage_c_component_probability_result_pack_current_repo_is_non_authoritative(
) -> None:
    artifact = result_pack.generate_stage_c_component_probability_result_pack(
        repo_root=REPO_ROOT
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_c_component_probability_result_pack.v1"
    assert (
        artifact["status"]
        == "candidate_non_authoritative_stage_c_component_probability_result_pack"
    )

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["component_name"] == "right_aileron_actuator"

    artifact_hashes = artifact["artifact_hashes"]
    assert len(artifact_hashes) == 3
    assert [row["artifact_id"] for row in artifact_hashes] == [
        "ART-RUNTIME-AUTH-001",
        "ART-STAGE-C-SNAPSHOT-001",
        "ART-STAGE-C-SURFACE-001",
    ]
    assert all(len(row["sha256"]) == 64 for row in artifact_hashes)

    result_summary = artifact["result_table_summary"]
    assert result_summary["all_hard_gates_pass_in_current_snapshot"] is True
    assert result_summary["failed_criteria_ids"] == []
    assert result_summary["reviewed_checks"] == [
        "runtime_projected_component_row_present",
        "descriptor_authority_flags",
        "component_provenance_fields",
        "mechanism_load_gate_band_contains_primary_row",
        "component_probability_surface_probe",
    ]
    assert (
        result_summary["primary_release_scope"]
        == "component_failure_probability_authority_only"
    )
    assert (
        result_summary["review_status"]
        == "author_result_pack_only_pending_independent_review"
    )

    probability = artifact["component_probability_result_summary"]
    assert probability["baseline_component_probability_source"] == "synthetic_sigmoid"
    assert probability["candidate_component_name"] == "right_aileron_actuator"
    assert probability["candidate_component_system"] == "flight_control"
    assert (
        probability["candidate_component_redundancy_group_id"]
        == "lateral_flight_control_actuators"
    )
    assert probability["candidate_component_failure_probability"] == 0.67
    assert "candidate component-specific probability snapshot only" in probability[
        "result_interpretation"
    ]

    scope_audit = artifact["scope_audit_summary"]
    assert scope_audit["projected_component_row_count"] >= 1
    assert scope_audit["primary_component_name"] == "right_aileron_actuator"
    assert scope_audit["gate_band_contains_primary_blast_scaled_distance"] is True
    assert scope_audit["gate_band_contains_primary_fragment_density"] is True
    assert scope_audit["gate_band_contains_primary_fragment_energy"] is True
    assert scope_audit["gate_band_contains_primary_penetration_margin"] is True
    assert scope_audit["gate_band_contains_primary_blast_impulse"] is True
    assert scope_audit["gate_band_contains_primary_surface_incidence"] is True
    assert "one component-specific candidate row" in scope_audit[
        "scope_guard_interpretation"
    ]

    fragility_surface = artifact["fragility_surface_summary"]
    assert (
        fragility_surface["surface_probe_status"]
        == "candidate_non_authoritative_stage_c_component_probability_surface_probe"
    )
    assert fragility_surface["probe_row_count"] == 3
    assert fragility_surface["probe_labels"] == ["inner", "middle", "outer"]
    assert fragility_surface["runtime_seed_values_are_fixed"] == [
        20260526,
        20260527,
        20260528,
    ]
    assert fragility_surface["json_output_uses_sort_keys"] is True
    assert fragility_surface["primary_component_identity_stable_pass"] is True
    assert fragility_surface["component_specific_precedence_pass"] is True
    assert fragility_surface["selected_rows_cover_primary_loads_pass"] is True
    assert fragility_surface["probability_monotonic_decreasing_with_standoff_pass"] is True
    assert fragility_surface["anchor_seed_window_probability_cv"] <= 0.05
    assert "candidate fragility-surface" in fragility_surface["result_interpretation"]
    assert fragility_surface["stock_baseline_sources_are_synthetic_sigmoid"] is True
    assert (
        fragility_surface["component_scope_locked_to_right_aileron_actuator"]
        is True
    )

    upstream = artifact["upstream_stage_b_dependency_summary"]
    assert upstream["dependency_role"] == (
        "separate_upstream_effect_scale_authority_track"
    )
    assert upstream["status"] == "blocked_non_authoritative_stage_b_release_candidate"
    assert upstream["release_target"] == "effect_scale_authority_only"
    assert upstream["dependency_preserved_as_blocked"] is True
    assert "RES-010" in upstream["blocking_residual_ids"]
    assert "Stage C component-probability packaging remains candidate" in upstream[
        "stage_c_interlock"
    ]

    independence = artifact["independence_audit"]
    assert [row["artifact_id"] for row in independence] == [
        "ART-RUNTIME-AUTH-001",
        "ART-STAGE-C-SNAPSHOT-001",
        "ROW-COMPONENT-001",
    ]
    assert independence[0]["audit_outcome"] == "test_local_positive_path_only"
    assert (
        independence[1]["audit_outcome"]
        == "candidate_snapshot_only_not_independent_validation"
    )
    assert independence[2]["audit_outcome"] == "candidate_component_specific_only"

    findings = artifact["current_findings"]
    assert "surface probe" in findings[0]
    assert "synthetic component probability" in findings[1]
    assert "lacks independent fragility validation" in findings[2]

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False


def test_a2_blastfrag_stage_c_component_probability_result_pack_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_component_probability_result_pack.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_c_component_probability_result_pack.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert (
        artifact["status"]
        == "candidate_non_authoritative_stage_c_component_probability_result_pack"
    )
    assert artifact["result_table_summary"]["all_hard_gates_pass_in_current_snapshot"] is True
    assert artifact["scope_audit_summary"]["gate_band_contains_primary_surface_incidence"]
    assert artifact["scope_audit_summary"]["gate_band_contains_primary_blast_impulse"]
    assert artifact["fragility_surface_summary"]["probe_row_count"] == 3
    assert (
        artifact["upstream_stage_b_dependency_summary"]["dependency_preserved_as_blocked"]
        is True
    )
