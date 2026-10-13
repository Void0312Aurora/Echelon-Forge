from __future__ import annotations

import json
import hashlib
from pathlib import Path

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
    ResolvedInputLock,
    build_resolved_input_lock,
    compare_resolved_input_locks,
    join_run_receipt,
    join_run_receipt_path,
    project_compiled_scenario_dependencies,
)
from python.scenario.compiler import ScenarioCompiler
from python.tasking_contracts.failure_domains import (
    WorldOutcome,
    WorldState,
    build_batch_outcome,
    project_unresolved_batch_fault,
)
from tools.maintenance.runtime_run_receipt import build_run_receipt


def test_input_lock_rejects_mutated_compiler_snapshot_with_unchanged_source(tmp_path):
    path = tmp_path / "scenario.json"
    path.write_text('{"entities": [], "meta": {"stage": "qualification"}}', encoding="utf-8")
    compiled = ScenarioCompiler.compile_path(str(path))
    original_mtimes = compiled.dependency_mtimes_ns
    compiled.merged_scenario_data["meta"]["stage"] = "changed"
    assert compiled.dependency_mtimes_ns == original_mtimes
    with pytest.raises(InputLockError, match="dependencies_stale"):
        project_compiled_scenario_dependencies(compiled, repo_root=tmp_path)


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


def _native(topology: str = "topo-a") -> dict[str, str]:
    return {
        "resolved_manifest_sha256": "1" * 64,
        "executable_graph_sha256": "2" * 64,
        "realized_topology_digest": hashlib.sha256(topology.encode()).hexdigest(),
    }


def _receipt(candidate):
    vector = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "tests/architecture/composition/fixtures/run_receipt.v1.json"
        ).read_text(encoding="utf-8")
    )
    payload = json.loads(vector["canonical_envelope_json"])["payload"]
    payload["inputs"]["artifacts"]["resolved_input_lock"] = candidate.digest
    payload["execution_scope"]["world_ids"] = ["world-1", "world-2"]
    return build_run_receipt(**payload)


def _completed_lock(*args, **kwargs):
    """Synthetic owner receipt fixture, not a claim of an actual run."""
    native = kwargs.pop("native_runtime", _native())
    candidate = build_resolved_input_lock(*args, **kwargs)
    outcome = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(
            WorldOutcome(0, WorldState.COMPLETED, True),
            WorldOutcome(1, WorldState.COMPLETED, True),
        ),
        expected_world_indices=frozenset({0, 1}),
    )
    return join_run_receipt(
        candidate, receipt=_receipt(candidate), native_runtime=native, outcome=outcome
    )


def test_lock_is_canonical_under_scenario_json_key_order(tmp_path) -> None:
    path = tmp_path / "scenarios/test/test_free_fall.json"
    path.parent.mkdir(parents=True)
    first = {"b": 2, "a": {"z": 1, "y": 0}}
    path.write_text(json.dumps(first), encoding="utf-8")
    left = build_resolved_input_lock(
        _experiment(),
        _registry(),
        repo_root=tmp_path,
        dependencies={"scenario": "sha:ignored-by-content"},
        native_runtime={"realized_topology_digest": "topo-1"},
    )
    path.write_text(json.dumps({"a": {"y": 0, "z": 1}, "b": 2}), encoding="utf-8")
    right = build_resolved_input_lock(
        _experiment(),
        _registry(),
        repo_root=tmp_path,
        dependencies={"scenario": "sha:ignored-by-content"},
        native_runtime={"realized_topology_digest": "topo-1"},
    )
    assert left.digest == right.digest


def test_empty_declared_seeds_require_effective_seed_record() -> None:
    with pytest.raises(InputLockError, match="effective_seed_set_required"):
        build_resolved_input_lock(_experiment(SeedSpec()), _registry())
    lock = build_resolved_input_lock(_experiment(SeedSpec()), _registry(), effective_seeds=(7, 11))
    assert lock.as_dict()["input_lock"]["effective_seed_set"] == [7, 11]


