from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

from tools.maintenance.runtime_authority_contracts import AUTHORITY_SPECS


ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "src" / "runtime" / "contracts" / "authority" / "authority_payloads.v1.schema.json"
VECTOR = ROOT / "tests" / "architecture" / "composition" / "fixtures" / "authority_cross_language_vector.v1.json"
VECTOR_NAMES = (
  "authority_resolved_composition_plan.v1.json",
  "authority_cross_language_vector.v1.json",
  "authority_rollout_decision.v1.json",
  "authority_state_checkpoint.v1.json",
)


def test_authority_schema_selector_and_python_required_fields_are_one_surface() -> None:
  schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
  assert len(schema["oneOf"]) == 4
  for kind, spec in AUTHORITY_SPECS.items():
    definition = schema["$defs"][kind]
    assert set(definition["required"]) == set(spec.required_fields)
    assert definition["additionalProperties"] is False


def test_cross_language_vector_is_referenced_by_all_three_lanes() -> None:
  for name in VECTOR_NAMES:
    vector_text = (VECTOR.parent / name).read_text(encoding="utf-8")
    assert '"vector_kind": "authority_envelope_v1"' in vector_text
  python_test = (ROOT / "tests" / "architecture" / "composition" / "test_runtime_authority_contracts.py").read_text(encoding="utf-8")
  cordis_test = (ROOT / "packages" / "cordis-runtime" / "test" / "authority.test.mjs").read_text(encoding="utf-8")
  native_test = (ROOT / "src" / "tests" / "test_runtime_authority_contract.cpp").read_text(encoding="utf-8")
  assert "authority_cross_language_vector.v1.json" in python_test
  assert "authority_cross_language_vector.v1.json" in cordis_test
  assert "authority_cross_language_vector.v1.json" in native_test
  assert "authority_resolved_composition_plan.v1.json" in native_test
  assert "authority_rollout_decision.v1.json" in native_test
  assert "authority_state_checkpoint.v1.json" in native_test


def test_all_checked_in_authority_vectors_are_exact_schema_and_digest_inputs() -> None:
  from tools.maintenance.runtime_authority_contracts import authority_digest_sha256, canonical_json_bytes, validate_authority_envelope

  for name in VECTOR_NAMES:
    vector = json.loads((VECTOR.parent / name).read_text(encoding="utf-8"))
    payload_bytes = vector["canonical_payload_bytes"].encode("utf-8")
    assert canonical_json_bytes(json.loads(vector["canonical_payload_bytes"])) == payload_bytes
    assert authority_digest_sha256(vector["domain"], vector["media_type"], payload_bytes) == vector["payload_sha256"]
    assert validate_authority_envelope(json.loads(vector["envelope_json"]))["payload_sha256"] == vector["payload_sha256"]


def test_authority_vectors_are_fresh_from_the_canonical_generator() -> None:
  from tools.maintenance.generate_runtime_authority_vectors import build_vectors

  for name, expected in build_vectors().items():
    assert json.loads((VECTOR.parent / name).read_text(encoding="utf-8")) == expected


def test_envelope_schema_executes_against_vector_and_rejects_unknown_payload() -> None:
  envelope_schema = json.loads((SCHEMA.parent / "authority_envelope.v1.schema.json").read_text(encoding="utf-8"))
  payload_schema = json.loads((SCHEMA.parent / "authority_payloads.v1.schema.json").read_text(encoding="utf-8"))
  payload_uri = "https://echelon-forge.local/contracts/authority/authority_payloads.v1.schema.json"
  resolver = RefResolver(base_uri=f"{SCHEMA.parent.as_uri()}/", referrer=envelope_schema, store={payload_uri: payload_schema})
  validator = Draft202012Validator(envelope_schema, resolver=resolver)
  vector = json.loads(VECTOR.read_text(encoding="utf-8"))
  validator.validate(json.loads(vector["envelope_json"]))
  invalid = json.loads(vector["envelope_json"])
  invalid["payload"]["hidden_default"] = True
  assert list(validator.iter_errors(invalid))
