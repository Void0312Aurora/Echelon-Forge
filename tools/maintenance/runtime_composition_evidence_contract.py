"""P5-A runtime composition evidence and strict comparison contract.

The static identity bundle is derived from already accepted request, lock,
profile-projection, resolved-manifest, backend-provider, and native executable
graph owners. Runtime producers add observed scope generations before sealing
the final evidence identity.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import simulation_composition_contract as low_level


SCHEMA_VERSION = "echelon_forge.runtime_composition_evidence.v1"
CONTRACT_VERSION = "1.0.0"
CANONICALIZATION = "echelon_forge.sorted_utf8_json.v1"
HASH_ALGORITHM = "sha256"
HOST_MODE = "native_cpp"
BINDING_VERSION = "native.v1"
SCOPE_NAMES = ("application", "backend", "batch", "world", "episode")
MAX_INT64 = (1 << 63) - 1

FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"
REQUEST_PATH = FIXTURES / "default_runtime_composition_request.v1.json"
LOCK_PATH = FIXTURES / "default_admitted_catalog_lock.v1.json"
PROJECTION_PATH = FIXTURES / "default_runtime_profile_projection.v1.json"
BACKEND_REQUEST_PATH = FIXTURES / "default_backend_provider_request.v1.json"
RESOLVED_PATH = FIXTURES / "default_compatibility_manifest.resolved.json"
EVIDENCE_PATH = FIXTURES / "default_runtime_composition_evidence.v1.json"
INVALID_MATRIX_PATH = FIXTURES / "invalid_runtime_composition_evidence_matrix.v1.json"
SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/runtime_composition_evidence.v1.schema.json"
)
GENERATED_HEADER_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/runtime_composition_evidence.v1.generated.h"
)
REGISTRY_PATH = REPO_ROOT / "src/core/engine/system_contribution_registry.cpp"


@dataclass(frozen=True, order=True)
class ValidationIssue:
  code: str
  path: str
  detail: str


class ContractError(ValueError):
  def __init__(self, issues: Iterable[ValidationIssue]):
    self.issues = tuple(sorted(issues))
    super().__init__("; ".join(f"{issue.code}@{issue.path}" for issue in self.issues))


def _read(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _pretty(value: Any) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _normalize(value: dict[str, Any]) -> dict[str, Any]:
  normalized = low_level._normalize_value(deepcopy(value), "$")
  normalized["provider_versions"] = sorted(
    normalized["provider_versions"],
    key=lambda row: (row["provider_id"].encode(), row["implementation_version"].encode()),
  )
  normalized["backend"]["admitted_capabilities"] = sorted(
    normalized["backend"]["admitted_capabilities"], key=lambda value: value.encode()
  )
  for world in normalized["world_instances"]:
    world["scope_generations"] = sorted(
      world["scope_generations"],
      key=lambda row: (row["scope"].encode(), row["instance_id"].encode(), row["generation"]),
    )
  normalized["world_instances"] = sorted(
    normalized["world_instances"], key=lambda row: row["world_index"]
  )
  return normalized


def _payload(value: dict[str, Any]) -> dict[str, Any]:
  return {
    key: item
    for key, item in value.items()
    if key not in {"canonical_json", "evidence_sha256"}
  }


def _non_ascii_issues(value: Any, path: str = "$") -> list[ValidationIssue]:
  issues: list[ValidationIssue] = []
  if isinstance(value, str):
    if not value.isascii():
      issues.append(
        ValidationIssue("evidence.non_ascii_string", path, "v1 evidence strings must be ASCII")
      )
  elif isinstance(value, list):
    for index, item in enumerate(value):
      issues.extend(_non_ascii_issues(item, f"{path}[{index}]"))
  elif isinstance(value, dict):
    for key, item in value.items():
      issues.extend(_non_ascii_issues(item, f"{path}.{key}"))
  return issues


def _registry_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
  import re

  source = REGISTRY_PATH.read_text(encoding="utf-8")
  component_block = source.split("#define EF_DEFAULT_COMPONENT_CONTRIBUTIONS", 1)[1].split(
    "#define EF_DEFAULT_SYSTEM_CONTRIBUTIONS", 1
  )[0]
  component_block = re.sub(r"\\\s*", "", component_block)
  components = [
    {"component_id": component_id, "registration_id": registration_id}
    for _, component_id, registration_id in re.findall(
      r'X\(([^,]+),\s*"([^"]+)",\s*"([^"]+)"\)', component_block
    )
  ]

  system_block = source.split("#define EF_DEFAULT_SYSTEM_CONTRIBUTIONS", 1)[1].split(
    "#define EF_KERNEL_SYSTEM_CONTRIBUTIONS", 1
  )[0]
  system_block = re.sub(r"\\\s*", "", system_block)
  systems = [
    {
      "contribution_id": contribution_id,
      "registration_factory_id": factory,
      "domain": domain,
      "stage_id": stage_id,
      "stage_order": int(order),
      "after_contribution_id": after,
    }
    for contribution_id, factory, domain, stage_id, order, after in re.findall(
      r'X\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*(\d+),\s*"([^"]*)"',
      system_block,
    )
  ]

  kernel_block = source.split("#define EF_KERNEL_SYSTEM_CONTRIBUTIONS", 1)[1].split(
    "#define EF_COMPONENT_ROW", 1
  )[0]
  kernel_block = re.sub(r"\\\s*", "", kernel_block)
  kernel_systems = [
    {"contribution_id": contribution_id, "stage_id": stage_id, "stage_order": int(order)}
    for contribution_id, stage_id, order in re.findall(
      r'X\("([^"]+)",\s*"([^"]+)",\s*(\d+),', kernel_block
    )
  ]
  if len(components) != 83 or len(systems) != 34 or len(kernel_systems) != 2:
    raise ContractError(
      [ValidationIssue("evidence.registry_drift", "$", "expected 83 components, 2 kernel systems, and 34 resolved systems")]
    )
  return components, kernel_systems, systems


def _graph_payload(resolved: dict[str, Any]) -> dict[str, Any]:
  components, kernel_systems, systems = _registry_graph()
  manifest_components = sorted(
    (
      {"component_id": row["component_id"], "registration_id": row["registration_id"]}
      for row in resolved["manifest"]["component_contributions"]
    ),
    key=lambda row: row["component_id"].encode(),
  )
  if sorted(components, key=lambda row: row["component_id"].encode()) != manifest_components:
    raise ContractError(
      [ValidationIssue("evidence.registry_manifest_mismatch", "$.component_contributions", "owner registry and resolved manifest differ")]
    )
  if [row["contribution_id"] for row in sorted(systems, key=lambda row: row["stage_order"])] != resolved["system_registration_order"]:
    raise ContractError(
      [ValidationIssue("evidence.registry_manifest_mismatch", "$.system_registration_order", "owner registry and resolved order differ")]
    )
  return {
    "graph_contract_version": "echelon_forge.executable_system_graph.v1",
    "stage_contract_version": resolved["manifest"]["contract_versions"]["stage"],
    "component_contributions": components,
    "kernel_system_contributions": kernel_systems,
    "resolved_system_contributions": systems,
  }


def executable_graph_sha256(resolved: dict[str, Any]) -> str:
  return low_level.canonical_sha256(_graph_payload(resolved))


def _inputs() -> tuple[dict[str, Any], ...]:
  return tuple(
    _read(path)
    for path in (REQUEST_PATH, LOCK_PATH, PROJECTION_PATH, BACKEND_REQUEST_PATH, RESOLVED_PATH)
  )


def build_evidence(
  request: dict[str, Any],
  lock: dict[str, Any],
  projection: dict[str, Any],
  backend_request: dict[str, Any],
  resolved: dict[str, Any],
  *,
  world_instances: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
  manifest = resolved["manifest"]
  providers = sorted(
    (
      {
        "provider_id": row["provider_id"],
        "implementation_version": row["implementation_version"],
      }
      for row in manifest["providers"]
    ),
    key=lambda row: row["provider_id"].encode(),
  )
  value = {
    "schema_version": SCHEMA_VERSION,
    "evidence_contract_version": CONTRACT_VERSION,
    "composition_id": manifest["composition_id"],
    "requested_profile_id": manifest["requested_profile"]["profile_id"],
    "requested_profile_version": manifest["requested_profile"]["profile_version"],
    "runtime_request_sha256": lock["request_sha256"],
    "requested_manifest_sha256": resolved["requested_manifest_sha256"],
    "resolved_manifest_sha256": resolved["resolved_manifest_sha256"],
    "catalog_lock_sha256": lock["lock_sha256"],
    "profile_projection_sha256": projection["projection_sha256"],
    "resolver_contract_version": resolved["resolver_contract_version"],
    "provider_versions": providers,
    "backend": {
      "provider_id": backend_request["provider_id"],
      "implementation_version": backend_request["provider_implementation_version"],
      "backend_profile_id": backend_request["backend_profile_id"],
      "admitted_capabilities": backend_request["required_capabilities"],
    },
    "executable_graph_sha256": executable_graph_sha256(resolved),
    "stage_contract_version": manifest["contract_versions"]["stage"],
    "host_mode": HOST_MODE,
    "binding_version": BINDING_VERSION,
    "world_instances": world_instances
    if world_instances is not None
    else [
      {
        "world_index": 0,
        "scope_generations": [
          {"scope": scope, "instance_id": f"composition:1/world:0/{scope}", "generation": 1}
          for scope in SCOPE_NAMES
        ],
      }
    ],
    "canonicalization": CANONICALIZATION,
    "hash_algorithm": HASH_ALGORITHM,
  }
  value = _normalize(value)
  value["canonical_json"] = low_level.canonical_json_bytes(_payload(value)).decode("utf-8")
  value["evidence_sha256"] = low_level.canonical_sha256(_payload(value))
  return value


def validate_evidence(
  value: dict[str, Any],
  request: dict[str, Any],
  lock: dict[str, Any],
  projection: dict[str, Any],
  backend_request: dict[str, Any],
  resolved: dict[str, Any],
) -> list[ValidationIssue]:
  issues: list[ValidationIssue] = []
  required = set(evidence_schema()["required"])
  if not isinstance(value, dict) or set(value) != required:
    return [ValidationIssue("evidence.invalid_shape", "$", "fields do not match v1")]

  issues.extend(_non_ascii_issues(value))

  worlds = value.get("world_instances")
  if not isinstance(worlds, list) or not worlds:
    return [ValidationIssue("evidence.invalid_world_instances", "$.world_instances", "non-empty array required")]
  seen_worlds: set[int] = set()
  worlds_safe_for_normalization = True
  for world_index, world in enumerate(worlds):
    if not isinstance(world, dict) or set(world) != {"world_index", "scope_generations"}:
      issues.append(ValidationIssue("evidence.invalid_world_instances", f"$.world_instances[{world_index}]", "invalid world row"))
      worlds_safe_for_normalization = False
      continue
    index_value = world.get("world_index")
    valid_world_index = (
      not isinstance(index_value, bool)
      and isinstance(index_value, int)
      and 0 <= index_value <= MAX_INT64
    )
    if not valid_world_index or index_value in seen_worlds:
      issues.append(ValidationIssue("evidence.invalid_world_instances", f"$.world_instances[{world_index}].world_index", "invalid or duplicate world index"))
      worlds_safe_for_normalization = False
    if valid_world_index:
      seen_worlds.add(index_value)
    scopes = world.get("scope_generations")
    if not isinstance(scopes, list) or len(scopes) != 5:
      issues.append(ValidationIssue("evidence.invalid_scope_generation", f"$.world_instances[{world_index}].scope_generations", "all five scopes are required"))
      worlds_safe_for_normalization = False
      continue
    seen_scopes: set[str] = set()
    seen_instance_ids: set[str] = set()
    for scope_index, row in enumerate(scopes):
      path = f"$.world_instances[{world_index}].scope_generations[{scope_index}]"
      if not isinstance(row, dict) or set(row) != {"scope", "instance_id", "generation"}:
        issues.append(ValidationIssue("evidence.invalid_scope_generation", path, "invalid row"))
        worlds_safe_for_normalization = False
        continue
      scope_name = row.get("scope")
      instance_id = row.get("instance_id")
      valid_scope_name = isinstance(scope_name, str) and scope_name in SCOPE_NAMES
      valid_instance_id = isinstance(instance_id, str) and bool(instance_id)
      valid_generation = (
        not isinstance(row.get("generation"), bool)
        and isinstance(row.get("generation"), int)
        and 1 <= row["generation"] <= MAX_INT64
      )
      if (
        not valid_scope_name
        or not valid_instance_id
        or not valid_generation
        or (valid_scope_name and scope_name in seen_scopes)
        or (valid_instance_id and instance_id in seen_instance_ids)
      ):
        issues.append(ValidationIssue("evidence.invalid_scope_generation", path, "invalid or duplicate scope generation"))
        worlds_safe_for_normalization = False
      if valid_scope_name:
        seen_scopes.add(scope_name)
      if valid_instance_id:
        seen_instance_ids.add(instance_id)
    if seen_scopes != set(SCOPE_NAMES):
      issues.append(ValidationIssue("evidence.invalid_scope_generation", f"$.world_instances[{world_index}].scope_generations", "all five distinct scopes are required"))

  if [world.get("world_index") for world in worlds if isinstance(world, dict)] != list(range(len(worlds))):
    issues.append(ValidationIssue("evidence.invalid_world_instances", "$.world_instances", "world indices must be the contiguous canonical range [0, world_count)"))
    worlds_safe_for_normalization = False

  if not worlds_safe_for_normalization:
    return sorted(set(issues))

  try:
    expected = build_evidence(
      request,
      lock,
      projection,
      backend_request,
      resolved,
      world_instances=worlds,
    )
  except (AttributeError, KeyError, TypeError, ValueError) as error:
    issues.append(
      ValidationIssue(
        "evidence.invalid_shape", "$", f"evidence reconstruction rejected malformed input: {error}"
      )
    )
    return sorted(set(issues))
  groups = (
    ("runtime_request_sha256", "evidence.request_identity_mismatch"),
    ("composition_id", "evidence.manifest_identity_mismatch"),
    ("requested_profile_id", "evidence.manifest_identity_mismatch"),
    ("requested_profile_version", "evidence.manifest_identity_mismatch"),
    ("requested_manifest_sha256", "evidence.manifest_identity_mismatch"),
    ("resolved_manifest_sha256", "evidence.manifest_identity_mismatch"),
    ("catalog_lock_sha256", "evidence.catalog_lock_mismatch"),
    ("profile_projection_sha256", "evidence.profile_projection_mismatch"),
    ("resolver_contract_version", "evidence.resolver_identity_mismatch"),
    ("provider_versions", "evidence.provider_identity_mismatch"),
    ("backend", "evidence.provider_identity_mismatch"),
    ("executable_graph_sha256", "evidence.graph_identity_mismatch"),
    ("stage_contract_version", "evidence.graph_identity_mismatch"),
    ("host_mode", "evidence.host_identity_mismatch"),
    ("binding_version", "evidence.host_identity_mismatch"),
  )
  for field, code in groups:
    if value.get(field) != expected[field]:
      issues.append(ValidationIssue(code, f"$.{field}", "does not match admitted owner input"))
  if value.get("schema_version") != SCHEMA_VERSION or value.get("evidence_contract_version") != CONTRACT_VERSION:
    issues.append(ValidationIssue("evidence.unsupported_version", "$.schema_version", "version is not admitted"))
  if value.get("canonicalization") != CANONICALIZATION or value.get("hash_algorithm") != HASH_ALGORITHM:
    issues.append(ValidationIssue("evidence.invalid_identity_policy", "$.canonicalization", "identity policy mismatch"))

  try:
    normalized = _normalize(value)
  except (AttributeError, KeyError, TypeError, ValueError) as error:
    issues.append(ValidationIssue("evidence.invalid_shape", "$", f"normalization rejected malformed evidence: {error}"))
    return sorted(set(issues))
  if normalized["provider_versions"] != value["provider_versions"] or normalized["backend"]["admitted_capabilities"] != value["backend"]["admitted_capabilities"] or normalized["world_instances"] != value["world_instances"]:
    issues.append(ValidationIssue("evidence.noncanonical_order", "$", "set-like fields are not normalized"))
  canonical = low_level.canonical_json_bytes(_payload(normalized)).decode("utf-8")
  if value.get("canonical_json") != canonical:
    issues.append(ValidationIssue("evidence.canonical_bytes_mismatch", "$.canonical_json", "canonical bytes mismatch"))
  if value.get("evidence_sha256") != low_level.canonical_sha256(_payload(normalized)):
    issues.append(ValidationIssue("evidence.identity_mismatch", "$.evidence_sha256", "identity mismatch"))
  return sorted(set(issues))


def evidence_schema() -> dict[str, Any]:
  string = {"type": "string", "minLength": 1, "pattern": low_level.ASCII_PATTERN}
  sha = {"type": "string", "pattern": low_level.HEX64_RE.pattern}
  provider = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"provider_id": string, "implementation_version": string},
    "required": ["provider_id", "implementation_version"],
  }
  backend = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "provider_id": string,
      "implementation_version": string,
      "backend_profile_id": string,
      "admitted_capabilities": {"type": "array", "items": string, "minItems": 1, "uniqueItems": True},
    },
    "required": ["provider_id", "implementation_version", "backend_profile_id", "admitted_capabilities"],
  }
  scope = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "scope": {"enum": ["application", "backend", "batch", "world", "episode"]},
      "instance_id": string,
      "generation": {"type": "integer", "minimum": 1, "maximum": MAX_INT64},
    },
    "required": ["scope", "instance_id", "generation"],
  }
  world = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "world_index": {"type": "integer", "minimum": 0, "maximum": MAX_INT64},
      "scope_generations": {
        "type": "array",
        "items": scope,
        "minItems": 5,
        "maxItems": 5,
        "allOf": [
          {
            "contains": {
              "type": "object",
              "properties": {"scope": {"const": scope_name}},
              "required": ["scope"],
            },
            "minContains": 1,
            "maxContains": 1,
          }
          for scope_name in SCOPE_NAMES
        ],
      },
    },
    "required": ["world_index", "scope_generations"],
  }
  properties: dict[str, Any] = {
    "schema_version": {"const": SCHEMA_VERSION},
    "evidence_contract_version": {"const": CONTRACT_VERSION},
    "composition_id": string,
    "requested_profile_id": string,
    "requested_profile_version": string,
    "runtime_request_sha256": sha,
    "requested_manifest_sha256": sha,
    "resolved_manifest_sha256": sha,
    "catalog_lock_sha256": sha,
    "profile_projection_sha256": sha,
    "resolver_contract_version": string,
    "provider_versions": {"type": "array", "items": provider, "minItems": 1},
    "backend": backend,
    "executable_graph_sha256": sha,
    "stage_contract_version": string,
    "host_mode": string,
    "binding_version": string,
    "world_instances": {"type": "array", "items": world, "minItems": 1},
    "canonicalization": {"const": CANONICALIZATION},
    "hash_algorithm": {"const": HASH_ALGORITHM},
    "canonical_json": string,
    "evidence_sha256": sha,
  }
  return {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": SCHEMA_VERSION,
    "type": "object",
    "additionalProperties": False,
    "properties": properties,
    "required": list(properties),
  }


def generated_header(value: dict[str, Any]) -> str:
  providers = "\n".join(
    f'    {{"{row["provider_id"]}", "{row["implementation_version"]}"}},'
    for row in value["provider_versions"]
  )
  capabilities = "\n".join(
    f'    "{capability}",'
    for capability in value["backend"]["admitted_capabilities"]
  )
  return f'''#pragma once

#include <array>
#include <string_view>

namespace runtime::composition_evidence_contracts::generated {{

struct ProviderVersion {{
    std::string_view provider_id;
    std::string_view implementation_version;
}};

inline constexpr std::string_view kRuntimeRequestSha256 =
    "{value["runtime_request_sha256"]}";
inline constexpr std::string_view kCompositionId = "{value["composition_id"]}";
inline constexpr std::string_view kRequestedProfileId = "{value["requested_profile_id"]}";
inline constexpr std::string_view kRequestedProfileVersion = "{value["requested_profile_version"]}";
inline constexpr std::string_view kRequestedManifestSha256 =
    "{value["requested_manifest_sha256"]}";
inline constexpr std::string_view kResolvedManifestSha256 =
    "{value["resolved_manifest_sha256"]}";
inline constexpr std::string_view kCatalogLockSha256 =
    "{value["catalog_lock_sha256"]}";
inline constexpr std::string_view kProfileProjectionSha256 =
    "{value["profile_projection_sha256"]}";
inline constexpr std::string_view kResolverContractVersion =
    "{value["resolver_contract_version"]}";
inline constexpr std::string_view kExecutableGraphSha256 =
    "{value["executable_graph_sha256"]}";
inline constexpr std::string_view kStageContractVersion = "{value["stage_contract_version"]}";
inline constexpr std::string_view kHostMode = "{value["host_mode"]}";
inline constexpr std::string_view kBindingVersion = "{value["binding_version"]}";
inline constexpr std::string_view kBackendProviderId = "{value["backend"]["provider_id"]}";
inline constexpr std::string_view kBackendImplementationVersion = "{value["backend"]["implementation_version"]}";
inline constexpr std::string_view kBackendProfileId = "{value["backend"]["backend_profile_id"]}";

inline constexpr std::array<ProviderVersion, {len(value["provider_versions"])}> kProviderVersions = {{{{
{providers}
}}}};

inline constexpr std::array<std::string_view, {len(value["backend"]["admitted_capabilities"])}> kBackendCapabilities = {{{{
{capabilities}
}}}};

}} // namespace runtime::composition_evidence_contracts::generated
'''


def invalid_matrix() -> dict[str, Any]:
  return {
    "schema_version": "echelon_forge.invalid_runtime_composition_evidence_matrix.v1",
    "cases": [
      {"id": "catalog-lock", "path": "/catalog_lock_sha256", "value": "0" * 64, "code": "evidence.catalog_lock_mismatch"},
      {"id": "projection", "path": "/profile_projection_sha256", "value": "0" * 64, "code": "evidence.profile_projection_mismatch"},
      {"id": "provider-version", "path": "/provider_versions/0/implementation_version", "value": "9.9.9", "code": "evidence.provider_identity_mismatch"},
      {"id": "backend-profile", "path": "/backend/backend_profile_id", "value": "gpu.candidate", "code": "evidence.provider_identity_mismatch"},
      {"id": "graph", "path": "/executable_graph_sha256", "value": "0" * 64, "code": "evidence.graph_identity_mismatch"},
      {"id": "host", "path": "/host_mode", "value": "python.direct", "code": "evidence.host_identity_mismatch"},
      {"id": "scope", "path": "/world_instances/0/scope_generations/0/generation", "value": 0, "code": "evidence.invalid_scope_generation"},
      {"id": "duplicate-scope", "path": "/world_instances/0/scope_generations/1/scope", "value": "application", "code": "evidence.invalid_scope_generation"},
      {"id": "noncontiguous-world", "path": "/world_instances/0/world_index", "value": 1, "code": "evidence.invalid_world_instances"},
      {"id": "non-ascii-instance", "path": "/world_instances/0/scope_generations/0/instance_id", "value": "composition:1/world:0/applicatión", "code": "evidence.non_ascii_string"},
      {"id": "generation-overflow", "path": "/world_instances/0/scope_generations/0/generation", "value": MAX_INT64 + 1, "code": "evidence.invalid_scope_generation"},
    ],
  }


def generate() -> dict[str, Any]:
  value = build_evidence(*_inputs())
  SCHEMA_PATH.write_text(_pretty(evidence_schema()), encoding="utf-8", newline="\n")
  EVIDENCE_PATH.write_text(_pretty(value), encoding="utf-8", newline="\n")
  INVALID_MATRIX_PATH.write_text(_pretty(invalid_matrix()), encoding="utf-8", newline="\n")
  GENERATED_HEADER_PATH.write_text(generated_header(value), encoding="utf-8", newline="\n")
  return value


def check() -> None:
  value = build_evidence(*_inputs())
  expected = {
    SCHEMA_PATH: _pretty(evidence_schema()),
    EVIDENCE_PATH: _pretty(value),
    INVALID_MATRIX_PATH: _pretty(invalid_matrix()),
    GENERATED_HEADER_PATH: generated_header(value),
  }
  stale = [str(path.relative_to(REPO_ROOT)) for path, text in expected.items() if not path.exists() or path.read_text(encoding="utf-8") != text]
  if stale:
    raise SystemExit("stale runtime composition evidence artifacts: " + ", ".join(stale))


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("command", choices=("generate", "check", "validate"))
  parser.add_argument("--evidence", type=Path, default=EVIDENCE_PATH)
  args = parser.parse_args()
  if args.command == "generate":
    value = generate()
    print(value["evidence_sha256"])
    return 0
  if args.command == "check":
    check()
    return 0
  issues = validate_evidence(_read(args.evidence), *_inputs())
  for issue in issues:
    print(f"{issue.code}@{issue.path}: {issue.detail}", file=sys.stderr)
  return 1 if issues else 0


if __name__ == "__main__":
  raise SystemExit(main())
