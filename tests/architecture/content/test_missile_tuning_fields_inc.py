"""Anti-drift gate for the MissileTuningDefinition parse field list (I58).

T11 slice 4 bundle 1 moved the 52 JSON keys read by
``parse_missile_tuning_json_fields`` onto a single-source X-macro list at
``src/content/detail/missile_tuning_fields.inc``. This gate pins that list to
the I52 survey's authoritative inventory and pins the loader helper body to
being fully table-driven. It mirrors the I10/I26 xmacro architecture-test
precedent and reuses the same ``parse_xmacro`` reader that
``tests/support/xmacro_text.py`` uses.

Anchor structure (review hardening, I58 repair round):

- The **I52 survey section 1.2 table**
  (``docs/plan/archive/unified_architecture_program_completed_20260727/``
  ``t11_content_schema_survey_20260721.md``) is parsed at test time and is the
  authoritative anchor: ``.inc`` key set/order/type families must match it. A
  synchronized tamper of the ``.inc`` and this file's pinned table can no
  longer stay green, because neither of them is the anchor.
- The pinned ``_EXPECTED_FIELDS`` table below is kept as a third leg of a
  three-way cross-check (survey == .inc == pinned) so a survey-edit-plus-.inc
  edit still needs a matching edit here to pass.
- The helper body in ``unit_definition_loader.cpp`` is located by text
  boundary (signature + brace matching) and scanned for hand-written read
  residues of **all 52 keys** (``src.value("key"`` / ``parse_vector("key"``
  forms, plus a stricter no-quoted-key-literal belt), so a re-introduced
  hand-written read of any key -- first, middle, or last -- goes red.

The four MissileTuningDefinition members NOT read by the helper --
``warhead_profile``, ``has_warhead_profile``, ``fuze_profile``,
``has_fuze_profile`` -- are populated from the warhead/fuze/fuse object keys in
``parse_unit_json`` (survey section 1.1 rows 42-44) and are intentionally
absent from both the ``.inc`` and the survey 1.2 table.
"""

from __future__ import annotations

import re

import pytest

from tests.support.paths import REPO_ROOT


_INC_PATH = REPO_ROOT / "src" / "content" / "detail" / "missile_tuning_fields.inc"
_LOADER_PATH = REPO_ROOT / "src" / "content" / "unit_definition_loader.cpp"
_SURVEY_PATH = (
    REPO_ROOT
    / "docs"
    / "plan"
    / "archive"
    / "unified_architecture_program_completed_20260727"
    / "t11_content_schema_survey_20260721.md"
)

_SCALAR_MACRO = "EF_MISSILE_TUNING_FIELD"
_VECTOR_MACRO = "EF_MISSILE_TUNING_VECTOR_FIELD"
_MACROS = frozenset({_SCALAR_MACRO, _VECTOR_MACRO})

_INC_INCLUDE_DIRECTIVE = '#include "content/detail/missile_tuning_fields.inc"'
_HELPER_SIGNATURE = "void parse_missile_tuning_json_fields("

# Survey section 1.2 anchoring. The heading prefix is matched literally (the
# full heading carries an em dash and backticks); the section ends at the next
# markdown heading. Row cells: | # | `key` | json_type | ... |. The parser is
# deliberately strict: if the survey table moves or is reshaped, this gate must
# go red rather than silently anchor to nothing.
_SURVEY_HEADING_PREFIX = "### 1.2 Missile-Tuning Helper Keys (52)"
_SURVEY_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|")
_NEXT_HEADING_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)

_SURVEY_JSON_TYPE_TO_CPP = {
    "number": "double",
    "int": "int",
    "bool": "bool",
    "array": "std::vector<double>",
}

