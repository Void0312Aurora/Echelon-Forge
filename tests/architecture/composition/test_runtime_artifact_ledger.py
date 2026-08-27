from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, RefResolver

from tools.maintenance.generate_runtime_authority_vectors import (
  CANDIDATE_RELEASE_PACKAGE_BYTES,
  ROLLBACK_RELEASE_PACKAGE_BYTES,
  build_inventory,
)
from tools.maintenance.generate_runtime_ledger_fixtures import build_fixtures
from tools.maintenance.runtime_artifact_ledger import (
  ArtifactDescriptor,
  CanaryHealth,
  CompatibilityReader,
  LedgerContractError,
  ReaderDeployment,
  QualificationEvidence,
  SimulatedArtifactLedger,
  SimulatedRolloutController,
  StoredArtifactInventory,
  TerminationProof,
  inventory_payload,
  kill_switch_reasons,
  qualification_evidence_payload,
  reader_first_ready,
  select_backout_protocol,
  shadow_receipt_payload,
  store_inventory,
  validate_release_inventory,
  validate_release_inventory_binding,
)
from tools.maintenance.runtime_authority_contracts import (
  build_release_manifest_shell,
  build_rollout_decision_shell,
  build_state_checkpoint_shell,
  canonical_json_bytes,
)


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "architecture" / "composition" / "fixtures"


def _vector(name: str) -> dict[str, object]:
  return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _plan_envelope() -> dict[str, object]:
  return json.loads(_vector("authority_resolved_composition_plan.v1.json")["envelope_json"])


def _inventory() -> StoredArtifactInventory:
  vectors = {
    name: _vector(name) for name in (
      "authority_resolved_composition_plan.generation2.v1.json",
      "authority_state_checkpoint.v1.json",
    )
  }
  return build_inventory(
    _plan_envelope(),
    json.loads(vectors["authority_resolved_composition_plan.generation2.v1.json"]["envelope_json"]),
    _p3c_checkpoint(),
  )


def _p3c_checkpoint() -> dict[str, object]:
  canonical = json.loads(_vector("authority_state_checkpoint.v1.json")["envelope_json"])
  return build_state_checkpoint_shell({**canonical["payload"], "decision_id": "decision-5"})


def _checkpoint_bytes() -> bytes:
  return canonical_json_bytes(_p3c_checkpoint())


def _test_release_envelope() -> dict[str, object]:
  inventory = _inventory()
  canonical = json.loads(_vector("authority_cross_language_vector.v1.json")["envelope_json"])
  return build_release_manifest_shell({
    **canonical["payload"],
    "stored_artifact_inventory_sha256": hashlib.sha256(
      canonical_json_bytes(inventory_payload(inventory))
    ).hexdigest(),
  })


def _plan_bytes() -> bytes:
  return _vector("authority_resolved_composition_plan.v1.json")["envelope_json"].encode("utf-8")


def _artifact_bytes(descriptor: ArtifactDescriptor) -> bytes:
  if descriptor.authority_kind == "resolved_composition_plan":
    name = "authority_resolved_composition_plan.v1.json" if descriptor.writer_generation == 1 else "authority_resolved_composition_plan.generation2.v1.json"
    return _vector(name)["envelope_json"].encode("utf-8")
  if descriptor.authority_kind == "state_checkpoint":
    return _checkpoint_bytes()
  if descriptor.authority_kind == "release_package":
    return ROLLBACK_RELEASE_PACKAGE_BYTES if descriptor.writer_generation == 1 else CANDIDATE_RELEASE_PACKAGE_BYTES
  raise AssertionError(f"unsupported descriptor {descriptor.authority_kind}")


def _descriptor(inventory: StoredArtifactInventory, kind: str, generation: int) -> ArtifactDescriptor:
  return next(item for item in inventory.artifacts if item.authority_kind == kind and item.writer_generation == generation)


def _populate_inventory(ledger: SimulatedArtifactLedger, inventory: StoredArtifactInventory) -> None:
  for descriptor in inventory.artifacts:
    payload = _artifact_bytes(descriptor)
    role = {
      "resolved_composition_plan": "plan_compiler",
      "state_checkpoint": "runtime_host",
      "release_package": "release_artifact_pipeline",
    }[descriptor.authority_kind]
    ledger.put_blob(
      role=role, payload=payload, media_type=descriptor.media_type,
      expected_sha256=descriptor.blob_sha256, retention_class="rollback-window",
      audit_identity=f"audit-{descriptor.authority_kind}-{descriptor.writer_generation}",
    )
  try:
    ledger.read_checkpoint(role="runtime_evidence", checkpoint_id="checkpoint-1")
  except LedgerContractError:
    checkpoint_token = ledger.acquire_fence(
      role="runtime_host", stream_id="checkpoint:checkpoint-1", writer_id="host-checkpoint",
      expected_generation=0, audit_identity="audit-inventory-checkpoint-fence",
    )
    ledger.persist_checkpoint(
      role="runtime_host", envelope_bytes=_checkpoint_bytes(),
      expected_slot_version=0, token=checkpoint_token, audit_identity="audit-inventory-checkpoint-slot",
    )


def _put_qualification_blob(ledger: SimulatedArtifactLedger) -> str:
  payload = canonical_json_bytes(json.loads((FIXTURES / "rollout_qualification_record.v1.json").read_text(encoding="utf-8")))
  digest = hashlib.sha256(payload).hexdigest()
  ledger.put_blob(
    role="release_controller", payload=payload,
    media_type="application/vnd.echelon-forge.rollout-qualification-record.v1+json",
    expected_sha256=digest, retention_class="rollback-window", audit_identity="audit-slot-blob",
  )
  return digest


def _reader_deployments(inventory: StoredArtifactInventory) -> tuple[ReaderDeployment, ...]:
  admitted = tuple(sorted(item.blob_sha256 for item in inventory.artifacts))
  return (
    ReaderDeployment("reader-a", 2, True, True, (1, 2), admitted, 1, ("native_step_authority",), ("in-process",)),
    ReaderDeployment("reader-b", 2, True, True, (1, 2), admitted, 1, ("native_step_authority",), ("in-process",)),
  )


def _put_evidence_blob(
  ledger: SimulatedArtifactLedger,
  *,
  document: dict[str, object],
  media_type: str,
  identity: str,
  role: str,
) -> str:
  proof = f"{identity}-proof".encode("utf-8")
  proof_digest = hashlib.sha256(proof).hexdigest()
  ledger.put_blob(
    role=role, payload=proof,
    media_type="application/vnd.echelon-forge.qualification-proof.v1+octets",
    expected_sha256=proof_digest, retention_class="rollback-window",
    audit_identity=f"audit-{identity}-proof",
  )
  document = dict(document, evidence_sha256=proof_digest)
  payload = canonical_json_bytes(document)
  digest = hashlib.sha256(payload).hexdigest()
  ledger.put_blob(
    role=role, payload=payload, media_type=media_type, expected_sha256=digest,
    retention_class="rollback-window", audit_identity=f"audit-{identity}",
  )
  return digest


