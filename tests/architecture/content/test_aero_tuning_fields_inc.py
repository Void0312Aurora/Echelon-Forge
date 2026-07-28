"""Anti-drift gate for the AeroTuning parse field list (T11 slice 4 bundle 3).

This iteration moved the 44 purely-mechanical JSON keys read by
``parse_aero_tuning_json_fields`` onto a single-source X-macro list at
``src/content/detail/aero_tuning_fields.inc``, following the I58
``missile_tuning_fields.inc`` precedent and the landed I61 direct-fields test
template (commit e710d64f on codex/redundancy-consolidation).

Anchor structure (the I58 review-hardening discipline: the gate must not be a
two-way comparison that a synchronized tamper can satisfy):

- The **AeroTuning declaration** in
  ``src/components/domains/air/platform/flight_dynamics_tuning.h`` is parsed at
  test time and is the authoritative anchor. Unlike the missile-tuning bundle
  (whose anchor is the I52 survey's explicit 52-row table), the I52 survey has
  no per-key table for the aero helper -- it records ``aero_tuning`` as a single
  object row (section 1.1 row 29) -- so the struct declaration is the only
  independent inventory of this parse surface. The ``.inc`` must cover exactly
  the declaration's members minus the adjudicated absence set, with matching
  C++ types and macro groups.
- The pinned ``_EXPECTED_FIELDS`` table below is a third leg of a three-way
  cross-check (declaration == .inc == pinned), so a header-edit-plus-.inc-edit
  still needs a matching edit here to pass.
- The helper body in ``unit_definition_loader.cpp`` is located by text boundary
  (signature + brace matching) and scanned for hand-written read residues of
  **all 44 keys**, plus a stricter no-quoted-key-literal belt, so a
  re-introduced hand-written read of any key -- first, middle, or last -- goes
  red.
- The two-pass include contract (scalars before the ``parse_vector`` lambda,
  vectors after it) is pinned, because it is what makes the expansion
  token-for-token equal to the pre-change statement order.

ABSENCE SET: ``enabled`` is the one member read by the helper that stays
hand-written. Its read takes a *literal* ``true`` default rather than the
"missing key keeps the existing value" form, which is load-bearing for the
``airframe.tuning`` / ``aero_tuning`` codec escape hatch (census section 3 red
line "codec escape hatches must be preserved"): both call sites seed from the
``flight_dynamics::default_aero_tuning()`` preset and then merge, so a present
``aero_tuning`` object without an ``enabled`` key must still come out enabled.
This gate pins both that ``enabled`` is absent from the ``.inc`` and that the
literal-default hand-written read is still present in the helper body.
"""

from __future__ import annotations

import re

import pytest

from tests.support.paths import REPO_ROOT
from tools.maintenance.dto_schema.parse_xmacro import parse_xmacro_text


_INC_PATH = REPO_ROOT / "src" / "content" / "detail" / "aero_tuning_fields.inc"
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

_SCALAR_MACRO = "EF_AERO_TUNING_FIELD"
_VECTOR_MACRO = "EF_AERO_TUNING_VECTOR_FIELD"
_MACROS = frozenset({_SCALAR_MACRO, _VECTOR_MACRO})

_INC_INCLUDE_DIRECTIVE = '#include "content/detail/aero_tuning_fields.inc"'
_HELPER_SIGNATURE = "void parse_aero_tuning_json_fields("

# The hand-written literal-default read that must survive the migration.
_ENABLED_HAND_WRITTEN_READ = 'tuning.enabled = src.value("enabled", true);'

# Members declared on AeroTuning but deliberately NOT in the field list.
_ABSENT_MEMBERS = ("enabled",)

# AeroTuning declaration parsing. Members are plain `<type> <name> = <init>;` or
# `std::vector<double> <name>;` lines inside the struct body.
_STRUCT_OPEN = "struct AeroTuning {"
_MEMBER_RE = re.compile(
    r"^(?P<type>bool|double|std::vector<double>)\s+(?P<name>\w+)"
    r"\s*(?:=\s*(?P<init>[^;]*?)\s*)?;$"
)

