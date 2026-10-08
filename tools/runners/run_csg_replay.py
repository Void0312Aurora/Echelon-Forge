#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture or verify an agent-free native CSG replay artifact")
    parser.add_argument("--scenario", required=True, help="CSG scenario JSON path")
    parser.add_argument("--output", required=True, help="Replay artifact JSON path")
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--verify", action="store_true", help="Verify the existing artifact after capture")
    args = parser.parse_args()

    from python.runtime_bootstrap import ensure_repo_imports

    ensure_repo_imports()
    from python.scenario.runtime.csg_replay import write_csg_replay_artifact

    artifact = write_csg_replay_artifact(
        args.scenario,
        args.output,
        seed=int(args.seed),
        max_steps=args.max_steps,
    )
    print(
        f"WROTE: {args.output}: {len(artifact['frames'])} frames, "
        f"{len(artifact['entity_roster'])} entities, duration={artifact['duration_s']:.1f}s"
    )
    if not args.verify:
        return 0

    from python.testing.contracts.unit.comm import _check_naval_csg_replay

    ok, message = _check_naval_csg_replay(
        {
            "replay": args.output,
            "scenario": args.scenario,
            "seed": int(args.seed),
            "max_steps": int(artifact["max_steps"]),
        }
    )
    print(f"{'PASS' if ok else 'FAIL'}: {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
