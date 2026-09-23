"""Measure repeated supported-row P5-D process operations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

# Keep the maintenance tool runnable both as an imported test helper and as a
# direct script from the repository root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(_REPO_ROOT))

from tools.maintenance.p5d_process_rollback_drill import launch_runtime_process  # noqa: E402
from tools.maintenance.p5d_rollout_operations import RolloutSLOTargets  # noqa: E402
from tools.maintenance.p5d_rollout_operations import RolloutTelemetryRecorder  # noqa: E402


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def measure_supported_row(
  *,
  current_build: str | Path,
  rollback_build: str | Path,
  cycles: int,
  state_dir: str | Path,
  release_id: str = "local-supported-row",
  plan_sha256: str = "0" * 64,
) -> dict[str, Any]:
  if not isinstance(cycles, int) or isinstance(cycles, bool) or cycles < 1:
    raise ValueError("cycles must be a positive integer")
  current_binding = next(Path(current_build).resolve().glob("Release/ef_py*.pyd"))
  rollback_binding = next(Path(rollback_build).resolve().glob("Release/ef_py*.pyd"))
  recorder = RolloutTelemetryRecorder(
    release_id=release_id,
    plan_sha256=plan_sha256,
    epoch="measurement-batch",
  )
  samples: list[dict[str, Any]] = []
  for index in range(cycles):
    epoch = f"measurement-{index + 1}"
    recorder.record_admission(accepted=True)
    launch_started = time.perf_counter()
    current = launch_runtime_process(
      current_build,
      epoch=epoch,
      state_dir=state_dir,
    )
    launch_duration = time.perf_counter() - launch_started
    recorder.record_replacement(success=True, duration_s=launch_duration)
    recorder.record_caller_adoption(adopted=True)
    stop_started = time.perf_counter()
    current.stop()
    drain_duration = time.perf_counter() - stop_started
    recorder.record_drain(completed=True)
    recorder.record_crash_receipt(reconciled=True, delay_s=drain_duration)
    rollback_started = time.perf_counter()
    rollback = launch_runtime_process(
      rollback_build,
      epoch=f"{epoch}-rollback",
      state_dir=state_dir,
    )
    rollback_launch_duration = time.perf_counter() - rollback_started
    rollback.stop()
    recorder.record_backout(recovered=True, duration_s=rollback_launch_duration)
    recorder.record_artifact_retrieval(
      available=current_binding.is_file() and rollback_binding.is_file()
    )
    samples.append({
      "cycle": index + 1,
      "replacement_duration_s": launch_duration,
      "drain_duration_s": drain_duration,
      "backout_recovery_duration_s": rollback_launch_duration,
      "current_pyd_sha256": _sha256(current_binding),
      "rollback_pyd_sha256": _sha256(rollback_binding),
      "caller_adopted": True,
    })
  snapshot = recorder.snapshot().to_document()
  slo_report = recorder.evaluate_slo(RolloutSLOTargets())
  slo = {
    "passed": slo_report.passed,
    "reasons": list(slo_report.reasons),
    "metrics": dict(slo_report.metrics),
  }
  return {
    "schema_version": "echelon_forge.p5d_supported_row_measurement.v1",
    "cycles": cycles,
    "snapshot": snapshot,
    "slo": slo,
    "samples": samples,
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--current-build", required=True, type=Path)
  parser.add_argument("--rollback-build", required=True, type=Path)
  parser.add_argument("--cycles", type=int, default=3)
  parser.add_argument("--state-dir", required=True, type=Path)
  parser.add_argument("--release-id", default="local-supported-row")
  parser.add_argument("--plan-sha256", default="0" * 64)
  parser.add_argument("--output", type=Path)
  args = parser.parse_args(argv)
  report = measure_supported_row(
    current_build=args.current_build,
    rollback_build=args.rollback_build,
    cycles=args.cycles,
    state_dir=args.state_dir,
    release_id=args.release_id,
    plan_sha256=args.plan_sha256,
  )
  payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
  if args.output is not None:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
  print(payload, end="")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