# Pinned third leg of the three-way cross-check (survey == .inc == pinned):
# (json_key == member name, type_family, macro group). Transcribed from I52
# survey section 1.2 rows 1-52; the survey parse is the anchor, this table only
# forces a deliberate edit in this gate file as well.
_TYPE_FAMILY_TO_CPP = {
    "double": "double",
    "int": "int",
    "bool": "bool",
    "vector": "std::vector<double>",
}
_EXPECTED_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("max_speed", "double", _SCALAR_MACRO),
    ("turn_rate", "double", _SCALAR_MACRO),
    ("fuse_distance", "double", _SCALAR_MACRO),
    ("damage", "double", _SCALAR_MACRO),
    ("seeker_fov_deg", "double", _SCALAR_MACRO),
    ("seeker_lock_range", "double", _SCALAR_MACRO),
    ("guidance_delay_s", "double", _SCALAR_MACRO),
    ("guidance_update_period_s", "double", _SCALAR_MACRO),
    ("max_flight_time_s", "double", _SCALAR_MACRO),
    ("nav_gain", "double", _SCALAR_MACRO),
    ("apn_target_accel_gain", "double", _SCALAR_MACRO),
    ("sensor_max_range", "double", _SCALAR_MACRO),
    ("sensor_fov_deg", "double", _SCALAR_MACRO),
    ("sensor_scan_period", "double", _SCALAR_MACRO),
    ("sensor_detection_prob", "double", _SCALAR_MACRO),
    ("sensor_bearing_noise_std", "double", _SCALAR_MACRO),
    ("sensor_range_noise_std", "double", _SCALAR_MACRO),
    ("sensor_track_memory_s", "double", _SCALAR_MACRO),
    ("seeker_type", "int", _SCALAR_MACRO),
    ("seeker_activation_range_m", "double", _SCALAR_MACRO),
    ("seeker_gimbal_limit_deg", "double", _SCALAR_MACRO),
    ("seeker_ifov_deg", "double", _SCALAR_MACRO),
    ("bearing_filter_tau_s", "double", _SCALAR_MACRO),
    ("elevation_filter_tau_s", "double", _SCALAR_MACRO),
    ("range_filter_tau_s", "double", _SCALAR_MACRO),
    ("track_break_time_s", "double", _SCALAR_MACRO),
    ("boost_time_s", "double", _SCALAR_MACRO),
    ("sustain_time_s", "double", _SCALAR_MACRO),
    ("boost_thrust_n", "double", _SCALAR_MACRO),
    ("sustain_thrust_n", "double", _SCALAR_MACRO),
    ("reference_area_m2", "double", _SCALAR_MACRO),
    ("cd0_subsonic", "double", _SCALAR_MACRO),
    ("cd0_supersonic", "double", _SCALAR_MACRO),
    ("induced_drag_k", "double", _SCALAR_MACRO),
    ("cd0_mach_breakpoints", "vector", _VECTOR_MACRO),
    ("cd0_mach_values", "vector", _VECTOR_MACRO),
    ("induced_drag_k_mach_breakpoints", "vector", _VECTOR_MACRO),
    ("induced_drag_k_mach_values", "vector", _VECTOR_MACRO),
    ("propellant_mass_kg", "double", _SCALAR_MACRO),
    ("max_lateral_g", "double", _SCALAR_MACRO),
    ("autopilot_tau_s", "double", _SCALAR_MACRO),
    ("autopilot_damping", "double", _SCALAR_MACRO),
    ("autopilot_order", "int", _SCALAR_MACRO),
    ("max_accel_response_g_per_s", "double", _SCALAR_MACRO),
    ("mach_transonic_start", "double", _SCALAR_MACRO),
    ("mach_transonic_end", "double", _SCALAR_MACRO),
    ("cd0_power_on_ratio", "double", _SCALAR_MACRO),
    ("min_launch_range_m", "double", _SCALAR_MACRO),
    ("max_launch_off_boresight_deg", "double", _SCALAR_MACRO),
    ("lobl_required", "bool", _SCALAR_MACRO),
    ("midcourse_datalink_supported", "bool", _SCALAR_MACRO),
    ("use_kalman_seeker", "bool", _SCALAR_MACRO),
)

