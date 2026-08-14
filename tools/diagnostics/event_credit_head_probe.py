#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from tools.diagnostics.common import (
    build_mode_dispatch_parser,
    extract_mode,
    strip_mode_args,
)
from tools.diagnostics.event_credit_head import offline_fit, online_update
from tools.diagnostics.event_credit_head.offline_fit import _to_serializable


DEFAULT_MODE = "offline_fit"
VALID_MODES = {"offline_fit", "online_update"}


def build_arg_parser() -> argparse.ArgumentParser:
    return build_mode_dispatch_parser(
        description="Event-credit head diagnostic probe.",
        valid_modes=VALID_MODES,
        default=DEFAULT_MODE,
        epilog=(
            "Use --mode offline_fit for supervised fixed-batch fitting, or "
            "--mode online_update for update-path isolation."
        ),
    )


# The sibling --mode routers hand the stripped argv to a module ``main`` via
# ``dispatch_mode_module``; here each mode module exposes ``run_probe(args)``
# and the JSON payload is serialized by this entrypoint, so only the argv-side
# helpers are shared.
def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    mode = extract_mode(raw_argv, valid_modes=VALID_MODES, default=DEFAULT_MODE)
    mode_argv = strip_mode_args(raw_argv)
    if mode == "online_update":
        args = online_update.build_arg_parser().parse_args(mode_argv)
        payload = online_update.run_probe(args)
    else:
        args = offline_fit.build_arg_parser().parse_args(mode_argv)
        payload = offline_fit.run_probe(args)
    print(json.dumps(_to_serializable(payload), indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
