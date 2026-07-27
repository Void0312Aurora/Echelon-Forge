"""Anti-drift gate for the parse_unit_json direct-scalar field list (I61).

T11 slice 4 bundle 2 moved the purely-mechanical direct top-level scalar reads
of ``parse_unit_json`` (content/unit_definition_loader.cpp) onto a single-source
X-macro list at ``src/content/detail/unit_definition_direct_fields.inc``. This
gate pins that list to the I52 survey's authoritative section 1.1 "54 direct
keys" inventory and pins the loader body to being table-driven for the converged
subset while the *excluded* keys stay hand-written. It mirrors the I58
``test_missile_tuning_fields_inc.py`` precedent and reuses the same
``parse_xmacro`` reader.

Anchor structure (three-way closure, survey == .inc == pinned):

- The **I52 survey section 1.1 table** is parsed at test time and is the
  authoritative anchor. ``.inc`` converged keys must be a subset of it with
  matching key name, JSON->C++ type, and ascending survey order; the *excluded*
  register is the survey key set minus the **pinned adjudicated converged set**
  (``_ADJUDICATED_CONVERGED_KEYS``, transcribed from the I61 verdict matrix) --
  deliberately NOT survey minus the ``.inc``'s own key set, which is
  tautological (any key added to the ``.inc`` silently leaves that "excluded"
  set; I61 repair round, review P2) -- and no ``.inc`` key may fall in it (the
  "no silent extra convergence" clause: converging any un-adjudicated survey
  key goes red here by name).
- The pinned ``_CONVERGED_FIELDS`` / ``_LITERAL_DIRECT_READ_VERDICTS`` tables are the third
  leg so a survey-edit-plus-.inc-edit still needs a matching edit here.
- The ``parse_unit_json`` body is located by text boundary (signature + brace
  matching that skips strings/comments) and scanned for hand-written read
  residues of every converged key (``entry.value("key"`` / ``entry.contains(
  "key"`` / ``entry["key"]`` forms) plus a stricter quoted-key-literal belt.
  The belt is body-scoped and safe: each converged key's exact quoted literal
  is unique to its (now removed) hand-written read inside ``parse_unit_json``
  (verified: ``"mass_kg"`` elsewhere in the file lives in
  ``parse_warhead_json_fields``, outside this body).
- Both expansion sites are pinned between their original neighboring reads.
  This is behavioral, not cosmetic: JSON conversions throw, so moving a field
  changes which malformed key fails first. The two phase macros keep
  ``mass_kg`` early and ``data_link_network_id`` in the data-link block.

Converged subset scope (I61 bundle 2): ``mass_kg`` and
``data_link_network_id``. They are the two non-FLAG members among the eight
same-name, literal-default direct reads. The other six are ``has_*`` presence
or default-enablement flags whose later object-block/control-flow writes are
semantic coupling, so they stay hand-written. ``_LITERAL_DIRECT_READ_VERDICTS``
pins all eight and a source scan proves there is no ninth shape hidden by the
classification. The remaining 46 survey keys are object/escape-hatch/nested/
computed-default/clamp/fallback/validated forms rather than this exact shape.
"""

from __future__ import annotations

import re

import pytest

from tests.support.paths import REPO_ROOT
from tools.maintenance.dto_schema.parse_xmacro import parse_xmacro_text


_INC_PATH = REPO_ROOT / "src" / "content" / "detail" / "unit_definition_direct_fields.inc"
_LOADER_PATH = REPO_ROOT / "src" / "content" / "unit_definition_loader.cpp"
_SURVEY_PATH = (
    REPO_ROOT
    / "docs"
    / "plan"
    / "unified_architecture_program"
    / "t11_content_schema_survey_20260721.md"
)

_EARLY_MACRO = "EF_UNIT_DIRECT_EARLY_FIELD"
_DATA_LINK_MACRO = "EF_UNIT_DIRECT_DATA_LINK_FIELD"
_MACROS = frozenset({_EARLY_MACRO, _DATA_LINK_MACRO})

_INC_INCLUDE_DIRECTIVE = '#include "content/detail/unit_definition_direct_fields.inc"'
_LOADER_SIGNATURE = "bool parse_unit_json("

