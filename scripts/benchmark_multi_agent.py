#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.runtime_bootstrap import configure_repo_imports


configure_repo_imports()

from python.rl.support.multi_agent_benchmark import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
