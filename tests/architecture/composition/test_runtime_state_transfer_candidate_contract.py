from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HEADER = REPO_ROOT / "src" / "runtime" / "host" / "runtime_state_transfer_candidate.h"
SOURCE = REPO_ROOT / "src" / "runtime" / "host" / "runtime_state_transfer_candidate.cpp"
HOST_HEADER = REPO_ROOT / "src" / "runtime" / "host" / "runtime_host_candidate.h"
HOST_SOURCE = REPO_ROOT / "src" / "runtime" / "host" / "runtime_host_candidate.cpp"
NATIVE_TEST = REPO_ROOT / "src" / "tests" / "test_runtime_state_transfer_candidate.cpp"
HOST_NATIVE_TEST = REPO_ROOT / "src" / "tests" / "test_runtime_host_candidate.cpp"
KERNEL_ADAPTER_HEADER = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "host"
    / "integration"
    / "simulation_kernel_state_owner_adapters.h"
)
KERNEL_ADAPTER_SOURCE = KERNEL_ADAPTER_HEADER.with_suffix(".cpp")
KERNEL_ADAPTER_TEST = (
    REPO_ROOT / "src" / "tests" / "test_simulation_kernel_state_owner_adapters.cpp"
)
CMAKE = REPO_ROOT / "CMakeLists.txt"
MIRROR = REPO_ROOT / "tests" / "runtime" / "shadow_runtime_episode_mirror.py"
MIRROR_TEST = REPO_ROOT / "tests" / "runtime" / "test_runtime_episode_mirror.py"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci-smoke.yml"


STATE_CATEGORIES = (
    "CompositionProviderSystemGraph",
    "EcsComponentTruth",
    "RngState",
    "ClockCadence",
    "DelayedEventsQueues",
    "CommandsLinksPendingIntent",
    "EpisodeRewardTermination",
    "PythonLoaderControllerCaches",
    "BackendDeviceAllocationsLeases",
    "InFlightRequestsResults",
    "ExternalSideEffects",
    "DiagnosticsTelemetry",
)


def _enum_members(header: str, enum_name: str) -> tuple[str, ...]:
    body = header.split(f"enum class {enum_name}", 1)[1].split("};", 1)[0]
    body = body.split("{", 1)[1]
    return tuple(
        line.split("=", 1)[0].strip().rstrip(",")
        for line in body.splitlines()
        if line.strip() and not line.lstrip().startswith("//")
    )


def test_p4b_census_is_exactly_the_frozen_twelve_category_contract() -> None:
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")

    assert "kRuntimeStateCategoryCount = 12" in header
    assert _enum_members(header, "RuntimeStateCategory") == STATE_CATEGORIES
    assert "profile.rows.size() != kRuntimeStateCategoryCount" in source
    assert "request.census.entries" in source
    assert "RuntimeStateTransferError::MissingCategory" in source
    assert "RuntimeStateTransferError::DuplicateCategory" in source
    for category in STATE_CATEGORIES:
        assert f"RuntimeStateCategory::{category}" in source
    assert source.count('return "echelon_forge.runtime_state.') == 12
    assert source.count('return "native.') == 11
    assert 'return "python.mirror-owner"' in source


def test_p4b_native_authority_and_transfer_proofs_are_capabilities_not_booleans() -> None:
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    host_header = HOST_HEADER.read_text(encoding="utf-8")
    host_source = HOST_SOURCE.read_text(encoding="utf-8")

    assert "class RuntimeEpisodeCoordinatorCandidate" in header
    assert "RuntimeNativeEpisodeCommand" in header
    assert "RuntimeEpisodeBarrierCapability(const RuntimeEpisodeBarrierCapability &) = delete" in header
    assert "RuntimeValidatedStateTransfer(const RuntimeValidatedStateTransfer &) = delete" in header
    assert "RuntimeStateTransferValidator" in header
    assert "release_unclaimed_barrier" in source
    assert "coordinator->phase = RuntimeEpisodePhase::TransferCommitted" in source
    assert "coordinator->phase = RuntimeEpisodePhase::Terminal" in source
    assert "native_barrier_observed" not in host_header
    assert "RuntimeShadowEpisodeAdmissionProof" not in host_header
    assert "RuntimeValidatedStateTransfer validated_transfer" in host_header
    assert "std::shared_ptr<RuntimeStateTransferOwnerRegistry> owner_registry" in host_source
    assert "active->owner_registry" in host_source
    assert "candidate->owner_registry" in host_source
    assert "source_owner_registry" in source
    assert "target_owner_registry" in source
    assert "RuntimeStateOwnerArtifact" in header
    assert "validate_source_artifacts" in source
    assert "owner source artifact payload digest is invalid" in source
    assert "native_episode_control()" in host_header
    assert "submit_shadow_episode(const RuntimeShadowEpisodeCapability &episode" in host_header
    assert "prepare_for_host" in host_source
    assert "commit_for_host" in host_source
    assert host_source.count("abandon_transfer_outside_host_mutex") >= 4


