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
RUNTIME_WINDOW_HELPERS = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "facade"
    / "runtime_window_coordinator_helpers.h"
)
COUNTERFACTUAL_CONSTANTS = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "contracts"
    / "counterfactual_replay_contract_constants.h"
)

EXPECTED_CLASSIFICATIONS = {
    "src/runtime/facade/runtime_window_coordinator.h": "maintained_spine",
    "src/runtime/contracts/stage_node_manifest_registry.h": "maintained_spine",
    "tests/runtime/facade/test_runtime_facade_window_loop_injection.py": "maintained_spine",
    "tests/runtime/bindings/test_bindings_engagement_surface.py": "maintained_spine",
    "src/runtime/facade/runtime_facade.h": "maintained_spine",
    "src/runtime/facade/runtime_facade.cpp": "compatibility_wrapper",
    "python/rl/runtime/world_batch/adapter.py": "compatibility_wrapper",
    "python/rl/runtime/world_batch_vec_env.py": "compatibility_wrapper",
    "python/rl/runtime/world_batch/runtime_access.py": "compatibility_wrapper",
    "python/rl/runtime/world_batch/runtime_support.py": "compatibility_wrapper",
    "python/rl/runtime/leader_world_batch_runtime.py": "compatibility_wrapper",
    "python/rl/runtime/single_world_batch_runtime.py": "compatibility_wrapper",
    "python/rl/runtime/leader_window_runtime.py": "compatibility_wrapper",
    "src/runtime/contracts/platform_capability_contracts.h": "compatibility_wrapper",
    "src/core/engine/world_batch_runtime.h": "deprecated_candidate",
    "src/core/engine/world_batch_runtime.cpp": "deprecated_candidate",
    "tests/world_batch/test_world_batch_runtime.py": "deprecated_candidate",
    "tests/world_batch/test_world_batch_vec_env.py": "compatibility_wrapper",
    "tests/runtime/engagement/test_facade_engagement_export.py": "diagnostics_only",
    "tests/runtime/engagement/test_diagnostics_trace_contract.py": "diagnostics_only",
    "tests/diagnostics/test_diagnostics_import_order.py": "diagnostics_only",
    "python/scenario/compiler/generation_request.py": "blocked",
    "src/runtime/contracts/counterfactual_replay_contracts.h": "blocked",
    "tests/training/test_cooperative_diagnostics_callback.py": "unknown_requires_owner",
}

EXPECTED_SELECTED_NODES = [
    "p7.fire_control_launch.v1",
    "p9.effects_damage.v1",
    "p10.observation_export.v1",
]
EXPECTED_EXCLUDED_NODES = [
    "p7.launch_request_adapter_compat.v1",
    "p10.observation_trace_diagnostics.v1",
]
EXPECTED_SELECTED_BARRIERS = [
    "input_injection",
    "window_commit",
    "export",
]
EXPECTED_RESERVED_BARRIERS = ["stage_publish"]


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _entries_by_path() -> dict[str, dict]:
    entries = _load_fixture()["entries"]
    return {entry["path"]: entry for entry in entries}


def test_wp16_fixture_uses_only_canonical_classification_vocabulary() -> None:
    fixture = _load_fixture()
    allowed = set(fixture["allowed_classifications"])
    assert allowed == {
        "maintained_spine",
        "compatibility_wrapper",
        "diagnostics_only",
        "deprecated_candidate",
        "blocked",
        "unknown_requires_owner",
    }

    for entry in fixture["entries"]:
        assert entry["classification"] in allowed


def test_wp16_fixture_covers_required_candidate_paths_with_anchored_classifications() -> None:
    entries = _entries_by_path()
    assert set(EXPECTED_CLASSIFICATIONS).issubset(entries)

    for path, expected_classification in EXPECTED_CLASSIFICATIONS.items():
        assert entries[path]["classification"] == expected_classification


def test_wp16_fixture_entries_reference_real_files_and_code_markers() -> None:
    for path, entry in _entries_by_path().items():
        file_path = REPO_ROOT / path
        assert file_path.is_file(), f"missing inventory path: {path}"
        source = file_path.read_text(encoding="utf-8")
        for marker in entry["evidence_markers"]:
            assert marker in source, f"{path} missing evidence marker: {marker}"


