from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.diagnostics import cuda_resident_cr2_counter_evidence as counter
from tools.diagnostics import cuda_resident_cr2_resource_evidence as resource


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_counter_evidence_contract.h"
COLLECTOR = ROOT / "tools/diagnostics/cuda_resident_cr2_counter_evidence.py"
RESOURCE_EVIDENCE = (
    ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cr2_resource_evidence_20260804.json"
)
EVIDENCE = ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cr2_counter_evidence_20260804.json"
BASELINE = "6d7ec7ddbf4163436de6a2db3d2e13829227d1f8"
EVIDENCE_COMMIT = "05b05c5a1f7968c603a4a933531bb52bdc30b9c4"
RESOURCE_EVIDENCE_COMMIT = "6d7ec7ddbf4163436de6a2db3d2e13829227d1f8"


def _git_blob(commit: str, path: Path) -> bytes:
    relative = path.relative_to(ROOT).as_posix().replace("tests/fixtures/runtime_profiles/cuda_resident_program_2/", "docs/plan/exact_runtime/", 1)
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _git_source_sha256(commit: str, path: Path) -> str:
    content = _git_blob(commit, path).replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def _numeric_paths(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _numeric_paths(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _numeric_paths(child, (*path, index))
    elif type(value) in {bool, int, float}:
        yield path, value


def _set_path(value, path, replacement) -> None:
    target = value
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = replacement


def _type_mutations(value):
    if type(value) is bool:
        yield int(value)
        yield float(value)
    elif type(value) is int:
        yield float(value)
        if value in {0, 1}:
            yield bool(value)
    elif type(value) is float and value.is_integer():
        yield int(value)
        if value in {0.0, 1.0}:
            yield bool(value)


def _fixed_counter_type_mutations(value):
    if type(value) is bool:
        yield int(value)
        yield float(value)
    elif type(value) is int:
        yield float(value)
        if value in {0, 1}:
            yield bool(value)


def _evidence() -> dict[str, object]:
    value = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _available_report() -> dict[str, object]:
    report = deepcopy(_evidence())
    report["inputs"]["ncu_report_sha256"] = "0" * 64
    attempt = report["attempt"]
    attempt.update(
        {
            "status": "available",
            "exit_code": 0,
            "report_created": True,
            "blocker_code": None,
            "blocker_kind": None,
            "collected_launch_count": counter.REQUIRED_LAUNCH_COUNT,
            "log_error_codes": [],
            "recognized_error_line_sha256": None,
        }
    )
    for family, unit in counter.COUNTER_FAMILIES.items():
        report["achieved_counters"][family] = {
            "unit": unit,
            "provenance": "nsight_compute_hardware_counter",
            "metric_names": [f"ncu.metric.{family}"],
            "values_by_launch": [0.5 if unit == "ratio" else 1.0] * 12,
        }
    report["gates"].update(
        {
            "cr2_5b_counter_attempt_complete": True,
            "cr2_5_achieved_counter_gate_complete": True,
            "cr2_5_disposition": "achieved_counter_evidence_complete",
        }
    )
    return report


def test_cr2_5b_contract_freezes_fail_closed_counter_scope() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    assert counter.SCHEMA in contract
    assert counter.PROFILE in contract
    assert f'kPermissionBlockerCode = "{counter.PERMISSION_CODE}"' in contract
    assert "kRequiredLaunchCount = 12" in contract
    assert '"available"' in contract
    assert '"external_blocked"' in contract
    assert '"collection_failed"' in contract
    for family, unit in counter.COUNTER_FAMILIES.items():
        assert f'{{"{family}", "{unit}"}}' in contract
    assert "kTheoreticalOccupancyMaySubstituteAchieved = false" in contract
    assert "kMissingCounterMayDefaultToZero = false" in contract
    assert "kMaintainedClaimAllowed = false" in contract
    assert "kPublicSupportEnabled = false" in contract
    assert "kPromotionAllowed = false" in contract
    assert "kTuningAuthorized = false" in contract


def test_cr2_5b_evidence_records_real_permission_block_without_counter_claims() -> None:
    evidence = _evidence()
    counter.validate_report(evidence)
    parent = json.loads(RESOURCE_EVIDENCE.read_text(encoding="utf-8"))
    resource.validate_report(parent)

    assert evidence["source"] == {
        "baseline_commit": BASELINE,
        "candidate_state": "cr2_5b_unpromoted_worktree",
    }
    assert evidence["attempt"] == {
        "status": "external_blocked",
        "exit_code": 1,
        "connected_pid": evidence["attempt"]["connected_pid"],
        "disconnected_pid": evidence["attempt"]["connected_pid"],
        "application_completed": True,
        "report_created": False,
        "blocker_code": "ERR_NVGPUCTRPERM",
        "blocker_kind": "external_permission",
        "required_launch_count": 12,
        "collected_launch_count": 0,
        "log_error_codes": ["ERR_NVGPUCTRPERM"],
        "recognized_error_line_sha256": evidence["attempt"]["recognized_error_line_sha256"],
    }
    assert all(
        row["provenance"] is None
        and row["metric_names"] is None
        and row["values_by_launch"] is None
        for row in evidence["achieved_counters"].values()
    )
    assert evidence["gates"]["cr2_5b_counter_attempt_complete"] is True
    assert evidence["gates"]["cr2_5_achieved_counter_gate_complete"] is False
    assert evidence["gates"]["cr2_5_disposition"] == "documented_external_blocker"
    for flag in (
        "maintained_claim_allowed",
        "public_support_enabled",
        "promotion_allowed",
        "tuning_authorized",
    ):
        assert evidence["gates"][flag] is False

    inputs = evidence["inputs"]
    assert inputs["source_hash_canonicalization"] == "utf8_lf"
    captured_resource_bytes = _git_blob(RESOURCE_EVIDENCE_COMMIT, RESOURCE_EVIDENCE).replace(
        b"\n", b"\r\n"
    )
    assert inputs["resource_evidence_sha256"] == hashlib.sha256(captured_resource_bytes).hexdigest()
    assert inputs["binary_sha256"] == parent["inputs"]["binary_sha256"]
    assert inputs["probe_output_sha256"] == parent["inputs"]["probe_sha256"]
    assert inputs["collector_source_sha256"] == _git_source_sha256(EVIDENCE_COMMIT, COLLECTOR)
    assert inputs["contract_source_sha256"] == _git_source_sha256(EVIDENCE_COMMIT, CONTRACT)
    for key, value in inputs.items():
        if key.endswith("_sha256") and value is not None:
            assert isinstance(value, str) and len(value) == 64
    assert inputs["ncu_report_sha256"] is None
    assert evidence["toolchain"]["nsight_compute_version"].startswith("2025.3.1.0 ")
    assert evidence["toolchain"]["counter_set"] == "full"
    assert evidence["toolchain"]["launch_count_limit"] == 12
    assert evidence["capture"]["world_count"] == 256
    assert evidence["capture"]["window_count"] == 1
    assert evidence["capture"]["consumer_await_completed"] is True
    assert evidence["capture"]["diagnostic_materialization_called"] is False
    assert EVIDENCE.stat().st_size < 524_288


def test_permission_log_parser_requires_exact_error_and_process_lifecycle() -> None:
    valid = "\n".join(
        [
            "==PROF== Connected to process 42 (probe.exe)",
            "==ERROR== ERR_NVGPUCTRPERM - The user does not have permission to access "
            "NVIDIA GPU Performance Counters on the target device 0.",
            "==PROF== Disconnected from process 42",
        ]
    )
    parsed = counter.parse_attempt_log(valid)
    assert parsed["connected_pids"] == [42]
    assert parsed["disconnected_pids"] == [42]
    assert parsed["error_codes"] == ["ERR_NVGPUCTRPERM"]
    assert parsed["permission_denied"] is True
    assert len(parsed["permission_line_sha256"]) == 64

    wrong_code = valid.replace("ERR_NVGPUCTRPERM", "ERR_OTHER")
    assert counter.parse_attempt_log(wrong_code)["permission_denied"] is False
    missing_text = valid.replace("does not have permission", "failed")
    assert counter.parse_attempt_log(missing_text)["permission_denied"] is False
    second_error = valid + "\n==ERROR== ERR_OTHER - unrelated"
    assert counter.parse_attempt_log(second_error)["permission_denied"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["attempt"].update({"exit_code": 0}),
        lambda value: value["attempt"].update({"blocker_code": "ERR_OTHER"}),
        lambda value: value["attempt"].update({"report_created": True}),
        lambda value: value["attempt"].update({"collected_launch_count": 12}),
        lambda value: value["attempt"].update({"log_error_codes": []}),
        lambda value: value["gates"].update({"promotion_allowed": True}),
        lambda value: value["gates"].update({"cr2_5_achieved_counter_gate_complete": True}),
        lambda value: value["achieved_counters"]["achieved_occupancy"].update(
            {"values_by_launch": [0.0] * 12}
        ),
    ],
)
def test_external_blocker_validation_rejects_claim_or_provenance_drift(mutation) -> None:
    evidence = deepcopy(_evidence())
    mutation(evidence)
    with pytest.raises(counter.CounterEvidenceError):
        counter.validate_report(evidence)


def test_available_state_requires_every_launch_and_hardware_provenance() -> None:
    complete = _available_report()
    counter.validate_report(complete)

    missing_launch = deepcopy(complete)
    missing_launch["achieved_counters"]["local_memory_traffic"]["values_by_launch"].pop()
    with pytest.raises(counter.CounterEvidenceError, match="all launch values"):
        counter.validate_report(missing_launch)

    missing_metric = deepcopy(complete)
    missing_metric["achieved_counters"]["global_memory_traffic"]["metric_names"] = []
    with pytest.raises(counter.CounterEvidenceError, match="metric names"):
        counter.validate_report(missing_metric)

    theoretical = deepcopy(complete)
    theoretical["achieved_counters"]["achieved_occupancy"]["provenance"] = (
        "cr2_5a_theoretical_occupancy"
    )
    with pytest.raises(counter.CounterEvidenceError, match="non-hardware provenance"):
        counter.validate_report(theoretical)

    nonzero_exit = deepcopy(complete)
    nonzero_exit["attempt"]["exit_code"] = 1
    with pytest.raises(counter.CounterEvidenceError, match="exit code zero"):
        counter.validate_report(nonzero_exit)


def test_cr2_5b_parent_link_rejects_binary_or_probe_hash_drift() -> None:
    parent = json.loads(RESOURCE_EVIDENCE.read_text(encoding="utf-8"))
    binary_sha256 = parent["inputs"]["binary_sha256"]
    probe_sha256 = parent["inputs"]["probe_sha256"]
    counter.validate_parent_link(parent, binary_sha256, probe_sha256)
    with pytest.raises(counter.CounterEvidenceError, match="binary differs"):
        counter.validate_parent_link(parent, "0" * 64, probe_sha256)
    with pytest.raises(counter.CounterEvidenceError, match="probe output differs"):
        counter.validate_parent_link(parent, binary_sha256, "0" * 64)

    incomplete_parent = deepcopy(parent)
    incomplete_parent["launch_topology"]["launches"] = []
    with pytest.raises(resource.EvidenceError, match="launch inventory"):
        counter.validate_parent_link(incomplete_parent, binary_sha256, probe_sha256)


def test_resource_parent_link_rejects_equal_valued_non_integer_numeric_types() -> None:
    parent = json.loads(RESOURCE_EVIDENCE.read_text(encoding="utf-8"))
    binary_sha256 = parent["inputs"]["binary_sha256"]
    probe_sha256 = parent["inputs"]["probe_sha256"]
    mutation_count = 0
    for path, original in _numeric_paths(parent):
        for replacement in _type_mutations(original):
            mutated = deepcopy(parent)
            _set_path(mutated, path, replacement)
            with pytest.raises(resource.EvidenceError):
                resource.validate_report(mutated)
            with pytest.raises(resource.EvidenceError):
                counter.validate_parent_link(mutated, binary_sha256, probe_sha256)
            mutation_count += 1
    assert mutation_count >= 100


@pytest.mark.parametrize(
    ("factory", "expected_mutation_count"),
    ((_evidence, 47), (_available_report, 46)),
    ids=("blocked", "available"),
)
def test_cr2_5b_counter_reports_reject_equal_valued_non_json_types(
    factory, expected_mutation_count: int
) -> None:
    report = factory()
    mutation_count = 0
    for path, original in _numeric_paths(report):
        for replacement in _fixed_counter_type_mutations(original):
            mutated = deepcopy(report)
            _set_path(mutated, path, replacement)
            with pytest.raises(counter.CounterEvidenceError):
                counter.validate_report(mutated)
            mutation_count += 1
    assert mutation_count == expected_mutation_count


def test_cr2_5b_does_not_rewrite_cr2_5a_or_historical_rb9_evidence() -> None:
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            BASELINE,
            "05b05c5a",
            "--",
            "docs/plan/exact_runtime/cuda_resident_cr2_resource_evidence_20260804.json",
            "docs/plan/exact_runtime/cuda_resident_rb9_evidence_20260730",
        ],
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 0
    assert not list((ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2").glob("cuda_resident_cr2_counter_*.ncu-rep"))


def test_cr2_5b_new_modules_remain_below_soft_size_targets() -> None:
    assert len(CONTRACT.read_text(encoding="utf-8").splitlines()) <= 600
    assert len(COLLECTOR.read_text(encoding="utf-8").splitlines()) <= 700
    this_file = Path(__file__)
    assert len(this_file.read_text(encoding="utf-8").splitlines()) <= 700
