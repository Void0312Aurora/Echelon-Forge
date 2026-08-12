from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.diagnostics import cuda_resident_cr2_matrix_evidence as collector
from tools.diagnostics import cuda_resident_cr2_matrix_evidence_schema as schema
from tools.diagnostics import cuda_resident_cr2_matrix_probe as matrix_probe


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = ROOT / "docs/plan/exact_runtime/cuda_resident_cr2_matrix_evidence_20260804"
MANIFEST = EVIDENCE_DIR / "manifest.json"
EVIDENCE = ROOT / "docs/plan/exact_runtime/cuda_resident_cr2_matrix_evidence_20260804.json"
PARITY = EVIDENCE_DIR / "parity-comparison.json"
COLLECTOR = ROOT / "tools/diagnostics/cuda_resident_cr2_matrix_evidence.py"
SCHEMA = ROOT / "tools/diagnostics/cuda_resident_cr2_matrix_evidence_schema.py"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _committed_source_descriptor(commit: str, relative: str) -> dict[str, object]:
    """Canonical descriptor of a source file as of the evidence's own commit.

    Frozen packages pin the tool sources that produced them; the live tree
    moves on (the collector went generation-aware, the probe gained the CP-6
    learner mode), so the immutability check must read the blob at the
    package's source_commit, mirroring the counter chain's precedent.
    """
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    payload = completed.stdout.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {
        "path": relative,
        "canonicalization": "utf8_lf",
        "canonical_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _tracked_reports() -> tuple[dict[str, object], dict[tuple[str, str], dict[str, object]]]:
    manifest = _load(MANIFEST)
    reports: dict[tuple[str, str], dict[str, object]] = {}
    for campaign in manifest["campaigns"]:
        for lane, descriptor in campaign["reports"].items():
            path = ROOT / descriptor["path"]
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
        "path": MANIFEST.relative_to(ROOT).as_posix(),
        "bytes": MANIFEST.stat().st_size,
        "sha256": _sha256(MANIFEST),
    }
    # The package's tool descriptors were captured when the evidence landed
    # (the collector did not exist yet at the campaigns' source_commit), so
    # immutability is checked against the landing commit's blobs.
    landing = "356bcd56a61e40f1327d16b6a2dda335d7fdd553"
    assert evidence["inputs"]["collector_source"] == _committed_source_descriptor(
        landing, COLLECTOR.relative_to(ROOT).as_posix()
    )
    assert evidence["inputs"]["schema_source"] == _committed_source_descriptor(
        landing, SCHEMA.relative_to(ROOT).as_posix()
    )
    for descriptor in manifest["source_inputs"].values():
        assert descriptor == _committed_source_descriptor(landing, descriptor["path"])
    for descriptor in manifest["prior_evidence_inputs"].values():
        assert descriptor == _committed_source_descriptor(landing, descriptor["path"])
        assert descriptor["canonicalization"] == "utf8_lf"
    for campaign in manifest["campaigns"]:
        for descriptor in campaign["reports"].values():
            path = ROOT / descriptor["path"]
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
        name: ROOT / descriptor["path"]
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


def test_unknown_generations_fail_closed() -> None:
    evidence = deepcopy(_load(EVIDENCE))
    evidence["schema_version"] = "cuda_resident.cr2.production_matrix_evidence.v99"
    with pytest.raises(schema.MatrixEvidenceError, match="unknown matrix evidence generation"):
        schema.validate_evidence(evidence)
    with pytest.raises(schema.MatrixEvidenceError, match="unknown matrix manifest generation"):
        schema.generation_for_manifest("cuda_resident.cr2.production_matrix_campaign_manifest.v99")


def test_generation_registry_keeps_v1_frozen_and_registers_cp8_once() -> None:
    """The CP-8 kickoff's pin inventory: v2 re-owns every identity instead of
    inheriting CR2-6b content. The v1 entry must stay the frozen package's
    exact era; the v2 entry drops the selection-policy result block (routing
    authority lives with CP-7a), references the CR2-6b package as a prior
    input, and carries capture-time counter truth (G-D closed with achieved
    counters that predate the CP-5 fusion)."""
    v1 = schema.GENERATIONS[schema.EVIDENCE_SCHEMA]
    assert v1["iteration"] == "CR2-6b"
    assert v1["evidence_date"] == "2026-08-04"
    assert v1["has_selection_policy"] is True
    assert v1["prior_evidence_inputs"] == ("counter_evidence", "resource_evidence")
    assert v1["counter_status"]["achieved_counter_gate_complete"] is False
    assert v1["counter_status"]["counter_blocker_code"] == "ERR_NVGPUCTRPERM"
    assert v1["gates"]["cr2_6_matrix_evidence_complete"] is True

    v2 = schema.GENERATIONS[schema.EVIDENCE_SCHEMA_V2]
    assert schema.EVIDENCE_SCHEMA_V2 == "cuda_resident.cp8.production_matrix_evidence.v2"
    assert v2["manifest_schema"] == "cuda_resident.cp8.production_matrix_campaign_manifest.v2"
    assert v2["iteration"] == "CP-8"
    assert v2["evidence_date"] == "2026-08-12"
    assert v2["has_selection_policy"] is False
    assert "matrix_evidence_cr2_6b" in v2["prior_evidence_inputs"]
    assert v2["counter_status"]["achieved_counter_gate_complete"] is True
    assert v2["counter_status"]["achieved_counters_predate_cp5_fusion"] is True
    assert "counter_blocker_code" not in v2["counter_status"]
    assert v2["gates"]["cp8_matrix_evidence_complete"] is True
    assert v2["interpretation_scope"] == "host_specific_post_optimization_comparison_only"
    for spec in schema.GENERATIONS.values():
        for gate in (
            "maintained_claim_allowed",
            "promotion_allowed",
            "public_support_enabled",
            "tuning_authorized",
        ):
            assert spec["gates"][gate] is False
        assert spec["counter_status"]["tuning_authorized"] is False

    assert schema.generation_for_manifest(v2["manifest_schema"]) is v2
    assert schema.generation_for_evidence(schema.EVIDENCE_SCHEMA) is v1


def test_v2_evidence_shape_rejects_a_selection_policy_block() -> None:
    """Relabeling the frozen v1 package as v2 must fail on the first v2-owned
    pin (the selection-policy block v2 deliberately does not carry)."""
    evidence = deepcopy(_load(EVIDENCE))
    evidence["schema_version"] = schema.EVIDENCE_SCHEMA_V2
    with pytest.raises(schema.MatrixEvidenceError, match="top-level schema drifted"):
        schema.validate_evidence(evidence)


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
