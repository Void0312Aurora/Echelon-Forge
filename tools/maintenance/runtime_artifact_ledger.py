"""P3-C non-production ArtifactLedger and rollout compatibility simulator.

The module models the frozen durability, fencing, N/N-1, shadow, and backout
contracts.  It is deliberately incapable of authorizing production execution;
P5-B must qualify a durable backend and P5-D owns the only production cutover.
"""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from tools.maintenance.runtime_authority_contracts import (
  AuthorityContractError,
  canonical_json_bytes,
  parse_canonical_json_bytes,
  validate_authority_envelope,
  validate_rollout_transition,
)


LEDGER_CONTRACT_VERSION = "echelon_forge.artifact_ledger_contract.v1"
INVENTORY_SCHEMA_VERSION = "echelon_forge.stored_artifact_inventory.v1"
SHADOW_RECEIPT_SCHEMA_VERSION = "echelon_forge.shadow_comparison_receipt.v1"
KILL_SWITCH_SCHEMA_VERSION = "echelon_forge.kill_switch_record.v1"
ROLLOUT_QUALIFICATION_SCHEMA_VERSION = "echelon_forge.rollout_qualification_record.v1"
QUALIFICATION_EVIDENCE_SCHEMA_VERSION = "echelon_forge.qualification_evidence.v1"
RETENTION_CLASSES = frozenset({"active-release", "rollback-window", "run-retained", "evidence-short"})
TERMINAL_JOURNAL_STATES = frozenset({"completed", "failed", "cancelled", "rejected", "crashed", "incomplete"})
ROLL_OUT_TRANSITIONS = {
  "prepared": frozenset({"shadow", "backed-out"}),
  "shadow": frozenset({"canary-ready", "backed-out"}),
  "canary-ready": frozenset({"production-canary", "backed-out"}),
  "production-canary": frozenset({"adoption-expanding", "backed-out"}),
  "adoption-expanding": frozenset({"adoption-expanding", "rollback-window", "backed-out"}),
  "rollback-window": frozenset({"stable", "backed-out"}),
  "stable": frozenset({"prepared"}),
  "backed-out": frozenset({"prepared"}),
}
ROLE_PERMISSIONS = {
  "plan_compiler": frozenset({"blob.put"}),
  "release_artifact_pipeline": frozenset({"blob.put", "blob.get", "blob.stat", "inventory.write"}),
  "release_controller": frozenset({"blob.put", "blob.get", "blob.stat", "fence.acquire", "slot.write", "rollout.write", "audit.read"}),
  "runtime_host": frozenset({"blob.put", "blob.get", "fence.acquire", "journal.write", "checkpoint.read", "checkpoint.write", "slot.write"}),
  "runtime_evidence": frozenset({"blob.get", "blob.stat", "inventory.read", "journal.read", "checkpoint.read", "audit.read"}),
  "shadow_observer": frozenset({"blob.put", "blob.get", "inventory.read"}),
  "crash_reconciler": frozenset({"blob.put", "blob.get", "fence.acquire", "process.confirm_terminated", "writer.tombstone", "journal.write", "journal.read", "audit.read"}),
}
ROLE_MEDIA_TYPES = {
  "plan_compiler": frozenset({"application/vnd.echelon-forge.resolved-composition-plan-envelope.v1+json"}),
  "release_artifact_pipeline": frozenset({
    "application/vnd.echelon-forge.release-manifest-envelope.v1+json",
    "application/vnd.echelon-forge.stored-artifact-inventory.v1+json",
    "application/vnd.echelon-forge.release-package.v1+octets",
  }),
  "release_controller": frozenset({
    "application/vnd.echelon-forge.rollout-qualification-record.v1+json",
    "application/vnd.echelon-forge.kill-switch-record.v1+json",
    "application/vnd.echelon-forge.qualification-evidence.v1+json",
    "application/vnd.echelon-forge.qualification-proof.v1+octets",
    "application/vnd.echelon-forge.shadow-comparison-receipt.v1+json",
  }),
  "runtime_host": frozenset({
    "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json",
    "application/vnd.echelon-forge.run-journal-header.v1+json",
    "application/vnd.echelon-forge.run-journal-record.v1+octets",
  }),
  "shadow_observer": frozenset({
    "application/vnd.echelon-forge.shadow-comparison-receipt.v1+json",
    "application/vnd.echelon-forge.qualification-proof.v1+octets",
  }),
  "crash_reconciler": frozenset({"application/vnd.echelon-forge.run-journal-record.v1+octets"}),
}
ROLE_READ_MEDIA_TYPES = {
  "plan_compiler": frozenset(),
  "release_artifact_pipeline": ROLE_MEDIA_TYPES["release_artifact_pipeline"],
  "release_controller": frozenset({
    "application/vnd.echelon-forge.resolved-composition-plan-envelope.v1+json",
    "application/vnd.echelon-forge.release-manifest-envelope.v1+json",
    "application/vnd.echelon-forge.stored-artifact-inventory.v1+json",
    "application/vnd.echelon-forge.rollout-qualification-record.v1+json",
    "application/vnd.echelon-forge.kill-switch-record.v1+json",
    "application/vnd.echelon-forge.qualification-evidence.v1+json",
    "application/vnd.echelon-forge.qualification-proof.v1+octets",
    "application/vnd.echelon-forge.shadow-comparison-receipt.v1+json",
  }),
  "runtime_host": ROLE_MEDIA_TYPES["runtime_host"],
  "runtime_evidence": frozenset().union(*ROLE_MEDIA_TYPES.values()),
  "shadow_observer": ROLE_MEDIA_TYPES["shadow_observer"],
  "crash_reconciler": frozenset({
    "application/vnd.echelon-forge.run-journal-header.v1+json",
    "application/vnd.echelon-forge.run-journal-record.v1+octets",
  }),
}
ROLE_STAT_MEDIA_TYPES = {
  "plan_compiler": frozenset(),
  "release_artifact_pipeline": frozenset({
    "application/vnd.echelon-forge.resolved-composition-plan-envelope.v1+json",
    "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json",
    "application/vnd.echelon-forge.release-package.v1+octets",
    "application/vnd.echelon-forge.release-manifest-envelope.v1+json",
    "application/vnd.echelon-forge.stored-artifact-inventory.v1+json",
  }),
  "release_controller": ROLE_READ_MEDIA_TYPES["release_controller"],
  "runtime_host": ROLE_MEDIA_TYPES["runtime_host"],
  "runtime_evidence": frozenset().union(*ROLE_MEDIA_TYPES.values()),
  "shadow_observer": ROLE_MEDIA_TYPES["shadow_observer"],
  "crash_reconciler": frozenset({
    "application/vnd.echelon-forge.run-journal-header.v1+json",
    "application/vnd.echelon-forge.run-journal-record.v1+octets",
  }),
}
ROLE_STREAM_PREFIXES = {
  "release_controller": ("qualification-rollout:",),
  "runtime_host": ("journal:", "checkpoint:"),
  "crash_reconciler": ("journal:",),
}
AUTHORITY_ENVELOPE_MEDIA_TYPES = {
  "resolved_composition_plan": "application/vnd.echelon-forge.resolved-composition-plan-envelope.v1+json",
  "release_manifest": "application/vnd.echelon-forge.release-manifest-envelope.v1+json",
  "rollout_decision": "application/vnd.echelon-forge.rollout-decision-envelope.v1+json",
  "state_checkpoint": "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json",
  "release_package": "application/vnd.echelon-forge.release-package.v1+octets",
}


class LedgerContractError(RuntimeError):
  """Fail-closed result for storage, compatibility, rollout, or fencing."""


@dataclass(frozen=True, slots=True)
class DurableAck:
  operation: str
  audit_identity: str
  object_identity: str
  version: int
  digest: str
  durable: bool = True


@dataclass(frozen=True, slots=True)
class FenceToken:
  stream_id: str
  writer_id: str
  generation: int


@dataclass(frozen=True, slots=True)
class TerminationProof:
  stream_id: str
  writer_id: str
  generation: int
  observed_exit_sha256: str


@dataclass(frozen=True, slots=True)
class BlobMetadata:
  digest: str
  media_type: str
  size: int
  retention_class: str
  audit_identity: str


@dataclass(frozen=True, slots=True)
class SlotRevision:
  key: str
  version: int
  blob_digest: str
  fence_generation: int
  audit_identity: str


@dataclass(frozen=True, slots=True)
class JournalFrame:
  stream_id: str
  fence_generation: int
  sequence: int
  prior_record_sha256: str
  payload_sha256: str
  payload_size: int
  frame_sha256: str
  frame_checksum: int
  frame_length: int


@dataclass(frozen=True, slots=True)
class JournalRead:
  frames: tuple[JournalFrame, ...]
  terminal_state: str | None
  torn_tail_discarded: bool


@dataclass(frozen=True, slots=True)
class JournalFinalization:
  stream_id: str
  fence_generation: int
  writer_id: str
  last_sequence: int
  terminal_state: str
  last_record_sha256: str
  finalization_sha256: str


@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
  authority_kind: str
  blob_sha256: str
  media_type: str
  size: int
  writer_generation: int
  reader_generation_min: int
  reader_generation_max: int
  state_schema_generation: int
  truth_features: tuple[str, ...]
  topology: str
  rollback_eligible: bool


@dataclass(frozen=True, slots=True)
class StoredArtifactInventory:
  release_id: str
  compatibility_generation: int
  writer_generation: int
  minimum_reader_generation: int
  rollback_deadline: str
  last_reader_deadline: str
  irreversible_write_boundary: str
  eligible_reader_ids: tuple[str, ...]
  artifacts: tuple[ArtifactDescriptor, ...]


@dataclass(frozen=True, slots=True)
class ReaderDeployment:
  reader_id: str
  generation: int
  eligible: bool
  healthy: bool
  supported_generations: tuple[int, ...]
  admitted_artifact_digests: tuple[str, ...] = ()
  supported_state_schema_generation: int = 0
  supported_features: tuple[str, ...] = ()
  supported_topologies: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class QualificationEvidence:
  reader_deployments: tuple[ReaderDeployment, ...] = ()
  shadow_receipt_sha256: str = ""
  storage_restore_drill_sha256: str = ""
  rollback_drill_sha256: str = ""
  cutover_drill_sha256: str = ""
  adoption_health_sha256: str = ""
  inventory_disposition_sha256: str = ""
  rollback_receipt_sha256: str = ""
  deadline_elapsed: bool = False
  no_unresolved_high_findings: bool = False


@dataclass(frozen=True, slots=True)
class CanaryHealth:
  wrong_epoch_results: int = 0
  duplicate_publications: int = 0
  stale_references_accepted: int = 0
  episode_double_resets: int = 0
  result_identity_mismatches: int = 0
  receipt_integrity_failures: int = 0
  plan_byte_divergences: int = 0
  hidden_defaults: int = 0
  unsupported_reader_acceptances: int = 0
  unsupported_topology_acceptances: int = 0
  cpu_exact_mismatches: int = 0
  security_bypasses: int = 0
  drain_deadline_breaches: int = 0
  unresolved_quarantines: int = 0
  resource_growth_over_budget: int = 0
  lifecycle_slo_breaches: int = 0
  artifact_slo_breaches: int = 0


@dataclass(slots=True)
class _JournalState:
  fence_generation: int
  writer_id: str
  header_blob_sha256: str
  frames: list[JournalFrame]
  finalization: JournalFinalization | None = None
  torn_tail: bytes | None = None


_RECOVERY_FINALIZE_GRANT = object()


def _sha256(payload: bytes) -> str:
  return hashlib.sha256(payload).hexdigest()


def _require_identity(value: str, field: str) -> None:
  if not isinstance(value, str) or not value or len(value) > 128:
    raise LedgerContractError(f"{field} must be a non-empty bounded identity")


def _require_sha256(value: str, field: str) -> None:
  if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
    raise LedgerContractError(f"{field} must be lowercase SHA-256")


def _require_exact_fields(value: Mapping[str, Any], fields: set[str], context: str) -> None:
  if not isinstance(value, Mapping) or set(value) != fields:
    raise LedgerContractError(f"{context} fields are not exact")