# clang-format (repo style, ColumnLimit 100) right-aligns macro continuation
# backslashes to column 100; the pins carry that exact padded text.
_EARLY_EXPANSION_BLOCK = (
    "#define EF_UNIT_DIRECT_EARLY_FIELD(cpp_type, name, default_value)" + 34 * " " + "\\\n"
    "    def.name = entry.value(#name, default_value);\n"
    "#define EF_UNIT_DIRECT_DATA_LINK_FIELD(cpp_type, name, default_value)\n"
    f"{_INC_INCLUDE_DIRECTIVE}"
)
_DATA_LINK_EXPANSION_BLOCK = (
    "#define EF_UNIT_DIRECT_EARLY_FIELD(cpp_type, name, default_value)\n"
    "#define EF_UNIT_DIRECT_DATA_LINK_FIELD(cpp_type, name, default_value)" + 30 * " " + "\\\n"
    "    def.name = entry.value(#name, default_value);\n"
    f"{_INC_INCLUDE_DIRECTIVE}"
)

# Survey section 1.1 anchoring. The heading prefix is matched literally (the
# full heading carries an em dash and backticks); the section ends at the next
# markdown heading. Row cells: | # | `key` | json_type | ... |.
_SURVEY_HEADING_PREFIX = "### 1.1 Direct Top-Level Keys (54)"
_SURVEY_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|")
_NEXT_HEADING_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)

_SURVEY_ROW_COUNT = 54
_SURVEY_JSON_TYPES = frozenset({"string", "number", "object", "array", "bool", "int"})
_SURVEY_JSON_TYPE_TO_CPP = {
    "number": "double",
    "int": "int",
    "bool": "bool",
    "array": "std::vector<double>",
    "string": "std::string",
    # `object` keys are never in the mechanical subset; no cpp mapping needed.
}

# Pinned third leg (survey == .inc == pinned): (json_key == member, cpp_type,
# exact default token, expansion phase). Defaults are tokens, not numeric
# equivalence: ``0.0f`` must not silently replace the pre-I61 ``0.0``.
_CONVERGED_FIELDS: tuple[tuple[str, str, str, str], ...] = (
    ("mass_kg", "double", "0.0", _EARLY_MACRO),
    ("data_link_network_id", "int", "0", _DATA_LINK_MACRO),
)

# The I61 adjudication verdict as a set: the ONLY survey keys allowed to appear
# in the .inc. The excluded register is computed as survey MINUS this pinned
# set. Computing it as survey minus the .inc's own key set is tautological --
# any key appended to the .inc silently leaves that "excluded" set (review P2);
# test_excluded_key_convergence_injection_goes_red replays that exact bypass.
_ADJUDICATED_CONVERGED_KEYS: frozenset[str] = frozenset(
    name for name, _cpp_type, _default, _group in _CONVERGED_FIELDS
)

# Exhaustive verdict over the strict source shape
# ``def.<same-name> = entry.value("<same-name>", <literal>);``. The test-time
# loader scan plus the .inc rows must equal this table exactly, so this is not a
# conclusion derived from the desired converged set. Six flags remain local
# because later control flow can override them or their truth means presence /
# enablement rather than a scalar content value.
_LITERAL_DIRECT_READ_VERDICTS: dict[str, tuple[str, str]] = {
    "mass_kg": ("converged", "independent scalar at the early parse seam"),
    "has_flight_model": ("held", "presence flag coupled to flight_model object parsing"),
    "has_landing_gear": ("held", "enablement flag coupled to landing_gear defaults"),
    "has_score": ("held", "default-enabled presence flag coupled to score object parsing"),
    "has_ammo": ("held", "presence flag coupled to ammo object parsing"),
    "has_command_link": ("held", "presence flag overridden by command_link object parsing"),
    "has_data_link": ("held", "data-link presence flag, not an independent scalar value"),
    "data_link_network_id": ("converged", "independent scalar at the data-link parse seam"),
}

