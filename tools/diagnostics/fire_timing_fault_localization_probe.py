#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

_REPO_ROOT_HINT = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()
from tools.diagnostics.common import build_mode_dispatch_parser, dispatch_mode_module
from tools.diagnostics.fire_timing_fault_localization import (
    chain_breakpoint,
    learnability_audit,
    real_update,
    structural_toy,
    window_position_sweep,
)


DEFAULT_MODE = "chain_breakpoint"
MODE_MODULES = {
    "chain_breakpoint": chain_breakpoint,
    "learnability_audit": learnability_audit,
    "real_update": real_update,
    "structural_toy": structural_toy,
    "window_position_sweep": window_position_sweep,
}
VALID_MODES = set(MODE_MODULES)


def build_arg_parser() -> argparse.ArgumentParser:
    return build_mode_dispatch_parser(
        description="Fire-timing fault-localization diagnostic probe.",
        valid_modes=VALID_MODES,
        default=DEFAULT_MODE,
        epilog=(
            "Use --mode structural_toy for the abstract grouped-stopping toy, "
            "--mode real_update for the real update-path probe, or "
            "--mode chain_breakpoint for fixed-batch breakpoint attribution, or "
            "--mode learnability_audit for oracle fire-timing learnability checks, or "
            "--mode window_position_sweep for legal-window launch-position effect sweeps."
        ),
    )


def main(argv: list[str] | None = None) -> int:
    return dispatch_mode_module(argv, modules=MODE_MODULES, default=DEFAULT_MODE)


if __name__ == "__main__":
    raise SystemExit(main())
