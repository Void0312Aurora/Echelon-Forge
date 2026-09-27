#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

LANE_MANIFEST = Path("tests/suites/ci_lane_manifest.json")
PRIMARY_LANES = {"fast", "qualification", "nightly", "release", "research"}
ALLOWED_CTEST_LABELS = PRIMARY_LANES | {"native", "cuda", "boundary", "p5b"}
REQUIRED_METADATA = ("owner", "failure_audience", "execution_strategy")
SCHEMA_VERSION = 1


class CiLaneAuditError(ValueError):
  """Raised when the maintained CI lane declaration is inconsistent."""


def _repo_relative(path: Path, root: Path) -> str:
  try:
    return path.resolve().relative_to(root.resolve()).as_posix()
  except ValueError as exc:
    raise CiLaneAuditError(f"path is outside repository root: {path}") from exc


def _load_json(path: Path) -> dict[str, Any]:
  try:
    value = json.loads(path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError) as exc:
    raise CiLaneAuditError(f"cannot read CI lane manifest {path}: {exc}") from exc
  if not isinstance(value, dict):
    raise CiLaneAuditError(f"CI lane manifest must contain an object: {path}")
  return value


def _required_string(payload: dict[str, Any], key: str, path: Path) -> str:
  value = payload.get(key)
  if not isinstance(value, str) or not value.strip():
    raise CiLaneAuditError(f"{path} must declare non-empty {key}")
  return value.strip()


def _workflow_job_ids(workflow: Path) -> set[str]:
  text = workflow.read_text(encoding="utf-8")
  try:
    jobs_text = text.split("\njobs:", 1)[1]
  except IndexError as exc:
    raise CiLaneAuditError(f"workflow has no jobs section: {workflow}") from exc
  return set(re.findall(r"^  ([A-Za-z0-9_-]+):\s*$", jobs_text, re.MULTILINE))


def _workflow_job_text(workflow: Path, job: str) -> str:
  text = workflow.read_text(encoding="utf-8")
  jobs_text = text.split("\njobs:", 1)[1]
  match = re.search(
    rf"(?ms)^  {re.escape(job)}:\s*\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)",
    jobs_text,
  )
  if match is None:
    raise CiLaneAuditError(f"workflow job not found: {workflow}::{job}")
  return match.group("body")


def _workflow_events(workflow: Path) -> set[str]:
  text = workflow.read_text(encoding="utf-8")
  match = re.search(r"(?ms)^on:\s*\n(?P<body>.*?)(?=^jobs:\s*$)", text)
  if match is None:
    raise CiLaneAuditError(f"workflow has no on section: {workflow}")
  event_text = match.group("body")
  return set(re.findall(r"^  ([A-Za-z0-9_-]+):", event_text, re.MULTILINE))


def _entry_base(entry: str) -> str:
  return entry.split("::", 1)[0].replace("\\", "/")


def _validate_path_entries(root: Path, entries: Iterable[Any], *, kind: str, lane_id: str) -> list[str]:
  normalized: list[str] = []
  for entry in entries:
    if not isinstance(entry, str) or not entry.strip():
      raise CiLaneAuditError(f"lane {lane_id} contains an invalid {kind} entry: {entry!r}")
    relative = _entry_base(entry)
    candidate = root / relative
    if not candidate.is_file():
      raise CiLaneAuditError(f"lane {lane_id} contains a stale {kind} entry: {entry}")
    normalized.append(entry)
  return normalized


