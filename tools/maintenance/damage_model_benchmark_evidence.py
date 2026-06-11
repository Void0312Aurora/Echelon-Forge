#!/usr/bin/env python3
"""Unified damage-model benchmark evidence and admission entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.benchmark_evidence import (  # noqa: E402
    benchmark_execution_admission,
    comparison_hashes,
    debris_admission,
    mechanism_evidence,
    selected_debris_case_admission,
    selected_debris_case_packet,
    spreadsheet_lineage_tolerance_packet,
    spreadsheet_recalculation_admission,
    spreadsheet_replacement_tolerance,
)


CommandMain = Callable[[list[str] | None], int]

COMMANDS: dict[str, tuple[str, CommandMain]] = {
    "mechanism-evidence": (
        "Generate the mechanism benchmark evidence manifest.",
        mechanism_evidence.main,
    ),
    "comparison-hashes": (
        "Generate hash-only mechanism comparison evidence.",
        comparison_hashes.main,
    ),
    "benchmark-execution-admission": (
        "Evaluate benchmark execution admission evidence.",
        benchmark_execution_admission.main,
    ),
    "debris-admission": (
        "Evaluate debris criteria admission evidence.",
        debris_admission.main,
    ),
    "selected-debris-case-admission": (
        "Evaluate selected debris case admission evidence.",
        selected_debris_case_admission.main,
    ),
    "selected-debris-case-packet": (
        "Build the selected debris case candidate packet.",
        selected_debris_case_packet.main,
    ),
    "spreadsheet-recalculation-admission": (
        "Evaluate spreadsheet recalculation admission evidence.",
        spreadsheet_recalculation_admission.main,
    ),
    "spreadsheet-replacement-tolerance": (
        "Evaluate spreadsheet replacement/tolerance admission evidence.",
        spreadsheet_replacement_tolerance.main,
    ),
    "spreadsheet-lineage-tolerance-packet": (
        "Build the spreadsheet lineage/tolerance review packet.",
        spreadsheet_lineage_tolerance_packet.main,
    ),
}


def _print_help() -> None:
    print("usage: damage_model_benchmark_evidence.py <command> [options]\n")
    print("Damage-model benchmark evidence commands:\n")
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
