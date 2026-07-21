"""T9 slice 1 architecture gate: agency authority registry <-> census ratchet.

This gate ties four things together for the maintained authority surface:

1. **Registry consistency.** ``python/tasking_contracts/agency_registry.py``
   declares the role/scope/delegation/arbitration/gating/doctrine vocabulary; the
   gate asserts every authority category surfaced by the census has a non-empty
   registered vocabulary, that each census file's adjudicated categories are
   *grounded* in (and *cover*) its pinned tokens' candidate categories, and that
   the SCAL ``AgentRole`` five-part schema / ``DoctrineFamily`` placeholder are
   declared as expected.

2. **Compiled authority mirror.** The gate parses the compiled enum/scope headers
   (``core_tasking_enums.h``, ``naval_tasking_enums.h``, ``policy_contracts.h``)
   and asserts the registry mirror reproduces the actual enum members and
   action-interface scope values, so any drift between the declared vocabulary and
   the compiled authority model fails loudly.

3. **Census fingerprint pin.** Every scattered authority-check site is pinned in
   ``tests/architecture/fixtures/agency_authority_census_20260721.json`` by a
   per-file **token->count** fingerprint. Tokens are matched by **word boundary**
   (``\bTOKEN\b``) so a token never double-counts inside a longer identifier
   (``commander_id`` inside ``ground_commander_id``); this is what lets the synonym
   family (``commander_id`` / ``command_relationship`` / ``infer_command_relationship``
   / the loader-delegate ``_hierarchical_command_chain_active``) be tokenized without
   collisions. If a pinned file's authority-token *count* drifts (a token
   added/removed, including a *second* occurrence of an already-present token), the
   gate fails loudly so the census cannot silently rot -- the same shrink-only
   discipline as the I38 include-direction allowlist. The **key re-adjudicated
   sites** (A5/A7/A8/A9/A14) additionally pin their *exact* category set, so a
   silent re-flip of a repair conclusion also fails.

4. **Ratchet against new scatter.** The gate scans the maintained authority
   surface for the registered detection tokens (ignoring comments, docstrings, and
   import/``__all__`` re-export plumbing) and fails if any file carries authority
   logic without a census entry.

This slice makes **zero** C2 behavior change: the gate is descriptive/structural
only. Converging the pinned call sites onto the registry is deferred to a later,
domain-evidence-reviewed slice.
"""

from __future__ import annotations

import ast
import io
import json
import re
import tokenize
from pathlib import Path

import pytest

from python.tasking_contracts import agency_registry as registry
from tests.support.paths import REPO_ROOT, read_repo_text

CENSUS_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "architecture"
    / "fixtures"
    / "agency_authority_census_20260721.json"
)

# Maintained authority-decision surface scanned by the ratchet, as *directories*
# scanned recursively so a new authority-bearing file inside the owned surface
# cannot hide outside a narrower file-level root (I47 repair: close the
# new-file-outside-roots blind spot). The runtime/observation face
# (``python/rl/runtime/**``) and the policy-network face
# (``python/rl/policy_algo/**``) are deliberately out of scope; their authority
# sites are cross-referenced in the census document, not gated here.
SCAN_ROOTS: tuple[str, ...] = (
    "python/tasking_contracts",
    "python/rl/tasking",
    "python/rl/profile",
    "gym_envs/scenario_loader",
    "gym_envs/universal_env_parts",
)

# The registry module is the vocabulary *owner* (and this test + fixture are the
# gate); they name the tokens definitionally and must not be scanned as scatter.
EXCLUDED_FILES: frozenset[str] = frozenset(
    {"python/tasking_contracts/agency_registry.py"}
)

# Compiled authorities the registry vocabulary mirrors.
CORE_TASKING_ENUMS_HEADER = "src/components/tasking/common/core_tasking_enums.h"
NAVAL_TASKING_ENUMS_HEADER = "src/components/domains/naval/tasking/naval_tasking_enums.h"
POLICY_CONTRACTS_HEADER = "src/runtime/contracts/policy_contracts.h"

# Single source of the detection vocabulary: the registry's token->categories map.
AUTHORITY_TOKENS: tuple[str, ...] = tuple(sorted(registry.AUTHORITY_TOKEN_CATEGORIES))

_REQUIRED_ENTRY_FIELDS = (
    "file",
    "tokens",
    "token_counts",
    "categories",
    "form",
    "semantic",
    "owner",
    "note",
)