def _evidence(
  ledger: SimulatedArtifactLedger,
  state: str,
  inventory: StoredArtifactInventory,
  *,
  predecessor: dict[str, object] | None = None,
) -> QualificationEvidence:
  readers = _reader_deployments(inventory)
  kwargs: dict[str, object] = {"reader_deployments": readers}
  def qualification_document(kind: str, marker: str) -> dict[str, object]:
    if predecessor is None:
      raise AssertionError(f"{state} evidence requires its predecessor authority")
    return qualification_evidence_payload(
      release_id=inventory.release_id, evidence_kind=kind, evidence_sha256=marker * 64,
      plan_sha256=predecessor["payload"]["plan_sha256"],
      rollout_decision_sha256=predecessor["payload_sha256"],
    )
  if state == "shadow":
    kwargs["shadow_receipt_sha256"] = _put_evidence_blob(
      ledger,
      document=shadow_receipt_payload(
        receipt_id="shadow-receipt",
        plan_sha256=_vector("authority_resolved_composition_plan.v1.json")["payload_sha256"],
        release_manifest_sha256=_test_release_envelope()["payload_sha256"],
        rollout_decision_sha256=(predecessor or _decision(state="prepared", sequence=0, decision_id="decision-0"))["payload_sha256"],
        comparison_kind="cpu-exact-result", outcome="match", evidence_sha256="9" * 64,
      ),
      media_type="application/vnd.echelon-forge.shadow-comparison-receipt.v1+json",
      identity="shadow-receipt", role="shadow_observer",
    )
  if state == "canary-ready":
    kwargs["storage_restore_drill_sha256"] = _put_evidence_blob(
      ledger, document=qualification_document("storage-restore-drill", "1"),
      media_type="application/vnd.echelon-forge.qualification-evidence.v1+json",
      identity="storage-restore", role="release_controller",
    )
    kwargs["rollback_drill_sha256"] = _put_evidence_blob(
      ledger, document=qualification_document("rollback-drill", "2"),
      media_type="application/vnd.echelon-forge.qualification-evidence.v1+json",
      identity="rollback-drill", role="release_controller",
    )
  if state == "production-canary":
    kwargs["cutover_drill_sha256"] = _put_evidence_blob(
      ledger, document=qualification_document("cutover-drill", "3"),
      media_type="application/vnd.echelon-forge.qualification-evidence.v1+json",
      identity="cutover-drill", role="release_controller",
    )
  if state in {"adoption-expanding", "rollback-window"}:
    kwargs["adoption_health_sha256"] = _put_evidence_blob(
      ledger, document=qualification_document("adoption-health", "4"),
      media_type="application/vnd.echelon-forge.qualification-evidence.v1+json",
      identity="adoption-health", role="release_controller",
    )
  if state == "stable":
    kwargs["inventory_disposition_sha256"] = _put_evidence_blob(
      ledger, document=qualification_document("inventory-disposition", "5"),
      media_type="application/vnd.echelon-forge.qualification-evidence.v1+json",
      identity="inventory-disposition", role="release_controller",
    )
    kwargs["deadline_elapsed"] = True
    kwargs["no_unresolved_high_findings"] = True
  if state == "backed-out":
    kwargs["rollback_receipt_sha256"] = _put_evidence_blob(
      ledger, document=qualification_document("rollback-receipt", "6"),
      media_type="application/vnd.echelon-forge.qualification-evidence.v1+json",
      identity="rollback-receipt", role="release_controller",
    )
  return QualificationEvidence(**kwargs)


def _generation_2_plan() -> tuple[ArtifactDescriptor, bytes]:
  envelope_bytes = _vector("authority_resolved_composition_plan.generation2.v1.json")["envelope_json"].encode("utf-8")
  descriptor = ArtifactDescriptor(
    authority_kind="resolved_composition_plan",
    blob_sha256=hashlib.sha256(envelope_bytes).hexdigest(),
    media_type="application/vnd.echelon-forge.resolved-composition-plan-envelope.v1+json",
    size=len(envelope_bytes),
    writer_generation=2,
    reader_generation_min=2,
    reader_generation_max=2,
    state_schema_generation=1,
    truth_features=("native_step_authority",),
    topology="in-process",
    rollback_eligible=False,
  )
  return descriptor, envelope_bytes


def _decision(
  *,
  state: str,
  sequence: int,
  decision_id: str,
  predecessor: str = "",
  writer_generation: int = 1,
  checkpoint_id: str = "",
) -> dict[str, object]:
  release = _test_release_envelope()
  plan = _vector("authority_resolved_composition_plan.v1.json") if writer_generation == 1 else _vector("authority_resolved_composition_plan.generation2.v1.json")
  plan_reader_min = "1" if writer_generation == 1 else "2"
  plan_reader_max = "2" if writer_generation == 1 else "2"
  return build_rollout_decision_shell({
    "authority_kind": "rollout_decision",
    "schema_version": "echelon_forge.rollout_decision.v1",
    "contract_version": "echelon_forge.rollout_decision_contract.v1",
    "writer_role": "release_controller",
    "decision_id": decision_id,
    "release_id": "release-2026-08-25",
    "manifest_sha256": release["payload_sha256"],
    "plan_sha256": plan["payload_sha256"],
    "plan_reader_generation_min": plan_reader_min,
    "plan_reader_generation_max": plan_reader_max,
    "predecessor_decision_id": predecessor,
    "state": state,
    "writer_generation": str(writer_generation),
    "decision_sequence": str(sequence),
    "cohort": "qualification",
    "rollback_deadline": "2026-09-01T00:00:00Z",
    "checkpoint_id": checkpoint_id,
    "irreversible_write_boundary": "none",
  })


def _put_plan(ledger: SimulatedArtifactLedger) -> str:
  payload = _plan_bytes()
  digest = hashlib.sha256(payload).hexdigest()
  ack = ledger.put_blob(
    role="plan_compiler",
    payload=payload,
    media_type="application/vnd.echelon-forge.resolved-composition-plan-envelope.v1+json",
    expected_sha256=digest,
    retention_class="rollback-window",
    audit_identity="audit-plan-1",
  )
  assert ack.durable
  return digest


def _controller(
  ledger: SimulatedArtifactLedger,
  token: object,
  *,
  plan_envelope: dict[str, object] | None = None,
) -> SimulatedRolloutController:
  inventory = _inventory()
  _populate_inventory(ledger, inventory)
  inventory_sha256 = hashlib.sha256(canonical_json_bytes(inventory_payload(inventory))).hexdigest()
  store_inventory(ledger, inventory, audit_identity="audit-controller-inventory")
  release_envelope = _test_release_envelope()
  release_bytes = canonical_json_bytes(release_envelope)
  ledger.put_blob(
    role="release_artifact_pipeline", payload=release_bytes,
    media_type="application/vnd.echelon-forge.release-manifest-envelope.v1+json",
    expected_sha256=hashlib.sha256(release_bytes).hexdigest(), retention_class="rollback-window",
    audit_identity="audit-release-envelope",
  )
  return SimulatedRolloutController(
    ledger,
    release_id="release-2026-08-25",
    token=token,
    inventory=inventory,
    inventory_sha256=inventory_sha256,
    release_envelope=release_envelope,
    plan_envelope=plan_envelope or _plan_envelope(),
  )