class SimulatedArtifactLedger:
  """Deterministic in-memory model of the minimum ledger contract.

  A `DurableAck` means committed to this model only.  It is not production
  durability evidence, and the class exposes no runtime execution authority.
  """

  def __init__(self) -> None:
    self._blobs: dict[str, tuple[bytes, BlobMetadata]] = {}
    self._unavailable_blobs: set[str] = set()
    self._slots: dict[str, SlotRevision] = {}
    self._fence_generations: dict[str, int] = {}
    self._active_writers: dict[str, str] = {}
    self._confirmed_termination_proofs: dict[tuple[str, str, int], str] = {}
    self._tombstones: set[tuple[str, str, int]] = set()
    self._journals: dict[str, _JournalState] = {}
    self._audit: list[dict[str, Any]] = []

  def _authorize(self, role: str, permission: str) -> None:
    if permission not in ROLE_PERMISSIONS.get(role, frozenset()):
      raise LedgerContractError(f"role {role!r} lacks {permission!r}")

  def _audit_record(self, operation: str, role: str, audit_identity: str, object_identity: str, version: int, digest: str) -> None:
    _require_identity(audit_identity, "audit_identity")
    self._audit.append({
      "sequence": len(self._audit),
      "operation": operation,
      "role": role,
      "audit_identity": audit_identity,
      "object_identity": object_identity,
      "version": version,
      "digest": digest,
    })

  def put_blob(
    self,
    *,
    role: str,
    payload: bytes,
    media_type: str,
    expected_sha256: str,
    retention_class: str,
    audit_identity: str,
  ) -> DurableAck:
    _require_identity(audit_identity, "audit_identity")
    self._authorize(role, "blob.put")
    if not isinstance(payload, bytes) or not payload:
      raise LedgerContractError("blob payload must be non-empty bytes")
    _require_identity(media_type, "media_type")
    _require_sha256(expected_sha256, "expected_sha256")
    if retention_class not in RETENTION_CLASSES:
      raise LedgerContractError("retention_class is not admitted")
    if media_type not in ROLE_MEDIA_TYPES.get(role, frozenset()):
      raise LedgerContractError(f"role {role!r} cannot store media type {media_type!r}")
    if _sha256(payload) != expected_sha256:
      raise LedgerContractError("blob digest does not match bytes")
    metadata = BlobMetadata(expected_sha256, media_type, len(payload), retention_class, audit_identity)
    existing = self._blobs.get(expected_sha256)
    if existing is not None:
      existing_payload, existing_metadata = existing
      if (existing_payload != payload or existing_metadata.media_type != media_type or
          existing_metadata.size != len(payload) or existing_metadata.retention_class != retention_class):
        raise LedgerContractError("content-addressed blob metadata conflict")
    else:
      self._blobs[expected_sha256] = (payload, metadata)
    self._audit_record("blob.put", role, audit_identity, expected_sha256, 1, expected_sha256)
    return DurableAck("blob.put", audit_identity, expected_sha256, 1, expected_sha256)

  def get_blob(self, *, role: str, digest: str) -> tuple[bytes, BlobMetadata]:
    self._authorize(role, "blob.get")
    _require_sha256(digest, "digest")
    if digest in self._unavailable_blobs or digest not in self._blobs:
      raise LedgerContractError("blob is unavailable")
    payload, metadata = self._blobs[digest]
    if metadata.media_type not in ROLE_READ_MEDIA_TYPES.get(role, frozenset()):
      permission = "checkpoint.read" if metadata.media_type == "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json" else "journal.read"
      raise LedgerContractError(f"role {role!r} lacks '{permission}' for media type {metadata.media_type!r}")
    if _sha256(payload) != digest or len(payload) != metadata.size:
      raise LedgerContractError("stored blob failed hash/size verification")
    return payload, metadata

  def stat_blob(self, *, role: str, digest: str) -> BlobMetadata:
    self._authorize(role, "blob.stat")
    _require_sha256(digest, "digest")
    if digest in self._unavailable_blobs or digest not in self._blobs:
      raise LedgerContractError("blob is unavailable")
    payload, metadata = self._blobs[digest]
    if metadata.media_type not in ROLE_STAT_MEDIA_TYPES.get(role, frozenset()):
      raise LedgerContractError(f"role {role!r} lacks metadata access for media type {metadata.media_type!r}")
    if _sha256(payload) != digest or len(payload) != metadata.size:
      raise LedgerContractError("stored blob failed hash/size verification")
    return metadata

  def acquire_fence(
    self,
    *,
    role: str,
    stream_id: str,
    writer_id: str,
    expected_generation: int,
    audit_identity: str,
  ) -> FenceToken:
    _require_identity(audit_identity, "audit_identity")
    self._authorize(role, "fence.acquire")
    _require_identity(stream_id, "stream_id")
    _require_identity(writer_id, "writer_id")
    current = self._fence_generations.get(stream_id, 0)
    if not stream_id.startswith(ROLE_STREAM_PREFIXES.get(role, ())):
      raise LedgerContractError("role cannot acquire a fence for this stream namespace")
    if expected_generation != current:
      raise LedgerContractError("fence generation compare-and-swap failed")
    active = self._active_writers.get(stream_id)
    if active is not None:
      raise LedgerContractError("prior writer must be tombstoned before takeover")
    generation = current + 1
    self._fence_generations[stream_id] = generation
    self._active_writers[stream_id] = writer_id
    self._audit_record("fence.acquire", role, audit_identity, stream_id, generation, "0" * 64)
    return FenceToken(stream_id, writer_id, generation)

  def confirm_process_terminated(
    self,
    *,
    role: str,
    token: FenceToken,
    observed_exit_sha256: str,
    audit_identity: str,
  ) -> TerminationProof:
    _require_identity(audit_identity, "audit_identity")
    self._authorize(role, "process.confirm_terminated")
    self.assert_fence(token)
    _require_sha256(observed_exit_sha256, "observed_exit_sha256")
    identity = (token.stream_id, token.writer_id, token.generation)
    self._confirmed_termination_proofs[identity] = observed_exit_sha256
    self._audit_record("process.confirm_terminated", role, audit_identity, token.stream_id, token.generation, observed_exit_sha256)
    return TerminationProof(*identity, observed_exit_sha256)

  def tombstone_writer(
    self,
    *,
    role: str,
    token: FenceToken,
    termination_proof: TerminationProof,
    audit_identity: str,
  ) -> DurableAck:
    _require_identity(audit_identity, "audit_identity")
    self._authorize(role, "writer.tombstone")
    self.assert_fence(token)
    identity = (token.stream_id, token.writer_id, token.generation)
    if ((termination_proof.stream_id, termination_proof.writer_id, termination_proof.generation) != identity or
        self._confirmed_termination_proofs.get(identity) != termination_proof.observed_exit_sha256):
      raise LedgerContractError("writer tombstone lacks matching process-termination proof")
    self._tombstones.add(identity)
    self._active_writers.pop(token.stream_id, None)
    self._confirmed_termination_proofs.pop(identity, None)
    self._audit_record("writer.tombstone", role, audit_identity, token.stream_id, token.generation, "0" * 64)
    return DurableAck("writer.tombstone", audit_identity, token.stream_id, token.generation, "0" * 64)

  def assert_fence(self, token: FenceToken) -> None:
    if self._fence_generations.get(token.stream_id) != token.generation or self._active_writers.get(token.stream_id) != token.writer_id:
      raise LedgerContractError("stale or inactive writer fence")
    if (token.stream_id, token.writer_id, token.generation) in self._tombstones:
      raise LedgerContractError("writer fence is tombstoned")

  @staticmethod
  def _slot_contract(role: str, key: str) -> str:
    if role == "release_controller" and key.startswith("qualification-rollout:"):
      return "application/vnd.echelon-forge.rollout-qualification-record.v1+json"
    if role == "release_controller" and key.startswith("qualification-kill:"):
      return "application/vnd.echelon-forge.kill-switch-record.v1+json"
    if role == "runtime_host" and key.startswith("checkpoint:"):
      return "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json"
    raise LedgerContractError("role cannot write this slot namespace")

  @staticmethod
  def _slot_fence_stream(key: str) -> str:
    if key.startswith("qualification-kill:"):
      return f"qualification-rollout:{key.removeprefix('qualification-kill:')}"
    return key

  def _validate_slot_target(self, *, role: str, key: str, blob_digest: str, token: FenceToken) -> None:
    _require_identity(key, "key")
    _require_sha256(blob_digest, "blob_digest")
    if self._slot_fence_stream(key) != token.stream_id:
      raise LedgerContractError("slot key must belong to its fence stream")
    expected_media = self._slot_contract(role, key)
    stored = self._blobs.get(blob_digest)
    if stored is None:
      raise LedgerContractError("slot cannot reference an absent blob")
    if stored[1].media_type != expected_media:
      raise LedgerContractError("slot target media type does not match its namespace")
    try:
      if expected_media == "application/vnd.echelon-forge.rollout-qualification-record.v1+json":
        qualification = parse_rollout_qualification_bytes(stored[0])
        if key != f"qualification-rollout:{qualification['candidate_rollout_decision']['payload']['release_id']}":
          raise LedgerContractError("qualification slot release identity differs from its namespace")
      elif expected_media == "application/vnd.echelon-forge.kill-switch-record.v1+json":
        kill = parse_kill_switch_bytes(stored[0])
        if key != f"qualification-kill:{kill['release_id']}":
          raise LedgerContractError("kill-switch slot release identity differs from its namespace")
      else:
        checkpoint = validate_authority_envelope(parse_canonical_json_bytes(stored[0]))
        if checkpoint["payload"]["authority_kind"] != "state_checkpoint" or key != f"checkpoint:{checkpoint['payload']['checkpoint_id']}":
          raise LedgerContractError("checkpoint slot authority identity differs from its namespace")
    except (AuthorityContractError, LedgerContractError, ValueError, UnicodeError) as error:
      raise LedgerContractError("slot target schema/authority is invalid") from error

  def conditional_create(
    self,
    *,
    role: str,
    key: str,
    blob_digest: str,
    token: FenceToken,
    audit_identity: str,
  ) -> DurableAck:
    _require_identity(audit_identity, "audit_identity")
    self._authorize(role, "slot.write")
    self.assert_fence(token)
    self._validate_slot_target(role=role, key=key, blob_digest=blob_digest, token=token)
    if key in self._slots:
      raise LedgerContractError("conditional create requires an absent key")
    revision = SlotRevision(key, 1, blob_digest, token.generation, audit_identity)
    self._slots[key] = revision
    self._audit_record("slot.create", role, audit_identity, key, 1, blob_digest)
    return DurableAck("slot.create", audit_identity, key, 1, blob_digest)

  def compare_and_swap(
    self,
    *,
    role: str,
    key: str,
    expected_version: int,
    blob_digest: str,
    token: FenceToken,
    audit_identity: str,
  ) -> DurableAck:
    _require_identity(audit_identity, "audit_identity")
    self._authorize(role, "slot.write")
    self.assert_fence(token)
    self._validate_slot_target(role=role, key=key, blob_digest=blob_digest, token=token)
    current = self._slots.get(key)
    if current is None or current.version != expected_version:
      raise LedgerContractError("slot compare-and-swap version mismatch")
    revision = SlotRevision(key, expected_version + 1, blob_digest, token.generation, audit_identity)
    self._slots[key] = revision
    self._audit_record("slot.cas", role, audit_identity, key, revision.version, blob_digest)
    return DurableAck("slot.cas", audit_identity, key, revision.version, blob_digest)

  def slot(self, *, role: str, key: str) -> SlotRevision:
    if key.startswith("checkpoint:"):
      self._authorize(role, "checkpoint.read")
    else:
      self._authorize(role, "blob.get")
    if key not in self._slots:
      raise LedgerContractError("slot is absent")
    return self._slots[key]

  def persist_checkpoint(
    self,
    *,
    role: str,
    envelope_bytes: bytes,
    expected_slot_version: int,
    token: FenceToken,
    audit_identity: str,
  ) -> tuple[str, DurableAck]:
    """Persist an already finalized checkpoint through a fenced conditional pointer."""

    _require_identity(audit_identity, "audit_identity")
    if role != "runtime_host":
      raise LedgerContractError("checkpoint persistence is runtime_host-only")
    self._authorize(role, "checkpoint.write")
    self.assert_fence(token)
    envelope = parse_canonical_json_bytes(envelope_bytes)
    try:
      normalized = validate_authority_envelope(envelope)
    except AuthorityContractError as error:
      raise LedgerContractError(f"checkpoint envelope rejected: {error}") from error
    payload = normalized["payload"]
    if payload["authority_kind"] != "state_checkpoint":
      raise LedgerContractError("checkpoint persistence requires state-checkpoint authority")
    key = f"checkpoint:{payload['checkpoint_id']}"
    if token.stream_id != key:
      raise LedgerContractError("checkpoint fence stream differs from checkpoint identity")
    current = self._slots.get(key)
    if expected_slot_version != 0:
      raise LedgerContractError("finalized checkpoint identities are immutable and cannot be CAS-rewritten")
    if current is not None:
      raise LedgerContractError("checkpoint conditional create requires an absent key")
    digest = _sha256(envelope_bytes)
    self.put_blob(
      role="runtime_host", payload=envelope_bytes,
      media_type="application/vnd.echelon-forge.state-checkpoint-envelope.v1+json",
      expected_sha256=digest, retention_class="rollback-window", audit_identity=audit_identity,
    )
    ack = self.conditional_create(
      role="runtime_host", key=key, blob_digest=digest, token=token,
      audit_identity=audit_identity,
    )
    return digest, ack

  def read_checkpoint(self, *, role: str, checkpoint_id: str) -> dict[str, Any]:
    self._authorize(role, "checkpoint.read")
    key = f"checkpoint:{checkpoint_id}"
    revision = self._slots.get(key)
    if revision is None:
      raise LedgerContractError("checkpoint slot is absent")
    payload, metadata = self.get_blob(role=role, digest=revision.blob_digest)
    if metadata.media_type != "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json":
      raise LedgerContractError("checkpoint slot media type is invalid")
    envelope = parse_canonical_json_bytes(payload)
    try:
      normalized = validate_authority_envelope(envelope)
    except AuthorityContractError as error:
      raise LedgerContractError(f"stored checkpoint rejected: {error}") from error
    if normalized["payload"]["authority_kind"] != "state_checkpoint" or normalized["payload"]["checkpoint_id"] != checkpoint_id:
      raise LedgerContractError("checkpoint slot identity differs from stored authority")
    return normalized

  def open_journal(
    self,
    *,
    role: str,
    journal_id: str,
    header_blob_sha256: str,
    token: FenceToken,
    audit_identity: str,
  ) -> DurableAck:
    _require_identity(audit_identity, "audit_identity")
    self._authorize(role, "journal.write")
    if role != "runtime_host":
      raise LedgerContractError("only runtime_host may commit an initial journal header")
    self.assert_fence(token)
    if token.stream_id != f"journal:{journal_id}":
      raise LedgerContractError("journal fence stream mismatch")
    if journal_id in self._journals:
      raise LedgerContractError("journal header already committed")
    header = self._blobs.get(header_blob_sha256)
    if header is None:
      raise LedgerContractError("journal header blob is absent")
    if header[1].media_type != "application/vnd.echelon-forge.run-journal-header.v1+json":
      raise LedgerContractError("journal header media type is invalid")
    try:
      header_document = parse_canonical_json_bytes(header[0])
    except (AuthorityContractError, ValueError, UnicodeError) as error:
      raise LedgerContractError("journal header is not canonical JSON") from error
    if not isinstance(header_document, Mapping) or header_document.get("run_id") != journal_id:
      raise LedgerContractError("journal header run identity differs from journal stream")
    self._journals[journal_id] = _JournalState(token.generation, token.writer_id, header_blob_sha256, [])
    self._audit_record("journal.open", role, audit_identity, journal_id, 0, header_blob_sha256)
    return DurableAck("journal.open", audit_identity, journal_id, 0, header_blob_sha256)

  def append_journal(
    self,
    *,
    role: str,
    journal_id: str,
    payload: bytes,
    expected_sequence: int,
    token: FenceToken,
    audit_identity: str,
  ) -> DurableAck:
    _require_identity(audit_identity, "audit_identity")
    self._authorize(role, "journal.write")
    if role != "runtime_host":
      raise LedgerContractError("journal append is runtime_host-only")
    self.assert_fence(token)
    state = self._journals.get(journal_id)
    if state is None or token.stream_id != f"journal:{journal_id}":
      raise LedgerContractError("journal is absent or fence stream mismatches")
    if state.finalization is not None:
      raise LedgerContractError("finalized journal cannot be appended")
    if not isinstance(payload, bytes) or not payload:
      raise LedgerContractError("journal payload must be non-empty bytes")
    if state.fence_generation != token.generation or state.writer_id != token.writer_id:
      raise LedgerContractError("journal writer fence is stale")
    if expected_sequence != len(state.frames):
      raise LedgerContractError("journal append sequence mismatch")
    payload_sha = _sha256(payload)
    self.put_blob(
      role=role,
      payload=payload,
      media_type="application/vnd.echelon-forge.run-journal-record.v1+octets",
      expected_sha256=payload_sha,
      retention_class="run-retained",
      audit_identity=audit_identity,
    )
    prior = state.frames[-1].frame_sha256 if state.frames else state.header_blob_sha256
    frame_body = canonical_json_bytes({
      "fence_generation": token.generation,
      "payload_sha256": payload_sha,
      "payload_size": len(payload),
      "prior_record_sha256": prior,
      "sequence": expected_sequence,
      "stream_id": token.stream_id,
    })
    frame_sha = _sha256(frame_body)
    frame = JournalFrame(
      token.stream_id, token.generation, expected_sequence, prior, payload_sha,
      len(payload), frame_sha, zlib.crc32(frame_body), len(frame_body) + 4,
    )
    state.frames.append(frame)
    self._audit_record("journal.append", role, audit_identity, journal_id, expected_sequence, frame_sha)
    return DurableAck("journal.append", audit_identity, journal_id, expected_sequence, frame_sha)

  def finalize_journal(
    self,
    *,
    role: str,
    journal_id: str,
    terminal_state: str,
    expected_last_sequence: int,
    token: FenceToken,
    audit_identity: str,
  ) -> DurableAck:
    _require_identity(audit_identity, "audit_identity")
    if role != "runtime_host":
      raise LedgerContractError("generic journal finalization is runtime_host-only; recovery must use reconcile_crashed_journal")
    return self._finalize_journal(
      role=role,
      journal_id=journal_id,
      terminal_state=terminal_state,
      expected_last_sequence=expected_last_sequence,
      token=token,
      audit_identity=audit_identity,
    )

  def _finalize_journal(
    self,
    *,
    role: str,
    journal_id: str,
    terminal_state: str,
    expected_last_sequence: int,
    token: FenceToken,
    audit_identity: str,
    recovery_grant: object | None = None,
  ) -> DurableAck:
    self._authorize(role, "journal.write")
    self.assert_fence(token)
    state = self._journals.get(journal_id)
    if state is None or token.stream_id != f"journal:{journal_id}":
      raise LedgerContractError("journal is absent or fence stream mismatches")
    if state.finalization is not None:
      raise LedgerContractError("journal is already finalized")
    if state.fence_generation != token.generation or state.writer_id != token.writer_id:
      raise LedgerContractError("journal finalizer fence is stale")
    if terminal_state not in TERMINAL_JOURNAL_STATES:
      raise LedgerContractError("journal terminal state is not admitted")
    if role == "crash_reconciler" and (
      recovery_grant is not _RECOVERY_FINALIZE_GRANT or terminal_state not in {"crashed", "incomplete"}
    ):
      raise LedgerContractError("crash reconciler finalization lacks an internal recovery grant")
    if role == "runtime_host" and terminal_state in {"crashed", "incomplete"}:
      raise LedgerContractError("live runtime host cannot self-author crash reconciliation")
    actual_last = len(state.frames) - 1
    if expected_last_sequence != actual_last:
      raise LedgerContractError("journal finalization sequence mismatch")
    last_record = state.frames[-1].frame_sha256 if state.frames else state.header_blob_sha256
    body = canonical_json_bytes({
      "fence_generation": token.generation,
      "last_record_sha256": last_record,
      "last_sequence": actual_last,
      "stream_id": token.stream_id,
      "terminal_state": terminal_state,
      "writer_id": token.writer_id,
    })
    finalization = JournalFinalization(
      token.stream_id, token.generation, token.writer_id, actual_last,
      terminal_state, last_record, _sha256(body),
    )
    state.finalization = finalization
    self._audit_record("journal.finalize", role, audit_identity, journal_id, actual_last, finalization.finalization_sha256)
    return DurableAck("journal.finalize", audit_identity, journal_id, actual_last, finalization.finalization_sha256)

  def reconcile_crashed_journal(
    self,
    *,
    role: str,
    journal_id: str,
    payload: bytes,
    terminal_state: str,
    token: FenceToken,
    audit_identity: str,
  ) -> DurableAck:
    """Take over only after a durable prior-writer tombstone and finalize once."""

    _require_identity(audit_identity, "audit_identity")
    if role != "crash_reconciler":
      raise LedgerContractError("crash reconciliation is crash_reconciler-only")
    self._authorize(role, "journal.write")
    self.assert_fence(token)
    state = self._journals.get(journal_id)
    if state is None or state.finalization is not None or token.stream_id != f"journal:{journal_id}":
      raise LedgerContractError("journal is absent, final, or has the wrong recovery stream")
    if terminal_state not in {"crashed", "incomplete"}:
      raise LedgerContractError("crash reconciliation may finalize only crashed/incomplete")
    prior_identity = (token.stream_id, state.writer_id, state.fence_generation)
    if prior_identity not in self._tombstones or token.generation <= state.fence_generation:
      raise LedgerContractError("crash reconciliation requires a newer fence and prior-writer tombstone")
    if not isinstance(payload, bytes) or not payload:
      raise LedgerContractError("journal payload must be non-empty bytes")
    payload_sha = _sha256(payload)
    prior = state.frames[-1].frame_sha256 if state.frames else state.header_blob_sha256
    sequence = len(state.frames)
    frame_body = canonical_json_bytes({
      "fence_generation": token.generation,
      "payload_sha256": payload_sha,
      "payload_size": len(payload),
      "prior_record_sha256": prior,
      "sequence": sequence,
      "stream_id": token.stream_id,
    })
    frame = JournalFrame(
      token.stream_id, token.generation, sequence, prior, payload_sha, len(payload),
      _sha256(frame_body), zlib.crc32(frame_body), len(frame_body) + 4,
    )
    finalization_body = canonical_json_bytes({
      "fence_generation": token.generation,
      "last_record_sha256": frame.frame_sha256,
      "last_sequence": sequence,
      "stream_id": token.stream_id,
      "terminal_state": terminal_state,
      "writer_id": token.writer_id,
    })
    finalization = JournalFinalization(
      token.stream_id, token.generation, token.writer_id, sequence, terminal_state,
      frame.frame_sha256, _sha256(finalization_body),
    )
    self.put_blob(
      role="crash_reconciler", payload=payload,
      media_type="application/vnd.echelon-forge.run-journal-record.v1+octets",
      expected_sha256=payload_sha, retention_class="run-retained", audit_identity=audit_identity,
    )
    state.fence_generation = token.generation
    state.writer_id = token.writer_id
    state.frames.append(frame)
    state.finalization = finalization
    self._audit_record("journal.append", "crash_reconciler", audit_identity, journal_id, sequence, frame.frame_sha256)
    self._audit_record("journal.finalize", "crash_reconciler", audit_identity, journal_id, sequence, finalization.finalization_sha256)
    return DurableAck("journal.finalize", audit_identity, journal_id, sequence, finalization.finalization_sha256)

  def read_journal(self, *, role: str, journal_id: str) -> JournalRead:
    self._authorize(role, "journal.read")
    state = self._journals.get(journal_id)
    if state is None:
      raise LedgerContractError("journal is absent")
    header = self._blobs.get(state.header_blob_sha256)
    if header is None or header[1].media_type != "application/vnd.echelon-forge.run-journal-header.v1+json":
      raise LedgerContractError("journal header media type integrity failure")
    try:
      header_document = parse_canonical_json_bytes(header[0])
    except (AuthorityContractError, ValueError, UnicodeError) as error:
      raise LedgerContractError("journal header is not canonical JSON") from error
    if not isinstance(header_document, Mapping) or header_document.get("run_id") != journal_id:
      raise LedgerContractError("journal header run identity differs from journal stream")
    prior = state.header_blob_sha256
    previous_fence = 0
    for sequence, frame in enumerate(state.frames):
      body = canonical_json_bytes({
        "fence_generation": frame.fence_generation,
        "payload_sha256": frame.payload_sha256,
        "payload_size": frame.payload_size,
        "prior_record_sha256": frame.prior_record_sha256,
        "sequence": frame.sequence,
        "stream_id": frame.stream_id,
      })
      blob = self._blobs.get(frame.payload_sha256)
      if (frame.sequence != sequence or frame.prior_record_sha256 != prior or frame.stream_id != f"journal:{journal_id}" or
          frame.fence_generation < previous_fence or frame.fence_generation > state.fence_generation or
          blob is None or blob[1].media_type != "application/vnd.echelon-forge.run-journal-record.v1+octets" or
          len(blob[0]) != frame.payload_size or _sha256(blob[0]) != frame.payload_sha256 or
          frame.frame_length != len(body) + 4 or _sha256(body) != frame.frame_sha256 or
          zlib.crc32(body) != frame.frame_checksum):
        raise LedgerContractError("journal frame integrity failure")
      prior = frame.frame_sha256
      previous_fence = frame.fence_generation
    if state.finalization is not None:
      finalization = state.finalization
      last_record = state.frames[-1].frame_sha256 if state.frames else state.header_blob_sha256
      body = canonical_json_bytes({
        "fence_generation": finalization.fence_generation,
        "last_record_sha256": finalization.last_record_sha256,
        "last_sequence": finalization.last_sequence,
        "stream_id": finalization.stream_id,
        "terminal_state": finalization.terminal_state,
        "writer_id": finalization.writer_id,
      })
      if (finalization.stream_id != f"journal:{journal_id}" or
          finalization.fence_generation != state.fence_generation or
          finalization.writer_id != state.writer_id or
          finalization.last_sequence != len(state.frames) - 1 or
          finalization.terminal_state not in TERMINAL_JOURNAL_STATES or
          finalization.last_record_sha256 != last_record or
          finalization.finalization_sha256 != _sha256(body)):
        raise LedgerContractError("journal finalization integrity failure")
    terminal_state = state.finalization.terminal_state if state.finalization is not None else None
    return JournalRead(tuple(state.frames), terminal_state, state.torn_tail is not None)

  def audit_log(self, *, role: str) -> tuple[dict[str, Any], ...]:
    self._authorize(role, "audit.read")
    return tuple(dict(record) for record in self._audit)

  def export_snapshot(self, *, role: str) -> bytes:
    if role != "runtime_evidence":
      raise LedgerContractError("snapshot export is runtime_evidence-only")
    self._authorize(role, "audit.read")
    document = {
      "schema_version": "echelon_forge.simulated_artifact_ledger_snapshot.v1",
      "blobs": [{
        "payload_base64": base64.b64encode(payload).decode("ascii"),
        "metadata": asdict(metadata),
      } for _, (payload, metadata) in sorted(self._blobs.items())],
      "slots": [asdict(value) for _, value in sorted(self._slots.items())],
      "fence_generations": dict(sorted(self._fence_generations.items())),
      "active_writers": dict(sorted(self._active_writers.items())),
      "confirmed_termination_proofs": [
        [*identity, digest] for identity, digest in sorted(self._confirmed_termination_proofs.items())
      ],
      "tombstones": [list(value) for value in sorted(self._tombstones)],
      "journals": [{
        "journal_id": journal_id,
        "fence_generation": state.fence_generation,
        "writer_id": state.writer_id,
        "header_blob_sha256": state.header_blob_sha256,
        "frames": [asdict(frame) for frame in state.frames],
        "finalization": asdict(state.finalization) if state.finalization is not None else None,
      } for journal_id, state in sorted(self._journals.items())],
      "audit": self._audit,
      "audit_sha256": _sha256(canonical_json_bytes(self._audit)),
    }
    return canonical_json_bytes(document)

  @classmethod
  def restore_snapshot(cls, snapshot: bytes) -> SimulatedArtifactLedger:
    document = parse_canonical_json_bytes(snapshot)
    _require_exact_fields(document, {
      "schema_version", "blobs", "slots", "fence_generations", "active_writers",
      "confirmed_termination_proofs", "tombstones", "journals", "audit", "audit_sha256",
    }, "snapshot")
    if document.get("schema_version") != "echelon_forge.simulated_artifact_ledger_snapshot.v1":
      raise LedgerContractError("snapshot schema version mismatch")
    _require_sha256(document["audit_sha256"], "snapshot audit_sha256")
    if _sha256(canonical_json_bytes(document["audit"])) != document["audit_sha256"]:
      raise LedgerContractError("snapshot audit digest mismatch")
    ledger = cls()
    allowed_media_types = frozenset().union(*ROLE_MEDIA_TYPES.values())
    seen_blobs: set[str] = set()
    for item in document["blobs"]:
      _require_exact_fields(item, {"payload_base64", "metadata"}, "snapshot blob")
      _require_exact_fields(item["metadata"], {"digest", "media_type", "size", "retention_class", "audit_identity"}, "snapshot blob metadata")
      metadata = BlobMetadata(**item["metadata"])
      payload = base64.b64decode(item["payload_base64"], validate=True)
      if (metadata.digest in seen_blobs or _sha256(payload) != metadata.digest or len(payload) != metadata.size or
          metadata.media_type not in allowed_media_types or metadata.retention_class not in RETENTION_CLASSES):
        raise LedgerContractError("snapshot blob integrity failure")
      if (metadata.media_type in {
          "application/vnd.echelon-forge.run-journal-header.v1+json",
          "application/vnd.echelon-forge.run-journal-record.v1+octets",
        } and metadata.retention_class != "run-retained"):
        raise LedgerContractError("snapshot journal retention class is invalid")
      if (metadata.media_type not in {
          "application/vnd.echelon-forge.run-journal-header.v1+json",
          "application/vnd.echelon-forge.run-journal-record.v1+octets",
        } and metadata.retention_class != "rollback-window"):
        raise LedgerContractError("snapshot authority retention class is invalid")
      _require_identity(metadata.audit_identity, "snapshot blob audit_identity")
      seen_blobs.add(metadata.digest)
      ledger._blobs[metadata.digest] = (payload, metadata)
    seen_slots: set[str] = set()
    for item in document["slots"]:
      _require_exact_fields(item, {"key", "version", "blob_digest", "fence_generation", "audit_identity"}, "snapshot slot")
      _require_identity(item["key"], "snapshot slot key")
      _require_sha256(item["blob_digest"], "snapshot slot blob_digest")
      if (not isinstance(item["version"], int) or item["version"] < 1 or
          not isinstance(item["fence_generation"], int) or item["fence_generation"] < 1):
        raise LedgerContractError("snapshot slot version/fence is invalid")
      _require_identity(item["audit_identity"], "snapshot slot audit_identity")
      if item["key"] in seen_slots:
        raise LedgerContractError("snapshot contains duplicate slot identities")
      seen_slots.add(item["key"])
      ledger._slots[item["key"]] = SlotRevision(**item)
    if (not isinstance(document["fence_generations"], Mapping) or
        any(not isinstance(value, int) or value < 1 for value in document["fence_generations"].values())):
      raise LedgerContractError("snapshot fence generations are invalid")
    for stream_id in document["fence_generations"]:
      _require_identity(stream_id, "snapshot fence stream")
      if not stream_id.startswith(("qualification-rollout:", "checkpoint:", "journal:")):
        raise LedgerContractError("snapshot fence stream namespace is invalid")
    ledger._fence_generations = dict(document["fence_generations"])
    if not isinstance(document["active_writers"], Mapping):
      raise LedgerContractError("snapshot active writers are invalid")
    for stream_id, writer_id in document["active_writers"].items():
      _require_identity(stream_id, "snapshot active writer stream")
      _require_identity(writer_id, "snapshot active writer identity")
      if not stream_id.startswith(("qualification-rollout:", "checkpoint:", "journal:")):
        raise LedgerContractError("snapshot active writer stream namespace is invalid")
    ledger._active_writers = dict(document["active_writers"])
    for item in document["confirmed_termination_proofs"]:
      if (not isinstance(item, list) or len(item) != 4 or not isinstance(item[2], int) or item[2] < 1 or
          tuple(item[:3]) in ledger._confirmed_termination_proofs):
        raise LedgerContractError("snapshot termination proof shape is invalid")
      _require_identity(item[0], "snapshot termination stream")
      _require_identity(item[1], "snapshot termination writer")
      _require_sha256(item[3], "snapshot termination proof digest")
      ledger._confirmed_termination_proofs[tuple(item[:3])] = item[3]
    if any(not isinstance(item, list) or len(item) != 3 or not isinstance(item[2], int) or item[2] < 1 for item in document["tombstones"]):
      raise LedgerContractError("snapshot tombstone shape is invalid")
    for item in document["tombstones"]:
      _require_identity(item[0], "snapshot tombstone stream")
      _require_identity(item[1], "snapshot tombstone writer")
    if len({tuple(item) for item in document["tombstones"]}) != len(document["tombstones"]):
      raise LedgerContractError("snapshot contains duplicate tombstones")
    ledger._tombstones = {tuple(item) for item in document["tombstones"]}
    if any(identity in ledger._tombstones for identity in ledger._confirmed_termination_proofs):
      raise LedgerContractError("restored termination proof is already consumed")
    seen_journals: set[str] = set()
    for item in document["journals"]:
      _require_exact_fields(item, {"journal_id", "fence_generation", "writer_id", "header_blob_sha256", "frames", "finalization"}, "snapshot journal")
      _require_identity(item["journal_id"], "snapshot journal_id")
      if not isinstance(item["fence_generation"], int) or item["fence_generation"] < 1:
        raise LedgerContractError("snapshot journal fence generation is invalid")
      _require_identity(item["writer_id"], "snapshot journal writer_id")
      _require_sha256(item["header_blob_sha256"], "snapshot journal header digest")
      if item["journal_id"] in seen_journals:
        raise LedgerContractError("snapshot contains duplicate journal identities")
      seen_journals.add(item["journal_id"])
      for frame in item["frames"]:
        _require_exact_fields(frame, {"stream_id", "fence_generation", "sequence", "prior_record_sha256", "payload_sha256", "payload_size", "frame_sha256", "frame_checksum", "frame_length"}, "snapshot journal frame")
        if (frame["stream_id"] != f"journal:{item['journal_id']}" or
            not isinstance(frame["fence_generation"], int) or frame["fence_generation"] < 1 or
            not isinstance(frame["sequence"], int) or frame["sequence"] < 0 or
            not isinstance(frame["payload_size"], int) or frame["payload_size"] <= 0 or
            not isinstance(frame["frame_checksum"], int) or not isinstance(frame["frame_length"], int) or
            frame["frame_length"] <= 0):
          raise LedgerContractError("snapshot journal frame identity/shape is invalid")
        _require_sha256(frame["prior_record_sha256"], "snapshot journal prior digest")
        _require_sha256(frame["payload_sha256"], "snapshot journal payload digest")
        _require_sha256(frame["frame_sha256"], "snapshot journal frame digest")
      if item["finalization"] is not None:
        _require_exact_fields(item["finalization"], {"stream_id", "fence_generation", "writer_id", "last_sequence", "terminal_state", "last_record_sha256", "finalization_sha256"}, "snapshot journal finalization")
        finalization = item["finalization"]
        if (finalization["stream_id"] != f"journal:{item['journal_id']}" or
            finalization["fence_generation"] < 1 or finalization["fence_generation"] > item["fence_generation"] or
            not isinstance(finalization["last_sequence"], int) or finalization["last_sequence"] < -1):
          raise LedgerContractError("snapshot journal finalization identity/shape is invalid")
        _require_identity(finalization["writer_id"], "snapshot journal finalization writer")
        _require_sha256(finalization["last_record_sha256"], "snapshot journal finalization record digest")
        _require_sha256(finalization["finalization_sha256"], "snapshot journal finalization digest")
      ledger._journals[item["journal_id"]] = _JournalState(
        item["fence_generation"], item["writer_id"], item["header_blob_sha256"],
        [JournalFrame(**frame) for frame in item["frames"]],
        JournalFinalization(**item["finalization"]) if item["finalization"] is not None else None,
      )
    for sequence, record in enumerate(document["audit"]):
      _require_exact_fields(record, {"sequence", "operation", "role", "audit_identity", "object_identity", "version", "digest"}, "snapshot audit record")
      if record["sequence"] != sequence:
        raise LedgerContractError("snapshot audit sequence is not contiguous")
      _require_identity(record["operation"], "snapshot audit operation")
      _require_identity(record["role"], "snapshot audit role")
      _require_identity(record["audit_identity"], "snapshot audit identity")
      _require_identity(record["object_identity"], "snapshot audit object")
      if not isinstance(record["version"], int) or record["version"] < 0:
        raise LedgerContractError("snapshot audit version is invalid")
      _require_sha256(record["digest"], "snapshot audit digest")
    ledger._audit = list(document["audit"])
    for digest, (payload, _) in ledger._blobs.items():
      if _sha256(payload) != digest:
        raise LedgerContractError("restored blob digest mismatch")
    for slot in ledger._slots.values():
      stored = ledger._blobs.get(slot.blob_digest)
      if stored is None:
        raise LedgerContractError("restored slot references an absent blob")
      if slot.key.startswith("qualification-rollout:"):
        expected_media = "application/vnd.echelon-forge.rollout-qualification-record.v1+json"
      elif slot.key.startswith("qualification-kill:"):
        expected_media = "application/vnd.echelon-forge.kill-switch-record.v1+json"
      elif slot.key.startswith("checkpoint:"):
        expected_media = "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json"
      else:
        raise LedgerContractError("restored slot has an unsupported namespace")
      fence_stream = ledger._slot_fence_stream(slot.key)
      if stored[1].media_type != expected_media or slot.fence_generation > ledger._fence_generations.get(fence_stream, 0):
        raise LedgerContractError("restored slot namespace/media/fence mismatch")
      if slot.key.startswith("qualification-rollout:"):
        qualification = parse_rollout_qualification_bytes(stored[0])
        if slot.key != f"qualification-rollout:{qualification['candidate_rollout_decision']['payload']['release_id']}":
          raise LedgerContractError("restored qualification slot release identity mismatch")
      elif slot.key.startswith("qualification-kill:"):
        kill = parse_kill_switch_bytes(stored[0])
        if slot.key != f"qualification-kill:{kill['release_id']}":
          raise LedgerContractError("restored kill-switch slot release identity mismatch")
      else:
        checkpoint = validate_authority_envelope(parse_canonical_json_bytes(stored[0]))
        if (checkpoint["payload"]["authority_kind"] != "state_checkpoint" or
            slot.key != f"checkpoint:{checkpoint['payload']['checkpoint_id']}"):
          raise LedgerContractError("restored checkpoint slot schema/identity mismatch")
    for stream_id, writer_id in ledger._active_writers.items():
      if ledger._fence_generations.get(stream_id, 0) < 1 or not writer_id or not stream_id.startswith(("qualification-rollout:", "checkpoint:", "journal:")):
        raise LedgerContractError("restored active writer/fence identity mismatch")
    for journal_id, state in ledger._journals.items():
      header = ledger._blobs.get(state.header_blob_sha256)
      if (header is None or header[1].media_type != "application/vnd.echelon-forge.run-journal-header.v1+json" or
          state.fence_generation > ledger._fence_generations.get(f"journal:{journal_id}", 0)):
        raise LedgerContractError("restored journal header/terminal state is invalid")
      ledger.read_journal(role="crash_reconciler", journal_id=journal_id)
    return ledger

  # Fault injection is explicit and simulator-only; production APIs must not expose it.
  def inject_torn_tail_for_test(self, journal_id: str, tail: bytes) -> None:
    if journal_id not in self._journals or not tail:
      raise LedgerContractError("torn-tail injection requires an existing journal and bytes")
    self._journals[journal_id].torn_tail = bytes(tail)

  def set_blob_availability_for_test(self, digest: str, *, available: bool) -> None:
    if digest not in self._blobs:
      raise LedgerContractError("availability injection requires an existing blob")
    if available:
      self._unavailable_blobs.discard(digest)
    else:
      self._unavailable_blobs.add(digest)


