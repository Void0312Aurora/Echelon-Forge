"""Layered failure-domain outcome contract for facade/batch callers.

This is a stdlib-only projection contract.  It records observed completion
and uncertainty; it does not claim rollback, retry safety, or process
isolation, and it does not replace native WorldBatch/RunReceipt authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

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


@dataclass(frozen=True)
class WorldOutcome:
    world_index: int
    state: WorldState
    step_committed: bool | None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.world_index, bool) or not isinstance(self.world_index, int) or self.world_index < 0:
            raise ValueError("world_index must be a non-negative integer")
        if not isinstance(self.state, WorldState):
            raise TypeError("state must be a WorldState")
        if self.state is WorldState.UNKNOWN_AFTER_FAULT and self.step_committed is not None:
            raise ValueError("unknown_after_fault must use step_committed=None")
        if self.state is WorldState.COMPLETED and self.step_committed is not True:
            raise ValueError("completed world must declare step_committed=True")
        if self.state is WorldState.SKIPPED and self.step_committed is not False:
            raise ValueError("skipped world must declare step_committed=False")
        if self.state is WorldState.FAILED and self.step_committed not in (False, None):
            raise ValueError("failed world cannot claim a committed step")
        if self.error_code is not None and (not isinstance(self.error_code, str) or not self.error_code.strip()):
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
    recovery_admission: RecoveryAdmission = RecoveryAdmission.NONE
    diagnostics: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("batch_generation_ref", self.batch_generation_ref), ("operation_ref", self.operation_ref), ("operation", self.operation)):
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
        if self.result is BatchResult.REJECTED and self.worlds:
            raise ValueError("admission rejection must not publish world outcomes")
        states = {world.state for world in self.worlds}
        if self.result is BatchResult.COMPLETED and (not self.worlds or states != {WorldState.COMPLETED}):
            raise ValueError("completed outcome requires only completed worlds")
        if any(world.state is WorldState.UNKNOWN_AFTER_FAULT for world in self.worlds):
            if self.recovery_admission not in {
                RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE,
                RecoveryAdmission.TERMINATE_GENERATION,
            }:
                raise ValueError("unknown world state requires explicit reset/recreate or generation termination")
        if self.result is BatchResult.PARTIAL_FAILURE and not states.intersection({WorldState.FAILED, WorldState.UNKNOWN_AFTER_FAULT}):
            raise ValueError("partial_failure requires a failed or unknown world")
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
            "recovery_admission": self.recovery_admission.value,
            "diagnostics": list(self.diagnostics),
        }

    @property
    def retry_allowed(self) -> bool:
        """Conservative default: no transparent retry for mutating outcomes."""

        return self.result is BatchResult.REJECTED and self.recovery_admission is RecoveryAdmission.CALLER_FIX_REQUIRED


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
    domain: FailureDomain = FailureDomain.BATCH,
    diagnostics: tuple[str, ...] = (),
) -> BatchOperationOutcome:
    """Classify observed world outcomes without inferring rollback or retry."""

    if not worlds:
        raise ValueError("world outcomes are required for a batch execution")
    states = {world.state for world in worlds}
    if states == {WorldState.COMPLETED}:
        result = BatchResult.COMPLETED
        recovery = RecoveryAdmission.NONE
    elif WorldState.UNKNOWN_AFTER_FAULT in states:
        result = BatchResult.PARTIAL_FAILURE if WorldState.COMPLETED in states else BatchResult.FAILED
        recovery = RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    elif WorldState.COMPLETED in states:
        result = BatchResult.PARTIAL_FAILURE
        recovery = RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    else:
        result = BatchResult.FAILED
        recovery = RecoveryAdmission.TERMINATE_GENERATION
    return BatchOperationOutcome(
        batch_generation_ref=batch_generation_ref,
        operation_ref=operation_ref,
        operation=operation,
        domain=domain,
        result=result,
        worlds=worlds,
        recovery_admission=recovery,
        diagnostics=diagnostics,
    )


__all__ = [
    "BatchOperationOutcome",
    "BatchResult",
    "FailureDomain",
    "RecoveryAdmission",
    "SCHEMA_VERSION",
    "WorldOutcome",
    "WorldState",
    "admission_rejection",
    "build_batch_outcome",
]
