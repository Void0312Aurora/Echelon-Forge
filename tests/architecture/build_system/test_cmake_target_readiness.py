from __future__ import annotations

import re
from pathlib import Path

from tests.architecture.helpers import REPO_ROOT


CMAKE = REPO_ROOT / "CMakeLists.txt"


def _cmake_source() -> str:
  return CMAKE.read_text(encoding="utf-8")


def _option_default(source: str, option_name: str) -> str:
  match = re.search(
    rf"option\(\s*{re.escape(option_name)}\s+\"[^\"]*\"\s+(ON|OFF)\s*\)",
    source,
  )
  assert match is not None, f"missing CMake option: {option_name}"
  return match.group(1)


def _command_body(source: str, command: str, first_args: str) -> str:
  match = re.search(
    rf"{re.escape(command)}\s*\(\s*{re.escape(first_args)}(.*?)\n\)",
    source,
    re.DOTALL,
  )
  assert match is not None, f"missing CMake command: {command}({first_args}"
  return match.group(1)


def test_compiler_cache_is_explicit_opt_in_and_unsafe_sccache_is_blocked() -> None:
  source = _cmake_source()
  assert _option_default(source, "EF_ENABLE_COMPILER_CACHE") == "OFF"
  assert 'MSVC\n            AND CMAKE_GENERATOR MATCHES "Ninja"' in source
  assert 'EF_COMPILER_CACHE_NAME STREQUAL "sccache"' in source


def test_fetchcontent_pins_revalidate_by_default_and_old_cmake_fails_closed() -> None:
  source = _cmake_source()
  assert _option_default(source, "EF_FETCHCONTENT_REVALIDATE_PINS") == "ON"
  assert (
    "if (NOT EF_FETCHCONTENT_REVALIDATE_PINS AND CMAKE_VERSION VERSION_LESS 3.27)"
    in source
  )

  for dependency in ("flecs", "spdlog", "nanobind", "nlohmann_json", "doctest"):
    body = _command_body(source, "FetchContent_Declare", dependency)
    assert "${EF_FETCHCONTENT_PIN_MODE}" in body, (
      f"{dependency} bypasses the repository-wide pin revalidation mode"
    )
    assert "UPDATE_DISCONNECTED TRUE" not in body, (
      f"{dependency} hard-codes disconnected updates"
    )


# --- Robust CMake parsing for the content leaf-split gate (I46 slice 1) -------
# The layout-sensitive ``_command_body`` matcher above is kept for the simpler
# gates, but the content link-unit invariant needs to survive semantically
# neutral rewrites of CMakeLists.txt (comments, whitespace/newline reflow,
# alternate link scopes) while still catching real regressions.  These helpers
# parse the file into a ``set()`` variable table plus per-target
# ``add_library`` / ``target_sources`` / ``target_link_libraries`` calls, so the
# gate reasons over resolved tokens instead of raw text.

_LINK_SCOPES = {"PRIVATE", "PUBLIC", "INTERFACE"}
_LIBRARY_TYPES = {
  "STATIC",
  "SHARED",
  "MODULE",
  "OBJECT",
  "INTERFACE",
  "UNKNOWN",
  "ALIAS",
  "IMPORTED",
  "EXCLUDE_FROM_ALL",
  "GLOBAL",
}


def _strip_cmake_comments(text: str) -> str:
  """Drop CMake bracket comments (``#[[ ... ]]``) and ``#`` line comments.

  Bracket comments are removed first so a later ``#`` inside them is not
  mishandled; line comments are then stripped with double-quote awareness so a
  ``#`` inside a quoted argument survives.  Running this first is what makes a
  bare mention of ``ef_core`` or ``${EF_CONTENT_SOURCES}`` in a comment
  harmless to every matcher below."""
  text = re.sub(r"#\[(=*)\[.*?\]\1\]", "", text, flags=re.DOTALL)
  out: list[str] = []
  in_string = False
  i = 0
  n = len(text)
  while i < n:
    ch = text[i]
    if in_string:
      out.append(ch)
      if ch == "\\" and i + 1 < n:
        out.append(text[i + 1])
        i += 2
        continue
      if ch == '"':
        in_string = False
      i += 1
      continue
    if ch == '"':
      in_string = True
      out.append(ch)
      i += 1
      continue
    if ch == "#":
      while i < n and text[i] != "\n":
        i += 1
      continue
    out.append(ch)
    i += 1
  return "".join(out)


def _string_span_mask(text: str) -> list[bool]:
  """Mark every index inside a double-quoted string *or* a bracket argument.

  Two CMake lexical forms can carry a ``command(`` spelling that is plain text,
  not a real call, and must be hidden from ``_find_commands``; this returns the
  union of their spans:

  * **Double-quoted strings** -- e.g.
    ``message("target_link_libraries(ef_content INTERFACE ef_core)")`` -- use the
    backslash-aware quote state machine shared with ``_strip_cmake_comments``.
  * **Bracket arguments** ``[[ ... ]]`` / ``[=[ ... ]=]`` / ... -- e.g.
    ``message([[target_link_libraries(ef_content INTERFACE ef_core)]])`` -- are a
    distinct form in the same syntax family as the ``#[[ ... ]]`` bracket
    *comment*.  The comment (leading ``#``) is already removed by
    ``_strip_cmake_comments``; the bracket *argument* has no ``#`` and survives to
    command parsing, so it must be masked here.  A bracket argument has no escape
    semantics: its content runs verbatim until the matching close ``]=*]`` whose
    ``=`` count equals the opener's, so a plain ``]]`` inside a ``[==[`` span does
    not end it.

  Openers are recognised only outside a quoted string (a ``"`` suppresses ``[``),
  and quotes are inert inside a bracket argument, mirroring CMake's own lexer.

  Known boundary (intentionally *not* masked): the single quote ``'`` is not a
  string delimiter in CMake -- an unquoted ``'`` only raises a CMake developer
  warning -- so a ``command(`` written inside ``'...'`` stays visible.  That is
  not valid CMake string syntax, so masking it is neither needed nor correct."""
  mask = [False] * len(text)
  n = len(text)
  i = 0
  while i < n:
    ch = text[i]
    if ch == '"':
      # Double-quoted string: backslash-aware, ends at the next bare quote.
      mask[i] = True
      i += 1
      while i < n:
        mask[i] = True
        if text[i] == "\\" and i + 1 < n:
          mask[i + 1] = True
          i += 2
          continue
        closing = text[i] == '"'
        i += 1
        if closing:
          break
      continue
    if ch == "[":
      # Bracket argument ``[`` ``=``*k ``[`` ... ``]`` ``=``*k ``]`` (no escapes).
      j = i + 1
      while j < n and text[j] == "=":
        j += 1
      if j < n and text[j] == "[":
        close = "]" + "=" * (j - i - 1) + "]"
        end = text.find(close, j + 1)
        stop = end + len(close) if end != -1 else n
        for k in range(i, stop):
          mask[k] = True
        i = stop
        continue
    i += 1
  return mask