# Key re-adjudicated sites (I47 repair round 2): sites whose classification the
# review specifically re-decided. Their adjudicated category set is pinned *exactly*
# here (not merely grounded + covering), so a silent re-flip -- deleting A5's
# arbitration, re-adding A8's arbitration, moving A7/A9 off gating, or reverting A14
# to arbitration -- fails the gate. Ordinary sites keep the candidate-set model
# (grounded + cover) to avoid over-rigidity; only these pinned sites are frozen.
PINNED_SITE_CATEGORIES: dict[str, frozenset[str]] = {
    "python/rl/profile/ground_profile.py": frozenset(  # A5
        {"arbitration", "delegation", "role", "scope"}
    ),
    "gym_envs/scenario_loader/core.py": frozenset({"gating"}),  # A7
    "gym_envs/scenario_loader/runtime_state.py": frozenset(  # A8
        {"delegation", "doctrine", "role"}
    ),
    "gym_envs/scenario_loader/behavior_runtime/command_chain.py": frozenset(  # A9
        {"gating"}
    ),
    "gym_envs/scenario_loader/mission_observation.py": frozenset(  # A14
        {"delegation", "doctrine", "gating"}
    ),
}


# --------------------------------------------------------------------------- #
# Scanner: code/prose split + token->count fingerprint
# --------------------------------------------------------------------------- #
def _split_code_and_prose(source: str) -> tuple[str, str]:
    """Split Python source into ``(code_text, prose_text)``.

    ``code_text`` is the executable code with comments, docstrings, import
    statements, and ``__all__`` assignments removed (so an innocent docstring
    mention or a pure re-export is not counted as an authority site).
    ``prose_text`` is the docstrings + comments (where folklore conventions live).
    """
    lines = source.split("\n")
    prose_chunks: list[str] = []

    # 1) Comments -> prose; blank them out of the code lines (tokenize is precise
    #    about string vs comment, so a '#' inside a string is not a comment).
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                (srow, scol), (erow, ecol) = tok.start, tok.end
                prose_chunks.append(tok.string)
                if srow == erow and 1 <= srow <= len(lines):
                    line = lines[srow - 1]
                    lines[srow - 1] = line[:scol] + (" " * max(0, ecol - scol)) + line[ecol:]
    except (tokenize.TokenError, IndentationError):
        pass

    # 2) Docstrings -> prose; import / __all__ -> dropped (re-export plumbing).
    doc_lines: set[int] = set()
    drop_lines: set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return "\n".join(lines), "\n".join(prose_chunks)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None) or []
            if body:
                first = body[0]
                if (
                    isinstance(first, ast.Expr)
                    and isinstance(getattr(first, "value", None), ast.Constant)
                    and isinstance(first.value.value, str)
                ):
                    start = first.lineno
                    end = getattr(first, "end_lineno", start) or start
                    doc_lines.update(range(start, end + 1))
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start = node.lineno
            end = getattr(node, "end_lineno", start) or start
            drop_lines.update(range(start, end + 1))
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            start = node.lineno
            end = getattr(node, "end_lineno", start) or start
            drop_lines.update(range(start, end + 1))

    code_out: list[str] = []
    for idx, line in enumerate(lines, start=1):
        if idx in doc_lines:
            prose_chunks.append(line)
            continue
        if idx in drop_lines:
            continue
        code_out.append(line)
    return "\n".join(code_out), "\n".join(prose_chunks)


def _count_token_occurrences(haystack: str, token: str) -> int:
    r"""Count whole-word (``\bTOKEN\b``) occurrences of ``token``.

    I47 repair P1-2: a plain ``str.count`` double-counts a token that is a
    substring of a longer identifier (``commander_id`` inside ``ground_commander_id``,
    ``command_relationship`` inside ``_command_relationship_default``), which both
    inflated fingerprints and blocked tokenizing the synonym family. Word-boundary
    matching counts only standalone occurrences, so a synonym token is detectable
    without colliding with its compounds. Every registered token begins and ends
    with a word character (identifiers and the prose folklore phrase), so ``\b`` is
    well-defined for all of them.
    """
    return len(re.findall(r"\b" + re.escape(token) + r"\b", haystack))


