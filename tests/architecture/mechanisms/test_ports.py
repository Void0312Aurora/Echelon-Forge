from __future__ import annotations

import json
import pytest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from python.mechanisms.ports import (
    FreshnessVocabulary,
    FreshnessVocabularyEntry,
    GraphEdge,
    MechanismGraphError,
    MechanismSchemaVocabulary,
    MechanismSchemaVocabularyRegistry,
    MechanismSpec,
    StageManifestQualificationProjection,
    PortSpec,
    SchemaVocabularyEntry,
    compile_mechanism_graph,
    compose_graph_as_mechanism,
    project_stage_manifest_qualification,
    validate_stage_manifest_bindings,
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


def test_owner_schema_vocabulary_rejects_unknown_port_schema() -> None:
    graph = compile_mechanism_graph(
        "owned-schema",
        {"sensor": _sensor()},
        (),
        known_schemas=frozenset({"TrackCollection.v1"}),
    )
    assert not graph.valid
    assert [(item.code, item.path) for item in graph.diagnostics] == [
        ("mechanism.schema_unknown", "nodes.sensor.outputs.measurements")
    ]


def test_versioned_owner_schema_vocabulary_is_bound_to_graph_identity() -> None:
    vocabulary = MechanismSchemaVocabulary(
        vocabulary_id="test.owner.schemas",
        version="1",
        entries=(SchemaVocabularyEntry("Measurement3D.v1", "native.sensor"),),
    )
    graph = compile_mechanism_graph(
        "owned-schema",
        {"sensor": _sensor()},
        (),
        schema_vocabulary=vocabulary,
    )
    assert graph.valid
    assert graph.schema_vocabulary_ref == "test.owner.schemas"
    assert graph.schema_vocabulary_version == "1"
    assert graph.schema_vocabulary_digest == vocabulary.identity_digest
    assert graph.as_dict()["schema_vocabulary"]["identity_digest"] == vocabulary.identity_digest
    assert vocabulary.identity_digest == "aa3e4b77f4531bc67eaa2cdc5bc9456ba77013d2eebe55eea5288a0c05977de8"
    assert graph.identity_digest == "fc78b1071370b1348f1017cefa7ff07e69a6e7b91679b985a8cd18abe2abb3a7"

    changed = replace(
        vocabulary,
        entries=(SchemaVocabularyEntry("Measurement3D.v1", "native.sensor.v2"),),
    )
    changed_graph = compile_mechanism_graph(
        "owned-schema",
        {"sensor": _sensor()},
        (),
        schema_vocabulary=changed,
    )
    assert changed_graph.valid
    assert changed_graph.identity_digest != graph.identity_digest


def test_schema_vocabulary_rejects_duplicate_entries_and_mixed_api() -> None:
    with pytest.raises(ValueError, match="unique schema names"):
        MechanismSchemaVocabulary(
            vocabulary_id="duplicate",
            version="1",
            entries=(
                SchemaVocabularyEntry("Measurement3D.v1", "native.sensor"),
                SchemaVocabularyEntry("Measurement3D.v1", "native.sensor.v2"),
            ),
        )
    with pytest.raises(MechanismGraphError, match="mutually exclusive"):
        compile_mechanism_graph(
            "mixed-schema-api",
            {"sensor": _sensor()},
            (),
            known_schemas=frozenset({"Measurement3D.v1"}),
            schema_vocabulary=MechanismSchemaVocabulary(
                vocabulary_id="test.owner.schemas",
                version="1",
                entries=(SchemaVocabularyEntry("Measurement3D.v1", "native.sensor"),),
            ),
        )


def test_owner_schema_registry_merges_explicit_vocabularies_and_binds_digest() -> None:
    first = MechanismSchemaVocabulary(
        vocabulary_id="owner.sensor.schemas",
        version="1",
        entries=(
            SchemaVocabularyEntry("Measurement3D.v1", "native.sensor"),
            SchemaVocabularyEntry("WorldDirection3.v1", "native.sensor"),
        ),
    )
    second = MechanismSchemaVocabulary(
        vocabulary_id="owner.tracker.schemas",
        version="1",
        entries=(
            SchemaVocabularyEntry("Measurement3D.v1", "native.sensor"),
            SchemaVocabularyEntry("TrackCollection.v1", "native.tracker"),
        ),
    )
    registry = MechanismSchemaVocabularyRegistry(
        registry_id="qualification.repository.schemas",
        version="1",
        vocabularies=(second, first),
    )

    assert registry.vocabulary_id == "qualification.repository.schemas"
    assert registry.schema_names == frozenset(
        {"Measurement3D.v1", "WorldDirection3.v1", "TrackCollection.v1"}
    )
    assert [item.vocabulary_id for item in registry.vocabularies] == [
        "owner.sensor.schemas",
        "owner.tracker.schemas",
    ]
    graph = compile_mechanism_graph(
        "registry-bound",
        {"sensor": _sensor()},
        (),
        schema_vocabulary=registry,
    )
    assert graph.valid
    assert graph.schema_vocabulary_ref == registry.registry_id
    assert graph.schema_vocabulary_digest == registry.identity_digest
    assert registry.identity_digest == "270cfad8a4d94c816a9cfcb8b32a0495ef624ed859ca4f6cb5e0b2318127543d"
    assert graph.identity_digest == "6217d7083f890fe1314bae192717a92f998818d985d28a2434feeba213fbf7e2"
    assert registry.as_dict() == replace(registry, vocabularies=(first, second)).as_dict()
    assert [entry.schema for entry in registry.entries] == sorted(registry.schema_names)
    merged_graph = compile_mechanism_graph(
        "merged-owner-graph",
        {"sensor": _sensor(), "tracker": _tracker()},
        (GraphEdge("sensor", "measurements", "tracker", "measurements"),),
        schema_vocabulary=registry,
    )
    assert merged_graph.valid
    assert registry.identity_digest != replace(
        registry, vocabularies=(first, replace(second, version="2"))
    ).identity_digest

    with pytest.raises(ValueError, match="owner conflict"):
        MechanismSchemaVocabularyRegistry(
            registry_id="conflict",
            version="1",
            vocabularies=(
                first,
                replace(
                    second,
                    entries=(SchemaVocabularyEntry("Measurement3D.v1", "other.owner"),),
                ),
            ),
        )


def test_freshness_is_part_of_edge_and_composite_compatibility() -> None:
    producer = MechanismSpec(
        "producer",
        "1",
        outputs=(PortSpec("out", "Track.v1", freshness="per_window"),),
    )
    consumer = MechanismSpec(
        "consumer",
        "1",
        inputs=(PortSpec("in", "Track.v1", freshness="per_tick"),),
    )
    graph = compile_mechanism_graph(
        "freshness",
        {"p": producer, "c": consumer},
        (GraphEdge("p", "out", "c", "in"),),
    )
    assert not graph.valid
    assert "mechanism.freshness_incompatible" in {item.code for item in graph.diagnostics}

    with pytest.raises(ValueError, match="freshness"):
        PortSpec("invalid", "Track.v1", freshness="")


def test_owner_freshness_vocabulary_rejects_unknown_labels_and_binds_identity() -> None:
    vocabulary = FreshnessVocabulary(
        vocabulary_id="test.owner.freshness",
        version="1",
        entries=(
            FreshnessVocabularyEntry("per_window", "native.window_owner"),
            FreshnessVocabularyEntry("per_tick", "native.tick_owner"),
        ),
    )
    producer = MechanismSpec(
        "producer",
        "1",
        outputs=(PortSpec("out", "Track.v1", freshness="per_window"),),
    )
    consumer = MechanismSpec(
        "consumer",
        "1",
        inputs=(PortSpec("in", "Track.v1", freshness="per_window"),),
    )
    graph = compile_mechanism_graph(
        "owned-freshness",
        {"p": producer, "c": consumer},
        (GraphEdge("p", "out", "c", "in"),),
        freshness_vocabulary=vocabulary,
    )
    assert graph.valid
    assert graph.freshness_vocabulary_ref == vocabulary.vocabulary_id
    assert graph.freshness_vocabulary_version == vocabulary.version
    assert graph.freshness_vocabulary_digest == vocabulary.identity_digest
    assert graph.as_dict()["freshness_vocabulary"]["identity_digest"] == vocabulary.identity_digest

    unknown = compile_mechanism_graph(
        "owned-freshness",
        {"p": replace(producer, outputs=(PortSpec("out", "Track.v1", freshness="per_frame"),)), "c": consumer},
        (GraphEdge("p", "out", "c", "in"),),
        freshness_vocabulary=vocabulary,
    )
    assert ("mechanism.freshness_unknown", "nodes.p.outputs.out") in {
        (item.code, item.path) for item in unknown.diagnostics
    }

    changed = replace(
        vocabulary,
        entries=(
            FreshnessVocabularyEntry("per_window", "native.window_owner.v2"),
            FreshnessVocabularyEntry("per_tick", "native.tick_owner"),
        ),
    )
    changed_graph = compile_mechanism_graph(
        "owned-freshness",
        {"p": producer, "c": consumer},
        (GraphEdge("p", "out", "c", "in"),),
        freshness_vocabulary=changed,
    )
    assert changed_graph.identity_digest != graph.identity_digest


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
        delay_windows=1,
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
        (
            GraphEdge("a", "out", "b", "in"),
            GraphEdge("b", "out", "a", "in", delayed=True, delay_windows=1, state_owner="b"),
        ),
    )
    assert delayed.valid