def test_blob_store_is_content_addressed_role_scoped_and_restore_verifiable() -> None:
  ledger = SimulatedArtifactLedger()
  digest = _put_plan(ledger)
  payload, metadata = ledger.get_blob(role="runtime_evidence", digest=digest)
  assert payload == _plan_bytes()
  assert metadata.size == len(payload)
  with pytest.raises(LedgerContractError, match="lacks 'blob.get'"):
    ledger.get_blob(role="plan_compiler", digest=digest)
  with pytest.raises(LedgerContractError, match="digest does not match"):
    ledger.put_blob(
      role="plan_compiler", payload=b"wrong", media_type="application/vnd.echelon-forge.resolved-composition-plan-envelope.v1+json",
      expected_sha256=digest, retention_class="rollback-window", audit_identity="audit-wrong",
    )
  with pytest.raises(LedgerContractError, match="cannot store media type"):
    ledger.put_blob(
      role="plan_compiler", payload=b"{}", media_type="application/json",
      expected_sha256=hashlib.sha256(b"{}").hexdigest(), retention_class="rollback-window",
      audit_identity="audit-wrong-media",
    )
  ledger.set_blob_availability_for_test(digest, available=False)
  with pytest.raises(LedgerContractError, match="unavailable"):
    ledger.get_blob(role="runtime_evidence", digest=digest)
  ledger.set_blob_availability_for_test(digest, available=True)
  snapshot = ledger.export_snapshot(role="runtime_evidence")
  restored = SimulatedArtifactLedger.restore_snapshot(snapshot)
  assert restored.get_blob(role="runtime_evidence", digest=digest)[0] == payload
  unknown = json.loads(snapshot)
  unknown["hidden_default"] = True
  with pytest.raises(LedgerContractError, match="fields are not exact"):
    SimulatedArtifactLedger.restore_snapshot(canonical_json_bytes(unknown))


def test_conditional_slots_and_fences_reject_stale_or_parallel_writers() -> None:
  ledger = SimulatedArtifactLedger()
  digest = _put_qualification_blob(ledger)
  with pytest.raises(LedgerContractError, match="audit_identity"):
    ledger.acquire_fence(
      role="release_controller", stream_id="qualification-rollout:release-2026-08-25", writer_id="controller-a",
      expected_generation=0, audit_identity="",
    )
  token = ledger.acquire_fence(
    role="release_controller", stream_id="qualification-rollout:release-2026-08-25", writer_id="controller-a",
    expected_generation=0, audit_identity="audit-fence-1",
  )
  with pytest.raises(LedgerContractError, match="tombstoned"):
    ledger.acquire_fence(
      role="release_controller", stream_id=token.stream_id, writer_id=token.writer_id,
      expected_generation=1, audit_identity="audit-same-writer-reacquire",
    )
  created = ledger.conditional_create(
    role="release_controller", key="qualification-rollout:release-2026-08-25", blob_digest=digest,
    token=token, audit_identity="audit-slot-1",
  )
  assert created.version == 1
  with pytest.raises(LedgerContractError, match="version mismatch"):
    ledger.compare_and_swap(
      role="release_controller", key="qualification-rollout:release-2026-08-25", expected_version=0,
      blob_digest=digest, token=token, audit_identity="audit-slot-bad",
    )
  with pytest.raises(LedgerContractError, match="tombstoned"):
    ledger.acquire_fence(
      role="release_controller", stream_id=token.stream_id, writer_id="controller-b",
      expected_generation=1, audit_identity="audit-fence-bad",
    )
  proof = ledger.confirm_process_terminated(
    role="crash_reconciler", token=token, observed_exit_sha256="f" * 64,
    audit_identity="audit-exit-proof",
  )
  with pytest.raises(LedgerContractError, match="termination proof"):
    ledger.tombstone_writer(
      role="crash_reconciler", token=token, termination_proof=replace(proof, writer_id="other-writer"),
      audit_identity="audit-bad-tombstone",
    )
  ledger.tombstone_writer(
    role="crash_reconciler", token=token, termination_proof=proof,
    audit_identity="audit-tombstone",
  )
  successor = ledger.acquire_fence(
    role="release_controller", stream_id=token.stream_id, writer_id="controller-b",
    expected_generation=1, audit_identity="audit-fence-2",
  )
  assert successor.generation == 2
  with pytest.raises(LedgerContractError, match="stale"):
    ledger.compare_and_swap(
      role="release_controller", key="qualification-rollout:release-2026-08-25", expected_version=1,
      blob_digest=digest, token=token, audit_identity="audit-stale",
    )


def test_slot_and_journal_namespaces_bind_media_and_termination_proof_identity() -> None:
  ledger = SimulatedArtifactLedger()
  plan_digest = _put_plan(ledger)
  token = ledger.acquire_fence(
    role="release_controller", stream_id="qualification-rollout:release-media", writer_id="controller-a",
    expected_generation=0, audit_identity="audit-media-fence",
  )
  with pytest.raises(LedgerContractError, match="media type"):
    ledger.conditional_create(
      role="release_controller", key=token.stream_id, blob_digest=plan_digest,
      token=token, audit_identity="audit-media-slot",
    )
  forged = replace(
    TerminationProof(token.stream_id, token.writer_id, token.generation, "f" * 64),
    observed_exit_sha256="f" * 64,
  )
  with pytest.raises(LedgerContractError, match="termination proof"):
    ledger.tombstone_writer(
      role="crash_reconciler", token=token, termination_proof=forged,
      audit_identity="audit-forged-proof",
    )
  assert not any(record["operation"] == "writer.tombstone" for record in ledger.audit_log(role="runtime_evidence"))
  header_digest = hashlib.sha256(b"not-a-header").hexdigest()
  ledger.put_blob(
    role="runtime_host", payload=b"not-a-header",
    media_type="application/vnd.echelon-forge.state-checkpoint-envelope.v1+json",
    expected_sha256=header_digest, retention_class="run-retained", audit_identity="audit-wrong-header",
  )
  journal_token = ledger.acquire_fence(
    role="runtime_host", stream_id="journal:media-run", writer_id="host-a",
    expected_generation=0, audit_identity="audit-journal-media-fence",
  )
  with pytest.raises(LedgerContractError, match="header media type"):
    ledger.open_journal(
      role="runtime_host", journal_id="media-run", header_blob_sha256=header_digest,
      token=journal_token, audit_identity="audit-journal-wrong-header",
    )


def test_checkpoint_persistence_is_fenced_conditional_and_hash_valid() -> None:
  ledger = SimulatedArtifactLedger()
  checkpoint = json.loads(_vector("authority_state_checkpoint.v1.json")["envelope_json"])
  checkpoint_bytes = canonical_json_bytes(checkpoint)
  token = ledger.acquire_fence(
    role="runtime_host", stream_id="checkpoint:checkpoint-1", writer_id="host-a",
    expected_generation=0, audit_identity="audit-checkpoint-fence",
  )
  with pytest.raises(LedgerContractError, match="runtime_host-only"):
    ledger.persist_checkpoint(
      role="release_controller", envelope_bytes=checkpoint_bytes, expected_slot_version=0,
      token=token, audit_identity="audit-checkpoint-wrong-role",
    )
  digest, ack = ledger.persist_checkpoint(
    role="runtime_host", envelope_bytes=checkpoint_bytes, expected_slot_version=0, token=token,
    audit_identity="audit-checkpoint-create",
  )
  assert ack.version == 1
  assert ledger.read_checkpoint(role="runtime_evidence", checkpoint_id="checkpoint-1")["payload_sha256"] == checkpoint["payload_sha256"]
  for role in ("release_controller", "crash_reconciler", "shadow_observer"):
    with pytest.raises(LedgerContractError, match="checkpoint.read"):
      ledger.slot(role=role, key="checkpoint:checkpoint-1")
    with pytest.raises(LedgerContractError, match="checkpoint.read"):
      ledger.get_blob(role=role, digest=digest)
    with pytest.raises(LedgerContractError, match="metadata access"):
      ledger.stat_blob(role="release_controller", digest=digest)
  assert ledger.slot(role="runtime_host", key="checkpoint:checkpoint-1").blob_digest == digest
  tampered_snapshot = json.loads(ledger.export_snapshot(role="runtime_evidence"))
  tampered_snapshot["slots"][0]["fence_generation"] = 0
  with pytest.raises(LedgerContractError, match="slot version/fence"):
    SimulatedArtifactLedger.restore_snapshot(canonical_json_bytes(tampered_snapshot))
  with pytest.raises(LedgerContractError, match="absent key"):
    ledger.persist_checkpoint(
      role="runtime_host", envelope_bytes=checkpoint_bytes, expected_slot_version=0, token=token,
      audit_identity="audit-checkpoint-stale-create",
    )
  with pytest.raises(LedgerContractError, match="immutable"):
    ledger.persist_checkpoint(
      role="runtime_host", envelope_bytes=checkpoint_bytes, expected_slot_version=1, token=token,
      audit_identity="audit-checkpoint-rewrite",
    )
  with pytest.raises(LedgerContractError, match="stale or inactive"):
    ledger.persist_checkpoint(
      role="runtime_host", envelope_bytes=checkpoint_bytes, expected_slot_version=1,
      token=replace(token, generation=2), audit_identity="audit-checkpoint-stale-fence",
    )
  assert digest == hashlib.sha256(checkpoint_bytes).hexdigest()


