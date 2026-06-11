#!/usr/bin/env python3
"""Unified damage-model candidate artifact entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import (  # noqa: E402
    effect_scale_result_pack,
    effect_scale_retained_pack,
    effect_scale_snapshot,
    package_bundle,
    runtime_authority_exercise,
    scope_boundary_probe,
    validation_scaffold,
)


CommandMain = Callable[[list[str] | None], int]

COMMANDS: dict[str, tuple[str, CommandMain]] = {
    "validation-scaffold": (
        "Generate the non-authoritative validation scaffold artifact.",
        validation_scaffold.main,
    ),
    "scope-boundary-probe": (
        "Generate Stage B scope boundary probe results.",
        scope_boundary_probe.main,
    ),
    "effect-scale-snapshot": (
        "Generate the Stage B effect-scale candidate snapshot.",
        effect_scale_snapshot.main,
    ),
    "effect-scale-result-pack": (
        "Generate the Stage B effect-scale validation result pack.",
        effect_scale_result_pack.main,
    ),
    "effect-scale-retained-pack": (
        "Write retained Stage B effect-scale candidate artifacts.",
        effect_scale_retained_pack.main,
    ),
    "runtime-authority-exercise": (
        "Generate the test-local runtime authority exercise pack.",
        runtime_authority_exercise.main,
    ),
    "package-bundle": (
        "Assemble the current candidate package bundle.",
        package_bundle.main,
    ),
}


def _print_help() -> None:
    print("usage: damage_model_candidate_artifacts.py <command> [options]\n")
    print("Damage-model candidate artifact commands:\n")
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
