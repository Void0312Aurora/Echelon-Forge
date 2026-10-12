from __future__ import annotations

import pytest

from python.tasking_contracts.failure_domains import (
    BatchOperationOutcome,
    BatchResult,
    FailureDomain,
    RecoveryAdmission,
    WorldOutcome,
    WorldState,
    admission_rejection,
    build_batch_outcome,
    project_native_batch_fault,
    project_unresolved_batch_fault,
)


def _world(
    index: int, state: WorldState, committed: bool | None, error: str | None = None
) -> WorldOutcome:
    return WorldOutcome(index, state, committed, error)


def test_preflight_rejection_has_no_world_publication_and_is_retryable_after_fix() -> None:
    result = admission_rejection(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="setup",
        error_code="capability_missing",
    )
    assert result.domain is FailureDomain.ADMISSION
    assert result.result is BatchResult.REJECTED
    assert result.worlds == ()
    assert result.retry_allowed is True
    assert result.as_dict()["diagnostics"] == ["capability_missing"]


def test_completed_batch_requires_all_worlds_committed() -> None:
    result = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(_world(0, WorldState.COMPLETED, True), _world(1, WorldState.COMPLETED, True)),
        expected_world_indices=frozenset({0, 1}),
    )
    assert result.result is BatchResult.COMPLETED
    assert result.recovery_admission is RecoveryAdmission.NONE
    assert result.retry_allowed is False


def test_partial_failure_fences_retry_when_one_world_completed() -> None:
    result = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(
            _world(0, WorldState.COMPLETED, True),
            _world(1, WorldState.FAILED, None, "worker_exception"),
        ),
        expected_world_indices=frozenset({0, 1}),
    )
    assert result.result is BatchResult.PARTIAL_FAILURE
    assert result.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    assert result.retry_allowed is False


def test_unknown_after_fault_cannot_claim_committed_or_automatic_retry() -> None:
    result = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(_world(0, WorldState.UNKNOWN_AFTER_FAULT, None, "mid_step_exception"),),
        expected_world_indices=frozenset({0}),
    )
    assert result.result is BatchResult.FAILED
    assert result.as_dict()["worlds"][0]["step_committed"] is None
    assert result.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE


def test_cycle_and_duplicate_indexes_fail_closed() -> None:
    with pytest.raises(ValueError, match="unique, sorted"):
        build_batch_outcome(
            batch_generation_ref="g1",
            operation_ref="op1",
            operation="step",
            worlds=(_world(1, WorldState.COMPLETED, True), _world(0, WorldState.COMPLETED, True)),
            expected_world_indices=frozenset({0, 1}),
        )
    with pytest.raises(ValueError, match="unique, sorted"):
        build_batch_outcome(
            batch_generation_ref="g1",
            operation_ref="op1",
            operation="step",
            worlds=(_world(0, WorldState.COMPLETED, True), _world(0, WorldState.COMPLETED, True)),
            expected_world_indices=frozenset({0}),
        )


def test_outcome_rejects_inconsistent_completed_record() -> None:
    with pytest.raises(ValueError, match="completed world"):
        WorldOutcome(0, WorldState.COMPLETED, None)
    with pytest.raises(ValueError, match="unknown_after_fault"):
        WorldOutcome(0, WorldState.UNKNOWN_AFTER_FAULT, False)


def test_omitted_expected_world_cannot_be_reported_as_completed() -> None:
    result = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(_world(0, WorldState.COMPLETED, True),),
        expected_world_indices=frozenset({0, 1}),
    )
    assert result.result is BatchResult.PARTIAL_FAILURE
    assert result.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    assert result.as_dict()["expected_world_indices"] == [0, 1]
    assert "batch.world_scope_incomplete:missing=1" in result.as_dict()["diagnostics"]


@pytest.mark.parametrize("expected", [(), (0, 1)])
def test_direct_completed_constructor_requires_exact_expected_world_scope(expected) -> None:
    with pytest.raises(ValueError, match="complete expected world scope"):
        BatchOperationOutcome(
            batch_generation_ref="g1",
            operation_ref="op1",
            operation="step",
            domain=FailureDomain.BATCH,
            result=BatchResult.COMPLETED,
            worlds=(_world(0, WorldState.COMPLETED, True),),
            expected_world_indices=expected,
        )


def test_completed_and_skipped_worlds_form_partial_failure() -> None:
    result = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(_world(0, WorldState.COMPLETED, True), _world(1, WorldState.SKIPPED, False)),
        expected_world_indices=frozenset({0, 1}),
    )
    assert result.result is BatchResult.PARTIAL_FAILURE
    assert result.retry_allowed is False


def test_aggregate_fault_does_not_infer_unchanged_worlds_or_rollback() -> None:
    result = project_unresolved_batch_fault(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="setup",
        expected_world_indices=frozenset({0, 1, 2}),
        error_code="setup.aggregate_exception",
    )
    assert all(
        world.state is WorldState.UNKNOWN_AFTER_FAULT and world.step_committed is None
        for world in result.worlds
    )
    assert result.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE


def test_native_fault_projection_requires_observed_unhealthy_owner() -> None:
    class FakeRuntime:
        def batch_healthy(self) -> bool:
            return False

        def batch_failure_reason(self) -> str:
            return "worker_exception"

    result = project_native_batch_fault(
        runtime=FakeRuntime(),
        batch_generation_ref="native.g1",
        operation_ref="step.1",
        operation="step_batch",
        expected_world_indices=frozenset({0, 1}),
    )
    assert result.result is BatchResult.FAILED
    assert result.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    assert result.as_dict()["diagnostics"] == [
        "native.batch.failure",
        "native.batch.failure_reason:worker_exception",
    ]
    assert all(world.step_committed is None for world in result.worlds)

    class HealthyRuntime(FakeRuntime):
        def batch_healthy(self) -> bool:
            return True

    with pytest.raises(ValueError, match="unhealthy runtime"):
        project_native_batch_fault(
            runtime=HealthyRuntime(),
            batch_generation_ref="native.g1",
            operation_ref="step.1",
            operation="step_batch",
            expected_world_indices=frozenset({0}),
        )