def test_journal_append_torn_tail_takeover_and_terminal_finalize_are_fenced() -> None:
  ledger = SimulatedArtifactLedger()
  header = b'{"run_id":"run-1"}'
  header_sha = hashlib.sha256(header).hexdigest()
  ledger.put_blob(
    role="runtime_host", payload=header, media_type="application/vnd.echelon-forge.run-journal-header.v1+json",
    expected_sha256=header_sha, retention_class="run-retained", audit_identity="audit-header",
  )
  token = ledger.acquire_fence(
    role="runtime_host", stream_id="journal:run-1", writer_id="boot-a",
    expected_generation=0, audit_identity="audit-journal-fence",
  )
  ledger.open_journal(
    role="runtime_host", journal_id="run-1", header_blob_sha256=header_sha,
    token=token, audit_identity="audit-journal-open",
  )
  ledger.append_journal(
    role="runtime_host", journal_id="run-1", payload=b"step-0",
    expected_sequence=0, token=token, audit_identity="audit-step-0",
  )
  for digest in (header_sha, hashlib.sha256(b"step-0").hexdigest()):
    with pytest.raises(LedgerContractError, match="journal.read"):
      ledger.get_blob(role="release_controller", digest=digest)
  with pytest.raises(LedgerContractError, match="audit_identity"):
    ledger.finalize_journal(
      role="runtime_host", journal_id="run-1", terminal_state="failed",
      expected_last_sequence=0, token=token, audit_identity="",
    )
  assert ledger.read_journal(role="runtime_evidence", journal_id="run-1").terminal_state is None
  other = ledger.acquire_fence(
    role="runtime_host", stream_id="journal:run-2", writer_id="boot-b",
    expected_generation=0, audit_identity="audit-other-fence",
  )
  other_header = b'{"run_id":"run-2"}'
  other_header_sha = hashlib.sha256(other_header).hexdigest()
  ledger.put_blob(
    role="runtime_host", payload=other_header,
    media_type="application/vnd.echelon-forge.run-journal-header.v1+json",
    expected_sha256=other_header_sha, retention_class="run-retained", audit_identity="audit-other-header",
  )
  ledger.open_journal(
    role="runtime_host", journal_id="run-2", header_blob_sha256=other_header_sha,
    token=other, audit_identity="audit-other-open",
  )
  with pytest.raises(LedgerContractError, match="stream mismatches"):
    ledger.finalize_journal(
      role="runtime_host", journal_id="run-1", terminal_state="failed",
      expected_last_sequence=0, token=other, audit_identity="audit-cross-finalize",
    )
  for fake_terminal in ("completed", "crashed", "incomplete"):
    with pytest.raises(LedgerContractError, match="reconcile_crashed_journal"):
      ledger.finalize_journal(
        role="crash_reconciler", journal_id="run-1", terminal_state=fake_terminal,
        expected_last_sequence=0, token=token, audit_identity=f"audit-fake-{fake_terminal}",
      )
  with pytest.raises(LedgerContractError, match="sequence"):
    ledger.append_journal(
      role="runtime_host", journal_id="run-1", payload=b"step-2",
      expected_sequence=2, token=token, audit_identity="audit-step-bad",
    )
  with pytest.raises(LedgerContractError, match="runtime_host-only"):
    ledger.append_journal(
      role="crash_reconciler", journal_id="run-1", payload=b"rogue",
      expected_sequence=1, token=token, audit_identity="audit-rogue-append",
    )
  ledger.inject_torn_tail_for_test("run-1", b"partial-frame")
  read = ledger.read_journal(role="runtime_evidence", journal_id="run-1")
  assert len(read.frames) == 1 and read.torn_tail_discarded
  proof = ledger.confirm_process_terminated(
    role="crash_reconciler", token=token, observed_exit_sha256="f" * 64,
    audit_identity="audit-crash-exit-proof",
  )
  ledger.tombstone_writer(
    role="crash_reconciler", token=token, termination_proof=proof,
    audit_identity="audit-crash-tombstone",
  )
  recovery = ledger.acquire_fence(
    role="crash_reconciler", stream_id="journal:run-1", writer_id="reconciler-b",
    expected_generation=1, audit_identity="audit-recovery-fence",
  )
  with pytest.raises(LedgerContractError, match="non-empty"):
    ledger.reconcile_crashed_journal(
      role="crash_reconciler", journal_id="run-1", payload=b"", terminal_state="crashed",
      token=recovery, audit_identity="audit-reconcile-empty",
    )
  with pytest.raises(LedgerContractError, match="crash_reconciler-only"):
    ledger.reconcile_crashed_journal(
      role="runtime_host", journal_id="run-1", payload=b"wrong-role", terminal_state="crashed",
      token=recovery, audit_identity="audit-reconcile-wrong-role",
    )
  finalized = ledger.reconcile_crashed_journal(
    role="crash_reconciler", journal_id="run-1", payload=b"crash-reconciliation", terminal_state="crashed",
    token=recovery, audit_identity="audit-reconcile",
  )
  assert finalized.durable
  assert ledger.read_journal(role="runtime_evidence", journal_id="run-1").terminal_state == "crashed"
  with pytest.raises(LedgerContractError, match="runtime_host-only"):
    ledger.append_journal(
      role="crash_reconciler", journal_id="run-1", payload=b"rewrite",
      expected_sequence=2, token=recovery, audit_identity="audit-rewrite",
    )
  restored = SimulatedArtifactLedger.restore_snapshot(ledger.export_snapshot(role="runtime_evidence"))
  assert restored.read_journal(role="runtime_evidence", journal_id="run-1").terminal_state == "crashed"
  tampered_media = json.loads(ledger.export_snapshot(role="runtime_evidence"))
  record_digest = hashlib.sha256(b"step-0").hexdigest()
  tampered_record_metadata = next(blob["metadata"] for blob in tampered_media["blobs"] if blob["metadata"]["digest"] == record_digest)
  tampered_record_metadata["media_type"] = "application/vnd.echelon-forge.state-checkpoint-envelope.v1+json"
  tampered_record_metadata["retention_class"] = "rollback-window"
  with pytest.raises(LedgerContractError, match="journal frame integrity"):
    SimulatedArtifactLedger.restore_snapshot(canonical_json_bytes(tampered_media))
  tampered = json.loads(ledger.export_snapshot(role="runtime_evidence"))
  tampered["blobs"][0]["metadata"]["media_type"] = "application/x-forged"
  with pytest.raises(LedgerContractError, match="integrity"):
    SimulatedArtifactLedger.restore_snapshot(canonical_json_bytes(tampered))
  tampered_terminal = json.loads(ledger.export_snapshot(role="runtime_evidence"))
  tampered_terminal["journals"][0]["finalization"]["terminal_state"] = "failed"
  with pytest.raises(LedgerContractError, match="finalization integrity"):
    SimulatedArtifactLedger.restore_snapshot(canonical_json_bytes(tampered_terminal))
  open_journal_snapshot = SimulatedArtifactLedger()
  open_header = b'{"run_id":"open-run"}'
  open_header_sha = hashlib.sha256(open_header).hexdigest()
  open_journal_snapshot.put_blob(
    role="runtime_host", payload=open_header,
    media_type="application/vnd.echelon-forge.run-journal-header.v1+json",
    expected_sha256=open_header_sha, retention_class="run-retained", audit_identity="audit-open-header",
  )
  open_token = open_journal_snapshot.acquire_fence(
    role="runtime_host", stream_id="journal:open-run", writer_id="open-writer",
    expected_generation=0, audit_identity="audit-open-fence",
  )
  open_journal_snapshot.open_journal(
    role="runtime_host", journal_id="open-run", header_blob_sha256=open_header_sha,
    token=open_token, audit_identity="audit-open-journal",
  )
  tampered_open = json.loads(open_journal_snapshot.export_snapshot(role="runtime_evidence"))
  tampered_open["journals"][0]["fence_generation"] = 0
  tampered_open["journals"][0]["writer_id"] = ""
  with pytest.raises(LedgerContractError, match="journal fence generation"):
    SimulatedArtifactLedger.restore_snapshot(canonical_json_bytes(tampered_open))
  tampered_retention = json.loads(open_journal_snapshot.export_snapshot(role="runtime_evidence"))
  next(blob["metadata"] for blob in tampered_retention["blobs"] if blob["metadata"]["digest"] == open_header_sha)["retention_class"] = "evidence-short"
  with pytest.raises(LedgerContractError, match="journal retention class"):
    SimulatedArtifactLedger.restore_snapshot(canonical_json_bytes(tampered_retention))
  with pytest.raises(LedgerContractError, match="snapshot export is runtime_evidence-only"):
    open_journal_snapshot.export_snapshot(role="crash_reconciler")


