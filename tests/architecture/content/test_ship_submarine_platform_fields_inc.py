"""Anti-drift gate for the ship/submarine platform inner-field lists.

The T11 loader table-drive bundle (this iteration) moved the repetitive inner
scalar field reads of ``parse_unit_json``'s ``ship_platform`` and
``submarine_platform`` object blocks (content/unit_definition_loader.cpp) onto
two single-source X-macro lists:

- ``src/content/detail/ship_platform_fields.inc`` (22 ShipPlatform members)
- ``src/content/detail/submarine_platform_fields.inc`` (15 SubmarinePlatform
  members)

Two lists rather than one shared list: the families are distinct component
structs with disjoint parse seams, and their same-named members (``length_m``,
``beam_m``, ``draft_m``, ``max_accel_mps2``, ``max_decel_mps2``,
``max_turn_rate_deg_s``, ``crew``) carry DIFFERENT struct default tokens per
family, so a shared list would need family-tagged duplicate rows with
conflicting default tokens and would break the one-struct/one-list review
parity (``test_shared_member_names_have_diverging_default_tokens`` pins the
divergence that forces this shape).

This gate mirrors the I58/I61 precedents
(``test_missile_tuning_fields_inc.py`` / ``test_unit_definition_direct_fields_inc.py``)
and reuses the same ``parse_xmacro`` reader. The mechanical substrate (``.inc``
reader, struct-declaration parser, body extractor, residue belts) is shared
with the other content gates via ``tests/support/xmacro_gate.py``; every
judgment below -- the two-list decision, the ``length_m`` exemption, the
expansion-site seams -- is bundle-specific and deliberately stays here.

Anchor structure (three-way closure, struct header == .inc == pinned):

- The **component struct headers**
  (``src/components/domains/naval/platform/ship_platform.h`` /
  ``submarine_platform.h``) are parsed at test time and are the authoritative
  anchor. Unlike I58/I61 there is no I52 survey table for these inner keys
  (survey section 1.1 lists ``ship_platform``/``submarine_platform`` only as
  object rows 31/32), but the header is a *stronger* anchor here: the JSON key
  is byte-identical to the member name, the block reads EVERY struct member in
  declaration order, and ``parse_unit_json`` resets the struct (``def.x = {}``)
  before the block, so the effective missing-key default is the struct
  initializer whose exact token the .inc mirrors.
- The pinned ``_SHIP_FIELDS`` / ``_SUBMARINE_FIELDS`` tables are the third leg:
  a header-edit-plus-.inc-edit still needs a matching edit here.
- The ``parse_unit_json`` body is located by text boundary (signature + brace
  matching that skips strings/comments) and scanned for hand-written residues:
  a generic ``.value("key"`` / ``.contains("key"`` / ``["key"]`` pattern scan,
  a quoted-key-literal belt, and a member-write belt
  (``def.ship_platform.<member> =`` may appear exactly once, inside the phase
  macro definition). The quoted-literal belt is body-scoped and excludes
  ``length_m`` from the body-wide sweep because the airframe block's
  ``def.airframe.length_m = af.value("length_m", 15.0);`` read is a different
  member on a different sub-object and stays hand-written by design; the
  platform if-block-scoped sweep covers ``length_m`` for both families.
- Both expansion sites are pinned inside their original if-blocks between
  their original neighbors. This is behavioral, not cosmetic: JSON conversion
  can throw, so moving a read across another read changes which malformed key
  fails first (the C++ parity case "platform fields parse: malformed-key
  fail-first order" exercises the runtime side).

Deliberately NOT absorbed (red line of this bundle): the object-presence
``has_ship_platform`` / ``has_submarine_platform`` flags, the six held
top-level ``has_*`` flags from the I61 adjudication, ``default_loadout``, and
the codec escape hatches. Only the repetitive inner field reads are
table-driven.
"""

from __future__ import annotations

import re

import pytest

