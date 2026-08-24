#!/usr/bin/env python3
"""P2-C0 producer-neutral request and owner-derived catalog-lock contract.

This module deliberately stops at projection and admission.  It does not lower
requests into the P1-B manifest and does not construct runtime providers.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import simulation_composition_contract as low_level


REQUEST_SCHEMA_VERSION = "echelon_forge.runtime_composition_request.v1"
LOCK_SCHEMA_VERSION = "echelon_forge.admitted_catalog_lock.v1"
LOCK_CONTRACT_VERSION = "echelon_forge.admitted_catalog_lock_contract.v1"
AUTHORITY_SCHEMA_VERSION = "echelon_forge.owner_authority_registry.v1"
AUTHORITY_REGISTRY_ID = "echelon_forge.runtime_composition_owners"
AUTHORITY_REGISTRY_VERSION = "1.0.0"
CANONICALIZATION_ID = low_level.CANONICALIZATION_ID
HASH_ALGORITHM = low_level.HASH_ALGORITHM
MAX_CANONICAL_VALUE_DEPTH = 64

REQUEST_SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/runtime_composition_request.v1.schema.json"
)
LOCK_SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/admitted_catalog_lock.v1.schema.json"
)
AUTHORITY_SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/owner_authority_registry.v1.schema.json"
)
REQUEST_FIXTURE_PATH = REPO_ROOT / (
  "tests/architecture/composition/fixtures/default_runtime_composition_request.v1.json"
)
LOCK_FIXTURE_PATH = REPO_ROOT / (
  "tests/architecture/composition/fixtures/default_admitted_catalog_lock.v1.json"
)
AUTHORITY_FIXTURE_PATH = REPO_ROOT / (
  "tests/architecture/composition/fixtures/owner_authority_registry.v1.json"
)
INVALID_MATRIX_PATH = REPO_ROOT / (
  "tests/architecture/composition/fixtures/invalid_projection_matrix.v1.json"
)

ID_RE = low_level.ID_RE
VERSION_RE = low_level.VERSION_RE
HEX64_RE = low_level.HEX64_RE
CATEGORIES = ("model", "system", "backend", "domain", "evidence", "security")
TRUST_DECISIONS = ("admitted",)
ARTIFACT_KINDS = ("repository_builtin", "native_package", "cordis_package")
OWNER_AUTHORITY_BY_CATEGORY = {
  "model": "owner.model",
  "system": "owner.scheduler",
  "backend": "owner.backend",
  "domain": "owner.domain",
  "evidence": "owner.evidence",
  "security": "owner.security",
}


@dataclass(frozen=True, order=True)
class ValidationIssue:
  code: str
  path: str
  detail: str


class ContractError(ValueError):
  def __init__(self, issues: Iterable[ValidationIssue]):
    self.issues = tuple(sorted(issues))
    super().__init__("; ".join(f"{row.code}@{row.path}" for row in self.issues))


def _issue(issues: list[ValidationIssue], code: str, path: str, detail: str) -> None:
  issues.append(ValidationIssue(code, path, detail))


def _object_schema(properties: dict[str, Any]) -> dict[str, Any]:
  return {
    "type": "object",
    "additionalProperties": False,
    "properties": properties,
    "required": list(properties),
  }


def _string_schema(pattern: str | None = None) -> dict[str, Any]:
  return {"type": "string", "minLength": 1, "pattern": pattern or low_level.ASCII_PATTERN}


def _string_array() -> dict[str, Any]:
  return {"type": "array", "items": _string_schema(), "uniqueItems": True}


def _version_schema() -> dict[str, Any]:
  return _string_schema(VERSION_RE.pattern)


def _authority_payload(registry: dict[str, Any]) -> dict[str, Any]:
  return {
    key: value
    for key, value in registry.items()
    if key not in {"canonical_json", "registry_sha256"}
  }


def default_authority_registry() -> dict[str, Any]:
  registry: dict[str, Any] = {
    "schema_version": AUTHORITY_SCHEMA_VERSION,
    "registry_id": AUTHORITY_REGISTRY_ID,
    "registry_version": AUTHORITY_REGISTRY_VERSION,
    "categories": [
      {"category": category, "owner_id": OWNER_AUTHORITY_BY_CATEGORY[category]}
      for category in CATEGORIES
    ],
    "canonicalization": CANONICALIZATION_ID,
    "hash_algorithm": HASH_ALGORITHM,
  }
  normalized = low_level._normalize_value(deepcopy(registry), "$")
  registry["canonical_json"] = low_level.canonical_json_bytes(_authority_payload(normalized)).decode("utf-8")
  registry["registry_sha256"] = low_level.canonical_sha256(_authority_payload(normalized))
  return registry


def validate_authority_registry(registry: Any) -> list[ValidationIssue]:
  issues: list[ValidationIssue] = []
  if not isinstance(registry, dict):
    return [ValidationIssue("projection.invalid_json_type", "$", "expected object")]
  required = {
    "schema_version", "registry_id", "registry_version", "categories",
    "canonicalization", "hash_algorithm", "canonical_json", "registry_sha256",
  }
  if set(registry) != required:
    _issue(issues, "projection.invalid_authority_registry", "$", "invalid authority registry shape")
    return sorted(issues)
  if registry["schema_version"] != AUTHORITY_SCHEMA_VERSION:
    _issue(issues, "projection.unsupported_schema_version", "$.schema_version", AUTHORITY_SCHEMA_VERSION)
  if registry["registry_id"] != AUTHORITY_REGISTRY_ID or ID_RE.fullmatch(registry["registry_id"]) is None:
    _issue(issues, "projection.invalid_identifier", "$.registry_id", "invalid authority registry id")
  if registry["registry_version"] != AUTHORITY_REGISTRY_VERSION or VERSION_RE.fullmatch(registry["registry_version"]) is None:
    _issue(issues, "projection.invalid_version", "$.registry_version", "invalid authority registry version")
  if registry["canonicalization"] != CANONICALIZATION_ID or registry["hash_algorithm"] != HASH_ALGORITHM:
    _issue(issues, "projection.invalid_identity", "$.canonicalization", "authority identity algorithm mismatch")
  if not isinstance(registry["canonical_json"], str) or not isinstance(registry["registry_sha256"], str) or HEX64_RE.fullmatch(registry["registry_sha256"]) is None:
    _issue(issues, "projection.invalid_identity", "$.registry_sha256", "expected canonical bytes and SHA-256")
  categories = registry["categories"]
  if not isinstance(categories, list) or not categories:
    _issue(issues, "projection.invalid_json_type", "$.categories", "expected non-empty array")
  else:
    seen: set[str] = set()
    for index, row in enumerate(categories):
      path = f"$.categories[{index}]"
      if not isinstance(row, dict) or set(row) != {"category", "owner_id"}:
        _issue(issues, "projection.invalid_authority", path, "invalid category authority")
        continue
      category, owner = row["category"], row["owner_id"]
      if not isinstance(category, str) or category not in CATEGORIES or owner != OWNER_AUTHORITY_BY_CATEGORY.get(category):
        _issue(issues, "projection.invalid_authority", path, "category owner does not match repository authority")
      if isinstance(category, str) and category in seen:
        _issue(issues, "projection.duplicate_value", f"{path}.category", "category is repeated")
      if isinstance(category, str):
        seen.add(category)
    if set(seen) != set(CATEGORIES):
      _issue(issues, "projection.invalid_authority", "$.categories", "registry must cover every admitted category")
  if not issues:
    normalized = low_level._normalize_value(deepcopy(registry), "$")
    expected = default_authority_registry()
    if registry != expected:
      _issue(issues, "projection.authority_registry_mismatch", "$", "registry is not the repository authority artifact")
  return sorted(issues)


def request_schema() -> dict[str, Any]:
  versions = _object_schema({
    "composition": _version_schema(),
    "runtime": _version_schema(),
    "content": _version_schema(),
    "stage": _version_schema(),
  })
  intent = _object_schema({
    "simulation_id": _string_schema(ID_RE.pattern),
    "policy_id": _string_schema(ID_RE.pattern),
    "evaluation_id": _string_schema(ID_RE.pattern),
  })
  profile = _object_schema({
    "profile_id": _string_schema(ID_RE.pattern),
    "profile_version": _version_schema(),
  })
  canonical_value = {"$ref": "#/$defs/canonical_value"}
  return {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": REQUEST_SCHEMA_VERSION,
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "schema_version": {"const": REQUEST_SCHEMA_VERSION},
      "request_id": _string_schema(ID_RE.pattern),
      "request_version": _version_schema(),
      "contract_versions": versions,
      "intent": intent,
      "requested_profile": profile,
      "required_capabilities": _string_array(),
      "required_policies": _string_array(),
      "configuration": canonical_value,
    },
    "required": [
      "schema_version", "request_id", "request_version", "contract_versions", "intent",
      "requested_profile", "required_capabilities", "required_policies", "configuration",
    ],
    "$defs": {
      "canonical_value": {
        "oneOf": [
          {"type": "null"},
          {"type": "boolean"},
          {"type": "integer", "minimum": low_level.INT64_MIN, "maximum": low_level.INT64_MAX},
          {"type": "string", "pattern": low_level.ASCII_PATTERN},
          {"type": "array", "items": {"$ref": "#/$defs/canonical_value"}},
          {
            "type": "object",
            "propertyNames": {"pattern": low_level.ASCII_PATTERN},
            "additionalProperties": {"$ref": "#/$defs/canonical_value"},
          },
        ]
      }
    },
  }


def authority_registry_schema() -> dict[str, Any]:
  category = _object_schema({
    "category": {"enum": list(CATEGORIES)},
    "owner_id": _string_schema(ID_RE.pattern),
  })
  return {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": AUTHORITY_SCHEMA_VERSION,
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "schema_version": {"const": AUTHORITY_SCHEMA_VERSION},
      "registry_id": _string_schema(ID_RE.pattern),
      "registry_version": _version_schema(),
      "categories": {"type": "array", "items": category, "minItems": len(CATEGORIES), "uniqueItems": True},
      "canonicalization": {"const": CANONICALIZATION_ID},
      "hash_algorithm": {"const": HASH_ALGORITHM},
      "canonical_json": _string_schema(),
      "registry_sha256": {"type": "string", "pattern": HEX64_RE.pattern},
    },
    "required": [
      "schema_version", "registry_id", "registry_version", "categories",
      "canonicalization", "hash_algorithm", "canonical_json", "registry_sha256",
    ],
  }


def lock_schema() -> dict[str, Any]:
  provenance = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "artifact_kind": {"enum": list(ARTIFACT_KINDS)},
      "artifact_identity": _string_schema(),
      "artifact_sha256": {"type": ["string", "null"], "pattern": HEX64_RE.pattern},
    },
    "required": ["artifact_kind", "artifact_identity", "artifact_sha256"],
    "oneOf": [
      {
        "properties": {"artifact_kind": {"const": "repository_builtin"}},
        "required": ["artifact_kind", "artifact_identity", "artifact_sha256"],
      },
      {
        "properties": {
          "artifact_kind": {"enum": ["native_package", "cordis_package"]},
          "artifact_sha256": {"type": "string", "pattern": HEX64_RE.pattern},
        },
        "required": ["artifact_kind", "artifact_identity", "artifact_sha256"],
      },
    ],
  }
  authority = _object_schema({
    "category": {"enum": list(CATEGORIES)},
    "owner_id": _string_schema(ID_RE.pattern),
  })
  entry = _object_schema({
    "category": {"enum": list(CATEGORIES)},
    "owner_id": _string_schema(ID_RE.pattern),
    "descriptor_id": _string_schema(ID_RE.pattern),
    "implementation_id": _string_schema(ID_RE.pattern),
    "implementation_version": _version_schema(),
    "capabilities": _string_array(),
    "provenance": provenance,
    "trust_decision": {"enum": list(TRUST_DECISIONS)},
  })
  return {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": LOCK_SCHEMA_VERSION,
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "schema_version": {"const": LOCK_SCHEMA_VERSION},
      "contract_version": {"const": LOCK_CONTRACT_VERSION},
      "lock_id": _string_schema(ID_RE.pattern),
      "lock_version": _version_schema(),
      "request_schema_version": {"const": REQUEST_SCHEMA_VERSION},
      "request_sha256": {"type": "string", "pattern": HEX64_RE.pattern},
      "authority_registry_sha256": {"type": "string", "pattern": HEX64_RE.pattern},
      "category_authorities": {"type": "array", "items": authority, "minItems": 1, "uniqueItems": True},
      "entries": {"type": "array", "items": entry, "minItems": 1, "uniqueItems": True},
      "canonicalization": {"const": CANONICALIZATION_ID},
      "hash_algorithm": {"const": HASH_ALGORITHM},
      "canonical_json": _string_schema(),
      "lock_sha256": {"type": "string", "pattern": HEX64_RE.pattern},
    },
    "required": [
      "schema_version", "contract_version", "lock_id", "lock_version",
      "request_schema_version", "request_sha256", "category_authorities", "entries",
      "authority_registry_sha256",
      "canonicalization", "hash_algorithm", "canonical_json", "lock_sha256",
    ],
  }


def _normalize_request(request: dict[str, Any]) -> dict[str, Any]:
  normalized = low_level._normalize_value(deepcopy(request), "$")
  normalized["required_capabilities"] = sorted(
    set(normalized["required_capabilities"]), key=lambda value: value.encode("utf-8")
  )
  normalized["required_policies"] = sorted(
    set(normalized["required_policies"]), key=lambda value: value.encode("utf-8")
  )
  return normalized


def _normalize_entry(entry: dict[str, Any]) -> dict[str, Any]:
  normalized = low_level._normalize_value(deepcopy(entry), "$")
  normalized["capabilities"] = sorted(
    set(normalized["capabilities"]), key=lambda value: value.encode("utf-8")
  )
  return normalized


def normalize_lock(lock: dict[str, Any]) -> dict[str, Any]:
  normalized = low_level._normalize_value(deepcopy(lock), "$")
  normalized["category_authorities"] = sorted(
    normalized["category_authorities"], key=lambda row: row["category"].encode("utf-8")
  )
  normalized["entries"] = sorted(
    (_normalize_entry(row) for row in normalized["entries"]),
    key=lambda row: (row["category"].encode("utf-8"), row["descriptor_id"].encode("utf-8")),
  )
  return normalized


def request_identity(request: dict[str, Any]) -> str:
  issues = validate_request(request)
  if issues:
    raise ContractError(issues)
  return low_level.canonical_sha256(_normalize_request(request))


def _validate_string_array(values: Any, path: str, issues: list[ValidationIssue]) -> None:
  if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
    _issue(issues, "projection.invalid_json_type", path, "expected ASCII string array")
    return
  normalized = [low_level._nfc(value) for value in values]
  for index, value in enumerate(values):
    if not value or not value.isascii() or normalized[index] != value:
      _issue(issues, "projection.invalid_string_value", f"{path}[{index}]", "expected non-empty ASCII NFC string")
  if len(normalized) != len(set(normalized)):
    _issue(issues, "projection.duplicate_value", path, "values must be unique after NFC normalization")


def _validate_exact_object(value: Any, path: str, fields: set[str], issues: list[ValidationIssue]) -> bool:
  if not isinstance(value, dict):
    _issue(issues, "projection.invalid_json_type", path, "expected object")
    return False
  for field in sorted(fields - set(value)):
    _issue(issues, "projection.missing_field", f"{path}.{field}", "required field is missing")
  for field in sorted(set(value) - fields):
    _issue(issues, "projection.unexpected_field", f"{path}.{field}", "field is not in v1 contract")
  return set(value) == fields


def _validate_canonical_value(value: Any, path: str, issues: list[ValidationIssue], depth: int = 0) -> None:
  if depth > MAX_CANONICAL_VALUE_DEPTH:
    _issue(issues, "projection.configuration_depth_exceeded", path, f"maximum depth is {MAX_CANONICAL_VALUE_DEPTH}")
    return
  if value is None or isinstance(value, bool):
    return
  if isinstance(value, int):
    if not low_level.INT64_MIN <= value <= low_level.INT64_MAX:
      _issue(issues, "projection.noncanonical_configuration", path, "integer outside signed 64-bit range")
    return
  if isinstance(value, float):
    _issue(issues, "projection.noncanonical_configuration", path, "floating-point values are forbidden")
    return
  if isinstance(value, str):
    if not value.isascii():
      _issue(issues, "projection.invalid_string_value", path, "configuration strings must be ASCII")
    return
  if isinstance(value, list):
    for index, item in enumerate(value):
      _validate_canonical_value(item, f"{path}[{index}]", issues, depth + 1)
    return
  if isinstance(value, dict):
    for key, item in value.items():
      if not isinstance(key, str) or not key.isascii():
        _issue(issues, "projection.invalid_string_value", f"{path}.{key}", "configuration keys must be ASCII")
      _validate_canonical_value(item, f"{path}.{key}", issues, depth + 1)
    return
  _issue(issues, "projection.noncanonical_configuration", path, f"unsupported JSON type {type(value).__name__}")


def _lock_payload(lock: dict[str, Any]) -> dict[str, Any]:
  return {key: value for key, value in lock.items() if key not in {"canonical_json", "lock_sha256"}}


def catalog_lock_identity(lock: dict[str, Any]) -> str:
  issues = validate_catalog_lock(lock, check_identity=False)
  if issues:
    raise ContractError(issues)
  return low_level.canonical_sha256(_lock_payload(normalize_lock(lock)))


def validate_request(request: Any) -> list[ValidationIssue]:
  issues: list[ValidationIssue] = []
  if not isinstance(request, dict):
    return [ValidationIssue("projection.invalid_json_type", "$", "expected object")]
  required = {
    "schema_version", "request_id", "request_version", "contract_versions", "intent",
    "requested_profile", "required_capabilities", "required_policies", "configuration",
  }
  for field in sorted(required - request.keys()):
    _issue(issues, "projection.missing_field", f"$.{field}", "required field is missing")
  for field in sorted(request.keys() - required):
    _issue(issues, "projection.unexpected_field", f"$.{field}", "field is not in v1 contract")
  if issues:
    return issues
  if request["schema_version"] != REQUEST_SCHEMA_VERSION:
    _issue(issues, "projection.unsupported_schema_version", "$.schema_version", REQUEST_SCHEMA_VERSION)
  _validate_exact_object(request["contract_versions"], "$.contract_versions", {"composition", "runtime", "content", "stage"}, issues)
  _validate_exact_object(request["intent"], "$.intent", {"simulation_id", "policy_id", "evaluation_id"}, issues)
  _validate_exact_object(request["requested_profile"], "$.requested_profile", {"profile_id", "profile_version"}, issues)
  def nested(path: str) -> Any:
    parent: Any = request
    for part in path.split("."):
      if not isinstance(parent, dict) or part not in parent:
        return None
      parent = parent[part]
    return parent
  for path in ("request_id", "intent.simulation_id", "intent.policy_id", "intent.evaluation_id",
               "requested_profile.profile_id"):
    value = nested(path)
    if not isinstance(value, str) or ID_RE.fullmatch(value) is None:
      _issue(issues, "projection.invalid_identifier", f"$.{path}", "expected stable identifier")
  for path in ("request_version", "requested_profile.profile_version",
               "contract_versions.composition", "contract_versions.runtime",
               "contract_versions.content", "contract_versions.stage"):
    value = nested(path)
    if not isinstance(value, str) or VERSION_RE.fullmatch(value) is None:
      _issue(issues, "projection.invalid_version", f"$.{path}", "expected semantic version")
  for field in ("required_capabilities", "required_policies"):
    _validate_string_array(request[field], f"$.{field}", issues)
  _validate_canonical_value(request["configuration"], "$.configuration", issues)
  try:
    low_level._normalize_value(request["configuration"], "$.configuration")
  except (TypeError, ValueError, UnicodeError, RecursionError) as error:
    _issue(issues, "projection.noncanonical_configuration", "$.configuration", str(error))
  return sorted(issues)


def validate_catalog_lock(lock: Any, *, check_identity: bool = True, request: Any | None = None) -> list[ValidationIssue]:
  issues: list[ValidationIssue] = []
  if not isinstance(lock, dict):
    return [ValidationIssue("projection.invalid_json_type", "$", "expected object")]
  required = {
    "schema_version", "contract_version", "lock_id", "lock_version", "request_schema_version",
    "request_sha256", "authority_registry_sha256", "category_authorities", "entries", "canonicalization", "hash_algorithm",
    "canonical_json", "lock_sha256",
  }
  for field in sorted(required - lock.keys()):
    _issue(issues, "projection.missing_field", f"$.{field}", "required field is missing")
  for field in sorted(lock.keys() - required):
    _issue(issues, "projection.unexpected_field", f"$.{field}", "field is not in v1 contract")
  if issues:
    return issues
  if lock["schema_version"] != LOCK_SCHEMA_VERSION:
    _issue(issues, "projection.unsupported_schema_version", "$.schema_version", LOCK_SCHEMA_VERSION)
  if lock["contract_version"] != LOCK_CONTRACT_VERSION:
    _issue(issues, "projection.unsupported_contract_version", "$.contract_version", LOCK_CONTRACT_VERSION)
  if lock["request_schema_version"] != REQUEST_SCHEMA_VERSION:
    _issue(issues, "projection.request_schema_mismatch", "$.request_schema_version", REQUEST_SCHEMA_VERSION)
  for field in ("lock_id",):
    if not isinstance(lock[field], str) or ID_RE.fullmatch(lock[field]) is None:
      _issue(issues, "projection.invalid_identifier", f"$.{field}", "expected stable identifier")
  if not isinstance(lock["lock_version"], str) or VERSION_RE.fullmatch(lock["lock_version"]) is None:
    _issue(issues, "projection.invalid_version", "$.lock_version", "expected semantic version")
  if not isinstance(lock["request_sha256"], str) or HEX64_RE.fullmatch(lock["request_sha256"]) is None:
    _issue(issues, "projection.invalid_identity", "$.request_sha256", "expected SHA-256")
  authority_registry = default_authority_registry()
  if not isinstance(lock["authority_registry_sha256"], str) or HEX64_RE.fullmatch(lock["authority_registry_sha256"]) is None:
    _issue(issues, "projection.invalid_identity", "$.authority_registry_sha256", "expected SHA-256")
  elif lock["authority_registry_sha256"] != authority_registry["registry_sha256"]:
    _issue(issues, "projection.authority_registry_mismatch", "$.authority_registry_sha256", "does not match repository authority registry")
  if lock["canonicalization"] != CANONICALIZATION_ID or lock["hash_algorithm"] != HASH_ALGORITHM:
    _issue(issues, "projection.invalid_identity", "$.canonicalization", "identity algorithm mismatch")
  if not isinstance(lock["canonical_json"], str):
    _issue(issues, "projection.invalid_json_type", "$.canonical_json", "expected string")
  if not isinstance(lock["lock_sha256"], str) or HEX64_RE.fullmatch(lock["lock_sha256"]) is None:
    _issue(issues, "projection.invalid_identity", "$.lock_sha256", "expected SHA-256")
  if request is not None:
    request_issues = validate_request(request)
    if request_issues:
      issues.extend(ValidationIssue(issue.code, f"$.request{issue.path[1:]}", issue.detail) for issue in request_issues)
    elif lock["request_sha256"] != request_identity(request):
      _issue(issues, "projection.request_identity_mismatch", "$.request_sha256", "does not match supplied request")
  authorities = lock["category_authorities"]
  entries = lock["entries"]
  if not isinstance(authorities, list) or not isinstance(entries, list) or not authorities or not entries:
    _issue(issues, "projection.invalid_json_type", "$.entries", "expected non-empty arrays")
    return sorted(issues)
  authority_map: dict[str, str] = {}
  for index, authority in enumerate(authorities):
    if not isinstance(authority, dict) or set(authority) != {"category", "owner_id"}:
      _issue(issues, "projection.invalid_authority", f"$.category_authorities[{index}]", "invalid authority")
      continue
    category, owner = authority["category"], authority["owner_id"]
    if not isinstance(category, str) or category not in CATEGORIES or not isinstance(owner, str) or ID_RE.fullmatch(owner) is None:
      _issue(issues, "projection.invalid_authority", f"$.category_authorities[{index}]", "invalid category or owner")
    elif owner != OWNER_AUTHORITY_BY_CATEGORY[category]:
      _issue(issues, "projection.owner_authority_mismatch", f"$.category_authorities[{index}].owner_id", "owner does not match repository authority")
    elif category in authority_map:
      _issue(issues, "projection.duplicate_value", f"$.category_authorities[{index}].category", "category has two owners")
    else:
      authority_map[category] = owner
  if set(authority_map) != set(CATEGORIES):
    _issue(issues, "projection.invalid_authority", "$.category_authorities", "authority list must cover every admitted category")
  seen_entries: set[tuple[str, str]] = set()
  for index, entry in enumerate(entries):
    path = f"$.entries[{index}]"
    expected = {"category", "owner_id", "descriptor_id", "implementation_id", "implementation_version", "capabilities", "provenance", "trust_decision"}
    if not isinstance(entry, dict) or set(entry) != expected:
      _issue(issues, "projection.invalid_entry", path, "invalid entry shape")
      continue
    category = entry["category"]
    descriptor_id = entry["descriptor_id"]
    key = (category, descriptor_id) if isinstance(category, str) and isinstance(descriptor_id, str) else None
    if not isinstance(category, str) or category not in CATEGORIES:
      _issue(issues, "projection.unknown_category", f"{path}.category", "category is not admitted in v1")
    if key is not None and key in seen_entries:
      _issue(issues, "projection.duplicate_entry", path, "descriptor is repeated")
    if key is not None:
      seen_entries.add(key)
    if isinstance(category, str) and authority_map.get(category) != entry["owner_id"]:
      _issue(issues, "projection.owner_mismatch", path, "entry owner does not match category authority")
    for field in ("owner_id", "descriptor_id", "implementation_id"):
      if not isinstance(entry[field], str) or ID_RE.fullmatch(entry[field]) is None:
        _issue(issues, "projection.invalid_identifier", f"{path}.{field}", "expected stable identifier")
    if not isinstance(entry["implementation_version"], str) or VERSION_RE.fullmatch(entry["implementation_version"]) is None:
      _issue(issues, "projection.invalid_version", f"{path}.implementation_version", "expected semantic version")
    _validate_string_array(entry["capabilities"], f"{path}.capabilities", issues)
    if entry["trust_decision"] not in TRUST_DECISIONS:
      _issue(issues, "projection.unadmitted_implementation", f"{path}.trust_decision", "only admitted entries may be locked")
    provenance = entry["provenance"]
    if not isinstance(provenance, dict) or set(provenance) != {"artifact_kind", "artifact_identity", "artifact_sha256"}:
      _issue(issues, "projection.invalid_provenance", f"{path}.provenance", "invalid provenance shape")
    elif (
      provenance["artifact_kind"] not in ARTIFACT_KINDS
      or not isinstance(provenance["artifact_identity"], str)
      or not provenance["artifact_identity"]
      or not provenance["artifact_identity"].isascii()
      or low_level._nfc(provenance["artifact_identity"]) != provenance["artifact_identity"]
    ):
      _issue(issues, "projection.invalid_provenance", f"{path}.provenance", "invalid artifact provenance")
    elif provenance["artifact_sha256"] is not None and (
      not isinstance(provenance["artifact_sha256"], str) or HEX64_RE.fullmatch(provenance["artifact_sha256"]) is None
    ):
      _issue(issues, "projection.invalid_provenance", f"{path}.provenance.artifact_sha256", "expected SHA-256 or null")
    elif provenance["artifact_kind"] in {"native_package", "cordis_package"} and (
      not isinstance(provenance["artifact_sha256"], str)
      or HEX64_RE.fullmatch(provenance["artifact_sha256"]) is None
    ):
      _issue(
        issues,
        "projection.provenance_hash_required",
        f"{path}.provenance.artifact_sha256",
        "native_package and cordis_package provenance must carry a SHA-256",
      )
  if request is not None and not any(issue.path.startswith("$.request") for issue in issues):
    locked_categories = {
      entry["category"] for entry in entries
      if isinstance(entry, dict) and isinstance(entry.get("category"), str)
    }
    missing_categories = sorted(set(CATEGORIES) - locked_categories)
    for category in missing_categories:
      _issue(
        issues,
        "projection.missing_category",
        "$.entries",
        f"request-bound lock must admit category {category}",
      )
    admitted_capabilities: set[str] = set()
    for entry in entries:
      if isinstance(entry, dict) and isinstance(entry.get("capabilities"), list):
        admitted_capabilities.update(
          capability for capability in entry["capabilities"] if isinstance(capability, str)
        )
    required_capabilities = request.get("required_capabilities", []) if isinstance(request, dict) else []
    if isinstance(required_capabilities, list):
      for capability in sorted(set(required_capabilities) - admitted_capabilities):
        _issue(
          issues,
          "projection.unmet_capability",
          "$.entries",
          f"request capability {capability} is not covered by the admitted catalog lock",
        )
  if not issues:
    try:
      normalized = normalize_lock(lock)
      if check_identity:
        expected_json = low_level.canonical_json_bytes(_lock_payload(normalized)).decode("utf-8")
        if lock["canonical_json"] != expected_json:
          _issue(issues, "projection.canonical_bytes_mismatch", "$.canonical_json", "does not match canonical lock payload")
        if lock["lock_sha256"] != low_level.canonical_sha256(_lock_payload(normalized)):
          _issue(issues, "projection.identity_mismatch", "$.lock_sha256", "does not match canonical lock payload")
    except (TypeError, ValueError, KeyError, UnicodeError) as error:
      _issue(issues, "projection.noncanonical_lock", "$", str(error))
  return sorted(issues)


def default_request() -> dict[str, Any]:
  return {
    "schema_version": REQUEST_SCHEMA_VERSION,
    "request_id": "default.experiment",
    "request_version": "1.0.0",
    "contract_versions": {"composition": "1.0.0", "runtime": "1.0.0", "content": "1.0.0", "stage": "1.0.0"},
    "intent": {"simulation_id": "default.simulation", "policy_id": "default.policy", "evaluation_id": "default.evaluation"},
    "requested_profile": {"profile_id": "builtin.default_compatibility", "profile_version": "1.0.0"},
    "required_capabilities": ["deterministic.step", "runtime.world_batch.cpu"],
    "required_policies": ["native_step_authority", "no_mid_episode_truth_reconfiguration"],
    "configuration": {"seed": 42, "time_step_ns": 16666667},
  }


def default_entries() -> list[dict[str, Any]]:
  def entry(
    category: str,
    owner: str,
    descriptor: str,
    implementation: str,
    capabilities: str | list[str],
  ) -> dict[str, Any]:
    capability_values = [capabilities] if isinstance(capabilities, str) else list(capabilities)
    return {
      "category": category,
      "owner_id": owner,
      "descriptor_id": descriptor,
      "implementation_id": implementation,
      "implementation_version": "1.0.0",
      "capabilities": capability_values,
      "provenance": {"artifact_kind": "repository_builtin", "artifact_identity": "echelon-forge-source-tree", "artifact_sha256": None},
      "trust_decision": "admitted",
    }
  return [
    entry("model", "owner.model", "builtin.default.models", "echelon_forge.native_builtin", "simulation.model.default"),
    entry(
      "system",
      "owner.scheduler",
      "builtin.default.system_graph",
      "echelon_forge.native_builtin",
      ["deterministic.step", "simulation.system.default"],
    ),
    entry("backend", "owner.backend", "builtin.backend.flecs_cpu", "echelon_forge.native_builtin", "runtime.world_batch.cpu"),
    entry("domain", "owner.domain", "builtin.domain.combined", "echelon_forge.native_builtin", "domain.combined"),
    entry("evidence", "owner.evidence", "builtin.composition.evidence", "echelon_forge.native_builtin", "runtime.composition.evidence"),
    entry("security", "owner.security", "builtin.repository.admission", "echelon_forge.native_builtin", "runtime.repository_builtin"),
  ]


def build_catalog_lock(request: dict[str, Any], entries: list[dict[str, Any]], *, lock_id: str = "default.admitted_catalog", lock_version: str = "1.0.0") -> dict[str, Any]:
  issues = validate_request(request)
  if issues:
    raise ContractError(issues)
  if not isinstance(entries, list) or not entries:
    raise ContractError([ValidationIssue("projection.invalid_json_type", "$.entries", "expected non-empty array")])
  normalized_entries: list[dict[str, Any]] = []
  entry_issues: list[ValidationIssue] = []
  expected_entry_fields = {
    "category", "owner_id", "descriptor_id", "implementation_id",
    "implementation_version", "capabilities", "provenance", "trust_decision",
  }
  for index, row in enumerate(entries):
    path = f"$.entries[{index}]"
    if not isinstance(row, dict):
      entry_issues.append(ValidationIssue("projection.invalid_entry", path, "expected object"))
      continue
    try:
      normalized = _normalize_entry(row)
    except (TypeError, ValueError, KeyError, OverflowError, UnicodeError) as error:
      entry_issues.append(ValidationIssue("projection.invalid_entry", path, str(error)))
      continue
    if set(normalized) != expected_entry_fields:
      entry_issues.append(ValidationIssue("projection.invalid_entry", path, "invalid entry shape"))
      continue
    if not isinstance(normalized["category"], str) or not isinstance(normalized["owner_id"], str):
      entry_issues.append(ValidationIssue("projection.invalid_entry", path, "category and owner_id must be strings"))
      continue
    normalized_entries.append(normalized)
  if entry_issues:
    raise ContractError(sorted(entry_issues))
  categories = sorted({row["category"] for row in normalized_entries}, key=lambda value: value.encode("utf-8"))
  unknown_categories = sorted(set(categories) - set(CATEGORIES))
  if unknown_categories:
    raise ContractError([ValidationIssue("projection.unknown_category", "$.entries", f"unknown category: {category}") for category in unknown_categories])
  invalid_owners = [
    ValidationIssue("projection.owner_authority_mismatch", f"$.entries[{index}].owner_id", "owner does not match repository authority")
    for index, row in enumerate(normalized_entries)
    if row["owner_id"] != OWNER_AUTHORITY_BY_CATEGORY[row["category"]]
  ]
  if invalid_owners:
    raise ContractError(invalid_owners)
  authorities = [
    {"category": category, "owner_id": OWNER_AUTHORITY_BY_CATEGORY[category]}
    for category in CATEGORIES
  ]
  authority_registry = default_authority_registry()
  payload: dict[str, Any] = {
    "schema_version": LOCK_SCHEMA_VERSION,
    "contract_version": LOCK_CONTRACT_VERSION,
    "lock_id": lock_id,
    "lock_version": lock_version,
    "request_schema_version": REQUEST_SCHEMA_VERSION,
    "request_sha256": request_identity(request),
    "authority_registry_sha256": authority_registry["registry_sha256"],
    "category_authorities": authorities,
    "entries": normalized_entries,
    "canonicalization": CANONICALIZATION_ID,
    "hash_algorithm": HASH_ALGORITHM,
  }
  candidate = payload | {"canonical_json": "", "lock_sha256": "0" * 64}
  issues = validate_catalog_lock(candidate, check_identity=False, request=request)
  if issues:
    raise ContractError(issues)
  normalized = normalize_lock(payload | {"canonical_json": "", "lock_sha256": ""})
  payload["canonical_json"] = low_level.canonical_json_bytes(_lock_payload(normalized)).decode("utf-8")
  payload["lock_sha256"] = low_level.canonical_sha256(_lock_payload(normalized))
  return normalize_lock(payload)


def _pretty(value: Any) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def generate() -> None:
  request = _normalize_request(default_request())
  authority_registry = default_authority_registry()
  lock = build_catalog_lock(request, default_entries())
  REQUEST_SCHEMA_PATH.write_text(_pretty(request_schema()), encoding="utf-8", newline="\n")
  LOCK_SCHEMA_PATH.write_text(_pretty(lock_schema()), encoding="utf-8", newline="\n")
  AUTHORITY_SCHEMA_PATH.write_text(_pretty(authority_registry_schema()), encoding="utf-8", newline="\n")
  REQUEST_FIXTURE_PATH.write_text(_pretty(request), encoding="utf-8", newline="\n")
  LOCK_FIXTURE_PATH.write_text(_pretty(lock), encoding="utf-8", newline="\n")
  AUTHORITY_FIXTURE_PATH.write_text(_pretty(authority_registry), encoding="utf-8", newline="\n")
  INVALID_MATRIX_PATH.write_text(_pretty({
    "request_fixture": REQUEST_FIXTURE_PATH.name,
    "lock_fixture": LOCK_FIXTURE_PATH.name,
    "cases": [
      {"id": "request_unknown_field", "artifact": "request", "path": "/unknown", "value": True, "code": "projection.unexpected_field"},
      {"id": "request_duplicate_capability", "artifact": "request", "path": "/required_capabilities", "value": ["deterministic.step", "deterministic.step"], "code": "projection.duplicate_value"},
      {"id": "lock_unknown_category", "artifact": "lock", "path": "/entries/0/category", "value": "plugin", "code": "projection.unknown_category"},
      {"id": "lock_owner_mismatch", "artifact": "lock", "path": "/entries/0/owner_id", "value": "owner.other", "code": "projection.owner_mismatch"},
      {"id": "lock_unadmitted", "artifact": "lock", "path": "/entries/0/trust_decision", "value": "quarantined", "code": "projection.unadmitted_implementation"},
      {"id": "lock_identity_mismatch", "artifact": "lock", "path": "/lock_sha256", "value": "0" * 64, "code": "projection.identity_mismatch"},
    ],
  }), encoding="utf-8", newline="\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("command", choices=("generate", "validate"))
  parser.add_argument("--request", type=Path)
  parser.add_argument("--lock", type=Path)
  return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  args = parse_args(argv)
  if args.command == "generate":
    generate()
    return 0
  if args.request is None or args.lock is None:
    raise SystemExit("validate requires --request and --lock")
  try:
    request = json.loads(args.request.read_text(encoding="utf-8"))
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
  except (OSError, UnicodeError, json.JSONDecodeError) as error:
    print(f"projection.input_error: {error}")
    return 2
  issues = validate_request(request) + validate_catalog_lock(lock, request=request)
  if issues:
    for issue in sorted(issues):
      print(f"{issue.code}@{issue.path}: {issue.detail}")
    return 1
  print(request_identity(request))
  print(catalog_lock_identity(lock))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
