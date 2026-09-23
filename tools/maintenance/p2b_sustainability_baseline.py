"""Collect a repeatable P2-B governance and supported-row baseline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(_REPO_ROOT))

from tools.maintenance.p5d_measure_supported_row import measure_supported_row  # noqa: E402


_PASSED = re.compile(r"(?P<count>\d+) passed")
_FAILED = re.compile(r"(?P<count>\d+) failed")
_SKIPPED = re.compile(r"(?P<count>\d+) skipped")
_XFAILED = re.compile(r"(?P<count>\d+) xfailed")

_MANIFESTS = (
  Path("tests/smoke/ci_smoke_suite.json"),
  Path("tests/smoke/ci_contract_suite.json"),
  Path("tests/suites/architecture_guard_suite.json"),
  Path("tests/suites/governance_audit_suite.json"),
)
_EVIDENCE_PATHS = (
  Path("docs/architecture/work/active/long_horizon_architecture_governance/evidence/p2_control_lifecycle_inventory_20260923.md"),
  Path("docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_supported_row_measurement_20260923.md"),
  Path("docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_real_process_package_rollback_20260923.md"),
)
_CHECKS: tuple[tuple[str, tuple[str, ...]], ...] = (
  (
    "lifecycle_and_manifest",
    (
      "tests/architecture/governance/test_control_lifecycle_metadata.py",
      "tests/runners/test_pytest_suite_manifests.py",
    ),
  ),
  (
    "rollout_and_storage_guards",
    (
      "tests/architecture/runtime_host/test_p5d_rollout_operations.py",
      "tests/architecture/runtime_host/test_sqlite_rollout_admission.py",
    ),
  ),
  (
    "plan_and_authority_negative_guards",
    (
      "tests/architecture/composition/test_runtime_resolved_plan_contract.py",
      "tests/architecture/composition/test_runtime_authority_contracts.py",
    ),
  ),
  (
    "candidate_teardown_and_state_transfer_guards",
    (
      "tests/architecture/runtime_host/test_runtime_kernel_candidate_contract.py",
      "tests/architecture/composition/test_runtime_host_candidate_contract.py",
      "tests/architecture/composition/test_runtime_state_transfer_candidate_contract.py",
    ),
  ),
)


def _parse_count(pattern: re.Pattern[str], output: str) -> int:
  matches = pattern.findall(output)
  return int(matches[-1]) if matches else 0


def _run_check(
  name: str,
  paths: Sequence[str],
  *,
  env: dict[str, str],
) -> dict[str, Any]:
  command = [sys.executable, "-m", "pytest", "-q", *paths]
  started = time.perf_counter()
  completed = subprocess.run(
    command,
    cwd=_REPO_ROOT,
    env=env,
    check=False,
    capture_output=True,
    text=True,
    encoding="utf-8",
  )
  duration = time.perf_counter() - started
  output = f"{completed.stdout}\n{completed.stderr}"
  return {
    "name": name,
    "command": " ".join(command),
    "passed": completed.returncode == 0,
    "returncode": completed.returncode,
    "duration_s": duration,
    "test_counts": {
      "passed": _parse_count(_PASSED, output),
      "failed": _parse_count(_FAILED, output),
      "skipped": _parse_count(_SKIPPED, output),
      "xfailed": _parse_count(_XFAILED, output),
    },
  }


def _load_controls() -> dict[str, Any]:
  controls: list[dict[str, Any]] = []
  for relative in _MANIFESTS:
    payload = json.loads((_REPO_ROOT / relative).read_text(encoding="utf-8"))
    for control in payload["control_lifecycle"]["controls"]:
      row = dict(control)
      row["manifest"] = relative.as_posix()
      controls.append(row)
  counts: dict[str, int] = {}
  for control in controls:
    kind = str(control["kind"])
    counts[kind] = counts.get(kind, 0) + 1
  return {
    "declared": len(controls),
    "by_kind": dict(sorted(counts.items())),
    "migratory_due_2027_04_01": sum(
      1 for control in controls
      if control["kind"] == "migratory" and str(control["expiry"]) < "2027-04-01"
    ),
  }


def _measure_evidence_retrieval() -> dict[str, Any]:
  rows: list[dict[str, Any]] = []
  for relative in _EVIDENCE_PATHS:
    path = _REPO_ROOT / relative
    if not path.is_file():
      rows.append({"path": relative.as_posix(), "available": False, "bytes": 0})
      continue
    payload = path.read_bytes()
    rows.append({
      "path": relative.as_posix(),
      "available": True,
      "bytes": len(payload),
      "sha256": hashlib.sha256(payload).hexdigest(),
    })
  available = sum(1 for row in rows if row["available"])
  return {
    "attempts": len(rows),
    "available": available,
    "availability_ratio": available / len(rows) if rows else 0.0,
    "bytes": sum(int(row["bytes"]) for row in rows),
    "rows": rows,
  }


def _measure_supported_row(
  *,
  current_build: Path,
  rollback_build: Path,
  runs: int,
  process_cycles: int,
) -> dict[str, Any]:
  reports: list[dict[str, Any]] = []
  for index in range(runs):
    with tempfile.TemporaryDirectory(prefix="echelon-forge-p2b-") as state_dir:
      reports.append(measure_supported_row(
        current_build=current_build,
        rollback_build=rollback_build,
        cycles=process_cycles,
        state_dir=state_dir,
        release_id=f"p2b-baseline-{index + 1}",
        plan_sha256="b" * 64,
      ))
  passed = sum(1 for report in reports if report["slo"]["passed"])
  samples = [sample for report in reports for sample in report["samples"]]
  snapshots = [report["snapshot"] for report in reports]
  return {
    "runs": runs,
    "cycles_per_run": process_cycles,
    "slo_pass_rate": passed / runs if runs else 0.0,
    "passed_runs": passed,
    "total_cycles": len(samples),
    "max_replacement_duration_s": max(
      (float(snapshot["max_durations_s"]["replacement"]) for snapshot in snapshots),
      default=0.0,
    ),
    "max_backout_recovery_s": max(
      (float(snapshot["max_durations_s"]["backout_recovery"]) for snapshot in snapshots),
      default=0.0,
    ),
    "replacement_success_rate": _ratio(
      snapshots, "replacement_successes", "replacement_attempts"
    ),
    "drain_completion_rate": _ratio(
      snapshots, "drain_completed", "drain_attempts"
    ),
    "caller_adoption_rate": _ratio(
      snapshots, "caller_adoptions", "caller_total"
    ),
    "artifact_availability_rate": _ratio_available(snapshots),
    "safety_events": {
      key: sum(int(snapshot["counters"][key]) for snapshot in snapshots)
      for key in (
        "stale_reference_rejections",
        "wrong_epoch_results",
        "duplicate_publications",
        "security_denials",
      )
    },
  }


def _ratio(snapshots: Sequence[dict[str, Any]], numerator: str, denominator: str) -> float:
  total_numerator = sum(int(snapshot["counters"][numerator]) for snapshot in snapshots)
  total_denominator = sum(int(snapshot["counters"][denominator]) for snapshot in snapshots)
  return total_numerator / total_denominator if total_denominator else 0.0


def _ratio_available(snapshots: Sequence[dict[str, Any]]) -> float:
  attempts = sum(int(snapshot["counters"]["artifact_retrieval_attempts"]) for snapshot in snapshots)
  failures = sum(int(snapshot["counters"]["artifact_retrieval_failures"]) for snapshot in snapshots)
  return (attempts - failures) / attempts if attempts else 0.0


def build_baseline(
  *,
  current_build: str | Path,
  rollback_build: str | Path,
  runs: int = 3,
  process_cycles: int = 1,
) -> dict[str, Any]:
  if not isinstance(runs, int) or isinstance(runs, bool) or runs < 1:
    raise ValueError("runs must be a positive integer")
  if not isinstance(process_cycles, int) or isinstance(process_cycles, bool) or process_cycles < 1:
    raise ValueError("process_cycles must be a positive integer")
  current = Path(current_build).resolve()
  rollback = Path(rollback_build).resolve()
  if "CMO_BUILD_DIR" not in os.environ:
    os.environ["CMO_BUILD_DIR"] = str(current)
  env = os.environ.copy()
  env.setdefault("CMO_BUILD_DIR", str(current))
  from tools.runners import audit_test_system

  checks: list[dict[str, Any]] = []
  for name, paths in _CHECKS:
    for _ in range(runs):
      checks.append(_run_check(name, paths, env=env))
  passing_checks = sum(1 for check in checks if check["passed"])
  evidence = _measure_evidence_retrieval()
  audit = audit_test_system.build_audit(
    pytest_smoke_suite=Path("tests/smoke/ci_smoke_suite.json"),
    contract_smoke_suite=Path("tests/smoke/ci_contract_suite.json"),
  )
  supported_row = _measure_supported_row(
    current_build=current,
    rollback_build=rollback,
    runs=runs,
    process_cycles=process_cycles,
  )
  total_check_runs = len(checks)
  return {
    "schema_version": "echelon_forge.p2b_sustainability_baseline.v1",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "owner": "cross-domain-architecture",
    "cadence": "three local repetitions per implementation batch; representative release cadence before P8",
    "environment": {
      "python": platform.python_version(),
      "platform": platform.platform(),
      "current_build": str(current),
      "rollback_build": str(rollback),
    },
    "controls": _load_controls(),
    "control_yield": {
      "check_runs": total_check_runs,
      "passing_check_runs": passing_checks,
      "observed_pass_rate": passing_checks / total_check_runs if total_check_runs else 0.0,
      "healthy_sample_failure_observations": total_check_runs - passing_checks,
    },
    "checks": checks,
    "supported_row": supported_row,
    "evidence_retrieval": evidence,
    "static_test_audit": audit["summary"],
    "metric_owners": {
      "control_yield_and_cost": "cross-domain-architecture",
      "replacement_drain_rollback_adoption": "release/runtime-integration",
      "stale_reference_and_plan_skew": "runtime-composition",
      "evidence_retrieval": "documentation-lifecycle",
    },
    "status": "passed" if passing_checks == total_check_runs and supported_row["slo_pass_rate"] == 1.0 and evidence["availability_ratio"] == 1.0 else "needs-disposition",
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--current-build", type=Path, required=True)
  parser.add_argument("--rollback-build", type=Path, required=True)
  parser.add_argument("--runs", type=int, default=3)
  parser.add_argument("--process-cycles", type=int, default=1)
  parser.add_argument("--output", type=Path)
  args = parser.parse_args(argv)
  report = build_baseline(
    current_build=args.current_build,
    rollback_build=args.rollback_build,
    runs=args.runs,
    process_cycles=args.process_cycles,
  )
  payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
  if args.output is not None:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
  print(payload, end="")
  return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
  raise SystemExit(main())
