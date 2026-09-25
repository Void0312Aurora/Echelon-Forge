"""SQLite-backed durable ArtifactLedger qualification backend for P5-B.

SQLite WAL plus ``synchronous=FULL`` supplies the local supported-topology
durability boundary. Content blobs are immutable and content-addressed;
journals and receipts advance only through fenced transactions.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import zlib
from pathlib import Path
from typing import Any, Callable, Mapping

from tools.maintenance.runtime_artifact_ledger import (
  LedgerContractError,
  FenceToken,
  TerminationProof,
)
from tools.maintenance.p7b_evidence_manifest import EvidenceManifestError
from tools.maintenance.p7b_evidence_manifest import validate_evidence_manifest
from tools.maintenance.runtime_authority_contracts import (
  canonical_json_bytes,
  parse_canonical_json_bytes,
  validate_authority_envelope,
  validate_rollout_transition,
)
from python.rl.runtime.rollout_gate import SCHEMA_VERSION as ROLLOUT_SLOT_SCHEMA_VERSION
from python.rl.runtime.rollout_gate import TRANSITIONS as ROLLOUT_TRANSITIONS
from python.rl.runtime.rollout_gate import RolloutAdmissionError
from python.rl.runtime.rollout_gate import validate_rollout_envelope
from python.rl.runtime.rollout_evidence import assert_rollout_evidence_decision_binding
from python.rl.runtime.rollout_evidence import RolloutEvidenceError
from python.rl.runtime.rollout_evidence import project_rollout_evidence
from tools.maintenance.runtime_execution_provenance import (
  ExecutionObservation,
  verify_actual_bindings,
)
from tools.maintenance.runtime_run_receipt import canonical_json, validate_run_receipt


JOURNAL_HEADER_MEDIA_TYPE = "application/vnd.echelon-forge.run-journal-header.v1+json"
JOURNAL_RECORD_MEDIA_TYPE = "application/vnd.echelon-forge.run-journal-record.v1+octets"
RECEIPT_MEDIA_TYPE = "application/vnd.echelon-forge.run-receipt.v1+json"
RELEASE_MANIFEST_MEDIA_TYPE = "application/vnd.echelon-forge.release-manifest.v1+json"
ROLLOUT_DECISION_MEDIA_TYPE = "application/vnd.echelon-forge.rollout-decision.v1+json"
ROLLOUT_EVIDENCE_MEDIA_TYPE = "application/vnd.echelon-forge.rollout-evidence-binding.v1+json"
EVIDENCE_MANIFEST_MEDIA_TYPE = "application/vnd.echelon-forge.evidence-manifest.v1+json"
ROLLOUT_EVIDENCE_SCHEMA_VERSION = "echelon_forge.rollout_evidence_binding.v1"
CHECKPOINT_MEDIA_TYPE = "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json"
CHECKPOINT_VALIDATION_MEDIA_TYPE = "application/vnd.echelon-forge.state-checkpoint-validation.v1+json"
OUTPUT_ARTIFACT_MEDIA_TYPE = "application/octet-stream"
LEDGER_SCHEMA_VERSION = "echelon_forge.sqlite_artifact_ledger.v1"
REQUIRED_LEDGER_TABLES = frozenset({
  "metadata",
  "blobs",
  "fences",
  "terminations",
  "writer_processes",
  "tombstones",
  "slots",
  "journals",
  "frames",
  "receipts",
  "audit",
})
REQUIRED_LEDGER_COLUMNS = {
  "metadata": frozenset({"key", "value"}),
  "blobs": frozenset({"digest", "payload", "media_type", "retention_class", "audit_identity", "size"}),
  "fences": frozenset({"stream_id", "generation", "writer_id"}),
  "terminations": frozenset({"stream_id", "generation", "writer_id", "observed_exit_digest"}),
  "writer_processes": frozenset({"stream_id", "generation", "writer_id", "process_id", "process_start_identity", "os_boot_marker", "host_boot_id"}),
  "tombstones": frozenset({"stream_id", "generation", "writer_id", "observed_exit_digest"}),
  "slots": frozenset({"slot_key", "version", "blob_digest", "fence_generation", "audit_identity"}),
  "journals": frozenset({"journal_id", "stream_id", "generation", "writer_id", "header_digest", "last_sequence", "last_record_digest", "terminal_state", "finalization_digest"}),
  "frames": frozenset({"journal_id", "sequence", "fence_generation", "payload", "payload_digest", "prior_digest", "frame_digest", "frame_length", "frame_checksum"}),
  "receipts": frozenset({"receipt_id", "journal_id", "blob_digest", "receipt_digest", "terminal_state"}),
  "audit": frozenset({"sequence", "operation", "object_id", "digest"}),
}
RETENTION_CLASSES = frozenset({"active-release", "rollback-window", "run-retained", "evidence-short"})
ROLE_PERMISSIONS = {
  "runtime_host": frozenset({"blob.put", "blob.get", "blob.stat", "fence.acquire", "process.register", "journal.write", "checkpoint.read", "checkpoint.write", "slot.write"}),
  "runtime_evidence": frozenset({"blob.get", "blob.stat", "journal.read", "checkpoint.read", "audit.read"}),
  "crash_reconciler": frozenset({"blob.put", "blob.get", "blob.stat", "fence.acquire", "process.confirm_terminated", "writer.tombstone", "journal.write", "journal.read", "checkpoint.read", "audit.read"}),
  "release_controller": frozenset({"blob.put", "blob.get", "blob.stat", "fence.acquire", "slot.write", "audit.read"}),
}
ROLE_WRITE_MEDIA_TYPES = {
  "runtime_host": frozenset({JOURNAL_HEADER_MEDIA_TYPE, JOURNAL_RECORD_MEDIA_TYPE, RECEIPT_MEDIA_TYPE, CHECKPOINT_MEDIA_TYPE, CHECKPOINT_VALIDATION_MEDIA_TYPE, OUTPUT_ARTIFACT_MEDIA_TYPE}),
  "crash_reconciler": frozenset({JOURNAL_RECORD_MEDIA_TYPE, RECEIPT_MEDIA_TYPE}),
  "release_controller": frozenset({RELEASE_MANIFEST_MEDIA_TYPE, ROLLOUT_DECISION_MEDIA_TYPE, RECEIPT_MEDIA_TYPE, ROLLOUT_EVIDENCE_MEDIA_TYPE, EVIDENCE_MANIFEST_MEDIA_TYPE}),
}
ROLE_READ_MEDIA_TYPES = {
  "runtime_host": ROLE_WRITE_MEDIA_TYPES["runtime_host"],
  "runtime_evidence": ROLE_WRITE_MEDIA_TYPES["runtime_host"] | ROLE_WRITE_MEDIA_TYPES["release_controller"],
  "crash_reconciler": frozenset({JOURNAL_HEADER_MEDIA_TYPE, JOURNAL_RECORD_MEDIA_TYPE, RECEIPT_MEDIA_TYPE, CHECKPOINT_MEDIA_TYPE, CHECKPOINT_VALIDATION_MEDIA_TYPE, OUTPUT_ARTIFACT_MEDIA_TYPE}),
  "release_controller": ROLE_WRITE_MEDIA_TYPES["release_controller"],
}


def _sha(payload: bytes) -> str:
  return hashlib.sha256(payload).hexdigest()


def _host_boot_marker() -> str:
  if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetTickCount64.restype = ctypes.c_ulonglong
    kernel32.GetSystemTimeAsFileTime.argtypes = (ctypes.POINTER(wintypes.FILETIME),)
    now = wintypes.FILETIME()
    kernel32.GetSystemTimeAsFileTime(ctypes.byref(now))
    now_filetime = (int(now.dwHighDateTime) << 32) | int(now.dwLowDateTime)
    boot_filetime = now_filetime - int(kernel32.GetTickCount64()) * 10_000
    return f"windows-boot-filetime:{boot_filetime}"
  boot_id = Path("/proc/sys/kernel/random/boot_id")
  if boot_id.is_file():
    return f"linux-boot-id:{boot_id.read_text(encoding='ascii').strip()}"
  raise LedgerContractError("supported process observation requires Windows or Linux /proc")


def _inspect_process(pid: int) -> tuple[str, bool, int | None] | None:
  """Return an OS-bound creation identity, liveness, and exit code."""

  if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
    raise LedgerContractError("writer process id must be a positive integer")
  if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    process_query_limited_information = 0x1000
    still_active = 259

    class FileTime(ctypes.Structure):
      _fields_ = (("low", wintypes.DWORD), ("high", wintypes.DWORD))

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.GetProcessTimes.argtypes = (
      wintypes.HANDLE, ctypes.POINTER(FileTime), ctypes.POINTER(FileTime),
      ctypes.POINTER(FileTime), ctypes.POINTER(FileTime),
    )
    kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
      error = ctypes.get_last_error()
      if error in {87, 1168}:
        return None
      raise LedgerContractError(f"writer process observation failed with Windows error {error}")
    try:
      creation, exited, kernel, user = FileTime(), FileTime(), FileTime(), FileTime()
      if not kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
        raise LedgerContractError("writer process creation-time observation failed")
      exit_code = wintypes.DWORD()
      if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
        raise LedgerContractError("writer process exit-code observation failed")
      creation_value = (int(creation.high) << 32) | int(creation.low)
      return f"windows-filetime:{creation_value}", int(exit_code.value) == still_active, int(exit_code.value)
    finally:
      kernel32.CloseHandle(handle)

  stat_path = Path("/proc") / str(pid) / "stat"
  try:
    stat = stat_path.read_text(encoding="ascii")
  except FileNotFoundError:
    return None
  except OSError as error:
    raise LedgerContractError("writer process /proc observation failed") from error
  close = stat.rfind(")")
  fields = stat[close + 2:].split() if close >= 0 else []
  if len(fields) <= 19:
    raise LedgerContractError("writer process /proc identity is malformed")
  state = fields[0]
  start_ticks = fields[19]
  return f"linux-start-ticks:{start_ticks}", state != "Z", None


def _require_identity(value: str, field: str) -> None:
  if not isinstance(value, str) or not value or len(value) > 128:
    raise LedgerContractError(f"{field} must be a non-empty bounded identity")


def _require_sha256(value: str, field: str) -> None:
  if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
    raise LedgerContractError(f"{field} must be lowercase SHA-256")


class SQLiteArtifactLedger:
  """Durable local ledger; production activation remains owned by P5-D."""

  def __init__(self, root: str | Path):
    self.root = Path(root)
    self.root.mkdir(parents=True, exist_ok=True)
    self.db_path = self.root / "artifact-ledger.sqlite3"
    existing = self.db_path.exists()
    self.db = sqlite3.connect(self.db_path, isolation_level=None, check_same_thread=False)
    if existing:
      try:
        self._validate_schema_identity(self.db, context="existing ledger")
      except Exception:
        self.db.close()
        raise
    self.db.execute("PRAGMA journal_mode=WAL")
    self.db.execute("PRAGMA synchronous=FULL")
    self.db.execute("PRAGMA foreign_keys=ON")
    self._init_schema()

  def _init_schema(self) -> None:
    self.db.executescript("""
      CREATE TABLE IF NOT EXISTS metadata(
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
      );
      INSERT OR IGNORE INTO metadata(key, value)
        VALUES('schema_version', 'echelon_forge.sqlite_artifact_ledger.v1');
      CREATE TABLE IF NOT EXISTS blobs(
        digest TEXT PRIMARY KEY,
        payload BLOB NOT NULL,
        media_type TEXT NOT NULL,
        retention_class TEXT NOT NULL,
        audit_identity TEXT NOT NULL,
        size INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS fences(
        stream_id TEXT PRIMARY KEY,
        generation INTEGER NOT NULL,
        writer_id TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS terminations(
        stream_id TEXT NOT NULL,
        generation INTEGER NOT NULL,
        writer_id TEXT NOT NULL,
        observed_exit_digest TEXT NOT NULL,
        PRIMARY KEY(stream_id, generation, writer_id)
      );
      CREATE TABLE IF NOT EXISTS writer_processes(
        stream_id TEXT NOT NULL,
        generation INTEGER NOT NULL,
        writer_id TEXT NOT NULL,
        process_id INTEGER NOT NULL,
        process_start_identity TEXT NOT NULL,
        os_boot_marker TEXT NOT NULL,
        host_boot_id TEXT NOT NULL,
        PRIMARY KEY(stream_id, generation, writer_id)
      );
      CREATE TABLE IF NOT EXISTS tombstones(
        stream_id TEXT NOT NULL,
        generation INTEGER NOT NULL,
        writer_id TEXT NOT NULL,
        observed_exit_digest TEXT NOT NULL,
        PRIMARY KEY(stream_id, generation, writer_id)
      );
      CREATE TABLE IF NOT EXISTS slots(
        slot_key TEXT PRIMARY KEY,
        version INTEGER NOT NULL,
        blob_digest TEXT NOT NULL,
        fence_generation INTEGER NOT NULL,
        audit_identity TEXT NOT NULL,
        FOREIGN KEY(blob_digest) REFERENCES blobs(digest)
      );
      CREATE TABLE IF NOT EXISTS journals(
        journal_id TEXT PRIMARY KEY,
        stream_id TEXT NOT NULL UNIQUE,
        generation INTEGER NOT NULL,
        writer_id TEXT NOT NULL,
        header_digest TEXT NOT NULL,
        last_sequence INTEGER NOT NULL,
        last_record_digest TEXT NOT NULL,
        terminal_state TEXT,
        finalization_digest TEXT
      );
      CREATE TABLE IF NOT EXISTS frames(
        journal_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        fence_generation INTEGER NOT NULL,
        payload BLOB NOT NULL,
        payload_digest TEXT NOT NULL,
        prior_digest TEXT NOT NULL,
        frame_digest TEXT NOT NULL,
        frame_length INTEGER NOT NULL,
        frame_checksum INTEGER NOT NULL,
        PRIMARY KEY(journal_id, sequence),
        FOREIGN KEY(journal_id) REFERENCES journals(journal_id)
      );
      CREATE TABLE IF NOT EXISTS receipts(
        receipt_id TEXT PRIMARY KEY,
        journal_id TEXT NOT NULL UNIQUE,
        blob_digest TEXT NOT NULL,
        receipt_digest TEXT NOT NULL,
        terminal_state TEXT NOT NULL,
        FOREIGN KEY(journal_id) REFERENCES journals(journal_id),
        FOREIGN KEY(blob_digest) REFERENCES blobs(digest)
      );
      CREATE TABLE IF NOT EXISTS audit(
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        operation TEXT NOT NULL,
        object_id TEXT NOT NULL,
        digest TEXT NOT NULL
      );
    """)
    schema_row = self.db.execute(
      "SELECT value FROM metadata WHERE key='schema_version'",
    ).fetchone()
    if schema_row is None or schema_row[0] != LEDGER_SCHEMA_VERSION:
      raise LedgerContractError("SQLite ArtifactLedger schema version is unsupported")

  @staticmethod
  def _validate_schema_identity(db: sqlite3.Connection, *, context: str) -> None:
    tables = {
      row[0] for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'",
      )
    }
    if not REQUIRED_LEDGER_TABLES.issubset(tables):
      raise LedgerContractError(f"{context} is not a complete SQLite ArtifactLedger")
    for table, required_columns in REQUIRED_LEDGER_COLUMNS.items():
      columns = {
        row[1] for row in db.execute(f"PRAGMA table_info({table})")
      }
      missing = required_columns - columns
      if missing:
        missing_text = ", ".join(sorted(missing))
        raise LedgerContractError(
          f"{context} table {table!r} schema is incomplete; missing columns: {missing_text}",
        )
    schema_row = db.execute(
      "SELECT value FROM metadata WHERE key='schema_version'",
    ).fetchone()
    if schema_row is None or schema_row[0] != LEDGER_SCHEMA_VERSION:
      raise LedgerContractError(f"{context} schema version is unsupported")

  def close(self) -> None:
    self.db.close()

  def _authorize(self, role: str, permission: str) -> None:
    if permission not in ROLE_PERMISSIONS.get(role, frozenset()):
      raise LedgerContractError(f"role {role!r} lacks {permission!r}")

  def _validate_media(self, role: str, media_type: str, *, write: bool) -> None:
    allowed = ROLE_WRITE_MEDIA_TYPES if write else ROLE_READ_MEDIA_TYPES
    if media_type not in allowed.get(role, frozenset()):
      raise LedgerContractError(f"role {role!r} cannot access media type {media_type!r}")

  def _transaction(self):
    self.db.execute("BEGIN IMMEDIATE")

  def _finish(self) -> None:
    self.db.execute("COMMIT")

  def _abort(self) -> None:
    if self.db.in_transaction:
      self.db.execute("ROLLBACK")

  def _audit(self, operation: str, object_id: str, digest: str) -> None:
    self.db.execute("INSERT INTO audit(operation, object_id, digest) VALUES(?,?,?)", (operation, object_id, digest))

  def _put_blob_locked(
    self,
    payload: bytes,
    *,
    media_type: str,
    retention_class: str,
    audit_identity: str,
    expected_sha256: str | None = None,
  ) -> str:
    """Insert or verify a content-addressed blob in the caller's transaction."""

    digest = _sha(payload)
    if expected_sha256 is not None and digest != expected_sha256:
      raise LedgerContractError("blob digest does not match expected content address")
    existing = self.db.execute(
      "SELECT payload, media_type, retention_class FROM blobs WHERE digest=?", (digest,)
    ).fetchone()
    if existing is not None:
      if bytes(existing[0]) != payload or existing[1] != media_type or existing[2] != retention_class:
        raise LedgerContractError("content-addressed blob identity collision")
      return digest
    self.db.execute(
      "INSERT INTO blobs VALUES(?,?,?,?,?,?)",
      (digest, payload, media_type, retention_class, audit_identity, len(payload)),
    )
    self._audit("blob.put", digest, digest)
    return digest

  def put_blob(self, payload: bytes, *, media_type: str, retention_class: str, audit_identity: str, expected_sha256: str | None = None, role: str = "runtime_host") -> str:
    self._authorize(role, "blob.put")
    _require_identity(audit_identity, "audit_identity")
    if not isinstance(payload, bytes) or not payload:
      raise LedgerContractError("blob payload must be non-empty bytes")
    if retention_class not in RETENTION_CLASSES:
      raise LedgerContractError("retention_class is not admitted")
    self._validate_media(role, media_type, write=True)
    if media_type == EVIDENCE_MANIFEST_MEDIA_TYPE:
      try:
        validate_evidence_manifest(json.loads(payload.decode("utf-8")))
      except (EvidenceManifestError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LedgerContractError("evidence manifest blob is invalid") from error
    try:
      self._transaction()
      digest = self._put_blob_locked(
        payload, media_type=media_type, retention_class=retention_class,
        audit_identity=audit_identity, expected_sha256=expected_sha256,
      )
      self._finish()
    except Exception:
      self._abort()
      raise
    return digest

  def get_blob(self, digest: str, *, role: str = "runtime_host") -> tuple[bytes, str, str]:
    self._authorize(role, "blob.get")
    _require_sha256(digest, "digest")
    row = self.db.execute("SELECT payload, media_type, retention_class FROM blobs WHERE digest=?", (digest,)).fetchone()
    if row is None:
      raise LedgerContractError("blob is absent")
    payload = bytes(row[0])
    if _sha(payload) != digest:
      raise LedgerContractError("blob digest verification failed")
    self._validate_media(role, row[1], write=False)
    if self.db.execute("SELECT size FROM blobs WHERE digest=?", (digest,)).fetchone()[0] != len(payload):
      raise LedgerContractError("blob size verification failed")
    return payload, row[1], row[2]

  def stat_blob(self, digest: str, *, role: str = "runtime_host") -> tuple[str, int, str, str]:
    self._authorize(role, "blob.stat")
    _require_sha256(digest, "digest")
    row = self.db.execute("SELECT media_type,size,retention_class,audit_identity FROM blobs WHERE digest=?", (digest,)).fetchone()
    if row is None:
      raise LedgerContractError("blob is absent")
    self._validate_media(role, row[0], write=False)
    return row[0], int(row[1]), row[2], row[3]

  def acquire_fence(
    self,
    stream_id: str,
    writer_id: str,
    *,
    expected_generation: int | None = None,
    audit_identity: str = "fence-acquire",
    role: str = "runtime_host",
  ) -> FenceToken:
    self._authorize(role, "fence.acquire")
    _require_identity(stream_id, "stream_id")
    _require_identity(writer_id, "writer_id")
    _require_identity(audit_identity, "audit_identity")
    if not stream_id.startswith(("journal:", "checkpoint:", "rollout:")):
      raise LedgerContractError("fence stream namespace is not admitted")
    try:
      self._transaction()
      row = self.db.execute("SELECT generation,writer_id FROM fences WHERE stream_id=?", (stream_id,)).fetchone()
      current = 0 if row is None else int(row[0])
      if expected_generation is not None and expected_generation != current:
        raise LedgerContractError("fence generation compare-and-swap failed")
      if row is not None and self.db.execute(
        "SELECT 1 FROM tombstones WHERE stream_id=? AND generation=? AND writer_id=?",
        (stream_id, int(row[0]), row[1]),
      ).fetchone() is None:
        raise LedgerContractError("prior writer must be tombstoned before takeover")
      generation = current + 1
      self.db.execute("INSERT INTO fences(stream_id,generation,writer_id) VALUES(?,?,?) ON CONFLICT(stream_id) DO UPDATE SET generation=excluded.generation, writer_id=excluded.writer_id", (stream_id, generation, writer_id))
      self._audit("fence.acquire", stream_id, hashlib.sha256(f"{stream_id}:{generation}:{writer_id}:{audit_identity}".encode()).hexdigest())
      self._finish()
      return FenceToken(stream_id, writer_id, generation)
    except Exception:
      self._abort()
      raise

  def _assert_fence(self, token: FenceToken) -> None:
    row = self.db.execute("SELECT generation, writer_id FROM fences WHERE stream_id=?", (token.stream_id,)).fetchone()
    if row is None or int(row[0]) != token.generation or row[1] != token.writer_id:
      raise LedgerContractError("stale writer fence")
    if self.db.execute(
      "SELECT 1 FROM tombstones WHERE stream_id=? AND generation=? AND writer_id=?",
      (token.stream_id, token.generation, token.writer_id),
    ).fetchone() is not None:
      raise LedgerContractError("writer fence is tombstoned")

  def assert_fence(self, token: FenceToken) -> None:
    self._assert_fence(token)

  def register_writer_process(
    self,
    token: FenceToken,
    process_id: int,
    *,
    host_boot_id: str,
    audit_identity: str,
    role: str = "runtime_host",
  ) -> None:
    self._authorize(role, "process.register")
    _require_identity(host_boot_id, "host_boot_id")
    _require_identity(audit_identity, "audit_identity")
    observed = _inspect_process(process_id)
    if observed is None or not observed[1]:
      raise LedgerContractError("writer process must be alive when its fence is registered")
    process_start_identity = observed[0]
    boot_marker = _host_boot_marker()
    observation_digest = _sha(canonical_json_bytes({
      "generation": token.generation,
      "host_boot_id": host_boot_id,
      "os_boot_marker": boot_marker,
      "process_id": process_id,
      "process_start_identity": process_start_identity,
      "stream_id": token.stream_id,
      "writer_id": token.writer_id,
    }))
    try:
      self._transaction()
      self._assert_fence(token)
      self.db.execute(
        "INSERT INTO writer_processes VALUES(?,?,?,?,?,?,?)",
        (token.stream_id, token.generation, token.writer_id, process_id,
         process_start_identity, boot_marker, host_boot_id),
      )
      self._audit("process.register", token.stream_id, observation_digest)
      self._finish()
    except Exception:
      self._abort()
      raise

  def confirm_process_terminated(
    self,
    token: FenceToken,
    *,
    audit_identity: str,
    role: str = "crash_reconciler",
  ) -> TerminationProof:
    self._authorize(role, "process.confirm_terminated")
    _require_identity(audit_identity, "audit_identity")
    registered = self.db.execute(
      "SELECT process_id,process_start_identity,os_boot_marker,host_boot_id FROM writer_processes "
      "WHERE stream_id=? AND generation=? AND writer_id=?",
      (token.stream_id, token.generation, token.writer_id),
    ).fetchone()
    if registered is None:
      raise LedgerContractError("writer fence has no registered OS process identity")
    process_id = int(registered[0])
    current = _inspect_process(process_id)
    if current is not None and current[0] == registered[1] and current[1]:
      raise LedgerContractError("writer process is still alive")
    try:
      self._transaction()
      self._assert_fence(token)
      if self.db.execute(
        "SELECT process_id,process_start_identity,os_boot_marker,host_boot_id FROM writer_processes "
        "WHERE stream_id=? AND generation=? AND writer_id=?",
        (token.stream_id, token.generation, token.writer_id),
      ).fetchone() != registered:
        raise LedgerContractError("writer process registration changed during observation")
      current_locked = _inspect_process(process_id)
      if current_locked is not None and current_locked[0] == registered[1] and current_locked[1]:
        raise LedgerContractError("writer process is still alive")
      observation = {
        "generation": token.generation,
        "host_boot_id": registered[3],
        "observed_exit_code": None if current_locked is None or current_locked[0] != registered[1] else current_locked[2],
        "observed_process_start_identity": None if current_locked is None else current_locked[0],
        "os_boot_marker": registered[2],
        "process_id": process_id,
        "registered_process_start_identity": registered[1],
        "stream_id": token.stream_id,
        "writer_id": token.writer_id,
      }
      observed_exit_sha256 = _sha(canonical_json_bytes(observation))
      self.db.execute(
        "INSERT OR REPLACE INTO terminations VALUES(?,?,?,?)",
        (token.stream_id, token.generation, token.writer_id, observed_exit_sha256),
      )
      self._audit("process.confirm_terminated", token.stream_id, observed_exit_sha256)
      self._finish()
    except Exception:
      self._abort()
      raise
    return TerminationProof(token.stream_id, token.writer_id, token.generation, observed_exit_sha256)

  def tombstone_writer(
    self,
    token: FenceToken,
    termination_proof: TerminationProof,
    *,
    audit_identity: str,
    role: str = "crash_reconciler",
  ) -> None:
    self._authorize(role, "writer.tombstone")
    _require_identity(audit_identity, "audit_identity")
    if (token.stream_id, token.writer_id, token.generation) != (
      termination_proof.stream_id, termination_proof.writer_id, termination_proof.generation,
    ):
      raise LedgerContractError("writer tombstone identity mismatch")
    try:
      self._transaction()
      self._assert_fence(token)
      row = self.db.execute(
        "SELECT observed_exit_digest FROM terminations WHERE stream_id=? AND generation=? AND writer_id=?",
        (token.stream_id, token.generation, token.writer_id),
      ).fetchone()
      if row is None or row[0] != termination_proof.observed_exit_sha256:
        raise LedgerContractError("writer tombstone lacks matching process-termination proof")
      self.db.execute("INSERT INTO tombstones VALUES(?,?,?,?)", (token.stream_id, token.generation, token.writer_id, row[0]))
      self._audit("writer.tombstone", token.stream_id, row[0])
      self._finish()
    except Exception:
      self._abort()
      raise

  def open_journal(self, token: FenceToken, journal_id: str, header: Mapping[str, Any], *, audit_identity: str, role: str = "runtime_host") -> None:
    self._authorize(role, "journal.write")
    if role != "runtime_host":
      raise LedgerContractError("only runtime_host may commit an initial journal header")
    _require_identity(audit_identity, "audit_identity")
    registered = self.db.execute(
      "SELECT 1 FROM writer_processes WHERE stream_id=? AND generation=? AND writer_id=?",
      (token.stream_id, token.generation, token.writer_id),
    ).fetchone()
    if registered is None:
      # The supported local topology is in-process: bind the journal to this
      # OS process before the first durable header.  A caller that owns a
      # different writer process must register it explicitly first.
      self.register_writer_process(
        token, os.getpid(), host_boot_id=_host_boot_marker(), audit_identity=audit_identity,
        role=role,
      )
    header_bytes = canonical_json(header).encode("utf-8")
    try:
      self._transaction()
      self._assert_fence(token)
      if token.stream_id != f"journal:{journal_id}":
        raise LedgerContractError("journal fence stream mismatch")
      if not isinstance(header, Mapping) or header.get("run_id") != journal_id:
        raise LedgerContractError("journal header run identity differs from journal stream")
      if self.db.execute("SELECT 1 FROM journals WHERE journal_id=?", (journal_id,)).fetchone() is not None:
        raise LedgerContractError("journal already exists")
      header_digest = self._put_blob_locked(
        header_bytes, media_type=JOURNAL_HEADER_MEDIA_TYPE,
        retention_class="run-retained", audit_identity=audit_identity,
      )
      self.db.execute("INSERT INTO journals VALUES(?,?,?,?,?,?,?,?,?)", (journal_id, token.stream_id, token.generation, token.writer_id, header_digest, -1, "0" * 64, None, None))
      self._audit("journal.open", journal_id, header_digest)
      self._finish()
    except Exception:
      self._abort()
      raise

  def append_journal(self, token: FenceToken, journal_id: str, payload: bytes, *, sequence: int, audit_identity: str, role: str = "runtime_host") -> str:
    self._authorize(role, "journal.write")
    if role not in {"runtime_host", "crash_reconciler"}:
      raise LedgerContractError("journal append role is not admitted")
    _require_identity(audit_identity, "audit_identity")
    try:
      self._transaction()
      self._assert_fence(token)
      row = self.db.execute(
        "SELECT stream_id,last_sequence,last_record_digest,terminal_state,generation,writer_id "
        "FROM journals WHERE journal_id=?", (journal_id,),
      ).fetchone()
      if row is None or row[0] != token.stream_id or row[3] is not None or sequence != int(row[1]) + 1:
        raise LedgerContractError("journal sequence, identity, or terminal state is invalid")
      if not isinstance(payload, bytes) or not payload:
        raise LedgerContractError("journal payload must be non-empty bytes")
      if role == "crash_reconciler":
        try:
          recovery_event = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
          raise LedgerContractError("crash reconciler may append only a canonical terminal event") from error
        if (
          canonical_json(recovery_event).encode("utf-8") != payload
          or set(recovery_event) != {
            "event", "observed_exit_sha256", "prior_writer_generation", "prior_writer_id",
            "recovery_writer_generation", "recovery_writer_id",
          }
          or recovery_event.get("event") != "crash_reconciled"
        ):
          raise LedgerContractError("crash reconciler may append only crash_reconciled terminal evidence")
        _require_sha256(recovery_event["observed_exit_sha256"], "observed_exit_sha256")
        _require_identity(recovery_event["prior_writer_id"], "prior_writer_id")
        _require_identity(recovery_event["recovery_writer_id"], "recovery_writer_id")
        for generation_field in ("prior_writer_generation", "recovery_writer_generation"):
          if not isinstance(recovery_event[generation_field], int) or recovery_event[generation_field] < 1:
            raise LedgerContractError("crash reconciliation writer generations are invalid")
        termination = self.db.execute(
          "SELECT observed_exit_digest FROM terminations "
          "WHERE stream_id=? AND generation=? AND writer_id=?",
          (row[0], recovery_event["prior_writer_generation"],
           recovery_event["prior_writer_id"]),
        ).fetchone()
        tombstone = self.db.execute(
          "SELECT observed_exit_digest FROM tombstones "
          "WHERE stream_id=? AND generation=? AND writer_id=?",
          (row[0], recovery_event["prior_writer_generation"],
           recovery_event["prior_writer_id"]),
        ).fetchone()
        recovery_frame_count = self.db.execute(
          "SELECT COUNT(*) FROM frames WHERE journal_id=? AND fence_generation=?",
          (journal_id, token.generation),
        ).fetchone()[0]
        if (
          recovery_event["prior_writer_generation"] != int(row[4])
          or recovery_event["prior_writer_id"] != row[5]
          or recovery_event["recovery_writer_generation"] != token.generation
          or recovery_event["recovery_writer_id"] != token.writer_id
          or termination is None
          or tombstone is None
          or termination[0] != recovery_event["observed_exit_sha256"]
          or tombstone[0] != recovery_event["observed_exit_sha256"]
          or recovery_frame_count != 0
        ):
          raise LedgerContractError(
            "crash reconciliation marker does not match termination, tombstone, and fence"
          )
      payload_digest = _sha(payload)
      frame_body = canonical_json_bytes({
        "fence_generation": token.generation,
        "journal_id": journal_id,
        "payload_sha256": payload_digest,
        "payload_size": len(payload),
        "prior_record_sha256": row[2],
        "sequence": sequence,
        "stream_id": token.stream_id,
      })
      frame_digest = _sha(frame_body)
      frame_length = len(frame_body) + 4
      frame_checksum = zlib.crc32(frame_body)
      self._put_blob_locked(
        payload, media_type=JOURNAL_RECORD_MEDIA_TYPE,
        retention_class="run-retained", audit_identity=audit_identity,
        expected_sha256=payload_digest,
      )
      self.db.execute(
        "INSERT INTO frames VALUES(?,?,?,?,?,?,?,?,?)",
        (journal_id, sequence, token.generation, payload, payload_digest, row[2], frame_digest, frame_length, frame_checksum),
      )
      self.db.execute("UPDATE journals SET last_sequence=?, last_record_digest=? WHERE journal_id=?", (sequence, frame_digest, journal_id))
      self._audit("journal.append", journal_id, frame_digest)
      self._finish()
    except Exception:
      self._abort()
      raise
    return frame_digest

  def finalize_journal(self, token: FenceToken, journal_id: str, *, receipt: Mapping[str, Any], terminal_state: str, audit_identity: str, actual_bindings: ExecutionObservation | None = None, role: str = "runtime_host") -> str:
    self._authorize(role, "journal.write")
    if role not in {"runtime_host", "crash_reconciler"}:
      raise LedgerContractError("journal finalization role is not admitted")
    if role == "crash_reconciler" and terminal_state not in {"crashed", "incomplete"}:
      raise LedgerContractError("crash reconciler may finalize only crashed or incomplete receipts")
    _require_identity(audit_identity, "audit_identity")
    validated = validate_run_receipt(receipt)
    receipt_payload = validated["payload"]
    if receipt_payload["terminal_state"] != terminal_state or receipt_payload["journal_id"] != journal_id:
      raise LedgerContractError("receipt/journal terminal binding mismatch")
    if receipt_payload["writer_generation"] != str(token.generation):
      raise LedgerContractError("receipt writer generation differs from active journal fence")
    if terminal_state == "completed" and actual_bindings is None:
      raise LedgerContractError("completed receipt requires observed execution provenance")
    if actual_bindings is not None:
      try:
        verify_actual_bindings(receipt_payload, actual_bindings)
      except ValueError as error:
        raise LedgerContractError("receipt actual execution provenance mismatch") from error
    self._verify_checkpoint_references(receipt_payload, role=role)
    self._verify_output_artifacts(receipt_payload, role=role)
    receipt_bytes = canonical_json(validated).encode("utf-8")
    try:
      self._transaction()
      self._assert_fence(token)
      row = self.db.execute("SELECT stream_id,last_sequence,last_record_digest,terminal_state,header_digest FROM journals WHERE journal_id=?", (journal_id,)).fetchone()
      if row is None or row[0] != token.stream_id or row[3] is not None or receipt_payload["journal_last_sequence"] != int(row[1]) or receipt_payload["journal_last_record_sha256"] != row[2]:
        raise LedgerContractError("receipt does not match the last durable journal record")
      if role == "crash_reconciler":
        frame = self.db.execute(
          "SELECT payload FROM frames WHERE journal_id=? AND sequence=? AND fence_generation=?",
          (journal_id, int(row[1]), token.generation),
        ).fetchone()
        recovery_frame_count = self.db.execute(
          "SELECT COUNT(*) FROM frames WHERE journal_id=? AND fence_generation=?",
          (journal_id, token.generation),
        ).fetchone()[0]
        try:
          marker = None if frame is None else json.loads(bytes(frame[0]).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
          marker = None
        termination = None
        tombstone = None
        if isinstance(marker, Mapping):
          identity = (
            row[0], marker.get("prior_writer_generation", -1),
            marker.get("prior_writer_id", ""),
          )
          termination = self.db.execute(
            "SELECT observed_exit_digest FROM terminations "
            "WHERE stream_id=? AND generation=? AND writer_id=?", identity,
          ).fetchone()
          tombstone = self.db.execute(
            "SELECT observed_exit_digest FROM tombstones "
            "WHERE stream_id=? AND generation=? AND writer_id=?", identity,
          ).fetchone()
        if (
          not isinstance(marker, Mapping)
          or marker.get("event") != "crash_reconciled"
          or marker.get("recovery_writer_generation") != token.generation
          or marker.get("recovery_writer_id") != token.writer_id
          or termination is None
          or tombstone is None
          or marker.get("observed_exit_sha256") != termination[0]
          or marker.get("observed_exit_sha256") != tombstone[0]
          or recovery_frame_count != 1
        ):
          raise LedgerContractError(
            "crash receipt lacks the unique durable termination/tombstone marker"
          )
      header_bytes, header_media_type, _ = self.get_blob(row[4], role=role)
      if header_media_type != JOURNAL_HEADER_MEDIA_TYPE:
        raise LedgerContractError("journal header media type integrity failure")
      header = json.loads(header_bytes.decode("utf-8"))
      plan_sha = header.get("plan_sha256") if isinstance(header, Mapping) else None
      if plan_sha is not None and receipt_payload["plan_binding"]["plan_sha256"] != plan_sha:
        raise LedgerContractError("receipt plan binding differs from journal header")
      release_sha = header.get("release_manifest_sha256") if isinstance(header, Mapping) else None
      if release_sha is not None and receipt_payload["release_binding"]["release_manifest_sha256"] != release_sha:
        raise LedgerContractError("receipt release binding differs from journal header")
      receipt_digest = self._put_blob_locked(
        receipt_bytes, media_type=RECEIPT_MEDIA_TYPE,
        retention_class=receipt_payload["retention_class"], audit_identity=audit_identity,
      )
      self.db.execute("INSERT INTO receipts VALUES(?,?,?,?,?)", (receipt_payload["receipt_id"], journal_id, receipt_digest, validated["payload_sha256"], terminal_state))
      self.db.execute(
        "UPDATE journals SET generation=?, writer_id=?, terminal_state=?, finalization_digest=? WHERE journal_id=?",
        (token.generation, token.writer_id, terminal_state, validated["payload_sha256"], journal_id),
      )
      self._audit("journal.finalize", journal_id, validated["payload_sha256"])
      self._finish()
    except Exception:
      self._abort()
      raise
    return receipt_digest

  def _verify_checkpoint_references(self, receipt_payload: Mapping[str, Any], *, role: str) -> None:
    checkpoints = receipt_payload["checkpoints"]
    for collection_name in ("source_refs", "created_refs"):
      for reference in checkpoints[collection_name]:
        checkpoint_id = reference["checkpoint_id"]
        row = self.db.execute(
          "SELECT blob_digest FROM slots WHERE slot_key=?",
          (f"checkpoint:{checkpoint_id}",),
        ).fetchone()
        if row is None or row[0] != reference["checkpoint_sha256"]:
          raise LedgerContractError("receipt checkpoint digest is not the persisted slot digest")
        normalized = self.read_checkpoint(checkpoint_id, role=role)
        checkpoint_payload = normalized["payload"]
        if checkpoint_payload.get("state_schema_generation") != reference["state_schema_generation"]:
          raise LedgerContractError("receipt checkpoint schema generation differs from persisted state")
        identity_fields = [
          ("plan_sha256", receipt_payload["plan_binding"]["plan_sha256"]),
          ("release_id", receipt_payload["release_binding"]["release_id"]),
          ("decision_id", receipt_payload["release_binding"]["rollout_decision_id"]),
        ]
        # A created checkpoint belongs to this run/boot/epoch. A source
        # checkpoint is intentionally allowed to come from an older run or
        # process, but it must still match the executable plan/release graph.
        if collection_name == "created_refs":
          identity_fields.extend((
            ("run_id", receipt_payload["run_id"]),
            ("host_boot_id", receipt_payload["host_boot_id"]),
            ("incarnation_epoch", receipt_payload["incarnation_epoch"]),
          ))
        for checkpoint_field, receipt_value in identity_fields:
          if checkpoint_payload.get(checkpoint_field) != receipt_value:
            raise LedgerContractError(f"receipt checkpoint {checkpoint_field} differs from the run")
        checkpoint_min = int(checkpoint_payload["target_reader_generation_min"])
        checkpoint_max = int(checkpoint_payload["target_reader_generation_max"])
        receipt_min = int(receipt_payload["reader_generation_min"])
        receipt_max = int(receipt_payload["reader_generation_max"])
        if max(checkpoint_min, receipt_min) > min(checkpoint_max, receipt_max):
          raise LedgerContractError(
            "receipt checkpoint target reader generation is incompatible"
          )
        checkpoint_worlds = {
          fragment["world_id"]: set(fragment["episode_ids"])
          for fragment in checkpoint_payload["world_fragments"]
        }
        receipt_worlds = set(receipt_payload["execution_scope"]["world_ids"])
        receipt_episodes = set(receipt_payload["execution_scope"]["episode_ids"])
        if (
          set(checkpoint_worlds) != receipt_worlds
          or set().union(*checkpoint_worlds.values()) != receipt_episodes
          or int(checkpoint_payload["transfer_fence_sequence"]) < 1
        ):
          raise LedgerContractError(
            "receipt checkpoint world, episode, or transfer fence coverage differs"
          )
        if reference["retrieval_location"] != f"ledger://checkpoint-{checkpoint_id}":
          raise LedgerContractError("receipt checkpoint retrieval location is not durable")
        validation = self.db.execute(
          "SELECT payload,media_type FROM blobs WHERE digest=?",
          (reference["validation_sha256"],),
        ).fetchone()
        if validation is None or validation[1] != CHECKPOINT_VALIDATION_MEDIA_TYPE or _sha(bytes(validation[0])) != reference["validation_sha256"]:
          raise LedgerContractError("receipt checkpoint validation evidence is absent or corrupt")
        validation_bytes = bytes(validation[0])
        try:
          validation_document = json.loads(validation_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
          raise LedgerContractError("receipt checkpoint validation evidence is not JSON") from error
        if (
          not isinstance(validation_document, Mapping)
          or not set(validation_document).issubset({
            "accepted", "checkpoint_id", "state_sha256", "validator_id",
            "state_payload_hex", "aggregate_replay_sha256",
          })
          or not {"accepted", "checkpoint_id", "state_sha256", "validator_id"}.issubset(
            validation_document
          )
          or canonical_json_bytes(validation_document) != validation_bytes
          or validation_document["accepted"] is not True
          or validation_document["checkpoint_id"] != checkpoint_id
          or validation_document["state_sha256"] != checkpoint_payload["aggregate_state_sha256"]
        ):
          raise LedgerContractError(
            "receipt checkpoint validation evidence is not accepted or state-bound"
          )
        _require_identity(validation_document["validator_id"], "checkpoint validator_id")
        _require_sha256(validation_document["state_sha256"], "checkpoint validation state_sha256")
        if "state_payload_hex" not in validation_document:
          raise LedgerContractError("checkpoint validation lacks recoverable state bytes")
        try:
          state_bytes = bytes.fromhex(validation_document["state_payload_hex"])
        except (TypeError, ValueError) as error:
          raise LedgerContractError("checkpoint state_payload_hex is invalid") from error
        if _sha(state_bytes) != validation_document["state_sha256"]:
          raise LedgerContractError("checkpoint state bytes do not match state_sha256")

        world_fragments = checkpoint_payload["world_fragments"]
        aggregate_material = canonical_json_bytes({
          "state_schema_generation": checkpoint_payload["state_schema_generation"],
          "transfer_fence_sequence": checkpoint_payload["transfer_fence_sequence"],
          "world_fragments": world_fragments,
        })
        aggregate_replay_sha256 = _sha(aggregate_material)
        if validation_document.get("aggregate_replay_sha256") is None:
          raise LedgerContractError("checkpoint validation lacks replay aggregate evidence")
        _require_sha256(
          validation_document["aggregate_replay_sha256"],
          "checkpoint validation aggregate_replay_sha256",
        )
        if validation_document["aggregate_replay_sha256"] != aggregate_replay_sha256:
          raise LedgerContractError("checkpoint replay aggregate evidence differs")

  def _verify_output_artifacts(self, receipt_payload: Mapping[str, Any], *, role: str) -> None:
    """Require completed outputs to resolve to immutable ledger blobs."""

    if receipt_payload["terminal_state"] != "completed":
      return
    for output in receipt_payload["results"]["output_artifacts"]:
      digest = output["digest"]
      expected_location = f"ledger://blob-{digest}"
      if output["retrieval_location"] != expected_location:
        raise LedgerContractError("completed receipt output retrieval is not content-addressed")
      payload, media_type, retention_class = self.get_blob(digest, role=role)
      if (
        media_type != output["media_type"]
        or retention_class != output["retention_class"]
        or len(payload) != output["size"]
      ):
        raise LedgerContractError("completed receipt output blob metadata differs")

  def recover_crashed_journal(
    self,
    journal_id: str,
    *,
    writer_id: str,
    receipt_builder: Callable[[int, str], Mapping[str, Any]],
    audit_identity: str,
    prior_token: FenceToken | None = None,
  ) -> str:
    row = self.db.execute(
      "SELECT stream_id, generation, writer_id, terminal_state, last_sequence, last_record_digest "
      "FROM journals WHERE journal_id=?", (journal_id,),
    ).fetchone()
    if row is None or row[3] is not None:
      raise LedgerContractError("journal is absent or already finalized")
    # If a prior recovery writer already committed the terminal reconciliation
    # frame but receipt construction/finalization failed, retry from that
    # durable point instead of attempting a second tombstone/fence transition.
    if int(row[4]) >= 0:
      frame = self.db.execute(
        "SELECT payload FROM frames WHERE journal_id=? AND sequence=?",
        (journal_id, int(row[4])),
      ).fetchone()
      if frame is not None:
        try:
          marker = json.loads(bytes(frame[0]).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
          marker = None
        if isinstance(marker, Mapping) and marker.get("event") == "crash_reconciled":
          termination = self.db.execute(
            "SELECT observed_exit_digest FROM terminations WHERE stream_id=? AND generation=? AND writer_id=?",
            (row[0], int(marker.get("prior_writer_generation", -1)), marker.get("prior_writer_id", "")),
          ).fetchone()
          current_fence = self.db.execute(
            "SELECT generation,writer_id FROM fences WHERE stream_id=?", (row[0],),
          ).fetchone()
          if (
            termination is None
            or marker.get("observed_exit_sha256") != termination[0]
            or marker.get("prior_writer_generation") != int(row[1])
            or marker.get("prior_writer_id") != row[2]
            or current_fence is None
            or marker.get("recovery_writer_generation") != int(current_fence[0])
            or marker.get("recovery_writer_id") != current_fence[1]
          ):
            raise LedgerContractError("crash reconciliation marker does not match durable recovery state")
          token = FenceToken(
            row[0], str(marker["recovery_writer_id"]),
            int(marker["recovery_writer_generation"]),
          )
          receipt = receipt_builder(int(row[4]), row[5])
          return self.finalize_journal(
            token, journal_id, receipt=receipt, terminal_state="crashed",
            audit_identity=audit_identity, role="crash_reconciler",
          )
    prior = prior_token or FenceToken(row[0], row[2], int(row[1]))
    if (prior.stream_id, prior.writer_id, prior.generation) != (row[0], row[2], int(row[1])):
      raise LedgerContractError("crash recovery prior fence does not match journal owner")
    if not callable(receipt_builder):
      raise LedgerContractError("crash recovery requires a receipt builder")
    termination_row = self.db.execute(
      "SELECT observed_exit_digest FROM terminations WHERE stream_id=? AND generation=? AND writer_id=?",
      (prior.stream_id, prior.generation, prior.writer_id),
    ).fetchone()
    if termination_row is None:
      proof = self.confirm_process_terminated(prior, audit_identity=audit_identity)
    else:
      proof = TerminationProof(prior.stream_id, prior.writer_id, prior.generation, termination_row[0])
    tombstoned = self.db.execute(
      "SELECT 1 FROM tombstones WHERE stream_id=? AND generation=? AND writer_id=?",
      (prior.stream_id, prior.generation, prior.writer_id),
    ).fetchone() is not None
    if not tombstoned:
      self.tombstone_writer(prior, proof, audit_identity=audit_identity)
    current = self.db.execute(
      "SELECT generation,writer_id FROM fences WHERE stream_id=?", (row[0],),
    ).fetchone()
    if current is not None and int(current[0]) > prior.generation and current[1] == writer_id:
      token = FenceToken(row[0], writer_id, int(current[0]))
    else:
      token = self.acquire_fence(
        row[0], writer_id, expected_generation=prior.generation,
        audit_identity=audit_identity, role="crash_reconciler",
      )
    journal = self.db.execute(
      "SELECT last_sequence FROM journals WHERE journal_id=?", (journal_id,),
    ).fetchone()
    if journal is None:
      raise LedgerContractError("crash recovery journal disappeared")
    terminal_sequence = int(journal[0]) + 1
    terminal_record = canonical_json_bytes({
      "event": "crash_reconciled",
      "observed_exit_sha256": proof.observed_exit_sha256,
      "prior_writer_generation": prior.generation,
      "prior_writer_id": prior.writer_id,
      "recovery_writer_generation": token.generation,
      "recovery_writer_id": token.writer_id,
    })
    terminal_digest = self.append_journal(
      token, journal_id, terminal_record, sequence=terminal_sequence,
      audit_identity=audit_identity, role="crash_reconciler",
    )
    receipt = receipt_builder(terminal_sequence, terminal_digest)
    return self.finalize_journal(
      token, journal_id, receipt=receipt, terminal_state="crashed",
      audit_identity=audit_identity, role="crash_reconciler",
    )

  def read_receipt(self, receipt_id: str, *, role: str = "runtime_host") -> dict[str, Any]:
    self._authorize(role, "blob.get")
    row = self.db.execute(
      "SELECT journal_id, blob_digest, receipt_digest, terminal_state FROM receipts WHERE receipt_id=?",
      (receipt_id,),
    ).fetchone()
    if row is None:
      raise LedgerContractError("receipt is absent")
    payload, media_type, _ = self.get_blob(row[1], role=role)
    if media_type != RECEIPT_MEDIA_TYPE:
      raise LedgerContractError("receipt media type integrity failure")
    try:
      receipt_text = payload.decode("utf-8")
      receipt = json.loads(receipt_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
      raise LedgerContractError("stored receipt is not JSON") from error
    if canonical_json(receipt) != receipt_text:
      raise LedgerContractError("stored receipt is not canonical JSON")
    try:
      normalized = validate_run_receipt(receipt)
    except ValueError as error:
      raise LedgerContractError("stored receipt rejected") from error
    payload = normalized["payload"]
    if (
      payload["receipt_id"] != receipt_id
      or payload["journal_id"] != row[0]
      or payload["terminal_state"] != row[3]
      or normalized["payload_sha256"] != row[2]
    ):
      raise LedgerContractError("stored receipt identity differs from ledger index")
    self._verify_checkpoint_references(payload, role=role)
    self._verify_output_artifacts(payload, role=role)
    return normalized

  def persist_checkpoint(
    self,
    token: FenceToken,
    envelope_bytes: bytes,
    *,
    expected_slot_version: int,
    audit_identity: str,
    role: str = "runtime_host",
  ) -> tuple[str, int]:
    self._authorize(role, "checkpoint.write")
    if role != "runtime_host":
      raise LedgerContractError("checkpoint persistence is runtime_host-only")
    _require_identity(audit_identity, "audit_identity")
    if not isinstance(envelope_bytes, bytes) or not envelope_bytes:
      raise LedgerContractError("checkpoint envelope must be non-empty bytes")
    try:
      envelope = parse_canonical_json_bytes(envelope_bytes)
      normalized = validate_authority_envelope(envelope)
    except (ValueError, UnicodeError) as error:
      raise LedgerContractError("checkpoint envelope rejected") from error
    payload = normalized["payload"]
    if payload.get("authority_kind") != "state_checkpoint":
      raise LedgerContractError("checkpoint persistence requires state-checkpoint authority")
    checkpoint_id = payload["checkpoint_id"]
    key = f"checkpoint:{checkpoint_id}"
    if token.stream_id != key:
      raise LedgerContractError("checkpoint fence stream differs from checkpoint identity")
    if payload.get("writer_generation") != str(token.generation):
      raise LedgerContractError("checkpoint writer generation differs from its fence")
    digest = _sha(envelope_bytes)
    try:
      self._transaction()
      self._assert_fence(token)
      current = self.db.execute("SELECT version FROM slots WHERE slot_key=?", (key,)).fetchone()
      if expected_slot_version != 0 or current is not None:
        raise LedgerContractError("checkpoint conditional create requires an absent slot")
      self._put_blob_locked(
        envelope_bytes, media_type=CHECKPOINT_MEDIA_TYPE,
        retention_class="rollback-window", audit_identity=audit_identity,
        expected_sha256=digest,
      )
      self.db.execute(
        "INSERT INTO slots VALUES(?,?,?,?,?)", (key, 1, digest, token.generation, audit_identity)
      )
      self._audit("checkpoint.create", key, digest)
      self._finish()
    except Exception:
      self._abort()
      raise
    return digest, 1

  def read_checkpoint(self, checkpoint_id: str, *, role: str = "runtime_host") -> dict[str, Any]:
    self._authorize(role, "checkpoint.read")
    row = self.db.execute("SELECT blob_digest FROM slots WHERE slot_key=?", (f"checkpoint:{checkpoint_id}",)).fetchone()
    if row is None:
      raise LedgerContractError("checkpoint slot is absent")
    payload, media_type, _ = self.get_blob(row[0], role=role)
    if media_type != CHECKPOINT_MEDIA_TYPE:
      raise LedgerContractError("checkpoint slot media type is invalid")
    try:
      normalized = validate_authority_envelope(parse_canonical_json_bytes(payload))
    except (ValueError, UnicodeError) as error:
      raise LedgerContractError("stored checkpoint rejected") from error
    if normalized["payload"].get("checkpoint_id") != checkpoint_id:
      raise LedgerContractError("checkpoint slot identity differs from stored authority")
    return normalized

  @staticmethod
  def _validate_rollout_evidence_document(document: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
      "schema_version", "release_id", "decision_id", "decision_payload_sha256",
      "release_manifest_blob_sha256", "release_manifest_payload_sha256",
      "run_receipt_blob_sha256", "run_receipt_payload_sha256", "receipt_id",
      "package_digest", "wheel_digest", "admissions_open",
      "writer_advancement_frozen", "kill_switch_reasons",
    }
    if not isinstance(document, Mapping) or set(document) != expected:
      raise LedgerContractError("rollout evidence binding fields are not exact")
    if document["schema_version"] != ROLLOUT_EVIDENCE_SCHEMA_VERSION:
      raise LedgerContractError("rollout evidence binding schema is unsupported")
    for field in (
      "release_id", "decision_id", "receipt_id",
    ):
      _require_identity(document[field], field)
    for field in (
      "decision_payload_sha256", "release_manifest_blob_sha256",
      "release_manifest_payload_sha256", "run_receipt_blob_sha256",
      "run_receipt_payload_sha256", "package_digest", "wheel_digest",
    ):
      _require_sha256(document[field], field)
    if not isinstance(document["admissions_open"], bool) or not isinstance(document["writer_advancement_frozen"], bool):
      raise LedgerContractError("rollout evidence admission flags are invalid")
    reasons = document["kill_switch_reasons"]
    if not isinstance(reasons, list) or any(not isinstance(item, str) or not item for item in reasons) or reasons != sorted(set(reasons)):
      raise LedgerContractError("rollout evidence kill-switch reasons are invalid")
    if bool(reasons) != (not document["admissions_open"] and document["writer_advancement_frozen"]):
      raise LedgerContractError("rollout evidence kill-switch state is inconsistent")
    return dict(document)

  @staticmethod
  def _rollout_slot_keys(release_id: str) -> tuple[str, str]:
    _require_identity(release_id, "release_id")
    return f"rollout:{release_id}", f"rollout-evidence:{release_id}"

  def _read_blob_locked(self, digest: str) -> tuple[bytes, str, str]:
    _require_sha256(digest, "blob digest")
    row = self.db.execute(
      "SELECT payload,media_type,retention_class,size FROM blobs WHERE digest=?",
      (digest,),
    ).fetchone()
    if row is None:
      raise LedgerContractError("blob is absent")
    payload = bytes(row[0])
    if _sha(payload) != digest or int(row[3]) != len(payload):
      raise LedgerContractError("blob digest or size verification failed")
    return payload, str(row[1]), str(row[2])

  def commit_rollout_admission(
    self,
    token: FenceToken,
    decision: Mapping[str, Any],
    *,
    release_manifest: Mapping[str, Any],
    run_receipt: Mapping[str, Any],
    verification_key: bytes,
    audit_identity: str,
    expected_slot_version: int = 0,
    admissions_open: bool = True,
    writer_advancement_frozen: bool = False,
    kill_switch_reasons: tuple[str, ...] = (),
    expected_package_digest: str | None = None,
    expected_wheel_digest: str | None = None,
    role: str = "release_controller",
  ) -> tuple[int, dict[str, Any]]:
    """Atomically commit a release decision and its evidence binding.

    This is the P5-D release-controller boundary on top of the qualified
    SQLite ArtifactLedger. Release, decision, receipt, and the evidence
    projection are content-addressed in the same transaction as the two CAS
    slots. The method does not publish a runtime host; it only makes a durable
    admission record available to a later runtime reader.
    """

    self._authorize(role, "slot.write")
    _require_identity(audit_identity, "audit_identity")
    if not isinstance(expected_slot_version, int) or isinstance(expected_slot_version, bool) or expected_slot_version < 0:
      raise LedgerContractError("expected rollout slot version is invalid")
    try:
      normalized_decision = validate_rollout_envelope(
        decision,
        verification_key=verification_key,
      )
      normalized_release = validate_authority_envelope(release_manifest)
      normalized_receipt = validate_run_receipt(run_receipt)
    except (RolloutAdmissionError, ValueError, TypeError) as error:
      raise LedgerContractError("rollout admission authority validation failed") from error
    if normalized_release["media_type"] != RELEASE_MANIFEST_MEDIA_TYPE:
      raise LedgerContractError("rollout release manifest media type is invalid")
    if normalized_receipt["media_type"] != RECEIPT_MEDIA_TYPE:
      raise LedgerContractError("rollout RunReceipt media type is invalid")
    decision_payload = normalized_decision["payload"]
    release_id = decision_payload["release_id"]
    decision_key, evidence_key = self._rollout_slot_keys(release_id)
    if token.stream_id != decision_key:
      raise LedgerContractError("rollout fence stream differs from release identity")
    if decision_payload["manifest_sha256"] != normalized_release["payload_sha256"]:
      raise LedgerContractError("rollout decision does not name the supplied release manifest")
    try:
      binding = project_rollout_evidence(normalized_release, normalized_receipt)
      assert_rollout_evidence_decision_binding(
        normalized_decision,
        binding,
        expected_package_digest=expected_package_digest,
        expected_wheel_digest=expected_wheel_digest,
      )
    except (RolloutEvidenceError, ValueError, TypeError, KeyError) as error:
      raise LedgerContractError("rollout release/receipt evidence binding failed") from error
    if binding.release_id != release_id or binding.receipt_id != normalized_receipt["payload"]["receipt_id"]:
      raise LedgerContractError("rollout evidence release or receipt identity differs")
    if (
      not isinstance(admissions_open, bool)
      or not isinstance(writer_advancement_frozen, bool)
      or (admissions_open, writer_advancement_frozen) not in ((True, False), (False, True))
    ):
      raise LedgerContractError("rollout admission flags must be open/unfrozen or closed/frozen")
    if not isinstance(kill_switch_reasons, (tuple, list)) or any(
      not isinstance(reason, str) or not reason for reason in kill_switch_reasons
    ):
      raise LedgerContractError("rollout kill-switch reasons are invalid")
    reasons = tuple(sorted(set(kill_switch_reasons)))
    if bool(reasons) != (not admissions_open and writer_advancement_frozen):
      raise LedgerContractError("rollout kill-switch reasons differ from admission state")
    if decision_payload["state"] == "backed-out":
      if decision_payload["irreversible_write_boundary"] != "none":
        raise LedgerContractError("rollout backout is forbidden after the irreversible write boundary")
      admissions_open = False
      writer_advancement_frozen = True
      reasons = tuple(sorted(set((*reasons, "typed-backout"))))
    try:
      release_bytes = canonical_json_bytes(normalized_release)
      decision_bytes = canonical_json_bytes(normalized_decision)
      receipt_bytes = canonical_json(normalized_receipt).encode("utf-8")
      release_blob_digest = _sha(release_bytes)
      decision_blob_digest = _sha(decision_bytes)
      receipt_blob_digest = _sha(receipt_bytes)
      evidence_document = {
        "schema_version": ROLLOUT_EVIDENCE_SCHEMA_VERSION,
        "release_id": release_id,
        "decision_id": decision_payload["decision_id"],
        "decision_payload_sha256": normalized_decision["payload_sha256"],
        "release_manifest_blob_sha256": release_blob_digest,
        "release_manifest_payload_sha256": normalized_release["payload_sha256"],
        "run_receipt_blob_sha256": receipt_blob_digest,
        "run_receipt_payload_sha256": normalized_receipt["payload_sha256"],
        "receipt_id": binding.receipt_id,
        "package_digest": binding.package_digest,
        "wheel_digest": binding.wheel_digest,
        "admissions_open": bool(admissions_open),
        "writer_advancement_frozen": bool(writer_advancement_frozen),
        "kill_switch_reasons": list(reasons),
      }
      evidence_document = self._validate_rollout_evidence_document(evidence_document)
      evidence_bytes = canonical_json_bytes(evidence_document)
      evidence_blob_digest = _sha(evidence_bytes)
    except (KeyError, TypeError, ValueError) as error:
      raise LedgerContractError("rollout evidence projection could not be materialized") from error
    previous: dict[str, Any] | None = None
    current_version = 0
    try:
      self._transaction()
      self._assert_fence(token)
      current_row = self.db.execute(
        "SELECT version,blob_digest FROM slots WHERE slot_key=?",
        (decision_key,),
      ).fetchone()
      current_evidence_row = self.db.execute(
        "SELECT version,blob_digest FROM slots WHERE slot_key=?",
        (evidence_key,),
      ).fetchone()
      if current_row is None:
        if expected_slot_version != 0:
          raise LedgerContractError("rollout slot compare-and-swap predecessor mismatch")
        if current_evidence_row is not None:
          raise LedgerContractError("rollout evidence slot exists without its decision slot")
        if decision_payload["state"] != "prepared" or decision_payload["decision_sequence"] != "0" or decision_payload["predecessor_decision_id"]:
          raise LedgerContractError("rollout slot must begin with prepared sequence zero")
      else:
        current_version = int(current_row[0])
        if expected_slot_version != current_version:
          raise LedgerContractError("rollout slot compare-and-swap predecessor mismatch")
        if current_evidence_row is None or int(current_evidence_row[0]) < current_version:
          raise LedgerContractError("rollout decision/evidence slot versions diverged")
        prior_bytes, prior_media, _ = self._read_blob_locked(str(current_row[1]))
        if prior_media != ROLLOUT_DECISION_MEDIA_TYPE:
          raise LedgerContractError("stored rollout decision media type is invalid")
        try:
          previous = validate_rollout_envelope(
            parse_canonical_json_bytes(prior_bytes),
            verification_key=verification_key,
          )
        except (RolloutAdmissionError, ValueError, TypeError) as error:
          raise LedgerContractError("stored rollout predecessor is invalid") from error
        previous_payload = previous["payload"]
        if decision_payload["release_id"] != previous_payload["release_id"] or decision_payload["manifest_sha256"] != previous_payload["manifest_sha256"]:
          raise LedgerContractError("rollout release binding changed")
        try:
          validate_rollout_transition(previous, normalized_decision)
        except Exception as error:
          raise LedgerContractError("rollout predecessor/sequence transition is invalid") from error
        if decision_payload["state"] not in ROLLOUT_TRANSITIONS[previous_payload["state"]]:
          raise LedgerContractError("rollout state transition is not admitted")
        writer_changed = decision_payload["writer_generation"] != previous_payload["writer_generation"]
        plan_changed = decision_payload["plan_sha256"] != previous_payload["plan_sha256"]
        if writer_changed != plan_changed:
          raise LedgerContractError("rollout writer and plan changed independently")
        if plan_changed and decision_payload["state"] not in {"adoption-expanding", "backed-out"}:
          raise LedgerContractError("rollout plan changed outside advancement/backout")
        if writer_changed:
          expected_generation = int(previous_payload["writer_generation"]) - 1 if decision_payload["state"] == "backed-out" else int(previous_payload["writer_generation"]) + 1
          if int(decision_payload["writer_generation"]) != expected_generation:
            raise LedgerContractError("rollout writer generation is not adjacent")
        prior_evidence_bytes, prior_evidence_media, _ = self._read_blob_locked(str(current_evidence_row[1]))
        if prior_evidence_media != ROLLOUT_EVIDENCE_MEDIA_TYPE:
          raise LedgerContractError("stored rollout evidence media type is invalid")
        prior_evidence = self._validate_rollout_evidence_document(
          parse_canonical_json_bytes(prior_evidence_bytes),
        )
        if (
          prior_evidence["release_manifest_blob_sha256"] != release_blob_digest
          or prior_evidence["release_manifest_payload_sha256"] != normalized_release["payload_sha256"]
        ):
          raise LedgerContractError("rollout release manifest changed")
        if not prior_evidence["admissions_open"] and not (
          decision_payload["state"] == "backed-out"
          or (previous_payload["state"] == "backed-out" and decision_payload["state"] == "prepared")
        ):
          raise LedgerContractError("closed rollout admission requires typed backout repair")
      self._validate_media(role, RELEASE_MANIFEST_MEDIA_TYPE, write=True)
      self._validate_media(role, ROLLOUT_DECISION_MEDIA_TYPE, write=True)
      self._validate_media(role, RECEIPT_MEDIA_TYPE, write=True)
      self._validate_media(role, ROLLOUT_EVIDENCE_MEDIA_TYPE, write=True)
      self._put_blob_locked(
        release_bytes, media_type=RELEASE_MANIFEST_MEDIA_TYPE,
        retention_class="active-release", audit_identity=audit_identity,
        expected_sha256=release_blob_digest,
      )
      self._put_blob_locked(
        decision_bytes, media_type=ROLLOUT_DECISION_MEDIA_TYPE,
        retention_class="rollback-window", audit_identity=audit_identity,
        expected_sha256=decision_blob_digest,
      )
      self._put_blob_locked(
        receipt_bytes, media_type=RECEIPT_MEDIA_TYPE,
        retention_class="run-retained", audit_identity=audit_identity,
        expected_sha256=receipt_blob_digest,
      )
      self._put_blob_locked(
        evidence_bytes, media_type=ROLLOUT_EVIDENCE_MEDIA_TYPE,
        retention_class="rollback-window", audit_identity=audit_identity,
        expected_sha256=evidence_blob_digest,
      )
      next_version = current_version + 1
      if current_row is None:
        self.db.execute(
          "INSERT INTO slots VALUES(?,?,?,?,?)",
          (decision_key, next_version, decision_blob_digest, token.generation, audit_identity),
        )
        self.db.execute(
          "INSERT INTO slots VALUES(?,?,?,?,?)",
          (evidence_key, next_version, evidence_blob_digest, token.generation, audit_identity),
        )
      else:
        updated = self.db.execute(
          "UPDATE slots SET version=?,blob_digest=?,fence_generation=?,audit_identity=? WHERE slot_key=? AND version=?",
          (next_version, decision_blob_digest, token.generation, audit_identity, decision_key, current_version),
        ).rowcount
        evidence_updated = self.db.execute(
          "UPDATE slots SET version=?,blob_digest=?,fence_generation=?,audit_identity=? WHERE slot_key=? AND version=?",
          (next_version, evidence_blob_digest, token.generation, audit_identity, evidence_key, int(current_evidence_row[0])),
        ).rowcount
        if updated != 1 or evidence_updated != 1:
          raise LedgerContractError("rollout decision/evidence CAS lost")
      self._audit("rollout.commit", decision_key, decision_blob_digest)
      self._audit("rollout.evidence", evidence_key, evidence_blob_digest)
      self._finish()
    except Exception:
      self._abort()
      raise
    return next_version, evidence_document

  def read_rollout_admission(
    self,
    release_id: str,
    *,
    verification_key: bytes,
    role: str = "runtime_evidence",
  ) -> dict[str, Any]:
    """Read and revalidate the durable release/decision/receipt admission."""

    self._authorize(role, "blob.get")
    decision_key, evidence_key = self._rollout_slot_keys(release_id)
    decision_row = self.db.execute(
      "SELECT version,blob_digest FROM slots WHERE slot_key=?", (decision_key,)
    ).fetchone()
    evidence_row = self.db.execute(
      "SELECT version,blob_digest FROM slots WHERE slot_key=?", (evidence_key,)
    ).fetchone()
    if decision_row is None or evidence_row is None:
      raise LedgerContractError("rollout admission slot is absent")
    if int(evidence_row[0]) < int(decision_row[0]):
      raise LedgerContractError("rollout decision/evidence slot versions diverged")
    decision_bytes, decision_media, _ = self.get_blob(str(decision_row[1]), role=role)
    evidence_bytes, evidence_media, _ = self.get_blob(str(evidence_row[1]), role=role)
    if decision_media != ROLLOUT_DECISION_MEDIA_TYPE or evidence_media != ROLLOUT_EVIDENCE_MEDIA_TYPE:
      raise LedgerContractError("rollout admission media type is invalid")
    try:
      decision = validate_rollout_envelope(
        parse_canonical_json_bytes(decision_bytes),
        verification_key=verification_key,
      )
      evidence = self._validate_rollout_evidence_document(parse_canonical_json_bytes(evidence_bytes))
      release_digest = evidence["release_manifest_blob_sha256"]
      receipt_digest = evidence["run_receipt_blob_sha256"]
      release_bytes, release_media, _ = self.get_blob(release_digest, role=role)
      receipt_bytes, receipt_media, _ = self.get_blob(receipt_digest, role=role)
      if release_media != RELEASE_MANIFEST_MEDIA_TYPE or receipt_media != RECEIPT_MEDIA_TYPE:
        raise LedgerContractError("rollout evidence authority media type is invalid")
      release = validate_authority_envelope(parse_canonical_json_bytes(release_bytes))
      receipt = validate_run_receipt(json.loads(receipt_bytes.decode("utf-8")))
      binding = project_rollout_evidence(release, receipt)
      assert_rollout_evidence_decision_binding(decision, binding)
    except (RolloutAdmissionError, RolloutEvidenceError, ValueError, TypeError) as error:
      raise LedgerContractError("durable rollout admission validation failed") from error
    if decision["payload"]["release_id"] != release_id or evidence["release_id"] != release_id:
      raise LedgerContractError("rollout admission release identity differs from slot")
    if (
      evidence["decision_id"] != decision["payload"]["decision_id"]
      or evidence["decision_payload_sha256"] != decision["payload_sha256"]
    ):
      raise LedgerContractError("rollout evidence decision digest differs")
    if (
      evidence["receipt_id"] != binding.receipt_id
      or evidence["package_digest"] != binding.package_digest
      or evidence["wheel_digest"] != binding.wheel_digest
      or evidence["release_manifest_payload_sha256"] != release["payload_sha256"]
      or evidence["run_receipt_payload_sha256"] != receipt["payload_sha256"]
    ):
      raise LedgerContractError("rollout evidence authority digest differs")
    return {
      "version": int(decision_row[0]),
      "evidence_version": int(evidence_row[0]),
      "decision": decision,
      "release_manifest": release,
      "run_receipt": receipt,
      "evidence": evidence,
      "admissions_open": evidence["admissions_open"],
      "writer_advancement_frozen": evidence["writer_advancement_frozen"],
      "kill_switch_reasons": tuple(evidence["kill_switch_reasons"]),
    }

  def read_rollout_snapshot(
    self,
    release_id: str,
    *,
    verification_key: bytes,
    role: str = "runtime_evidence",
  ) -> dict[str, Any]:
    """Return a slot-compatible snapshot for a facade admission reader."""

    admission = self.read_rollout_admission(
      release_id,
      verification_key=verification_key,
      role=role,
    )
    decision = admission["decision"]
    slot = {
      "schema_version": ROLLOUT_SLOT_SCHEMA_VERSION,
      "decision": decision,
      "decision_sha256": _sha(canonical_json_bytes(decision)),
      "admissions_open": admission["admissions_open"],
      "writer_advancement_frozen": admission["writer_advancement_frozen"],
      "kill_switch_reasons": list(admission["kill_switch_reasons"]),
    }
    return {
      "slot": slot,
      "release_manifest": admission["release_manifest"],
      "run_receipt": admission["run_receipt"],
    }

  def read_rollout_retention(
    self,
    release_id: str,
    *,
    verification_key: bytes,
    role: str = "runtime_evidence",
  ) -> dict[str, Any]:
    """Verify that the live rollout authority blobs retain their rollback roles.

    The admission reader already validates the authority graph.  This
    projection adds the storage-side invariant needed by P5-D: the release,
    decision, RunReceipt, and evidence blobs must remain present with the
    retention class assigned by the durable rollout transaction.  It is a
    read-only check and does not advance or rewrite the rollout slot.
    """

    admission = self.read_rollout_admission(
      release_id,
      verification_key=verification_key,
      role=role,
    )
    decision_digest = _sha(canonical_json_bytes(admission["decision"]))
    evidence_digest = _sha(canonical_json_bytes(admission["evidence"]))
    evidence = admission["evidence"]
    references = (
      ("release_manifest", evidence["release_manifest_blob_sha256"], RELEASE_MANIFEST_MEDIA_TYPE, "active-release"),
      ("rollout_decision", decision_digest, ROLLOUT_DECISION_MEDIA_TYPE, "rollback-window"),
      ("run_receipt", evidence["run_receipt_blob_sha256"], RECEIPT_MEDIA_TYPE, "run-retained"),
      ("rollout_evidence", evidence_digest, ROLLOUT_EVIDENCE_MEDIA_TYPE, "rollback-window"),
    )
    blobs: dict[str, dict[str, Any]] = {}
    for name, digest, expected_media_type, expected_retention in references:
      media_type, size, retention_class, audit_identity = self.stat_blob(
        digest,
        role=role,
      )
      if media_type != expected_media_type:
        raise LedgerContractError(f"rollout retention media type differs for {name}")
      if retention_class != expected_retention:
        raise LedgerContractError(f"rollout retention class differs for {name}")
      blobs[name] = {
        "digest": digest,
        "media_type": media_type,
        "size": size,
        "retention_class": retention_class,
        "audit_identity": audit_identity,
      }
    return {
      "schema_version": "echelon_forge.rollout_retention_check.v1",
      "release_id": release_id,
      "state": admission["decision"]["payload"]["state"],
      "slot_version": admission["version"],
      "evidence_version": admission["evidence_version"],
      "blobs": blobs,
    }

  def trip_rollout_kill_switch(
    self,
    token: FenceToken,
    reasons: list[str],
    *,
    verification_key: bytes,
    audit_identity: str,
    role: str = "release_controller",
  ) -> dict[str, Any]:
    """Close rollout admission without changing the decision payload."""

    self._authorize(role, "slot.write")
    _require_identity(audit_identity, "audit_identity")
    if not reasons or any(not isinstance(reason, str) or not reason for reason in reasons):
      raise LedgerContractError("rollout kill switch requires typed reasons")
    if not token.stream_id.startswith("rollout:"):
      raise LedgerContractError("rollout kill switch requires a rollout fence")
    current = self.read_rollout_admission(
      token.stream_id.removeprefix("rollout:"),
      verification_key=verification_key,
      role=role,
    )
    evidence = dict(current["evidence"])
    evidence["admissions_open"] = False
    evidence["writer_advancement_frozen"] = True
    evidence["kill_switch_reasons"] = sorted(set((*evidence["kill_switch_reasons"], *reasons)))
    evidence = self._validate_rollout_evidence_document(evidence)
    evidence_bytes = canonical_json_bytes(evidence)
    evidence_digest = _sha(evidence_bytes)
    _, evidence_key = self._rollout_slot_keys(token.stream_id.removeprefix("rollout:"))
    try:
      self._transaction()
      self._assert_fence(token)
      row = self.db.execute("SELECT version FROM slots WHERE slot_key=?", (evidence_key,)).fetchone()
      if row is None or int(row[0]) != int(current["evidence_version"]):
        raise LedgerContractError("rollout kill-switch CAS predecessor mismatch")
      self._put_blob_locked(
        evidence_bytes, media_type=ROLLOUT_EVIDENCE_MEDIA_TYPE,
        retention_class="rollback-window", audit_identity=audit_identity,
        expected_sha256=evidence_digest,
      )
      updated = self.db.execute(
        "UPDATE slots SET version=?,blob_digest=?,fence_generation=?,audit_identity=? WHERE slot_key=? AND version=?",
        (int(row[0]) + 1, evidence_digest, token.generation, audit_identity, evidence_key, int(row[0])),
      ).rowcount
      if updated != 1:
        raise LedgerContractError("rollout kill-switch CAS lost")
      self._audit("rollout.kill", evidence_key, evidence_digest)
      self._finish()
    except Exception:
      self._abort()
      raise
    # Re-read is intentionally performed after commit so callers observe the
    # durable closed state rather than an in-memory projection.
    return self.read_rollout_admission(
      token.stream_id.removeprefix("rollout:"),
      verification_key=verification_key,
      role=role,
    )

  def read_journal(self, journal_id: str, *, role: str = "runtime_host") -> tuple[dict[str, Any], tuple[tuple[int, str, str], ...]]:
    self._authorize(role, "journal.read" if role == "runtime_evidence" else "blob.get")
    row = self.db.execute("SELECT stream_id,generation,writer_id,header_digest,last_sequence,last_record_digest,terminal_state,finalization_digest FROM journals WHERE journal_id=?", (journal_id,)).fetchone()
    if row is None:
      raise LedgerContractError("journal is absent")
    header_payload, header_media_type, _ = self.get_blob(row[3], role=role)
    if header_media_type != JOURNAL_HEADER_MEDIA_TYPE:
      raise LedgerContractError("journal header media type integrity failure")
    try:
      header = json.loads(header_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
      raise LedgerContractError("journal header is not canonical JSON") from error
    if not isinstance(header, Mapping) or header.get("run_id") != journal_id or header_payload != canonical_json(header).encode("utf-8"):
      raise LedgerContractError("journal header run identity differs from journal stream")
    frames = []
    prior = "0" * 64
    previous_fence = 0
    for expected_sequence, (sequence, fence_generation, payload, payload_digest, prior_digest, frame_digest, frame_length, frame_checksum) in enumerate(self.db.execute("SELECT sequence,fence_generation,payload,payload_digest,prior_digest,frame_digest,frame_length,frame_checksum FROM frames WHERE journal_id=? ORDER BY sequence", (journal_id,))):
      frame_body = canonical_json_bytes({
        "fence_generation": fence_generation,
        "journal_id": journal_id,
        "payload_sha256": payload_digest,
        "payload_size": len(payload),
        "prior_record_sha256": prior_digest,
        "sequence": sequence,
        "stream_id": row[0],
      })
      expected = _sha(frame_body)
      if (
        sequence != expected_sequence or expected != frame_digest or prior_digest != prior or
        _sha(bytes(payload)) != payload_digest or frame_length != len(frame_body) + 4 or
        frame_checksum != zlib.crc32(frame_body) or fence_generation < previous_fence or
        fence_generation > row[1]
      ):
        raise LedgerContractError("journal frame integrity failure")
      frames.append((sequence, payload_digest, frame_digest))
      prior = frame_digest
      previous_fence = fence_generation
    expected_last_sequence = len(frames) - 1
    expected_last_digest = frames[-1][2] if frames else "0" * 64
    if row[4] != expected_last_sequence or row[5] != expected_last_digest:
      raise LedgerContractError("journal last-record digest mismatch")
    return {"stream_id": row[0], "generation": row[1], "writer_id": row[2], "header_digest": row[3], "last_sequence": row[4], "terminal_state": row[6], "finalization_digest": row[7]}, tuple(frames)

  def backup_to(self, target: str | Path) -> None:
    target_path = Path(target)
    if target_path.resolve() == self.db_path.resolve():
      raise LedgerContractError("backup target must differ from the live ledger")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_db = sqlite3.connect(target_path)
    try:
      self.db.backup(target_db)
      target_db.execute("PRAGMA synchronous=FULL")
    finally:
      target_db.close()

  @classmethod
  def restore_from(cls, source: str | Path, root: str | Path) -> "SQLiteArtifactLedger":
    """Restore a closed SQLite backup into a fresh ledger root."""

    source_path = Path(source).resolve()
    if not source_path.is_file():
      raise LedgerContractError("restore source backup is absent")
    target_root = Path(root)
    target_root.mkdir(parents=True, exist_ok=True)
    target_path = (target_root / "artifact-ledger.sqlite3").resolve()
    if source_path == target_path:
      raise LedgerContractError("restore source and target must differ")
    if target_path.exists():
      raise LedgerContractError("restore target already exists")
    source_db = sqlite3.connect(source_path)
    target_db: sqlite3.Connection | None = None
    try:
      cls._validate_schema_identity(source_db, context="restore source")
      target_db = sqlite3.connect(target_path)
      source_db.backup(target_db)
      integrity = target_db.execute("PRAGMA integrity_check").fetchone()[0]
      if integrity != "ok":
        raise LedgerContractError(f"restored SQLite integrity check failed: {integrity}")
      if target_db.execute("PRAGMA foreign_key_check").fetchall():
        raise LedgerContractError("restored SQLite foreign-key check failed")
    finally:
      if target_db is not None:
        target_db.close()
      source_db.close()
    restored: SQLiteArtifactLedger | None = None
    try:
      restored = cls(target_root)
      journal_ids = tuple(row[0] for row in restored.db.execute("SELECT journal_id FROM journals"))
      receipt_ids = tuple(row[0] for row in restored.db.execute("SELECT receipt_id FROM receipts"))
      checkpoint_ids = tuple(
        row[0][len("checkpoint:"):]
        for row in restored.db.execute("SELECT slot_key FROM slots WHERE slot_key LIKE 'checkpoint:%'")
      )
      for journal_id in journal_ids:
        restored.read_journal(journal_id)
      for receipt_id in receipt_ids:
        restored.read_receipt(receipt_id)
      for checkpoint_id in checkpoint_ids:
        restored.read_checkpoint(checkpoint_id)
    except Exception:
      if restored is not None:
        restored.close()
        restored = None
      for sidecar in (target_path, Path(f"{target_path}-wal"), Path(f"{target_path}-shm")):
        try:
          sidecar.unlink()
        except FileNotFoundError:
          pass
      raise
    finally:
      if restored is not None:
        restored.close()
    return cls(target_root)

  def audit_rows(self) -> tuple[tuple[int, str, str, str], ...]:
    return tuple(self.db.execute("SELECT sequence,operation,object_id,digest FROM audit ORDER BY sequence"))