# A spot set of section-1.1 keys deliberately kept hand-written (escape-hatch /
# object-block / has_*-flag / clamp/fallback / validated). Pinned so a future
# "just add it to the .inc" convergence of any of these trips the excluded-key
# clause with a named key rather than only the computed survey-minus-converged
# set. Not exhaustive; the computed excluded set below covers all 52 non-converged
# keys.
_EXCLUDED_KEYS_SPOT: tuple[str, ...] = (
    "type",  # REQ discriminant, validated via parse_unit_type
    "name",  # default is type_str (a computed local), not a literal
    "engine_ref",  # get<string>, REF family
    "mil_thrust_n",  # engine flat-vs-nested escape hatch; member is engine_data.*
    "sensor_ref",  # four-sensor variant escape hatch
    "has_sensor",  # SEN chain FLAG
    "has_flight_model",  # FLAG set true by the flight_model object block
    "flight_model",  # object block
    "damage_model",  # polymorphic object block
    "has_data_link",  # has_* FLAG (no object pair; deferred out of bundle 2)
    "data_link_max_reports_per_update",  # std::max(0, ...) clamp
    "data_link_max_messages_per_update",  # contains-ternary fallback
    "guidance",  # missile-tuning triple-source merge
    "fuze",  # fuze/fuse dual spelling
    "fuse",  # fuze/fuse dual spelling
)


# ---------------------------------------------------------------------------
# Pure readers/checkers. Negative tests drive these with tampered in-memory
# inputs, so none of them may read global state beyond their arguments.
# ---------------------------------------------------------------------------


def _parse_inc_fields(inc_text: str):
    return parse_xmacro_text(inc_text, _MACROS).fields


def _survey_direct_key_rows(survey_text: str) -> tuple[tuple[int, str, str], ...]:
    """Parse (row_number, key, json_type) from survey section 1.1 only."""
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
    assert rows, "survey section 1.1 contains no parsable key rows"
    return tuple(rows)


def _check_survey_is_the_54_row_inventory(survey_rows) -> None:
    numbers = [number for number, _key, _json_type in survey_rows]
    assert numbers == list(range(1, _SURVEY_ROW_COUNT + 1)), (
        "survey section 1.1 must stay the contiguous 54-row inventory, got "
        f"{len(numbers)} rows"
    )
    keys = [key for _number, key, _json_type in survey_rows]
    assert len(set(keys)) == _SURVEY_ROW_COUNT, "survey keys must be unique"
    types = {json_type for _number, _key, json_type in survey_rows}
    assert types <= _SURVEY_JSON_TYPES, f"unexpected survey json types: {types}"


def _check_inc_matches_survey(inc_fields, survey_rows) -> None:
    """Anchor: .inc converged keys are a survey subset with matching type and
    ascending survey order, and every .inc key is a member of the pinned
    adjudicated converged set (excluded register = survey keys minus
    _ADJUDICATED_CONVERGED_KEYS; never survey minus the .inc's own keys, which
    can never intersect the .inc -- review P2)."""
    survey_by_key = {key: (number, json_type) for number, key, json_type in survey_rows}
    survey_keys = set(survey_by_key)

    inc_names = [field.name for field in inc_fields]
    assert len(inc_names) == len(set(inc_names)), "duplicate key in .inc"

    converged = set(inc_names)
    assert converged <= survey_keys, (
        f".inc keys not present in survey 1.1: {sorted(converged - survey_keys)}"
    )

    # Ascending survey-row order for the converged subset.
    orders = [survey_by_key[name][0] for name in inc_names]
    assert orders == sorted(orders), (
        "unit_definition_direct_fields.inc drifted from survey 1.1 ascending order"
    )

    for field in inc_fields:
        _number, json_type = survey_by_key[field.name]
        expected_cpp = _SURVEY_JSON_TYPE_TO_CPP[json_type]
        assert field.cpp_type == expected_cpp, (
            f"{field.name}: expected {expected_cpp} for survey type {json_type}, "
            f"got {field.cpp_type}"
        )
        pinned = {name: (default, group) for name, _cpp, default, group in _CONVERGED_FIELDS}
        assert field.name in pinned, f"{field.name}: missing pinned verdict"
        expected_default, expected_group = pinned[field.name]
        assert field.default == expected_default, (
            f"{field.name}: expected exact default token {expected_default!r}, "
            f"got {field.default!r}"
        )
        assert field.group == expected_group, (
            f"{field.name}: expected phase {expected_group}, got {field.group}"
        )

    # No silent extra convergence: the excluded register derives from the
    # PINNED adjudicated set, so a well-typed survey key appended to the .inc
    # (the review-P2 bypass shape) is caught here by name.
    excluded = survey_keys - _ADJUDICATED_CONVERGED_KEYS
    leaked = converged & excluded
    assert not leaked, (
        "keys converged into the .inc without an I61 adjudication verdict: "
        f"{sorted(leaked)}"
    )


