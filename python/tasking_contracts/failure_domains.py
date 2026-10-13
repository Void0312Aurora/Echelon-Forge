"""Layered failure-domain outcome contract for facade/batch callers.

This is a stdlib-only projection contract.  It records observed completion
and uncertainty; it does not claim rollback, retry safety, or process
isolation, and it does not replace native WorldBatch/RunReceipt authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

SCHEMA_VERSION = "echelon_forge.batch_operation_outcome.v1"


class FailureDomain(str, Enum):
    ADMISSION = "admission"
    MECHANISM = "mechanism"
    WORLD = "world"
    BATCH = "batch"
    HOST = "host"


class WorldState(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNKNOWN_AFTER_FAULT = "unknown_after_fault"


class BatchResult(str, Enum):
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_FAILURE = "partial_failure"


class RecoveryAdmission(str, Enum):
    NONE = "none"
    CALLER_FIX_REQUIRED = "caller_fix_required"
    REQUIRE_EXPLICIT_RESET_OR_RECREATE = "require_explicit_reset_or_recreate"
    TERMINATE_GENERATION = "terminate_generation"


class NativeBatchHealth(Protocol):
    """Small read-only seam exposed by the native batch owner.

    This deliberately omits reset and mutation methods. The projection may
    observe the native fence, but it cannot clear it or invent recovery truth.
    """

    def batch_healthy(self) -> bool: ...

    def batch_failure_reason(self) -> str: ...

    def batch_generation(self) -> int: ...


@dataclass(frozen=True)
class WorldOutcome:
    world_index: int
    state: WorldState
    step_committed: bool | None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.world_index, bool)
            or not isinstance(self.world_index, int)
            or self.world_index < 0
        ):
            raise ValueError("world_index must be a non-negative integer")
        if not isinstance(self.state, WorldState):
            raise TypeError("state must be a WorldState")
        if self.state is WorldState.UNKNOWN_AFTER_FAULT and self.step_committed is not None:
            raise ValueError("unknown_after_fault must use step_committed=None")
        if self.state is WorldState.COMPLETED and self.step_committed is not True:
            raise ValueError("completed world must declare step_committed=True")
        if self.state is WorldState.SKIPPED and self.step_committed is not False:
            raise ValueError("skipped world must declare step_committed=False")
        if (
            self.state is WorldState.FAILED
            and self.step_committed is not False
            and self.step_committed is not None
        ):
            raise ValueError("failed world cannot claim a committed step")
        if self.error_code is not None and (
            not isinstance(self.error_code, str) or not self.error_code.strip()
        ):
            raise ValueError("error_code must be a non-empty string when supplied")

    def as_dict(self) -> dict[str, Any]:
        return {
            "world_index": self.world_index,
            "state": self.state.value,
            "step_committed": self.step_committed,
            **({"error_code": self.error_code} if self.error_code is not None else {}),
        }


@dataclass(frozen=True)
class BatchOperationOutcome:
    batch_generation_ref: str
    operation_ref: str
    operation: str
    domain: FailureDomain
    result: BatchResult
    worlds: tuple[WorldOutcome, ...] = ()
    expected_world_indices: tuple[int, ...] = ()
    recovery_admission: RecoveryAdmission = RecoveryAdmission.NONE
    diagnostics: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("batch_generation_ref", self.batch_generation_ref),
            ("operation_ref", self.operation_ref),
            ("operation", self.operation),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.domain, FailureDomain):
            raise TypeError("domain must be a FailureDomain")
        if not isinstance(self.result, BatchResult):
            raise TypeError("result must be a BatchResult")
        if not isinstance(self.recovery_admission, RecoveryAdmission):
            raise TypeError("recovery_admission must be a RecoveryAdmission")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version!r}")
        indexes = [world.world_index for world in self.worlds]
        if indexes != sorted(set(indexes)):
            raise ValueError("world outcomes must have unique, sorted world indexes")
        if self.expected_world_indices != tuple(sorted(set(self.expected_world_indices))):
            raise ValueError("expected world indexes must be unique and sorted")
        if any(
            isinstance(index, bool) or not isinstance(index, int) or index < 0
            for index in self.expected_world_indices
        ):
            raise ValueError("expected world indexes must be non-negative integers")
        if self.result is not BatchResult.REJECTED and not self.expected_world_indices:
            raise ValueError("execution outcome requires expected world scope")
        if self.expected_world_indices and not set(indexes).issubset(self.expected_world_indices):
            raise ValueError("world outcome is outside the expected world scope")
        if self.result is BatchResult.REJECTED and self.worlds:
            raise ValueError("admission rejection must not publish world outcomes")
        states = {world.state for world in self.worlds}
        if self.result is BatchResult.COMPLETED and (
            not self.worlds or states != {WorldState.COMPLETED}
        ):
            raise ValueError("completed outcome requires only completed worlds")
        if self.result is BatchResult.COMPLETED and (
            not self.expected_world_indices or set(indexes) != set(self.expected_world_indices)
        ):
            raise ValueError("completed outcome requires complete expected world scope")
        if any(world.state is WorldState.UNKNOWN_AFTER_FAULT for world in self.worlds):
            if self.recovery_admission not in {
                RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE,
                RecoveryAdmission.TERMINATE_GENERATION,
            }:
                raise ValueError(
                    "unknown world state requires explicit reset/recreate or generation termination"
                )
        incomplete_scope = bool(self.expected_world_indices) and set(indexes) != set(
            self.expected_world_indices
        )
        if (
            self.result is BatchResult.PARTIAL_FAILURE
            and not incomplete_scope
            and not states.intersection(
                {WorldState.FAILED, WorldState.UNKNOWN_AFTER_FAULT, WorldState.SKIPPED}
            )
        ):
            raise ValueError("partial_failure requires a failed, unknown or skipped world")
        if self.result in {
            BatchResult.FAILED,
            BatchResult.PARTIAL_FAILURE,
        } and self.recovery_admission not in {
            RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE,
            RecoveryAdmission.TERMINATE_GENERATION,
        }:
            raise ValueError(
                "execution failure requires explicit recovery or generation termination"
            )
        if self.result is BatchResult.FAILED and states == {WorldState.COMPLETED}:
            raise ValueError("failed outcome cannot contain only completed worlds")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "batch_generation_ref": self.batch_generation_ref,
            "operation_ref": self.operation_ref,
            "operation": self.operation,
            "domain": self.domain.value,
            "result": self.result.value,
            "worlds": [world.as_dict() for world in self.worlds],
            "expected_world_indices": list(self.expected_world_indices),
            "recovery_admission": self.recovery_admission.value,
            "diagnostics": list(self.diagnostics),
        }

    @property
    def retry_allowed(self) -> bool:
        """Conservative default: no transparent retry for mutating outcomes."""

        return (
            self.result is BatchResult.REJECTED
            and self.recovery_admission is RecoveryAdmission.CALLER_FIX_REQUIRED
        )


def admission_rejection(
    *, batch_generation_ref: str, operation_ref: str, operation: str, error_code: str
) -> BatchOperationOutcome:
    if not error_code.strip():
        raise ValueError("error_code must be non-empty")
    return BatchOperationOutcome(
        batch_generation_ref=batch_generation_ref,
        operation_ref=operation_ref,
        operation=operation,
        domain=FailureDomain.ADMISSION,
        result=BatchResult.REJECTED,
        recovery_admission=RecoveryAdmission.CALLER_FIX_REQUIRED,
        diagnostics=(error_code,),
    )


def build_batch_outcome(
    *,
    batch_generation_ref: str,
    operation_ref: str,
    operation: str,
    worlds: tuple[WorldOutcome, ...],
    expected_world_indices: frozenset[int],
    domain: FailureDomain = FailureDomain.BATCH,
    diagnostics: tuple[str, ...] = (),
) -> BatchOperationOutcome:
    """Classify observed world outcomes without inferring rollback or retry."""

    if not worlds:
        raise ValueError("world outcomes are required for a batch execution")
    if not expected_world_indices:
        raise ValueError("expected_world_indices are required for a batch execution")
    if any(
        isinstance(index, bool) or not isinstance(index, int) or index < 0
        for index in expected_world_indices
    ):
        raise ValueError("expected world indexes must be non-negative integers")
    observed_indexes = {world.world_index for world in worlds}
    if not observed_indexes.issubset(expected_world_indices):
        raise ValueError("world outcome is outside the expected world scope")
    missing_indexes = sorted(expected_world_indices - observed_indexes)
    states = {world.state for world in worlds}
    if states == {WorldState.COMPLETED} and not missing_indexes:
        result = BatchResult.COMPLETED
        recovery = RecoveryAdmission.NONE
    elif WorldState.UNKNOWN_AFTER_FAULT in states:
        result = (
            BatchResult.PARTIAL_FAILURE if WorldState.COMPLETED in states else BatchResult.FAILED
        )
        recovery = RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    elif WorldState.COMPLETED in states or missing_indexes:
        result = BatchResult.PARTIAL_FAILURE
        recovery = RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    else:
        result = BatchResult.FAILED
        recovery = RecoveryAdmission.TERMINATE_GENERATION
    effective_diagnostics = tuple(diagnostics)
    if missing_indexes:
        effective_diagnostics += (
            f"batch.world_scope_incomplete:missing={','.join(map(str, missing_indexes))}",
        )
    return BatchOperationOutcome(
        batch_generation_ref=batch_generation_ref,
        operation_ref=operation_ref,
        operation=operation,
        domain=domain,
        result=result,
        worlds=worlds,
        expected_world_indices=tuple(sorted(expected_world_indices)),
        recovery_admission=recovery,
        diagnostics=effective_diagnostics,
    )


def project_unresolved_batch_fault(
    *,
    batch_generation_ref: str,
    operation_ref: str,
    operation: str,
    expected_world_indices: frozenset[int],
    error_code: str,
) -> BatchOperationOutcome:
    """Project an aggregate exception with no authoritative per-world status.

    Clocks alone cannot establish effect commit/rollback. Every affected world
    stays unknown, even when its clock did not advance. This records evidence;
    the #210 native fence remains the recovery authority.
    """
    return build_batch_outcome(
        batch_generation_ref=batch_generation_ref,
        operation_ref=operation_ref,
        operation=operation,
        expected_world_indices=expected_world_indices,
        worlds=tuple(
            WorldOutcome(index, WorldState.UNKNOWN_AFTER_FAULT, None, error_code)
            for index in sorted(expected_world_indices)
        ),
        diagnostics=(error_code,),
    )


def project_native_batch_fault(
    *,
    runtime: NativeBatchHealth,
    batch_generation_ref: str,
    operation_ref: str,
    operation: str,
    expected_world_indices: frozenset[int],
    error_code: str = "native.batch.failure",
) -> BatchOperationOutcome:
    """Project an observed native fence without manufacturing commit status.

    The native owner remains authoritative for health and failure reason. This
    adapter only copies that observation into the conservative all-unknown
    outcome; it does not infer rollback or perform a reset. The supplied
    generation reference must match the native-owned generation, so callers
    cannot create a failure record detached from the observed native batch.
    A healthy runtime is rejected so callers cannot create a failure record
    detached from an observed native fault.
    """

    if runtime.batch_healthy():
        raise ValueError("native batch fault projection requires an unhealthy runtime")
    if not isinstance(error_code, str) or not error_code.strip():
        raise ValueError("error_code must be a non-empty string")
    reason = runtime.batch_failure_reason()
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("unhealthy native runtime must provide a failure reason")
    native_generation = runtime.batch_generation()
    if (
        isinstance(native_generation, bool)
        or not isinstance(native_generation, int)
        or native_generation < 0
    ):
        raise TypeError("native batch generation must be a non-negative integer")
    if batch_generation_ref != str(native_generation):
        raise ValueError("batch generation reference does not match native batch generation")
    if not expected_world_indices:
        raise ValueError("expected_world_indices are required for a batch execution")
    return build_batch_outcome(
        batch_generation_ref=batch_generation_ref,
        operation_ref=operation_ref,
        operation=operation,
        domain=FailureDomain.BATCH,
        expected_world_indices=expected_world_indices,
        worlds=tuple(
            WorldOutcome(index, WorldState.UNKNOWN_AFTER_FAULT, None, error_code)
            for index in sorted(expected_world_indices)
        ),
        diagnostics=(error_code, f"native.batch.failure_reason:{reason}"),
    )


def project_host_fault(
    *,
    batch_generation_ref: str,
    operation_ref: str,
    operation: str,
    expected_world_indices: frozenset[int],
    error_code: str,
    process_survived: bool,
) -> BatchOperationOutcome:
    """Project an independently observed host/process fault conservatively.

    A caller or supervisor supplies the process-survival observation. This
    helper never infers per-world commit state, recovery, or isolation from a
    Python exception; the generation is terminated and every affected world is
    explicitly unknown until an owner reset/recreate path establishes truth.
    """

    if not isinstance(process_survived, bool):
        raise TypeError("process_survived must be a bool observation")
    if not isinstance(error_code, str) or not error_code.strip():
        raise ValueError("error_code must be a non-empty string")
    if not expected_world_indices:
        raise ValueError("expected_world_indices are required for a host fault")
    worlds = tuple(
        WorldOutcome(index, WorldState.UNKNOWN_AFTER_FAULT, None, error_code)
        for index in sorted(expected_world_indices)
    )
    return BatchOperationOutcome(
        batch_generation_ref=batch_generation_ref,
        operation_ref=operation_ref,
        operation=operation,
        domain=FailureDomain.HOST,
        result=BatchResult.FAILED,
        worlds=worlds,
        expected_world_indices=tuple(sorted(expected_world_indices)),
        recovery_admission=RecoveryAdmission.TERMINATE_GENERATION,
        diagnostics=(error_code, f"host.process_survived:{str(process_survived).lower()}"),
    )


__all__ = [
    "BatchOperationOutcome",
    "BatchResult",
    "FailureDomain",
    "NativeBatchHealth",
    "RecoveryAdmission",
    "SCHEMA_VERSION",
    "WorldOutcome",
    "WorldState",
    "admission_rejection",
    "build_batch_outcome",
    "project_unresolved_batch_fault",
    "project_native_batch_fault",
    "project_host_fault",
]