_VECTOR_CPP_TYPE = "std::vector<double>"

# Pinned third leg (declaration == .inc == pinned): (member, cpp_type, macro).
# Order is the historical hand-written READ order, which differs from the
# declaration order: the struct declares control_effectiveness_scale_vs_mach
# among the scalars (between fbw_pitch_rate_per_g_err and actuator_tau_*), while
# the hand-written body read all scalars first and all vectors after, putting it
# last. Read order is what token-for-token parity requires, so read order is
# what the .inc pins; the struct layout is untouched (ABI red line).
_EXPECTED_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("cl_alpha_per_deg", "double", _SCALAR_MACRO),
    ("cl0", "double", _SCALAR_MACRO),
    ("cd0_clean", "double", _SCALAR_MACRO),
    ("induced_drag_k", "double", _SCALAR_MACRO),
    ("cm_alpha_per_rad", "double", _SCALAR_MACRO),
    ("cm_q", "double", _SCALAR_MACRO),
    ("alpha_stall_clean_deg", "double", _SCALAR_MACRO),
    ("alpha_stall_flaps_full_deg", "double", _SCALAR_MACRO),
    ("alpha_peak_offset_deg", "double", _SCALAR_MACRO),
    ("alpha_deep_offset_deg", "double", _SCALAR_MACRO),
    ("cl_peak_clean", "double", _SCALAR_MACRO),
    ("cl_peak_flaps_full", "double", _SCALAR_MACRO),
    ("cl_deep_clean", "double", _SCALAR_MACRO),
    ("cl_deep_flaps_full", "double", _SCALAR_MACRO),
    ("pitch_break_onset_deg", "double", _SCALAR_MACRO),
    ("pitch_break_full_deg", "double", _SCALAR_MACRO),
    ("pitch_break_cm_nose_down", "double", _SCALAR_MACRO),
    ("post_stall_damp_floor", "double", _SCALAR_MACRO),
    ("aoa_rate_pitch_break_gain", "double", _SCALAR_MACRO),
    ("elevator_max_deflection_deg", "double", _SCALAR_MACRO),
    ("aileron_max_deflection_deg", "double", _SCALAR_MACRO),
    ("rudder_max_deflection_deg", "double", _SCALAR_MACRO),
    ("cm_delta_e_per_rad", "double", _SCALAR_MACRO),
    ("cl_delta_a_per_rad", "double", _SCALAR_MACRO),
    ("cn_delta_r_per_rad", "double", _SCALAR_MACRO),
    ("fbw_elevator_cmd_per_rate_err", "double", _SCALAR_MACRO),
    ("fbw_aileron_cmd_per_rate_err", "double", _SCALAR_MACRO),
    ("fbw_rudder_cmd_per_rate_err", "double", _SCALAR_MACRO),
    ("ari_rudder_cmd_per_aileron_cmd", "double", _SCALAR_MACRO),
    ("fbw_g_command_enabled", "bool", _SCALAR_MACRO),
    ("fbw_g_command_neutral", "double", _SCALAR_MACRO),
    ("fbw_g_command_max", "double", _SCALAR_MACRO),
    ("fbw_g_command_min", "double", _SCALAR_MACRO),
    ("fbw_pitch_rate_per_g_err", "double", _SCALAR_MACRO),
    ("actuator_tau_elevator_s", "double", _SCALAR_MACRO),
    ("actuator_tau_aileron_s", "double", _SCALAR_MACRO),
    ("actuator_tau_rudder_s", "double", _SCALAR_MACRO),
    ("mach_breakpoints", _VECTOR_CPP_TYPE, _VECTOR_MACRO),
    ("cl_alpha_scale_vs_mach", _VECTOR_CPP_TYPE, _VECTOR_MACRO),
    ("cd0_add_vs_mach", _VECTOR_CPP_TYPE, _VECTOR_MACRO),
    ("induced_drag_scale_vs_mach", _VECTOR_CPP_TYPE, _VECTOR_MACRO),
    ("cm_alpha_scale_vs_mach", _VECTOR_CPP_TYPE, _VECTOR_MACRO),
    ("stall_alpha_delta_deg_vs_mach", _VECTOR_CPP_TYPE, _VECTOR_MACRO),
    ("control_effectiveness_scale_vs_mach", _VECTOR_CPP_TYPE, _VECTOR_MACRO),
)