def _excluded_survey_keys(survey_rows) -> set[str]:
    """The fixed exclusion register: survey keys minus the PINNED adjudicated
    converged set (independent of whatever the .inc currently contains)."""
    return {key for _number, key, _json_type in survey_rows} - _ADJUDICATED_CONVERGED_KEYS


def _loader_function_body(loader_text: str, signature: str) -> str:
    """Extract a function definition body by text boundary: the signature
    occurrence followed by '{' (not ';'), then brace matching that skips string
    literals, char literals, and // and /* */ comments (parse_unit_json is large
    and carries braced struct-init literals, so naive counting is still safe,
    but string/comment skipping hardens against future edits)."""
    for match in re.finditer(re.escape(signature), loader_text):
        index = match.end()
        while index < len(loader_text) and loader_text[index] not in "{;":
            index += 1
        if index >= len(loader_text) or loader_text[index] != "{":
            continue  # forward declaration; keep scanning
        depth = 0
        pos = index
        n = len(loader_text)
        while pos < n:
            ch = loader_text[pos]
            two = loader_text[pos : pos + 2]
            if two == "//":
                nl = loader_text.find("\n", pos)
                pos = n if nl < 0 else nl
                continue
            if two == "/*":
                end = loader_text.find("*/", pos + 2)
                pos = n if end < 0 else end + 2
                continue
            if ch in ('"', "'"):
                quote = ch
                pos += 1
                while pos < n:
                    if loader_text[pos] == "\\":
                        pos += 2
                        continue
                    if loader_text[pos] == quote:
                        pos += 1
                        break
                    pos += 1
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return loader_text[index : pos + 1]
            pos += 1
        raise AssertionError("unbalanced braces in parse_unit_json definition")
    raise AssertionError("parse_unit_json definition not found")


def _hand_written_read_residues(loader_text: str, keys) -> list[str]:
    """Keys with a hand-written read (entry.value("key" / entry.contains("key"
    / entry["key"] forms) inside the parse_unit_json body."""
    body = _loader_function_body(loader_text, _LOADER_SIGNATURE)
    residues = []
    for key in keys:
        pattern = re.compile(
            r'entry\s*(?:\.\s*(?:value|contains)\s*\(\s*|\[\s*)"' + re.escape(key) + r'"'
        )
        if pattern.search(body):
            residues.append(key)
    return residues


def _quoted_key_literals_in_body(loader_text: str, keys) -> list[str]:
    """Stricter belt: the table-driven body contains no quoted converged-key
    literal at all (keys only enter via #name stringification inside the .inc)."""
    body = _loader_function_body(loader_text, _LOADER_SIGNATURE)
    return [key for key in keys if f'"{key}"' in body]


_LITERAL_DIRECT_READ_RE = re.compile(
    r'def\.([A-Za-z_]\w*)\s*=\s*entry\.value\("([A-Za-z_]\w*)",\s*'
    r'(true|false|-?\d+(?:\.\d+)?)\s*\);'
)


def _literal_direct_read_tokens(loader_text: str) -> dict[str, str]:
    """Return strict same-name literal reads still hand-written in the body."""
    body = _loader_function_body(loader_text, _LOADER_SIGNATURE)
    rows: dict[str, str] = {}
    for member, key, default in _LITERAL_DIRECT_READ_RE.findall(body):
        if member != key:
            continue
        assert key not in rows, f"duplicate literal direct read for {key}"
        rows[key] = default
    return rows


def _strict_shape_inventory(loader_text: str, inc_text: str) -> dict[str, str]:
    """Combine local strict-shape reads with the table-driven replacements."""
    inventory = _literal_direct_read_tokens(loader_text)
    for field in _parse_inc_fields(inc_text):
        assert field.name not in inventory, f"{field.name} is both table-driven and local"
        inventory[field.name] = field.default
    return inventory