def _find_commands(text: str, command: str) -> list[str]:
  """Return the raw argument text of every ``command(...)`` invocation.

  Scans balanced, quote-aware parentheses so arbitrary internal whitespace and
  newlines are tolerated, and requires a whole-word command name so ``set``
  never matches ``set_target_properties`` or ``offset``.  The command *name*
  match must additionally start outside any double-quoted string, so a command
  spelled inside a quoted argument is not mistaken for a real call."""
  results: list[str] = []
  in_string_at = _string_span_mask(text)
  pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(command)}\s*\(", re.IGNORECASE)
  n = len(text)
  for match in pattern.finditer(text):
    if in_string_at[match.start()]:
      continue
    i = match.end()
    start = i
    depth = 1
    in_string = False
    while i < n and depth > 0:
      ch = text[i]
      if in_string:
        if ch == "\\":
          i += 2
          continue
        if ch == '"':
          in_string = False
        i += 1
        continue
      if ch == '"':
        in_string = True
      elif ch == "(":
        depth += 1
      elif ch == ")":
        depth -= 1
        if depth == 0:
          break
      i += 1
    results.append(text[start:i])
  return results


def _tokenize(body: str) -> list[str]:
  """Split a command body into CMake arguments (quoted or whitespace-split)."""
  tokens: list[str] = []
  i = 0
  n = len(body)
  while i < n:
    ch = body[i]
    if ch.isspace():
      i += 1
      continue
    if ch == '"':
      buf: list[str] = []
      i += 1
      while i < n:
        if body[i] == "\\" and i + 1 < n:
          buf.append(body[i + 1])
          i += 2
          continue
        if body[i] == '"':
          i += 1
          break
        buf.append(body[i])
        i += 1
      tokens.append("".join(buf))
      continue
    j = i
    while j < n and not body[j].isspace() and body[j] not in "()":
      j += 1
    tokens.append(body[i:j])
    i = j
  return tokens


def _as_var_ref(token: str) -> str | None:
  """Return ``NAME`` when ``token`` is exactly ``${NAME}``, else ``None``."""
  match = re.fullmatch(r"\$\{(\w+)\}", token)
  return match.group(1) if match else None


def _set_variable_map(text: str) -> dict[str, list[str]]:
  """Map every ``set(NAME ...)`` variable to its list of value tokens."""
  mapping: dict[str, list[str]] = {}
  for body in _find_commands(text, "set"):
    tokens = _tokenize(body)
    if tokens:
      mapping[tokens[0]] = tokens[1:]
  return mapping


def _add_library_targets(text: str) -> dict[str, tuple[str | None, list[str]]]:
  """Map every ``add_library`` target to ``(type, source_tokens)``."""
  targets: dict[str, tuple[str | None, list[str]]] = {}
  for body in _find_commands(text, "add_library"):
    tokens = _tokenize(body)
    if not tokens:
      continue
    rest = tokens[1:]
    lib_type: str | None = None
    if rest and rest[0].upper() in _LIBRARY_TYPES:
      lib_type = rest[0].upper()
      rest = rest[1:]
    targets[tokens[0]] = (lib_type, rest)
  return targets


def _scoped_call_args(text: str, command: str, target: str) -> list[list[str]]:
  """Args (minus scope keywords) of every ``command(target ...)`` call.

  Returns one list per matching call so callers can traverse *all* of a
  target's calls rather than only the first textual match."""
  calls: list[list[str]] = []
  for body in _find_commands(text, command):
    tokens = _tokenize(body)
    if not tokens or tokens[0] != target:
      continue
    calls.append([t for t in tokens[1:] if t.upper() not in _LINK_SCOPES])
  return calls


def _resolve_sources(
  set_map: dict[str, list[str]], roots: list[str]
) -> tuple[set[str], set[str]]:
  """Transitively expand ``${VAR}`` roots into (referenced vars, literal tokens)."""
  referenced: set[str] = set()
  literals: set[str] = set()
  seen: set[str] = set()
  stack = list(roots)
  while stack:
    token = stack.pop()
    name = _as_var_ref(token)
    if name is not None:
      referenced.add(name)
      if name not in seen:
        seen.add(name)
        stack.extend(set_map.get(name, []))
    else:
      literals.add(token)
  return referenced, literals


_SOURCE_ROOT_PREFIXES = (
  "${CMAKE_CURRENT_SOURCE_DIR}/",
  "${CMAKE_SOURCE_DIR}/",
  "${PROJECT_SOURCE_DIR}/",
)


def _normalize_source_path(token: str) -> str:
  """Reduce equivalent spellings of a source path to a bare repo-relative form.

  Strips a single known CMake source-root variable prefix
  (``${CMAKE_CURRENT_SOURCE_DIR}/`` and friends) and any leading ``./`` segments
  so ``./src/content/x.cpp`` and ``${CMAKE_CURRENT_SOURCE_DIR}/src/content/x.cpp``
  both resolve to ``src/content/x.cpp``.  This keeps a content path from dodging
  the leaf gate by changing how its root is written."""
  path = token
  for prefix in _SOURCE_ROOT_PREFIXES:
    if path.startswith(prefix):
      path = path[len(prefix):]
      break
  while path.startswith("./"):
    path = path[2:]
  return path


def _is_content_path(token: str) -> bool:
  """True when ``token`` addresses a file under ``src/content/`` in any
  equivalent spelling, matched by path *segment* so a sibling directory such as
  ``src/content_x/`` is never mis-flagged."""
  segments = _normalize_source_path(token).split("/")
  return any(
    segments[i] == "src" and segments[i + 1] == "content"
    for i in range(len(segments) - 1)
  )


def _content_leaf_split_violations(source: str) -> list[str]:
  """Return every way ``source`` breaks the T3 content link-unit invariant.

  An empty list means the gate is green.  Each check traverses *all* relevant
  calls (not just the first textual match), so equivalent rewrites cannot hide a
  regression:

  * (a) no content source -- neither the ``${EF_CONTENT_SOURCES}`` group nor any
    literal ``src/content/`` path (in any equivalent spelling: a ``./`` prefix or
    a known ``${CMAKE_*_SOURCE_DIR}/`` root prefix, matched by path segment) --
    is compiled into ``ef_core`` (via its ``add_library`` sources, any
    ``target_sources`` call, or any variable that transitively expands into them);
  * (b) no ``target_link_libraries(ef_content ...)`` call links ``ef_core``,
    under any scope keyword;
  * (c) an ``ef_content`` STATIC target exists and is built from the content
    source group only -- its ``add_library`` sources plus every later
    ``target_sources(ef_content ...)`` call must stay within
    ``${EF_CONTENT_SOURCES}`` with no literal ``src/`` path smuggled in;
  * (d) ``ef_core`` links ``ef_content`` (the one allowed direction)."""
  text = _strip_cmake_comments(source)
  set_map = _set_variable_map(text)
  libraries = _add_library_targets(text)
  violations: list[str] = []

  # (c) ef_content is a STATIC archive built from the content source group only.
  # Aggregate its add_library sources with every later target_sources(ef_content
  # ...) call so a stray source appended after the fact is still caught.
  content = libraries.get("ef_content")
  if content is None:
    violations.append("no add_library(ef_content ...) target found")
  else:
    content_type, add_library_sources = content
    content_sources = list(add_library_sources)
    for call in _scoped_call_args(text, "target_sources", "ef_content"):
      content_sources.extend(call)
    if content_type != "STATIC":
      violations.append(
        f"ef_content must be a STATIC archive (found type {content_type!r})"
      )
    if "${EF_CONTENT_SOURCES}" not in content_sources:
      violations.append(
        "add_library(ef_content) must build from the ${EF_CONTENT_SOURCES} group"
      )
    stray = [s for s in content_sources if _normalize_source_path(s).startswith("src/")]
    if stray:
      violations.append(
        "ef_content must consume the ${EF_CONTENT_SOURCES} group only, not "
        f"literal sources: {stray}"
      )

  content_group_literals = {
    token
    for token in set_map.get("EF_CONTENT_SOURCES", [])
    if _as_var_ref(token) is None
  }

  def _is_content_source(token: str) -> bool:
    return _is_content_path(token) or token in content_group_literals

  # (a) content must not be compiled into ef_core (variable or literal form).
  core = libraries.get("ef_core")
  core_roots: list[str] = list(core[1]) if core else []
  for call in _scoped_call_args(text, "target_sources", "ef_core"):
    core_roots.extend(call)
  referenced, literals = _resolve_sources(set_map, core_roots)
  if "EF_CONTENT_SOURCES" in referenced:
    violations.append(
      "ef_core compiles the ${EF_CONTENT_SOURCES} group; content must stay a "
      "separate archive"
    )
  content_in_core = sorted(token for token in literals if _is_content_source(token))
  if content_in_core:
    violations.append(f"ef_core compiles content sources directly: {content_in_core}")

  # (b) ef_content must never link ef_core -- traverse *every* call and scope.
  for libs in _scoped_call_args(text, "target_link_libraries", "ef_content"):
    if "ef_core" in libs:
      violations.append(
        "ef_content links ef_core: content must stay a leaf (back-edge / "
        "static-library cycle)"
      )
      break

  # (d) ef_core must link ef_content (the single allowed direction).
  core_links = [
    lib
    for call in _scoped_call_args(text, "target_link_libraries", "ef_core")
    for lib in call
  ]
  if "ef_content" not in core_links:
    violations.append("ef_core must link ef_content (forward dependency edge missing)")

  return violations


def test_core_source_groups_are_named_for_future_targets() -> None:
  source = _cmake_source()
  required_groups = [
    "EF_CORE_ENGINE_SOURCES",
    "EF_CORE_GEOMETRY_SOURCES",
    "EF_CORE_MISSION_RUNTIME_SOURCES",
    "EF_CORE_MISSION_EPISODE_SOURCES",
    "EF_CORE_MISSION_EPISODE_DETAIL_SOURCES",
    "EF_CORE_MISSION_SOURCES",
    "EF_RUNTIME_FACADE_SOURCES",
    "EF_MODEL_DEFAULT_SOURCES",
    "EF_CONTENT_SOURCES",
    "EF_CORE_SOURCES",
    "EF_PYTHON_BINDING_SOURCES",
    "EF_GPU_MAINTAINED_HELPER_SOURCES",
    "EF_GPU_EXPERIMENT_SOURCES",
  ]
  missing = [name for name in required_groups if f"set({name}" not in source]
  assert not missing, f"missing future target source groups: {missing}"


def test_core_target_uses_source_group_instead_of_flat_file_list() -> None:
  source = _cmake_source()
  body = _command_body(source, "add_library", "ef_core STATIC")
  assert "${EF_CORE_SOURCES}" in body
  assert "src/" not in body, (
    "add_library(ef_core) should consume grouped source variables only"
  )


def test_content_layer_is_its_own_static_link_unit_and_stays_a_leaf() -> None:
  """T3 physical link-unit split (I46 slice 1): content/ compiles into its own
  ``ef_content`` static archive that ``ef_core`` links one-way, and
  ``ef_content`` never links ``ef_core``.

  This is the CMake-level companion to the include-direction gate
  (``test_cpp_include_direction.py``): the include gate proves content's
  *source* never depends on engine/mission/facade, and this gate proves the
  *build* keeps content in a separate archive that does not pull the
  engine/mission/facade objects back in (linking ``ef_core`` would both invert
  the layer direction and create a static-library cycle).

  The invariant is evaluated by parsing CMakeLists.txt into variables and
  per-target calls (``_content_leaf_split_violations``) rather than by matching
  fixed text, so semantically neutral edits stay green while real regressions --
  including a literal ``src/content/`` path smuggled into ef_core, or a
  back-edge added under any link scope -- turn red.  The negative cases below
  pin that behaviour down against layout drift."""
  violations = _content_leaf_split_violations(_cmake_source())
  assert not violations, "content leaf-split regressed:\n  " + "\n  ".join(violations)


# A minimal but structurally faithful correct split, used as the baseline for
# the negative gate cases below.  It mirrors the real CMakeLists layering
# (grouped core sources -> ef_core; ${EF_CONTENT_SOURCES} -> ef_content;
# ef_core links ef_content one-way) so mutations exercise the same parser.
_GOLDEN_CONTENT_SPLIT = """\
set(EF_CORE_ENGINE_SOURCES
    src/core/engine/simulation_kernel.cpp
)

set(EF_CONTENT_SOURCES
    src/content/unit_definition_loader.cpp
)

set(EF_CORE_SOURCES
    ${EF_CORE_ENGINE_SOURCES}
)

add_library(ef_content STATIC
    ${EF_CONTENT_SOURCES}
)
target_include_directories(ef_content PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(ef_content PUBLIC
    spdlog::spdlog
    nlohmann_json::nlohmann_json
)

add_library(ef_core STATIC
    ${EF_CORE_SOURCES}
)
target_include_directories(ef_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(ef_core PUBLIC
    ef_content
    spdlog::spdlog
)
"""


def test_gate_baseline_golden_split_is_green() -> None:
  """Sanity anchor: the correct synthetic split must pass, so the red cases
  below prove the mutation was caught rather than a broken fixture."""
  assert _content_leaf_split_violations(_GOLDEN_CONTENT_SPLIT) == []


def test_gate_flags_content_group_readded_to_core() -> None:
  """Review scenario 1: ``${EF_CONTENT_SOURCES}`` folded back into the ef_core
  source group must turn the gate red (the one case the original gate caught)."""
  regressed = _GOLDEN_CONTENT_SPLIT.replace(
    "set(EF_CORE_SOURCES\n    ${EF_CORE_ENGINE_SOURCES}\n)",
    "set(EF_CORE_SOURCES\n    ${EF_CORE_ENGINE_SOURCES}\n    ${EF_CONTENT_SOURCES}\n)",
  )
  assert regressed != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  violations = _content_leaf_split_violations(regressed)
  assert any("${EF_CONTENT_SOURCES}" in v for v in violations), violations


def test_gate_flags_literal_content_path_smuggled_into_core() -> None:
  """Review scenario 2: a literal ``src/content/`` path added to an ef_core
  source group (bypassing the variable) must turn red.  This is the
  false-negative the original text-only gate missed."""
  regressed = _GOLDEN_CONTENT_SPLIT.replace(
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n)",
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n"
    "    src/content/unit_definition_loader.cpp\n)",
  )
  assert regressed != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  violations = _content_leaf_split_violations(regressed)
  assert any("content sources directly" in v for v in violations), violations


