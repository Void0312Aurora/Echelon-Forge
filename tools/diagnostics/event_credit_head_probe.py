#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from tools.diagnostics.event_credit_head import offline_fit, online_update
from tools.diagnostics.event_credit_head.offline_fit import _to_serializable


VALID_MODES = {"offline_fit", "online_update"}


def _extract_mode(argv: list[str]) -> str:
    for index, arg in enumerate(argv):
        if arg == "--mode" and index + 1 < len(argv):
            value = str(argv[index + 1]).strip()
            return value if value in VALID_MODES else "offline_fit"
        if arg.startswith("--mode="):
            value = str(arg.split("=", 1)[1]).strip()
            return value if value in VALID_MODES else "offline_fit"
    return "offline_fit"


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


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Event-credit head diagnostic probe.")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="offline_fit")
    parser.epilog = (
        "Use --mode offline_fit for supervised fixed-batch fitting, or "
        "--mode online_update for update-path isolation."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    mode = _extract_mode(raw_argv)
    mode_argv = _remove_mode(raw_argv)
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