def _iter_scan_files(repo_root: Path, scan_roots: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for root in scan_roots:
        target = repo_root / root
        if target.is_file():
            candidates = [target]
        elif target.is_dir():
            candidates = sorted(target.rglob("*.py"))
        else:
            continue
        for path in candidates:
            if any(part.startswith("__pycache__") or part == "_generated" for part in path.parts):
                continue
            if path in seen:
                continue
            seen.add(path)
            files.append(path)
    return files


def scan_authority_surface(
    repo_root: Path = REPO_ROOT,
    scan_roots: tuple[str, ...] = SCAN_ROOTS,
    *,
    tokens: tuple[str, ...] = AUTHORITY_TOKENS,
    surfaces: dict[str, str] | None = None,
    excluded: frozenset[str] = EXCLUDED_FILES,
) -> dict[str, dict[str, int]]:
    """Map every scanned file carrying >=1 authority token to its token->count map.

    ``code``-surface tokens are counted in the executable code only; ``prose``
    surface tokens (folklore phrases) are counted in the docstrings + comments.
    """
    resolved_surfaces = dict(registry.AUTHORITY_TOKEN_SURFACE) if surfaces is None else surfaces
    result: dict[str, dict[str, int]] = {}
    for path in _iter_scan_files(repo_root, scan_roots):
        rel = path.relative_to(repo_root).as_posix()
        if rel in excluded:
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        code_text, prose_text = _split_code_and_prose(source)
        counts: dict[str, int] = {}
        for token in tokens:
            surface = resolved_surfaces.get(token, registry.SURFACE_CODE)
            haystack = prose_text if surface == registry.SURFACE_PROSE else code_text
            occurrences = _count_token_occurrences(haystack, token)
            if occurrences:
                counts[token] = occurrences
        if counts:
            result[rel] = counts
    return result


# --------------------------------------------------------------------------- #
# Compiled-header enum/scope extraction (authority-comparison)
# --------------------------------------------------------------------------- #
def _strip_cpp_comments(text: str) -> str:
    r"""Strip C++ ``//`` and ``/* */`` comments, leaving string/char literals intact.

    Quote-aware (I47 repair P1-1): comment markers that appear *inside* a string
    (``"..."``) or char (``'...'``) literal are preserved, because the compiled
    action-interface authority scopes are string literals
    (``kAgentAuthorityScope* = "..."``) and a naive strip would corrupt a literal
    containing ``//`` or ``/*``. Stripping comments from the *whole* header before
    any enum/scope regex runs fixes two extractor deceptions the previous
    strip-after-match approach had: (1) a commented-out ("ghost") member left in a
    ``//`` or ``/* */`` comment is no longer resurrected into the mirror, and (2) a
    ``}`` inside a block comment can no longer truncate the enum body (the old
    non-greedy ``{(.*?)}`` stopped at the first brace, in-comment or not).

    Line-splicing preprocessing (I47 repair round 3): a C++ ``//`` line comment
    continues onto the next physical line when that line ends with a backslash,
    because translation phase 2 (backslash-newline splicing) runs *before* comment
    recognition. The prior state machine returned to ``code`` at the physical
    newline, so a member parked on the continuation line of a ``// ghost \`` comment
    (or of a commented-out scope declaration) was resurrected as a real member. We
    therefore splice ``\<newline>`` out of the whole text first
    (``re.sub(r"\\\r?\n", "", text)``), mirroring the compiler exactly. Trade-off vs.
    special-casing the continuation only inside the ``line`` state: a single
    preprocessing pass matches phase 2 for *every* lexical state, so it also makes
    the ``block``/``string``/``char`` states line-continuation consistent for free,
    instead of a per-state patch that would leave the other states inconsistent.
    Splicing is correct for string literals too -- C++ splices ``\<newline>`` inside
    a string the same way, so a spliced scope literal matches what the compiler sees.
    A header with no line continuation (all three real headers) is unaffected, so
    real extraction is byte-identical. Physical newlines are otherwise preserved; a
    block comment collapses to one space so tokens do not fuse.
    """
    text = re.sub(r"\\\r?\n", "", text)
    out: list[str] = []
    i = 0
    n = len(text)
    state = "code"  # code | line | block | string | char
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if state == "code":
            if ch == "/" and nxt == "/":
                state = "line"
                i += 2
            elif ch == "/" and nxt == "*":
                state = "block"
                out.append(" ")
                i += 2
            elif ch == '"':
                state = "string"
                out.append(ch)
                i += 1
            elif ch == "'":
                state = "char"
                out.append(ch)
                i += 1
            else:
                out.append(ch)
                i += 1
        elif state == "line":
            if ch == "\n":
                state = "code"
                out.append(ch)
            i += 1
        elif state == "block":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 2
            else:
                if ch == "\n":
                    out.append(ch)
                i += 1
        elif state == "string":
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
            elif ch == '"':
                state = "code"
                i += 1
            else:
                i += 1
        else:  # char literal
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
            elif ch == "'":
                state = "code"
                i += 1
            else:
                i += 1
    return "".join(out)


def _extract_enum_members(header_text: str, enum_name: str) -> tuple[str, ...]:
    """Extract the member names of ``enum class <enum_name> : <type> { ... }``.

    Comments are stripped (quote-aware) from the whole header first, so the enum
    body is delimited by its *real* closing brace and carries no ghost members.
    """
    clean = _strip_cpp_comments(header_text)
    pattern = re.compile(
        r"enum\s+class\s+" + re.escape(enum_name) + r"\s*:\s*\w+\s*\{([^}]*)\}",
    )
    match = pattern.search(clean)
    assert match is not None, f"enum class {enum_name} not found in header"
    members: list[str] = []
    for chunk in match.group(1).split(","):
        name = chunk.strip().split("=", 1)[0].strip()
        if name:
            members.append(name)
    return tuple(members)


def _extract_agent_authority_scopes(header_text: str) -> tuple[str, ...]:
    """Extract the ``kAgentAuthorityScope*`` string-literal values, in source order.

    Comments are stripped (quote-aware) first, so a commented-out scope declaration
    is not extracted while a real string-literal scope value survives intact.
    """
    clean = _strip_cpp_comments(header_text)
    return tuple(
        match.group(1)
        for match in re.finditer(r'kAgentAuthorityScope\w+\s*=\s*"([^"]+)"', clean)
    )


# --------------------------------------------------------------------------- #
# Census loading
# --------------------------------------------------------------------------- #
def _load_census() -> dict:
    return json.loads(CENSUS_FIXTURE.read_text(encoding="utf-8"))


def _census_by_file() -> dict[str, dict]:
    payload = _load_census()
    by_file: dict[str, dict] = {}
    for entry in payload["entries"]:
        rel = entry["file"]
        assert rel not in by_file, f"duplicate census entry for {rel}"
        by_file[rel] = entry
    return by_file


# --------------------------------------------------------------------------- #
# Fixture well-formedness + registry consistency
# --------------------------------------------------------------------------- #
def test_census_fixture_entries_are_well_formed() -> None:
    payload = _load_census()
    assert payload.get("schema") == "agency_authority_census/v1"
    entries = payload["entries"]
    assert entries, "expected at least one census entry"

    for entry in entries:
        rel = entry.get("file", "<missing>")
        for key in _REQUIRED_ENTRY_FIELDS:
            assert key in entry, f"{rel}: missing census field {key!r}"
        assert str(entry["file"]).strip(), f"{rel}: blank file"
        assert str(entry["form"]).strip(), f"{rel}: blank form"
        assert str(entry["semantic"]).strip(), f"{rel}: blank semantic"
        assert str(entry["owner"]).strip(), f"{rel}: blank owner"

        tokens = entry["tokens"]
        assert tokens, f"{rel}: census entry must pin at least one token"
        assert tokens == sorted(tokens), f"{rel}: tokens must be sorted"
        unknown_tokens = [t for t in tokens if t not in registry.AUTHORITY_TOKEN_CATEGORIES]
        assert not unknown_tokens, f"{rel}: unknown detection token(s) {unknown_tokens}"

        token_counts = entry["token_counts"]
        assert sorted(token_counts) == tokens, (
            f"{rel}: token_counts keys {sorted(token_counts)} must match tokens {tokens}"
        )
        for token, count in token_counts.items():
            assert isinstance(count, int) and count >= 1, (
                f"{rel}: token {token!r} count must be a positive int, got {count!r}"
            )

        categories = entry["categories"]
        assert categories == sorted(categories), f"{rel}: categories must be sorted"
        unknown_categories = [c for c in categories if c not in registry.AUTHORITY_CATEGORIES]
        assert not unknown_categories, f"{rel}: unknown category(ies) {unknown_categories}"


def test_census_categories_are_grounded_and_cover_tokens() -> None:
    """Registry <-> census consistency (candidate-set model): each file's adjudicated
    categories are (a) *grounded* -- every category is a candidate of at least one
    pinned token -- and (b) *cover* every token -- each token contributes at least
    one of its candidate categories. This replaces the rigid token->fixed-category
    derivation with per-site adjudication that still cannot invent categories or
    silently ignore a token (I47 repair P1-2)."""
    for rel, entry in _census_by_file().items():
        declared = set(entry["categories"])
        tokens = tuple(entry["tokens"])
        candidate_union = set(registry.candidate_categories_for_tokens(tokens))

        ungrounded = sorted(declared - candidate_union)
        assert not ungrounded, (
            f"{rel}: categories {ungrounded} are not a candidate of any pinned token "
            f"{list(tokens)} (candidate union {sorted(candidate_union)})"
        )

        for token in tokens:
            token_candidates = registry.authority_categories_for_token(token)
            assert token_candidates & declared, (
                f"{rel}: token {token!r} (candidates {sorted(token_candidates)}) "
                f"contributes no declared category {sorted(declared)}"
            )


def test_registry_declares_a_nonempty_vocabulary_for_every_census_category() -> None:
    """Declared role/scope/delegation/arbitration/gating/doctrine sets cover the census."""
    present_categories: set[str] = set()
    for entry in _census_by_file().values():
        present_categories.update(entry["categories"])

    for category in present_categories:
        terms = registry.registered_terms_for_category(category)
        assert terms, f"census surfaces category {category!r} but the registry declares no terms"


def test_registry_agent_role_schema_and_doctrine_family_are_declared() -> None:
    # SCAL AgentRole five-part schema key order.
    assert registry.AGENT_ROLE_SCHEMA_FIELDS == (
        "role",
        "authority_scope",
        "information_state_source",
        "decision_model_ref",
        "action_interface",
    )
    # Every declared role carries the five-part schema, with action-interface
    # scope / kind slots drawn from the compiled vocabulary (or "unspecified").
    allowed_scopes = set(registry.ACTION_INTERFACE_SCOPES) | {registry.SCHEMA_UNSPECIFIED}
    allowed_kinds = set(registry.ACTION_INTERFACE_KINDS) | {registry.SCHEMA_UNSPECIFIED}
    for role_id, role in registry.AUTHORITY_ROLES.items():
        assert role.role_id == role_id
        assert len(role.schema_values()) == len(registry.AGENT_ROLE_SCHEMA_FIELDS)
        assert role.authority_scope in allowed_scopes, (
            f"{role_id}: authority_scope {role.authority_scope!r} not in {sorted(allowed_scopes)}"
        )
        assert role.action_interface in allowed_kinds, (
            f"{role_id}: action_interface {role.action_interface!r} not in {sorted(allowed_kinds)}"
        )
        assert role.decision_model_ref, f"{role_id}: decision_model_ref must be non-empty"

    # DoctrineFamily is a declared-only placeholder this slice (no mechanism).
    assert registry.DOCTRINE_FAMILY.name == "DoctrineFamily"
    assert registry.DOCTRINE_FAMILY.status == "vocabulary_placeholder"
    assert "roe" in registry.DOCTRINE_FAMILY.declared_components
    assert "authority_delegation" in registry.DOCTRINE_FAMILY.declared_components

    # Every detection token maps to known authority categories and a known surface.
    for token, categories in registry.AUTHORITY_TOKEN_CATEGORIES.items():
        assert categories, f"token {token!r} has no candidate categories"
        assert categories <= registry.AUTHORITY_CATEGORIES, f"token {token!r} -> unknown category"
        assert registry.token_surface(token) in {registry.SURFACE_CODE, registry.SURFACE_PROSE}


def test_registry_mirrors_compiled_enum_authorities() -> None:
    """Authority-comparison: the registry vocabulary must reproduce the compiled
    enum members / action-interface scopes exactly (parsed from the headers), so a
    later drift in either the header or the mirror fails the gate (I47 repair P1-1)."""
    core = read_repo_text(CORE_TASKING_ENUMS_HEADER)
    naval = read_repo_text(NAVAL_TASKING_ENUMS_HEADER)
    policy = read_repo_text(POLICY_CONTRACTS_HEADER)

    assert _extract_enum_members(core, "CommandRelationship") == registry.COMMAND_RELATIONSHIPS
    assert _extract_enum_members(core, "AuthorityScope") == registry.AUTHORITY_SCOPE_LEVELS
    assert _extract_enum_members(core, "CoordinationMode") == registry.COORDINATION_MODES
    assert _extract_enum_members(naval, "NavalWarfareRole") == registry.NAVAL_WARFARE_ROLES
    assert _extract_agent_authority_scopes(policy) == registry.ACTION_INTERFACE_SCOPES


def test_enum_extractor_detects_registry_drift() -> None:
    """Negative self-test for the authority-comparison extraction method: the
    extractor recovers members (stripping ``= value`` and comments) and a mirror
    that drops a member is detected as a mismatch."""
    header = (
        "enum class Sample : int {\n"
        "    Alpha = 0,\n"
        "    Beta = 1,  // trailing comment\n"
        "    Gamma = 2,\n"
        "};\n"
    )
    assert _extract_enum_members(header, "Sample") == ("Alpha", "Beta", "Gamma")
    assert _extract_enum_members(header, "Sample") != ("Alpha", "Beta")  # dropped member -> drift
    scope_header = 'inline constexpr std::string_view kAgentAuthorityScopeFoo = "foo";\n'
    assert _extract_agent_authority_scopes(scope_header) == ("foo",)


def test_enum_extractor_ignores_commented_ghost_members() -> None:
    """Negative self-test (I47 repair P1-1): a commented-out ("ghost") member left
    in a ``//`` line comment or a ``/* */`` block comment must NOT be resurrected
    into the extracted mirror. The previous strip-after-match extractor could be
    deceived; comments are now stripped (quote-aware) from the whole header first."""
    header = (
        "enum class Sample : int {\n"
        "    Alpha = 0,\n"
        "    // Removed = 1,  <- line-comment ghost\n"
        "    /* Retired = 2, <- block-comment ghost */\n"
        "    Beta = 3,\n"
        "};\n"
    )
    members = _extract_enum_members(header, "Sample")
    assert members == ("Alpha", "Beta"), members
    assert "Removed" not in members and "Retired" not in members
    # A commented-out scope declaration must not be extracted either.
    scope_header = (
        '// inline constexpr std::string_view kAgentAuthorityScopeGhost = "ghost";\n'
        '/* kAgentAuthorityScopeStale = "stale"; */\n'
        'inline constexpr std::string_view kAgentAuthorityScopeReal = "real";\n'
    )
    assert _extract_agent_authority_scopes(scope_header) == ("real",)


def test_enum_extractor_survives_brace_in_block_comment() -> None:
    """Negative self-test (I47 repair P1-1): a ``}`` inside a block comment must NOT
    truncate the enum body. The previous non-greedy ``{(.*?)}`` regex stopped at the
    first brace -- in a comment or not -- silently dropping every member after it."""
    header = (
        "enum class Sample : int {\n"
        "    Alpha = 0,\n"
        "    Beta = 1,  /* a stray closing brace } must not truncate the body */\n"
        "    Gamma = 2,\n"
        "};\n"
    )
    members = _extract_enum_members(header, "Sample")
    assert members == ("Alpha", "Beta", "Gamma"), members


def test_enum_extractor_ignores_line_continuation_comment_ghost() -> None:
    r"""Negative self-test (I47 repair round 3): a ``//`` line comment ending with a
    backslash continues onto the next physical line -- C++ translation phase 2 splices
    ``\<newline>`` before comment recognition -- so a member parked on the continuation
    line must NOT be resurrected. The prior state machine returned to ``code`` at the
    physical newline and wrongly extracted the ghost (``Alpha, Ghost, Beta``)."""
    header = (
        "enum class Sample : int {\n"
        "    Alpha = 0,\n"
        "    // ghost \\\n"
        "    Ghost = 1,\n"
        "    Beta = 2,\n"
        "};\n"
    )
    members = _extract_enum_members(header, "Sample")
    assert members == ("Alpha", "Beta"), members
    assert "Ghost" not in members
    # The same splicing hides a scope declaration parked on a comment continuation.
    scope_header = (
        "// leading comment \\\n"
        'inline constexpr std::string_view kAgentAuthorityScopeGhost = "ghost";\n'
        'inline constexpr std::string_view kAgentAuthorityScopeReal = "real";\n'
    )
    assert _extract_agent_authority_scopes(scope_header) == ("real",)


def test_comment_stripper_preserves_string_literal_comment_markers() -> None:
    """The C++ comment stripper is quote-aware (I47 repair P1-1): ``//`` and ``/*``
    that appear inside a string literal are preserved, so a string-literal authority
    scope survives stripping intact (the compiled scopes are string literals)."""
    text = 'inline constexpr std::string_view kAgentAuthorityScopeUrlish = "a//b/*c*/d";\n'
    assert _extract_agent_authority_scopes(text) == ("a//b/*c*/d",)
    # And a real comment after the literal is still removed.
    text2 = (
        'inline constexpr std::string_view kAgentAuthorityScopeReal = "real";  // note\n'
        '// inline constexpr std::string_view kAgentAuthorityScopeGhost = "ghost";\n'
    )
    assert _extract_agent_authority_scopes(text2) == ("real",)


# --------------------------------------------------------------------------- #
# Fingerprint pin + ratchet
# --------------------------------------------------------------------------- #
def test_scan_roots_match_census_declared_scan_roots() -> None:
    payload = _load_census()
    assert tuple(payload["scan_roots"]) == SCAN_ROOTS


def test_no_unregistered_authority_scatter_beyond_the_census_ratchet() -> None:
    """Ratchet: every file carrying authority logic is pinned in the census, and
    every census file still reproduces its exact token->count fingerprint."""
    scanned = scan_authority_surface()
    census = _census_by_file()

    new_files = sorted(set(scanned) - set(census))
    assert not new_files, (
        "New authority-check scatter site(s) not registered in the census "
        f"({CENSUS_FIXTURE.relative_to(REPO_ROOT).as_posix()}). Either route the "
        "authority decision through python/tasking_contracts/agency_registry.py, or "
        "add an attributed census entry pinning the site: "
        + "; ".join(f"{rel} {scanned[rel]}" for rel in new_files)
    )

    stale_files = sorted(set(census) - set(scanned))
    assert not stale_files, (
        "Census entries no longer reproduced by the scan (the authority logic was "
        f"removed or the file moved) -- shrink the census: {stale_files}"
    )

    drifted: list[str] = []
    for rel, entry in census.items():
        want = {str(token): int(count) for token, count in entry["token_counts"].items()}
        found = scanned.get(rel, {})
        if found != want:
            drifted.append(f"{rel}: census={want} scanned={found}")
    assert not drifted, (
        "Census token->count fingerprint drifted (an authority token was added to or "
        "removed from a pinned file, including a repeated occurrence); update the "
        "census entry to match: " + "; ".join(drifted)
    )


# --------------------------------------------------------------------------- #
# Negative self-tests: the ratchet + scanner bite rather than pass vacuously
# --------------------------------------------------------------------------- #
def test_gate_flags_an_injected_unregistered_scatter(tmp_path: Path) -> None:
    """Negative self-test (no real source touched): a synthetic file carrying an
    authority token in a fake tree must be reported as an unregistered scatter by
    the same scan the real gate runs."""
    fake_repo = tmp_path / "fake_repo"
    fake_root = fake_repo / "python" / "rl" / "tasking"
    fake_root.mkdir(parents=True)
    offender = fake_root / "sneaky_authority.py"
    offender.write_text(
        "def decide(cmd):\n"
        "    return bool(cmd.get('authorization_to_fire', False))\n",
        encoding="utf-8",
    )

    scanned = scan_authority_surface(
        repo_root=fake_repo,
        scan_roots=("python/rl/tasking",),
    )
    assert scanned == {"python/rl/tasking/sneaky_authority.py": {"authorization_to_fire": 1}}, scanned

    census_files: set[str] = set()
    with pytest.raises(AssertionError):
        new_files = sorted(set(scanned) - census_files)
        assert not new_files, "expected the injected scatter to be flagged as unregistered"


def test_scanner_counts_repeated_tokens_in_the_same_file(tmp_path: Path) -> None:
    """Blind spot 1 (I47): a *second* occurrence of an already-present token in the
    same file changes the count and therefore drifts the fingerprint."""
    fake_repo = tmp_path / "repo"
    fake_root = fake_repo / "python" / "rl" / "tasking"
    fake_root.mkdir(parents=True)
    offender = fake_root / "double_fire.py"
    offender.write_text(
        "def a(cmd):\n"
        "    return bool(cmd.get('authorization_to_fire', False))\n"
        "def b(cmd):\n"
        "    return bool(cmd.get('authorization_to_fire', True))\n",
        encoding="utf-8",
    )
    scanned = scan_authority_surface(repo_root=fake_repo, scan_roots=("python/rl/tasking",))
    assert scanned == {"python/rl/tasking/double_fire.py": {"authorization_to_fire": 2}}
    # A fingerprint pinned at the single-occurrence count must drift-fail.
    assert scanned["python/rl/tasking/double_fire.py"] != {"authorization_to_fire": 1}


def test_scanner_ignores_docstring_and_comment_mentions(tmp_path: Path) -> None:
    """Blind spot 4 (I47): an innocent docstring/comment mention of a code token is
    not a false positive (comments + docstrings are stripped from the code surface)."""
    fake_repo = tmp_path / "repo"
    fake_root = fake_repo / "python" / "rl" / "tasking"
    fake_root.mkdir(parents=True)
    innocent = fake_root / "innocent.py"
    innocent.write_text(
        '"""This module mentions authorization_to_fire and roe_state in prose only."""\n'
        "\n"
        "def f():\n"
        "    # authorization_to_fire is discussed here but never referenced in code\n"
        "    return 0\n",
        encoding="utf-8",
    )
    scanned = scan_authority_surface(repo_root=fake_repo, scan_roots=("python/rl/tasking",))
    assert scanned == {}


def test_scanner_ignores_reexport_import_plumbing(tmp_path: Path) -> None:
    """Blind spot 5 (I47): pure re-export plumbing (import + ``__all__``) is not an
    authority site -- unifying the standard so a re-export like
    ``behavior_runtime/__init__.py`` is treated exactly like ``ground_adapter.py``."""
    fake_repo = tmp_path / "repo"
    fake_root = fake_repo / "gym_envs" / "scenario_loader" / "behavior_runtime"
    fake_root.mkdir(parents=True)
    reexport = fake_root / "__init__.py"
    reexport.write_text(
        "from .command_chain import hierarchical_command_chain_active\n"
        "\n"
        '__all__ = ["hierarchical_command_chain_active"]\n',
        encoding="utf-8",
    )
    scanned = scan_authority_surface(repo_root=fake_repo, scan_roots=("gym_envs/scenario_loader",))
    assert scanned == {}


def test_scanner_matches_prose_folklore_only_in_docstrings(tmp_path: Path) -> None:
    """Prose-surface folklore (e.g. the scripted-C2 authorship boundary) is matched
    in a docstring -- confirming the prose surface still catches deliberate folklore
    while the code surface ignores innocent mentions."""
    fake_repo = tmp_path / "repo"
    fake_root = fake_repo / "python" / "rl" / "tasking"
    fake_root.mkdir(parents=True)
    folklore = fake_root / "c2.py"
    folklore.write_text(
        "class C2:\n"
        '    """The C2 layer is not allowed to directly author low-level mission commands."""\n'
        "    value = 1\n",
        encoding="utf-8",
    )
    scanned = scan_authority_surface(repo_root=fake_repo, scan_roots=("python/rl/tasking",))
    assert scanned == {"python/rl/tasking/c2.py": {"allowed to directly author": 1}}


def test_scanner_detects_synonym_only_file(tmp_path: Path) -> None:
    """Negative self-test (I47 repair P1-2): a file that carries authority logic
    ONLY under a synonym spelling (bare ``commander_id`` / snake_case
    ``command_relationship``) is now detected. The previous scanner tokenized
    neither, so such a file scanned empty and slipped the ratchet entirely; the
    first round only *documented* the gap as a coverage boundary, which the review
    ruled did not resolve the P1. Detection is non-empty and, absent a census
    entry, the ratchet reports the site as unregistered scatter."""
    fake_repo = tmp_path / "repo"
    fake_root = fake_repo / "python" / "rl" / "tasking"
    fake_root.mkdir(parents=True)
    offender = fake_root / "synonym_only.py"
    offender.write_text(
        "def resolve(spec):\n"
        "    return spec.get('commander_id'), spec.get('command_relationship')\n",
        encoding="utf-8",
    )
    scanned = scan_authority_surface(repo_root=fake_repo, scan_roots=("python/rl/tasking",))
    assert scanned == {
        "python/rl/tasking/synonym_only.py": {"command_relationship": 1, "commander_id": 1}
    }, scanned
    # Absent a census entry, the ratchet flags the synonym-only site as unregistered.
    census_files: set[str] = set()
    with pytest.raises(AssertionError):
        new_files = sorted(set(scanned) - census_files)
        assert not new_files, "expected the synonym-only site to be flagged as unregistered"


def test_scanner_word_boundary_excludes_substring(tmp_path: Path) -> None:
    """Negative self-test (I47 repair P1-2): word-boundary matching means a synonym
    token never double-counts inside a longer identifier. A file using only
    ``ground_commander_id`` yields the ground_commander_id count but NOT a spurious
    ``commander_id`` count -- ``\\bcommander_id\\b`` cannot match inside
    ``ground_commander_id``."""
    fake_repo = tmp_path / "repo"
    fake_root = fake_repo / "python" / "rl" / "tasking"
    fake_root.mkdir(parents=True)
    compound = fake_root / "compound.py"
    compound.write_text(
        "def f(spec):\n"
        "    return spec.get('ground_commander_id')\n",
        encoding="utf-8",
    )
    scanned = scan_authority_surface(repo_root=fake_repo, scan_roots=("python/rl/tasking",))
    assert scanned == {"python/rl/tasking/compound.py": {"ground_commander_id": 1}}, scanned
    assert "commander_id" not in scanned["python/rl/tasking/compound.py"]


# --------------------------------------------------------------------------- #
# Key re-adjudicated sites: exact-category pins (I47 repair round 2, NB-4)
# --------------------------------------------------------------------------- #
def test_key_readjudicated_sites_pin_exact_categories() -> None:
    """NB-4 (I47 repair round 2): the key re-adjudicated sites pin their EXACT
    category set, not merely a grounded+covering subset, so a silent re-flip of a
    repair conclusion fails the gate. Each pinned set is still internally consistent
    (grounded in + covering its tokens' candidate categories)."""
    census = _census_by_file()
    for rel, expected in PINNED_SITE_CATEGORIES.items():
        assert rel in census, f"pinned key site {rel} missing from census"
        actual = frozenset(census[rel]["categories"])
        assert actual == expected, (
            f"{rel}: adjudicated categories {sorted(actual)} must EQUAL the pinned "
            f"repair-round-2 adjudication {sorted(expected)} (this site's classification "
            "was specifically re-decided; a silent re-flip is not allowed)"
        )
        tokens = tuple(census[rel]["tokens"])
        candidate_union = set(registry.candidate_categories_for_tokens(tokens))
        assert expected <= candidate_union, (
            f"{rel}: pinned categories {sorted(expected)} not grounded in the token "
            f"candidate union {sorted(candidate_union)}"
        )
        for token in tokens:
            assert registry.authority_categories_for_token(token) & expected, (
                f"{rel}: token {token!r} contributes no pinned category"
            )


def test_pinned_key_site_check_bites_on_reflip() -> None:
    """Negative self-test for NB-4: the exact-equality pin is sensitive -- deleting
    A5's arbitration, re-adding A8's arbitration, reverting A14 to arbitration, or
    moving A7 off gating each breaks the pin (the check is not vacuous)."""
    census = _census_by_file()

    a5 = frozenset(census["python/rl/profile/ground_profile.py"]["categories"])
    assert a5 == PINNED_SITE_CATEGORIES["python/rl/profile/ground_profile.py"]
    assert (a5 - {"arbitration"}) != PINNED_SITE_CATEGORIES["python/rl/profile/ground_profile.py"]

    a8 = frozenset(census["gym_envs/scenario_loader/runtime_state.py"]["categories"])
    assert a8 == PINNED_SITE_CATEGORIES["gym_envs/scenario_loader/runtime_state.py"]
    assert (a8 | {"arbitration"}) != PINNED_SITE_CATEGORIES["gym_envs/scenario_loader/runtime_state.py"]

    a14 = frozenset(census["gym_envs/scenario_loader/mission_observation.py"]["categories"])
    assert a14 == PINNED_SITE_CATEGORIES["gym_envs/scenario_loader/mission_observation.py"]
    assert (a14 - {"gating"}) != PINNED_SITE_CATEGORIES["gym_envs/scenario_loader/mission_observation.py"]
    # Reverting A14 to the round-1 arbitration misclassification also breaks the pin.
    assert frozenset({"arbitration", "delegation", "doctrine"}) != PINNED_SITE_CATEGORIES[
        "gym_envs/scenario_loader/mission_observation.py"
    ]

    a7 = frozenset(census["gym_envs/scenario_loader/core.py"]["categories"])
    assert a7 == PINNED_SITE_CATEGORIES["gym_envs/scenario_loader/core.py"]
    assert (a7 | {"arbitration"}) != PINNED_SITE_CATEGORIES["gym_envs/scenario_loader/core.py"]
