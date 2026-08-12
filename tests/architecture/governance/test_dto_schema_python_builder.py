from __future__ import annotations

import importlib
import types
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
  from tools.maintenance.dto_schema.model import DtoSchema


def _load_builder_module(schema: DtoSchema, name: str) -> types.ModuleType:
  from tools.maintenance.dto_schema.python_builder import render_builder_text

  source = render_builder_text(schema)
  module = types.ModuleType(name)
  exec(compile(source, f"<generated {name}>", "exec"), module.__dict__)
  return module


class _ReadOnlyProductDto:
  """Mimics a nanobind class bound with def_ro: properties without setters."""

  @property
  def valid(self) -> bool:
    return False

  @property
  def total(self) -> float:
    return 0.0


class _MixedDto:
  """Writable plain attributes plus one def_ro-style read-only property."""

  def __init__(self) -> None:
    self.alpha = 0.0
    self.beta = 0

  @property
  def gamma(self) -> float:
    return 1.0


class _Source:
  def __init__(self, **kwargs: object) -> None:
    for key, value in kwargs.items():
      setattr(self, key, value)


def test_all_readonly_schema_generates_no_assigner() -> None:
  from tools.maintenance.dto_schema.model import DtoSchema, Field

  schema = DtoSchema(
    name="readonly_probe",
    output_path="src/fake/readonly_probe.inc",
    fields=(
      Field(name="valid", cpp_type="bool", default="false", group="EF_PROBE", readonly=True),
      Field(name="total", cpp_type="double", default="0.0", group="EF_PROBE", readonly=True),
    ),
  )
  module = _load_builder_module(schema, "readonly_probe_builder")

  assert module.FIELD_NAMES == ("valid", "total")
  assert module.WRITABLE_FIELD_NAMES == ()
  assert module.READONLY_FIELDS == frozenset({"valid", "total"})
  # Calling the assign API on an all-readonly products builder is well-defined:
  # the module exports no assigner, so attribute access raises AttributeError.
  assert not hasattr(module, "assign_from_object")
  with pytest.raises(AttributeError):
    _ = module.assign_from_object

  # Reading the def_ro-style DTO attributes still works without the builder.
  dto = _ReadOnlyProductDto()
  assert [getattr(dto, name) for name in module.FIELD_NAMES] == [False, 0.0]


def test_mixed_schema_assigner_skips_readonly_fields() -> None:
  from tools.maintenance.dto_schema.model import DtoSchema, Field

  schema = DtoSchema(
    name="mixed_probe",
    output_path="src/fake/mixed_probe.inc",
    fields=(
      Field(name="alpha", cpp_type="double", default="0.0", group="EF_PROBE"),
      Field(name="beta", cpp_type="int", default="0", group="EF_PROBE"),
      Field(name="gamma", cpp_type="double", default="1.0", group="EF_PROBE", readonly=True),
    ),
  )
  module = _load_builder_module(schema, "mixed_probe_builder")

  assert module.WRITABLE_FIELD_NAMES == ("alpha", "beta")
  assert module.READONLY_FIELDS == frozenset({"gamma"})

  source = _Source(alpha=2.5, beta=7, gamma=99.0)

  # Default field set: only writable fields are assigned; the read-only
  # property is skipped, so no AttributeError is raised.
  dto = _MixedDto()
  assert module.assign_from_object(dto, source) == 2
  assert dto.alpha == 2.5
  assert dto.beta == 7
  assert dto.gamma == 1.0

  # Explicitly listing a read-only field is equally well-defined: it is
  # skipped instead of raising.
  dto = _MixedDto()
  assert module.assign_from_object(dto, source, ("alpha", "gamma")) == 1
  assert dto.alpha == 2.5
  assert dto.beta == 0
  assert dto.gamma == 1.0


def test_generated_builders_match_schema_writability() -> None:
  from tools.maintenance.dto_schema.generate import load_schemas

  registrations = load_schemas()
  assert registrations

  all_readonly_modules = []
  readonly_field_total = 0
  for _, schema in registrations:
    module = importlib.import_module(
      f"gym_envs.scenario_loader._generated.{schema.name}_builder"
    )
    field_names = tuple(field.name for field in schema.fields)
    writable = tuple(field.name for field in schema.fields if not field.readonly)
    readonly = frozenset(field.name for field in schema.fields if field.readonly)

    assert module.FIELD_NAMES == field_names
    assert module.WRITABLE_FIELD_NAMES == writable
    assert module.READONLY_FIELDS == readonly
    assert hasattr(module, "assign_from_object") == bool(writable)

    readonly_field_total += len(readonly)
    if not writable:
      all_readonly_modules.append(schema.name)

  assert sorted(all_readonly_modules) == [
    "approach_reward_products",
    "mission_nav_products",
    "objective_products",
    "safety_runtime_products",
    "step_info_products",
    "waypoint_reward_products",
  ]
  assert readonly_field_total == 77


def test_safety_builder_call_path_unaffected() -> None:
  from gym_envs.scenario_loader._generated import safety_runtime_inputs_builder
  from gym_envs.scenario_loader.reward_runtime.safety import _CFG_FIELDS

  assert set(_CFG_FIELDS) <= set(safety_runtime_inputs_builder.WRITABLE_FIELD_NAMES)

  source = _Source(**{name: float(i) for i, name in enumerate(_CFG_FIELDS)})
  dto = _Source()
  assigned = safety_runtime_inputs_builder.assign_from_object(
    dto, source, _CFG_FIELDS
  )
  assert assigned == len(_CFG_FIELDS)
  for i, name in enumerate(_CFG_FIELDS):
    assert getattr(dto, name) == float(i)