def _check_loader_expansion_sites(loader_text: str) -> None:
    """Pin both phase blocks to their exact pre-I61 parse neighborhoods."""
    body = _loader_function_body(loader_text, _LOADER_SIGNATURE)
    assert body.count(_INC_INCLUDE_DIRECTIVE) == 2, "expected exactly two phase expansions"
    assert body.count(_EARLY_EXPANSION_BLOCK) == 1, "early expansion block drifted"
    assert body.count(_DATA_LINK_EXPANSION_BLOCK) == 1, "data-link expansion block drifted"

    name_read = body.index('def.name = entry.value("name", type_str);')
    early = body.index(_EARLY_EXPANSION_BLOCK)
    stall_init = body.index("def.has_stall_state = false;")
    assert name_read < early < stall_init, "early expansion left its original seam"

    has_data_link = body.index('def.has_data_link = entry.value("has_data_link", false);')
    data_link = body.index(_DATA_LINK_EXPANSION_BLOCK)
    max_reports = body.index("def.data_link_max_reports_per_update =")
    assert has_data_link < data_link < max_reports, "data-link expansion left its original seam"
    assert early < data_link


def _real_inc_text() -> str:
    return _INC_PATH.read_text(encoding="utf-8")


def _real_loader_text() -> str:
    return _LOADER_PATH.read_text(encoding="utf-8")


def _real_survey_rows() -> tuple[tuple[int, str, str], ...]:
    return _survey_direct_key_rows(_SURVEY_PATH.read_text(encoding="utf-8"))


def _converged_keys() -> set[str]:
    return {field.name for field in _parse_inc_fields(_real_inc_text())}


# ---------------------------------------------------------------------------
# Positive gates.
# ---------------------------------------------------------------------------


def test_inc_exists_and_parses() -> None:
    assert _INC_PATH.is_file(), f"missing single-source field list: {_INC_PATH}"
    fields = _parse_inc_fields(_real_inc_text())
    assert len(fields) == len(_CONVERGED_FIELDS)


def test_survey_section_parses_exactly_54_ordered_rows() -> None:
    _check_survey_is_the_54_row_inventory(_real_survey_rows())


def test_inc_matches_i52_survey_anchor() -> None:
    _check_inc_matches_survey(_parse_inc_fields(_real_inc_text()), _real_survey_rows())


def test_pinned_table_matches_survey_and_inc_third_leg() -> None:
    rows = _real_survey_rows()
    survey_by_key = {key: json_type for _number, key, json_type in rows}
    inc_fields = _parse_inc_fields(_real_inc_text())

    pinned_names = [name for name, _cpp, _default, _group in _CONVERGED_FIELDS]
    assert [field.name for field in inc_fields] == pinned_names, (
        "pinned _CONVERGED_FIELDS drifted from the .inc"
    )
    for name, cpp_type, default, group in _CONVERGED_FIELDS:
        assert name in survey_by_key, f"pinned converged key {name} absent from survey 1.1"
        assert _SURVEY_JSON_TYPE_TO_CPP[survey_by_key[name]] == cpp_type
        field = next(item for item in inc_fields if item.name == name)
        assert field.default == default
        assert field.group == group


def test_converged_subset_is_the_two_non_flag_literal_direct_reads() -> None:
    # Bundle-2 scope pin: converging another key must be a deliberate, reviewed
    # change to the .inc, the pinned adjudicated set, AND this literal.
    expected = {"mass_kg", "data_link_network_id"}
    assert _converged_keys() == expected
    assert set(_ADJUDICATED_CONVERGED_KEYS) == expected


def test_literal_direct_read_verdict_is_exhaustive_against_source_shape() -> None:
    inventory = _strict_shape_inventory(_real_loader_text(), _real_inc_text())
    assert set(inventory) == set(_LITERAL_DIRECT_READ_VERDICTS)
    assert inventory == {
        "mass_kg": "0.0",
        "has_flight_model": "false",
        "has_landing_gear": "false",
        "has_score": "true",
        "has_ammo": "false",
        "has_command_link": "false",
        "has_data_link": "false",
        "data_link_network_id": "0",
    }
    assert {
        key for key, (verdict, _reason) in _LITERAL_DIRECT_READ_VERDICTS.items()
        if verdict == "converged"
    } == _converged_keys()
    assert all(reason.strip() for _verdict, reason in _LITERAL_DIRECT_READ_VERDICTS.values())


