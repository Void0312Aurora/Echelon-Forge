from __future__ import annotations

import pytest

from python.tasking_contracts.failure_domains import (
    BatchResult,
    FailureDomain,
    RecoveryAdmission,
    WorldOutcome,
    WorldState,
    admission_rejection,
    build_batch_outcome,
)


def _world(index: int, state: WorldState, committed: bool | None, error: str | None = None) -> WorldOutcome:
    return WorldOutcome(index, state, committed, error)


def test_preflight_rejection_has_no_world_publication_and_is_retryable_after_fix() -> None:
    result = admission_rejection(
        batch_generation_ref="g1", operation_ref="op1", operation="setup", error_code="capability_missing"
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
    )
    assert result.result is BatchResult.COMPLETED
    assert result.recovery_admission is RecoveryAdmission.NONE
    assert result.retry_allowed is False


def test_partial_failure_fences_retry_when_one_world_completed() -> None:
    result = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(_world(0, WorldState.COMPLETED, True), _world(1, WorldState.FAILED, None, "worker_exception")),
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
    )
    assert result.result is BatchResult.FAILED
    assert result.as_dict()["worlds"][0]["step_committed"] is None
    assert result.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE


def test_cycle_and_duplicate_indexes_fail_closed() -> None:
    with pytest.raises(ValueError, match="unique, sorted"):
        build_batch_outcome(
            batch_generation_ref="g1", operation_ref="op1", operation="step",
            worlds=(_world(1, WorldState.COMPLETED, True), _world(0, WorldState.COMPLETED, True)),
        )
    with pytest.raises(ValueError, match="unique, sorted"):
        build_batch_outcome(
            batch_generation_ref="g1", operation_ref="op1", operation="step",
            worlds=(_world(0, WorldState.COMPLETED, True), _world(0, WorldState.COMPLETED, True)),
        )


def test_outcome_rejects_inconsistent_completed_record() -> None:
    with pytest.raises(ValueError, match="completed world"):
        WorldOutcome(0, WorldState.COMPLETED, None)
    with pytest.raises(ValueError, match="unknown_after_fault"):
        WorldOutcome(0, WorldState.UNKNOWN_AFTER_FAULT, False)
