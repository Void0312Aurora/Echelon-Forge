#!/usr/bin/env python3
"""Report whether the active environment can import the RL runtime stack.

Shared by ``cmo_env.sh validate-rl`` and ``cmo_env.ps1 validate-rl`` so both
shells report the same modules, the same message shapes, and the same exit
code. Exit code 6 means at least one required import failed.
"""

from __future__ import annotations

import importlib
import sys


REQUIRED_MODULES = ("ef_py", "gymnasium", "stable_baselines3", "torch")
IMPORT_FAILURE_EXIT_CODE = 6


def main() -> int:
  failed = False

  for name in REQUIRED_MODULES:
    try:
      module = importlib.import_module(name)
    except Exception as exc:
      failed = True
      print(f"[cmo_env] import failed: {name}: {exc}", file=sys.stderr)
      continue
    version = getattr(module, "__version__", None)
    location = getattr(module, "__file__", None)
    detail = []
    if version:
      detail.append(f"version={version}")
    if location:
      detail.append(f"file={location}")
    suffix = f" ({', '.join(detail)})" if detail else ""
    print(f"[cmo_env] import ok: {name}{suffix}")

  if failed:
    print(
      "[cmo_env] RL validation failed; install the `.[rl]` extra or the "
      "equivalent direct dependencies, and rebuild ef_py if that import failed.",
      file=sys.stderr,
    )
    return IMPORT_FAILURE_EXIT_CODE

  print("[cmo_env] RL validation ok")
  return 0


if __name__ == "__main__":
  sys.exit(main())
