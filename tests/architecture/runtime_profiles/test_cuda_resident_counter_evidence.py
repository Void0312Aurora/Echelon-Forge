from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.diagnostics.cuda_resident_retained_evidence_paths import logical_relative
from tools.diagnostics import cuda_resident_cr2_counter_evidence as counter
from tools.diagnostics import cuda_resident_cr2_resource_evidence as resource

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_counter_evidence_contract.h"
COLLECTOR = ROOT / "tools/diagnostics/cuda_resident_cr2_counter_evidence.py"
RESOURCE_EVIDENCE = (
    ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cr2_resource_evidence_20260804.json"
)
EVIDENCE = ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cr2_counter_evidence_20260804.json"
CP_EVIDENCE = (
    ROOT
    / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cp_counter_evidence_20260810.json"
)
CP_RESOURCE_EVIDENCE = (
    ROOT
    / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cp_resource_evidence_20260810.json"
)
BASELINE = "6d7ec7ddbf4163436de6a2db3d2e13829227d1f8"
EVIDENCE_COMMIT = "05b05c5a1f7968c603a4a933531bb52bdc30b9c4"
RESOURCE_EVIDENCE_COMMIT = "6d7ec7ddbf4163436de6a2db3d2e13829227d1f8"


def _git_blob(commit: str, path: Path) -> bytes:
    relative = logical_relative(path.relative_to(ROOT).as_posix())
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
            "collected_launch_count": counter.required_launch_count(1),
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
    # Launch counts are derived from the resource contract's launch sequences,
    # one per generation, and pinned against the retained artifacts.
    assert "kRequiredLaunchCountV1 = resource_evidence::kLaunchSequence.size()" in contract
    assert "kRequiredLaunchCountV2 = resource_evidence::kLaunchSequenceV2.size()" in contract
    assert "kRequiredLaunchCountV3 = resource_evidence::kLaunchSequenceV3.size()" in contract
    assert "static_assert(kRequiredLaunchCountV1 == 12);" in contract
    assert "static_assert(kRequiredLaunchCountV2 == 12);" in contract
    assert "static_assert(kRequiredLaunchCountV3 == 7);" in contract
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


def test_cp_achieved_counter_evidence_validates_against_its_declared_generation() -> None:
    """The tracked v2 achieved capture must keep passing the generation-aware
    validator byte-for-byte: it is the regression guard for deriving launch
    counts from the parent generation instead of a module constant."""
    evidence = json.loads(CP_EVIDENCE.read_text(encoding="utf-8"))
    counter.validate_report(evidence)
    assert evidence["profile_id"] == resource.PROFILE_V2
    assert evidence["attempt"]["status"] == "available"
    assert evidence["attempt"]["collected_launch_count"] == counter.required_launch_count(2) == 12


def _v3_report() -> dict[str, object]:
    """The shape a fused-graph recapture will produce: v3 parent profile,
    seven launches, the same measured units and counter schema as v2, and the
    in-artifact elevation record that post-frozen generations must carry."""
    report = json.loads(CP_EVIDENCE.read_text(encoding="utf-8"))
    report["profile_id"] = resource.PROFILE_V3
    toolchain = report["toolchain"]
    toolchain["launch_count_limit"] = 7
    toolchain["command_template"] = [
        str(entry).replace("--launch-count=12", "--launch-count=7")
        for entry in toolchain["command_template"]
    ]
    report["attempt"]["required_launch_count"] = 7
    report["attempt"]["collected_launch_count"] = 7
    report["attempt"]["elevation"] = {
        "elevated": True,
        "mechanism": "windows_administrator_shell",
        "recorded_utc": "2026-08-13T00:00:00Z",
    }
    for family in report["achieved_counters"].values():
        family["values_by_launch"] = family["values_by_launch"][:7]
    return report


def test_v3_counter_report_shape_follows_the_fused_launch_sequence() -> None:
    assert counter.required_launch_count(3) == 7
    counter.validate_report(_v3_report())


def _historical_v1_parent_bytes() -> bytes:
    """The v1 counter artifact predates the ``-text`` attribute and hashed the
    CRLF checkout of its parent; reproduce those bytes from the recorded
    commit, exactly as the frozen evidence saw them."""
    return _git_blob(RESOURCE_EVIDENCE_COMMIT, RESOURCE_EVIDENCE).replace(b"\n", b"\r\n")


def test_report_pair_binds_generation_and_parent_bytes() -> None:
    """The pair validator is the non-optional binding: both tracked pairs must
    pass it, a relabeled generation over the same parent must die on the
    profile check, and a swapped parent must die on the bytes hash."""
    counter.validate_report_pair(_evidence(), _historical_v1_parent_bytes())
    cp_parent_bytes = CP_RESOURCE_EVIDENCE.read_bytes()
    counter.validate_report_pair(
        json.loads(CP_EVIDENCE.read_text(encoding="utf-8")), cp_parent_bytes
    )
    with pytest.raises(counter.CounterEvidenceError, match="generation differs"):
        counter.validate_report_pair(_v3_report(), cp_parent_bytes)
    with pytest.raises(counter.CounterEvidenceError, match="bytes differ"):
        counter.validate_report_pair(
            json.loads(CP_EVIDENCE.read_text(encoding="utf-8")),
            _historical_v1_parent_bytes(),
        )


def test_parent_link_still_accepts_the_optional_report_binding() -> None:
    parent = json.loads(RESOURCE_EVIDENCE.read_text(encoding="utf-8"))
    binary_sha256 = parent["inputs"]["binary_sha256"]
    probe_sha256 = parent["inputs"]["probe_sha256"]
    matching = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    counter.validate_parent_link(parent, binary_sha256, probe_sha256, counter_report=matching)
    with pytest.raises(counter.CounterEvidenceError, match="generation differs"):
        counter.validate_parent_link(
            parent, binary_sha256, probe_sha256, counter_report=_v3_report()
        )