def test_gate_flags_content_backedge_under_any_scope() -> None:
  """Review scenario 3: a *second* ``target_link_libraries(ef_content ...)``
  call that links ef_core under PRIVATE must turn red.  This is the
  false-negative the original gate missed by inspecting only the first
  ``ef_content PUBLIC`` block."""
  regressed = _GOLDEN_CONTENT_SPLIT + "\ntarget_link_libraries(ef_content PRIVATE ef_core)\n"
  violations = _content_leaf_split_violations(regressed)
  assert any("back-edge" in v for v in violations), violations


def test_gate_tolerates_comments_reflow_and_bracket_comments() -> None:
  """Review scenario 4 (inverse): comment-only mentions and whitespace reflow
  must stay green.  A ``${EF_CONTENT_SOURCES}`` mention inside a comment in the
  ef_core group, an ``ef_core`` mention in an ef_content-link comment, a
  multi-line ``add_library`` reflow, and a trailing bracket comment are all
  semantically neutral and must not produce false positives."""
  rewritten = (
    _GOLDEN_CONTENT_SPLIT.replace(
      "set(EF_CORE_SOURCES\n    ${EF_CORE_ENGINE_SOURCES}\n)",
      "set(EF_CORE_SOURCES\n    ${EF_CORE_ENGINE_SOURCES}\n"
      "    # ${EF_CONTENT_SOURCES} stays in ef_content -- never compiled here\n)",
    )
    .replace(
      "add_library(ef_content STATIC\n    ${EF_CONTENT_SOURCES}\n)",
      "add_library(ef_content\n    STATIC\n    ${EF_CONTENT_SOURCES}\n)"
      "  #[[ content leaf archive ]]",
    )
    .replace(
      "target_link_libraries(ef_content PUBLIC\n    spdlog::spdlog\n"
      "    nlohmann_json::nlohmann_json\n)",
      "target_link_libraries(ef_content PUBLIC\n"
      "    # ef_content is a leaf: do NOT add ef_core here\n"
      "    spdlog::spdlog\n    nlohmann_json::nlohmann_json\n)",
    )
  )
  assert rewritten != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  assert _content_leaf_split_violations(rewritten) == []