_EXPECTED_FIELD_COUNT = 44


# ---------------------------------------------------------------------------
# Pure readers/checkers. Negative tests drive these with tampered in-memory
# inputs, so none of them may read global state beyond their arguments.
# ---------------------------------------------------------------------------


def _parse_inc_fields(inc_text: str):
    return parse_xmacro_text(inc_text, _MACROS).fields


def _struct_members(header_text: str) -> tuple[tuple[str, str], ...]:
    """Parse (member, cpp_type) from the AeroTuning declaration, in declaration
    order. Strict: if the struct moves or is reshaped, the gate goes red rather
    than silently anchoring to nothing."""
    return tuple(
        (name, cpp_type) for name, cpp_type, _init in _struct_members_with_init(header_text)
    )


def _struct_members_with_init(
    header_text: str,
) -> tuple[tuple[str, str, str], ...]:
    """Parse (member, cpp_type, initializer_text) from the AeroTuning
    declaration. The initializer is "" for the default-constructed vectors."""
    open_index = header_text.find(_STRUCT_OPEN)
    assert open_index >= 0, f"{_STRUCT_OPEN!r} not found in {_HEADER_PATH}"
    body_start = open_index + len(_STRUCT_OPEN)
    end_index = header_text.find("\n};", body_start)
    assert end_index > body_start, "unterminated AeroTuning declaration"
    body = header_text[body_start:end_index]
    members: list[tuple[str, str, str]] = []
    for raw_line in body.splitlines():
        # Several members carry a trailing `// unit` comment (e.g.
        # `double fbw_g_command_max = 8.0;  // g at full aft stick`), so strip
        # trailing comments before matching the declaration shape.
        line = re.sub(r"//.*$", "", raw_line).strip()
        match = _MEMBER_RE.match(line)
        if match:
            members.append(
                (match.group("name"), match.group("type"), match.group("init") or "")
            )
    assert members, "AeroTuning declaration yielded no parsable members"
    return tuple(members)


def _check_recorded_defaults_match_struct(inc_fields, struct_members_with_init) -> None:
    """The .inc's default_value token is parity-only (never expanded into the
    parse), so nothing in the build would notice if it drifted from the struct
    initializer it claims to mirror. This check is what makes that claim
    load-bearing: every scalar row's recorded token must equal the declared
    initializer verbatim, and every vector row must record `{}` for the
    default-constructed empty table."""
    declared_init = {
        name: init for name, _cpp_type, init in struct_members_with_init
    }
    for field in inc_fields:
        recorded = field.default.strip()
        if field.group == _VECTOR_MACRO:
            assert declared_init[field.name] == "", (
                f"{field.name}: declared vector gained an initializer "
                f"({declared_init[field.name]!r}); the .inc records `{{}}`"
            )
            assert recorded == "{}", (
                f"{field.name}: vector rows must record `{{}}`, got {recorded!r}"
            )
            continue
        assert recorded == declared_init[field.name], (
            f"{field.name}: .inc records default {recorded!r} but AeroTuning "
            f"declares {declared_init[field.name]!r}; the parity-only token must "
            "mirror the struct initializer exactly"
        )


