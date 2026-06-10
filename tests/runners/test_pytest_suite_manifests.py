from __future__ import annotations

import glob
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
CONTRACT_SYSTEM_MATRIX = REPO_ROOT / "tests" / "suites" / "contract_system_matrix.json"
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


def _contract_glob_matches(pattern: str) -> set[str]:
    assert pattern.startswith("tests/"), f"contract glob must be repo-relative: {pattern!r}"
    matches = {
        str(Path(path).relative_to(REPO_ROOT)).replace("\\", "/")
        for path in glob.glob(str(REPO_ROOT / pattern), recursive=True)
        if Path(path).is_file() and Path(path).suffix == ".json"
    }
    return matches


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


def test_contract_system_matrix_globs_resolve_to_contract_specs() -> None:
    matrix = _load_json(CONTRACT_SYSTEM_MATRIX)
    for surface in matrix.get("surfaces", []):
        assert isinstance(surface, dict)
        surface_id = surface.get("id", "<missing-id>")
        globs = surface.get("path_globs")
        assert isinstance(globs, list) and globs, f"{surface_id} has no path_globs"
        for pattern in globs:
            assert isinstance(pattern, str) and pattern.strip(), (
                f"{surface_id}.path_globs contains invalid entry: {pattern!r}"
            )
            matches = _contract_glob_matches(pattern)
            assert matches, f"{surface_id}.path_globs matched no specs: {pattern}"
            assert all(path.startswith("tests/contracts/") for path in matches), (
                f"{surface_id}.path_globs must stay within tests/contracts/: {pattern}"
            )


def test_contract_system_matrix_covers_all_maintained_contract_specs() -> None:
    matrix = _load_json(CONTRACT_SYSTEM_MATRIX)
    covered: set[str] = set()
    for surface in matrix.get("surfaces", []):
        if not isinstance(surface, dict):
            continue
        for pattern in surface.get("path_globs", []):
            covered.update(_contract_glob_matches(pattern))

    maintained = {
        str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        for path in (REPO_ROOT / "tests" / "contracts").rglob("*.json")
    }
    missing = sorted(maintained - covered)
    extra = sorted(covered - maintained)
    assert not missing, f"maintained contract specs missing from contract matrix: {missing}"
    assert not extra, f"contract matrix covers non-maintained specs: {extra}"


def test_archived_contract_specs_stay_out_of_maintained_contract_root() -> None:
    matrix = _load_json(CONTRACT_SYSTEM_MATRIX)
    archived_patterns: list[str] = []
    for surface in matrix.get("archived_surfaces", []):
        if isinstance(surface, dict):
            archived_patterns.extend(surface.get("path_globs", []))

    archived_matches: set[str] = set()
    for pattern in archived_patterns:
        archived_matches.update(_contract_glob_matches(pattern))

    assert archived_matches, "contract matrix should track archived contract provenance"
    assert all(path.startswith("tests/archive/contracts/") for path in archived_matches)
    assert not (REPO_ROOT / "tests" / "contracts" / "Archive").exists()


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
    broad_runtime_facade_files = (
        "tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py",
        "tests/architecture/runtime_facade/test_runtime_escape_hatches.py",
        "tests/architecture/runtime_facade/test_runtime_facade_contract_boundaries.py",
    )
    for broad_runtime_facade_file in broad_runtime_facade_files:
        assert broad_runtime_facade_file not in entries

    selected_nodes = [
        entry
        for entry in entries
        if any(entry.startswith(path + "::") for path in broad_runtime_facade_files)
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
