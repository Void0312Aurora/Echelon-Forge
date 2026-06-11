#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from types import ModuleType

from tools.diagnostics.fire_timing_fault_localization import chain_breakpoint, real_update, structural_toy


VALID_MODES = {"chain_breakpoint", "real_update", "structural_toy"}


def _extract_mode(argv: list[str]) -> str:
    for index, arg in enumerate(argv):
        if arg == "--mode" and index + 1 < len(argv):
            value = str(argv[index + 1]).strip()
            return value if value in VALID_MODES else "chain_breakpoint"
        if arg.startswith("--mode="):
            value = str(arg.split("=", 1)[1]).strip()
            return value if value in VALID_MODES else "chain_breakpoint"
    return "chain_breakpoint"


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
    parser = argparse.ArgumentParser(description="Fire-timing fault-localization diagnostic probe.")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="chain_breakpoint")
    parser.epilog = (
        "Use --mode structural_toy for the abstract grouped-stopping toy, "
        "--mode real_update for the real update-path probe, or "
        "--mode chain_breakpoint for fixed-batch breakpoint attribution."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    mode = _extract_mode(raw_argv)
    mode_argv = _remove_mode(raw_argv)
    if mode == "structural_toy":
        return _run_module(structural_toy, mode_argv)
    if mode == "real_update":
        return _run_module(real_update, mode_argv)
    return _run_module(chain_breakpoint, mode_argv)


if __name__ == "__main__":
    raise SystemExit(main())