def build_report(*, root: Path = REPO_ROOT, manifest_path: Path = LANE_MANIFEST) -> dict[str, Any]:
  root = root.resolve()
  manifest = manifest_path if manifest_path.is_absolute() else root / manifest_path
  payload = _load_json(manifest)
  if payload.get("schema_version") != SCHEMA_VERSION:
    raise CiLaneAuditError(
      f"{manifest} schema_version must be {SCHEMA_VERSION}, got {payload.get('schema_version')!r}"
    )
  metadata = {key: _required_string(payload, key, manifest) for key in REQUIRED_METADATA}
  lanes = payload.get("lanes")
  if not isinstance(lanes, list) or not lanes:
    raise CiLaneAuditError(f"{manifest} must contain a non-empty lanes list")

  lane_rows: list[dict[str, Any]] = []
  seen_ids: set[str] = set()
  seen_jobs: dict[tuple[str, str], str] = {}
  primary_seen: set[str] = set()
  for lane in lanes:
    if not isinstance(lane, dict):
      raise CiLaneAuditError(f"{manifest} contains a non-object lane")
    lane_id = _required_string(lane, "id", manifest)
    if lane_id in seen_ids:
      raise CiLaneAuditError(f"duplicate CI lane id: {lane_id}")
    seen_ids.add(lane_id)
    if lane_id not in PRIMARY_LANES:
      raise CiLaneAuditError(f"unsupported CI lane id: {lane_id}")
    lane_metadata = {
      key: _required_string(lane, key, manifest)
      for key in ("owner", "failure_audience", "workflow", "runner", "run_mode")
    }
    workflow = root / lane_metadata["workflow"]
    if not workflow.is_file():
      raise CiLaneAuditError(f"lane {lane_id} references missing workflow: {workflow}")
    jobs = lane.get("jobs")
    if not isinstance(jobs, list) or not jobs or not all(isinstance(job, str) and job.strip() for job in jobs):
      raise CiLaneAuditError(f"lane {lane_id} must declare a non-empty jobs list")
    workflow_jobs = _workflow_job_ids(workflow)
    missing_jobs = sorted(set(jobs) - workflow_jobs)
    if missing_jobs:
      raise CiLaneAuditError(
        f"lane {lane_id} references missing jobs in {workflow}: {missing_jobs}"
      )
    events = lane.get("trigger_events")
    if not isinstance(events, list) or not events or not all(isinstance(event, str) for event in events):
      raise CiLaneAuditError(f"lane {lane_id} must declare trigger_events")
    missing_events = sorted(set(events) - _workflow_events(workflow))
    if missing_events:
      raise CiLaneAuditError(
        f"lane {lane_id} references missing workflow events in {workflow}: {missing_events}"
      )
    for job in jobs:
      key = (lane_metadata["workflow"], job)
      previous = seen_jobs.get(key)
      if previous is not None:
        raise CiLaneAuditError(
          f"workflow job is assigned to multiple lane authorities: {key} ({previous}, {lane_id})"
        )
      seen_jobs[key] = lane_id
    timeout = lane.get("timeout_minutes")
    build_parallelism = lane.get("build_parallelism")
    test_parallelism = lane.get("test_parallelism")
    if not isinstance(timeout, int) or timeout <= 0:
      raise CiLaneAuditError(f"lane {lane_id} timeout_minutes must be a positive integer")
    if not isinstance(build_parallelism, int) or not 1 <= build_parallelism <= 16:
      raise CiLaneAuditError(f"lane {lane_id} build_parallelism must be an integer from 1 to 16")
    if not isinstance(test_parallelism, int) or not 1 <= test_parallelism <= 16:
      raise CiLaneAuditError(f"lane {lane_id} test_parallelism must be an integer from 1 to 16")
    ctest_labels = lane.get("ctest_labels")
    if not isinstance(ctest_labels, list) or not ctest_labels or not all(isinstance(label, str) for label in ctest_labels):
      raise CiLaneAuditError(f"lane {lane_id} must declare ctest_labels")
    invalid_labels = sorted(set(ctest_labels) - ALLOWED_CTEST_LABELS)
    if invalid_labels:
      raise CiLaneAuditError(f"lane {lane_id} declares unsupported CTest labels: {invalid_labels}")
    if not PRIMARY_LANES.intersection(ctest_labels):
      raise CiLaneAuditError(f"lane {lane_id} must include its primary CTest label")
    primary_seen.update(PRIMARY_LANES.intersection(ctest_labels))
    selected_ctest_labels = lane.get("selected_ctest_labels")
    if not isinstance(selected_ctest_labels, list) or not all(
      isinstance(label, str) and label.strip() for label in selected_ctest_labels
    ):
      raise CiLaneAuditError(f"lane {lane_id} must declare selected_ctest_labels")
    invalid_selected_labels = sorted(set(selected_ctest_labels) - ALLOWED_CTEST_LABELS)
    if invalid_selected_labels:
      raise CiLaneAuditError(
        f"lane {lane_id} selects unsupported CTest labels: {invalid_selected_labels}"
      )
    undeclared_selected_labels = sorted(set(selected_ctest_labels) - set(ctest_labels))
    if undeclared_selected_labels:
      raise CiLaneAuditError(
        f"lane {lane_id} selects undeclared CTest labels: {undeclared_selected_labels}"
      )
    if lane_id != "research" and not selected_ctest_labels:
      raise CiLaneAuditError(f"lane {lane_id} must select at least one CTest label")
    if lane_id == "research" and selected_ctest_labels:
      raise CiLaneAuditError("research compile-only lane must not select CTest labels")
    for job in jobs:
      job_text = _workflow_job_text(workflow, job)
      if not re.search(rf"(?m)^    runs-on:\s*{re.escape(lane_metadata['runner'])}\s*$", job_text):
        raise CiLaneAuditError(f"lane {lane_id} runner does not match workflow job {job}")
      if not re.search(rf"(?m)^    timeout-minutes:\s*{timeout}\s*$", job_text):
        raise CiLaneAuditError(f"lane {lane_id} timeout does not match workflow job {job}")
      if not re.search(rf"(?:--parallel\s+|-j\s*){build_parallelism}(?:\s|$)", job_text):
        raise CiLaneAuditError(
          f"lane {lane_id} build parallelism is not used by workflow job {job}"
        )
      if lane_id == "research":
        if re.search(r"(?m)^\s*(?:run:\s*)?ctest\b", job_text):
          raise CiLaneAuditError("research compile-only lane must not run CTest")
      elif not all(
        re.search(
          rf"(?m)^\s*(?:run:\s*)?.*?\bctest\b[^\n]*\s-L\s+{re.escape(label)}(?:\s|$)",
          job_text,
        )
        for label in selected_ctest_labels
      ):
        raise CiLaneAuditError(
          f"lane {lane_id} workflow job {job} does not select its CTest label"
        )
      selected_parallelism = re.findall(
        r"(?m)^\s*(?:run:\s*)?.*?\bctest\b[^\n]*--parallel\s+(\d+)",
        job_text,
      )
      actual_test_parallelism = int(selected_parallelism[0]) if selected_parallelism else 1
      if actual_test_parallelism != test_parallelism:
        raise CiLaneAuditError(
          f"lane {lane_id} test parallelism does not match workflow job {job}"
        )
    pytest_entries = lane.get("pytest_entries", [])
    contract_suites = lane.get("contract_suites", [])
    if not isinstance(pytest_entries, list) or not isinstance(contract_suites, list):
      raise CiLaneAuditError(f"lane {lane_id} pytest_entries and contract_suites must be lists")
    normalized_pytest = _validate_path_entries(root, pytest_entries, kind="pytest", lane_id=lane_id)
    normalized_contracts = _validate_path_entries(root, contract_suites, kind="contract suite", lane_id=lane_id)
    lane_rows.append(
      {
        "id": lane_id,
        **lane_metadata,
        "workflow": _repo_relative(workflow, root),
        "jobs": list(jobs),
        "trigger_events": list(events),
        "timeout_minutes": timeout,
        "build_parallelism": build_parallelism,
        "test_parallelism": test_parallelism,
        "ctest_labels": list(ctest_labels),
        "selected_ctest_labels": list(selected_ctest_labels),
        "pytest_entries": normalized_pytest,
        "contract_suites": normalized_contracts,
      }
    )

  missing_primary = sorted(PRIMARY_LANES - primary_seen)
  if missing_primary:
    raise CiLaneAuditError(f"CI lane manifest omits primary labels: {missing_primary}")
  return {
    "schema_version": "ci_lane_audit.v1",
    "report_authority": "maintained_lane_manifest",
    "source_of_truth": _repo_relative(manifest, root),
    "metadata": metadata,
    "summary": {
      "lane_count": len(lane_rows),
      "primary_lane_count": len(primary_seen),
      "workflow_job_count": len(seen_jobs),
      "workflow_count": len({row["workflow"] for row in lane_rows}),
    },
    "lanes": sorted(lane_rows, key=lambda row: row["id"]),
  }


