"""Shared mechanical substrate for the content X-macro anti-drift gates.

``tests/architecture/content/test_*_fields_inc.py`` pin the single-source
X-macro field lists under ``src/content/detail/`` against an independent
anchor. Five bundles landed as five hand-expansions of one template (I58
missile tuning, I61 direct fields, I66 aero tuning, engine tuning,
ship/submarine platform), so the same ``.inc`` reader, function-body
extractor, residue scanner and anchor parser were written out five times.

This module owns those *mechanical* pieces only. Every judgment -- which
anchor is authoritative, what the absence set is and why, which statement
order is load-bearing -- stays in the bundle's own gate module, because that
is the part a reviewer has to read.

Two anchor sources are in use and both stay first class:

- ``WorktreeAnchor``: a component struct header parsed out of the working
  tree (aero, engine, ship, submarine).
- ``GitObjectAnchor``: the retired I52 survey document, pinned as an
  immutable ``<rev>:<path>`` git object (``docs/archive_ledger.md``) so a
  working-tree edit can no longer tamper with the anchor (missile tuning,
  unit-definition direct fields).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Iterable, Union

from tests.support.paths import REPO_ROOT
from tools.maintenance.dto_schema.parse_xmacro import parse_xmacro_text


# Survey tables share one row shape across sections: | # | `key` | json_type | ...
SURVEY_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|")
_NEXT_HEADING_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)


@dataclass(frozen=True)
class WorktreeAnchor:
    """Anchor text read from a working-tree file."""

    path: Path

    def read_text(self) -> str:
        return self.path.read_text(encoding="utf-8")

    @property
    def label(self) -> str:
        return str(self.path)


@dataclass(frozen=True)
class GitObjectAnchor:
    """Anchor text read from an immutable ``<rev>:<path>`` git object.

    The pinned rev is what makes this anchor independent: unlike a
    working-tree file it cannot be edited into agreement with the ``.inc`` by
    the same commit that drifts the ``.inc``.
    """

    pin: str

    def read_text(self) -> str:
        return subprocess.run(
            ["git", "show", self.pin],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout

    @property
    def label(self) -> str:
        return f"git object {self.pin}"


AnchorSource = Union[WorktreeAnchor, GitObjectAnchor]


def parse_inc_fields(inc_text: str, macros: Iterable[str]):
    """Parse an ``.inc`` X-macro list into its ``Field`` rows."""
    return parse_xmacro_text(inc_text, frozenset(macros)).fields


def _closing_brace(source: str, opening: int):
    depth = 0
    for position in range(opening, len(source)):
        char = source[position]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return position
    return None


def _closing_brace_skipping_literals(source: str, opening: int):
    depth = 0
    pos = opening
    n = len(source)
    while pos < n:
        char = source[pos]
        two = source[pos : pos + 2]
        if two == "//":
            newline = source.find("\n", pos)
            pos = n if newline < 0 else newline
            continue
        if two == "/*":
            end = source.find("*/", pos + 2)
            pos = n if end < 0 else end + 2
            continue
        if char in ('"', "'"):
            quote = char
            pos += 1
            while pos < n:
                if source[pos] == "\\":
                    pos += 2
                    continue
                if source[pos] == quote:
                    pos += 1
                    break
                pos += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return pos
        pos += 1
    return None


def function_body(
    source: str, signature: str, *, label: str, skip_literals: bool = False
) -> str:
    """Extract a function definition body by text boundary: the signature
    occurrence followed by '{' (not ';'), then brace matching to the
    function's closing brace.

    ``skip_literals`` additionally skips string literals, char literals and
    ``//`` / ``/* */`` comments while matching. The large ``parse_unit_json``
    body needs that hardening; the small tuning helpers keep the plain matcher
    they landed with, so their tamper drills stay byte-for-byte the drills
    that were reviewed.
    """
    for match in re.finditer(re.escape(signature), source):
        index = match.end()
        while index < len(source) and source[index] not in "{;":
            index += 1
        if index >= len(source) or source[index] != "{":
            continue  # forward declaration; keep scanning
        end = (
            _closing_brace_skipping_literals(source, index)
            if skip_literals
            else _closing_brace(source, index)
        )
        if end is None:
            raise AssertionError(f"unbalanced braces in {label} definition")
        return source[index : end + 1]
    raise AssertionError(f"{label} definition not found")


def read_residues(text: str, keys: Iterable[str], access_prefix: str) -> list:
    """Keys reached by a hand-written read inside ``text``.

    ``access_prefix`` is the regex source for the accessor shapes that must
    precede the quoted key. Each bundle pins its own accessor vocabulary
    because a scan wider than the helper's own idiom produces false positives
    on neighbouring code, and a narrower one misses the shape that was
    actually migrated away.
    """
    return [
        key
        for key in keys
        if re.search(access_prefix + '"' + re.escape(key) + '"', text) is not None
    ]


def quoted_key_literals(text: str, keys: Iterable[str]) -> list:
    """Stricter belt: a table-driven region contains no quoted key literal at
    all (keys enter only via ``#name`` stringification inside the ``.inc``),
    so any quoted key literal left in it is a hand-written access of some
    form (``.value``, ``operator[]``, ``.contains``, ``.find``, ...)."""
    return [key for key in keys if f'"{key}"' in text]


def struct_members_line_scan(
    header_text: str,
    *,
    struct_open: str,
    struct_name: str,
    member_re,
    source_label: str,
) -> tuple:
    """Parse ``(member, cpp_type, initializer_text)`` in declaration order
    from a struct body delimited by ``struct_open`` up to the newline-anchored
    ``};`` that closes it.

    Strict: if the struct moves or is reshaped the gate goes red rather than
    silently anchoring to nothing. Trailing ``// unit`` comments are stripped
    before matching (several members carry them), and the initializer is ""
    for a default-constructed member.
    """
    open_index = header_text.find(struct_open)
    assert open_index >= 0, f"{struct_open!r} not found in {source_label}"
    body_start = open_index + len(struct_open)
    end_index = header_text.find("\n};", body_start)
    assert end_index > body_start, f"unterminated {struct_name} declaration"
    body = header_text[body_start:end_index]
    members = []
    for raw_line in body.splitlines():
        line = re.sub(r"//.*$", "", raw_line).strip()
        match = member_re.match(line)
        if match:
            members.append(
                (match.group("name"), match.group("type"), match.group("init") or "")
            )
    assert members, f"{struct_name} declaration yielded no parsable members"
    return tuple(members)


def struct_members_regex_scan(header_text: str, *, struct_name: str, member_re) -> tuple:
    """Parse ``(member, cpp_type, exact default token)`` in declaration order
    from a flat all-default-initialized aggregate delimited by
    ``struct <name> {`` .. ``};``. A member without the
    ``type name = default;`` shape is a reshape the caller must go red on."""
    marker = f"struct {struct_name} {{"
    start = header_text.find(marker)
    assert start >= 0, f"struct {struct_name} not found"
    end = header_text.find("};", start)
    assert end > start, f"struct {struct_name} body not terminated"
    section = header_text[start + len(marker) : end]
    rows = tuple(
        (match.group(2), match.group(1), match.group(3))
        for match in member_re.finditer(section)
    )
    assert rows, f"struct {struct_name} contains no parsable members"
    return rows


def survey_section_rows(
    survey_text: str,
    *,
    heading_prefix: str,
    section_label: str,
    source_label: str,
    row_re=SURVEY_ROW_RE,
) -> tuple:
    """Parse ``(row_number, key, json_type)`` from one survey section.

    The heading prefix is matched literally (the full heading carries an em
    dash and backticks); the section ends at the next markdown heading. The
    parser is deliberately strict: if the survey table moves or is reshaped
    the gate must go red rather than silently anchor to nothing."""
    heading_index = survey_text.find(heading_prefix)
    assert heading_index >= 0, (
        f"survey heading {heading_prefix!r} not found in {source_label}"
    )
    after_heading = survey_text[heading_index + len(heading_prefix) :]
    next_heading = _NEXT_HEADING_RE.search(after_heading)
    section = (
        after_heading if next_heading is None else after_heading[: next_heading.start()]
    )
    rows = []
    for line in section.splitlines():
        match = row_re.match(line.strip())
        if match:
            rows.append((int(match.group(1)), match.group(2), match.group(3).strip()))
    assert rows, f"{section_label} contains no parsable key rows"
    return tuple(rows)
