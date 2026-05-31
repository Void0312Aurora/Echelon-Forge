from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_component_probability_surface_probe as surface_probe,
)


def test_a2_blastfrag_stage_c_component_probability_surface_probe_is_non_authoritative(
) -> None:
    artifact = surface_probe.generate_stage_c_component_probability_surface_probe(
        repo_root=REPO_ROOT
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert (
        artifact["schema_version"]
        == "a2.stage_c_component_probability_surface_probe.v1"
    )
    assert (
        artifact["status"]
        == "candidate_non_authoritative_stage_c_component_probability_surface_probe"
    )

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["runtime_miss_distance_bucket"] == "near_miss"
    assert scope["component_name"] == "right_aileron_actuator"
    assert scope["component_system"] == "flight_control"
    assert scope["component_redundancy_group_id"] == "lateral_flight_control_actuators"

    descriptor = artifact["descriptor_candidate_summary"]
    assert descriptor["dataset_id"] == (
        "unit_test_a2_blastfrag_runtime_aligned_component_probability_surface_probe"
    )
    assert descriptor["source_kind"] == "validated_physics_surrogate"
    assert descriptor["calibration_status"] == "calibrated"
    assert descriptor["component_failure_probability_authority"] is True
    assert descriptor["row_count"] == 4
    assert descriptor["component_specific_row_count"] == 3
    assert descriptor["global_fallback_row_id"] == "global-fallback"

    determinism = artifact["determinism_summary"]
    assert determinism["probe_labels_are_fixed"] == ["inner", "middle", "outer"]
    assert determinism["probe_local_points_are_fixed"] == [
        [-0.753, 5.5, 0.0],
        [-0.753, 5.8, 0.0],
        [-0.753, 6.0, 0.0],
    ]
    assert determinism["runtime_seed_values_are_fixed"] == [
        20260526,
        20260527,
        20260528,
    ]
    assert determinism["descriptor_gate_bands_use_stock_seed"] == 20260526
    assert determinism["json_output_uses_sort_keys"] is True
    assert determinism["runtime_database_copy_is_temporary"] is True

    stock_baseline = artifact["stock_baseline_probe_summary"]
    assert stock_baseline["source_database"] == "examples/config/database"
    assert stock_baseline["probe_labels"] == ["inner", "middle", "outer"]
    assert stock_baseline["component_primary_names"] == [
        "right_aileron_actuator",
        "right_aileron_actuator",
        "right_aileron_actuator",
    ]
    assert stock_baseline["component_probability_sources"] == [
        "synthetic_sigmoid",
        "synthetic_sigmoid",
        "synthetic_sigmoid",
    ]
    assert stock_baseline["all_probability_sources_are_synthetic_sigmoid"] is True
    assert stock_baseline["any_calibrated_component_probability"] is False

    scope_audit = artifact["component_scope_audit"]
    assert scope_audit["candidate_component_name"] == "right_aileron_actuator"
    assert scope_audit["candidate_component_system"] == "flight_control"
    assert (
        scope_audit["candidate_component_redundancy_group_id"]
        == "lateral_flight_control_actuators"
    )
    assert scope_audit["component_specific_row_ids"] == [
        "component-inner",
        "component-middle",
        "component-outer",
    ]
    assert (
        scope_audit["component_specific_rows_scope_locked_to_primary_component"]
        is True
    )
    assert scope_audit["selected_rows_scope_locked_to_primary_component"] is True
    assert scope_audit["global_fallback_row_id"] == "global-fallback"
    assert scope_audit["global_fallback_row_has_no_component_identity"] is True

    rows = artifact["surface_probe_rows"]
    assert [row["probe_label"] for row in rows] == ["inner", "middle", "outer"]
    assert [row["selected_row_id"] for row in rows] == [
        "component-inner",
        "component-middle",
        "component-outer",
    ]
    assert [row["selected_row_probability"] for row in rows] == [0.52, 0.37, 0.21]
    assert all(row["component_primary_name"] == "right_aileron_actuator" for row in rows)
    assert all(row["selected_row_matches_component_specific_scope"] for row in rows)
    assert all(row["selected_row_covers_primary_loads"] for row in rows)

    metrics = artifact["metrics"]
    assert metrics["primary_component_identity_stable_pass"] is True
    assert metrics["component_specific_precedence_pass"] is True
    assert metrics["selected_rows_cover_primary_loads_pass"] is True
    assert metrics["probability_monotonic_decreasing_with_standoff_pass"] is True
    assert metrics["selected_row_ids_are_distinct_pass"] is True
    assert metrics["anchor_seed_window_cv_pass"] is True

    repeatability = artifact["repeatability_summary"]
    assert repeatability["anchor_probe_label"] == "middle"
    assert repeatability["seed_values"] == [20260526, 20260527, 20260528]
    assert repeatability["selected_row_ids"] == [
        "component-middle",
        "component-middle",
        "component-middle",
    ]
    assert repeatability["component_failure_probability"]["cv"] <= 0.05
    assert repeatability["fragment_areal_density_per_m2"]["cv"] <= 0.05
    assert repeatability["fragment_energy_j"]["cv"] <= 0.05
    assert repeatability["penetration_margin"]["cv"] <= 0.05
    assert repeatability["blast_impulse_kpa_ms"]["cv"] <= 0.05

    findings = artifact["current_findings"]
    assert "three-point component-specific surface probe" in findings[0]
    assert "decrease monotonically" in findings[1]
    assert "does not close fragility truth" in findings[2]

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False


def test_a2_blastfrag_stage_c_component_probability_surface_probe_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_component_probability_surface_probe.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_c_component_probability_surface_probe.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert (
        artifact["status"]
        == "candidate_non_authoritative_stage_c_component_probability_surface_probe"
    )
    assert artifact["metrics"]["probability_monotonic_decreasing_with_standoff_pass"] is True
    assert artifact["repeatability_summary"]["component_failure_probability"]["cv"] <= 0.05