def test_p4b_state_transfer_fails_closed_on_schema_truth_and_live_work() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    native_test = NATIVE_TEST.read_text(encoding="utf-8")

    for invariant in (
        "UnknownTruthField",
        "RawHandleTransferForbidden",
        "UnsettledWork",
        "ReplacementRejected",
        "PayloadDigestMismatch",
        "SchemaMismatch",
        "PlanMismatch",
        "BarrierReplay",
    ):
        assert f"RuntimeStateTransferError::{invariant}" in source
    assert "kRuntimeStateTransferPreviousGeneration" in source
    assert "maximum_schema_generation > kRuntimeStateTransferContractGeneration" in source
    assert "runtime_state_owner_id(row.category)" in source
    assert "runtime_state_schema_id(row.category)" in source
    assert "state census rejects omission duplication unknown truth and payload tampering" in native_test
    assert "resource in-flight and side-effect rows fail closed" in native_test
    assert "host-bound source and target owner registries" in source
    assert "export_source" in source
    assert "same_source_census" in source
    assert "ImportTransactionAbortGuard" in source
    assert "import_abort.disarm()" in source
    assert "request.owner_registry" not in source


def test_p4b_import_transaction_has_bounded_statusful_commit_abort_and_recovery() -> None:
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    host_header = HOST_HEADER.read_text(encoding="utf-8")
    host_source = HOST_SOURCE.read_text(encoding="utf-8")
    native_test = NATIVE_TEST.read_text(encoding="utf-8")
    host_native_test = HOST_NATIVE_TEST.read_text(encoding="utf-8")

    for phase in (
        "Prepared",
        "Committing",
        "Committed",
        "Aborting",
        "Aborted",
        "Ambiguous",
    ):
        assert phase in header
    for method in (
        "commit_with_deadline",
        "abort_with_deadline",
        "recover_with_deadline",
        "status() const noexcept",
    ):
        assert method in header
    assert "journal_sequence" in header
    assert "durable" in header
    assert "ImportTransactionDeadlineExceeded" in header
    assert "ImportTransactionAmbiguous" in header
    assert "transaction->status()" in source
    assert "transaction->abort_with_deadline(0, 0)" in source
    assert "runtime_state_decoder_replay_matrix" in source
    assert "RuntimeStateDecoderReplayRule" in header
    assert "runtime_state_transfer_profile_from_decoder_matrix" in header
    assert "runtime_state_transfer_profile_from_decoder_matrix" in source
    assert source.count("migration_sha256 =") == 12
    assert "one generation window" in native_test
    assert "canonical profile factory binds all rows to the decoder matrix" in native_test
    assert "RuntimeValidatedTransferLifecycle::Ambiguous" in source
    assert "transaction_status.durable" in source
    assert "transaction_status.journal_sequence != 0" in source
    assert "owner import transaction did not commit" in source
    assert "commit_for_host(\n" in host_source or "commit_for_host(" in host_source
    assert "std::uint64_t now_tick" in host_header
    assert "commit_prepared_candidate(const RuntimeCandidateHandle &handle);" not in host_header
    assert "prepared replacement publication requires an unexpired clock sample" in host_native_test
    assert "owner import transactions expose bounded durable lifecycle status" in native_test


def test_p4b_fixed_owner_registry_and_local_wal_are_executable_candidates() -> None:
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    native_test = NATIVE_TEST.read_text(encoding="utf-8")

    assert "class RuntimeStateOwnerAdapterRegistry final" in header
    assert "RuntimeStateOwnerAdapterRegistration" in header
    assert "RuntimeStateTransferFileJournal final" in header
    assert "RuntimeDurableOwnerImportTransaction final" in header
    # The durable WAL API is exposed as append_and_sync; the locked record
    # helper is the implementation seam that provides append+flush semantics.
    assert "append_and_sync" in source
    assert "append_journal_record_with_lock" in source
    assert "truncate_journal_file" in source
    assert "valid_journal_transition" in source
    assert "CompositeOwnerImportTransaction" in source
    assert "fixed twelve-owner adapter registry executes current and N-1 generations" in native_test
    assert "file WAL persists terminal owner transaction across journal reopen" in native_test
    assert "file WAL reconciles interrupted commit and rejects complete corruption" in native_test


