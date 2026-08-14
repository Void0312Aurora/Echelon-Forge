from __future__ import annotations

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


def _world_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def test_observation_packet_export_populates_provenance_metadata() -> None:
    facade = ef_py.RuntimeFacade(1)
    ref = _world_ref(0, 1234)

    packet = facade.export_observation_packet([ref])

    assert int(packet.snapshot_version) == 1
    assert packet.barrier_id == "export"
    assert float(packet.source_time_s) >= 0.0
    assert packet.provenance.information_state_layer == "AgentObservation"
    assert packet.provenance.source_label == "facade_observation_packet"
    assert packet.provenance.maintained_status == "maintained"
    assert list(packet.provenance.observation_packet_ids) == ["obs:1"]
    assert list(packet.provenance.source_observation_versions) == ["global:1"]
    assert [(int(item.world_index), int(item.entity_id)) for item in packet.refs] == [
        (0, 1234)
    ]


def test_observation_view_spec_compatibility_major_minor_rules_are_exercised_from_python() -> None:
    checkpoint = ef_py.ObservationViewSpec()
    checkpoint.schema_version = "1.0"
    checkpoint.required_fields = ["pose", "health"]
    checkpoint.optional_fields = ["legacy_heading_raw"]

    provider_minor = ef_py.ObservationViewSpec()
    provider_minor.schema_version = "1.3"
    provider_minor.required_fields = ["pose", "health"]
    provider_minor.optional_fields = ["radar_altitude"]

    provider_major = ef_py.ObservationViewSpec()
    provider_major.schema_version = "2.0"
    provider_major.required_fields = ["pose", "health"]

    minor_report = ef_py.evaluate_observation_view_checkpoint_compatibility(
        checkpoint,
        provider_minor,
    )
    major_report = ef_py.evaluate_observation_view_checkpoint_compatibility(
        checkpoint,
        provider_major,
    )

    assert bool(minor_report.compatible)
    assert bool(minor_report.major_compatible)
    assert not bool(major_report.compatible)
    assert not bool(major_report.major_compatible)