def test_external_inputs_cover_required_ports() -> None:
    graph = compile_mechanism_graph(
        "external", {"tracker": _tracker()}, (), external_inputs=frozenset({"tracker.measurements"})
    )
    assert graph.valid


def test_delayed_feedback_requires_positive_window_and_source_state_owner() -> None:
    stateless = MechanismSpec(
        "stateless",
        "1",
        inputs=(PortSpec("in", "Scalar.v1"),),
        outputs=(PortSpec("out", "Scalar.v1"),),
    )
    graph = compile_mechanism_graph(
        "invalid-feedback",
        {"a": stateless, "b": stateless},
        (
            GraphEdge("a", "out", "b", "in"),
            GraphEdge("b", "out", "a", "in", delayed=True),
        ),
    )
    assert not graph.valid
    assert {
        "mechanism.delayed_edge_window_missing",
        "mechanism.delayed_edge_state_owner_missing",
    } <= {item.code for item in graph.diagnostics}

    owner_mismatch = compile_mechanism_graph(
        "owner-mismatch",
        {
            "a": MechanismSpec(
                "stateful-a",
                "1",
                inputs=(PortSpec("in", "Scalar.v1"),),
                outputs=(PortSpec("out", "Scalar.v1"),),
                stateful=True,
                delay_windows=1,
            ),
            "b": stateless,
        },
        (
            GraphEdge("a", "out", "b", "in"),
            GraphEdge("b", "out", "a", "in", delayed=True, delay_windows=1, state_owner="a"),
        ),
    )
    assert not owner_mismatch.valid
    assert "mechanism.delayed_edge_state_owner_mismatch" in {
        item.code for item in owner_mismatch.diagnostics
    }

    owner_not_stateful = compile_mechanism_graph(
        "owner-not-stateful",
        {"a": stateless, "b": stateless},
        (
            GraphEdge("a", "out", "b", "in"),
            GraphEdge("b", "out", "a", "in", delayed=True, delay_windows=1, state_owner="b"),
        ),
    )
    assert not owner_not_stateful.valid
    assert "mechanism.delayed_edge_state_owner_not_stateful" in {
        item.code for item in owner_not_stateful.diagnostics
    }


