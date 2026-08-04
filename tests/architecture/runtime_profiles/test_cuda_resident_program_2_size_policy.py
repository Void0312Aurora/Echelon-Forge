from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HEADER_EXTENSIONS = {".cuh", ".h", ".hh", ".hpp"}
TEST_PATH_MARKERS = ("src/tests/", "tests/", "_probe.cpp")
POLICY_PATH = (
    ROOT / "docs/plan/exact_runtime/cuda_resident_runtime_program_2_size_policy_20260731.json"
)


def _policy() -> dict[str, object]:
    value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _scope_paths() -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "src/runtime/facade/internal/cuda_resident/**",
            "src/runtime/contracts/cuda_resident*",
            "src/tools/experimental/cuda_resident/**",
            "src/tests/test_cuda_resident*",
            "tests/architecture/runtime_profiles/test_cuda_resident*",
            "tests/runtime/facade/test_cuda_resident*",
            "tools/diagnostics/cuda_resident_cr2*",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    extensions = {
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".cu",
        ".cuh",
        ".h",
        ".hh",
        ".hpp",
        ".py",
    }
    return [
        path
        for path in completed.stdout.splitlines()
        if Path(path).suffix in extensions and (ROOT / path).is_file()
    ]


def _line_count(path: str) -> int:
    return len((ROOT / path).read_text(encoding="utf-8").splitlines())


def _line_limits(path: str, thresholds: dict[str, object]) -> tuple[int, int, int]:
    normalized = path.replace("\\", "/")
    if Path(normalized).suffix in HEADER_EXTENSIONS:
        prefix = "header"
    elif normalized.startswith(TEST_PATH_MARKERS) or "_probe.cpp" in normalized:
        prefix = "test"
    else:
        prefix = "implementation"
    return (
        int(thresholds[f"{prefix}_soft_lines"]),
        int(thresholds[f"{prefix}_review_lines"]),
        int(thresholds[f"{prefix}_hard_lines"]),
    )