from tests.support.paths import REPO_ROOT
from tests.support.xmacro_gate import (
    WorktreeAnchor,
    function_body,
    parse_inc_fields,
    quoted_key_literals,
    read_residues,
    struct_members_regex_scan,
)


_SHIP_INC_PATH = REPO_ROOT / "src" / "content" / "detail" / "ship_platform_fields.inc"
_SUBMARINE_INC_PATH = (
    REPO_ROOT / "src" / "content" / "detail" / "submarine_platform_fields.inc"
)
_LOADER_PATH = REPO_ROOT / "src" / "content" / "unit_definition_loader.cpp"
_SHIP_HEADER_PATH = (
    REPO_ROOT / "src" / "components" / "domains" / "naval" / "platform" / "ship_platform.h"
)
_SUBMARINE_HEADER_PATH = (
    REPO_ROOT
    / "src"
    / "components"
    / "domains"
    / "naval"
    / "platform"
    / "submarine_platform.h"
)

_SHIP_MACRO = "EF_SHIP_PLATFORM_FIELD"
_SUBMARINE_MACRO = "EF_SUBMARINE_PLATFORM_FIELD"

_SHIP_INC_INCLUDE = '#include "content/detail/ship_platform_fields.inc"'
_SUBMARINE_INC_INCLUDE = '#include "content/detail/submarine_platform_fields.inc"'
_LOADER_SIGNATURE = "bool parse_unit_json("

# clang-format (repo style, ColumnLimit 100) right-aligns macro continuation
# backslashes to column 100 and indents the macro body one level (4 spaces);
# the pins carry that exact padded text.
_SHIP_EXPANSION_BLOCK = (
    "#define EF_SHIP_PLATFORM_FIELD(cpp_type, name, default_value)" + 38 * " " + "\\\n"
    "    def.ship_platform.name = sp.value(#name, def.ship_platform.name);\n"
    f"{_SHIP_INC_INCLUDE}"
)
_SUBMARINE_EXPANSION_BLOCK = (
    "#define EF_SUBMARINE_PLATFORM_FIELD(cpp_type, name, default_value)" + 33 * " " + "\\\n"
    "    def.submarine_platform.name = sp.value(#name, def.submarine_platform.name);\n"
    f"{_SUBMARINE_INC_INCLUDE}"
)

# Pinned third leg (struct header == .inc == pinned): (member == json_key,
# cpp_type, exact struct-default token). Defaults are tokens, not numeric
# equivalence: ``0.12f`` must not silently replace ``0.12``.
_SHIP_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("displacement_light_kg", "double", "0.0"),
    ("displacement_full_load_kg", "double", "0.0"),
    ("length_m", "double", "0.0"),
    ("beam_m", "double", "0.0"),
    ("draft_m", "double", "0.0"),
    ("height_above_waterline_m", "double", "0.0"),
    ("max_speed_mps", "double", "0.0"),
    ("economical_speed_mps", "double", "0.0"),
    ("range_nm", "double", "0.0"),
    ("range_speed_mps", "double", "0.0"),
    ("max_accel_mps2", "double", "0.12"),
    ("max_decel_mps2", "double", "0.18"),
    ("max_turn_rate_deg_s", "double", "2.0"),
    ("low_speed_turn_factor", "double", "0.25"),
    ("steerageway_speed_mps", "double", "0.5"),
    ("sea_state", "double", "0.0"),
    ("wave_heading_deg", "double", "0.0"),
    ("wave_period_s", "double", "8.0"),
    ("max_roll_deg_sea_state_6", "double", "8.0"),
    ("max_pitch_deg_sea_state_6", "double", "3.0"),
    ("added_resistance_fraction_sea_state_6", "double", "0.12"),
    ("crew", "int", "0"),
)
_SUBMARINE_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("submerged_displacement_kg", "double", "0.0"),
    ("length_m", "double", "0.0"),
    ("beam_m", "double", "0.0"),
    ("draft_m", "double", "0.0"),
    ("max_speed_submerged_mps", "double", "0.0"),
    ("quiet_speed_mps", "double", "0.0"),
    ("max_accel_mps2", "double", "0.05"),
    ("max_decel_mps2", "double", "0.08"),
    ("max_turn_rate_deg_s", "double", "1.5"),
    ("max_depth_rate_mps", "double", "3.0"),
    ("nominal_patrol_depth_m", "double", "60.0"),
    ("max_operating_depth_m", "double", "300.0"),
    ("acoustic_stealth_bias_db", "double", "0.0"),
    ("self_noise_per_speed_db", "double", "1.2"),
    ("crew", "int", "0"),
)