def test_gate_ignores_backedge_written_only_inside_a_string() -> None:
  """Repair round P1: a back-edge spelled inside a quoted ``message(...)``
  argument is not a real command and must stay green.  Before the string-aware
  command scan, ``_find_commands`` matched the ``(`` inside the quotes and
  reported a phantom ``ef_content -> ef_core`` back-edge."""
  rewritten = _GOLDEN_CONTENT_SPLIT + (
    '\nmessage(STATUS "target_link_libraries(ef_content INTERFACE ef_core)")\n'
  )
  assert rewritten != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  assert _content_leaf_split_violations(rewritten) == []


def test_gate_rejects_forward_edge_written_only_inside_a_string() -> None:
  """Repair round P1: with the real ``ef_core -> ef_content`` link removed and
  the edge only *mentioned* inside a quoted string, assertion (d) must still
  fail.  Before the string-aware scan, the phantom
  ``target_link_libraries(ef_core ...)`` inside the string satisfied the
  forward-edge check and hid the missing dependency."""
  regressed = _GOLDEN_CONTENT_SPLIT.replace(
    "target_link_libraries(ef_core PUBLIC\n    ef_content\n    spdlog::spdlog\n)",
    "target_link_libraries(ef_core PUBLIC\n    spdlog::spdlog\n)\n"
    'message(STATUS "target_link_libraries(ef_core PUBLIC ef_content)")',
  )
  assert regressed != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  violations = _content_leaf_split_violations(regressed)
  assert any("forward dependency edge missing" in v for v in violations), violations


