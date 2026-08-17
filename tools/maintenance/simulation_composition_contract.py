#!/usr/bin/env python3
"""Generate and validate the host-neutral simulation composition contract.

This module is the P1-B executable specification.  It owns schema generation,
normalization, stable diagnostics, deterministic dependency ordering, and the
default pre-migration compatibility fixture.  It does not construct runtime
providers or execute simulation stages.
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
import unicodedata
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "echelon_forge.simulation_composition_manifest.v1"
RESOLVED_SCHEMA_VERSION = "echelon_forge.resolved_simulation_composition.v1"
COMPOSITION_CONTRACT_VERSION = "1.0.0"
RESOLVER_CONTRACT_VERSION = "echelon_forge.simulation_composition_resolver.v1"
CANONICALIZATION_ID = "echelon_forge.sorted_utf8_json.v1"
HASH_ALGORITHM = "sha256"
BACKEND_SERVICE_KEY = "runtime.world_batch_backend"

SCHEMA_PATH = (
  REPO_ROOT
  / "src/runtime/contracts/composition/simulation_composition_manifest.v1.schema.json"
)
REQUESTED_FIXTURE_PATH = (
  REPO_ROOT
  / "tests/architecture/composition/fixtures/default_compatibility_manifest.requested.json"
)
RESOLVED_FIXTURE_PATH = (
  REPO_ROOT
  / "tests/architecture/composition/fixtures/default_compatibility_manifest.resolved.json"
)
RESOLVED_SCHEMA_PATH = (
  REPO_ROOT
  / "src/runtime/contracts/composition/resolved_simulation_composition.v1.schema.json"
)

ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
ASCII_PATTERN = r"^[\u0000-\u007F]*$"
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1

SCOPE_ORDER = ("application", "backend", "batch", "world", "episode")
SCOPE_PARENT = {
  "application": None,
  "backend": "application",
  "batch": "backend",
  "world": "batch",
  "episode": "world",
}

SERVICE_KEYS = (
  "simulation.environment.model",
  "simulation.unit_factory",
  "simulation.effects.model",
  "simulation.sensor.model",
  "simulation.acoustic.model",
  "simulation.control.model",
  "simulation.guidance.model",
  "runtime.engagement_event_recorder",
  "runtime.weapon_release.damage_bridge",
  "runtime.weapon_release.service",
  BACKEND_SERVICE_KEY,
  "runtime.composition_evidence_sink",
)

ERROR_CODES = (
  "composition.invalid_json_type",
  "composition.unsupported_schema_version",
  "composition.missing_field",
  "composition.unexpected_field",
  "composition.invalid_identifier",
  "composition.invalid_version",
  "composition.duplicate_id",
  "composition.duplicate_value",
  "composition.unknown_plugin",
  "composition.unknown_provider",
  "composition.unknown_consumer",
  "composition.unknown_service",
  "composition.service_not_offered",
  "composition.missing_service_binding",
  "composition.ambiguous_service_binding",
  "composition.scope_capture_violation",
  "composition.provider_conflict",
  "composition.provider_dependency_cycle",
  "composition.unknown_component",
  "composition.unknown_system_dependency",
  "composition.system_conflict",
  "composition.system_dependency_cycle",
  "composition.backend_provider_mismatch",
  "composition.invalid_scope_policy",
  "composition.invalid_reconfiguration_policy",
  "composition.invalid_evidence_policy",
  "composition.noncanonical_number",
)


@dataclass(frozen=True, order=True)
class ValidationIssue:
  code: str
  path: str
  detail: str

  def to_dict(self) -> dict[str, str]:
    return {"code": self.code, "path": self.path, "detail": self.detail}


class ContractError(ValueError):
  """Raised when resolution is requested for an invalid manifest."""

  def __init__(self, issues: Iterable[ValidationIssue]):
    self.issues = tuple(sorted(issues))
    super().__init__("; ".join(f"{row.code}@{row.path}" for row in self.issues))


def _object_schema(
  properties: dict[str, Any],
  *,
  required: Iterable[str] | None = None,
) -> dict[str, Any]:
  return {
    "type": "object",
    "additionalProperties": False,
    "properties": properties,
    "required": list(required if required is not None else properties),
  }


def _string_schema(
  *,
  pattern: str | None = None,
  enum: Iterable[str] | None = None,
  max_length: int | None = None,
) -> dict[str, Any]:
  schema: dict[str, Any] = {"type": "string", "minLength": 1}
  if pattern is not None:
    schema["pattern"] = pattern
  else:
    schema["pattern"] = ASCII_PATTERN
  if enum is not None:
    schema["enum"] = list(enum)
  if max_length is not None:
    schema["maxLength"] = max_length
  return schema


def _string_array(*, min_items: int = 0) -> dict[str, Any]:
  return {
    "type": "array",
    "items": _string_schema(),
    "minItems": min_items,
    "uniqueItems": True,
  }


def manifest_schema() -> dict[str, Any]:
  identifier = _string_schema(pattern=ID_RE.pattern, max_length=128)
  version = _string_schema(pattern=VERSION_RE.pattern)
  canonical_value: dict[str, Any] = {
    "oneOf": [
      {"type": "null"},
      {"type": "boolean"},
      {"type": "integer", "minimum": INT64_MIN, "maximum": INT64_MAX},
      {"type": "string", "pattern": ASCII_PATTERN},
      {"type": "array", "items": {"$ref": "#/$defs/canonical_value"}},
      {
        "type": "object",
        "propertyNames": {"pattern": ASCII_PATTERN},
        "additionalProperties": {"$ref": "#/$defs/canonical_value"},
      },
    ]
  }

  plugin = _object_schema(
    {
      "plugin_id": identifier,
      "implementation_id": identifier,
      "plugin_version": version,
      "composition_contract_range": _string_schema(),
      "host_support": {
        "type": "array",
        "items": {"enum": ["native", "cordis"]},
        "minItems": 1,
        "uniqueItems": True,
      },
      "determinism_class": {
        "enum": ["truth_affecting_deterministic", "diagnostics_only"]
      },
      "artifact": _object_schema(
        {
          "kind": {"enum": ["repository_builtin", "native_package", "cordis_package"]},
          "identity": _string_schema(),
          "sha256": {"type": ["string", "null"], "pattern": HEX64_RE.pattern},
        }
      ),
      "required_capabilities": _string_array(),
      "conflicts": _string_array(),
      "configuration": {"$ref": "#/$defs/canonical_value"},
    }
  )

  provider = _object_schema(
    {
      "provider_id": identifier,
      "plugin_id": identifier,
      "implementation_version": version,
      "scope": {"enum": list(SCOPE_ORDER)},
      "cardinality": {"enum": ["one_per_scope"]},
      "offered_services": _string_array(min_items=1),
      "required_services": _string_array(),
      "required_capabilities": _string_array(),
      "conflicts": _string_array(),
      "after_provider_ids": _string_array(),
      "restart_policy": {
        "enum": ["rebuild_scope_generation", "process_restart", "diagnostics_restart"]
      },
      "teardown_policy": {"enum": ["reverse_dependency_order"]},
      "configuration": {"$ref": "#/$defs/canonical_value"},
    }
  )

  service_binding = _object_schema(
    {
      "consumer_kind": {"enum": ["provider", "system"]},
      "consumer_id": identifier,
      "service_key": _string_schema(),
      "provider_id": identifier,
    }
  )

  component = _object_schema(
    {
      "component_id": _string_schema(),
      "plugin_id": identifier,
      "registration_id": identifier,
    }
  )

  system = _object_schema(
    {
      "contribution_id": identifier,
      "plugin_id": identifier,
      "registration_factory_id": identifier,
      "domain": {
        "enum": ["common", "air", "naval", "ground", "cross_domain", "diagnostics"]
      },
      "required_services": _string_array(),
      "required_components": _string_array(),
      "provided_components": _string_array(),
      "semantic_stage_ids": _string_array(),
      "executable_node_ids": _string_array(),
      "read_state_shards": _string_array(),
      "write_state_shards": _string_array(),
      "required_barriers": _string_array(),
      "required_capabilities": _string_array(),
      "conflicts": _string_array(),
      "after": _string_array(),
      "before": _string_array(),
    }
  )

  scope_policy = _object_schema(
    {
      "scope": {"enum": list(SCOPE_ORDER)},
      "parent_scope": {"type": ["string", "null"], "enum": [*SCOPE_ORDER, None]},
      "cardinality": {"enum": ["singleton", "one_per_parent"]},
      "rebuild_trigger": _string_schema(),
    }
  )

  schema = _object_schema(
    {
      "schema_version": {"const": SCHEMA_VERSION},
      "composition_id": identifier,
      "contract_versions": _object_schema(
        {
          "composition": {"const": COMPOSITION_CONTRACT_VERSION},
          "runtime": version,
          "content": version,
          "stage": version,
        }
      ),
      "requested_profile": _object_schema(
        {"profile_id": identifier, "profile_version": version}
      ),
      "plugins": {"type": "array", "items": plugin, "minItems": 1},
      "providers": {"type": "array", "items": provider, "minItems": 1},
      "service_bindings": {"type": "array", "items": service_binding},
      "component_contributions": {"type": "array", "items": component},
      "system_contributions": {"type": "array", "items": system},
      "backend_request": _object_schema(
        {
          "backend_profile_id": identifier,
          "provider_id": identifier,
          "required_capabilities": _string_array(),
        }
      ),
      "scope_policies": {
        "type": "array",
        "items": scope_policy,
        "minItems": len(SCOPE_ORDER),
        "maxItems": len(SCOPE_ORDER),
      },
      "reconfiguration_policy": _object_schema(
        {
          "truth_affecting_change": {"const": "rebuild_scope_generation"},
          "active_episode_change": {"const": "forbidden"},
          "allowed_barriers": _string_array(min_items=1),
        }
      ),
      "evidence_policy": _object_schema(
        {
          "canonicalization": {"const": CANONICALIZATION_ID},
          "hash_algorithm": {"const": HASH_ALGORITHM},
          "include_provider_versions": {"const": True},
          "include_graph_hash": {"const": True},
          "include_scope_generations": {"const": True},
        }
      ),
      "compatibility_claims": _string_array(),
    }
  )
  schema.update(
    {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": (
        "https://echelon-forge.local/contracts/"
        "simulation_composition_manifest.v1.schema.json"
      ),
      "title": "Echelon Forge Simulation Composition Manifest v1",
      "$comment": (
        "JSON Schema treats 1.0 as an integer by mathematical value. Consumers MUST also run "
        "the executable lexical-number validator, which rejects fraction/exponent tokens. "
        "The v1 native admission subset accepts ASCII text only; ASCII is already NFC, while "
        "full Unicode NFC admission remains closed until every producer links one normalizer."
      ),
      "$defs": {"canonical_value": canonical_value},
    }
  )
  return schema


def resolved_schema() -> dict[str, Any]:
  manifest = manifest_schema()
  manifest.pop("$schema", None)
  manifest.pop("$id", None)
  manifest.pop("title", None)
  manifest.pop("$comment", None)
  definitions = manifest.pop("$defs")
  return {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": (
      "https://echelon-forge.local/contracts/"
      "resolved_simulation_composition.v1.schema.json"
    ),
    "title": "Echelon Forge Resolved Simulation Composition v1",
    "$defs": definitions,
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "schema_version": {"const": RESOLVED_SCHEMA_VERSION},
      "resolver_contract_version": {"const": RESOLVER_CONTRACT_VERSION},
      "requested_manifest_sha256": {"type": "string", "pattern": HEX64_RE.pattern},
      "resolved_manifest_sha256": {"type": "string", "pattern": HEX64_RE.pattern},
      "provider_construction_order": _string_array(),
      "system_registration_order": _string_array(),
      "manifest": manifest,
    },
    "required": [
      "schema_version",
      "resolver_contract_version",
      "requested_manifest_sha256",
      "resolved_manifest_sha256",
      "provider_construction_order",
      "system_registration_order",
      "manifest",
    ],
  }


def _nfc(value: str) -> str:
  return unicodedata.normalize("NFC", value)


def _normalize_value(value: Any, path: str = "$.") -> Any:
  if value is None or isinstance(value, bool):
    return value
  if isinstance(value, int):
    if not INT64_MIN <= value <= INT64_MAX:
      raise ValueError(f"integer outside signed 64-bit range at {path}")
    return value
  if isinstance(value, float):
    raise ValueError(f"floating-point values are forbidden at {path}")
  if isinstance(value, str):
    return _nfc(value)
  if isinstance(value, list):
    return [_normalize_value(item, f"{path}[]") for item in value]
  if isinstance(value, dict):
    normalized: dict[str, Any] = {}
    for key, item in value.items():
      if not isinstance(key, str):
        raise ValueError(f"non-string object key at {path}")
      normalized_key = _nfc(key)
      if normalized_key in normalized:
        raise ValueError(f"Unicode NFC object-key collision at {path}.{key}")
      normalized[normalized_key] = _normalize_value(item, f"{path}.{key}")
    return normalized
  raise ValueError(f"unsupported JSON type {type(value).__name__} at {path}")


def _sorted_unique_strings(values: Any) -> list[str]:
  if not isinstance(values, list):
    return values
  normalized = [_nfc(value) for value in values]
  if len(set(normalized)) != len(normalized):
    raise ValueError("duplicate string after Unicode NFC normalization")
  return sorted(normalized, key=lambda value: value.encode("utf-8"))


def normalize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
  normalized = _normalize_value(deepcopy(manifest), "$")

  for plugin in normalized.get("plugins", []):
    for field in ("host_support", "required_capabilities", "conflicts"):
      plugin[field] = _sorted_unique_strings(plugin.get(field, []))
  normalized["plugins"] = sorted(
    normalized.get("plugins", []), key=lambda row: row.get("plugin_id", "").encode("utf-8")
  )

  for provider in normalized.get("providers", []):
    for field in (
      "offered_services",
      "required_services",
      "required_capabilities",
      "conflicts",
      "after_provider_ids",
    ):
      provider[field] = _sorted_unique_strings(provider.get(field, []))
  normalized["providers"] = sorted(
    normalized.get("providers", []),
    key=lambda row: row.get("provider_id", "").encode("utf-8"),
  )

  normalized["service_bindings"] = sorted(
    normalized.get("service_bindings", []),
    key=lambda row: (
      row.get("consumer_kind", "").encode("utf-8"),
      row.get("consumer_id", "").encode("utf-8"),
      row.get("service_key", "").encode("utf-8"),
      row.get("provider_id", "").encode("utf-8"),
    ),
  )
  normalized["component_contributions"] = sorted(
    normalized.get("component_contributions", []),
    key=lambda row: row.get("component_id", "").encode("utf-8"),
  )

  set_fields = (
    "required_services",
    "required_components",
    "provided_components",
    "semantic_stage_ids",
    "executable_node_ids",
    "read_state_shards",
    "write_state_shards",
    "required_barriers",
    "required_capabilities",
    "conflicts",
    "after",
    "before",
  )
  for system in normalized.get("system_contributions", []):
    for field in set_fields:
      system[field] = _sorted_unique_strings(system.get(field, []))
  normalized["system_contributions"] = sorted(
    normalized.get("system_contributions", []),
    key=lambda row: row.get("contribution_id", "").encode("utf-8"),
  )

  normalized["scope_policies"] = sorted(
    normalized.get("scope_policies", []),
    key=lambda row: SCOPE_ORDER.index(row.get("scope"))
    if row.get("scope") in SCOPE_ORDER
    else len(SCOPE_ORDER),
  )
  if isinstance(normalized.get("backend_request"), dict):
    normalized["backend_request"]["required_capabilities"] = _sorted_unique_strings(
      normalized["backend_request"].get("required_capabilities", [])
    )
  if isinstance(normalized.get("reconfiguration_policy"), dict):
    normalized["reconfiguration_policy"]["allowed_barriers"] = _sorted_unique_strings(
      normalized["reconfiguration_policy"].get("allowed_barriers", [])
    )
  normalized["compatibility_claims"] = _sorted_unique_strings(
    normalized.get("compatibility_claims", [])
  )
  return normalized


def canonical_json_bytes(value: Any) -> bytes:
  normalized = _normalize_value(value, "$")
  return json.dumps(
    normalized,
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
  ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
  return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _issue(issues: list[ValidationIssue], code: str, path: str, detail: Any) -> None:
  issues.append(ValidationIssue(str(code), str(path), str(detail)))


def _validate_ascii_text(issues: list[ValidationIssue], value: Any, path: str) -> None:
  if isinstance(value, str):
    if not value.isascii():
      _issue(
        issues,
        "composition.invalid_json_type",
        path,
        "v1 native admission accepts ASCII text only",
      )
    return
  if isinstance(value, list):
    for index, item in enumerate(value):
      _validate_ascii_text(issues, item, f"{path}[{index}]")
    return
  if isinstance(value, dict):
    for key, item in value.items():
      if isinstance(key, str) and not key.isascii():
        _issue(
          issues,
          "composition.invalid_json_type",
          path,
          "v1 native admission accepts ASCII object keys only",
        )
      _validate_ascii_text(issues, item, f"{path}.{key}")


def _validate_identifier(
  issues: list[ValidationIssue], value: Any, path: str, *, version: bool = False
) -> None:
  if not isinstance(value, str) or not value:
    _issue(issues, "composition.invalid_json_type", path, "expected non-empty string")
    return
  pattern = VERSION_RE if version else ID_RE
  if pattern.fullmatch(value) is None:
    code = "composition.invalid_version" if version else "composition.invalid_identifier"
    _issue(issues, code, path, f"value {value!r} does not match {pattern.pattern}")
  elif not version and len(value) > 128:
    _issue(issues, "composition.invalid_identifier", path, "identifier exceeds 128 characters")


def _validate_unique(
  issues: list[ValidationIssue], values: Any, path: str, *, code: str = "composition.duplicate_value"
) -> None:
  if not isinstance(values, list):
    _issue(issues, "composition.invalid_json_type", path, "expected array")
    return
  seen: set[Any] = set()
  for index, value in enumerate(values):
    marker_value = _nfc(value) if isinstance(value, str) else value
    marker = json.dumps(marker_value, sort_keys=True, ensure_ascii=False)
    if marker in seen:
      detail = (
        f"duplicate value {value!r} after Unicode NFC normalization"
        if isinstance(value, str)
        else f"duplicate value {value!r}"
      )
      _issue(issues, code, f"{path}[{index}]", detail)
    seen.add(marker)


def _validate_string_array(
  issues: list[ValidationIssue],
  values: Any,
  path: str,
  *,
  min_items: int = 0,
  allowed: set[str] | None = None,
) -> bool:
  if not isinstance(values, list):
    _issue(issues, "composition.invalid_json_type", path, "expected array")
    return False
  if len(values) < min_items:
    _issue(issues, "composition.invalid_json_type", path, f"expected at least {min_items} entries")
  valid = True
  normalized_seen: set[str] = set()
  for index, value in enumerate(values):
    item_path = f"{path}[{index}]"
    if not isinstance(value, str) or not value:
      _issue(issues, "composition.invalid_json_type", item_path, "expected non-empty string")
      valid = False
      continue
    normalized = _nfc(value)
    if normalized in normalized_seen:
      _issue(issues, "composition.duplicate_value", item_path, "duplicate after Unicode NFC")
      valid = False
    normalized_seen.add(normalized)
    if allowed is not None and value not in allowed:
      _issue(issues, "composition.invalid_json_type", item_path, f"unsupported value {value!r}")
      valid = False
  _validate_unique(issues, values, path)
  return valid


def _required_fields(
  issues: list[ValidationIssue], value: Any, path: str, expected: set[str]
) -> bool:
  if not isinstance(value, dict):
    _issue(issues, "composition.invalid_json_type", path, "expected object")
    return False
  for field in sorted(expected - set(value)):
    _issue(issues, "composition.missing_field", f"{path}.{field}", "field is required")
  for field in sorted(set(value) - expected):
    _issue(issues, "composition.unexpected_field", f"{path}.{field}", "field is not allowed")
  return expected <= set(value)


def _scope_can_supply(provider_scope: str, consumer_scope: str) -> bool:
  if provider_scope not in SCOPE_ORDER or consumer_scope not in SCOPE_ORDER:
    return False
  return SCOPE_ORDER.index(provider_scope) <= SCOPE_ORDER.index(consumer_scope)


def _stable_topological_order(
  node_ids: Iterable[str], edges: Iterable[tuple[str, str]]
) -> tuple[list[str], list[str]]:
  nodes = sorted(set(node_ids), key=lambda value: value.encode("utf-8"))
  successors = {node: set() for node in nodes}
  indegree = {node: 0 for node in nodes}
  for source, target in sorted(set(edges)):
    if source not in indegree or target not in indegree:
      continue
    if target not in successors[source]:
      successors[source].add(target)
      indegree[target] += 1

  ready = sorted(
    (node for node in nodes if indegree[node] == 0), key=lambda value: value.encode("utf-8")
  )
  order: list[str] = []
  while ready:
    node = ready.pop(0)
    order.append(node)
    for successor in sorted(successors[node], key=lambda value: value.encode("utf-8")):
      indegree[successor] -= 1
      if indegree[successor] == 0:
        ready.append(successor)
        ready.sort(key=lambda value: value.encode("utf-8"))
  cycle = sorted(
    (node for node in nodes if indegree[node] > 0), key=lambda value: value.encode("utf-8")
  )
  return order, cycle


def _validate_manifest_impl(manifest: Any) -> list[ValidationIssue]:
  issues: list[ValidationIssue] = []
  top_fields = {
    "schema_version",
    "composition_id",
    "contract_versions",
    "requested_profile",
    "plugins",
    "providers",
    "service_bindings",
    "component_contributions",
    "system_contributions",
    "backend_request",
    "scope_policies",
    "reconfiguration_policy",
    "evidence_policy",
    "compatibility_claims",
  }
  if not _required_fields(issues, manifest, "$", top_fields):
    return sorted(issues)
  _validate_ascii_text(issues, manifest, "$")

  if manifest["schema_version"] != SCHEMA_VERSION:
    _issue(
      issues,
      "composition.unsupported_schema_version",
      "$.schema_version",
      f"expected {SCHEMA_VERSION}",
    )
  _validate_identifier(issues, manifest["composition_id"], "$.composition_id")

  contract_fields = {"composition", "runtime", "content", "stage"}
  if _required_fields(issues, manifest["contract_versions"], "$.contract_versions", contract_fields):
    for field in sorted(contract_fields):
      _validate_identifier(
        issues,
        manifest["contract_versions"][field],
        f"$.contract_versions.{field}",
        version=True,
      )
    if manifest["contract_versions"]["composition"] != COMPOSITION_CONTRACT_VERSION:
      _issue(
        issues,
        "composition.unsupported_schema_version",
        "$.contract_versions.composition",
        f"expected {COMPOSITION_CONTRACT_VERSION}",
      )

  profile_fields = {"profile_id", "profile_version"}
  if _required_fields(issues, manifest["requested_profile"], "$.requested_profile", profile_fields):
    _validate_identifier(issues, manifest["requested_profile"]["profile_id"], "$.requested_profile.profile_id")
    _validate_identifier(
      issues,
      manifest["requested_profile"]["profile_version"],
      "$.requested_profile.profile_version",
      version=True,
    )

  plugin_fields = {
    "plugin_id",
    "implementation_id",
    "plugin_version",
    "composition_contract_range",
    "host_support",
    "determinism_class",
    "artifact",
    "required_capabilities",
    "conflicts",
    "configuration",
  }
  provider_fields = {
    "provider_id",
    "plugin_id",
    "implementation_version",
    "scope",
    "cardinality",
    "offered_services",
    "required_services",
    "required_capabilities",
    "conflicts",
    "after_provider_ids",
    "restart_policy",
    "teardown_policy",
    "configuration",
  }
  binding_fields = {"consumer_kind", "consumer_id", "service_key", "provider_id"}
  component_fields = {"component_id", "plugin_id", "registration_id"}
  system_fields = {
    "contribution_id",
    "plugin_id",
    "registration_factory_id",
    "domain",
    "required_services",
    "required_components",
    "provided_components",
    "semantic_stage_ids",
    "executable_node_ids",
    "read_state_shards",
    "write_state_shards",
    "required_barriers",
    "required_capabilities",
    "conflicts",
    "after",
    "before",
  }

  plugins = manifest["plugins"] if isinstance(manifest["plugins"], list) else []
  providers = manifest["providers"] if isinstance(manifest["providers"], list) else []
  bindings = (
    manifest["service_bindings"] if isinstance(manifest["service_bindings"], list) else []
  )
  components = (
    manifest["component_contributions"]
    if isinstance(manifest["component_contributions"], list)
    else []
  )
  systems = (
    manifest["system_contributions"]
    if isinstance(manifest["system_contributions"], list)
    else []
  )

  if not isinstance(manifest["plugins"], list):
    _issue(issues, "composition.invalid_json_type", "$.plugins", "expected array")
  if not isinstance(manifest["providers"], list):
    _issue(issues, "composition.invalid_json_type", "$.providers", "expected array")
  for field in (
    "service_bindings",
    "component_contributions",
    "system_contributions",
    "scope_policies",
  ):
    if not isinstance(manifest[field], list):
      _issue(issues, "composition.invalid_json_type", f"$.{field}", "expected array")

  plugin_ids: list[str] = []
  for index, plugin in enumerate(plugins):
    path = f"$.plugins[{index}]"
    if not _required_fields(issues, plugin, path, plugin_fields):
      continue
    _validate_identifier(issues, plugin["plugin_id"], f"{path}.plugin_id")
    _validate_identifier(issues, plugin["implementation_id"], f"{path}.implementation_id")
    _validate_identifier(issues, plugin["plugin_version"], f"{path}.plugin_version", version=True)
    if isinstance(plugin["plugin_id"], str):
      plugin_ids.append(plugin["plugin_id"])
    if not isinstance(plugin["composition_contract_range"], str) or not plugin[
      "composition_contract_range"
    ]:
      _issue(
        issues,
        "composition.invalid_json_type",
        f"{path}.composition_contract_range",
        "expected non-empty string",
      )
    _validate_string_array(
      issues,
      plugin["host_support"],
      f"{path}.host_support",
      min_items=1,
      allowed={"native", "cordis"},
    )
    for field in ("required_capabilities", "conflicts"):
      _validate_string_array(issues, plugin[field], f"{path}.{field}")
    if plugin["determinism_class"] not in {
      "truth_affecting_deterministic",
      "diagnostics_only",
    }:
      _issue(
        issues,
        "composition.invalid_json_type",
        f"{path}.determinism_class",
        "unknown determinism class",
      )
    artifact_fields = {"kind", "identity", "sha256"}
    if _required_fields(issues, plugin["artifact"], f"{path}.artifact", artifact_fields):
      artifact = plugin["artifact"]
      if artifact["kind"] not in {"repository_builtin", "native_package", "cordis_package"}:
        _issue(issues, "composition.invalid_json_type", f"{path}.artifact.kind", artifact["kind"])
      if not isinstance(artifact["identity"], str) or not artifact["identity"]:
        _issue(
          issues,
          "composition.invalid_json_type",
          f"{path}.artifact.identity",
          "expected non-empty string",
        )
      if artifact["sha256"] is not None and (
        not isinstance(artifact["sha256"], str) or HEX64_RE.fullmatch(artifact["sha256"]) is None
      ):
        _issue(issues, "composition.invalid_identifier", f"{path}.artifact.sha256", "expected SHA-256")
    try:
      _normalize_value(plugin["configuration"], f"{path}.configuration")
    except ValueError as exc:
      _issue(issues, "composition.noncanonical_number", f"{path}.configuration", str(exc))
  _validate_unique(issues, plugin_ids, "$.plugins", code="composition.duplicate_id")
  plugin_set = set(plugin_ids)

  provider_ids: list[str] = []
  provider_by_id: dict[str, dict[str, Any]] = {}
  offered_by_provider: dict[str, set[str]] = {}
  provider_edges: list[tuple[str, str]] = []
  for index, provider in enumerate(providers):
    path = f"$.providers[{index}]"
    if not _required_fields(issues, provider, path, provider_fields):
      continue
    provider_id = provider["provider_id"]
    _validate_identifier(issues, provider_id, f"{path}.provider_id")
    _validate_identifier(issues, provider["plugin_id"], f"{path}.plugin_id")
    _validate_identifier(
      issues, provider["implementation_version"], f"{path}.implementation_version", version=True
    )
    if isinstance(provider_id, str):
      provider_ids.append(provider_id)
      provider_by_id.setdefault(provider_id, provider)
    if provider["plugin_id"] not in plugin_set:
      _issue(issues, "composition.unknown_plugin", f"{path}.plugin_id", provider["plugin_id"])
    if provider["scope"] not in SCOPE_ORDER:
      _issue(issues, "composition.invalid_scope_policy", f"{path}.scope", provider["scope"])
    if provider["cardinality"] != "one_per_scope":
      _issue(issues, "composition.invalid_scope_policy", f"{path}.cardinality", provider_id)
    if provider["restart_policy"] not in {
      "rebuild_scope_generation",
      "process_restart",
      "diagnostics_restart",
    }:
      _issue(issues, "composition.invalid_json_type", f"{path}.restart_policy", provider_id)
    if provider["teardown_policy"] != "reverse_dependency_order":
      _issue(issues, "composition.invalid_json_type", f"{path}.teardown_policy", provider_id)
    array_fields = (
      "offered_services",
      "required_services",
      "required_capabilities",
      "conflicts",
      "after_provider_ids",
    )
    for field in array_fields:
      _validate_string_array(
        issues, provider[field], f"{path}.{field}", min_items=1 if field == "offered_services" else 0
      )
    offered_services = provider["offered_services"] if isinstance(provider["offered_services"], list) else []
    required_services = provider["required_services"] if isinstance(provider["required_services"], list) else []
    if isinstance(provider_id, str):
      offered_by_provider[provider_id] = {
        value for value in offered_services if isinstance(value, str)
      }
    for service in [*offered_services, *required_services]:
      if not isinstance(service, str):
        continue
      if service not in SERVICE_KEYS:
        _issue(issues, "composition.unknown_service", f"{path}.services", service)
    try:
      _normalize_value(provider["configuration"], f"{path}.configuration")
    except ValueError as exc:
      _issue(issues, "composition.noncanonical_number", f"{path}.configuration", str(exc))
  _validate_unique(issues, provider_ids, "$.providers", code="composition.duplicate_id")
  provider_set = set(provider_ids)

  component_ids: list[str] = []
  for index, component in enumerate(components):
    path = f"$.component_contributions[{index}]"
    if not _required_fields(issues, component, path, component_fields):
      continue
    if not isinstance(component["component_id"], str) or not component["component_id"]:
      _issue(issues, "composition.invalid_json_type", f"{path}.component_id", "expected string")
    else:
      component_ids.append(component["component_id"])
    if component["plugin_id"] not in plugin_set:
      _issue(issues, "composition.unknown_plugin", f"{path}.plugin_id", component["plugin_id"])
    _validate_identifier(issues, component["registration_id"], f"{path}.registration_id")
  _validate_unique(
    issues, component_ids, "$.component_contributions", code="composition.duplicate_id"
  )
  component_set = set(component_ids)

  system_ids: list[str] = []
  system_by_id: dict[str, dict[str, Any]] = {}
  for index, system in enumerate(systems):
    path = f"$.system_contributions[{index}]"
    if not _required_fields(issues, system, path, system_fields):
      continue
    system_id = system["contribution_id"]
    _validate_identifier(issues, system_id, f"{path}.contribution_id")
    _validate_identifier(issues, system["registration_factory_id"], f"{path}.registration_factory_id")
    if isinstance(system_id, str):
      system_ids.append(system_id)
      system_by_id.setdefault(system_id, system)
    if system["plugin_id"] not in plugin_set:
      _issue(issues, "composition.unknown_plugin", f"{path}.plugin_id", system["plugin_id"])
    if system["domain"] not in {"common", "air", "naval", "ground", "cross_domain", "diagnostics"}:
      _issue(issues, "composition.invalid_json_type", f"{path}.domain", system["domain"])
    for field in system_fields - {"contribution_id", "plugin_id", "registration_factory_id", "domain"}:
      _validate_string_array(issues, system[field], f"{path}.{field}")
    required_services = system["required_services"] if isinstance(system["required_services"], list) else []
    required_components = system["required_components"] if isinstance(system["required_components"], list) else []
    for service in required_services:
      if not isinstance(service, str):
        continue
      if service not in SERVICE_KEYS:
        _issue(issues, "composition.unknown_service", f"{path}.required_services", service)
    for component_id in required_components:
      if not isinstance(component_id, str):
        continue
      if component_id not in component_set:
        _issue(issues, "composition.unknown_component", f"{path}.required_components", component_id)
  _validate_unique(issues, system_ids, "$.system_contributions", code="composition.duplicate_id")
  system_set = set(system_ids)

  binding_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
  for index, binding in enumerate(bindings):
    path = f"$.service_bindings[{index}]"
    if not _required_fields(issues, binding, path, binding_fields):
      continue
    consumer_kind = binding["consumer_kind"]
    consumer_id = binding["consumer_id"]
    provider_id = binding["provider_id"]
    service_key = binding["service_key"]
    for field in ("consumer_id", "provider_id"):
      _validate_identifier(issues, binding[field], f"{path}.{field}")
    if not isinstance(service_key, str) or not service_key:
      _issue(issues, "composition.invalid_json_type", f"{path}.service_key", "expected string")
      continue
    if provider_id not in provider_set:
      _issue(issues, "composition.unknown_provider", f"{path}.provider_id", provider_id)
    if consumer_kind == "provider":
      if consumer_id not in provider_set:
        _issue(issues, "composition.unknown_consumer", f"{path}.consumer_id", consumer_id)
      else:
        required = set(provider_by_id[consumer_id]["required_services"])
        if service_key not in required:
          _issue(issues, "composition.unknown_service", f"{path}.service_key", "consumer does not require service")
    elif consumer_kind == "system":
      if consumer_id not in system_set:
        _issue(issues, "composition.unknown_consumer", f"{path}.consumer_id", consumer_id)
      else:
        required = set(system_by_id[consumer_id]["required_services"])
        if service_key not in required:
          _issue(issues, "composition.unknown_service", f"{path}.service_key", "consumer does not require service")
    else:
      _issue(issues, "composition.invalid_json_type", f"{path}.consumer_kind", consumer_kind)
    if service_key not in SERVICE_KEYS:
      _issue(issues, "composition.unknown_service", f"{path}.service_key", service_key)
    if provider_id in offered_by_provider and service_key not in offered_by_provider[provider_id]:
      _issue(issues, "composition.service_not_offered", f"{path}.provider_id", service_key)
    binding_groups.setdefault((consumer_kind, consumer_id, service_key), []).append(binding)

    if consumer_kind == "provider" and consumer_id in provider_by_id and provider_id in provider_by_id:
      provider_scope = provider_by_id[provider_id]["scope"]
      consumer_scope = provider_by_id[consumer_id]["scope"]
      if not _scope_can_supply(provider_scope, consumer_scope):
        _issue(
          issues,
          "composition.scope_capture_violation",
          path,
          f"{provider_scope} provider cannot be retained by {consumer_scope} consumer",
        )
      provider_edges.append((provider_id, consumer_id))

  for provider_id, provider in provider_by_id.items():
    for service in provider["required_services"]:
      rows = binding_groups.get(("provider", provider_id, service), [])
      if not rows:
        _issue(
          issues,
          "composition.missing_service_binding",
          f"$.providers[{provider_id}].required_services",
          service,
        )
      elif len(rows) > 1:
        _issue(
          issues,
          "composition.ambiguous_service_binding",
          f"$.providers[{provider_id}].required_services",
          service,
        )
    for dependency in provider["after_provider_ids"]:
      if dependency not in provider_set:
        _issue(
          issues,
          "composition.unknown_provider",
          f"$.providers[{provider_id}].after_provider_ids",
          dependency,
        )
      elif dependency == provider_id:
        _issue(
          issues,
          "composition.provider_dependency_cycle",
          f"$.providers[{provider_id}].after_provider_ids",
          provider_id,
        )
        provider_edges.append((dependency, provider_id))
      else:
        provider_edges.append((dependency, provider_id))
    for conflict in provider["conflicts"]:
      if conflict in provider_set:
        _issue(
          issues,
          "composition.provider_conflict",
          f"$.providers[{provider_id}].conflicts",
          conflict,
        )

  for system_id, system in system_by_id.items():
    for service in system["required_services"]:
      rows = binding_groups.get(("system", system_id, service), [])
      if not rows:
        _issue(
          issues,
          "composition.missing_service_binding",
          f"$.system_contributions[{system_id}].required_services",
          service,
        )
      elif len(rows) > 1:
        _issue(
          issues,
          "composition.ambiguous_service_binding",
          f"$.system_contributions[{system_id}].required_services",
          service,
        )

  _, provider_cycle = _stable_topological_order(provider_set, provider_edges)
  if provider_cycle:
    _issue(
      issues,
      "composition.provider_dependency_cycle",
      "$.providers",
      ",".join(provider_cycle),
    )

  system_edges: list[tuple[str, str]] = []
  for system_id, system in system_by_id.items():
    for dependency in system["after"]:
      if dependency not in system_set:
        _issue(
          issues,
          "composition.unknown_system_dependency",
          f"$.system_contributions[{system_id}].after",
          dependency,
        )
      elif dependency == system_id:
        _issue(
          issues,
          "composition.system_dependency_cycle",
          f"$.system_contributions[{system_id}].after",
          system_id,
        )
        system_edges.append((dependency, system_id))
      else:
        system_edges.append((dependency, system_id))
    for successor in system["before"]:
      if successor not in system_set:
        _issue(
          issues,
          "composition.unknown_system_dependency",
          f"$.system_contributions[{system_id}].before",
          successor,
        )
      elif successor == system_id:
        _issue(
          issues,
          "composition.system_dependency_cycle",
          f"$.system_contributions[{system_id}].before",
          system_id,
        )
        system_edges.append((system_id, successor))
      else:
        system_edges.append((system_id, successor))
    for conflict in system["conflicts"]:
      if conflict in system_set:
        _issue(
          issues,
          "composition.system_conflict",
          f"$.system_contributions[{system_id}].conflicts",
          conflict,
        )
  _, system_cycle = _stable_topological_order(system_set, system_edges)
  if system_cycle:
    _issue(
      issues,
      "composition.system_dependency_cycle",
      "$.system_contributions",
      ",".join(system_cycle),
    )

  backend_fields = {"backend_profile_id", "provider_id", "required_capabilities"}
  if _required_fields(issues, manifest["backend_request"], "$.backend_request", backend_fields):
    backend = manifest["backend_request"]
    _validate_identifier(issues, backend["backend_profile_id"], "$.backend_request.backend_profile_id")
    if backend["provider_id"] not in provider_set:
      _issue(issues, "composition.unknown_provider", "$.backend_request.provider_id", backend["provider_id"])
    elif BACKEND_SERVICE_KEY not in offered_by_provider[backend["provider_id"]]:
      _issue(
        issues,
        "composition.backend_provider_mismatch",
        "$.backend_request.provider_id",
        f"provider must offer {BACKEND_SERVICE_KEY}",
      )
    _validate_string_array(
      issues, backend["required_capabilities"], "$.backend_request.required_capabilities"
    )

  scope_fields = {"scope", "parent_scope", "cardinality", "rebuild_trigger"}
  scope_rows = manifest["scope_policies"] if isinstance(manifest["scope_policies"], list) else []
  scope_names: list[str] = []
  for index, row in enumerate(scope_rows):
    path = f"$.scope_policies[{index}]"
    if not _required_fields(issues, row, path, scope_fields):
      continue
    scope = row["scope"]
    if isinstance(scope, str):
      scope_names.append(scope)
    expected_cardinality = "singleton" if scope in {"application", "backend"} else "one_per_parent"
    expected_trigger = {
      "application": "host_reconfiguration_or_shutdown",
      "backend": "backend_switch_or_failure",
      "batch": "batch_resize_or_reconfiguration",
      "world": "world_replacement_or_composition_change",
      "episode": "reset_or_episode_completion",
    }.get(scope)
    if (
      scope not in SCOPE_ORDER
      or row["parent_scope"] != SCOPE_PARENT.get(scope)
      or row["cardinality"] != expected_cardinality
      or row["rebuild_trigger"] != expected_trigger
    ):
      _issue(issues, "composition.invalid_scope_policy", path, f"invalid parent for {scope}")
  if set(scope_names) != set(SCOPE_ORDER) or len(scope_names) != len(SCOPE_ORDER):
    _issue(issues, "composition.invalid_scope_policy", "$.scope_policies", "exact scope hierarchy required")

  reconfiguration_fields = {
    "truth_affecting_change",
    "active_episode_change",
    "allowed_barriers",
  }
  if _required_fields(
    issues,
    manifest["reconfiguration_policy"],
    "$.reconfiguration_policy",
    reconfiguration_fields,
  ):
    policy = manifest["reconfiguration_policy"]
    if policy["truth_affecting_change"] != "rebuild_scope_generation" or policy[
      "active_episode_change"
    ] != "forbidden":
      _issue(
        issues,
        "composition.invalid_reconfiguration_policy",
        "$.reconfiguration_policy",
        "truth-affecting active mutation is forbidden",
      )
    _validate_string_array(
      issues, policy["allowed_barriers"], "$.reconfiguration_policy.allowed_barriers", min_items=1
    )

  evidence_fields = {
    "canonicalization",
    "hash_algorithm",
    "include_provider_versions",
    "include_graph_hash",
    "include_scope_generations",
  }
  if _required_fields(issues, manifest["evidence_policy"], "$.evidence_policy", evidence_fields):
    evidence = manifest["evidence_policy"]
    if evidence != {
      "canonicalization": CANONICALIZATION_ID,
      "hash_algorithm": HASH_ALGORITHM,
      "include_provider_versions": True,
      "include_graph_hash": True,
      "include_scope_generations": True,
    }:
      _issue(
        issues,
        "composition.invalid_evidence_policy",
        "$.evidence_policy",
        "v1 evidence identity fields are mandatory",
      )

  _validate_string_array(issues, manifest["compatibility_claims"], "$.compatibility_claims")
  try:
    normalize_manifest(manifest)
  except (TypeError, ValueError) as exc:
    _issue(issues, "composition.invalid_json_type", "$", str(exc))
  return sorted(set(issues))


def validate_manifest(manifest: Any) -> list[ValidationIssue]:
  """Validate arbitrary input without allowing malformed shapes to escape as exceptions."""
  try:
    return _validate_manifest_impl(manifest)
  except (AttributeError, IndexError, KeyError, RecursionError, TypeError, ValueError):
    return [
      ValidationIssue(
        "composition.invalid_json_type",
        "$",
        "malformed manifest shape or value",
      )
    ]


def resolve_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
  issues = validate_manifest(manifest)
  if issues:
    raise ContractError(issues)
  normalized = normalize_manifest(manifest)
  provider_ids = [row["provider_id"] for row in normalized["providers"]]
  provider_edges: list[tuple[str, str]] = []
  for binding in normalized["service_bindings"]:
    if binding["consumer_kind"] == "provider" and binding["provider_id"] != binding["consumer_id"]:
      provider_edges.append((binding["provider_id"], binding["consumer_id"]))
  for provider in normalized["providers"]:
    provider_edges.extend(
      (dependency, provider["provider_id"]) for dependency in provider["after_provider_ids"]
    )
  provider_order, provider_cycle = _stable_topological_order(provider_ids, provider_edges)
  if provider_cycle:
    raise ContractError(
      [
        ValidationIssue(
          "composition.provider_dependency_cycle", "$.providers", ",".join(provider_cycle)
        )
      ]
    )

  system_ids = [row["contribution_id"] for row in normalized["system_contributions"]]
  system_edges: list[tuple[str, str]] = []
  for system in normalized["system_contributions"]:
    system_edges.extend((dependency, system["contribution_id"]) for dependency in system["after"])
    system_edges.extend((system["contribution_id"], successor) for successor in system["before"])
  system_order, system_cycle = _stable_topological_order(system_ids, system_edges)
  if system_cycle:
    raise ContractError(
      [
        ValidationIssue(
          "composition.system_dependency_cycle",
          "$.system_contributions",
          ",".join(system_cycle),
        )
      ]
    )

  requested_hash = canonical_sha256(normalized)
  resolved_payload = {
    "schema_version": RESOLVED_SCHEMA_VERSION,
    "resolver_contract_version": RESOLVER_CONTRACT_VERSION,
    "requested_manifest_sha256": requested_hash,
    "provider_construction_order": provider_order,
    "system_registration_order": system_order,
    "manifest": normalized,
  }
  return {
    **resolved_payload,
    "resolved_manifest_sha256": canonical_sha256(resolved_payload),
  }


DEFAULT_COMPONENTS = (
  "Transform",
  "Velocity",
  "Alliance",
  "KeyEntity",
  "MovementCommand",
  "MissionCommandControlState",
  "PilotAction",
  "MissionCommand",
  "TaskOrder",
  "LeaderIntent",
  "PendingMissionCommand",
  "MissionCommandPendingQueue",
  "ActionCommand",
  "ActionSpaceConfig",
  "CommandLag",
  "LaggedCommand",
  "CommandLink",
  "PendingMovementCommand",
  "PendingActionCommand",
  "LandingGear",
  "Health",
  "Mass",
  "MassProperties",
  "ShipPlatform",
  "SubmarinePlatform",
  "Propulsion",
  "AeroTuning",
  "EngineTuning",
  "StallState",
  "ForceAccumulator",
  "AeroState",
  "ControlLawState",
  "ControlSurfaceState",
  "Inertia",
  "AngularVelocity",
  "GroundState",
  "GearState",
  "Missile",
  "Munition",
  "Ammo",
  "WeaponCooldown",
  "PilotWeaponReleaseState",
  "NavalWeaponSystem",
  "Jammer",
  "Countermeasures",
  "RWR",
  "ESMReceiver",
  "RCSProfile",
  "Lifetime",
  "FuelSystem",
  "Loadout",
  "LogisticsNode",
  "NavalStores",
  "ResupplyState",
  "Sensor",
  "MountedSensors",
  "Sonar",
  "MountedSonars",
  "ContactList",
  "FlightModel",
  "Score",
  "DataLink",
  "CommQueue",
  "PilotReport",
  "InstrumentState",
  "EGI",
  "TrackDatabase",
  "EmbarkedAirOps",
  "HitboxConfig",
  "SystemHealth",
  "ComponentDamageState",
  "StructuralBreakupState",
  "PlatformDamageState",
  "AircraftDamageState",
  "AircraftDamageBaseline",
  "EffectsModelRef",
  "EngagementEventRecorderRef",
  "SensorModelRef",
  "AcousticModelRef",
  "ControlModelRef",
  "GuidanceModelRef",
  "EnvironmentModelRef",
)

DEFAULT_SYSTEMS = (
  ("builtin.system.command_link", "register_command_link_system", "common", ()),
  ("builtin.system.action_mapping", "register_action_mapping_system", "common", ()),
  ("builtin.system.command_lag", "register_command_lag_system", "common", ()),
  ("builtin.system.control", "register_control_system", "air", ("simulation.control.model",)),
  ("builtin.system.force_clear", "register_force_clear_system", "air", ()),
  ("builtin.system.aero_state", "register_aero_state_system", "air", ("simulation.environment.model",)),
  ("builtin.system.propulsion", "flight_dynamics.register_propulsion_system", "air", ("simulation.environment.model",)),
  ("builtin.system.force", "register_force_system", "air", ()),
  ("builtin.system.actuator", "flight_dynamics.register_actuator_system", "air", ()),
  ("builtin.system.aerodynamics", "register_aerodynamics_system", "air", ("simulation.environment.model",)),
  ("builtin.system.ground_contact", "register_ground_contact_system", "ground", ("simulation.environment.model",)),
  ("builtin.system.rotational_integration", "register_rotational_integration_system", "air", ()),
  ("builtin.system.guidance", "register_guidance_system", "cross_domain", ("simulation.guidance.model",)),
  ("builtin.system.leapfrog_integration", "register_leapfrog_integration_system", "common", ()),
  ("builtin.system.ship_motion", "register_ship_motion_system", "naval", ("simulation.environment.model",)),
  ("builtin.system.submarine_motion", "register_submarine_motion_system", "naval", ()),
  ("builtin.system.navigation", "register_navigation_system", "common", ()),
  ("builtin.system.sensor", "register_sensor_system", "cross_domain", ("simulation.sensor.model",)),
  ("builtin.system.sonar", "register_sonar_system", "naval", ("simulation.acoustic.model",)),
  ("builtin.system.track_manager", "register_track_manager_system", "common", ()),
  ("builtin.system.data_link", "register_data_link_system", "common", ()),
  ("builtin.system.embarked_air_ops", "register_embarked_air_ops_system", "naval", ()),
  ("builtin.system.pilot_weapon_release", "register_pilot_weapon_release_system", "air", ("runtime.weapon_release.service",)),
  ("builtin.system.naval_weapon_release", "register_naval_mission_weapon_release_system", "naval", ("runtime.weapon_release.service",)),
  ("builtin.system.instrument", "register_instrument_system", "common", ()),
  ("builtin.system.damage_common", "register_damage_system_common", "common", ("simulation.effects.model",)),
  ("builtin.system.aircraft_damage", "register_aircraft_damage_system", "air", ()),
  ("builtin.system.structural_failure", "register_structural_failure_system", "air", ()),
  ("builtin.system.structural_consequence", "register_structural_consequence_system", "air", ()),
  ("builtin.system.naval_damage", "register_naval_damage_system", "naval", ()),
  ("builtin.system.ground_damage", "register_ground_damage_system", "ground", ()),
  ("builtin.system.ew", "register_ew_system", "cross_domain", ()),
  ("builtin.system.logistics", "register_logistics_system", "common", ()),
  ("builtin.system.naval_logistics", "register_naval_logistics_system", "naval", ()),
)

EXACT_NODE_BY_SYSTEM = {
  "builtin.system.command_link": ("CommandLinkMovement", "CommandLinkAction", "CommandLinkMission"),
  "builtin.system.action_mapping": ("ActionMapping",),
  "builtin.system.command_lag": ("CommandLag",),
  "builtin.system.control": ("FlightControl",),
  "builtin.system.force_clear": ("ClearForces",),
  "builtin.system.aero_state": ("ComputeAeroState",),
  "builtin.system.propulsion": ("ComputePropulsion",),
  "builtin.system.force": ("ComputeForces",),
  "builtin.system.actuator": ("AdvanceControlSurfaces",),
  "builtin.system.aerodynamics": ("ComputeAerodynamics",),
  "builtin.system.ground_contact": ("GroundContact",),
  "builtin.system.rotational_integration": ("RotationalIntegrate",),
  "builtin.system.guidance": ("MissileGuidance",),
  "builtin.system.leapfrog_integration": ("LeapfrogIntegrate",),
  "builtin.system.navigation": ("NavigationSystem",),
  "builtin.system.sensor": ("SensorSystem",),
  "builtin.system.data_link": ("DataLinkFusionSystem",),
  "builtin.system.instrument": ("UpdateInstruments",),
  "builtin.system.ew": ("EW_Release_Chaff", "EW_Release_Flare", "EW_Lifetime_Manager"),
  "builtin.system.logistics": ("FuelConsumption", "MassUpdate", "LogisticsAction", "ResupplyLogic"),
}


def _provider(
  provider_id: str,
  scope: str,
  offered: Iterable[str],
  required: Iterable[str] = (),
) -> dict[str, Any]:
  return {
    "provider_id": provider_id,
    "plugin_id": "builtin.core_runtime",
    "implementation_version": "1.0.0",
    "scope": scope,
    "cardinality": "one_per_scope",
    "offered_services": list(offered),
    "required_services": list(required),
    "required_capabilities": [],
    "conflicts": [],
    "after_provider_ids": [],
    "restart_policy": "rebuild_scope_generation",
    "teardown_policy": "reverse_dependency_order",
    "configuration": {},
  }


def _component_registration_id(component: str) -> str:
  snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", component).lower()
  return f"flecs.component.{snake}"


def default_compatibility_manifest() -> dict[str, Any]:
  providers = [
    _provider("builtin.backend.flecs_cpu", "backend", (BACKEND_SERVICE_KEY,)),
    _provider("builtin.environment.default", "world", ("simulation.environment.model",)),
    _provider("builtin.unit_factory.default", "world", ("simulation.unit_factory",)),
    _provider("builtin.effects.default", "world", ("simulation.effects.model",)),
    _provider(
      "builtin.sensor.default",
      "world",
      ("simulation.sensor.model",),
      ("simulation.environment.model",),
    ),
    _provider(
      "builtin.acoustic.default",
      "world",
      ("simulation.acoustic.model",),
      ("simulation.environment.model",),
    ),
    _provider(
      "builtin.control.default",
      "world",
      ("simulation.control.model",),
      ("simulation.environment.model",),
    ),
    _provider(
      "builtin.guidance.default",
      "world",
      ("simulation.guidance.model",),
      ("simulation.environment.model", "runtime.engagement_event_recorder"),
    ),
    _provider(
      "builtin.engagement_event_store",
      "world",
      ("runtime.engagement_event_recorder",),
    ),
    _provider(
      "builtin.weapon_release.damage_bridge",
      "world",
      ("runtime.weapon_release.damage_bridge",),
      ("simulation.effects.model",),
    ),
    _provider(
      "builtin.weapon_release.service",
      "world",
      ("runtime.weapon_release.service",),
      (
        "simulation.unit_factory",
        "runtime.engagement_event_recorder",
        "runtime.weapon_release.damage_bridge",
      ),
    ),
  ]

  provider_for_service = {
    service: provider["provider_id"]
    for provider in providers
    for service in provider["offered_services"]
  }
  bindings: list[dict[str, str]] = []
  for provider in providers:
    for service in provider["required_services"]:
      bindings.append(
        {
          "consumer_kind": "provider",
          "consumer_id": provider["provider_id"],
          "service_key": service,
          "provider_id": provider_for_service[service],
        }
      )

  systems: list[dict[str, Any]] = []
  previous: str | None = None
  for contribution_id, factory_id, domain, required_services in DEFAULT_SYSTEMS:
    system = {
      "contribution_id": contribution_id,
      "plugin_id": "builtin.core_runtime",
      "registration_factory_id": factory_id,
      "domain": domain,
      "required_services": list(required_services),
      "required_components": [],
      "provided_components": [],
      "semantic_stage_ids": [],
      "executable_node_ids": list(EXACT_NODE_BY_SYSTEM.get(contribution_id, ())),
      "read_state_shards": [],
      "write_state_shards": [],
      "required_barriers": [],
      "required_capabilities": [],
      "conflicts": [],
      "after": [previous] if previous is not None else [],
      "before": [],
    }
    systems.append(system)
    for service in required_services:
      bindings.append(
        {
          "consumer_kind": "system",
          "consumer_id": contribution_id,
          "service_key": service,
          "provider_id": provider_for_service[service],
        }
      )
    previous = contribution_id

  return {
    "schema_version": SCHEMA_VERSION,
    "composition_id": "builtin.default_compatibility",
    "contract_versions": {
      "composition": COMPOSITION_CONTRACT_VERSION,
      "runtime": "1.0.0",
      "content": "1.0.0",
      "stage": "1.0.0",
    },
    "requested_profile": {
      "profile_id": "builtin.default_compatibility",
      "profile_version": "1.0.0",
    },
    "plugins": [
      {
        "plugin_id": "builtin.core_runtime",
        "implementation_id": "echelon_forge.native_builtin",
        "plugin_version": "1.0.0",
        "composition_contract_range": ">=1.0.0 <2.0.0",
        "host_support": ["native"],
        "determinism_class": "truth_affecting_deterministic",
        "artifact": {
          "kind": "repository_builtin",
          "identity": "echelon-forge-source-tree",
          "sha256": None,
        },
        "required_capabilities": [],
        "conflicts": [],
        "configuration": {},
      }
    ],
    "providers": providers,
    "service_bindings": bindings,
    "component_contributions": [
      {
        "component_id": component,
        "plugin_id": "builtin.core_runtime",
        "registration_id": _component_registration_id(component),
      }
      for component in DEFAULT_COMPONENTS
    ],
    "system_contributions": systems,
    "backend_request": {
      "backend_profile_id": "cpu_exact.reference",
      "provider_id": "builtin.backend.flecs_cpu",
      "required_capabilities": ["runtime.cpu_exact"],
    },
    "scope_policies": [
      {
        "scope": scope,
        "parent_scope": SCOPE_PARENT[scope],
        "cardinality": "singleton" if scope in {"application", "backend"} else "one_per_parent",
        "rebuild_trigger": {
          "application": "host_reconfiguration_or_shutdown",
          "backend": "backend_switch_or_failure",
          "batch": "batch_resize_or_reconfiguration",
          "world": "world_replacement_or_composition_change",
          "episode": "reset_or_episode_completion",
        }[scope],
      }
      for scope in SCOPE_ORDER
    ],
    "reconfiguration_policy": {
      "truth_affecting_change": "rebuild_scope_generation",
      "active_episode_change": "forbidden",
      "allowed_barriers": ["pre_run", "episode_end", "world_rebuild"],
    },
    "evidence_policy": {
      "canonicalization": CANONICALIZATION_ID,
      "hash_algorithm": HASH_ALGORITHM,
      "include_provider_versions": True,
      "include_graph_hash": True,
      "include_scope_generations": True,
    },
    "compatibility_claims": [
      "legacy.default_kernel_construction.v1",
      "legacy.registration_order.v1",
      "legacy.cpu_exact_backend.v1",
    ],
  }


def _pretty_json(value: Any) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_or_check(path: Path, value: Any, *, check: bool) -> bool:
  expected = _pretty_json(value)
  if check:
    return path.is_file() and path.read_text(encoding="utf-8") == expected
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(expected, encoding="utf-8")
  return True


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
    "command",
    choices=("schema", "fixtures", "check", "validate", "resolve"),
  )
  parser.add_argument("--manifest", type=Path)
  return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  args = parse_args(argv)
  if args.command == "schema":
    _write_or_check(SCHEMA_PATH, manifest_schema(), check=False)
    _write_or_check(RESOLVED_SCHEMA_PATH, resolved_schema(), check=False)
    print(SCHEMA_PATH.relative_to(REPO_ROOT).as_posix())
    print(RESOLVED_SCHEMA_PATH.relative_to(REPO_ROOT).as_posix())
    return 0
  if args.command == "fixtures":
    requested = normalize_manifest(default_compatibility_manifest())
    resolved = resolve_manifest(requested)
    _write_or_check(REQUESTED_FIXTURE_PATH, requested, check=False)
    _write_or_check(RESOLVED_FIXTURE_PATH, resolved, check=False)
    print(REQUESTED_FIXTURE_PATH.relative_to(REPO_ROOT).as_posix())
    print(RESOLVED_FIXTURE_PATH.relative_to(REPO_ROOT).as_posix())
    return 0
  if args.command == "check":
    requested = normalize_manifest(default_compatibility_manifest())
    checks = (
      (SCHEMA_PATH, manifest_schema()),
      (REQUESTED_FIXTURE_PATH, requested),
      (RESOLVED_SCHEMA_PATH, resolved_schema()),
      (RESOLVED_FIXTURE_PATH, resolve_manifest(requested)),
    )
    stale = [path for path, value in checks if not _write_or_check(path, value, check=True)]
    for path in stale:
      print(f"stale: {path.relative_to(REPO_ROOT).as_posix()}")
    return 1 if stale else 0
  if args.manifest is None:
    raise SystemExit("--manifest is required for validate/resolve")
  try:
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"), parse_float=lambda value: (_ for _ in ()).throw(ValueError(f"noncanonical number {value}")))
  except (OSError, json.JSONDecodeError, ValueError) as exc:
    print(
      _pretty_json(
        {
          "valid": False,
          "issues": [
            ValidationIssue("composition.invalid_json_type", "$", str(exc)).to_dict()
          ],
        }
      ),
      end="",
    )
    return 1
  if args.command == "validate":
    issues = validate_manifest(manifest)
    print(_pretty_json({"valid": not issues, "issues": [row.to_dict() for row in issues]}), end="")
    return 1 if issues else 0
  if args.command == "resolve":
    try:
      resolved = resolve_manifest(manifest)
    except ContractError as exc:
      print(_pretty_json({"valid": False, "issues": [row.to_dict() for row in exc.issues]}), end="")
      return 1
    print(_pretty_json(resolved), end="")
    return 0
  raise AssertionError(args.command)


if __name__ == "__main__":
  sys.exit(main())