def test_dependency_order_does_not_change_identity() -> None:
    left = build_resolved_input_lock(
        _experiment(),
        _registry(),
        dependencies={"content": "sha:content", "policy": {"id": "p.v1", "digest": "d"}},
    )
    right = build_resolved_input_lock(
        _experiment(),
        _registry(),
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
    left = _completed_lock(
        _experiment(),
        _registry(),
        status="completed",
        native_runtime=_native("topo-a"),
    )
    right = _completed_lock(
        _experiment(),
        _registry(),
        status="completed",
        native_runtime=_native("topo-b"),
    )
    result = compare_resolved_input_locks(left, right)
    assert result.comparable is False
    assert result.differences == ("realized_topology_digest",)


def test_policy_only_axis_can_be_declared_intentional() -> None:
    left = _completed_lock(
        _experiment(),
        _registry(),
        status="completed",
        policy={"id": "policy-a"},
        native_runtime=_native("topo-a"),
    )
    right = _completed_lock(
        _experiment(),
        _registry(),
        status="completed",
        policy={"id": "policy-b"},
        native_runtime=_native("topo-a"),
    )
    result = compare_resolved_input_locks(left, right, intentional_axes=frozenset({"policy"}))
    assert result.comparable is True


def test_completed_comparison_requires_complete_native_identity() -> None:
    left = _completed_lock(
        _experiment(),
        _registry(),
        status="completed",
        native_runtime={"realized_topology_digest": _native()["realized_topology_digest"]},
    )
    right = _completed_lock(
        _experiment(),
        _registry(),
        status="completed",
        native_runtime=_native("topo-a"),
    )
    result = compare_resolved_input_locks(left, right)
    assert result.comparable is False
    assert result.differences == ("executable_graph_sha256", "resolved_manifest_sha256")


def test_completed_comparison_checks_manifest_and_executable_identity() -> None:
    left_native = _native()
    right_native = _native()
    right_native["resolved_manifest_sha256"] = "3" * 64
    right_native["executable_graph_sha256"] = "4" * 64
    left = _completed_lock(
        _experiment(), _registry(), status="completed", native_runtime=left_native
    )
    right = _completed_lock(
        _experiment(), _registry(), status="completed", native_runtime=right_native
    )
    result = compare_resolved_input_locks(left, right)
    assert result.comparable is False
    assert result.differences == ("executable_graph_sha256", "resolved_manifest_sha256")


def test_lock_is_deeply_immutable_and_run_evidence_does_not_change_input_identity() -> None:
    candidate = build_resolved_input_lock(_experiment(), _registry())
    completed = _completed_lock(_experiment(), _registry())
    assert candidate.digest == completed.digest
    with pytest.raises(TypeError):
        candidate.document["input_lock"]["config"]["n_envs"] = 50


def test_claimed_completed_status_without_owner_receipt_is_not_comparable() -> None:
    claimed = build_resolved_input_lock(
        _experiment(), _registry(), status="completed", native_runtime=_native()
    )
    assert compare_resolved_input_locks(claimed, claimed).differences == ("completion_evidence",)


def test_truthy_but_incomplete_completion_evidence_is_not_comparable() -> None:
    claimed = build_resolved_input_lock(
        _experiment(), _registry(), status="completed", native_runtime=_native()
    )
    document = claimed.as_dict()
    document["completion_evidence"] = {"receipt_id": "caller-claim"}
    forged = ResolvedInputLock(document, claimed.digest)
    result = compare_resolved_input_locks(forged, forged)
    assert result.comparable is False
    assert result.differences == ("completion_evidence",)


def test_completion_evidence_rejects_receipt_binding_identity_drift() -> None:
    completed = _completed_lock(_experiment(), _registry())
    document = completed.as_dict()
    document["completion_evidence"]["receipt_binding"]["receipt_id"] = "other-receipt"
    forged = ResolvedInputLock(document, completed.digest)
    result = compare_resolved_input_locks(forged, forged)
    assert result.comparable is False
    assert result.differences == ("completion_evidence",)


def test_completed_receipt_cannot_hide_an_unknown_batch_outcome() -> None:
    candidate = build_resolved_input_lock(_experiment(), _registry())
    outcome = project_unresolved_batch_fault(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        expected_world_indices=frozenset({0, 1}),
        error_code="worker_exception",
    )
    observed = join_run_receipt(
        candidate, receipt=_receipt(candidate), native_runtime=_native(), outcome=outcome
    )
    assert observed.status == "unknown"
    assert not compare_resolved_input_locks(observed, observed).comparable


def test_receipt_input_binding_mismatch_is_rejected() -> None:
    candidate = build_resolved_input_lock(_experiment(), _registry())
    different = build_resolved_input_lock(_experiment(), _registry(), policy={"id": "changed"})
    outcome = project_unresolved_batch_fault(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        expected_world_indices=frozenset({0, 1}),
        error_code="worker_exception",
    )
    with pytest.raises(InputLockError, match="receipt_input_binding_mismatch"):
        join_run_receipt(
            candidate, receipt=_receipt(different), native_runtime=_native(), outcome=outcome
        )


def test_host_receipt_binding_is_preserved_and_checked() -> None:
    candidate = build_resolved_input_lock(_experiment(), _registry())
    receipt = _receipt(candidate)
    payload = receipt["payload"]
    native = _native()
    native["receipt_binding"] = {
        "receipt_id": payload["receipt_id"],
        "run_id": payload["run_id"],
        "attempt_id": payload["attempt_id"],
        "host_boot_id": payload["host_boot_id"],
        "writer_generation": payload["writer_generation"],
        "backend_system_graph_sha256": payload["backend"]["system_graph_sha256"],
        "native_validation_evidence_sha256": payload["results"]["native_validation"][
            "evidence_sha256"
        ],
        "durable_ack": payload["completion"]["durable_ack"],
    }
    outcome = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(
            WorldOutcome(0, WorldState.COMPLETED, True),
            WorldOutcome(1, WorldState.COMPLETED, True),
        ),
        expected_world_indices=frozenset({0, 1}),
    )
    joined = join_run_receipt(
        candidate, receipt=receipt, native_runtime=native, outcome=outcome
    )
    assert joined.as_dict()["completion_evidence"]["receipt_binding"] == native[
        "receipt_binding"
    ]

    mismatched = dict(native)
    mismatched["receipt_binding"] = dict(native["receipt_binding"])
    mismatched["receipt_binding"]["run_id"] = "other-run"
    with pytest.raises(InputLockError, match="receipt_binding_mismatch"):
        join_run_receipt(
            candidate, receipt=receipt, native_runtime=mismatched, outcome=outcome
        )


