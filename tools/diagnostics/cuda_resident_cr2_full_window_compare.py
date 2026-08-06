from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


COMMON_KEYS = ("schema_version", "surface_id", "trace_signature", "operations")


def _run_probe(path: Path, database: str) -> dict[str, Any]:
    completed = subprocess.run(
        [str(path), "--database", database],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"probe failed ({path}, exit={completed.returncode}): {completed.stderr.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"probe stdout is not pure JSON ({path}): {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"probe payload is not an object: {path}")
    return payload


def _common_projection(payload: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in COMMON_KEYS if key not in payload]
    if missing:
        raise RuntimeError(f"probe payload missing keys {missing!r}")
    if payload.get("completed") is not True or payload.get("failure") is not None:
        raise RuntimeError(f"probe did not complete cleanly: {payload!r}")
    operations = payload["operations"]
    if not isinstance(operations, list):
        raise RuntimeError("probe operations must be a list")
    return {key: payload[key] for key in COMMON_KEYS}


def compare(cpu: dict[str, Any], cuda: dict[str, Any]) -> dict[str, Any]:
    cpu_common = _common_projection(cpu)
    cuda_common = _common_projection(cuda)
    if cpu_common != cuda_common:
        raise RuntimeError("CPU/CUDA common surface or operation projection diverged")
    if cpu.get("lane") != "cpu_reference" or cuda.get("lane") != "cuda_resident":
        raise RuntimeError("probe lane labels are not explicit")
    if cpu.get("backend_id") == cuda.get("backend_id"):
        raise RuntimeError("CPU and CUDA backend identifiers unexpectedly match")
    return {
        "surface_id": cpu_common["surface_id"],
        "trace_signature": cpu_common["trace_signature"],
        "operation_count": len(cpu_common["operations"]),
        "cpu_lane": cpu["lane"],
        "cuda_lane": cuda["lane"],
        "common_sequence_equal": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", type=Path, required=True, help="CPU probe executable")
    parser.add_argument("--cuda", type=Path, required=True, help="CUDA probe executable")
    parser.add_argument("--database", default="examples/config/database")
    args = parser.parse_args()
    summary = compare(_run_probe(args.cpu, args.database), _run_probe(args.cuda, args.database))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
