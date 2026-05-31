from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_component_probability_snapshot as snapshot,
)


def test_a2_blastfrag_stage_c_component_probability_snapshot_current_repo_is_non_authoritative(
) -> None:
    artifact = snapshot.generate_stage_c_component_probability_snapshot(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_c_component_probability_snapshot.v1"
    assert (
        artifact["status"]
        == "candidate_non_authoritative_stage_c_component_probability_snapshot"
    )

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["candidate_scope_label"] == "near_miss_0_35m"
    assert scope["runtime_miss_distance_bucket"] == "near_miss"
    assert scope["component_name"] == "right_aileron_actuator"
    assert scope["component_system"] == "flight_control"
    assert scope["component_redundancy_group_id"] == "lateral_flight_control_actuators"

    summary = artifact["summary"]
    assert summary["all_hard_gates_pass_in_current_snapshot"]
    assert summary["failed_criteria_ids"] == []
    assert summary["reviewed_checks"] == [
        "runtime_projected_component_row_present",
        "descriptor_authority_flags",
        "component_provenance_fields",
        "mechanism_load_gate_band_contains_primary_row",
        "component_probability_surface_probe",
    ]
    assert summary["primary_release_scope"] == "component_failure_probability_authority_only"
    assert summary["review_status"] == "author_snapshot_only_pending_independent_review"

    criteria_rows = artifact["criteria_evaluation"]
    assert len(criteria_rows) == 23
    assert all(row["pass"] for row in criteria_rows)
    assert criteria_rows[0]["criteria_id"] == "BFM-CRIT-CP-001"
    assert criteria_rows[-1]["criteria_id"] == "BFM-CRIT-CP-023"

    baseline = artifact["baseline_event_summary"]
    assert baseline["component_primary_name"] == "right_aileron_actuator"
    assert baseline["component_failure_probability_source"] == "synthetic_sigmoid"
    assert baseline["component_primary_mechanism_fragment_energy_j"] > 0.0
    assert baseline["component_primary_mechanism_penetration_margin"] > 0.0
    assert baseline["component_primary_mechanism_blast_impulse_kpa_ms"] > 0.0

    component_snapshot = artifact["component_probability_snapshot"]
    assert component_snapshot["descriptor_status"] == (
        "test_local_component_specific_probability_candidate"
    )
    assert component_snapshot["source_kind"] == "validated_physics_surrogate"
    assert component_snapshot["calibration_status"] == "calibrated"
    assert component_snapshot["component_failure_probability_authority"] is True
    assert component_snapshot["row"]["component_name"] == "right_aileron_actuator"
    assert component_snapshot["row"]["component_failure_probability"] == 0.67
    assert component_snapshot["row"]["min_fragment_energy_j"] > 0.0
    assert component_snapshot["row"]["min_blast_impulse_kpa_ms"] > 0.0

    surface_probe = artifact["surface_probe_summary"]
    assert surface_probe["status"] == (
        "candidate_non_authoritative_stage_c_component_probability_surface_probe"
    )
    assert surface_probe["probe_labels"] == ["inner", "middle", "outer"]
    assert surface_probe["runtime_seed_values_are_fixed"] == [
        20260526,
        20260527,
        20260528,
    ]
    assert surface_probe["json_output_uses_sort_keys"] is True
    assert surface_probe["selected_row_ids"] == [
        "component-inner",
        "component-middle",
        "component-outer",
    ]
    assert surface_probe["primary_component_identity_stable_pass"] is True
    assert surface_probe["component_specific_precedence_pass"] is True
    assert surface_probe["selected_rows_cover_primary_loads_pass"] is True
    assert surface_probe["probability_monotonic_decreasing_with_standoff_pass"] is True
    assert surface_probe["anchor_seed_window_probability_cv"] <= 0.05
    assert surface_probe["stock_baseline_sources_are_synthetic_sigmoid"] is True
    assert surface_probe["stock_baseline_calibrated_probability_present"] is False
    assert (
        surface_probe[
            "component_specific_rows_scope_locked_to_right_aileron_actuator"
        ]
        is True
    )
    assert (
        surface_probe["selected_rows_scope_locked_to_right_aileron_actuator"]
        is True
    )

    findings = artifact["current_findings"]
    assert "bind a component-specific probability row" in findings[0]
    assert "three-point candidate component-probability surface probe" in findings[1]
    assert "synthetic component probability" in findings[2]
    assert "does not validate fragility truth" in findings[3]

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False


def test_a2_blastfrag_stage_c_component_probability_snapshot_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_component_probability_snapshot.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_c_component_probability_snapshot.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert (
        artifact["status"]
        == "candidate_non_authoritative_stage_c_component_probability_snapshot"
    )
    assert artifact["summary"]["all_hard_gates_pass_in_current_snapshot"] is True
    assert artifact["non_authoritative_guards"]["stock_runtime_authority_granted"] is False