def inventory_payload(inventory: StoredArtifactInventory) -> dict[str, Any]:
  _require_identity(inventory.release_id, "release_id")
  _require_identity(inventory.rollback_deadline, "rollback_deadline")
  _require_identity(inventory.last_reader_deadline, "last_reader_deadline")
  _require_identity(inventory.irreversible_write_boundary, "irreversible_write_boundary")
  if (not inventory.eligible_reader_ids or
      tuple(sorted(set(inventory.eligible_reader_ids))) != inventory.eligible_reader_ids):
    raise LedgerContractError("inventory eligible reader identities must be non-empty, sorted and unique")
  for reader_id in inventory.eligible_reader_ids:
    _require_identity(reader_id, "eligible_reader_id")
  if (inventory.compatibility_generation < 1 or inventory.writer_generation < 1 or
      inventory.minimum_reader_generation < 1 or inventory.minimum_reader_generation > inventory.compatibility_generation):
    raise LedgerContractError("inventory compatibility/writer/reader generation is invalid")
  admitted_generations = {inventory.compatibility_generation, inventory.compatibility_generation - 1}
  if inventory.writer_generation not in admitted_generations or inventory.minimum_reader_generation not in admitted_generations:
    raise LedgerContractError("inventory writer/minimum reader is outside bounded N/N-1")
  artifacts = [asdict(artifact) for artifact in inventory.artifacts]
  if not artifacts:
    raise LedgerContractError("stored artifact inventory must not be empty")
  identities = [(item["authority_kind"], item["writer_generation"], item["blob_sha256"]) for item in artifacts]
  if identities != sorted(identities) or len(set(identities)) != len(identities):
    raise LedgerContractError("stored artifacts must be sorted and identity-unique")
  kind_generation_identities = [(item["authority_kind"], item["writer_generation"]) for item in artifacts]
  if len(set(kind_generation_identities)) != len(kind_generation_identities):
    raise LedgerContractError("inventory must select one exact artifact per authority kind and generation")
  for item in artifacts:
    _require_sha256(item["blob_sha256"], "artifact.blob_sha256")
    _require_identity(item["authority_kind"], "artifact.authority_kind")
    _require_identity(item["media_type"], "artifact.media_type")
    _require_identity(item["topology"], "artifact.topology")
    if item["authority_kind"] not in AUTHORITY_ENVELOPE_MEDIA_TYPES or item["media_type"] != AUTHORITY_ENVELOPE_MEDIA_TYPES[item["authority_kind"]]:
      raise LedgerContractError("artifact authority kind/media type mismatch")
    if item["topology"] != "in-process":
      raise LedgerContractError("P3-C inventory supports only in-process topology")
    if item["size"] <= 0 or item["writer_generation"] < 0 or item["reader_generation_min"] < 0:
      raise LedgerContractError("stored artifact size/generation is invalid")
    if item["writer_generation"] not in {inventory.compatibility_generation, inventory.compatibility_generation - 1}:
      raise LedgerContractError("stored artifact is outside inventory N/N-1 generations")
    if item["reader_generation_min"] > item["reader_generation_max"]:
      raise LedgerContractError("stored artifact reader window is inverted")
    if (item["reader_generation_min"] < inventory.minimum_reader_generation or
        item["reader_generation_max"] > inventory.compatibility_generation):
      raise LedgerContractError("stored artifact reader window exceeds the bounded inventory N/N-1 range")
    if item["state_schema_generation"] < 1:
      raise LedgerContractError("stored artifact state schema generation is invalid")
    if tuple(item["truth_features"]) != tuple(sorted(set(item["truth_features"]))):
      raise LedgerContractError("truth features must be sorted and unique")
    for feature in item["truth_features"]:
      _require_identity(feature, "artifact.truth_feature")
    if (item["writer_generation"] == inventory.compatibility_generation and
        item["authority_kind"] in {"resolved_composition_plan", "release_package"} and
        not (item["reader_generation_min"] <= inventory.compatibility_generation <= item["reader_generation_max"])):
      raise LedgerContractError("generation-N plan/package must admit the generation-N reader")
    if (item["rollback_eligible"] and item["writer_generation"] == inventory.compatibility_generation - 1 and
        not (item["reader_generation_min"] <= inventory.compatibility_generation - 1 and
             item["reader_generation_max"] >= inventory.compatibility_generation)):
      raise LedgerContractError("N-1 rollback artifacts must remain readable by N-1 and N")
  rollback_kinds = {
    item["authority_kind"] for item in artifacts
    if item["rollback_eligible"] and item["writer_generation"] == inventory.compatibility_generation - 1
  }
  candidate_kinds = {
    item["authority_kind"] for item in artifacts
    if item["writer_generation"] == inventory.compatibility_generation
  }
  if rollback_kinds != {"resolved_composition_plan", "state_checkpoint", "release_package"}:
    raise LedgerContractError("inventory lacks the exact N-1 plan/checkpoint/package rollback set")
  if not {"resolved_composition_plan", "release_package"}.issubset(candidate_kinds):
    raise LedgerContractError("inventory lacks the generation-N plan/package candidate set")
  return {
    "schema_version": INVENTORY_SCHEMA_VERSION,
    "contract_version": LEDGER_CONTRACT_VERSION,
    "release_id": inventory.release_id,
    "compatibility_generation": str(inventory.compatibility_generation),
    "writer_generation": str(inventory.writer_generation),
    "minimum_reader_generation": str(inventory.minimum_reader_generation),
    "rollback_deadline": inventory.rollback_deadline,
    "last_reader_deadline": inventory.last_reader_deadline,
    "irreversible_write_boundary": inventory.irreversible_write_boundary,
    "eligible_reader_ids": list(inventory.eligible_reader_ids),
    "artifacts": [{
      **item,
      "writer_generation": str(item["writer_generation"]),
      "reader_generation_min": str(item["reader_generation_min"]),
      "reader_generation_max": str(item["reader_generation_max"]),
      "state_schema_generation": str(item["state_schema_generation"]),
      "truth_features": list(item["truth_features"]),
    } for item in artifacts],
  }


