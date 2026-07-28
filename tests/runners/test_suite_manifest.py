from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.testing.suite_manifest import (
    load_contract_suite_manifest,
    load_pytest_suite_manifest,
    pytest_entry_path,
    resolve_pytest_entry,
)


def _write_manifest(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_pytest_manifest_preserves_nodeid_and_tracks_missing_entries(
    tmp_path: Path,
) -> None:
    existing = tmp_path / "tests" / "test_example.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("def test_example():\n  assert True\n", encoding="utf-8")
    manifest_path = tmp_path / "suite.json"
    _write_manifest(
        manifest_path,
        {
            "name": "focused",
            "paths": [
                "tests/test_example.py::TestExample::test_case[param]",
                "tests/test_missing.py::test_missing",
            ],
        },
    )

    manifest = load_pytest_suite_manifest(manifest_path, tmp_path)

    assert manifest.name == "focused"
    assert manifest.entries[0].resolved == (f"{existing}::TestExample::test_case[param]")
    assert manifest.entries[0].check_path == str(existing)
    assert [entry.raw for entry in manifest.missing_entries] == [
        "tests/test_missing.py::test_missing"
    ]
    assert pytest_entry_path(manifest.entries[0].raw) == "tests/test_example.py"


def test_pytest_entry_rejects_empty_nodeid_suffix(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="node ID suffix must be non-empty"):
        resolve_pytest_entry("tests/test_example.py::", tmp_path)


@pytest.mark.parametrize("invalid_entry", [None, 7, {"path": "tests/test.py"}])
def test_pytest_manifest_rejects_non_string_entries(
    tmp_path: Path,
    invalid_entry: object,
) -> None:
    manifest_path = tmp_path / "suite.json"
    _write_manifest(manifest_path, {"paths": [invalid_entry]})

    with pytest.raises(TypeError, match="pytest suite path entries must be strings"):
        load_pytest_suite_manifest(manifest_path, tmp_path)


def test_contract_manifest_accepts_paths_alias_and_validates_entries(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "contract_suite.json"
    _write_manifest(
        manifest_path,
        {"paths": ["tests/contracts/unit/example.json"]},
    )

    manifest = load_contract_suite_manifest(manifest_path, tmp_path)

    assert [entry.resolved for entry in manifest.entries] == [
        str(tmp_path / "tests" / "contracts" / "unit" / "example.json")
    ]


def test_audit_callers_can_load_empty_manifests(tmp_path: Path) -> None:
    pytest_path = tmp_path / "pytest_suite.json"
    contract_path = tmp_path / "contract_suite.json"
    _write_manifest(pytest_path, {"paths": []})
    _write_manifest(contract_path, {"specs": []})

    assert load_pytest_suite_manifest(pytest_path, tmp_path, allow_empty=True).entries == ()
    assert load_contract_suite_manifest(contract_path, tmp_path, allow_empty=True).entries == ()
