from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_scope_boundary_probe as boundary_probe


def test_a2_blastfrag_scope_boundary_probe_current_repo_is_non_authoritative() -> None:
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
    assert [row["standoff_m"] for row in miss_distance_probe["rows"]] == [0.25, 0.35, 0.45]
    assert all(row["runtime_miss_distance_bucket"] == "near_miss" for row in miss_distance_probe["rows"])

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
    assert [row["closure_mps"] for row in closure_probe["rows"]] == [700.0, 900.0, 1100.0]
    assert (
        closure_probe["rows"][0]["fragment_areal_density_per_m2"] <
        closure_probe["rows"][1]["fragment_areal_density_per_m2"] <
        closure_probe["rows"][2]["fragment_areal_density_per_m2"]
    )
    assert (
        closure_probe["rows"][0]["blast_impulse_kpa_ms_proxy"] <
        closure_probe["rows"][1]["blast_impulse_kpa_ms_proxy"] <
        closure_probe["rows"][2]["blast_impulse_kpa_ms_proxy"]
    )
    assert (
        closure_probe["rows"][0]["fragment_energy_j_proxy"] <
        closure_probe["rows"][1]["fragment_energy_j_proxy"] <
        closure_probe["rows"][2]["fragment_energy_j_proxy"]
    )
    assert "candidate closure-sensitive response is present" in closure_probe["limitation_note"]
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


def test_a2_blastfrag_scope_boundary_probe_cli_writes_json(tmp_path: Path) -> None:
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
