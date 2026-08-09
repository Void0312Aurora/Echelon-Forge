from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.diagnostics import cuda_resident_retained_evidence_paths as retained_paths
from tools.diagnostics import cuda_resident_cr2_matrix_evidence as collector
from tools.diagnostics import cuda_resident_cr2_matrix_evidence_schema as schema
from tools.diagnostics import cuda_resident_cr2_matrix_probe as matrix_probe


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cr2_matrix_evidence_20260804"
MANIFEST = EVIDENCE_DIR / "manifest.json"
EVIDENCE = ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cr2_matrix_evidence_20260804.json"
PARITY = EVIDENCE_DIR / "parity-comparison.json"
COLLECTOR = ROOT / "tools/diagnostics/cuda_resident_cr2_matrix_evidence.py"
SCHEMA = ROOT / "tools/diagnostics/cuda_resident_cr2_matrix_evidence_schema.py"
BASELINE_SOURCE_COMMIT = "356bcd56a61e40f1327d16b6a2dda335d7fdd553"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_source_descriptor(path: Path, commit: str | None = None) -> dict[str, object]:
    encoded = retained_paths.canonical_source_bytes(path, ROOT, commit)
    return {
        "path": retained_paths.logical_relative(path.relative_to(ROOT).as_posix()),
        "canonicalization": "utf8_lf",
        "canonical_bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _tracked_reports() -> tuple[dict[str, object], dict[tuple[str, str], dict[str, object]]]:
    manifest = _load(MANIFEST)
    reports: dict[tuple[str, str], dict[str, object]] = {}
    for campaign in manifest["campaigns"]:
        for lane, descriptor in campaign["reports"].items():
            path = ROOT / retained_paths.physical_relative(str(descriptor["path"]))
            report = matrix_probe.load_report(path)
            matrix_probe.validate_report(report, require_production=True)
            reports[(campaign["campaign_id"], lane)] = report
    return manifest, reports


def test_tracked_manifest_reports_and_evidence_hashes_are_exact() -> None:
    manifest, _ = _tracked_reports()
    evidence = _load(EVIDENCE)
    schema.validate_evidence(evidence)
    assert evidence["source_commit"] == "0c24a07549e238222741da6b20100537e7a9be22"
    assert evidence["inputs"]["manifest"] == {
        "path": retained_paths.logical_relative(MANIFEST.relative_to(ROOT).as_posix()),
        "bytes": MANIFEST.stat().st_size,
        "sha256": _sha256(MANIFEST),
    }
    assert evidence["inputs"]["collector_source"] == _canonical_source_descriptor(COLLECTOR, BASELINE_SOURCE_COMMIT)
    assert evidence["inputs"]["schema_source"] == _canonical_source_descriptor(SCHEMA, BASELINE_SOURCE_COMMIT)
    for descriptor in manifest["source_inputs"].values():
        path = ROOT / retained_paths.physical_relative(str(descriptor["path"]))
        assert descriptor == _canonical_source_descriptor(path)
    for descriptor in manifest["prior_evidence_inputs"].values():
        path = ROOT / retained_paths.physical_relative(str(descriptor["path"]))
        assert descriptor == _canonical_source_descriptor(path)
        assert descriptor["canonicalization"] == "utf8_lf"
    for campaign in manifest["campaigns"]:
        for descriptor in campaign["reports"].values():
            path = ROOT / retained_paths.physical_relative(str(descriptor["path"]))
            assert path.stat().st_size == descriptor["bytes"] < 1_048_576
            assert _sha256(path) == descriptor["sha256"]
    assert PARITY.stat().st_size == evidence["parity_confirmation"]["bytes"]
    assert _sha256(PARITY) == evidence["parity_confirmation"]["sha256"]


def test_production_reports_rederive_exact_comparisons_and_policy() -> None:
    _, reports = _tracked_reports()
    collector._validate_campaign_invariants(reports)
    comparisons = collector._comparison_rows(reports)
    policy = collector._selection_policy(comparisons)
    evidence = _load(EVIDENCE)
    assert comparisons == evidence["comparisons"]
    assert policy == evidence["selection_policy"] == schema.selection_policy_contract()
    indexed = {(row["world_count"], row["mode_id"]): row for row in comparisons}
    assert indexed[(1, "no_export_no_device")]["all_metric_direction"] == "flecs_cpu_reference"
    assert indexed[(4, "no_export_no_device")]["all_metric_direction"] == "cuda_resident"
    assert indexed[(4, "host_export_no_device")]["all_metric_direction"] == "mixed"
    for world in (16, 64, 256):
        for mode in schema.COMMON_MODES:
            assert indexed[(world, mode)]["all_metric_direction"] == "cuda_resident"


def test_fresh_parity_and_counter_blocker_inputs_remain_fail_closed() -> None:
    parity = _load(PARITY)
    assert parity["schema_version"] == "cuda_resident.selected_slice_parity.comparison.v1"
    assert parity["status"] == "pass"
    assert parity["coverage"]["released_numeric_field_count"] == 12
    assert parity["coverage"]["partition_complete"] is True
    for family in (
        parity["cross_lane_fields"],
        parity["same_backend_reset_fields"]["cpu_reference"],
        parity["same_backend_reset_fields"]["cuda_resident"],
    ):
        assert len(family) == 12
        assert all(row["matched_count"] == row["comparison_count"] > 0 for row in family)
    manifest = _load(MANIFEST)
    paths = {
        name: ROOT / retained_paths.physical_relative(str(descriptor["path"]))
        for name, descriptor in manifest["prior_evidence_inputs"].items()
    }
    status = collector._validate_prior_evidence(paths)
    assert status == _load(EVIDENCE)["counter_status"]
    assert status["achieved_counter_gate_complete"] is False
    assert status["tuning_authorized"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["gates"].update({"promotion_allowed": 0}),
        lambda value: value["gates"].update({"cr2_6_matrix_evidence_complete": False}),
        lambda value: value["selection_policy"].update(
            {"maintained_default_backend": "cuda_resident"}
        ),
        lambda value: value["selection_policy"].update(
            {"applies_only_to_measured_world_counts": 1}
        ),
        lambda value: value["selection_policy"]["rules"][-1].update(
            {"comparative_performance_claimed": True}
        ),
        lambda value: value["parity_confirmation"].update({"status": "fail"}),
        lambda value: value["counter_status"].update({"achieved_counter_gate_complete": 0}),
        lambda value: value["limitations"].update({"promotion_claimed": 0}),
        lambda value: value["campaigns"][0].update(
            {"execution_order": ["cuda_resident", "flecs_cpu_reference"]}
        ),
        lambda value: value["capture_design"].update({"source_worktree_clean_at_capture": 1}),
        lambda value: value["comparisons"][0].update({"world_count": True}),
        lambda value: value["comparisons"][0]["metrics"]["warmed_end_to_end_p50"]["campaigns"][
            0
        ].update({"cpu_over_cuda": 1.0}),
    ],
)
def test_evidence_validator_rejects_policy_gate_or_ratio_drift(mutation) -> None:
    evidence = deepcopy(_load(EVIDENCE))
    mutation(evidence)
    with pytest.raises(schema.MatrixEvidenceError):
        schema.validate_evidence(evidence)