def _artifact_paths(policy: dict[str, object]) -> list[str]:
    scope = policy["scope"]
    assert isinstance(scope, dict)
    prefixes = scope["artifact_path_prefixes"]
    assert isinstance(prefixes, list)
    normalized_prefixes = [str(prefix) for prefix in prefixes]
    tracked = subprocess.run(
        ["git", "ls-files", "--", "docs/plan/exact_runtime"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    paths = {
        path for path in tracked if any(path.startswith(prefix) for prefix in normalized_prefixes)
    }
    artifact_root = ROOT / "docs/plan/exact_runtime"
    for candidate in artifact_root.rglob("*"):
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(ROOT).as_posix()
        if any(relative.startswith(prefix) for prefix in normalized_prefixes):
            paths.add(relative)
    return sorted(paths)


def test_cr2_size_policy_is_explicit_and_self_consistent() -> None:
    policy = _policy()
    assert policy["schema_version"] == "cuda_resident.program2.size_policy.v1"
    assert policy["policy_id"] == "cr2.size_governance.20260731"
    assert policy["measurement"] == {
        "line_definition": "physical lines from tracked file bytes after checkout",
        "counter": "Python str.splitlines()",
        "compression_or_multistatement_lines_waive_policy": False,
    }
    thresholds = policy["thresholds"]
    assert isinstance(thresholds, dict)
    assert thresholds["implementation_soft_lines"] == 700
    assert thresholds["implementation_review_lines"] == 800
    assert thresholds["implementation_hard_lines"] == 1000
    assert thresholds["header_soft_lines"] == 600
    assert thresholds["header_review_lines"] == 800
    assert thresholds["test_soft_lines"] == 700
    assert thresholds["header_hard_lines"] == 1000
    assert thresholds["test_hard_lines"] == 1000
    assert thresholds["tracked_artifact_hard_bytes"] == 1_048_576


def test_cr2_split_inventory_and_watch_items_match_worktree_lines() -> None:
    policy = _policy()
    exceptions = policy["baseline_exceptions"]
    watch_items = policy["watch_items"]
    assert isinstance(exceptions, list)
    assert isinstance(watch_items, list)
    assert exceptions == []
    scope = _scope_paths()
    counts = {path: _line_count(path) for path in scope}
    thresholds = policy["thresholds"]
    assert isinstance(thresholds, dict)

    watch_map = {str(entry["path"]): entry for entry in watch_items if isinstance(entry, dict)}
    hard_violations = {
        path for path, lines in counts.items() if lines > _line_limits(path, thresholds)[2]
    }
    soft_or_higher = {
        path for path, lines in counts.items() if lines > _line_limits(path, thresholds)[0]
    }
    review_or_higher = {
        path for path, lines in counts.items() if lines >= _line_limits(path, thresholds)[1]
    }

    assert hard_violations == set()
    assert soft_or_higher == set(watch_map)
    assert review_or_higher == set()
    for path, entry in watch_map.items():
        assert counts[path] == entry["observed_lines"]
        assert entry["required_action"] == "no_growth_before_split_or_reclassification"

    inventory = policy["module_inventory"]
    assert isinstance(inventory, list)
    inventory_map = {str(entry["path"]): entry for entry in inventory if isinstance(entry, dict)}
    expected_inventory = {
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh": 291,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_math.cuh": 139,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_storage.cu": 547,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_barrier.cu": 264,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_phase_a.cu": 204,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_phase_b.cu": 497,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_phase_d.cu": 231,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_observation.cu": 441,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_state_readback.cu": 271,
        "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_window.cu": 69,
        "src/tests/test_cuda_resident_replay.cpp": 139,
        "src/tests/test_cuda_resident_replay_projection.cpp": 611,
        "src/tests/test_cuda_resident_replay_support.cpp": 175,
        "src/tests/test_cuda_resident_replay_support.h": 58,
        "src/runtime/contracts/cuda_resident_parity_release_contract.h": 244,
        "src/runtime/contracts/cuda_resident_full_window_contract.h": 118,
        "src/runtime/facade/internal/cuda_resident/cuda_resident_full_window_runner.cpp": 257,
        "src/tools/experimental/cuda_resident/cuda_resident_full_window_probe.cpp": 337,
        "src/tests/test_cuda_resident_full_window.cpp": 417,
        "tools/diagnostics/cuda_resident_cr2_parity_compare.py": 494,
        "tests/architecture/runtime_profiles/test_cuda_resident_cr2_parity.py": 239,
        "src/runtime/contracts/cuda_resident_resource_evidence_contract.h": 93,
        "src/tools/experimental/cuda_resident/cuda_resident_resource_probe.cpp": 350,
        "tools/diagnostics/cuda_resident_cr2_resource_evidence.py": 655,
        "tools/diagnostics/cuda_resident_cr2_resource_static.py": 116,
        "tests/architecture/runtime_profiles/test_cuda_resident_resource_evidence.py": 382,
        "src/runtime/contracts/cuda_resident_counter_evidence_contract.h": 58,
        "tools/diagnostics/cuda_resident_cr2_counter_evidence.py": 657,
        "tests/architecture/runtime_profiles/test_cuda_resident_counter_evidence.py": 255,
        "src/runtime/contracts/cuda_resident_matrix_contract.h": 107,
        "src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.h": 53,
        "src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.cpp": 288,
        "src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_probe.cpp": 475,
        "tools/diagnostics/cuda_resident_cr2_matrix_probe.py": 603,
        "tests/architecture/runtime_profiles/test_cuda_resident_cr2_matrix_probe.py": 450,
        "tools/diagnostics/cuda_resident_cr2_matrix_evidence.py": 620,
        "tools/diagnostics/cuda_resident_cr2_matrix_evidence_schema.py": 450,
        "tests/architecture/runtime_profiles/test_cuda_resident_cr2_matrix_evidence.py": 207,
    }
    assert set(inventory_map) == set(expected_inventory)
    for path, expected_lines in expected_inventory.items():
        assert counts[path] == expected_lines == inventory_map[path]["observed_lines"]
    assert not (
        ROOT / "src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda.cu"
    ).exists()


def test_cr2_tracked_cuda_evidence_and_plan_artifacts_stay_below_byte_cap() -> None:
    policy = _policy()
    hard_bytes = int(policy["thresholds"]["tracked_artifact_hard_bytes"])
    paths = _artifact_paths(policy)
    assert paths
    oversized = {
        path: (ROOT / path).stat().st_size
        for path in paths
        if (ROOT / path).stat().st_size > hard_bytes
    }
    assert oversized == {}
