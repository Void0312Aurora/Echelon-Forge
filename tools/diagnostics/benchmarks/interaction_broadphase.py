"""Reproducible CPU/GPU interaction-broadphase benchmark matrix."""

from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROBE = REPO_ROOT / "build-gpu" / "ef_gpu_interaction_broadphase_phase0_probe"


def _csv_ints(value: str) -> list[int]:
  values = [int(part.strip()) for part in value.split(",") if part.strip()]
  if not values or any(item <= 0 for item in values):
    raise argparse.ArgumentTypeError("expected a comma-separated list of positive integers")
  return values


def _csv_floats(value: str) -> list[float]:
  values = [float(part.strip()) for part in value.split(",") if part.strip()]
  if not values or any(item <= 0 for item in values):
    raise argparse.ArgumentTypeError("expected a comma-separated list of positive floats")
  return values


def _find_probe(path: str | None) -> Path:
  candidate = Path(path) if path else DEFAULT_PROBE
  if candidate.is_file():
    return candidate
  if os.name == "nt" and candidate.with_suffix(".exe").is_file():
    return candidate.with_suffix(".exe")
  raise FileNotFoundError(
    f"native broadphase probe not found at {candidate}; build ef_gpu_interaction_broadphase_phase0_probe first"
  )


def _number(output: str, label: str) -> float | None:
  match = re.search(rf"^{re.escape(label)}:\s*([-+0-9.eE]+)", output, flags=re.MULTILINE)
  return float(match.group(1)) if match else None


def _integer(output: str, label: str) -> int | None:
  value = _number(output, label)
  return None if value is None else int(value)


def _text(output: str, label: str) -> str | None:
  match = re.search(rf"^{re.escape(label)}:\s*(.+)$", output, flags=re.MULTILINE)
  return match.group(1).strip() if match else None


def _run_case(
  probe: Path,
  worlds: int,
  entities: int,
  queries: int,
  range_km: float,
  cell_km: float,
  seed: int,
) -> dict[str, Any]:
  command = [
    str(probe),
    "--worlds", str(worlds),
    "--entities", str(entities),
    "--queries", str(queries),
    "--cell-size", str(cell_km * 1000.0),
    "--query-range-km", str(range_km),
    "--seed", str(seed),
  ]
  completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
  output = f"{completed.stdout}\n{completed.stderr}"
  row: dict[str, Any] = {
    "worlds": worlds,
    "entities_per_world": entities,
    "queries_per_world": queries,
    "range_km": range_km,
    "cell_km": cell_km,
    "seed": seed,
    "exit_code": completed.returncode,
    "cuda_built": _text(output, "CUDA built"),
    "cuda_runtime_available": _text(output, "CUDA runtime available"),
    "cuda_device_count": _integer(output, "CUDA device count"),
    "device": _text(output, "Active device"),
    "cpu_ms": _number(output, "CPU exact reference"),
    "gpu_host_ms": _number(output, "GPU host-readback"),
    "missing_pairs": _integer(output, "Missing reference pairs"),
    "queries_with_miss": _integer(output, "Queries with any miss"),
    "overflow_buckets": _integer(output, "Overflow buckets"),
    "overflow_queries": _integer(output, "Overflow queries"),
  }
  row["gpu_exercised"] = (
    row["cuda_runtime_available"] == "yes"
    and row["gpu_host_ms"] is not None
    and row["gpu_host_ms"] > 0.0
  )
  row["superset_ok"] = row["missing_pairs"] == 0
  row["raw_output"] = output
  return row


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--probe", help="path to ef_gpu_interaction_broadphase_phase0_probe")
  parser.add_argument("--output", type=Path, required=True, help="JSON result path")
  parser.add_argument("--worlds", type=_csv_ints, default=[1, 4, 16])
  parser.add_argument("--entities", type=_csv_ints, default=[8, 32, 128, 512, 2048])
  parser.add_argument("--queries", type=_csv_ints, default=[1, 8, 32, 128])
  parser.add_argument("--ranges-km", type=_csv_floats, default=[1.0, 10.0, 50.0, 100.0, 300.0])
  parser.add_argument("--cells-km", type=_csv_floats, default=[1.0, 2.0, 5.0, 10.0])
  parser.add_argument("--seed", type=int, default=7)
  parser.add_argument("--require-cuda", action="store_true", help="fail if any case did not execute CUDA")
  args = parser.parse_args()

  probe = _find_probe(args.probe)
  rows = []
  for index, (worlds, entities, queries, range_km, cell_km) in enumerate(
    itertools.product(args.worlds, args.entities, args.queries, args.ranges_km, args.cells_km),
    start=1,
  ):
    row = _run_case(probe, worlds, entities, queries, range_km, cell_km, args.seed + index)
    rows.append(row)
    print(json.dumps({key: value for key, value in row.items() if key != "raw_output"}, sort_keys=True))

  payload = {
    "schema_version": 1,
    "benchmark": "interaction_broadphase",
    "probe": str(probe),
    "cases": rows,
    "case_count": len(rows),
  }
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  if any(not row["superset_ok"] for row in rows):
    return 2
  if args.require_cuda and any(not row["gpu_exercised"] for row in rows):
    return 3
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
