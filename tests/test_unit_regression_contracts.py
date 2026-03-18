#!/usr/bin/env python3

from __future__ import annotations

import glob
import os
import subprocess
import sys


def main() -> int:
    from python.testing.runtime import ensure_repo_imports, resolve_repo_path

    repo_root = ensure_repo_imports()

    spec_paths = sorted(glob.glob(resolve_repo_path("tests", "contracts", "unit", "**", "*.json"), recursive=True))
    if not spec_paths:
        print("FAIL: no unit regression contracts found")
        return 1

    pythonpath_parts = [resolve_repo_path("build"), repo_root]
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    child_env = dict(os.environ)
    child_env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    runner = resolve_repo_path("tools", "run_scenario_contract.py")

    for spec_path in spec_paths:
        proc = subprocess.run(
            [sys.executable, runner, "--spec", spec_path],
            cwd=repo_root,
            env=child_env,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        if proc.returncode != 0:
            if not stdout and not stderr:
                print(f"FAIL: {spec_path}: contract subprocess exited with code {proc.returncode}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
