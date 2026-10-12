"""Shared descriptor/native proof for the opt-in Air seeker slice."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from python.mechanisms.air_perception import (
    AIR_PERCEPTION_SCHEMA_VOCABULARY,
    NATIVE_IMPLEMENTATIONS,
    air_perception_composite,
    air_perception_qualification_graph,
)
from python.mechanisms.ports import GraphEdge, MechanismSpec, PortSpec, compile_mechanism_graph
from python.runtime_bootstrap import build_dir
from python.tasking_contracts.failure_domains import (
    BatchResult,
    FailureDomain,
    RecoveryAdmission,
    WorldOutcome,
    WorldState,
    build_batch_outcome,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tests/fixtures/mechanisms/air_perception_qualification.json"


def _config():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_native_slice_is_recursive_and_identity_binds_parameters_backend_and_policy():
    config = _config()
    graph = air_perception_qualification_graph(config)
    assert graph.valid
    assert {
        port.schema
        for _, spec in graph.nodes
        for port in (*spec.inputs, *spec.outputs)
    } <= AIR_PERCEPTION_SCHEMA_VOCABULARY
    assert [
        dict(graph.nodes)[name].implementation_ref for name in ("los", "projection", "tracker")
    ] == list(NATIVE_IMPLEMENTATIONS)
    composite = air_perception_composite(graph)
    assert composite.stateful and composite.backend_ref == "cpu_exact.reference"
    sink = MechanismSpec(
        "qualification.track_consumer",
        "1",
        inputs=(PortSpec("track", "WorldCvTrack.v1", None, "world_enu"),),
        backend_ref=composite.backend_ref,
    )
    parent = compile_mechanism_graph(
        "parent",
        {"perception": composite, "sink": sink},
        (GraphEdge("perception", "track", "sink", "track"),),
        external_inputs=frozenset(
            {"perception.angles", "perception.range_observer", "perception.epochs"}
        ),
    )
    assert parent.valid
    assert graph.identity_digest == air_perception_qualification_graph(_config()).identity_digest
    for key, value in (
        ("implementation_version", "2"),
        ("backend_ref", "qualification.other_backend"),
    ):
        variant = deepcopy(config)
        variant[key] = value
        assert air_perception_qualification_graph(variant).identity_digest != graph.identity_digest
    variant = deepcopy(config)
    variant["tracker_parameters"]["alpha"] = 0.3
    assert air_perception_qualification_graph(variant).identity_digest != graph.identity_digest
    assert (
        air_perception_composite(air_perception_qualification_graph(variant)).implementation_ref
        != composite.implementation_ref
    )
    variant = deepcopy(config)
    variant["clock_policy"]["evidence_note"] = "qualified fixed measurement schedule"
    assert air_perception_qualification_graph(variant).identity_digest != graph.identity_digest
    config["tracker_parameters"]["alpha"] = 0.99
    assert dict(graph.nodes)["tracker"].parameters["alpha"] == 0.2
    with pytest.raises(TypeError):
        dict(graph.nodes)["tracker"].parameters["alpha"] = 0.4


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0, True])
def test_invalid_native_parameters_reject_before_execution(value):
    config = _config()
    config["tracker_parameters"]["minimum_velocity_baseline_s"] = value
    with pytest.raises(ValueError, match="tracker parameter"):
        air_perception_qualification_graph(config)


def test_native_slice_wrong_quantity_rejects_with_stable_edge_path():
    graph = air_perception_qualification_graph(_config())
    nodes = dict(graph.nodes)
    inputs = nodes["tracker"].inputs
    nodes["tracker"] = replace(
        nodes["tracker"], inputs=(replace(inputs[0], unit="kilometer"), inputs[1])
    )
    rejected = compile_mechanism_graph(
        graph.graph_id,
        nodes,
        graph.edges,
        external_inputs=graph.external_inputs,
    )
    assert not rejected.valid
    assert [(diagnostic.code, diagnostic.path) for diagnostic in rejected.diagnostics] == [
        ("mechanism.unit_incompatible", "edges[1]")
    ]


def test_native_elapsed_time_and_child_fault_evidence_use_existing_models(record_property):
    build = Path(build_dir())
    candidates = (build / "Release/ef_test.exe", build / "ef_test.exe", build / "ef_test")
    executable = next((path for path in candidates if path.is_file()), None)
    if executable is None:
        pytest.skip("native qualification requires building the existing ef_test target")
    graph = air_perception_qualification_graph(_config())
    assert graph.valid  # Resolve the descriptor before invoking native test code.
    process = subprocess.run(
        [str(executable), "--test-suite=air_perception_qualification", "--no-colors"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    records = [
        line.removeprefix("RFC229_NATIVE_EVIDENCE=")
        for line in process.stdout.splitlines()
        if line.startswith("RFC229_NATIVE_EVIDENCE=")
    ]
    assert len(records) == 1
    evidence = json.loads(records[0])
    assert evidence["config"] == _config()
    assert evidence["implementations"] == list(NATIVE_IMPLEMENTATIONS)
    assert len(evidence["samples"]) == 4
    assert {row["horizon_s"] for row in evidence["samples"]} == {4.0}
    assert len({row["dt_s"] for row in evidence["samples"]}) == 4
    assert all(
        row["position_error_m"] < 1e-8 and row["velocity_error_mps"] < 1e-9
        for row in evidence["samples"]
    )
    fault = evidence["child_fault"]
    assert fault["state_changed"] and not fault["output_published"] and not fault["rollback_proven"]
    outcome = build_batch_outcome(
        batch_generation_ref="qualification.test_state",
        operation_ref=graph.identity_digest,
        operation="PerceptionComposite",
        domain=FailureDomain.MECHANISM,
        worlds=(WorldOutcome(0, WorldState.UNKNOWN_AFTER_FAULT, None, fault["error_code"]),),
        expected_world_indices=frozenset({0}),
        diagnostics=(fault["error_code"],),
    )
    assert outcome.result is BatchResult.FAILED
    assert outcome.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    # Bind the executed binary separately from descriptor identity. This is
    # local evidence, not a production receipt or a binary trust attestation.
    binary_digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    record_property("mechanism_graph_digest", graph.identity_digest)
    record_property("native_test_binary_sha256", binary_digest)
    record_property("native_qualification_evidence", json.dumps(evidence, sort_keys=True))
