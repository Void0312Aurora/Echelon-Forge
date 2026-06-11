#!/usr/bin/env python3
"""Unified damage-model source governance maintenance entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.source_governance import (  # noqa: E402
    admission_audit,
    payload_pack,
    rights_output_policy,
)


CommandMain = Callable[[list[str] | None], int]

COMMANDS: dict[str, tuple[str, CommandMain]] = {
    "admission-audit": (
        "Audit source ledgers and candidate docs for fail-closed admission.",
        admission_audit.main,
    ),
    "payload-pack": (
        "Build or inspect the retained source payload pack.",
        payload_pack.main,
    ),
    "rights-output-policy": (
        "Evaluate the source rights and allowed-output policy gate.",
        rights_output_policy.main,
    ),
}


def _print_help() -> None:
    print("usage: damage_model_source_governance.py <command> [options]\n")
    print("Damage-model source governance commands:\n")
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
