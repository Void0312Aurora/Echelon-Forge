#!/usr/bin/env python3
"""Commit one signed local P5-D RolloutDecision slot.

The command is intentionally explicit: it accepts a fully materialized
authority payload and a key file, signs only that payload, and performs a
durable compare-and-swap through ``FileRolloutDecisionStore``.  It cannot
select a remote or multi-process topology and it never changes the default
development runtime path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.rl.runtime.rollout_gate import FileRolloutDecisionStore
from python.rl.runtime.rollout_gate import RolloutAdmissionError
from python.rl.runtime.rollout_gate import build_rollout_decision_envelope


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--writer-id", required=True)
    parser.add_argument("--expected-decision-sha256")
    parser.add_argument("--admissions-open", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--writer-advancement-frozen", action=argparse.BooleanOptionalAction, default=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload: Any = json.loads(args.payload.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RolloutAdmissionError("rollout payload file must contain an object")
        signing_key = args.key_file.read_bytes()
        envelope = build_rollout_decision_envelope(
            payload,
            key_id=args.key_id,
            signing_key=signing_key,
        )
        admission = FileRolloutDecisionStore(
            args.slot,
            writer_id=args.writer_id,
            signing_key=signing_key,
            key_id=args.key_id,
        ).commit(
            envelope,
            admissions_open=bool(args.admissions_open),
            writer_advancement_frozen=bool(args.writer_advancement_frozen),
            expected_decision_sha256=args.expected_decision_sha256,
        )
    except (OSError, json.JSONDecodeError, RolloutAdmissionError) as error:
        print(f"rollout decision commit rejected: {error}", file=sys.stderr)
        return 1
    print(json.dumps({
        "slot": str(admission.path),
        "decision_id": admission.envelope["payload"]["decision_id"],
        "state": admission.state,
        "decision_sha256": admission.decision_sha256,
        "production_authorized": admission.production_authorized,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