# The airframe block reads a DIFFERENT length_m member
# (def.airframe.length_m); it stays hand-written and is the sole documented
# exception to the body-wide quoted-literal sweep.
_BODY_WIDE_LITERAL_EXEMPT = frozenset({"length_m"})
_AIRFRAME_LENGTH_READ = 'def.airframe.length_m = af.value("length_m", 15.0);'

_FAMILIES = {
    "ship": {
        "inc_path": _SHIP_INC_PATH,
        "header_path": _SHIP_HEADER_PATH,
        "struct_name": "ShipPlatform",
        "macro": _SHIP_MACRO,
        "include": _SHIP_INC_INCLUDE,
        "expansion": _SHIP_EXPANSION_BLOCK,
        "pinned": _SHIP_FIELDS,
        "member_prefix": "def.ship_platform.",
        "block_open": 'if (entry.contains("ship_platform") && entry["ship_platform"].is_object()) {',
    },
    "submarine": {
        "inc_path": _SUBMARINE_INC_PATH,
        "header_path": _SUBMARINE_HEADER_PATH,
        "struct_name": "SubmarinePlatform",
        "macro": _SUBMARINE_MACRO,
        "include": _SUBMARINE_INC_INCLUDE,
        "expansion": _SUBMARINE_EXPANSION_BLOCK,
        "pinned": _SUBMARINE_FIELDS,
        "member_prefix": "def.submarine_platform.",
        "block_open": (
            'if (entry.contains("submarine_platform") && '
            'entry["submarine_platform"].is_object()) {'
        ),
    },
}

_MEMBER_RE = re.compile(
    r"^\s*(double|int|bool)\s+([A-Za-z_]\w*)\s*=\s*([^;]+?)\s*;", re.MULTILINE
)


# ---------------------------------------------------------------------------
# Pure readers/checkers. Negative tests drive these with tampered in-memory
# inputs, so none of them may read global state beyond their arguments.
# ---------------------------------------------------------------------------


def _parse_inc_fields(inc_text: str, macro: str):
    return parse_inc_fields(inc_text, frozenset({macro}))


def _struct_member_rows(header_text: str, struct_name: str) -> tuple[tuple[str, str, str], ...]:
    """Parse (member, cpp_type, exact default token) from the struct body in
    declaration order. The platform structs are flat all-default-initialized
    aggregates, so a member without the ``type name = default;`` shape is a
    reshape this gate must go red on (count check downstream)."""
    return struct_members_regex_scan(
        header_text, struct_name=struct_name, member_re=_MEMBER_RE
    )


def _check_inc_matches_header(inc_fields, header_rows, macro: str, label: str) -> None:
    """Anchor: the .inc rows equal the struct members -- same names, same
    declaration order, same cpp types, same exact default tokens -- and every
    row uses the family macro. The block reads the FULL struct, so this is an
    equality, not a subset check."""
    inc_names = [field.name for field in inc_fields]
    assert len(inc_names) == len(set(inc_names)), f"duplicate key in {label} .inc"
    header_names = [name for name, _cpp, _default in header_rows]
    assert inc_names == header_names, (
        f"{label} .inc drifted from the struct declaration order/name set: "
        f"{inc_names} != {header_names}"
    )
    header_by_name = {name: (cpp, default) for name, cpp, default in header_rows}
    for field in inc_fields:
        expected_cpp, expected_default = header_by_name[field.name]
        assert field.cpp_type == expected_cpp, (
            f"{label} {field.name}: expected {expected_cpp}, got {field.cpp_type}"
        )
        assert field.default == expected_default, (
            f"{label} {field.name}: expected exact default token "
            f"{expected_default!r}, got {field.default!r}"
        )
        assert field.group == macro, (
            f"{label} {field.name}: expected macro {macro}, got {field.group}"
        )


