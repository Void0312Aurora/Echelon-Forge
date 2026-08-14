#!/usr/bin/env python3
from __future__ import annotations

import argparse

from tools.diagnostics.common import build_mode_dispatch_parser, dispatch_mode_module
from tools.diagnostics.flight_trajectory import runway_drift_sweep, takeoff_to_landing


DEFAULT_MODE = "takeoff_to_landing"
MODE_MODULES = {
    "runway_drift_sweep": runway_drift_sweep,
    "takeoff_to_landing": takeoff_to_landing,
}
VALID_MODES = set(MODE_MODULES)


def build_arg_parser() -> argparse.ArgumentParser:
    return build_mode_dispatch_parser(
        description="Flight trajectory diagnostic dispatcher.",
        valid_modes=VALID_MODES,
        default=DEFAULT_MODE,
        epilog=(
            "Use --mode takeoff_to_landing for single-episode route/landing trajectory export, "
            "or --mode runway_drift_sweep for runway ground-roll drift sweeps."
        ),
    )


def main(argv: list[str] | None = None) -> int:
    return dispatch_mode_module(argv, modules=MODE_MODULES, default=DEFAULT_MODE)


if __name__ == "__main__":
    raise SystemExit(main())