# Members that live on MissileTuningDefinition but are NOT read by the helper.
_NON_HELPER_MEMBERS = (
    "warhead_profile",
    "has_warhead_profile",
    "fuze_profile",
    "has_fuze_profile",
)


# ---------------------------------------------------------------------------
# Pure readers/checkers. Negative tests drive these with tampered in-memory
# inputs, so none of them may read global state beyond their arguments.
# ---------------------------------------------------------------------------


def _parse_inc_fields(inc_text: str):
    from tools.maintenance.dto_schema.parse_xmacro import parse_xmacro_text

    return parse_xmacro_text(inc_text, _MACROS).fields


def _survey_helper_key_rows(survey_text: str) -> tuple[tuple[int, str, str], ...]:
    """Parse (row_number, key, json_type) from survey section 1.2 only."""
    heading_index = survey_text.find(_SURVEY_HEADING_PREFIX)
    assert heading_index >= 0, (
        f"survey heading {_SURVEY_HEADING_PREFIX!r} not found in {_SURVEY_PATH}"
    )
    after_heading = survey_text[heading_index + len(_SURVEY_HEADING_PREFIX) :]
    next_heading = _NEXT_HEADING_RE.search(after_heading)
    section = after_heading if next_heading is None else after_heading[: next_heading.start()]
    rows: list[tuple[int, str, str]] = []
    for line in section.splitlines():
        match = _SURVEY_ROW_RE.match(line.strip())
        if match:
            rows.append((int(match.group(1)), match.group(2), match.group(3).strip()))
    assert rows, "survey section 1.2 contains no parsable key rows"
    return tuple(rows)


def _check_inc_matches_survey(inc_fields, survey_rows) -> None:
    """Anchor assertion: .inc key set/order/type families == survey 1.2 table."""
    numbers = [number for number, _key, _json_type in survey_rows]
    assert numbers == list(range(1, 53)), (
        "survey section 1.2 must stay the contiguous 52-row inventory, got "
        f"{len(numbers)} rows"
    )
    survey_keys = [key for _number, key, _json_type in survey_rows]
    assert len(set(survey_keys)) == 52, "survey keys must be unique"
    inc_names = [field.name for field in inc_fields]
    assert inc_names == survey_keys, (
        "missile_tuning_fields.inc drifted from the I52 survey 52-key set/order"
    )
    for (number, key, json_type), field in zip(survey_rows, inc_fields):
        expected_cpp = _SURVEY_JSON_TYPE_TO_CPP[json_type]
        assert field.cpp_type == expected_cpp, (
            f"survey row {number} ({key}): expected {expected_cpp}, got {field.cpp_type}"
        )
        expected_group = _VECTOR_MACRO if json_type == "array" else _SCALAR_MACRO
        assert field.group == expected_group, (
            f"survey row {number} ({key}): wrong macro group {field.group}"
        )


def _helper_body(loader_text: str) -> str:
    """Extract the parse_missile_tuning_json_fields definition body by text
    boundary: the signature occurrence that is followed by '{' (not ';'), then
    brace matching to the function's closing brace."""
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
            "unbalanced braces in parse_missile_tuning_json_fields definition"
        )
    raise AssertionError("parse_missile_tuning_json_fields definition not found")


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
    """Stricter belt: the table-driven body contains no quoted key literal at
    all (keys only enter via #name stringification inside the .inc), so any
    quoted 52-key literal in the body is a hand-written access of some form
    (src.value, src[...], src.contains, ...)."""
    body = _helper_body(loader_text)
    return [key for key in keys if f'"{key}"' in body]


def _real_inc_text() -> str:
    return _INC_PATH.read_text(encoding="utf-8")


def _real_loader_text() -> str:
    return _LOADER_PATH.read_text(encoding="utf-8")


