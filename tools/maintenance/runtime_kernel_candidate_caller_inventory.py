#!/usr/bin/env python3
"""Inventory the P4-C candidate references and enforce its caller boundary.

The runtime candidate is intentionally a build-tree/shadow seam.  This tool
keeps the negative production-caller claim executable instead of relying on a
hand-maintained list in the evidence packet.
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
    / "runtime_kernel_candidate_caller_inventory.v1.json"
)
SCHEMA_VERSION = "echelon_forge.runtime_kernel_candidate_caller_inventory.v1"

# Keep the lexical surface deliberately small.  The path check below also
# protects the Python shadow adapter, whose module name is not a native symbol.
CANDIDATE_TOKENS = (
    "RuntimeKernelCandidate",
    "runtime_kernel_candidate",
    "candidate_adapter",
    "EpochReferenceFence",
)
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
    ".json",
}
SCAN_ROOTS = (
    "CMakeLists.txt",
    "pyproject.toml",
    "src",
    "python/rl/runtime/world_batch",
    "examples",
    "tools/diagnostics",
    "tools/maintenance/runtime_kernel_candidate_caller_inventory.py",
    "tools/maintenance/runtime_composition_migration_closure.py",
    "tests/architecture/runtime_host",
    "tests/architecture/composition/test_runtime_composition_migration_closure.py",
    "tests/architecture/composition/fixtures/default_runtime_composition_migration_closure.v1.json",
)
SKIP_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}

IMPLEMENTATION_CALLERS = {
    "src/runtime/host/integration/runtime_kernel_candidate.cpp",
    "src/runtime/host/integration/runtime_kernel_candidate.h",
    "src/runtime/host/integration/runtime_kernel_candidate_facade.cpp",
    "src/runtime/host/integration/runtime_kernel_candidate_facade.h",
}
TEST_ONLY_CALLERS = {
    "src/tests/test_runtime_kernel_candidate.cpp",
    "src/tests/test_runtime_kernel_candidate_parity.cpp",
    "tests/architecture/runtime_host/test_runtime_kernel_candidate_contract.py",
}
SHADOW_ONLY_CALLERS = {
    "python/rl/runtime/world_batch/candidate_adapter.py",
}
GOVERNANCE_CALLERS = {
    "tools/maintenance/runtime_kernel_candidate_caller_inventory.py",
    "tools/maintenance/runtime_composition_migration_closure.py",
    "tests/architecture/composition/test_runtime_composition_migration_closure.py",
    "tests/architecture/composition/fixtures/default_runtime_composition_migration_closure.v1.json",
    "tests/architecture/runtime_host/fixtures/runtime_kernel_candidate_caller_inventory.v1.json",
    "CMakeLists.txt",
    "pyproject.toml",
}
MAINTAINED_SURFACE_PREFIXES = (
    "src/runtime/facade/",
    "src/interfaces/python/",
    "python/rl/runtime/world_batch/adapter.py",
    "examples/",
    "tools/diagnostics/",
)


class InventoryError(ValueError):
    """Raised when the candidate caller inventory is stale or unsafe."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRECTORY_NAMES or part.startswith("build-") for part in path.parts)


def _candidate_matches(text: str) -> list[str]:
    return [token for token in CANDIDATE_TOKENS if re.search(re.escape(token), text)]


def scan_references() -> dict[str, list[str]]:
    references: dict[str, list[str]] = {}
    paths: list[Path] = []
    for root_name in SCAN_ROOTS:
        root = ROOT / root_name
        if root.is_file():
            paths.append(root)
        elif root.is_dir():
            paths.extend(root.rglob("*"))
    for path in paths:
        if (
            not path.is_file()
            or _should_skip(path)
            or (path.name != "CMakeLists.txt" and path.suffix.lower() not in SCAN_SUFFIXES)
        ):
            continue
        path_name = relative(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        matches = _candidate_matches(text)
        if path_name in SHADOW_ONLY_CALLERS and "candidate_adapter" not in matches:
            matches.append("candidate_adapter")
        if matches:
            references[path_name] = sorted(set(matches))
    return dict(sorted(references.items()))


def _classification(path_name: str) -> str:
    if path_name in IMPLEMENTATION_CALLERS:
        return "build_tree_candidate"
    if path_name in TEST_ONLY_CALLERS:
        return "test_only"
    if path_name in SHADOW_ONLY_CALLERS:
        return "shadow_only"
    if path_name in GOVERNANCE_CALLERS:
        return "governance"
    return "unclassified"


def build_inventory() -> dict[str, Any]:
    references = scan_references()
    classified = {
        category: sorted(path for path in references if _classification(path) == category)
        for category in (
            "build_tree_candidate",
            "test_only",
            "shadow_only",
            "governance",
            "unclassified",
        )
    }
    maintained_violations = sorted(
        path
        for path in references
        if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in MAINTAINED_SURFACE_PREFIXES)
    )
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "scope": "P4-C build-tree/internal candidate caller boundary",
        "tokens": list(CANDIDATE_TOKENS),
        "references": references,
        "classified_callers": classified,
        "maintained_surface_prefixes": list(MAINTAINED_SURFACE_PREFIXES),
        "maintained_surface_violations": maintained_violations,
        "production_authority": "forbidden",
    }
    body["inventory_sha256"] = sha256_text(canonical_json(body))
    return body


def validate_inventory(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise InventoryError("inventory must be an object")
    expected = build_inventory()
    if record != expected:
        raise InventoryError("candidate caller inventory is stale or does not match the live tree")
    if record["maintained_surface_violations"]:
        raise InventoryError(
            "candidate references appeared in maintained surfaces: "
            + ", ".join(record["maintained_surface_violations"])
        )
    if record["classified_callers"]["unclassified"]:
        raise InventoryError(
            "candidate references are unclassified: "
            + ", ".join(record["classified_callers"]["unclassified"])
        )
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
        print(f"candidate caller inventory validation failed: {error}", file=sys.stderr)
        return 1
    print(f"validated {args.fixture}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