def test_top_level_native_receipt_fields_are_cross_checked_against_owner_receipt() -> None:
    candidate = build_resolved_input_lock(_experiment(), _registry())
    receipt = _receipt(candidate)
    payload = receipt["payload"]
    native = _native()
    native["backend_system_graph_sha256"] = payload["backend"]["system_graph_sha256"]
    native["native_validation_evidence_sha256"] = payload["results"]["native_validation"][
        "evidence_sha256"
    ]
    native["durable_ack"] = payload["completion"]["durable_ack"]
    outcome = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(
            WorldOutcome(0, WorldState.COMPLETED, True),
            WorldOutcome(1, WorldState.COMPLETED, True),
        ),
        expected_world_indices=frozenset({0, 1}),
    )
    joined = join_run_receipt(candidate, receipt=receipt, native_runtime=native, outcome=outcome)
    assert joined.status == "completed"

    native["backend_system_graph_sha256"] = "f" * 64
    with pytest.raises(InputLockError, match="native_receipt_binding_mismatch"):
        join_run_receipt(candidate, receipt=receipt, native_runtime=native, outcome=outcome)


def test_host_published_receipt_path_requires_canonical_owner_bytes(tmp_path) -> None:
    candidate = build_resolved_input_lock(_experiment(), _registry())
    receipt = _receipt(candidate)
    path = tmp_path / "run_receipt.json"
    path.write_bytes(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    outcome = build_batch_outcome(
        batch_generation_ref="g1",
        operation_ref="op1",
        operation="step",
        worlds=(
            WorldOutcome(0, WorldState.COMPLETED, True),
            WorldOutcome(1, WorldState.COMPLETED, True),
        ),
        expected_world_indices=frozenset({0, 1}),
    )
    joined = join_run_receipt_path(
        candidate,
        receipt_path=path,
        native_runtime=_native(),
        outcome=outcome,
    )
    assert joined.status == "completed"

    path.write_text(" {\"not\": \"canonical\"} ", encoding="utf-8")
    with pytest.raises(InputLockError, match="receipt_not_canonical"):
        join_run_receipt_path(
            candidate,
            receipt_path=path,
            native_runtime=_native(),
            outcome=outcome,
        )
