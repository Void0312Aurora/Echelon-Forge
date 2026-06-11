#!/usr/bin/env python3
"""Unified damage-model independent review entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.independent_review import (  # noqa: E402
    effect_scale_review,
    review_closeout,
    scope_bucket_review,
    uncertainty_review,
)


CommandMain = Callable[[list[str] | None], int]

COMMANDS: dict[str, tuple[str, CommandMain]] = {
    "effect-scale-review": (
        "Evaluate bounded Stage B effect-scale independent review evidence.",
        effect_scale_review.main,
    ),
    "review-closeout": (
        "Evaluate RES-011/012 independent review closeout evidence.",
        review_closeout.main,
    ),
    "scope-bucket-review": (
        "Evaluate scope-bucket independent review evidence.",
        scope_bucket_review.main,
    ),
    "uncertainty-review": (
        "Evaluate uncertainty review evidence.",
        uncertainty_review.main,
    ),
}


def _print_help() -> None:
    print("usage: damage_model_independent_review.py <command> [options]\n")
    print("Damage-model independent review commands:\n")
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
