from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.maintenance.runtime_authority_contracts import (
  AUTHORITY_ENVELOPE_FIELDS,
  AUTHORITY_SPECS,
  AuthorityContractError,
  adapt_current_resolved_manifest,
  build_release_manifest_shell,
  build_rollout_decision_shell,
  build_state_checkpoint_shell,
  canonical_json_bytes,
  parse_canonical_json_bytes,
  validate_authority_chain,
  validate_authority_envelope,
  authority_digest_sha256,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPO_ROOT / "tests" / "architecture" / "composition" / "fixtures"


def _fixture(name: str) -> dict[str, object]:
  return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _legacy_resolved() -> dict[str, object]:
  return _fixture("default_compatibility_manifest.resolved.json")


def _source_request() -> dict[str, object]:
  return _fixture("default_runtime_composition_request.v1.json")


def _release_payload() -> dict[str, object]:
  return {
    "authority_kind": "release_manifest",
    "schema_version": "echelon_forge.release_manifest.v1",
    "contract_version": "echelon_forge.release_manifest_contract.v1",
    "writer_role": "release_artifact_pipeline",
    "release_id": "release-2026-08-25",
    "writer_generation": "1",
    "reader_generation_min": "1",
    "reader_generation_max": "2",
    "package_set": [{"name": "cmo", "sha256": "a" * 64}],
    "supported_rows": ["windows-amd64-msvc"],
    "provenance_sha256": "b" * 64,
    "sbom_sha256": "c" * 64,
    "toolchain_identity": "msvc-v143",
    "source_revision": "82d5b6e893c442950e334eb3e9ec92f8174eeb35",
    "compatibility_generation": "1",
    "minimum_reader_generation": "1",
    "state_schema_generation": "1",
    "rollback_policy": "checkpoint-recovery",
  }


def _plan() -> dict[str, object]:
  return adapt_current_resolved_manifest(
    _legacy_resolved(), source_request=_source_request(), source_requested_manifest=_legacy_resolved()["manifest"], plan_id="plan-1"
  )


def _rollout_payload(manifest_sha256: str, plan_sha256: str = "f" * 64) -> dict[str, object]:
  return {
    "authority_kind": "rollout_decision",
    "schema_version": "echelon_forge.rollout_decision.v1",
    "contract_version": "echelon_forge.rollout_decision_contract.v1",
    "writer_role": "release_controller",
    "decision_id": "decision-1",
    "release_id": "release-2026-08-25",
    "manifest_sha256": manifest_sha256,
    "plan_sha256": plan_sha256,
    "plan_reader_generation_min": "1",
    "plan_reader_generation_max": "2",
    "predecessor_decision_id": "",
    "state": "shadow",
    "writer_generation": "1",
    "decision_sequence": "0",
    "cohort": "shadow",
    "rollback_deadline": "2026-09-01T00:00:00Z",
    "checkpoint_id": "",
    "irreversible_write_boundary": "none",
  }


def _checkpoint_payload(plan_sha256: str) -> dict[str, object]:
  return {
    "authority_kind": "state_checkpoint",
    "schema_version": "echelon_forge.state_checkpoint.v1",
    "contract_version": "echelon_forge.state_checkpoint_contract.v1",
    "writer_role": "runtime_host",
    "writer_generation": "1",
    "checkpoint_id": "checkpoint-1",
    "plan_sha256": plan_sha256,
    "release_id": "release-2026-08-25",
    "decision_id": "decision-1",
    "run_id": "run-1",
    "host_boot_id": "boot-1",
    "incarnation_epoch": "1",
    "transfer_fence_sequence": "7",
    "world_fragments": [{
      "world_id": "world-1",
      "episode_ids": ["episode-1"],
      "fragment_sequence": "0",
      "state_sha256": "d" * 64,
    }],
    "aggregate_state_sha256": "e" * 64,
    "state_schema_generation": "1",
    "target_reader_generation_min": "1",
    "target_reader_generation_max": "2",
  }


def test_canonical_authority_encoding_matches_rfc_number_profile_and_rejects_ambiguity() -> None:
  assert canonical_json_bytes({"b": 1, "a": [True, "x"]}) == b'{"a":[true,"x"],"b":1}'
  assert canonical_json_bytes({"n": -0.0, "small": 1e-6, "large": 1e6}) == b'{"large":1000000,"n":0,"small":0.000001}'
  assert parse_canonical_json_bytes(b'{"a":1}') == {"a": 1}
  with pytest.raises(AuthorityContractError, match="duplicate object key"):
    parse_canonical_json_bytes(b'{"a":1,"a":2}')
  with pytest.raises(AuthorityContractError, match="not canonical"):
    parse_canonical_json_bytes(b'{ "a": 1 }')
  with pytest.raises(AuthorityContractError, match="outside exact"):
    canonical_json_bytes({"counter": 2**64})
  with pytest.raises(AuthorityContractError, match="integer-valued float"):
    canonical_json_bytes({"counter": 1e20})
  with pytest.raises(AuthorityContractError, match="surrogate"):
    canonical_json_bytes({"\ud800": 1})
  with pytest.raises(AuthorityContractError, match="BOM"):
    parse_canonical_json_bytes(b"\xef\xbb\xbf{}")


def test_checked_in_cross_language_vector_is_executable() -> None:
  vector = _fixture("authority_cross_language_vector.v1.json")
  payload_bytes = vector["canonical_payload_bytes"].encode("utf-8")
  assert canonical_json_bytes(json.loads(vector["canonical_payload_bytes"])) == payload_bytes
  assert authority_digest_sha256(vector["domain"], vector["media_type"], payload_bytes) == vector["payload_sha256"]
  envelope = json.loads(vector["envelope_json"])
  assert validate_authority_envelope(envelope)["payload_sha256"] == vector["payload_sha256"]


def test_all_four_authorities_have_distinct_domains_and_typed_envelopes() -> None:
  plan = _plan()
  release = build_release_manifest_shell(_release_payload())
  rollout = build_rollout_decision_shell(_rollout_payload(release["payload_sha256"], plan["payload_sha256"]))
  checkpoint = build_state_checkpoint_shell(_checkpoint_payload(plan["payload_sha256"]))
  envelopes = [plan, release, rollout, checkpoint]
  assert len({envelope["domain"] for envelope in envelopes}) == 4
  assert len({envelope["media_type"] for envelope in envelopes}) == 4
  assert set(AUTHORITY_SPECS) == {"resolved_composition_plan", "release_manifest", "rollout_decision", "state_checkpoint"}
  for envelope in envelopes:
    assert set(envelope) == AUTHORITY_ENVELOPE_FIELDS
    assert validate_authority_envelope(envelope) == envelope
  validate_authority_chain(plan, release, rollout, checkpoint)


def test_authority_chain_rejects_rollout_bound_to_a_different_plan() -> None:
  plan = _plan()
  release = build_release_manifest_shell(_release_payload())
  rollout = build_rollout_decision_shell(_rollout_payload(release["payload_sha256"], "0" * 64))
  checkpoint = build_state_checkpoint_shell(_checkpoint_payload(plan["payload_sha256"]))
  with pytest.raises(AuthorityContractError, match="rollout plan digest"):
    validate_authority_chain(plan, release, rollout, checkpoint)


def test_current_adapter_binds_source_request_and_does_not_rewrite_legacy_artifact() -> None:
  legacy = _legacy_resolved()
  envelope = _plan()
  assert envelope["payload"]["resolved_plan"] == legacy
  assert envelope["payload"]["source_artifact_schema_version"] == legacy["schema_version"]
  tampered_request = dict(_source_request())
  tampered_request["request_id"] = "other-request"
  assert envelope["payload"]["request_sha256"] != adapt_current_resolved_manifest(
    legacy, source_request=tampered_request, source_requested_manifest=legacy["manifest"], plan_id="plan-1"
  )["payload"]["request_sha256"]
  tampered = dict(legacy)
  tampered["evil"] = True
  with pytest.raises(AuthorityContractError, match="unknown or missing|digest"):
    adapt_current_resolved_manifest(tampered, source_request=_source_request(), source_requested_manifest=legacy["manifest"], plan_id="plan-1")
  with pytest.raises(AuthorityContractError, match="source request"):
    adapt_current_resolved_manifest(legacy, source_request={"evil": True}, source_requested_manifest=legacy["manifest"], plan_id="plan-1")
  with pytest.raises(AuthorityContractError, match="requested manifest"):
    adapt_current_resolved_manifest(legacy, source_request=_source_request(), source_requested_manifest={"evil": True}, plan_id="plan-1")


@pytest.mark.parametrize("kind,field", [
  ("release_manifest", "writer_role"),
  ("rollout_decision", "state"),
  ("state_checkpoint", "world_fragments"),
])
def test_typed_shells_reject_none_unknown_nested_and_unordered_values(kind: str, field: str) -> None:
  release = _release_payload()
  payload = release if kind == "release_manifest" else (
    _rollout_payload("a" * 64) if kind == "rollout_decision" else _checkpoint_payload("a" * 64)
  )
  payload[field] = None
  builder = {
    "release_manifest": build_release_manifest_shell,
    "rollout_decision": build_rollout_decision_shell,
    "state_checkpoint": build_state_checkpoint_shell,
  }[kind]
  with pytest.raises(AuthorityContractError):
    builder(payload)
  if kind == "release_manifest":
    payload = _release_payload()
    payload["package_set"] = [{"name": "z", "sha256": "a" * 64}, {"name": "a", "sha256": "b" * 64}]
    with pytest.raises(AuthorityContractError, match="sorted"):
      builder(payload)


def test_envelope_rejects_wrong_owner_domain_signature_context_and_digest() -> None:
  release = build_release_manifest_shell(_release_payload())
  wrong = dict(release)
  wrong["domain"] = "other.domain"
  with pytest.raises(AuthorityContractError, match="domain/media type"):
    validate_authority_envelope(wrong)
  wrong = dict(release)
  wrong["signatures"] = [{"algorithm": "bogus"}]
  with pytest.raises(AuthorityContractError, match="typed context"):
    validate_authority_envelope(wrong)
  wrong = dict(release)
  wrong["payload_sha256"] = "0" * 64
  with pytest.raises(AuthorityContractError, match="digest"):
    validate_authority_envelope(wrong)