def format_markdown(report: dict[str, Any]) -> str:
  lines = [
    "# CI Lane Audit",
    "",
    f"- Report authority: `{report['report_authority']}`",
    f"- Source of truth: `{report['source_of_truth']}`",
    f"- Lanes: `{report['summary']['lane_count']}`",
    f"- Workflow jobs: `{report['summary']['workflow_job_count']}`",
    "",
    "| Lane | Workflow | Jobs | Runner | Timeout (min) | Build / test parallelism | Declared / selected CTest labels | Failure audience |",
    "| --- | --- | --- | --- | ---: | --- | --- | --- |",
  ]
  for row in report["lanes"]:
    declared_labels = ", ".join(f"`{label}`" for label in row["ctest_labels"])
    selected_labels = ", ".join(f"`{label}`" for label in row["selected_ctest_labels"]) or "none (compile/link only)"
    jobs = ", ".join(f"`{job}`" for job in row["jobs"])
    lines.append(
      "| " + " | ".join(
        [
          row["id"],
          f"`{row['workflow']}`",
          jobs,
          row["runner"],
          str(row["timeout_minutes"]),
          f"{row['build_parallelism']} / {row['test_parallelism']}",
          f"declared: {declared_labels}; selected: {selected_labels}",
          row["failure_audience"],
        ]
      ) + " |"
    )
  return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Validate the maintained CI lane declaration.")
  parser.add_argument("--format", choices=("json", "markdown"), default="json")
  parser.add_argument("--output", help="Optional output file; defaults to stdout.")
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  report = build_report()
  content = (
    format_markdown(report)
    if args.format == "markdown"
    else json.dumps(report, indent=2, sort_keys=True) + "\n"
  )
  if args.output:
    output = Path(args.output)
    if not output.is_absolute():
      output = REPO_ROOT / output
    output.write_text(content, encoding="utf-8")
  else:
    print(content, end="")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
