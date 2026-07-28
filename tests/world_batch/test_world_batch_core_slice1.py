"""Load-bearing tests for the I83 WorldBatchCore slice 1 seam.

The tests stay independent of a live scenario for the new owner itself.  The
single/leader/cooperative runtime suites exercise the real callers; these
pins cover the shared packet/evidence transformations and their fail-closed
boundary so a future extraction cannot silently broaden the seam.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from python.rl.runtime.world_batch.core import WorldBatchCore


_REPO_ROOT = Path(__file__).resolve().parents[2]


def _packet(*, truth=None, inst=None):
    return SimpleNamespace(
        agent_observations=[] if truth is None else truth,
        instrument_states=[] if inst is None else inst,
    )


def test_extract_observation_batch_preserves_packet_order_and_values() -> None:
    truth = ["truth-0", "truth-1"]
    inst = ["inst-0", "inst-1"]

    actual_truth, actual_inst = WorldBatchCore.extract_observation_batch(
        _packet(truth=truth, inst=inst),
        consumer="slice1-test",
    )

    assert actual_truth == truth
    assert actual_inst == inst
    assert actual_truth is not truth
    assert actual_inst is not inst


def test_extract_observation_pair_fails_closed_on_missing_payload() -> None:
    with pytest.raises(RuntimeError, match="required payload"):
        WorldBatchCore.extract_observation_pair(
            _packet(truth=["truth-only"]),
            consumer="slice1-test",
            missing_message="slice1-test required payload",
        )


def test_extract_observation_batch_can_preserve_cooperative_empty_packet_behavior() -> None:
    assert WorldBatchCore.extract_observation_batch(
        _packet(),
        consumer="cooperative slot state readers",
        require_payload=False,
    ) == ([], [])


def test_record_observation_state_only_updates_mirror_fields() -> None:
    handle = SimpleNamespace(steps=7, loader=SimpleNamespace(steps=7))

    WorldBatchCore.record_observation_state(
        handle,
        truth="truth",
        inst="instrument",
    )

    assert handle.last_truth == "truth"
    assert handle.last_inst == "instrument"
    assert handle.steps == 7
    assert handle.loader.steps == 7


def test_loader_runtime_is_the_i73_typed_sim_boundary() -> None:
    runtime = SimpleNamespace(get_time_step=lambda: 0.05)
    loader = SimpleNamespace(sim=runtime)

    assert WorldBatchCore.loader_runtime(loader) is runtime

    with pytest.raises(AttributeError):
        WorldBatchCore.loader_runtime(SimpleNamespace())


def test_runtime_window_evidence_projection_matches_maintained_info_shape() -> None:
    evidence = SimpleNamespace(
        barrier_trace=[SimpleNamespace(barrier_id="input"), SimpleNamespace(barrier_id="export")],
        observation_packet=SimpleNamespace(
            barrier_id="export",
            provenance=SimpleNamespace(source_label="facade_observation_packet"),
        ),
        engagement_packet=SimpleNamespace(
            barrier_id="export",
            packet_provenance=SimpleNamespace(source_label="track_state_packet"),
            diagnostics_provenance=SimpleNamespace(source_label="world_truth_diagnostics"),
        ),
        cadence_reason="selected_slice_cadence_trace_runtime_window",
        uses_compat_fallback=False,
    )

    assert WorldBatchCore.runtime_window_evidence_info(evidence) == {
        "barrier_ids": ["input", "export"],
        "event_barrier_id": "export",
        "observation_barrier_id": "export",
        "observation_provenance": "facade_observation_packet",
        "engagement_provenance": "track_state_packet",
        "diagnostics_provenance": "world_truth_diagnostics",
        "cadence_reason": "selected_slice_cadence_trace_runtime_window",
        "uses_compat_fallback": False,
    }


def test_slice1_owner_stays_domain_free_and_all_three_modes_consume_it() -> None:
    core_path = _REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "core.py"
    tree = ast.parse(core_path.read_text(encoding="utf-8"))
    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    imports.extend(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert not any(name.split(".", 1)[0] == "gym_envs" for name in imports)

    callers = {
        "single": _REPO_ROOT / "python" / "rl" / "runtime" / "single_world_batch_runtime.py",
        "leader": _REPO_ROOT / "python" / "rl" / "runtime" / "leader_world_batch_runtime.py",
        "cooperative": _REPO_ROOT / "python" / "rl" / "runtime" / "cooperative_world_batch_vec_env.py",
    }
    for mode, path in callers.items():
        source = path.read_text(encoding="utf-8")
        assert "WorldBatchCore.extract_observation" in source, mode
        assert "WorldBatchCore.record_observation_state" in source, mode

    assert "WorldBatchCore.runtime_window_evidence_info" in callers["single"].read_text(encoding="utf-8")
    assert "WorldBatchCore.runtime_window_evidence_info" in callers["leader"].read_text(encoding="utf-8")