def test_composite_preserves_declared_delay_window() -> None:
    node = MechanismSpec(
        "stateful",
        "1",
        inputs=(PortSpec("in", "Scalar.v1"),),
        outputs=(PortSpec("out", "Scalar.v1"),),
        stateful=True,
        delay_windows=2,
    )
    graph = compile_mechanism_graph(
        "delayed-composite",
        {"node": node},
        (),
        external_inputs=frozenset({"node.in"}),
    )
    composite = compose_graph_as_mechanism(
        graph,
        mechanism_id="community.delayed",
        version="1",
        inputs=(PortSpec("in", "Scalar.v1"),),
        outputs=(PortSpec("out", "Scalar.v1"),),
        input_bindings={"in": "node.in"},
        output_bindings={"out": "node.out"},
    )
    assert composite.delay_windows == 2
    assert composite.clock_policy["delay_windows"] == 2


def test_identity_changes_when_semantic_edge_changes() -> None:
    graph_a = compile_mechanism_graph(
        "g",
        {"sensor": _sensor(), "tracker": _tracker()},
        (GraphEdge("sensor", "measurements", "tracker", "measurements"),),
    )
    delayed_sensor = MechanismSpec(
        "builtin.radar",
        "1",
        outputs=(PortSpec("measurements", "Measurement3D.v1", "meter", "enu"),),
        stateful=True,
        delay_windows=1,
    )
    graph_b = compile_mechanism_graph(
        "g",
        {"sensor": delayed_sensor, "tracker": _tracker()},
        (
            GraphEdge(
                "sensor",
                "measurements",
                "tracker",
                "measurements",
                delayed=True,
                delay_windows=1,
                state_owner="sensor",
            ),
        ),
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


def test_stage_manifest_binding_consumes_owner_snapshot_and_checks_realized_order() -> None:
    producer = replace(_sensor(), implementation_ref="native.sensor")
    consumer = replace(_tracker(), implementation_ref="native.tracker")
    graph = compile_mechanism_graph(
        "native-qualification",
        {"sensor": producer, "tracker": consumer},
        (GraphEdge("sensor", "measurements", "tracker", "measurements"),),
    )
    manifests = {
        "native.sensor.v1": {
            "node_id": "native.sensor.v1",
            "semantic_stage": ["P8 Sensor"],
            "owner_module": "native.sensor",
            "facade_visibility": "maintained_facade_surface",
            "native_system": "SensorSystem",
        },
        "native.tracker.v1": {
            "node_id": "native.tracker.v1",
            "semantic_stage": ["P10 ObservationExport"],
            "owner_module": "native.tracker",
            "facade_visibility": "maintained_facade_surface",
            "native_system": "TrackerSystem",
        },
    }
    assert validate_stage_manifest_bindings(
        graph,
        node_stage_bindings={"sensor": "native.sensor.v1", "tracker": "native.tracker.v1"},
        stage_manifests=manifests,
        pipeline_order=("SensorSystem", "TrackerSystem"),
    ) == ()
    reversed_diagnostics = validate_stage_manifest_bindings(
        graph,
        node_stage_bindings={"sensor": "native.sensor.v1", "tracker": "native.tracker.v1"},
        stage_manifests=manifests,
        pipeline_order=("TrackerSystem", "SensorSystem"),
    )
    assert [item.code for item in reversed_diagnostics] == ["mechanism.realized_order_mismatch"]


def test_stage_manifest_binding_rejects_projection_and_missing_owner_evidence() -> None:
    graph = compile_mechanism_graph(
        "native-qualification", {"tracker": replace(_tracker(), implementation_ref="native.tracker")}, (),
        external_inputs=frozenset({"tracker.measurements"}),
    )
    diagnostics = validate_stage_manifest_bindings(
        graph,
        node_stage_bindings={"tracker": "projection"},
        stage_manifests={
            "projection": {
                "node_id": "projection",
                "semantic_stage": ["P10"],
                "owner_module": "adapter",
                "facade_visibility": "adapter_projection",
                "native_system": "ProjectionSystem",
            }
        },
    )
    assert [item.code for item in diagnostics] == ["mechanism.native_stage_not_scheduler_truth"]
    with pytest.raises(MechanismGraphError, match="cover every graph node"):
        validate_stage_manifest_bindings(
            graph,
            node_stage_bindings={},
            stage_manifests={},
        )


def test_strict_stage_manifest_admission_rejects_shard_conflicts() -> None:
    graph = compile_mechanism_graph(
        "native-qualification",
        {
            "a": replace(_sensor(), implementation_ref="native.a"),
            "b": replace(_tracker(), implementation_ref="native.b"),
        },
        (),
        external_inputs=frozenset({"b.measurements"}),
    )
    common = {
        "semantic_stage": ["P8"],
        "owner_module": "native.owner",
        "input_packets": ["InputPacket"],
        "output_packets": ["OutputPacket"],
        "read_state_shards": ["state"],
        "read_snapshot_policy": "committed",
        "write_commit_policy": "window_commit",
        "clock_domain": "window",
        "latency_policy": "same_window",
        "sync_policy": "host_owned",
        "required_barriers": ["window_commit"],
        "diagnostic_trace_obligations": ["trace_id"],
        "allowed_same_window_edges": ["stage.a->stage.b"],
        "facade_visibility": "internal",
        "native_system": "NativeSystem",
        "write_state_shards": ["shared"],
    }
    manifests = {
        "stage.a": {**common, "node_id": "stage.a"},
        "stage.b": {**common, "node_id": "stage.b"},
    }
    diagnostics = validate_stage_manifest_bindings(
        graph,
        node_stage_bindings={"a": "stage.a", "b": "stage.b"},
        stage_manifests=manifests,
        require_native_contract=True,
    )
    assert "mechanism.native_stage_write_shard_conflict" in {item.code for item in diagnostics}


def test_strict_stage_manifest_admission_rejects_malformed_owner_fields_and_publish_claims() -> None:
    graph = compile_mechanism_graph(
        "native-qualification-shape",
        {"node": replace(_sensor(), implementation_ref="native.node")},
        (),
    )
    manifest = {
        "node_id": "stage.node",
        "semantic_stage": ["P8"],
        "owner_module": "native.owner",
        "input_packets": "InputPacket",
        "output_packets": ["ObservationEvent"],
        "read_state_shards": ["state"],
        "write_state_shards": [],
        "read_snapshot_policy": "committed",
        "write_commit_policy": "stage_publish",
        "clock_domain": "window",
        "latency_policy": "same_window",
        "sync_policy": "host_owned",
        "allowed_same_window_edges": [],
        "required_barriers": ["window_commit"],
        "event_families_emitted": [],
        "diagnostic_trace_obligations": ["trace_id"],
        "facade_visibility": "internal",
        "adapter_projection_allowed": False,
        "native_system": "NativeSystem",
    }
    diagnostics = validate_stage_manifest_bindings(
        graph,
        node_stage_bindings={"node": "stage.node"},
        stage_manifests={"stage.node": manifest},
        require_native_contract=True,
    )
    codes = {item.code for item in diagnostics}
    assert {
        "mechanism.native_stage_contract_field_invalid",
        "mechanism.native_stage_same_window_edges_missing",
        "mechanism.native_stage_publish_barrier_missing",
        "mechanism.native_stage_event_families_missing",
    } <= codes


def _native_projection_fixture():
    graph = compile_mechanism_graph(
        "native-projection",
        {
            "sensor": replace(_sensor(), implementation_ref="native.sensor"),
            "tracker": replace(_tracker(), implementation_ref="native.tracker"),
        },
        (GraphEdge("sensor", "measurements", "tracker", "measurements"),),
    )
    common = {
        "semantic_stage": ["P8"],
        "owner_module": "native.owner",
        "input_packets": ["InputPacket"],
        "output_packets": ["OutputPacket"],
        "read_state_shards": ["state"],
        "write_state_shards": [],
        "read_snapshot_policy": "committed",
        "write_commit_policy": "window_commit",
        "clock_domain": "window",
        "latency_policy": "same_window",
        "sync_policy": "host_owned",
        "allowed_same_window_edges": ["stage.sensor->stage.tracker"],
        "required_barriers": ["window_commit"],
        "diagnostic_trace_obligations": ["trace_id"],
        "facade_visibility": "internal",
        "adapter_projection_allowed": False,
    }
    manifests = {
        "stage.sensor": {
            **common,
            "node_id": "stage.sensor",
            "owner_module": "native.sensor",
            "native_system": "SensorSystem",
        },
        "stage.tracker": SimpleNamespace(
            **{
                **common,
                "node_id": "stage.tracker",
                "owner_module": "native.tracker",
            }
        ),
    }
    return graph, manifests


def test_stage_manifest_projection_emits_stable_owner_bound_qualification_only_artifact() -> None:
    graph, manifests = _native_projection_fixture()

    projection = project_stage_manifest_qualification(
        graph,
        node_stage_bindings={"sensor": "stage.sensor", "tracker": "stage.tracker"},
        stage_manifests=manifests,
        pipeline_order=("SensorSystem", "native.tracker"),
    )

    assert isinstance(projection, StageManifestQualificationProjection)
    assert projection.qualification_only
    assert not projection.executable
    assert projection.graph_identity_digest == graph.identity_digest
    assert [item.node_id for item in projection.node_contracts] == ["sensor", "tracker"]
    assert projection.node_contracts[1].owner_contract["node_id"] == "stage.tracker"
    assert "native_system" not in projection.node_contracts[1].owner_contract
    assert graph.identity_digest == "d2edb8749cf2f9aad15e5f575011e999426a2b9091d469591ec667cc4577cc60"
    assert projection.manifest_registry_digest == "f874257e05a8fd74c0858f3a78c86a1f5bf5b894618a344beefffa6410b7677d"
    assert projection.identity_digest == "5a68b37dc80baa7c965e8248bd5118ac1fd684c8bc51ca7c49977119d7d4fa06"
    assert [item.identity_digest for item in projection.node_contracts] == [
        "65273c2e7961deabee675500a7858255789ccbea0b3c089fa565e298ea6a9136",
        "44b0464a01ca874ca73cdfdb9f893e6ca24a05fa58d224541e19aecfb6b95510",
    ]
    assert projection.identity_digest == project_stage_manifest_qualification(
        graph,
        node_stage_bindings={"sensor": "stage.sensor", "tracker": "stage.tracker"},
        stage_manifests=manifests,
        pipeline_order=("SensorSystem", "native.tracker"),
    ).identity_digest
    snapshot = projection.as_dict()
    manifests["stage.tracker"].node_id = "stage.tracker.v2"
    manifests["stage.tracker"].owner_module = "new.owner"
    manifests["stage.sensor"]["required_barriers"].append("export")
    assert projection.as_dict() == snapshot
    exported = projection.as_dict()
    exported["node_contracts"][0]["owner_contract"]["required_barriers"].append("mutated")
    assert projection.as_dict() == snapshot


@pytest.mark.parametrize(("field_name", "value"), [
    ("semantic_stage", ["P8 revised"]),
    ("owner_module", "native.sensor.v2"),
    ("input_packets", ["RevisedInputPacket"]),
    ("output_packets", ["RevisedOutputPacket"]),
    ("read_state_shards", ["revised_state"]),
    ("write_state_shards", ["sensor_state"]),
    ("read_snapshot_policy", "post_injection"),
    ("write_commit_policy", "export_only"),
    ("clock_domain", "event_driven"),
    ("latency_policy", "window_commit_same_timestamp"),
    ("sync_policy", "explicit_export"),
    ("allowed_same_window_edges", ["stage.sensor->stage.tracker:revised"]),
    ("required_barriers", ["window_commit", "export"]),
    ("event_families_emitted", ["sensor_events"]),
    ("diagnostic_trace_obligations", ["source_snapshot_version"]),
    ("facade_visibility", "maintained_facade_export"),
    ("adapter_projection_allowed", True),
    ("native_system", "RevisedSensorSystem"),
])
def test_projection_rejects_stale_owner_snapshot_for_every_retained_field(field_name, value):
    graph, manifests = _native_projection_fixture()
    bindings = {"sensor": "stage.sensor", "tracker": "stage.tracker"}
    stale = project_stage_manifest_qualification(
        graph, node_stage_bindings=bindings, stage_manifests=manifests,
    )
    current_manifests = {
        **manifests, "stage.sensor": {**manifests["stage.sensor"], field_name: value},
    }
    current = project_stage_manifest_qualification(
        graph, node_stage_bindings=bindings, stage_manifests=current_manifests,
    )
    assert current.graph_identity_digest == stale.graph_identity_digest
    assert current.manifest_registry_digest != stale.manifest_registry_digest
    assert current.identity_digest != stale.identity_digest
    assert current.node_contracts[0].identity_digest != stale.node_contracts[0].identity_digest
    assert current.node_contracts[1].identity_digest == stale.node_contracts[1].identity_digest
    assert project_stage_manifest_qualification(
        graph, node_stage_bindings=bindings, stage_manifests=current_manifests,
        expected_manifest_registry_digest=current.manifest_registry_digest,
    ).as_dict() == current.as_dict()
    with pytest.raises(MechanismGraphError, match="native_stage_manifest_stale"):
        project_stage_manifest_qualification(
            graph, node_stage_bindings=bindings, stage_manifests=manifests,
            expected_manifest_registry_digest=current.manifest_registry_digest,
        )


def test_projection_rejects_stale_native_manifest_version_under_new_binding():
    graph, manifests = _native_projection_fixture()
    with pytest.raises(MechanismGraphError, match="native_stage_manifest_identity_mismatch"):
        project_stage_manifest_qualification(
            graph,
            node_stage_bindings={"sensor": "stage.sensor.v2", "tracker": "stage.tracker"},
            stage_manifests={**manifests, "stage.sensor.v2": manifests["stage.sensor"]},
        )


@pytest.mark.parametrize("change", ["freshness", "visibility", "clock", "delay", "parameters"])
def test_authored_semantics_keep_identity_separate_from_native_snapshot(change):
    graph, manifests = _native_projection_fixture()
    bindings = {"sensor": "stage.sensor", "tracker": "stage.tracker"}
    baseline = project_stage_manifest_qualification(
        graph, node_stage_bindings=bindings, stage_manifests=manifests,
    )
    nodes = {}
    for node_id, spec in graph.nodes:
        if change in {"freshness", "visibility"}:
            port_change = {change: "per_tick" if change == "freshness" else "truth"}
            spec = replace(
                spec,
                inputs=tuple(replace(port, **port_change) for port in spec.inputs),
                outputs=tuple(replace(port, **port_change) for port in spec.outputs),
            )
        elif change == "clock":
            spec = replace(spec, stateful=True, clock="per_second")
        elif change == "delay":
            spec = replace(spec, stateful=True, delay_windows=1)
        else:
            spec = replace(spec, parameters={"gain": 0.5})
        nodes[node_id] = spec
    changed_graph = compile_mechanism_graph(graph.graph_id, nodes, graph.edges)
    assert changed_graph.valid
    changed = project_stage_manifest_qualification(
        changed_graph, node_stage_bindings=bindings, stage_manifests=manifests,
        expected_manifest_registry_digest=baseline.manifest_registry_digest,
    )
    assert changed.graph_identity_digest != baseline.graph_identity_digest
    assert changed.identity_digest != baseline.identity_digest
    assert changed.manifest_registry_digest == baseline.manifest_registry_digest


def test_existing_air_seeker_fixture_retains_vocabulary_graph_and_composite_identities():
    from python.mechanisms.air_perception import (
        AIR_PERCEPTION_OWNER_SCHEMA_VOCABULARY,
        air_perception_composite,
        air_perception_qualification_graph,
    )

    fixture = Path(__file__).resolve().parents[2] / "fixtures/mechanisms/air_perception_qualification.json"
    graph = air_perception_qualification_graph(json.loads(fixture.read_text(encoding="utf-8")))
    assert graph.valid
    assert graph.schema_version == "echelon_forge.mechanism_ports.v1"
    assert AIR_PERCEPTION_OWNER_SCHEMA_VOCABULARY.version == "1"
    assert graph.schema_vocabulary_digest == "97efe5aab24b95b3b04dc7c999dab67c47d03ba9f17e4e2885822ccc09836165"
    assert graph.identity_digest == "5d6e796479250b6dd2ea0b4e0c8474d41705602839d6612bff749f934f747abe"
    assert air_perception_composite(graph).implementation_ref == (
        "composite:1da7b280da71a9de2e3df8a9ea53c98fd3759bfa401d42588b766fd6eef9c8dd"
    )


def test_air_launch_to_observation_graph_lowers_to_native_owner_snapshot():
    from python.runtime_bootstrap import ensure_repo_imports

    try:
        ensure_repo_imports()
    except RuntimeError as error:
        if "No local ef_py build artifact found" not in str(error):
            raise
        pytest.skip("requires the local ef_py build for the native owner snapshot")
    import ef_py

    runtime = ef_py.WorldBatchRuntime(1)
    manifests = {item.node_id: item for item in runtime.maintained_stage_node_manifests()}
    launch = manifests["fire_control_launch.v1"]
    observation = manifests["observation_export.v1"]
    assert "LaunchEvent" in launch.output_packets
    assert "LaunchEvent" in observation.input_packets
    graph = compile_mechanism_graph(
        "qualification.air.launch_to_observation",
        {
            "launch": MechanismSpec(
                "air.fire_control_launch", "1", stateful=True,
                inputs=(PortSpec("request", "LaunchRequest"), PortSpec("track", "TrackPacket")),
                outputs=(PortSpec("event", "LaunchEvent", visibility="effect"),),
                implementation_ref=launch.owner_module,
            ),
            "observation": MechanismSpec(
                "air.observation_export", "1",
                inputs=(PortSpec("launch", "LaunchEvent", visibility="effect"),),
                outputs=(PortSpec("observation", "ObservationBatchPacket", visibility="agent_observation"),),
                implementation_ref=observation.owner_module,
            ),
        },
        (GraphEdge("launch", "event", "observation", "launch"),),
        external_inputs=frozenset({"launch.request", "launch.track"}),
    )
    assert graph.valid
    projection = project_stage_manifest_qualification(
        graph,
        node_stage_bindings={"launch": launch.node_id, "observation": observation.node_id},
        stage_manifests=manifests,
    )
    assert projection.qualification_only and not projection.executable
    assert projection.edge_bindings == graph.edges
    assert [item.stage_node_id for item in projection.node_contracts] == [launch.node_id, observation.node_id]
    assert all("native_system" not in item.owner_contract for item in projection.node_contracts)
    assert projection.node_contracts[0].owner_contract["write_state_shards"] == tuple(launch.write_state_shards)
    pinned_digest = projection.manifest_registry_digest
    launch.read_snapshot_policy = "pre_window"
    with pytest.raises(MechanismGraphError, match="native_stage_manifest_stale"):
        project_stage_manifest_qualification(
            graph,
            node_stage_bindings={"launch": launch.node_id, "observation": observation.node_id},
            stage_manifests=manifests,
            expected_manifest_registry_digest=pinned_digest,
        )
    fresh_launch = next(
        item for item in runtime.maintained_stage_node_manifests() if item.node_id == launch.node_id
    )
    assert fresh_launch.read_snapshot_policy == "post_injection"
    assert projection.node_contracts[0].owner_contract["read_snapshot_policy"] == "post_injection"


def test_stage_manifest_projection_rejects_duplicate_or_non_scheduler_bindings() -> None:
    graph = compile_mechanism_graph(
        "native-projection",
        {
            "sensor": replace(_sensor(), implementation_ref="native.sensor"),
            "tracker": replace(_tracker(), implementation_ref="native.tracker"),
        },
        (),
        external_inputs=frozenset({"tracker.measurements"}),
    )
    with pytest.raises(MechanismGraphError, match="one-to-one"):
        project_stage_manifest_qualification(
            graph,
            node_stage_bindings={"sensor": "stage", "tracker": "stage"},
            stage_manifests={
                "stage": {
                    "node_id": "stage",
                    "semantic_stage": ["P8"],
                    "owner_module": "adapter",
                    "facade_visibility": "adapter_projection",
                }
            },
        )
    single_graph = compile_mechanism_graph(
        "native-projection-single",
        {"sensor": replace(_sensor(), implementation_ref="native.sensor")},
        (),
    )
    with pytest.raises(MechanismGraphError, match="native_stage_not_scheduler_truth"):
        project_stage_manifest_qualification(
            single_graph,
            node_stage_bindings={"sensor": "projection"},
            stage_manifests={
                "projection": {
                    "node_id": "projection",
                    "semantic_stage": ["P8"],
                    "owner_module": "adapter",
                    "facade_visibility": "adapter_projection",
                }
            },
        )
