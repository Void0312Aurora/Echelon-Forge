from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_stage_b_retained_artifact_pack as retained_pack


def test_a2_blastfrag_stage_b_retained_artifact_pack_writes_retained_files(
    tmp_path: Path,
) -> None:
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


def test_a2_blastfrag_stage_b_retained_artifact_pack_cli_writes_manifest(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "retained_pack_cli"
    completed = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_b_retained_artifact_pack.py",
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
