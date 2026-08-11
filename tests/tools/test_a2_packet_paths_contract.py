"""Contract tests for the retained A2 packet's production filesystem paths.

Every prior test for the retained-evidence tooling built its inputs under
``tmp_path``, so none of them ever resolved the production defaults. When the
ownership-first documentation migration moved the A2 packet out of
``docs/task/air_combat/archive/``, those defaults silently pointed at a removed
tree: the manifest glob matched nothing, every integrity counter read zero, and
the tool exited 0 while verifying no artifact at all.

These tests assert the production surface directly -- that the packet locations
exist, that a scan of them sees a non-empty inventory, that an empty inventory
fails closed, and that no tool writes into a retired documentation root.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tools.maintenance import a2_packet_paths as paths
from tools.maintenance.retained_artifacts import manifest_integrity as integrity


RETIRED_DOC_ROOTS = (
  "docs/task/",
  "docs/plan/",
  "docs/standards/",
  "docs/evaluation/archive/",
  "docs/manual/archive/",
)


def test_production_packet_directories_exist() -> None:
  assert paths.PACKET_ROOT.is_dir(), paths.PACKET_ROOT
  assert paths.CANDIDATE_PACKAGE_DIR.is_dir(), paths.CANDIDATE_PACKAGE_DIR
  assert paths.RETAINED_ARTIFACTS_DIR.is_dir(), paths.RETAINED_ARTIFACTS_DIR
  assert paths.DATA_COLLECTION_DIR.is_dir(), paths.DATA_COLLECTION_DIR


def test_relative_and_absolute_packet_forms_agree() -> None:
  assert paths.packet_root(paths.REPO_ROOT) == paths.PACKET_ROOT
  assert (
    paths.candidate_package_dir(paths.REPO_ROOT) == paths.CANDIDATE_PACKAGE_DIR
  )


def test_require_candidate_package_dir_accepts_the_production_location() -> None:
  assert paths.require_candidate_package_dir() == paths.CANDIDATE_PACKAGE_DIR


def test_integrity_default_package_dir_is_the_owner_root() -> None:
  assert integrity.CANDIDATE_PACKAGE_DIR == paths.CANDIDATE_PACKAGE_DIR
  resolved = integrity.CANDIDATE_PACKAGE_DIR.as_posix()
  for retired in RETIRED_DOC_ROOTS:
    assert retired not in resolved, resolved


def test_production_scan_sees_a_non_empty_manifest_inventory() -> None:
  """The regression this suite exists for: a zero-manifest scan is not clean."""
  manifests = sorted(
    paths.CANDIDATE_PACKAGE_DIR.glob(integrity.DEFAULT_MANIFEST_GLOB)
  )

  assert manifests, (
    "no retained manifests matched the production glob; the packet moved or "
    "a2_packet_paths.py is stale"
  )


def test_empty_inventory_fails_closed(tmp_path: Path) -> None:
  empty = tmp_path / "no_such_package"
  empty.mkdir()

  summary = integrity.check_retained_manifest_integrity(
    repo_root=tmp_path,
    package_dir=empty,
  )

  assert summary["manifest_count"] == 0
  assert integrity._summary_failed(summary), (
    "a scan that matched zero manifests must fail, not report success"
  )


def test_missing_package_dir_raises_rather_than_scanning_nothing(
  monkeypatch: pytest.MonkeyPatch,
  tmp_path: Path,
) -> None:
  monkeypatch.setattr(
    paths, "CANDIDATE_PACKAGE_DIR", tmp_path / "no_such_package"
  )

  with pytest.raises(FileNotFoundError):
    paths.require_candidate_package_dir()


def test_no_maintenance_tool_defaults_into_a_retired_documentation_root() -> None:
  """A writer default under a retired root would recreate the pruned tree."""
  tracked = subprocess.run(
    ["git", "ls-files", "tools"],
    capture_output=True,
    text=True,
    check=True,
    cwd=paths.REPO_ROOT,
  ).stdout.split()

  offenders: list[str] = []
  for rel in tracked:
    if not rel.endswith(".py"):
      continue
    text = (paths.REPO_ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    if "a2_high_fidelity_damage_model" not in text:
      continue
    # Segment-built paths: a "task" segment in the same expression as the
    # packet segment is the stale pre-migration form.
    if '"a2_high_fidelity_damage_model"' in text and '"task"' in text:
      offenders.append(rel)
    if "docs/task/air_combat" in text:
      offenders.append(rel)

  assert not offenders, (
    "these tools still resolve the retired docs/task A2 root: "
    + ", ".join(sorted(set(offenders)))
  )
