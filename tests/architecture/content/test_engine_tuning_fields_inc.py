"""Anti-drift gate for the EngineTuning parse field list (T11, this iteration).

This iteration moved the 16 purely-mechanical JSON keys read by
``parse_engine_tuning_json_fields`` onto a single-source X-macro list at
``src/content/detail/engine_tuning_fields.inc``, following the I58
``missile_tuning_fields.inc`` and I66 ``aero_tuning_fields.inc`` precedents and
the landed I61 direct-fields test template.

Anchor structure (the I58 review-hardening discipline: the gate must not be a
two-way comparison that a synchronized tamper can satisfy):

- The **EngineTuning declaration** in
  ``src/components/domains/air/platform/flight_dynamics_tuning.h`` is parsed at
  test time and is the authoritative anchor. As with the aero bundle, the I52
  survey has no per-key table for the engine helper -- it records
  ``engine_tuning`` as a single object row -- so the struct declaration is the
  only independent inventory of this parse surface. The ``.inc`` must cover
  exactly the declaration's members minus the adjudicated absence set, with
  matching C++ types.
- The pinned ``_EXPECTED_FIELDS`` table below is a third leg of a three-way
  cross-check (declaration == .inc == pinned), so a header-edit-plus-.inc-edit
  still needs a matching edit here to pass.
- The helper body in ``unit_definition_loader.cpp`` is located by text boundary
  (signature + brace matching) and scanned for hand-written read residues of
  **all 16 keys**, plus a stricter no-quoted-key-literal belt, so a
  re-introduced hand-written read of any key -- first, middle, or last -- goes
  red.
- The SINGLE-pass include contract is pinned (exactly one include of the list
  inside the helper). Unlike the aero helper there is no ``parse_vector``
  lambda to order around, because EngineTuning has no vector members; the gate
  also pins that member-type set, so a future vector member forces the
  adjudication and pass structure to be revisited rather than silently
  extended.

ABSENCE SET: ``enabled`` is the one member read by the helper that stays
hand-written. Its read takes a *literal* ``true`` default rather than the
"missing key keeps the existing value" form, which is load-bearing for the
``engine.tuning`` / ``engine_tuning`` codec escape hatch (census red line
"codec escape hatches must be preserved"): both call sites seed from the
``flight_dynamics::default_engine_tuning()`` preset and then merge, so a
present tuning object without an ``enabled`` key must still come out enabled.
The top-level ``engine_tuning`` call site additionally branches on
``tuning.enabled`` to decide whether to re-seed before merging on top of an
``engine.tuning`` block. This gate pins both that ``enabled`` is absent from
the ``.inc`` and that the literal-default hand-written read is still present in
the helper body.
"""

from __future__ import annotations

import re

import pytest

from tests.support.paths import REPO_ROOT


_INC_PATH = REPO_ROOT / "src" / "content" / "detail" / "engine_tuning_fields.inc"
_LOADER_PATH = REPO_ROOT / "src" / "content" / "unit_definition_loader.cpp"
_HEADER_PATH = (
    REPO_ROOT
    / "src"
    / "components"
    / "domains"
    / "air"
    / "platform"
    / "flight_dynamics_tuning.h"
)

_SCALAR_MACRO = "EF_ENGINE_TUNING_FIELD"
_MACROS = frozenset({_SCALAR_MACRO})

_INC_INCLUDE_DIRECTIVE = '#include "content/detail/engine_tuning_fields.inc"'
_HELPER_SIGNATURE = "void parse_engine_tuning_json_fields("

# The hand-written literal-default read that must survive the migration.
_ENABLED_HAND_WRITTEN_READ = 'tuning.enabled = src.value("enabled", true);'

# Members declared on EngineTuning but deliberately NOT in the field list.
_ABSENT_MEMBERS = ("enabled",)

# EngineTuning declaration parsing. Members are plain `<type> <name> = <init>;`
# lines inside the struct body. std::vector<double> stays in the alternation so
# a future vector member is *parsed* and then rejected by the type-set gate
# (single-macro adjudication) instead of being silently skipped.
_STRUCT_OPEN = "struct EngineTuning {"
_MEMBER_RE = re.compile(
    r"^(?P<type>bool|double|std::vector<double>)\s+(?P<name>\w+)"
    r"\s*(?:=\s*(?P<init>[^;]*?)\s*)?;$"
)