def test_excluded_spot_keys_are_real_survey_keys_and_not_in_inc() -> None:
    rows = _real_survey_rows()
    survey_keys = {key for _number, key, _json_type in rows}
    inc_names = {field.name for field in _parse_inc_fields(_real_inc_text())}
    for key in _EXCLUDED_KEYS_SPOT:
        assert key in survey_keys, f"pinned excluded key {key} is not a survey 1.1 key"
        assert key not in _ADJUDICATED_CONVERGED_KEYS, (
            f"{key} is both pinned-excluded and adjudicated-converged"
        )
        assert key not in inc_names, f"excluded key {key} leaked into the .inc"


def test_all_excluded_survey_keys_absent_from_inc() -> None:
    # The exclusion register derives from the PINNED adjudicated set (52 keys
    # under the bundle-2 verdict), not from the .inc's own key set: the latter
    # can never intersect the .inc, so the check would be tautological
    # (review P2).
    rows = _real_survey_rows()
    excluded = _excluded_survey_keys(rows)
    assert len(excluded) == _SURVEY_ROW_COUNT - len(_ADJUDICATED_CONVERGED_KEYS)
    inc_names = {field.name for field in _parse_inc_fields(_real_inc_text())}
    leaked = inc_names & excluded
    assert not leaked, f"excluded survey keys leaked into the .inc: {sorted(leaked)}"


def test_loader_consumes_the_inc() -> None:
    _check_loader_expansion_sites(_real_loader_text())


def test_body_has_no_hand_written_read_for_any_converged_key() -> None:
    loader = _real_loader_text()
    converged = sorted(_converged_keys())
    assert _hand_written_read_residues(loader, converged) == []
    assert _quoted_key_literals_in_body(loader, converged) == []


def test_body_extractor_isolates_parse_unit_json() -> None:
    # Sanity: the extracted body is parse_unit_json (not the whole file) and is
    # brace-balanced -- it must contain the include and the trailing return but
    # not the following load_file definition.
    body = _loader_function_body(_real_loader_text(), _LOADER_SIGNATURE)
    assert _INC_INCLUDE_DIRECTIVE in body
    assert "return true;" in body
    assert "load_file(" not in body
    # The unrelated warhead-helper "mass_kg" literal must be outside the body.
    assert 'profile.mass_kg = src.value("mass_kg"' not in body


# ---------------------------------------------------------------------------
# Negative gates (in-memory tamper drills; the gate must go red).
# ---------------------------------------------------------------------------


def test_key_deletion_from_inc_goes_red_against_pinned_count() -> None:
    inc_lines = _real_inc_text().splitlines(keepends=True)
    dropped = "".join(line for line in inc_lines if "mass_kg" not in line)
    dropped_fields = _parse_inc_fields(dropped)
    with pytest.raises(AssertionError):
        assert len(dropped_fields) == len(_CONVERGED_FIELDS)


def test_survey_anchor_catches_synchronized_inc_and_pinned_tamper() -> None:
    # Reviewer bypass replay: rename the converged key the same way in the .inc
    # and (hypothetically) the pinned table. The survey is untampered, so the
    # anchor still goes red because the renamed key is not a survey 1.1 key.
    tampered_inc_text = _real_inc_text().replace(
        "EF_UNIT_DIRECT_EARLY_FIELD(double, mass_kg, 0.0)",
        "EF_UNIT_DIRECT_EARLY_FIELD(double, massp_kg, 0.0)",
        1,
    )
    assert tampered_inc_text != _real_inc_text()
    tampered_fields = _parse_inc_fields(tampered_inc_text)
    with pytest.raises(AssertionError):
        _check_inc_matches_survey(tampered_fields, _real_survey_rows())


def test_exact_default_token_tamper_goes_red() -> None:
    tampered = _real_inc_text().replace(
        "EF_UNIT_DIRECT_EARLY_FIELD(double, mass_kg, 0.0)",
        "EF_UNIT_DIRECT_EARLY_FIELD(double, mass_kg, 0.0f)",
        1,
    )
    assert tampered != _real_inc_text()
    with pytest.raises(AssertionError, match="exact default token"):
        _check_inc_matches_survey(_parse_inc_fields(tampered), _real_survey_rows())


