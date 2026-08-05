from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HARNESS = ROOT / "src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp"
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_replay_contract.h"
TEST = ROOT / "src/tests/test_cuda_resident_replay.cpp"
CMAKE = ROOT / "CMakeLists.txt"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_rb8_consumes_only_the_frozen_resident_budget() -> None:
    contract = _text(CONTRACT)
    harness = _text(HARNESS)
    assert 'kCudaResidentReplayProfileId =\n    "resident_state.unmaintained_candidate"' in contract
    assert "kCudaResidentReplayBudgetRef" in contract
    assert "resident_candidate_selected_slice_field_contract()" in harness
    assert "resident_candidate_barrier_contract()" in harness
    assert "selected_slice_fields" in harness
    assert "comparison_barriers" in harness
    assert "expected_selected_field_count" in harness
    assert "available_field_instances == report.coverage.expected_field_instances" in harness
    assert "unavailable_field_instances == 0" in harness
    assert "consumed_selected_field_count ==" in harness
    assert "kCudaResidentReplayShadowBudgetRef" in contract


def test_rb8_rejects_structural_drift_and_runner_failure() -> None:
    harness = _text(HARNESS)
    assert "count_frames" in harness
    assert "duplicate_frame" in harness
    assert "duplicate_field" in harness
    assert "source_snapshot_mismatch" in harness
    assert "reference_runner_failed" in harness
    assert "shadow_runner_failed" in harness
    assert "candidate_promotion_blocked" in harness
    assert "nondeterministic_rerun" in harness
    assert "prior.trace_signature != requested_trace_signature" in harness
    assert "report.trace_signature" in harness
    assert "reference_source_snapshot_versions" in harness
    assert "shadow_source_snapshot_versions" in harness


def test_rb8_trace_identity_covers_forbidden_control_fields() -> None:
    harness = _text(HARNESS)
    for field in (
        "radar_active",
        "radar_scan_az",
        "radar_scan_el",
        "tms_up",
        "master_arm",
        "fire_weapon",
        "fire_gun",
        "weapon_select_id",
        "jettison_emergency",
        "program_chaff",
        "program_flare",
    ):
        assert field in harness


def test_rb8_empty_events_are_typed_sentinels_and_cpu_lane_is_oracle_only() -> None:
    test = _text(TEST)
    assert '"events.timestamp"' in test
    assert '"events.priority"' in test
    assert '"events.event_id"' in test
    assert '"events.event_family_membership"' in test
    assert 'ParityBudgetValueKind::signed_integer' in test
    assert 'ParityBudgetValueKind::unsigned_integer' in test
    assert '"fixed_air_cpu_fixture_oracle"' in test
    cpu_section = test.split("ReplayLaneResult run_cpu_reference", 1)[1].split(
        "ReplayLaneResult run_cuda_resident", 1
    )[0]
    assert "CudaWorldStore" not in cpu_section
    assert "CudaResidentBackend" not in cpu_section


def test_rb8_has_a_separate_diagnostics_target_and_no_capability_promotion() -> None:
    cmake = _text(CMAKE)
    assert "ef_cuda_resident_replay_test" in cmake
    assert "cuda_resident_replay_harness.cpp" in cmake
    assert "test_cuda_resident_replay.cpp" in cmake
    assert "add_test(NAME cuda_resident_replay" in cmake
    assert "RuntimeFacade" in cmake
    # RB8 must not silently turn on the public support projection.
    config = _text(ROOT / "src/runtime/facade/runtime_facade_config.cpp")
    assert ".supports_shadow_compare = false" in config