# The single-macro contract: EngineTuning is scalars-only.
_ALLOWED_MEMBER_TYPES = frozenset({"bool", "double"})

# Pinned third leg (declaration == .inc == pinned): (member, cpp_type, macro).
# Order is both the declaration order and the historical hand-written read
# order, which for this struct are identical (unlike AeroTuning).
_EXPECTED_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("mil_thrust_n", "double", _SCALAR_MACRO),
    ("ab_thrust_n", "double", _SCALAR_MACRO),
    ("throttle_ab_threshold", "double", _SCALAR_MACRO),
    ("throttle_idle_bias", "double", _SCALAR_MACRO),
    ("tau_spool_up_s", "double", _SCALAR_MACRO),
    ("tau_spool_down_s", "double", _SCALAR_MACRO),
    ("tau_ab_light_s", "double", _SCALAR_MACRO),
    ("tau_ab_extinguish_s", "double", _SCALAR_MACRO),
    ("ram_rise_gain", "double", _SCALAR_MACRO),
    ("ram_rise_mach_cap", "double", _SCALAR_MACRO),
    ("ram_decay_start_mach", "double", _SCALAR_MACRO),
    ("ram_decay_gain", "double", _SCALAR_MACRO),
    ("thrust_sigma_exponent", "double", _SCALAR_MACRO),
    ("thrust_theta_exponent", "double", _SCALAR_MACRO),
    ("tsfc_mil_kg_per_nh", "double", _SCALAR_MACRO),
    ("tsfc_ab_kg_per_nh", "double", _SCALAR_MACRO),
)

_EXPECTED_FIELD_COUNT = 16


# ---------------------------------------------------------------------------
# Pure readers/checkers. Negative tests drive these with tampered in-memory
# inputs, so none of them may read global state beyond their arguments.
# ---------------------------------------------------------------------------


def _parse_inc_fields(inc_text: str):
    from tools.maintenance.dto_schema.parse_xmacro import parse_xmacro_text

    return parse_xmacro_text(inc_text, _MACROS).fields


def _struct_members(header_text: str) -> tuple[tuple[str, str], ...]:
    """Parse (member, cpp_type) from the EngineTuning declaration, in
    declaration order. Strict: if the struct moves or is reshaped, the gate goes
    red rather than silently anchoring to nothing."""
    return tuple(
        (name, cpp_type) for name, cpp_type, _init in _struct_members_with_init(header_text)
    )


def _struct_members_with_init(
    header_text: str,
) -> tuple[tuple[str, str, str], ...]:
    """Parse (member, cpp_type, initializer_text) from the EngineTuning
    declaration."""
    open_index = header_text.find(_STRUCT_OPEN)
    assert open_index >= 0, f"{_STRUCT_OPEN!r} not found in {_HEADER_PATH}"
    body_start = open_index + len(_STRUCT_OPEN)
    end_index = header_text.find("\n};", body_start)
    assert end_index > body_start, "unterminated EngineTuning declaration"
    body = header_text[body_start:end_index]
    members: list[tuple[str, str, str]] = []
    for raw_line in body.splitlines():
        line = re.sub(r"//.*$", "", raw_line).strip()
        match = _MEMBER_RE.match(line)
        if match:
            members.append(
                (match.group("name"), match.group("type"), match.group("init") or "")
            )
    assert members, "EngineTuning declaration yielded no parsable members"
    return tuple(members)


def _check_member_types_are_scalar_only(struct_members) -> None:
    """The single-macro / single-pass shape of this bundle is only valid while
    EngineTuning has no vector (or otherwise non-scalar) members. A new vector
    member must go through re-adjudication (macro split + pass structure), so
    it trips this gate instead of silently joining the scalar list."""
    for name, cpp_type in struct_members:
        assert cpp_type in _ALLOWED_MEMBER_TYPES, (
            f"EngineTuning member {name} has type {cpp_type}; the single-macro "
            "engine_tuning_fields.inc contract covers only bool/double scalars "
            "and must be re-adjudicated before this member is parsed"
        )


