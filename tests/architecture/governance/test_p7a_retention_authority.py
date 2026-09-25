from __future__ import annotations

import json
import hashlib
import subprocess
from pathlib import Path

import pytest

from tools.maintenance.p7b_evidence_manifest import EvidenceManifestError
from tools.maintenance.p7b_evidence_manifest import build_evidence_manifest
from tools.maintenance.p7b_evidence_manifest import validate_evidence_manifest
from tools.maintenance.runtime_authority_contracts import canonical_json_bytes
from tools.maintenance.runtime_artifact_ledger import LedgerContractError
from tools.maintenance.runtime_durable_artifact_ledger import EVIDENCE_MANIFEST_MEDIA_TYPE
from tools.maintenance.runtime_durable_artifact_ledger import SQLiteArtifactLedger
from tests.architecture.runtime_host import test_rollout_evidence_binding as evidence_fixtures
from tests.architecture.runtime_host.test_sqlite_rollout_admission import (
  _advance_to_stable,
  _open_ledger,
)

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


def test_p7b_local_ledger_projection_emits_provider_neutral_manifest(tmp_path: Path) -> None:
  ledger, token, release = _open_ledger(tmp_path)
  try:
    _advance_to_stable(ledger, token, release)
    admission = ledger.read_rollout_admission(
      "release-evidence-test",
      verification_key=evidence_fixtures.KEY,
    )
    retention = ledger.read_rollout_retention(
      "release-evidence-test",
      verification_key=evidence_fixtures.KEY,
    )
    payload = canonical_json_bytes(json.loads(json.dumps({
      "admission": admission,
      "retention": retention,
    })))
    manifest = build_evidence_manifest(
      artifact_id="release-evidence-test:stable:7",
      claim="durable stable rollout admission and rollback retention projection",
      payload=payload,
      producer="release/runtime integration",
      created_at="2026-09-25T00:00:00Z",
      retention_until="2026-12-31T00:00:00Z",
      restore_owner="release-engineering",
      access_policy="runtime-evidence-reader",
      backup_policy="SQLite backup before provider migration",
      provider="SQLiteArtifactLedger-local",
      provider_migration_policy="restore into a distinct ledger root and revalidate digests",
    )

    assert validate_evidence_manifest(manifest, payload=payload) == manifest
    assert manifest["sha256"]
    assert manifest["provider"] == "SQLiteArtifactLedger-local"
    manifest_blob = canonical_json_bytes(manifest)
    manifest_blob_digest = ledger.put_blob(
      manifest_blob,
      media_type=EVIDENCE_MANIFEST_MEDIA_TYPE,
      retention_class="evidence-short",
      audit_identity="p7b-manifest-test",
      role="release_controller",
    )
    assert manifest_blob_digest == hashlib.sha256(manifest_blob).hexdigest()
    with pytest.raises(LedgerContractError, match="evidence manifest blob is invalid"):
      ledger.put_blob(
        canonical_json_bytes({**manifest, "unexpected": True}),
        media_type=EVIDENCE_MANIFEST_MEDIA_TYPE,
        retention_class="evidence-short",
        audit_identity="p7b-invalid-manifest-test",
        role="release_controller",
      )

    backup = tmp_path / "evidence-manifest.sqlite3"
    ledger.backup_to(backup)
    restored = SQLiteArtifactLedger.restore_from(backup, tmp_path / "restored-ledger")
    try:
      restored_payload = canonical_json_bytes(json.loads(json.dumps({
        "admission": restored.read_rollout_admission(
          "release-evidence-test",
          verification_key=evidence_fixtures.KEY,
        ),
        "retention": restored.read_rollout_retention(
          "release-evidence-test",
          verification_key=evidence_fixtures.KEY,
        ),
      })))
      assert restored_payload == payload
      assert validate_evidence_manifest(manifest, payload=restored_payload) == manifest
      restored_manifest_blob, media_type, retention_class = restored.get_blob(
        manifest_blob_digest,
        role="runtime_evidence",
      )
      assert media_type == EVIDENCE_MANIFEST_MEDIA_TYPE
      assert retention_class == "evidence-short"
      assert validate_evidence_manifest(
        json.loads(restored_manifest_blob),
        payload=restored_payload,
      ) == manifest
    finally:
      restored.close()
  finally:
    ledger.close()


def test_p7b_manifest_rejects_tampered_or_incomplete_shape() -> None:
  manifest = build_evidence_manifest(
    artifact_id="manifest-test",
    claim="test evidence",
    payload=b"stable-evidence",
    producer="test",
    created_at="2026-09-25T00:00:00Z",
    retention_until="2026-12-31T00:00:00Z",
    restore_owner="release-engineering",
    access_policy="read-only",
    backup_policy="copy-before-migration",
    provider="local-test",
    provider_migration_policy="distinct-root-restore",
  )
  tampered = {**manifest, "sha256": "0" * 64}
  with pytest.raises(EvidenceManifestError, match="fields are not exact"):
    validate_evidence_manifest({**manifest, "unexpected": True})
  with pytest.raises(EvidenceManifestError, match="payload digest differs"):
    validate_evidence_manifest(tampered, payload=b"stable-evidence")


def test_p7b_manifest_rejects_ambiguous_or_reversed_time_bounds() -> None:
  manifest = build_evidence_manifest(
    artifact_id="manifest-time-test",
    claim="test evidence",
    payload=b"stable-evidence",
    producer="test",
    created_at="2026-09-25T00:00:00Z",
    retention_until="2026-12-31T00:00:00Z",
    restore_owner="release-engineering",
    access_policy="read-only",
    backup_policy="copy-before-migration",
    provider="local-test",
    provider_migration_policy="distinct-root-restore",
  )
  cases = (
    ({"created_at": "2026-09-25", "retention_until": manifest["retention_until"]}, "created_at"),
    ({"created_at": "2026-09-25T00:00:00", "retention_until": manifest["retention_until"]}, "created_at"),
    ({"created_at": "2026-12-31T00:00:00Z", "retention_until": "2026-09-25T00:00:00Z"}, "retention_until"),
  )
  for updates, message in cases:
    with pytest.raises(EvidenceManifestError, match=message):
      validate_evidence_manifest({**manifest, **updates})
