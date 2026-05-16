#!/usr/bin/env python3

from __future__ import annotations

import os
import sys


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from tests.runners.test_contract_batches import main as run_batch_main

    if len(sys.argv) <= 1:
        sys.argv = [sys.argv[0], "--default-group", "sim_kernel"]
    return int(run_batch_main())


if __name__ == "__main__":
    raise SystemExit(main())