def _check_recorded_defaults_match_struct(inc_fields, struct_members_with_init) -> None:
    """The .inc's default_value token is parity-only (never expanded into the
    parse), so nothing in the build would notice if it drifted from the struct
    initializer it claims to mirror. This check is what makes that claim
    load-bearing: every row's recorded token must equal the declared
    initializer verbatim."""
    declared_init = {
        name: init for name, _cpp_type, init in struct_members_with_init
    }
    for field in inc_fields:
        recorded = field.default.strip()
        assert recorded == declared_init[field.name], (
            f"{field.name}: .inc records default {recorded!r} but EngineTuning "
            f"declares {declared_init[field.name]!r}; the parity-only token must "
            "mirror the struct initializer exactly"
        )


def _check_inc_matches_struct(inc_fields, struct_members) -> None:
    """Anchor assertion: .inc covers exactly the EngineTuning members minus the
    adjudicated absence set, with matching types."""
    declared = {name: cpp_type for name, cpp_type in struct_members}
    assert len(declared) == len(struct_members), "duplicate EngineTuning member"

    for absent in _ABSENT_MEMBERS:
        assert absent in declared, (
            f"absence-set member {absent} no longer exists on EngineTuning; the "
            "adjudication must be revisited"
        )

    expected_covered = {
        name for name in declared if name not in set(_ABSENT_MEMBERS)
    }
    inc_names = [field.name for field in inc_fields]
    assert len(set(inc_names)) == len(inc_names), ".inc has a duplicate key"
    assert set(inc_names) == expected_covered, (
        "engine_tuning_fields.inc drifted from the EngineTuning declaration: "
        f"missing={sorted(expected_covered - set(inc_names))} "
        f"unexpected={sorted(set(inc_names) - expected_covered)}"
    )
    for field in inc_fields:
        assert field.cpp_type == declared[field.name], (
            f"{field.name}: .inc type {field.cpp_type} != declared "
            f"{declared[field.name]}"
        )
        assert field.group == _SCALAR_MACRO, (
            f"{field.name}: wrong macro group {field.group}"
        )


def _check_pinned_matches_struct(struct_members) -> None:
    """Third leg: the pinned table itself must agree with the declaration on the
    member set, per-member type, and (for this struct) the declaration order,
    which is also the read order."""
    declared = dict(struct_members)
    pinned = {name: cpp_type for name, cpp_type, _group in _EXPECTED_FIELDS}
    expected_covered = {
        name for name in declared if name not in set(_ABSENT_MEMBERS)
    }
    assert set(pinned) == expected_covered, (
        "pinned _EXPECTED_FIELDS drifted from the EngineTuning declaration"
    )
    for name, cpp_type in pinned.items():
        assert cpp_type == declared[name], f"pinned {name}: type disagrees"
    declaration_order = [
        name for name, _cpp_type in struct_members if name not in set(_ABSENT_MEMBERS)
    ]
    assert declaration_order == [name for name, _t, _g in _EXPECTED_FIELDS], (
        "pinned order no longer matches the EngineTuning declaration order "
        "(which is also the historical read order for this struct)"
    )


def _helper_body(loader_text: str) -> str:
    """Extract the parse_engine_tuning_json_fields definition body by text
    boundary: the signature occurrence followed by '{' (not ';'), then brace
    matching to the function's closing brace."""
    for match in re.finditer(re.escape(_HELPER_SIGNATURE), loader_text):
        index = match.end()
        while index < len(loader_text) and loader_text[index] not in "{;":
            index += 1
        if index >= len(loader_text) or loader_text[index] != "{":
            continue  # forward declaration; keep scanning
        depth = 0
        for position in range(index, len(loader_text)):
            char = loader_text[position]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return loader_text[index : position + 1]
        raise AssertionError(
            "unbalanced braces in parse_engine_tuning_json_fields definition"
        )
    raise AssertionError("parse_engine_tuning_json_fields definition not found")


