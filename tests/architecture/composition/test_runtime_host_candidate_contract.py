from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HEADER = REPO_ROOT / "src" / "runtime" / "host" / "runtime_host_candidate.h"
SOURCE = REPO_ROOT / "src" / "runtime" / "host" / "runtime_host_candidate.cpp"
TRANSFER_HEADER = REPO_ROOT / "src" / "runtime" / "host" / "runtime_state_transfer_candidate.h"
TRANSFER_SOURCE = REPO_ROOT / "src" / "runtime" / "host" / "runtime_state_transfer_candidate.cpp"
CMAKE = REPO_ROOT / "CMakeLists.txt"
BOUNDARY = REPO_ROOT / "cmake" / "verify_runtime_host_candidate_boundary.cmake"


def test_p4a_host_candidate_is_a_separate_native_link_unit() -> None:
    cmake = CMAKE.read_text(encoding="utf-8")
    assert "add_library(ef_runtime_host_candidate STATIC" in cmake
    assert "src/runtime/host/runtime_host_candidate.h" in cmake
    assert "src/runtime/host/runtime_host_candidate.cpp" in cmake
    assert "src/runtime/host/runtime_state_transfer_candidate.h" in cmake
    assert "src/runtime/host/runtime_state_transfer_candidate.cpp" in cmake
    assert "target_link_libraries(ef_runtime_host_candidate PUBLIC ef_runtime_contracts)" in cmake
    assert "install(TARGETS ef_runtime_host_candidate" not in cmake


def test_p4a_host_candidate_has_no_production_or_engine_dependency() -> None:
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    transfer_header = TRANSFER_HEADER.read_text(encoding="utf-8")
    transfer_source = TRANSFER_SOURCE.read_text(encoding="utf-8")
    boundary = BOUNDARY.read_text(encoding="utf-8")

    assert "production_authorized" in header
    assert "RuntimeFacade" not in header
    assert "SimulationKernel" not in header
    assert "WorldBatchRuntime" not in header
    assert "ef_core" in boundary
    assert "ef_facade" in boundary
    assert "Cordis" in boundary
    assert "production mode" in header
    assert "RuntimeShadowEpisodeCapability" in header
    assert "const RuntimeEpisodeRef &episode,\n                                                      RuntimeLeaseKind" not in header
    assert "lifecycle_deadline_tick" in header
    assert "resource_identity()" in header
    assert "orphaned_host_count" in header
    assert "native_barrier_observed" not in header
    assert "RuntimeShadowEpisodeAdmissionProof" not in header
    assert "RuntimeNativeEpisodeCapability" in header
    assert "RuntimeOwnerHandle" in header
    assert "issue_owner_handle" in header
    assert "RuntimeOwnerAdmissionBinding" in header
    assert "owner handle admission binding does not match request" in source
    assert "owner handle is stale, forged, or already consumed" in source
    assert "RuntimeValidatedStateTransfer validated_transfer" in header
    for forbidden in ("RuntimeFacade", "SimulationKernel", "WorldBatchRuntime"):
        assert forbidden not in transfer_header
        assert forbidden not in transfer_source


def test_p4a_publication_has_one_cas_and_no_reopen_after_successful_publish() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    tests = (REPO_ROOT / "src" / "tests" / "test_runtime_host_candidate.cpp").read_text(
        encoding="utf-8"
    )
    assert source.count("state.active.compare_exchange_strong") == 1
    assert "state_->active.compare_exchange" not in source
    cas_body = source.split("RuntimeHostStatus compare_exchange_active", 1)[1].split(
        "RuntimeHostStatus settle_candidate_at_deadline", 1
    )[0]
    assert "force_loss(" not in cas_body
    assert "invoke_cas_fault_injector" in source
    assert "RuntimeSlotCasOperation::InitialPublish" in source
    assert "RuntimeSlotCasOperation::ReplacementPublish" in source
    assert "RuntimeSlotCasOperation::RecoveryPublish" in source
    assert "RuntimeSlotCasOperation::ShutdownUnpublish" in source
    assert "RuntimeSlotCasOperation::QuiesceTimeoutUnpublish" in source
    assert "RuntimeSlotCasOperation::FaultTimeoutUnpublish" in source
    assert "PublicationRaceLost" in source
    assert "commit_prepared_candidate" in source
    assert "candidate->state = RuntimeSlotState::Active" in source
    assert "old->state = RuntimeSlotState::Draining" in source
    assert "timeout CAS losses preserve state" in tests
    assert "lease settlement and terminal-result admission" in tests
    assert "candidate deadline quarantines cancellation-unacknowledged resources" in tests
    assert "host-issued owner handles bind admission and are single-use" in tests
    assert "failed host-issued admission releases the token for retry" in tests
    assert "token->consumed.exchange(true" in source
    assert "owner handle resource identity drifted" in source
