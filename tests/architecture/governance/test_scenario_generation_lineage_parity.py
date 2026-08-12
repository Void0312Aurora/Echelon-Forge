"""Cross-language parity gate for the scenario-generation lineage vocabulary.

The shared schema owner (T10 census VA-6) lives in
tools/maintenance/dto_schema/schemas/scenario/scenario_generation_request_metadata_fields.py
and .../scenario_generation_evidence_ref_fields.py. This gate holds both
language faces to that owner:

- C++ face: the header
  src/runtime/contracts/counterfactual_replay_contract_types.h now includes
  the generated .inc fragments at the structs' original seams (the
  mechanical include swap deferred from the initial slice landed this
  iteration), so the compiled member list IS the generated rendering. The
  gate therefore no longer parses hand-written member declarations
  (ADJUDICATED: a hand-written-member parser would only re-verify text the
  generator owns). Instead it verifies (a) SEAM ADOPTION — each struct body
  is exactly the field macro definition plus the ``#include`` of the
  schema's registered output, so no hand-written member can bypass the
  schema owner — and (b) SCHEMA==INC — the checked-in .inc field list
  equals the schema (name, type, default, and field ORDER — order is ABI),
  so this gate stays meaningful in isolation. Byte-exact freshness of the
  .inc AND the generated Python builder against the schema
  (generated-source-of-truth == .inc == Python builder) is owned by
  tests/architecture/governance/test_dto_schema_freshness.py via
  ``generate.py --check``.
- Python face: ``ScenarioGenerationEvidenceRef`` and
  ``ScenarioGenerationRequest`` in
  python/scenario/compiler/generation_request.py must expose exactly the
  schema's field names (minus the held C++-only ``has_deterministic_seed``
  presence flag), with matching defaults, and ``to_metadata()`` must emit
  keys in the schema's ABI order.

The Python face intentionally does not import the generated builder at
runtime: python/scenario does not import gym_envs today, and this gate must
not create a new runtime import direction — parity is enforced here instead.
"""

from __future__ import annotations

from dataclasses import MISSING, fields as dataclass_fields
from pathlib import Path
import re

import pytest

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from python.scenario.compiler.generation_request import (  # noqa: E402
  SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION,
  ScenarioGenerationEvidenceRef,
  ScenarioGenerationRequest,
)
from tools.maintenance.dto_schema.schemas.scenario.scenario_generation_evidence_ref_fields import (  # noqa: E402
  SCHEMA as EVIDENCE_REF_SCHEMA,
)
from tools.maintenance.dto_schema.parse_xmacro import parse_xmacro_text  # noqa: E402
from tools.maintenance.dto_schema.schemas.scenario.scenario_generation_request_metadata_fields import (  # noqa: E402
  SCHEMA as REQUEST_METADATA_SCHEMA,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_TYPES_HEADER = (
  REPO_ROOT / "src" / "runtime" / "contracts" / "counterfactual_replay_contract_types.h"
)
CONTRACT_CONSTANTS_HEADER = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_contract_constants.h"
)

# Held verdict (see the schema module docstring): the C++ presence flag has
# no Python counterpart; the Python face requires deterministic_seed
# structurally and serializes without the flag.
CPP_ONLY_PRESENCE_FLAG = "has_deterministic_seed"


def _cpp_struct_body_lines(header_text: str, struct_name: str) -> list[str]:
  match = re.search(
    rf"struct {struct_name} \{{\n(.*?)\n\}};", header_text, re.DOTALL
  )
  assert match is not None, f"struct {struct_name} not found in {CONTRACT_TYPES_HEADER}"
  physical_lines = [line.strip() for line in match.group(1).splitlines()]
  logical_lines: list[str] = []
  continuation = ""
  for line in physical_lines:
    if continuation:
      assert line, f"blank line after line continuation in {struct_name}"
      line = f"{continuation} {line}"
      continuation = ""
    if not line:
      continue
    if line.endswith("\\"):
      continuation = line[:-1].rstrip()
    else:
      logical_lines.append(" ".join(line.split()))
  assert not continuation, f"unterminated preprocessor directive in {struct_name}"
  return logical_lines