def _hand_written_read_residues(loader_text: str, keys) -> list[str]:
    """Keys with a hand-written read (src.value("key" form) inside the helper
    body."""
    body = _helper_body(loader_text)
    residues = []
    for key in keys:
        pattern = re.compile(r'src\s*\.\s*value\s*\(\s*"' + re.escape(key) + r'"')
        if pattern.search(body):
            residues.append(key)
    return residues


def _quoted_key_literals_in_helper_body(loader_text: str, keys) -> list[str]:
    """Stricter belt: the table-driven part of the body contains no quoted key
    literal at all (keys enter only via #name stringification inside the .inc),
    so any quoted migrated-key literal in the body is a hand-written access of
    some form (src.value, src[...], src.contains, ...)."""
    body = _helper_body(loader_text)
    return [key for key in keys if f'"{key}"' in body]


def _include_passes(loader_text: str) -> int:
    return _helper_body(loader_text).count(_INC_INCLUDE_DIRECTIVE)


def _real_inc_text() -> str:
    return _INC_PATH.read_text(encoding="utf-8")


def _real_loader_text() -> str:
    return _LOADER_PATH.read_text(encoding="utf-8")


def _real_struct_members() -> tuple[tuple[str, str], ...]:
    return _struct_members(_HEADER_PATH.read_text(encoding="utf-8"))


