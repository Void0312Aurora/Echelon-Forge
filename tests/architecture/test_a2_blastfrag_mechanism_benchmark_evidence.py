from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_mechanism_benchmark_evidence as evidence,
)


def _by_residual(artifact: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = artifact["residual_benchmark_evidence"]
    assert isinstance(rows, list)
    return {str(row["residual_id"]): row for row in rows}


def _matrix_by_lineage(artifact: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = artifact["source_consumption_validation_matrix"]
    assert isinstance(rows, list)
    return {str(row["lineage_id"]): row for row in rows}


def test_a2_blastfrag_mechanism_benchmark_evidence_current_repo_fails_closed() -> None:
    artifact = evidence.generate_mechanism_benchmark_evidence(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.mechanism_benchmark_evidence.v1"
    assert (
        artifact["status"]
        == "blocked_fail_closed_mechanism_benchmark_evidence_manifest"
    )
    for ref in artifact["doc_refs"].values():
        assert (REPO_ROOT / str(ref)).exists()

    assert artifact["current_gate_results"] == {
        "RES-003": "blocked_fail_closed_release_grade_geometry_benchmark_missing",
        "RES-004": (
            "blocked_fail_closed_release_grade_warhead_sensitivity_benchmark_missing"
        ),
        "RES-005": "blocked_fail_closed_fragment_benchmark_payload_missing",
        "RES-006": "blocked_fail_closed_blast_benchmark_payload_missing",
    }

    decision = artifact["benchmark_evidence_decision"]
    assert decision["mechanism_benchmark_evidence_ready"] is False
    assert decision["mechanism_benchmark_evidence_blocked"] is True
    assert decision["fail_closed"] is True
    assert decision["closed_residual_ids_by_this_gate"] == []
    assert decision["candidate_or_toy_probe_is_calibration"] is False
    assert decision["pk_authority_included"] is False
    assert decision["deterministic_fuze_authority_included"] is False

    rows = _by_residual(artifact)
    for residual_id in ("RES-003", "RES-004", "RES-005", "RES-006"):
        row = rows[residual_id]
        assert row["source_present"] is True
        assert row["candidate_or_scaffold_consumed"] is True
        assert row["benchmark_consumed"] is False
        assert row["release_grade_validated"] is False
        assert row["shortest_completion_path"]

    res003 = rows["RES-003"]
    assert res003["evidence_status"] == (
        "review_inputs_present_external_geometry_benchmark_missing"
    )
    res003_observed = res003["observed_evidence"]
    assert res003_observed["target_geometry_assumption_summary"][
        "unsupported_row_count"
    ] == 2
    assert "PIN-F16-003" in res003_observed["pin_evidence"]["sanity_only_pin_ids"]

    res004 = rows["RES-004"]
    assert res004["evidence_status"] == (
        "scope_and_sensitivity_boundary_present_external_warhead_benchmark_missing"
    )
    res004_observed = res004["observed_evidence"]
    assert res004_observed["warhead_scope_summary"][
        "consumed_by_surrogate_yes_count"
    ] == 3
    assert "PIN-AIM120-TPC-REJ" in res004_observed["pin_evidence"][
        "rejected_pin_ids"
    ]


def test_a2_blastfrag_mechanism_benchmark_evidence_separates_source_consumption_and_validation() -> None:
    artifact = evidence.generate_mechanism_benchmark_evidence(repo_root=REPO_ROOT)

    matrix = _matrix_by_lineage(artifact)
    assert set(matrix) == {
        "FRAG-GURNEY-BRL405",
        "FRAG-TP21-DEBRIS",
        "FRAG-TOY-SCAFFOLD",
        "BLAST-KINGERY-BULMASH",
        "BLAST-BEC-O-TP20",
        "BLAST-TOY-SCAFFOLD",
    }
    for row in matrix.values():
        assert set(row) == {
            "lineage_id",
            "residual_id",
            "source_present",
            "benchmark_consumed",
            "release_grade_validated",
            "evidence_status",
        }
        assert row["source_present"] is True
        assert row["benchmark_consumed"] is False
        assert row["release_grade_validated"] is False

    lineages = artifact["fragment_blast_lineage_summary"]
    frag = {row["lineage_id"]: row for row in lineages["fragment"]}
    blast = {row["lineage_id"]: row for row in lineages["blast"]}

    assert "VPS-BFM-007" in frag["FRAG-GURNEY-BRL405"][
        "pending_acquisition_source_ids"
    ]
    assert "PIN-BFM-002" in frag["FRAG-TP21-DEBRIS"]["pin_evidence"][
        "externally_verified_candidate_pin_ids"
    ]
    assert frag["FRAG-TP21-DEBRIS"]["pin_evidence"][
        "consumption_status_by_pin"
    ]["PIN-BFM-002"] == "not_consumed_for_stage_b_release"
    assert frag["FRAG-TOY-SCAFFOLD"]["candidate_or_scaffold_consumed"] is True
    assert frag["FRAG-TOY-SCAFFOLD"]["evidence_status"] == (
        "toy_probe_consumed_for_hygiene_not_calibration"
    )

    assert "VPS-BFM-003" in blast["BLAST-KINGERY-BULMASH"][
        "pending_acquisition_source_ids"
    ]
    assert "PIN-BFM-001" in blast["BLAST-BEC-O-TP20"]["pin_evidence"][
        "externally_verified_candidate_pin_ids"
    ]
    assert blast["BLAST-BEC-O-TP20"]["pin_evidence"][
        "consumption_status_by_pin"
    ]["PIN-BFM-001"] == "not_consumed_for_stage_b_release"
    assert blast["BLAST-TOY-SCAFFOLD"]["candidate_or_scaffold_consumed"] is True
    assert blast["BLAST-TOY-SCAFFOLD"]["evidence_status"] == (
        "toy_probe_consumed_for_hygiene_not_calibration"
    )


def test_a2_blastfrag_mechanism_benchmark_evidence_cli_and_authority_guards(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "mechanism_benchmark_evidence.json"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_mechanism_benchmark_evidence.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert result.stdout == ""
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "a2.mechanism_benchmark_evidence.v1"

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["target_geometry_authority_granted"] is False
    assert guards["aim120c_warhead_authority_granted"] is False
    assert guards["fragment_mechanism_authority_granted"] is False
    assert guards["blast_mechanism_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False
    assert any("source_present" in note for note in artifact["integration_notes"])
