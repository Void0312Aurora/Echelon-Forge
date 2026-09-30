"""Versioned native-owned RunReceipt contract for the P5-B durable ledger."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from tools.maintenance.runtime_authority_contracts import (
  CANONICALIZATION,
  ENVELOPE_VERSION,
  authority_digest_sha256,
  canonical_json_bytes,
)


SCHEMA_VERSION = "echelon_forge.run_receipt.v1"
CONTRACT_VERSION = "echelon_forge.run_receipt_contract.v1"
AUTHORITY_KIND = "run_receipt"
WRITER_ROLE = "runtime_host"
DOMAIN = "runtime.run-receipt"
MEDIA_TYPE = "application/vnd.echelon-forge.run-receipt.v1+json"
HASH_ALGORITHM = "sha256"
MAX_SAFE_INTEGER = 9_007_199_254_740_991
TERMINAL_STATES = frozenset({"completed", "failed", "cancelled", "rejected", "crashed", "incomplete"})
RETENTION_CLASSES = frozenset({"active-release", "rollback-window", "run-retained", "evidence-short"})
CHECKPOINT_REF_FIELDS = frozenset({
  "checkpoint_id", "checkpoint_sha256", "validation_sha256", "state_schema_generation",
  "retrieval_location",
})
LIFECYCLE_EVENTS = (
  "journal_admitted", "construction", "validation", "publication", "episode",
  "drain", "rollback", "shutdown", "reclamation", "terminal",
)
COMPLETED_LIFECYCLE = (
  "journal_admitted", "construction", "validation", "publication", "episode",
  "drain", "shutdown", "reclamation", "terminal",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "src/runtime/contracts/ledger/run_receipt.v1.schema.json"


class RunReceiptError(ValueError):
  """Fail-closed receipt admission error."""


PAYLOAD_REQUIRED_FIELDS = frozenset({
  "authority_kind", "schema_version", "contract_version", "writer_role",
  "receipt_id", "run_id", "attempt_id", "host_boot_id", "incarnation_epoch",
  "writer_generation", "reader_generation_min", "reader_generation_max",
  "admission_binding_sha256",
  "plan_binding", "release_binding", "executable", "package", "build", "platform",
  "inputs", "backend", "execution_scope", "lifecycle", "results", "checkpoints",
  "qualification_refs", "side_effect_receipts", "completion", "terminal_state",
  "terminal_reason", "journal_id", "journal_last_sequence",
  "journal_last_record_sha256", "retention_class", "hash_algorithm", "authenticity",
})
REQUIRED_FIELDS = frozenset({
  "canonicalization", "domain", "envelope_version", "media_type", "payload",
  "payload_sha256", "signatures",
})


def canonical_json(value: Any) -> str:
  return canonical_json_bytes(value).decode("utf-8")


def _require_exact(value: Any, fields: set[str], path: str) -> dict[str, Any]:
  if not isinstance(value, dict) or set(value) != fields:
    raise RunReceiptError(f"{path} fields are not exact")
  return value


def _require_id(value: Any, path: str) -> None:
  if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
    raise RunReceiptError(f"{path} must be an admitted identifier")


def _require_sha(value: Any, path: str, *, allow_empty: bool = False) -> None:
  if allow_empty and value == "":
    return
  if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
    raise RunReceiptError(f"{path} must be a lowercase SHA-256 digest")


def _require_text(value: Any, path: str) -> None:
  if not isinstance(value, str) or not value:
    raise RunReceiptError(f"{path} must be non-empty text")


def _require_generation(value: Any, path: str) -> None:
  if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)", value):
    raise RunReceiptError(f"{path} must be a decimal generation string")


def _require_safe_integer(value: Any, path: str) -> None:
  if (
    not isinstance(value, int)
    or isinstance(value, bool)
    or value < 0
    or value > MAX_SAFE_INTEGER
  ):
    raise RunReceiptError(f"{path} must be a non-negative interoperable integer")


def _require_digest_map(value: Any, path: str, *, allow_empty: bool = False) -> None:
  if not isinstance(value, dict) or (not value and not allow_empty):
    raise RunReceiptError(f"{path} must be a digest map")
  for key, digest in value.items():
    _require_id(key, f"{path} key")
    _require_sha(digest, f"{path}.{key}")


def _require_sorted_ids(value: Any, path: str, *, allow_empty: bool = False) -> None:
  if not isinstance(value, list) or (not value and not allow_empty):
    raise RunReceiptError(f"{path} must be an ordered identity list")
  for index, item in enumerate(value):
    _require_id(item, f"{path}[{index}]")
  if value != sorted(value) or len(set(value)) != len(value):
    raise RunReceiptError(f"{path} must be sorted and identity-unique")


def validate_run_receipt_payload(value: Mapping[str, Any]) -> dict[str, Any]:
  if not isinstance(value, Mapping):
    raise RunReceiptError("receipt payload must be an object")
  payload = deepcopy(dict(value))
  if set(payload) != PAYLOAD_REQUIRED_FIELDS:
    raise RunReceiptError("receipt payload fields are not exact")
  if (
    payload["authority_kind"] != AUTHORITY_KIND
    or payload["schema_version"] != SCHEMA_VERSION
    or payload["contract_version"] != CONTRACT_VERSION
    or payload["writer_role"] != WRITER_ROLE
    or payload["hash_algorithm"] != HASH_ALGORITHM
  ):
    raise RunReceiptError("receipt owner, schema, contract, or hash algorithm mismatch")
  for field in ("receipt_id", "run_id", "attempt_id", "host_boot_id", "journal_id"):
    _require_id(payload[field], field)
  for field in ("incarnation_epoch", "writer_generation", "reader_generation_min", "reader_generation_max"):
    _require_generation(payload[field], field)
  _require_sha(payload["admission_binding_sha256"], "admission_binding_sha256")
  if int(payload["reader_generation_min"]) > int(payload["reader_generation_max"]):
    raise RunReceiptError("receipt reader generation window is inverted")

  plan = _require_exact(payload["plan_binding"], {
    "plan_id", "plan_sha256", "request_sha256", "plan_generation",
    "plan_canonical_sha256", "plan_location", "request_canonical_sha256",
    "request_location", "compiler_identity", "compiler_version",
  }, "plan_binding")
  _require_id(plan["plan_id"], "plan_binding.plan_id")
  for field in ("plan_sha256", "request_sha256", "plan_canonical_sha256", "request_canonical_sha256"):
    _require_sha(plan[field], f"plan_binding.{field}")
  _require_generation(plan["plan_generation"], "plan_binding.plan_generation")
  for field in ("plan_location", "request_location", "compiler_identity", "compiler_version"):
    _require_text(plan[field], f"plan_binding.{field}")

  release = _require_exact(payload["release_binding"], {
    "release_id", "release_manifest_sha256", "rollout_decision_id",
    "rollout_decision_sha256", "provenance_sha256", "sbom_sha256", "attestation_sha256",
  }, "release_binding")
  for field in ("release_id", "rollout_decision_id"):
    _require_id(release[field], f"release_binding.{field}")
  for field in ("release_manifest_sha256", "rollout_decision_sha256", "provenance_sha256", "sbom_sha256", "attestation_sha256"):
    _require_sha(release[field], f"release_binding.{field}")

  executable = _require_exact(payload["executable"], {
    "identity", "version", "digest", "native_module_digests", "plugin_digests",
  }, "executable")
  _require_id(executable["identity"], "executable.identity")
  _require_text(executable["version"], "executable.version")
  _require_sha(executable["digest"], "executable.digest")
  _require_digest_map(executable["native_module_digests"], "executable.native_module_digests")
  _require_digest_map(executable["plugin_digests"], "executable.plugin_digests", allow_empty=True)

  package = _require_exact(payload["package"], {
    "identity", "version", "digest", "wheel_digest", "dependency_graph_sha256",
  }, "package")
  _require_id(package["identity"], "package.identity")
  _require_text(package["version"], "package.version")
  for field in ("digest", "wheel_digest", "dependency_graph_sha256"):
    _require_sha(package[field], f"package.{field}")

  build = _require_exact(payload["build"], {
    "source_revision", "dirty", "build_mode", "linker", "toolchain", "cxx_abi", "python_abi", "node_abi",
  }, "build")
  for field in ("source_revision", "build_mode", "linker", "toolchain", "cxx_abi", "python_abi", "node_abi"):
    _require_text(build[field], f"build.{field}")
  if not isinstance(build["dirty"], bool):
    raise RunReceiptError("build.dirty must be boolean")

  platform = _require_exact(payload["platform"], {
    "os", "architecture", "compiler", "standard_library", "cpu", "gpu", "driver", "runtime_dependency_digests",
  }, "platform")
  for field in ("os", "architecture", "compiler", "standard_library", "cpu", "gpu", "driver"):
    _require_text(platform[field], f"platform.{field}")
  _require_digest_map(platform["runtime_dependency_digests"], "platform.runtime_dependency_digests")

  inputs = _require_exact(payload["inputs"], {
    "scenario_id", "content_id", "database_id", "configuration_id", "seed_policy",
    "seed_value", "seed_stream_id", "artifacts",
  }, "inputs")
  for field in ("scenario_id", "content_id", "database_id", "configuration_id", "seed_policy", "seed_value", "seed_stream_id"):
    _require_text(inputs[field], f"inputs.{field}")
  _require_digest_map(inputs["artifacts"], "inputs.artifacts")

  backend = _require_exact(payload["backend"], {
    "profile_id", "backend_provider_id", "backend_implementation_version", "determinism_profile",
    "system_graph_sha256", "stage_contract_sha256",
  }, "backend")
  for field in ("profile_id", "backend_provider_id", "backend_implementation_version", "determinism_profile"):
    _require_text(backend[field], f"backend.{field}")
  _require_sha(backend["system_graph_sha256"], "backend.system_graph_sha256")
  _require_sha(backend["stage_contract_sha256"], "backend.stage_contract_sha256")

  scope = _require_exact(payload["execution_scope"], {
    "world_ids", "entity_ids", "episode_ids", "request_ids", "epochs",
  }, "execution_scope")
  for field in ("world_ids", "episode_ids", "request_ids"):
    _require_sorted_ids(scope[field], f"execution_scope.{field}")
  _require_sorted_ids(scope["entity_ids"], "execution_scope.entity_ids", allow_empty=True)
  epochs = _require_exact(scope["epochs"], {"world", "entity", "episode", "request"}, "execution_scope.epochs")
  for field in epochs:
    _require_generation(epochs[field], f"execution_scope.epochs.{field}")

  lifecycle = payload["lifecycle"]
  if not isinstance(lifecycle, list) or not lifecycle:
    raise RunReceiptError("lifecycle must be a non-empty ordered list")
  event_order = {event: index for index, event in enumerate(LIFECYCLE_EVENTS)}
  previous_rank = -1
  previous_durable_sequence = -1
  for index, event in enumerate(lifecycle):
    row = _require_exact(event, {"sequence", "event", "timestamp", "epoch", "durable_sequence"}, f"lifecycle[{index}]")
    _require_safe_integer(row["sequence"], f"lifecycle[{index}].sequence")
    if row["sequence"] != index:
      raise RunReceiptError("lifecycle sequence must be contiguous from zero")
    if row["event"] not in event_order or event_order[row["event"]] < previous_rank:
      raise RunReceiptError("lifecycle events are not admitted or ordered")
    previous_rank = event_order[row["event"]]
    _require_text(row["timestamp"], f"lifecycle[{index}].timestamp")
    _require_generation(row["epoch"], f"lifecycle[{index}].epoch")
    _require_safe_integer(row["durable_sequence"], f"lifecycle[{index}].durable_sequence")
    if row["durable_sequence"] < previous_durable_sequence:
      raise RunReceiptError("lifecycle durable sequence must be monotonic")
    previous_durable_sequence = row["durable_sequence"]
  if lifecycle[0]["event"] != "journal_admitted" or lifecycle[-1]["event"] != "terminal":
    raise RunReceiptError("lifecycle must begin at durable admission and end terminal")
  _require_safe_integer(payload["journal_last_sequence"], "journal_last_sequence")
  journal_tail = payload["journal_last_sequence"]
  if any(row["durable_sequence"] > journal_tail for row in lifecycle):
    raise RunReceiptError("lifecycle durable sequence exceeds the journal tail")
  if lifecycle[-1]["durable_sequence"] != journal_tail:
    raise RunReceiptError("terminal lifecycle event is not bound to the journal tail")

  results = _require_exact(payload["results"], {"result_digest", "output_artifacts", "native_validation"}, "results")
  _require_sha(results["result_digest"], "results.result_digest", allow_empty=True)
  if not isinstance(results["output_artifacts"], list):
    raise RunReceiptError("results.output_artifacts must be an array")
  output_names: list[str] = []
  for index, output in enumerate(results["output_artifacts"]):
    row = _require_exact(output, {
      "name", "digest", "media_type", "size", "availability", "retention_class", "retrieval_location",
    }, f"results.output_artifacts[{index}]")
    _require_id(row["name"], f"results.output_artifacts[{index}].name")
    _require_sha(row["digest"], f"results.output_artifacts[{index}].digest")
    for field in ("media_type", "availability", "retrieval_location"):
      _require_text(row[field], f"results.output_artifacts[{index}].{field}")
    _require_safe_integer(row["size"], f"results.output_artifacts[{index}].size")
    if row["retention_class"] not in RETENTION_CLASSES:
      raise RunReceiptError("output artifact retention class is not admitted")
    output_names.append(row["name"])
  if output_names != sorted(output_names) or len(set(output_names)) != len(output_names):
    raise RunReceiptError("output artifacts must be sorted and name-unique")
  native_validation = _require_exact(results["native_validation"], {"accepted", "validator_id", "evidence_sha256"}, "results.native_validation")
  if not isinstance(native_validation["accepted"], bool):
    raise RunReceiptError("results.native_validation.accepted must be boolean")
  _require_id(native_validation["validator_id"], "results.native_validation.validator_id")
  _require_sha(native_validation["evidence_sha256"], "results.native_validation.evidence_sha256")

  checkpoints = _require_exact(payload["checkpoints"], {"source_refs", "created_refs"}, "checkpoints")
  for collection_name in ("source_refs", "created_refs"):
    refs = checkpoints[collection_name]
    if not isinstance(refs, list):
      raise RunReceiptError(f"checkpoints.{collection_name} must be an array")
    previous_id = ""
    for index, ref in enumerate(refs):
      row = _require_exact(ref, set(CHECKPOINT_REF_FIELDS), f"checkpoints.{collection_name}[{index}]")
      _require_id(row["checkpoint_id"], f"checkpoints.{collection_name}[{index}].checkpoint_id")
      for field in ("checkpoint_sha256", "validation_sha256"):
        _require_sha(row[field], f"checkpoints.{collection_name}[{index}].{field}")
      _require_generation(row["state_schema_generation"], f"checkpoints.{collection_name}[{index}].state_schema_generation")
      _require_text(row["retrieval_location"], f"checkpoints.{collection_name}[{index}].retrieval_location")
      if previous_id >= row["checkpoint_id"]:
        raise RunReceiptError(f"checkpoints.{collection_name} must be sorted and identity-unique")
      previous_id = row["checkpoint_id"]
  for collection, path in ((payload["qualification_refs"], "qualification_refs"), (payload["side_effect_receipts"], "side_effect_receipts")):
    if not isinstance(collection, list):
      raise RunReceiptError(f"{path} must be an array")
    identities: list[str] = []
    for index, item in enumerate(collection):
      fields = {"identity", "digest"} if path == "qualification_refs" else {"identity", "digest", "media_type", "retrieval_location"}
      row = _require_exact(item, fields, f"{path}[{index}]")
      _require_id(row["identity"], f"{path}[{index}].identity")
      _require_sha(row["digest"], f"{path}[{index}].digest")
      if path == "side_effect_receipts":
        _require_text(row["media_type"], f"{path}[{index}].media_type")
        _require_text(row["retrieval_location"], f"{path}[{index}].retrieval_location")
      identities.append(row["identity"])
    if identities != sorted(identities) or len(set(identities)) != len(identities):
      raise RunReceiptError(f"{path} must be sorted and identity-unique")

  completion = _require_exact(payload["completion"], {"created_at", "finalized_at", "durable_ack"}, "completion")
  for field in ("created_at", "finalized_at"):
    _require_text(completion[field], f"completion.{field}")
  if completion["durable_ack"] is not True:
    raise RunReceiptError("completion requires a durable acknowledgement")
  if payload["terminal_state"] not in TERMINAL_STATES:
    raise RunReceiptError("terminal_state is not admitted")
  _require_text(payload["terminal_reason"], "terminal_reason")
  _require_safe_integer(payload["journal_last_sequence"], "journal_last_sequence")
  _require_sha(payload["journal_last_record_sha256"], "journal_last_record_sha256")
  if payload["retention_class"] not in RETENTION_CLASSES:
    raise RunReceiptError("retention_class is not admitted")
  if payload["terminal_state"] == "completed":
    if not results["result_digest"] or not native_validation["accepted"]:
      raise RunReceiptError("completed receipt requires a validated result digest")
    if not results["output_artifacts"]:
      raise RunReceiptError("completed receipt requires at least one durable output artifact")
    events = tuple(row["event"] for row in lifecycle)
    if any(event not in events for event in COMPLETED_LIFECYCLE):
      raise RunReceiptError("completed receipt lifecycle is incomplete")

  authenticity = _require_exact(payload["authenticity"], {"attestation_sha256", "signatures"}, "authenticity")
  _require_sha(authenticity["attestation_sha256"], "authenticity.attestation_sha256")
  if not isinstance(authenticity["signatures"], list):
    raise RunReceiptError("authenticity.signatures must be an array")
  for index, signature in enumerate(authenticity["signatures"]):
    row = _require_exact(signature, {"algorithm", "key_id", "signature", "signer_context"}, f"authenticity.signatures[{index}]")
    for field in row:
      _require_text(row[field], f"authenticity.signatures[{index}].{field}")
  return payload


def validate_run_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
  if not isinstance(value, Mapping):
    raise RunReceiptError("receipt envelope must be an object")
  envelope = deepcopy(dict(value))
  if set(envelope) != REQUIRED_FIELDS:
    raise RunReceiptError("receipt envelope fields are not exact")
  if (
    envelope["canonicalization"] != CANONICALIZATION
    or envelope["envelope_version"] != ENVELOPE_VERSION
    or envelope["domain"] != DOMAIN
    or envelope["media_type"] != MEDIA_TYPE
  ):
    raise RunReceiptError("receipt envelope profile, domain, or media type mismatch")
  payload = validate_run_receipt_payload(envelope["payload"])
  if envelope["payload"] != payload:
    raise RunReceiptError("receipt payload is not canonical")
  _require_sha(envelope["payload_sha256"], "payload_sha256")
  expected = authority_digest_sha256(DOMAIN, MEDIA_TYPE, canonical_json_bytes(payload))
  if envelope["payload_sha256"] != expected:
    raise RunReceiptError("receipt detached payload digest mismatch")
  if not isinstance(envelope["signatures"], list):
    raise RunReceiptError("receipt envelope signatures must be an array")
  for index, signature in enumerate(envelope["signatures"]):
    row = _require_exact(signature, {"algorithm", "key_id", "signature", "signer_context"}, f"signatures[{index}]")
    for field in row:
      _require_text(row[field], f"signatures[{index}].{field}")
  return envelope


def build_run_receipt(**fields: Any) -> dict[str, Any]:
  payload = validate_run_receipt_payload({
    "authority_kind": AUTHORITY_KIND,
    "schema_version": SCHEMA_VERSION,
    "contract_version": CONTRACT_VERSION,
    "writer_role": WRITER_ROLE,
    "hash_algorithm": HASH_ALGORITHM,
    **deepcopy(fields),
  })
  return validate_run_receipt({
    "canonicalization": CANONICALIZATION,
    "domain": DOMAIN,
    "envelope_version": ENVELOPE_VERSION,
    "media_type": MEDIA_TYPE,
    "payload": payload,
    "payload_sha256": authority_digest_sha256(DOMAIN, MEDIA_TYPE, canonical_json_bytes(payload)),
    "signatures": [],
  })


def run_receipt_schema() -> dict[str, Any]:
  return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
