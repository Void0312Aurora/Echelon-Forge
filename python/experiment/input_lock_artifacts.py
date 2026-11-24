"""Experiment-owned handoff of the two resolved input-lock file roles.

The projection loader reads the full ``resolved_experiment`` document. Native
provenance collection instead measures the exact canonical ``input_lock``
payload bytes. These are separate files with one existing input identity; no
receipt, completion evidence, or additional manifest is created here.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from python.experiment.resolved_input_lock import (
    InputLockError,
    ResolvedInputLock,
    canonical_json_bytes,
    load_resolved_input_lock_path,
)


def _artifact_paths(
    projection_path: str | Path, native_input_lock_path: str | Path
) -> tuple[Path, Path]:
    projection = Path(projection_path)
    native_input_lock = Path(native_input_lock_path)
    if projection.resolve() == native_input_lock.resolve() or (
        projection.exists()
        and native_input_lock.exists()
        and projection.samefile(native_input_lock)
    ):
        raise InputLockError("input_lock.artifact_paths_must_differ")
    return projection, native_input_lock


def write_resolved_input_lock_artifacts(
    candidate: ResolvedInputLock,
    *,
    projection_path: str | Path,
    native_input_lock_path: str | Path,
) -> None:
    """Export an unjoined owner projection and its canonical native payload.

    ``projection_path`` is for the existing projection loader and adapter's
    ``production_resolved_input_lock_path``. ``native_input_lock_path`` is for
    native ``RuntimeExecutionProvenanceSources.resolved_input_lock_path``.
    The latter file's raw SHA-256 equals ``candidate.digest``; the full
    projection file's raw SHA-256 is not the input-lock identity.

    Both parent directories must already exist. This is a two-file export,
    not a transaction: validate the pair before handing it to a runtime.
    """

    projection, native_input_lock = _artifact_paths(projection_path, native_input_lock_path)
    document = candidate.as_dict()
    if "completion_evidence" in document:
        raise InputLockError("input_lock.unjoined_projection_required")
    payload_bytes = canonical_json_bytes(document["input_lock"])
    if hashlib.sha256(payload_bytes).hexdigest() != candidate.digest:
        raise InputLockError("input_lock.identity_mismatch")
    projection_bytes = canonical_json_bytes(document)
    native_input_lock.write_bytes(payload_bytes)
    projection.write_bytes(projection_bytes)


def load_resolved_input_lock_artifacts(
    *,
    projection_path: str | Path,
    native_input_lock_path: str | Path,
) -> ResolvedInputLock:
    """Use the existing projection reader, then verify its exact native bytes.

    Successful loading verifies input identity only. It does not attest
    execution, durable storage, generation health, or receipt completion.
    """

    projection, native_input_lock = _artifact_paths(projection_path, native_input_lock_path)
    candidate = load_resolved_input_lock_path(projection)
    try:
        raw = native_input_lock.read_bytes()
    except OSError as exc:
        raise InputLockError(f"input_lock.native_artifact_unreadable:{native_input_lock}") from exc
    if hashlib.sha256(raw).hexdigest() != candidate.digest:
        raise InputLockError("input_lock.native_artifact_digest_mismatch")
    return candidate
