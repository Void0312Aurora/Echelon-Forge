#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path
from tools.diagnostics.benchmark_registry import BENCHMARK_FAMILIES
from tools.diagnostics.common import load_json_config, write_json_output


ensure_repo_imports()


def _resolve_repo_or_abs(path: str) -> str:
    raw = str(path).strip()
    if os.path.isabs(raw):
        return raw
    candidate = resolve_repo_path(raw)
    return candidate if os.path.exists(candidate) else os.path.abspath(raw)


def _normalize_job_args(args: list[Any] | None) -> list[str]:
    return [str(item) for item in list(args or [])]


def _run_job(job: dict[str, Any], *, shared_args: list[str], python_exe: str) -> dict[str, Any]:
    name = str(job.get("name", "") or "").strip()
    family_name = str(job.get("family", "") or "").strip()
    if not name:
        raise ValueError("benchmark job is missing non-empty 'name'")
    if not family_name:
        raise ValueError(f"benchmark job {name!r} must provide non-empty 'family'")

    if family_name not in BENCHMARK_FAMILIES:
        raise ValueError(f"benchmark job {name!r} references unknown family {family_name!r}")
    benchmark_cli = _resolve_repo_or_abs("tools/diagnostics/benchmark.py")
    cmd = [
        python_exe,
        benchmark_cli,
        "--family",
        family_name,
        *_normalize_job_args(shared_args),
        *_normalize_job_args(job.get("args")),
    ]
    module_path = BENCHMARK_FAMILIES[family_name].module_path

    started_at = time.time()
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    elapsed_s = time.perf_counter() - t0
    stdout = proc.stdout or ""
    return {
        "name": name,
        "family": family_name,
        "module": module_path,
        "args": _normalize_job_args(job.get("args")),
        "command": cmd,
        "returncode": int(proc.returncode),
        "ok": bool(proc.returncode == 0),
        "started_at_unix_s": float(started_at),
        "elapsed_s": float(elapsed_s),
        "stdout": stdout,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configuration-driven benchmark suite runner for maintained diagnostics."
    )
    parser.add_argument("--config", required=True, help="Benchmark suite JSON config.")
    parser.add_argument("--json-out", default="", help="Optional path to write suite results as JSON.")
    parser.add_argument(
        "--fail-fast",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Stop after the first failed benchmark job.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to launch benchmark jobs. Default: current interpreter.",
    )
    args = parser.parse_args()

    config_path = _resolve_repo_or_abs(str(args.config))
    config = load_json_config(config_path)
    suite_name = str(config.get("name", Path(config_path).stem))
    shared_args = _normalize_job_args(config.get("shared_args"))
    jobs = list(config.get("jobs", []) or [])
    if not jobs:
        raise ValueError(f"benchmark suite {config_path!r} has no jobs")

    rows: list[dict[str, Any]] = []
    for job in jobs:
        if not isinstance(job, dict):
            raise TypeError("each benchmark suite job must be a JSON object")
        row = _run_job(job, shared_args=shared_args, python_exe=str(args.python))
        rows.append(row)
        status = "OK" if row["ok"] else "FAIL"
        print(f"[{status}] {row['name']}  {row['elapsed_s']:.2f}s")
        if row["stdout"].strip():
            print(row["stdout"].rstrip())
        if bool(args.fail_fast) and not bool(row["ok"]):
            break

    payload = {
        "suite_name": suite_name,
        "config": config_path,
        "python": str(args.python),
        "shared_args": shared_args,
        "job_count": int(len(rows)),
        "success_count": int(sum(1 for row in rows if bool(row["ok"]))),
        "failure_count": int(sum(1 for row in rows if not bool(row["ok"]))),
        "rows": rows,
    }
    write_json_output(str(args.json_out), payload)
    return 0 if payload["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
