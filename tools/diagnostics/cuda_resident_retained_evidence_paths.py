"""Logical-to-physical path resolution for retained CUDA-resident evidence.

The CR2/RB evidence manifests record their inputs and outputs under the
`docs/plan/exact_runtime/` prefix, which is where those packets lived when the
evidence was captured. The documentation ownership migration moved the retained
packet to `tests/fixtures/runtime_profiles/cuda_resident_program_2/`, but the
manifests are byte-stable evidence: rewriting a recorded path would invalidate
the canonical byte counts and SHA-256 digests that pin each descriptor, and a
regenerated hash is no longer the hash that was reviewed.

So the recorded prefix stays as the *logical* identity of a descriptor, and this
module is the single place that maps it onto the *physical* location on disk.
Readers resolve through `physical_relative`; writers that must not recreate the
retired tree resolve through the same function before opening a path.

Keeping one owner for this mapping matters because the translation used to be
duplicated as an inline `str.replace` at every call site, and the matrix
evidence collector was missed — it resolved recorded paths verbatim and failed
on its first manifest read once the packet moved.
"""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

LOGICAL_EVIDENCE_PREFIX = "docs/plan/exact_runtime/"
PHYSICAL_EVIDENCE_PREFIX = "tests/fixtures/runtime_profiles/cuda_resident_program_2/"


def physical_relative(recorded: str) -> str:
    """Map a manifest-recorded repository-relative path to its location on disk.

    Paths that do not carry the logical prefix are returned unchanged, so this
    is safe to apply to every descriptor rather than only the known-migrated
    ones.
    """
    if recorded.startswith(LOGICAL_EVIDENCE_PREFIX):
        return PHYSICAL_EVIDENCE_PREFIX + recorded[len(LOGICAL_EVIDENCE_PREFIX):]
    return recorded


def logical_relative(physical: str) -> str:
    """Inverse of `physical_relative`, for comparing against recorded values."""
    if physical.startswith(PHYSICAL_EVIDENCE_PREFIX):
        return LOGICAL_EVIDENCE_PREFIX + physical[len(PHYSICAL_EVIDENCE_PREFIX):]
    return physical


def physical_path(root: Path, recorded: str) -> Path:
    """Resolve a recorded path under `root`, applying the logical mapping."""
    return root / Path(physical_relative(recorded))


def logical_path_of(root: Path, path: Path) -> str:
    """Return the logical repository-relative spelling of an on-disk path."""
    return logical_relative(PurePosixPath(path.relative_to(root).as_posix()).as_posix())


def canonical_source_bytes(path: Path, root: Path, commit: str | None = None) -> bytes:
    """Read current or historical source bytes with the evidence line ending rule."""
    if commit is None:
        payload = path.read_bytes()
    else:
        payload = subprocess.run(
            ["git", "show", f"{commit}:{path.relative_to(root).as_posix()}"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    return payload.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
