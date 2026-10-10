from __future__ import annotations

import json

import pytest

from python.experiment.definition import (
    ConfigComposition,
    EvaluationProtocol,
    Experiment,
    ExperimentRegistry,
    ScenarioRef,
    SeedSpec,
)
from python.experiment.resolved_input_lock import (
    InputLockError,
    build_resolved_input_lock,
    compare_resolved_input_locks,
)


def _registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.register_config_base("air_base_v1", {"mode": "air", "n_envs": 1})
    registry.register_evaluation_protocol(EvaluationProtocol("smoke", "bounded smoke"))
    return registry


def _experiment(seeds: SeedSpec | None = None) -> Experiment:
    return Experiment(
        "air_lock_v1",
        ScenarioRef("scenarios/test/test_free_fall.json"),
        ConfigComposition("air_base_v1", {"n_envs": 2}),
        seeds or SeedSpec((101, 103)),
        "smoke",
    )


def test_lock_is_canonical_under_scenario_json_key_order(tmp_path) -> None:
    path = tmp_path / "scenarios/test/test_free_fall.json"
    path.parent.mkdir(parents=True)
    first = {"b": 2, "a": {"z": 1, "y": 0}}
    path.write_text(json.dumps(first), encoding="utf-8")
    left = build_resolved_input_lock(
        _experiment(), _registry(), repo_root=tmp_path,
        dependencies={"scenario": "sha:ignored-by-content"},
        native_runtime={"realized_topology_digest": "topo-1"},
    )
    path.write_text(json.dumps({"a": {"y": 0, "z": 1}, "b": 2}), encoding="utf-8")
    right = build_resolved_input_lock(
        _experiment(), _registry(), repo_root=tmp_path,
        dependencies={"scenario": "sha:ignored-by-content"},
        native_runtime={"realized_topology_digest": "topo-1"},
    )
    assert left.digest == right.digest


def test_empty_declared_seeds_require_effective_seed_record() -> None:
    with pytest.raises(InputLockError, match="effective_seed_set_required"):
        build_resolved_input_lock(_experiment(SeedSpec()), _registry())
    lock = build_resolved_input_lock(
        _experiment(SeedSpec()), _registry(), effective_seeds=(7, 11)
    )
    assert lock.as_dict()["input_lock"]["effective_seed_set"] == [7, 11]


def test_dependency_order_does_not_change_identity() -> None:
    left = build_resolved_input_lock(
        _experiment(), _registry(),
        dependencies={"content": "sha:content", "policy": {"id": "p.v1", "digest": "d"}},
    )
    right = build_resolved_input_lock(
        _experiment(), _registry(),
        dependencies={"policy": {"digest": "d", "id": "p.v1"}, "content": "sha:content"},
    )
    assert left.digest == right.digest


def test_missing_scenario_is_rejected_when_root_is_supplied(tmp_path) -> None:
    with pytest.raises(InputLockError, match="does not exist"):
        build_resolved_input_lock(_experiment(), _registry(), repo_root=tmp_path)


def test_candidate_status_is_not_claimed_comparable() -> None:
    candidate = build_resolved_input_lock(_experiment(), _registry())
    assert compare_resolved_input_locks(candidate, candidate).comparable is False


def test_failed_or_unknown_runs_are_not_comparable() -> None:
    failed = build_resolved_input_lock(_experiment(), _registry(), status="failed")
    unknown = build_resolved_input_lock(_experiment(), _registry(), status="unknown")
    result = compare_resolved_input_locks(failed, unknown)
    assert result.comparable is False
    assert result.differences == ("status",)


def test_completed_locks_require_same_realized_topology() -> None:
    left = build_resolved_input_lock(
        _experiment(), _registry(), status="completed",
        native_runtime={"realized_topology_digest": "topo-a"},
    )
    right = build_resolved_input_lock(
        _experiment(), _registry(), status="completed",
        native_runtime={"realized_topology_digest": "topo-b"},
    )
    result = compare_resolved_input_locks(left, right)
    assert result.comparable is False
    assert result.differences == ("realized_topology_digest",)


def test_policy_only_axis_can_be_declared_intentional() -> None:
    left = build_resolved_input_lock(
        _experiment(), _registry(), status="completed",
        policy={"id": "policy-a"},
        native_runtime={"realized_topology_digest": "topo-a"},
    )
    right = build_resolved_input_lock(
        _experiment(), _registry(), status="completed",
        policy={"id": "policy-b"},
        native_runtime={"realized_topology_digest": "topo-a"},
    )
    result = compare_resolved_input_locks(left, right, intentional_axes=frozenset({"policy"}))
    assert result.comparable is True
