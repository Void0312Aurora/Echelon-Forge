from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_mechanism_comparison_hashes as hashes,
)


HEX64 = re.compile(r"^[a-f0-9]{64}$")


def _walk(payload: Any) -> list[Any]:
    values = [payload]
    if isinstance(payload, dict):
        for value in payload.values():
            values.extend(_walk(value))
    elif isinstance(payload, list):
        for value in payload:
            values.extend(_walk(value))
    return values


def test_a2_blastfrag_mechanism_comparison_hashes_current_repo_is_fail_closed() -> None:
    artifact = hashes.generate_mechanism_comparison_hashes(repo_root=REPO_ROOT)

    assert artifact["schema_version"] == "a2.mechanism_comparison_hashes.v1"
    assert artifact["status"] == "partial_fail_closed_mechanism_comparison_hash_manifest"
    assert artifact["current_gate_results"] == {
        "RES-005": (
            "partial_fail_closed_tp21_criteria_vocabulary_hash_present_"
            "selected_debris_output_requirements_open"
        ),
        "RES-006": (
            "partial_fail_closed_beco_cached_comparison_hashes_present_"
            "spreadsheet_execution_required"
        ),
    }

    decision = artifact["comparison_hash_decision"]
    assert decision["closed_residual_ids_by_this_gate"] == []
    assert decision["fail_closed"] is True
    assert decision["source_presence_is_calibration"] is False
    assert decision["beco_cached_hashes_are_calibration"] is False
    assert decision["tp21_vocabulary_is_calibration"] is False
    assert decision["benchmark_consumed_for_release"] is False
    assert decision["release_grade_validated"] is False
    assert decision["selected_beco_cached_output_hashes_present"] is True
    assert decision["tp21_selected_debris_output_hashes_present"] is False

    matrix = {
        row["lineage_id"]: row for row in artifact["source_consumption_validation_matrix"]
    }
    assert matrix["FRAG-TP21-DEBRIS"]["source_present"] is True
    assert matrix["FRAG-TP21-DEBRIS"]["comparison_output_hash_present"] is False
    assert matrix["FRAG-TP21-DEBRIS"]["benchmark_consumed"] is False
    assert matrix["BLAST-BEC-O-TP20"]["source_present"] is True
    assert matrix["BLAST-BEC-O-TP20"]["comparison_output_hash_present"] is True
    assert matrix["BLAST-BEC-O-TP20"]["benchmark_consumed"] is False

    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["non_authoritative_guards"].values())


def test_a2_blastfrag_mechanism_comparison_hashes_beco_metadata_and_hash_only_outputs() -> None:
    artifact = hashes.generate_mechanism_comparison_hashes(repo_root=REPO_ROOT)
    beco = artifact["beco_workbook"]

    assert beco["workbook_sha256"] == (
        "82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc"
    )
    assert beco["parse_status"] == "metadata_and_cached_formula_hashes_retained"
    assert beco["spreadsheet_calculation_executed"] is False
    assert beco["spreadsheet_execution_status"] == (
        "not_executed_fail_closed_cached_values_only"
    )
    assert beco["benchmark_consumed_for_release"] is False
    assert beco["cached_workbook_values_are_calibration"] is False

    sheets = {row["sheet_name"]: row for row in beco["sheet_inventory"]}
    assert set(sheets) == {
        "START",
        "ENGLISH UNITS ",
        "ENGLISH-TO-METRIC CONVERSION",
        "METRIC UNITS",
        "METRIC-TO-ENGLISH CONVERSION",
        "Munition Data",
        "Explosive Data",
    }
    assert sheets["METRIC UNITS"]["dimension"] == "A1:CL273"
    assert sheets["METRIC UNITS"]["numeric_cached_formula_value_count"] > 0

    selected = beco["selected_comparison_hashes"]
    assert len(selected) == len(hashes.BECO_SELECTED_OUTPUTS)
    assert beco["selected_comparison_output_count"] == len(hashes.BECO_SELECTED_OUTPUTS)
    assert HEX64.fullmatch(beco["selected_comparison_output_set_sha256"])
    for row in selected:
        assert row["value_kind"] == "cached_formula_numeric"
        assert row["formula_present"] is True
        assert row["cached_formula_value_present"] is True
        assert row["numeric_cached_formula_value_present"] is True
        assert HEX64.fullmatch(row["formula_sha256"])
        assert HEX64.fullmatch(row["comparison_output_sha256"])
        assert row["benchmark_consumed_for_release"] is False
        assert row["comparison_hash_is_calibration"] is False

    forbidden_raw_keys = {"cached_formula_value", "formula"}
    for value in _walk(beco):
        if isinstance(value, dict):
            assert not (forbidden_raw_keys & set(value))

    requirements = artifact["fail_closed_selected_output_requirements"]["RES-006"]
    assert len(requirements) == len(hashes.BECO_SELECTED_OUTPUTS)
    assert all(
        row["current_status"] == "cached_hash_available_recalculation_required"
        for row in requirements
    )
    assert all(row["raw_source_value_must_not_be_copied_to_dataset"] for row in requirements)