def _check_inc_matches_struct(inc_fields, struct_members) -> None:
    """Anchor assertion: .inc covers exactly the AeroTuning members minus the
    adjudicated absence set, with matching types and macro groups."""
    declared = {name: cpp_type for name, cpp_type in struct_members}
    assert len(declared) == len(struct_members), "duplicate AeroTuning member"

    for absent in _ABSENT_MEMBERS:
        assert absent in declared, (
            f"absence-set member {absent} no longer exists on AeroTuning; the "
            "adjudication must be revisited"
        )

    expected_covered = {
        name for name in declared if name not in set(_ABSENT_MEMBERS)
    }
    inc_names = [field.name for field in inc_fields]
    assert len(set(inc_names)) == len(inc_names), ".inc has a duplicate key"
    assert set(inc_names) == expected_covered, (
        "aero_tuning_fields.inc drifted from the AeroTuning declaration: "
        f"missing={sorted(expected_covered - set(inc_names))} "
        f"unexpected={sorted(set(inc_names) - expected_covered)}"
    )
    for field in inc_fields:
        assert field.cpp_type == declared[field.name], (
            f"{field.name}: .inc type {field.cpp_type} != declared "
            f"{declared[field.name]}"
        )
        expected_group = (
            _VECTOR_MACRO if declared[field.name] == _VECTOR_CPP_TYPE else _SCALAR_MACRO
        )
        assert field.group == expected_group, (
            f"{field.name}: wrong macro group {field.group}"
        )


def _check_pinned_matches_struct(struct_members) -> None:
    """Third leg: the pinned table itself must agree with the declaration on the
    member set and per-member type/group (order is read order, not declaration
    order, so only the set and the per-member data are cross-checked here)."""
    declared = dict(struct_members)
    pinned = {name: (cpp_type, group) for name, cpp_type, group in _EXPECTED_FIELDS}
    expected_covered = {
        name for name in declared if name not in set(_ABSENT_MEMBERS)
    }
    assert set(pinned) == expected_covered, (
        "pinned _EXPECTED_FIELDS drifted from the AeroTuning declaration"
    )
    for name, (cpp_type, group) in pinned.items():
        assert cpp_type == declared[name], f"pinned {name}: type disagrees"
        expected_group = (
            _VECTOR_MACRO if declared[name] == _VECTOR_CPP_TYPE else _SCALAR_MACRO
        )
        assert group == expected_group, f"pinned {name}: wrong macro group"


