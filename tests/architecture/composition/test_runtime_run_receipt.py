from __future__ import annotations

import json
import hashlib
import os
import sqlite3
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import pytest
from jsonschema import Draft202012Validator

from tools.maintenance.generate_runtime_run_receipt_vector import build_vector
from tools.maintenance.runtime_durable_artifact_ledger import (
  CHECKPOINT_VALIDATION_MEDIA_TYPE,
  FenceToken,
  SQLiteArtifactLedger,
)
from tools.maintenance.runtime_execution_provenance import (
  ExecutionObservation,
  collect_actual_bindings,
  observed_measurement_sha256,
)
from tools.maintenance.runtime_authority_contracts import build_state_checkpoint_shell, canonical_json_bytes
from tools.maintenance.runtime_run_receipt import (
  MAX_SAFE_INTEGER,
  REQUIRED_FIELDS,
  RunReceiptError,
  build_run_receipt,
  run_receipt_schema,
  validate_run_receipt,
)


ROOT = Path(__file__).resolve().parents[3]


def _default_execution_observation() -> ExecutionObservation:
  fixtures = ROOT / "tests/architecture/composition/fixtures"
  return collect_actual_bindings(
    executable_path=fixtures / "authority_cross_language_vector.v1.json",
    executable_identity="ef_test", executable_version="1.0.0",
    package_path=fixtures / "authority_rollout_decision.v1.json",
    package_identity="echelon-forge-wheel", package_version="1.0.0",
    wheel_path=fixtures / "authority_rollout_decision.v1.json",
    native_module_paths={"ef_core": fixtures / "authority_state_checkpoint.v1.json"},
    runtime_dependency_paths={
      "nlohmann_json": fixtures / "authority_resolved_composition_plan.v1.json",
    },
    input_artifact_paths={
      "plan": fixtures / "authority_resolved_composition_plan.v1.json",
      "request": fixtures / "authority_rollout_decision.v1.json",
    },
    gpu="none", driver="none",
  )


def _receipt(*, terminal_state: str = "completed", journal_last_sequence: int = 0, journal_last_record_sha256: str | None = None, **overrides: object) -> dict:
  value = {
    "receipt_id": "receipt-1",
    "run_id": "run-1",
    "attempt_id": "attempt-1",
    "host_boot_id": "boot-1",
    "incarnation_epoch": "1",
    "writer_generation": "1", "reader_generation_min": "1", "reader_generation_max": "1",
    "plan_binding": {
      "plan_id": "plan-1", "plan_sha256": "1" * 64, "request_sha256": "2" * 64, "plan_generation": "1",
      "plan_canonical_sha256": "1" * 64, "plan_location": "ledger://plan-1", "request_canonical_sha256": "2" * 64,
      "request_location": "ledger://request-1", "compiler_identity": "PlanCompiler", "compiler_version": "1.0.0",
    },
    "release_binding": {
      "release_id": "release-1", "release_manifest_sha256": "3" * 64, "rollout_decision_id": "decision-1",
      "rollout_decision_sha256": "4" * 64, "provenance_sha256": "5" * 64, "sbom_sha256": "6" * 64, "attestation_sha256": "7" * 64,
    },
    "executable": {"identity": "ef_test", "version": "1.0.0", "digest": "8" * 64, "native_module_digests": {"ef_core": "9" * 64}, "plugin_digests": {}},
    "package": {"identity": "echelon-forge-wheel", "version": "1.0.0", "digest": "a" * 64, "wheel_digest": "b" * 64, "dependency_graph_sha256": "c" * 64},
    "build": {"source_revision": "revision-1", "dirty": False, "build_mode": "Release", "linker": "link.exe", "toolchain": "msvc-v143", "cxx_abi": "msvc-14.44", "python_abi": "cp312-win_amd64", "node_abi": "node-127"},
    "platform": {"os": "windows", "architecture": "amd64", "compiler": "msvc", "standard_library": "msvc", "cpu": "x64", "gpu": "none", "driver": "none", "runtime_dependency_digests": {"nlohmann_json": "d" * 64}},
    "inputs": {
      "scenario_id": "scenario-1", "content_id": "content-1", "database_id": "database-1", "configuration_id": "config-1",
      "seed_policy": "fixed", "seed_value": "seed-1", "seed_stream_id": "seed-stream-1", "artifacts": {"plan": "1" * 64, "request": "2" * 64},
    },
    "backend": {"profile_id": "cpu_exact.reference", "backend_provider_id": "builtin.backend.flecs_cpu", "backend_implementation_version": "1.0.0", "determinism_profile": "exact", "system_graph_sha256": "e" * 64, "stage_contract_sha256": "f" * 64},
    "execution_scope": {"world_ids": ["world-1"], "entity_ids": ["entity-1"], "episode_ids": ["episode-1"], "request_ids": ["request-1"], "epochs": {"world": "1", "entity": "1", "episode": "1", "request": "1"}},
    "lifecycle": [
      {"sequence": 0, "event": "journal_admitted", "timestamp": "2026-09-19T00:00:00Z", "epoch": "1", "durable_sequence": 0},
      {"sequence": 1, "event": "construction", "timestamp": "2026-09-19T00:00:00Z", "epoch": "1", "durable_sequence": 0},
      {"sequence": 2, "event": "validation", "timestamp": "2026-09-19T00:00:00Z", "epoch": "1", "durable_sequence": 0},
      {"sequence": 3, "event": "publication", "timestamp": "2026-09-19T00:00:00Z", "epoch": "1", "durable_sequence": 0},
      {"sequence": 4, "event": "episode", "timestamp": "2026-09-19T00:00:00Z", "epoch": "1", "durable_sequence": journal_last_sequence},
      {"sequence": 5, "event": "drain", "timestamp": "2026-09-19T00:00:01Z", "epoch": "1", "durable_sequence": journal_last_sequence},
      {"sequence": 6, "event": "shutdown", "timestamp": "2026-09-19T00:00:01Z", "epoch": "1", "durable_sequence": journal_last_sequence},
      {"sequence": 7, "event": "reclamation", "timestamp": "2026-09-19T00:00:01Z", "epoch": "1", "durable_sequence": journal_last_sequence},
      {"sequence": 8, "event": "terminal", "timestamp": "2026-09-19T00:00:01Z", "epoch": "1", "durable_sequence": journal_last_sequence},
    ],
    "results": {"result_digest": "1" * 64, "output_artifacts": [{"name": "trace", "digest": "2" * 64, "media_type": "application/octet-stream", "size": 7, "availability": "durable", "retention_class": "run-retained", "retrieval_location": "ledger://blob-" + "2" * 64}], "native_validation": {"accepted": True, "validator_id": "native-run-validator", "evidence_sha256": "3" * 64}},
    "checkpoints": {"source_refs": [], "created_refs": []}, "qualification_refs": [], "side_effect_receipts": [],
    "completion": {"created_at": "2026-09-19T00:00:00Z", "finalized_at": "2026-09-19T00:00:01Z", "durable_ack": True},
    "terminal_state": terminal_state,
    "terminal_reason": "completed" if terminal_state == "completed" else "test failure",
    "journal_id": "run-1",
    "journal_last_sequence": journal_last_sequence,
    "journal_last_record_sha256": journal_last_record_sha256 or "4" * 64,
    "retention_class": "run-retained",
    "authenticity": {"attestation_sha256": "5" * 64, "signatures": []},
  }
  measured = _default_execution_observation()
  value["executable"] = measured["executable"]
  value["package"] = measured["package"]
  value["platform"] = measured["platform"]
  value["inputs"] = {
    **value["inputs"], "artifacts": measured["inputs"]["artifacts"],
  }
  value.update(overrides)
  admission_bindings = {
    key: value[key]
    for key in (
      "receipt_id", "attempt_id", "plan_binding", "release_binding", "executable", "package",
      "build", "platform", "inputs", "backend", "reader_generation_min", "reader_generation_max",
    )
  }
  value["admission_binding_sha256"] = hashlib.sha256(
    canonical_json_bytes(admission_bindings),
  ).hexdigest()
  return build_run_receipt(**value)


