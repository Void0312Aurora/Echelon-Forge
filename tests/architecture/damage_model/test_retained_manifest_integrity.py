from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.maintenance.retained_artifacts import manifest_integrity as integrity


def _sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_path_resolution_prefers_repo_relative_paths_and_manifest_filenames(
  tmp_path: Path,
) -> None:
  repo_root = tmp_path / "repo"
  manifest_dir = repo_root / "package" / "retained_artifacts" / "sample"
  manifest_dir.mkdir(parents=True)
  repo_relative = repo_root / "artifact.json"
  local_filename = manifest_dir / "artifact.json"
  repo_relative.write_text("repo-root artifact\n", encoding="utf-8")
  local_filename.write_text("manifest-local artifact\n", encoding="utf-8")
  nested_local = manifest_dir / "nested.json"
  nested_local.write_text("nested manifest-local artifact\n", encoding="utf-8")

  manifest_path = manifest_dir / "manifest.json"
  _write_json(
    manifest_path,
    {
      "artifacts": [
        {"path": "artifact.json", "sha256": _sha256(repo_relative)},
        {"filename": "artifact.json", "sha256": _sha256(local_filename)},
        {"relative_path": "nested.json", "sha256": _sha256(nested_local)},
      ]
    },
  )

  summary = integrity.check_retained_manifest_integrity(
    repo_root=repo_root,
    manifest_paths=[manifest_path],
  )

  assert summary["manifest_count"] == 1
  assert summary["missing_total"] == 0
  assert summary["sha_mismatch_total"] == 0
  assert summary["guard_true_total"] == 0


def test_hash_mismatch_is_reported_per_hash_field(tmp_path: Path) -> None:
  repo_root = tmp_path / "repo"
  manifest_dir = repo_root / "package" / "retained_artifacts" / "sample"
  artifact = manifest_dir / "artifact.json"
  artifact.parent.mkdir(parents=True)
  artifact.write_text("actual artifact\n", encoding="utf-8")
  manifest_path = manifest_dir / "manifest.json"
  _write_json(
    manifest_path,
    {
      "artifacts": [
        {
          "filename": "artifact.json",
          "sha256": "0" * 64,
          "content_hash": "sha256:" + ("1" * 64),
        }
      ]
    },
  )

  summary = integrity.check_retained_manifest_integrity(
    repo_root=repo_root,
    manifest_paths=[manifest_path],
  )

  assert summary["missing_total"] == 0
  assert summary["sha_mismatch_total"] == 2
  assert {row["field"] for row in summary["sha_mismatches"]} == {
    "sha256",
    "content_hash",
  }


def test_guard_true_counts_only_boolean_authority_stock_pk_and_fuze_fields(
  tmp_path: Path,
) -> None:
  repo_root = tmp_path / "repo"
  manifest_dir = repo_root / "package" / "retained_artifacts" / "sample"
  artifact = manifest_dir / "artifact.json"
  artifact.parent.mkdir(parents=True)
  artifact.write_text("actual artifact\n", encoding="utf-8")
  manifest_path = manifest_dir / "manifest.json"
  _write_json(
    manifest_path,
    {
      "status": "pk_authority_granted",
      "authority_guards_all_false": True,
      "authority_guards": {
        "pk_authority_granted": True,
        "stock_database_authority_granted": False,
        "deterministic_fuze_authority_released": "true",
        "stock_effect_component_pk_fuze_authority_all_false": True,
      },
      "artifacts": [{"filename": "artifact.json", "sha256": _sha256(artifact)}],
    },
  )

  summary = integrity.check_retained_manifest_integrity(
    repo_root=repo_root,
    manifest_paths=[manifest_path],
  )

  assert summary["guard_true_total"] == 1
  assert summary["guard_true"][0]["field"].endswith("pk_authority_granted")


def test_fix_updates_only_hashes_for_artifacts_under_manifest_directory(
  tmp_path: Path,
) -> None:
  repo_root = tmp_path / "repo"
  manifest_dir = repo_root / "package" / "retained_artifacts" / "sample"
  local_artifact = manifest_dir / "artifact.json"
  external_artifact = repo_root / "outside.json"
  local_artifact.parent.mkdir(parents=True)
  local_artifact.write_text("local artifact\n", encoding="utf-8")
  external_artifact.write_text("external artifact\n", encoding="utf-8")
  manifest_path = manifest_dir / "manifest.json"
  _write_json(
    manifest_path,
    {
      "artifacts": [
        {
          "filename": "artifact.json",
          "sha256": "0" * 64,
          "content_hash": "sha256:" + ("0" * 64),
        },
        {
          "relative_path": "outside.json",
          "sha256": "1" * 64,
        },
      ]
    },
  )

  summary = integrity.check_retained_manifest_integrity(
    repo_root=repo_root,
    manifest_paths=[manifest_path],
    fix=True,
  )
  fixed_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

  assert summary["fixed_hash_fields"] == 2
  assert summary["sha_mismatch_total"] == 1
  assert fixed_manifest["artifacts"][0]["sha256"] == _sha256(local_artifact)
  assert fixed_manifest["artifacts"][0]["content_hash"] == (
    f"sha256:{_sha256(local_artifact)}"
  )
  assert fixed_manifest["artifacts"][1]["sha256"] == "1" * 64
  assert summary["sha_mismatches"][0]["target"].endswith("outside.json")


@pytest.mark.parametrize(
  "summary",
  [
    {
      "manifest_count": 1,
      "missing_total": 0,
      "sha_mismatch_total": 0,
      "guard_true_total": 0,
    },
    {
      "manifest_count": 1,
      "missing_total": 1,
      "sha_mismatch_total": 0,
      "guard_true_total": 0,
    },
    {
      "manifest_count": 1,
      "missing_total": 0,
      "sha_mismatch_total": 1,
      "guard_true_total": 0,
    },
    {
      "manifest_count": 1,
      "missing_total": 0,
      "sha_mismatch_total": 0,
      "guard_true_total": 1,
    },
    # An empty inventory must fail even with clean counters: a glob that
    # matched no manifest verified nothing.
    {
      "manifest_count": 0,
      "missing_total": 0,
      "sha_mismatch_total": 0,
      "guard_true_total": 0,
    },
  ],
)
def test_summary_failure_status(summary: dict[str, int]) -> None:
  assert integrity._summary_failed(summary) is (
    summary["manifest_count"] == 0
    or summary["missing_total"] != 0
    or summary["sha_mismatch_total"] != 0
    or summary["guard_true_total"] != 0
  )
