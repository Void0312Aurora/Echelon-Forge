#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.diagnostics.benchmark_registry import BENCHMARK_FAMILIES, load_benchmark_entrypoint


def _family_choices_text() -> str:
    rows = []
    for name, family in sorted(BENCHMARK_FAMILIES.items()):
        rows.append(f"  {name}: {family.description}")
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified benchmark CLI for diagnostics families.",
        epilog="Available benchmark families:\n" + _family_choices_text(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--family", required=True, choices=sorted(BENCHMARK_FAMILIES.keys()))
    parser.add_argument(
        "--family-help",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show help for the selected benchmark family and exit.",
    )
    args, forwarded = parser.parse_known_args()

    sys.argv = [sys.argv[0], *(["--help"] if bool(args.family_help) else forwarded)]
    entrypoint = load_benchmark_entrypoint(str(args.family))
    return int(entrypoint())


if __name__ == "__main__":
    raise SystemExit(main())