@pytest.mark.parametrize("block", [_EARLY_EXPANSION_BLOCK, _DATA_LINK_EXPANSION_BLOCK])
def test_expansion_site_move_goes_red(block: str) -> None:
    loader = _real_loader_text()
    without = loader.replace(block, "", 1)
    moved = without.replace("    return true;", f"    {block}\n    return true;", 1)
    assert moved != loader
    with pytest.raises(AssertionError):
        _check_loader_expansion_sites(moved)


def test_survey_parse_tamper_goes_red() -> None:
    rows = list(_real_survey_rows())

    # Tamper A: drop a middle row (contiguity guard trips).
    dropped = tuple(row for row in rows if row[0] != 25)
    with pytest.raises(AssertionError):
        _check_survey_is_the_54_row_inventory(dropped)

    # Tamper B: renumber so it is no longer 1..54.
    renumbered = tuple((num + 1, key, jt) for num, key, jt in rows)
    with pytest.raises(AssertionError):
        _check_survey_is_the_54_row_inventory(renumbered)


def test_residue_scan_catches_hand_written_injection_of_converged_key() -> None:
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker + '    def.mass_kg = entry.value("mass_kg", 0.0);\n',
        1,
    )
    assert injected != loader
    assert _hand_written_read_residues(injected, ["mass_kg"]) == ["mass_kg"]
    assert _quoted_key_literals_in_body(injected, ["mass_kg"]) == ["mass_kg"]


def test_belt_catches_non_value_form_injection_of_converged_key() -> None:
    # A hand-written access that avoids entry.value/contains/operator[] shapes
    # still trips the quoted-literal belt.
    loader = _real_loader_text()
    marker = _INC_INCLUDE_DIRECTIVE + "\n"
    injected = loader.replace(
        marker,
        marker
        + "    { const auto& mk = entry.find(\"mass_kg\");\n"
        + "      if (mk != entry.end()) def.mass_kg = mk->get<double>(); }\n",
        1,
    )
    assert injected != loader
    assert _hand_written_read_residues(injected, ["mass_kg"]) == []
    assert _quoted_key_literals_in_body(injected, ["mass_kg"]) == ["mass_kg"]


def test_excluded_key_convergence_injection_goes_red() -> None:
    # Review-P2 bypass replay: silently converge `has_data_link` -- a well-typed
    # survey bool key adjudicated OUT as a semantic presence flag -- immediately
    # before the row-48 network id. It survives survey subset/type/order checks;
    # the pinned verdict/exclusion clauses must flag it by name.
    injected_inc = _real_inc_text().replace(
        "EF_UNIT_DIRECT_DATA_LINK_FIELD(int, data_link_network_id, 0)",
        "EF_UNIT_DIRECT_DATA_LINK_FIELD(bool, has_data_link, false)\n"
        "EF_UNIT_DIRECT_DATA_LINK_FIELD(int, data_link_network_id, 0)",
        1,
    )
    assert injected_inc != _real_inc_text()
    injected_fields = _parse_inc_fields(injected_inc)
    injected_names = {field.name for field in injected_fields}
    assert injected_names == {"mass_kg", "has_data_link", "data_link_network_id"}
    rows = _real_survey_rows()
    survey_keys = {key for _number, key, _json_type in rows}

    # Old-gate simulation (the reviewed tautology): with excluded computed as
    # survey MINUS the .inc's own keys, the injected key leaves the excluded
    # set the moment it enters the .inc, so both pre-repair clauses stayed
    # green on the injected copy.
    tautological_excluded = survey_keys - injected_names
    assert tautological_excluded & injected_names == set()  # old clause 1: green
    assert all(  # old clause 2 (all-excluded-absent-from-inc): green
        key not in injected_names for key in tautological_excluded
    )

    # Repaired gate: the exclusion register is pinned, so the injected key is
    # caught by name.
    assert "has_data_link" in _excluded_survey_keys(rows)
    with pytest.raises(AssertionError, match="has_data_link"):
        _check_inc_matches_survey(injected_fields, rows)
