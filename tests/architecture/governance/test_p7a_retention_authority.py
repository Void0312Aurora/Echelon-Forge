from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.governance_audit

REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = REPO_ROOT / "docs" / "engineering" / "documentation" / "reference" / "retention_authority.json"


def _policy() -> dict:
  payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
  assert payload["schema_version"] == 1
  assert payload["policy_id"] == "documentation_retention.v1"
  return payload


def test_p7a_retention_authority_has_one_history_route_and_restore_contract() -> None:
  policy = _policy()
  routes = policy["history_routes"]
  git_route = routes["git_history_owner_ledger"]
  owner_route = routes["owner_local_archive"]

  assert git_route["retrieval"] == "git show <last_commit>:<path>"
  assert git_route["registry"] == (
    "docs/engineering/documentation/reference/retired_documents.json"
  )
  assert git_route["ledgers"] == [
    "docs/archive_ledger.md",
    "docs/systems/archive_ledger.md",
  ]
  assert owner_route["default"] == "forbidden"
  assert owner_route["required_readme_lifecycle"] == "archived"
  assert len(owner_route["allowed_roots"]) == 1
  assert owner_route["allowed_files"] == [
    "docs/architecture/work/archive/README.md",
    "docs/architecture/work/archive/README.zh.md",
  ]

  for path in [git_route["registry"], *git_route["ledgers"]]:
    assert (REPO_ROOT / path).is_file(), path
  for entry in owner_route["allowed_roots"]:
    assert (REPO_ROOT / entry["readme"]).is_file(), entry["readme"]
    assert entry["indexes"]
    assert all((REPO_ROOT / index).is_file() for index in entry["indexes"])
  assert all((REPO_ROOT / path).is_file() for path in owner_route["allowed_files"])


def test_p7a_evidence_retention_requires_restore_and_provider_migration_fields() -> None:
  retention = _policy()["evidence_retention"]
  required = set(retention["manifest_required_fields"])
  assert {
    "artifact_id",
    "claim",
    "sha256",
    "producer",
    "created_at",
    "retention_until",
    "restore_owner",
    "access_policy",
    "backup_policy",
    "provider",
    "provider_migration_policy",
  } <= required
  drill = retention["restore_drill"]
  assert drill["cadence"] == "quarterly"
  assert drill["owner"]
  assert "RunReceipt" in drill["minimum_scope"]


def test_p7a_policy_bindings_match_lifecycle_standard_and_governance_suite() -> None:
  bindings = _policy()["governance_bindings"]
  for key in (
    "lifecycle_policy",
    "lifecycle_policy_zh",
    "retirement_gate",
    "governance_suite",
  ):
    assert (REPO_ROOT / bindings[key]).is_file(), bindings[key]

  lifecycle = (REPO_ROOT / bindings["lifecycle_policy"]).read_text(encoding="utf-8")
  lifecycle_zh = (REPO_ROOT / bindings["lifecycle_policy_zh"]).read_text(encoding="utf-8")
  assert "retention_authority.json" in lifecycle
  assert "unregistered archive path" in lifecycle
  assert "retention_authority.json" in lifecycle_zh
  assert "未登记的 archive 路径" in lifecycle_zh

  suite = json.loads((REPO_ROOT / bindings["governance_suite"]).read_text(encoding="utf-8"))
  assert bindings["retirement_gate"] in suite["paths"]


def test_p7a_git_history_route_restores_one_entry_per_ledger() -> None:
  registry_path = REPO_ROOT / _policy()["history_routes"]["git_history_owner_ledger"]["registry"]
  registry = json.loads(registry_path.read_text(encoding="utf-8"))
  probes: dict[str, tuple[str, str]] = {}
  for path, entry in registry["documents"].items():
    probes.setdefault(entry["ledger"], (path, entry["last_commit"]))

  assert set(probes) == {
    "docs/archive_ledger.md",
    "docs/systems/archive_ledger.md",
  }
  for path, commit in probes.values():
    result = subprocess.run(
      ["git", "cat-file", "-e", f"{commit}:{path}"],
      cwd=REPO_ROOT,
      capture_output=True,
    )
    assert result.returncode == 0, f"unrestorable retained document: {commit}:{path}"