def test_stored_inventory_is_hash_bound_to_release_and_rollout() -> None:
  ledger = SimulatedArtifactLedger()
  inventory = _inventory()
  _populate_inventory(ledger, inventory)
  assert _descriptor(inventory, "resolved_composition_plan", 1).blob_sha256 == hashlib.sha256(_plan_bytes()).hexdigest()
  inventory_sha, ack = store_inventory(ledger, inventory, audit_identity="audit-inventory")
  assert ack.durable
  release = _test_release_envelope()
  rollout = _decision(state="prepared", sequence=0, decision_id="decision-0")
  validate_release_inventory_binding(release, rollout, inventory, inventory_sha)
  with pytest.raises(LedgerContractError, match="inventory digest differs"):
    validate_release_inventory_binding(release, rollout, inventory, "0" * 64)


def test_n_and_n_minus_one_readers_fail_closed_for_skew_features_state_and_topology() -> None:
  plan_bytes = _plan_bytes()
  inventory = _inventory()
  descriptor = _descriptor(inventory, "resolved_composition_plan", 1)
  reader_n = CompatibilityReader(
    generation=2, supported_state_schema_generation=1,
    supported_features={"native_step_authority"},
  )
  assert reader_n.admit_authority(descriptor, plan_bytes)["payload"]["authority_kind"] == "resolved_composition_plan"
  descriptor_n, plan_bytes_n = _generation_2_plan()
  assert reader_n.admit_authority(descriptor_n, plan_bytes_n)["payload"]["writer_generation"] == "2"
  reader_same = CompatibilityReader(
    generation=1, supported_state_schema_generation=1,
    supported_features={"native_step_authority"},
  )
  reader_same.admit_authority(descriptor, plan_bytes)
  with pytest.raises(LedgerContractError, match="N/N-1"):
    CompatibilityReader(
      generation=3, supported_state_schema_generation=1,
      supported_features={"native_step_authority"},
    ).admit_authority(descriptor, plan_bytes)
  with pytest.raises(LedgerContractError, match="N/N-1"):
    reader_same.admit_authority(descriptor_n, plan_bytes_n)
  with pytest.raises(LedgerContractError, match="unknown truth"):
    reader_n.admit_authority(replace(descriptor, truth_features=("future_truth",)), plan_bytes)
  with pytest.raises(LedgerContractError, match="state schema"):
    reader_n.admit_authority(replace(descriptor, state_schema_generation=2), plan_bytes)
  with pytest.raises(LedgerContractError, match="topology"):
    reader_n.admit_authority(replace(descriptor, topology="remote"), plan_bytes)
  with pytest.raises(LedgerContractError, match="bytes differ"):
    reader_n.admit_authority(descriptor, plan_bytes + b" ")


def test_reader_first_gate_requires_every_reader_and_available_rollback_artifact() -> None:
  ledger = SimulatedArtifactLedger()
  inventory = _inventory()
  _populate_inventory(ledger, inventory)
  digest = frozenset(item.blob_sha256 for item in inventory.artifacts)
  admitted = tuple(sorted(item.blob_sha256 for item in inventory.artifacts))
  readers = (
    ReaderDeployment("reader-a", 2, True, True, (1, 2), admitted, 1, ("native_step_authority",), ("in-process",)),
    ReaderDeployment("reader-b", 2, True, True, (1, 2), admitted, 1, ("native_step_authority",), ("in-process",)),
    ReaderDeployment("diagnostic-old", 1, False, True, (1,)),
  )
  assert reader_first_ready(
    current_writer_generation=1, target_writer_generation=2, readers=readers,
    inventory=inventory, available_blob_digests=digest, ledger=ledger,
  )
  assert not reader_first_ready(
    current_writer_generation=1, target_writer_generation=2,
    readers=(replace(readers[0], healthy=False), readers[1]), inventory=inventory,
    available_blob_digests=digest, ledger=ledger,
  )
  assert not reader_first_ready(
    current_writer_generation=1, target_writer_generation=2, readers=readers,
    inventory=inventory, available_blob_digests=set(), ledger=ledger,
  )
  assert not reader_first_ready(
    current_writer_generation=1, target_writer_generation=2,
    readers=(ReaderDeployment("future-reader", 3, True, True, (2, 3), admitted, 1, ("native_step_authority",), ("in-process",)),),
    inventory=inventory, available_blob_digests=digest, ledger=ledger,
  )
  missing_package_admission = tuple(
    item for item in readers[0].admitted_artifact_digests
    if item not in {
      artifact.blob_sha256 for artifact in inventory.artifacts if artifact.authority_kind == "release_package"
    }
  )
  assert not reader_first_ready(
    current_writer_generation=1, target_writer_generation=2,
    readers=(replace(readers[0], admitted_artifact_digests=missing_package_admission), readers[1]),
    inventory=inventory, available_blob_digests=digest, ledger=ledger,
  )
  bad_candidate_package = replace(
    inventory,
    artifacts=tuple(
      replace(item, reader_generation_min=1, reader_generation_max=1)
      if item.authority_kind == "release_package" and item.writer_generation == 2 else item
      for item in inventory.artifacts
    ),
  )
  assert not reader_first_ready(
    current_writer_generation=1, target_writer_generation=2, readers=readers,
    inventory=bad_candidate_package, available_blob_digests=digest, ledger=ledger,
  )
  with pytest.raises(LedgerContractError, match="generation-N plan/package"):
    inventory_payload(bad_candidate_package)
  rollback_package = _descriptor(inventory, "release_package", 1)
  duplicate_rollback_package = replace(
    rollback_package,
    blob_sha256="f" * 64,
  )
  duplicate_inventory = replace(
    inventory,
    artifacts=tuple(sorted(
      (*inventory.artifacts, duplicate_rollback_package),
      key=lambda item: (item.authority_kind, item.writer_generation, item.blob_sha256),
    )),
  )
  with pytest.raises(LedgerContractError, match="one exact artifact"):
    inventory_payload(duplicate_inventory)
  no_candidate_plan = replace(
    inventory,
    artifacts=tuple(
      item for item in inventory.artifacts
      if not (item.authority_kind == "resolved_composition_plan" and item.writer_generation == 2)
    ),
  )
  assert not reader_first_ready(
    current_writer_generation=1, target_writer_generation=2, readers=readers,
    inventory=no_candidate_plan, available_blob_digests=digest, ledger=ledger,
  )
  assert not reader_first_ready(
    current_writer_generation=1, target_writer_generation=2,
    readers=(readers[0], replace(readers[1], reader_id="reader-a")),
    inventory=inventory, available_blob_digests=digest, ledger=ledger,
  )
  assert not reader_first_ready(
    current_writer_generation=1, target_writer_generation=2,
    readers=(replace(readers[0], supported_state_schema_generation=0), readers[1]),
    inventory=inventory, available_blob_digests=digest, ledger=ledger,
  )


