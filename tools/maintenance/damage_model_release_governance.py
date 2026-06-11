#!/usr/bin/env python3
"""Unified damage-model release governance entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.release_governance import (  # noqa: E402
    effect_scale_release_closeout,
    effect_scale_release_readiness,
    package_provenance_identity,
    provenance_closeout,
    provenance_identity_review,
    scoped_release_identity,
    source_release_signoff,
)


CommandMain = Callable[[list[str] | None], int]

COMMANDS: dict[str, tuple[str, CommandMain]] = {
    "package-provenance-identity": (
        "Evaluate package provenance and surrogate identity boundaries.",
        package_provenance_identity.main,
    ),
    "provenance-identity-review": (
        "Evaluate retained provenance identity review evidence.",
        provenance_identity_review.main,
    ),
    "provenance-closeout": (
        "Evaluate release provenance closeout evidence.",
        provenance_closeout.main,
    ),
    "source-release-signoff": (
        "Evaluate source release signoff evidence.",
        source_release_signoff.main,
    ),
    "scoped-release-identity": (
        "Evaluate scoped release identity evidence.",
        scoped_release_identity.main,
    ),
    "effect-scale-readiness": (
        "Evaluate Stage B effect-scale release readiness.",
        effect_scale_release_readiness.main,
    ),
    "effect-scale-closeout": (
        "Evaluate Stage B effect-scale release closeout.",
        effect_scale_release_closeout.main,
    ),
}


def _print_help() -> None:
    print("usage: damage_model_release_governance.py <command> [options]\n")
    print("Damage-model release governance commands:\n")
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