def _helper_body(loader_text: str) -> str:
    """Extract the parse_aero_tuning_json_fields definition body by text
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
            "unbalanced braces in parse_aero_tuning_json_fields definition"
        )
    raise AssertionError("parse_aero_tuning_json_fields definition not found")


def _hand_written_read_residues(loader_text: str, keys) -> list[str]:
    """Keys with a hand-written read (src.value("key" / parse_vector("key"
    forms) inside the helper body."""
    body = _helper_body(loader_text)
    residues = []
    for key in keys:
        pattern = re.compile(
            r'(?:src\s*\.\s*value|parse_vector)\s*\(\s*"' + re.escape(key) + r'"'
        )
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
    # 44 migrated keys + the held `enabled`.
    assert len(members) == _EXPECTED_FIELD_COUNT + len(_ABSENT_MEMBERS)
    assert {cpp_type for _name, cpp_type in members} <= {
        "bool",
        "double",
        _VECTOR_CPP_TYPE,
    }


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
    # Read order (all scalars, then all vectors) is what token-for-token parity
    # with the pre-change body requires; it is deliberately not declaration
    # order (see the module docstring and the .inc header).
    inc_fields = _parse_inc_fields(_real_inc_text())
    assert [field.name for field in inc_fields] == [
        name for name, _cpp_type, _group in _EXPECTED_FIELDS
    ]
    groups = [field.group for field in inc_fields]
    assert groups == sorted(groups, key=lambda g: 0 if g == _SCALAR_MACRO else 1), (
        "the .inc must list all scalar rows before all vector rows: the loader's "
        "two-pass include reproduces the pre-change statement order from it"
    )


def test_vector_family_is_exactly_the_seven_mach_tables() -> None:
    vectors = tuple(
        field.name
        for field in _parse_inc_fields(_real_inc_text())
        if field.group == _VECTOR_MACRO
    )
    assert vectors == (
        "mach_breakpoints",
        "cl_alpha_scale_vs_mach",
        "cd0_add_vs_mach",
        "induced_drag_scale_vs_mach",
        "cm_alpha_scale_vs_mach",
        "stall_alpha_delta_deg_vs_mach",
        "control_effectiveness_scale_vs_mach",
    )


def test_no_angle_bracket_comma_type_entered_the_list() -> None:
    # Census red line "X-macro comma blockers" / I31 precedent: the preprocessor
    # pairs only parentheses, so a type carrying an intra-angle comma would be
    # mis-split. None of AeroTuning's members qualify, and no alias exemption is
    # used, so every row's recorded type must be comma-free.
    for field in _parse_inc_fields(_real_inc_text()):
        assert "," not in field.cpp_type, (
            f"{field.name}: angle-bracket-comma type {field.cpp_type} must be "
            "held hand-written per the I31 precedent, not aliased into the list"
        )
    for _name, cpp_type in _real_struct_members():
        assert "," not in cpp_type, (
            f"AeroTuning gained an angle-bracket-comma member ({cpp_type}); it "
            "must be adjudicated before entering the X-macro list"
        )


def test_absence_set_is_absent_and_its_hand_written_read_survives() -> None:
    inc_names = {field.name for field in _parse_inc_fields(_real_inc_text())}
    body = _helper_body(_real_loader_text())
    for member in _ABSENT_MEMBERS:
        assert member not in inc_names, (
            f"{member} is not a mechanical read and must stay hand-written"
        )
    # The literal `true` default is the codec escape hatch's contract.
    assert _ENABLED_HAND_WRITTEN_READ in body, (
        "the hand-written literal-default read of `enabled` must survive: the "
        "airframe.tuning / aero_tuning preset-then-merge path depends on it"
    )


def test_loader_helper_consumes_the_inc_in_two_passes() -> None:
    loader = _real_loader_text()
    assert _include_passes(loader) == 2, (
        "parse_aero_tuning_json_fields must include the single-source list twice "
        "(scalars before the parse_vector lambda, vectors after) to preserve the "
        "pre-change statement order"
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
    # The drill that found this gap during authoring: silently changing a
    # recorded default must not stay green.
    tampered = _real_inc_text().replace(
        "EF_AERO_TUNING_FIELD(double, cm_q, -12.0)",
        "EF_AERO_TUNING_FIELD(double, cm_q, -13.0)",
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
    tampered = header.replace("double cm_q = -12.0;", "double cm_q = -14.0;", 1)
    assert tampered != header
    with pytest.raises(AssertionError):
        _check_recorded_defaults_match_struct(
            _parse_inc_fields(_real_inc_text()), _struct_members_with_init(tampered)
        )


def test_key_deletion_from_inc_goes_red_against_struct() -> None:
    inc_lines = _real_inc_text().splitlines(keepends=True)
    dropped = "".join(
        line for line in inc_lines if "actuator_tau_rudder_s" not in line
    )
    mutated = _parse_inc_fields(dropped)
    assert len(mutated) == _EXPECTED_FIELD_COUNT - 1
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(mutated, _real_struct_members())


def test_struct_anchor_catches_synchronized_inc_and_pinned_tamper() -> None:
    # A tamper of the .inc AND the pinned table the same way would satisfy a
    # two-way gate. The struct declaration is untampered, so the gate goes red.
    tampered_inc_text = _real_inc_text().replace(
        "EF_AERO_TUNING_FIELD(double, cm_q,",
        "EF_AERO_TUNING_FIELD(double, cm_qq,",
        1,
    )
    assert tampered_inc_text != _real_inc_text()
    tampered_fields = _parse_inc_fields(tampered_inc_text)
    tampered_pinned = tuple(
        ("cm_qq" if name == "cm_q" else name, cpp_type, group)
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
        "EF_AERO_TUNING_FIELD(bool, fbw_g_command_enabled,",
        "EF_AERO_TUNING_FIELD(double, fbw_g_command_enabled,",
        1,
    )
    assert tampered != _real_inc_text()
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(_parse_inc_fields(tampered), _real_struct_members())


def test_absence_set_leak_goes_red() -> None:
    # Folding `enabled` into the list would silently change its literal `true`
    # default into the seeded value and break the codec escape hatch.
    leaked = _real_inc_text().replace(
        "EF_AERO_TUNING_FIELD(double, cl_alpha_per_deg, 0.1)",
        "EF_AERO_TUNING_FIELD(bool, enabled, false)\n"
        "EF_AERO_TUNING_FIELD(double, cl_alpha_per_deg, 0.1)",
        1,
    )
    assert leaked != _real_inc_text()
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(_parse_inc_fields(leaked), _real_struct_members())


def test_struct_member_addition_goes_red() -> None:
    # A new AeroTuning member that the parse map does not cover must trip the
    # gate rather than silently become an unread key.
    header = _HEADER_PATH.read_text(encoding="utf-8")
    tampered = header.replace(
        "    double actuator_tau_rudder_s = 0.12;",
        "    double actuator_tau_rudder_s = 0.12;\n    double brand_new_knob = 1.0;",
        1,
    )
    assert tampered != header
    with pytest.raises(AssertionError):
        _check_inc_matches_struct(
            _parse_inc_fields(_real_inc_text()), _struct_members(tampered)
        )


def test_residue_scan_catches_middle_key_hand_written_injection() -> None:
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker + '    tuning.cm_q = src.value("cm_q", tuning.cm_q);\n',
        1,
    )
    assert injected != loader
    keys = [name for name, _cpp_type, _group in _EXPECTED_FIELDS]
    assert _hand_written_read_residues(injected, keys) == ["cm_q"]
    assert _quoted_key_literals_in_helper_body(injected, keys) == ["cm_q"]


def test_residue_scan_catches_vector_key_hand_written_injection() -> None:
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker + '    parse_vector("mach_breakpoints", &tuning.mach_breakpoints);\n',
        1,
    )
    assert injected != loader
    keys = [name for name, _cpp_type, _group in _EXPECTED_FIELDS]
    assert _hand_written_read_residues(injected, keys) == ["mach_breakpoints"]


def test_quoted_literal_belt_catches_non_value_form_injection() -> None:
    # A hand-written access avoiding the src.value/parse_vector shapes slips past
    # the pattern scan by design; the quoted-literal belt still catches it.
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker
        + '    if (src.contains("cd0_clean")) {\n'
        + '        tuning.cd0_clean = src["cd0_clean"].get<double>();\n'
        + "    }\n",
        1,
    )
    assert injected != loader
    keys = [name for name, _cpp_type, _group in _EXPECTED_FIELDS]
    assert _hand_written_read_residues(injected, keys) == []
    assert _quoted_key_literals_in_helper_body(injected, keys) == ["cd0_clean"]


def test_two_pass_include_collapse_goes_red() -> None:
    # Dropping one include pass would drop 37 scalar reads or 7 vector reads.
    loader = _real_loader_text()
    collapsed = loader.replace(_INC_INCLUDE_DIRECTIVE + "\n", "", 1)
    assert collapsed != loader
    assert _include_passes(collapsed) == 1


def test_enabled_read_removal_goes_red() -> None:
    loader = _real_loader_text()
    stripped = loader.replace(_ENABLED_HAND_WRITTEN_READ, "", 1)
    assert stripped != loader
    assert _ENABLED_HAND_WRITTEN_READ not in _helper_body(stripped)
