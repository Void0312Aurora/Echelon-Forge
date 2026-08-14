"""Shared dispatch utilities for maintenance CLIs.

Provides a reusable command-routing pattern for both single-domain wrappers
and unified multi-domain entrypoints.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

CommandMain = Callable[[list[str] | None], int]

#: Repository root resolved once, added to sys.path by each caller that
#: needs ``tools.*`` imports before the package is installed.
REPO_ROOT = Path(__file__).resolve().parents[2]

CommandRegistry = dict[str, tuple[str, CommandMain]]


def _print_help(prog: str, description: str, commands: CommandRegistry) -> None:
  print(_usage_hint(prog, commands) + "\n")
  print(description)
  print()
  width = max((len(c) for c in commands), default=0)
  for command, (desc, _) in sorted(commands.items()):
    print(f" {command:<{width}} {desc}")
  print("\nUse '<command> --help' for command-specific options.")


def ensure_path() -> None:
  """Add the repository root to ``sys.path`` if it isn't already there."""
  if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _resolve_command(
  args: list[str], commands: CommandRegistry
) -> tuple[str, CommandMain, list[str]]:
  """Resolve a (possibly compound) command name and return remaining argv.

  Supports two forms so both single-domain and unified entrypoints work::

    tool.py <single-word-cmd> [opts ...]    # legacy routers
    tool.py <domain> <sub-cmd> [opts ...]    # unified entrypoint
  """
  if len(args) >= 2:
    compound = f"{args[0]} {args[1]}"
    if compound in commands:
      return compound, commands[compound][1], args[2:]

  single = args[0]
  if single in commands:
    return single, commands[single][1], args[1:]

  return "", _noop, []


def _noop(_argv: list[str] | None = None) -> int:
  return 2


def _usage_hint(prog: str, commands: CommandRegistry) -> str:
  """Return the usage line adjusted for whether commands are compound."""
  has_compound = any(" " in c for c in commands)
  if has_compound:
    return f"usage: {prog} <domain> <command> [options]"
  return f"usage: {prog} <command> [options]"


def dispatch(
  *,
  prog: str,
  description: str,
  commands: CommandRegistry,
  argv: list[str] | None = None,
) -> int:
  """Route a sub-command to the matching ``main`` callable.

  Args:
    prog: Display name for the CLI (e.g. ``generate.py``).
    description: One-line summary printed by ``--help``.
    commands: Mapping of ``{command_name: (description, main_callable)}``.
         Keys may be single words or compound (``domain subcmd``).
    argv: Argument list; defaults to ``sys.argv[1:]``.

  Returns:
    Exit code (0 = success, 2 = unknown command).
  """
  args = list(sys.argv[1:] if argv is None else argv)
  if not args or args[0] in {"-h", "--help"}:
    _print_help(prog, description, commands)
    return 0

  resolved, main_func, remainder = _resolve_command(args, commands)
  if main_func is _noop:
    attempted = " ".join(args[:2]) if len(args) >= 2 else args[0]
    print(f"unknown command: {attempted}", file=sys.stderr)
    _print_help(prog, description, commands)
    return 2

  return main_func(remainder)
