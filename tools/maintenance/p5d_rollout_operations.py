"""P5-D operational telemetry and rollback-drill contracts.

The runtime remains the authority for host publication, checkpoints, journals,
and receipts.  This module is an evidence/runbook helper: it records
epoch/plan/release-tagged counters and validates the operator prerequisites for
the two P1-C backout protocols.  It deliberately does not publish a runtime
slot, manufacture a checkpoint, or select a production route.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

from tools.maintenance.runtime_artifact_ledger import select_backout_protocol


class RolloutOperationsError(RuntimeError):
  """Raised when an operational drill or telemetry sample is not admissible."""


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")


def _require_id(value: str, field: str) -> str:
  if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
    raise RolloutOperationsError(f"{field} must be a bounded identifier")
  return value


def _require_sha(value: str, field: str) -> str:
  if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
    raise RolloutOperationsError(f"{field} must be a lowercase SHA-256 digest")
  return value


def _require_nonnegative_int(value: int, field: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise RolloutOperationsError(f"{field} must be a non-negative integer")
  return value


def _require_duration(value: float, field: str) -> float:
  if not isinstance(value, (int, float)) or isinstance(value, bool):
    raise RolloutOperationsError(f"{field} must be a finite non-negative duration")
  normalized = float(value)
  if not math.isfinite(normalized) or normalized < 0.0:
    raise RolloutOperationsError(f"{field} must be a finite non-negative duration")
  return normalized


@dataclass(frozen=True, slots=True)
class RolloutSLOTargets:
  """Initial P1-C launch targets; P2-B may tighten, never weaken them."""

  replacement_success_rate: float = 0.999
  drain_completion_rate: float = 0.99
  backout_recovery_deadline_s: float = 300.0
  crash_receipt_deadline_s: float = 300.0
  artifact_availability: float = 0.999

  def __post_init__(self) -> None:
    for field in (
      "replacement_success_rate",
      "drain_completion_rate",
      "artifact_availability",
    ):
      value = float(getattr(self, field))
      if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise RolloutOperationsError(f"{field} must be a finite ratio in [0, 1]")
    for field in ("backout_recovery_deadline_s", "crash_receipt_deadline_s"):
      _require_duration(float(getattr(self, field)), field)


@dataclass(frozen=True, slots=True)
class RolloutSLOReport:
  passed: bool
  reasons: tuple[str, ...]
  metrics: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class RolloutTelemetrySnapshot:
  """Secret-free, tagged counters suitable for evidence and dashboards."""

  release_id: str
  plan_sha256: str
  epoch: str
  admission_attempts: int = 0
  admission_rejections: int = 0
  replacement_attempts: int = 0
  replacement_successes: int = 0
  replacement_duration_max_s: float = 0.0
  drain_attempts: int = 0
  drain_completed: int = 0
  drain_deadline_breaches: int = 0
  backout_attempts: int = 0
  backout_recoveries: int = 0
  backout_recovery_max_s: float = 0.0
  crash_receipt_attempts: int = 0
  crash_receipt_breaches: int = 0
  artifact_retrieval_attempts: int = 0
  artifact_retrieval_failures: int = 0
  stale_reference_rejections: int = 0
  wrong_epoch_results: int = 0
  duplicate_publications: int = 0
  caller_adoptions: int = 0
  caller_total: int = 0
  security_denials: int = 0

  def __post_init__(self) -> None:
    _require_id(self.release_id, "release_id")
    _require_sha(self.plan_sha256, "plan_sha256")
    _require_id(self.epoch, "epoch")
    for field in (
      "admission_attempts", "admission_rejections", "replacement_attempts",
      "replacement_successes", "drain_attempts", "drain_completed",
      "drain_deadline_breaches", "backout_attempts", "backout_recoveries",
      "crash_receipt_attempts", "crash_receipt_breaches",
      "artifact_retrieval_attempts", "artifact_retrieval_failures",
      "stale_reference_rejections", "wrong_epoch_results", "duplicate_publications",
      "caller_adoptions", "caller_total", "security_denials",
    ):
      _require_nonnegative_int(getattr(self, field), field)
    _require_duration(self.replacement_duration_max_s, "replacement_duration_max_s")
    _require_duration(self.backout_recovery_max_s, "backout_recovery_max_s")
    if self.replacement_successes > self.replacement_attempts:
      raise RolloutOperationsError("replacement successes exceed attempts")
    if self.drain_completed > self.drain_attempts:
      raise RolloutOperationsError("drain completions exceed attempts")
    if self.backout_recoveries > self.backout_attempts:
      raise RolloutOperationsError("backout recoveries exceed attempts")
    if self.caller_adoptions > self.caller_total:
      raise RolloutOperationsError("caller adoptions exceed caller total")
    if self.artifact_retrieval_failures > self.artifact_retrieval_attempts:
      raise RolloutOperationsError("artifact retrieval failures exceed attempts")

  def to_document(self) -> dict[str, Any]:
    """Return a stable, non-authoritative evidence projection."""

    replacement_rate = (
      self.replacement_successes / self.replacement_attempts
      if self.replacement_attempts else 0.0
    )
    drain_rate = (
      self.drain_completed / self.drain_attempts
      if self.drain_attempts else 0.0
    )
    artifact_rate = (
      (self.artifact_retrieval_attempts - self.artifact_retrieval_failures)
      / self.artifact_retrieval_attempts
      if self.artifact_retrieval_attempts else 0.0
    )
    adoption_rate = (
      self.caller_adoptions / self.caller_total
      if self.caller_total else 0.0
    )
    return {
      "schema_version": "echelon_forge.p5d_rollout_telemetry.v1",
      "release_id": self.release_id,
      "plan_sha256": self.plan_sha256,
      "epoch": self.epoch,
      "counters": {
        "admission_attempts": self.admission_attempts,
        "admission_rejections": self.admission_rejections,
        "replacement_attempts": self.replacement_attempts,
        "replacement_successes": self.replacement_successes,
        "drain_attempts": self.drain_attempts,
        "drain_completed": self.drain_completed,
        "drain_deadline_breaches": self.drain_deadline_breaches,
        "backout_attempts": self.backout_attempts,
        "backout_recoveries": self.backout_recoveries,
        "crash_receipt_attempts": self.crash_receipt_attempts,
        "crash_receipt_breaches": self.crash_receipt_breaches,
        "artifact_retrieval_attempts": self.artifact_retrieval_attempts,
        "artifact_retrieval_failures": self.artifact_retrieval_failures,
        "stale_reference_rejections": self.stale_reference_rejections,
        "wrong_epoch_results": self.wrong_epoch_results,
        "duplicate_publications": self.duplicate_publications,
        "caller_adoptions": self.caller_adoptions,
        "caller_total": self.caller_total,
        "security_denials": self.security_denials,
      },
      "max_durations_s": {
        "replacement": self.replacement_duration_max_s,
        "backout_recovery": self.backout_recovery_max_s,
      },
      "ratios": {
        "replacement_success": replacement_rate,
        "drain_completion": drain_rate,
        "artifact_availability": artifact_rate,
        "caller_adoption": adoption_rate,
      },
    }


class RolloutTelemetryRecorder:
  """Small in-memory recorder used by drills and operator integrations."""

  def __init__(self, *, release_id: str, plan_sha256: str, epoch: str) -> None:
    self._release_id = _require_id(release_id, "release_id")
    self._plan_sha256 = _require_sha(plan_sha256, "plan_sha256")
    self._epoch = _require_id(epoch, "epoch")
    self._counts: dict[str, int] = {}
    self._max_durations = {"replacement": 0.0, "backout_recovery": 0.0}

  def _inc(self, field: str, amount: int = 1) -> None:
    _require_nonnegative_int(amount, field)
    self._counts[field] = self._counts.get(field, 0) + amount

  def _max_duration(self, field: str, value: float) -> None:
    normalized = _require_duration(value, field)
    self._max_durations[field] = max(self._max_durations[field], normalized)

  def record_admission(self, *, accepted: bool) -> None:
    self._inc("admission_attempts")
    if not accepted:
      self._inc("admission_rejections")

  def record_replacement(self, *, success: bool, duration_s: float) -> None:
    self._inc("replacement_attempts")
    if success:
      self._inc("replacement_successes")
    self._max_duration("replacement", duration_s)

  def record_drain(self, *, completed: bool, deadline_breached: bool = False) -> None:
    self._inc("drain_attempts")
    if completed:
      self._inc("drain_completed")
    if deadline_breached:
      self._inc("drain_deadline_breaches")

  def record_backout(self, *, recovered: bool, duration_s: float) -> None:
    self._inc("backout_attempts")
    if recovered:
      self._inc("backout_recoveries")
    self._max_duration("backout_recovery", duration_s)

  def record_crash_receipt(self, *, reconciled: bool, delay_s: float) -> None:
    self._inc("crash_receipt_attempts")
    if not reconciled or _require_duration(delay_s, "delay_s") > 300.0:
      self._inc("crash_receipt_breaches")

  def record_artifact_retrieval(self, *, available: bool) -> None:
    self._inc("artifact_retrieval_attempts")
    if not available:
      self._inc("artifact_retrieval_failures")

  def record_caller_adoption(self, *, adopted: bool) -> None:
    self._inc("caller_total")
    if adopted:
      self._inc("caller_adoptions")

  def record_safety_event(
    self,
    *,
    stale_reference: bool = False,
    wrong_epoch_result: bool = False,
    duplicate_publication: bool = False,
    security_denial: bool = False,
  ) -> None:
    for enabled, field in (
      (stale_reference, "stale_reference_rejections"),
      (wrong_epoch_result, "wrong_epoch_results"),
      (duplicate_publication, "duplicate_publications"),
      (security_denial, "security_denials"),
    ):
      if enabled:
        self._inc(field)

  def snapshot(self) -> RolloutTelemetrySnapshot:
    return RolloutTelemetrySnapshot(
      release_id=self._release_id,
      plan_sha256=self._plan_sha256,
      epoch=self._epoch,
      replacement_duration_max_s=self._max_durations["replacement"],
      backout_recovery_max_s=self._max_durations["backout_recovery"],
      **self._counts,
    )

  def evaluate_slo(self, targets: RolloutSLOTargets = RolloutSLOTargets()) -> RolloutSLOReport:
    snapshot = self.snapshot()
    reasons: list[str] = []
    if snapshot.wrong_epoch_results or snapshot.duplicate_publications or snapshot.stale_reference_rejections or snapshot.security_denials:
      reasons.append("zero-tolerance-safety-event")
    if snapshot.replacement_attempts == 0:
      reasons.append("replacement-observation-missing")
    elif snapshot.replacement_successes / snapshot.replacement_attempts < targets.replacement_success_rate:
      reasons.append("replacement-success-rate")
    if snapshot.drain_attempts == 0:
      reasons.append("drain-observation-missing")
    elif snapshot.drain_completed / snapshot.drain_attempts < targets.drain_completion_rate:
      reasons.append("drain-completion-rate")
    if snapshot.backout_attempts == 0:
      reasons.append("backout-observation-missing")
    elif snapshot.backout_recovery_max_s > targets.backout_recovery_deadline_s:
      reasons.append("backout-recovery-deadline")
    if snapshot.crash_receipt_attempts == 0:
      reasons.append("crash-receipt-observation-missing")
    elif snapshot.crash_receipt_breaches:
      reasons.append("crash-receipt-deadline")
    if snapshot.artifact_retrieval_attempts == 0:
      reasons.append("artifact-retrieval-observation-missing")
    elif (
      (snapshot.artifact_retrieval_attempts - snapshot.artifact_retrieval_failures)
      / snapshot.artifact_retrieval_attempts < targets.artifact_availability
    ):
      reasons.append("artifact-availability")
    metrics = snapshot.to_document()["ratios"] | snapshot.to_document()["max_durations_s"]
    return RolloutSLOReport(passed=not reasons, reasons=tuple(reasons), metrics=metrics)


@dataclass(frozen=True, slots=True)
class BackoutDrillResult:
  protocol: str
  accepted: bool
  source_generation: int
  target_generation: int
  source_epoch: str
  target_epoch: str
  admission_closed: bool
  checkpoint_validated: bool
  package_restarted: bool
  caller_resynchronized: bool
  receipt_finalized: bool
  fail_stop: bool = False

  def to_document(self) -> dict[str, Any]:
    return {
      "schema_version": "echelon_forge.p5d_backout_drill.v1",
      "protocol": self.protocol,
      "accepted": self.accepted,
      "source_generation": self.source_generation,
      "target_generation": self.target_generation,
      "source_epoch": self.source_epoch,
      "target_epoch": self.target_epoch,
      "admission_closed": self.admission_closed,
      "checkpoint_validated": self.checkpoint_validated,
      "package_restarted": self.package_restarted,
      "caller_resynchronized": self.caller_resynchronized,
      "receipt_finalized": self.receipt_finalized,
      "fail_stop": self.fail_stop,
    }


def rehearse_same_release_checkpoint_recovery(
  *,
  current_generation: int,
  source_epoch: str,
  target_epoch: str,
  checkpoint_available: bool,
  checkpoint_validated: bool,
  source_faulted: bool,
  source_truth_exported: bool,
  admission_closed: bool,
  caller_resynchronized: bool,
  receipt_finalized: bool,
  recovery_duration_s: float,
  irreversible_write_boundary: str = "none",
) -> BackoutDrillResult:
  """Validate the same-release recovery prerequisites without mutating runtime."""

  _require_nonnegative_int(current_generation, "current_generation")
  _require_id(source_epoch, "source_epoch")
  _require_id(target_epoch, "target_epoch")
  if source_epoch == target_epoch:
    raise RolloutOperationsError("same-release recovery must publish a new epoch")
  protocol = select_backout_protocol(
    current_generation=current_generation,
    target_generation=current_generation,
    same_release=True,
    compatible_checkpoint_available=checkpoint_available,
    rollback_package_available=True,
    irreversible_write_boundary=irreversible_write_boundary,
  )
  if protocol != "same-release-checkpoint-recovery":
    raise RolloutOperationsError(f"unexpected same-release protocol: {protocol}")
  if not source_faulted:
    raise RolloutOperationsError("same-release recovery requires a faulted source")
  if source_truth_exported:
    raise RolloutOperationsError("faulted source truth must not be exported")
  if not checkpoint_validated:
    raise RolloutOperationsError("same-release recovery requires a validated checkpoint")
  if not admission_closed:
    raise RolloutOperationsError("same-release recovery requires closed admission")
  if not caller_resynchronized:
    raise RolloutOperationsError("same-release recovery requires caller resynchronization")
  if not receipt_finalized:
    raise RolloutOperationsError("same-release recovery requires a finalized receipt")
  _require_duration(recovery_duration_s, "recovery_duration_s")
  return BackoutDrillResult(
    protocol=protocol,
    accepted=True,
    source_generation=current_generation,
    target_generation=current_generation,
    source_epoch=source_epoch,
    target_epoch=target_epoch,
    admission_closed=True,
    checkpoint_validated=True,
    package_restarted=False,
    caller_resynchronized=True,
    receipt_finalized=True,
  )


def rehearse_package_restart(
  *,
  current_generation: int,
  target_generation: int,
  source_epoch: str,
  target_epoch: str,
  checkpoint_available: bool,
  package_available: bool,
  admission_closed: bool,
  journals_finalized: bool,
  source_stopped: bool,
  new_boot_identity: bool,
  caller_resynchronized: bool,
  receipt_finalized: bool,
  recovery_duration_s: float,
  irreversible_write_boundary: str = "none",
) -> BackoutDrillResult:
  """Validate the stop/drain/replace/reconnect package rollback protocol."""

  _require_nonnegative_int(current_generation, "current_generation")
  _require_nonnegative_int(target_generation, "target_generation")
  _require_id(source_epoch, "source_epoch")
  _require_id(target_epoch, "target_epoch")
  if source_epoch == target_epoch:
    raise RolloutOperationsError("package restart must publish a new epoch")
  protocol = select_backout_protocol(
    current_generation=current_generation,
    target_generation=target_generation,
    same_release=False,
    compatible_checkpoint_available=checkpoint_available,
    rollback_package_available=package_available,
    irreversible_write_boundary=irreversible_write_boundary,
  )
  if protocol == "stop-or-roll-forward":
    return BackoutDrillResult(
      protocol=protocol,
      accepted=False,
      source_generation=current_generation,
      target_generation=target_generation,
      source_epoch=source_epoch,
      target_epoch=target_epoch,
      admission_closed=admission_closed,
      checkpoint_validated=False,
      package_restarted=False,
      caller_resynchronized=False,
      receipt_finalized=receipt_finalized,
      fail_stop=True,
    )
  if not admission_closed:
    raise RolloutOperationsError("package rollback requires closed admission")
  if not journals_finalized:
    raise RolloutOperationsError("package rollback requires finalized journals")
  if not source_stopped:
    raise RolloutOperationsError("package rollback requires the source process to stop")
  if not new_boot_identity:
    raise RolloutOperationsError("package rollback requires a new boot identity")
  if not caller_resynchronized:
    raise RolloutOperationsError("package rollback requires caller resynchronization")
  if not receipt_finalized:
    raise RolloutOperationsError("package rollback requires a finalized receipt")
  _require_duration(recovery_duration_s, "recovery_duration_s")
  checkpoint_validated = protocol == "package-restart-from-checkpoint"
  return BackoutDrillResult(
    protocol=protocol,
    accepted=True,
    source_generation=current_generation,
    target_generation=target_generation,
    source_epoch=source_epoch,
    target_epoch=target_epoch,
    admission_closed=True,
    checkpoint_validated=checkpoint_validated,
    package_restarted=True,
    caller_resynchronized=True,
    receipt_finalized=True,
  )


__all__ = [
  "BackoutDrillResult",
  "RolloutOperationsError",
  "RolloutSLOReport",
  "RolloutSLOTargets",
  "RolloutTelemetryRecorder",
  "RolloutTelemetrySnapshot",
  "rehearse_package_restart",
  "rehearse_same_release_checkpoint_recovery",
]