def _observed_bindings_for(receipt: Mapping[str, Any]) -> ExecutionObservation:
  observed = _default_execution_observation()
  payload = receipt["payload"]
  assert payload["executable"] == observed["executable"]
  assert payload["package"] == observed["package"]
  assert payload["platform"] == observed["platform"]
  assert payload["inputs"]["artifacts"] == observed["inputs"]["artifacts"]
  return observed


def _bind_output_blob(
  ledger: SQLiteArtifactLedger,
  receipt: Mapping[str, Any],
  *,
  audit_identity: str,
  payload: bytes = b"durable-trace",
) -> dict[str, Any]:
  """Materialize the receipt's output slot before completing the run."""

  output = deepcopy(receipt["payload"])
  digest = ledger.put_blob(
    payload,
    media_type="application/octet-stream",
    retention_class="run-retained",
    audit_identity=audit_identity,
  )
  artifact = output["results"]["output_artifacts"][0]
  artifact.update({
    "digest": digest,
    "size": len(payload),
    "retrieval_location": f"ledger://blob-{digest}",
  })
  return build_run_receipt(**output)


def test_run_receipt_is_canonical_and_schema_shaped() -> None:
  receipt = _receipt()
  validate_run_receipt(receipt)
  assert receipt["payload"]["schema_version"] == "echelon_forge.run_receipt.v1"
  assert receipt["payload_sha256"]
  assert run_receipt_schema()["$id"] == "https://echelon-forge.local/contracts/ledger/run_receipt.v1.schema.json"
  schema = json.loads((ROOT / "src/runtime/contracts/ledger/run_receipt.v1.schema.json").read_text(encoding="utf-8"))
  Draft202012Validator.check_schema(schema)
  Draft202012Validator(schema).validate(receipt)
  assert set(schema["required"]) == set(REQUIRED_FIELDS)


def test_run_receipt_cross_language_vector_is_fresh() -> None:
  fixture = json.loads(
    (ROOT / "tests/architecture/composition/fixtures/run_receipt.v1.json").read_text(
      encoding="utf-8",
    )
  )
  assert fixture == build_vector()


def test_run_receipt_rejects_resealed_lifecycle_or_missing_durable_ack() -> None:
  receipt = _receipt()
  receipt["payload"]["lifecycle"][1]["sequence"] = 99
  with pytest.raises(RunReceiptError, match="lifecycle sequence"):
    validate_run_receipt(receipt)
  receipt = _receipt()
  receipt["payload"]["completion"]["durable_ack"] = False
  with pytest.raises(RunReceiptError, match="durable acknowledgement"):
    validate_run_receipt(receipt)
  receipt = _receipt()
  for event in receipt["payload"]["lifecycle"]:
    event["durable_sequence"] = 999
  with pytest.raises(RunReceiptError, match="journal tail"):
    validate_run_receipt(receipt)