def _loader_function_body(loader_text: str, signature: str) -> str:
    """Extract a function definition body by text boundary: the signature
    occurrence followed by '{' (not ';'), then brace matching that skips string
    literals, char literals, and // and /* */ comments (I61 extractor)."""
    return function_body(
        loader_text, signature, label="parse_unit_json", skip_literals=True
    )


def _platform_if_block(body: str, block_open: str) -> str:
    """Extract one platform if-block (brace-matched from its opening line).
    The block is small and brace-free apart from the outer pair post-migration,
    but full matching keeps the extractor honest under future edits."""
    start = body.find(block_open)
    assert start >= 0, f"platform block opener not found: {block_open!r}"
    brace = body.index("{", start + len(block_open) - 1)
    depth = 0
    for pos in range(brace, len(body)):
        if body[pos] == "{":
            depth += 1
        elif body[pos] == "}":
            depth -= 1
            if depth == 0:
                return body[start : pos + 1]
    raise AssertionError("unbalanced platform if-block")


# Deliberately object-agnostic (no `entry`/`sp` prefix): the platform reads
# bind a local `sp` alias, so a residue could reappear under either spelling.
_READ_ACCESS_PREFIX = r'(?:\.\s*(?:value|contains)\s*\(\s*|\[\s*)'


def _hand_written_read_residues(body_text: str, keys) -> list[str]:
    """Keys with a hand-written read (.value("key" / .contains("key" /
    ["key"] forms, any object expression) inside the given text."""
    return read_residues(body_text, keys, _READ_ACCESS_PREFIX)


def _check_loader_expansion_sites(loader_text: str) -> None:
    """Pin both expansion blocks inside their original if-block seams."""
    body = _loader_function_body(loader_text, _LOADER_SIGNATURE)
    assert body.count(_SHIP_INC_INCLUDE) == 1, "expected exactly one ship expansion"
    assert body.count(_SUBMARINE_INC_INCLUDE) == 1, (
        "expected exactly one submarine expansion"
    )
    assert body.count(_SHIP_EXPANSION_BLOCK) == 1, "ship expansion block drifted"
    assert body.count(_SUBMARINE_EXPANSION_BLOCK) == 1, (
        "submarine expansion block drifted"
    )

    ship_open = body.index(_FAMILIES["ship"]["block_open"])
    ship_bind = body.index('const auto &sp = entry["ship_platform"];')
    ship_expansion = body.index(_SHIP_EXPANSION_BLOCK)
    submarine_reset = body.index("def.has_submarine_platform = false;")
    assert ship_open < ship_bind < ship_expansion < submarine_reset, (
        "ship expansion left its original seam"
    )

    submarine_open = body.index(_FAMILIES["submarine"]["block_open"])
    submarine_bind = body.index('const auto &sp = entry["submarine_platform"];')
    submarine_expansion = body.index(_SUBMARINE_EXPANSION_BLOCK)
    naval_stores_reset = body.index("def.has_naval_stores = false;")
    assert submarine_reset < submarine_open < submarine_bind < submarine_expansion, (
        "submarine expansion left its original seam"
    )
    assert submarine_expansion < naval_stores_reset, (
        "submarine expansion left its original seam"
    )
    assert ship_expansion < submarine_expansion


