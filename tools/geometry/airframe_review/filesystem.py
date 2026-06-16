"""Filesystem helpers shared by airframe review subdomains."""

from __future__ import annotations

import hashlib
from pathlib import Path


def display_path(path: Path, repo_root: Path) -> str:
  try:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
  except ValueError:
    return str(path)


def sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()