def test_run_receipt_rejects_integers_outside_the_cross_language_safe_range() -> None:
  schema = json.loads(
    (ROOT / "src/runtime/contracts/ledger/run_receipt.v1.schema.json").read_text(encoding="utf-8")
  )
  receipt = _receipt()
  receipt["payload"]["journal_last_sequence"] = MAX_SAFE_INTEGER + 1
  with pytest.raises(RunReceiptError, match="interoperable integer"):
    validate_run_receipt(receipt)
  assert list(Draft202012Validator(schema).iter_errors(receipt))

  receipt = _receipt()
  receipt["payload"]["results"]["output_artifacts"][0]["size"] = MAX_SAFE_INTEGER + 1
  with pytest.raises(RunReceiptError, match="interoperable integer"):
    validate_run_receipt(receipt)
  assert list(Draft202012Validator(schema).iter_errors(receipt))


def test_failed_receipt_empty_result_digest_matches_json_schema() -> None:
  receipt = _receipt(
    terminal_state="failed",
    results={
      "result_digest": "", "output_artifacts": [],
      "native_validation": {"accepted": False, "validator_id": "native-run-validator", "evidence_sha256": "3" * 64},
    },
  )
  validate_run_receipt(receipt)
  schema = json.loads((ROOT / "src/runtime/contracts/ledger/run_receipt.v1.schema.json").read_text(encoding="utf-8"))
  Draft202012Validator(schema).validate(receipt)


def test_completed_receipt_requires_a_durable_output_artifact() -> None:
  receipt = _receipt()
  receipt["payload"]["results"]["output_artifacts"] = []
  with pytest.raises(Exception, match="durable output artifact"):
    build_run_receipt(**receipt["payload"])