def test_wp16_non_maintained_entries_have_owner_gate_reason_and_unknown_stays_non_maintained() -> None:
    unknown_entries: list[dict] = []
    for entry in _load_fixture()["entries"]:
        if entry["classification"] != "maintained_spine":
            assert entry["owner"].strip()
            assert entry["next_gate"].strip()
            assert entry["reason"].strip()
        if entry["classification"] == "unknown_requires_owner":
            unknown_entries.append(entry)

    assert unknown_entries, "expected at least one explicit unknown_requires_owner path"
    for entry in unknown_entries:
        assert entry["classification"] != "maintained_spine"
        assert "packet" in entry["reason"] or "barrier" in entry["reason"] or "trace" in entry["reason"]


def test_wp16_selected_slice_matches_runtime_window_and_manifest_clues() -> None:
    fixture = _load_fixture()
    selected = fixture["selected_spine_slice"]

    assert selected["node_ids"] == EXPECTED_SELECTED_NODES
    assert selected["excluded_node_ids"] == EXPECTED_EXCLUDED_NODES
    assert selected["barrier_ids"] == EXPECTED_SELECTED_BARRIERS
    assert selected["reserved_barrier_ids"] == EXPECTED_RESERVED_BARRIERS
    assert selected["window_api"] == [
        "RuntimeFacade::run_wp10_window",
        "RuntimeFacade::export_observation_packet",
        "RuntimeFacade::export_engagement_event_packet",
        "RuntimeFacade::export_diagnostics_traces",
    ]

    runtime_facade_header = (
        REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h"
    ).read_text(encoding="utf-8")
    runtime_window_source = (
        REPO_ROOT / "src" / "runtime" / "facade" / "runtime_window_coordinator.h"
    ).read_text(encoding="utf-8")
    runtime_window_helper_source = RUNTIME_WINDOW_HELPERS.read_text(encoding="utf-8")
    manifest_source = (
        REPO_ROOT / "src" / "runtime" / "contracts" / "stage_node_manifest_registry.h"
    ).read_text(encoding="utf-8")

    assert "run_wp10_window" in runtime_facade_header
    for barrier_id in EXPECTED_SELECTED_BARRIERS + EXPECTED_RESERVED_BARRIERS:
        assert barrier_id in runtime_window_source or barrier_id in runtime_window_helper_source
    for node_id in EXPECTED_SELECTED_NODES + EXPECTED_EXCLUDED_NODES:
        assert node_id in manifest_source


def test_wp16_blocked_and_compatibility_entries_do_not_hide_maintained_default_claims() -> None:
    entries = _entries_by_path()

    assert entries["python/scenario/compiler/generation_request.py"]["classification"] == "blocked"
    assert entries["src/runtime/contracts/counterfactual_replay_contracts.h"]["classification"] == "blocked"
    assert entries["src/runtime/facade/runtime_facade.h"]["classification"] == "maintained_spine"
    assert entries["python/rl/runtime/world_batch/adapter.py"]["classification"] == "compatibility_wrapper"

    facade_header = (
        REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h"
    ).read_text(encoding="utf-8")
    adapter_source = (
        REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
    ).read_text(encoding="utf-8")
    generation_request_source = (
        REPO_ROOT / "python" / "scenario" / "compiler" / "generation_request.py"
    ).read_text(encoding="utf-8")
    replay_source = (
        REPO_ROOT / "src" / "runtime" / "contracts" / "counterfactual_replay_contracts.h"
    ).read_text(encoding="utf-8")
    replay_constants_source = COUNTERFACTUAL_CONSTANTS.read_text(encoding="utf-8")

    assert "runtime_compatibility_quarantine() noexcept" not in facade_header
    assert "self.facade.runtime_compatibility_quarantine()" not in adapter_source
    assert "authoritative_state_mutation_allowed: bool = False" in generation_request_source
    assert "metadata_only" in replay_source or "metadata_only" in replay_constants_source