def _check_member_write_belt(loader_text: str) -> None:
    """Every ``def.ship_platform.<member>`` / ``def.submarine_platform.<member>``
    access in the body lives inside the macro definition line (which carries
    the dotted prefix exactly twice: target and current-value default). The
    ``def.x = {};`` resets and ``def.has_x`` flags do not match the dotted
    prefix, so any extra occurrence is a hand-written member access."""
    body = _loader_function_body(loader_text, _LOADER_SIGNATURE)
    for label, family in _FAMILIES.items():
        expected = family["expansion"].count(family["member_prefix"])
        assert expected == 2, f"{label}: expansion block shape changed"
        count = body.count(family["member_prefix"])
        assert count == expected, (
            f"{label}: expected {family['member_prefix']!r} only inside the "
            f"macro definition ({expected} occurrences), found {count}"
        )


def _real_text(path) -> str:
    # Both platform anchors are working-tree struct headers (the survey has no
    # per-key table for these inner keys); the git-object anchor form is the
    # other half of the shared anchor interface and is used by the two
    # survey-anchored bundles.
    return WorktreeAnchor(path).read_text()


def _real_loader_text() -> str:
    return _real_text(_LOADER_PATH)


# ---------------------------------------------------------------------------
# Positive gates (leg 1: shape inventory, struct-header anchor, pinned table).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("label", sorted(_FAMILIES))
def test_inc_exists_and_parses(label: str) -> None:
    family = _FAMILIES[label]
    assert family["inc_path"].is_file(), f"missing field list: {family['inc_path']}"
    fields = _parse_inc_fields(_real_text(family["inc_path"]), family["macro"])
    assert len(fields) == len(family["pinned"])


@pytest.mark.parametrize("label", sorted(_FAMILIES))
def test_struct_header_parses_expected_member_count(label: str) -> None:
    family = _FAMILIES[label]
    rows = _struct_member_rows(_real_text(family["header_path"]), family["struct_name"])
    assert len(rows) == len(family["pinned"]), (
        f"{family['struct_name']} member count drifted from the pinned table; "
        "adjudicate the new/removed member and update the .inc and this gate"
    )


@pytest.mark.parametrize("label", sorted(_FAMILIES))
def test_inc_matches_struct_header_anchor(label: str) -> None:
    family = _FAMILIES[label]
    _check_inc_matches_header(
        _parse_inc_fields(_real_text(family["inc_path"]), family["macro"]),
        _struct_member_rows(_real_text(family["header_path"]), family["struct_name"]),
        family["macro"],
        label,
    )


@pytest.mark.parametrize("label", sorted(_FAMILIES))
def test_pinned_table_matches_header_and_inc_third_leg(label: str) -> None:
    family = _FAMILIES[label]
    header_rows = _struct_member_rows(
        _real_text(family["header_path"]), family["struct_name"]
    )
    inc_fields = _parse_inc_fields(_real_text(family["inc_path"]), family["macro"])
    assert tuple(family["pinned"]) == header_rows, (
        f"pinned {label} table drifted from the struct header"
    )
    assert [field.name for field in inc_fields] == [
        name for name, _cpp, _default in family["pinned"]
    ], f"pinned {label} table drifted from the .inc"
    for field, (name, cpp, default) in zip(inc_fields, family["pinned"]):
        assert (field.name, field.cpp_type, field.default) == (name, cpp, default)


def test_shared_member_names_have_diverging_default_tokens() -> None:
    # The rationale pin for two .inc files instead of one shared list: the
    # families overlap in member names but NOT in default tokens, so one row
    # per key cannot single-source both structs' defaults.
    ship = {name: default for name, _cpp, default in _SHIP_FIELDS}
    submarine = {name: default for name, _cpp, default in _SUBMARINE_FIELDS}
    shared = sorted(set(ship) & set(submarine))
    assert shared == [
        "beam_m",
        "crew",
        "draft_m",
        "length_m",
        "max_accel_mps2",
        "max_decel_mps2",
        "max_turn_rate_deg_s",
    ]
    diverging = [name for name in shared if ship[name] != submarine[name]]
    assert diverging == ["max_accel_mps2", "max_decel_mps2", "max_turn_rate_deg_s"], (
        "default-token divergence between the families changed; revisit the "
        "one-.inc-per-family decision note in both .inc headers"
    )