def test_sqlite_ledger_admits_receipt_only_after_fenced_journal(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  try:
    token = ledger.acquire_fence("journal:run-1", "writer-1")
    ledger.open_journal(token, "run-1", {"run_id": "run-1", "plan_sha256": "1" * 64}, audit_identity="audit-1")
    frame_digest = ledger.append_journal(token, "run-1", b"step-0", sequence=0, audit_identity="audit-1")
    receipt = _bind_output_blob(
      ledger, _receipt(journal_last_record_sha256=frame_digest), audit_identity="audit-1",
    )
    blob_digest = ledger.finalize_journal(token, "run-1", receipt=receipt, terminal_state="completed", audit_identity="audit-1", actual_bindings=_observed_bindings_for(receipt))
    payload, media_type, retention = ledger.get_blob(blob_digest)
    assert json.loads(payload)["payload"]["receipt_id"] == "receipt-1"
    assert media_type.endswith("run-receipt.v1+json")
    assert retention == "run-retained"
    assert ledger.read_receipt("receipt-1")["payload_sha256"] == receipt["payload_sha256"]
    journal, frames = ledger.read_journal("run-1")
    assert journal["terminal_state"] == "completed"
    assert frames[0][2] == frame_digest
  finally:
    ledger.close()


def test_sqlite_ledger_rejects_stale_writer_and_recovers_crash(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
  try:
    token = ledger.acquire_fence("journal:run-2", "writer-1")
    ledger.register_writer_process(
      token, child.pid, host_boot_id="boot-child-1", audit_identity="audit-2",
    )
    ledger.open_journal(token, "run-2", {"run_id": "run-2", "plan_sha256": "1" * 64}, audit_identity="audit-2")
    ledger.append_journal(token, "run-2", b"step-0", sequence=0, audit_identity="audit-2")
    with pytest.raises(Exception, match="still alive"):
      ledger.confirm_process_terminated(token, audit_identity="audit-2")
    child.terminate()
    child.wait(timeout=10)
    ledger.recover_crashed_journal(
      "run-2", writer_id="writer-2", prior_token=token, audit_identity="audit-2",
      receipt_builder=lambda sequence, digest: _receipt(
        receipt_id="receipt-2", run_id="run-2", attempt_id="attempt-2",
        journal_id="run-2", writer_generation="2", terminal_state="crashed",
        terminal_reason="writer lost", journal_last_sequence=sequence,
        journal_last_record_sha256=digest,
      ),
    )
    with pytest.raises(Exception, match="tombstoned|stale writer"):
      ledger.append_journal(token, "run-2", b"stale", sequence=1, audit_identity="audit-2")
    journal, frames = ledger.read_journal("run-2")
    assert journal["terminal_state"] == "crashed"
    assert [frame[0] for frame in frames] == [0, 1]
    terminal_payload = ledger.db.execute(
      "SELECT payload FROM frames WHERE journal_id=? AND sequence=1", ("run-2",),
    ).fetchone()[0]
    assert json.loads(terminal_payload)["event"] == "crash_reconciled"
  finally:
    if child.poll() is None:
      child.kill()
      child.wait(timeout=10)
    ledger.close()


def test_crash_recovery_is_terminal_only_and_retryable_after_builder_failure(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
  try:
    token = ledger.acquire_fence("journal:run-retry", "writer-1")
    ledger.register_writer_process(token, child.pid, host_boot_id="boot-child", audit_identity="audit-retry")
    ledger.open_journal(token, "run-retry", {"run_id": "run-retry"}, audit_identity="audit-retry")
    ledger.append_journal(token, "run-retry", b"step-0", sequence=0, audit_identity="audit-retry")
    child.terminate()
    child.wait(timeout=10)
    with pytest.raises(RuntimeError, match="receipt builder failed"):
      ledger.recover_crashed_journal(
        "run-retry", writer_id="writer-2", audit_identity="audit-retry", prior_token=token,
        receipt_builder=lambda _sequence, _digest: (_ for _ in ()).throw(RuntimeError("receipt builder failed")),
        )
    marker_row = ledger.db.execute(
      "SELECT payload FROM frames WHERE journal_id=? AND sequence=1", ("run-retry",),
    ).fetchone()
    forged_marker = json.loads(bytes(marker_row[0]).decode("utf-8"))
    forged_marker["prior_writer_generation"] = 999
    ledger.db.execute(
      "UPDATE frames SET payload=? WHERE journal_id=? AND sequence=1",
      (canonical_json_bytes(forged_marker), "run-retry"),
    )
    with pytest.raises(Exception, match="marker does not match"):
      ledger.recover_crashed_journal(
        "run-retry", writer_id="writer-2", audit_identity="audit-retry", prior_token=token,
        receipt_builder=lambda sequence, digest: _receipt(
          receipt_id="receipt-retry-forged", run_id="run-retry", attempt_id="attempt-retry",
          journal_id="run-retry", writer_generation="2", terminal_state="crashed",
          terminal_reason="writer lost", journal_last_sequence=sequence,
          journal_last_record_sha256=digest,
        ),
      )
    ledger.db.execute(
      "UPDATE frames SET payload=? WHERE journal_id=? AND sequence=1",
      (marker_row[0], "run-retry"),
    )
    recovery_token = FenceToken("journal:run-retry", "writer-2", 2)
    with pytest.raises(Exception, match="crash_reconciled|terminal"):
      ledger.append_journal(
        recovery_token, "run-retry", b'{"event":"rogue-nonterminal"}', sequence=2,
        audit_identity="audit-retry", role="crash_reconciler",
      )
    ledger.recover_crashed_journal(
      "run-retry", writer_id="writer-2", audit_identity="audit-retry", prior_token=token,
      receipt_builder=lambda sequence, digest: _receipt(
        receipt_id="receipt-retry", run_id="run-retry", attempt_id="attempt-retry",
        journal_id="run-retry", writer_generation="2", terminal_state="crashed",
        terminal_reason="writer lost", journal_last_sequence=sequence,
        journal_last_record_sha256=digest,
      ),
    )
    assert ledger.read_journal("run-retry")[0]["terminal_state"] == "crashed"
  finally:
    if child.poll() is None:
      child.kill()
      child.wait(timeout=10)
    ledger.close()


@pytest.mark.parametrize("durable_stage", ["terminated", "tombstoned", "refenced"])
def test_crash_recovery_resumes_from_each_durable_stage(
  tmp_path: Path, durable_stage: str,
) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / durable_stage)
  child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
  run_id = f"run-{durable_stage}"
  audit_id = f"audit-{durable_stage}"
  try:
    token = ledger.acquire_fence(f"journal:{run_id}", "writer-1")
    ledger.register_writer_process(
      token, child.pid, host_boot_id="boot-child", audit_identity=audit_id,
    )
    ledger.open_journal(token, run_id, {"run_id": run_id}, audit_identity=audit_id)
    ledger.append_journal(token, run_id, b"step-0", sequence=0, audit_identity=audit_id)
    child.terminate()
    child.wait(timeout=10)

    proof = ledger.confirm_process_terminated(token, audit_identity=audit_id)
    if durable_stage in {"tombstoned", "refenced"}:
      ledger.tombstone_writer(token, proof, audit_identity=audit_id)
    if durable_stage == "refenced":
      recovery_token = ledger.acquire_fence(
        f"journal:{run_id}", "writer-2", expected_generation=1,
        audit_identity=audit_id, role="crash_reconciler",
      )
      with pytest.raises(Exception, match="does not match termination, tombstone, and fence"):
        ledger.append_journal(
          recovery_token, run_id,
          canonical_json_bytes({
            "event": "crash_reconciled", "observed_exit_sha256": "f" * 64,
            "prior_writer_generation": 999, "prior_writer_id": "forged-writer",
            "recovery_writer_generation": recovery_token.generation,
            "recovery_writer_id": recovery_token.writer_id,
          }),
          sequence=1, audit_identity=audit_id, role="crash_reconciler",
        )

    ledger.recover_crashed_journal(
      run_id, writer_id="writer-2", prior_token=token, audit_identity=audit_id,
      receipt_builder=lambda sequence, digest: _receipt(
        receipt_id=f"receipt-{durable_stage}", run_id=run_id,
        attempt_id=f"attempt-{durable_stage}", journal_id=run_id,
        writer_generation="2", terminal_state="crashed", terminal_reason="writer lost",
        journal_last_sequence=sequence, journal_last_record_sha256=digest,
      ),
    )
    journal, frames = ledger.read_journal(run_id)
    assert journal["terminal_state"] == "crashed"
    assert [frame[0] for frame in frames] == [0, 1]
  finally:
    if child.poll() is None:
      child.kill()
      child.wait(timeout=10)
    ledger.close()


def test_open_journal_always_binds_an_os_process(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  try:
    token = ledger.acquire_fence("journal:auto-process", "writer")
    ledger.open_journal(token, "auto-process", {"run_id": "auto-process"}, audit_identity="audit-auto")
    assert ledger.db.execute(
      "SELECT process_id FROM writer_processes WHERE stream_id=? AND generation=? AND writer_id=?",
      (token.stream_id, token.generation, token.writer_id),
    ).fetchone()[0] == os.getpid()
  finally:
    ledger.close()


def test_sqlite_backup_is_readable(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  token = ledger.acquire_fence("journal:backup", "writer")
  ledger.open_journal(token, "backup", {"run_id": "backup", "plan_sha256": "1" * 64}, audit_identity="audit-backup")
  frame_digest = ledger.append_journal(token, "backup", b"durable", sequence=0, audit_identity="audit-backup")
  backup_receipt = _bind_output_blob(
    ledger,
    _receipt(
      receipt_id="receipt-backup", run_id="backup", attempt_id="attempt-backup",
      journal_id="backup", journal_last_record_sha256=frame_digest,
    ),
    audit_identity="audit-backup",
  )
  ledger.finalize_journal(
    token, "backup",
    receipt=backup_receipt,
    terminal_state="completed", audit_identity="audit-backup",
    actual_bindings=_observed_bindings_for(backup_receipt),
  )
  checkpoint_token = ledger.acquire_fence(
    "checkpoint:checkpoint-backup", "writer", audit_identity="audit-backup",
  )
  checkpoint = build_state_checkpoint_shell({
    "authority_kind": "state_checkpoint",
    "schema_version": "echelon_forge.state_checkpoint.v1",
    "contract_version": "echelon_forge.state_checkpoint_contract.v1",
    "writer_role": "runtime_host",
    "writer_generation": "1",
    "checkpoint_id": "checkpoint-backup",
    "plan_sha256": "1" * 64,
    "release_id": "release-1",
    "decision_id": "decision-1",
    "run_id": "backup",
    "host_boot_id": "boot-1",
    "incarnation_epoch": "1",
    "transfer_fence_sequence": "1",
    "world_fragments": [{
      "world_id": "world-1", "episode_ids": ["episode-1"],
      "fragment_sequence": "0", "state_sha256": "2" * 64,
    }],
    "aggregate_state_sha256": "3" * 64,
    "state_schema_generation": "1",
    "target_reader_generation_min": "1",
    "target_reader_generation_max": "1",
  })
  ledger.persist_checkpoint(
    checkpoint_token, canonical_json_bytes(checkpoint), expected_slot_version=0,
    audit_identity="audit-backup",
  )
  backup = tmp_path / "backup.sqlite3"
  ledger.backup_to(backup)
  ledger.close()
  restored = SQLiteArtifactLedger.restore_from(backup, tmp_path / "restored")
  try:
    assert restored.read_journal("backup")[1][0][0] == 0
    assert restored.read_receipt("receipt-backup")["payload"]["run_id"] == "backup"
    assert restored.read_checkpoint("checkpoint-backup")["payload"]["run_id"] == "backup"
    restored.db.execute("UPDATE frames SET prior_digest=? WHERE journal_id=? AND sequence=0", ("f" * 64, "backup"))
    with pytest.raises(Exception, match="journal frame integrity"):
      restored.read_journal("backup")
  finally:
    restored.close()
  corrupted = sqlite3.connect(backup)
  try:
    corrupted.execute(
      "UPDATE frames SET frame_digest=? WHERE journal_id=? AND sequence=0",
      ("f" * 64, "backup"),
    )
    corrupted.commit()
  finally:
    corrupted.close()
  with pytest.raises(Exception, match="journal frame integrity"):
    SQLiteArtifactLedger.restore_from(backup, tmp_path / "corrupt-restored")


def test_sqlite_detects_torn_or_missing_frame_material(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  try:
    token = ledger.acquire_fence("journal:torn", "writer")
    ledger.open_journal(token, "torn", {"run_id": "torn"}, audit_identity="audit-torn")
    ledger.append_journal(token, "torn", b"durable-record", sequence=0, audit_identity="audit-torn")
    original = ledger.db.execute(
      "SELECT payload,payload_digest,prior_digest,frame_digest,frame_length,frame_checksum "
      "FROM frames WHERE journal_id='torn' AND sequence=0",
    ).fetchone()
    mutations = (
      ("payload", b"durable-recor"),
      ("payload_digest", "f" * 64),
      ("prior_digest", "f" * 64),
      ("frame_digest", "f" * 64),
      ("frame_length", int(original[4]) - 1),
      ("frame_checksum", int(original[5]) ^ 1),
    )
    columns = ("payload", "payload_digest", "prior_digest", "frame_digest", "frame_length", "frame_checksum")
    for field, corrupt in mutations:
      ledger.db.execute(f"UPDATE frames SET {field}=? WHERE journal_id='torn' AND sequence=0", (corrupt,))
      with pytest.raises(Exception, match="journal frame integrity"):
        ledger.read_journal("torn")
      ledger.db.execute(
        f"UPDATE frames SET {field}=? WHERE journal_id='torn' AND sequence=0",
        (original[columns.index(field)],),
      )
    ledger.db.execute("DELETE FROM frames WHERE journal_id='torn' AND sequence=0")
    with pytest.raises(Exception, match="last-record digest"):
      ledger.read_journal("torn")
  finally:
    ledger.close()


def test_sqlite_restore_rejects_an_incomplete_database(tmp_path: Path) -> None:
  source = tmp_path / "not-a-ledger.sqlite3"
  db = sqlite3.connect(source)
  try:
    db.executescript("""
      CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
      INSERT INTO metadata VALUES('schema_version', 'echelon_forge.sqlite_artifact_ledger.v1');
      CREATE TABLE blobs(digest TEXT);
      CREATE TABLE fences(stream_id TEXT);
      CREATE TABLE journals(journal_id TEXT);
      CREATE TABLE frames(journal_id TEXT);
      CREATE TABLE receipts(receipt_id TEXT);
      CREATE TABLE audit(sequence INTEGER);
    """)
    db.commit()
  finally:
    db.close()
  with pytest.raises(Exception, match="not a complete SQLite ArtifactLedger"):
    SQLiteArtifactLedger.restore_from(source, tmp_path / "restored")


def test_sqlite_refuses_to_silently_version_an_existing_database(tmp_path: Path) -> None:
  root = tmp_path / "ledger"
  ledger = SQLiteArtifactLedger(root)
  ledger.close()
  db = sqlite3.connect(root / "artifact-ledger.sqlite3")
  try:
    db.execute("DROP TABLE metadata")
    db.commit()
  finally:
    db.close()
  with pytest.raises(Exception, match="not a complete SQLite ArtifactLedger"):
    SQLiteArtifactLedger(root)


def test_sqlite_rejects_header_identity_mismatch(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  try:
    token = ledger.acquire_fence("journal:run-1", "writer-1")
    with pytest.raises(Exception, match="header run identity"):
      ledger.open_journal(token, "run-1", {"run_id": "other", "plan_sha256": "1" * 64}, audit_identity="audit-1")
  finally:
    ledger.close()


def test_sqlite_checkpoint_is_fenced_immutable_and_role_scoped(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  try:
    token = ledger.acquire_fence("checkpoint:checkpoint-1", "writer-1", audit_identity="audit-checkpoint")
    envelope = build_state_checkpoint_shell({
      "authority_kind": "state_checkpoint",
      "schema_version": "echelon_forge.state_checkpoint.v1",
      "contract_version": "echelon_forge.state_checkpoint_contract.v1",
      "writer_role": "runtime_host",
      "writer_generation": "1",
      "checkpoint_id": "checkpoint-1",
      "plan_sha256": "1" * 64,
      "release_id": "release-1",
      "decision_id": "decision-1",
      "run_id": "run-1",
      "host_boot_id": "boot-1",
      "incarnation_epoch": "1",
      "transfer_fence_sequence": "1",
      "world_fragments": [{"world_id": "world-1", "episode_ids": ["episode-1"], "fragment_sequence": "0", "state_sha256": "2" * 64}],
      "aggregate_state_sha256": "3" * 64,
      "state_schema_generation": "1",
      "target_reader_generation_min": "1",
      "target_reader_generation_max": "1",
    })
    payload = canonical_json_bytes(envelope)
    digest, version = ledger.persist_checkpoint(token, payload, expected_slot_version=0, audit_identity="audit-checkpoint")
    assert version == 1 and digest
    assert ledger.read_checkpoint("checkpoint-1")["payload"]["checkpoint_id"] == "checkpoint-1"
    with pytest.raises(Exception, match="role"):
      ledger.persist_checkpoint(token, payload, expected_slot_version=0, audit_identity="audit-checkpoint", role="runtime_evidence")
    with pytest.raises(Exception, match="immutable|absent"):
      ledger.persist_checkpoint(token, payload, expected_slot_version=1, audit_identity="audit-checkpoint")
  finally:
    ledger.close()


def test_receipt_checkpoint_refs_bind_persisted_bytes_and_validation(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  try:
    checkpoint_state = b"recoverable-checkpoint-state"
    checkpoint_state_sha256 = hashlib.sha256(checkpoint_state).hexdigest()
    checkpoint_token = ledger.acquire_fence("checkpoint:checkpoint-bound", "writer", audit_identity="audit-bound")
    checkpoint = build_state_checkpoint_shell({
      "authority_kind": "state_checkpoint",
      "schema_version": "echelon_forge.state_checkpoint.v1",
      "contract_version": "echelon_forge.state_checkpoint_contract.v1",
      "writer_role": "runtime_host",
      "writer_generation": "1",
      "checkpoint_id": "checkpoint-bound",
      "plan_sha256": "1" * 64,
      "release_id": "release-1",
      "decision_id": "decision-1",
      "run_id": "source-run",
      "host_boot_id": "source-boot",
      "incarnation_epoch": "9",
      "transfer_fence_sequence": "1",
      "world_fragments": [{"world_id": "world-1", "episode_ids": ["episode-1"], "fragment_sequence": "0", "state_sha256": "2" * 64}],
      "aggregate_state_sha256": checkpoint_state_sha256,
      "state_schema_generation": "1",
      "target_reader_generation_min": "1",
      "target_reader_generation_max": "2",
    })
    aggregate_replay_sha256 = hashlib.sha256(canonical_json_bytes({
      "state_schema_generation": checkpoint["payload"]["state_schema_generation"],
      "transfer_fence_sequence": checkpoint["payload"]["transfer_fence_sequence"],
      "world_fragments": checkpoint["payload"]["world_fragments"],
    })).hexdigest()
    checkpoint_bytes = canonical_json_bytes(checkpoint)
    checkpoint_digest, _ = ledger.persist_checkpoint(
      checkpoint_token, checkpoint_bytes, expected_slot_version=0, audit_identity="audit-bound",
    )
    validation_bytes = canonical_json_bytes({
      "accepted": True, "checkpoint_id": "checkpoint-bound",
      "state_sha256": checkpoint_state_sha256,
      "state_payload_hex": checkpoint_state.hex(),
      "aggregate_replay_sha256": aggregate_replay_sha256,
      "validator_id": "native-runtime-state",
    })
    validation_digest = ledger.put_blob(
      validation_bytes, media_type=CHECKPOINT_VALIDATION_MEDIA_TYPE,
      retention_class="rollback-window", audit_identity="audit-bound",
      expected_sha256=hashlib.sha256(validation_bytes).hexdigest(),
    )
    run_token = ledger.acquire_fence("journal:run-bound", "writer", audit_identity="audit-bound")
    ledger.open_journal(run_token, "run-bound", {"run_id": "run-bound"}, audit_identity="audit-bound")
    frame_digest = ledger.append_journal(run_token, "run-bound", b"step-0", sequence=0, audit_identity="audit-bound")
    receipt = _bind_output_blob(
      ledger,
      _receipt(
        receipt_id="receipt-bound", run_id="run-bound", attempt_id="attempt-bound", journal_id="run-bound",
        journal_last_record_sha256=frame_digest,
        checkpoints={
          "source_refs": [{
            "checkpoint_id": "checkpoint-bound", "checkpoint_sha256": checkpoint_digest,
            "validation_sha256": validation_digest, "state_schema_generation": "1",
            "retrieval_location": "ledger://checkpoint-checkpoint-bound",
          }],
          "created_refs": [],
        },
      ),
      audit_identity="audit-bound",
    )
    rejected_validation = canonical_json_bytes({
      "accepted": False, "checkpoint_id": "checkpoint-bound",
      "state_sha256": checkpoint_state_sha256,
      "state_payload_hex": checkpoint_state.hex(),
      "aggregate_replay_sha256": aggregate_replay_sha256,
      "validator_id": "native-runtime-state",
    })
    rejected_validation_digest = ledger.put_blob(
      rejected_validation, media_type=CHECKPOINT_VALIDATION_MEDIA_TYPE,
      retention_class="rollback-window", audit_identity="audit-bound",
      expected_sha256=hashlib.sha256(rejected_validation).hexdigest(),
    )
    rejected_receipt = _bind_output_blob(
      ledger,
      _receipt(
        receipt_id="receipt-bound-rejected", run_id="run-bound",
        attempt_id="attempt-bound-rejected", journal_id="run-bound",
        journal_last_record_sha256=frame_digest,
        checkpoints={
          "source_refs": [{
            "checkpoint_id": "checkpoint-bound", "checkpoint_sha256": checkpoint_digest,
            "validation_sha256": rejected_validation_digest, "state_schema_generation": "1",
            "retrieval_location": "ledger://checkpoint-checkpoint-bound",
          }],
          "created_refs": [],
        },
      ),
      audit_identity="audit-bound",
    )
    with pytest.raises(Exception, match="not accepted or state-bound"):
      ledger.finalize_journal(
        run_token, "run-bound", receipt=rejected_receipt, terminal_state="completed",
        audit_identity="audit-bound", actual_bindings=_observed_bindings_for(rejected_receipt),
      )
    incompatible_checkpoint = build_state_checkpoint_shell({
      **checkpoint["payload"],
      "checkpoint_id": "checkpoint-incompatible",
      "target_reader_generation_min": "99",
      "target_reader_generation_max": "99",
    })
    incompatible_token = ledger.acquire_fence(
      "checkpoint:checkpoint-incompatible", "writer", audit_identity="audit-bound",
    )
    incompatible_bytes = canonical_json_bytes(incompatible_checkpoint)
    incompatible_digest, _ = ledger.persist_checkpoint(
      incompatible_token, incompatible_bytes, expected_slot_version=0,
      audit_identity="audit-bound",
    )
    incompatible_validation = canonical_json_bytes({
      "accepted": True, "checkpoint_id": "checkpoint-incompatible",
      "state_sha256": checkpoint_state_sha256,
      "state_payload_hex": checkpoint_state.hex(),
      "aggregate_replay_sha256": aggregate_replay_sha256,
      "validator_id": "native-runtime-state",
    })
    incompatible_validation_digest = ledger.put_blob(
      incompatible_validation, media_type=CHECKPOINT_VALIDATION_MEDIA_TYPE,
      retention_class="rollback-window", audit_identity="audit-bound",
      expected_sha256=hashlib.sha256(incompatible_validation).hexdigest(),
    )
    incompatible_receipt = _bind_output_blob(
      ledger,
      _receipt(
        receipt_id="receipt-bound-incompatible", run_id="run-bound",
        attempt_id="attempt-bound-incompatible", journal_id="run-bound",
        reader_generation_min="1", reader_generation_max="2",
        journal_last_record_sha256=frame_digest,
        checkpoints={
          "source_refs": [{
            "checkpoint_id": "checkpoint-incompatible",
            "checkpoint_sha256": incompatible_digest,
            "validation_sha256": incompatible_validation_digest,
            "state_schema_generation": "1",
            "retrieval_location": "ledger://checkpoint-checkpoint-incompatible",
          }],
          "created_refs": [],
        },
      ),
      audit_identity="audit-bound",
    )
    with pytest.raises(Exception, match="target reader generation is incompatible"):
      ledger.finalize_journal(
        run_token, "run-bound", receipt=incompatible_receipt,
        terminal_state="completed", audit_identity="audit-bound",
        actual_bindings=_observed_bindings_for(incompatible_receipt),
      )
    ledger.finalize_journal(run_token, "run-bound", receipt=receipt, terminal_state="completed", audit_identity="audit-bound", actual_bindings=_observed_bindings_for(receipt))
    assert ledger.read_receipt("receipt-bound")["payload"]["checkpoints"]["source_refs"][0]["checkpoint_sha256"] == checkpoint_digest
  finally:
    ledger.close()


def test_actual_execution_provenance_is_measured_and_bound_at_finalize(tmp_path: Path) -> None:
  executable = tmp_path / "ef-test.exe"
  package = tmp_path / "package.whl"
  module = tmp_path / "ef-core.dll"
  dependency = tmp_path / "nlohmann-json.dll"
  input_artifact = tmp_path / "scenario.json"
  for path, payload in (
    (executable, b"executable-v1"), (package, b"package-v1"), (module, b"module-v1"),
    (dependency, b"dependency-v1"), (input_artifact, b"scenario-v1"),
  ):
    path.write_bytes(payload)
  observed = collect_actual_bindings(
    executable_path=executable, executable_identity="ef_test", executable_version="1.0.0",
    package_path=package, package_identity="echelon-forge-wheel", package_version="1.0.0",
    wheel_path=package, native_module_paths={"ef_core": module},
    runtime_dependency_paths={"nlohmann_json": dependency}, input_artifact_paths={"scenario": input_artifact},
    gpu="none", driver="none",
  )
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  try:
    token = ledger.acquire_fence("journal:run-provenance", "writer")
    ledger.open_journal(token, "run-provenance", {"run_id": "run-provenance"}, audit_identity="audit-provenance")
    frame_digest = ledger.append_journal(token, "run-provenance", b"step-0", sequence=0, audit_identity="audit-provenance")
    receipt = _receipt(
      receipt_id="receipt-provenance", run_id="run-provenance", attempt_id="attempt-provenance",
      journal_id="run-provenance", journal_last_record_sha256=frame_digest,
      executable=observed["executable"], package=observed["package"],
      platform=observed["platform"], inputs={**_receipt()["payload"]["inputs"], "artifacts": observed["inputs"]["artifacts"]},
    )
    receipt = _bind_output_blob(ledger, receipt, audit_identity="audit-provenance")
    executable.write_bytes(b"executable-tampered")
    bad_observed = collect_actual_bindings(
      executable_path=executable, executable_identity="ef_test", executable_version="1.0.0",
      package_path=package, package_identity="echelon-forge-wheel", package_version="1.0.0",
      wheel_path=package, native_module_paths={"ef_core": module},
      runtime_dependency_paths={"nlohmann_json": dependency},
      input_artifact_paths={"scenario": input_artifact}, gpu="none", driver="none",
    )
    with pytest.raises(Exception, match="provenance mismatch"):
      ledger.finalize_journal(
        token, "run-provenance", receipt=receipt, terminal_state="completed",
        audit_identity="audit-provenance", actual_bindings=bad_observed,
      )
    executable.write_bytes(b"executable-v1")
    observed = collect_actual_bindings(
      executable_path=executable, executable_identity="ef_test", executable_version="1.0.0",
      package_path=package, package_identity="echelon-forge-wheel", package_version="1.0.0",
      wheel_path=package, native_module_paths={"ef_core": module},
      runtime_dependency_paths={"nlohmann_json": dependency},
      input_artifact_paths={"scenario": input_artifact}, gpu="none", driver="none",
    )
    ledger.finalize_journal(
      token, "run-provenance", receipt=receipt, terminal_state="completed",
      audit_identity="audit-provenance", actual_bindings=observed,
    )
  finally:
    ledger.close()


def test_completed_receipt_rejects_an_ephemeral_output_location(tmp_path: Path) -> None:
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  try:
    token = ledger.acquire_fence("journal:ephemeral-output", "writer")
    ledger.open_journal(
      token, "ephemeral-output", {"run_id": "ephemeral-output"}, audit_identity="audit-output",
    )
    frame_digest = ledger.append_journal(
      token, "ephemeral-output", b"step-0", sequence=0, audit_identity="audit-output",
    )
    receipt = _receipt(
      receipt_id="receipt-ephemeral", run_id="ephemeral-output", attempt_id="attempt-ephemeral",
      journal_id="ephemeral-output", journal_last_record_sha256=frame_digest,
    )
    ephemeral_payload = deepcopy(receipt["payload"])
    ephemeral_payload["results"]["output_artifacts"][0]["retrieval_location"] = "workspace://trace"
    receipt = build_run_receipt(**ephemeral_payload)
    with pytest.raises(Exception, match="not content-addressed"):
      ledger.finalize_journal(
        token, "ephemeral-output", receipt=receipt, terminal_state="completed",
        audit_identity="audit-output", actual_bindings=_observed_bindings_for(receipt),
      )
  finally:
    ledger.close()
