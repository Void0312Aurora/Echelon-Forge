"""Versioned authority shells shared by Python, Cordis, and native adapters.

This module owns validation and a Python projection only.  It does not publish
runtime truth or persist an authority.  Native and Cordis consumers use the
same checked-in schemas and vectors; entry from current artifacts is possible
only through an explicit one-way adapter.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

from tools.maintenance.simulation_composition_contract import (
  RESOLVER_CONTRACT_VERSION,
  RESOLVED_SCHEMA_VERSION,
  canonical_sha256 as legacy_canonical_sha256,
  validate_manifest,
)
from tools.maintenance.runtime_composition_projection_contract import validate_request


CANONICALIZATION = "echelon_forge.canonical_json.v2"
ENVELOPE_VERSION = "echelon_forge.authority_envelope.v1"
DOMAIN_SEPARATOR = b"echelon-forge-authority-v1\x00"
MAX_SAFE_INTEGER = 9_007_199_254_740_991
AUTHORITY_ENVELOPE_FIELDS = frozenset(
  {"canonicalization", "domain", "envelope_version", "media_type", "payload", "payload_sha256", "signatures"}
)
DECIMAL_GENERATION_RE = re.compile(r"^(?:0|[1-9][0-9]*)$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AuthorityContractError(ValueError):
  """Raised when an authority payload or envelope fails closed."""


@dataclass(frozen=True, slots=True)
class AuthoritySpec:
  kind: str
  domain: str
  media_type: str
  writer_role: str
  required_fields: frozenset[str]


AUTHORITY_SPECS: dict[str, AuthoritySpec] = {
  "resolved_execution_plan": AuthoritySpec(
    "resolved_execution_plan",
    "composition.execution-plan",
    "application/vnd.echelon-forge.resolved-execution-plan.v1+json",
    "plan_compiler",
    frozenset({
      "authority_kind", "schema_version", "contract_version", "writer_role", "plan_id",
      "writer_generation", "reader_generation_min", "reader_generation_max", "request_sha256",
      "catalog_lock_sha256", "profile_projection_sha256", "backend_request_sha256",
      "requested_manifest_sha256", "resolved_manifest_sha256", "composition_id",
      "requested_profile", "backend", "provider_versions", "resolved_manifest",
    }),
  ),
  "resolved_composition_plan": AuthoritySpec(
    "resolved_composition_plan",
    "composition.resolved-plan",
    "application/vnd.echelon-forge.resolved-composition-plan.v1+json",
    "plan_compiler",
    frozenset({
      "authority_kind", "schema_version", "contract_version", "writer_role", "adapter_role",
       "plan_id", "request_sha256", "writer_generation", "reader_generation_min",
       "reader_generation_max", "source_artifact_sha256", "source_artifact_schema_version",
       "source_request_manifest_binding_sha256", "source_requested_manifest_sha256", "resolved_plan",
    }),
  ),
  "release_manifest": AuthoritySpec(
    "release_manifest",
    "release.manifest",
    "application/vnd.echelon-forge.release-manifest.v1+json",
    "release_artifact_pipeline",
    frozenset({
      "authority_kind", "schema_version", "contract_version", "writer_role", "release_id",
      "writer_generation", "reader_generation_min", "reader_generation_max", "package_set",
      "supported_rows", "provenance_sha256", "sbom_sha256", "toolchain_identity", "source_revision",
      "compatibility_generation", "minimum_reader_generation", "state_schema_generation", "rollback_policy",
      "stored_artifact_inventory_sha256", "rollback_deadline", "last_reader_deadline", "irreversible_write_boundary",
    }),
  ),
  "rollout_decision": AuthoritySpec(
    "rollout_decision",
    "release.rollout-decision",
    "application/vnd.echelon-forge.rollout-decision.v1+json",
    "release_controller",
    frozenset({
      "authority_kind", "schema_version", "contract_version", "writer_role", "decision_id",
      "release_id", "manifest_sha256", "plan_sha256", "plan_reader_generation_min", "plan_reader_generation_max",
      "predecessor_decision_id", "state", "writer_generation",
      "decision_sequence", "cohort", "rollback_deadline", "checkpoint_id", "irreversible_write_boundary",
    }),
  ),
  "state_checkpoint": AuthoritySpec(
    "state_checkpoint",
    "runtime.state-checkpoint",
    "application/vnd.echelon-forge.state-checkpoint.v1+json",
    "runtime_host",
    frozenset({
      "authority_kind", "schema_version", "contract_version", "writer_role", "writer_generation",
      "checkpoint_id", "plan_sha256", "release_id", "decision_id", "run_id", "host_boot_id",
      "incarnation_epoch", "transfer_fence_sequence", "world_fragments", "aggregate_state_sha256",
      "state_schema_generation", "target_reader_generation_min", "target_reader_generation_max",
    }),
  ),
}


def _error(path: str, detail: str) -> AuthorityContractError:
  return AuthorityContractError(f"{path}: {detail}")


def _canonical_number(value: int | float, path: str) -> str:
  if isinstance(value, bool):
    raise _error(path, "boolean is not a number")
  if isinstance(value, int):
    if abs(value) > MAX_SAFE_INTEGER:
      raise _error(path, "integer outside exact cross-language range must be a decimal string")
    return str(value)
  if not math.isfinite(value):
    raise _error(path, "non-finite number is forbidden")
  if value.is_integer() and abs(value) > MAX_SAFE_INTEGER:
    raise _error(path, "integer-valued float outside exact cross-language range must be a decimal string")
  if value == 0:
    return "0"
  text = repr(value).lower()
  negative = text.startswith("-")
  unsigned = text[1:] if negative else text
  if "e" not in unsigned:
    if unsigned.endswith(".0"):
      unsigned = unsigned[:-2]
    return ("-" if negative else "") + unsigned
  significand, exponent_text = unsigned.split("e", 1)
  exponent = int(exponent_text)
  digits = significand.replace(".", "")
  decimal_index = (significand.find(".") if "." in significand else len(significand)) + exponent
  if 1e-6 <= abs(value) < 1e21:
    if decimal_index <= 0:
      fixed = "0." + ("0" * -decimal_index) + digits
    elif decimal_index >= len(digits):
      fixed = digits + ("0" * (decimal_index - len(digits)))
    else:
      fixed = digits[:decimal_index] + "." + digits[decimal_index:]
    if "." in fixed:
      fixed = fixed.rstrip("0").rstrip(".")
    return ("-" if negative else "") + fixed
  mantissa = digits[0] + (("." + digits[1:].rstrip("0")) if digits[1:].rstrip("0") else "")
  sign = "+" if exponent >= 0 else "-"
  return ("-" if negative else "") + mantissa + "e" + sign + str(abs(exponent))


def _canonical_string(value: str, path: str) -> str:
  if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
    raise _error(path, "lone UTF-16 surrogate is forbidden")
  return value


def _canonical_value(value: Any, path: str = "$") -> Any:
  if value is None or isinstance(value, bool):
    return value
  if isinstance(value, (int, float)):
    _canonical_number(value, path)
    return value
  if isinstance(value, str):
    return _canonical_string(value, path)
  if isinstance(value, list):
    return [_canonical_value(item, f"{path}[{index}]") for index, item in enumerate(value)]
  if isinstance(value, Mapping):
    normalized: dict[str, Any] = {}
    keys: list[str] = []
    for key in value:
      if not isinstance(key, str):
        raise _error(path, "object keys must be strings")
      _canonical_string(key, f"{path}.<key>")
      keys.append(key)
    for key in sorted(keys, key=lambda item: item.encode("utf-16-be")):
      if key in normalized:
        raise _error(path, f"duplicate object key {key!r}")
      normalized[key] = _canonical_value(value[key], f"{path}.{key}")
    return normalized
  raise _error(path, f"unsupported JSON value {type(value).__name__}")


def _encode(value: Any, path: str = "$") -> str:
  if value is None:
    return "null"
  if isinstance(value, bool):
    return "true" if value else "false"
  if isinstance(value, (int, float)):
    return _canonical_number(value, path)
  if isinstance(value, str):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
  if isinstance(value, list):
    return "[" + ",".join(_encode(item, f"{path}[{index}]") for index, item in enumerate(value)) + "]"
  if isinstance(value, Mapping):
    keys = sorted(value, key=lambda item: item.encode("utf-16-be"))
    return "{" + ",".join(
      json.dumps(key, ensure_ascii=False) + ":" + _encode(value[key], f"{path}.{key}") for key in keys
    ) + "}"
  raise _error(path, f"unsupported JSON value {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
  """Return UTF-8 RFC-8785 profile bytes with project schema restrictions."""

  return _encode(_canonical_value(value)).encode("utf-8")


def authority_digest_sha256(domain: str, media_type: str, payload_bytes: bytes) -> str:
  if not isinstance(domain, str) or not domain or "\x00" in domain:
    raise AuthorityContractError("domain must be a non-empty UTF-8 string without NUL")
  if not isinstance(media_type, str) or not media_type or "\x00" in media_type:
    raise AuthorityContractError("media_type must be a non-empty UTF-8 string without NUL")
  _canonical_string(domain, "domain")
  _canonical_string(media_type, "media_type")
  if not isinstance(payload_bytes, bytes):
    raise AuthorityContractError("payload_bytes must be bytes")
  return hashlib.sha256(
    DOMAIN_SEPARATOR + domain.encode("utf-8") + b"\x00" + media_type.encode("utf-8") + b"\x00" + payload_bytes
  ).hexdigest()


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  result: dict[str, Any] = {}
  for key, value in pairs:
    if key in result:
      raise AuthorityContractError(f"duplicate object key: {key!r}")
    result[key] = value
  return result


def parse_canonical_json_bytes(payload_bytes: bytes) -> dict[str, Any]:
  if payload_bytes.startswith(b"\xef\xbb\xbf"):
    raise AuthorityContractError("UTF-8 BOM is forbidden")
  try:
    parsed = json.loads(
      payload_bytes.decode("utf-8"),
      object_pairs_hook=_reject_duplicate_pairs,
      parse_constant=lambda value: (_ for _ in ()).throw(AuthorityContractError(f"non-finite JSON constant: {value}")),
    )
  except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
    raise AuthorityContractError(f"invalid UTF-8/JSON authority payload: {exc}") from exc
  if not isinstance(parsed, dict):
    raise AuthorityContractError("authority payload must be a JSON object")
  if canonical_json_bytes(parsed) != payload_bytes:
    raise AuthorityContractError("payload is not canonical JSON v2")
  return parsed


def _require_string(value: Any, field: str, *, identifier: bool = False, nonempty: bool = True) -> None:
  if not isinstance(value, str) or (nonempty and not value):
    raise AuthorityContractError(f"{field} must be a non-empty string")
  if identifier and IDENTIFIER_RE.fullmatch(value) is None:
    raise AuthorityContractError(f"{field} must be a bounded identifier")


def _require_sha256(value: Any, field: str) -> None:
  if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
    raise AuthorityContractError(f"{field} must be lowercase SHA-256 hex")


def _require_generation(value: Any, field: str) -> None:
  if not isinstance(value, str) or DECIMAL_GENERATION_RE.fullmatch(value) is None:
    raise AuthorityContractError(f"{field} must be a canonical decimal string")


def _require_generation_window(payload: Mapping[str, Any]) -> None:
  for field in ("writer_generation", "reader_generation_min", "reader_generation_max"):
    if field in payload:
      _require_generation(payload[field], field)
  if "reader_generation_min" in payload and "reader_generation_max" in payload:
    if int(payload["reader_generation_min"]) > int(payload["reader_generation_max"]):
      raise AuthorityContractError("reader generation window is inverted")


def _require_set_array(value: Any, field: str, *, object_key: str | None = None) -> None:
  if not isinstance(value, list):
    raise AuthorityContractError(f"{field} must be an array")
  if not value:
    raise AuthorityContractError(f"{field} must not be empty")
  if object_key is None:
    if any(not isinstance(item, str) or not item for item in value):
      raise AuthorityContractError(f"{field} must contain non-empty strings")
    if value != sorted(value, key=lambda item: item.encode("utf-16-be")) or len(set(value)) != len(value):
      raise AuthorityContractError(f"{field} must be sorted and duplicate-free")
  else:
    if any(not isinstance(item, dict) or not isinstance(item.get(object_key), str) or not item[object_key] for item in value):
      raise AuthorityContractError(f"{field} objects must have non-empty {object_key}")
    keys = [item[object_key] for item in value]
    if keys != sorted(keys, key=lambda item: item.encode("utf-16-be")) or len(set(keys)) != len(keys):
      raise AuthorityContractError(f"{field} must be sorted and duplicate-free by {object_key}")


def _require_sequence_array(value: Any, field: str) -> None:
  if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
    raise AuthorityContractError(f"{field} must contain non-empty strings")
  if len(set(value)) != len(value):
    raise AuthorityContractError(f"{field} must be duplicate-free")


def _require_signatures(value: Any) -> None:
  if not isinstance(value, list):
    raise AuthorityContractError("signatures must be an array")
  required = {"algorithm", "key_id", "signature", "signer_context"}
  for index, item in enumerate(value):
    if not isinstance(item, dict) or set(item) != required:
      raise AuthorityContractError(f"signatures[{index}] has an invalid typed context")
    for field in required:
      _require_string(item[field], f"signatures[{index}].{field}")


def _validate_resolved_plan(value: Any) -> None:
  if not isinstance(value, dict):
    raise AuthorityContractError("resolved_plan must be an object")
  expected = {"schema_version", "resolver_contract_version", "requested_manifest_sha256", "provider_construction_order", "system_registration_order", "manifest", "resolved_manifest_sha256"}
  if set(value) != expected:
    raise AuthorityContractError("resolved_plan has unknown or missing fields")
  if value["schema_version"] != RESOLVED_SCHEMA_VERSION:
    raise AuthorityContractError("resolved_plan schema version mismatch")
  for field in ("resolver_contract_version", "requested_manifest_sha256", "resolved_manifest_sha256"):
    _require_string(value[field], f"resolved_plan.{field}")
  _require_sha256(value["requested_manifest_sha256"], "resolved_plan.requested_manifest_sha256")
  if value["resolver_contract_version"] != RESOLVER_CONTRACT_VERSION:
    raise AuthorityContractError("resolved_plan resolver contract version mismatch")
  _require_sha256(value["resolved_manifest_sha256"], "resolved_plan.resolved_manifest_sha256")
  for field in ("provider_construction_order", "system_registration_order"):
    _require_sequence_array(value[field], f"resolved_plan.{field}")
  if not isinstance(value["manifest"], dict) or validate_manifest(value["manifest"]):
    raise AuthorityContractError("resolved_plan.manifest is not a valid current manifest")
  body = {key: nested for key, nested in value.items() if key != "resolved_manifest_sha256"}
  if legacy_canonical_sha256(body) != value["resolved_manifest_sha256"]:
    raise AuthorityContractError("resolved_plan digest mismatch")


def validate_authority_payload(kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
  spec = AUTHORITY_SPECS.get(kind)
  if spec is None:
    raise AuthorityContractError(f"unknown authority kind: {kind}")
  if not isinstance(payload, Mapping):
    raise AuthorityContractError("authority payload must be an object")
  normalized = _canonical_value(dict(payload))
  missing = sorted(spec.required_fields - normalized.keys())
  unknown = sorted(normalized.keys() - spec.required_fields)
  if missing:
    raise AuthorityContractError(f"{kind} missing required fields: {missing}")
  if unknown:
    raise AuthorityContractError(f"{kind} has unknown fields: {unknown}")
  for field in ("authority_kind", "schema_version", "contract_version", "writer_role"):
    _require_string(normalized[field], field)
  if normalized["authority_kind"] != kind:
    raise AuthorityContractError(f"authority_kind must be {kind!r}")
  if normalized["schema_version"] != f"echelon_forge.{kind}.v1":
    raise AuthorityContractError(f"{kind} schema_version mismatch")
  if normalized["contract_version"] != f"echelon_forge.{kind}_contract.v1":
    raise AuthorityContractError(f"{kind} contract_version mismatch")
  if normalized["writer_role"] != spec.writer_role:
    raise AuthorityContractError(f"{kind} writer_role must be {spec.writer_role!r}")
  _require_generation_window(normalized)
  if kind == "resolved_execution_plan":
    for field in (
      "plan_id", "composition_id", "request_sha256", "catalog_lock_sha256",
      "profile_projection_sha256", "backend_request_sha256", "requested_manifest_sha256",
      "resolved_manifest_sha256",
    ):
      _require_string(normalized[field], field, identifier=field in {"plan_id", "composition_id"})
      if field.endswith("sha256"):
        _require_sha256(normalized[field], field)
    _require_string(normalized["requested_profile"]["profile_id"], "requested_profile.profile_id", identifier=True)
    _require_string(normalized["requested_profile"]["profile_version"], "requested_profile.profile_version")
    if set(normalized["requested_profile"]) != {"profile_id", "profile_version"}:
      raise AuthorityContractError("requested_profile fields are not exact")
    backend = normalized["backend"]
    if set(backend) != {"provider_id", "profile_id", "implementation_version", "required_capabilities"}:
      raise AuthorityContractError("execution-plan backend fields are not exact")
    _require_string(backend["provider_id"], "backend.provider_id", identifier=True)
    _require_string(backend["profile_id"], "backend.profile_id", identifier=True)
    _require_string(backend["implementation_version"], "backend.implementation_version")
    _require_set_array(backend["required_capabilities"], "backend.required_capabilities")
    if not isinstance(normalized["provider_versions"], list) or not normalized["provider_versions"]:
      raise AuthorityContractError("provider_versions must be non-empty")
    for row in normalized["provider_versions"]:
      if set(row) != {"provider_id", "implementation_version"}:
        raise AuthorityContractError("provider_versions row fields are not exact")
      _require_string(row["provider_id"], "provider_versions.provider_id", identifier=True)
      _require_string(row["implementation_version"], "provider_versions.implementation_version")
    resolved = normalized["resolved_manifest"]
    if not isinstance(resolved, dict) or not resolved.get("manifest"):
      raise AuthorityContractError("resolved_manifest is not a resolved composition artifact")
    try:
      _validate_resolved_plan(resolved)
      manifest = resolved["manifest"]
      if manifest["composition_id"] != normalized["composition_id"] or manifest["requested_profile"] != normalized["requested_profile"]:
        raise AuthorityContractError("execution-plan composition/profile binding mismatch")
      if manifest["backend_request"]["provider_id"] != backend["provider_id"] or manifest["backend_request"]["backend_profile_id"] != backend["profile_id"]:
        raise AuthorityContractError("execution-plan backend binding mismatch")
      provider_rows = [row for row in manifest["providers"] if row["provider_id"] == backend["provider_id"]]
      if len(provider_rows) != 1 or provider_rows[0]["implementation_version"] != backend["implementation_version"]:
        raise AuthorityContractError("execution-plan backend implementation mismatch")
    except (KeyError, TypeError, ValueError) as error:
      raise AuthorityContractError(f"resolved_manifest rejected: {error}") from error
    if normalized["requested_manifest_sha256"] != resolved["requested_manifest_sha256"] or normalized["resolved_manifest_sha256"] != resolved["resolved_manifest_sha256"]:
      raise AuthorityContractError("execution-plan manifest digest binding mismatch")
  elif kind == "resolved_composition_plan":
    _require_string(normalized["adapter_role"], "adapter_role")
    if normalized["adapter_role"] != "legacy_resolved_manifest_reader":
      raise AuthorityContractError("resolved plan adapter_role is not the one-way legacy reader")
    _require_string(normalized["plan_id"], "plan_id", identifier=True)
    _require_sha256(normalized["request_sha256"], "request_sha256")
    _require_sha256(normalized["source_artifact_sha256"], "source_artifact_sha256")
    _require_sha256(normalized["source_requested_manifest_sha256"], "source_requested_manifest_sha256")
    _require_sha256(normalized["source_request_manifest_binding_sha256"], "source_request_manifest_binding_sha256")
    if normalized["source_artifact_schema_version"] != RESOLVED_SCHEMA_VERSION:
      raise AuthorityContractError("source artifact schema version mismatch")
    _validate_resolved_plan(normalized["resolved_plan"])
    if normalized["source_requested_manifest_sha256"] != normalized["resolved_plan"]["requested_manifest_sha256"]:
      raise AuthorityContractError("source requested-manifest digest mismatch")
    expected_binding = hashlib.sha256(
      (normalized["request_sha256"] + "\0" + normalized["source_requested_manifest_sha256"]).encode("ascii")
    ).hexdigest()
    if normalized["source_request_manifest_binding_sha256"] != expected_binding:
      raise AuthorityContractError("source request/manifest provenance binding mismatch")
    if legacy_canonical_sha256(normalized["resolved_plan"]) != normalized["source_artifact_sha256"]:
      raise AuthorityContractError("source artifact digest mismatch")
  elif kind == "release_manifest":
    _require_string(normalized["release_id"], "release_id", identifier=True)
    _require_set_array(normalized["package_set"], "package_set", object_key="name")
    for item in normalized["package_set"]:
      if set(item) != {"name", "sha256"}:
        raise AuthorityContractError("package_set entries have unknown fields")
      _require_sha256(item["sha256"], "package_set.sha256")
    _require_set_array(normalized["supported_rows"], "supported_rows")
    for field in ("provenance_sha256", "sbom_sha256", "stored_artifact_inventory_sha256"):
      _require_sha256(normalized[field], field)
    for field in ("toolchain_identity", "source_revision"):
      _require_string(normalized[field], field)
    _require_generation(normalized["compatibility_generation"], "compatibility_generation")
    _require_generation(normalized["minimum_reader_generation"], "minimum_reader_generation")
    _require_generation(normalized["state_schema_generation"], "state_schema_generation")
    _require_string(normalized["rollback_policy"], "rollback_policy")
    if normalized["rollback_policy"] not in {"checkpoint-recovery", "package-restart"}:
      raise AuthorityContractError("rollback_policy is not an admitted enum")
    for field in ("rollback_deadline", "last_reader_deadline", "irreversible_write_boundary"):
      _require_string(normalized[field], field)
  elif kind == "rollout_decision":
    for field in ("decision_id", "release_id", "cohort", "rollback_deadline", "irreversible_write_boundary"):
      _require_string(normalized[field], field, identifier=field in {"decision_id", "release_id"})
    _require_sha256(normalized["manifest_sha256"], "manifest_sha256")
    _require_sha256(normalized["plan_sha256"], "plan_sha256")
    _require_generation(normalized["plan_reader_generation_min"], "plan_reader_generation_min")
    _require_generation(normalized["plan_reader_generation_max"], "plan_reader_generation_max")
    if int(normalized["plan_reader_generation_min"]) > int(normalized["plan_reader_generation_max"]):
      raise AuthorityContractError("rollout plan reader window is inverted")
    _require_generation(normalized["decision_sequence"], "decision_sequence")
    _require_string(normalized["state"], "state")
    if normalized["state"] not in {"prepared", "shadow", "canary-ready", "production-canary", "adoption-expanding", "rollback-window", "stable", "backed-out"}:
      raise AuthorityContractError("rollout state is not an admitted enum")
    if not isinstance(normalized["predecessor_decision_id"], str):
      raise AuthorityContractError("predecessor_decision_id must be a string")
    if not isinstance(normalized["checkpoint_id"], str):
      raise AuthorityContractError("checkpoint_id must be a string")
    if normalized["predecessor_decision_id"]:
      _require_string(normalized["predecessor_decision_id"], "predecessor_decision_id", identifier=True)
    if normalized["checkpoint_id"]:
      _require_string(normalized["checkpoint_id"], "checkpoint_id", identifier=True)
  else:
    for field in ("checkpoint_id", "release_id", "decision_id", "run_id", "host_boot_id"):
      _require_string(normalized[field], field, identifier=True)
    for field in ("plan_sha256", "aggregate_state_sha256"):
      _require_sha256(normalized[field], field)
    for field in ("incarnation_epoch", "transfer_fence_sequence", "state_schema_generation"):
      _require_generation(normalized[field], field)
    for field in ("target_reader_generation_min", "target_reader_generation_max"):
      _require_generation(normalized[field], field)
    if int(normalized["target_reader_generation_min"]) > int(normalized["target_reader_generation_max"]):
      raise AuthorityContractError("checkpoint target reader window is inverted")
    fragments = normalized["world_fragments"]
    if not isinstance(fragments, list) or not fragments:
      raise AuthorityContractError("world_fragments must be a non-empty ordered array")
    expected_fragment = {"world_id", "episode_ids", "fragment_sequence", "state_sha256"}
    sequences: list[str] = []
    for index, fragment in enumerate(fragments):
      if not isinstance(fragment, dict) or set(fragment) != expected_fragment:
        raise AuthorityContractError(f"world_fragments[{index}] has an invalid shape")
      _require_string(fragment["world_id"], f"world_fragments[{index}].world_id", identifier=True)
      _require_set_array(fragment["episode_ids"], f"world_fragments[{index}].episode_ids")
      _require_generation(fragment["fragment_sequence"], f"world_fragments[{index}].fragment_sequence")
      _require_sha256(fragment["state_sha256"], f"world_fragments[{index}].state_sha256")
      sequences.append(fragment["fragment_sequence"])
    world_ids = [fragment["world_id"] for fragment in fragments]
    if len(set(world_ids)) != len(world_ids):
      raise AuthorityContractError("world_fragments must cover each world exactly once")
    if sequences != sorted(sequences, key=int) or len(set(sequences)) != len(sequences):
      raise AuthorityContractError("world_fragments must be ordered and sequence-unique")
  return normalized


def _build_authority_envelope(kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
  spec = AUTHORITY_SPECS.get(kind)
  if spec is None:
    raise AuthorityContractError(f"unknown authority kind: {kind}")
  normalized = validate_authority_payload(kind, payload)
  payload_bytes = canonical_json_bytes(normalized)
  return validate_authority_envelope({
    "canonicalization": CANONICALIZATION,
    "domain": spec.domain,
    "envelope_version": ENVELOPE_VERSION,
    "media_type": spec.media_type,
    "payload": normalized,
    "payload_sha256": authority_digest_sha256(spec.domain, spec.media_type, payload_bytes),
    "signatures": [],
  })


def validate_authority_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
  normalized = _canonical_value(dict(envelope))
  if set(normalized) != AUTHORITY_ENVELOPE_FIELDS:
    raise AuthorityContractError("authority envelope fields are not exact")
  if normalized["canonicalization"] != CANONICALIZATION:
    raise AuthorityContractError("unsupported canonicalization profile")
  if normalized["envelope_version"] != ENVELOPE_VERSION:
    raise AuthorityContractError("unsupported authority envelope version")
  _require_string(normalized["domain"], "domain")
  _require_string(normalized["media_type"], "media_type")
  if not isinstance(normalized["payload"], dict):
    raise AuthorityContractError("authority envelope payload must be an object")
  _require_signatures(normalized["signatures"])
  payload_kind = normalized["payload"].get("authority_kind")
  spec = AUTHORITY_SPECS.get(payload_kind)
  if spec is None:
    raise AuthorityContractError("authority envelope payload has unknown kind")
  if normalized["domain"] != spec.domain or normalized["media_type"] != spec.media_type:
    raise AuthorityContractError("authority envelope domain/media type mismatch")
  validate_authority_payload(payload_kind, normalized["payload"])
  expected = authority_digest_sha256(normalized["domain"], normalized["media_type"], canonical_json_bytes(normalized["payload"]))
  _require_sha256(normalized["payload_sha256"], "payload_sha256")
  if normalized["payload_sha256"] != expected:
    raise AuthorityContractError("detached authority digest mismatch")
  return normalized


def adapt_current_resolved_manifest(
  resolved_manifest: Mapping[str, Any],
  *,
  source_request: Mapping[str, Any],
  source_requested_manifest: Mapping[str, Any],
  plan_id: str,
  writer_generation: str = "1",
  reader_generation_min: str = "1",
  reader_generation_max: str = "1",
) -> dict[str, Any]:
  """Read one current artifact and bind it to the exact source request."""

  if (not isinstance(resolved_manifest, Mapping) or not isinstance(source_request, Mapping) or
      not isinstance(source_requested_manifest, Mapping)):
    raise AuthorityContractError("resolved artifact, source request, and requested manifest must be objects")
  request_issues = validate_request(dict(source_request))
  if request_issues:
    raise AuthorityContractError("source request is not a valid admitted request")
  candidate = dict(resolved_manifest)
  _validate_resolved_plan(candidate)
  requested_manifest_digest = legacy_canonical_sha256(dict(source_requested_manifest))
  if requested_manifest_digest != candidate["requested_manifest_sha256"]:
    raise AuthorityContractError("source requested manifest does not match resolved artifact")
  return _build_authority_envelope("resolved_composition_plan", {
    "authority_kind": "resolved_composition_plan",
    "schema_version": "echelon_forge.resolved_composition_plan.v1",
    "contract_version": "echelon_forge.resolved_composition_plan_contract.v1",
    "writer_role": "plan_compiler",
    "adapter_role": "legacy_resolved_manifest_reader",
    "plan_id": plan_id,
    "request_sha256": legacy_canonical_sha256(dict(source_request)),
    "writer_generation": writer_generation,
    "reader_generation_min": reader_generation_min,
    "reader_generation_max": reader_generation_max,
      "source_artifact_sha256": legacy_canonical_sha256(candidate),
      "source_artifact_schema_version": RESOLVED_SCHEMA_VERSION,
      "source_requested_manifest_sha256": requested_manifest_digest,
      "source_request_manifest_binding_sha256": hashlib.sha256(
        (legacy_canonical_sha256(dict(source_request)) + "\0" + requested_manifest_digest).encode("ascii")
      ).hexdigest(),
      "resolved_plan": candidate,
  })


def build_resolved_execution_plan_authority(payload: Mapping[str, Any]) -> dict[str, Any]:
  """Build the P5-A authority from a closed plan payload.

  The legacy manifest adapter remains available for the P3/P4 reader window;
  production plan admission uses this owner-complete authority instead.
  """

  return _build_authority_envelope("resolved_execution_plan", payload)


def build_release_manifest_shell(payload: Mapping[str, Any]) -> dict[str, Any]:
  return _build_authority_envelope("release_manifest", payload)


def build_rollout_decision_shell(payload: Mapping[str, Any]) -> dict[str, Any]:
  return _build_authority_envelope("rollout_decision", payload)


def build_state_checkpoint_shell(payload: Mapping[str, Any]) -> dict[str, Any]:
  return _build_authority_envelope("state_checkpoint", payload)


def validate_authority_chain(plan: Mapping[str, Any], release: Mapping[str, Any], rollout: Mapping[str, Any], checkpoint: Mapping[str, Any]) -> None:
  """Validate the cross-authority identity graph before P3-C storage."""

  p = validate_authority_envelope(plan)["payload"]
  r = validate_authority_envelope(release)["payload"]
  d = validate_authority_envelope(rollout)["payload"]
  c = validate_authority_envelope(checkpoint)["payload"]
  if d["release_id"] != r["release_id"] or c["release_id"] != r["release_id"] or c["decision_id"] != d["decision_id"]:
    raise AuthorityContractError("release/rollout/checkpoint identity binding mismatch")
  if c["plan_sha256"] != plan["payload_sha256"]:
    raise AuthorityContractError("checkpoint plan digest does not match plan envelope")
  if d["plan_sha256"] != plan["payload_sha256"]:
    raise AuthorityContractError("rollout plan digest does not match plan envelope")
  if d["manifest_sha256"] != release["payload_sha256"]:
    raise AuthorityContractError("rollout manifest digest does not match release envelope")
  if int(d["decision_sequence"]) == 0 and d["predecessor_decision_id"]:
    raise AuthorityContractError("initial rollout cannot have a predecessor")
  if int(d["decision_sequence"]) > 0 and not d["predecessor_decision_id"]:
    raise AuthorityContractError("non-initial rollout must name a predecessor")
  if int(p["reader_generation_max"]) < int(r["reader_generation_min"]):
    raise AuthorityContractError("plan/release reader generation windows do not overlap")
  if d["checkpoint_id"] and d["checkpoint_id"] != c["checkpoint_id"]:
    raise AuthorityContractError("rollout checkpoint does not match checkpoint envelope")
  if int(c["writer_generation"]) < int(d["writer_generation"]):
    raise AuthorityContractError("checkpoint writer generation is older than rollout decision")


def validate_rollout_transition(previous: Mapping[str, Any], current: Mapping[str, Any]) -> None:
  """Validate the monotonic N/N-1 decision transition before storage."""

  previous_payload = validate_authority_envelope(previous)["payload"]
  current_payload = validate_authority_envelope(current)["payload"]
  if current_payload["predecessor_decision_id"] != previous_payload["decision_id"]:
    raise AuthorityContractError("rollout predecessor identity mismatch")
  if int(current_payload["decision_sequence"]) != int(previous_payload["decision_sequence"]) + 1:
    raise AuthorityContractError("rollout decision sequence is not monotonic")
