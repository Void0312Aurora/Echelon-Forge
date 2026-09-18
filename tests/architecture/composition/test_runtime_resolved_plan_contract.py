from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from tools.maintenance import runtime_resolved_plan_contract as plan


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "architecture" / "composition" / "fixtures"


def _read(name: str) -> dict:
  return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _inputs() -> tuple[dict, ...]:
  return tuple(_read(name) for name in (
    "default_runtime_composition_request.v1.json",
    "default_admitted_catalog_lock.v1.json",
    "default_runtime_profile_projection.v1.json",
    "default_backend_provider_request.v1.json",
    "default_compatibility_manifest.requested.json",
    "default_compatibility_manifest.resolved.json",
  ))


def test_closed_plan_fixture_is_owner_derived_and_schema_valid() -> None:
  value = _read("default_resolved_execution_plan.v1.json")
  expected = plan.build_closed_plan(*_inputs())
  assert value == expected
  assert plan.SCHEMA_PATH.read_text(encoding="utf-8") == plan._pretty(plan.plan_schema())
  jsonschema.Draft202012Validator(plan.plan_schema()).validate(value)
  plan.validate_closed_plan(value, *_inputs())
  assert value["authority_payload_bytes"]["authority_kind"] == "resolved_execution_plan"
  assert set(value["input_bindings"]) == {
    "request_sha256", "catalog_lock_sha256", "profile_projection_sha256",
    "backend_request_sha256", "requested_manifest_sha256", "resolved_manifest_sha256",
  }
  assert plan.GENERATED_HEADER_PATH.read_text(encoding="utf-8") == plan.generated_header(value)


@pytest.mark.parametrize("path", [
  "/input_bindings/catalog_lock_sha256",
  "/input_bindings/profile_projection_sha256",
  "/input_bindings/backend_request_sha256",
  "/owner_join/backend_provider_id",
])
def test_closed_plan_rejects_any_owner_join_mutation(path: str) -> None:
  value = copy.deepcopy(_read("default_resolved_execution_plan.v1.json"))
  parts = path.strip("/").split("/")
  target = value
  for part in parts[:-1]:
    target = target[part]
  target[parts[-1]] = "0" * 64 if path.endswith("sha256") else "attacker.provider"
  with pytest.raises(plan.ClosedPlanError):
    plan.validate_closed_plan(value, *_inputs())


def test_closed_plan_rejects_stale_projection_even_when_legacy_manifest_is_unchanged() -> None:
  value = copy.deepcopy(_read("default_resolved_execution_plan.v1.json"))
  projection_value = copy.deepcopy(_inputs()[2])
  projection_value["compatibility_claims"] = ["attacker.claim"]
  with pytest.raises(plan.ClosedPlanError, match="profile projection validation"):
    plan.validate_closed_plan(value, _inputs()[0], _inputs()[1], projection_value, *_inputs()[3:])


def test_closed_plan_does_not_admit_hidden_default_or_backend_substitution() -> None:
  backend = copy.deepcopy(_inputs()[3])
  backend["provider_id"] = "builtin.attacker"
  with pytest.raises(plan.ClosedPlanError, match="backend request"):
    plan.build_closed_plan(*_inputs()[:3], backend, *_inputs()[4:])


def test_closed_plan_binds_backend_implementation_to_admitted_catalog_entry() -> None:
  backend = copy.deepcopy(_inputs()[3])
  backend["provider_implementation_version"] = "9.9.9"
  with pytest.raises(plan.ClosedPlanError, match="admitted catalog backend entry"):
    plan.build_closed_plan(*_inputs()[:3], backend, *_inputs()[4:])
