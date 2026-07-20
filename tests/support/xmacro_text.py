"""Shared helper for source-text-scanning tests that pin DTO field surfaces.

Several architecture/boundary-guard tests assert on the literal source text
of contract headers and ``bindings_runtime.cpp`` to pin a struct's field
inventory or a binding's registered property names. Once a field family
moves to ``tools/maintenance/dto_schema`` (see I18/I23/I26 and friends), the
field list itself lives in a generated ``.inc`` fragment and the struct body
only contains an ``#include`` line, so a raw read of the owning file no
longer contains the field tokens those tests look for.

These helpers textually expand ``#include ".../*.inc"`` lines the same way
the surrounding ``EF_*_FIELD`` macro expands them at compile time, so
existing source-text assertions keep matching the compiled shape without
having to special-case every migrated struct.
"""

from __future__ import annotations

import re

from tests.support.paths import REPO_ROOT
from tools.maintenance.dto_schema.parse_xmacro import parse_xmacro_text


_INC_INCLUDE_RE = re.compile(r'#include "([^"]+\.inc)"\n?')
_MACRO_NAME_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)\(", re.MULTILINE)


def _parsed_inc_fields(inc_rel_path: str) -> tuple:
  inc_path = REPO_ROOT / "src" / inc_rel_path
  inc_text = inc_path.read_text(encoding="utf-8")
  macro_names = frozenset(_MACRO_NAME_RE.findall(inc_text))
  return parse_xmacro_text(inc_text, macro_names).fields


def _rendered_header_field(cpp_type: str, name: str, default: str) -> str:
  # ``default == "{}"`` is this schema suite's convention for "the source
  # field had no explicit initializer" (value-initialized via the type's
  # own default constructor), so render it bare rather than as
  # ``type name = {};``. That keeps the simulated text matching the
  # pre-migration hand-written style byte-for-byte in the common case, and
  # incidentally avoids a spurious ``"};"`` substring that would otherwise
  # confuse naive "find the struct's closing brace" text scans.
  if default == "{}":
    return f"{cpp_type} {name};"
  return f"{cpp_type} {name} = {default};"


def expand_header_field_incs(text: str) -> str:
  """Expand ``#include`` lines as ``EF_*_FIELD(t, n, d) -> t n = d;`` does
  inside a struct body (the header/field-declaration side of the macro)."""

  def _replace(match: re.Match[str]) -> str:
    fields = _parsed_inc_fields(match.group(1))
    return "\n".join(
      _rendered_header_field(field.cpp_type, field.name, field.default) for field in fields
    )

  return _INC_INCLUDE_RE.sub(_replace, text)


def expand_binding_field_incs(text: str) -> str:
  """Expand ``#include`` lines as the ``def_rw(#name, ...)``/``def_ro(#name,
  ...)`` stringification does at each generated binding call site (the
  Python-registration side of the macro)."""

  def _replace(match: re.Match[str]) -> str:
    fields = _parsed_inc_fields(match.group(1))
    return "\n".join(f'"{field.name}"' for field in fields)

  return _INC_INCLUDE_RE.sub(_replace, text)
