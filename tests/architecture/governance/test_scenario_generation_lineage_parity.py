"""Serialization-order gate for the scenario-generation lineage vocabulary.

This vocabulary once had three faces held to one declarative owner: a C++
struct, the generated X-macro .inc fragment it included, and the Python
dataclasses in python/scenario/compiler/generation_request.py. The C++ face
(src/runtime/contracts/counterfactual_replay_contract_types.h) was retired
with the maintained-evidence/counterfactual producers, which left the .inc
fragment with zero #include sites and its DtoSchema module with no consumer
but this gate. Both have now been retired too: a DtoSchema declares C++
member order, and keeping one alive purely to describe a Python dataclass was
describing the wrong language.

What survives is the face that still has consumers. ``to_metadata()`` emits
the request lineage into scenario-generation artifacts, so its key ORDER is a
serialization contract even though there is no longer an ABI behind it, and
tests/scenario/test_scenario_generation_contracts.py compares whole metadata
dicts -- which is order-insensitive. So the order pin lives here, against the
tables below.

Those tables are the anchor now rather than a projection of a shared owner:
adding or reordering a field means editing the dataclass and the table
together, deliberately. Two things went away with the C++ face and are not
coming back through this gate: the ``has_deterministic_seed`` presence flag,
which never had a Python counterpart (the dataclass encodes presence
structurally by requiring ``deterministic_seed``), and the schema==.inc
field-equality check, which had no .inc left to check.

Still held: the constructor parameter order deviates from the serialization
order because dataclasses require defaulted parameters last. That permutation
is pinned below rather than "fixed", since reordering keyword-capable
parameters is a public API change.
"""

from __future__ import annotations

from dataclasses import MISSING, fields as dataclass_fields
from functools import cache
from types import ModuleType


@cache
def _generation_request_face() -> ModuleType:
  """Import the Python face on first use rather than at collection time.

  ``python.scenario.compiler`` imports ``ef_py``, so the local build has to be
  on the path first. ``tests/conftest.py`` already does that at
  ``pytest_configure``; ``ensure_repo_imports`` is re-entrant but rescans the
  build directories and PATH on every call, so repeating it at module import
  time charged every collect of this directory for a bootstrap that had
  already happened.
  """
  from python.runtime_bootstrap import ensure_repo_imports

  ensure_repo_imports()

  from python.scenario.compiler import generation_request

  return generation_request


# Sentinel for the one default that is a module constant, not a literal.
_CONTRACT_VERSION = object()

# (field name, constructor default) in ``to_metadata()`` key order.
# ``MISSING`` marks a required constructor argument.
EVIDENCE_REF_FIELDS: tuple[tuple[str, object], ...] = (
  ("ref_id", MISSING),
  ("evidence_kind", MISSING),
  ("provenance_label", ""),
)

REQUEST_FIELDS: tuple[tuple[str, object], ...] = (
  ("request_id", MISSING),
  ("request_version", "1"),
  ("contract_version", _CONTRACT_VERSION),
  ("generation_kind", MISSING),
  ("source", MISSING),
  ("generator_version", MISSING),
  ("deterministic_seed", MISSING),
  ("baseline_scenario_ref", MISSING),
  ("replay_envelope_ref", ""),
  ("branch_point_ref", ""),
  ("capability_refs", ()),
  ("evidence_refs", ()),
)


def _expected_default(default: object) -> object:
  if default is _CONTRACT_VERSION:
    return _generation_request_face().SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION
  return default


def _assert_python_face_matches_table(
  table: tuple[tuple[str, object], ...],
  dataclass_type: type,
) -> None:
  pinned_names = [name for name, _ in table]
  py_fields = dataclass_fields(dataclass_type)
  py_names = [field.name for field in py_fields]
  assert sorted(py_names) == sorted(pinned_names)

  defaulted = {name for name, default in table if default is not MISSING}
  expected_permutation = [
    name for name in pinned_names if name not in defaulted
  ] + [name for name in pinned_names if name in defaulted]
  assert py_names == expected_permutation

  pinned_by_name = dict(table)
  for py_field in py_fields:
    pinned_default = pinned_by_name[py_field.name]
    if pinned_default is MISSING:
      assert py_field.default is MISSING, (
        f"{dataclass_type.__name__}.{py_field.name} gained a default; it is "
        "pinned as a required constructor argument"
      )
      continue
    assert py_field.default is not MISSING, (
      f"{dataclass_type.__name__}.{py_field.name} lost its default"
    )
    assert py_field.default == _expected_default(pinned_default), (
      f"default mismatch for {dataclass_type.__name__}.{py_field.name}"
    )


def test_python_faces_match_pinned_names_and_defaults() -> None:
  face = _generation_request_face()
  _assert_python_face_matches_table(
    EVIDENCE_REF_FIELDS, face.ScenarioGenerationEvidenceRef
  )
  _assert_python_face_matches_table(
    REQUEST_FIELDS, face.ScenarioGenerationRequest
  )


def test_python_serialization_order_and_values_follow_pinned_order() -> None:
  face = _generation_request_face()
  evidence = face.ScenarioGenerationEvidenceRef(
    ref_id="replay-envelope-1",
    evidence_kind="replay_envelope",
    provenance_label="maintained-run",
  )
  evidence_metadata = evidence.to_metadata()
  assert list(evidence_metadata) == [name for name, _ in EVIDENCE_REF_FIELDS]
  assert evidence_metadata == {
    "ref_id": "replay-envelope-1",
    "evidence_kind": "replay_envelope",
    "provenance_label": "maintained-run",
  }

  request = face.ScenarioGenerationRequest(
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
  assert list(metadata) == [name for name, _ in REQUEST_FIELDS]
  assert metadata == {
    "request_id": "req-1",
    "request_version": "1",
    "contract_version": face.SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION,
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