def test_policy_derivation_rejects_direction_or_ambiguity_drift() -> None:
    evidence = _load(EVIDENCE)
    comparisons = deepcopy(evidence["comparisons"])
    comparisons[0]["all_metric_direction"] = "cuda_resident"
    with pytest.raises(schema.MatrixEvidenceError, match="world 1"):
        collector._selection_policy(comparisons)
    comparisons = deepcopy(evidence["comparisons"])
    world4_export = next(
        row
        for row in comparisons
        if row["world_count"] == 4 and row["mode_id"] == "host_export_no_device"
    )
    world4_export["all_metric_direction"] = "cuda_resident"
    with pytest.raises(schema.MatrixEvidenceError, match="ambiguity"):
        collector._selection_policy(comparisons)


def test_manifest_loader_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
    with pytest.raises(schema.MatrixEvidenceError, match="duplicate JSON key"):
        collector._load(path)


def test_cr2_6b_is_evidence_only_and_modules_remain_below_soft_limits() -> None:
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            "0c24a075",
            "356bcd56",
            "--",
            "src/runtime/contracts",
            "src/runtime/facade/internal/cuda_resident",
            "src/tools/experimental/cuda_resident",
        ],
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 0
    assert len(COLLECTOR.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(SCHEMA.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(Path(__file__).read_text(encoding="utf-8").splitlines()) <= 700
    for path in EVIDENCE_DIR.iterdir():
        assert path.stat().st_size < 1_048_576
    assert EVIDENCE.stat().st_size < 1_048_576