def _schema_members(schema) -> list[tuple[str, str, str]]:
  return [(field.cpp_type, field.name, field.default) for field in schema.fields]


def _schema_field_macro(schema) -> str:
  groups = {field.group for field in schema.fields}
  assert len(groups) == 1, f"{schema.name} fields must share one macro group"
  return next(iter(groups))


def _assert_cpp_seam_adopts_generated_include(struct_name: str, schema) -> None:
  """The struct body must be exactly the field-macro define + .inc include.

  With the generated include at the original seam, the compiled member list
  is the schema's rendering by construction; any hand-written member added
  next to the include would break this exact-logical-body check. Preprocessor
  continuation and whitespace are normalized so clang-format does not turn
  a physical-line change into a false governance failure. A blank line after
  a continuation fails closed because it terminates a C++ macro definition.
  """
  header_text = CONTRACT_TYPES_HEADER.read_text(encoding="utf-8")
  macro = _schema_field_macro(schema)
  assert schema.output_path.startswith("src/")
  include_path = schema.output_path[len("src/"):]
  assert _cpp_struct_body_lines(header_text, struct_name) == [
    f"#define {macro}(type, name, default_value) type name = default_value;",
    f'#include "{include_path}"',
  ]


def _parsed_inc_members(schema) -> list[tuple[str, str, str]]:
  inc_path = REPO_ROOT / schema.output_path
  inc_text = inc_path.read_text(encoding="utf-8")
  parsed = parse_xmacro_text(inc_text, frozenset({_schema_field_macro(schema)}))
  return [(field.cpp_type, field.name, field.default) for field in parsed.fields]


def test_cpp_seams_adopt_generated_includes() -> None:
  _assert_cpp_seam_adopts_generated_include(
    "ScenarioGenerationEvidenceMetadataRef", EVIDENCE_REF_SCHEMA
  )
  _assert_cpp_seam_adopts_generated_include(
    "ScenarioGenerationRequestMetadata", REQUEST_METADATA_SCHEMA
  )


def test_cpp_seam_parser_rejects_blank_macro_continuation() -> None:
  macro = "#define EF_SYNTHETIC_FIELD(type, name, default_value)"
  include = '#include "runtime/contracts/detail/synthetic.inc"'
  header_text = (
    "struct Synthetic {\n\n"
    f"{macro} \\\n"
    "    type name = default_value;\n\n"
    f"{include}\n\n"
    "};"
  )
  assert _cpp_struct_body_lines(header_text, "Synthetic") == [
    f"{macro} type name = default_value;",
    include,
  ]

  malformed_header = header_text.replace(
    f"{macro} \\\n", f"{macro} \\\n\n"
  )
  with pytest.raises(AssertionError, match="blank line after line continuation"):
    _cpp_struct_body_lines(malformed_header, "Synthetic")


def test_checked_in_incs_match_schema_names_types_defaults_and_order() -> None:
  # Field-level re-verification so this gate stands alone; byte-exact
  # freshness (including the generated Python builder) is owned by
  # test_dto_schema_freshness.py via generate.py --check.
  assert _parsed_inc_members(EVIDENCE_REF_SCHEMA) == _schema_members(
    EVIDENCE_REF_SCHEMA
  )
  assert _parsed_inc_members(REQUEST_METADATA_SCHEMA) == _schema_members(
    REQUEST_METADATA_SCHEMA
  )


def test_contract_version_constant_value_parity() -> None:
  constants_text = CONTRACT_CONSTANTS_HEADER.read_text(encoding="utf-8")
  match = re.search(
    r'kScenarioGenerationContractVersionRequestV1\s*=\s*"([^"]+)"',
    constants_text,
  )
  assert match is not None
  assert match.group(1) == SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION
  # The schema's C++ default expression names exactly that constant.
  contract_field = next(
    field
    for field in REQUEST_METADATA_SCHEMA.fields
    if field.name == "contract_version"
  )
  assert contract_field.default == (
    "std::string(kScenarioGenerationContractVersionRequestV1)"
  )