def _real_survey_rows() -> tuple[tuple[int, str, str], ...]:
    return _survey_helper_key_rows(_SURVEY_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Positive gates.
# ---------------------------------------------------------------------------


def test_inc_exists_and_parses() -> None:
    assert _INC_PATH.is_file(), f"missing single-source field list: {_INC_PATH}"
    assert len(_parse_inc_fields(_real_inc_text())) == 52


def test_survey_section_parses_exactly_52_ordered_rows() -> None:
    rows = _real_survey_rows()
    assert [number for number, _key, _json_type in rows] == list(range(1, 53))
    assert {json_type for _number, _key, json_type in rows} <= set(
        _SURVEY_JSON_TYPE_TO_CPP
    )


def test_inc_matches_i52_survey_anchor() -> None:
    _check_inc_matches_survey(_parse_inc_fields(_real_inc_text()), _real_survey_rows())


def test_pinned_table_matches_survey_third_leg() -> None:
    # Three-way closure: the pinned table in this file must itself match the
    # survey anchor (names, order, type family, macro group).
    rows = _real_survey_rows()
    pinned_names = [name for name, _family, _group in _EXPECTED_FIELDS]
    assert pinned_names == [key for _number, key, _json_type in rows]
    for (number, key, json_type), (name, family, group) in zip(rows, _EXPECTED_FIELDS):
        assert _TYPE_FAMILY_TO_CPP[family] == _SURVEY_JSON_TYPE_TO_CPP[json_type], (
            f"survey row {number} ({key}): pinned family {family} disagrees"
        )
        expected_group = _VECTOR_MACRO if json_type == "array" else _SCALAR_MACRO
        assert group == expected_group, f"pinned row {name}: wrong macro group"


def test_vector_family_is_exactly_the_four_mach_arrays() -> None:
    vectors = tuple(
        field.name
        for field in _parse_inc_fields(_real_inc_text())
        if field.group == _VECTOR_MACRO
    )
    assert vectors == (
        "cd0_mach_breakpoints",
        "cd0_mach_values",
        "induced_drag_k_mach_breakpoints",
        "induced_drag_k_mach_values",
    )


def test_non_helper_members_are_absent_from_inc_and_survey() -> None:
    inc_names = {field.name for field in _parse_inc_fields(_real_inc_text())}
    survey_keys = {key for _number, key, _json_type in _real_survey_rows()}
    for member in _NON_HELPER_MEMBERS:
        assert member not in inc_names, (
            f"{member} is populated outside parse_missile_tuning_json_fields "
            "and must not appear in the parse field list"
        )
        assert member not in survey_keys


def test_loader_helper_consumes_the_inc() -> None:
    loader = _real_loader_text()
    assert _INC_INCLUDE_DIRECTIVE in _helper_body(loader), (
        "parse_missile_tuning_json_fields must include the single-source list"
    )


def test_helper_body_has_no_hand_written_read_for_any_of_the_52_keys() -> None:
    # Full-inventory residue scan (review hardening: first/last-key spot checks
    # missed a middle-key reintroduction).
    loader = _real_loader_text()
    survey_keys = [key for _number, key, _json_type in _real_survey_rows()]
    assert _hand_written_read_residues(loader, survey_keys) == []
    assert _quoted_key_literals_in_helper_body(loader, survey_keys) == []


# ---------------------------------------------------------------------------
# Negative gates (in-memory tamper drills; the gate must go red).
# ---------------------------------------------------------------------------


def test_key_deletion_from_inc_goes_red_against_survey() -> None:
    inc_lines = _real_inc_text().splitlines(keepends=True)
    dropped = "".join(line for line in inc_lines if "use_kalman_seeker" not in line)
    mutated_fields = _parse_inc_fields(dropped)
    assert len(mutated_fields) == 51
    with pytest.raises(AssertionError):
        _check_inc_matches_survey(mutated_fields, _real_survey_rows())


def test_survey_anchor_catches_synchronized_inc_and_pinned_tamper() -> None:
    # Reviewer bypass replay (P2-1): tamper the .inc AND the pinned table the
    # same way. The old gate compared only these two against each other and
    # stayed green; the survey anchor now catches it.
    tampered_inc_text = _real_inc_text().replace(
        "EF_MISSILE_TUNING_FIELD(double, damage,",
        "EF_MISSILE_TUNING_FIELD(double, dammage,",
        1,
    )
    assert tampered_inc_text != _real_inc_text()
    tampered_inc_fields = _parse_inc_fields(tampered_inc_text)
    tampered_pinned = tuple(
        ("dammage" if name == "damage" else name, family, group)
        for name, family, group in _EXPECTED_FIELDS
    )

    # Old-gate simulation: .inc vs pinned-table comparison is green after the
    # synchronized tamper (this was the reviewer's bypass evidence).
    assert [field.name for field in tampered_inc_fields] == [
        name for name, _family, _group in tampered_pinned
    ]

    # New anchor: the survey is not tampered, so the gate goes red.
    with pytest.raises(AssertionError):
        _check_inc_matches_survey(tampered_inc_fields, _real_survey_rows())


def test_survey_parse_tamper_goes_red() -> None:
    rows = list(_real_survey_rows())
    real_inc_fields = _parse_inc_fields(_real_inc_text())

    # Tamper A: swap two middle keys (row numbers stay contiguous).
    swapped = list(rows)
    swapped[25], swapped[26] = (
        (swapped[25][0], swapped[26][1], swapped[26][2]),
        (swapped[26][0], swapped[25][1], swapped[25][2]),
    )
    with pytest.raises(AssertionError):
        _check_inc_matches_survey(real_inc_fields, tuple(swapped))

    # Tamper B: drop a middle row entirely (contiguity guard trips).
    dropped = tuple(row for row in rows if row[0] != 26)
    with pytest.raises(AssertionError):
        _check_inc_matches_survey(real_inc_fields, dropped)


def test_residue_scan_catches_middle_key_hand_written_injection() -> None:
    # Reviewer bypass replay (P2-2): inject a hand-written read of the middle
    # key `damage` into the helper body. The old gate only spot-checked
    # max_speed / use_kalman_seeker and stayed green; the full scan catches it.
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker + '    tuning.damage = src.value("damage", tuning.damage);\n',
        1,
    )
    assert injected != loader

    # Old-gate simulation: both spot-checked patterns are still absent, so the
    # old assertions would have stayed green on the injected text.
    assert 'tuning.max_speed = src.value("max_speed"' not in injected
    assert 'tuning.use_kalman_seeker = src.value("use_kalman_seeker"' not in injected

    survey_keys = [key for _number, key, _json_type in _real_survey_rows()]
    assert _hand_written_read_residues(injected, survey_keys) == ["damage"]
    assert _quoted_key_literals_in_helper_body(injected, survey_keys) == ["damage"]


def test_residue_scan_catches_vector_key_hand_written_injection() -> None:
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker + '    parse_vector("cd0_mach_values", &tuning.cd0_mach_values);\n',
        1,
    )
    assert injected != loader
    survey_keys = [key for _number, key, _json_type in _real_survey_rows()]
    assert _hand_written_read_residues(injected, survey_keys) == ["cd0_mach_values"]


def test_quoted_literal_belt_catches_non_value_form_injection() -> None:
    # A hand-written access that avoids the src.value/parse_vector shapes (e.g.
    # operator[] with contains) slips past the pattern scan by design; the
    # quoted-literal belt still catches it.
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker
        + '    if (src.contains("boost_time_s")) {\n'
        + '        tuning.boost_time_s = src["boost_time_s"].get<double>();\n'
        + "    }\n",
        1,
    )
    assert injected != loader
    survey_keys = [key for _number, key, _json_type in _real_survey_rows()]
    assert _hand_written_read_residues(injected, survey_keys) == []
    assert _quoted_key_literals_in_helper_body(injected, survey_keys) == [
        "boost_time_s"
    ]
