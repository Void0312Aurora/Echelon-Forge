from __future__ import annotations

import pytest
from dataclasses import replace
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


def test_stage_manifest_projection_emits_stable_owner_bound_qualification_only_artifact() -> None:
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
    assert projection.identity_digest == project_stage_manifest_qualification(
        graph,
        node_stage_bindings={"sensor": "stage.sensor", "tracker": "stage.tracker"},
        stage_manifests=manifests,
        pipeline_order=("SensorSystem", "native.tracker"),
    ).identity_digest


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
