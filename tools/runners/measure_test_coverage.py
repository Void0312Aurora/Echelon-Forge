#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.runners import run_pytest_suite


DEFAULT_PYTHON_SOURCES = ("gym_envs", "python")
DEFAULT_GCOVR_FILTERS = ("src/",)
DEFAULT_GCOVR_EXCLUDES = ("src/tests/.*",)


class UnavailableCoverageReportError(RuntimeError):
    pass


def _resolve_repo_or_abs(path: str) -> Path:
    raw = str(path).strip()
    if not raw:
        raise ValueError("paths must be non-empty")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate.resolve()


def _load_suite_paths(suite_path: Path) -> list[str]:
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    if not isinstance(suite, dict):
        raise TypeError(f"expected suite JSON object at {suite_path}")
    raw_paths = suite.get("paths")
    if not isinstance(raw_paths, list) or not raw_paths:
        raise ValueError(f"pytest suite {suite_path} has no non-empty 'paths' list")

    resolved_paths: list[str] = []
    missing_paths: list[str] = []
    for raw in raw_paths:
        if not isinstance(raw, str):
            raise TypeError(f"pytest suite entry must be a string: {raw!r}")
        resolved, check_path = run_pytest_suite._resolve_pytest_entry(raw)
        if not Path(check_path).exists():
            missing_paths.append(raw)
            continue
        resolved_paths.append(resolved)

    if missing_paths:
        missing = "\n".join(f"  - {path}" for path in missing_paths)
        raise FileNotFoundError(
            f"pytest suite {suite_path} has stale entries:\n{missing}"
        )
    return resolved_paths


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _venv_tool(name: str) -> str | None:
    executable = Path(sys.executable).resolve().with_name(name)
    if executable.exists() and os.access(executable, os.X_OK):
        return str(executable)
    return shutil.which(name)


def _python_module_tool(name: str) -> list[str] | None:
    executable = _venv_tool(name)
    if executable:
        return [executable]
    if _module_available(name):
        return [sys.executable, "-m", name]
    return None


def _run(
    cmd: list[str],
    *,
    capture: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    print(f"[coverage] running: {' '.join(cmd)}", flush=True)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=capture,
        env=env,
    )


def _write_captured(path: Path, proc: subprocess.CompletedProcess[str]) -> None:
    content = ""
    if proc.stdout:
        content += proc.stdout
    if proc.stderr:
        if content and not content.endswith("\n"):
            content += "\n"
        content += proc.stderr
    path.write_text(content, encoding="utf-8")


def _python_coverage(
    *,
    suite_path: Path,
    output_dir: Path,
    sources: list[str],
    pytest_args: list[str],
) -> list[dict[str, Any]]:
    if not _module_available("coverage"):
        raise UnavailableCoverageReportError(
            "coverage is not installed; install the smoke coverage dependencies first"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    data_file = output_dir / ".coverage"
    resolved_paths = _load_suite_paths(suite_path)
    source_arg = ",".join(sources)
    results: list[dict[str, Any]] = []

    run_cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--data-file={data_file}",
        f"--source={source_arg}",
        "-m",
        "pytest",
        "-q",
        *resolved_paths,
        *pytest_args,
    ]
    proc = _run(run_cmd)
    results.append({"name": "python-coverage-run", "returncode": proc.returncode})

    report_cmd = [
        sys.executable,
        "-m",
        "coverage",
        "report",
        f"--data-file={data_file}",
        "-m",
    ]
    report_proc = _run(report_cmd, capture=True)
    _write_captured(output_dir / "python-coverage.txt", report_proc)
    if report_proc.stdout:
        print(report_proc.stdout, end="")
    if report_proc.stderr:
        print(report_proc.stderr, end="", file=sys.stderr)
    results.append(
        {"name": "python-coverage-report", "returncode": report_proc.returncode}
    )

    xml_proc = _run(
        [
            sys.executable,
            "-m",
            "coverage",
            "xml",
            f"--data-file={data_file}",
            "-o",
            str(output_dir / "python-coverage.xml"),
        ]
    )
    results.append({"name": "python-coverage-xml", "returncode": xml_proc.returncode})

    json_proc = _run(
        [
            sys.executable,
            "-m",
            "coverage",
            "json",
            f"--data-file={data_file}",
            "-o",
            str(output_dir / "python-coverage.json"),
        ]
    )
    results.append(
        {"name": "python-coverage-json", "returncode": json_proc.returncode}
    )
    return results


