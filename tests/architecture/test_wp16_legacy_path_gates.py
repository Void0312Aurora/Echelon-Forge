from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "architecture"
    / "fixtures"
    / "wp16_runtime_spine_inventory_20260521.json"
)


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _entries_by_path() -> dict[str, dict]:
    return {entry["path"]: entry for entry in _load_fixture()["entries"]}


def test_wp16_legacy_gate_key_paths_have_bounded_status_owner_gate_and_reason() -> None:
    entries = _entries_by_path()
    expected = {
        "src/core/engine/world_batch_runtime.h": "deprecated_candidate",
        "src/core/engine/world_batch_runtime.cpp": "deprecated_candidate",
        "python/rl/runtime/world_batch/compat.py": "compatibility_wrapper",
        "src/runtime/facade/runtime_facade.h": "compatibility_wrapper",
        "tests/runtime/engagement/test_facade_engagement_export.py": "diagnostics_only",
    }

    for path, classification in expected.items():
        entry = entries[path]
        assert entry["classification"] == classification
        assert entry["owner"].strip()
        assert entry["next_gate"].strip()
        assert entry["reason"].strip()


def test_wp16_legacy_gate_preserves_public_compatibility_surfaces_until_replacement_gate() -> None:
    entries = _entries_by_path()
    facade_header = (
        REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h"
    ).read_text(encoding="utf-8")
    vec_env_source = (
        REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py"
    ).read_text(encoding="utf-8")
    compat_source = (
        REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "compat.py"
    ).read_text(encoding="utf-8")

    facade_entry = entries["src/runtime/facade/runtime_facade.h"]
    compat_entry = entries["python/rl/runtime/world_batch/compat.py"]

    assert facade_entry["classification"] == "compatibility_wrapper"
    assert compat_entry["classification"] == "compatibility_wrapper"
    assert "WorldBatchRuntime& runtime_compatibility_quarantine() noexcept;" in facade_header
    assert "Compatibility escape hatch for diagnostics and legacy adapters only." in facade_header
    assert "def batch_runtime(self):" in vec_env_source
    assert "Compatibility-only view for callers that still expect `vec_env.batch_runtime`." in compat_source


def test_wp16_legacy_gate_runtime_world_escape_hatch_is_bounded_to_diagnostics_or_compatibility() -> None:
    entries = _entries_by_path()
    facade_header = (
        REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h"
    ).read_text(encoding="utf-8")
    diagnostics_test = (
        REPO_ROOT / "tests" / "runtime" / "engagement" / "test_facade_engagement_export.py"
    ).read_text(encoding="utf-8")
    adapter_source = (
        REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
    ).read_text(encoding="utf-8")

    assert entries["src/runtime/facade/runtime_facade.h"]["classification"] == "compatibility_wrapper"
    assert entries["tests/runtime/engagement/test_facade_engagement_export.py"]["classification"] == "diagnostics_only"
    assert "RuntimeFacade::run_wp10_window" in _load_fixture()["selected_spine_slice"]["window_api"]
    assert "WorldBatchRuntime& runtime_compatibility_quarantine() noexcept;" in facade_header
    assert "self.runtime_compatibility_enabled = normalize_runtime_compatibility_enabled(runtime_compatibility_enabled)" in adapter_source
    assert "def _batch_target(self):" in adapter_source
    assert "self._batch_target().step_batch()" in adapter_source
    assert "world = facade.runtime_compatibility_quarantine().world_compatibility_quarantine(0)" in diagnostics_test
    assert "escape hatches" in entries["tests/runtime/engagement/test_facade_engagement_export.py"]["reason"]


def test_wp16_legacy_gate_diagnostics_and_unknown_paths_never_count_as_maintained() -> None:
    entries = list(_load_fixture()["entries"])
    diagnostics_or_unknown = [
        entry
        for entry in entries
        if entry["classification"] in {"diagnostics_only", "unknown_requires_owner"}
    ]

    assert diagnostics_or_unknown
    for entry in diagnostics_or_unknown:
        assert entry["classification"] != "maintained_spine"
        assert entry["owner"].strip()
        assert entry["next_gate"].strip()
        assert entry["reason"].strip()
        assert "maintained" not in entry["classification"]

    unknown_entries = [
        entry for entry in diagnostics_or_unknown if entry["classification"] == "unknown_requires_owner"
    ]
    assert unknown_entries, "expected explicit unknown_requires_owner coverage"
    for entry in unknown_entries:
        assert "packet" in entry["reason"] or "barrier" in entry["reason"] or "trace" in entry["reason"]


def test_wp16_legacy_gate_deprecated_candidates_have_replacement_clue_or_next_gate() -> None:
    fixture = _load_fixture()
    entries = fixture["entries"]
    replacement_clues = set(fixture["selected_spine_slice"]["window_api"])
    deprecated_entries = [
        entry for entry in entries if entry["classification"] == "deprecated_candidate"
    ]

    assert deprecated_entries, "expected deprecated candidate coverage"
    assert "RuntimeFacade::run_wp10_window" in replacement_clues
    assert "RuntimeFacade::export_observation_packet" in replacement_clues

    for entry in deprecated_entries:
        has_next_gate = bool(entry["next_gate"].strip())
        has_replacement_clue = any(clue in entry["reason"] for clue in replacement_clues)
        assert has_next_gate or has_replacement_clue
        assert entry["owner"] == "WP16-D"
        assert "bypass" in entry["reason"] or "direct" in entry["reason"] or "raw" in entry["reason"]


def test_wp16_legacy_gate_compatibility_and_diagnostics_paths_do_not_upgrade_to_maintained_via_names() -> None:
    entries = _entries_by_path()
    allowed_non_maintained = {
        "python/rl/runtime/world_batch/compat.py",
        "src/runtime/facade/runtime_facade.h",
        "tests/runtime/engagement/test_facade_engagement_export.py",
        "tests/runtime/engagement/test_diagnostics_trace_contract.py",
        "tests/training/test_cooperative_diagnostics_callback.py",
    }

    for path in allowed_non_maintained:
        assert entries[path]["classification"] != "maintained_spine"

    assert entries["python/rl/runtime/world_batch/compat.py"]["classification"] == "compatibility_wrapper"
    assert entries["tests/runtime/engagement/test_diagnostics_trace_contract.py"]["classification"] == "diagnostics_only"
    assert entries["tests/training/test_cooperative_diagnostics_callback.py"]["classification"] == "unknown_requires_owner"
