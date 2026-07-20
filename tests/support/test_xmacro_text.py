"""Unit tests for the ``tests/support/xmacro_text.py`` X-macro expansion helper.

I33 registered (T6 residual ledger section 2) that ``expand_header_field_incs``
consumed the ``#include ".../*.inc"`` line's own trailing newline without the
replacement text supplying one back, so a fully macro-owned struct's last
expanded field ended up glued directly onto the struct's ``};`` with no
newline in between. I37 fixes the helper itself; these tests pin the fix at
the helper level (independent of any specific production header) by
constructing a synthetic "single macro group immediately followed by ``};``"
fragment -- the exact shape the bug required -- and asserting the strict,
no-``\n?``-relaxation closing-brace form now matches.
"""

from __future__ import annotations

import re

from tests.support.xmacro_text import expand_binding_field_incs
from tests.support.xmacro_text import expand_header_field_incs


# A real, already-macro-owned .inc fragment with exactly two fields
# (world_index, entity_id) -- small and stable enough to use as read-only
# fixture input without inventing a new schema/generated artifact.
_ENTITY_REF_INC = "runtime/contracts/detail/engagement_entity_ref.inc"


def _strict_struct_body(text: str, struct_name: str) -> str:
  # Deliberately the *strict* form (no "?" after "\n"): this is the form
  # that skips past a struct whose expansion still glues its last field to
  # "};". A test using this helper is only meaningful if it fails on the
  # pre-fix helper and passes on the fixed one.
  pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
  match = re.search(pattern, text, flags=re.DOTALL)
  assert match is not None, f"{struct_name} did not match the strict closing-brace form"
  return match.group("body")


def test_expand_header_field_incs_preserves_newline_before_closing_brace() -> None:
  header = "struct FullyMacroOwnedProbe {\n" f'#include "{_ENTITY_REF_INC}"\n' "};\n"

  expanded = expand_header_field_incs(header)

  assert "#include" not in expanded
  # The struct's own closing brace must be reachable via the strict "\n};"
  # pattern -- i.e. the last expanded field is on its own line, not glued
  # to the following "};".
  body = _strict_struct_body(expanded, "FullyMacroOwnedProbe")
  assert "std::uint64_t world_index = 0;" in body
  assert "std::uint64_t entity_id = 0;" in body


def test_expand_header_field_incs_does_not_swallow_neighbouring_struct() -> None:
  header = (
    "struct FullyMacroOwnedProbe {\n"
    f'#include "{_ENTITY_REF_INC}"\n'
    "};\n"
    "\n"
    "struct NeighbouringGuardProbe {\n"
    "  std::string forbidden_swallowed_marker;\n"
    "};\n"
  )

  expanded = expand_header_field_incs(header)

  # Under the pre-fix helper, the strict "\n};" pattern skipped the glued
  # "};" of FullyMacroOwnedProbe and greedily matched through to this
  # struct's closing brace instead, swallowing the marker below into its
  # "body". With the newline preserved, the match must stop at the correct
  # struct boundary.
  probe_body = _strict_struct_body(expanded, "FullyMacroOwnedProbe")
  assert "forbidden_swallowed_marker" not in probe_body

  neighbour_body = _strict_struct_body(expanded, "NeighbouringGuardProbe")
  assert "forbidden_swallowed_marker" in neighbour_body


def test_expand_header_field_incs_keeps_consecutive_include_lines_on_separate_lines() -> None:
  header = (
    "struct TwinIncludeProbe {\n"
    f'#include "{_ENTITY_REF_INC}"\n'
    f'#include "{_ENTITY_REF_INC}"\n'
    "};\n"
  )

  expanded = expand_header_field_incs(header)
  body = _strict_struct_body(expanded, "TwinIncludeProbe")

  assert body.count("std::uint64_t world_index = 0;") == 2
  # The boundary between the first include's last field and the second
  # include's first field must also carry a newline, not just the
  # boundary against the struct's closing brace.
  assert "entity_id = 0;\nstd::uint64_t world_index = 0;" in body


def test_expand_binding_field_incs_preserves_newline_before_following_code() -> None:
  bindings = (
    "engagement_entity_ref_class.def_rw(#name, &EngagementEntityRef::name);\n"
    f'#include "{_ENTITY_REF_INC}"\n'
    "#undef EF_ENGAGEMENT_ENTITY_REF_FIELD\n"
  )

  expanded = expand_binding_field_incs(bindings)

  assert "#include" not in expanded
  assert '"world_index"\n"entity_id"\n#undef' in expanded
  assert '"entity_id"#undef' not in expanded