def test_gate_ignores_backedge_written_only_inside_a_bracket_argument() -> None:
  """Repair round P4: a back-edge spelled inside a CMake *bracket argument*
  (``message([[ ... ]])``) is plain text -- ``cmake -P`` prints it and runs no
  command -- so the gate must stay green.  Bracket arguments are a distinct
  lexical form from double-quoted strings and from the ``#[[ ... ]]`` bracket
  *comment* that ``_strip_cmake_comments`` removes (the argument carries no
  leading ``#`` and survives to command parsing).  Before the bracket-aware span
  mask, ``_find_commands`` harvested the ``(`` inside ``[[ ]]`` and reported a
  phantom ``ef_content -> ef_core`` back-edge."""
  rewritten = _GOLDEN_CONTENT_SPLIT + (
    "\nmessage([[target_link_libraries(ef_content INTERFACE ef_core)]])\n"
  )
  assert rewritten != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  assert _content_leaf_split_violations(rewritten) == []


def test_gate_rejects_forward_edge_written_only_inside_a_bracket_argument() -> None:
  """Repair round P4: with the real ``ef_core -> ef_content`` link removed and
  the edge only *mentioned* inside an equals-form bracket argument
  (``message([=[ ... ]=])``), assertion (d) must still fail.  The close bracket
  ``]=]`` must carry the same ``=`` count as the opener to bound the masked span,
  so the phantom ``target_link_libraries(ef_core ...)`` inside it cannot satisfy
  the forward-edge check and hide the missing dependency."""
  regressed = _GOLDEN_CONTENT_SPLIT.replace(
    "target_link_libraries(ef_core PUBLIC\n    ef_content\n    spdlog::spdlog\n)",
    "target_link_libraries(ef_core PUBLIC\n    spdlog::spdlog\n)\n"
    "message([=[target_link_libraries(ef_core PUBLIC ef_content)]=])",
  )
  assert regressed != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  violations = _content_leaf_split_violations(regressed)
  assert any("forward dependency edge missing" in v for v in violations), violations


def test_gate_flags_dot_slash_content_path_smuggled_into_core() -> None:
  """Repair round P2: a ``./src/content/`` spelling folded into an ef_core
  source group must turn red -- equivalent-path normalization strips the ``./``
  before the segment match.  A sibling ``./src/content_x/`` path stays green,
  proving the match is by path segment and not a naive prefix."""
  regressed = _GOLDEN_CONTENT_SPLIT.replace(
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n)",
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n"
    "    ./src/content/unit_definition_loader.cpp\n)",
  )
  assert regressed != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  violations = _content_leaf_split_violations(regressed)
  assert any("content sources directly" in v for v in violations), violations

  sibling = _GOLDEN_CONTENT_SPLIT.replace(
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n)",
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n"
    "    ./src/content_x/sibling_loader.cpp\n)",
  )
  assert sibling != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  assert _content_leaf_split_violations(sibling) == []


def test_gate_flags_source_dir_var_content_path_smuggled_into_core() -> None:
  """Repair round P2: the same content file addressed through
  ``${CMAKE_CURRENT_SOURCE_DIR}/src/content/`` must turn red -- the known
  source-root variable prefix is stripped before the segment match, so a
  root-variable spelling cannot bypass the leaf gate."""
  regressed = _GOLDEN_CONTENT_SPLIT.replace(
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n)",
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n"
    "    ${CMAKE_CURRENT_SOURCE_DIR}/src/content/unit_definition_loader.cpp\n)",
  )
  assert regressed != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  violations = _content_leaf_split_violations(regressed)
  assert any("content sources directly" in v for v in violations), violations


def test_gate_flags_stray_source_appended_to_content_via_target_sources() -> None:
  """Repair round P3: a ``target_sources(ef_content PRIVATE src/core/...)`` call
  appended after ``add_library`` must turn red.  Assertion (c) aggregates every
  ``target_sources(ef_content ...)`` call, so the leaf archive cannot be padded
  with engine sources outside its ``${EF_CONTENT_SOURCES}`` group."""
  regressed = _GOLDEN_CONTENT_SPLIT + (
    "\ntarget_sources(ef_content PRIVATE src/core/engine/extra.cpp)\n"
  )
  assert regressed != _GOLDEN_CONTENT_SPLIT, "fixture mutation did not apply"
  violations = _content_leaf_split_violations(regressed)
  assert any("literal sources" in v for v in violations), violations


# --- Facade link-unit split gate (T3 second physical split, this iteration) --
# runtime/facade compiles into its own ``ef_facade`` static archive.  Unlike
# the I46 content split, the facade sits ABOVE ef_core, so the invariant is
# direction-inverted: ``ef_facade`` links ``ef_core`` (facade TUs resolve
# engine/mission symbols downward) and ``ef_core`` must never link
# ``ef_facade`` (that back-edge would both invert the layer direction and
# declare a static-library cycle, because the forward facade -> core edge is
# required).  The consumers whose TUs reference facade symbols (``ef_py``,
# ``ef_test``) must link ``ef_facade`` so the single-pass link order
# "consumer objects, ef_facade, ef_core, ..." holds.


def _is_facade_path(token: str) -> bool:
  """True when ``token`` addresses a file under ``src/runtime/facade/`` in any
  equivalent spelling, matched by path *segment* so a sibling directory such as
  ``src/runtime/facade_x/`` is never mis-flagged."""
  segments = _normalize_source_path(token).split("/")
  return any(
    segments[i] == "src"
    and segments[i + 1] == "runtime"
    and segments[i + 2] == "facade"
    for i in range(len(segments) - 2)
  )


_FACADE_SYMBOL_CONSUMERS = ("ef_py", "ef_test")