def store_inventory(
  ledger: SimulatedArtifactLedger,
  inventory: StoredArtifactInventory,
  *,
  audit_identity: str,
) -> tuple[str, DurableAck]:
  for artifact in inventory.artifacts:
    metadata = ledger.stat_blob(role="release_artifact_pipeline", digest=artifact.blob_sha256)
    if (metadata.size != artifact.size or metadata.media_type != artifact.media_type or
        metadata.retention_class != "rollback-window"):
      raise LedgerContractError("inventory artifact metadata differs from stored blob")
  payload = canonical_json_bytes(inventory_payload(inventory))
  digest = _sha256(payload)
  ack = ledger.put_blob(
    role="release_artifact_pipeline",
    payload=payload,
    media_type="application/vnd.echelon-forge.stored-artifact-inventory.v1+json",
    expected_sha256=digest,
    retention_class="rollback-window",
    audit_identity=audit_identity,
  )
  return digest, ack


def validate_release_inventory(
  release_envelope: Mapping[str, Any],
  inventory: StoredArtifactInventory,
  inventory_sha256: str,
) -> dict[str, Any]:
  release = validate_authority_envelope(release_envelope)["payload"]
  if release["authority_kind"] != "release_manifest":
    raise LedgerContractError("release/inventory binding requires a release authority")
  _require_sha256(inventory_sha256, "inventory_sha256")
  expected_inventory_sha256 = _sha256(canonical_json_bytes(inventory_payload(inventory)))
  if inventory_sha256 != expected_inventory_sha256:
    raise LedgerContractError("inventory digest differs from canonical inventory bytes")
  expected = {
    "release_id": inventory.release_id,
    "compatibility_generation": str(inventory.compatibility_generation),
    "writer_generation": str(inventory.writer_generation),
    "minimum_reader_generation": str(inventory.minimum_reader_generation),
    "rollback_deadline": inventory.rollback_deadline,
    "last_reader_deadline": inventory.last_reader_deadline,
    "irreversible_write_boundary": inventory.irreversible_write_boundary,
    "stored_artifact_inventory_sha256": inventory_sha256,
    "reader_generation_min": str(inventory.compatibility_generation - 1),
    "reader_generation_max": str(inventory.compatibility_generation),
  }
  for field, value in expected.items():
    if release[field] != value:
      raise LedgerContractError(f"release manifest differs from stored inventory at {field}")
  state_schema_generations = {artifact.state_schema_generation for artifact in inventory.artifacts}
  if state_schema_generations != {int(release["state_schema_generation"])}:
    raise LedgerContractError("release state schema generation differs from stored inventory")
  candidate_packages = {
    artifact.blob_sha256 for artifact in inventory.artifacts
    if artifact.authority_kind == "release_package" and
    artifact.writer_generation == inventory.compatibility_generation and not artifact.rollback_eligible
  }
  package_set = {item["sha256"] for item in release["package_set"]}
  if package_set != candidate_packages:
    raise LedgerContractError("release package set differs from generation-N stored package")
  return release


