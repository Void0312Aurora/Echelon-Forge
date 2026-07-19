#!/usr/bin/env python3
"""Parse compact X-macro field lists into declarative DTO schema modules."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.dto_schema.model import Field  # noqa: E402


@dataclass(frozen=True, slots=True)
class ParsedXMacroFile:
  file_header: str
  fields: tuple[Field, ...]
  file_footer: str


def _matching_parenthesis(text: str, opening_index: int) -> int:
  depth = 0
  quote: str | None = None
  escaped = False
  for index in range(opening_index, len(text)):
    char = text[index]
    if quote is not None:
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == quote:
        quote = None
      continue
    if char in {'"', "'"}:
      quote = char
    elif char == "(":
      depth += 1
    elif char == ")":
      depth -= 1
      if depth == 0:
        return index
  raise ValueError(f"unbalanced macro invocation: {text!r}")


def _split_arguments(payload: str) -> tuple[str, ...]:
  arguments: list[str] = []
  start = 0
  quote: str | None = None
  escaped = False
  depths = {"(": 0, "[": 0, "{": 0, "<": 0}
  closing = {")": "(", "]": "[", "}": "{", ">": "<"}

  for index, char in enumerate(payload):
    if quote is not None:
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == quote:
        quote = None
      continue
    if char in {'"', "'"}:
      quote = char
      continue
    if char in depths:
      depths[char] += 1
      continue
    if char in closing and depths[closing[char]] > 0:
      depths[closing[char]] -= 1
      continue
    if char == "," and not any(depths.values()):
      arguments.append(payload[start:index].strip())
      start = index + 1

  arguments.append(payload[start:].strip())
  return tuple(arguments)


def _parse_macro_line(line: str, macros: frozenset[str]) -> Field | None:
  stripped = line.strip()
  for macro in macros:
    prefix = f"{macro}("
    if not stripped.startswith(prefix):
      continue
    closing_index = _matching_parenthesis(stripped, len(macro))
    remainder = stripped[closing_index + 1 :].strip()
    if remainder and not remainder.startswith("//"):
      raise ValueError(f"unexpected text after macro invocation: {line!r}")
    arguments = _split_arguments(stripped[len(prefix) : closing_index])
    if len(arguments) != 3:
      raise ValueError(
        f"{macro} requires type, name, and default; got {len(arguments)} arguments"
      )
    comment = remainder[2:].strip() if remainder else None
    return Field(
      name=arguments[1],
      cpp_type=arguments[0],
      default=arguments[2],
      group=macro,
      comment=comment or None,
    )
  return None


def parse_xmacro_text(text: str, macros: frozenset[str]) -> ParsedXMacroFile:
  """Parse field invocations while preserving the exact outer file template."""

  if not macros:
    raise ValueError("at least one macro name is required")

  lines = text.splitlines(keepends=True)
  parsed_lines: list[tuple[int, Field]] = []
  for index, line in enumerate(lines):
    field = _parse_macro_line(line.rstrip("\r\n"), macros)
    if field is not None:
      parsed_lines.append((index, field))

  if not parsed_lines:
    raise ValueError(f"no invocations found for macros: {sorted(macros)}")

  first_index = parsed_lines[0][0]
  last_index = parsed_lines[-1][0]
  parsed_indexes = {index for index, _ in parsed_lines}
  unsupported = [
    lines[index].rstrip("\r\n")
    for index in range(first_index, last_index + 1)
    if index not in parsed_indexes and lines[index].strip()
  ]
  if unsupported:
    raise ValueError(
      "non-macro content between field invocations is not supported: "
      f"{unsupported[:3]}"
    )

  canonical_header = "".join(lines[:first_index]).replace("\r\n", "\n")
  canonical_footer = "".join(lines[last_index + 1 :]).replace("\r\n", "\n")
  return ParsedXMacroFile(
    file_header=canonical_header,
    fields=tuple(field for _, field in parsed_lines),
    file_footer=canonical_footer,
  )


def parse_xmacro_file(path: Path, macros: frozenset[str]) -> ParsedXMacroFile:
  return parse_xmacro_text(path.read_bytes().decode("utf-8"), macros)


def _parenthesized_string(value: str) -> str:
  if not value:
    return '""'
  chunks = value.splitlines(keepends=True)
  if not chunks:
    chunks = [value]
  return "(\n" + "".join(f"  {chunk!r}\n" for chunk in chunks) + ")"


def render_schema_module(
  *,
  parsed: ParsedXMacroFile,
  schema_name: str,
  output_path: str,
  source_path: str,
) -> str:
  """Render a reviewable Python schema module from parsed X-macro fields."""

  lines = [
    f'"""Declarative DTO schema parsed from {source_path}."""\n',
    "\n",
    "from __future__ import annotations\n",
    "\n",
    "from tools.maintenance.dto_schema.model import DtoSchema, Field\n",
    "\n",
    "\n",
    f"FILE_HEADER = {_parenthesized_string(parsed.file_header)}\n",
    f"FILE_FOOTER = {_parenthesized_string(parsed.file_footer)}\n",
    "\n",
    "\n",
    "SCHEMA = DtoSchema(\n",
    f"  name={schema_name!r},\n",
    f"  output_path={output_path!r},\n",
    "  file_header=FILE_HEADER,\n",
    "  fields=(\n",
  ]
  for field in parsed.fields:
    arguments = [
      f"name={field.name!r}",
      f"cpp_type={field.cpp_type!r}",
      f"default={field.default!r}",
      f"group={field.group!r}",
    ]
    if field.comment is not None:
      arguments.append(f"comment={field.comment!r}")
    lines.append(f"    Field({', '.join(arguments)}),\n")
  lines.extend(
    [
      "  ),\n",
      "  file_footer=FILE_FOOTER,\n",
      ")\n",
    ]
  )
  return "".join(lines)


def _build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="Parse an X-macro field list into a DTO schema module."
  )
  parser.add_argument("source", type=Path)
  parser.add_argument("--macro", action="append", required=True, dest="macros")
  parser.add_argument("--schema-name", required=True)
  parser.add_argument("--output-path", required=True)
  parser.add_argument("--schema-output", type=Path)
  return parser


def main(argv: list[str] | None = None) -> int:
  args = _build_parser().parse_args(argv)
  parsed = parse_xmacro_file(args.source, frozenset(args.macros))
  source = render_schema_module(
    parsed=parsed,
    schema_name=args.schema_name,
    output_path=args.output_path,
    source_path=args.source.as_posix(),
  )
  if args.schema_output is None:
    sys.stdout.write(source)
  else:
    args.schema_output.write_bytes(source.encode("utf-8"))
    print(f"WROTE {args.schema_output.as_posix()} ({len(parsed.fields)} fields)")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
