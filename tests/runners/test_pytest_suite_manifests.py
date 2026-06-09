from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.runners import run_pytest_suite


REPO_ROOT = Path(run_pytest_suite.REPO_ROOT)
CI_SMOKE_SUITE_ENTRY = "tests/smoke/ci_smoke_suite.json"
PYTEST_SUITE_MANIFESTS = (
    REPO_ROOT / "tests" / "smoke" / "ci_smoke_suite.json",
    REPO_ROOT / "tests" / "suites" / "focused_runtime_suite.json",
)
TEST_SYSTEM_MATRIX = REPO_ROOT / "tests" / "suites" / "test_system_matrix.json"
MATRIX_PATH_KEYS = (
    "primary_paths",
    "smoke_paths",
    "tool_paths",
    "contract_paths",
)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} must contain a JSON object"
    return data


def _base_entry(entry: str) -> str:
    return entry.split("::", 1)[0].replace("\\", "/")


def _is_same_or_nested(path: str, root: str) -> bool:
    normalized_path = path.rstrip("/")
    normalized_root = root.rstrip("/")
    return normalized_path == normalized_root or normalized_path.startswith(
        normalized_root + "/"
    )


def test_pytest_suite_manifest_entries_resolve_to_existing_base_paths() -> None:
    for manifest_path in PYTEST_SUITE_MANIFESTS:
        suite = _load_json(manifest_path)
        entries = suite.get("paths")
        assert isinstance(entries, list) and entries, f"{manifest_path} has no paths"
        for entry in entries:
            assert isinstance(entry, str) and entry.strip(), (
                f"{manifest_path} contains an invalid pytest entry: {entry!r}"
            )
            _, check_path = run_pytest_suite._resolve_pytest_entry(entry)
            assert Path(check_path).exists(), (
                f"{manifest_path} contains a stale pytest entry: {entry}"
            )


def test_test_system_matrix_paths_resolve_to_existing_base_paths() -> None:
    matrix = _load_json(TEST_SYSTEM_MATRIX)
    for system in matrix.get("systems", []):
        assert isinstance(system, dict)
        system_id = system.get("id", "<missing-id>")
        for key in MATRIX_PATH_KEYS:
            for entry in system.get(key, []):
                assert isinstance(entry, str) and entry.strip(), (
                    f"{system_id}.{key} contains an invalid path entry: {entry!r}"
                )
                _, check_path = run_pytest_suite._resolve_pytest_entry(entry)
                assert Path(check_path).exists(), (
                    f"{system_id}.{key} contains a stale path entry: {entry}"
                )


def test_matrix_smoke_paths_are_declared_in_ci_smoke_manifest() -> None:
    matrix = _load_json(TEST_SYSTEM_MATRIX)
    smoke_entries = set(_load_json(PYTEST_SUITE_MANIFESTS[0])["paths"])
    declared_smoke_paths: set[str] = set()
    for system in matrix.get("systems", []):
        if not isinstance(system, dict):
            continue
        declared_smoke_paths.update(system.get("smoke_paths", []))

    missing = sorted(declared_smoke_paths - smoke_entries)
    assert not missing, f"matrix smoke_paths missing from ci smoke suite: {missing}"


def test_ci_smoke_suite_membership_requires_explicit_smoke_paths() -> None:
    matrix = _load_json(TEST_SYSTEM_MATRIX)
    missing: list[str] = []
    for system in matrix.get("systems", []):
        if not isinstance(system, dict):
            continue
        if CI_SMOKE_SUITE_ENTRY not in system.get("suite_membership", []):
            continue
        smoke_paths = system.get("smoke_paths")
        if not isinstance(smoke_paths, list) or not smoke_paths:
            missing.append(str(system.get("id", "<missing-id>")))

    assert not missing, (
        "systems listed in ci smoke suite_membership must declare explicit "
        f"smoke_paths: {missing}"
    )


def test_ci_smoke_uses_nodeids_for_broad_runtime_facade_layering_guard() -> None:
    entries = _load_json(PYTEST_SUITE_MANIFESTS[0])["paths"]
    broad_layering_file = "tests/architecture/runtime_facade/test_layering.py"
    assert broad_layering_file not in entries

    selected_nodes = [
        entry for entry in entries if entry.startswith(broad_layering_file + "::")
    ]
    assert selected_nodes, "ci smoke should keep representative runtime facade nodeids"
    assert all("::" in entry for entry in selected_nodes)


def test_ci_smoke_uses_explicit_files_or_nodeids_not_directories() -> None:
    entries = _load_json(PYTEST_SUITE_MANIFESTS[0])["paths"]
    directory_entries = []
    for entry in entries:
        _, check_path = run_pytest_suite._resolve_pytest_entry(entry)
        if Path(check_path).is_dir():
            directory_entries.append(entry)

    assert not directory_entries, (
        "ci smoke should list explicit files or nodeids so new tests are not "
        f"promoted accidentally: {directory_entries}"
    )


def test_ci_smoke_keeps_manual_matrix_pytest_roots_out() -> None:
    matrix = _load_json(TEST_SYSTEM_MATRIX)
    smoke_bases = [_base_entry(entry) for entry in _load_json(PYTEST_SUITE_MANIFESTS[0])["paths"]]
    manual_roots: list[str] = []
    for system in matrix.get("systems", []):
        if not isinstance(system, dict) or system.get("recommended_tier") != "manual":
            continue
        manual_roots.extend(
            _base_entry(path)
            for path in system.get("primary_paths", [])
            if str(path).startswith("tests/")
        )

    violations = [
        (smoke_base, manual_root)
        for smoke_base in smoke_bases
        for manual_root in manual_roots
        if _is_same_or_nested(smoke_base, manual_root)
        or _is_same_or_nested(manual_root, smoke_base)
    ]
    assert not violations, f"manual-tier pytest roots leaked into ci smoke: {violations}"
