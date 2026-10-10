"""Reproducible CPU/GPU interaction-broadphase benchmark matrix."""

from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import statistics
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


def _run_probe_once(
  probe: Path,
  worlds: int,
  entities: int,
  queries: int,
  range_km: float,
  cell_km: float,
  seed: int,
  timeout_s: float,
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
  try:
    completed = subprocess.run(
      command,
      cwd=REPO_ROOT,
      text=True,
      capture_output=True,
      check=False,
      timeout=timeout_s,
    )
  except subprocess.TimeoutExpired as exc:
    output = f"{exc.stdout or ''}\n{exc.stderr or ''}"
    return {
      "exit_code": None,
      "timed_out": True,
      "timeout_s": timeout_s,
      "raw_output": output,
    }
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
    "gpu_device_ms": _number(output, "GPU device-resident"),
    "missing_pairs": _integer(output, "Missing reference pairs"),
    "queries_with_miss": _integer(output, "Queries with any miss"),
    "overflow_buckets": _integer(output, "Overflow buckets"),
    "overflow_queries": _integer(output, "Overflow queries"),
    "timed_out": False,
    "timeout_s": timeout_s,
  }
  row["gpu_exercised"] = (
    row["cuda_runtime_available"] == "yes"
    and row["gpu_host_ms"] is not None
    and row["gpu_host_ms"] > 0.0
  )
  row["superset_ok"] = row["missing_pairs"] == 0
  row["raw_output"] = output
  return row


def _timing_summary(samples: list[dict[str, Any]], field: str) -> dict[str, float | int]:
  values = [float(sample[field]) for sample in samples if sample.get(field) is not None]
  if not values:
    return {"sample_count": 0}
  return {
    "sample_count": len(values),
    "min_ms": min(values),
    "max_ms": max(values),
    "mean_ms": statistics.fmean(values),
    "stdev_ms": statistics.pstdev(values) if len(values) > 1 else 0.0,
  }


def _run_case(
  probe: Path,
  worlds: int,
  entities: int,
  queries: int,
  range_km: float,
  cell_km: float,
  seed: int,
  repetitions: int,
  timeout_s: float,
) -> dict[str, Any]:
  samples = [
    _run_probe_once(
      probe,
      worlds,
      entities,
      queries,
      range_km,
      cell_km,
      seed + repetition,
      timeout_s,
    )
    for repetition in range(repetitions)
  ]
  completed_samples = [sample for sample in samples if not sample.get("timed_out")]
  reference = next((sample for sample in completed_samples if sample.get("exit_code") == 0), samples[0])
  row: dict[str, Any] = {
    "worlds": worlds,
    "entities_per_world": entities,
    "queries_per_world": queries,
    "range_km": range_km,
    "cell_km": cell_km,
    "seed": seed,
    "sample_count": repetitions,
    "successful_sample_count": len(completed_samples),
    "timed_out_sample_count": sum(1 for sample in samples if sample.get("timed_out")),
    "exit_codes": [sample.get("exit_code") for sample in samples],
    "cuda_built": reference.get("cuda_built"),
    "cuda_runtime_available": reference.get("cuda_runtime_available"),
    "cuda_device_count": reference.get("cuda_device_count"),
    "device": reference.get("device"),
    "missing_pairs": reference.get("missing_pairs"),
    "queries_with_miss": reference.get("queries_with_miss"),
    "overflow_buckets": reference.get("overflow_buckets"),
    "overflow_queries": reference.get("overflow_queries"),
    "timing_ms": {
      field: _timing_summary(completed_samples, field)
      for field in ("cpu_ms", "gpu_host_ms", "gpu_device_ms")
    },
    "samples": [
      {key: value for key, value in sample.items() if key != "raw_output"}
      for sample in samples
    ],
  }
  row["gpu_exercised"] = bool(completed_samples) and all(
    sample.get("cuda_runtime_available") == "yes"
    and sample.get("gpu_host_ms", 0.0) > 0.0
    for sample in completed_samples
  )
  row["superset_ok"] = bool(completed_samples) and all(
    sample.get("exit_code") == 0 and sample.get("missing_pairs") == 0
    for sample in completed_samples
  ) and not any(sample.get("timed_out") for sample in samples)
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
  parser.add_argument("--repetitions", type=int, default=3, help="samples per matrix cell")
  parser.add_argument("--timeout-s", type=float, default=10.0, help="per-sample timeout")
  parser.add_argument("--require-cuda", action="store_true", help="fail if any case did not execute CUDA")
  args = parser.parse_args()

  if args.repetitions <= 0:
    parser.error("--repetitions must be positive")
  if args.timeout_s <= 0:
    parser.error("--timeout-s must be positive")

  probe = _find_probe(args.probe)
  rows = []
  for index, (worlds, entities, queries, range_km, cell_km) in enumerate(
    itertools.product(args.worlds, args.entities, args.queries, args.ranges_km, args.cells_km),
    start=1,
  ):
    row = _run_case(
      probe,
      worlds,
      entities,
      queries,
      range_km,
      cell_km,
      args.seed + index * args.repetitions,
      args.repetitions,
      args.timeout_s,
    )
    rows.append(row)
    print(json.dumps({key: value for key, value in row.items() if key != "raw_output"}, sort_keys=True))

  payload = {
    "schema_version": 2,
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
