#!/usr/bin/env python3
"""Unified damage-model scope and provenance closeout entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.scope_provenance import (  # noqa: E402
    geometry_warhead_row_provenance,
    mechanism_source_closeout,
    target_geometry_closeout,
    warhead_scope_closeout,
)


CommandMain = Callable[[list[str] | None], int]

COMMANDS: dict[str, tuple[str, CommandMain]] = {
    "row-provenance": (
        "Evaluate geometry and warhead row provenance boundaries.",
        geometry_warhead_row_provenance.main,
    ),
    "target-geometry-closeout": (
        "Evaluate target-geometry scope closeout evidence.",
        target_geometry_closeout.main,
    ),
    "warhead-scope-closeout": (
        "Evaluate warhead-family scope closeout evidence.",
        warhead_scope_closeout.main,
    ),
    "mechanism-source-closeout": (
        "Evaluate mechanism source closeout evidence.",
        mechanism_source_closeout.main,
    ),
}


def _print_help() -> None:
    print("usage: damage_model_scope_provenance.py <command> [options]\n")
    print("Damage-model scope/provenance commands:\n")
    width = max(len(command) for command in COMMANDS)
    for command, (description, _) in sorted(COMMANDS.items()):
        print(f"  {command:<{width}}  {description}")
    print("\nUse '<command> --help' for command-specific options.")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        _print_help()
        return 0

    command = args[0]
    if command not in COMMANDS:
        print(f"unknown command: {command}", file=sys.stderr)
        _print_help()
        return 2

    return COMMANDS[command][1](args[1:])


if __name__ == "__main__":
    raise SystemExit(main())
