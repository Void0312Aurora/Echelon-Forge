from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_runtime_aligned_authority_pack as authority_pack,
)


def test_a2_blastfrag_runtime_aligned_authority_pack_current_repo_is_test_local_only() -> None:
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

    component_rows = artifact["baseline_component_rows"]
    assert len(component_rows) >= 1
    primary_rows = [
        row for row in component_rows if row["component_name"] == "right_aileron_actuator"
    ]
    assert len(primary_rows) == 1

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


def test_a2_blastfrag_runtime_aligned_authority_pack_is_reproducible() -> None:
    lhs = authority_pack.generate_runtime_aligned_authority_pack(repo_root=REPO_ROOT)
    rhs = authority_pack.generate_runtime_aligned_authority_pack(repo_root=REPO_ROOT)

    assert lhs["baseline_event_summary"] == rhs["baseline_event_summary"]
    assert lhs["baseline_component_rows"] == rhs["baseline_component_rows"]
    assert lhs["effect_scale_descriptor_candidate"] == rhs["effect_scale_descriptor_candidate"]
    assert (
        lhs["component_failure_probability_descriptor_candidate"]
        == rhs["component_failure_probability_descriptor_candidate"]
    )


def test_a2_blastfrag_runtime_aligned_authority_pack_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "blastfrag_runtime_aligned_authority_pack.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py",
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
