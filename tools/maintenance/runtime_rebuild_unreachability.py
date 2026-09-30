"""Capture and validate the P5-D in-kernel rebuild reachability boundary.

The native ``SimulationKernel::rebuild_world_composition`` capability remains
in the compatibility implementation until the unique production cutover and
rollback-window gate are complete.  This inventory makes the interim safety
claim executable: only the native declaration/definition and test-only calls
may mention the callable symbol, while the production wheel stays facade-only
and the diagnostics binding remains an explicit opt-in target.

This tool deliberately does *not* mark the rebuild capability retired.  A
zero-caller inventory is a prerequisite for retirement, not the retirement
decision itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = (
    ROOT
    / "tests"
    / "architecture"
    / "runtime_host"
    / "fixtures"
    / "runtime_rebuild_unreachability.v1.json"
)
SCHEMA_VERSION = "echelon_forge.runtime_rebuild_unreachability.v1"
SYMBOL = "rebuild_world_composition"
QUALIFIED_SYMBOL = "SimulationKernel::rebuild_world_composition"

SCAN_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".inl",
    ".ipp",
    ".py",
    ".pyi",
    ".toml",
    ".yml",
    ".yaml",
}
SCAN_ROOTS = (
    "CMakeLists.txt",
    "pyproject.toml",
    "src",
    "python",
    "examples",
    "tools/diagnostics",
)
SKIP_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "node_modules",
}
TEST_CALL_ROOTS = ("src/tests/",)
CALL_PATTERN = re.compile(rf"(?<![\w:]){re.escape(SYMBOL)}\s*\(")


class InventoryError(ValueError):
    """Raised when the rebuild reachability record is stale or unsafe."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRECTORY_NAMES or part.startswith("build-") for part in path.parts)


def _iter_scan_paths() -> list[Path]:
    paths: list[Path] = []
    for root_name in SCAN_ROOTS:
        root = ROOT / root_name
        if root.is_file():
            paths.append(root)
        elif root.is_dir():
            paths.extend(root.rglob("*"))
    return sorted(
        path
        for path in paths
        if path.is_file()
        and not _should_skip(path)
        and (path.name == "CMakeLists.txt" or path.suffix.lower() in SCAN_SUFFIXES)
    )


def _matching_lines(path: Path) -> list[int]:
    return [
        lineno
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1)
        if SYMBOL in line
    ]


def _is_test_path(path_name: str) -> bool:
    return any(path_name.startswith(prefix) for prefix in TEST_CALL_ROOTS)


def _is_python_binding_path(path_name: str) -> bool:
    return path_name.startswith("src/interfaces/python/")


def _strip_cpp_line_comments(source: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in source.splitlines())


def _is_callable_line(path: Path, lineno: int) -> bool:
    line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[lineno - 1]
    return CALL_PATTERN.search(line) is not None


def _source_references() -> dict[str, list[int]]:
    references: dict[str, list[int]] = {}
    for path in _iter_scan_paths():
        lines = _matching_lines(path)
        if lines:
            references[relative(path)] = lines
    return dict(sorted(references.items()))


def _production_package_guard() -> dict[str, Any]:
    cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    module = (ROOT / "src/interfaces/python/python_module.cpp").read_text(encoding="utf-8")
    facade_bindings = (
        ROOT / "src/interfaces/python/bindings_runtime_facade_only.cpp"
    ).read_text(encoding="utf-8")
    return {
        "pyproject_production_facade_only": 'EF_PRODUCTION_FACADE_ONLY = "ON"' in pyproject,
        "pyproject_diagnostics_disabled": 'EF_BUILD_DIAGNOSTICS_BINDINGS = "OFF"' in pyproject,
        "cmake_production_filter_excludes_raw_bindings": (
            'EXCLUDE REGEX "bindings_core|bindings_gpu|bindings_runtime\\.cpp$|'
            'bindings_runtime_engine\\.cpp$"'
        ) in cmake,
        "cmake_diagnostics_is_opt_in": "if (EF_BUILD_DIAGNOSTICS_BINDINGS)" in cmake,
        "production_module_selects_facade_only": "bind_runtime_facade_only(m);" in module,
        "production_module_does_not_select_raw_core": "bind_core(m);" not in module.split(
            "#else", 1
        )[0],
        "facade_binding_does_not_export_simulation_kernel": not re.search(
            r"\bSimulationKernel\b", _strip_cpp_line_comments(facade_bindings)
        ),
    }


def build_inventory() -> dict[str, Any]:
    references = _source_references()
    test_only_references = {
        path: lines for path, lines in references.items() if _is_test_path(path)
    }
    python_binding_references = {
        path: lines
        for path, lines in references.items()
        if _is_python_binding_path(path)
    }
    callable_references: dict[str, list[int]] = {}
    for path_name, lines in references.items():
        path = ROOT / path_name
        callable_lines = [lineno for lineno in lines if _is_callable_line(path, lineno)]
        if callable_lines:
            callable_references[path_name] = callable_lines

    production_callable_references = {
        path: lines
        for path, lines in callable_references.items()
        if not _is_test_path(path)
        and path not in {
            "src/core/engine/simulation_kernel.cpp",
            "src/core/engine/simulation_kernel.h",
        }
    }
    implementation_lines = {
        path: lines
        for path, lines in references.items()
        if path in {
            "src/core/engine/simulation_kernel.cpp",
            "src/core/engine/simulation_kernel.h",
        }
    }
    package_guard = _production_package_guard()
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "scope": "P5-D in-kernel rebuild reachability before production cutover",
        "symbol": QUALIFIED_SYMBOL,
        "references": references,
        "implementation_references": implementation_lines,
        "callable_references": callable_references,
        "test_only_references": test_only_references,
        "production_callable_references": production_callable_references,
        "python_binding_references": python_binding_references,
        "production_package_guard": package_guard,
        "reachability_state": "quarantined_before_production_cutover",
        "retired": False,
        "retirement_gate": (
            "single production cutover plus rollback-window retention and rebuild gate"
        ),
    }
    body["inventory_sha256"] = sha256_text(canonical_json(body))
    return body


def validate_inventory(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise InventoryError("inventory must be an object")
    expected = build_inventory()
    if record != expected:
        raise InventoryError("rebuild reachability inventory is stale or does not match the live tree")
    if record["production_callable_references"]:
        raise InventoryError(
            "production rebuild call sites remain: "
            + ", ".join(record["production_callable_references"])
        )
    if record["python_binding_references"]:
        raise InventoryError(
            "rebuild symbol appeared in Python binding sources: "
            + ", ".join(record["python_binding_references"])
        )
    if record["retired"]:
        raise InventoryError("rebuild retirement cannot be asserted by the pre-cutover inventory")
    if not all(record["production_package_guard"].values()):
        raise InventoryError("production package is not fail-closed to the facade-only boundary")
    return record


def load_fixture(path: Path = DEFAULT_FIXTURE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("capture", "validate"))
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "capture":
        print(json.dumps(build_inventory(), ensure_ascii=False, indent=2) + "\n")
        return 0
    try:
        validate_inventory(load_fixture(args.fixture))
    except (OSError, json.JSONDecodeError, InventoryError) as error:
        print(f"rebuild reachability validation failed: {error}", file=sys.stderr)
        return 1
    print(f"validated {args.fixture}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