# ---------------------------------------------------------------------------
# Positive gates (leg 2: expansion-site positional pins and residue belts).
# ---------------------------------------------------------------------------


def test_loader_consumes_both_incs_at_their_seams() -> None:
    _check_loader_expansion_sites(_real_loader_text())


def test_body_has_no_hand_written_read_or_member_write_residue() -> None:
    loader = _real_loader_text()
    body = _loader_function_body(loader, _LOADER_SIGNATURE)
    all_keys = sorted(
        {name for name, _cpp, _default in _SHIP_FIELDS}
        | {name for name, _cpp, _default in _SUBMARINE_FIELDS}
    )
    body_wide_keys = [key for key in all_keys if key not in _BODY_WIDE_LITERAL_EXEMPT]

    # Body-wide sweep (all keys except the documented airframe length_m read).
    assert _hand_written_read_residues(body, body_wide_keys) == []
    assert quoted_key_literals(body, body_wide_keys) == []

    # The length_m exemption stays exactly the airframe read: one quoted
    # occurrence, and it is that statement.
    assert body.count('"length_m"') == 1
    assert _AIRFRAME_LENGTH_READ in body

    # Block-scoped sweep covers length_m (and everything else) inside both
    # platform if-blocks: post-migration the blocks contain no quoted key
    # literal at all.
    for label, family in _FAMILIES.items():
        block = _platform_if_block(body, family["block_open"])
        family_keys = [name for name, _cpp, _default in family["pinned"]]
        assert quoted_key_literals(block, family_keys) == [], (
            f"hand-written key literal reintroduced in the {label} block"
        )
        assert family["expansion"] in block

    _check_member_write_belt(loader)


def test_body_extractor_isolates_parse_unit_json() -> None:
    # Sanity: the extracted body is parse_unit_json (not the whole file) and is
    # brace-balanced -- it must contain both includes and the trailing return
    # but not the following definitions.
    body = _loader_function_body(_real_loader_text(), _LOADER_SIGNATURE)
    assert _SHIP_INC_INCLUDE in body
    assert _SUBMARINE_INC_INCLUDE in body
    assert "return true;" in body
    assert "load_file(" not in body


# ---------------------------------------------------------------------------
# Negative gates (leg 3: in-memory tamper drills; the gate must go red).
# ---------------------------------------------------------------------------


def test_key_deletion_from_inc_goes_red() -> None:
    inc_lines = _real_text(_SHIP_INC_PATH).splitlines(keepends=True)
    dropped = "".join(line for line in inc_lines if "steerageway_speed_mps" not in line)
    dropped_fields = _parse_inc_fields(dropped, _SHIP_MACRO)
    assert len(dropped_fields) == len(_SHIP_FIELDS) - 1
    with pytest.raises(AssertionError):
        _check_inc_matches_header(
            dropped_fields,
            _struct_member_rows(_real_text(_SHIP_HEADER_PATH), "ShipPlatform"),
            _SHIP_MACRO,
            "ship",
        )


def test_header_anchor_catches_synchronized_inc_and_pinned_tamper() -> None:
    # Reviewer bypass replay: rename a key the same way in the .inc and
    # (hypothetically) the pinned table. The struct header is untampered, so
    # the anchor still goes red because the renamed key is not a member.
    tampered_inc_text = _real_text(_SUBMARINE_INC_PATH).replace(
        "EF_SUBMARINE_PLATFORM_FIELD(double, quiet_speed_mps, 0.0)",
        "EF_SUBMARINE_PLATFORM_FIELD(double, quiett_speed_mps, 0.0)",
        1,
    )
    assert tampered_inc_text != _real_text(_SUBMARINE_INC_PATH)
    tampered_fields = _parse_inc_fields(tampered_inc_text, _SUBMARINE_MACRO)
    tampered_pinned = [
        ("quiett_speed_mps" if name == "quiet_speed_mps" else name)
        for name, _cpp, _default in _SUBMARINE_FIELDS
    ]
    # Old-gate simulation: .inc vs pinned-table comparison stays green after
    # the synchronized tamper.
    assert [field.name for field in tampered_fields] == tampered_pinned
    with pytest.raises(AssertionError):
        _check_inc_matches_header(
            tampered_fields,
            _struct_member_rows(_real_text(_SUBMARINE_HEADER_PATH), "SubmarinePlatform"),
            _SUBMARINE_MACRO,
            "submarine",
        )


