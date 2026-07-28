from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SuiteEntry:
    raw: str
    resolved: str
    check_path: str

    @property
    def missing(self) -> bool:
        return not os.path.exists(self.check_path)


@dataclass(frozen=True)
class SuiteManifest:
    path: str
    name: str
    entries: tuple[SuiteEntry, ...]

    @property
    def missing_entries(self) -> tuple[SuiteEntry, ...]:
        return tuple(entry for entry in self.entries if entry.missing)


def resolve_repo_or_abs(
    path: str | os.PathLike[str],
    repo_root: str | os.PathLike[str],
    *,
    empty_message: str = "suite path entries must be non-empty",
) -> str:
    raw = os.fspath(path).strip()
    if not raw:
        raise ValueError(empty_message)
    if os.path.isabs(raw):
        return os.path.abspath(raw)
    normalized_parts = raw.replace("\\", "/").split("/")
    return os.path.abspath(os.path.join(os.fspath(repo_root), *normalized_parts))


def pytest_entry_path(entry: str) -> str:
    raw = _validated_entry(entry, entry_kind="pytest suite path")
    path_part, separator, node_part = raw.partition("::")
    if separator and not node_part.strip():
        raise ValueError("pytest suite node ID suffix must be non-empty")
    return path_part.replace("\\", "/")


def resolve_pytest_entry(
    entry: str,
    repo_root: str | os.PathLike[str],
) -> SuiteEntry:
    raw = _validated_entry(entry, entry_kind="pytest suite path")
    path_part, separator, node_part = raw.partition("::")
    if separator and not node_part.strip():
        raise ValueError("pytest suite node ID suffix must be non-empty")
    resolved_path = resolve_repo_or_abs(
        path_part,
        repo_root,
        empty_message="pytest suite path entries must be non-empty",
    )
    resolved = resolved_path
    if separator:
        resolved = f"{resolved_path}{separator}{node_part}"
    return SuiteEntry(raw=raw, resolved=resolved, check_path=resolved_path)


def load_pytest_suite_manifest(
    path: str | os.PathLike[str],
    repo_root: str | os.PathLike[str],
    *,
    allow_empty: bool = False,
) -> SuiteManifest:
    suite_path = resolve_repo_or_abs(path, repo_root)
    suite = load_suite_object(suite_path)
    raw_entries = _manifest_entries(
        suite,
        suite_path=suite_path,
        keys=("paths",),
        suite_kind="pytest suite",
        entry_kind="pytest suite path",
        allow_empty=allow_empty,
    )
    entries = tuple(resolve_pytest_entry(entry, repo_root) for entry in raw_entries)
    return SuiteManifest(
        path=suite_path,
        name=_suite_name(suite, suite_path),
        entries=entries,
    )


def load_contract_suite_manifest(
    path: str | os.PathLike[str],
    repo_root: str | os.PathLike[str],
    *,
    allow_empty: bool = False,
) -> SuiteManifest:
    suite_path = resolve_repo_or_abs(
        path,
        repo_root,
        empty_message="contract suite path entries must be non-empty",
    )
    suite = load_suite_object(suite_path, object_kind="contract suite")
    raw_entries = _manifest_entries(
        suite,
        suite_path=suite_path,
        keys=("specs", "paths"),
        suite_kind="contract suite",
        entry_kind="contract suite spec",
        allow_empty=allow_empty,
    )
    entries: list[SuiteEntry] = []
    for entry in raw_entries:
        resolved = resolve_repo_or_abs(
            entry,
            repo_root,
            empty_message="contract suite spec entries must be non-empty",
        )
        entries.append(SuiteEntry(raw=entry, resolved=resolved, check_path=resolved))
    return SuiteManifest(
        path=suite_path,
        name=_suite_name(suite, suite_path),
        entries=tuple(entries),
    )


def load_suite_object(
    path: str | os.PathLike[str],
    *,
    object_kind: str = "suite",
) -> dict[str, Any]:
    suite_path = os.fspath(path)
    with open(suite_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"expected {object_kind} JSON object at {suite_path!r}")
    return data


def _manifest_entries(
    suite: dict[str, Any],
    *,
    suite_path: str,
    keys: tuple[str, ...],
    suite_kind: str,
    entry_kind: str,
    allow_empty: bool,
) -> tuple[str, ...]:
    raw_entries: Any = []
    selected_key = keys[0]
    for key in keys:
        if key in suite:
            raw_entries = suite[key]
            selected_key = key
            break
    if not isinstance(raw_entries, list):
        raise TypeError(f"{suite_kind} {suite_path!r} has non-list '{selected_key}'")
    if not raw_entries and not allow_empty:
        raise ValueError(f"{suite_kind} {suite_path!r} has no non-empty '{keys[0]}' list")
    return tuple(_validated_entry(entry, entry_kind=entry_kind) for entry in raw_entries)


def _validated_entry(entry: object, *, entry_kind: str) -> str:
    if not isinstance(entry, str):
        raise TypeError(f"{entry_kind} entries must be strings")
    raw = entry.strip()
    if not raw:
        raise ValueError(f"{entry_kind} entries must be non-empty")
    return raw


def _suite_name(suite: dict[str, Any], suite_path: str) -> str:
    return str(suite.get("name", Path(suite_path).stem))