def validate_release_inventory_binding(
  release_envelope: Mapping[str, Any],
  rollout_envelope: Mapping[str, Any],
  inventory: StoredArtifactInventory,
  inventory_sha256: str,
) -> None:
  release = validate_release_inventory(release_envelope, inventory, inventory_sha256)
  rollout = validate_authority_envelope(rollout_envelope)["payload"]
  if rollout["authority_kind"] != "rollout_decision":
    raise LedgerContractError("release/inventory binding requires a rollout authority")
  if rollout["release_id"] != release["release_id"] or rollout["manifest_sha256"] != release_envelope["payload_sha256"]:
    raise LedgerContractError("rollout decision differs from release authority")
  if rollout["irreversible_write_boundary"] != release["irreversible_write_boundary"]:
    raise LedgerContractError("rollout/release irreversible-write boundary mismatch")


class CompatibilityReader:
  def __init__(self, *, generation: int, supported_state_schema_generation: int, supported_features: Iterable[str], supported_topologies: Iterable[str] = ("in-process",)) -> None:
    if generation < 1 or supported_state_schema_generation < 1:
      raise LedgerContractError("reader and state-schema generations must be positive")
    self.generation = generation
    self.supported_state_schema_generation = supported_state_schema_generation
    self.supported_features = frozenset(supported_features)
    self.supported_topologies = frozenset(supported_topologies)

  def admit_authority(self, descriptor: ArtifactDescriptor, envelope_bytes: bytes) -> dict[str, Any]:
    if descriptor.authority_kind == "release_package":
      raise LedgerContractError("release packages require package admission, not authority-envelope admission")
    if _sha256(envelope_bytes) != descriptor.blob_sha256 or len(envelope_bytes) != descriptor.size:
      raise LedgerContractError("stored authority bytes differ from inventory")
    if descriptor.writer_generation not in {self.generation, self.generation - 1}:
      raise LedgerContractError("stored authority is outside the bounded N/N-1 window")
    if not (descriptor.reader_generation_min <= self.generation <= descriptor.reader_generation_max):
      raise LedgerContractError("reader generation is outside the artifact window")
    if descriptor.state_schema_generation > self.supported_state_schema_generation:
      raise LedgerContractError("state schema generation is unsupported")
    unknown = set(descriptor.truth_features) - self.supported_features
    if unknown:
      raise LedgerContractError(f"unknown truth-affecting features: {sorted(unknown)}")
    if descriptor.topology not in self.supported_topologies:
      raise LedgerContractError("artifact topology is unsupported")
    if descriptor.media_type != AUTHORITY_ENVELOPE_MEDIA_TYPES.get(descriptor.authority_kind):
      raise LedgerContractError("artifact media type does not match authority kind")
    envelope = parse_canonical_json_bytes(envelope_bytes)
    try:
      validate_authority_envelope(envelope)
    except AuthorityContractError as error:
      raise LedgerContractError(f"stored authority envelope rejected: {error}") from error
    payload = envelope["payload"]
    if payload["authority_kind"] != descriptor.authority_kind or int(payload["writer_generation"]) != descriptor.writer_generation:
      raise LedgerContractError("stored authority identity/generation differs from inventory")
    window_fields = {
      "resolved_composition_plan": ("reader_generation_min", "reader_generation_max"),
      "release_manifest": ("reader_generation_min", "reader_generation_max"),
      "rollout_decision": ("plan_reader_generation_min", "plan_reader_generation_max"),
      "state_checkpoint": ("target_reader_generation_min", "target_reader_generation_max"),
    }
    minimum_field, maximum_field = window_fields[descriptor.authority_kind]
    if (int(payload[minimum_field]) != descriptor.reader_generation_min or
        int(payload[maximum_field]) != descriptor.reader_generation_max):
      raise LedgerContractError("stored authority reader window differs from inventory")
    if descriptor.authority_kind in {"release_manifest", "state_checkpoint"} and int(payload["state_schema_generation"]) != descriptor.state_schema_generation:
      raise LedgerContractError("stored authority state schema generation differs from inventory")
    return envelope


def reader_first_ready(
  *,
  current_writer_generation: int,
  target_writer_generation: int,
  readers: Iterable[ReaderDeployment],
  inventory: StoredArtifactInventory,
  available_blob_digests: Iterable[str],
  ledger: SimulatedArtifactLedger,
) -> bool:
  if target_writer_generation != current_writer_generation + 1:
    return False
  if inventory.compatibility_generation != target_writer_generation:
    return False
  eligible = [reader for reader in readers if reader.eligible]
  if (len({reader.reader_id for reader in eligible}) != len(eligible) or
      tuple(sorted(reader.reader_id for reader in eligible)) != inventory.eligible_reader_ids):
    return False
  required_generations = (current_writer_generation, target_writer_generation)
  if not eligible or any(
    not reader.healthy or reader.generation != target_writer_generation or
    tuple(sorted(set(reader.supported_generations))) != required_generations or
    tuple(sorted(set(reader.admitted_artifact_digests))) != reader.admitted_artifact_digests or
    tuple(sorted(set(reader.supported_features))) != reader.supported_features or
    tuple(sorted(set(reader.supported_topologies))) != reader.supported_topologies or
    reader.supported_state_schema_generation < 1
    for reader in eligible
  ):
    return False
  rollback_artifacts = [
    artifact for artifact in inventory.artifacts
    if artifact.rollback_eligible and artifact.writer_generation == current_writer_generation
  ]
  candidate_artifacts = [
    artifact for artifact in inventory.artifacts
    if artifact.writer_generation == target_writer_generation and
    artifact.authority_kind in {"resolved_composition_plan", "release_package"}
  ]
  if ({artifact.authority_kind for artifact in rollback_artifacts} !=
      {"resolved_composition_plan", "state_checkpoint", "release_package"} or
      {artifact.authority_kind for artifact in candidate_artifacts} !=
      {"resolved_composition_plan", "release_package"}):
    return False
  reader_admission_required = {
    artifact.blob_sha256 for artifact in (*rollback_artifacts, *candidate_artifacts)
  }
  available = frozenset(available_blob_digests)
  required_artifacts = (*rollback_artifacts, *candidate_artifacts)
  if inventory.writer_generation != current_writer_generation:
    return False
  for reader in eligible:
    if tuple(sorted(set(reader.admitted_artifact_digests))) != tuple(sorted(reader_admission_required)):
      return False
    compatibility_reader = CompatibilityReader(
      generation=reader.generation,
      supported_state_schema_generation=reader.supported_state_schema_generation,
      supported_features=reader.supported_features,
      supported_topologies=reader.supported_topologies,
    )
    for artifact in (*rollback_artifacts, *candidate_artifacts):
      try:
        payload, metadata = ledger.get_blob(role="runtime_evidence", digest=artifact.blob_sha256)
      except LedgerContractError:
        return False
      if metadata.retention_class != "rollback-window":
        return False
      if artifact.authority_kind == "release_package":
        if (metadata.media_type != artifact.media_type or metadata.size != artifact.size or
            artifact.writer_generation not in reader.supported_generations or
            not (artifact.reader_generation_min <= reader.generation <= artifact.reader_generation_max) or
            artifact.state_schema_generation > reader.supported_state_schema_generation or
            not set(artifact.truth_features).issubset(reader.supported_features) or
            artifact.topology not in reader.supported_topologies):
          return False
      else:
        try:
          compatibility_reader.admit_authority(artifact, payload)
        except LedgerContractError:
          return False
  return all(
    artifact.blob_sha256 in available for artifact in required_artifacts
  )


def shadow_receipt_payload(
  *,
  receipt_id: str,
  plan_sha256: str,
  release_manifest_sha256: str,
  rollout_decision_sha256: str,
  comparison_kind: str,
  outcome: str,
  evidence_sha256: str,
) -> dict[str, Any]:
  for field, value in {
    "receipt_id": receipt_id,
    "comparison_kind": comparison_kind,
    "outcome": outcome,
  }.items():
    _require_identity(value, field)
  for field, value in {
    "plan_sha256": plan_sha256,
    "release_manifest_sha256": release_manifest_sha256,
    "rollout_decision_sha256": rollout_decision_sha256,
    "evidence_sha256": evidence_sha256,
  }.items():
    _require_sha256(value, field)
  if outcome not in {"match", "mismatch", "inconclusive"}:
    raise LedgerContractError("shadow comparison outcome is not admitted")
  return {
    "schema_version": SHADOW_RECEIPT_SCHEMA_VERSION,
    "contract_version": LEDGER_CONTRACT_VERSION,
    "receipt_id": receipt_id,
    "authoritative": False,
    "plan_sha256": plan_sha256,
    "release_manifest_sha256": release_manifest_sha256,
    "rollout_decision_sha256": rollout_decision_sha256,
    "comparison_kind": comparison_kind,
    "outcome": outcome,
    "evidence_sha256": evidence_sha256,
  }


def qualification_evidence_payload(
  *,
  release_id: str,
  evidence_kind: str,
  evidence_sha256: str,
  plan_sha256: str,
  rollout_decision_sha256: str,
) -> dict[str, Any]:
  _require_identity(release_id, "release_id")
  if evidence_kind not in {
    "storage-restore-drill", "rollback-drill", "cutover-drill",
    "adoption-health", "inventory-disposition", "rollback-receipt",
  }:
    raise LedgerContractError("qualification evidence kind is not admitted")
  _require_sha256(evidence_sha256, "evidence_sha256")
  _require_sha256(plan_sha256, "plan_sha256")
  _require_sha256(rollout_decision_sha256, "rollout_decision_sha256")
  return {
    "schema_version": QUALIFICATION_EVIDENCE_SCHEMA_VERSION,
    "contract_version": LEDGER_CONTRACT_VERSION,
    "release_id": release_id,
    "evidence_kind": evidence_kind,
    "outcome": "pass",
    "evidence_sha256": evidence_sha256,
    "plan_sha256": plan_sha256,
    "rollout_decision_sha256": rollout_decision_sha256,
    "authoritative_runtime_mutation": False,
  }


def _qualification_evidence_document(evidence: QualificationEvidence) -> dict[str, Any]:
  digest_fields = (
    "shadow_receipt_sha256", "storage_restore_drill_sha256", "rollback_drill_sha256",
    "cutover_drill_sha256", "adoption_health_sha256", "inventory_disposition_sha256",
    "rollback_receipt_sha256",
  )
  for field in digest_fields:
    value = getattr(evidence, field)
    if value:
      _require_sha256(value, field)
  readers: list[dict[str, Any]] = []
  reader_ids: set[str] = set()
  for reader in evidence.reader_deployments:
    _require_identity(reader.reader_id, "reader_id")
    if reader.reader_id in reader_ids or reader.generation < 1:
      raise LedgerContractError("qualification reader identity/generation is invalid")
    reader_ids.add(reader.reader_id)
    supported = tuple(sorted(set(reader.supported_generations)))
    admitted = tuple(sorted(set(reader.admitted_artifact_digests)))
    features = tuple(sorted(set(reader.supported_features)))
    topologies = tuple(sorted(set(reader.supported_topologies)))
    if (supported != reader.supported_generations or admitted != reader.admitted_artifact_digests or
        features != reader.supported_features or topologies != reader.supported_topologies or
        reader.supported_state_schema_generation < 1):
      raise LedgerContractError("qualification reader capabilities/digests must be positive, sorted and unique")
    for digest in admitted:
      _require_sha256(digest, "reader admitted artifact digest")
    readers.append({
      "reader_id": reader.reader_id,
      "generation": str(reader.generation),
      "eligible": reader.eligible,
      "healthy": reader.healthy,
      "supported_generations": [str(value) for value in supported],
      "admitted_artifact_digests": list(admitted),
      "supported_state_schema_generation": str(reader.supported_state_schema_generation),
      "supported_features": list(features),
      "supported_topologies": list(topologies),
    })
  if [item["reader_id"] for item in readers] != sorted(item["reader_id"] for item in readers):
    raise LedgerContractError("qualification readers must be sorted by identity")
  return {
    "reader_deployments": readers,
    **{field: getattr(evidence, field) for field in digest_fields},
    "deadline_elapsed": evidence.deadline_elapsed,
    "no_unresolved_high_findings": evidence.no_unresolved_high_findings,
  }


def _qualification_evidence_from_document(document: Mapping[str, Any]) -> QualificationEvidence:
  expected = {
    "reader_deployments", "shadow_receipt_sha256", "storage_restore_drill_sha256",
    "rollback_drill_sha256", "cutover_drill_sha256", "adoption_health_sha256",
    "inventory_disposition_sha256", "rollback_receipt_sha256", "deadline_elapsed",
    "no_unresolved_high_findings",
  }
  _require_exact_fields(document, expected, "qualification entry evidence")
  readers: list[ReaderDeployment] = []
  for item in document["reader_deployments"]:
    _require_exact_fields(item, {
      "reader_id", "generation", "eligible", "healthy", "supported_generations",
      "admitted_artifact_digests", "supported_state_schema_generation", "supported_features",
      "supported_topologies",
    }, "qualification reader deployment")
    readers.append(ReaderDeployment(
      item["reader_id"], int(item["generation"]), item["eligible"], item["healthy"],
      tuple(int(value) for value in item["supported_generations"]),
      tuple(item["admitted_artifact_digests"]),
      int(item["supported_state_schema_generation"]),
      tuple(item["supported_features"]),
      tuple(item["supported_topologies"]),
    ))
  evidence = QualificationEvidence(
    reader_deployments=tuple(readers),
    **{field: document[field] for field in expected - {"reader_deployments"}},
  )
  _qualification_evidence_document(evidence)
  return evidence