def _python_default_for_schema_field(field) -> object:
  if field.name == "contract_version":
    return SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION
  if field.cpp_type == "std::string":
    assert field.default.startswith('"') and field.default.endswith('"')
    return field.default[1:-1]
  if field.cpp_type.startswith("std::vector<"):
    assert field.default == "{}"
    return ()
  raise AssertionError(f"no Python default mapping for {field.name}: {field.cpp_type}")


def _assert_python_face_matches_schema(schema, dataclass_type) -> None:
  schema_names = [
    field.name for field in schema.fields if field.name != CPP_ONLY_PRESENCE_FLAG
  ]
  py_fields = dataclass_fields(dataclass_type)
  py_names = [field.name for field in py_fields]
  assert sorted(py_names) == sorted(schema_names)

  # Held verdict: the constructor permutation is the schema (ABI) order
  # stably partitioned into required-then-defaulted, as dataclasses require;
  # serialization order (checked separately) follows the ABI order itself.
  defaulted = {
    field.name for field in py_fields if field.default is not MISSING
  }
  expected_permutation = [
    name for name in schema_names if name not in defaulted
  ] + [name for name in schema_names if name in defaulted]
  assert py_names == expected_permutation

  schema_by_name = {field.name: field for field in schema.fields}
  for py_field in py_fields:
    if py_field.default is MISSING:
      continue
    assert py_field.default == _python_default_for_schema_field(
      schema_by_name[py_field.name]
    ), f"default mismatch for {dataclass_type.__name__}.{py_field.name}"


def test_python_faces_match_schema_names_and_defaults() -> None:
  _assert_python_face_matches_schema(
    EVIDENCE_REF_SCHEMA, ScenarioGenerationEvidenceRef
  )
  _assert_python_face_matches_schema(
    REQUEST_METADATA_SCHEMA, ScenarioGenerationRequest
  )


def test_python_serialization_order_and_values_follow_schema() -> None:
  evidence = ScenarioGenerationEvidenceRef(
    ref_id="replay-envelope-1",
    evidence_kind="replay_envelope",
    provenance_label="maintained-run",
  )
  evidence_metadata = evidence.to_metadata()
  assert list(evidence_metadata) == [
    field.name for field in EVIDENCE_REF_SCHEMA.fields
  ]
  assert evidence_metadata == {
    "ref_id": "replay-envelope-1",
    "evidence_kind": "replay_envelope",
    "provenance_label": "maintained-run",
  }

  request = ScenarioGenerationRequest(
    request_id="req-1",
    generation_kind="scenario_variation",
    source="counterfactual_branch",
    generator_version="gen-1.0",
    deterministic_seed=7,
    baseline_scenario_ref="baseline-1",
    replay_envelope_ref="replay-envelope-1",
    branch_point_ref="branch-point-1",
    capability_refs=("cap-a",),
    evidence_refs=(evidence,),
  )
  metadata = request.to_metadata()
  assert list(metadata) == [
    field.name
    for field in REQUEST_METADATA_SCHEMA.fields
    if field.name != CPP_ONLY_PRESENCE_FLAG
  ]
  assert metadata == {
    "request_id": "req-1",
    "request_version": "1",
    "contract_version": SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION,
    "generation_kind": "scenario_variation",
    "source": "counterfactual_branch",
    "generator_version": "gen-1.0",
    "deterministic_seed": 7,
    "baseline_scenario_ref": "baseline-1",
    "replay_envelope_ref": "replay-envelope-1",
    "branch_point_ref": "branch-point-1",
    "capability_refs": ["cap-a"],
    "evidence_refs": [evidence_metadata],
  }