def _facade_split_violations(source: str) -> list[str]:
  """Return every way ``source`` breaks the T3 facade link-unit invariant.

  An empty list means the gate is green.  The checks reuse the robust
  parser/token machinery of the content gate (comments, string masking,
  multi-call traversal), with the dependency direction inverted:

  * (a) no facade source -- neither the ``${EF_RUNTIME_FACADE_SOURCES}`` group
    nor any literal ``src/runtime/facade/`` path in any equivalent spelling --
    is compiled into ``ef_core``;
  * (b) no ``target_link_libraries(ef_core ...)`` call links ``ef_facade``,
    under any scope keyword (back-edge / static-library cycle);
  * (c) an ``ef_facade`` STATIC target exists and is built from the facade
    source group only -- its ``add_library`` sources plus every later
    ``target_sources(ef_facade ...)`` call must stay within
    ``${EF_RUNTIME_FACADE_SOURCES}`` with no literal ``src/`` path smuggled in;
  * (d) ``ef_facade`` links ``ef_core`` (the one allowed direction: the facade
    is the application layer above the core aggregate);
  * (e) every consumer target whose TUs reference facade symbols (``ef_py``
    bindings, the ``ef_test`` facade suites) links ``ef_facade`` in at least
    one of its ``target_link_libraries`` calls."""
  text = _strip_cmake_comments(source)
  set_map = _set_variable_map(text)
  libraries = _add_library_targets(text)
  violations: list[str] = []

  # (c) ef_facade is a STATIC archive built from the facade source group only.
  facade = libraries.get("ef_facade")
  if facade is None:
    violations.append("no add_library(ef_facade ...) target found")
  else:
    facade_type, add_library_sources = facade
    facade_sources = list(add_library_sources)
    for call in _scoped_call_args(text, "target_sources", "ef_facade"):
      facade_sources.extend(call)
    if facade_type != "STATIC":
      violations.append(
        f"ef_facade must be a STATIC archive (found type {facade_type!r})"
      )
    if "${EF_RUNTIME_FACADE_SOURCES}" not in facade_sources:
      violations.append(
        "add_library(ef_facade) must build from the ${EF_RUNTIME_FACADE_SOURCES} group"
      )
    stray = [s for s in facade_sources if _normalize_source_path(s).startswith("src/")]
    if stray:
      violations.append(
        "ef_facade must consume the ${EF_RUNTIME_FACADE_SOURCES} group only, not "
        f"literal sources: {stray}"
      )

  facade_group_literals = {
    token
    for token in set_map.get("EF_RUNTIME_FACADE_SOURCES", [])
    if _as_var_ref(token) is None
  }

  def _is_facade_source(token: str) -> bool:
    return _is_facade_path(token) or token in facade_group_literals

  # (a) facade must not be compiled into ef_core (variable or literal form).
  core = libraries.get("ef_core")
  core_roots: list[str] = list(core[1]) if core else []
  for call in _scoped_call_args(text, "target_sources", "ef_core"):
    core_roots.extend(call)
  referenced, literals = _resolve_sources(set_map, core_roots)
  if "EF_RUNTIME_FACADE_SOURCES" in referenced:
    violations.append(
      "ef_core compiles the ${EF_RUNTIME_FACADE_SOURCES} group; the facade must "
      "stay a separate archive"
    )
  facade_in_core = sorted(token for token in literals if _is_facade_source(token))
  if facade_in_core:
    violations.append(f"ef_core compiles facade sources directly: {facade_in_core}")

  # (b) ef_core must never link ef_facade -- traverse *every* call and scope.
  for libs in _scoped_call_args(text, "target_link_libraries", "ef_core"):
    if "ef_facade" in libs:
      violations.append(
        "ef_core links ef_facade: the facade sits above the core aggregate "
        "(back-edge / static-library cycle)"
      )
      break

  # (d) ef_facade must link ef_core (the single allowed direction).
  facade_links = [
    lib
    for call in _scoped_call_args(text, "target_link_libraries", "ef_facade")
    for lib in call
  ]
  if "ef_core" not in facade_links:
    violations.append(
      "ef_facade must link ef_core (downward dependency edge missing)"
    )

  # (e) facade-symbol consumers must link the facade unit.
  for consumer in _FACADE_SYMBOL_CONSUMERS:
    consumer_links = [
      lib
      for call in _scoped_call_args(text, "target_link_libraries", consumer)
      for lib in call
    ]
    if "ef_facade" not in consumer_links:
      violations.append(
        f"{consumer} references RuntimeFacade symbols but does not link ef_facade"
      )

  return violations


def test_facade_layer_is_its_own_static_link_unit_above_the_core_aggregate() -> None:
  """T3 physical link-unit split (this iteration, second slice after I46's
  content split): runtime/facade compiles into its own ``ef_facade`` static
  archive that links ``ef_core`` one-way, ``ef_core`` never links back, and
  the facade-symbol consumers (``ef_py``, ``ef_test``) link ``ef_facade``.

  This is the CMake-level companion to the include-direction gates: the
  governance gate proves no engine/mission/model/content source may #include
  runtime/facade (so the split direction is real at the source level), and
  this gate proves the *build* keeps the facade in a separate archive whose
  only project dependency edge points downward at ``ef_core``."""
  violations = _facade_split_violations(_cmake_source())
  assert not violations, "facade link-unit split regressed:\n  " + "\n  ".join(violations)


# A minimal but structurally faithful correct facade split, used as the
# baseline for the negative gate cases below.  It mirrors the real CMakeLists
# layering (grouped core sources -> ef_core; ${EF_RUNTIME_FACADE_SOURCES} ->
# ef_facade; ef_facade links ef_core one-way; ef_py/ef_test link ef_facade)
# so mutations exercise the same parser.
_GOLDEN_FACADE_SPLIT = """\
set(EF_CORE_ENGINE_SOURCES
    src/core/engine/simulation_kernel.cpp
)

set(EF_RUNTIME_FACADE_SOURCES
    src/runtime/facade/runtime_facade.cpp
)

set(EF_CORE_SOURCES
    ${EF_CORE_ENGINE_SOURCES}
)

add_library(ef_core STATIC
    ${EF_CORE_SOURCES}
)
target_include_directories(ef_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(ef_core PUBLIC
    spdlog::spdlog
)

add_library(ef_facade STATIC
    ${EF_RUNTIME_FACADE_SOURCES}
)
target_include_directories(ef_facade PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(ef_facade PUBLIC
    ef_core
    spdlog::spdlog
)

nanobind_add_module(ef_py
    src/interfaces/python/python_module.cpp
)
target_link_libraries(ef_py PRIVATE ef_facade)

add_executable(ef_test src/tests/test_main.cpp)
target_link_libraries(ef_test PRIVATE ef_facade ef_core doctest::doctest)
"""


