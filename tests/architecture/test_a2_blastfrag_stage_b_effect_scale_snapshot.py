from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_stage_b_effect_scale_snapshot as snapshot


def test_a2_blastfrag_stage_b_effect_scale_snapshot_current_repo_is_non_authoritative() -> None:
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

    guards = artifact["non_authoritative_guards"]
    assert not guards["stock_runtime_authority_granted"]
    assert not guards["effect_scale_authority_granted"]
    assert not guards["component_failure_probability_authority_granted"]
    assert not guards["pk_authority_granted"]
    assert not guards["deterministic_fuze_authority_granted"]


def test_a2_blastfrag_stage_b_effect_scale_snapshot_cli_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "a2_stage_b_effect_scale_snapshot.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_b_effect_scale_snapshot.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["status"] == "candidate_non_authoritative_stage_b_snapshot"
    assert artifact["summary"]["all_hard_gates_pass_in_current_snapshot"] is True
    assert artifact["non_authoritative_guards"]["stock_runtime_authority_granted"] is False
