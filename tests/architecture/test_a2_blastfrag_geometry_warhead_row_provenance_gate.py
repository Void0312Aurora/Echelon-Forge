from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_geometry_warhead_row_provenance_gate as gate,
)


def test_a2_blastfrag_geometry_warhead_row_provenance_gate_blocks_current_scope(
) -> None:
    artifact = gate.generate_geometry_warhead_row_provenance_gate(repo_root=REPO_ROOT)

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
    for row in required_inputs.values():
        assert row["exists"] is True
        assert len(row["sha256"]) == 64
        assert row["content_hash"] == f"sha256:{row['sha256']}"
        assert row["size_bytes"] > 0

    residual_status = artifact["residual_status"]
    assert residual_status["RES-003"]["status"] == "blocked_row_level_bounds_missing"
    assert residual_status["RES-003"]["register"]["register_status"] == "open"
    assert residual_status["RES-003"]["closed_by_this_gate"] is False
    assert residual_status["RES-004"]["status"] == "blocked_warhead_class_bounds_missing"
    assert residual_status["RES-004"]["register"]["register_status"] == "open"
    assert residual_status["RES-004"]["closed_by_this_gate"] is False

    assert [check["check_id"] for check in artifact["gate_checks"]] == [
        "ROWWAR-RES003-001",
        "ROWWAR-RES003-002",
        "ROWWAR-RES004-001",
        "ROWWAR-RES004-002",
    ]
    assert not any(check["release_grade_satisfied"] for check in artifact["gate_checks"])

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


def test_a2_blastfrag_geometry_warhead_row_provenance_gate_keeps_all_authority_guards_false(
) -> None:
    artifact = gate.generate_geometry_warhead_row_provenance_gate(repo_root=REPO_ROOT)

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


def test_a2_blastfrag_geometry_warhead_row_provenance_gate_cli_writes_retained_artifacts(
    tmp_path: Path,
) -> None:
    retained_dir = tmp_path / "retained"
    doc_output = tmp_path / "validation_geometry_warhead_row_provenance_gate.md"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_geometry_warhead_row_provenance_gate.py",
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
