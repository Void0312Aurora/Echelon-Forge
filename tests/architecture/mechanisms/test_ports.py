from __future__ import annotations

import pytest
from dataclasses import replace

from python.mechanisms.ports import (
    GraphEdge,
    MechanismGraphError,
    MechanismSpec,
    PortSpec,
    compile_mechanism_graph,
    compose_graph_as_mechanism,
)


def _sensor() -> MechanismSpec:
    return MechanismSpec(
        "builtin.radar",
        "1",
        outputs=(PortSpec("measurements", "Measurement3D.v1", "meter", "enu"),),
    )


def _tracker() -> MechanismSpec:
    return MechanismSpec(
        "builtin.tracker",
        "1",
        inputs=(PortSpec("measurements", "Measurement3D.v1", "meter", "enu"),),
        outputs=(PortSpec("tracks", "TrackCollection.v1", None, "enu"),),
    )


def test_valid_graph_is_deterministic_and_recursive_composition_preserves_external_ports() -> None:
    graph = compile_mechanism_graph(
        "perception",
        {"tracker": _tracker()},
        (),
        external_inputs=frozenset({"tracker.measurements"}),
    )
    assert graph.valid
    composite = compose_graph_as_mechanism(
        graph,
        mechanism_id="community.perception",
        version="1",
        inputs=(PortSpec("measurements", "Measurement3D.v1", "meter", "enu"),),
        outputs=(PortSpec("tracks", "TrackCollection.v1", None, "enu"),),
        input_bindings={"measurements": "tracker.measurements"},
        output_bindings={"tracks": "tracker.tracks"},
    )
    assert composite.implementation_ref.startswith("composite:")
    assert composite.inputs[0].schema == "Measurement3D.v1"


def test_composite_rejects_unbound_or_fabricated_boundary_ports() -> None:
    graph = compile_mechanism_graph(
        "perception",
        {"tracker": _tracker()},
        (),
        external_inputs=frozenset({"tracker.measurements"}),
    )
    with pytest.raises(MechanismGraphError, match="declared graph external input"):
        compose_graph_as_mechanism(
            graph,
            mechanism_id="bad",
            version="1",
            inputs=(PortSpec("environment", "EnvironmentSnapshot.v1"),),
            outputs=(PortSpec("health", "HealthState.v1"),),
            input_bindings={"environment": "tracker.missing"},
            output_bindings={"health": "tracker.tracks"},
        )
    with pytest.raises(MechanismGraphError, match="type mismatch"):
        compose_graph_as_mechanism(
            graph,
            mechanism_id="bad",
            version="1",
            inputs=(PortSpec("measurements", "Measurement3D.v1", "meter", "enu"),),
            outputs=(PortSpec("health", "HealthState.v1"),),
            input_bindings={"measurements": "tracker.measurements"},
            output_bindings={"health": "tracker.tracks"},
        )


def test_incompatible_schema_unit_and_frame_are_rejected_before_publication() -> None:
    producer = MechanismSpec(
        "producer", "1", outputs=(PortSpec("out", "BearingOnly.v1", "degree", "body"),)
    )
    consumer = MechanismSpec(
        "consumer", "1", inputs=(PortSpec("in", "Measurement3D.v1", "meter", "enu"),)
    )
    graph = compile_mechanism_graph(
        "bad", {"p": producer, "c": consumer}, (GraphEdge("p", "out", "c", "in"),)
    )
    assert graph.valid is False
    assert {item.code for item in graph.diagnostics} == {
        "mechanism.schema_incompatible",
        "mechanism.unit_incompatible",
        "mechanism.frame_incompatible",
    }