def _cpp_coverage(
    *,
    object_dir: Path,
    output_dir: Path,
    filters: list[str],
    excludes: list[str],
) -> list[dict[str, Any]]:
    gcovr = _python_module_tool("gcovr")
    if not gcovr:
        raise UnavailableCoverageReportError(
            "gcovr is not installed; install the smoke coverage dependencies first"
        )
    if not object_dir.exists():
        raise UnavailableCoverageReportError(
            f"C++ coverage object directory is missing: {object_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    base_cmd = [
        *gcovr,
        "-r",
        str(REPO_ROOT),
        "--object-directory",
        str(object_dir),
        "--gcov-ignore-errors=all",
    ]
    for filter_pattern in filters:
        base_cmd.extend(["--filter", filter_pattern])
    for exclude_pattern in excludes:
        base_cmd.extend(["--exclude", exclude_pattern])

    results: list[dict[str, Any]] = []
    summary_proc = _run([*base_cmd, "--txt-summary"], capture=True)
    _write_captured(output_dir / "cpp-gcovr-summary.txt", summary_proc)
    if summary_proc.stdout:
        print(summary_proc.stdout, end="")
    if summary_proc.stderr:
        print(summary_proc.stderr, end="", file=sys.stderr)
    results.append({"name": "cpp-gcovr-summary", "returncode": summary_proc.returncode})

    xml_proc = _run(
        [*base_cmd, "--xml-pretty", "--xml", str(output_dir / "cpp-gcovr.xml")]
    )
    results.append({"name": "cpp-gcovr-xml", "returncode": xml_proc.returncode})

    json_proc = _run(
        [*base_cmd, "--json-pretty", "--json", str(output_dir / "cpp-gcovr.json")]
    )
    results.append({"name": "cpp-gcovr-json", "returncode": json_proc.returncode})
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate retained Python coverage and optional C++ gcovr reports from "
            "a checked-in pytest suite manifest."
        )
    )
    parser.add_argument(
        "--suite",
        default="tests/smoke/ci_smoke_suite.json",
        help="Checked-in pytest suite manifest to run under Python coverage.",
    )
    parser.add_argument(
        "--output-dir",
        default="coverage-reports",
        help="Directory for retained coverage reports.",
    )
    parser.add_argument(
        "--python-source",
        action="append",
        default=None,
        help=(
            "Python source root passed to coverage. Repeat to add roots; defaults "
            "to gym_envs and python."
        ),
    )
    parser.add_argument(
        "--skip-python",
        action="store_true",
        help="Skip Python coverage generation.",
    )
    parser.add_argument(
        "--cpp-object-dir",
        default=os.environ.get("CMO_BUILD_DIR", "build-coverage"),
        help="Coverage-instrumented CMake build directory for gcovr.",
    )
    parser.add_argument(
        "--gcovr-filter",
        action="append",
        default=None,
        help="gcovr source filter. Repeat to add filters; defaults to src/.",
    )
    parser.add_argument(
        "--gcovr-exclude",
        action="append",
        default=None,
        help="gcovr exclude regex. Repeat to add excludes; defaults to src/tests/.*.",
    )
    parser.add_argument(
        "--skip-cpp",
        action="store_true",
        help="Skip C++ gcovr report generation.",
    )
    parser.add_argument(
        "--allow-test-failures",
        action="store_true",
        help="Write reports but exit 0 when only the pytest coverage run failed.",
    )
    parser.add_argument(
        "--skip-unavailable-reports",
        action="store_true",
        help=(
            "Skip report families whose tools or build artifacts are unavailable, "
            "while recording the skip in metadata."
        ),
    )
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Additional args passed through to pytest after the suite paths.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = _resolve_repo_or_abs(str(args.output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    if not args.skip_python:
        try:
            results.extend(
                _python_coverage(
                    suite_path=_resolve_repo_or_abs(str(args.suite)),
                    output_dir=output_dir,
                    sources=list(args.python_source or DEFAULT_PYTHON_SOURCES),
                    pytest_args=list(args.pytest_args or []),
                )
            )
        except UnavailableCoverageReportError as exc:
            if not args.skip_unavailable_reports:
                raise
            print(f"[coverage] skipping Python coverage: {exc}", file=sys.stderr)
            results.append(
                {
                    "name": "python-coverage",
                    "returncode": 0,
                    "skipped": str(exc),
                }
            )

    if not args.skip_cpp:
        try:
            results.extend(
                _cpp_coverage(
                    object_dir=_resolve_repo_or_abs(str(args.cpp_object_dir)),
                    output_dir=output_dir,
                    filters=list(args.gcovr_filter or DEFAULT_GCOVR_FILTERS),
                    excludes=list(args.gcovr_exclude or DEFAULT_GCOVR_EXCLUDES),
                )
            )
        except UnavailableCoverageReportError as exc:
            if not args.skip_unavailable_reports:
                raise
            print(f"[coverage] skipping C++ coverage: {exc}", file=sys.stderr)
            results.append(
                {
                    "name": "cpp-gcovr",
                    "returncode": 0,
                    "skipped": str(exc),
                }
            )

    metadata = {
        "suite": str(_resolve_repo_or_abs(str(args.suite))),
        "output_dir": str(output_dir),
        "python_sources": list(args.python_source or DEFAULT_PYTHON_SOURCES),
        "cpp_object_dir": str(_resolve_repo_or_abs(str(args.cpp_object_dir))),
        "results": results,
    }
    (output_dir / "coverage-run-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    failing = [
        result
        for result in results
        if int(result.get("returncode", 0)) != 0
        and not (
            args.allow_test_failures
            and str(result.get("name")) == "python-coverage-run"
        )
    ]
    if failing:
        print("[coverage] one or more coverage commands failed:", file=sys.stderr)
        for result in failing:
            print(
                f"  - {result['name']}: exit {result['returncode']}",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