def test_release_reader_window_and_state_schema_are_bound_to_inventory() -> None:
  inventory = _inventory()
  release = _test_release_envelope()
  rollout = json.loads(_vector("authority_rollout_decision.v1.json")["envelope_json"])
  widened = dict(release["payload"], reader_generation_max="9")
  widened_envelope = build_release_manifest_shell(widened)
  with pytest.raises(LedgerContractError, match="reader_generation_max"):
    validate_release_inventory(
      widened_envelope, inventory,
      hashlib.sha256(canonical_json_bytes(inventory_payload(inventory))).hexdigest(),
    )
  schema_skew = dict(release["payload"], state_schema_generation="2")
  schema_skew_envelope = build_release_manifest_shell(schema_skew)
  with pytest.raises(LedgerContractError, match="state schema"):
    validate_release_inventory(
      schema_skew_envelope, inventory,
      hashlib.sha256(canonical_json_bytes(inventory_payload(inventory))).hexdigest(),
    )
  assert rollout["payload"]["plan_reader_generation_max"] == "2"


def test_shadow_receipt_is_structurally_non_authoritative_and_schema_valid() -> None:
  fixture = shadow_receipt_payload(
    receipt_id="shadow-1", plan_sha256="a" * 64, release_manifest_sha256="b" * 64,
    rollout_decision_sha256="c" * 64, comparison_kind="cpu-exact-result",
    outcome="match", evidence_sha256="d" * 64,
  )
  assert fixture["authoritative"] is False
  schema = json.loads((ROOT / "src/runtime/contracts/ledger/artifact_ledger_contract.v1.schema.json").read_text(encoding="utf-8"))
  Draft202012Validator(schema).validate(fixture)
  invalid = dict(fixture, authoritative=True)
  assert list(Draft202012Validator(schema).iter_errors(invalid))


def test_rollout_state_machine_is_single_writer_nonproduction_and_kill_switch_fail_closed() -> None:
  ledger = SimulatedArtifactLedger()
  token = ledger.acquire_fence(
    role="release_controller", stream_id="qualification-rollout:release-2026-08-25", writer_id="controller-a",
    expected_generation=0, audit_identity="audit-rollout-fence",
  )
  controller = _controller(ledger, token)
  inventory = _inventory()
  with pytest.raises(LedgerContractError, match="checkpoint"):
    controller.commit_qualification_decision(
      _decision(state="prepared", sequence=0, decision_id="decision-forged-checkpoint", checkpoint_id="missing-checkpoint"),
      audit_identity="audit-forged-checkpoint", evidence=_evidence(ledger, "prepared", inventory),
    )
  controller.commit_qualification_decision(
    _decision(state="prepared", sequence=0, decision_id="decision-0"),
    audit_identity="audit-prepared", evidence=_evidence(ledger, "prepared", inventory),
  )
  with pytest.raises(LedgerContractError, match="state transition"):
    controller.commit_qualification_decision(
      _decision(state="canary-ready", sequence=1, decision_id="decision-skip", predecessor="decision-0"),
      audit_identity="audit-skip",
    )
  controller.commit_qualification_decision(
    _decision(state="shadow", sequence=1, decision_id="decision-1", predecessor="decision-0"),
    audit_identity="audit-shadow", evidence=_evidence(ledger, "shadow", inventory),
  )
  assert controller.production_authorized is False
  reasons = controller.activate_kill_switch(CanaryHealth(wrong_epoch_results=1), audit_identity="audit-kill")
  assert reasons == ("wrong_epoch_results",) and not controller.admissions_open
  with pytest.raises(LedgerContractError, match="backed-out successor"):
    controller.commit_qualification_decision(
      _decision(state="canary-ready", sequence=2, decision_id="decision-2", predecessor="decision-1"),
      audit_identity="audit-canary-ready",
    )
  controller.commit_qualification_decision(
    _decision(state="backed-out", sequence=2, decision_id="decision-5", predecessor="decision-1", checkpoint_id="checkpoint-1"),
    audit_identity="audit-backout",
    evidence=_evidence(
      ledger, "backed-out", inventory,
      predecessor=_decision(state="shadow", sequence=1, decision_id="decision-1", predecessor="decision-0"),
    ),
  )
  controller = _controller(ledger, token)
  reasons = controller.activate_kill_switch(
    CanaryHealth(security_bypasses=1), audit_identity="audit-kill-after-backout-restart",
  )
  assert reasons == ("security_bypasses", "wrong_epoch_results")
  controller.commit_qualification_decision(
    _decision(state="prepared", sequence=3, decision_id="decision-repaired", predecessor="decision-5"),
    audit_identity="audit-repaired-prepared", evidence=_evidence(ledger, "prepared", inventory),
  )
  assert controller.admissions_open


