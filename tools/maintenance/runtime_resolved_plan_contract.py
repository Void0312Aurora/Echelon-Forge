"""P5-A closed resolved execution-plan contract.

The legacy resolved manifest remains an input-only compatibility artifact.  A
closed plan records every owner-derived join needed to admit execution so a
consumer cannot silently select a different request, catalog lock, profile
projection, backend request, or manifest.  This module is intentionally a
pure contract/compiler helper; durable storage and production cutover remain
P5-B/P5-D responsibilities.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import runtime_authority_contracts as authority
from tools.maintenance import runtime_composition_projection_contract as projection
from tools.maintenance import runtime_profile_projection_contract as profile
from tools.maintenance import simulation_composition_contract as composition


SCHEMA_VERSION = "echelon_forge.resolved_execution_plan.v1"
CONTRACT_VERSION = "1.0.0"
CANONICALIZATION = composition.CANONICALIZATION_ID
HASH_ALGORITHM = "sha256"
BACKEND_SCHEMA_PATH = REPO_ROOT / "src/runtime/contracts/composition/runtime_backend_provider_request.v1.schema.json"
SCHEMA_PATH = REPO_ROOT / "src/runtime/contracts/composition/resolved_execution_plan.v1.schema.json"
GENERATED_HEADER_PATH = REPO_ROOT / "src/runtime/contracts/composition/resolved_execution_plan.v1.generated.h"
FIXTURE_DIR = REPO_ROOT / "tests/architecture/composition/fixtures"
DEFAULT_OUTPUT = FIXTURE_DIR / "default_resolved_execution_plan.v1.json"


class ClosedPlanError(ValueError):
  """Raised when a closed plan cannot be admitted."""


def _read(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _payload(value: Mapping[str, Any]) -> dict[str, Any]:
  return {key: item for key, item in value.items() if key not in {"canonical_json", "plan_sha256"}}


def _pretty(value: Any) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
  return composition.canonical_json_bytes(dict(value))


def _digest(value: Mapping[str, Any]) -> str:
  return composition.canonical_sha256(dict(value))


def _validate_backend_request(value: Mapping[str, Any]) -> None:
  schema = _read(BACKEND_SCHEMA_PATH)
  try:
    jsonschema.Draft202012Validator(schema).validate(value)
  except jsonschema.ValidationError as error:
    raise ClosedPlanError(f"backend request rejected: {error.message}") from error
  required = {"provider_id", "provider_implementation_version", "backend_profile_id", "required_capabilities", "schema_version"}
  if set(value) != required:
    raise ClosedPlanError("backend request fields are not exact")


def _validate_inputs(
  request: Mapping[str, Any],
  lock: Mapping[str, Any],
  projection_value: Mapping[str, Any],
  backend_request: Mapping[str, Any],
  requested_manifest: Mapping[str, Any],
  resolved_manifest: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
  request_value = deepcopy(dict(request))
  lock_value = deepcopy(dict(lock))
  projection_value = deepcopy(dict(projection_value))
  backend_value = deepcopy(dict(backend_request))
  requested_value = deepcopy(dict(requested_manifest))
  resolved_value = deepcopy(dict(resolved_manifest))

  request_issues = projection.validate_request(request_value)
  lock_issues = projection.validate_catalog_lock(lock_value, request=request_value)
  if request_issues or lock_issues:
    raise ClosedPlanError(
      "request/lock validation failed: "
      + "; ".join(f"{issue.code}@{issue.path}" for issue in [*request_issues, *lock_issues])
    )
  _validate_backend_request(backend_value)
  backend_entries = [entry for entry in lock_value["entries"] if entry["category"] == "backend"]
  if len(backend_entries) != 1:
    raise ClosedPlanError("catalog lock must contain exactly one admitted backend entry")
  backend_entry = backend_entries[0]
  if (
    backend_entry["descriptor_id"] != backend_value["provider_id"]
    or backend_entry["implementation_version"] != backend_value["provider_implementation_version"]
    or backend_entry["trust_decision"] != "admitted"
  ):
    raise ClosedPlanError("backend request is not bound to the admitted catalog backend entry")
  requested_issues = composition.validate_manifest(requested_value)
  try:
    authority._validate_resolved_plan(resolved_value)
    resolved_issues = composition.validate_manifest(resolved_value.get("manifest"))
  except (authority.AuthorityContractError, TypeError, KeyError, ValueError) as error:
    resolved_issues = [composition.ValidationIssue("composition.resolved_invalid", "$", str(error))]
  if requested_issues or resolved_issues:
    raise ClosedPlanError(
      "manifest validation failed: "
      + "; ".join(f"{issue.code}@{issue.path}" for issue in [*requested_issues, *resolved_issues])
    )
  projection_issues = profile.validate_profile_projection(
    projection_value, request_value, lock_value, requested_value, resolved_value
  )
  if projection_issues:
    raise ClosedPlanError(
      "profile projection validation failed: "
      + "; ".join(f"{issue.code}@{issue.path}" for issue in projection_issues)
    )
  if lock_value["request_sha256"] != projection.request_identity(request_value):
    raise ClosedPlanError("catalog lock request identity does not match request")
  if lock_value["lock_sha256"] != projection.catalog_lock_identity(lock_value):
    raise ClosedPlanError("catalog lock digest is stale")
  if projection_value["projection_sha256"] != profile.projection_identity(projection_value):
    raise ClosedPlanError("profile projection digest is stale")
  manifest = resolved_value.get("manifest", resolved_value)
  requested_payload = requested_value.get("manifest", requested_value)
  backend_from_manifest = manifest.get("backend_request")
  if (
    not isinstance(backend_from_manifest, Mapping)
    or backend_from_manifest.get("provider_id") != backend_value["provider_id"]
    or backend_from_manifest.get("backend_profile_id") != backend_value["backend_profile_id"]
    or backend_from_manifest.get("required_capabilities") != backend_value["required_capabilities"]
  ):
    raise ClosedPlanError("backend request does not match resolved manifest owner input")
  provider_rows = [row for row in resolved_value["manifest"]["providers"] if row["provider_id"] == backend_value["provider_id"]]
  if len(provider_rows) != 1 or provider_rows[0]["implementation_version"] != backend_value["provider_implementation_version"]:
    raise ClosedPlanError("backend request implementation version does not match resolved provider")
  if manifest != requested_payload:
    raise ClosedPlanError("requested and resolved manifest payloads differ")
  if resolved_value["requested_manifest_sha256"] != composition.canonical_sha256(requested_value):
    raise ClosedPlanError("resolved requested-manifest digest is stale")
  resolved_body = {key: value for key, value in resolved_value.items() if key != "resolved_manifest_sha256"}
  if resolved_value["resolved_manifest_sha256"] != composition.canonical_sha256(resolved_body):
    raise ClosedPlanError("resolved-manifest digest is stale")
  return request_value, lock_value, projection_value, backend_value, requested_value, resolved_value


def build_closed_plan(
  request: Mapping[str, Any],
  lock: Mapping[str, Any],
  projection_value: Mapping[str, Any],
  backend_request: Mapping[str, Any],
  requested_manifest: Mapping[str, Any],
  resolved_manifest: Mapping[str, Any],
  *,
  plan_id: str = "plan-default-closed",
  writer_generation: str = "1",
  reader_generation_min: str = "1",
  reader_generation_max: str = "1",
) -> dict[str, Any]:
  request_value, lock_value, projection_value, backend_value, requested_value, resolved_value = _validate_inputs(
    request, lock, projection_value, backend_request, requested_manifest, resolved_manifest
  )
  bindings = {
    "request_sha256": projection.request_identity(request_value),
    "catalog_lock_sha256": lock_value["lock_sha256"],
    "profile_projection_sha256": projection_value["projection_sha256"],
    "backend_request_sha256": _digest(backend_value),
    "requested_manifest_sha256": _digest(requested_value),
    "resolved_manifest_sha256": resolved_value["resolved_manifest_sha256"],
  }
  owner_join = {
    "composition_id": resolved_value["manifest"]["composition_id"],
    "requested_profile": deepcopy(resolved_value["manifest"]["requested_profile"]),
    "backend_provider_id": backend_value["provider_id"],
    "backend_profile_id": backend_value["backend_profile_id"],
    "backend_implementation_version": backend_value["provider_implementation_version"],
    "catalog_backend_owner_id": next(entry for entry in lock_value["entries"] if entry["category"] == "backend")["owner_id"],
    "catalog_backend_implementation_id": next(entry for entry in lock_value["entries"] if entry["category"] == "backend")["implementation_id"],
    "catalog_backend_provenance": deepcopy(next(entry for entry in lock_value["entries"] if entry["category"] == "backend")["provenance"]),
    "catalog_backend_capabilities": sorted(next(entry for entry in lock_value["entries"] if entry["category"] == "backend")["capabilities"]),
    "resolver_contract_version": resolved_value["resolver_contract_version"],
  }
  authority_payload = {
    "authority_kind": "resolved_execution_plan",
    "schema_version": "echelon_forge.resolved_execution_plan.v1",
    "contract_version": "echelon_forge.resolved_execution_plan_contract.v1",
    "writer_role": "plan_compiler",
    "plan_id": plan_id,
    "writer_generation": writer_generation,
    "reader_generation_min": reader_generation_min,
    "reader_generation_max": reader_generation_max,
    "request_sha256": bindings["request_sha256"],
    "catalog_lock_sha256": bindings["catalog_lock_sha256"],
    "profile_projection_sha256": bindings["profile_projection_sha256"],
    "backend_request_sha256": bindings["backend_request_sha256"],
    "requested_manifest_sha256": bindings["requested_manifest_sha256"],
    "resolved_manifest_sha256": bindings["resolved_manifest_sha256"],
    "composition_id": owner_join["composition_id"],
    "requested_profile": owner_join["requested_profile"],
    "backend": {
      "provider_id": owner_join["backend_provider_id"],
      "profile_id": owner_join["backend_profile_id"],
      "implementation_version": owner_join["backend_implementation_version"],
      "required_capabilities": backend_value["required_capabilities"],
    },
    "provider_versions": [
      {"provider_id": row["provider_id"], "implementation_version": row["implementation_version"]}
      for row in resolved_value["manifest"]["providers"]
    ],
    "resolved_manifest": resolved_value,
  }
  plan_authority = authority.build_resolved_execution_plan_authority(authority_payload)
  body: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "plan_contract_version": CONTRACT_VERSION,
    "plan_id": plan_id,
    "writer_role": "plan_compiler",
    "writer_generation": writer_generation,
    "reader_generation_min": reader_generation_min,
    "reader_generation_max": reader_generation_max,
    "authority_envelope_json": json.dumps(plan_authority, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
    "authority_payload_bytes": plan_authority["payload"],
    "owner_inputs": {
      "request": request_value,
      "catalog_lock": lock_value,
      "profile_projection": projection_value,
      "backend_request": backend_value,
      "requested_manifest": requested_value,
      "resolved_manifest": resolved_value,
    },
    "input_bindings": bindings,
    "owner_join": owner_join,
    "canonicalization": CANONICALIZATION,
    "hash_algorithm": HASH_ALGORITHM,
  }
  normalized = json.loads(_canonical_bytes(body))
  normalized["canonical_json"] = _canonical_bytes(normalized).decode("utf-8")
  normalized["plan_sha256"] = _digest(_payload(normalized))
  return normalized


def validate_closed_plan(
  value: Mapping[str, Any],
  request: Mapping[str, Any],
  lock: Mapping[str, Any],
  projection_value: Mapping[str, Any],
  backend_request: Mapping[str, Any],
  requested_manifest: Mapping[str, Any],
  resolved_manifest: Mapping[str, Any],
) -> None:
  expected = build_closed_plan(
    request, lock, projection_value, backend_request, requested_manifest, resolved_manifest,
    plan_id=str(value.get("plan_id", "")),
    writer_generation=str(value.get("writer_generation", "")),
    reader_generation_min=str(value.get("reader_generation_min", "")),
    reader_generation_max=str(value.get("reader_generation_max", "")),
  )
  if dict(value) != expected:
    raise ClosedPlanError("closed plan is stale, tampered, or joined to a different owner input")
  if value.get("canonical_json") != _canonical_bytes(_payload(value)).decode("utf-8"):
    raise ClosedPlanError("closed plan canonical_json is not the canonical payload")
  if value.get("plan_sha256") != _digest(_payload(value)):
    raise ClosedPlanError("closed plan digest does not seal the canonical payload")


def plan_schema() -> dict[str, Any]:
  sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
  string = {"type": "string", "minLength": 1, "pattern": "^[\\u0000-\\u007F]*$"}
  bindings = {
    "type": "object", "additionalProperties": False,
    "properties": {key: sha for key in ("request_sha256", "catalog_lock_sha256", "profile_projection_sha256", "backend_request_sha256", "requested_manifest_sha256", "resolved_manifest_sha256")},
    "required": ["request_sha256", "catalog_lock_sha256", "profile_projection_sha256", "backend_request_sha256", "requested_manifest_sha256", "resolved_manifest_sha256"],
  }
  owner_join = {
    "type": "object", "additionalProperties": False,
    "properties": {
      "composition_id": string,
      "requested_profile": {"type": "object", "additionalProperties": False, "properties": {"profile_id": string, "profile_version": string}, "required": ["profile_id", "profile_version"]},
      "backend_provider_id": string,
      "backend_profile_id": string,
      "backend_implementation_version": string,
      "catalog_backend_owner_id": string,
      "catalog_backend_implementation_id": string,
      "catalog_backend_provenance": {
        "type": "object", "additionalProperties": False,
        "properties": {"artifact_identity": string, "artifact_kind": string, "artifact_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"}},
        "required": ["artifact_identity", "artifact_kind", "artifact_sha256"],
      },
      "catalog_backend_capabilities": {"type": "array", "items": string, "minItems": 1, "uniqueItems": True},
      "resolver_contract_version": string,
    },
    "required": ["composition_id", "requested_profile", "backend_provider_id", "backend_profile_id", "backend_implementation_version", "catalog_backend_owner_id", "catalog_backend_implementation_id", "catalog_backend_provenance", "catalog_backend_capabilities", "resolver_contract_version"],
  }
  owner_inputs = {
    "type": "object", "additionalProperties": False,
    "properties": {key: {"type": "object"} for key in ("request", "catalog_lock", "profile_projection", "backend_request", "requested_manifest", "resolved_manifest")},
    "required": ["request", "catalog_lock", "profile_projection", "backend_request", "requested_manifest", "resolved_manifest"],
  }
  return {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": SCHEMA_VERSION,
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "schema_version": {"const": SCHEMA_VERSION},
      "plan_contract_version": {"const": CONTRACT_VERSION},
      "plan_id": string,
      "writer_role": {"const": "plan_compiler"},
      "writer_generation": {"pattern": "^(?:0|[1-9][0-9]*)$", "type": "string"},
      "reader_generation_min": {"pattern": "^(?:0|[1-9][0-9]*)$", "type": "string"},
      "reader_generation_max": {"pattern": "^(?:0|[1-9][0-9]*)$", "type": "string"},
      "authority_envelope_json": string,
      "authority_payload_bytes": {"type": "object"},
      "owner_inputs": owner_inputs,
      "input_bindings": bindings,
      "owner_join": owner_join,
      "canonicalization": {"const": CANONICALIZATION},
      "hash_algorithm": {"const": HASH_ALGORITHM},
      "canonical_json": string,
      "plan_sha256": sha,
    },
    "required": ["schema_version", "plan_contract_version", "plan_id", "writer_role", "writer_generation", "reader_generation_min", "reader_generation_max", "authority_envelope_json", "authority_payload_bytes", "owner_inputs", "input_bindings", "owner_join", "canonicalization", "hash_algorithm", "canonical_json", "plan_sha256"],
  }


def generated_header(value: Mapping[str, Any]) -> str:
  encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
  chunks = [encoded[index:index + 16000] for index in range(0, len(encoded), 16000)]
  literals = "\n".join(f'    R"EFPLAN({chunk})EFPLAN"' for chunk in chunks)
  return (
    "#pragma once\n\n"
    "#include <string_view>\n\n"
    "namespace runtime::contracts::generated {\n"
    "// clang-format off\n"
    "inline const std::string_view kDefaultResolvedExecutionPlanJson =\n"
    + literals
    + ";\n"
    "// clang-format on\n"
    "} // namespace runtime::contracts::generated\n"
  )


def _default_inputs() -> tuple[dict[str, Any], ...]:
  return tuple(_read(FIXTURE_DIR / name) for name in (
    "default_runtime_composition_request.v1.json",
    "default_admitted_catalog_lock.v1.json",
    "default_runtime_profile_projection.v1.json",
    "default_backend_provider_request.v1.json",
    "default_compatibility_manifest.requested.json",
    "default_compatibility_manifest.resolved.json",
  ))


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("command", choices=("generate", "validate"))
  parser.add_argument("--plan", type=Path, default=DEFAULT_OUTPUT)
  args = parser.parse_args(argv)
  inputs = _default_inputs()
  if args.command == "generate":
    value = build_closed_plan(*inputs)
    args.plan.write_bytes(_canonical_bytes(value))
    SCHEMA_PATH.write_text(_pretty(plan_schema()), encoding="utf-8", newline="\n")
    GENERATED_HEADER_PATH.write_text(generated_header(value), encoding="utf-8", newline="\n")
    print(value["plan_sha256"])
    return 0
  value = _read(args.plan)
  jsonschema.Draft202012Validator(plan_schema()).validate(value)
  validate_closed_plan(value, *inputs)
  print(value["plan_sha256"])
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