def test_a2_blastfrag_mechanism_comparison_hashes_tp21_vocabulary_not_dataset() -> None:
    artifact = hashes.generate_mechanism_comparison_hashes(repo_root=REPO_ROOT)
    tp21 = artifact["tp21_criteria_vocabulary"]

    assert tp21["artifact_sha256"] == (
        "84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8"
    )
    assert tp21["criteria_vocabulary_status"] == (
        "controlled_vocabulary_hash_retained_no_source_text_dataset"
    )
    assert HEX64.fullmatch(tp21["criteria_vocabulary_sha256"])
    assert tp21["source_text_copied_to_dataset"] is False
    assert tp21["selected_debris_output_hashes"] == []
    assert tp21["benchmark_consumed_for_release"] is False
    assert tp21["criteria_vocabulary_is_calibration"] is False

    vocab_keys = [row["criteria_key"] for row in tp21["allowed_criteria_vocabulary"]]
    assert vocab_keys == [
        "debris_item_class",
        "debris_mass_bin",
        "debris_velocity_or_throw_bin",
        "standoff_or_separation_bin",
        "target_exposure_or_area_bin",
        "unit_system",
        "applicability_limit",
        "exclusion_reason",
    ]
    requirements = artifact["fail_closed_selected_output_requirements"]["RES-005"]
    assert len(requirements) == len(vocab_keys)
    assert all(
        row["current_status"] == "selected_debris_output_hash_missing"
        for row in requirements
    )
    assert all(row["source_text_must_not_be_copied_to_dataset"] for row in requirements)

    assert "extracted_text" not in json.dumps(tp21, ensure_ascii=False)
    assert "source_table" not in json.dumps(tp21, ensure_ascii=False)


def test_a2_blastfrag_mechanism_comparison_hashes_cli_writes_retained_manifest(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "mechanism_comparison_hashes_cli.json"
    retained_dir = tmp_path / "retained"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_mechanism_comparison_hashes.py",
            "--write-retained-artifacts",
            "--retained-dir",
            str(retained_dir),
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
    assert artifact["schema_version"] == "a2.mechanism_comparison_hashes.v1"
    assert artifact["retained_artifact_sha256"]
    assert artifact["retained_manifest_sha256"]
    assert (retained_dir / "mechanism_comparison_hashes.json").exists()
    assert (retained_dir / "manifest.json").exists()

    manifest = json.loads((retained_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == (
        "a2.mechanism_comparison_hashes_retained_manifest.v1"
    )
    assert manifest["status"] == "partial_fail_closed_mechanism_comparison_hash_manifest"
    assert HEX64.fullmatch(manifest["mechanism_comparison_hashes_artifact"]["sha256"])
    assert HEX64.fullmatch(manifest["beco_selected_comparison_output_set_sha256"])
    assert HEX64.fullmatch(manifest["tp21_criteria_vocabulary_sha256"])
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["non_authoritative_guards"].values())