def _real_struct_members_with_init() -> tuple[tuple[str, str, str], ...]:
    return _struct_members_with_init(_HEADER_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Positive gates.
# ---------------------------------------------------------------------------


def test_inc_exists_and_parses() -> None:
    assert _INC_PATH.is_file(), f"missing single-source field list: {_INC_PATH}"
    assert len(_parse_inc_fields(_real_inc_text())) == _EXPECTED_FIELD_COUNT


def test_struct_declaration_parses() -> None:
    members = _real_struct_members()
    # 16 migrated keys + the held `enabled`.
    assert len(members) == _EXPECTED_FIELD_COUNT + len(_ABSENT_MEMBERS)
    _check_member_types_are_scalar_only(members)


def test_inc_matches_struct_declaration_anchor() -> None:
    _check_inc_matches_struct(_parse_inc_fields(_real_inc_text()), _real_struct_members())


def test_pinned_table_matches_struct_third_leg() -> None:
    _check_pinned_matches_struct(_real_struct_members())


def test_recorded_defaults_mirror_the_struct_initializers() -> None:
    # The default_value token is parity-only (the parse never expands it), so
    # without this gate it could drift from the initializer it claims to mirror
    # and nothing in the build would notice.
    _check_recorded_defaults_match_struct(
        _parse_inc_fields(_real_inc_text()), _real_struct_members_with_init()
    )


def test_inc_order_is_the_pinned_read_order() -> None:
    # For EngineTuning the read order equals the declaration order (verified
    # against the pre-change hand-written body); the .inc pins that shared
    # order and token-for-token parity depends on it.
    inc_fields = _parse_inc_fields(_real_inc_text())
    assert [field.name for field in inc_fields] == [
        name for name, _cpp_type, _group in _EXPECTED_FIELDS
    ]


def test_no_angle_bracket_comma_type_entered_the_list() -> None:
    # Census red line "X-macro comma blockers" / I31 precedent: the preprocessor
    # pairs only parentheses, so a type carrying an intra-angle comma would be
    # mis-split. No EngineTuning member is templated at all, so every row's
    # recorded type must be comma-free.
    for field in _parse_inc_fields(_real_inc_text()):
        assert "," not in field.cpp_type, (
            f"{field.name}: angle-bracket-comma type {field.cpp_type} must be "
            "held hand-written per the I31 precedent, not aliased into the list"
        )
    for _name, cpp_type in _real_struct_members():
        assert "," not in cpp_type, (
            f"EngineTuning gained an angle-bracket-comma member ({cpp_type}); it "
            "must be adjudicated before entering the X-macro list"
        )


def test_absence_set_is_absent_and_its_hand_written_read_survives() -> None:
    inc_names = {field.name for field in _parse_inc_fields(_real_inc_text())}
    body = _helper_body(_real_loader_text())
    for member in _ABSENT_MEMBERS:
        assert member not in inc_names, (
            f"{member} is not a mechanical read and must stay hand-written"
        )
    # The literal `true` default is the codec escape hatch's contract, and the
    # top-level engine_tuning call site's re-seed branch reads it.
    assert _ENABLED_HAND_WRITTEN_READ in body, (
        "the hand-written literal-default read of `enabled` must survive: the "
        "engine.tuning / engine_tuning preset-then-merge path depends on it"
    )


def test_loader_helper_consumes_the_inc_in_a_single_pass() -> None:
    loader = _real_loader_text()
    assert _include_passes(loader) == 1, (
        "parse_engine_tuning_json_fields must include the single-source list "
        "exactly once: EngineTuning has no vector members, so there is no "
        "second (vector) pass, and zero passes drops all 16 reads"
    )


def test_helper_body_has_no_hand_written_read_for_any_migrated_key() -> None:
    loader = _real_loader_text()
    keys = [name for name, _cpp_type, _group in _EXPECTED_FIELDS]
    assert _hand_written_read_residues(loader, keys) == []
    assert _quoted_key_literals_in_helper_body(loader, keys) == []


# ---------------------------------------------------------------------------
# Negative gates (in-memory tamper drills; the gate must go red).
# ---------------------------------------------------------------------------


def test_default_token_drift_goes_red() -> None:
    tampered = _real_inc_text().replace(
        "EF_ENGINE_TUNING_FIELD(double, tau_spool_up_s, 2.5)",
        "EF_ENGINE_TUNING_FIELD(double, tau_spool_up_s, 9.9)",
        1,
    )
    assert tampered != _real_inc_text()
    with pytest.raises(AssertionError):
        _check_recorded_defaults_match_struct(
            _parse_inc_fields(tampered), _real_struct_members_with_init()
        )


def test_struct_initializer_drift_goes_red() -> None:
    # The other direction: retuning the struct default without updating the .inc
    # must also trip the parity gate.
    header = _HEADER_PATH.read_text(encoding="utf-8")
    tampered = header.replace(
        "double tau_spool_up_s = 2.5;", "double tau_spool_up_s = 3.5;", 1
    )
    assert tampered != header
    with pytest.raises(AssertionError):
        _check_recorded_defaults_match_struct(
            _parse_inc_fields(_real_inc_text()), _struct_members_with_init(tampered)
        )


def test_key_deletion_from_inc_goes_red_against_struct() -> None:
    inc_lines = _real_inc_text().splitlines(keepends=True)
    dropped = "".join(
        line for line in inc_lines if "tsfc_ab_kg_per_nh" not in line
    )
    mutated = _parse_inc_fields(dropped)
    assert len(mutated) == _EXPECTED_FIELD_COUNT - 1
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(mutated, _real_struct_members())


def test_struct_anchor_catches_synchronized_inc_and_pinned_tamper() -> None:
    # A tamper of the .inc AND the pinned table the same way would satisfy a
    # two-way gate. The struct declaration is untampered, so the gate goes red.
    tampered_inc_text = _real_inc_text().replace(
        "EF_ENGINE_TUNING_FIELD(double, ram_rise_gain,",
        "EF_ENGINE_TUNING_FIELD(double, ram_rise_gainn,",
        1,
    )
    assert tampered_inc_text != _real_inc_text()
    tampered_fields = _parse_inc_fields(tampered_inc_text)
    tampered_pinned = tuple(
        ("ram_rise_gainn" if name == "ram_rise_gain" else name, cpp_type, group)
        for name, cpp_type, group in _EXPECTED_FIELDS
    )

    # Old-style two-way comparison stays green after the synchronized tamper.
    assert [field.name for field in tampered_fields] == [
        name for name, _cpp_type, _group in tampered_pinned
    ]

    # Struct anchor catches it.
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(tampered_fields, _real_struct_members())


def test_type_drift_in_inc_goes_red() -> None:
    tampered = _real_inc_text().replace(
        "EF_ENGINE_TUNING_FIELD(double, mil_thrust_n,",
        "EF_ENGINE_TUNING_FIELD(bool, mil_thrust_n,",
        1,
    )
    assert tampered != _real_inc_text()
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(_parse_inc_fields(tampered), _real_struct_members())


def test_absence_set_leak_goes_red() -> None:
    # Folding `enabled` into the list would silently change its literal `true`
    # default into the seeded value and break the codec escape hatch plus the
    # top-level call site's re-seed branch.
    leaked = _real_inc_text().replace(
        "EF_ENGINE_TUNING_FIELD(double, mil_thrust_n, 0.0)",
        "EF_ENGINE_TUNING_FIELD(bool, enabled, false)\n"
        "EF_ENGINE_TUNING_FIELD(double, mil_thrust_n, 0.0)",
        1,
    )
    assert leaked != _real_inc_text()
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(_parse_inc_fields(leaked), _real_struct_members())


def test_struct_member_addition_goes_red() -> None:
    # A new EngineTuning member that the parse map does not cover must trip the
    # gate rather than silently become an unread key.
    header = _HEADER_PATH.read_text(encoding="utf-8")
    tampered = header.replace(
        "    double tsfc_ab_kg_per_nh = 0.25;",
        "    double tsfc_ab_kg_per_nh = 0.25;\n    double brand_new_knob = 1.0;",
        1,
    )
    assert tampered != header
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(
            _parse_inc_fields(_real_inc_text()), _struct_members(tampered)
        )


def test_struct_vector_member_addition_trips_the_scalar_only_gate() -> None:
    # The single-macro / single-pass shape is an adjudicated contract, not an
    # accident: a vector member must force a re-adjudication (macro split, pass
    # structure, parse_vector semantics) instead of silently joining the list.
    header = _HEADER_PATH.read_text(encoding="utf-8")
    tampered = header.replace(
        "    double tsfc_ab_kg_per_nh = 0.25;",
        "    double tsfc_ab_kg_per_nh = 0.25;\n"
        "    std::vector<double> thrust_scale_vs_mach;",
        1,
    )
    assert tampered != header
    with pytest.raises(AssertionError):
        _check_member_types_are_scalar_only(_struct_members(tampered))


def test_residue_scan_catches_middle_key_hand_written_injection() -> None:
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker + '    tuning.ram_rise_gain = src.value("ram_rise_gain", tuning.ram_rise_gain);\n',
        1,
    )
    assert injected != loader
    keys = [name for name, _cpp_type, _group in _EXPECTED_FIELDS]
    assert _hand_written_read_residues(injected, keys) == ["ram_rise_gain"]
    assert _quoted_key_literals_in_helper_body(injected, keys) == ["ram_rise_gain"]