def test_exact_default_token_tamper_goes_red() -> None:
    tampered = _real_text(_SHIP_INC_PATH).replace(
        "EF_SHIP_PLATFORM_FIELD(double, max_accel_mps2, 0.12)",
        "EF_SHIP_PLATFORM_FIELD(double, max_accel_mps2, 0.12f)",
        1,
    )
    assert tampered != _real_text(_SHIP_INC_PATH)
    with pytest.raises(AssertionError, match="exact default token"):
        _check_inc_matches_header(
            _parse_inc_fields(tampered, _SHIP_MACRO),
            _struct_member_rows(_real_text(_SHIP_HEADER_PATH), "ShipPlatform"),
            _SHIP_MACRO,
            "ship",
        )


def test_struct_header_tamper_goes_red() -> None:
    # A header retype (int crew -> double crew) without a matching .inc edit
    # must trip the anchor comparison.
    tampered_header = _real_text(_SHIP_HEADER_PATH).replace(
        "int crew = 0;", "double crew = 0;", 1
    )
    assert tampered_header != _real_text(_SHIP_HEADER_PATH)
    with pytest.raises(AssertionError):
        _check_inc_matches_header(
            _parse_inc_fields(_real_text(_SHIP_INC_PATH), _SHIP_MACRO),
            _struct_member_rows(tampered_header, "ShipPlatform"),
            _SHIP_MACRO,
            "ship",
        )


@pytest.mark.parametrize(
    "block", [_SHIP_EXPANSION_BLOCK, _SUBMARINE_EXPANSION_BLOCK]
)
def test_expansion_site_move_goes_red(block: str) -> None:
    loader = _real_loader_text()
    without = loader.replace(block, "", 1)
    moved = without.replace("    return true;", f"    {block}\n    return true;", 1)
    assert moved != loader
    with pytest.raises(AssertionError):
        _check_loader_expansion_sites(moved)


def test_residue_scan_catches_hand_written_injection() -> None:
    loader = _real_loader_text()
    marker = _SHIP_INC_INCLUDE + "\n"
    injected = loader.replace(
        marker,
        marker + '        def.ship_platform.beam_m = sp.value("beam_m", def.ship_platform.beam_m);\n',
        1,
    )
    assert injected != loader
    body = _loader_function_body(injected, _LOADER_SIGNATURE)
    assert _hand_written_read_residues(body, ["beam_m"]) == ["beam_m"]
    assert quoted_key_literals(body, ["beam_m"]) == ["beam_m"]
    with pytest.raises(AssertionError):
        _check_member_write_belt(injected)


def test_belt_catches_non_value_form_injection() -> None:
    # A hand-written access that avoids the .value/.contains/[] shapes still
    # trips the quoted-literal belt.
    loader = _real_loader_text()
    marker = _SUBMARINE_INC_INCLUDE + "\n"
    injected = loader.replace(
        marker,
        marker
        + '        { const auto it = sp.find("draft_m");\n'
        + "          if (it != sp.end()) def.submarine_platform.draft_m = it->get<double>(); }\n",
        1,
    )
    assert injected != loader
    body = _loader_function_body(injected, _LOADER_SIGNATURE)
    assert _hand_written_read_residues(body, ["draft_m"]) == []
    assert quoted_key_literals(body, ["draft_m"]) == ["draft_m"]
    with pytest.raises(AssertionError):
        _check_member_write_belt(injected)
