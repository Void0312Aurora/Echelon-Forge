"""Generate the P5-B canonical RunReceipt cross-language vector."""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.maintenance.runtime_run_receipt import build_run_receipt, canonical_json
from tools.maintenance.runtime_execution_provenance import collect_actual_bindings


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/architecture/composition/fixtures/run_receipt.v1.json"


def build_sample_run_receipt(
  *,
  terminal_state: str = "completed",
  journal_last_sequence: int = 0,
  journal_last_record_sha256: str | None = None,
  **overrides: Any,
) -> dict[str, Any]:
  value: dict[str, Any] = {
    "receipt_id": "receipt-1", "run_id": "run-1", "attempt_id": "attempt-1",
    "host_boot_id": "boot-1", "incarnation_epoch": "1",
    "writer_generation": "1", "reader_generation_min": "1", "reader_generation_max": "1",
    "plan_binding": {
      "plan_id": "plan-1", "plan_sha256": "1" * 64, "request_sha256": "2" * 64,
      "plan_generation": "1", "plan_canonical_sha256": "1" * 64,
      "plan_location": "ledger://plan-1", "request_canonical_sha256": "2" * 64,
      "request_location": "ledger://request-1", "compiler_identity": "PlanCompiler",
      "compiler_version": "1.0.0",
    },
    "release_binding": {
      "release_id": "release-1", "release_manifest_sha256": "3" * 64,
      "rollout_decision_id": "decision-1", "rollout_decision_sha256": "4" * 64,
      "provenance_sha256": "5" * 64, "sbom_sha256": "6" * 64,
      "attestation_sha256": "7" * 64,
    },
    "executable": {
      "identity": "ef_test", "version": "1.0.0", "digest": "8" * 64,
      "native_module_digests": {"ef_core": "9" * 64}, "plugin_digests": {},
    },
    "package": {
      "identity": "echelon-forge-wheel", "version": "1.0.0", "digest": "a" * 64,
      "wheel_digest": "b" * 64, "dependency_graph_sha256": "c" * 64,
    },
    "build": {
      "source_revision": "revision-1", "dirty": False, "build_mode": "Release",
      "linker": "link.exe", "toolchain": "msvc-v143", "cxx_abi": "msvc-14.44",
      "python_abi": "cp312-win_amd64", "node_abi": "node-127",
    },
    "platform": {
      "os": "windows", "architecture": "amd64", "compiler": "msvc",
      "standard_library": "msvc", "cpu": "x64", "gpu": "none", "driver": "none",
      "runtime_dependency_digests": {"nlohmann_json": "d" * 64},
    },
    "inputs": {
      "scenario_id": "scenario-1", "content_id": "content-1", "database_id": "database-1",
      "configuration_id": "config-1", "seed_policy": "fixed", "seed_value": "seed-1",
      "seed_stream_id": "seed-stream-1", "artifacts": {"plan": "1" * 64, "request": "2" * 64},
    },
    "backend": {
      "profile_id": "cpu_exact.reference", "backend_provider_id": "builtin.backend.flecs_cpu",
      "backend_implementation_version": "1.0.0", "determinism_profile": "exact",
      "system_graph_sha256": "e" * 64, "stage_contract_sha256": "f" * 64,
    },
    "execution_scope": {
      "world_ids": ["world-1"], "entity_ids": ["entity-1"],
      "episode_ids": ["episode-1"], "request_ids": ["request-1"],
      "epochs": {"world": "1", "entity": "1", "episode": "1", "request": "1"},
    },
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
    "results": {
      "result_digest": "1" * 64,
      "output_artifacts": [{
        "name": "trace", "digest": "2" * 64, "media_type": "application/octet-stream",
        "size": 7, "availability": "durable", "retention_class": "run-retained",
        "retrieval_location": "ledger://blob-" + "2" * 64,
      }],
      "native_validation": {"accepted": True, "validator_id": "native-run-validator", "evidence_sha256": "3" * 64},
    },
    "checkpoints": {"source_refs": [], "created_refs": []},
    "qualification_refs": [], "side_effect_receipts": [],
    "completion": {"created_at": "2026-09-19T00:00:00Z", "finalized_at": "2026-09-19T00:00:01Z", "durable_ack": True},
    "terminal_state": terminal_state,
    "terminal_reason": "completed" if terminal_state == "completed" else "test failure",
    "journal_id": "run-1", "journal_last_sequence": journal_last_sequence,
    "journal_last_record_sha256": journal_last_record_sha256 or "a" * 64,
    "retention_class": "run-retained",
    "authenticity": {"attestation_sha256": "5" * 64, "signatures": []},
  }
  fixtures = ROOT / "tests/architecture/composition/fixtures"
  release_package = fixtures / "candidate_release_package.v1.bin"
  measured = collect_actual_bindings(
    executable_path=fixtures / "authority_cross_language_vector.v1.json",
    executable_identity="ef_test", executable_version="1.0.0",
    package_path=release_package,
    package_identity="cmo", package_version="1.0.0",
    wheel_path=release_package,
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
  value["executable"] = measured["executable"]
  value["package"] = measured["package"]
  # This is a contract example, not a receipt attesting to the generator host.
  # Preserve its declared Windows/MSVC row while measuring fixture byte inputs.
  value["platform"] = {
    "os": "windows", "architecture": "amd64", "compiler": "msvc",
    "standard_library": "msvc", "cpu": "x64", "gpu": "none", "driver": "none",
    "runtime_dependency_digests": measured["platform"]["runtime_dependency_digests"],
  }
  value["inputs"] = {
    **value["inputs"], "artifacts": measured["inputs"]["artifacts"],
  }
  release_vector = json.loads(
    (fixtures / "authority_cross_language_vector.v1.json").read_text(encoding="utf-8")
  )
  rollout_vector = json.loads(
    (fixtures / "authority_rollout_decision.v1.json").read_text(encoding="utf-8")
  )
  release = json.loads(release_vector["envelope_json"])
  rollout = json.loads(rollout_vector["envelope_json"])
  value["reader_generation_min"] = release["payload"]["reader_generation_min"]
  value["reader_generation_max"] = release["payload"]["reader_generation_max"]
  value["plan_binding"] = {
    **value["plan_binding"],
    "plan_sha256": rollout["payload"]["plan_sha256"],
    "plan_canonical_sha256": rollout["payload"]["plan_sha256"],
  }
  value["release_binding"] = {
    "release_id": release["payload"]["release_id"],
    "release_manifest_sha256": release["payload_sha256"],
    "rollout_decision_id": rollout["payload"]["decision_id"],
    "rollout_decision_sha256": rollout["payload_sha256"],
    "provenance_sha256": release["payload"]["provenance_sha256"],
    "sbom_sha256": release["payload"]["sbom_sha256"],
    "attestation_sha256": value["release_binding"]["attestation_sha256"],
  }
  value["build"] = {
    **value["build"],
    "source_revision": release["payload"]["source_revision"],
    "toolchain": release["payload"]["toolchain_identity"],
  }
  value.update(deepcopy(overrides))
  admission_bindings = {
    key: value[key]
    for key in (
      "receipt_id", "attempt_id", "plan_binding", "release_binding", "executable", "package",
      "build", "platform", "inputs", "backend", "reader_generation_min", "reader_generation_max",
    )
  }
  value["admission_binding_sha256"] = hashlib.sha256(
    canonical_json(admission_bindings).encode("utf-8"),
  ).hexdigest()
  return build_run_receipt(**value)


def build_vector() -> dict[str, Any]:
  receipt = build_sample_run_receipt()
  return {
    "vector_kind": "run_receipt_v1",
    "canonical_envelope_json": canonical_json(receipt),
    "canonical_payload_bytes": canonical_json(receipt["payload"]),
    "payload_sha256": receipt["payload_sha256"],
  }


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--write", action="store_true")
  args = parser.parse_args()
  rendered = json.dumps(build_vector(), ensure_ascii=False, indent=2) + "\n"
  if args.write:
    FIXTURE.write_text(rendered, encoding="utf-8", newline="\n")
    return 0
  if not FIXTURE.is_file() or FIXTURE.read_text(encoding="utf-8") != rendered:
    raise SystemExit("stale run_receipt.v1.json fixture")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
