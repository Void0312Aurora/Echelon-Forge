"""P3-B capability/profile projection and owner-admitted bundle contract.

This contract is deliberately downstream of the P2-C0 request and catalog-lock
contracts.  A named profile is only an explicit compatibility alias for a
capability/policy set; it cannot select a component or system outside the
owner-admitted lock and the native resolved artifact.
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

from tools.maintenance import runtime_composition_projection_contract as projection
from tools.maintenance import simulation_composition_contract as low_level


SCHEMA_VERSION = "echelon_forge.runtime_profile_projection.v1"
PROJECTION_VERSION = "1.0.0"
PROFILE_KEY = ("builtin.default_compatibility", "1.0.0")
PROFILE_DEFINITIONS: dict[tuple[str, str], dict[str, Any]] = {
  PROFILE_KEY: {
    "required_capabilities": ["deterministic.step", "runtime.world_batch.cpu"],
    "required_policies": ["native_step_authority", "no_mid_episode_truth_reconfiguration"],
    "required_categories": list(projection.CATEGORIES),
  },
}

PROJECTION_FIXTURE_PATH = REPO_ROOT / (
  "tests/architecture/composition/fixtures/default_runtime_profile_projection.v1.json"
)
PROJECTION_SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/runtime_profile_projection.v1.schema.json"
)
INVALID_MATRIX_PATH = REPO_ROOT / (
  "tests/architecture/composition/fixtures/invalid_profile_projection_matrix.v1.json"
)


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


def _payload(value: dict[str, Any]) -> dict[str, Any]:
  return {key: item for key, item in value.items() if key not in {"canonical_json", "projection_sha256"}}


def projection_identity(value: dict[str, Any]) -> str:
  return low_level.canonical_sha256(_payload(_normalize(value)))


def _normalize(value: dict[str, Any]) -> dict[str, Any]:
  normalized = low_level._normalize_value(deepcopy(value), "$")
  normalized["required_capabilities"] = sorted(
    set(normalized["required_capabilities"]), key=lambda item: item.encode("utf-8")
  )
  normalized["required_policies"] = sorted(
    set(normalized["required_policies"]), key=lambda item: item.encode("utf-8")
  )
  normalized["catalog_entries"] = sorted(
    (
      {
        **item,
        "capabilities": sorted(
          set(item["capabilities"]), key=lambda capability: capability.encode("utf-8")
        ),
      }
      for item in normalized["catalog_entries"]
    ),
    key=lambda item: (item["category"].encode("utf-8"), item["descriptor_id"].encode("utf-8")),
  )
  normalized["component_contributions"] = sorted(
    normalized["component_contributions"],
    key=lambda item: item["component_id"].encode("utf-8"),
  )
  # System order is executable semantics, so this array is intentionally not
  # sorted.  It is copied from the native resolved artifact's order.
  normalized["compatibility_claims"] = sorted(
    set(normalized["compatibility_claims"]), key=lambda item: item.encode("utf-8")
  )
  return normalized


def _validate_exact_object(
  value: Any,
  path: str,
  fields: set[str],
  issues: list[ValidationIssue],
) -> bool:
  if not isinstance(value, dict):
    _issue(issues, "profile.invalid_json_type", path, "expected object")
    return False
  if set(value) != fields:
    _issue(issues, "profile.invalid_shape", path, "fields do not match the v1 contract")
    return False
  return True


def _validate_string(
  value: Any,
  path: str,
  issues: list[ValidationIssue],
  *,
  pattern: Any | None = None,
) -> bool:
  if not isinstance(value, str):
    _issue(issues, "profile.invalid_json_type", path, "expected string")
    return False
  if not value or not value.isascii() or (pattern is not None and pattern.fullmatch(value) is None):
    _issue(issues, "profile.invalid_value", path, "expected a non-empty ASCII contract value")
    return False
  return True


def _validate_string_array(
  value: Any,
  path: str,
  issues: list[ValidationIssue],
) -> bool:
  if not isinstance(value, list):
    _issue(issues, "profile.invalid_json_type", path, "expected string array")
    return False
  valid = True
  for index, item in enumerate(value):
    valid = _validate_string(item, f"{path}[{index}]", issues) and valid
  if valid and len(value) != len(set(value)):
    _issue(issues, "profile.invalid_value", path, "string array values must be unique")
    valid = False
  return valid


def _validate_projection_shape(value: dict[str, Any]) -> list[ValidationIssue]:
  issues: list[ValidationIssue] = []
  fields = set(profile_schema()["required"])
  if not _validate_exact_object(value, "$", fields, issues):
    return sorted(issues)

  for field in (
    "schema_version", "projection_id", "canonicalization", "hash_algorithm", "canonical_json",
  ):
    _validate_string(value[field], f"$.{field}", issues)
  _validate_string(value["projection_version"], "$.projection_version", issues, pattern=low_level.VERSION_RE)
  for field in ("request_sha256", "lock_sha256", "authority_registry_sha256", "projection_sha256"):
    _validate_string(value[field], f"$.{field}", issues, pattern=low_level.HEX64_RE)

  profile = value["requested_profile"]
  if _validate_exact_object(profile, "$.requested_profile", {"profile_id", "profile_version"}, issues):
    _validate_string(profile["profile_id"], "$.requested_profile.profile_id", issues)
    _validate_string(
      profile["profile_version"],
      "$.requested_profile.profile_version",
      issues,
      pattern=low_level.VERSION_RE,
    )

  for field in ("required_capabilities", "required_policies", "compatibility_claims"):
    _validate_string_array(value[field], f"$.{field}", issues)

  catalog_entries = value["catalog_entries"]
  if not isinstance(catalog_entries, list):
    _issue(issues, "profile.invalid_json_type", "$.catalog_entries", "expected non-empty array")
  elif not catalog_entries:
    _issue(issues, "profile.invalid_value", "$.catalog_entries", "expected non-empty array")
  else:
    catalog_fields = {"category", "owner_id", "descriptor_id", "capabilities"}
    for index, entry in enumerate(catalog_entries):
      path = f"$.catalog_entries[{index}]"
      if not _validate_exact_object(entry, path, catalog_fields, issues):
        continue
      if not isinstance(entry["category"], str):
        _issue(issues, "profile.invalid_json_type", f"{path}.category", "expected string")
      elif entry["category"] not in projection.CATEGORIES:
        _issue(issues, "profile.invalid_value", f"{path}.category", "category is not admitted")
      _validate_string(entry["owner_id"], f"{path}.owner_id", issues)
      _validate_string(entry["descriptor_id"], f"{path}.descriptor_id", issues)
      _validate_string_array(entry["capabilities"], f"{path}.capabilities", issues)

  components = value["component_contributions"]
  if not isinstance(components, list):
    _issue(issues, "profile.invalid_json_type", "$.component_contributions", "expected non-empty array")
  elif not components:
    _issue(issues, "profile.invalid_value", "$.component_contributions", "expected non-empty array")
  else:
    component_fields = {"component_id", "registration_id"}
    for index, row in enumerate(components):
      path = f"$.component_contributions[{index}]"
      if not _validate_exact_object(row, path, component_fields, issues):
        continue
      _validate_string(row["component_id"], f"{path}.component_id", issues)
      _validate_string(row["registration_id"], f"{path}.registration_id", issues)

  systems = value["system_contributions"]
  if not isinstance(systems, list):
    _issue(issues, "profile.invalid_json_type", "$.system_contributions", "expected non-empty array")
  elif not systems:
    _issue(issues, "profile.invalid_value", "$.system_contributions", "expected non-empty array")
  else:
    system_fields = {"contribution_id", "stage_order"}
    for index, row in enumerate(systems):
      path = f"$.system_contributions[{index}]"
      if not _validate_exact_object(row, path, system_fields, issues):
        continue
      _validate_string(row["contribution_id"], f"{path}.contribution_id", issues)
      if isinstance(row["stage_order"], bool) or not isinstance(row["stage_order"], int):
        _issue(issues, "profile.invalid_json_type", f"{path}.stage_order", "expected integer")
      elif row["stage_order"] < 0:
        _issue(issues, "profile.invalid_value", f"{path}.stage_order", "expected non-negative integer")

  return sorted(issues)


def profile_schema() -> dict[str, Any]:
  string = {"type": "string", "minLength": 1, "pattern": low_level.ASCII_PATTERN}
  version = {"type": "string", "pattern": low_level.VERSION_RE.pattern}
  profile = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"profile_id": string, "profile_version": version},
    "required": ["profile_id", "profile_version"],
  }
  catalog_entry = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "category": {"enum": list(projection.CATEGORIES)},
      "owner_id": string,
      "descriptor_id": string,
      "capabilities": {"type": "array", "items": string, "uniqueItems": True},
    },
    "required": ["category", "owner_id", "descriptor_id", "capabilities"],
  }
  component = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"component_id": string, "registration_id": string},
    "required": ["component_id", "registration_id"],
  }
  system = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"contribution_id": string, "stage_order": {"type": "integer", "minimum": 0}},
    "required": ["contribution_id", "stage_order"],
  }
  return {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": SCHEMA_VERSION,
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "schema_version": {"const": SCHEMA_VERSION},
      "projection_id": string,
      "projection_version": version,
      "requested_profile": profile,
      "request_sha256": {"type": "string", "pattern": low_level.HEX64_RE.pattern},
      "lock_sha256": {"type": "string", "pattern": low_level.HEX64_RE.pattern},
      "authority_registry_sha256": {"type": "string", "pattern": low_level.HEX64_RE.pattern},
      "required_capabilities": {"type": "array", "items": string, "uniqueItems": True},
      "required_policies": {"type": "array", "items": string, "uniqueItems": True},
      "catalog_entries": {"type": "array", "items": catalog_entry, "minItems": 1},
      "component_contributions": {"type": "array", "items": component, "minItems": 1},
      "system_contributions": {"type": "array", "items": system, "minItems": 1},
      "compatibility_claims": {"type": "array", "items": string, "uniqueItems": True},
      "canonicalization": {"const": projection.CANONICALIZATION_ID},
      "hash_algorithm": {"const": projection.HASH_ALGORITHM},
      "canonical_json": string,
      "projection_sha256": {"type": "string", "pattern": low_level.HEX64_RE.pattern},
    },
    "required": [
      "schema_version", "projection_id", "projection_version", "requested_profile",
      "request_sha256", "lock_sha256", "authority_registry_sha256",
      "required_capabilities", "required_policies", "catalog_entries",
      "component_contributions", "system_contributions", "compatibility_claims",
      "canonicalization", "hash_algorithm", "canonical_json", "projection_sha256",
    ],
  }


def build_profile_projection(
  request: dict[str, Any],
  lock: dict[str, Any],
  requested_manifest: dict[str, Any],
  resolved_manifest: dict[str, Any],
) -> dict[str, Any]:
  profile = request.get("requested_profile") if isinstance(request, dict) else None
  key = (
    profile.get("profile_id"), profile.get("profile_version")
  ) if isinstance(profile, dict) else (None, None)
  definition = PROFILE_DEFINITIONS.get(key)
  if definition is None:
    raise ContractError([ValidationIssue("profile.unadmitted", "$.requested_profile", "profile is not owner-admitted")])
  if (
    not isinstance(request, dict)
    or request.get("required_capabilities") != definition["required_capabilities"]
    or request.get("required_policies") != definition["required_policies"]
  ):
    raise ContractError([ValidationIssue(
      "profile.capability_policy_mismatch", "$.requested_profile", "profile alias does not match its admitted capability/policy set",
    )])
  request_issues = projection.validate_request(request)
  lock_issues = projection.validate_catalog_lock(lock, request=request)
  if request_issues or lock_issues:
    raise ContractError([
      ValidationIssue(issue.code, f"request.{issue.path}", issue.detail)
      for issue in request_issues
    ] + [
      ValidationIssue(issue.code, f"lock.{issue.path}", issue.detail)
      for issue in lock_issues
    ])
  if request["required_capabilities"] != definition["required_capabilities"] or \
      request["required_policies"] != definition["required_policies"]:
    raise ContractError([ValidationIssue(
      "profile.capability_policy_mismatch", "$.requested_profile", "profile alias does not match its admitted capability/policy set",
    )])
  manifest = resolved_manifest.get("manifest", resolved_manifest)
  requested = requested_manifest.get("manifest", requested_manifest)
  if manifest != requested:
    raise ContractError([ValidationIssue("profile.manifest_mismatch", "$.manifest", "requested and resolved payloads differ")])
  catalog_entries = []
  for category in definition["required_categories"]:
    matches = [entry for entry in lock["entries"] if entry["category"] == category]
    if len(matches) != 1:
      raise ContractError([ValidationIssue("profile.category_admission", f"$.catalog_entries.{category}", "profile requires exactly one owner-admitted entry")])
    entry = matches[0]
    catalog_entries.append({
      "category": entry["category"],
      "owner_id": entry["owner_id"],
      "descriptor_id": entry["descriptor_id"],
      "capabilities": entry["capabilities"],
    })
  components = [
    {"component_id": row["component_id"], "registration_id": row["registration_id"]}
    for row in low_level.normalize_manifest(manifest)["component_contributions"]
  ]
  system_order = list(resolved_manifest.get("system_registration_order", []))
  systems = [
    {"contribution_id": contribution_id, "stage_order": index}
    for index, contribution_id in enumerate(system_order)
  ]
  payload: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "projection_id": f"{profile['profile_id']}.projection",
    "projection_version": PROJECTION_VERSION,
    "requested_profile": profile,
    "request_sha256": projection.request_identity(request),
    "lock_sha256": lock["lock_sha256"],
    "authority_registry_sha256": lock["authority_registry_sha256"],
    "required_capabilities": definition["required_capabilities"],
    "required_policies": definition["required_policies"],
    "catalog_entries": catalog_entries,
    "component_contributions": components,
    "system_contributions": systems,
    "compatibility_claims": manifest.get("compatibility_claims", []),
    "canonicalization": projection.CANONICALIZATION_ID,
    "hash_algorithm": projection.HASH_ALGORITHM,
  }
  normalized = _normalize(payload)
  payload["canonical_json"] = low_level.canonical_json_bytes(_payload(normalized)).decode("utf-8")
  payload["projection_sha256"] = projection_identity(payload)
  return _normalize(payload)


def validate_profile_projection(
  value: Any,
  request: dict[str, Any],
  lock: dict[str, Any],
  requested_manifest: dict[str, Any],
  resolved_manifest: dict[str, Any],
) -> list[ValidationIssue]:
  issues: list[ValidationIssue] = []
  if not isinstance(value, dict):
    return [ValidationIssue("profile.invalid_json_type", "$", "expected object")]
  shape_issues = _validate_projection_shape(value)
  if shape_issues:
    return shape_issues
  try:
    expected_value = build_profile_projection(request, lock, requested_manifest, resolved_manifest)
  except ContractError as error:
    return [ValidationIssue(issue.code, issue.path, issue.detail) for issue in error.issues]
  if value != expected_value:
    _issue(issues, "profile.projection_mismatch", "$", "projection is not the owner-derived request/lock/manifest join")
  try:
    if value.get("projection_sha256") != projection_identity(value):
      _issue(issues, "profile.identity_mismatch", "$.projection_sha256", "does not match canonical projection payload")
    if value.get("canonical_json") != low_level.canonical_json_bytes(_payload(_normalize(value))).decode("utf-8"):
      _issue(issues, "profile.canonical_bytes_mismatch", "$.canonical_json", "does not match canonical projection payload")
  except (KeyError, TypeError, ValueError, UnicodeError) as error:
    _issue(issues, "profile.invalid_json_type", "$", f"projection cannot be canonicalized: {error}")
  return sorted(issues)


def _pretty(value: Any) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def generate() -> None:
  fixture_dir = REPO_ROOT / "tests/architecture/composition/fixtures"
  request = json.loads((fixture_dir / "default_runtime_composition_request.v1.json").read_text(encoding="utf-8"))
  lock = json.loads((fixture_dir / "default_admitted_catalog_lock.v1.json").read_text(encoding="utf-8"))
  requested = json.loads((fixture_dir / "default_compatibility_manifest.requested.json").read_text(encoding="utf-8"))
  resolved = json.loads((fixture_dir / "default_compatibility_manifest.resolved.json").read_text(encoding="utf-8"))
  PROJECTION_FIXTURE_PATH.write_text(_pretty(build_profile_projection(request, lock, requested, resolved)), encoding="utf-8", newline="\n")
  PROJECTION_SCHEMA_PATH.write_text(_pretty(profile_schema()), encoding="utf-8", newline="\n")
  INVALID_MATRIX_PATH.write_text(_pretty({
    "projection_fixture": PROJECTION_FIXTURE_PATH.name,
    "cases": [
      {"path": "/requested_profile/profile_id", "value": "attacker.profile", "code": "profile.projection_mismatch"},
      {"path": "/required_capabilities/0", "value": "attacker.capability", "code": "profile.projection_mismatch"},
      {"path": "/required_policies/0", "value": "attacker.policy", "code": "profile.projection_mismatch"},
      {"path": "/catalog_entries/0/owner_id", "value": "owner.attacker", "code": "profile.projection_mismatch"},
      {"path": "/component_contributions/0/registration_id", "value": "attacker.registration", "code": "profile.projection_mismatch"},
      {"path": "/system_contributions/0/stage_order", "value": 99, "code": "profile.projection_mismatch"},
      {"path": "/compatibility_claims/0", "value": "attacker.claim", "code": "profile.projection_mismatch"},
      {"path": "/required_capabilities", "value": 7, "code": "profile.invalid_json_type"},
      {"path": "/required_policies", "value": None, "code": "profile.invalid_json_type"},
      {"path": "/catalog_entries", "value": "not-an-array", "code": "profile.invalid_json_type"},
      {"path": "/catalog_entries/0/capabilities", "value": 7, "code": "profile.invalid_json_type"},
      {"path": "/component_contributions/0", "value": False, "code": "profile.invalid_json_type"},
      {"path": "/system_contributions/0/stage_order", "value": False, "code": "profile.invalid_json_type"},
      {"path": "/compatibility_claims", "value": False, "code": "profile.invalid_json_type"},
    ],
  }), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("command", choices=("generate", "validate"))
  parser.add_argument("--projection", type=Path)
  args = parser.parse_args(argv)
  if args.command == "generate":
    generate()
    return 0
  if args.projection is None:
    raise SystemExit("validate requires --projection")
  fixture_dir = REPO_ROOT / "tests/architecture/composition/fixtures"
  value = json.loads(args.projection.read_text(encoding="utf-8"))
  request = json.loads((fixture_dir / "default_runtime_composition_request.v1.json").read_text(encoding="utf-8"))
  lock = json.loads((fixture_dir / "default_admitted_catalog_lock.v1.json").read_text(encoding="utf-8"))
  requested = json.loads((fixture_dir / "default_compatibility_manifest.requested.json").read_text(encoding="utf-8"))
  resolved = json.loads((fixture_dir / "default_compatibility_manifest.resolved.json").read_text(encoding="utf-8"))
  issues = validate_profile_projection(value, request, lock, requested, resolved)
  if issues:
    for issue in issues:
      print(f"{issue.code}@{issue.path}: {issue.detail}")
    return 1
  print(value["projection_sha256"])
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