def test_empty_counter_families_declare_generation_units() -> None:
    """Pin the generator against independent expectations so a regression to
    v1 units in blocked v2/v3 evidence cannot hide behind its own map."""
    v1_units = {family: row["unit"] for family, row in counter.empty_counter_families(1).items()}
    assert v1_units == {
        "achieved_occupancy": "ratio",
        "branch_divergence": "ratio",
        "global_memory_traffic": "bytes",
        "local_memory_traffic": "bytes",
        "shared_memory_traffic": "bytes",
    }
    for generation in (2, 3):
        rows = counter.empty_counter_families(generation)
        assert {family: row["unit"] for family, row in rows.items()} == {
            "achieved_occupancy": "ratio",
            "branch_divergence": "ratio",
            "global_memory_traffic": "sector",
            "local_memory_traffic": "sector",
            "shared_memory_traffic": "wavefront",
        }
        assert all(
            row["provenance"] is None
            and row["metric_names"] is None
            and row["values_by_launch"] is None
            for row in rows.values()
        )


def _unavailable_report_for(generation: int, profile_id: str, status: str) -> dict[str, object]:
    """The shape a blocked or failed v2/v3 attempt must leave behind: the
    generation's measured units with null values, its launch budget, and
    attempt fields matching the declared status."""
    report = deepcopy(_evidence())
    launch_count = counter.required_launch_count(generation)
    report["profile_id"] = profile_id
    toolchain = report["toolchain"]
    toolchain["launch_count_limit"] = launch_count
    toolchain["command_template"] = [
        str(entry).replace("--launch-count=12", f"--launch-count={launch_count}")
        for entry in toolchain["command_template"]
    ]
    report["attempt"]["required_launch_count"] = launch_count
    if generation >= 3:
        # Post-frozen artifacts carry the elevation slot even when blocked;
        # only an available capture must fill it with an elevated record.
        report["attempt"]["elevation"] = None
    report["achieved_counters"] = counter.empty_counter_families(generation)
    if status == "collection_failed":
        report["attempt"].update(
            {
                "status": "collection_failed",
                "blocker_code": None,
                "blocker_kind": None,
                "recognized_error_line_sha256": None,
            }
        )
        report["gates"].update(
            {
                "cr2_5b_counter_attempt_complete": False,
                "cr2_5_disposition": "collection_failed",
            }
        )
    return report


@pytest.mark.parametrize("status", ("external_blocked", "collection_failed"))
@pytest.mark.parametrize(
    ("generation", "profile_attr"), ((2, "PROFILE_V2"), (3, "PROFILE_V3")), ids=("v2", "v3")
)
def test_unavailable_attempts_stay_self_validating_for_later_generations(
    generation: int, profile_attr: str, status: str
) -> None:
    counter.validate_report(
        _unavailable_report_for(generation, getattr(resource, profile_attr), status)
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"profile_id": "cp.resource.steady_full_window_body.sm86.v4"}),
        lambda value: value["toolchain"].update({"launch_count_limit": 12}),
        lambda value: value["attempt"].update({"required_launch_count": 12}),
        lambda value: value["achieved_counters"]["achieved_occupancy"].update(
            {"values_by_launch": [0.5] * 12}
        ),
    ],
    ids=("unknown-generation", "pre-fusion-limit", "pre-fusion-required", "pre-fusion-values"),
)
def test_v3_counter_reports_reject_pre_fusion_shape_or_unknown_generations(mutation) -> None:
    report = _v3_report()
    mutation(report)
    with pytest.raises(counter.CounterEvidenceError):
        counter.validate_report(report)


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


def test_post_frozen_counter_captures_must_record_elevation_in_the_artifact() -> None:
    """The program constraint requires counter artifacts to record elevation.
    The frozen v1/v2 captures carry that fact in the program plan prose only,
    which the CP-9 decision record waives by owner authority; every later
    generation (the v3+ parents of the optimized graphs) must embed the
    record, so an available capture without one fails closed."""
    missing_key = _v3_report()
    del missing_key["attempt"]["elevation"]
    with pytest.raises(counter.CounterEvidenceError, match="counter attempt"):
        counter.validate_report(missing_key)

    null_record = _v3_report()
    null_record["attempt"]["elevation"] = None
    with pytest.raises(counter.CounterEvidenceError, match="elevation record"):
        counter.validate_report(null_record)

    unelevated = _v3_report()
    unelevated["attempt"]["elevation"] = {
        "elevated": False,
        "mechanism": "none",
        "recorded_utc": "2026-08-13T00:00:00Z",
    }
    with pytest.raises(counter.CounterEvidenceError, match="elevation flag"):
        counter.validate_report(unelevated)

    # The properly recorded shape passes end to end via _v3_report, which
    # test_v3_counter_report_shape_follows_the_fused_launch_sequence pins.
    # The frozen generations stay exactly as captured: no elevation key, and
    # the CP-9 waiver keeps them valid.
    frozen = _available_report()
    assert "elevation" not in frozen["attempt"]
    counter.validate_report(frozen)


def test_cr2_5b_new_modules_remain_below_soft_size_targets() -> None:
    assert len(CONTRACT.read_text(encoding="utf-8").splitlines()) <= 600
    assert len(COLLECTOR.read_text(encoding="utf-8").splitlines()) <= 700
    this_file = Path(__file__)
    assert len(this_file.read_text(encoding="utf-8").splitlines()) <= 700
