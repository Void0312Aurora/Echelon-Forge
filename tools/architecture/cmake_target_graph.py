"""Small, source-only CMake target link graph scanner.

This intentionally extracts only project target-to-target links from
``target_link_libraries``. It does not evaluate CMake conditions or claim that
link order, generator expressions, or imported third-party targets are fully
resolved.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class CMakeTargetEdge:
  source: str
  target: str
  path: str
  line: int


def _strip_comments(text: str) -> str:
  text = re.sub(
    r"#\[(=*)\[.*?\]\1\]",
    lambda match: "\n" * match.group().count("\n"),
    text,
    flags=re.DOTALL,
  )
  lines: list[str] = []
  for line in text.splitlines():
    quote = False
    escaped = False
    output: list[str] = []
    for char in line:
      if char == '"' and not escaped:
        quote = not quote
      if char == "#" and not quote:
        break
      output.append(char)
      escaped = char == "\\" and not escaped
      if char != "\\":
        escaped = False
    lines.append("".join(output))
  return "\n".join(lines)


def _commands(text: str, name: str) -> list[tuple[int, str]]:
  pattern = re.compile(rf"(?im)^\s*{re.escape(name)}\s*\(")
  results: list[tuple[int, str]] = []
  for match in pattern.finditer(text):
    depth = 1
    quote = False
    escaped = False
    index = match.end()
    start = index
    while index < len(text) and depth:
      char = text[index]
      if char == '"' and not escaped:
        quote = not quote
      elif not quote and char == "(":
        depth += 1
      elif not quote and char == ")":
        depth -= 1
      escaped = char == "\\" and not escaped
      if char != "\\":
        escaped = False
      index += 1
    if depth == 0:
      line = text.count("\n", 0, match.start()) + 1
      results.append((line, text[start : index - 1]))
  return results


def _tokens(body: str) -> list[str]:
  return re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"|([^\s()]+)', body)


def _token_values(body: str) -> list[str]:
  return [quoted or bare for quoted, bare in _tokens(body)]


def build_edges(cmake_path: Path) -> tuple[CMakeTargetEdge, ...]:
  text = _strip_comments(cmake_path.read_text(encoding="utf-8"))
  target_names: set[str] = set()
  declarations = (
    _commands(text, "add_library")
    + _commands(text, "add_executable")
    + _commands(text, "nanobind_add_module")
  )
  for _, body in declarations:
    tokens = _token_values(body)
    if tokens and tokens[0].startswith("ef_"):
      target_names.add(tokens[0])

  edges: set[CMakeTargetEdge] = set()
  scopes = {"PRIVATE", "PUBLIC", "INTERFACE"}
  for line, body in _commands(text, "target_link_libraries"):
    tokens = _token_values(body)
    if not tokens:
      continue
    source = tokens[0]
    if source not in target_names:
      continue
    for token in tokens[1:]:
      if token.upper() in scopes or token.startswith("${") or token.startswith("$<"):
        continue
      if token in target_names:
        edges.add(CMakeTargetEdge(source, token, cmake_path.as_posix(), line))
  return tuple(sorted(edges))


def strongly_connected_components(edges: tuple[CMakeTargetEdge, ...]) -> list[list[str]]:
  graph: dict[str, set[str]] = defaultdict(set)
  for edge in edges:
    graph[edge.source].add(edge.target)
  indices: dict[str, int] = {}
  lowlinks: dict[str, int] = {}
  stack: list[str] = []
  active: set[str] = set()
  components: list[list[str]] = []
  index = 0

  def visit(node: str) -> None:
    nonlocal index
    indices[node] = lowlinks[node] = index
    index += 1
    stack.append(node)
    active.add(node)
    for target in sorted(graph[node]):
      if target not in indices:
        visit(target)
        lowlinks[node] = min(lowlinks[node], lowlinks[target])
      elif target in active:
        lowlinks[node] = min(lowlinks[node], indices[target])
    if lowlinks[node] == indices[node]:
      component: list[str] = []
      while True:
        member = stack.pop()
        active.remove(member)
        component.append(member)
        if member == node:
          break
      if len(component) > 1:
        components.append(sorted(component))

  for node in sorted(graph):
    if node not in indices:
      visit(node)
  return sorted(components)