def rollout_qualification_payload(
  envelope: Mapping[str, Any],
  *,
  inventory_sha256: str,
  release_manifest_blob_sha256: str,
  active_plan_blob_sha256: str,
  evidence: QualificationEvidence,
  admissions_open: bool,
  writer_advancement_frozen: bool,
  kill_switch_record_sha256: str = "",
  predecessor_qualification_sha256: str = "",
) -> dict[str, Any]:
  normalized = validate_authority_envelope(envelope)
  if normalized["payload"]["authority_kind"] != "rollout_decision":
    raise LedgerContractError("qualification record requires a rollout decision candidate")
  for field, digest in {
    "inventory_sha256": inventory_sha256,
    "release_manifest_blob_sha256": release_manifest_blob_sha256,
    "active_plan_blob_sha256": active_plan_blob_sha256,
  }.items():
    _require_sha256(digest, field)
  if kill_switch_record_sha256:
    _require_sha256(kill_switch_record_sha256, "kill_switch_record_sha256")
  if predecessor_qualification_sha256:
    _require_sha256(predecessor_qualification_sha256, "predecessor_qualification_sha256")
  return {
    "schema_version": ROLLOUT_QUALIFICATION_SCHEMA_VERSION,
    "contract_version": LEDGER_CONTRACT_VERSION,
    "authoritative": False,
    "production_activation_enabled": False,
    "inventory_sha256": inventory_sha256,
    "release_manifest_blob_sha256": release_manifest_blob_sha256,
    "active_plan_blob_sha256": active_plan_blob_sha256,
    "admissions_open": admissions_open,
    "writer_advancement_frozen": writer_advancement_frozen,
    "kill_switch_record_sha256": kill_switch_record_sha256,
    "predecessor_qualification_sha256": predecessor_qualification_sha256,
    "entry_evidence": _qualification_evidence_document(evidence),
    "candidate_rollout_decision": normalized,
  }


def parse_rollout_qualification_bytes(payload: bytes) -> dict[str, Any]:
  document = parse_canonical_json_bytes(payload)
  _require_exact_fields(document, {
    "schema_version", "contract_version", "authoritative", "production_activation_enabled",
    "inventory_sha256", "release_manifest_blob_sha256", "active_plan_blob_sha256",
    "admissions_open", "writer_advancement_frozen", "kill_switch_record_sha256",
    "predecessor_qualification_sha256", "entry_evidence", "candidate_rollout_decision",
  }, "rollout qualification record")
  if (document["schema_version"] != ROLLOUT_QUALIFICATION_SCHEMA_VERSION or
      document["contract_version"] != LEDGER_CONTRACT_VERSION or document["authoritative"] is not False or
      document["production_activation_enabled"] is not False or
      not isinstance(document["admissions_open"], bool) or
      not isinstance(document["writer_advancement_frozen"], bool)):
    raise LedgerContractError("rollout qualification record constants are invalid")
  for field in ("inventory_sha256", "release_manifest_blob_sha256", "active_plan_blob_sha256"):
    _require_sha256(document[field], field)
  if document["kill_switch_record_sha256"]:
    _require_sha256(document["kill_switch_record_sha256"], "kill_switch_record_sha256")
  if document["predecessor_qualification_sha256"]:
    _require_sha256(document["predecessor_qualification_sha256"], "predecessor_qualification_sha256")
  normalized = validate_authority_envelope(document["candidate_rollout_decision"])
  if normalized["payload"]["authority_kind"] != "rollout_decision":
    raise LedgerContractError("qualification record embeds a non-rollout authority")
  _qualification_evidence_from_document(document["entry_evidence"])
  return document


def parse_kill_switch_bytes(payload: bytes) -> dict[str, Any]:
  document = parse_canonical_json_bytes(payload)
  _require_exact_fields(document, {
    "schema_version", "contract_version", "release_id", "admissions_open",
    "writer_advancement_frozen", "reasons", "authoritative_runtime_mutation",
  }, "kill switch record")
  if (document["schema_version"] != KILL_SWITCH_SCHEMA_VERSION or
      document["contract_version"] != LEDGER_CONTRACT_VERSION or
      document["admissions_open"] is not False or document["writer_advancement_frozen"] is not True or
      not isinstance(document["reasons"], list) or not document["reasons"] or
      tuple(sorted(set(document["reasons"]))) != tuple(document["reasons"]) or
      document["authoritative_runtime_mutation"] is not False):
    raise LedgerContractError("kill switch record constants are invalid")
  _require_identity(document["release_id"], "kill switch release_id")
  for reason in document["reasons"]:
    _require_identity(reason, "kill switch reason")
  return document


def kill_switch_reasons(health: CanaryHealth) -> tuple[str, ...]:
  reasons: list[str] = []
  for field, count in asdict(health).items():
    if not isinstance(count, int) or count < 0:
      raise LedgerContractError("canary health counters must be non-negative integers")
    if count > 0:
      reasons.append(field)
  return tuple(reasons)


def select_backout_protocol(
  *,
  current_generation: int,
  target_generation: int,
  same_release: bool,
  compatible_checkpoint_available: bool,
  rollback_package_available: bool,
  irreversible_write_boundary: str,
) -> str:
  if irreversible_write_boundary != "none":
    return "stop-or-roll-forward"
  if same_release:
    if target_generation != current_generation:
      raise LedgerContractError("same-release rollback must keep the loaded generation")
    if not compatible_checkpoint_available:
      return "fail-stop"
    return "same-release-checkpoint-recovery"
  if target_generation != current_generation - 1:
    raise LedgerContractError("package rollback is bounded to N to N-1")
  if rollback_package_available:
    return "package-restart-from-checkpoint" if compatible_checkpoint_available else "package-restart-new-run"
  return "fail-stop"