def test_p4b_simulation_kernel_adapter_is_dark_complete_and_strict() -> None:
    adapter_header = KERNEL_ADAPTER_HEADER.read_text(encoding="utf-8")
    adapter_source = KERNEL_ADAPTER_SOURCE.read_text(encoding="utf-8")
    adapter_test = KERNEL_ADAPTER_TEST.read_text(encoding="utf-8")
    cmake = CMAKE.read_text(encoding="utf-8")

    assert "SimulationKernelStateOwnerBridge" in adapter_header
    assert "create_registry" in adapter_header
    assert "RuntimeStateOwnerAdapterRegistry" in adapter_source
    assert "validate_component_payload" in adapter_source
    assert "descriptor.strict = true" in adapter_source
    assert 'schema == "missile-runtime.v3"' in adapter_source
    assert 'schema == "missile-runtime.v4"' in adapter_source
    assert "candidate.seeker_decoy_rejection = 1.0" in adapter_source
    assert "candidate.seeker_resolution_cell_m = 0.0" in adapter_source
    assert "decode_entity_references" in adapter_source
    assert "python-mirror-rederive.v2" in adapter_source
    assert "backend-resource-rederive.v2" in adapter_source
    assert "in-flight-drain.v2" in adapter_source
    assert "episode-barrier.v2" in adapter_source
    assert "clock owner payload does not match its native barrier" in adapter_source
    assert "episode owner payload does not match its native barrier" in adapter_source
    assert "real SimulationKernel owner registry exports and imports all twelve rows" in adapter_test
    assert "host replacement commits all twelve real SimulationKernel owner rows" in adapter_test
    assert "every registered component has transfer or explicit rederive policy" in adapter_test
    assert "real RNG owner imports N-1 through the durable adapter journal" in adapter_test
    assert "clock owner imports N-1 and rejects trailing or stale barrier metadata" in adapter_test
    assert "episode owner binds the exact host replacement barrier to its WAL" in adapter_test
    assert "composition and explicit policy owners import N-1 durably" in adapter_test
    assert "side-effect-outbox.v2" in adapter_source
    assert "telemetry-rederive.v2" in adapter_source
    assert "unknown_truth" in adapter_test
    assert "previous_missile" in adapter_test
    assert 'missile["schema"] = "missile-runtime.v3"' in adapter_test
    assert "CHECK_FALSE" in adapter_test
    assert "ef_runtime_state_owner_adapters_candidate" in cmake
    assert "install(TARGETS ef_runtime_state_owner_adapters_candidate" not in cmake


def test_p4b_python_is_a_strict_native_receipt_mirror_without_reset_authority() -> None:
    mirror_text = MIRROR.read_text(encoding="utf-8")
    tests = MIRROR_TEST.read_text(encoding="utf-8")
    tree = ast.parse(mirror_text)
    mirror_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "NativeEpisodeMirror"
    )
    public_methods = {
        node.name for node in mirror_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }

    assert public_methods == {"state", "apply_receipt", "acknowledge_receipt"}
    assert "receipt has unknown or missing fields" in mirror_text
    assert "resync_required" in mirror_text
    assert "receipt.ack_invalid" in mirror_text
    assert "reset receipt violates native authority" in mirror_text
    assert "280f80bf64d46f9b2746f5d450dc8456e8fff4a1fe6180dd5c3e8b6a608370fe" in tests


def test_p4b_fixed_cross_language_receipt_vector_is_native_and_python_visible() -> None:
    native_test = NATIVE_TEST.read_text(encoding="utf-8")
    mirror_test = MIRROR_TEST.read_text(encoding="utf-8")
    expected = "280f80bf64d46f9b2746f5d450dc8456e8fff4a1fe6180dd5c3e8b6a608370fe"

    assert "native receipt bytes match the Python shadow mirror vector" in native_test
    assert expected in native_test
    assert expected in mirror_test


def test_p4b_fixed_cross_language_intent_vector_is_native_and_python_visible() -> None:
    native_test = NATIVE_TEST.read_text(encoding="utf-8")
    mirror_test = MIRROR_TEST.read_text(encoding="utf-8")
    native_source = SOURCE.read_text(encoding="utf-8")
    mirror_source = MIRROR.read_text(encoding="utf-8")
    expected = "7a9b047d12c941acf2153bb69d4bb20b0fba6feec9f9b2b92d845df503ab1c71"

    assert "canonical_episode_transition_intent_bytes" in native_source
    assert "native intent bytes match the cross-language authority vector" in native_test
    assert expected in native_test
    assert "canonical_episode_transition_intent_bytes" in mirror_source
    assert "episode_transition_intent_sha256" in mirror_source
    assert expected in mirror_test


def test_p4b_native_and_mirror_lanes_are_explicitly_ci_qualified() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "ef_runtime_host_candidate_test" in workflow
    assert "runtime_host_candidate_boundary" in workflow
    assert "test_runtime_state_transfer_candidate_contract.py" in workflow
    assert "test_runtime_episode_mirror.py" in workflow