def test_unknown_required_input_and_truth_boundary_fail_closed() -> None:
    source = MechanismSpec(
        "source", "1", outputs=(PortSpec("truth", "TrackCollection.v1", None, "enu", "truth"),)
    )
    sink = MechanismSpec(
        "sink",
        "1",
        inputs=(
            PortSpec("tracks", "TrackCollection.v1", None, "enu", "agent_observation"),
            PortSpec("required", "Scalar.v1"),
        ),
    )
    graph = compile_mechanism_graph(
        "boundary",
        {"source": source, "sink": sink},
        (GraphEdge("source", "truth", "sink", "tracks"),),
    )
    assert graph.valid is False
    assert {item.code for item in graph.diagnostics} == {
        "mechanism.truth_boundary_violation",
        "mechanism.required_input_missing",
    }


def test_instantaneous_cycles_are_rejected_but_delayed_feedback_is_explicitly_allowed() -> None:
    node = MechanismSpec(
        "stateful",
        "1",
        inputs=(PortSpec("in", "Scalar.v1"),),
        outputs=(PortSpec("out", "Scalar.v1"),),
        stateful=True,
        clock="per_second",
    )
    instant = compile_mechanism_graph(
        "cycle",
        {"a": node, "b": node},
        (GraphEdge("a", "out", "b", "in"), GraphEdge("b", "out", "a", "in")),
    )
    assert "mechanism.instantaneous_cycle" in {item.code for item in instant.diagnostics}
    delayed = compile_mechanism_graph(
        "feedback",
        {"a": node, "b": node},
        (GraphEdge("a", "out", "b", "in"), GraphEdge("b", "out", "a", "in", delayed=True)),
    )
    assert delayed.valid


def test_external_inputs_cover_required_ports() -> None:
    graph = compile_mechanism_graph(
        "external", {"tracker": _tracker()}, (), external_inputs=frozenset({"tracker.measurements"})
    )
    assert graph.valid


def test_identity_changes_when_semantic_edge_changes() -> None:
    graph_a = compile_mechanism_graph(
        "g",
        {"sensor": _sensor(), "tracker": _tracker()},
        (GraphEdge("sensor", "measurements", "tracker", "measurements"),),
    )
    graph_b = compile_mechanism_graph(
        "g",
        {"sensor": _sensor(), "tracker": _tracker()},
        (GraphEdge("sensor", "measurements", "tracker", "measurements", delayed=True),),
    )
    assert graph_a.identity_digest != graph_b.identity_digest


def test_composite_cannot_hide_a_required_inner_input() -> None:
    graph = compile_mechanism_graph(
        "two-inputs",
        {"a": _tracker(), "b": _tracker()},
        (),
        external_inputs=frozenset({"a.measurements", "b.measurements"}),
    )
    assert graph.valid
    with pytest.raises(MechanismGraphError, match="external input closure"):
        compose_graph_as_mechanism(
            graph,
            mechanism_id="incomplete",
            version="1",
            inputs=(PortSpec("measurements", "Measurement3D.v1", "meter", "enu"),),
            outputs=(PortSpec("tracks", "TrackCollection.v1", None, "enu"),),
            input_bindings={"measurements": "a.measurements"},
            output_bindings={"tracks": "a.tracks"},
        )


def test_temporal_mismatch_and_multiple_producers_require_explicit_adapters() -> None:
    graph = compile_mechanism_graph(
        "g",
        {
            "a": _sensor(),
            "b": replace(_sensor(), stateful=True, clock="per_second"),
            "c": _tracker(),
        },
        (
            GraphEdge("a", "measurements", "c", "measurements"),
            GraphEdge("b", "measurements", "c", "measurements"),
        ),
    )
    assert {d.code for d in graph.diagnostics} == {
        "mechanism.clock_incompatible",
        "mechanism.input_multiple_producers",
    }


def test_truth_cannot_be_relabelled_as_belief_by_an_edge() -> None:
    graph = compile_mechanism_graph(
        "g",
        {
            "a": replace(
                _sensor(),
                outputs=(PortSpec("measurements", "Measurement3D.v1", "meter", "enu", "truth"),),
            ),
            "b": _tracker(),
        },
        (GraphEdge("a", "measurements", "b", "measurements"),),
    )
    assert "mechanism.visibility_incompatible" in {d.code for d in graph.diagnostics}
