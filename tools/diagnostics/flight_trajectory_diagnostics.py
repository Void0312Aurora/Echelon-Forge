#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from types import ModuleType

from tools.diagnostics.flight_trajectory import runway_drift_sweep, takeoff_to_landing


VALID_MODES = {"runway_drift_sweep", "takeoff_to_landing"}


def _extract_mode(argv: list[str]) -> str:
    for index, arg in enumerate(argv):
        if arg == "--mode" and index + 1 < len(argv):
            value = str(argv[index + 1]).strip()
            return value if value in VALID_MODES else "takeoff_to_landing"
        if arg.startswith("--mode="):
            value = str(arg.split("=", 1)[1]).strip()
            return value if value in VALID_MODES else "takeoff_to_landing"
    return "takeoff_to_landing"


def _remove_mode(argv: list[str]) -> list[str]:
    out: list[str] = []
    skip_next = False
    for arg in argv:
        if skip_next:
            skip_next = False
            continue
        if arg == "--mode":
            skip_next = True
            continue
        if arg.startswith("--mode="):
            continue
        out.append(arg)
    return out


def _run_module(module: ModuleType, argv: list[str]) -> int:
    old_argv = sys.argv
    try:
        sys.argv = [old_argv[0], *argv]
        return int(module.main())
    finally:
        sys.argv = old_argv


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flight trajectory diagnostic dispatcher.")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="takeoff_to_landing")
    parser.epilog = (
        "Use --mode takeoff_to_landing for single-episode route/landing trajectory export, "
        "or --mode runway_drift_sweep for runway ground-roll drift sweeps."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    mode = _extract_mode(raw_argv)
    mode_argv = _remove_mode(raw_argv)
    if mode == "runway_drift_sweep":
        return _run_module(runway_drift_sweep, mode_argv)
    return _run_module(takeoff_to_landing, mode_argv)


if __name__ == "__main__":
    raise SystemExit(main())