class SimulatedRolloutController:
  """Single-writer qualification state machine; never production authority."""

  def __init__(
    self,
    ledger: SimulatedArtifactLedger,
    *,
    release_id: str,
    token: FenceToken,
    inventory: StoredArtifactInventory,
    inventory_sha256: str,
    release_envelope: Mapping[str, Any],
    plan_envelope: Mapping[str, Any],
  ) -> None:
    if token.stream_id != f"qualification-rollout:{release_id}":
      raise LedgerContractError("rollout controller fence stream mismatch")
    ledger.assert_fence(token)
    if inventory.release_id != release_id:
      raise LedgerContractError("rollout controller inventory release mismatch")
    release = validate_release_inventory(release_envelope, inventory, inventory_sha256)
    plan = validate_authority_envelope(plan_envelope)
    plan_payload = plan["payload"]
    if plan_payload["authority_kind"] != "resolved_composition_plan":
      raise LedgerContractError("rollout controller requires a resolved plan authority")
    plan_bytes = canonical_json_bytes(plan)
    plan_blob_sha256 = _sha256(plan_bytes)
    plan_descriptors = [
      artifact for artifact in inventory.artifacts
      if artifact.authority_kind == "resolved_composition_plan" and artifact.blob_sha256 == plan_blob_sha256
    ]
    if not plan_descriptors:
      raise LedgerContractError("rollout controller plan is absent from stored inventory")
    descriptor = plan_descriptors[0]
    if (descriptor.size != len(plan_bytes) or descriptor.writer_generation != int(plan_payload["writer_generation"]) or
        descriptor.reader_generation_min != int(plan_payload["reader_generation_min"]) or
        descriptor.reader_generation_max != int(plan_payload["reader_generation_max"])):
      raise LedgerContractError("rollout controller plan metadata differs from inventory")
    # Context is not merely an in-memory constructor argument: all authorities
    # must already be durable and hash-addressable before the controller can
    # acquire a qualification slot.
    inventory_payload_bytes = canonical_json_bytes(inventory_payload(inventory))
    try:
      inventory_blob_payload, inventory_blob_metadata = ledger.get_blob(role="release_controller", digest=inventory_sha256)
    except LedgerContractError as error:
      raise LedgerContractError("rollout controller inventory blob is absent") from error
    if inventory_blob_metadata.media_type != "application/vnd.echelon-forge.stored-artifact-inventory.v1+json" or inventory_blob_payload != inventory_payload_bytes:
      raise LedgerContractError("rollout controller inventory blob is absent or mismatched")
    release_bytes = canonical_json_bytes(release_envelope)
    release_blob_sha256 = _sha256(release_bytes)
    try:
      stored_release, release_metadata = ledger.get_blob(role="release_controller", digest=release_blob_sha256)
    except LedgerContractError as error:
      raise LedgerContractError("rollout controller release blob is absent") from error
    if stored_release != release_bytes or release_metadata.media_type != AUTHORITY_ENVELOPE_MEDIA_TYPES["release_manifest"]:
      raise LedgerContractError("rollout controller release blob is mismatched")
    try:
      stored_plan, plan_metadata = ledger.get_blob(role="release_controller", digest=plan_blob_sha256)
    except LedgerContractError as error:
      raise LedgerContractError("rollout controller plan blob is absent") from error
    if stored_plan != plan_bytes or plan_metadata.media_type != AUTHORITY_ENVELOPE_MEDIA_TYPES["resolved_composition_plan"]:
      raise LedgerContractError("rollout controller plan blob is mismatched")
    self._ledger = ledger
    self._release_id = release_id
    self._token = token
    self._inventory = inventory
    self._inventory_sha256 = inventory_sha256
    self._release_envelope = dict(release_envelope)
    self._release_payload_sha256 = release_envelope["payload_sha256"]
    self._release_blob_sha256 = release_blob_sha256
    self._active_plan_envelope = dict(plan)
    self._plan_blob_sha256 = plan_blob_sha256
    self._plan_payload_sha256 = plan["payload_sha256"]
    self._plan_reader_generation_min = plan_payload["reader_generation_min"]
    self._plan_reader_generation_max = plan_payload["reader_generation_max"]
    self._last_decision: dict[str, Any] | None = None
    self._last_evidence = QualificationEvidence()
    self._last_qualification_sha256 = ""
    self._admitted_decision_ids: set[str] = set()
    self._slot_version = 0
    self._early_kill_slot_version = 0
    self._kill_switch_record_sha256 = ""
    self._admissions_open = True
    self._writer_advancement_frozen = False
    slot_key = f"qualification-rollout:{release_id}"
    early_kill_key = f"qualification-kill:{release_id}"
    if early_kill_key in ledger._slots:
      early_kill_revision = ledger.slot(role="release_controller", key=early_kill_key)
      try:
        early_kill_bytes, early_kill_metadata = ledger.get_blob(
          role="release_controller", digest=early_kill_revision.blob_digest,
        )
        early_kill = parse_kill_switch_bytes(early_kill_bytes)
      except LedgerContractError as error:
        raise LedgerContractError("rollout controller durable early kill-switch state is invalid") from error
      if (early_kill_metadata.media_type != "application/vnd.echelon-forge.kill-switch-record.v1+json" or
          early_kill["release_id"] != release_id):
        raise LedgerContractError("rollout controller durable early kill-switch context differs")
      self._early_kill_slot_version = early_kill_revision.version
      self._kill_switch_record_sha256 = early_kill_revision.blob_digest
      self._admissions_open = False
      self._writer_advancement_frozen = True
      if slot_key in ledger._slots:
        raise LedgerContractError("early kill-switch release must not contain rollout decisions")
    if slot_key in ledger._slots:
      revision = ledger.slot(role="release_controller", key=slot_key)
      try:
        qualification_bytes, qualification_metadata = ledger.get_blob(role="release_controller", digest=revision.blob_digest)
        qualification = parse_rollout_qualification_bytes(qualification_bytes)
      except LedgerContractError as error:
        raise LedgerContractError("rollout controller durable qualification state is invalid") from error
      if (qualification_metadata.media_type != "application/vnd.echelon-forge.rollout-qualification-record.v1+json" or
          qualification["inventory_sha256"] != inventory_sha256 or
          qualification["release_manifest_blob_sha256"] != release_blob_sha256 or
          qualification["active_plan_blob_sha256"] != plan_blob_sha256):
        raise LedgerContractError("rollout controller durable context differs from constructor context")
      history_records = [qualification]
      seen_qualification_digests = {revision.blob_digest}
      cursor = qualification["predecessor_qualification_sha256"]
      root_qualification = qualification
      while cursor:
        if cursor in seen_qualification_digests:
          raise LedgerContractError("rollout qualification history contains a cycle")
        seen_qualification_digests.add(cursor)
        historical_bytes, historical_metadata = ledger.get_blob(role="release_controller", digest=cursor)
        historical = parse_rollout_qualification_bytes(historical_bytes)
        if (historical_metadata.media_type != "application/vnd.echelon-forge.rollout-qualification-record.v1+json" or
            historical["inventory_sha256"] != inventory_sha256 or
            historical["release_manifest_blob_sha256"] != release_blob_sha256):
          raise LedgerContractError("rollout qualification history changes immutable context")
        root_qualification = historical
        history_records.append(historical)
        cursor = historical["predecessor_qualification_sha256"]
      root_payload = root_qualification["candidate_rollout_decision"]["payload"]
      if (root_payload["state"] != "prepared" or root_payload["decision_sequence"] != "0" or
          root_payload["predecessor_decision_id"]):
        raise LedgerContractError("rollout qualification history lacks a prepared sequence-zero root")
      candidate = qualification["candidate_rollout_decision"]
      candidate_payload = candidate["payload"]
      if candidate_payload["plan_sha256"] != plan["payload_sha256"]:
        raise LedgerContractError("rollout controller restart must supply the active plan")
      self._last_decision = candidate
      self._last_evidence = _qualification_evidence_from_document(qualification["entry_evidence"])
      self._slot_version = revision.version
      self._last_qualification_sha256 = revision.blob_digest
      self._admissions_open = qualification["admissions_open"]
      self._writer_advancement_frozen = qualification["writer_advancement_frozen"]
      kill_switch_sha256 = qualification["kill_switch_record_sha256"]
      self._kill_switch_record_sha256 = kill_switch_sha256
      if kill_switch_sha256:
        kill_bytes, kill_metadata = ledger.get_blob(role="release_controller", digest=kill_switch_sha256)
        kill = parse_kill_switch_bytes(kill_bytes)
        if (kill_metadata.media_type != "application/vnd.echelon-forge.kill-switch-record.v1+json" or
            kill["release_id"] != release_id or kill["admissions_open"] is not False or
            self._admissions_open or
            not self._writer_advancement_frozen):
          raise LedgerContractError("rollout controller durable kill-switch state is invalid")
      self._validate_durable_qualification_history(tuple(reversed(history_records)))

  @property
  def production_authorized(self) -> bool:
    return False

  @property
  def admissions_open(self) -> bool:
    return self._admissions_open

  def _validate_durable_decision_record(
    self,
    record: Mapping[str, Any],
    previous_record: Mapping[str, Any] | None,
  ) -> tuple[dict[str, Any], bool]:
    candidate = validate_authority_envelope(record["candidate_rollout_decision"])
    payload = candidate["payload"]
    validate_release_inventory_binding(
      self._release_envelope, candidate, self._inventory, self._inventory_sha256,
    )
    if (payload["rollback_deadline"] != self._inventory.rollback_deadline or
        payload["irreversible_write_boundary"] != self._inventory.irreversible_write_boundary):
      raise LedgerContractError("durable qualification decision changes the rollback boundary")
    writer_generation = int(payload["writer_generation"])
    plan_descriptors = [
      artifact for artifact in self._inventory.artifacts
      if artifact.authority_kind == "resolved_composition_plan" and
      artifact.writer_generation == writer_generation and
      artifact.blob_sha256 == record["active_plan_blob_sha256"]
    ]
    if len(plan_descriptors) != 1:
      raise LedgerContractError("durable qualification history lacks one exact active plan")
    plan_descriptor = plan_descriptors[0]
    try:
      plan_bytes, _ = self._ledger.get_blob(role="release_controller", digest=plan_descriptor.blob_sha256)
      plan = CompatibilityReader(
        generation=self._inventory.compatibility_generation,
        supported_state_schema_generation=plan_descriptor.state_schema_generation,
        supported_features=plan_descriptor.truth_features,
        supported_topologies=(plan_descriptor.topology,),
      ).admit_authority(plan_descriptor, plan_bytes)
    except (LedgerContractError, AuthorityContractError) as error:
      raise LedgerContractError("durable qualification active plan is unavailable or incompatible") from error
    if (payload["plan_sha256"] != plan["payload_sha256"] or
        payload["plan_reader_generation_min"] != plan["payload"]["reader_generation_min"] or
        payload["plan_reader_generation_max"] != plan["payload"]["reader_generation_max"]):
      raise LedgerContractError("durable qualification decision differs from its exact active plan")
    if (payload["state"] in {"rollback-window", "stable"} and
        writer_generation != self._inventory.compatibility_generation):
      raise LedgerContractError("durable rollback-window and stable require the generation-N writer")

    checkpoint_descriptor: ArtifactDescriptor | None = None
    if payload["checkpoint_id"]:
      for descriptor in self._inventory.artifacts:
        if descriptor.authority_kind != "state_checkpoint" or descriptor.writer_generation != writer_generation:
          continue
        try:
          checkpoint_bytes, _ = self._ledger.get_blob(role="runtime_evidence", digest=descriptor.blob_sha256)
          checkpoint = CompatibilityReader(
            generation=self._inventory.compatibility_generation,
            supported_state_schema_generation=descriptor.state_schema_generation,
            supported_features=descriptor.truth_features,
            supported_topologies=(descriptor.topology,),
          ).admit_authority(descriptor, checkpoint_bytes)
          persisted = self._ledger.read_checkpoint(
            role="runtime_evidence", checkpoint_id=payload["checkpoint_id"],
          )
        except (LedgerContractError, AuthorityContractError):
          continue
        if (checkpoint["payload"]["checkpoint_id"] == payload["checkpoint_id"] and
            checkpoint["payload"]["release_id"] == self._release_id and
            checkpoint["payload"]["plan_sha256"] == plan["payload_sha256"] and
            checkpoint["payload"]["decision_id"] == payload["decision_id"] and
            persisted == checkpoint):
          checkpoint_descriptor = descriptor
          break
      if checkpoint_descriptor is None:
        raise LedgerContractError("durable qualification checkpoint is not the exact fenced stored checkpoint")
    if payload["state"] == "backed-out":
      rollback = [
        artifact for artifact in self._inventory.artifacts
        if artifact.rollback_eligible and artifact.writer_generation == writer_generation
      ]
      if (checkpoint_descriptor is None or payload["irreversible_write_boundary"] != "none" or
          len(rollback) != 3 or
          {artifact.authority_kind for artifact in rollback} !=
          {"resolved_composition_plan", "state_checkpoint", "release_package"} or
          any(artifact.blob_sha256 not in self._available_blob_digests() for artifact in rollback)):
        raise LedgerContractError("durable backed-out decision lacks the exact N-1 rollback set")

    admissions_open = record["admissions_open"]
    writer_frozen = record["writer_advancement_frozen"]
    if (admissions_open, writer_frozen) not in ((True, False), (False, True)):
      raise LedgerContractError("durable qualification admission/freeze flags are inconsistent")
    kill_sha256 = record["kill_switch_record_sha256"]
    if kill_sha256:
      kill_bytes, kill_metadata = self._ledger.get_blob(role="release_controller", digest=kill_sha256)
      kill = parse_kill_switch_bytes(kill_bytes)
      if (kill_metadata.media_type != "application/vnd.echelon-forge.kill-switch-record.v1+json" or
          kill["release_id"] != self._release_id or admissions_open or not writer_frozen):
        raise LedgerContractError("durable qualification kill-switch binding is invalid")
    if payload["state"] == "backed-out" and (admissions_open or not writer_frozen):
      raise LedgerContractError("durable backed-out state must close admission and freeze the writer")

    duplicate_kill = False
    if previous_record is None:
      if (payload["state"] != "prepared" or payload["decision_sequence"] != "0" or
          payload["predecessor_decision_id"] or writer_generation != self._inventory.writer_generation):
        raise LedgerContractError("durable qualification history lacks the exact prepared root")
    else:
      previous = previous_record["candidate_rollout_decision"]
      previous_payload = previous["payload"]
      duplicate_kill = candidate["payload_sha256"] == previous["payload_sha256"]
      if duplicate_kill:
        if not kill_sha256 or admissions_open or not writer_frozen:
          raise LedgerContractError("duplicate durable decision is not a typed kill-switch record")
      else:
        try:
          validate_rollout_transition(previous, candidate)
        except AuthorityContractError as error:
          raise LedgerContractError("durable qualification decision history is not monotonic") from error
        if payload["state"] not in ROLL_OUT_TRANSITIONS[previous_payload["state"]]:
          raise LedgerContractError("durable qualification state history is not admitted")
        previous_writer = int(previous_payload["writer_generation"])
        previous_plan = previous_record["active_plan_blob_sha256"]
        writer_changed = writer_generation != previous_writer
        plan_changed = record["active_plan_blob_sha256"] != previous_plan
        if writer_changed != plan_changed:
          raise LedgerContractError("durable writer and active plan generations are decoupled")
        if plan_changed and payload["state"] not in {"adoption-expanding", "backed-out"}:
          raise LedgerContractError("durable plan change occurs outside advancement or backout")
        if writer_changed:
          if payload["state"] == "backed-out":
            if writer_generation != previous_writer - 1:
              raise LedgerContractError("durable backout is not exactly N to N-1")
          elif writer_generation != previous_writer + 1 or payload["state"] != "adoption-expanding":
            raise LedgerContractError("durable writer advancement is not one generation")
        repair_reopen = previous_payload["state"] == "backed-out" and payload["state"] == "prepared"
        if (not previous_record["admissions_open"] and payload["state"] != "backed-out" and
            not repair_reopen):
          raise LedgerContractError("durable closed admission has an untyped successor")
        if repair_reopen and (not admissions_open or writer_frozen):
          raise LedgerContractError("durable repair successor did not reopen admission")
    return candidate, duplicate_kill

  def _validate_durable_qualification_history(self, records: tuple[Mapping[str, Any], ...]) -> None:
    previous_record: Mapping[str, Any] | None = None
    forward_states = {"prepared", "shadow", "canary-ready", "production-canary", "adoption-expanding", "rollback-window", "stable"}
    for record in records:
      candidate, duplicate_kill = self._validate_durable_decision_record(record, previous_record)
      state = candidate["payload"]["state"]
      evidence = _qualification_evidence_from_document(record["entry_evidence"])
      if state in forward_states and not reader_first_ready(
        current_writer_generation=self._inventory.compatibility_generation - 1,
        target_writer_generation=self._inventory.compatibility_generation,
        readers=evidence.reader_deployments,
        inventory=self._inventory,
        available_blob_digests=self._available_blob_digests(),
        ledger=self._ledger,
      ):
        raise LedgerContractError("durable qualification history has invalid reader-first evidence")
      if previous_record is not None:
        previous = previous_record["candidate_rollout_decision"]
        if duplicate_kill:
          previous_record = record
          continue
        expected_plan_sha256 = previous["payload"]["plan_sha256"]
        expected_decision_sha256 = previous["payload_sha256"]
        required = {
          "shadow": (evidence.shadow_receipt_sha256, "application/vnd.echelon-forge.shadow-comparison-receipt.v1+json", ""),
          "canary-ready": (evidence.storage_restore_drill_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "storage-restore-drill"),
          "production-canary": (evidence.cutover_drill_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "cutover-drill"),
          "adoption-expanding": (evidence.adoption_health_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "adoption-health"),
          "rollback-window": (evidence.adoption_health_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "adoption-health"),
          "stable": (evidence.inventory_disposition_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "inventory-disposition"),
          "backed-out": (evidence.rollback_receipt_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "rollback-receipt"),
        }
        if state in required:
          digest, media_type, kind = required[state]
          if not digest:
            raise LedgerContractError("durable qualification history lacks state-entry evidence")
          self._require_evidence_blob(
            digest, expected_media_type=media_type, expected_kind=kind,
            expected_plan_sha256=expected_plan_sha256,
            expected_decision_sha256=expected_decision_sha256,
          )
        if state == "canary-ready":
          self._require_evidence_blob(
            evidence.rollback_drill_sha256,
            expected_media_type="application/vnd.echelon-forge.qualification-evidence.v1+json",
            expected_kind="rollback-drill", expected_plan_sha256=expected_plan_sha256,
            expected_decision_sha256=expected_decision_sha256,
          )
      self._admitted_decision_ids.add(candidate["payload"]["decision_id"])
      previous_record = record

  def _available_blob_digests(self) -> set[str]:
    available: set[str] = set()
    for artifact in self._inventory.artifacts:
      try:
        self._ledger.stat_blob(role="runtime_evidence", digest=artifact.blob_sha256)
        available.add(artifact.blob_sha256)
      except LedgerContractError:
        pass
    return available

  def _require_evidence_blob(
    self,
    digest: str,
    *,
    expected_media_type: str,
    expected_kind: str = "",
    expected_plan_sha256: str | None = None,
    expected_decision_sha256: str | None = None,
  ) -> dict[str, Any]:
    _require_sha256(digest, "qualification evidence digest")
    try:
      payload, metadata = self._ledger.get_blob(role="release_controller", digest=digest)
    except LedgerContractError as error:
      raise LedgerContractError("qualification entry evidence blob is unavailable") from error
    if metadata.media_type != expected_media_type:
      raise LedgerContractError("qualification entry evidence media type is invalid")
    document = parse_canonical_json_bytes(payload)
    if expected_media_type == "application/vnd.echelon-forge.shadow-comparison-receipt.v1+json":
      _require_exact_fields(document, {
        "schema_version", "contract_version", "receipt_id", "authoritative", "plan_sha256",
        "release_manifest_sha256", "rollout_decision_sha256", "comparison_kind", "outcome",
        "evidence_sha256",
      }, "shadow comparison receipt")
      plan_sha256 = expected_plan_sha256 or self._plan_payload_sha256
      decision_sha256 = expected_decision_sha256 or (self._last_decision["payload_sha256"] if self._last_decision is not None else "")
      if (document["schema_version"] != SHADOW_RECEIPT_SCHEMA_VERSION or
          document["contract_version"] != LEDGER_CONTRACT_VERSION or document["authoritative"] is not False or
          document["outcome"] != "match" or document["plan_sha256"] != plan_sha256 or
          document["release_manifest_sha256"] != self._release_payload_sha256 or
          document["rollout_decision_sha256"] != decision_sha256):
        raise LedgerContractError("shadow comparison receipt differs from active authority or is not a match")
    else:
      _require_exact_fields(document, {
        "schema_version", "contract_version", "release_id", "evidence_kind", "outcome",
        "evidence_sha256", "plan_sha256", "rollout_decision_sha256", "authoritative_runtime_mutation",
      }, "qualification evidence")
      plan_sha256 = expected_plan_sha256 or self._plan_payload_sha256
      decision_sha256 = expected_decision_sha256 or (self._last_decision["payload_sha256"] if self._last_decision is not None else "")
      if (document["schema_version"] != QUALIFICATION_EVIDENCE_SCHEMA_VERSION or
          document["contract_version"] != LEDGER_CONTRACT_VERSION or document["release_id"] != self._release_id or
          document["evidence_kind"] != expected_kind or document["outcome"] != "pass" or
          document["authoritative_runtime_mutation"] is not False or
          document["plan_sha256"] != plan_sha256 or
          document["rollout_decision_sha256"] != decision_sha256):
        raise LedgerContractError("qualification evidence content differs from the required release/kind/outcome")
      _require_sha256(document["evidence_sha256"], "qualification evidence payload digest")
    try:
      _, proof_metadata = self._ledger.get_blob(role="release_controller", digest=document["evidence_sha256"])
    except LedgerContractError as error:
      raise LedgerContractError("qualification evidence proof bytes are unavailable") from error
    if proof_metadata.media_type != "application/vnd.echelon-forge.qualification-proof.v1+octets":
      raise LedgerContractError("qualification evidence proof media type is invalid")
    return document

  def _validate_entry_evidence(
    self,
    state: str,
    evidence: QualificationEvidence,
    *,
    reader_deployments: tuple[ReaderDeployment, ...],
  ) -> QualificationEvidence:
    if not evidence.reader_deployments and reader_deployments:
      evidence = QualificationEvidence(
        reader_deployments=reader_deployments,
        shadow_receipt_sha256=evidence.shadow_receipt_sha256,
        storage_restore_drill_sha256=evidence.storage_restore_drill_sha256,
        rollback_drill_sha256=evidence.rollback_drill_sha256,
        cutover_drill_sha256=evidence.cutover_drill_sha256,
        adoption_health_sha256=evidence.adoption_health_sha256,
        inventory_disposition_sha256=evidence.inventory_disposition_sha256,
        rollback_receipt_sha256=evidence.rollback_receipt_sha256,
        deadline_elapsed=evidence.deadline_elapsed,
        no_unresolved_high_findings=evidence.no_unresolved_high_findings,
      )
    _qualification_evidence_document(evidence)
    available = self._available_blob_digests()
    eligible = tuple(reader for reader in evidence.reader_deployments if reader.eligible)
    if state in {"prepared", "shadow", "canary-ready", "production-canary", "adoption-expanding", "rollback-window", "stable"} and not evidence.reader_deployments:
      raise LedgerContractError(f"{state} entry lacks reader deployment evidence")
    if state in {"prepared", "shadow", "canary-ready", "production-canary", "adoption-expanding", "rollback-window", "stable"}:
      if not reader_first_ready(
        current_writer_generation=self._inventory.compatibility_generation - 1,
        target_writer_generation=self._inventory.compatibility_generation,
        readers=evidence.reader_deployments,
        inventory=self._inventory,
        available_blob_digests=available,
        ledger=self._ledger,
      ):
        raise LedgerContractError(f"{state} entry lacks current reader/package/inventory admission evidence")
    required = {
      "shadow": (evidence.shadow_receipt_sha256, "application/vnd.echelon-forge.shadow-comparison-receipt.v1+json", ""),
      "canary-ready": (evidence.storage_restore_drill_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "storage-restore-drill"),
      "production-canary": (evidence.cutover_drill_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "cutover-drill"),
      "adoption-expanding": (evidence.adoption_health_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "adoption-health"),
      "rollback-window": (evidence.adoption_health_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "adoption-health"),
      "stable": (evidence.inventory_disposition_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "inventory-disposition"),
      "backed-out": (evidence.rollback_receipt_sha256, "application/vnd.echelon-forge.qualification-evidence.v1+json", "rollback-receipt"),
    }
    if state in required:
      digest, media_type, evidence_kind = required[state]
      if not digest:
        raise LedgerContractError(f"{state} entry lacks required evidence")
      self._require_evidence_blob(digest, expected_media_type=media_type, expected_kind=evidence_kind)
    if state == "canary-ready" and not evidence.rollback_drill_sha256:
      raise LedgerContractError("canary-ready entry lacks rollback drill evidence")
    if state == "canary-ready":
      self._require_evidence_blob(
        evidence.rollback_drill_sha256,
        expected_media_type="application/vnd.echelon-forge.qualification-evidence.v1+json",
        expected_kind="rollback-drill",
      )
    if state == "stable" and (not evidence.deadline_elapsed or not evidence.no_unresolved_high_findings):
      raise LedgerContractError("stable entry lacks deadline/disposition health evidence")
    if state in {"shadow", "canary-ready", "production-canary", "adoption-expanding", "rollback-window"} and eligible:
      if any(not reader.healthy for reader in eligible):
        raise LedgerContractError("rollout entry contains an unhealthy eligible reader")
    return evidence

  def _persist_qualification(
    self,
    normalized: Mapping[str, Any],
    *,
    evidence: QualificationEvidence,
    audit_identity: str,
    kill_switch_record_sha256: str | None = None,
    active_plan_blob_sha256: str | None = None,
    admissions_open: bool | None = None,
    writer_advancement_frozen: bool | None = None,
  ) -> DurableAck:
    persisted_admissions_open = self._admissions_open if admissions_open is None else admissions_open
    persisted_writer_frozen = self._writer_advancement_frozen if writer_advancement_frozen is None else writer_advancement_frozen
    persisted_kill_switch_sha256 = (
      self._kill_switch_record_sha256
      if kill_switch_record_sha256 is None else kill_switch_record_sha256
    )
    qualification_bytes = canonical_json_bytes(rollout_qualification_payload(
      normalized,
      inventory_sha256=self._inventory_sha256,
      release_manifest_blob_sha256=self._release_blob_sha256,
      active_plan_blob_sha256=active_plan_blob_sha256 or self._plan_blob_sha256,
      evidence=evidence,
      admissions_open=persisted_admissions_open,
      writer_advancement_frozen=persisted_writer_frozen,
      kill_switch_record_sha256=persisted_kill_switch_sha256,
      predecessor_qualification_sha256=self._last_qualification_sha256,
    ))
    digest = _sha256(qualification_bytes)
    self._ledger.put_blob(
      role="release_controller", payload=qualification_bytes,
      media_type="application/vnd.echelon-forge.rollout-qualification-record.v1+json",
      expected_sha256=digest, retention_class="rollback-window", audit_identity=audit_identity,
    )
    if self._slot_version == 0:
      ack = self._ledger.conditional_create(
        role="release_controller", key=f"qualification-rollout:{self._release_id}", blob_digest=digest,
        token=self._token, audit_identity=audit_identity,
      )
    else:
      ack = self._ledger.compare_and_swap(
        role="release_controller", key=f"qualification-rollout:{self._release_id}", expected_version=self._slot_version,
        blob_digest=digest, token=self._token, audit_identity=audit_identity,
      )
    self._slot_version = ack.version
    self._last_qualification_sha256 = digest
    self._last_decision = dict(normalized)
    self._last_evidence = evidence
    self._admissions_open = persisted_admissions_open
    self._writer_advancement_frozen = persisted_writer_frozen
    self._kill_switch_record_sha256 = persisted_kill_switch_sha256
    return ack

  def commit_qualification_decision(
    self,
    envelope: Mapping[str, Any],
    *,
    audit_identity: str,
    reader_deployments: Iterable[ReaderDeployment] = (),
    evidence: QualificationEvidence = QualificationEvidence(),
  ) -> DurableAck:
    self._ledger.assert_fence(self._token)
    normalized = validate_authority_envelope(envelope)
    payload = normalized["payload"]
    if payload["authority_kind"] != "rollout_decision" or payload["release_id"] != self._release_id:
      raise LedgerContractError("rollout decision owner/release mismatch")
    validate_release_inventory_binding(
      self._release_envelope, normalized, self._inventory, self._inventory_sha256,
    )
    supplied_readers = tuple(reader_deployments)
    if payload["manifest_sha256"] != self._release_payload_sha256:
      raise LedgerContractError("rollout successor changes the immutable release binding")
    candidate_descriptors = [
      artifact for artifact in self._inventory.artifacts
      if artifact.authority_kind == "resolved_composition_plan" and
      artifact.writer_generation == int(payload["writer_generation"])
    ]
    matched = None
    for candidate in candidate_descriptors:
      try:
        candidate_bytes, _ = self._ledger.get_blob(role="release_controller", digest=candidate.blob_sha256)
        candidate_envelope = CompatibilityReader(
          generation=self._inventory.compatibility_generation,
          supported_state_schema_generation=candidate.state_schema_generation,
          supported_features=candidate.truth_features,
        ).admit_authority(candidate, candidate_bytes)
      except (LedgerContractError, AuthorityContractError):
        continue
      if candidate_envelope["payload_sha256"] == payload["plan_sha256"]:
        matched = (candidate, candidate_envelope)
        break
    if matched is None:
      raise LedgerContractError("rollout plan is not the exact stored plan for its writer generation")
    candidate, candidate_envelope = matched
    if (payload["plan_reader_generation_min"] != candidate_envelope["payload"]["reader_generation_min"] or
        payload["plan_reader_generation_max"] != candidate_envelope["payload"]["reader_generation_max"]):
      raise LedgerContractError("rollout plan reader window differs from stored candidate")
    next_plan_changed = candidate.blob_sha256 != self._plan_blob_sha256
    checkpoint_descriptor: ArtifactDescriptor | None = None
    if payload["checkpoint_id"]:
      for descriptor_item in self._inventory.artifacts:
        if descriptor_item.authority_kind != "state_checkpoint" or descriptor_item.writer_generation != int(payload["writer_generation"]):
          continue
        try:
          checkpoint_bytes, _ = self._ledger.get_blob(role="runtime_evidence", digest=descriptor_item.blob_sha256)
          checkpoint_envelope = CompatibilityReader(
            generation=self._inventory.compatibility_generation,
            supported_state_schema_generation=descriptor_item.state_schema_generation,
            supported_features=descriptor_item.truth_features,
          ).admit_authority(descriptor_item, checkpoint_bytes)
          checkpoint_payload = checkpoint_envelope["payload"]
          persisted_checkpoint = self._ledger.read_checkpoint(
            role="runtime_evidence", checkpoint_id=payload["checkpoint_id"],
          )
        except (LedgerContractError, AuthorityContractError):
          continue
        if (checkpoint_payload["checkpoint_id"] == payload["checkpoint_id"] and
            checkpoint_payload["release_id"] == self._release_id and
            checkpoint_payload["plan_sha256"] == candidate_envelope["payload_sha256"] and
            checkpoint_payload["decision_id"] == payload["decision_id"] and
            persisted_checkpoint == checkpoint_envelope):
          checkpoint_descriptor = descriptor_item
          break
      if checkpoint_descriptor is None:
        raise LedgerContractError("rollout checkpoint is not the exact fenced stored checkpoint for its plan/release")
    if payload["state"] == "backed-out" and checkpoint_descriptor is None:
      raise LedgerContractError("backed-out decision requires an exact fenced rollback checkpoint")
    if payload["state"] == "backed-out":
      rollback = [
        artifact for artifact in self._inventory.artifacts
        if artifact.rollback_eligible and artifact.writer_generation == int(payload["writer_generation"])
      ]
      available_rollback = self._available_blob_digests()
      if (payload["irreversible_write_boundary"] != "none" or
          {artifact.authority_kind for artifact in rollback} != {"resolved_composition_plan", "state_checkpoint", "release_package"} or
          any(artifact.blob_sha256 not in available_rollback for artifact in rollback)):
        raise LedgerContractError("backed-out decision lacks the exact available N-1 plan/checkpoint/package set")
    if self._last_decision is None:
      if payload["state"] != "prepared" or payload["decision_sequence"] != "0" or payload["predecessor_decision_id"]:
        raise LedgerContractError("rollout log must begin with prepared sequence zero")
      if int(payload["writer_generation"]) != self._inventory.writer_generation:
        raise LedgerContractError("initial rollout writer differs from inventory")
    else:
      try:
        validate_rollout_transition(self._last_decision, normalized)
      except AuthorityContractError as error:
        raise LedgerContractError(f"rollout transition identity rejected: {error}") from error
      previous_state = self._last_decision["payload"]["state"]
      if payload["state"] not in ROLL_OUT_TRANSITIONS[previous_state]:
        raise LedgerContractError("rollout state transition is not admitted")
      previous_writer = int(self._last_decision["payload"]["writer_generation"])
      next_writer = int(payload["writer_generation"])
      if (next_writer != previous_writer) != next_plan_changed:
        raise LedgerContractError("writer generation and active plan generation must advance or back out together")
      if next_plan_changed and payload["state"] not in {"adoption-expanding", "backed-out"}:
        raise LedgerContractError("only writer advancement or typed backout may activate another plan")
      if next_writer != previous_writer:
        available_blob_digests = self._available_blob_digests()
        if payload["state"] == "backed-out" and next_writer == previous_writer - 1:
          rollback = [artifact for artifact in self._inventory.artifacts if artifact.rollback_eligible and artifact.writer_generation == next_writer]
          if (payload["irreversible_write_boundary"] != "none" or
              {artifact.authority_kind for artifact in rollback} != {"resolved_composition_plan", "state_checkpoint", "release_package"} or
              any(artifact.blob_sha256 not in frozenset(available_blob_digests) for artifact in rollback)):
            raise LedgerContractError("writer backout lacks compatible stored artifact evidence")
        else:
          if self._writer_advancement_frozen:
            raise LedgerContractError("kill switch freezes writer advancement")
          if next_writer != previous_writer + 1 or payload["state"] != "adoption-expanding" or not reader_first_ready(
            current_writer_generation=previous_writer,
            target_writer_generation=next_writer,
            readers=supplied_readers,
            inventory=self._inventory,
            available_blob_digests=available_blob_digests,
            ledger=self._ledger,
          ):
            raise LedgerContractError("writer advancement lacks reader-first evidence")
    if (payload["rollback_deadline"] != self._inventory.rollback_deadline or
        payload["irreversible_write_boundary"] != self._inventory.irreversible_write_boundary):
      raise LedgerContractError("rollout decision differs from inventory rollback boundary")
    if (payload["state"] in {"rollback-window", "stable"} and
        int(payload["writer_generation"]) != self._inventory.compatibility_generation):
      raise LedgerContractError("rollback-window and stable require the generation-N writer")
    repair_reopen = (
      self._last_decision is not None and self._last_decision["payload"]["state"] == "backed-out" and
      payload["state"] == "prepared"
    )
    if not self._admissions_open and payload["state"] != "backed-out" and not repair_reopen:
      raise LedgerContractError("kill switch permits only a backed-out successor")
    evidence = self._validate_entry_evidence(payload["state"], evidence, reader_deployments=supplied_readers)
    ack = self._persist_qualification(
      normalized, evidence=evidence, audit_identity=audit_identity,
      kill_switch_record_sha256="" if repair_reopen else None,
      active_plan_blob_sha256=candidate.blob_sha256 if next_plan_changed else self._plan_blob_sha256,
      admissions_open=True if repair_reopen else (False if payload["state"] == "backed-out" else None),
      writer_advancement_frozen=False if repair_reopen else (True if payload["state"] == "backed-out" else None),
    )
    if next_plan_changed:
      self._active_plan_envelope = dict(candidate_envelope)
      self._plan_blob_sha256 = candidate.blob_sha256
      self._plan_payload_sha256 = candidate_envelope["payload_sha256"]
      self._plan_reader_generation_min = candidate_envelope["payload"]["reader_generation_min"]
      self._plan_reader_generation_max = candidate_envelope["payload"]["reader_generation_max"]
    self._admitted_decision_ids.add(payload["decision_id"])
    return ack

  def activate_kill_switch(self, health: CanaryHealth, *, audit_identity: str) -> tuple[str, ...]:
    reasons_set = set(kill_switch_reasons(health))
    if not reasons_set:
      raise LedgerContractError("kill switch requires an admitted trigger")
    if self._kill_switch_record_sha256:
      try:
        prior_bytes, _ = self._ledger.get_blob(role="release_controller", digest=self._kill_switch_record_sha256)
        reasons_set.update(parse_kill_switch_bytes(prior_bytes)["reasons"])
      except LedgerContractError as error:
        raise LedgerContractError("prior kill-switch record is unavailable") from error
    reasons = tuple(sorted(reasons_set))
    payload = canonical_json_bytes({
      "schema_version": KILL_SWITCH_SCHEMA_VERSION,
      "contract_version": LEDGER_CONTRACT_VERSION,
      "release_id": self._release_id,
      "admissions_open": False,
      "writer_advancement_frozen": True,
      "reasons": sorted(reasons),
      "authoritative_runtime_mutation": False,
    })
    digest = _sha256(payload)
    self._ledger.put_blob(
      role="release_controller", payload=payload,
      media_type="application/vnd.echelon-forge.kill-switch-record.v1+json",
      expected_sha256=digest, retention_class="rollback-window", audit_identity=audit_identity,
    )
    if self._last_decision is None:
      key = f"qualification-kill:{self._release_id}"
      if self._early_kill_slot_version == 0:
        ack = self._ledger.conditional_create(
          role="release_controller", key=key, blob_digest=digest,
          token=self._token, audit_identity=audit_identity,
        )
      else:
        ack = self._ledger.compare_and_swap(
          role="release_controller", key=key, expected_version=self._early_kill_slot_version,
          blob_digest=digest, token=self._token, audit_identity=audit_identity,
        )
      self._early_kill_slot_version = ack.version
      self._kill_switch_record_sha256 = digest
      self._admissions_open = False
      self._writer_advancement_frozen = True
      return reasons
    self._persist_qualification(
      self._last_decision,
      evidence=self._last_evidence,
      audit_identity=audit_identity,
      kill_switch_record_sha256=digest,
      admissions_open=False,
      writer_advancement_frozen=True,
    )
    self._kill_switch_record_sha256 = digest
    return reasons