def test_facade_gate_baseline_golden_split_is_green() -> None:
  """Sanity anchor: the correct synthetic facade split must pass, so the red
  cases below prove the mutation was caught rather than a broken fixture."""
  assert _facade_split_violations(_GOLDEN_FACADE_SPLIT) == []


def test_facade_gate_flags_facade_group_readded_to_core() -> None:
  """``${EF_RUNTIME_FACADE_SOURCES}`` folded back into the ef_core source
  group must turn the gate red (the exact regression this split removes)."""
  regressed = _GOLDEN_FACADE_SPLIT.replace(
    "set(EF_CORE_SOURCES\n    ${EF_CORE_ENGINE_SOURCES}\n)",
    "set(EF_CORE_SOURCES\n    ${EF_CORE_ENGINE_SOURCES}\n"
    "    ${EF_RUNTIME_FACADE_SOURCES}\n)",
  )
  assert regressed != _GOLDEN_FACADE_SPLIT, "fixture mutation did not apply"
  violations = _facade_split_violations(regressed)
  assert any("${EF_RUNTIME_FACADE_SOURCES}" in v and "ef_core" in v for v in violations), violations


def test_facade_gate_flags_literal_facade_path_smuggled_into_core() -> None:
  """A literal ``src/runtime/facade/`` path added to an ef_core source group
  (bypassing the variable) must turn red; a sibling ``src/runtime/facade_x/``
  path stays green, proving the match is by path segment."""
  regressed = _GOLDEN_FACADE_SPLIT.replace(
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n)",
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n"
    "    ${CMAKE_CURRENT_SOURCE_DIR}/src/runtime/facade/runtime_facade_query.cpp\n)",
  )
  assert regressed != _GOLDEN_FACADE_SPLIT, "fixture mutation did not apply"
  violations = _facade_split_violations(regressed)
  assert any("facade sources directly" in v for v in violations), violations

  sibling = _GOLDEN_FACADE_SPLIT.replace(
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n)",
    "set(EF_CORE_ENGINE_SOURCES\n    src/core/engine/simulation_kernel.cpp\n"
    "    ./src/runtime/facade_x/sibling.cpp\n)",
  )
  assert sibling != _GOLDEN_FACADE_SPLIT, "fixture mutation did not apply"
  assert _facade_split_violations(sibling) == []


def test_facade_gate_flags_core_backedge_under_any_scope() -> None:
  """A *second* ``target_link_libraries(ef_core ...)`` call that links
  ef_facade under PRIVATE must turn red: with the mandatory facade -> core
  edge in place, any core -> facade edge declares a static-library cycle."""
  regressed = _GOLDEN_FACADE_SPLIT + "\ntarget_link_libraries(ef_core PRIVATE ef_facade)\n"
  violations = _facade_split_violations(regressed)
  assert any("back-edge" in v for v in violations), violations


def test_facade_gate_flags_missing_downward_edge() -> None:
  """With the real ``ef_facade -> ef_core`` link removed (and the edge only
  *mentioned* inside a quoted string), assertion (d) must still fail: facade
  TUs cannot resolve engine/mission symbols without the downward edge."""
  regressed = _GOLDEN_FACADE_SPLIT.replace(
    "target_link_libraries(ef_facade PUBLIC\n    ef_core\n    spdlog::spdlog\n)",
    "target_link_libraries(ef_facade PUBLIC\n    spdlog::spdlog\n)\n"
    'message(STATUS "target_link_libraries(ef_facade PUBLIC ef_core)")',
  )
  assert regressed != _GOLDEN_FACADE_SPLIT, "fixture mutation did not apply"
  violations = _facade_split_violations(regressed)
  assert any("downward dependency edge missing" in v for v in violations), violations


def test_facade_gate_flags_consumer_dropping_the_facade_unit() -> None:
  """A facade-symbol consumer silently rewired back to ef_core only must turn
  red: its TUs reference RuntimeFacade symbols that no longer arrive."""
  regressed = _GOLDEN_FACADE_SPLIT.replace(
    "target_link_libraries(ef_py PRIVATE ef_facade)",
    "target_link_libraries(ef_py PRIVATE ef_core)",
  )
  assert regressed != _GOLDEN_FACADE_SPLIT, "fixture mutation did not apply"
  violations = _facade_split_violations(regressed)
  assert any("ef_py" in v and "ef_facade" in v for v in violations), violations


def test_facade_gate_flags_stray_source_appended_via_target_sources() -> None:
  """A ``target_sources(ef_facade PRIVATE src/core/...)`` call appended after
  ``add_library`` must turn red: the facade archive cannot be padded with
  engine sources outside its ``${EF_RUNTIME_FACADE_SOURCES}`` group."""
  regressed = _GOLDEN_FACADE_SPLIT + (
    "\ntarget_sources(ef_facade PRIVATE src/core/engine/extra.cpp)\n"
  )
  violations = _facade_split_violations(regressed)
  assert any("literal sources" in v for v in violations), violations


# --- Facade unit isolation hardening (source-level companion) ----------------
# The include-direction governance gate already constrains facade *targets*
# (runtime_facade may reach core_engine/core_mission/runtime_contracts/...).
# The link-unit split adds a finer isolation invariant: within the facade
# unit, direct engine includes are confined to the single declared engine-seam
# header (``runtime_facade_internal.h``), and that seam header is private to
# the unit -- no TU outside src/runtime/facade may include it.  Together with
# the existing public-header gates (test_runtime_facade_contract_boundaries),
# this pins "facade reaches engine internals only through the declared
# contract seam" as a mechanical property of the new archive.