def test_kill_switch_before_first_decision_is_durable_and_fail_closed() -> None:
  ledger = SimulatedArtifactLedger()
  token = ledger.acquire_fence(
    role="release_controller", stream_id="qualification-rollout:release-2026-08-25", writer_id="controller-a",
    expected_generation=0, audit_identity="audit-early-kill-fence",
  )
  controller = _controller(ledger, token)
  reasons = controller.activate_kill_switch(
    CanaryHealth(security_bypasses=1, artifact_slo_breaches=1), audit_identity="audit-early-kill",
  )
  assert reasons == ("artifact_slo_breaches", "security_bypasses") and not controller.admissions_open
  restarted = _controller(ledger, token)
  reasons = controller.activate_kill_switch(
    CanaryHealth(wrong_epoch_results=1), audit_identity="audit-early-kill-second-trigger",
  )
  assert reasons == ("artifact_slo_breaches", "security_bypasses", "wrong_epoch_results")
  restarted = _controller(ledger, token)
  assert not restarted.admissions_open
  reasons = restarted.activate_kill_switch(
    CanaryHealth(plan_byte_divergences=1), audit_identity="audit-early-kill-after-restart",
  )
  assert reasons == ("artifact_slo_breaches", "plan_byte_divergences", "security_bypasses", "wrong_epoch_results")
  with pytest.raises(LedgerContractError, match="kill switch"):
    restarted.commit_qualification_decision(
      _decision(state="prepared", sequence=0, decision_id="decision-early-kill-rejected"),
      audit_identity="audit-early-kill-rejected",
      evidence=_evidence(ledger, "prepared", _inventory()),
    )
  restored = SimulatedArtifactLedger.restore_snapshot(ledger.export_snapshot(role="runtime_evidence"))
  assert not _controller(restored, token).admissions_open


def test_rollout_controller_recovers_qualification_state_and_kill_switch_from_slot() -> None:
  ledger = SimulatedArtifactLedger()
  token = ledger.acquire_fence(
    role="release_controller", stream_id="qualification-rollout:release-2026-08-25", writer_id="controller-a",
    expected_generation=0, audit_identity="audit-recovery-fence",
  )
  controller = _controller(ledger, token)
  inventory = _inventory()
  controller.commit_qualification_decision(
    _decision(state="prepared", sequence=0, decision_id="decision-recovery-0"),
    audit_identity="audit-recovery-prepared", evidence=_evidence(ledger, "prepared", inventory),
  )
  restarted = _controller(ledger, token)
  assert restarted.admissions_open
  restarted.commit_qualification_decision(
    _decision(state="shadow", sequence=1, decision_id="decision-recovery-1", predecessor="decision-recovery-0"),
    audit_identity="audit-recovery-shadow",
    evidence=_evidence(
      ledger, "shadow", inventory,
      predecessor=_decision(state="prepared", sequence=0, decision_id="decision-recovery-0"),
    ),
  )
  restarted.activate_kill_switch(CanaryHealth(wrong_epoch_results=1), audit_identity="audit-recovery-kill")
  recovered_after_kill = _controller(ledger, token)
  assert not recovered_after_kill.admissions_open
  with pytest.raises(LedgerContractError, match="kill switch"):
    recovered_after_kill.commit_qualification_decision(
      _decision(state="canary-ready", sequence=2, decision_id="decision-recovery-2", predecessor="decision-recovery-1"),
      audit_identity="audit-recovery-rejected",
    )
  restored = SimulatedArtifactLedger.restore_snapshot(ledger.export_snapshot(role="runtime_evidence"))
  proof = restored.confirm_process_terminated(
    role="crash_reconciler", token=token, observed_exit_sha256="a" * 64,
    audit_identity="audit-controller-exit",
  )
  restored.tombstone_writer(
    role="crash_reconciler", token=token, termination_proof=proof,
    audit_identity="audit-controller-tombstone",
  )
  successor = restored.acquire_fence(
    role="release_controller", stream_id=token.stream_id, writer_id="controller-b",
    expected_generation=1, audit_identity="audit-controller-successor",
  )
  taken_over = _controller(restored, successor)
  assert not taken_over.admissions_open


def test_rollout_entry_evidence_requires_retrievable_proof_bytes() -> None:
  ledger = SimulatedArtifactLedger()
  token = ledger.acquire_fence(
    role="release_controller", stream_id="qualification-rollout:release-2026-08-25", writer_id="controller-a",
    expected_generation=0, audit_identity="audit-proof-fence",
  )
  controller = _controller(ledger, token)
  inventory = _inventory()
  prepared = _decision(state="prepared", sequence=0, decision_id="decision-proof-0")
  controller.commit_qualification_decision(
    prepared, audit_identity="audit-proof-prepared", evidence=_evidence(ledger, "prepared", inventory),
  )
  controller.commit_qualification_decision(
    _decision(state="shadow", sequence=1, decision_id="decision-proof-1", predecessor="decision-proof-0"),
    audit_identity="audit-proof-shadow", evidence=_evidence(ledger, "shadow", inventory, predecessor=prepared),
  )
  mismatched_evidence = _evidence(ledger, "canary-ready", inventory, predecessor=prepared)
  with pytest.raises(LedgerContractError, match="required release/kind/outcome"):
    controller.commit_qualification_decision(
      _decision(state="canary-ready", sequence=2, decision_id="decision-proof-mismatch", predecessor="decision-proof-1"),
      audit_identity="audit-proof-mismatched-authority", evidence=mismatched_evidence,
    )
  evidence = _evidence(
    ledger, "canary-ready", inventory,
    predecessor=_decision(state="shadow", sequence=1, decision_id="decision-proof-1", predecessor="decision-proof-0"),
  )
  evidence_record, _ = ledger.get_blob(role="release_controller", digest=evidence.storage_restore_drill_sha256)
  proof_digest = json.loads(evidence_record)["evidence_sha256"]
  ledger.set_blob_availability_for_test(proof_digest, available=False)
  with pytest.raises(LedgerContractError, match="proof bytes"):
    controller.commit_qualification_decision(
      _decision(state="canary-ready", sequence=2, decision_id="decision-proof-2", predecessor="decision-proof-1"),
      audit_identity="audit-proof-unavailable", evidence=evidence,
    )
  ledger.set_blob_availability_for_test(proof_digest, available=True)
def test_writer_advancement_requires_reader_first_inventory_evidence() -> None:
  ledger = SimulatedArtifactLedger()
  _put_plan(ledger)
  token = ledger.acquire_fence(
    role="release_controller", stream_id="qualification-rollout:release-2026-08-25", writer_id="controller-a",
    expected_generation=0, audit_identity="audit-rollout-fence",
  )
  controller = _controller(ledger, token)
  inventory = _inventory()
  states = ("prepared", "shadow", "canary-ready", "production-canary")
  predecessor = ""
  previous_envelope: dict[str, object] | None = None
  for sequence, state in enumerate(states):
    decision_id = f"decision-{sequence}"
    decision = _decision(state=state, sequence=sequence, decision_id=decision_id, predecessor=predecessor)
    controller.commit_qualification_decision(
      decision,
      audit_identity=f"audit-{state}",
      evidence=_evidence(ledger, state, inventory, predecessor=previous_envelope),
    )
    predecessor = decision_id
    previous_envelope = decision
  advanced = _decision(
    state="adoption-expanding", sequence=4, decision_id="decision-4",
    predecessor="decision-3", writer_generation=2,
  )
  retained_generation_1_plan = build_rollout_decision_shell({
    **advanced["payload"],
    "plan_sha256": _vector("authority_resolved_composition_plan.v1.json")["payload_sha256"],
    "plan_reader_generation_min": "1",
    "plan_reader_generation_max": "2",
  })
  with pytest.raises(LedgerContractError, match="exact stored plan"):
    controller.commit_qualification_decision(
      retained_generation_1_plan, audit_identity="audit-advance-retained-plan",
      reader_deployments=_reader_deployments(inventory),
      evidence=_evidence(ledger, "adoption-expanding", inventory, predecessor=previous_envelope),
    )
  with pytest.raises(LedgerContractError, match="reader-first"):
    controller.commit_qualification_decision(advanced, audit_identity="audit-advance-bad")
  ack = controller.commit_qualification_decision(
    advanced,
    audit_identity="audit-advance-good",
    reader_deployments=_reader_deployments(inventory),
    evidence=_evidence(ledger, "adoption-expanding", inventory, predecessor=previous_envelope),
  )
  assert ack.version == 5 and controller.production_authorized is False
  restarted_on_generation_2 = _controller(
    ledger, token,
    plan_envelope=json.loads(_vector("authority_resolved_composition_plan.generation2.v1.json")["envelope_json"]),
  )
  assert restarted_on_generation_2.admissions_open
  controller.activate_kill_switch(CanaryHealth(plan_byte_divergences=1), audit_identity="audit-kill-after-advance")
  backed_out = _decision(
    state="backed-out", sequence=5, decision_id="decision-5",
    predecessor="decision-4", writer_generation=1, checkpoint_id="checkpoint-1",
  )
  rollback_ack = controller.commit_qualification_decision(
    backed_out, audit_identity="audit-writer-backout",
    evidence=_evidence(ledger, "backed-out", inventory, predecessor=advanced),
  )
  assert rollback_ack.version == 7