def test_quoted_literal_belt_catches_non_value_form_injection() -> None:
    # A hand-written access avoiding the src.value shape slips past the pattern
    # scan by design; the quoted-literal belt still catches it.
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker
        + '    if (src.contains("ab_thrust_n")) {\n'
        + '        tuning.ab_thrust_n = src["ab_thrust_n"].get<double>();\n'
        + "    }\n",
        1,
    )
    assert injected != loader
    keys = [name for name, _cpp_type, _group in _EXPECTED_FIELDS]
    assert _hand_written_read_residues(injected, keys) == []
    assert _quoted_key_literals_in_helper_body(injected, keys) == ["ab_thrust_n"]


def test_include_removal_goes_red() -> None:
    # Dropping the single include pass would drop all 16 reads.
    loader = _real_loader_text()
    collapsed = loader.replace(_INC_INCLUDE_DIRECTIVE + "\n", "", 1)
    assert collapsed != loader
    assert _include_passes(collapsed) == 0


def test_enabled_read_removal_goes_red() -> None:
    # The identical read line also exists in the AERO helper (same held-field
    # pattern), and the aero helper precedes the engine helper in the file, so
    # the drill must strip the occurrence inside the ENGINE helper body
    # specifically -- a whole-file replace(..., 1) would tamper the wrong
    # function and leave this gate green.
    loader = _real_loader_text()
    body = _helper_body(loader)
    assert _ENABLED_HAND_WRITTEN_READ in body
    stripped_body = body.replace(_ENABLED_HAND_WRITTEN_READ, "", 1)
    stripped = loader.replace(body, stripped_body, 1)
    assert stripped != loader
    assert _ENABLED_HAND_WRITTEN_READ not in _helper_body(stripped)