_FACADE_SRC_REL = "src/runtime/facade"
_FACADE_ENGINE_SEAM_HEADER = "runtime_facade_internal.h"
_ISOLATION_SCAN_SUFFIXES = {".h", ".hpp", ".cpp", ".cc", ".cxx", ".inc", ".cu"}


def _facade_engine_include_offenders(repo_root: Path) -> list[tuple[str, int, str]]:
  """(file, line, text) for every direct core/engine include in a facade file
  other than the declared engine-seam header."""
  offenders: list[tuple[str, int, str]] = []
  facade_root = repo_root / _FACADE_SRC_REL
  for path in sorted(facade_root.rglob("*")):
    if path.suffix not in _ISOLATION_SCAN_SUFFIXES:
      continue
    if path.name == _FACADE_ENGINE_SEAM_HEADER:
      continue
    for lineno, line in enumerate(
      path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
      stripped = line.strip()
      if stripped.startswith("#include") and '"core/engine/' in stripped:
        offenders.append((path.relative_to(repo_root).as_posix(), lineno, stripped))
  return offenders


def _facade_internal_seam_offenders(repo_root: Path) -> list[tuple[str, int, str]]:
  """(file, line, text) for every include of the facade engine-seam header
  from outside the facade unit."""
  offenders: list[tuple[str, int, str]] = []
  src_root = repo_root / "src"
  facade_root = repo_root / _FACADE_SRC_REL
  for path in sorted(src_root.rglob("*")):
    if path.suffix not in _ISOLATION_SCAN_SUFFIXES:
      continue
    if path.is_relative_to(facade_root):
      continue
    for lineno, line in enumerate(
      path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
      stripped = line.strip()
      if stripped.startswith("#include") and _FACADE_ENGINE_SEAM_HEADER in stripped:
        offenders.append((path.relative_to(repo_root).as_posix(), lineno, stripped))
  return offenders


def test_facade_engine_includes_are_confined_to_the_declared_seam_header() -> None:
  """Within the facade link unit, only ``runtime_facade_internal.h`` (the
  declared engine seam that owns the ``WorldBatchRuntime`` wrapping) may
  include ``core/engine/*`` directly; every other facade TU and header goes
  through that seam or the contracts vocabulary."""
  offenders = _facade_engine_include_offenders(REPO_ROOT)
  assert offenders == [], (
    "facade files must reach core/engine only through the declared seam header "
    f"({_FACADE_SRC_REL}/{_FACADE_ENGINE_SEAM_HEADER}): {offenders}"
  )


def test_facade_engine_seam_header_stays_private_to_the_facade_unit() -> None:
  """The engine-seam header is the facade archive's private implementation
  boundary: nothing outside src/runtime/facade may include it (consumers get
  ``runtime_facade.h``/``runtime_facade_types.h``, which the contract-boundary
  gates keep engine-free)."""
  offenders = _facade_internal_seam_offenders(REPO_ROOT)
  assert offenders == [], (
    "the facade engine-seam header leaked outside the facade unit: "
    f"{offenders}"
  )


def test_facade_isolation_scans_catch_injected_offenders(tmp_path: Path) -> None:
  """Negative self-test (no real source files touched): a throwaway repo tree
  with (1) a facade helper including core/engine directly and (2) an outside
  TU including the seam header must be flagged by the same scan helpers the
  green gates above run."""
  fake_repo = tmp_path / "fake_repo"
  facade_dir = fake_repo / "src" / "runtime" / "facade"
  outside_dir = fake_repo / "src" / "interfaces" / "python"
  facade_dir.mkdir(parents=True)
  outside_dir.mkdir(parents=True)

  (facade_dir / _FACADE_ENGINE_SEAM_HEADER).write_text(
    '#pragma once\n#include "core/engine/world_batch_runtime.h"\n',
    encoding="utf-8",
  )
  (facade_dir / "rogue_helper.h").write_text(
    '#pragma once\n#include "core/engine/simulation_kernel.h"\n',
    encoding="utf-8",
  )
  (outside_dir / "rogue_binding.cpp").write_text(
    '#include "runtime/facade/runtime_facade_internal.h"\n',
    encoding="utf-8",
  )

  engine_offenders = _facade_engine_include_offenders(fake_repo)
  assert [(path, line) for path, line, _ in engine_offenders] == [
    ("src/runtime/facade/rogue_helper.h", 2)
  ], engine_offenders

  seam_offenders = _facade_internal_seam_offenders(fake_repo)
  assert [(path, line) for path, line, _ in seam_offenders] == [
    ("src/interfaces/python/rogue_binding.cpp", 1)
  ], seam_offenders


def test_python_module_uses_binding_source_group_instead_of_flat_file_list() -> None:
  source = _cmake_source()
  body = _command_body(source, "nanobind_add_module", "ef_py")
  assert "${EF_PYTHON_BINDING_SOURCES}" in body
  assert "src/" not in body, (
    "nanobind_add_module(ef_py) should consume grouped binding sources only"
  )


def test_core_mission_root_has_no_flat_runtime_sources() -> None:
  mission_root = REPO_ROOT / "src" / "core" / "mission"
  flat_sources = sorted(
    path.name for path in mission_root.iterdir() if path.suffix in {".cpp", ".h"}
  )
  assert not flat_sources, (
    f"mission sources should live under runtime/ or episode/: {flat_sources}"
  )


def test_core_mission_episode_detail_does_not_escape_controller_domain() -> None:
  allowed_roots = {
    REPO_ROOT / "src" / "core" / "mission" / "episode",
  }
  search_roots = [
    REPO_ROOT / "src",
    REPO_ROOT / "tests",
  ]
  forbidden_include = "core/mission/episode/" + "detail/"
  violations: list[tuple[str, int, str]] = []
  for root in search_roots:
    for path in root.rglob("*"):
      if path.suffix not in {".cpp", ".h", ".py"}:
        continue
      if any(path.is_relative_to(allowed_root) for allowed_root in allowed_roots):
        continue
      for lineno, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
      ):
        if forbidden_include in line:
          violations.append((str(path.relative_to(REPO_ROOT)), lineno, line.strip()))

  assert not violations, (
    "mission episode detail includes escaped controller domain: "
    f"{violations}"
  )