def test_rollback_window_and_stable_require_generation_n_writer() -> None:
  ledger = SimulatedArtifactLedger()
  token = ledger.acquire_fence(
    role="release_controller", stream_id="qualification-rollout:release-2026-08-25", writer_id="controller-a",
    expected_generation=0, audit_identity="audit-generation-state-fence",
  )
  controller = _controller(ledger, token)
  inventory = _inventory()
  predecessor = ""
  previous: dict[str, object] | None = None
  for sequence, state in enumerate(("prepared", "shadow", "canary-ready", "production-canary", "adoption-expanding")):
    decision = _decision(
      state=state, sequence=sequence, decision_id=f"decision-generation-{sequence}", predecessor=predecessor,
    )
    controller.commit_qualification_decision(
      decision, audit_identity=f"audit-generation-{state}",
      evidence=_evidence(ledger, state, inventory, predecessor=previous),
    )
    predecessor = decision["payload"]["decision_id"]
    previous = decision
  rejected = _decision(
    state="rollback-window", sequence=5, decision_id="decision-generation-rejected", predecessor=predecessor,
  )
  with pytest.raises(LedgerContractError, match="generation-N writer"):
    controller.commit_qualification_decision(
      rejected, audit_identity="audit-generation-rollback-rejected",
      evidence=_evidence(ledger, "rollback-window", inventory, predecessor=previous),
    )
  advanced = _decision(
    state="adoption-expanding", sequence=5, decision_id="decision-generation-advanced",
    predecessor=predecessor, writer_generation=2,
  )
  controller.commit_qualification_decision(
    advanced, audit_identity="audit-generation-advanced",
    reader_deployments=_reader_deployments(inventory),
    evidence=_evidence(ledger, "adoption-expanding", inventory, predecessor=previous),
  )
  rollback_window = _decision(
    state="rollback-window", sequence=6, decision_id="decision-generation-rollback-window",
    predecessor="decision-generation-advanced", writer_generation=2,
  )
  controller.commit_qualification_decision(
    rollback_window, audit_identity="audit-generation-rollback-window",
    evidence=_evidence(ledger, "rollback-window", inventory, predecessor=advanced),
  )
  stable = _decision(
    state="stable", sequence=7, decision_id="decision-generation-stable",
    predecessor="decision-generation-rollback-window", writer_generation=2,
  )
  ack = controller.commit_qualification_decision(
    stable, audit_identity="audit-generation-stable",
    evidence=_evidence(ledger, "stable", inventory, predecessor=rollback_window),
  )
  assert ack.durable


def test_kill_switch_thresholds_and_backout_protocols_preserve_irreversible_boundary() -> None:
  assert kill_switch_reasons(CanaryHealth()) == ()
  assert kill_switch_reasons(CanaryHealth(security_bypasses=1, artifact_slo_breaches=2)) == (
    "security_bypasses", "artifact_slo_breaches",
  )
  assert select_backout_protocol(
    current_generation=2, target_generation=2, same_release=True,
    compatible_checkpoint_available=True, rollback_package_available=True,
    irreversible_write_boundary="none",
  ) == "same-release-checkpoint-recovery"
  assert select_backout_protocol(
    current_generation=2, target_generation=1, same_release=False,
    compatible_checkpoint_available=True, rollback_package_available=True,
    irreversible_write_boundary="none",
  ) == "package-restart-from-checkpoint"
  assert select_backout_protocol(
    current_generation=2, target_generation=1, same_release=False,
    compatible_checkpoint_available=False, rollback_package_available=True,
    irreversible_write_boundary="none",
  ) == "package-restart-new-run"
  assert select_backout_protocol(
    current_generation=2, target_generation=1, same_release=False,
    compatible_checkpoint_available=True, rollback_package_available=True,
    irreversible_write_boundary="external-write-v2",
  ) == "stop-or-roll-forward"
  with pytest.raises(LedgerContractError, match="N to N-1"):
    select_backout_protocol(
      current_generation=3, target_generation=1, same_release=False,
      compatible_checkpoint_available=True, rollback_package_available=True,
      irreversible_write_boundary="none",
    )


def test_ledger_schema_and_generated_fixtures_are_fresh_and_exact() -> None:
  schema = json.loads((ROOT / "src/runtime/contracts/ledger/artifact_ledger_contract.v1.schema.json").read_text(encoding="utf-8"))
  Draft202012Validator.check_schema(schema)
  authority_root = ROOT / "src/runtime/contracts/authority"
  authority_envelope = json.loads((authority_root / "authority_envelope.v1.schema.json").read_text(encoding="utf-8"))
  authority_payloads = json.loads((authority_root / "authority_payloads.v1.schema.json").read_text(encoding="utf-8"))
  resolver = RefResolver(
    base_uri=schema["$id"],
    referrer=schema,
    store={authority_envelope["$id"]: authority_envelope, authority_payloads["$id"]: authority_payloads},
  )
  validator = Draft202012Validator(schema, resolver=resolver)
  fixtures = build_fixtures()
  for name, expected in fixtures.items():
    actual = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert actual == expected
    validator.validate(actual)
  rollout_only_constraint = schema["$defs"]["rollout_qualification_record"]["properties"]["candidate_rollout_decision"]["allOf"][1]
  assert list(Draft202012Validator(rollout_only_constraint).iter_errors(_plan_envelope()))
  inventory = inventory_payload(_inventory())
  unknown = dict(inventory, hidden_default=True)
  inventory_validator = Draft202012Validator({
    "$schema": schema["$schema"],
    "$defs": schema["$defs"],
    "$ref": "#/$defs/stored_artifact_inventory",
  })
  assert list(inventory_validator.iter_errors(unknown))


def test_inventory_rejects_duplicate_unsorted_or_inverted_artifacts() -> None:
  inventory = _inventory()
  descriptor = _descriptor(inventory, "resolved_composition_plan", 1)
  duplicate = replace(inventory, artifacts=(descriptor, descriptor))
  with pytest.raises(LedgerContractError, match="sorted and identity-unique"):
    inventory_payload(duplicate)
  inverted = replace(descriptor, reader_generation_min=2, reader_generation_max=1)
  with pytest.raises(LedgerContractError, match="window is inverted"):
    inventory_payload(replace(inventory, artifacts=(inverted,)))
  widened = replace(descriptor, reader_generation_max=999)
  with pytest.raises(LedgerContractError, match="bounded inventory"):
    inventory_payload(replace(inventory, artifacts=tuple(
      widened if item == descriptor else item for item in inventory.artifacts
    )))
